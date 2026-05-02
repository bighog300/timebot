from datetime import datetime, timezone

from app.api.v1 import monetization
from app.models.billing import Subscription
from app.services.subscriptions import ensure_default_free_subscription, seed_default_plans
from app.services.usage import record_usage


def test_signup_creates_free_subscription(client, db, test_user):
    sub = ensure_default_free_subscription(db, test_user.id)
    assert sub is not None
    assert sub.plan.slug == "free"


def test_upload_within_free_limit_succeeds(client, db, test_user, monkeypatch):
    seed_default_plans(db)
    free = ensure_default_free_subscription(db, test_user.id)
    free.plan.limits_json["documents_per_month"] = 1
    db.add(free)
    db.commit()

    from pathlib import Path
    async def _save_upload(_file):
        return (Path("/tmp/a.pdf"), 22)
    monkeypatch.setattr("app.services.storage.storage.save_upload", _save_upload)
    monkeypatch.setattr("app.workers.tasks.process_document_task.apply_async", lambda *args, **kwargs: type("T", (), {"id": "task1"})())

    response = client.post("/api/v1/upload", files={"file": ("a.pdf", b"%PDF-1.4 test", "application/pdf")})
    assert response.status_code == 202


def test_free_limit_blocks_upload(client, db, test_user, monkeypatch):
    seed_default_plans(db)
    ensure_default_free_subscription(db, test_user.id)
    monkeypatch.setattr("app.services.limit_enforcement._plan_limit", lambda *_args, **_kwargs: 0)

    response = client.post("/api/v1/upload", files={"file": ("a.pdf", b"%PDF-1.4 test", "application/pdf")})
    assert response.status_code == 402
    assert response.json()["detail"]["code"] == "limit_reached"


def test_mocked_webhook_upgrades_user_to_pro(client, db, test_user, monkeypatch):
    sub = ensure_default_free_subscription(db, test_user.id)
    sub.external_customer_id = "cus_abc"
    db.add(sub)
    db.commit()

    event = {
        "type": "customer.subscription.updated",
        "data": {"object": {"id": "sub_abc", "customer": "cus_abc", "status": "active", "items": {"data": [{"price": {"id": monetization.billing_service.stripe_price_pro_monthly}}]}, "current_period_start": 1700000000, "current_period_end": 1702600000, "cancel_at_period_end": False}},
    }
    monkeypatch.setattr(monetization.billing_service, "construct_event", lambda payload, signature: event)

    response = client.post("/api/v1/billing/webhook", data=b"{}", headers={"Stripe-Signature": "sig"})
    assert response.status_code == 200
    db.refresh(sub)
    assert sub.plan.slug != "free"


def test_upload_after_upgrade_succeeds(client, db, test_user, monkeypatch):
    seed_default_plans(db)
    sub = ensure_default_free_subscription(db, test_user.id)
    pro = db.query(sub.plan.__class__).filter_by(slug="pro").first()
    sub.plan_id = pro.id
    db.add(sub)
    db.commit()

    from pathlib import Path
    async def _save_upload(_file):
        return (Path("/tmp/a.pdf"), 22)
    monkeypatch.setattr("app.services.storage.storage.save_upload", _save_upload)
    monkeypatch.setattr("app.workers.tasks.process_document_task.apply_async", lambda *args, **kwargs: type("T", (), {"id": "task2"})())
    response = client.post("/api/v1/upload", files={"file": ("a.pdf", b"%PDF-1.4 test", "application/pdf")})
    assert response.status_code == 202


def test_mocked_cancel_webhook_marks_canceled(client, db, test_user, monkeypatch):
    sub = ensure_default_free_subscription(db, test_user.id)
    sub.external_customer_id = "cus_cancel"
    sub.external_subscription_id = "sub_cancel"
    db.add(sub)
    db.commit()

    event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_cancel", "customer": "cus_cancel", "status": "canceled", "items": {"data": [{"price": {"id": monetization.billing_service.stripe_price_pro_monthly}}]}, "current_period_start": int(datetime.now(timezone.utc).timestamp()), "current_period_end": int(datetime.now(timezone.utc).timestamp()), "cancel_at_period_end": True}},
    }
    monkeypatch.setattr(monetization.billing_service, "construct_event", lambda payload, signature: event)

    response = client.post("/api/v1/billing/webhook", data=b"{}", headers={"Stripe-Signature": "sig"})
    assert response.status_code == 200
    db.refresh(sub)
    assert sub.status == "canceled"
    assert sub.cancel_at_period_end is True


def test_billing_endpoints_require_auth(db):
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as unauth_client:
        assert unauth_client.get("/api/v1/me/usage").status_code == 401
        assert unauth_client.post("/api/v1/billing/checkout-session", json={"plan": "pro"}).status_code == 401


def test_webhook_requires_signature(client):
    response = client.post("/api/v1/billing/webhook", data=b"{}")
    assert response.status_code == 400
