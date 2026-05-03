import uuid

from sqlalchemy import Boolean, Column, Integer, Numeric, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class PromptExecutionLog(Base):
    __tablename__ = "prompt_execution_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prompt_template_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    purpose = Column(String(64), nullable=True, index=True)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    provider = Column(String(32), nullable=False, index=True)
    model = Column(String(120), nullable=False, index=True)
    fallback_used = Column(Boolean, nullable=False, default=False, index=True)
    fallback_reason = Column(String(64), nullable=True)
    primary_provider = Column(String(32), nullable=True)
    primary_model = Column(String(120), nullable=True)
    primary_error = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=True, index=True)
    error_message = Column(Text, nullable=True)
    source = Column(String(128), nullable=True, index=True)
    estimated_cost_usd = Column(Numeric(12, 6), nullable=True)
    currency = Column(String(8), nullable=True)
    pricing_known = Column(Boolean, nullable=False, default=False, server_default="false", index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), index=True)
