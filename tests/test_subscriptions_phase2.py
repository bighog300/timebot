import uuid
from datetime import datetime, timedelta, timezone

from app.models.billing import Plan, Subscription
from app.models.user import User
from app.services.auth import auth_service
from app.services.subscriptions import (
    ensure_default_free_subscription,
    get_plan_limit,
    get_user_plan,
    seed_default_plans,
    user_has_feature,
)


def test_default_plans_are_seeded(db):
    created = seed_default_plans(db)
    assert created == 3
    assert seed_default_plans(db) == 0

    slugs = {p.slug for p in db.query(Plan).all()}
    assert {"free", "pro", "team"}.issubset(slugs)


def test_new_user_receives_free_subscription(client, db):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": "password123", "display_name": "New User"},
    )
    assert res.status_code == 201

    user_id = res.json()["user"]["id"]
    subscription = db.query(Subscription).filter(Subscription.user_id == user_id).first()
    assert subscription is not None
    assert subscription.plan.slug == "free"


def test_get_user_plan_resolves_latest_subscription(db):
    seed_default_plans(db)
    user = User(
        id=uuid.uuid4(),
        email="planresolve@example.com",
        password_hash=auth_service.hash_password("password123"),
        display_name="Plan Resolver",
        is_active=True,
        role="viewer",
    )
    db.add(user)
    db.commit()

    ensure_default_free_subscription(db, user.id)
    team = db.query(Plan).filter(Plan.slug == "team").first()
    db.add(Subscription(user_id=user.id, plan_id=team.id, status="active", current_period_start=datetime.now(timezone.utc) + timedelta(seconds=5)))
    db.commit()

    plan = get_user_plan(db, user.id)
    assert plan is not None
    assert plan.slug == "team"


def test_limits_and_features_resolve_from_user_plan(db):
    seed_default_plans(db)
    user = User(
        id=uuid.uuid4(),
        email="limits@example.com",
        password_hash=auth_service.hash_password("password123"),
        display_name="Limits User",
        is_active=True,
        role="viewer",
    )
    db.add(user)
    db.commit()

    ensure_default_free_subscription(db, user.id)
    assert get_plan_limit(db, user.id, "documents_per_month") == 10
    assert user_has_feature(db, user.id, "chat") is True
    assert user_has_feature(db, user.id, "team_workspace") is False
