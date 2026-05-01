from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, GeneratedReport
from app.models.document import Document
from app.models.user import User


class PlanTier(str, Enum):
    FREE = "free"
    PRO = "pro"


class ActionType(str, Enum):
    UPLOAD_DOCUMENT = "upload_document"
    GENERATE_REPORT = "generate_report"
    SEND_CHAT = "send_chat"


@dataclass
class LimitCheckResult:
    allowed: bool
    used: int
    limit: int | None


PLAN_LIMITS: dict[PlanTier, dict[ActionType, int | None]] = {
    PlanTier.FREE: {
        ActionType.UPLOAD_DOCUMENT: 25,
        ActionType.GENERATE_REPORT: 10,
        ActionType.SEND_CHAT: 200,
    },
    PlanTier.PRO: {
        ActionType.UPLOAD_DOCUMENT: None,
        ActionType.GENERATE_REPORT: None,
        ActionType.SEND_CHAT: None,
    },
}


def _current_month_window() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    next_month = (start + timedelta(days=32)).replace(day=1)
    return start, next_month


def _normalize_plan(plan: str | None) -> PlanTier:
    try:
        return PlanTier((plan or "free").lower())
    except ValueError:
        return PlanTier.FREE


def check_user_limit(db: Session, user: User, action_type: ActionType) -> LimitCheckResult:
    plan = _normalize_plan(user.plan)
    limit = PLAN_LIMITS[plan][action_type]
    if limit is None:
        return LimitCheckResult(allowed=True, used=0, limit=None)

    if action_type == ActionType.UPLOAD_DOCUMENT:
        used = db.query(Document).filter(Document.user_id == user.id).count()
    else:
        start, end = _current_month_window()
        if action_type == ActionType.GENERATE_REPORT:
            used = db.query(GeneratedReport).filter(and_(GeneratedReport.created_by_id == user.id, GeneratedReport.created_at >= start, GeneratedReport.created_at < end)).count()
        else:
            used = db.query(ChatMessage).join(ChatMessage.session).filter(and_(ChatMessage.role == "user", ChatMessage.created_at >= start, ChatMessage.created_at < end, ChatMessage.session.has(user_id=user.id))).count()
    return LimitCheckResult(allowed=used < limit, used=used, limit=limit)


def ensure_user_limit(db: Session, user: User, action_type: ActionType) -> None:
    check = check_user_limit(db, user, action_type)
    if not check.allowed:
        raise HTTPException(status_code=429, detail="Usage limit reached")


def refresh_usage_counters(db: Session, user: User) -> None:
    start, end = _current_month_window()
    user.documents_uploaded_count = db.query(Document).filter(Document.user_id == user.id).count()
    user.reports_generated_count = db.query(GeneratedReport).filter(and_(GeneratedReport.created_by_id == user.id, GeneratedReport.created_at >= start, GeneratedReport.created_at < end)).count()
    user.chat_messages_count = db.query(ChatMessage).filter(and_(ChatMessage.role == "user", ChatMessage.created_at >= start, ChatMessage.created_at < end, ChatMessage.session.has(user_id=user.id))).count()
    db.add(user)


def usage_payload(db: Session, user: User) -> dict:
    plan = _normalize_plan(user.plan)
    refresh_usage_counters(db, user)
    return {
        "plan": plan.value,
        "documents": {"used": user.documents_uploaded_count, "limit": PLAN_LIMITS[plan][ActionType.UPLOAD_DOCUMENT]},
        "reports": {"used": user.reports_generated_count, "limit": PLAN_LIMITS[plan][ActionType.GENERATE_REPORT]},
        "chat_messages": {"used": user.chat_messages_count, "limit": PLAN_LIMITS[plan][ActionType.SEND_CHAT]},
    }
