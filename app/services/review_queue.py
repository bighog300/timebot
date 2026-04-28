from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.intelligence import DocumentReviewItem, ReviewAuditEvent
from app.services.review_audit import review_audit_service


class ReviewQueueService:
    def list_items(self, db: Session, user_id: UUID, status: str = "open") -> list[DocumentReviewItem]:
        from app.models.document import Document

        return (
            db.query(DocumentReviewItem)
            .join(Document, Document.id == DocumentReviewItem.document_id)
            .filter(Document.user_id == user_id, DocumentReviewItem.status == status)
            .order_by(DocumentReviewItem.created_at.asc())
            .all()
        )

    def get_item(self, db: Session, item_id: UUID, user_id: UUID) -> DocumentReviewItem | None:
        from app.models.document import Document

        return (
            db.query(DocumentReviewItem)
            .join(Document, Document.id == DocumentReviewItem.document_id)
            .filter(Document.user_id == user_id, DocumentReviewItem.id == item_id)
            .first()
        )

    def create_or_refresh_open_item(
        self,
        db: Session,
        *,
        document_id: UUID,
        review_type: str,
        reason: str,
        payload: dict | None = None,
    ) -> DocumentReviewItem:
        item = (
            db.query(DocumentReviewItem)
            .filter(
                DocumentReviewItem.document_id == document_id,
                DocumentReviewItem.review_type == review_type,
                DocumentReviewItem.status == "open",
            )
            .first()
        )
        if item:
            item.reason = reason
            item.payload = payload or {}
            item.updated_at = datetime.now(timezone.utc)
        else:
            item = DocumentReviewItem(
                document_id=document_id,
                review_type=review_type,
                reason=reason,
                payload=payload or {},
                status="open",
            )
            db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def resolve_item(
        self,
        db: Session,
        item: DocumentReviewItem,
        note: str | None = None,
        actor_id: UUID | None = None,
    ) -> DocumentReviewItem:
        before = {"status": item.status, "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None}
        item.status = "resolved"
        item.resolved_at = datetime.now(timezone.utc)
        payload = dict(item.payload or {})
        if note:
            payload["resolution_note"] = note
        item.payload = payload
        db.add(item)
        db.commit()
        db.refresh(item)
        review_audit_service.create_event(
            db,
            document_id=item.document_id,
            event_type="review_item_resolved",
            actor_id=actor_id,
            note=note,
            before_json=before,
            after_json={"status": item.status, "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None},
        )
        return item

    def dismiss_item(
        self,
        db: Session,
        item: DocumentReviewItem,
        note: str | None = None,
        actor_id: UUID | None = None,
    ) -> DocumentReviewItem:
        before = {"status": item.status, "dismissed_at": item.dismissed_at.isoformat() if item.dismissed_at else None}
        item.status = "dismissed"
        item.dismissed_at = datetime.now(timezone.utc)
        payload = dict(item.payload or {})
        if note:
            payload["dismiss_note"] = note
        item.payload = payload
        db.add(item)
        db.commit()
        db.refresh(item)
        review_audit_service.create_event(
            db,
            document_id=item.document_id,
            event_type="review_item_dismissed",
            actor_id=actor_id,
            note=note,
            before_json=before,
            after_json={"status": item.status, "dismissed_at": item.dismissed_at.isoformat() if item.dismissed_at else None},
        )
        return item

    def resolve_document_items(self, db: Session, document_id: UUID, review_type: str) -> None:
        items = (
            db.query(DocumentReviewItem)
            .filter(
                DocumentReviewItem.document_id == document_id,
                DocumentReviewItem.review_type == review_type,
                DocumentReviewItem.status == "open",
            )
            .all()
        )
        for item in items:
            item.status = "resolved"
            item.resolved_at = datetime.now(timezone.utc)
            db.add(item)
        db.commit()

    def bulk_resolve_items(
        self,
        db: Session,
        *,
        user_id: UUID,
        item_ids: list[UUID],
        note: str | None = None,
        actor_id: UUID | None = None,
    ) -> tuple[list[DocumentReviewItem], int]:
        from app.models.document import Document

        unique_ids: list[UUID] = list(dict.fromkeys(item_ids))
        if not unique_ids:
            return [], 0

        now = datetime.now(timezone.utc)
        items = (
            db.query(DocumentReviewItem)
            .join(Document, Document.id == DocumentReviewItem.document_id)
            .filter(Document.user_id == user_id, DocumentReviewItem.id.in_(unique_ids))
            .all()
        )
        items_by_id = {str(item.id): item for item in items}
        ordered_items = [items_by_id[str(item_id)] for item_id in unique_ids if str(item_id) in items_by_id]
        skipped_count = len(item_ids) - len(ordered_items)

        for item in ordered_items:
            before = {
                "status": item.status,
                "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
            }
            item.status = "resolved"
            item.resolved_at = now
            payload = dict(item.payload or {})
            if note:
                payload["resolution_note"] = note
            item.payload = payload
            db.add(item)
            db.add(
                ReviewAuditEvent(
                    document_id=item.document_id,
                    actor_id=actor_id,
                    event_type="review_item_resolved",
                    note=note,
                    before_json=before,
                    after_json={"status": item.status, "resolved_at": item.resolved_at.isoformat()},
                )
            )

        db.commit()
        for item in ordered_items:
            db.refresh(item)
        return ordered_items, skipped_count

    def bulk_dismiss_items(
        self,
        db: Session,
        *,
        user_id: UUID,
        item_ids: list[UUID],
        note: str | None = None,
        actor_id: UUID | None = None,
    ) -> tuple[list[DocumentReviewItem], int]:
        from app.models.document import Document

        unique_ids: list[UUID] = list(dict.fromkeys(item_ids))
        if not unique_ids:
            return [], 0

        now = datetime.now(timezone.utc)
        items = (
            db.query(DocumentReviewItem)
            .join(Document, Document.id == DocumentReviewItem.document_id)
            .filter(Document.user_id == user_id, DocumentReviewItem.id.in_(unique_ids))
            .all()
        )
        items_by_id = {str(item.id): item for item in items}
        ordered_items = [items_by_id[str(item_id)] for item_id in unique_ids if str(item_id) in items_by_id]
        skipped_count = len(item_ids) - len(ordered_items)

        for item in ordered_items:
            before = {
                "status": item.status,
                "dismissed_at": item.dismissed_at.isoformat() if item.dismissed_at else None,
            }
            item.status = "dismissed"
            item.dismissed_at = now
            payload = dict(item.payload or {})
            if note:
                payload["dismiss_note"] = note
            item.payload = payload
            db.add(item)
            db.add(
                ReviewAuditEvent(
                    document_id=item.document_id,
                    actor_id=actor_id,
                    event_type="review_item_dismissed",
                    note=note,
                    before_json=before,
                    after_json={"status": item.status, "dismissed_at": item.dismissed_at.isoformat()},
                )
            )

        db.commit()
        for item in ordered_items:
            db.refresh(item)
        return ordered_items, skipped_count


review_queue_service = ReviewQueueService()
