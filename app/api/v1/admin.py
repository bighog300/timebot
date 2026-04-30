from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_current_user_role
from app.models.admin_audit import AdminAuditEvent
from app.models.document import Document
from app.models.intelligence import DocumentActionItem, DocumentRelationshipReview, DocumentReviewItem
from app.models.user import User
from app.schemas.admin import (
    AdminAuditEventResponse,
    AdminAuditPageResponse,
    AdminMetricsResponse,
    AdminRoleUpdateRequest,
    AdminUserResponse,
    AdminUsersPageResponse,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(role: str = Depends(get_current_user_role)) -> str:
    if role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return role


@router.get("/users", response_model=AdminUsersPageResponse)
def list_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(User).order_by(User.created_at.desc())
    return AdminUsersPageResponse(items=q.offset(offset).limit(limit).all(), total_count=q.count(), limit=limit, offset=offset)


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
def update_user_role(
    user_id: str,
    payload: AdminRoleUpdateRequest,
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    next_role = payload.role.lower()
    if next_role not in {"viewer", "editor", "admin"}:
        raise HTTPException(status_code=422, detail="Invalid role")

    if user.role == "admin" and next_role != "admin":
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot demote the last admin")

    prev = user.role
    user.role = next_role
    db.add(
        AdminAuditEvent(
            actor_id=current_user.id,
            entity_type="user",
            entity_id=str(user.id),
            action="role_updated",
            details={"previous_role": prev, "new_role": next_role, "target_email": user.email},
        )
    )
    db.commit()
    db.refresh(user)
    return user


@router.get("/audit", response_model=AdminAuditPageResponse)
def list_admin_audit(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(AdminAuditEvent).order_by(AdminAuditEvent.created_at.desc())
    items = q.offset(offset).limit(limit).all()
    mapped = [
        AdminAuditEventResponse(
            id=i.id,
            actor_id=i.actor_id,
            actor_email=i.actor.email if i.actor else None,
            entity_type=i.entity_type,
            entity_id=i.entity_id,
            action=i.action,
            details=i.details or {},
            created_at=i.created_at,
        )
        for i in items
    ]
    return AdminAuditPageResponse(items=mapped, total_count=q.count(), limit=limit, offset=offset)


@router.get("/metrics", response_model=AdminMetricsResponse)
def admin_metrics(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    return AdminMetricsResponse(
        total_users=db.query(func.count(User.id)).scalar() or 0,
        total_documents=db.query(func.count(Document.id)).scalar() or 0,
        documents_processed=db.query(func.count(Document.id)).filter(Document.processing_status == "completed").scalar() or 0,
        documents_failed=db.query(func.count(Document.id)).filter(Document.processing_status == "failed").scalar() or 0,
        pending_review_items=db.query(func.count(DocumentReviewItem.id)).filter(DocumentReviewItem.status == "open").scalar() or 0,
        open_action_items=db.query(func.count(DocumentActionItem.id)).filter(DocumentActionItem.state == "open").scalar() or 0,
        pending_relationship_reviews=db.query(func.count(DocumentRelationshipReview.id)).filter(DocumentRelationshipReview.status == "pending").scalar() or 0,
    )
