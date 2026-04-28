from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.intelligence import DocumentActionItem, ReviewAuditEvent
from app.services.review_audit import review_audit_service


class ActionItemsService:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _parse_due_date(action_metadata: dict | None) -> datetime | None:
        if not isinstance(action_metadata, dict):
            return None
        raw_due_date = action_metadata.get("due_date")
        if not isinstance(raw_due_date, str) or not raw_due_date:
            return None
        normalized = raw_due_date.replace("Z", "+00:00")
        try:
            due_date = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if due_date.tzinfo is None:
            return due_date.replace(tzinfo=timezone.utc)
        return due_date.astimezone(timezone.utc)

    @staticmethod
    def _to_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def list_items(self, db: Session, user_id: UUID, state: str | None = None) -> list[DocumentActionItem]:
        from app.models.document import Document

        query = (
            db.query(DocumentActionItem)
            .join(Document, Document.id == DocumentActionItem.document_id)
            .filter(Document.user_id == user_id)
        )
        if state:
            query = query.filter(DocumentActionItem.state == state)
        return query.order_by(DocumentActionItem.created_at.desc()).all()

    def list_document_items(self, db: Session, user_id: UUID, document_id: UUID) -> list[DocumentActionItem]:
        from app.models.document import Document

        return (
            db.query(DocumentActionItem)
            .join(Document, Document.id == DocumentActionItem.document_id)
            .filter(Document.user_id == user_id, DocumentActionItem.document_id == document_id)
            .order_by(DocumentActionItem.created_at.desc())
            .all()
        )

    def get_metrics(
        self,
        db: Session,
        *,
        user_id: UUID,
        now: datetime | None = None,
        recent_window_hours: int = 24,
    ) -> dict:
        from app.models.document import Document

        now = now or self._now()
        items = (
            db.query(DocumentActionItem)
            .join(Document, Document.id == DocumentActionItem.document_id)
            .filter(Document.user_id == user_id)
            .all()
        )

        open_items = [item for item in items if item.state == "open"]
        completed_items = [item for item in items if item.state == "completed"]
        dismissed_items = [item for item in items if item.state == "dismissed"]
        total_count = len(items)
        recent_threshold = now.timestamp() - (recent_window_hours * 3600)

        parseable_open_due_dates = 0
        overdue_count = 0
        for item in open_items:
            due_date = self._parse_due_date(item.action_metadata)
            if due_date is None:
                continue
            parseable_open_due_dates += 1
            if due_date < now:
                overdue_count += 1

        recently_completed_count = 0
        for item in completed_items:
            completed_at = self._to_utc(item.completed_at)
            if completed_at and completed_at.timestamp() >= recent_threshold:
                recently_completed_count += 1

        return {
            "open_count": len(open_items),
            "completed_count": len(completed_items),
            "dismissed_count": len(dismissed_items),
            "overdue_count": overdue_count if parseable_open_due_dates > 0 else None,
            "completion_rate": round(len(completed_items) / total_count, 4) if total_count else 0.0,
            "recently_completed_count": recently_completed_count,
        }

    def get_item(self, db: Session, user_id: UUID, action_item_id: UUID) -> DocumentActionItem | None:
        from app.models.document import Document

        return (
            db.query(DocumentActionItem)
            .join(Document, Document.id == DocumentActionItem.document_id)
            .filter(Document.user_id == user_id, DocumentActionItem.id == action_item_id)
            .first()
        )

    def refresh_from_analysis(self, db: Session, document_id: UUID, action_items: list[str]) -> None:
        existing = {
            item.content: item
            for item in db.query(DocumentActionItem).filter(DocumentActionItem.document_id == document_id).all()
        }

        current_contents = set(action_items or [])
        for content in current_contents:
            if content in existing:
                item = existing[content]
                if item.state == "dismissed":
                    continue
                item.state = "open"
                db.add(item)
            else:
                db.add(DocumentActionItem(document_id=document_id, content=content, source="ai", state="open"))

        for content, item in existing.items():
            if content not in current_contents and item.source == "ai" and item.state == "open":
                item.state = "dismissed"
                item.dismissed_at = self._now()
                db.add(item)

        db.commit()

    def update_item(
        self,
        db: Session,
        item: DocumentActionItem,
        *,
        content: str | None,
        metadata: dict | None,
        actor_id: UUID | None = None,
        note: str | None = None,
    ) -> DocumentActionItem:
        before = {"content": item.content, "action_metadata": item.action_metadata}
        if content is not None:
            item.content = content
        if metadata is not None:
            item.action_metadata = metadata
        db.add(item)
        db.commit()
        db.refresh(item)
        review_audit_service.create_event(
            db,
            document_id=item.document_id,
            event_type="action_item_updated",
            actor_id=actor_id,
            note=note,
            before_json=before,
            after_json={"content": item.content, "action_metadata": item.action_metadata},
        )
        return item

    def complete_item(self, db: Session, item: DocumentActionItem, actor_id: UUID | None = None) -> DocumentActionItem:
        before = {"state": item.state, "completed_at": item.completed_at.isoformat() if item.completed_at else None}
        item.state = "completed"
        item.completed_at = self._now()
        db.add(item)
        db.commit()
        db.refresh(item)
        review_audit_service.create_event(
            db,
            document_id=item.document_id,
            event_type="action_item_completed",
            actor_id=actor_id,
            before_json=before,
            after_json={"state": item.state, "completed_at": item.completed_at.isoformat() if item.completed_at else None},
        )
        return item

    def dismiss_item(self, db: Session, item: DocumentActionItem, actor_id: UUID | None = None) -> DocumentActionItem:
        before = {"state": item.state, "dismissed_at": item.dismissed_at.isoformat() if item.dismissed_at else None}
        item.state = "dismissed"
        item.dismissed_at = self._now()
        db.add(item)
        db.commit()
        db.refresh(item)
        review_audit_service.create_event(
            db,
            document_id=item.document_id,
            event_type="action_item_dismissed",
            actor_id=actor_id,
            before_json=before,
            after_json={"state": item.state, "dismissed_at": item.dismissed_at.isoformat() if item.dismissed_at else None},
        )
        return item

    def bulk_complete_items(
        self,
        db: Session,
        *,
        user_id: UUID,
        item_ids: list[UUID],
        note: str | None = None,
        actor_id: UUID | None = None,
    ) -> tuple[list[DocumentActionItem], int]:
        from app.models.document import Document

        unique_ids: list[UUID] = list(dict.fromkeys(item_ids))
        if not unique_ids:
            return [], 0

        now = self._now()
        items = (
            db.query(DocumentActionItem)
            .join(Document, Document.id == DocumentActionItem.document_id)
            .filter(Document.user_id == user_id, DocumentActionItem.id.in_(unique_ids))
            .all()
        )
        items_by_id = {str(item.id): item for item in items}
        ordered_items = [items_by_id[str(item_id)] for item_id in unique_ids if str(item_id) in items_by_id]
        skipped_count = len(item_ids) - len(ordered_items)

        for item in ordered_items:
            before = {"state": item.state, "completed_at": item.completed_at.isoformat() if item.completed_at else None}
            item.state = "completed"
            item.completed_at = now
            db.add(item)
            db.add(
                ReviewAuditEvent(
                    document_id=item.document_id,
                    actor_id=actor_id,
                    event_type="action_item_completed",
                    note=note,
                    before_json=before,
                    after_json={"state": item.state, "completed_at": item.completed_at.isoformat()},
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
    ) -> tuple[list[DocumentActionItem], int]:
        from app.models.document import Document

        unique_ids: list[UUID] = list(dict.fromkeys(item_ids))
        if not unique_ids:
            return [], 0

        now = self._now()
        items = (
            db.query(DocumentActionItem)
            .join(Document, Document.id == DocumentActionItem.document_id)
            .filter(Document.user_id == user_id, DocumentActionItem.id.in_(unique_ids))
            .all()
        )
        items_by_id = {str(item.id): item for item in items}
        ordered_items = [items_by_id[str(item_id)] for item_id in unique_ids if str(item_id) in items_by_id]
        skipped_count = len(item_ids) - len(ordered_items)

        for item in ordered_items:
            before = {"state": item.state, "dismissed_at": item.dismissed_at.isoformat() if item.dismissed_at else None}
            item.state = "dismissed"
            item.dismissed_at = now
            db.add(item)
            db.add(
                ReviewAuditEvent(
                    document_id=item.document_id,
                    actor_id=actor_id,
                    event_type="action_item_dismissed",
                    note=note,
                    before_json=before,
                    after_json={"state": item.state, "dismissed_at": item.dismissed_at.isoformat()},
                )
            )

        db.commit()
        for item in ordered_items:
            db.refresh(item)
        return ordered_items, skipped_count


action_items_service = ActionItemsService()
