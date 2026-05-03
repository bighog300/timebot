import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.deps import get_active_workspace, get_current_user, get_db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceInvite, WorkspaceMember
from app.services.workspaces import workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

class WorkspaceCreate(BaseModel):
    name: str

class InviteCreate(BaseModel):
    email: EmailStr
    role: str = "member"

class AcceptInvite(BaseModel):
    token: str

class MemberRoleUpdate(BaseModel):
    role: str

@router.get("")
def list_workspaces(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    workspace_service.ensure_personal_workspace(db, current_user)
    return workspace_service.list_for_user(db, current_user.id)

@router.post("")
def create_workspace(payload: WorkspaceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ws = Workspace(name=payload.name.strip(), type="team", owner_user_id=current_user.id)
    db.add(ws); db.flush()
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=current_user.id, role="owner"))
    db.commit(); db.refresh(ws)
    return ws

@router.get("/{workspace_id}")
def get_workspace(workspace_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    workspace_service.require_member(db, workspace_id, current_user.id)
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws: raise HTTPException(status_code=404, detail="Workspace not found")
    return ws

@router.post("/{workspace_id}/invites")
def invite(workspace_id: str, payload: InviteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member = workspace_service.require_member(db, workspace_id, current_user.id)
    if member.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Only owner/admin may invite")
    invite, token = workspace_service.create_invite(db, workspace_id, payload.email, payload.role, current_user.id)
    return {"invite": invite, "token": token}

@router.post("/invites/{token}/accept")
def accept_workspace_invite(token: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    invite = db.query(WorkspaceInvite).filter(WorkspaceInvite.token_hash == token_hash).first()
    now = datetime.now(timezone.utc)
    if not invite or invite.accepted_at or invite.expires_at <= now:
        raise HTTPException(status_code=400, detail="Invalid invite")
    exists = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == invite.workspace_id, WorkspaceMember.user_id == current_user.id).first()
    if not exists:
        db.add(WorkspaceMember(workspace_id=invite.workspace_id, user_id=current_user.id, role=invite.role))
    invite.accepted_at = now
    db.commit()
    return {"accepted": True}

@router.patch("/{workspace_id}/members/{user_id}")
def patch_member(workspace_id: str, user_id: str, payload: MemberRoleUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    actor = workspace_service.require_member(db, workspace_id, current_user.id)
    if actor.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Only owner/admin may edit members")
    member = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.role = payload.role
    db.commit()
    return member

@router.delete("/{workspace_id}/members/{user_id}")
def remove_member(workspace_id: str, user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    actor = workspace_service.require_member(db, workspace_id, current_user.id)
    if actor.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Only owner/admin may remove members")
    member = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.role == "owner":
        raise HTTPException(status_code=400, detail="Owner cannot be removed")
    db.delete(member)
    db.commit()
    return {"removed": True}
