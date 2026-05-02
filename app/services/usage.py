from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.usage_event import UsageEvent


def record_usage(
    db: Session,
    user_id: UUID,
    metric: str,
    quantity: int = 1,
    metadata: dict[str, Any] | None = None,
) -> UsageEvent:
    event = UsageEvent(
        user_id=user_id,
        metric=metric,
        quantity=quantity,
        metadata_json=metadata or {},
    )
    db.add(event)
    return event


def usage_event_exists(
    db: Session,
    *,
    user_id: UUID,
    metric: str,
    idempotency_key: str,
) -> bool:
    rows = db.query(UsageEvent.metadata_json).filter(UsageEvent.user_id == user_id, UsageEvent.metric == metric).all()
    for (metadata,) in rows:
        if isinstance(metadata, dict) and metadata.get("idempotency_key") == idempotency_key:
            return True
    return False


def record_usage_once(
    db: Session,
    *,
    user_id: UUID,
    metric: str,
    idempotency_key: str,
    quantity: int = 1,
    metadata: dict[str, Any] | None = None,
) -> bool:
    if usage_event_exists(db, user_id=user_id, metric=metric, idempotency_key=idempotency_key):
        return False
    payload = dict(metadata or {})
    payload["idempotency_key"] = idempotency_key
    record_usage(db, user_id=user_id, metric=metric, quantity=quantity, metadata=payload)
    return True


def get_usage_total(
    db: Session,
    user_id: UUID,
    metric: str,
    period_start: datetime,
    period_end: datetime,
) -> int:
    total = (
        db.query(func.coalesce(func.sum(UsageEvent.quantity), 0))
        .filter(
            and_(
                UsageEvent.user_id == user_id,
                UsageEvent.metric == metric,
                UsageEvent.created_at >= period_start,
                UsageEvent.created_at < period_end,
            )
        )
        .scalar()
    )
    return int(total or 0)


def get_usage_summary(
    db: Session,
    user_id: UUID,
    period_start: datetime,
    period_end: datetime,
) -> dict[str, int]:
    rows = (
        db.query(UsageEvent.metric, func.coalesce(func.sum(UsageEvent.quantity), 0))
        .filter(
            and_(
                UsageEvent.user_id == user_id,
                UsageEvent.created_at >= period_start,
                UsageEvent.created_at < period_end,
            )
        )
        .group_by(UsageEvent.metric)
        .all()
    )
    summary: dict[str, int] = defaultdict(int)
    for metric, total in rows:
        summary[str(metric)] = int(total or 0)
    return dict(summary)
