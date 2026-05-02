from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.billing import Plan, Subscription

DEFAULT_PLANS = [
    {
        "slug": "free",
        "name": "Free",
        "price_monthly_cents": 0,
        "currency": "usd",
        "limits_json": {"documents_per_month": 10, "storage_bytes": 524288000, "processing_jobs_per_month": 10},
        "features_json": {
            "basic_search": True,
            "chat": True,
            "insights_enabled": False,
            "category_intelligence_enabled": False,
            "relationship_detection_enabled": False,
        },
    },
    {
        "slug": "pro",
        "name": "Pro",
        "price_monthly_cents": 2900,
        "currency": "usd",
        "limits_json": {"documents_per_month": 200, "storage_bytes": 10737418240, "processing_jobs_per_month": 200},
        "features_json": {
            "basic_search": True,
            "chat": True,
            "priority_support": True,
            "insights_enabled": True,
            "category_intelligence_enabled": True,
            "relationship_detection_enabled": True,
        },
    },
    {
        "slug": "team",
        "name": "Team",
        "price_monthly_cents": 9900,
        "currency": "usd",
        "limits_json": {"documents_per_month": 2000, "storage_bytes": 107374182400, "processing_jobs_per_month": 2000, "seats": 10},
        "features_json": {
            "basic_search": True,
            "chat": True,
            "priority_support": True,
            "team_workspace": True,
            "insights_enabled": True,
            "category_intelligence_enabled": True,
            "relationship_detection_enabled": True,
        },
    },
]


def seed_default_plans(db: Session) -> int:
    created = 0
    for payload in DEFAULT_PLANS:
        existing = db.query(Plan).filter(Plan.slug == payload["slug"]).first()
        if existing:
            continue
        db.add(Plan(**payload, is_active=True))
        created += 1
    if created:
        db.commit()
    return created


def get_user_subscription(db: Session, user_id) -> Subscription | None:
    return (
        db.query(Subscription)
        .filter(Subscription.user_id == user_id)
        .order_by(Subscription.current_period_start.desc(), Subscription.created_at.desc())
        .first()
    )


def get_user_plan(db: Session, user_id) -> Plan | None:
    sub = get_user_subscription(db, user_id)
    return sub.plan if sub else None


def ensure_default_free_subscription(db: Session, user_id) -> Subscription:
    seed_default_plans(db)
    existing = get_user_subscription(db, user_id)
    if existing:
        return existing
    free_plan = db.query(Plan).filter(Plan.slug == "free", Plan.is_active.is_(True)).first()
    if free_plan is None:
        raise RuntimeError("Free plan is not configured")

    now = datetime.now(timezone.utc)
    subscription = Subscription(
        user_id=user_id,
        plan_id=free_plan.id,
        status="active",
        current_period_start=now,
        current_period_end=None,
        cancel_at_period_end=False,
        external_provider="internal",
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def get_plan_limit(db: Session, user_id, metric: str):
    plan = get_user_plan(db, user_id)
    if not plan:
        return None
    return (plan.limits_json or {}).get(metric)


def user_has_feature(db: Session, user_id, feature: str) -> bool:
    plan = get_user_plan(db, user_id)
    if not plan:
        return False
    return bool((plan.features_json or {}).get(feature, False))
