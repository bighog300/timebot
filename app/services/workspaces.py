from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.workspace import Workspace, WorkspaceInvite, WorkspaceMember


class WorkspaceService:
    def ensure_personal_workspace(self, db: Session, user: User) -> Workspace:
        existing = db.query(Workspace).filter(Workspace.owner_user_id == user.id, Workspace.type == "personal").first()
        if existing:
            member = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == existing.id, WorkspaceMember.user_id == user.id).first()
            if not member:
                db.add(WorkspaceMember(workspace_id=existing.id, user_id=user.id, role="owner"))
                db.commit()
            return existing
        ws = Workspace(name=f"{user.display_name}'s Workspace", type="personal", owner_user_id=user.id)
        db.add(ws)
        if hasattr(db, "flush"):
            db.flush()
        else:
            db.commit()
        db.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="owner"))
        db.commit()
        db.refresh(ws)
        return ws

    def list_for_user(self, db: Session, user_id):
        return db.query(Workspace).join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id).filter(WorkspaceMember.user_id == user_id).all()

    def require_member(self, db: Session, workspace_id, user_id) -> WorkspaceMember:
        member = db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == workspace_id, WorkspaceMember.user_id == user_id).first()
        if not member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied")
        return member

    def create_invite(self, db: Session, workspace_id, email: str, role: str, invited_by_user_id):
        role = role.lower().strip()
        if role not in {"member", "admin"}:
            raise HTTPException(status_code=400, detail="Invalid invite role. Allowed roles: member, admin")
        normalized_email = email.lower().strip()
        existing_member = (
            db.query(WorkspaceMember)
            .join(User, User.id == WorkspaceMember.user_id)
            .filter(WorkspaceMember.workspace_id == workspace_id, User.email == normalized_email)
            .first()
        )
        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a workspace member")
        existing_invite = db.query(WorkspaceInvite).filter(
            WorkspaceInvite.workspace_id == workspace_id,
            WorkspaceInvite.email == normalized_email,
            WorkspaceInvite.accepted_at.is_(None),
            WorkspaceInvite.canceled_at.is_(None),
        ).first()
        if existing_invite:
            raise HTTPException(status_code=400, detail="An active invite already exists for this email")
        token = secrets.token_urlsafe(24)
        invite = WorkspaceInvite(
            workspace_id=workspace_id,
            email=normalized_email,
            role=role,
            token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
            invited_by_user_id=invited_by_user_id,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db.add(invite)
        db.commit()
        db.refresh(invite)
        return invite, token

workspace_service = WorkspaceService()
