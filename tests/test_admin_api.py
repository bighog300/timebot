import uuid
from datetime import datetime, timedelta, timezone

from app.models.admin_audit import AdminAuditEvent
from app.models.document import Document
from app.models.user import User
from app.services.usage import record_usage


def test_admin_can_list_users(client, test_user, db):
    test_user.role = 'admin'; db.commit()
    r = client.get('/api/v1/admin/users')
    assert r.status_code == 200
    assert r.json()['total_count'] >= 1


def test_non_admin_cannot_list_users(client, test_user, db):
    test_user.role = 'viewer'; db.commit()
    r = client.get('/api/v1/admin/users')
    assert r.status_code == 403


def test_admin_can_update_role_and_audit(client, test_user, db):
    test_user.role='admin';
    target=User(id=uuid.uuid4(), email='u2@example.com', password_hash='x', display_name='U2', is_active=True, role='viewer')
    db.add(target); db.commit()
    r=client.patch(f'/api/v1/admin/users/{target.id}/role', json={'role':'editor'})
    assert r.status_code==200
    db.refresh(target)
    assert target.role=='editor'
    ev=db.query(AdminAuditEvent).filter(AdminAuditEvent.entity_id==str(target.id)).first()
    assert ev is not None


def test_invalid_role_rejected(client, test_user, db):
    test_user.role='admin'; db.commit()
    r=client.patch(f'/api/v1/admin/users/{test_user.id}/role', json={'role':'bad'})
    assert r.status_code==422


def test_last_admin_cannot_be_demoted(client, test_user, db):
    test_user.role='admin'; db.commit()
    r=client.patch(f'/api/v1/admin/users/{test_user.id}/role', json={'role':'viewer'})
    assert r.status_code==400


def test_admin_metrics_works(client, test_user, db):
    test_user.role='admin'; db.commit()
    r=client.get('/api/v1/admin/metrics')
    assert r.status_code==200
    assert 'total_users' in r.json()


def test_admin_can_retrieve_processing_summary(client, test_user, db):
    test_user.role = "admin"
    db.commit()
    r = client.get('/api/v1/admin/processing-summary')
    assert r.status_code == 200
    assert "pending" in r.json()


def test_non_admin_cannot_retrieve_processing_summary(client, test_user, db):
    test_user.role = "viewer"
    db.commit()
    r = client.get('/api/v1/admin/processing-summary')
    assert r.status_code == 403


def test_processing_summary_counts_are_accurate(client, test_user, db):
    test_user.role = "admin"
    db.commit()
    now = datetime.now(timezone.utc)
    docs = [
        Document(id=uuid.uuid4(), filename="p1.pdf", original_path="/tmp/p1.pdf", file_type="pdf", file_size=1, mime_type="application/pdf", processing_status="pending", source="upload", user_id=test_user.id),
        Document(id=uuid.uuid4(), filename="q1.pdf", original_path="/tmp/q1.pdf", file_type="pdf", file_size=1, mime_type="application/pdf", processing_status="queued", source="upload", user_id=test_user.id),
        Document(id=uuid.uuid4(), filename="pr1.pdf", original_path="/tmp/pr1.pdf", file_type="pdf", file_size=1, mime_type="application/pdf", processing_status="processing", source="upload", user_id=test_user.id),
        Document(id=uuid.uuid4(), filename="c1.pdf", original_path="/tmp/c1.pdf", file_type="pdf", file_size=1, mime_type="application/pdf", processing_status="completed", source="upload", user_id=test_user.id),
        Document(id=uuid.uuid4(), filename="f_recent.pdf", original_path="/tmp/f_recent.pdf", file_type="pdf", file_size=1, mime_type="application/pdf", processing_status="failed", source="upload", user_id=test_user.id, updated_at=now - timedelta(hours=2)),
        Document(id=uuid.uuid4(), filename="f_old.pdf", original_path="/tmp/f_old.pdf", file_type="pdf", file_size=1, mime_type="application/pdf", processing_status="failed", source="upload", user_id=test_user.id, updated_at=now - timedelta(days=3)),
    ]
    db.add_all(docs)
    db.commit()
    r = client.get('/api/v1/admin/processing-summary')
    assert r.status_code == 200
    payload = r.json()
    assert payload["pending"] == 2
    assert payload["processing"] == 1
    assert payload["completed"] == 1
    assert payload["failed"] == 2
    assert payload["recently_failed"] == 1


def test_non_admin_rejected_for_admin_subscriptions(client, test_user, db):
    test_user.role = "viewer"; db.commit()
    r = client.get("/api/v1/admin/subscriptions")
    assert r.status_code == 403


def test_admin_can_view_subscription(client, test_user, db):
    test_user.role = "admin"; db.commit()
    client.patch(f"/api/v1/admin/users/{test_user.id}/plan", json={"plan_slug": "free"})
    r = client.get("/api/v1/admin/subscriptions")
    assert r.status_code == 200
    assert any(item["user_id"] == str(test_user.id) for item in r.json())


def test_admin_can_update_plan_and_audit_created(client, test_user, db):
    test_user.role = "admin"; db.commit()
    target = User(id=uuid.uuid4(), email="subtarget@example.com", password_hash="x", display_name="SubTarget", is_active=True, role="viewer")
    db.add(target); db.commit()
    r = client.patch(f"/api/v1/admin/users/{target.id}/plan", json={"plan_slug": "pro"})
    assert r.status_code == 200
    assert r.json()["plan_slug"] == "pro"
    ev = db.query(AdminAuditEvent).filter(AdminAuditEvent.entity_id == str(target.id), AdminAuditEvent.action == "plan_updated").first()
    assert ev is not None


def test_admin_override_and_credits_affect_enforcement(client, test_user, db, monkeypatch):
    from app.services.limit_enforcement import enforce_limit
    from fastapi import HTTPException
    test_user.role = "admin"; db.commit()
    target = User(id=uuid.uuid4(), email="credits@example.com", password_hash="x", display_name="Credits", is_active=True, role="viewer")
    db.add(target); db.commit()
    # move to free, grant small override and credits
    client.patch(f"/api/v1/admin/users/{target.id}/plan", json={"plan_slug": "free"})
    rr = client.patch(f"/api/v1/admin/users/{target.id}/usage-controls", json={"usage_credits": {"documents_per_month": 3}, "limit_overrides": {"documents_per_month": 5}})
    assert rr.status_code == 200
    monkeypatch.setattr("app.services.limit_enforcement.get_usage_total", lambda *args, **kwargs: 7)
    enforce_limit(db, target.id, "documents_per_month", 1)  # adjusted by credits => 4, limit 5
    monkeypatch.setattr("app.services.limit_enforcement.get_usage_total", lambda *args, **kwargs: 9)
    try:
        enforce_limit(db, target.id, "documents_per_month", 1)  # adjusted => 6 > 5
        assert False, "expected limit"
    except HTTPException as exc:
        assert exc.status_code == 402


def test_admin_can_access_system_status(client, test_user, db):
    test_user.role = 'admin'
    db.commit()
    response = client.get('/api/v1/admin/system-status')
    assert response.status_code == 200


def test_non_admin_cannot_access_system_status(client, test_user, db):
    test_user.role = 'viewer'
    db.commit()
    response = client.get('/api/v1/admin/system-status')
    assert response.status_code == 403


def test_system_status_response_shape_and_no_secrets(client, test_user, db, monkeypatch):
    from app.config import settings

    test_user.role = 'admin'
    db.commit()
    monkeypatch.setattr(settings, 'APP_ENV', 'staging')
    monkeypatch.setattr(settings, 'STRIPE_SECRET_KEY', 'sk_test_123')
    monkeypatch.setattr(settings, 'STRIPE_PRICE_PRO_MONTHLY', 'price_pro')
    monkeypatch.setattr(settings, 'STRIPE_PRICE_TEAM_MONTHLY', 'price_team')

    response = client.get('/api/v1/admin/system-status')
    assert response.status_code == 200
    payload = response.json()
    assert payload['billing_configured'] is True
    assert payload['stripe_configured'] is True
    assert payload['stripe_prices_configured'] is True
    assert payload['environment'] == 'staging'
    assert 'features' in payload
    assert 'insights_enabled' in payload['features']
    assert 'category_intelligence_enabled' in payload['features']
    assert 'relationship_detection_enabled' in payload['features']
    assert 'stripe_secret_key' not in payload
    assert 'sk_test_123' not in str(payload)


def test_admin_can_access_llm_models(client, test_user, db):
    test_user.role = "admin"
    db.commit()
    response = client.get("/api/v1/admin/llm-models")
    assert response.status_code == 200


def test_non_admin_cannot_access_llm_models(client, test_user, db):
    test_user.role = "viewer"
    db.commit()
    response = client.get("/api/v1/admin/llm-models")
    assert response.status_code == 403


def test_llm_models_contains_openai_and_gemini_and_safe_config(client, test_user, db, monkeypatch):
    from app.config import settings

    test_user.role = "admin"
    db.commit()
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test-openai")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")

    response = client.get("/api/v1/admin/llm-models")
    assert response.status_code == 200
    payload = response.json()
    provider_ids = {provider["id"] for provider in payload["providers"]}
    assert "openai" in provider_ids
    assert "gemini" in provider_ids

    openai = next(provider for provider in payload["providers"] if provider["id"] == "openai")
    gemini = next(provider for provider in payload["providers"] if provider["id"] == "gemini")
    assert openai["configured"] is True
    assert gemini["configured"] is False
    assert "gpt-4.1" in {model["id"] for model in openai["models"]}
    assert "gemini-1.5-pro" in {model["id"] for model in gemini["models"]}
    assert "OPENAI_API_KEY" not in str(payload)
    assert "GEMINI_API_KEY" not in str(payload)
    assert "sk-test-openai" not in str(payload)

def test_admin_can_list_prompt_execution_logs(client, test_user, db):
    from app.models.prompt_execution_log import PromptExecutionLog
    test_user.role='admin'; db.commit()
    db.add(PromptExecutionLog(provider='openai', model='gpt-4o-mini', fallback_used=False, success=True, source='x'))
    db.commit()
    r = client.get('/api/v1/admin/prompt-executions')
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_non_admin_cannot_list_prompt_execution_logs(client, test_user, db):
    test_user.role='viewer'; db.commit()
    r = client.get('/api/v1/admin/prompt-executions')
    assert r.status_code == 403



def test_prompt_execution_summary_includes_costs(client, test_user, db):
    from app.models.prompt_execution_log import PromptExecutionLog

    test_user.role = 'admin'
    db.commit()
    db.add(PromptExecutionLog(provider='openai', model='gpt-4o-mini', fallback_used=False, success=True, source='x', pricing_known=True, estimated_cost_usd=0.123456, currency='USD'))
    db.add(PromptExecutionLog(provider='openai', model='unknown', fallback_used=False, success=False, source='x', pricing_known=False, estimated_cost_usd=None, currency='USD'))
    db.commit()

    r = client.get('/api/v1/admin/prompt-executions/summary')
    assert r.status_code == 200
    payload = r.json()
    assert 'total_estimated_cost_usd' in payload
    assert payload['pricing_unknown_count'] >= 1


def test_prompt_execution_summary_breakdowns_and_filters(client, test_user, db):
    from app.models.prompt_execution_log import PromptExecutionLog

    test_user.role = 'admin'
    db.commit()
    db.add(PromptExecutionLog(provider='openai', model='gpt-4o-mini', fallback_used=True, success=False, source='audit', pricing_known=True, estimated_cost_usd=0.5, total_tokens=50))
    db.add(PromptExecutionLog(provider='gemini', model='gemini-1.5-pro', fallback_used=False, success=True, source='job', pricing_known=True, estimated_cost_usd=0.25, total_tokens=25))
    db.commit()

    r = client.get('/api/v1/admin/prompt-executions/summary', params={'provider': 'openai'})
    assert r.status_code == 200
    payload = r.json()
    assert payload['total_calls'] == 1
    assert payload['calls_by_source']['audit'] == 1
    assert payload['failures_by_provider']['openai'] == 1
    assert payload['fallback_by_provider']['openai'] == 1


def test_prompt_execution_summary_empty_safe_values(client, test_user, db):
    test_user.role = 'admin'
    db.commit()
    r = client.get('/api/v1/admin/prompt-executions/summary')
    assert r.status_code == 200
    payload = r.json()
    assert payload['total_calls'] == 0
    assert payload['success_rate'] == 0
    assert payload['fallback_rate'] == 0
    assert payload['total_tokens'] == 0
    assert payload['total_estimated_cost_usd'] == 0


def test_non_admin_cannot_access_prompt_execution_summary(client, test_user, db):
    test_user.role = 'viewer'
    db.commit()
    r = client.get('/api/v1/admin/prompt-executions/summary')
    assert r.status_code == 403


def test_non_admin_cannot_manage_users(client, test_user, db):
    target = User(id=uuid.uuid4(), email='deny-target@example.com', password_hash='x', display_name='Deny', is_active=True, role='viewer')
    db.add(target); db.commit()
    test_user.role = 'viewer'; db.commit()
    assert client.post('/api/v1/admin/users', json={'email': 'x@example.com', 'password': 'password123', 'role': 'viewer', 'display_name': 'X'}).status_code == 403
    assert client.post('/api/v1/admin/users/invite', json={'email': 'invite-deny@example.com', 'role': 'viewer', 'expires_in_days': 7}).status_code == 403
    assert client.patch(f'/api/v1/admin/users/{target.id}/role', json={'role': 'editor'}).status_code == 403
    assert client.post(f'/api/v1/admin/users/{target.id}/deactivate').status_code == 403
    assert client.request('DELETE', f'/api/v1/admin/users/{target.id}', json={'confirmation': 'DELETE'}).status_code == 403


def test_admin_create_user_creates_default_subscription(client, test_user, db):
    from app.models.billing import Subscription
    test_user.role = 'admin'; db.commit()
    r = client.post('/api/v1/admin/users', json={'email': 'new-admin-create@example.com', 'password': 'password123', 'role': 'viewer', 'display_name': 'New User'})
    assert r.status_code == 201
    created_id = r.json()['id']
    sub = db.query(Subscription).filter(Subscription.user_id == created_id).first()
    assert sub is not None


def test_admin_cannot_delete_self(client, test_user, db):
    test_user.role = 'admin'; db.commit()
    r = client.request('DELETE', f'/api/v1/admin/users/{test_user.id}', json={'confirmation': 'DELETE'})
    assert r.status_code == 400


def test_admin_cannot_remove_last_admin(client, test_user, db):
    test_user.role = 'admin'; db.commit()
    assert client.post(f'/api/v1/admin/users/{test_user.id}/deactivate').status_code == 400
    assert client.request('DELETE', f'/api/v1/admin/users/{test_user.id}', json={'confirmation': 'DELETE'}).status_code == 400


def test_invite_token_is_hashed_not_plaintext(client, test_user, db):
    from app.models.user import UserInvite
    import hashlib
    test_user.role = 'admin'; db.commit()
    r = client.post('/api/v1/admin/users/invite', json={'email': 'hashcheck@example.com', 'role': 'viewer', 'expires_in_days': 7})
    assert r.status_code == 200
    token = r.json()['invite_link'].split('token=')[1]
    invite = db.query(UserInvite).filter(UserInvite.email == 'hashcheck@example.com').first()
    assert invite is not None
    assert invite.token_hash != token
    assert invite.token_hash == hashlib.sha256(token.encode('utf-8')).hexdigest()


def test_invite_resend_rotates_hash_and_cancel_marks_canceled_at(client, test_user, db):
    from app.models.user import UserInvite
    test_user.role = 'admin'; db.commit()
    created = client.post('/api/v1/admin/users/invite', json={'email': 'rotate@example.com', 'role': 'viewer', 'expires_in_days': 7})
    invite_id = created.json()['id']
    invite = db.query(UserInvite).filter(UserInvite.id == invite_id).first()
    old_hash = invite.token_hash
    resent = client.post(f'/api/v1/admin/users/invites/{invite_id}/resend')
    assert resent.status_code == 200
    db.refresh(invite)
    assert invite.token_hash != old_hash
    canceled = client.post(f'/api/v1/admin/users/invites/{invite_id}/cancel')
    assert canceled.status_code == 200
    db.refresh(invite)
    assert invite.canceled_at is not None


def test_role_deactivate_reactivate_delete_are_audited(client, test_user, db):
    test_user.role = 'admin'; db.commit()
    target = User(id=uuid.uuid4(), email='audited@example.com', password_hash='x', display_name='Audited', is_active=True, role='viewer')
    db.add(target); db.commit()
    assert client.patch(f'/api/v1/admin/users/{target.id}/role', json={'role': 'editor'}).status_code == 200
    assert client.post(f'/api/v1/admin/users/{target.id}/deactivate').status_code == 200
    assert client.post(f'/api/v1/admin/users/{target.id}/reactivate').status_code == 200
    assert client.request('DELETE', f'/api/v1/admin/users/{target.id}', json={'confirmation': 'DELETE'}).status_code == 200
    actions = {e.action for e in db.query(AdminAuditEvent).filter(AdminAuditEvent.entity_id == str(target.id)).all()}
    assert 'role_updated' in actions
    assert 'deactivated' in actions
    assert 'reactivated' in actions
    assert 'soft_deleted' in actions
