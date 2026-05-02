from datetime import datetime, timezone
import uuid

import pytest
from fastapi import HTTPException

from app.models.billing import Plan, Subscription
from app.models.document import Document
from app.models.user import User
from app.services.limit_enforcement import enforce_feature, enforce_limit
from app.services.usage import record_usage


def _set_plan_limits(db, slug: str, limits: dict, features: dict | None = None):
    plan = db.query(Plan).filter(Plan.slug == slug).first()
    plan.limits_json = limits
    if features is not None:
        plan.features_json = features
    db.add(plan)
    db.commit()


def _mk_user(db, email: str) -> User:
    u = User(id=uuid.uuid4(), email=email, password_hash="x", display_name="U", is_active=True, role="editor")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _subscribe(db, user_id, slug: str):
    plan = db.query(Plan).filter(Plan.slug == slug).first()
    db.add(
        Subscription(
            user_id=user_id,
            plan_id=plan.id,
            status="active",
            current_period_start=datetime.now(timezone.utc),
            external_provider="internal",
        )
    )
    db.commit()


def _mk_doc(db, user_id, size: int = 100):
    db.add(Document(id=uuid.uuid4(), filename="a.pdf", original_path="/tmp/a.pdf", file_type="pdf", file_size=size, mime_type="application/pdf", processing_status="completed", source="upload", user_id=user_id))
    db.commit()


def test_free_user_can_upload_within_limit(db):
    from app.services.subscriptions import seed_default_plans

    seed_default_plans(db)
    _set_plan_limits(db, "free", {"documents_per_month": 10, "storage_bytes": 524288000, "processing_jobs_per_month": 10})
    user = _mk_user(db, "within@example.com")
    _subscribe(db, user.id, "free")
    for _ in range(9):
        record_usage(db, user.id, "documents_per_month", 1)
    db.commit()
    enforce_limit(db, user.id, "documents_per_month", 1)


def test_free_user_blocked_after_document_limit(db, monkeypatch):
    from app.services.subscriptions import seed_default_plans

    seed_default_plans(db)
    _set_plan_limits(db, "free", {"documents_per_month": 10, "storage_bytes": 524288000, "processing_jobs_per_month": 10})
    user = _mk_user(db, "blocked@example.com")
    _subscribe(db, user.id, "free")
    monkeypatch.setattr("app.services.limit_enforcement.get_usage_total", lambda *args, **kwargs: 30)
    with pytest.raises(HTTPException) as exc:
        enforce_limit(db, user.id, "documents_per_month", 1)
    assert exc.value.status_code == 402
    assert exc.value.detail["code"] == "limit_reached"


def test_storage_limit_blocks_large_upload(db):
    from app.services.subscriptions import seed_default_plans

    seed_default_plans(db)
    _set_plan_limits(db, "free", {"documents_per_month": 10, "storage_bytes": 524288000, "processing_jobs_per_month": 10})
    user = _mk_user(db, "storage@example.com")
    _subscribe(db, user.id, "free")
    _mk_doc(db, user.id, size=524288000)
    with pytest.raises(HTTPException):
        enforce_limit(db, user.id, "storage_bytes", 1)


def test_pro_user_has_higher_limits(db):
    from app.services.subscriptions import seed_default_plans

    seed_default_plans(db)
    _set_plan_limits(db, "pro", {"documents_per_month": 200, "storage_bytes": 10737418240, "processing_jobs_per_month": 200})
    user = _mk_user(db, "pro@example.com")
    _subscribe(db, user.id, "pro")
    for _ in range(150):
        record_usage(db, user.id, "documents_per_month", 1)
    db.commit()
    enforce_limit(db, user.id, "documents_per_month", 1)


def test_free_user_cannot_access_gated_features(db):
    from app.services.subscriptions import seed_default_plans

    seed_default_plans(db)
    _set_plan_limits(db, "free", {"documents_per_month": 10, "storage_bytes": 524288000, "processing_jobs_per_month": 10}, {"insights_enabled": False, "category_intelligence_enabled": False, "relationship_detection_enabled": False})
    user = _mk_user(db, "freegated@example.com")
    _subscribe(db, user.id, "free")
    with pytest.raises(HTTPException) as exc:
        enforce_feature(db, user.id, "insights_enabled")
    assert exc.value.status_code == 403
    assert exc.value.detail["code"] == "feature_not_available"


def test_pro_user_can_access_gated_features(db):
    from app.services.subscriptions import seed_default_plans

    seed_default_plans(db)
    _set_plan_limits(db, "pro", {"documents_per_month": 200, "storage_bytes": 10737418240, "processing_jobs_per_month": 200}, {"insights_enabled": True, "category_intelligence_enabled": True, "relationship_detection_enabled": True})
    user = _mk_user(db, "progated@example.com")
    _subscribe(db, user.id, "pro")
    enforce_feature(db, user.id, "insights_enabled")
    enforce_feature(db, user.id, "category_intelligence_enabled")
    enforce_feature(db, user.id, "relationship_detection_enabled")


def test_enforcement_is_user_scoped(db):
    from app.services.subscriptions import seed_default_plans

    seed_default_plans(db)
    _set_plan_limits(db, "free", {"documents_per_month": 10, "storage_bytes": 524288000, "processing_jobs_per_month": 10})
    user_a = _mk_user(db, "a@example.com")
    user_b = _mk_user(db, "b@example.com")
    _subscribe(db, user_a.id, "free")
    _subscribe(db, user_b.id, "free")
    for _ in range(10):
        record_usage(db, user_a.id, "documents_per_month", 1)
    db.commit()
    enforce_limit(db, user_b.id, "documents_per_month", 1)
