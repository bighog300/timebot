from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import secrets
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User


class AuthService:
    def hash_password(self, password: str) -> str:
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600000)
        return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            _algo, salt_hex, digest_hex = password_hash.split("$", 2)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(digest_hex)
        except ValueError:
            return False

        computed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600000)
        return hmac.compare_digest(expected, computed)

    def create_access_token(self, user: User) -> str:
        expires_delta = timedelta(minutes=settings.AUTH_ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + expires_delta
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "jti": secrets.token_hex(16),
        }
        return jwt.encode(payload, settings.AUTH_SECRET_KEY, algorithm=settings.AUTH_ALGORITHM)

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, settings.AUTH_SECRET_KEY, algorithms=[settings.AUTH_ALGORITHM])
        except jwt.PyJWTError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from exc

    def authenticate_user(self, db: Session, email: str, password: str) -> User | None:
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user or not self.verify_password(password, user.password_hash) or not user.is_active:
            return None
        return user

    def get_user_by_id(self, db: Session, user_id: UUID | str) -> User | None:
        return db.query(User).filter(User.id == user_id).first()


auth_service = AuthService()
