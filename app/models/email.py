import uuid

from sqlalchemy import Boolean, Column, ForeignKey, String, Text, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.db.base import Base


class EmailProviderConfig(Base):
    __tablename__ = "email_provider_configs"
    __table_args__ = (UniqueConstraint("provider", name="uq_email_provider_configs_provider"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(32), nullable=False, index=True)
    enabled = Column(Boolean, nullable=False, default=False)
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=True)
    reply_to = Column(String(255), nullable=True)
    api_key_encrypted = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())


class EmailTemplate(Base):
    __tablename__ = "email_templates"
    __table_args__ = (UniqueConstraint("slug", name="uq_email_templates_slug"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    category = Column(String(32), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="draft", index=True)
    subject = Column(String(500), nullable=False)
    preheader = Column(String(500), nullable=True)
    html_body = Column(Text, nullable=False)
    text_body = Column(Text, nullable=True)
    variables_json = Column(JSONB, nullable=False, default=dict)
    created_by_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())


class EmailSendLog(Base):
    __tablename__ = "email_send_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(32), nullable=False, index=True)
    recipient_email = Column(String(255), nullable=False, index=True)
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=True)
    reply_to = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("email_templates.id", ondelete="SET NULL"), nullable=True)
    campaign_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(16), nullable=False, default="queued", index=True)
    provider_message_id = Column(String(255), nullable=True)
    error_message_sanitized = Column(Text, nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    sent_at = Column(TIMESTAMP(timezone=True), nullable=True)
    failed_at = Column(TIMESTAMP(timezone=True), nullable=True)
