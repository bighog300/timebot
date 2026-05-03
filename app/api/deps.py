from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.user import User
from app.services.auth import auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = auth_service.decode_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token")

    user = auth_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user




def get_current_user_role(current_user: User = Depends(get_current_user)) -> str:
    return (current_user.role or "viewer").lower()


def require_editor_or_admin(role: str = Depends(get_current_user_role)) -> str:
    if role not in {"admin", "editor"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    return role


__all__ = ["get_db", "get_current_user", "get_current_user_role", "require_editor_or_admin"]


from fastapi import Header
from app.services.workspaces import workspace_service
from app.models.workspace import Workspace


def get_active_workspace(
    x_workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Workspace:
    personal = workspace_service.ensure_personal_workspace(db, current_user)
    if not x_workspace_id:
        return personal
    workspace_service.require_member(db, x_workspace_id, current_user.id)
    ws = db.query(Workspace).filter(Workspace.id == x_workspace_id).first()
    return ws or personal
