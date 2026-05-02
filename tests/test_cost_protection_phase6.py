from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.models.usage_event import UsageEvent
from app.services.cost_protection import enforce_daily_cap, enforce_rate_limit
from app.services.usage import get_usage_total, record_usage, record_usage_once


def test_rate_limit_blocks_repeated_upload_attempts(db, test_user):
    for _ in range(10):
        record_usage(db, test_user.id, "upload_requests_rate", 1)
    db.commit()
    with pytest.raises(HTTPException) as exc:
        enforce_rate_limit(db, user_id=test_user.id, metric="upload_requests_rate", max_calls=10)
    assert exc.value.status_code == 429


def test_retries_do_not_double_count_usage(db, test_user):
    assert record_usage_once(db, user_id=test_user.id, metric="processing_jobs_daily", idempotency_key="process:doc-1") is True
    assert record_usage_once(db, user_id=test_user.id, metric="processing_jobs_daily", idempotency_key="process:doc-1") is False
    db.commit()
    day_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    total = get_usage_total(db, test_user.id, "processing_jobs_daily", day_start, day_start + timedelta(days=1))
    assert total == 1


def test_worker_refuses_processing_when_quota_exceeded(db, test_user):
    record_usage(db, test_user.id, "processing_jobs_daily", 2)
    db.commit()
    with pytest.raises(HTTPException):
        enforce_daily_cap(db, user_id=test_user.id, metric="processing_jobs_daily", cap=2)


def test_daily_caps_reset_by_date(db, test_user):
    record_usage(db, test_user.id, "uploads_daily", 1)
    db.flush()
    event = db.query(UsageEvent).filter(UsageEvent.user_id == test_user.id, UsageEvent.metric == "uploads_daily").first()
    event.created_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.add(event)
    db.commit()

    enforce_daily_cap(db, user_id=test_user.id, metric="uploads_daily", cap=1)
