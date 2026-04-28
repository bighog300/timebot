from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.intelligence import DocumentActionItem


class ActionItemsService:
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
                item.dismissed_at = datetime.now(timezone.utc)
                db.add(item)

        db.commit()

    def update_item(self, db: Session, item: DocumentActionItem, *, content: str | None, metadata: dict | None) -> DocumentActionItem:
        if content is not None:
            item.content = content
        if metadata is not None:
            item.action_metadata = metadata
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def complete_item(self, db: Session, item: DocumentActionItem) -> DocumentActionItem:
        item.state = "completed"
        item.completed_at = datetime.now(timezone.utc)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def dismiss_item(self, db: Session, item: DocumentActionItem) -> DocumentActionItem:
        item.state = "dismissed"
        item.dismissed_at = datetime.now(timezone.utc)
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


action_items_service = ActionItemsService()
