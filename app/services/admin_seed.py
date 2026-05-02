import logging

from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.services.auth import auth_service

logger = logging.getLogger(__name__)


_MIGRATION_WARNING = "Skipping initial admin seed because migrations are not applied. Run alembic upgrade head."


def _is_missing_column_error(exc: ProgrammingError) -> bool:
    message = str(getattr(exc, "orig", exc)).lower()
    return "undefinedcolumn" in message or "column" in message and "does not exist" in message


def _can_reset_initial_admin_password() -> bool:
    return settings.APP_ENV.strip().lower() not in {"prod", "production"}


def seed_initial_admin(db: Session) -> bool:
    email = settings.INITIAL_ADMIN_EMAIL.strip().lower()
    password = settings.INITIAL_ADMIN_PASSWORD
    name = settings.INITIAL_ADMIN_NAME.strip() or "Timebot Admin"

    if not email or not password:
        return False

    try:
        existing = db.query(User).filter(User.email == email).first()
    except ProgrammingError as exc:
        if _is_missing_column_error(exc):
            db.rollback()
            logger.warning(_MIGRATION_WARNING)
            return False
        raise

    if existing:
        updated = False
        reset_password = settings.RESET_INITIAL_ADMIN_PASSWORD and _can_reset_initial_admin_password()
        if existing.role != "admin":
            existing.role = "admin"
            updated = True
        if not existing.is_active:
            existing.is_active = True
            updated = True
        if reset_password:
            existing.password_hash = auth_service.hash_password(password)
            updated = True
            logger.info("Reset initial admin password for: %s", email)

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
        role="admin",
    )
    db.add(user)
    db.commit()
    logger.info("Created initial admin user: %s", email)
    return True
