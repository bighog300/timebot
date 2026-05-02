from datetime import datetime, timezone

from app.api.v1 import monetization
from app.models.billing import Subscription
from app.services.subscriptions import ensure_default_free_subscription, seed_default_plans


def test_checkout_session_creation(client, db, test_user, monkeypatch):
    seed_default_plans(db)
    monkeypatch.setattr(monetization.billing_service, "create_checkout_session", lambda _db, _u, p: {"checkout_session_id": "cs_1", "checkout_url": "https://checkout", "plan": p})
    resp = client.post("/api/v1/billing/checkout-session", json={"plan": "pro"})
    assert resp.status_code == 200
    assert resp.json()["checkout_url"] == "https://checkout"


def test_customer_portal_creation(client, db, test_user, monkeypatch):
    ensure_default_free_subscription(db, test_user.id)
    monkeypatch.setattr(monetization.billing_service, "create_customer_portal_session", lambda _db, _u: {"portal_url": "https://portal"})
    resp = client.post("/api/v1/billing/customer-portal")
    assert resp.status_code == 200
    assert resp.json()["portal_url"] == "https://portal"


def test_valid_webhook_updates_subscription(client, db, test_user, monkeypatch):
    sub = ensure_default_free_subscription(db, test_user.id)
    sub.external_customer_id = "cus_123"
    db.add(sub)
    db.commit()

    event = {
        "type": "customer.subscription.updated",
        "data": {"object": {"id": "sub_123", "customer": "cus_123", "status": "active", "items": {"data": [{"price": {"id": monetization.billing_service.stripe_price_pro_monthly}}]}, "current_period_start": 1700000000, "current_period_end": 1702600000, "cancel_at_period_end": False}},
    }
    monkeypatch.setattr(monetization.billing_service, "construct_event", lambda payload, signature: event)
    resp = client.post("/api/v1/billing/webhook", data=b"{}", headers={"Stripe-Signature": "sig"})
    assert resp.status_code == 200
    db.refresh(sub)
    assert sub.status == "active"
    assert sub.external_subscription_id == "sub_123"


def test_invalid_webhook_rejected(client, monkeypatch):
    monkeypatch.setattr(monetization.billing_service, "construct_event", lambda payload, signature: (_ for _ in ()).throw(ValueError("Invalid Stripe signature")))
    resp = client.post("/api/v1/billing/webhook", data=b"{}")
    assert resp.status_code == 400


def test_canceled_subscription_handled(client, db, test_user, monkeypatch):
    sub = ensure_default_free_subscription(db, test_user.id)
    sub.external_customer_id = "cus_x"
    sub.external_subscription_id = "sub_x"
    db.add(sub)
    db.commit()
    event = {"type": "customer.subscription.deleted", "data": {"object": {"id": "sub_x", "customer": "cus_x", "status": "canceled", "items": {"data": [{"price": {"id": monetization.billing_service.stripe_price_pro_monthly}}]}, "current_period_start": int(datetime.now(timezone.utc).timestamp()), "current_period_end": int(datetime.now(timezone.utc).timestamp()), "cancel_at_period_end": True}}}
    monkeypatch.setattr(monetization.billing_service, "construct_event", lambda payload, signature: event)
    resp = client.post("/api/v1/billing/webhook", data=b"{}", headers={"Stripe-Signature": "sig"})
    assert resp.status_code == 200
    db.refresh(sub)
    assert sub.status == "canceled"
    assert sub.cancel_at_period_end is True


def test_invalid_plan_checkout_rejected(client):
    resp = client.post('/api/v1/billing/checkout-session', json={'plan': 'enterprise'})
    assert resp.status_code == 400
