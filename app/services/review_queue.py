from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.intelligence import DocumentReviewItem, ReviewAuditEvent
from app.services.review_audit import review_audit_service


class ReviewQueueService:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _priority_from_payload(payload: dict | None) -> str:
        if not isinstance(payload, dict):
            return "unknown"
        priority = payload.get("priority")
        if isinstance(priority, str) and priority:
            return priority
        return "unknown"

    @staticmethod
    def _to_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def list_items(self, db: Session, user_id: UUID, status: str = "open") -> list[DocumentReviewItem]:
        from app.models.document import Document

        return (
            db.query(DocumentReviewItem)
            .join(Document, Document.id == DocumentReviewItem.document_id)
            .filter(Document.user_id == user_id, DocumentReviewItem.status == status)
            .order_by(DocumentReviewItem.created_at.asc())
            .all()
        )

    def get_metrics(
        self,
        db: Session,
        *,
        user_id: UUID,
        now: datetime | None = None,
        recent_window_hours: int = 24,
        oldest_limit: int = 5,
    ) -> dict:
        from app.models.document import Document

        now = now or self._now()
        items = (
            db.query(DocumentReviewItem)
            .join(Document, Document.id == DocumentReviewItem.document_id)
            .filter(Document.user_id == user_id)
            .all()
        )

        open_items = [item for item in items if item.status == "open"]
        resolved_items = [item for item in items if item.status == "resolved"]
        dismissed_items = [item for item in items if item.status == "dismissed"]
        recent_threshold = now.timestamp() - (recent_window_hours * 3600)

        open_by_type: dict[str, int] = {}
        open_by_priority: dict[str, int] = {}
        total_open_age_hours = 0.0
        oldest_open_items: list[dict] = []
        recently_resolved_count = 0

        for item in open_items:
            open_by_type[item.review_type] = open_by_type.get(item.review_type, 0) + 1
            priority = self._priority_from_payload(item.payload)
            open_by_priority[priority] = open_by_priority.get(priority, 0) + 1

            created_at = self._to_utc(item.created_at)
            age_hours = max((now - created_at).total_seconds(), 0) / 3600 if created_at else 0
            total_open_age_hours += age_hours
            oldest_open_items.append(
                {
                    "id": item.id,
                    "document_id": item.document_id,
                    "review_type": item.review_type,
                    "priority": priority,
                    "age_hours": round(age_hours, 2),
                    "created_at": created_at,
                }
            )

        for item in resolved_items:
            resolved_at = self._to_utc(item.resolved_at)
            if resolved_at and resolved_at.timestamp() >= recent_threshold:
                recently_resolved_count += 1

        oldest_open_items.sort(key=lambda item: (item["created_at"], str(item["id"])))

        return {
            "open_review_count": len(open_items),
            "resolved_review_count": len(resolved_items),
            "dismissed_review_count": len(dismissed_items),
            "open_by_type": dict(sorted(open_by_type.items())),
            "open_by_priority": dict(sorted(open_by_priority.items())),
            "average_age_hours": round(total_open_age_hours / len(open_items), 2) if open_items else 0.0,
            "oldest_open_items": oldest_open_items[:oldest_limit],
            "recently_resolved_count": recently_resolved_count,
            "low_confidence_category_count": open_by_type.get("low_confidence", 0),
            "uncategorized_count": open_by_type.get("uncategorized", 0),
        }

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
            item.updated_at = self._now()
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
        item.resolved_at = self._now()
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
        item.dismissed_at = self._now()
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
            item.resolved_at = self._now()
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

        now = self._now()
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

        now = self._now()
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
