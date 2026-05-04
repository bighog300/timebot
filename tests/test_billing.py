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
