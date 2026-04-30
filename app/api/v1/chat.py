from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.api.v1.admin import _get_or_create_chatbot_settings
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.services.chat_retrieval import retrieve_chat_context
from app.services.openai_client import APIError, openai_client_service

router = APIRouter(prefix="/chat", tags=["chat"])


class CreateSessionRequest(BaseModel):
    title: str = "New chat"


class MessageRequest(BaseModel):
    message: str
    document_ids: list[str] | None = None
    include_timeline: bool = True
    include_full_text: bool = False


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
    s = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": s, "messages": s.messages}


@router.post("/sessions/{session_id}/messages")
def post_message(session_id: UUID, payload: MessageRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user.id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    bot_settings = _get_or_create_chatbot_settings(db)
    if not openai_client_service.enabled:
        raise HTTPException(status_code=503, detail="Chat AI is unavailable: OPENAI_API_KEY is not configured.")
    user_message = ChatMessage(session_id=s.id, role="user", content=payload.message)
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
        assistant_content = "Not enough information was found in accessible Timebot documents to answer this confidently."
    else:
        prompt = (
            f"{bot_settings.retrieval_prompt}\n\n"
            f"Context:\n{context}\n\n"
            f"Question:\n{payload.message}\n\n"
            f"{bot_settings.citation_prompt}\n"
            "Only answer using provided context. If uncertain, explicitly say evidence is insufficient."
        )
        try:
            response = openai_client_service.client.chat.completions.create(
                model=bot_settings.model,
                temperature=bot_settings.temperature,
                max_tokens=bot_settings.max_tokens,
                messages=[
                    {"role": "system", "content": bot_settings.system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
        except APIError as exc:
            raise HTTPException(status_code=503, detail=f"Chat AI request failed: {exc}") from exc
        assistant_content = (response.choices[0].message.content or "").strip() or "Not enough information was found in accessible Timebot documents."
        if context["source_refs"]:
            sources_lines = []
            for idx, ref in enumerate(context["source_refs"][:8], 1):
                date_hint = f", {ref.get('timeline_date')}" if ref.get("kind") == "timeline_event" and ref.get("timeline_date") else ""
                sources_lines.append(f"{idx}. {ref.get('document_title')} — {ref.get('kind')}{date_hint}")
            assistant_content += "\n\nSources:\n" + "\n".join(sources_lines)
    assistant_message = ChatMessage(session_id=s.id, role="assistant", content=assistant_content, source_refs=context["source_refs"])
    db.add(user_message)
    db.add(assistant_message)
    db.commit()
    return {"message": assistant_message.content, "source_refs": context["source_refs"]}
