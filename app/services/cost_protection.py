from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.services.usage import get_usage_total


def _utc_day_window(now: datetime | None = None) -> tuple[datetime, datetime]:
    ts = now or datetime.now(timezone.utc)
    start = datetime(ts.year, ts.month, ts.day, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


def enforce_rate_limit(db: Session, *, user_id: UUID, metric: str, max_calls: int, window_seconds: int = 60) -> None:
    if max_calls <= 0:
        return
    end = datetime.now(timezone.utc)
    start = end - timedelta(seconds=window_seconds)
    used = get_usage_total(db, user_id, metric, start, end + timedelta(seconds=1))
    if used >= max_calls:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "rate_limit_exceeded", "metric": metric, "window_seconds": window_seconds, "limit": max_calls},
        )


def enforce_daily_cap(db: Session, *, user_id: UUID, metric: str, cap: int) -> None:
    if cap <= 0:
        return
    start, end = _utc_day_window()
    used = get_usage_total(db, user_id, metric, start, end)
    if used >= cap:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "daily_cap_exceeded", "metric": metric, "limit": cap, "used": used},
        )


def hard_daily_caps() -> dict[str, int]:
    return {
        "uploads_daily": settings.HARD_DAILY_MAX_UPLOADS,
        "processing_jobs_daily": settings.HARD_DAILY_MAX_PROCESSING_JOBS,
        "failed_processing_retries_daily": settings.HARD_DAILY_MAX_FAILED_PROCESSING_RETRIES,
    }
