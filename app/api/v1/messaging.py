from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_current_user_role, get_db
from app.models.admin_audit import AdminAuditEvent
from app.models.messaging import Notification, UserMessage, UserMessageThread
from app.models.user import User
from app.services.workspaces import workspace_service
from app.schemas.messaging import (
    AdminThreadPatchRequest,
    MessageCreateRequest,
    MessageReplyRequest,
    NotificationResponse,
    ThreadResponse,
)

router = APIRouter(tags=["messaging"])
admin_router = APIRouter(prefix="/admin", tags=["admin-messaging"])


def _require_admin(role: str = Depends(get_current_user_role)) -> str:
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return role


@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications(limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(limit).all()


@router.post("/notifications/{notification_id}/read")
def mark_read(notification_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    n.read_at = n.read_at or datetime.now(timezone.utc)
    db.commit()
    return {"ok": True}


@router.post("/notifications/read-all")
def mark_all_read(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.query(Notification).filter(Notification.user_id == current_user.id, Notification.read_at.is_(None)).update({"read_at": datetime.now(timezone.utc)})
    db.commit()
    return {"ok": True}


@router.get("/messages", response_model=list[ThreadResponse])
def list_threads(limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(UserMessageThread).filter(UserMessageThread.user_id == current_user.id).order_by(UserMessageThread.updated_at.desc()).limit(limit).all()


@router.post("/messages", response_model=ThreadResponse, status_code=201)
def create_thread(payload: MessageCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if payload.workspace_id:
        workspace_service.require_member(db, str(payload.workspace_id), current_user.id)
    thread = UserMessageThread(user_id=current_user.id, workspace_id=payload.workspace_id, category=payload.category, subject=payload.subject, status="open")
    db.add(thread)
    db.flush()
    db.add(UserMessage(thread_id=thread.id, sender_user_id=current_user.id, sender_type="user", body=payload.body))
    db.commit(); db.refresh(thread)
    return thread


@router.get("/messages/{thread_id}", response_model=ThreadResponse)
def get_thread(thread_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(UserMessageThread).options(selectinload(UserMessageThread.messages)).filter(UserMessageThread.id == thread_id, UserMessageThread.user_id == current_user.id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Thread not found")
    return t


@router.post("/messages/{thread_id}/reply", response_model=ThreadResponse)
def user_reply(thread_id: UUID, payload: MessageReplyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(UserMessageThread).filter(UserMessageThread.id == thread_id, UserMessageThread.user_id == current_user.id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Thread not found")
    db.add(UserMessage(thread_id=t.id, sender_user_id=current_user.id, sender_type="user", body=payload.body))
    db.commit()
    return get_thread(thread_id, db, current_user)


@admin_router.get("/messages", response_model=list[ThreadResponse])
def admin_list_messages(status: str | None = Query(default=None), category: str | None = Query(default=None), limit: int = Query(default=100, ge=1, le=200), _: str = Depends(_require_admin), db: Session = Depends(get_db)):
    q = db.query(UserMessageThread)
    if status: q = q.filter(UserMessageThread.status == status)
    if category: q = q.filter(UserMessageThread.category == category)
    return q.order_by(UserMessageThread.updated_at.desc()).limit(limit).all()


@admin_router.get("/messages/{thread_id}", response_model=ThreadResponse)
def admin_get_message(thread_id: UUID, _: str = Depends(_require_admin), db: Session = Depends(get_db)):
    t = db.query(UserMessageThread).options(selectinload(UserMessageThread.messages)).filter(UserMessageThread.id == thread_id).first()
    if not t: raise HTTPException(status_code=404, detail="Thread not found")
    return t


@admin_router.post("/messages/{thread_id}/reply", response_model=ThreadResponse)
def admin_reply(thread_id: UUID, payload: MessageReplyRequest, _: str = Depends(_require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(UserMessageThread).filter(UserMessageThread.id == thread_id).first()
    if not t: raise HTTPException(status_code=404, detail="Thread not found")
    db.add(UserMessage(thread_id=t.id, sender_user_id=current_user.id, sender_type="admin", body=payload.body))
    db.add(Notification(user_id=t.user_id, type="admin_reply", title=f"Reply: {t.subject}", body=payload.body, link_url=f"/messages/{t.id}", metadata_json={"thread_id": str(t.id)}))
    db.add(AdminAuditEvent(actor_id=current_user.id, entity_type="user_message_thread", entity_id=str(t.id), action="admin_message_reply", details={"status": t.status}))
    db.commit()
    return admin_get_message(thread_id, "admin", db)


@admin_router.patch("/messages/{thread_id}", response_model=ThreadResponse)
def admin_patch_thread(thread_id: UUID, payload: AdminThreadPatchRequest, _: str = Depends(_require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(UserMessageThread).filter(UserMessageThread.id == thread_id).first()
    if not t: raise HTTPException(status_code=404, detail="Thread not found")
    t.status = payload.status
    db.add(AdminAuditEvent(actor_id=current_user.id, entity_type="user_message_thread", entity_id=str(t.id), action="admin_message_status_updated", details={"status": payload.status}))
    db.commit()
    return admin_get_message(thread_id, "admin", db)
