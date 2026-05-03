from app.models.admin_audit import AdminAuditEvent
from app.models.email import EmailCampaignRecipient, EmailSendLog, EmailSuppression, EmailTemplate
from app.models.user import User
from fastapi import HTTPException


def _template(db, status='active'):
    t = EmailTemplate(name=f'T-{status}', slug=f'e4-{status}', category='campaign', status=status, subject='Hello', html_body='<p>Hi</p>', text_body='Hi', variables_json={})
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def _campaign(client, template_id: str, **overrides):
    payload = {'name': 'C1', 'template_id': template_id, 'audience_type': 'manual_list', 'status': 'ready', 'audience_filters_json': {'emails': ['a@example.com']}}
    payload.update(overrides)
    r = client.post('/api/v1/admin/email/campaigns', json=payload)
    assert r.status_code == 201
    return r.json()['id']


def test_non_admin_blocked(client):
    assert client.get('/api/v1/admin/email/suppressions').status_code == 403


def test_suppression_crud_and_send_controls(client, test_user, db):
    test_user.role = 'admin'; db.commit()
    h = {}
    r = client.post('/api/v1/admin/email/suppressions', headers=h, json={'email': 'X@Example.com', 'reason': 'manual'})
    assert r.status_code == 201 and r.json()['email'] == 'x@example.com'
    assert client.get('/api/v1/admin/email/suppressions', headers=h).status_code == 200
    assert client.delete('/api/v1/admin/email/suppressions/x@example.com', headers=h).status_code == 200


def test_campaign_send_safety_and_tracking(client, test_user, db, monkeypatch):
    test_user.role = 'admin'; db.commit()
    extra = User(email='other@example.com', password_hash='x', display_name='o', is_active=True, role='viewer')
    db.add(extra); db.commit(); db.refresh(extra)
    t = _template(db, 'active')

    sent_to = []
    def fake_send(self, **kwargs):
        sent_to.append(kwargs['to_email'])
        if kwargs['to_email'] == 'fail@example.com':
            raise HTTPException(status_code=502, detail='Provider failed with key=SECRET_TOKEN')
        return {'status': 'sent', 'provider': 'default', 'log_id': 'log123'}
    monkeypatch.setattr('app.api.v1.admin.EmailDeliveryService.send_email', fake_send)

    cid = _campaign(client, str(t.id), audience_filters_json={'emails': ['a@example.com', 'A@example.com', 'bad', 'fail@example.com']})
    db.add(EmailSuppression(email='a@example.com', reason='manual'))
    db.commit()
    preview = client.post(f'/api/v1/admin/email/campaigns/{cid}/recipients/preview', json={})
    assert preview.status_code == 200
    p = preview.json()
    assert p['total_candidates'] == 4 and p['suppressed_count'] == 1 and p['invalid_count'] == 1 and p['duplicate_count'] == 1 and p['sendable_count'] == 1
    assert sent_to == []

    bad_confirm = client.post(f'/api/v1/admin/email/campaigns/{cid}/send', json={'confirmation_text': 'send campaign'})
    assert bad_confirm.status_code == 400

    ok = client.post(f'/api/v1/admin/email/campaigns/{cid}/send', json={'confirmation_text': 'SEND CAMPAIGN'})
    assert ok.status_code == 200
    assert sent_to == ['fail@example.com']
    rows = db.query(EmailCampaignRecipient).filter(EmailCampaignRecipient.campaign_id == cid).all()
    assert len(rows) == 3
    reasons = {(r.email, r.status, r.skip_reason) for r in rows if r.skip_reason}
    assert ('a@example.com', 'skipped', 'suppressed') in reasons and ('bad', 'skipped', 'invalid') in reasons
    failed = [r for r in rows if r.email == 'fail@example.com'][0]
    assert failed.status == 'failed'
    assert db.query(EmailSendLog).filter(EmailSendLog.campaign_id == cid, EmailSendLog.template_id == t.id).count() == 0
    assert db.query(AdminAuditEvent).filter(AdminAuditEvent.action == 'email_campaign_send_started').count() == 1


def test_campaign_send_validations_and_limits(client, test_user, db):
    test_user.role = 'admin'; db.commit()
    active_t = _template(db, 'active')

    not_ready = _campaign(client, str(active_t.id), status='draft')
    assert client.post(f'/api/v1/admin/email/campaigns/{not_ready}/send', json={'confirmation_text': 'SEND CAMPAIGN'}).status_code == 400

    archived_campaign = _campaign(client, str(active_t.id), status='ready')
    db.query(EmailTemplate).filter(EmailTemplate.id == active_t.id).update({'status': 'archived'})
    db.commit()
    assert client.post(f'/api/v1/admin/email/campaigns/{archived_campaign}/send', json={'confirmation_text': 'SEND CAMPAIGN'}).status_code == 400
    db.query(EmailTemplate).filter(EmailTemplate.id == active_t.id).update({'status': 'active'})
    db.commit()

    zero = _campaign(client, str(active_t.id), audience_filters_json={'emails': ['bad-email']})
    assert client.post(f'/api/v1/admin/email/campaigns/{zero}/send', json={'confirmation_text': 'SEND CAMPAIGN'}).status_code == 400

    over = _campaign(client, str(active_t.id), audience_filters_json={'emails': [f'u{i}@example.com' for i in range(26)]})
    assert client.post(f'/api/v1/admin/email/campaigns/{over}/send', json={'confirmation_text': 'SEND CAMPAIGN'}).status_code == 400

    all_users = _campaign(client, str(active_t.id), audience_type='all_users', audience_filters_json=None)
    db.add(EmailSuppression(email='test@example.com', reason='manual')); db.commit()
    p = client.post(f'/api/v1/admin/email/campaigns/{all_users}/recipients/preview', json={}).json()
    assert p['suppressed_count'] >= 1
