import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.services.auth import auth_service

logger = logging.getLogger(__name__)


def seed_initial_admin(db: Session) -> bool:
    email = settings.INITIAL_ADMIN_EMAIL.strip().lower()
    password = settings.INITIAL_ADMIN_PASSWORD
    name = settings.INITIAL_ADMIN_NAME.strip() or "Timebot Admin"

    if not email or not password:
        return False

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        updated = False
        if existing.role != "editor":
            existing.role = "editor"
            updated = True
        if not existing.is_active:
            existing.is_active = True
            updated = True
        if updated:
            db.add(existing)
            db.commit()
            logger.info("Updated existing initial admin user: %s", email)
        return True

    user = User(
        email=email,
        display_name=name,
        password_hash=auth_service.hash_password(password),
        is_active=True,
        role="editor",
    )
    db.add(user)
    db.commit()
    logger.info("Created initial admin user: %s", email)
    return True
