import uuid

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class ChatbotSettings(Base):
    __tablename__ = "chatbot_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_prompt = Column(Text, nullable=False)
    retrieval_prompt = Column(Text, nullable=False)
    report_prompt = Column(Text, nullable=False)
    citation_prompt = Column(Text, nullable=False)
    default_report_template = Column(Text, nullable=False)
    model = Column(String(100), nullable=False, default="gpt-4.1-mini")
    temperature = Column(Float, nullable=False, default=0.2)
    max_tokens = Column(Integer, nullable=False, default=1200)
    max_documents = Column(Integer, nullable=False, default=8)
    allow_full_text_retrieval = Column(Boolean, nullable=False, default=True)
    prompt_daily_cost_threshold_usd = Column(Float, nullable=True)
    prompt_monthly_cost_threshold_usd = Column(Float, nullable=True)
    prompt_user_cost_threshold_usd = Column(Float, nullable=True)
    prompt_workspace_cost_threshold_usd = Column(Float, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    updated_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)

    updated_by = relationship("User")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, default="New chat")
    assistant_id = Column(UUID(as_uuid=True), ForeignKey("assistant_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    prompt_template_id = Column(UUID(as_uuid=True), ForeignKey("prompt_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    is_archived = Column(Boolean, nullable=False, default=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    user = relationship("User")
    assistant = relationship("AssistantProfile")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    document_links = relationship("ChatDocumentLink", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    source_refs = Column(JSONB, default=list)
    metadata_json = Column(JSONB, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())

    session = relationship("ChatSession", back_populates="messages")


class AssistantProfile(Base):
    __tablename__ = "assistant_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(120), nullable=False, unique=True)
    description = Column(Text, nullable=False)
    required_plan = Column(String(50), nullable=False, default="free")
    default_prompt_template_id = Column(UUID(as_uuid=True), ForeignKey("prompt_templates.id", ondelete="SET NULL"), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    default_prompt_template = relationship("PromptTemplate", foreign_keys=[default_prompt_template_id])


class ChatDocumentLink(Base):
    __tablename__ = "chat_document_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())

    session = relationship("ChatSession", back_populates="document_links")


class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)
    content_markdown = Column(Text, nullable=False)
    sections = Column(JSONB, nullable=True)
    source_document_ids = Column(JSONB, default=list)
    source_refs = Column(JSONB, default=list)
    file_path = Column(Text)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    created_by = relationship("User")
