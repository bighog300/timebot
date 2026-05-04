from app.api.v1 import monetization
from app.config import settings


def test_billing_status_disabled_by_default(client):
    response = client.get('/api/v1/billing/status')
    assert response.status_code == 200
    payload = response.json()
    assert payload['enabled'] is False


def test_checkout_blocked_when_billing_disabled(client):
    response = client.post('/api/v1/billing/checkout', json={'plan': 'pro'})
    assert response.status_code == 503


def test_webhook_disabled_response(client, monkeypatch):
    monkeypatch.setattr(settings, 'STRIPE_ENABLED', False)
    monkeypatch.setattr(settings, 'BILLING_PROVIDER', 'manual')
    response = client.post('/api/v1/billing/webhook', data=b'{}')
    assert response.status_code == 503
    assert response.json()['detail']['code'] == 'billing_disabled'


def test_stripe_enabled_requires_env_vars(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, 'STRIPE_ENABLED', True)
    monkeypatch.setattr(settings, 'BILLING_PROVIDER', 'stripe')
    monkeypatch.setattr(monetization.billing_service, 'stripe_enabled', True)
    monkeypatch.setattr(monetization.billing_service, 'billing_provider', 'stripe')
    monkeypatch.setattr(monetization.billing_service, 'stripe_secret_key', '')
    response = client.post('/api/v1/billing/checkout', json={'plan': 'pro'}, headers=auth_headers)
    assert response.status_code == 400
    assert response.json()['detail']['code'] == 'billing_not_configured'



def _enable_stripe(monkeypatch):
    monkeypatch.setattr(settings, 'STRIPE_ENABLED', True)
    monkeypatch.setattr(settings, 'BILLING_PROVIDER', 'stripe')
    monkeypatch.setattr(monetization.billing_service, 'stripe_enabled', True)
    monkeypatch.setattr(monetization.billing_service, 'billing_provider', 'stripe')
    monkeypatch.setattr(monetization.billing_service, 'stripe_price_pro_monthly', 'price_pro')
    monkeypatch.setattr(monetization.billing_service, 'stripe_price_business_monthly', 'price_business')


def test_checkout_session_completed_updates_plan_and_ids(client, db, test_user, monkeypatch):
    from app.services.subscriptions import ensure_default_free_subscription

    _enable_stripe(monkeypatch)
    sub = ensure_default_free_subscription(db, test_user.id)
    event = {
        'type': 'checkout.session.completed',
        'data': {'object': {
            'id': 'cs_123',
            'client_reference_id': str(test_user.id),
            'customer': 'cus_new',
            'subscription': 'sub_new',
            'metadata': {'plan': 'pro'},
        }},
    }
    monkeypatch.setattr(monetization.billing_service, 'construct_event', lambda payload, signature: event)

    response = client.post('/api/v1/billing/webhook', data=b'{}', headers={'Stripe-Signature': 'sig'})
    assert response.status_code == 200
    db.refresh(sub)
    assert sub.plan.slug == 'pro'
    assert sub.status == 'active'
    assert sub.billing_customer_id == 'cus_new'
    assert sub.billing_subscription_id == 'sub_new'


def test_subscription_created_and_updated_map_plan_and_status(client, db, test_user, monkeypatch):
    from app.services.subscriptions import ensure_default_free_subscription

    _enable_stripe(monkeypatch)
    sub = ensure_default_free_subscription(db, test_user.id)
    sub.external_customer_id = 'cus_sub'
    db.commit()

    created = {
        'type': 'customer.subscription.created',
        'data': {'object': {
            'id': 'sub_sub', 'customer': 'cus_sub', 'status': 'active',
            'items': {'data': [{'price': {'id': 'price_pro'}}]},
            'current_period_start': 1700000000, 'current_period_end': 1702600000, 'cancel_at_period_end': False,
        }},
    }
    updated = {
        'type': 'customer.subscription.updated',
        'data': {'object': {
            'id': 'sub_sub', 'customer': 'cus_sub', 'status': 'past_due',
            'items': {'data': [{'price': {'id': 'price_pro'}}]},
            'current_period_start': 1700000000, 'current_period_end': 1703600000, 'cancel_at_period_end': True,
        }},
    }
    monkeypatch.setattr(monetization.billing_service, 'construct_event', lambda payload, signature: created)
    assert client.post('/api/v1/billing/webhook', data=b'{}', headers={'Stripe-Signature': 'sig'}).status_code == 200
    monkeypatch.setattr(monetization.billing_service, 'construct_event', lambda payload, signature: updated)
    assert client.post('/api/v1/billing/webhook', data=b'{}', headers={'Stripe-Signature': 'sig'}).status_code == 200

    db.refresh(sub)
    assert sub.plan.slug == 'pro'
    assert sub.status == 'past_due'
    assert sub.billing_customer_id == 'cus_sub'
    assert sub.billing_subscription_id == 'sub_sub'
    assert sub.cancel_at_period_end is True


def test_subscription_deleted_sets_canceled(client, db, test_user, monkeypatch):
    from app.services.subscriptions import ensure_default_free_subscription

    _enable_stripe(monkeypatch)
    sub = ensure_default_free_subscription(db, test_user.id)
    sub.external_customer_id = 'cus_del'
    db.commit()

    deleted = {
        'type': 'customer.subscription.deleted',
        'data': {'object': {
            'id': 'sub_del', 'customer': 'cus_del', 'status': 'canceled',
            'items': {'data': [{'price': {'id': 'price_pro'}}]},
            'current_period_start': 1700000000, 'current_period_end': 1702600000, 'cancel_at_period_end': True,
        }},
    }
    monkeypatch.setattr(monetization.billing_service, 'construct_event', lambda payload, signature: deleted)
    assert client.post('/api/v1/billing/webhook', data=b'{}', headers={'Stripe-Signature': 'sig'}).status_code == 200
    db.refresh(sub)
    assert sub.status == 'canceled'


def test_invoice_payment_failed_sets_past_due_and_duplicate_is_idempotent(client, db, test_user, monkeypatch):
    from app.services.subscriptions import ensure_default_free_subscription

    _enable_stripe(monkeypatch)
    sub = ensure_default_free_subscription(db, test_user.id)
    sub.external_customer_id = 'cus_inv'
    sub.status = 'active'
    db.commit()

    event = {'type': 'invoice.payment_failed', 'data': {'object': {'id': 'in_1', 'customer': 'cus_inv'}}}
    monkeypatch.setattr(monetization.billing_service, 'construct_event', lambda payload, signature: event)

    assert client.post('/api/v1/billing/webhook', data=b'{}', headers={'Stripe-Signature': 'sig'}).status_code == 200
    first_updated_at = sub.updated_at
    assert client.post('/api/v1/billing/webhook', data=b'{}', headers={'Stripe-Signature': 'sig'}).status_code == 200
    db.refresh(sub)
    assert sub.status == 'past_due'
    assert sub.billing_customer_id == 'cus_inv'
    assert sub.updated_at >= first_updated_at
