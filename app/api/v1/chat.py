from uuid import UUID
import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.v1.admin import _get_or_create_chatbot_settings
from app.models.chat import AssistantProfile, ChatDocumentLink, ChatMessage, ChatSession
from app.models.user import User
from app.services.chat_retrieval import format_chat_context, retrieve_chat_context
from app.services.openai_client import APIError, openai_client_service
from app.config import settings
from app.services.prompt_templates import get_active_prompt_content
from app.services.limit_enforcement import enforce_feature, enforce_limit, get_effective_plan
from app.services.entitlements import (
    can_create_chat,
    can_create_custom_prompt,
    can_use_assistant,
    can_use_system_intelligence,
    enforce_message_limit,
    require_upgrade,
)

router = APIRouter(prefix="/chat", tags=["chat"])


ANSWER_MODE_INSTRUCTIONS = {
    "timeline_reasoning": "Answer mode: timeline_reasoning. Focus on sequence, dates, and what happened next using only timeline evidence in context.",
    "relationship_reasoning": "Answer mode: relationship_reasoning. Focus on links between people, orgs, docs, or events supported by context evidence.",
    "change_analysis": "Answer mode: change_analysis. Compare before/after states and clearly describe what changed with evidence.",
    "inconsistency_check": "Answer mode: inconsistency_check. Identify contradictions or mismatches in context and call out missing corroboration.",
    "risk_analysis": "Answer mode: risk_analysis. Identify explicit risks, impacts, and uncertainty only where context supports it.",
    "general": "Answer mode: general. Provide a direct grounded answer based on the strongest available context evidence.",
}


def _detect_answer_mode(question: str) -> str:
    q = (question or "").strip().lower()
    if not q:
        return "general"

    timeline_terms = (
        "what happened next", "happened next", "after that", "then what", "sequence", "timeline", "chronology", "in order",
    )
    relationship_terms = (
        "relationship", "related to", "connected to", "connection between", "how does", "who worked with", "linked to",
    )
    change_terms = (
        "what changed", "changes", "changed", "difference", "different", "before and after", "delta", "evolution",
    )
    inconsistency_terms = (
        "inconsistent", "inconsistency", "contradiction", "conflict", "mismatch", "doesn't match", "do not match", "discrepancy",
    )
    risk_terms = (
        "risk", "risks", "risky", "exposure", "liability", "issue", "issues", "concern", "concerns", "red flag", "threat",
    )

    if any(t in q for t in inconsistency_terms):
        return "inconsistency_check"
    if any(t in q for t in risk_terms):
        return "risk_analysis"
    if any(t in q for t in change_terms):
        return "change_analysis"
    if any(t in q for t in timeline_terms):
        return "timeline_reasoning"
    if any(t in q for t in relationship_terms):
        return "relationship_reasoning"
    return "general"

logger = logging.getLogger(__name__)


class CreateSessionRequest(BaseModel):
    title: str = "New chat"
    assistant_id: UUID | None = None
    prompt_template_id: UUID | None = None
    linked_document_ids: list[UUID] | None = None


class UpdateSessionRequest(BaseModel):
    title: str | None = None
    is_archived: bool | None = None


class AssistantProfileOut(BaseModel):
    id: UUID
    name: str
    description: str
    required_plan: str
    default_prompt_template_id: UUID | None = None
    enabled: bool
    locked: bool = False

    model_config = {"from_attributes": True}


class MessageRequest(BaseModel):
    message: str
    document_ids: list[str] | None = None
    include_timeline: bool = True
    include_full_text: bool = False
    category: str | None = None
    jurisdiction: str | None = None
    legal_area: str | None = None


def _get_session_for_user(db: Session, session_id: UUID, user_id: UUID) -> ChatSession:
    s = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return s


def _load_recent_session_messages(db: Session, session_id: UUID, max_messages: int) -> list[dict]:
    if max_messages <= 0:
        return []
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(max_messages)
        .all()
    )
    rows.reverse()
    return [{"role": r.role, "content": r.content} for r in rows]


def _build_model_messages(db: Session, bot_settings, prompt: str, prior_messages: list[dict]) -> list[dict]:
    model_messages = [{"role": "system", "content": get_active_prompt_content(db, "chat", bot_settings.system_prompt)}]
    model_messages.extend(prior_messages)
    model_messages.append({"role": "user", "content": prompt})
    return model_messages


def _build_chat_payload(db: Session, user: User, payload: MessageRequest, session_id: UUID | None = None, assistant_type: str | None = None):
    bot_settings = _get_or_create_chatbot_settings(db)
    if not openai_client_service.enabled:
        raise HTTPException(status_code=503, detail="Chat AI is unavailable: OPENAI_API_KEY is not configured.")
    retrieval_start = time.perf_counter()
    context = retrieve_chat_context(
        db=db,
        query=payload.message,
        user_id=user.id,
        document_ids=payload.document_ids,
        include_timeline=payload.include_timeline,
        include_full_text=payload.include_full_text and bot_settings.allow_full_text_retrieval,
        max_documents=bot_settings.max_documents,
        assistant_type=assistant_type,
        category=payload.category,
        jurisdiction=payload.jurisdiction,
        legal_area=payload.legal_area,
        session_id=session_id,
    )
    retrieval_duration_ms = (time.perf_counter() - retrieval_start) * 1000
    logger.info(
        "chat_retrieval_timing",
        extra={
            "event": "chat_retrieval_timing",
            "user_id": str(user.id),
            "session_id": str(session_id) if session_id else None,
            "duration_ms": round(retrieval_duration_ms, 2),
            "document_count": len(context.get("documents", [])),
            "source_ref_count": len(context.get("source_refs", [])),
            "success": True,
        },
    )
    if not context["documents"]:
        return bot_settings, context, None
    retrieval_prompt_content = get_active_prompt_content(db, "retrieval", bot_settings.retrieval_prompt)
    answer_mode = _detect_answer_mode(payload.message)
    answer_mode_instruction = ANSWER_MODE_INSTRUCTIONS[answer_mode]
    prompt = (
        f"{retrieval_prompt_content}\n\n"
        f"Context:\n{format_chat_context(context)}\n\n"
        f"Question:\n{payload.message}\n\n"
        f"{answer_mode_instruction}\n"
        f"{bot_settings.citation_prompt}\n"
        "Only answer using provided context. If uncertain, explicitly say evidence is insufficient."
    )
    return bot_settings, context, prompt




def _log_chat_request(*, session_id: UUID, user_id: UUID, endpoint_type: str, retrieval_count: int, history_count: int, success: bool, latency_ms: float):
    logger.info(
        "chat_request",
        extra={
            "event": "chat_request",
            "session_id": str(session_id),
            "user_id": str(user_id),
            "endpoint_type": endpoint_type,
            "retrieval_count": retrieval_count,
            "history_message_count": history_count,
            "success": success,
            "latency_ms": round(latency_ms, 2),
        },
    )

def _append_sources(assistant_content: str, source_refs: list[dict]) -> str:
    if not source_refs:
        return assistant_content
    sources_lines = []
    for idx, ref in enumerate(source_refs[:8], 1):
        date_hint = f", {ref.get('timeline_date')}" if ref.get("kind") == "timeline_event" and ref.get("timeline_date") else ""
        sources_lines.append(f"{idx}. {ref.get('document_title')} — {ref.get('kind')}{date_hint}")
    return assistant_content + "\n\nSources:\n" + "\n".join(sources_lines)




def _plan_rank(slug: str) -> int:
    return {"free": 0, "pro": 1, "team": 2}.get((slug or "free").lower(), 0)


def _require_plan(db: Session, user_id: UUID, required_plan: str):
    effective = get_effective_plan(db, user_id)
    current = ((effective.get("plan") or None).slug if effective.get("plan") else "free")
    if _plan_rank(current) < _plan_rank(required_plan):
        raise HTTPException(status_code=402, detail={"code": "upgrade_required", "required_plan": required_plan})


def _seed_assistants(db: Session):
    defaults = [
        ("General Assistant", "General purpose workspace assistant.", "free"),
        ("Psychological Analyst", "Behavioral pattern analysis grounded in uploaded evidence.", "pro"),
        ("South African Legal Defense Expert", "South African defense-oriented legal analysis assistant.", "pro"),
        ("Document Research Assistant", "Finds and cites relevant workspace documents.", "free"),
    ]
    for name, desc, plan in defaults:
        if not db.query(AssistantProfile).filter(AssistantProfile.name == name).first():
            db.add(AssistantProfile(name=name, description=desc, required_plan=plan, enabled=True))
    db.commit()


@router.get("/assistants", response_model=list[AssistantProfileOut])
def list_assistants(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _seed_assistants(db)
    assistants = db.query(AssistantProfile).filter(AssistantProfile.enabled.is_(True)).order_by(AssistantProfile.name.asc()).all()
    return [AssistantProfileOut(id=a.id, name=a.name, description=a.description, required_plan=a.required_plan, default_prompt_template_id=a.default_prompt_template_id, enabled=a.enabled, locked=not can_use_assistant(db, user, a)) for a in assistants]
@router.post("/sessions")
def create_session(payload: CreateSessionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _seed_assistants(db)
    if not can_create_chat(db, user):
        require_upgrade("pro", "chat_sessions", "Upgrade to Pro to create more chat sessions.")
    if payload.assistant_id:
        assistant = db.query(AssistantProfile).filter(AssistantProfile.id == payload.assistant_id, AssistantProfile.enabled.is_(True)).first()
        if assistant and not can_use_assistant(db, user, assistant):
            require_upgrade("pro", "assistant_access", f"Upgrade to Pro to use {assistant.name}.")
    if payload.prompt_template_id and not can_create_custom_prompt(db, user):
        require_upgrade("pro", "custom_prompts", "Upgrade to Pro to use custom prompt templates.")
    session = ChatSession(user_id=user.id, title=payload.title, assistant_id=payload.assistant_id, prompt_template_id=payload.prompt_template_id)
    db.add(session)
    db.flush()
    for doc_id in (payload.linked_document_ids or []):
        db.add(ChatDocumentLink(session_id=session.id, document_id=doc_id))
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ChatSession).filter(ChatSession.user_id == user.id, ChatSession.is_deleted.is_(False)).order_by(ChatSession.updated_at.desc()).all()


@router.get("/sessions/{session_id}")
def get_session(session_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = _get_session_for_user(db, session_id, user.id)
    return {"session": s, "messages": s.messages, "linked_documents": [str(link.document_id) for link in s.document_links]}


@router.post("/sessions/{session_id}/messages")
def post_message(session_id: UUID, payload: MessageRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    enforce_feature(db, user.id, "chat")
    s = _get_session_for_user(db, session_id, user.id)
    if s.is_archived or s.is_deleted:
        raise HTTPException(status_code=400, detail="Chat session is archived or deleted")
    if s.assistant_id:
        assistant = db.query(AssistantProfile).filter(AssistantProfile.id == s.assistant_id, AssistantProfile.enabled.is_(True)).first()
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found or disabled")
        if not can_use_assistant(db, user, assistant):
            require_upgrade("pro", "legal_assistant", f"Upgrade to Pro to use {assistant.name}.")
    enforce_message_limit(db, user)
    enforce_limit(db, user.id, "processing_jobs_per_month", quantity=1)
    assistant_type = None
    if s.assistant_id:
        assistant_row = db.query(AssistantProfile).filter(AssistantProfile.id == s.assistant_id).first()
        assistant_type = assistant_row.name if assistant_row else None
    bot_settings, context, prompt = _build_chat_payload(db, user, payload, s.id, assistant_type)
    if not can_use_system_intelligence(db, user):
        context["system_intelligence_refs"] = []
        context["legal_web_refs"] = []
    prior_messages = _load_recent_session_messages(db, s.id, settings.CHAT_MAX_HISTORY_MESSAGES)
    user_message = ChatMessage(session_id=s.id, role="user", content=payload.message, metadata_json={"assistant_id": str(s.assistant_id) if s.assistant_id else None, "prompt_template_id": str(s.prompt_template_id) if s.prompt_template_id else None})
    start = time.perf_counter()
    success = False
    if not prompt:
        assistant_content = "Not enough information was found in accessible Timebot documents to answer this confidently."
    else:
        model_call_start = time.perf_counter()
        try:
            response = openai_client_service.generate_completion({
                "model": bot_settings.model,
                "temperature": bot_settings.temperature,
                "max_tokens": bot_settings.max_tokens,
                "messages": _build_model_messages(db, bot_settings, prompt, prior_messages),
            })
        except APIError as exc:
            logger.info(
                "chat_model_call_timing",
                extra={
                    "event": "chat_model_call_timing",
                    "user_id": str(user.id),
                    "session_id": str(s.id),
                    "duration_ms": round((time.perf_counter() - model_call_start) * 1000, 2),
                    "success": False,
                },
            )
            _log_chat_request(session_id=s.id, user_id=user.id, endpoint_type="non_streaming", retrieval_count=len(context.get("source_refs", [])), history_count=len(prior_messages), success=False, latency_ms=(time.perf_counter()-start)*1000)
            raise HTTPException(status_code=503, detail=f"Chat AI request failed: {exc}") from exc
        logger.info(
            "chat_model_call_timing",
            extra={
                "event": "chat_model_call_timing",
                "user_id": str(user.id),
                "session_id": str(s.id),
                "duration_ms": round((time.perf_counter() - model_call_start) * 1000, 2),
                "success": True,
            },
        )
        assistant_content = (response.choices[0].message.content or "").strip() or "Not enough information was found in accessible Timebot documents."
        assistant_content = _append_sources(assistant_content, context["source_refs"])
    success = True
    assistant_message = ChatMessage(session_id=s.id, role="assistant", content=assistant_content, source_refs=context["source_refs"], metadata_json={"assistant_id": str(s.assistant_id) if s.assistant_id else None, "prompt_template_id": str(s.prompt_template_id) if s.prompt_template_id else None, "model": bot_settings.model, "provider": "openai", "document_references": context["source_refs"], "user_evidence_refs": context.get("user_evidence_refs", []), "system_intelligence_refs": context.get("system_intelligence_refs", []), "legal_web_refs": context.get("legal_web_refs", []), "retrieval_meta": context.get("retrieval_meta", {})})
    db.add(user_message)
    db.add(assistant_message)
    db.commit()
    db.commit()
    _log_chat_request(session_id=s.id, user_id=user.id, endpoint_type="non_streaming", retrieval_count=len(context.get("source_refs", [])), history_count=len(prior_messages), success=success, latency_ms=(time.perf_counter()-start)*1000)
    return {"message": assistant_message.content, "source_refs": context["source_refs"]}


@router.post("/sessions/{session_id}/messages/stream")
def stream_message(session_id: UUID, payload: MessageRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    enforce_feature(db, user.id, "chat")
    s = _get_session_for_user(db, session_id, user.id)
    if s.is_archived or s.is_deleted:
        raise HTTPException(status_code=400, detail="Chat session is archived or deleted")
    if s.assistant_id:
        assistant = db.query(AssistantProfile).filter(AssistantProfile.id == s.assistant_id, AssistantProfile.enabled.is_(True)).first()
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found or disabled")
        if not can_use_assistant(db, user, assistant):
            require_upgrade("pro", "legal_assistant", f"Upgrade to Pro to use {assistant.name}.")
    enforce_message_limit(db, user)
    enforce_limit(db, user.id, "processing_jobs_per_month", quantity=1)
    bot_settings, context, prompt = _build_chat_payload(db, user, payload, s.id)
    if not can_use_system_intelligence(db, user):
        context["system_intelligence_refs"] = []
        context["legal_web_refs"] = []
    prior_messages = _load_recent_session_messages(db, s.id, settings.CHAT_MAX_HISTORY_MESSAGES)

    def _event(event_type: str, data: dict) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    def event_stream():
        start = time.perf_counter()
        success = False
        user_message = ChatMessage(session_id=s.id, role="user", content=payload.message, metadata_json={"assistant_id": str(s.assistant_id) if s.assistant_id else None, "prompt_template_id": str(s.prompt_template_id) if s.prompt_template_id else None})
        db.add(user_message)

        if not prompt:
            assistant_text = "Not enough information was found in accessible Timebot documents to answer this confidently."
            yield _event("chunk", {"delta": assistant_text})
        else:
            assistant_parts: list[str] = []
            model_call_start = time.perf_counter()
            try:
                stream = openai_client_service.stream_completion({
                    "model": bot_settings.model,
                    "temperature": bot_settings.temperature,
                    "max_tokens": bot_settings.max_tokens,
                    "messages": _build_model_messages(db, bot_settings, prompt, prior_messages),
                })
            except APIError as exc:
                logger.info(
                    "chat_model_call_timing",
                    extra={
                        "event": "chat_model_call_timing",
                        "user_id": str(user.id),
                        "session_id": str(s.id),
                        "duration_ms": round((time.perf_counter() - model_call_start) * 1000, 2),
                        "success": False,
                    },
                )
                _log_chat_request(session_id=s.id, user_id=user.id, endpoint_type="streaming", retrieval_count=len(context.get("source_refs", [])), history_count=len(prior_messages), success=False, latency_ms=(time.perf_counter()-start)*1000)
                raise HTTPException(status_code=503, detail=f"Chat AI request failed: {exc}") from exc

            for chunk in stream:
                choice = chunk.choices[0] if getattr(chunk, 'choices', None) else None
                delta = (getattr(getattr(choice, 'delta', None), 'content', None) or '')
                if delta:
                    assistant_parts.append(delta)
                    yield _event("chunk", {"delta": delta})
            assistant_text = "".join(assistant_parts).strip() or "Not enough information was found in accessible Timebot documents."
            logger.info(
                "chat_model_call_timing",
                extra={
                    "event": "chat_model_call_timing",
                    "user_id": str(user.id),
                    "session_id": str(s.id),
                    "duration_ms": round((time.perf_counter() - model_call_start) * 1000, 2),
                    "success": True,
                },
            )

        assistant_text = _append_sources(assistant_text, context["source_refs"])
        assistant_message = ChatMessage(session_id=s.id, role="assistant", content=assistant_text, source_refs=context["source_refs"], metadata_json={"user_evidence_refs": context.get("user_evidence_refs", []), "system_intelligence_refs": context.get("system_intelligence_refs", []), "legal_web_refs": context.get("legal_web_refs", [])})
        db.add(assistant_message)
        db.commit()
        success = True
        _log_chat_request(session_id=s.id, user_id=user.id, endpoint_type="streaming", retrieval_count=len(context.get("source_refs", [])), history_count=len(prior_messages), success=success, latency_ms=(time.perf_counter()-start)*1000)

        yield _event("final", {"message": assistant_text, "source_refs": context["source_refs"]})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.patch("/sessions/{session_id}")
def update_session(session_id: UUID, payload: UpdateSessionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = _get_session_for_user(db, session_id, user.id)
    if payload.title is not None:
        s.title = payload.title
    if payload.is_archived is not None:
        s.is_archived = payload.is_archived
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/sessions/{session_id}")
def delete_session(session_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = _get_session_for_user(db, session_id, user.id)
    s.is_deleted = True
    db.add(s)
    db.commit()
    return {"deleted": True}


@router.get("/sessions/{session_id}/messages")
def list_session_messages(session_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = _get_session_for_user(db, session_id, user.id)
    return db.query(ChatMessage).filter(ChatMessage.session_id == s.id).order_by(ChatMessage.created_at.asc()).all()
