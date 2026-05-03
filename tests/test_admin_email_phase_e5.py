import hashlib,hmac,json
from app.models.email import EmailCampaignRecipient, EmailProviderConfig, EmailSendLog, EmailSuppression, EmailTemplate
from app.services.email_secrets import email_secret_crypto


def _template(db):
    t=EmailTemplate(name='T',slug='e5',category='campaign',status='active',subject='Hello',html_body='<p>Hi</p>',text_body='Hi',variables_json={})
    db.add(t); db.commit(); db.refresh(t); return t

def _campaign(client, template_id, emails):
    r=client.post('/api/v1/admin/email/campaigns',json={'name':'C','template_id':template_id,'audience_type':'manual_list','status':'ready','audience_filters_json':{'emails':emails}})
    return r.json()['id']

def test_send_queues_without_sync_send(client,test_user,db,monkeypatch):
    test_user.role='admin'; db.commit(); t=_template(db)
    called=[]
    monkeypatch.setattr('app.services.email_delivery.EmailDeliveryService.send_email', lambda *a,**k: called.append(1))
    monkeypatch.setattr('app.api.v1.admin.enqueue_campaign_recipient_send', lambda rid: True)
    cid=_campaign(client,str(t.id),['a@example.com'])
    r=client.post(f'/api/v1/admin/email/campaigns/{cid}/send',json={'confirmation_text':'SEND CAMPAIGN'})
    assert r.status_code==200 and called==[]

def test_enqueue_failure_not_reported_as_queued(client,test_user,db,monkeypatch):
    test_user.role='admin'; db.commit(); t=_template(db)
    monkeypatch.setattr('app.api.v1.admin.enqueue_campaign_recipient_send', lambda rid: (_ for _ in ()).throw(RuntimeError('boom')))
    cid=_campaign(client,str(t.id),['a@example.com'])
    r=client.post(f'/api/v1/admin/email/campaigns/{cid}/send',json={'confirmation_text':'SEND CAMPAIGN'})
    assert r.status_code==503

def test_webhook_signature_required_and_valid(client,test_user,db):
    test_user.role='admin'; db.commit()
    secret='whsec123'
    cfg=db.query(EmailProviderConfig).filter(EmailProviderConfig.provider=='resend').first()
    if not cfg:
        cfg=EmailProviderConfig(provider='resend',enabled=True,from_email='x@example.com',api_key_encrypted='k',webhook_secret_encrypted=email_secret_crypto.encrypt(secret))
        db.add(cfg)
    else:
        cfg.webhook_secret_encrypted=email_secret_crypto.encrypt(secret)
    db.commit()
    payload=[{'id':'e1','type':'email.bounced','data':{'email_id':'m1','to':'a@example.com'}}]
    raw=json.dumps(payload, separators=(',', ':')).encode()
    bad=client.post('/api/v1/email/webhooks/resend',content=raw,headers={'content-type':'application/json'})
    assert bad.status_code==401 and bad.json()['detail']=='Missing webhook signature'
    db.add(EmailSendLog(provider='resend',recipient_email='a@example.com',from_email='x@example.com',subject='s',status='sent',provider_message_id='m1')); db.commit()
    sig=hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    ok=client.post('/api/v1/email/webhooks/resend',content=raw,headers={'content-type':'application/json','x-signature':sig})
    assert ok.status_code==200
    assert db.query(EmailSuppression).filter(EmailSuppression.email=='a@example.com').count()==1

    invalid=client.post('/api/v1/email/webhooks/resend',content=raw,headers={'content-type':'application/json','x-signature':'bad-signature'})
    assert invalid.status_code==401 and invalid.json()['detail']=='Invalid webhook signature'
