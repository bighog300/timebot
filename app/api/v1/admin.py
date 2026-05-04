from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_current_user_role
from app.models.admin_audit import AdminAuditEvent
from app.models.document import Document
from app.models.intelligence import DocumentActionItem, DocumentRelationshipReview, DocumentReviewItem
from app.models.prompt_execution_log import PromptExecutionLog
from app.models.relationships import ProcessingQueue
from app.models.user import User, UserInvite
from app.models.billing import Plan, Subscription
from app.models.processing_event import DocumentProcessingEvent

from app.models.chat import ChatbotSettings
from app.models.email import EmailProviderConfig, EmailTemplate, EmailCampaign, EmailSendLog, EmailSuppression, EmailCampaignRecipient
from app.models.prompt_template import PromptTemplate
from app.schemas.chatbot import ChatbotSettingsPayload, ChatbotSettingsResponse
from app.config import settings
from app.schemas.admin import (
    AdminAuditEventResponse,
    AdminAuditPageResponse,
    AdminMetricsResponse,
    AdminProcessingSummaryResponse,
    AdminRoleUpdateRequest,
    AdminUserCreateRequest,
    AdminDeleteUserRequest,
    AdminInviteCreateRequest,
    AdminInviteResponse,
    AdminSubscriptionResponse,
    AdminUsageSummaryResponse,
    AdminPlanUpdateRequest,
    AdminPlanResponse,
    AdminPlanPatchRequest,
    AdminUsageOverrideRequest,
    AdminCancelDowngradeRequest,
    AdminUserResponse,
    AdminUsersPageResponse,
    EmailProviderConfigResponse,
    EmailProviderConfigPatchRequest,
    EmailTemplateCreateRequest,
    EmailTemplatePatchRequest,
    EmailTemplateResponse,
    EmailCampaignCreateRequest,
    EmailCampaignPatchRequest,
    EmailCampaignResponse,
    EmailCampaignPreviewRequest,
    EmailCampaignPreviewResponse,
    EmailCampaignRecipientPreviewResponse,
    EmailCampaignSendRequest,
    EmailCampaignSendResponse,
    EmailSuppressionCreateRequest,
    EmailSuppressionResponse,
    EmailCampaignTestSendRequest,
    AdminEmailTestSendRequest,
    AdminEmailTestSendResponse,
    EmailSendLogResponse,
    ProcessingEventResponse,
    AdminSystemStatusFeaturesResponse,
    AdminSystemStatusResponse,
    AdminLlmModelsResponse,
    AdminSystemHealthResponse,
    AdminSystemJobsResponse,
    AdminLlmMetricsResponse,
    SystemComponentStatus,
    LlmProviderCatalogResponse,
    LlmModelOptionResponse,
)
from app.services.limit_enforcement import _current_period_window
from app.services.subscriptions import ensure_default_free_subscription, seed_default_plans
from app.services.auth import auth_service
from app.services.usage import get_usage_summary
from app.schemas.prompt_template import (
    PromptTemplateCreate,
    PromptTemplateResponse,
    PromptTemplateTestRequest,
    PromptTemplateTestResponse,
    PromptTemplateUpdate,
    PromptExecutionLogResponse,
    PromptExecutionSummaryResponse,
)
from app.services.openai_client import APIError, openai_client_service
from app.services.prompt_templates import activate_prompt_template, clear_default_for_purpose, run_prompt_with_fallback, list_prompt_executions, summarize_prompt_executions
from app.prompts.document_analysis import DOCUMENT_ANALYSIS_SYSTEM
from app.services.error_sanitizer import sanitize_processing_error
from app.services.email_secrets import email_secret_crypto
from app.workers.tasks import enqueue_campaign_recipient_send
from app.services.email_delivery import EmailDeliveryService

router = APIRouter(prefix="/admin", tags=["admin"])

_LLM_PROVIDER_CATALOG: list[dict[str, object]] = [
    {
        "id": "openai",
        "name": "OpenAI",
        "models": [
            {"id": "gpt-4.1", "name": "GPT-4.1"},
            {"id": "gpt-4.1-mini", "name": "GPT-4.1 Mini"},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
        ],
    },
    {
        "id": "gemini",
        "name": "Gemini",
        "models": [
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro"},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash"},
        ],
    },
]




def _supported_models_by_provider() -> dict[str, set[str]]:
    return {str(provider["id"]): {str(model["id"]) for model in provider["models"]} for provider in _LLM_PROVIDER_CATALOG}


def _validate_provider_model(provider: str, model: str) -> None:
    catalog = _supported_models_by_provider()
    if provider not in catalog:
        raise HTTPException(status_code=422, detail="Unsupported provider")
    if model not in catalog[provider]:
        raise HTTPException(status_code=422, detail="Unsupported model for provider")


def _validate_fallback_payload(primary_provider: str, primary_model: str, fallback_enabled: bool, fallback_provider: str | None, fallback_model: str | None) -> None:
    _validate_provider_model(primary_provider, primary_model)
    if not fallback_enabled:
        return
    if not fallback_provider or not fallback_model:
        raise HTTPException(status_code=422, detail="fallback_provider and fallback_model are required when fallback_enabled is true")
    _validate_provider_model(fallback_provider, fallback_model)

def _audit_admin_monetization_action(db: Session, *, current_user: User, target_user: User, action: str, details: dict) -> None:
    db.add(
        AdminAuditEvent(
            actor_id=current_user.id,
            entity_type="subscription",
            entity_id=str(target_user.id),
            action=action,
            details={"target_email": target_user.email, **details},
        )
    )


def require_admin(role: str = Depends(get_current_user_role)) -> str:
    if role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return role




def _safe_email_provider_response(cfg: EmailProviderConfig) -> EmailProviderConfigResponse:
    return EmailProviderConfigResponse(
        provider=cfg.provider,
        enabled=cfg.enabled,
        from_email=cfg.from_email,
        from_name=cfg.from_name,
        reply_to=cfg.reply_to,
        configured=bool(cfg.api_key_encrypted),
        webhook_configured=bool(cfg.webhook_secret_encrypted),
        created_at=cfg.created_at,
        updated_at=cfg.updated_at,
    )


def _audit_admin_email_action(db: Session, actor: User, entity_type: str, entity_id: str, action: str, details: dict) -> None:
    db.add(AdminAuditEvent(actor_id=actor.id, entity_type=entity_type, entity_id=entity_id, action=action, details=details))


def _validate_template_status_transition(current: str, nxt: str) -> None:
    if current == nxt:
        return
    allowed = {('draft', 'active'), ('active', 'archived'), ('draft', 'archived'), ('archived', 'draft')}
    if (current, nxt) not in allowed:
        raise HTTPException(status_code=422, detail='Invalid template status transition')


@router.get('/email/providers', response_model=list[EmailProviderConfigResponse])
def list_email_provider_configs(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    providers = ['resend', 'sendgrid']
    rows = {c.provider: c for c in db.query(EmailProviderConfig).filter(EmailProviderConfig.provider.in_(providers)).all()}
    out: list[EmailProviderConfigResponse] = []
    now = datetime.now(timezone.utc)
    for provider in providers:
        cfg = rows.get(provider)
        if cfg:
            out.append(_safe_email_provider_response(cfg))
        else:
            out.append(EmailProviderConfigResponse(provider=provider, enabled=False, from_email='', from_name=None, reply_to=None, configured=False, webhook_configured=False, created_at=now, updated_at=now))
    return out


@router.get('/email/providers/{provider}', response_model=EmailProviderConfigResponse)
def get_email_provider_config(provider: str, _: str = Depends(require_admin), db: Session = Depends(get_db)):
    if provider not in {'resend', 'sendgrid'}:
        raise HTTPException(status_code=404, detail='Provider not found')
    cfg = db.query(EmailProviderConfig).filter(EmailProviderConfig.provider == provider).first()
    if not cfg:
        now = datetime.now(timezone.utc)
        return EmailProviderConfigResponse(provider=provider, enabled=False, from_email='', from_name=None, reply_to=None, configured=False, webhook_configured=False, created_at=now, updated_at=now)
    return _safe_email_provider_response(cfg)


@router.patch('/email/providers/{provider}', response_model=EmailProviderConfigResponse)
def patch_email_provider_config(provider: str, payload: EmailProviderConfigPatchRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if provider not in {'resend', 'sendgrid'}:
        raise HTTPException(status_code=404, detail='Provider not found')
    cfg = db.query(EmailProviderConfig).filter(EmailProviderConfig.provider == provider).first()
    if not cfg:
        cfg = EmailProviderConfig(provider=provider, from_email='')
        db.add(cfg)
    if payload.enabled is not None: cfg.enabled = payload.enabled
    if payload.from_email is not None: cfg.from_email = payload.from_email
    if payload.from_name is not None: cfg.from_name = payload.from_name
    if payload.reply_to is not None: cfg.reply_to = payload.reply_to
    if payload.api_key is not None:
        val = payload.api_key.strip()
        cfg.api_key_encrypted = email_secret_crypto.encrypt(val) if val else None
    if payload.webhook_secret is not None:
        ws = payload.webhook_secret.strip()
        cfg.webhook_secret_encrypted = email_secret_crypto.encrypt(ws) if ws else None
    if payload.clear_webhook_secret:
        cfg.webhook_secret_encrypted = None
    db.flush()
    _audit_admin_email_action(db, current_user, 'email_provider_config', provider, 'email_provider_config_updated', {'provider': provider, 'enabled': cfg.enabled, 'configured': bool(cfg.api_key_encrypted)})
    db.commit(); db.refresh(cfg)
    return _safe_email_provider_response(cfg)


def _validate_campaign_status_transition(current_status: str, next_status: str) -> None:
    allowed = {"draft": {"ready", "archived"}, "ready": {"draft", "archived"}, "archived": {"draft"}}
    if current_status == next_status:
        return
    if next_status not in allowed.get(current_status, set()):
        raise HTTPException(status_code=400, detail=f"Invalid campaign status transition from {current_status} to {next_status}")


def _ensure_active_template(db: Session, template_id: str):
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t or t.status == 'archived':
        raise HTTPException(status_code=400, detail='Template is missing or archived')
    return t


def _render_simple_template(content: str | None, variables: dict) -> tuple[str, list[str]]:
    import re
    if not content:
        return '', []
    missing: list[str] = []
    def repl(match):
        key = match.group(1).strip()
        if key not in variables or variables.get(key) is None:
            missing.append(key)
            return ''
        return str(variables.get(key))
    rendered = re.sub(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}", repl, content)
    return rendered, sorted(set(missing))




def _normalize_email(value: str) -> str:
    return (value or '').strip().lower()


def _resolve_campaign_recipients(db: Session, campaign: EmailCampaign) -> dict:
    max_audience = 500
    rows = db.query(EmailSuppression.email).all()
    suppressed = {_normalize_email(r[0]) for r in rows if r[0]}
    candidates: list[tuple[str, str | None]] = []
    if campaign.audience_type == 'manual_list':
        raw = campaign.audience_filters_json if isinstance(campaign.audience_filters_json, dict) else {}
        emails = raw.get('emails') if isinstance(raw.get('emails'), list) else []
        if len(emails) > max_audience:
            raise HTTPException(status_code=400, detail=f'Manual audience exceeds max {max_audience}')
        candidates = [(_normalize_email(str(e)), None) for e in emails]
    elif campaign.audience_type == 'all_users':
        users = db.query(User.id, User.email).filter(User.email.isnot(None)).limit(max_audience + 1).all()
        if len(users) > max_audience:
            raise HTTPException(status_code=400, detail=f'Audience exceeds max {max_audience}')
        candidates = [(_normalize_email(u.email), str(u.id)) for u in users if u.email]
    else:
        raise HTTPException(status_code=400, detail='Unsupported audience type for E4')

    import re
    valid_re = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    seen=set(); sendable=[]; dup=0; invalid=[]; sup=[]
    for email, uid in candidates:
        if not email or not valid_re.match(email):
            invalid.append(email); continue
        if email in seen:
            dup += 1; continue
        seen.add(email)
        if email in suppressed:
            sup.append(email); continue
        sendable.append((email, uid))
    return {'total': len(candidates), 'sendable': sendable, 'suppressed': sup, 'invalid': invalid, 'duplicates': dup}

def _render_campaign(c: EmailCampaign, t: EmailTemplate, override_vars: dict | None = None) -> dict:
    merged = {}
    if isinstance(t.variables_json, dict): merged.update(t.variables_json)
    if isinstance(c.variables_json, dict): merged.update(c.variables_json)
    if isinstance(override_vars, dict): merged.update(override_vars)
    subject, m1 = _render_simple_template(c.subject_override or t.subject, merged)
    preheader, m2 = _render_simple_template(c.preheader_override or t.preheader or '', merged)
    html_body, m3 = _render_simple_template(t.html_body, merged)
    text_body, m4 = _render_simple_template(t.text_body or '', merged)
    return {'subject':subject,'preheader':preheader or None,'html_body':html_body,'text_body':text_body,'missing_variables':sorted(set(m1+m2+m3+m4))}


@router.get('/email/templates', response_model=list[EmailTemplateResponse])
def list_email_templates(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(EmailTemplate).order_by(EmailTemplate.updated_at.desc()).all()

@router.post('/email/templates', response_model=EmailTemplateResponse, status_code=201)
def create_email_template(payload: EmailTemplateCreateRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if db.query(EmailTemplate).filter(EmailTemplate.slug == payload.slug).first():
        raise HTTPException(status_code=400, detail='Slug already exists')
    t = EmailTemplate(**payload.model_dump(), created_by_admin_id=current_user.id, updated_by_admin_id=current_user.id)
    db.add(t); db.flush()
    _audit_admin_email_action(db, current_user, 'email_template', str(t.id), 'email_template_created', {'slug': t.slug, 'status': t.status})
    db.commit(); db.refresh(t); return t

@router.get('/email/templates/{template_id}', response_model=EmailTemplateResponse)
def get_email_template(template_id: str, _: str = Depends(require_admin), db: Session = Depends(get_db)):
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t: raise HTTPException(status_code=404, detail='Template not found')
    return t

@router.patch('/email/templates/{template_id}', response_model=EmailTemplateResponse)
def patch_email_template(template_id: str, payload: EmailTemplatePatchRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t: raise HTTPException(status_code=404, detail='Template not found')
    update = payload.model_dump(exclude_unset=True)
    if t.status == 'archived' and ('status' not in update or update.get('status') != 'draft'):
        raise HTTPException(status_code=400, detail='Archived templates are read-only')
    if 'slug' in update and update['slug'] != t.slug and db.query(EmailTemplate).filter(EmailTemplate.slug == update['slug']).first():
        raise HTTPException(status_code=400, detail='Slug already exists')
    if 'status' in update: _validate_template_status_transition(t.status, update['status'])
    for k,v in update.items(): setattr(t,k,v)
    t.updated_by_admin_id = current_user.id
    _audit_admin_email_action(db, current_user, 'email_template', str(t.id), 'email_template_updated', {'slug': t.slug, 'status': t.status})
    db.commit(); db.refresh(t); return t

@router.delete('/email/templates/{template_id}', response_model=EmailTemplateResponse)
def archive_email_template(template_id: str, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    t = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not t: raise HTTPException(status_code=404, detail='Template not found')
    t.status = 'archived'; t.updated_by_admin_id = current_user.id
    _audit_admin_email_action(db, current_user, 'email_template', str(t.id), 'email_template_archived', {'slug': t.slug})
    db.commit(); db.refresh(t); return t

@router.get('/email/campaigns', response_model=list[EmailCampaignResponse])
def list_email_campaigns(limit: int = Query(50, ge=1, le=200), _: str = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(EmailCampaign).order_by(EmailCampaign.created_at.desc()).limit(limit).all()


@router.post('/email/campaigns', response_model=EmailCampaignResponse, status_code=201)
def create_email_campaign(payload: EmailCampaignCreateRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_active_template(db, str(payload.template_id))
    c = EmailCampaign(**payload.model_dump(), created_by_admin_id=current_user.id, updated_by_admin_id=current_user.id)
    db.add(c); db.flush()
    _audit_admin_email_action(db, current_user, 'email_campaign', str(c.id), 'email_campaign_created', {'status': c.status, 'template_id': str(c.template_id)})
    db.commit(); db.refresh(c); return c


@router.get('/email/campaigns/{campaign_id}', response_model=EmailCampaignResponse)
def get_email_campaign(campaign_id: str, _: str = Depends(require_admin), db: Session = Depends(get_db)):
    c = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    if not c: raise HTTPException(status_code=404, detail='Campaign not found')
    return c


@router.patch('/email/campaigns/{campaign_id}', response_model=EmailCampaignResponse)
def patch_email_campaign(campaign_id: str, payload: EmailCampaignPatchRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    if not c: raise HTTPException(status_code=404, detail='Campaign not found')
    update = payload.model_dump(exclude_unset=True)
    if c.status == 'archived' and update.get('status') != 'draft': raise HTTPException(status_code=400, detail='Archived campaigns are read-only')
    if 'status' in update: _validate_campaign_status_transition(c.status, update['status'])
    if 'template_id' in update: _ensure_active_template(db, str(update['template_id']))
    for k,v in update.items(): setattr(c,k,v)
    c.updated_by_admin_id = current_user.id
    _audit_admin_email_action(db, current_user, 'email_campaign', str(c.id), 'email_campaign_updated', {'status': c.status})
    db.commit(); db.refresh(c); return c


@router.delete('/email/campaigns/{campaign_id}', response_model=EmailCampaignResponse)
def archive_email_campaign(campaign_id: str, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    if not c: raise HTTPException(status_code=404, detail='Campaign not found')
    c.status = 'archived'; c.updated_by_admin_id = current_user.id
    _audit_admin_email_action(db, current_user, 'email_campaign', str(c.id), 'email_campaign_archived', {'name': c.name})
    db.commit(); db.refresh(c); return c


@router.post('/email/campaigns/{campaign_id}/preview', response_model=EmailCampaignPreviewResponse)
def preview_email_campaign(campaign_id: str, payload: EmailCampaignPreviewRequest, _: str = Depends(require_admin), db: Session = Depends(get_db)):
    c = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    if not c: raise HTTPException(status_code=404, detail='Campaign not found')
    t = _ensure_active_template(db, str(c.template_id))
    return _render_campaign(c, t, payload.variables_json if isinstance(payload.variables_json, dict) else None)




@router.post('/email/campaigns/{campaign_id}/recipients/preview', response_model=EmailCampaignRecipientPreviewResponse)
def preview_email_campaign_recipients(campaign_id: str, _: str = Depends(require_admin), db: Session = Depends(get_db)):
    c = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    if not c: raise HTTPException(status_code=404, detail='Campaign not found')
    resolved = _resolve_campaign_recipients(db, c)
    return EmailCampaignRecipientPreviewResponse(
        total_candidates=resolved['total'],
        sendable_count=len(resolved['sendable']),
        suppressed_count=len(resolved['suppressed']),
        invalid_count=len(resolved['invalid']),
        duplicate_count=resolved['duplicates'],
        sample_recipients=[e for e,_ in resolved['sendable'][:10]],
        suppressed_samples=resolved['suppressed'][:10],
        invalid_samples=resolved['invalid'][:10],
    )


@router.post('/email/campaigns/{campaign_id}/send', response_model=EmailCampaignSendResponse)
def send_email_campaign(campaign_id: str, payload: EmailCampaignSendRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from datetime import datetime, timezone
    c = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    if not c: raise HTTPException(status_code=404, detail='Campaign not found')
    if c.status in ('sending','sent'): raise HTTPException(status_code=409, detail='Campaign already queued/sent')
    if c.status != 'ready': raise HTTPException(status_code=400, detail='Campaign must be ready')
    if payload.confirmation_text != 'SEND CAMPAIGN': raise HTTPException(status_code=400, detail='Invalid confirmation_text')
    t = _ensure_active_template(db, str(c.template_id))
    if t.status != 'active': raise HTTPException(status_code=400, detail='Template must be active')
    resolved = _resolve_campaign_recipients(db, c)
    if len(resolved['sendable']) == 0: raise HTTPException(status_code=400, detail='No sendable recipients')
    max_cap = int(getattr(settings, 'EMAIL_CAMPAIGN_MAX_SEND_CAP', 5000))
    if len(resolved['sendable']) > max_cap: raise HTTPException(status_code=400, detail=f'Sendable recipients exceed safety cap of {max_cap}')
    _audit_admin_email_action(db, current_user, 'email_campaign', str(c.id), 'email_campaign_send_started', {'total_candidates': resolved['total'], 'sendable_count': len(resolved['sendable'])})
    # clear old rows for deterministic reruns in E4
    db.query(EmailCampaignRecipient).filter(EmailCampaignRecipient.campaign_id == c.id).delete()
    for e in resolved['suppressed']:
        db.add(EmailCampaignRecipient(campaign_id=c.id, email=e, status='skipped', skip_reason='suppressed'))
    for e in resolved['invalid']:
        db.add(EmailCampaignRecipient(campaign_id=c.id, email=e, status='skipped', skip_reason='invalid'))
    queued_count=0
    enqueue_error: str | None = None
    for email, user_id in resolved['sendable']:
        recipient = EmailCampaignRecipient(campaign_id=c.id, email=email, user_id=user_id, status='queued', queued_at=datetime.now(timezone.utc))
        db.add(recipient); db.flush()
        try:
            enqueue_campaign_recipient_send(str(recipient.id))
            queued_count+=1
        except Exception as exc:
            recipient.status = 'failed'
            recipient.failed_at = datetime.now(timezone.utc)
            enqueue_error = sanitize_processing_error(str(exc))
            c.send_error_sanitized = enqueue_error
    if queued_count == 0:
        c.status = 'failed'
        c.send_failed_at = datetime.now(timezone.utc)
        db.commit()
        raise HTTPException(status_code=503, detail='Failed to queue campaign recipients')
    c.status='sending'; c.send_started_at=datetime.now(timezone.utc); c.send_failed_at=None; c.send_error_sanitized=None
    if enqueue_error:
        c.send_error_sanitized = enqueue_error
    _audit_admin_email_action(db, current_user, 'email_campaign', str(c.id), 'email_campaign_queued', {'queued_count': queued_count})
    db.commit()
    return EmailCampaignSendResponse(total_candidates=resolved['total'], sendable_count=len(resolved['sendable']), sent_count=0, failed_count=0, skipped_count=len(resolved['suppressed'])+len(resolved['invalid'])+resolved['duplicates'], status='sending', campaign_id=str(c.id), recipient_count=queued_count)



@router.get('/email/campaigns/{campaign_id}/send-status')
def email_campaign_send_status(campaign_id: str, _: str = Depends(require_admin), db: Session = Depends(get_db)):
    c = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    if not c: raise HTTPException(status_code=404, detail='Campaign not found')
    rows = db.query(EmailCampaignRecipient.status).filter(EmailCampaignRecipient.campaign_id == c.id).all()
    total=len(rows)
    counts={k:0 for k in ['queued','sent','delivered','bounced','complained','failed','skipped']}
    for (st,) in rows:
        if st in counts: counts[st]+=1
    done=counts['sent']+counts['delivered']+counts['bounced']+counts['complained']+counts['failed']+counts['skipped']
    return {'campaign_id': str(c.id), 'status': c.status, 'total': total, **counts, 'completion_percentage': (0 if total==0 else round(done*100/total,2)), 'send_started_at': c.send_started_at, 'send_completed_at': c.send_completed_at, 'send_failed_at': c.send_failed_at}

@router.get('/email/suppressions', response_model=list[EmailSuppressionResponse])
def list_email_suppressions(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(EmailSuppression).order_by(EmailSuppression.created_at.desc()).all()


@router.post('/email/suppressions', response_model=EmailSuppressionResponse, status_code=201)
def add_email_suppression(payload: EmailSuppressionCreateRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    email = _normalize_email(payload.email)
    row = db.query(EmailSuppression).filter(EmailSuppression.email == email).first()
    if row: return row
    row = EmailSuppression(email=email, reason=payload.reason, source=payload.source, created_by_admin_id=current_user.id)
    db.add(row); db.flush()
    _audit_admin_email_action(db, current_user, 'email_suppression', str(row.id), 'email_suppression_added', {'email': email, 'reason': payload.reason})
    db.commit(); db.refresh(row); return row


@router.delete('/email/suppressions/{email}')
def delete_email_suppression(email: str, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    normalized = _normalize_email(email)
    row = db.query(EmailSuppression).filter(EmailSuppression.email == normalized).first()
    if not row: raise HTTPException(status_code=404, detail='Suppression not found')
    db.delete(row)
    _audit_admin_email_action(db, current_user, 'email_suppression', normalized, 'email_suppression_removed', {'email': normalized})
    db.commit()
    return {'removed': True}
@router.post('/email/campaigns/{campaign_id}/test-send', response_model=AdminEmailTestSendResponse)
def test_send_campaign(campaign_id: str, payload: EmailCampaignTestSendRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    c = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id).first()
    if not c: raise HTTPException(status_code=404, detail='Campaign not found')
    t = _ensure_active_template(db, str(c.template_id))
    rendered = _render_campaign(c, t, payload.variables_json if isinstance(payload.variables_json, dict) else None)
    service = EmailDeliveryService(db)
    result = service.send_email(provider=payload.provider, to_email=payload.to_email, subject=rendered['subject'], html_body=rendered['html_body'], text_body=rendered['text_body'], template_id=str(t.id), campaign_id=str(c.id))
    _audit_admin_email_action(db, current_user, 'email_campaign', str(c.id), 'email_campaign_test_send', {'provider': result['provider'], 'status': result['status'], 'to_email': payload.to_email})
    db.commit()
    return result


@router.get("/llm-models", response_model=AdminLlmModelsResponse)
def admin_llm_models(_: str = Depends(require_admin)):
    provider_configured = {
        "openai": bool(settings.OPENAI_API_KEY.strip()),
        "gemini": bool(settings.GEMINI_API_KEY.strip()),
    }
    providers = [
        LlmProviderCatalogResponse(
            id=provider["id"],  # type: ignore[index]
            name=provider["name"],  # type: ignore[index]
            configured=provider_configured.get(provider["id"], False),  # type: ignore[index]
            models=[LlmModelOptionResponse(**model) for model in provider["models"]],  # type: ignore[index]
        )
        for provider in _LLM_PROVIDER_CATALOG
    ]
    return AdminLlmModelsResponse(providers=providers)


@router.get("/users", response_model=AdminUsersPageResponse)
def list_users(
    q: str | None = Query(None),
    role: str | None = Query(None),
    is_active: bool | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User).order_by(User.created_at.desc())
    if q:
        pattern = f"%{q.lower()}%"
        query = query.filter(or_(func.lower(User.email).like(pattern), func.lower(User.display_name).like(pattern)))
    if role:
        query = query.filter(User.role == role.lower())
    if is_active is not None:
        query = query.filter(User.is_active.is_(is_active))
    return AdminUsersPageResponse(items=query.offset(offset).limit(limit).all(), total_count=query.count(), limit=limit, offset=offset)


def _admin_count(db: Session) -> int:
    return db.query(User).filter(User.role == "admin", User.is_active.is_(True)).count()


def _audit_user_action(db: Session, actor: User, target: User | None, action: str, details: dict) -> None:
    db.add(AdminAuditEvent(actor_id=actor.id, entity_type="user", entity_id=str(target.id if target else details.get("email", "")), action=action, details=details))


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def admin_create_user(payload: AdminUserCreateRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if not payload.password and not payload.send_invite:
        raise HTTPException(status_code=400, detail="Password is required unless send_invite=true")
    if payload.send_invite and not payload.password:
        token = secrets.token_urlsafe(32)
        db.add(UserInvite(email=email, role=payload.role, token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(), invited_by_user_id=current_user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=7)))
    user = User(email=email, password_hash=auth_service.hash_password(payload.password or secrets.token_urlsafe(32)), display_name=(payload.display_name or email.split("@")[0]).strip(), is_active=True, role=payload.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    ensure_default_free_subscription(db, user.id)
    _audit_user_action(db, current_user, user, "user_created", {"target_email": user.email, "role": user.role, "send_invite": payload.send_invite})
    db.commit()
    return user


@router.get("/subscriptions", response_model=list[AdminSubscriptionResponse])
def list_user_subscriptions(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    seed_default_plans(db)
    rows = db.query(Subscription, User, Plan).join(User, User.id == Subscription.user_id).join(Plan, Plan.id == Subscription.plan_id).all()
    return [
        AdminSubscriptionResponse(
            user_id=u.id, email=u.email, subscription_id=s.id, plan_slug=p.slug, plan_name=p.name, status=s.status,
            cancel_at_period_end=s.cancel_at_period_end, usage_credits=s.usage_credits_json or {}, limit_overrides=s.limit_overrides_json or {},
        )
        for s, u, p in rows
    ]


def _validate_limits_json(limits_json: dict) -> None:
    allowed_keys = {"documents_per_month", "storage_bytes", "processing_jobs_per_month", "seats"}
    for key, value in limits_json.items():
        if key not in allowed_keys:
            raise HTTPException(status_code=422, detail=f"Unknown limit key '{key}'.")
        if value is None:
            continue
        if not isinstance(value, (int, float)) or value < 0:
            raise HTTPException(status_code=422, detail=f"Invalid limit for '{key}'. Expected non-negative number or null.")


def _validate_features_json(features_json: dict) -> None:
    allowed_keys = {"basic_search", "chat", "priority_support", "team_workspace", "insights_enabled", "category_intelligence_enabled", "relationship_detection_enabled"}
    for key, value in features_json.items():
        if key not in allowed_keys:
            raise HTTPException(status_code=422, detail=f"Unknown feature key '{key}'.")
        if not isinstance(value, bool):
            raise HTTPException(status_code=422, detail=f"Invalid feature flag for '{key}'. Expected boolean.")


@router.get("/plans", response_model=list[AdminPlanResponse])
def list_admin_plans(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    seed_default_plans(db)
    plans = db.query(Plan).filter(Plan.is_active.is_(True)).order_by(Plan.created_at.asc()).all()
    return plans


@router.patch("/plans/{plan_id}", response_model=AdminPlanResponse)
def patch_admin_plan(plan_id: str, payload: AdminPlanPatchRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if payload.limits_json is not None:
        _validate_limits_json(payload.limits_json)
    if payload.features_json is not None:
        _validate_features_json(payload.features_json)

    before = {
        "name": plan.name,
        "price_monthly_cents": plan.price_monthly_cents,
        "limits_json": dict(plan.limits_json or {}),
        "features_json": dict(plan.features_json or {}),
        "is_active": plan.is_active,
    }
    if payload.name is not None:
        plan.name = payload.name
    if payload.price_monthly_cents is not None:
        plan.price_monthly_cents = payload.price_monthly_cents
    if payload.limits_json is not None:
        plan.limits_json = payload.limits_json
    if payload.features_json is not None:
        plan.features_json = payload.features_json
    if payload.is_active is not None:
        plan.is_active = payload.is_active

    db.add(
        AdminAuditEvent(
            actor_id=current_user.id,
            entity_type="plan",
            entity_id=str(plan.id),
            action="plan_config_updated",
            details={"plan_slug": plan.slug, "before": before, "after": {"name": plan.name, "price_monthly_cents": plan.price_monthly_cents, "limits_json": plan.limits_json or {}, "features_json": plan.features_json or {}, "is_active": plan.is_active}},
        )
    )
    db.commit()
    db.refresh(plan)
    return plan


@router.post("/plans/reset-defaults", response_model=list[AdminPlanResponse])
def reset_admin_plan_defaults(_: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    seed_payloads = {}
    from app.services.subscriptions import DEFAULT_PLANS
    for payload in DEFAULT_PLANS:
        seed_payloads[payload["slug"]] = payload

    plans = db.query(Plan).filter(Plan.slug.in_(["free", "pro", "team"])).all()
    before = {}
    for plan in plans:
        before[plan.slug] = {"name": plan.name, "price_monthly_cents": plan.price_monthly_cents, "limits_json": plan.limits_json or {}, "features_json": plan.features_json or {}, "is_active": plan.is_active}
        defaults = seed_payloads.get(plan.slug)
        if not defaults:
            continue
        plan.name = defaults["name"]
        plan.price_monthly_cents = defaults["price_monthly_cents"]
        plan.limits_json = defaults["limits_json"]
        plan.features_json = defaults["features_json"]
        plan.is_active = True
    db.add(AdminAuditEvent(actor_id=current_user.id, entity_type="plan", entity_id="defaults", action="plan_defaults_reset", details={"before": before, "slugs": ["free", "pro", "team"]}))
    db.commit()
    return db.query(Plan).filter(Plan.is_active.is_(True)).order_by(Plan.created_at.asc()).all()


@router.get("/users/{user_id}/usage-summary", response_model=AdminUsageSummaryResponse)
def admin_user_usage_summary(user_id: str, _: str = Depends(require_admin), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    ensure_default_free_subscription(db, target.id)
    start, end = _current_period_window(db, target.id)
    return AdminUsageSummaryResponse(user_id=target.id, window_start=start, window_end=end, usage=get_usage_summary(db, target.id, start, end))


@router.patch("/users/{user_id}/plan", response_model=AdminSubscriptionResponse)
def admin_change_user_plan(user_id: str, payload: AdminPlanUpdateRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    seed_default_plans(db)
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    plan = db.query(Plan).filter(Plan.slug == payload.plan_slug, Plan.is_active.is_(True)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    sub = ensure_default_free_subscription(db, target.id)
    prev = sub.plan.slug if sub.plan else None
    sub.plan_id = plan.id
    _audit_admin_monetization_action(db, current_user=current_user, target_user=target, action="plan_updated", details={"previous_plan": prev, "new_plan": plan.slug})
    db.commit()
    db.refresh(sub)
    return AdminSubscriptionResponse(user_id=target.id, email=target.email, subscription_id=sub.id, plan_slug=sub.plan.slug, plan_name=sub.plan.name, status=sub.status, cancel_at_period_end=sub.cancel_at_period_end, usage_credits=sub.usage_credits_json or {}, limit_overrides=sub.limit_overrides_json or {})


@router.patch("/users/{user_id}/usage-controls", response_model=AdminSubscriptionResponse)
def admin_update_usage_controls(user_id: str, payload: AdminUsageOverrideRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    sub = ensure_default_free_subscription(db, target.id)
    credits = dict(sub.usage_credits_json or {})
    overrides = dict(sub.limit_overrides_json or {})
    credits.update(payload.usage_credits)
    for metric, value in payload.limit_overrides.items():
        if value is None:
            overrides.pop(metric, None)
        else:
            overrides[metric] = int(value)
    sub.usage_credits_json = credits
    sub.limit_overrides_json = overrides
    _audit_admin_monetization_action(db, current_user=current_user, target_user=target, action="usage_controls_updated", details={"usage_credits": payload.usage_credits, "limit_overrides": payload.limit_overrides})
    db.commit()
    db.refresh(sub)
    return AdminSubscriptionResponse(user_id=target.id, email=target.email, subscription_id=sub.id, plan_slug=sub.plan.slug, plan_name=sub.plan.name, status=sub.status, cancel_at_period_end=sub.cancel_at_period_end, usage_credits=sub.usage_credits_json or {}, limit_overrides=sub.limit_overrides_json or {})


@router.post("/users/{user_id}/cancel-or-downgrade", response_model=AdminSubscriptionResponse)
def admin_cancel_or_downgrade_subscription(user_id: str, payload: AdminCancelDowngradeRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    seed_default_plans(db)
    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    sub = ensure_default_free_subscription(db, target.id)
    plan = db.query(Plan).filter(Plan.slug == payload.downgrade_to_plan_slug, Plan.is_active.is_(True)).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    prev_plan = sub.plan.slug if sub.plan else None
    sub.plan_id = plan.id
    sub.status = "canceled" if plan.slug == "free" else "active"
    sub.cancel_at_period_end = True
    _audit_admin_monetization_action(db, current_user=current_user, target_user=target, action="subscription_canceled_or_downgraded", details={"previous_plan": prev_plan, "new_plan": plan.slug, "status": sub.status})
    db.commit()
    db.refresh(sub)
    return AdminSubscriptionResponse(user_id=target.id, email=target.email, subscription_id=sub.id, plan_slug=sub.plan.slug, plan_name=sub.plan.name, status=sub.status, cancel_at_period_end=sub.cancel_at_period_end, usage_credits=sub.usage_credits_json or {}, limit_overrides=sub.limit_overrides_json or {})


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
def update_user_role(
    user_id: str,
    payload: AdminRoleUpdateRequest,
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    next_role = payload.role.lower()
    if next_role not in {"viewer", "editor", "admin"}:
        raise HTTPException(status_code=422, detail="Invalid role")

    if user.role == "admin" and next_role != "admin":
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot self-demote admin role")
        if _admin_count(db) <= 1:
            raise HTTPException(status_code=400, detail="Cannot demote the last admin")

    prev = user.role
    user.role = next_role
    db.add(
        AdminAuditEvent(
            actor_id=current_user.id,
            entity_type="user",
            entity_id=str(user.id),
            action="role_updated",
            details={"previous_role": prev, "new_role": next_role, "target_email": user.email},
        )
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/deactivate", response_model=AdminUserResponse)
def deactivate_user(user_id: str, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    if user.role == "admin" and user.is_active and _admin_count(db) <= 1:
        raise HTTPException(status_code=400, detail="Cannot deactivate the last admin")
    user.is_active = False
    _audit_user_action(db, current_user, user, "deactivated", {"target_email": user.email})
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/reactivate", response_model=AdminUserResponse)
def reactivate_user(user_id: str, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    _audit_user_action(db, current_user, user, "reactivated", {"target_email": user.email})
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: str, payload: AdminDeleteUserRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    if user.role == "admin" and user.is_active and _admin_count(db) <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last admin")
    if payload.confirmation not in {"DELETE", user.email}:
        raise HTTPException(status_code=400, detail="Confirmation must match user email or DELETE")
    user.is_active = False
    _audit_user_action(db, current_user, user, "soft_deleted", {"target_email": user.email})
    db.commit()
    return {"ok": True}




def _invite_status(invite: UserInvite) -> str:
    now = datetime.now(timezone.utc)
    if invite.accepted_at:
        return "accepted"
    if invite.canceled_at:
        return "canceled"
    if invite.expires_at < now:
        return "expired"
    return "pending"

@router.post("/users/invite")
def create_invite(payload: AdminInviteCreateRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="User already exists")
    token = secrets.token_urlsafe(32)
    invite = UserInvite(email=email, role=payload.role, token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(), invited_by_user_id=current_user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days))
    db.add(invite)
    _audit_user_action(db, current_user, None, "invite_created", {"email": email, "role": payload.role})
    db.commit()
    return {"id": str(invite.id), "invite_link": f"/accept-invite?token={token}", "status": _invite_status(invite), "dev_invite_link": f"/accept-invite?token={token}"}




@router.post("/users/invites/{invite_id}/resend")
def resend_invite(invite_id: str, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invite = db.query(UserInvite).filter(UserInvite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.accepted_at or invite.canceled_at:
        raise HTTPException(status_code=400, detail="Invite is no longer active")
    if db.query(User).filter(User.email == invite.email.lower()).first():
        raise HTTPException(status_code=400, detail="User already exists")
    token = secrets.token_urlsafe(32)
    invite.token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    invite.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    _audit_user_action(db, current_user, None, "invite_resent", {"email": invite.email, "invite_id": str(invite.id)})
    db.commit()
    return {"id": str(invite.id), "invite_link": f"/accept-invite?token={token}", "status": _invite_status(invite), "dev_invite_link": f"/accept-invite?token={token}"}


@router.post("/users/invites/{invite_id}/cancel")
def cancel_invite(invite_id: str, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invite = db.query(UserInvite).filter(UserInvite.id == invite_id).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.accepted_at:
        raise HTTPException(status_code=400, detail="Invite is already accepted")
    if invite.canceled_at:
        raise HTTPException(status_code=400, detail="Invite already canceled")
    invite.canceled_at = datetime.now(timezone.utc)
    _audit_user_action(db, current_user, None, "invite_canceled", {"email": invite.email, "invite_id": str(invite.id)})
    db.commit()
    db.refresh(invite)
    return invite

@router.get("/users/invites", response_model=list[AdminInviteResponse])
def list_invites(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    invites = db.query(UserInvite).order_by(UserInvite.created_at.desc()).all()
    return [AdminInviteResponse.model_validate(invite, from_attributes=True).model_copy(update={"status": _invite_status(invite)}) for invite in invites]


@router.get("/audit", response_model=AdminAuditPageResponse)
def list_admin_audit(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(AdminAuditEvent).order_by(AdminAuditEvent.created_at.desc())
    items = q.offset(offset).limit(limit).all()
    mapped = [
        AdminAuditEventResponse(
            id=i.id,
            actor_id=i.actor_id,
            actor_email=i.actor.email if i.actor else None,
            entity_type=i.entity_type,
            entity_id=i.entity_id,
            action=i.action,
            details=i.details or {},
            created_at=i.created_at,
        )
        for i in items
    ]
    return AdminAuditPageResponse(items=mapped, total_count=q.count(), limit=limit, offset=offset)


@router.get("/system-status", response_model=AdminSystemStatusResponse)
def admin_system_status(_: str = Depends(require_admin)):
    stripe_configured = bool(settings.STRIPE_SECRET_KEY.strip())
    stripe_prices_configured = bool(settings.STRIPE_PRICE_PRO_MONTHLY.strip()) and bool(settings.STRIPE_PRICE_TEAM_MONTHLY.strip())
    billing_configured = stripe_configured and stripe_prices_configured
    limits_configured = all([
        settings.RATE_LIMIT_UPLOADS_PER_MINUTE > 0,
        settings.RATE_LIMIT_PROCESSING_PER_MINUTE > 0,
        settings.RATE_LIMIT_EXPENSIVE_READS_PER_MINUTE > 0,
        settings.RATE_LIMIT_RELATIONSHIP_DETECTION_PER_MINUTE > 0,
        settings.HARD_DAILY_MAX_UPLOADS > 0,
        settings.HARD_DAILY_MAX_PROCESSING_JOBS > 0,
        settings.HARD_DAILY_MAX_FAILED_PROCESSING_RETRIES > 0,
    ])
    environment = settings.APP_ENV if settings.APP_ENV in {"development", "staging", "production"} else "development"
    return AdminSystemStatusResponse(
        billing_configured=billing_configured,
        stripe_configured=stripe_configured,
        stripe_prices_configured=stripe_prices_configured,
        environment=environment,
        limits_configured=limits_configured,
        features=AdminSystemStatusFeaturesResponse(
            insights_enabled=settings.ENABLE_ENTITY_EXTRACTION,
            category_intelligence_enabled=settings.ENABLE_AUTO_CATEGORIZATION,
            relationship_detection_enabled=settings.RATE_LIMIT_RELATIONSHIP_DETECTION_PER_MINUTE > 0,
        ),
    )




def _status_from_ok(ok: bool) -> str:
    return "healthy" if ok else "down"


@router.get("/system/health", response_model=AdminSystemHealthResponse)
def admin_system_health(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    db_status = SystemComponentStatus(status="unknown")
    try:
        db.execute(text("SELECT 1"))
        db_status = SystemComponentStatus(status="healthy")
    except Exception:
        db_status = SystemComponentStatus(status="down", detail="database unavailable")

    redis_status = SystemComponentStatus(status="unknown")
    try:
        from redis import Redis
        client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
        redis_status = SystemComponentStatus(status=_status_from_ok(bool(client.ping())))
    except Exception:
        redis_status = SystemComponentStatus(status="down", detail="redis unavailable")

    celery_status = SystemComponentStatus(status="unknown")
    try:
        from app.workers.monitoring import inspect_workers
        workers = inspect_workers(timeout=2)
        celery_status = SystemComponentStatus(status="healthy" if workers.get("worker_count", 0) > 0 else "degraded", detail=f"workers={workers.get('worker_count', 0)}")
    except Exception:
        celery_status = SystemComponentStatus(status="degraded", detail="worker heartbeat unavailable")

    vector_status = SystemComponentStatus(status="unknown")
    try:
        if settings.QDRANT_HOST:
            from qdrant_client import QdrantClient
            q = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=1)
            q.get_collections()
            vector_status = SystemComponentStatus(status="healthy")
        else:
            vector_status = SystemComponentStatus(status="unknown", detail="not configured")
    except Exception:
        vector_status = SystemComponentStatus(status="degraded", detail="vector store unavailable")

    llm_providers = {
        "openai": SystemComponentStatus(status="configured" if bool(settings.OPENAI_API_KEY.strip()) else "unconfigured"),
        "gemini": SystemComponentStatus(status="configured" if bool(settings.GEMINI_API_KEY.strip()) else "unconfigured"),
        "anthropic": SystemComponentStatus(status="configured" if bool(settings.ANTHROPIC_API_KEY.strip()) else "unconfigured"),
    }
    statuses = [db_status.status, redis_status.status, celery_status.status, vector_status.status]
    overall = "healthy" if all(s == "healthy" for s in statuses if s != "unknown") else "degraded"
    if "down" in statuses:
        overall = "down"

    return AdminSystemHealthResponse(overall_status=overall, database=db_status, redis=redis_status, celery=celery_status, vector_store=vector_status, llm_providers=llm_providers, app={"version": settings.VERSION, "environment": settings.APP_ENV})


@router.get("/system/jobs", response_model=AdminSystemJobsResponse)
def admin_system_jobs(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    queue_length = db.query(func.count(ProcessingQueue.id)).filter(ProcessingQueue.status == "queued").scalar() or 0
    active_jobs = db.query(func.count(ProcessingQueue.id)).filter(ProcessingQueue.status == "processing").scalar() or 0
    failed_jobs = db.query(func.count(ProcessingQueue.id)).filter(ProcessingQueue.status == "failed").scalar() or 0
    recent_completed_jobs = db.query(func.count(ProcessingQueue.id)).filter(ProcessingQueue.status == "completed").scalar() or 0
    retry_count = db.query(func.coalesce(func.sum(ProcessingQueue.attempts), 0)).scalar() or 0
    last_failed = db.query(ProcessingQueue.error_message).filter(ProcessingQueue.status == "failed").order_by(ProcessingQueue.completed_at.desc(), ProcessingQueue.created_at.desc()).first()
    return AdminSystemJobsResponse(queue_length=queue_length, active_jobs=active_jobs, failed_jobs=failed_jobs, recent_completed_jobs=recent_completed_jobs, retry_count=int(retry_count), last_error_summary=sanitize_processing_error(last_failed[0] if last_failed and last_failed[0] else None))


@router.get("/system/llm-metrics", response_model=AdminLlmMetricsResponse)
def admin_llm_metrics(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    summary = summarize_prompt_executions(db)
    total = int(summary["total_calls"])
    success_count = int(round(summary["success_rate"] * total)) if total else 0
    error_count = max(0, total - success_count)
    lats = [row[0] for row in db.query(PromptExecutionLog.latency_ms).filter(PromptExecutionLog.latency_ms.isnot(None)).all()]
    lats = sorted(int(x) for x in lats if x is not None)
    def pct(p: float):
        if not lats:
            return None
        idx = min(len(lats)-1, max(0, int(round((len(lats)-1)*p))))
        return float(lats[idx])
    return AdminLlmMetricsResponse(total_calls=total, success_count=success_count, error_count=error_count, error_rate=(error_count/total if total else 0.0), provider_breakdown={k:int(v) for k,v in summary["calls_by_provider"].items()}, model_breakdown={k:int(v) for k,v in summary["calls_by_model"].items()}, fallback_usage=int(round(summary["fallback_rate"]*total)) if total else 0, latency_percentiles_ms={"p50": pct(0.5), "p90": pct(0.9), "p99": pct(0.99)}, cost_totals={"total_estimated_cost_usd": float(summary["total_estimated_cost_usd"]), "pricing_unknown_count": float(summary["pricing_unknown_count"])})

@router.get("/metrics", response_model=AdminMetricsResponse)
def admin_metrics(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    return AdminMetricsResponse(
        total_users=db.query(func.count(User.id)).scalar() or 0,
        total_documents=db.query(func.count(Document.id)).scalar() or 0,
        documents_processed=db.query(func.count(Document.id)).filter(Document.processing_status == "completed").scalar() or 0,
        documents_failed=db.query(func.count(Document.id)).filter(Document.processing_status == "failed").scalar() or 0,
        pending_review_items=db.query(func.count(DocumentReviewItem.id)).filter(DocumentReviewItem.status == "open").scalar() or 0,
        open_action_items=db.query(func.count(DocumentActionItem.id)).filter(DocumentActionItem.state == "open").scalar() or 0,
        pending_relationship_reviews=db.query(func.count(DocumentRelationshipReview.id)).filter(DocumentRelationshipReview.status == "pending").scalar() or 0,
    )


@router.get("/processing-summary", response_model=AdminProcessingSummaryResponse)
def admin_processing_summary(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    status_counts = (
        db.query(Document.processing_status, func.count(Document.id))
        .group_by(Document.processing_status)
        .all()
    )
    counts = {status: count for status, count in status_counts}
    recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recently_failed = (
        db.query(func.count(Document.id))
        .filter(Document.processing_status == "failed", Document.updated_at >= recent_cutoff)
        .scalar()
        or 0
    )
    return AdminProcessingSummaryResponse(
        pending=(counts.get("pending", 0) + counts.get("queued", 0)),
        processing=counts.get("processing", 0),
        completed=counts.get("completed", 0),
        failed=counts.get("failed", 0),
        recently_failed=recently_failed,
    )


@router.get("/documents/{document_id}/events", response_model=list[ProcessingEventResponse])
def list_document_processing_events(
    document_id: str,
    limit: int = Query(100, ge=1, le=500),
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return (
        db.query(DocumentProcessingEvent)
        .filter(DocumentProcessingEvent.document_id == document_id)
        .order_by(DocumentProcessingEvent.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/processing-events", response_model=list[ProcessingEventResponse])
def list_processing_events(
    document_id: str | None = None,
    stage: str | None = None,
    severity: str | None = None,
    event_type: str | None = None,
    provider: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(DocumentProcessingEvent)
    if document_id:
        q = q.filter(DocumentProcessingEvent.document_id == document_id)
    if stage:
        q = q.filter(DocumentProcessingEvent.stage == stage)
    if severity:
        q = q.filter(DocumentProcessingEvent.severity == severity)
    if event_type:
        q = q.filter(DocumentProcessingEvent.event_type == event_type)
    if provider:
        q = q.filter(DocumentProcessingEvent.provider == provider)
    if start_at:
        q = q.filter(DocumentProcessingEvent.created_at >= start_at)
    if end_at:
        q = q.filter(DocumentProcessingEvent.created_at <= end_at)
    return q.order_by(DocumentProcessingEvent.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/prompts", response_model=list[PromptTemplateResponse])
def list_prompt_templates(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(PromptTemplate).order_by(PromptTemplate.type.asc(), PromptTemplate.version.desc(), PromptTemplate.created_at.desc()).all()


@router.post("/prompts", response_model=PromptTemplateResponse, status_code=201)
def create_prompt_template(payload: PromptTemplateCreate, _: str = Depends(require_admin), db: Session = Depends(get_db)):
    _validate_fallback_payload(payload.provider, payload.model, payload.fallback_enabled, payload.fallback_provider, payload.fallback_model)
    prompt = PromptTemplate(**payload.model_dump())
    db.add(prompt)
    if prompt.is_default:
        db.flush()
        clear_default_for_purpose(db, prompt_type=prompt.type, exclude_id=str(prompt.id))
    if prompt.is_active:
        activate_prompt_template(db, prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.put("/prompts/{prompt_id}", response_model=PromptTemplateResponse)
def update_prompt_template(prompt_id: str, payload: PromptTemplateUpdate, _: str = Depends(require_admin), db: Session = Depends(get_db)):
    prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    changes = payload.model_dump(exclude_unset=True)
    merged = {"provider": prompt.provider, "model": prompt.model, "fallback_enabled": prompt.fallback_enabled, "fallback_provider": prompt.fallback_provider, "fallback_model": prompt.fallback_model, **changes}
    _validate_fallback_payload(merged["provider"], merged["model"], merged["fallback_enabled"], merged.get("fallback_provider"), merged.get("fallback_model"))
    for k, v in changes.items():
        setattr(prompt, k, v)
    if changes.get("is_default") is True:
        clear_default_for_purpose(db, prompt_type=prompt.type, exclude_id=str(prompt.id))
    if changes.get("is_active") is True:
        activate_prompt_template(db, prompt)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.post("/prompts/{prompt_id}/activate", response_model=PromptTemplateResponse)
def activate_prompt(prompt_id: str, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    activate_prompt_template(db, prompt)
    db.add(AdminAuditEvent(
        actor_id=current_user.id,
        entity_type="prompt_template",
        entity_id=str(prompt.id),
        action="prompt_template_activated",
        details={"type": prompt.type, "name": prompt.name, "version": prompt.version},
    ))
    db.commit()
    db.refresh(prompt)
    return prompt


@router.post("/prompts/test", response_model=PromptTemplateTestResponse)
def test_prompt_template(payload: PromptTemplateTestRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not openai_client_service.enabled:
        raise HTTPException(status_code=503, detail="AI service unavailable")

    system_prompt = DOCUMENT_ANALYSIS_SYSTEM if payload.type == "timeline_extraction" else ""
    user_prompt = payload.content.replace("{sample_context}", payload.sample_context)
    if "{sample_context}" not in payload.content:
        user_prompt = f"{payload.content}\n\n{payload.sample_context}"

    _validate_fallback_payload(payload.provider, payload.model, payload.fallback_enabled, payload.fallback_provider, payload.fallback_model)
    from app.models.prompt_template import PromptTemplate
    template = PromptTemplate(
        type=payload.type,
        name="admin-test",
        content=payload.content,
        provider=payload.provider,
        model=payload.model,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        top_p=payload.top_p,
        fallback_enabled=payload.fallback_enabled,
        fallback_provider=payload.fallback_provider,
        fallback_model=payload.fallback_model,
    )
    try:
        final_prompt = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt
        result = run_prompt_with_fallback(template, final_prompt, db=db, user_id=current_user.id, source="admin_test", purpose=payload.type)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=f"AI request failed: {exc}") from exc
    return PromptTemplateTestResponse(
        preview=result["output"],
        latency_ms=result["latency_ms"],
        usage_tokens=result["token_usage"],
        fallback_used=result["fallback_used"],
        provider_used=result["provider_used"],
        model_used=result["model_used"],
        primary_error=result["primary_error"],
        preview_mode=True,
        sample_context_used=True,
        system_prompt_source="production",
    )


DEFAULT_CHATBOT_SETTINGS = {
    "system_prompt": "You are Timebot. Use only uploaded and processed Timebot documents and persisted intelligence. If not found, say so.",
    "retrieval_prompt": "Retrieve timeline events, summaries, relationships, and excerpts.",
    "report_prompt": "Generate a markdown report grounded in sources.",
    "citation_prompt": "Cite document title and id for every factual claim.",
    "default_report_template": "# Report\n\n## Summary\n\n## Details\n\n## Sources",
    "model": "gpt-4.1-mini",
    "temperature": 0.2,
    "max_tokens": 1200,
    "max_documents": 8,
    "allow_full_text_retrieval": True,
    "prompt_daily_cost_threshold_usd": None,
    "prompt_monthly_cost_threshold_usd": None,
    "prompt_user_cost_threshold_usd": None,
    "prompt_workspace_cost_threshold_usd": None,
}


def _get_or_create_chatbot_settings(db: Session) -> ChatbotSettings:
    settings = db.query(ChatbotSettings).order_by(ChatbotSettings.created_at.asc()).first()
    if settings:
        return settings
    settings = ChatbotSettings(**DEFAULT_CHATBOT_SETTINGS)
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


@router.get("/chatbot-settings", response_model=ChatbotSettingsResponse)
def get_chatbot_settings(_: str = Depends(require_admin), db: Session = Depends(get_db)):
    return _get_or_create_chatbot_settings(db)


@router.put("/chatbot-settings", response_model=ChatbotSettingsResponse)
def update_chatbot_settings(payload: ChatbotSettingsPayload, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = _get_or_create_chatbot_settings(db)
    before = {k: getattr(settings, k) for k in DEFAULT_CHATBOT_SETTINGS.keys()}
    for k, v in payload.model_dump().items():
        setattr(settings, k, v)
    settings.updated_by_id = current_user.id
    db.add(settings)
    db.add(AdminAuditEvent(actor_id=current_user.id, entity_type="chatbot_settings", entity_id=str(settings.id), action="chatbot_settings_updated", details={"before": before, "after": payload.model_dump()}))
    db.commit()
    db.refresh(settings)
    return settings


@router.post("/chatbot-settings/reset", response_model=ChatbotSettingsResponse)
def reset_chatbot_settings(_: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    settings = _get_or_create_chatbot_settings(db)
    for k, v in DEFAULT_CHATBOT_SETTINGS.items():
        setattr(settings, k, v)
    settings.updated_by_id = current_user.id
    db.add(settings)
    db.add(AdminAuditEvent(actor_id=current_user.id, entity_type="chatbot_settings", entity_id=str(settings.id), action="chatbot_settings_reset", details={}))
    db.commit()
    db.refresh(settings)
    return settings


@router.get("/prompt-executions", response_model=list[PromptExecutionLogResponse])
def get_prompt_executions(prompt_template_id: str | None = None, provider: str | None = None, model: str | None = None, success: bool | None = None, fallback_used: bool | None = None, source: str | None = None, limit: int = 100, offset: int = 0, _: str = Depends(require_admin), db: Session = Depends(get_db)):
    return list_prompt_executions(db, prompt_template_id=prompt_template_id, provider=provider, model=model, success=success, fallback_used=fallback_used, source=source, limit=limit, offset=offset)


@router.get("/prompt-executions/summary", response_model=PromptExecutionSummaryResponse)
def get_prompt_executions_summary(provider: str | None = None, model: str | None = None, source: str | None = None, purpose: str | None = None, actor_user_id: str | None = None, success: bool | None = None, fallback_used: bool | None = None, created_after: datetime | None = None, created_before: datetime | None = None, _: str = Depends(require_admin), db: Session = Depends(get_db)):
    return summarize_prompt_executions(db, provider=provider, model=model, source=source, purpose=purpose, actor_user_id=actor_user_id, success=success, fallback_used=fallback_used, created_after=created_after, created_before=created_before)


@router.post('/email/test-send', response_model=AdminEmailTestSendResponse)
def admin_test_send_email(payload: AdminEmailTestSendRequest, _: str = Depends(require_admin), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = EmailDeliveryService(db)
    result = service.send_email(provider=payload.provider, to_email=payload.to_email, subject=payload.subject or 'Timebot Test Email', html_body=payload.html_body or '<p>This is a Timebot test email.</p>', text_body=payload.text_body)
    _audit_admin_email_action(db, current_user, 'email_test_send', result['log_id'], 'email_test_send', {'provider': result['provider'], 'status': result['status'], 'to_email': payload.to_email})
    db.commit()
    return result


@router.get('/email/send-logs', response_model=list[EmailSendLogResponse])
def list_email_send_logs(limit: int = Query(50, ge=1, le=200), _: str = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(EmailSendLog).order_by(EmailSendLog.created_at.desc()).limit(limit).all()
