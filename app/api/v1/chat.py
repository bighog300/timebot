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
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.services.chat_retrieval import retrieve_chat_context
from app.services.openai_client import APIError, openai_client_service
from app.config import settings

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


class CreateSessionRequest(BaseModel):
    title: str = "New chat"


class MessageRequest(BaseModel):
    message: str
    document_ids: list[str] | None = None
    include_timeline: bool = True
    include_full_text: bool = False


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


def _build_model_messages(bot_settings, prompt: str, prior_messages: list[dict]) -> list[dict]:
    model_messages = [{"role": "system", "content": bot_settings.system_prompt}]
    model_messages.extend(prior_messages)
    model_messages.append({"role": "user", "content": prompt})
    return model_messages


def _build_chat_payload(db: Session, user: User, payload: MessageRequest):
    bot_settings = _get_or_create_chatbot_settings(db)
    if not openai_client_service.enabled:
        raise HTTPException(status_code=503, detail="Chat AI is unavailable: OPENAI_API_KEY is not configured.")
    context = retrieve_chat_context(
        db=db,
        query=payload.message,
        user_id=user.id,
        document_ids=payload.document_ids,
        include_timeline=payload.include_timeline,
        include_full_text=payload.include_full_text and bot_settings.allow_full_text_retrieval,
        max_documents=bot_settings.max_documents,
    )
    if not context["documents"]:
        return bot_settings, context, None
    prompt = (
        f"{bot_settings.retrieval_prompt}\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{payload.message}\n\n"
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


@router.post("/sessions")
def create_session(payload: CreateSessionRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    session = ChatSession(user_id=user.id, title=payload.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions")
def list_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ChatSession).filter(ChatSession.user_id == user.id).order_by(ChatSession.updated_at.desc()).all()


@router.get("/sessions/{session_id}")
def get_session(session_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = _get_session_for_user(db, session_id, user.id)
    return {"session": s, "messages": s.messages}


@router.post("/sessions/{session_id}/messages")
def post_message(session_id: UUID, payload: MessageRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = _get_session_for_user(db, session_id, user.id)
    bot_settings, context, prompt = _build_chat_payload(db, user, payload)
    prior_messages = _load_recent_session_messages(db, s.id, settings.CHAT_MAX_HISTORY_MESSAGES)
    user_message = ChatMessage(session_id=s.id, role="user", content=payload.message)
    start = time.perf_counter()
    success = False
    if not prompt:
        assistant_content = "Not enough information was found in accessible Timebot documents to answer this confidently."
    else:
        try:
            response = openai_client_service.client.chat.completions.create(
                model=bot_settings.model,
                temperature=bot_settings.temperature,
                max_tokens=bot_settings.max_tokens,
                messages=_build_model_messages(bot_settings, prompt, prior_messages),
            )
        except APIError as exc:
            _log_chat_request(session_id=s.id, user_id=user.id, endpoint_type="non_streaming", retrieval_count=len(context.get("source_refs", [])), history_count=len(prior_messages), success=False, latency_ms=(time.perf_counter()-start)*1000)
            raise HTTPException(status_code=503, detail=f"Chat AI request failed: {exc}") from exc
        assistant_content = (response.choices[0].message.content or "").strip() or "Not enough information was found in accessible Timebot documents."
        assistant_content = _append_sources(assistant_content, context["source_refs"])
    success = True
    assistant_message = ChatMessage(session_id=s.id, role="assistant", content=assistant_content, source_refs=context["source_refs"])
    db.add(user_message)
    db.add(assistant_message)
    db.commit()
    _log_chat_request(session_id=s.id, user_id=user.id, endpoint_type="non_streaming", retrieval_count=len(context.get("source_refs", [])), history_count=len(prior_messages), success=success, latency_ms=(time.perf_counter()-start)*1000)
    return {"message": assistant_message.content, "source_refs": context["source_refs"]}


@router.post("/sessions/{session_id}/messages/stream")
def stream_message(session_id: UUID, payload: MessageRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = _get_session_for_user(db, session_id, user.id)
    bot_settings, context, prompt = _build_chat_payload(db, user, payload)
    prior_messages = _load_recent_session_messages(db, s.id, settings.CHAT_MAX_HISTORY_MESSAGES)

    def _event(event_type: str, data: dict) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

    def event_stream():
        start = time.perf_counter()
        success = False
        user_message = ChatMessage(session_id=s.id, role="user", content=payload.message)
        db.add(user_message)

        if not prompt:
            assistant_text = "Not enough information was found in accessible Timebot documents to answer this confidently."
            yield _event("chunk", {"delta": assistant_text})
        else:
            assistant_parts: list[str] = []
            try:
                stream = openai_client_service.client.chat.completions.create(
                    model=bot_settings.model,
                    temperature=bot_settings.temperature,
                    max_tokens=bot_settings.max_tokens,
                    messages=_build_model_messages(bot_settings, prompt, prior_messages),
                    stream=True,
                )
            except APIError as exc:
                _log_chat_request(session_id=s.id, user_id=user.id, endpoint_type="streaming", retrieval_count=len(context.get("source_refs", [])), history_count=len(prior_messages), success=False, latency_ms=(time.perf_counter()-start)*1000)
                raise HTTPException(status_code=503, detail=f"Chat AI request failed: {exc}") from exc

            for chunk in stream:
                choice = chunk.choices[0] if getattr(chunk, 'choices', None) else None
                delta = (getattr(getattr(choice, 'delta', None), 'content', None) or '')
                if delta:
                    assistant_parts.append(delta)
                    yield _event("chunk", {"delta": delta})
            assistant_text = "".join(assistant_parts).strip() or "Not enough information was found in accessible Timebot documents."

        assistant_text = _append_sources(assistant_text, context["source_refs"])
        assistant_message = ChatMessage(session_id=s.id, role="assistant", content=assistant_text, source_refs=context["source_refs"])
        db.add(assistant_message)
        db.commit()
        success = True
        _log_chat_request(session_id=s.id, user_id=user.id, endpoint_type="streaming", retrieval_count=len(context.get("source_refs", [])), history_count=len(prior_messages), success=success, latency_ms=(time.perf_counter()-start)*1000)

        yield _event("final", {"message": assistant_text, "source_refs": context["source_refs"]})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
