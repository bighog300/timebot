from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentUpdate


def create_document(db: Session, obj_in: DocumentCreate, user: User, workspace_id=None, **kwargs) -> Document:
    db_obj = Document(**obj_in.model_dump(), user_id=user.id, workspace_id=workspace_id, **kwargs)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def _workspace_filter(q, workspace_id, user_id):
    if workspace_id is not None:
        return q.filter(or_(Document.workspace_id == workspace_id, (Document.workspace_id.is_(None) & (Document.user_id == user_id))))
    return q.filter(Document.user_id == user_id)


def get_document(db: Session, id: UUID, user: User, workspace_id=None) -> Optional[Document]:
    q = db.query(Document).filter(Document.id == id)
    q = _workspace_filter(q, workspace_id, user.id)
    return q.first()


def get_documents(db: Session, user: User, workspace_id=None, skip: int = 0, limit: int = 100, include_archived: bool = False) -> List[Document]:
    q = _workspace_filter(db.query(Document), workspace_id, user.id)
    if not include_archived:
        q = q.filter(Document.is_archived == False)
    return q.order_by(desc(Document.upload_date)).offset(skip).limit(limit).all()


def update_document(db: Session, db_obj: Document, obj_in: DocumentUpdate) -> Document:
    for field, value in obj_in.model_dump(exclude_unset=True).items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_document_fields(db: Session, db_obj: Document, **kwargs) -> Document:
    for field, value in kwargs.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_document(db: Session, id: UUID, user: User, workspace_id=None) -> Optional[Document]:
    q = _workspace_filter(db.query(Document).filter(Document.id == id), workspace_id, user.id)
    obj = q.first()
    if obj:
        db.delete(obj)
        db.commit()
    return obj


def search_documents(db: Session, user: User, workspace_id, query: str, skip: int = 0, limit: int = 20) -> List[Document]:
    q = db.query(Document).filter(Document.search_vector.op("@@")(func.plainto_tsquery("english", query)), Document.is_archived == False)
    q = _workspace_filter(q, workspace_id, user.id)
    return q.order_by(desc(Document.upload_date)).offset(skip).limit(limit).all()


def get_documents_by_category(db: Session, user: User, category_id: UUID, workspace_id=None, skip: int = 0, limit: int = 100) -> List[Document]:
    q = db.query(Document).filter(or_(Document.ai_category_id == category_id, Document.user_category_id == category_id), Document.is_archived == False)
    q = _workspace_filter(q, workspace_id, user.id)
    return q.order_by(desc(Document.upload_date)).offset(skip).limit(limit).all()


def count_documents(db: Session, user: User, workspace_id=None, include_archived: bool = False) -> int:
    q = _workspace_filter(db.query(Document), workspace_id, user.id)
    if not include_archived:
        q = q.filter(Document.is_archived == False)
    return q.count()


def get_review_queue(db: Session, user: User, workspace_id=None, status: str = "pending", skip: int = 0, limit: int = 50) -> List[Document]:
    q = db.query(Document).filter(Document.review_status == status, Document.is_archived == False)
    q = _workspace_filter(q, workspace_id, user.id)
    return q.order_by(Document.ai_confidence.asc().nullsfirst(), desc(Document.upload_date)).offset(skip).limit(limit).all()
