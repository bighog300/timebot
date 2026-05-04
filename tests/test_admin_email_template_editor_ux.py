from app.models.email import EmailTemplate


def _admin(test_user, db):
    test_user.role = 'admin'; db.commit()


def test_template_preview_detects_and_missing_vars(client, test_user, db):
    _admin(test_user, db)
    r = client.post('/api/v1/admin/email/templates/preview', json={
        'subject': 'Hi {{first_name}}', 'preheader': 'For {{company}}', 'html_body': '<p>{{first_name}} {{cta_url}}</p>', 'text_body': 'txt {{missing}}', 'variables_json': {'first_name': 'Ada'}
    })
    assert r.status_code == 200
    body = r.json()
    assert set(body['detected_variables']) == {'first_name', 'company', 'cta_url', 'missing'}
    assert set(body['missing_variables']) == {'company', 'cta_url', 'missing'}


def test_duplicate_template(client, test_user, db):
    _admin(test_user, db)
    t = EmailTemplate(name='A', slug='slug-a', category='transactional', status='active', subject='S', html_body='H', text_body='T', variables_json={})
    db.add(t); db.commit(); db.refresh(t)
    r = client.post(f'/api/v1/admin/email/templates/{t.id}/duplicate')
    assert r.status_code == 201
    assert r.json()['slug'].startswith('slug-a-copy')


def test_template_test_send(client, test_user, db, monkeypatch):
    _admin(test_user, db)
    monkeypatch.setattr('app.services.email_delivery.EmailDeliveryService.send_email', lambda *a, **k: {'status': 'sent', 'provider': 'resend', 'provider_message_id': 'x', 'log_id': '1'})
    r = client.post('/api/v1/admin/email/templates/test-send', json={'to_email':'x@example.com','subject':'Hello {{n}}','html_body':'<p>{{n}}</p>','text_body':'{{n}}','variables_json':{'n':'Test'}})
    assert r.status_code == 200
    assert r.json()['status'] == 'sent'


def test_invalid_variables_json_on_create(client, test_user, db):
    _admin(test_user, db)
    r = client.post('/api/v1/admin/email/templates', json={'name':'x','slug':'x1','category':'transactional','status':'draft','subject':'s','html_body':'h','text_body':'t','variables_json':'bad'})
    assert r.status_code == 422
