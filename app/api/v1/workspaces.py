import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.api.deps import get_active_workspace, get_current_user, get_db
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceInvite, WorkspaceMember
from app.models.email import EmailTemplate
from app.services.email_delivery import EmailDeliveryService
from app.schemas.workspace import WorkspaceDetailResponse, WorkspaceInviteResponse, WorkspaceMemberResponse, WorkspaceResponse
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

@router.post("", response_model=WorkspaceResponse)
def create_workspace(payload: WorkspaceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ws = Workspace(name=payload.name.strip(), type="team", owner_user_id=current_user.id)
    db.add(ws); db.flush()
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=current_user.id, role="owner"))
    db.commit(); db.refresh(ws)
    return ws

def _invite_status(invite: WorkspaceInvite) -> str:
    now = datetime.now(timezone.utc)
    if invite.accepted_at:
        return "accepted"
    if invite.canceled_at:
        return "canceled"
    expires_at = invite.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at and expires_at <= now:
        return "expired"
    return "pending"

@router.get("/{workspace_id}", response_model=WorkspaceDetailResponse)
def get_workspace(workspace_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    workspace_service.require_member(db, workspace_id, current_user.id)
    ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not ws: raise HTTPException(status_code=404, detail="Workspace not found")
    members = db.query(WorkspaceMember, User).join(User, User.id == WorkspaceMember.user_id).filter(WorkspaceMember.workspace_id == ws.id).all()
    invites = db.query(WorkspaceInvite).filter(WorkspaceInvite.workspace_id == ws.id).order_by(WorkspaceInvite.created_at.desc()).all()
    return WorkspaceDetailResponse(
        **WorkspaceResponse.model_validate(ws, from_attributes=True).model_dump(),
        members=[WorkspaceMemberResponse(user_id=m.user_id, email=u.email, display_name=u.display_name, role=m.role, created_at=m.created_at) for m, u in members],
        invites=[WorkspaceInviteResponse.model_validate(i, from_attributes=True).model_copy(update={"status": _invite_status(i)}) for i in invites],
    )

@router.post("/{workspace_id}/invites")
def invite(workspace_id: str, payload: InviteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member = workspace_service.require_member(db, workspace_id, current_user.id)
    if member.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Only owner/admin may invite")
    invite, token = workspace_service.create_invite(db, workspace_id, payload.email, payload.role, current_user.id)
    accept_url = f"/workspaces/invites/{token}/accept"
    template = db.query(EmailTemplate).filter(EmailTemplate.slug == "workspace_invite", EmailTemplate.status == "active").first()
    if template:
        EmailDeliveryService(db).send_email(provider=None, to_email=invite.email, subject=template.subject.replace("{{workspace_name}}", db.query(Workspace).filter(Workspace.id == workspace_id).first().name), html_body=template.html_body.replace("{{accept_url}}", accept_url).replace("{{workspace_name}}", db.query(Workspace).filter(Workspace.id == workspace_id).first().name), text_body=(template.text_body or "").replace("{{accept_url}}", accept_url))
    invite_data = WorkspaceInviteResponse.model_validate({**invite.__dict__, "status": _invite_status(invite)})
    out = {"invite": invite_data}
    out["dev_invite_link"] = accept_url
    return out

@router.post("/invites/{token}/accept")
def accept_workspace_invite(token: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    invite = db.query(WorkspaceInvite).filter(WorkspaceInvite.token_hash == token_hash).first()
    now = datetime.now(timezone.utc)
    expires_at = invite.expires_at if invite else None
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if not invite or invite.accepted_at or (expires_at is not None and expires_at <= now):
        raise HTTPException(status_code=400, detail="Invalid invite")
    if invite.email.lower() != (current_user.email or "").lower():
        raise HTTPException(status_code=400, detail=f"Invite is for {invite.email}; signed-in user email does not match")
    exists = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == invite.workspace_id, WorkspaceMember.user_id == current_user.id).first()
    if not exists:
        db.add(WorkspaceMember(workspace_id=invite.workspace_id, user_id=current_user.id, role=invite.role))
    invite.accepted_at = now
    db.commit()
    return {"accepted": True}

@router.get("/{workspace_id}/invites", response_model=list[WorkspaceInviteResponse])
def list_workspace_invites(workspace_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member = workspace_service.require_member(db, workspace_id, current_user.id)
    if member.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Only owner/admin may view invites")
    invites = db.query(WorkspaceInvite).filter(WorkspaceInvite.workspace_id == workspace_id).order_by(WorkspaceInvite.created_at.desc()).all()
    return [WorkspaceInviteResponse.model_validate(i, from_attributes=True).model_copy(update={"status": _invite_status(i)}) for i in invites]

@router.post("/{workspace_id}/invites/{invite_id}/resend", response_model=WorkspaceInviteResponse)
def resend_workspace_invite(workspace_id: str, invite_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member = workspace_service.require_member(db, workspace_id, current_user.id)
    if member.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Only owner/admin may resend invites")
    invite = db.query(WorkspaceInvite).filter(WorkspaceInvite.id == invite_id, WorkspaceInvite.workspace_id == workspace_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if _invite_status(invite) != "pending":
        raise HTTPException(status_code=400, detail="Only pending invites can be resent")
    db.delete(invite); db.commit()
    new_invite, _ = workspace_service.create_invite(db, workspace_id, invite.email, invite.role, current_user.id)
    return WorkspaceInviteResponse.model_validate(new_invite, from_attributes=True).model_copy(update={"status": _invite_status(new_invite), "dev_invite_link": "/dev"})

@router.delete("/{workspace_id}/invites/{invite_id}")
def cancel_workspace_invite(workspace_id: str, invite_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member = workspace_service.require_member(db, workspace_id, current_user.id)
    if member.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Only owner/admin may cancel invites")
    invite = db.query(WorkspaceInvite).filter(WorkspaceInvite.id == invite_id, WorkspaceInvite.workspace_id == workspace_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    invite.canceled_at = datetime.now(timezone.utc)
    db.commit()
    return {"canceled": True}

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
