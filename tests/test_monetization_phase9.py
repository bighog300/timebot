import uuid

from datetime import datetime, timedelta, timezone

from app.models.billing import Plan, Subscription
from app.services.limit_enforcement import enforce_feature, enforce_limit


def _attach_subscription(db, user, slug: str, limits=None, features=None):
    plan = Plan(
        id=uuid.uuid4(),
        slug=f"{slug}-{uuid.uuid4()}",
        name=slug.title(),
        price_monthly_cents=0,
        currency="usd",
        limits_json=limits or {"documents_per_month": 1, "processing_jobs_per_month": 1, "storage_bytes": 1024},
        features_json=features or {"chat": True, "insights_enabled": False},
        is_active=True,
    )
    db.add(plan)
    db.commit()
    sub = Subscription(
        user_id=user.id,
        plan_id=plan.id,
        status="active",
        external_provider="internal",
        current_period_start=datetime.now(timezone.utc) + timedelta(seconds=1),
    )
    db.add(sub)
    db.commit()
    return plan, sub


def test_enforcement_uses_subscription_not_users_plan_for_limits(db, test_user):
    test_user.plan = "pro"
    db.add(test_user)
    db.commit()
    _attach_subscription(db, test_user, "freecheck", limits={"documents_per_month": 0, "processing_jobs_per_month": 0, "storage_bytes": 0})

    try:
        enforce_limit(db, test_user.id, "documents_per_month", quantity=1)
        assert False, "expected limit enforcement from subscription"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 402


def test_enforcement_uses_subscription_not_users_plan_for_features(db, test_user):
    test_user.plan = "pro"
    db.add(test_user)
    db.commit()
    _attach_subscription(db, test_user, "freefeatures", features={"chat": False, "insights_enabled": False})

    try:
        enforce_feature(db, test_user.id, "chat")
        assert False, "expected feature enforcement from subscription"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403


def test_subscription_change_affects_enforcement_users_plan_change_does_not(db, test_user):
    test_user.plan = "free"
    db.add(test_user)
    db.commit()
    _attach_subscription(db, test_user, "locked", features={"chat": False})

    test_user.plan = "pro"
    db.add(test_user)
    db.commit()
    try:
        enforce_feature(db, test_user.id, "chat")
        assert False, "chat should still be blocked"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 403

    _attach_subscription(db, test_user, "unlocked", features={"chat": True})
    enforce_feature(db, test_user.id, "chat")
