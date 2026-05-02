from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.subscriptions import ensure_default_free_subscription, get_user_subscription
from app.services.usage import get_usage_total


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
    ensure_default_free_subscription(db, user_id)
    subscription = get_user_subscription(db, user_id)
    limits = (subscription.plan.limits_json if subscription and subscription.plan else {}) or {}
    return limits.get(metric)


def enforce_limit(db: Session, user_id: UUID, metric: str, quantity: int = 1) -> None:
    limit = _plan_limit(db, user_id, metric)
    if limit is None:
        return

    period_start, period_end = _current_period_window(db, user_id)
    used = get_usage_total(db, user_id, metric, period_start, period_end)

    if metric == "storage_bytes":
        current_storage = db.query(Document.file_size).filter(Document.user_id == user_id).all()
        used = sum((row[0] or 0) for row in current_storage)

    if used + quantity > int(limit):
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
    ensure_default_free_subscription(db, user_id)
    subscription = get_user_subscription(db, user_id)
    features = (subscription.plan.features_json if subscription and subscription.plan else {}) or {}
    if not bool(features.get(feature, False)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "feature_not_available",
                "feature": feature,
                "message": f"Feature not available: {feature}.",
                "hint": "Upgrade your plan to unlock this feature.",
            },
        )
