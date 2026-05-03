from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from datetime import datetime, timezone
import hashlib

from app.models.user import User, UserInvite
from app.schemas.auth import AuthResponse, InviteAcceptRequest, LoginRequest, RegisterRequest, UserResponse


def _ensure_role(user: User):
    if not getattr(user, "role", None):
        user.role = "viewer"
    return user
from app.services.auth import auth_service
from app.services.subscriptions import ensure_default_free_subscription

router = APIRouter(prefix="/auth", tags=["auth"])


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
    token = auth_service.create_access_token(user)
    return AuthResponse(access_token=token, user=_ensure_role(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
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
    if not invite or invite.accepted_at or invite.canceled_at or invite.expires_at <= now:
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
    return AuthResponse(access_token=auth_service.create_access_token(user), user=_ensure_role(user))
