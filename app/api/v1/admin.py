from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, get_current_user_role
from app.models.admin_audit import AdminAuditEvent
from app.models.document import Document
from app.models.intelligence import DocumentActionItem, DocumentRelationshipReview, DocumentReviewItem
from app.models.user import User
from app.models.processing_event import DocumentProcessingEvent

from app.models.chat import ChatbotSettings
from app.models.prompt_template import PromptTemplate
from app.schemas.chatbot import ChatbotSettingsPayload, ChatbotSettingsResponse
from app.schemas.admin import (
    AdminAuditEventResponse,
    AdminAuditPageResponse,
    AdminMetricsResponse,
    AdminProcessingSummaryResponse,
    AdminRoleUpdateRequest,
    AdminUserResponse,
    AdminUsersPageResponse,
    ProcessingEventResponse,
)
from app.schemas.prompt_template import (
    PromptTemplateCreate,
    PromptTemplateResponse,
    PromptTemplateTestRequest,
    PromptTemplateTestResponse,
    PromptTemplateUpdate,
)
from app.services.openai_client import APIError, openai_client_service
from app.services.prompt_templates import activate_prompt_template

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(role: str = Depends(get_current_user_role)) -> str:
    if role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return role


@router.get("/users", response_model=AdminUsersPageResponse)
def list_users(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(User).order_by(User.created_at.desc())
    return AdminUsersPageResponse(items=q.offset(offset).limit(limit).all(), total_count=q.count(), limit=limit, offset=offset)


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
        admin_count = db.query(User).filter(User.role == "admin").count()
        if admin_count <= 1:
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
    prompt = PromptTemplate(**payload.model_dump())
    db.add(prompt)
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
    for k, v in changes.items():
        setattr(prompt, k, v)
    if changes.get("is_active") is True:
        activate_prompt_template(db, prompt)
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.post("/prompts/{prompt_id}/activate", response_model=PromptTemplateResponse)
def activate_prompt(prompt_id: str, _: str = Depends(require_admin), db: Session = Depends(get_db)):
    prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt template not found")
    activate_prompt_template(db, prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.post("/prompts/test", response_model=PromptTemplateTestResponse)
def test_prompt_template(payload: PromptTemplateTestRequest, _: str = Depends(require_admin)):
    if not openai_client_service.enabled:
        raise HTTPException(status_code=503, detail="AI service unavailable")

    system_prompt = (
        "You are a prompt sandbox for Timebot admins. "
        "Use only the provided sample context. "
        "Do not invent or fetch external information. "
        "If information is missing in sample context, explicitly say so."
    )
    user_prompt = (
        f"Prompt type: {payload.type}\n\n"
        "Candidate prompt template:\n"
        f"{payload.content}\n\n"
        "Sample context/query/document text:\n"
        f"{payload.sample_context}\n\n"
        "Return the assistant response preview only."
    )

    try:
        response = openai_client_service.generate_completion({
            "model": "gpt-4.1-mini",
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        })
    except APIError as exc:
        raise HTTPException(status_code=502, detail=f"AI request failed: {exc}") from exc

    preview = (response.choices[0].message.content or "").strip() if response.choices else ""
    return PromptTemplateTestResponse(preview=preview)


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
