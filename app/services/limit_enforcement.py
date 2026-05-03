from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.subscriptions import ensure_default_free_subscription, get_user_subscription
from app.services.usage import get_usage_total

logger = logging.getLogger(__name__)

UNLIMITED_LIMIT = None


def _current_month_window() -> tuple[datetime, datetime]:
    now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    end = (start + timedelta(days=32)).replace(day=1)
    return start, end


def _current_period_window(db: Session, user_id: UUID) -> tuple[datetime, datetime]:
    ensure_default_free_subscription(db, user_id)
    subscription = get_user_subscription(db, user_id)
    if not subscription:
        return _current_month_window()

    start = subscription.current_period_start or _current_month_window()[0]
    end = subscription.current_period_end or (start + timedelta(days=32)).replace(day=1)
    return start, end


def _plan_limit(db: Session, user_id: UUID, metric: str):
    effective = get_effective_plan(db, user_id)
    overrides = (effective.get("limit_overrides") or {})
    if metric in overrides:
        return overrides[metric]
    return (effective.get("limits") or {}).get(metric)


def get_user_plan(db: Session, user_id: UUID):
    ensure_default_free_subscription(db, user_id)
    subscription = get_user_subscription(db, user_id)
    return subscription.plan if subscription else None


def get_workspace_plan(db: Session, workspace) -> dict:
    # Workspace-scoped plans are not yet first-class in the current schema.
    # Fall back to owner/user plan semantics for consistent enforcement.
    return get_effective_plan(db, workspace.owner_id)


def get_effective_plan(db: Session, subject) -> dict:
    user_id = subject if isinstance(subject, UUID) else getattr(subject, "id", subject)
    ensure_default_free_subscription(db, user_id)
    subscription = get_user_subscription(db, user_id)
    plan = subscription.plan if subscription else None
    return {
        "plan": plan,
        "limits": (plan.limits_json if plan else {}) or {},
        "features": (plan.features_json if plan else {}) or {},
        "limit_overrides": (subscription.limit_overrides_json if subscription else {}) or {},
        "usage_credits": (subscription.usage_credits_json if subscription else {}) or {},
        "subscription": subscription,
    }


def check_limit(db: Session, subject, limit_key: str, quantity: int = 1) -> bool:
    limit = _plan_limit(db, subject if isinstance(subject, UUID) else subject.id, limit_key)
    if limit is UNLIMITED_LIMIT:
        return True
    enforce_limit(db, subject if isinstance(subject, UUID) else subject.id, limit_key, quantity=quantity)
    return True


def assert_limit(db: Session, subject, limit_key: str, quantity: int = 1) -> None:
    enforce_limit(db, subject if isinstance(subject, UUID) else subject.id, limit_key, quantity=quantity)


def has_feature(db: Session, subject, feature_key: str) -> bool:
    effective = get_effective_plan(db, subject if isinstance(subject, UUID) else subject.id)
    return bool((effective.get("features") or {}).get(feature_key, False))


def enforce_limit(db: Session, user_id: UUID, metric: str, quantity: int = 1) -> None:
    limit = _plan_limit(db, user_id, metric)
    if limit is None:
        return

    period_start, period_end = _current_period_window(db, user_id)
    used = get_usage_total(db, user_id, metric, period_start, period_end)
    subscription = get_user_subscription(db, user_id)
    credits = ((subscription.usage_credits_json if subscription else {}) or {}).get(metric, 0)

    if metric == "storage_bytes":
        current_storage = db.query(Document.file_size).filter(Document.user_id == user_id).all()
        used = sum((row[0] or 0) for row in current_storage)
    used = max(0, used - int(credits or 0))

    if used + quantity > int(limit):
        logger.info("Quota denied user_id=%s metric=%s used=%s quantity=%s limit=%s", user_id, metric, used, quantity, limit)
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "limit_reached",
                "metric": metric,
                "message": f"Limit reached for {metric}.",
                "hint": "Upgrade your plan to increase limits.",
                "used": used,
                "limit": int(limit),
            },
        )


def enforce_feature(db: Session, user_id: UUID, feature: str) -> None:
    if not has_feature(db, user_id, feature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "feature_not_available",
                "feature": feature,
                "message": f"Feature not available: {feature}.",
                "hint": "Upgrade your plan to unlock this feature.",
            },
        )
