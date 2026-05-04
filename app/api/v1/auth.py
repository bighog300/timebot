from fastapi import APIRouter, Depends, HTTPException, status
import httpx
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from datetime import datetime, timezone
import hashlib

from app.models.user import User, UserInvite
from app.config import settings
from app.schemas.auth import AuthConfigResponse, AuthResponse, GoogleLoginRequest, InviteAcceptRequest, LoginRequest, RegisterRequest, UserResponse


def _ensure_role(user: User):
    if not getattr(user, "role", None):
        user.role = "viewer"
    return user
from app.services.auth import auth_service
from app.services.subscriptions import ensure_default_free_subscription
from app.services.workspaces import workspace_service

router = APIRouter(prefix="/auth", tags=["auth"])

def _auth_flags() -> tuple[str, bool, bool, bool]:
    auth_mode = (settings.AUTH_MODE or "local").strip().lower()
    google_enabled = bool(settings.GOOGLE_AUTH_ENABLED) and auth_mode in {"google", "local_google"}
    local_enabled = auth_mode in {"local", "local_google"}
    return auth_mode, bool(settings.GOOGLE_AUTH_ENABLED), local_enabled, google_enabled


@router.get("/config", response_model=AuthConfigResponse)
def auth_config():
    mode, google_toggle, local_enabled, google_enabled = _auth_flags()
    return AuthConfigResponse(auth_mode=mode, google_auth_enabled=google_toggle, local_login_enabled=local_enabled, google_login_enabled=google_enabled)



@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email.lower(),
        display_name=payload.display_name.strip(),
        password_hash=auth_service.hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    ensure_default_free_subscription(db, user.id)
    workspace_service.ensure_personal_workspace(db, user)
    token = auth_service.create_access_token(user)
    return AuthResponse(access_token=token, user=_ensure_role(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    _, _, local_enabled, _ = _auth_flags()
    if not local_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Local login is disabled")
    user = auth_service.authenticate_user(db, payload.email, payload.password)
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing and not existing.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = auth_service.create_access_token(user)
    return AuthResponse(access_token=token, user=_ensure_role(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return _ensure_role(current_user)


@router.post("/invites/accept", response_model=AuthResponse)
def accept_invite(payload: InviteAcceptRequest, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    invite = db.query(UserInvite).filter(UserInvite.token_hash == token_hash).first()
    now = datetime.now(timezone.utc)
    expires_at = invite.expires_at.replace(tzinfo=timezone.utc) if invite and invite.expires_at.tzinfo is None else (invite.expires_at if invite else None)
    if not invite or invite.accepted_at or invite.canceled_at or (expires_at is not None and expires_at <= now):
        raise HTTPException(status_code=400, detail="Invite token is invalid or expired")
    existing = db.query(User).filter(User.email == invite.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists; please login")
    user = User(
        email=invite.email.lower(),
        display_name=(payload.display_name or invite.email.split("@")[0]).strip(),
        password_hash=auth_service.hash_password(payload.password),
        is_active=True,
        role=invite.role,
    )
    invite.accepted_at = now
    db.add(user)
    db.commit()
    db.refresh(user)
    ensure_default_free_subscription(db, user.id)
    workspace_service.ensure_personal_workspace(db, user)
    return AuthResponse(access_token=auth_service.create_access_token(user), user=_ensure_role(user))


@router.post("/google", response_model=AuthResponse)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    _, _, _, google_enabled = _auth_flags()
    if not google_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Google login is disabled")
    try:
        resp = httpx.get("https://oauth2.googleapis.com/tokeninfo", params={"id_token": payload.id_token}, timeout=10.0)
        data = resp.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unable to validate Google token") from exc
    if data.get("error_description"):
        raise HTTPException(status_code=401, detail="Invalid Google token")
    aud = (data.get("aud") or "").strip()
    if aud != settings.GOOGLE_OAUTH_CLIENT_ID.strip():
        raise HTTPException(status_code=401, detail="Google token audience mismatch")
    if data.get("email_verified") not in {"true", True}:
        raise HTTPException(status_code=401, detail="Google email must be verified")
    email = (data.get("email") or "").strip().lower()
    sub = (data.get("sub") or "").strip()
    if not email or not sub:
        raise HTTPException(status_code=401, detail="Invalid Google identity payload")
    user = db.query(User).filter(User.email == email).first()
    if user and not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    if not user:
        user = User(email=email, display_name=(data.get("name") or email.split("@")[0]).strip(), password_hash=auth_service.hash_password(sub), is_active=True, auth_provider="google", google_subject=sub)
        db.add(user); db.commit(); db.refresh(user)
        ensure_default_free_subscription(db, user.id)
        workspace_service.ensure_personal_workspace(db, user)
    elif not user.google_subject:
        user.google_subject = sub
        if user.auth_provider == "local":
            user.auth_provider = "local_google"
        db.add(user); db.commit(); db.refresh(user)
    token = auth_service.create_access_token(user)
    return AuthResponse(access_token=token, user=_ensure_role(user))
