from uuid import UUID

from sqlalchemy.orm import Session

from app.models.intelligence import ReviewAuditEvent


class ReviewAuditService:
    def create_event(
        self,
        db: Session,
        *,
        document_id: UUID,
        event_type: str,
        actor_id: UUID | None = None,
        note: str | None = None,
        before_json: dict | None = None,
        after_json: dict | None = None,
    ) -> ReviewAuditEvent:
        event = ReviewAuditEvent(
            document_id=document_id,
            actor_id=actor_id,
            event_type=event_type,
            note=note,
            before_json=before_json or {},
            after_json=after_json or {},
        )
        db.add(event)
        db.flush()
        return event

    def list_events(
        self,
        db: Session,
        *,
        user_id: UUID,
        event_type: str | None = None,
        document_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ReviewAuditEvent]:
        from app.models.document import Document

        query = (
            db.query(ReviewAuditEvent)
            .join(Document, Document.id == ReviewAuditEvent.document_id)
            .filter(Document.user_id == user_id)
        )
        if event_type:
            query = query.filter(ReviewAuditEvent.event_type == event_type)
        if document_id:
            query = query.filter(ReviewAuditEvent.document_id == document_id)

        return query.order_by(ReviewAuditEvent.created_at.desc()).offset(skip).limit(limit).all()


review_audit_service = ReviewAuditService()
