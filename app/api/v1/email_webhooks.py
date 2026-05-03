import hashlib, hmac, json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.models.email import EmailProviderConfig, EmailProviderEvent, EmailSendLog, EmailCampaignRecipient, EmailSuppression
from app.services.email_delivery import sanitize_provider_error
from app.services.email_secrets import email_secret_crypto

router=APIRouter(prefix='/email/webhooks', tags=['email-webhooks'])

def _safe_payload(payload: dict) -> dict:
    redacted={}
    for k,v in payload.items():
        if 'signature' in k.lower() or 'authorization' in k.lower() or 'secret' in k.lower() or 'api' in k.lower():
            continue
        redacted[k]=v
    return redacted

def _verify(provider:str, raw:bytes, sig:str|None, cfg:EmailProviderConfig):
    if not cfg or not cfg.webhook_secret_encrypted:
        raise HTTPException(status_code=401, detail='Webhook secret not configured')
    secret=email_secret_crypto.decrypt(cfg.webhook_secret_encrypted)
    if not sig:
        raise HTTPException(status_code=401, detail='Missing webhook signature')
    # Current E5 webhook signature contract for both providers:
    # header value must equal hex(HMAC_SHA256(raw_request_body, webhook_secret)).
    digest=hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, sig.strip()):
        raise HTTPException(status_code=401, detail='Invalid webhook signature')

def _apply_status(db, send_log, status, event_id):
    now=datetime.now(timezone.utc)
    if status in ('delivered','bounced','complained','failed'):
        send_log.status='failed' if status in ('bounced','complained','failed') else 'sent'
    r=db.query(EmailCampaignRecipient).filter(EmailCampaignRecipient.send_log_id==send_log.id).first()
    if r:
        r.status=status
        r.provider_event_id=event_id
        r.last_event_at=now
        if status=='delivered': r.delivered_at=now
        elif status=='bounced': r.bounced_at=now
        elif status=='complained': r.complained_at=now
        elif status=='failed': r.failed_at=now
    if status in ('bounced','complained'):
        email=send_log.recipient_email.lower().strip()
        if not db.query(EmailSuppression).filter(EmailSuppression.email==email).first():
            db.add(EmailSuppression(email=email,reason='bounce' if status=='bounced' else 'complaint',source='provider_webhook'))

@router.post('/resend')
async def resend_webhook(request:Request, x_signature:str|None=Header(default=None), db:Session=Depends(get_db)):
    raw=await request.body(); payload=await request.json()
    cfg=db.query(EmailProviderConfig).filter(EmailProviderConfig.provider=='resend').first()
    _verify('resend',raw,x_signature,cfg)
    events=payload if isinstance(payload,list) else [payload]
    for ev in events:
        event_id=str(ev.get('id') or '') or None
        if event_id and db.query(EmailProviderEvent).filter(EmailProviderEvent.provider=='resend', EmailProviderEvent.provider_event_id==event_id).first():
            continue
        msg_id=ev.get('data',{}).get('email_id') or ev.get('email_id')
        et=ev.get('type','unknown')
        rec=ev.get('data',{}).get('to')
        send_log=db.query(EmailSendLog).filter(EmailSendLog.provider_message_id==msg_id).first() if msg_id else None
        status_map={'email.delivered':'delivered','email.bounced':'bounced','email.complained':'complained','email.failed':'failed'}
        mapped=status_map.get(et)
        pe=EmailProviderEvent(provider='resend',event_type=et,provider_event_id=event_id,provider_message_id=msg_id,recipient_email=rec,campaign_id=(send_log.campaign_id if send_log else None),send_log_id=(send_log.id if send_log else None),payload_json_sanitized=_safe_payload(ev))
        db.add(pe)
        if send_log and mapped: _apply_status(db, send_log, mapped, event_id)
    db.commit(); return {'ok':True}

@router.post('/sendgrid')
async def sendgrid_webhook(request:Request, x_twilio_email_event_webhook_signature:str|None=Header(default=None), db:Session=Depends(get_db)):
    raw=await request.body(); events=await request.json()
    cfg=db.query(EmailProviderConfig).filter(EmailProviderConfig.provider=='sendgrid').first()
    _verify('sendgrid',raw,x_twilio_email_event_webhook_signature,cfg)
    if not isinstance(events,list): events=[events]
    for ev in events:
        event_id=str(ev.get('sg_event_id') or '') or None
        if event_id and db.query(EmailProviderEvent).filter(EmailProviderEvent.provider=='sendgrid', EmailProviderEvent.provider_event_id==event_id).first():
            continue
        msg_id=ev.get('sg_message_id') or ev.get('smtp-id')
        et=ev.get('event','unknown'); rec=ev.get('email')
        send_log=db.query(EmailSendLog).filter(EmailSendLog.provider_message_id==msg_id).first() if msg_id else None
        status_map={'delivered':'delivered','bounce':'bounced','dropped':'bounced','spamreport':'complained','deferred':'failed','processed':'sent'}
        mapped=status_map.get(et)
        pe=EmailProviderEvent(provider='sendgrid',event_type=et,provider_event_id=event_id,provider_message_id=msg_id,recipient_email=rec,campaign_id=(send_log.campaign_id if send_log else None),send_log_id=(send_log.id if send_log else None),payload_json_sanitized=_safe_payload(ev))
        db.add(pe)
        if send_log and mapped in ('delivered','bounced','complained','failed'): _apply_status(db, send_log, mapped, event_id)
    db.commit(); return {'ok':True}
