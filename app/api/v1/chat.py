from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])


class CreateSessionRequest(BaseModel):
    title: str = "New chat"


class MessageRequest(BaseModel):
    message: str


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
    user_message = ChatMessage(session_id=s.id, role="user", content=payload.message)
    assistant_message = ChatMessage(session_id=s.id, role="assistant", content="Not enough information found in accessible Timebot documents.", source_refs=[])
    db.add(user_message)
    db.add(assistant_message)
    db.commit()
    return {"message": assistant_message.content, "source_refs": []}
