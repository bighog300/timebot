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


from app.models.email import EmailTemplate


def seed_default_email_templates(db: Session) -> int:
    defaults = [
        ('Workspace Invite', 'workspace_invite', 'You are invited to {{workspace_name}}', 'Join {{workspace_name}}', '<p>You were invited to <b>{{workspace_name}}</b>.</p><p><a href="{{accept_url}}">Accept invite</a></p>', 'You were invited to {{workspace_name}}. Accept: {{accept_url}}', {'workspace_name':'Acme','accept_url':'https://app.example.com/invite/token'}),
        ('Password Reset', 'password_reset', 'Reset your password', 'Use this secure reset link', '<p>Reset link: <a href="{{reset_url}}">Reset password</a></p>', 'Reset your password: {{reset_url}}', {'reset_url':'https://app.example.com/reset/token'}),
        ('Welcome', 'welcome', 'Welcome to Timebot, {{first_name}}', "Let's get started", '<p>Welcome {{first_name}}! Visit {{app_url}}</p>', 'Welcome {{first_name}}! {{app_url}}', {'first_name':'Pat','app_url':'https://app.example.com'}),
        ('Billing Upgrade', 'billing_upgrade', 'Your plan is now {{plan_name}}', 'Billing upgrade confirmed', '<p>Your workspace upgraded to {{plan_name}}.</p>', 'Your workspace upgraded to {{plan_name}}.', {'plan_name':'Pro'}),
        ('Document Report Ready', 'document_report_ready', 'Your report is ready: {{document_name}}', 'Your document insights are ready', '<p>Report ready for {{document_name}}: <a href="{{report_url}}">Open report</a></p>', 'Report ready for {{document_name}}: {{report_url}}', {'document_name':'Contract.pdf','report_url':'https://app.example.com/reports/1'}),
    ]
    created = 0
    for name, slug, subject, preheader, html_body, text_body, variables_json in defaults:
        if db.query(EmailTemplate).filter(EmailTemplate.slug == slug).first():
            continue
        db.add(EmailTemplate(name=name, slug=slug, category='transactional', status='active', subject=subject, preheader=preheader, html_body=html_body, text_body=text_body, variables_json=variables_json))
        created += 1
    if created:
        db.commit()
    return created
