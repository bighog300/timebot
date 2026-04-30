from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from difflib import SequenceMatcher
from itertools import combinations
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

try:
    from sqlalchemy.orm import Session
except ModuleNotFoundError:  # pragma: no cover - local test fallback when deps are unavailable
    Session = Any

try:
    from app.models.document import Document
    from app.models.relationships import DocumentRelationship
except ModuleNotFoundError:  # pragma: no cover - local test fallback when deps are unavailable
    class _ModelFieldFallback:
        def is_(self, *_args, **_kwargs):
            return self

        def __eq__(self, _other):
            return self

        def __ne__(self, _other):
            return self

        def desc(self):
            return self

    class DocumentRelationship:  # type: ignore[no-redef]
        source_doc_id = _ModelFieldFallback()
        target_doc_id = _ModelFieldFallback()
        relationship_type = _ModelFieldFallback()

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    class Document:  # type: ignore[no-redef]
        id = _ModelFieldFallback()
        is_archived = _ModelFieldFallback()
        upload_date = _ModelFieldFallback()
from app.services.embedding_service import embedding_service
from app.services.relationship_review import relationship_review_service

logger = logging.getLogger(__name__)


@dataclass
class RelationshipCandidate:
    source_doc_id: UUID
    target_doc_id: UUID
    relationship_type: str
    confidence: float
    metadata: Dict


class RelationshipDetectionService:
    """Deterministic relationship detection with optional semantic boost."""

    def detect_for_document(self, db: Session, document_id: UUID, limit: int = 50) -> Dict[str, int]:
        logger.info("Relationship detection started doc_id=%s", document_id)
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.warning("Relationship detection skipped; source document missing doc_id=%s", document_id)
            return {"created": 0, "updated": 0, "scanned": 0}

        candidates = (
            db.query(Document)
            .filter(Document.id != document_id, Document.is_archived.is_(False))
            .order_by(Document.upload_date.desc())
            .limit(limit)
            .all()
        )

        matches = [self._score_pair(doc, other) for other in candidates]
        detected = [m for m in matches if m is not None]
        logger.info("Relationship candidates found=%d doc_id=%s", len(detected), document_id)
        persisted = self._persist_candidates(db, detected)
        persisted["scanned"] = len(candidates)
        return persisted

    def backfill_relationships(self, db: Session, limit: Optional[int] = None) -> Dict[str, int]:
        query = db.query(Document).filter(Document.is_archived.is_(False)).order_by(Document.upload_date.desc())
        docs = query.limit(limit).all() if limit else query.all()

        candidates: List[RelationshipCandidate] = []
        for left, right in combinations(docs, 2):
            result = self._score_pair(left, right)
            if result:
                candidates.append(result)

        persisted = self._persist_candidates(db, candidates)
        persisted["scanned"] = len(docs)
        return persisted

    def _score_pair(self, left: Document, right: Document) -> Optional[RelationshipCandidate]:
        left_tags = set((left.ai_tags or []) + (left.user_tags or []))
        right_tags = set((right.ai_tags or []) + (right.user_tags or []))

        tag_overlap = len(left_tags & right_tags) / max(len(left_tags | right_tags), 1)
        entity_overlap = self._entity_overlap(left.entities or {}, right.entities or {})
        title_similarity = SequenceMatcher(None, (left.filename or "").lower(), (right.filename or "").lower()).ratio()
        text_similarity = SequenceMatcher(None, (left.summary or "").lower(), (right.summary or "").lower()).ratio()

        date_adjacent = 0.0
        if left.upload_date and right.upload_date:
            delta = abs((left.upload_date - right.upload_date).days)
            date_adjacent = 1.0 if delta <= 2 else (0.6 if delta <= 7 else 0.0)

        semantic = self._semantic_similarity(str(left.id), str(right.id))

        weighted = {
            "title_similarity": title_similarity * 0.25,
            "summary_similarity": text_similarity * 0.2,
            "tag_overlap": tag_overlap * 0.2,
            "entity_overlap": entity_overlap * 0.15,
            "date_adjacency": date_adjacent * 0.1,
            "semantic_similarity": semantic * 0.1,
        }
        score = sum(weighted.values())

        relationship_type = "related_to"
        if score >= 0.92 or (title_similarity > 0.9 and text_similarity > 0.9):
            relationship_type = "duplicates"
        elif date_adjacent >= 1.0 and entity_overlap >= 0.3:
            relationship_type = "follows_up"
        elif semantic > 0.75 or score > 0.65:
            relationship_type = "similar_to"

        if score < 0.45:
            logger.debug(
                "Relationship skipped low-score left=%s right=%s score=%.5f signals=%s",
                left.id,
                right.id,
                score,
                {k: round(v, 5) for k, v in weighted.items()},
            )
            return None

        source_id, target_id = (left.id, right.id) if str(left.id) < str(right.id) else (right.id, left.id)
        return RelationshipCandidate(
            source_doc_id=source_id,
            target_doc_id=target_id,
            relationship_type=relationship_type,
            confidence=round(min(score, 1.0), 5),
            metadata={
                "signals": {k: round(v, 5) for k, v in weighted.items()},
                "titles": [left.filename, right.filename],
            },
        )

    def _entity_overlap(self, left_entities: Dict, right_entities: Dict) -> float:
        left_values = {str(v).lower() for values in left_entities.values() for v in (values or [])}
        right_values = {str(v).lower() for values in right_entities.values() for v in (values or [])}
        if not left_values and not right_values:
            return 0.0
        return len(left_values & right_values) / max(len(left_values | right_values), 1)

    def _semantic_similarity(self, left_doc_id: str, right_doc_id: str) -> float:
        if not embedding_service.enabled:
            return 0.0
        similar = embedding_service.find_similar_documents(document_id=left_doc_id, limit=30)
        for item in similar:
            if item["document_id"] == right_doc_id:
                return float(item["score"])
        return 0.0

    def _persist_candidates(self, db: Session, candidates: List[RelationshipCandidate]) -> Dict[str, int]:
        created = 0
        updated = 0
        duplicates_skipped = 0

        for candidate in candidates:
            existing = (
                db.query(DocumentRelationship)
                .filter(
                    DocumentRelationship.source_doc_id == candidate.source_doc_id,
                    DocumentRelationship.target_doc_id == candidate.target_doc_id,
                    DocumentRelationship.relationship_type == candidate.relationship_type,
                )
                .first()
            )
            if existing:
                duplicates_skipped += 1
                if (existing.confidence or 0.0) < candidate.confidence:
                    existing.confidence = candidate.confidence
                    existing.relationship_metadata = candidate.metadata
                    db.add(existing)
                    updated += 1
                continue

            db.add(
                DocumentRelationship(
                    source_doc_id=candidate.source_doc_id,
                    target_doc_id=candidate.target_doc_id,
                    relationship_type=candidate.relationship_type,
                    confidence=candidate.confidence,
                    relationship_metadata=candidate.metadata,
                )
            )
            created += 1

            review_type = self._to_review_type(candidate.relationship_type)
            if review_type:
                relationship_review_service.create_or_refresh_pending(
                    db,
                    source_document_id=candidate.source_doc_id,
                    target_document_id=candidate.target_doc_id,
                    relationship_type=review_type,
                    confidence=candidate.confidence,
                    reason_codes_json=["model_detection"],
                    metadata_json=candidate.metadata,
                )

        db.commit()
        logger.info(
            "Relationship candidate persistence finished: candidates=%s created=%s updated=%s duplicates_skipped=%s",
            len(candidates),
            created,
            updated,
            duplicates_skipped,
        )
        return {"created": created, "updated": updated}

    def _to_review_type(self, relationship_type: str) -> str | None:
        return {
            "duplicates": "duplicate",
            "similar_to": "similar",
            "related_to": "related",
            "follows_up": "related",
        }.get(relationship_type)


relationship_detection_service = RelationshipDetectionService()
