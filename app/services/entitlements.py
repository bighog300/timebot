from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.chat import AssistantProfile
from app.models.user import User
from app.services.limit_enforcement import get_effective_plan, get_usage_total

PLAN_RANK = {"free": 0, "pro": 1, "business": 2, "admin": 3, "team": 2}


def _plan_slug(db: Session, user: User) -> str:
    if user.role == "admin":
        return "admin"
    effective = get_effective_plan(db, user.id)
    plan = effective.get("plan")
    return str(getattr(plan, "slug", None) or user.plan or "free").lower()


def _at_least(current: str, required: str) -> bool:
    return PLAN_RANK.get(current, 0) >= PLAN_RANK.get(required, 0)


def get_usage_limits(db: Session, user: User) -> dict:
    plan = _plan_slug(db, user)
    if plan == "admin":
        return {"chat_sessions": None, "messages_per_month": None, "reports_per_month": None}
    return {
        "chat_sessions": 5 if plan == "free" else (50 if plan == "pro" else 250),
        "messages_per_month": 200 if plan == "free" else (2000 if plan == "pro" else 10000),
        "reports_per_month": 2 if plan == "free" else (25 if plan == "pro" else 250),
    }


def can_use_assistant(db: Session, user: User, assistant: AssistantProfile) -> bool:
    return _at_least(_plan_slug(db, user), str(assistant.required_plan or "free").lower())


def can_use_prompt_template(db: Session, user: User, template) -> bool:
    return _plan_slug(db, user) in {"pro", "business", "admin"}


def can_create_custom_prompt(db: Session, user: User) -> bool:
    return _plan_slug(db, user) in {"pro", "business", "admin"}


def can_create_chat(db: Session, user: User) -> bool:
    limits = get_usage_limits(db, user)
    if limits["chat_sessions"] is None:
        return True
    from app.models.chat import ChatSession
    count = db.query(ChatSession).filter(ChatSession.user_id == user.id, ChatSession.is_deleted.is_(False)).count()
    return count < int(limits["chat_sessions"])


def can_generate_report(db: Session, user: User) -> bool:
    return _plan_slug(db, user) in {"pro", "business", "admin"}


def can_use_system_intelligence(db: Session, user: User) -> bool:
    return _plan_slug(db, user) in {"pro", "business", "admin"}


def require_upgrade(required_plan: str, feature: str, message: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={"error": "upgrade_required", "required_plan": required_plan, "feature": feature, "message": message},
    )


def enforce_message_limit(db: Session, user: User) -> None:
    limits = get_usage_limits(db, user)
    msg_limit = limits["messages_per_month"]
    if msg_limit is None:
        return
    from app.services.limit_enforcement import _current_period_window
    start, end = _current_period_window(db, user.id)
    used = get_usage_total(db, user.id, "processing_jobs_per_month", start, end)
    if used >= int(msg_limit):
        require_upgrade("pro", "monthly_messages", f"Free plan includes {msg_limit} messages/month. Upgrade to Pro for more.")
