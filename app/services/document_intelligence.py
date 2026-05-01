from datetime import datetime, timezone
import logging
import re
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.models.intelligence import DocumentIntelligence
from app.services.action_items import action_items_service
from app.services.ai_analyzer import AIAnalysisError, ai_analyzer
from app.services.categorizer import categorizer
from app.services.review_audit import review_audit_service
from app.services.review_queue import review_queue_service


class DocumentIntelligenceService:
    _TIMELINE_STOPWORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "is", "it", "of", "on", "or", "that", "the", "to", "was", "were", "with",
    }

    def get_for_document(self, db: Session, document: Document) -> DocumentIntelligence | None:
        return db.query(DocumentIntelligence).filter(DocumentIntelligence.document_id == document.id).first()

    def create_from_analysis(self, db: Session, document: Document, analysis: dict) -> DocumentIntelligence:
        intelligence = self._upsert_from_analysis(db, document, analysis)
        self._refresh_gmail_thread_summary(db, document)
        self._refresh_review_items(db, document, intelligence)
        action_items_service.refresh_from_analysis(db, document.id, analysis.get("action_items", []))
        return intelligence

    def regenerate(self, db: Session, document: Document) -> DocumentIntelligence:
        if not document.raw_text:
            raise ValueError("Document has no extracted text")

        from app.models.category import Category

        categories = db.query(Category).all()
        try:
            analysis = ai_analyzer.analyze_document(
                text=document.raw_text,
                filename=document.filename,
                file_type=document.file_type,
                existing_categories=[c.name for c in categories],
                db=db,
            )
        except AIAnalysisError as exc:
            raise RuntimeError(str(exc)) from exc

        return self.create_from_analysis(db, document, analysis)

    def _upsert_from_analysis(self, db: Session, document: Document, analysis: dict) -> DocumentIntelligence:
        logger = logging.getLogger(__name__)
        confidence_score = ai_analyzer.compute_confidence(analysis)
        confidence_label = "high" if confidence_score >= 0.8 else "medium" if confidence_score >= 0.5 else "low"

        intelligence = self.get_for_document(db, document)
        if not intelligence:
            intelligence = DocumentIntelligence(document_id=document.id)
            db.add(intelligence)

        incoming_summary = (analysis.get("summary") or "").strip()
        if incoming_summary:
            intelligence.summary = incoming_summary
        elif not intelligence.summary:
            intelligence.summary = ""
        timeline_events = analysis.get("timeline_events", []) or []
        intelligence.key_points = analysis.get("key_points", [])
        intelligence.suggested_tags = analysis.get("tags", [])
        analysis_entities = analysis.get("entities", {})
        preview_event = timeline_events[0] if timeline_events and isinstance(timeline_events[0], dict) else {}
        logger.info(
            "timeline_pre_persist document_id=%s count=%s first_title=%s first_date=%s first_start=%s first_end=%s",
            document.id,
            len(timeline_events) if isinstance(timeline_events, list) else 0,
            preview_event.get("title"),
            preview_event.get("date"),
            preview_event.get("start_date"),
            preview_event.get("end_date"),
        )
        if isinstance(timeline_events, list):
            timeline_events = self._deduplicate_timeline_events(db, document, timeline_events)
            intelligence.entities = dict(analysis_entities or {})
            intelligence.entities["timeline_events"] = timeline_events
        else:
            intelligence.entities = analysis_entities
        intelligence.confidence = confidence_label
        intelligence.model_name = settings.OPENAI_MODEL
        intelligence.model_version = analysis.get("model_version")
        intelligence.model_metadata = analysis.get("model_metadata", {})
        intelligence.generated_at = datetime.now(timezone.utc)

        categorizer.apply_category(db, document, analysis)
        intelligence.suggested_category_id = document.ai_category_id

        if intelligence.summary:
            document.summary = intelligence.summary
        document.key_points = intelligence.key_points
        document.entities = intelligence.entities
        document.ai_tags = intelligence.suggested_tags
        document.action_items = analysis.get("action_items", [])
        document.ai_confidence = confidence_score

        db.add(document)
        db.add(intelligence)
        db.commit()
        db.refresh(intelligence)
        persisted = (intelligence.entities or {}).get("timeline_events", []) if isinstance(intelligence.entities, dict) else []
        logger.info("timeline_post_persist document_id=%s persisted_count=%s", document.id, len(persisted) if isinstance(persisted, list) else 0)
        return intelligence

    def _refresh_gmail_thread_summary(self, db: Session, document: Document) -> None:
        if document.source != "gmail":
            return
        metadata = document.extracted_metadata if isinstance(document.extracted_metadata, dict) else {}
        thread_id = metadata.get("gmail_thread_id")
        if not thread_id:
            return

        candidate_docs = db.query(Document).filter(
            Document.user_id == document.user_id,
            Document.source == "gmail",
        ).all()
        thread_docs = [
            doc for doc in candidate_docs
            if isinstance(doc.extracted_metadata, dict)
            and str(doc.extracted_metadata.get("gmail_thread_id") or "") == str(thread_id)
        ]
        if len(thread_docs) < 2:
            return

        summary_parts: list[str] = []
        seen: set[str] = set()
        for thread_doc in thread_docs:
            text = ((thread_doc.summary or "").strip() or (thread_doc.raw_text or "").strip())
            if not text:
                continue
            snippet = re.sub(r"\s+", " ", text)[:280].strip()
            if not snippet:
                continue
            norm = snippet.lower()
            if norm in seen:
                continue
            seen.add(norm)
            summary_parts.append(snippet)
            if len(summary_parts) >= 4:
                break
        if len(summary_parts) < 2:
            return

        thread_summary = " | ".join(summary_parts)
        for thread_doc in thread_docs:
            doc_metadata = thread_doc.extracted_metadata if isinstance(thread_doc.extracted_metadata, dict) else {}
            if doc_metadata.get("thread_summary") == thread_summary:
                continue
            updated_metadata = dict(doc_metadata)
            updated_metadata["thread_summary"] = thread_summary
            thread_doc.extracted_metadata = updated_metadata
            db.add(thread_doc)
        db.commit()

    def _deduplicate_timeline_events(self, db: Session, document: Document, incoming_events: list[dict]) -> list[dict]:
        existing_norm = self._existing_timeline_event_signatures(db, document)
        kept: list[dict] = []
        for event in incoming_events:
            if not isinstance(event, dict):
                continue
            sig = self._timeline_event_signature(event)
            if sig and sig in existing_norm:
                continue
            if sig:
                existing_norm.add(sig)
            kept.append(event)
        return kept

    def _existing_timeline_event_signatures(self, db: Session, document: Document) -> set[str]:
        related_docs: list[Document] = [document]
        try:
            metadata = getattr(document, "extracted_metadata", {}) or {}
            thread_id = metadata.get("gmail_thread_id") if isinstance(metadata, dict) else None
            if thread_id:
                related_docs = db.query(Document).filter(
                    Document.user_id == document.user_id,
                    Document.source == "gmail",
                    Document.extracted_metadata["gmail_thread_id"].astext == str(thread_id),
                    Document.id != document.id,
                ).all()
                related_docs = [document, *related_docs]
        except Exception:
            related_docs = [document]

        signatures: set[str] = set()
        for doc in related_docs:
            entities = getattr(doc, "entities", {}) or {}
            events = entities.get("timeline_events", []) if isinstance(entities, dict) else []
            if not isinstance(events, list):
                continue
            for event in events:
                if isinstance(event, dict):
                    sig = self._timeline_event_signature(event)
                    if sig:
                        signatures.add(sig)
        return signatures

    def _timeline_event_signature(self, event: dict) -> str:
        text_bits = [
            str(event.get("title") or ""),
            str(event.get("description") or ""),
            str(event.get("date") or ""),
            str(event.get("start_date") or ""),
            str(event.get("end_date") or ""),
        ]
        normalized = self._normalize_event_text(" ".join(text_bits))
        return normalized.strip()

    def _normalize_event_text(self, text: str) -> str:
        lowered = (text or "").lower().strip()
        no_punct = re.sub(r"[^\w\s]", " ", lowered)
        squashed = re.sub(r"\s+", " ", no_punct).strip()
        words = [w for w in squashed.split(" ") if w and w not in self._TIMELINE_STOPWORDS]
        return " ".join(words)

    def update_intelligence(
        self,
        db: Session,
        intelligence: DocumentIntelligence,
        updates: dict,
        actor_id: UUID | None = None,
    ) -> DocumentIntelligence:
        before = {field: getattr(intelligence, field) for field in updates}
        for field, value in updates.items():
            setattr(intelligence, field, value)
        db.add(intelligence)
        review_audit_service.create_event(
            db,
            document_id=intelligence.document_id,
            event_type="intelligence_updated",
            actor_id=actor_id,
            before_json=before,
            after_json={field: getattr(intelligence, field) for field in updates},
        )
        db.commit()
        db.refresh(intelligence)
        return intelligence

    def approve_category(
        self,
        db: Session,
        document: Document,
        intelligence: DocumentIntelligence,
        actor_id: UUID | None = None,
    ) -> Document:
        if not intelligence.suggested_category_id:
            raise ValueError("No suggested category to approve")

        before = {"user_category_id": str(document.user_category_id) if document.user_category_id else None, "category_status": intelligence.category_status}
        document.user_category_id = intelligence.suggested_category_id
        intelligence.category_status = "approved"
        review_queue_service.resolve_document_items(db, document.id, "uncategorized")
        db.add(document)
        db.add(intelligence)
        review_audit_service.create_event(
            db,
            document_id=document.id,
            event_type="category_approved",
            actor_id=actor_id,
            before_json=before,
            after_json={"user_category_id": str(document.user_category_id), "category_status": intelligence.category_status},
        )
        db.commit()
        db.refresh(document)
        return document

    def override_category(
        self,
        db: Session,
        document: Document,
        intelligence: DocumentIntelligence,
        category_id: UUID,
        actor_id: UUID | None = None,
    ) -> Document:
        before = {"user_category_id": str(document.user_category_id) if document.user_category_id else None, "category_status": intelligence.category_status}
        document.user_category_id = category_id
        intelligence.category_status = "overridden"
        review_queue_service.resolve_document_items(db, document.id, "uncategorized")
        db.add(document)
        db.add(intelligence)
        review_audit_service.create_event(
            db,
            document_id=document.id,
            event_type="category_overridden",
            actor_id=actor_id,
            before_json=before,
            after_json={"user_category_id": str(document.user_category_id), "category_status": intelligence.category_status},
        )
        db.commit()
        db.refresh(document)
        return document

    def _refresh_review_items(self, db: Session, document: Document, intelligence: DocumentIntelligence) -> None:
        if intelligence.confidence == "low":
            review_queue_service.create_or_refresh_open_item(
                db,
                document_id=document.id,
                review_type="low_confidence",
                reason="Model confidence is low for this document.",
            )

        if not intelligence.suggested_category_id:
            review_queue_service.create_or_refresh_open_item(
                db,
                document_id=document.id,
                review_type="uncategorized",
                reason="No category suggestion available.",
            )

        if not intelligence.suggested_tags:
            review_queue_service.create_or_refresh_open_item(
                db,
                document_id=document.id,
                review_type="missing_tags",
                reason="No tag suggestions were generated.",
            )

        if document.processing_status == "failed":
            review_queue_service.create_or_refresh_open_item(
                db,
                document_id=document.id,
                review_type="processing_issues",
                reason=document.processing_error or "Document processing encountered an issue.",
            )


document_intelligence_service = DocumentIntelligenceService()
