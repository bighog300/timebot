import uuid

from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(40), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    link_url = Column(String(1024), nullable=True)
    read_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    metadata_json = Column(JSONB, nullable=False, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), index=True)


class UserMessageThread(Base):
    __tablename__ = "user_message_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(40), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    status = Column(String(40), nullable=False, default="open", index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    messages = relationship("UserMessage", back_populates="thread", cascade="all, delete-orphan")


class UserMessage(Base):
    __tablename__ = "user_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    thread_id = Column(UUID(as_uuid=True), ForeignKey("user_message_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    sender_type = Column(String(20), nullable=False, index=True)
    body = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), index=True)

    thread = relationship("UserMessageThread", back_populates="messages")
