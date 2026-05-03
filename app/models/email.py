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
    webhook_secret_encrypted = Column(Text, nullable=True)
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


class EmailCampaign(Base):
    __tablename__ = "email_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey("email_templates.id", ondelete="RESTRICT"), nullable=False)
    audience_type = Column(String(64), nullable=False, default="all_users")
    audience_filters_json = Column(JSONB, nullable=True)
    status = Column(String(32), nullable=False, default="draft", index=True)
    subject_override = Column(String(500), nullable=True)
    preheader_override = Column(String(500), nullable=True)
    variables_json = Column(JSONB, nullable=True)
    created_by_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    send_started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    send_completed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    send_failed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    send_error_sanitized = Column(Text, nullable=True)


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


class EmailSuppression(Base):
    __tablename__ = "email_suppressions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    reason = Column(String(32), nullable=False)
    source = Column(String(255), nullable=True)
    created_by_admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())


class EmailCampaignRecipient(Base):
    __tablename__ = "email_campaign_recipients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("email_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    skip_reason = Column(String(255), nullable=True)
    send_log_id = Column(UUID(as_uuid=True), ForeignKey("email_send_logs.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    queued_at = Column(TIMESTAMP(timezone=True), nullable=True)
    sent_at = Column(TIMESTAMP(timezone=True), nullable=True)
    failed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    delivered_at = Column(TIMESTAMP(timezone=True), nullable=True)
    bounced_at = Column(TIMESTAMP(timezone=True), nullable=True)
    complained_at = Column(TIMESTAMP(timezone=True), nullable=True)
    provider_event_id = Column(String(255), nullable=True)
    last_event_at = Column(TIMESTAMP(timezone=True), nullable=True)


class EmailProviderEvent(Base):
    __tablename__ = "email_provider_events"
    __table_args__ = (UniqueConstraint("provider", "provider_event_id", name="uq_email_provider_event_provider_event_id"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(32), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    provider_event_id = Column(String(255), nullable=True, index=True)
    provider_message_id = Column(String(255), nullable=True, index=True)
    recipient_email = Column(String(255), nullable=True, index=True)
    campaign_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    send_log_id = Column(UUID(as_uuid=True), ForeignKey("email_send_logs.id", ondelete="SET NULL"), nullable=True)
    payload_json_sanitized = Column(JSONB, nullable=False, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
