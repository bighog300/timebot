import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.db.base import Base


class DocumentProcessingEvent(Base):
    __tablename__ = "document_processing_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    stage = Column(String(50), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="info", index=True)
    duration_ms = Column(Integer)
    provider = Column(String(50))
    model = Column(String(100))
    ai_call_count = Column(Integer)
    parse_retry_used = Column(String(10))
    error_type = Column(String(100))
    safe_metadata = Column(JSONB, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now(), index=True)

