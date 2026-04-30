from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.models.intelligence import DocumentIntelligence
from app.services.action_items import action_items_service
from app.services.ai_analyzer import ai_analyzer
from app.services.categorizer import categorizer
from app.services.review_audit import review_audit_service
from app.services.review_queue import review_queue_service


class DocumentIntelligenceService:
    def get_for_document(self, db: Session, document: Document) -> DocumentIntelligence | None:
        return db.query(DocumentIntelligence).filter(DocumentIntelligence.document_id == document.id).first()

    def create_from_analysis(self, db: Session, document: Document, analysis: dict) -> DocumentIntelligence:
        intelligence = self._upsert_from_analysis(db, document, analysis)
        self._refresh_review_items(db, document, intelligence)
        action_items_service.refresh_from_analysis(db, document.id, analysis.get("action_items", []))
        return intelligence

    def regenerate(self, db: Session, document: Document) -> DocumentIntelligence:
        if not document.raw_text:
            raise ValueError("Document has no extracted text")

        from app.models.category import Category

        categories = db.query(Category).all()
        analysis = ai_analyzer.analyze_document(
            text=document.raw_text,
            filename=document.filename,
            file_type=document.file_type,
            existing_categories=[c.name for c in categories],
        )
        if not analysis:
            raise RuntimeError("AI analysis failed")

        return self.create_from_analysis(db, document, analysis)

    def _upsert_from_analysis(self, db: Session, document: Document, analysis: dict) -> DocumentIntelligence:
        confidence_score = ai_analyzer.compute_confidence(analysis)
        confidence_label = "high" if confidence_score >= 0.8 else "medium" if confidence_score >= 0.5 else "low"

        intelligence = self.get_for_document(db, document)
        if not intelligence:
            intelligence = DocumentIntelligence(document_id=document.id)
            db.add(intelligence)

        intelligence.summary = analysis.get("summary")
        intelligence.key_points = analysis.get("key_points", [])
        intelligence.suggested_tags = analysis.get("tags", [])
        intelligence.entities = analysis.get("entities", {})

        timeline_events = analysis.get("timeline_events", []) or []
        if isinstance(timeline_events, list):
            intelligence.entities = dict(intelligence.entities or {})
            intelligence.entities["timeline_events"] = timeline_events
        intelligence.confidence = confidence_label
        intelligence.model_name = settings.OPENAI_MODEL
        intelligence.model_version = analysis.get("model_version")
        intelligence.model_metadata = analysis.get("model_metadata", {})
        intelligence.generated_at = datetime.now(timezone.utc)

        categorizer.apply_category(db, document, analysis)
        intelligence.suggested_category_id = document.ai_category_id

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
        return intelligence

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
