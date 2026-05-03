from app.models.admin_audit import AdminAuditEvent
from app.models.email import EmailProviderConfig, EmailSendLog
from app.services.email_secrets import email_secret_crypto


def _cfg(db, provider='resend', enabled=True, key='k'):
    c=EmailProviderConfig(provider=provider,enabled=enabled,from_email='noreply@example.com',api_key_encrypted=email_secret_crypto.encrypt(key))
    db.add(c); db.commit(); return c

def test_non_admin_cannot_test_send(client,test_user,db):
    test_user.role='viewer'; db.commit()
    assert client.post('/api/v1/admin/email/test-send',json={'to_email':'a@b.com'}).status_code==403

def test_test_send_missing_config(client,test_user,db):
    test_user.role='admin'; db.commit()
    r=client.post('/api/v1/admin/email/test-send',json={'to_email':'a@b.com'})
    assert r.status_code==400

def test_test_send_disabled_provider(client,test_user,db):
    test_user.role='admin'; db.commit(); _cfg(db,'resend',False)
    r=client.post('/api/v1/admin/email/test-send',json={'provider':'resend','to_email':'a@b.com'})
    assert r.status_code==400

def test_send_log_admin_only(client,test_user,db):
    test_user.role='viewer'; db.commit(); assert client.get('/api/v1/admin/email/send-logs').status_code==403

def test_test_send_failed_logs_and_sanitized(client,test_user,db,monkeypatch):
    test_user.role='admin'; db.commit(); _cfg(db,'resend',True,'secret')
    import app.services.email_delivery as d
    class R: status_code=500; text='authorization: Bearer secret';
    monkeypatch.setattr(d.requests,'post',lambda *a,**k:R())
    r=client.post('/api/v1/admin/email/test-send',json={'provider':'resend','to_email':'a@b.com'})
    assert r.status_code==502
    log=db.query(EmailSendLog).order_by(EmailSendLog.created_at.desc()).first(); assert log.status=='failed'; assert 'secret' not in (log.error_message_sanitized or '')

def test_test_send_success_and_audit(client,test_user,db,monkeypatch):
    test_user.role='admin'; db.commit(); _cfg(db,'sendgrid',True,'k')
    import app.services.email_delivery as d
    class R: status_code=202; headers={'X-Message-Id':'mid1'};
    monkeypatch.setattr(d.requests,'post',lambda *a,**k:R())
    r=client.post('/api/v1/admin/email/test-send',json={'provider':'sendgrid','to_email':'a@b.com'})
    assert r.status_code==200 and r.json()['status']=='sent'
    log=db.query(EmailSendLog).order_by(EmailSendLog.created_at.desc()).first(); assert log.status=='sent'
    ev=db.query(AdminAuditEvent).filter(AdminAuditEvent.entity_type=='email_test_send').first(); assert ev is not None
