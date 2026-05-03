from app.models.admin_audit import AdminAuditEvent
from app.models.email import EmailTemplate, EmailCampaign, EmailSendLog, EmailProviderConfig
from app.services.email_secrets import email_secret_crypto


def _template(db, status='draft'):
    t=EmailTemplate(name='T',slug='t1'+status,category='campaign',status=status,subject='Hello {{ name }}',html_body='<p>{{ name }}</p>',text_body='{{ name }}',variables_json={'name':'Friend'})
    db.add(t); db.commit(); db.refresh(t); return t


def _cfg(db):
    c=EmailProviderConfig(provider='resend',enabled=True,from_email='noreply@example.com',api_key_encrypted=email_secret_crypto.encrypt('k'))
    db.add(c); db.commit()


def test_campaign_admin_controls_and_preview_and_testsend(client,test_user,db,monkeypatch):
    t=_template(db)
    test_user.role='viewer'; db.commit(); assert client.get('/api/v1/admin/email/campaigns').status_code==403
    test_user.role='admin'; db.commit()
    c=client.post('/api/v1/admin/email/campaigns',json={'name':'C1','template_id':str(t.id),'audience_type':'all_users','variables_json':{'name':'Ada'}}); assert c.status_code==201
    cid=c.json()['id']
    p=client.post(f'/api/v1/admin/email/campaigns/{cid}/preview',json={}); assert p.status_code==200 and 'Ada' in p.json()['html_body']
    miss=client.post(f'/api/v1/admin/email/campaigns/{cid}/preview',json={'variables_json':{'name':None}}); assert 'name' in miss.json()['missing_variables']
    bad=client.patch(f'/api/v1/admin/email/campaigns/{cid}',json={'status':'archived'}); assert bad.status_code==200
    ro=client.patch(f'/api/v1/admin/email/campaigns/{cid}',json={'name':'x'}); assert ro.status_code==400
    restore=client.patch(f'/api/v1/admin/email/campaigns/{cid}',json={'status':'draft'}); assert restore.status_code==200
    _cfg(db)
    import app.services.email_delivery as d
    class R:
        status_code=200
        headers={}
        text=''
        def json(self):
            return {'id':'msg1'}
    def post(*a,**k): return R()
    monkeypatch.setattr(d.requests,'post',post)
    r=client.post(f'/api/v1/admin/email/campaigns/{cid}/test-send',json={'to_email':'a@b.com'})
    assert r.status_code==200
    log=db.query(EmailSendLog).order_by(EmailSendLog.created_at.desc()).first(); assert str(log.campaign_id)==cid and str(log.template_id)==str(t.id)
    ev=db.query(AdminAuditEvent).filter(AdminAuditEvent.action=='email_campaign_test_send').first(); assert ev is not None


def test_cannot_create_campaign_with_archived_template(client,test_user,db):
    test_user.role='admin'; db.commit(); t=_template(db,'archived')
    c=client.post('/api/v1/admin/email/campaigns',json={'name':'C1','template_id':str(t.id),'audience_type':'all_users'})
    assert c.status_code==400
