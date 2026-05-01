from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from itertools import combinations
import logging
import re
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
from app.services.prompt_templates import get_active_prompt_content
from app.services.relationship_review import relationship_review_service

logger = logging.getLogger(__name__)


@dataclass
class RelationshipCandidate:
    source_doc_id: UUID
    target_doc_id: UUID
    relationship_type: str
    confidence: float
    metadata: Dict


DEFAULT_RELATIONSHIP_PROMPT = """follow up
follow-up
update
next steps
status update
phase 2"""

STOPWORDS = {"a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "if", "in", "into", "is", "it", "no", "not", "of", "on", "or", "s", "such", "t", "that", "the", "their", "then", "there", "these", "they", "this", "to", "was", "will", "with", "you", "your"}


class RelationshipDetectionService:
    """Deterministic relationship detection with optional semantic boost."""

    def _build_explanation(self, *, confidence: float, signals: list[str], reason: str) -> Dict[str, Any]:
        clean_confidence = round(max(0.0, min(1.0, float(confidence))), 5)
        clean_signals = [s for s in signals if isinstance(s, str) and s.strip()]
        clean_reason = reason.strip() if isinstance(reason, str) and reason.strip() else "relationship detected"
        return {"confidence": clean_confidence, "signals": clean_signals, "reason": clean_reason}

    def detect_for_document(self, db: Session, document_id: UUID, limit: int = 50) -> Dict[str, int]:
        logger.info("Relationship detection started doc_id=%s", document_id)
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            logger.warning("Relationship detection skipped; source document missing doc_id=%s", document_id)
            return {"created": 0, "updated": 0, "scanned": 0}

        candidates = (
            db.query(Document)
            .filter(
                Document.id != document_id,
                Document.is_archived.is_(False),
                Document.processing_status == "completed",
                Document.user_id == doc.user_id,
            )
            .order_by(Document.upload_date.desc())
            .limit(limit)
            .all()
        )

        logger.info("Relationship detection compare-docs count=%d source_doc_id=%s", len(candidates), document_id)
        logger.info("Relationship detection source-intelligence entity_keys=%s", sorted((doc.entities or {}).keys()))
        matches = [self._score_pair(doc, other, db=db, log_prefix="detect_for_document") for other in candidates]
        detected = [m for m in matches if m is not None]
        logger.info("Relationship candidates pre-threshold count=%d doc_id=%s", len(matches), document_id)
        logger.info("Relationship candidates found=%d doc_id=%s", len(detected), document_id)
        persisted = self._persist_candidates(db, detected)
        persisted["scanned"] = len(candidates)
        return persisted

    def backfill_relationships(self, db: Session, limit: Optional[int] = None) -> Dict[str, int]:
        query = db.query(Document).filter(Document.is_archived.is_(False), Document.processing_status == "completed").order_by(Document.upload_date.desc())
        docs = query.limit(limit).all() if limit else query.all()

        candidates: List[RelationshipCandidate] = []
        for left, right in combinations(docs, 2):
            if left.user_id != right.user_id:
                logger.debug("Relationship skipped permission/user mismatch left=%s right=%s", left.id, right.id)
                continue
            result = self._score_pair(left, right, db=db, log_prefix="backfill")
            if result:
                candidates.append(result)

        persisted = self._persist_candidates(db, candidates)
        persisted["scanned"] = len(docs)
        return persisted

    def _score_pair(self, left: Document, right: Document, db: Session | None = None, log_prefix: str = "") -> Optional[RelationshipCandidate]:
        if left.id == right.id:
            logger.debug("Relationship skipped same doc left=%s right=%s", left.id, right.id)
            return None
        if left.is_archived or right.is_archived:
            logger.debug("Relationship skipped archived doc left=%s right=%s", left.id, right.id)
            return None
        if getattr(left, "user_id", None) != getattr(right, "user_id", None):
            logger.debug("Relationship skipped permission/user mismatch left=%s right=%s", left.id, right.id)
            return None
        if getattr(right, "processing_status", None) != "completed":
            logger.debug("Relationship skipped insufficient docs status left=%s right=%s", left.id, right.id)
            return None

        left_tags = set((left.ai_tags or []) + (left.user_tags or []))
        right_tags = set((right.ai_tags or []) + (right.user_tags or []))

        tag_overlap = len(left_tags & right_tags) / max(len(left_tags | right_tags), 1)
        entity_overlap = self._entity_overlap(left.entities or {}, right.entities or {})
        category_overlap = 1.0 if (left.user_category_id and left.user_category_id == right.user_category_id) or (left.ai_category_id and left.ai_category_id == right.ai_category_id) else 0.0
        timeline_overlap = self._timeline_overlap(left, right)
        runtime_prompt = get_active_prompt_content(db, "relationship_detection", DEFAULT_RELATIONSHIP_PROMPT) if db is not None else DEFAULT_RELATIONSHIP_PROMPT
        follow_up_signal = self._follow_up_signal(left, right, runtime_prompt)
        keyword_overlap = self._keyword_overlap(left, right)
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
            "tag_overlap": tag_overlap * 0.12,
            "entity_overlap": entity_overlap * 0.12,
            "category_overlap": category_overlap * 0.14,
            "timeline_overlap": timeline_overlap * 0.14,
            "keyword_overlap": keyword_overlap * 0.12,
            "follow_up_signal": follow_up_signal * 0.08,
            "date_adjacency": date_adjacent * 0.08,
            "semantic_similarity": semantic * 0.1,
        }
        score = sum(weighted.values())

        relationship_type = "related_to"
        if score >= 0.92 or (title_similarity > 0.9 and text_similarity > 0.9):
            relationship_type = "duplicates"
        elif follow_up_signal >= 0.9 or (date_adjacent >= 1.0 and (entity_overlap >= 0.2 or timeline_overlap >= 0.5)):
            relationship_type = "follows_up"
        elif semantic > 0.72 or keyword_overlap > 0.35 or score > 0.6:
            relationship_type = "similar_to"

        if not (left.entities or right.entities or (left.summary or left.filename) and (right.summary or right.filename)):
            logger.debug("Relationship skipped missing entities and text left=%s right=%s", left.id, right.id)
            return None

        if score < 0.33:
            logger.debug(
                "Relationship skipped low score left=%s right=%s score=%.5f signals=%s",
                left.id,
                right.id,
                score,
                {k: round(v, 5) for k, v in weighted.items()},
            )
            return None

        source_id, target_id = (left.id, right.id) if str(left.id) < str(right.id) else (right.id, left.id)
        normalized_confidence = round(min(score, 1.0), 5)
        return RelationshipCandidate(
            source_doc_id=source_id,
            target_doc_id=target_id,
            relationship_type=relationship_type,
            confidence=normalized_confidence,
            metadata={
                "signals": {k: round(v, 5) for k, v in weighted.items()},
                "titles": [left.filename, right.filename],
                "explanation": self._build_ai_explanation(weighted=weighted, relationship_type=relationship_type, confidence=normalized_confidence),
            },
        )

    def _build_ai_explanation(self, *, weighted: Dict[str, float], relationship_type: str, confidence: float) -> Dict[str, Any]:
        signals: list[str] = ["ai_detected"]
        if weighted.get("keyword_overlap", 0.0) > 0.03:
            signals.append("shared_terms")
        if weighted.get("timeline_overlap", 0.0) > 0.0 or weighted.get("date_adjacency", 0.0) > 0.0:
            signals.append("timeline_proximity")
        explanation = f"AI detected a {relationship_type.replace('_', ' ')} relationship from combined similarity signals."
        return self._build_explanation(confidence=confidence, signals=signals, reason=explanation)

    def _timeline_overlap(self, left: Document, right: Document) -> float:
        left_dates = self._extract_dates(left)
        right_dates = self._extract_dates(right)
        if not left_dates and not right_dates:
            return 0.0
        overlap = left_dates & right_dates
        return len(overlap) / max(len(left_dates | right_dates), 1)

    def _extract_dates(self, doc: Document) -> set[str]:
        values: set[str] = set()
        for source in [getattr(doc, "entities", {}) or {}, getattr(doc, "extracted_metadata", {}) or {}]:
            for key, v in source.items():
                if "date" in str(key).lower():
                    vals = v if isinstance(v, list) else [v]
                    for item in vals:
                        s = str(item)[:10]
                        if re.match(r"\d{4}-\d{2}-\d{2}", s):
                            values.add(s)
        for match in re.findall(r"\b\d{4}-\d{2}-\d{2}\b", (getattr(doc, "summary", "") or "") + " " + (getattr(doc, "raw_text", "") or "")):
            values.add(match)
        return values

    def _keyword_overlap(self, left: Document, right: Document) -> float:
        l_tokens = self._tokenize_text(f"{left.filename or ''} {left.summary or ''}")
        r_tokens = self._tokenize_text(f"{right.filename or ''} {right.summary or ''}")
        if not l_tokens or not r_tokens:
            return 0.0
        return len(l_tokens & r_tokens) / max(min(len(l_tokens), len(r_tokens)), 1)

    def _tokenize_text(self, text: str) -> set[str]:
        toks = {t for t in re.findall(r"[a-z0-9]{3,}", (text or "").lower()) if t not in STOPWORDS}
        return toks

    def _follow_up_signal(self, left: Document, right: Document, prompt_text: str) -> float:
        blob = f"{left.filename or ''} {left.summary or ''} {right.filename or ''} {right.summary or ''}".lower()
        phrases = [line.strip().lower() for line in (prompt_text or "").splitlines() if line.strip()]
        return 1.0 if any(p in blob for p in phrases) else 0.0

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
            structural_existing = (
                db.query(DocumentRelationship)
                .filter(
                    DocumentRelationship.source_doc_id == candidate.source_doc_id,
                    DocumentRelationship.target_doc_id == candidate.target_doc_id,
                    DocumentRelationship.relationship_type.in_(("thread", "attachment")),
                )
                .first()
            )
            if structural_existing:
                logger.info(
                    "relationship_skip_structural_existing source=%s target=%s type=%s existing_type=%s",
                    candidate.source_doc_id,
                    candidate.target_doc_id,
                    candidate.relationship_type,
                    structural_existing.relationship_type,
                )
                continue
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
                logger.info(
                    "relationship_skip_duplicate source=%s target=%s type=%s",
                    candidate.source_doc_id,
                    candidate.target_doc_id,
                    candidate.relationship_type,
                )
                if (existing.confidence or 0.0) < candidate.confidence:
                    existing.confidence = candidate.confidence
                    existing.relationship_metadata = candidate.metadata
                    db.add(existing)
                    updated += 1
            else:
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
