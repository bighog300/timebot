import uuid

from sqlalchemy import Boolean, Column, Float, Integer, String, Text, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    __table_args__ = (
        UniqueConstraint("type", "name", "version", name="uq_prompt_templates_type_name_version"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(64), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=False, index=True)
    provider = Column(String(32), nullable=False, default="openai")
    model = Column(String(120), nullable=False, default="gpt-4o-mini")
    temperature = Column(Float, nullable=False, default=0.2)
    max_tokens = Column(Integer, nullable=False, default=800)
    top_p = Column(Float, nullable=False, default=1.0)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    is_default = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
