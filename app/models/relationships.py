import uuid
from sqlalchemy import (
    Column, String, Integer, BigInteger, Float, Boolean, Text,
    TIMESTAMP, ForeignKey, CheckConstraint, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class DocumentRelationship(Base):
    __tablename__ = "document_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_doc_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_doc_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type = Column(String(50), nullable=False, index=True)
    confidence = Column(Float)
    relationship_metadata = Column("metadata", JSONB, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    source_document = relationship(
        "Document", foreign_keys=[source_doc_id], back_populates="outgoing_relationships"
    )
    target_document = relationship(
        "Document", foreign_keys=[target_doc_id], back_populates="incoming_relationships"
    )

    __table_args__ = (
        CheckConstraint(
            "relationship_type IN ('similar_to', 'references', 'follows_up', 'related_to', 'duplicates')",
            name="valid_relationship_type",
        ),
        CheckConstraint("source_doc_id != target_doc_id", name="no_self_reference"),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="valid_relationship_confidence",
        ),
        UniqueConstraint("source_doc_id", "target_doc_id", "relationship_type", name="unique_relationship"),
    )


class Connection(Base):
    __tablename__ = "connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False, index=True)
    status = Column(String(50), default="disconnected", index=True)
    display_name = Column(String(255), nullable=False)
    email = Column(String(255))
    last_sync_date = Column(TIMESTAMP(timezone=True), index=True)
    last_sync_status = Column(String(50))
    sync_progress = Column(Integer, default=0)
    document_count = Column(Integer, default=0)
    total_size = Column(BigInteger, default=0)
    auto_sync = Column(Boolean, default=True)
    sync_interval = Column(Integer, default=15)
    is_authenticated = Column(Boolean, default=False)
    external_account_id = Column(String(255))
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_scopes = Column(JSONB, default=list)
    token_expires_at = Column(TIMESTAMP(timezone=True))
    oauth_state = Column(String(255))
    oauth_state_expires_at = Column(TIMESTAMP(timezone=True))
    last_error_message = Column(Text)
    last_error_at = Column(TIMESTAMP(timezone=True))
    sync_state = Column(JSONB, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    owner = relationship("User", back_populates="connections")
    documents = relationship("Document", back_populates="connection")
    sync_logs = relationship(
        "SyncLog", back_populates="connection", cascade="all, delete-orphan",
        order_by="SyncLog.start_time.desc()",
    )

    __table_args__ = (
        CheckConstraint("type IN ('gmail', 'gdrive', 'dropbox', 'onedrive')", name="valid_connection_type"),
        CheckConstraint(
            "status IN ('connected', 'disconnected', 'error', 'syncing', 'auth_pending')", name="valid_connection_status"
        ),
        CheckConstraint(
            "last_sync_status IS NULL OR last_sync_status IN ('success', 'failed', 'partial', 'in_progress')",
            name="valid_sync_status",
        ),
        CheckConstraint("sync_progress >= 0 AND sync_progress <= 100", name="valid_sync_progress"),
        UniqueConstraint("user_id", "type", name="unique_connection_per_user"),
    )


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(
        UUID(as_uuid=True), ForeignKey("connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_time = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    end_time = Column(TIMESTAMP(timezone=True))
    status = Column(String(50), default="in_progress", index=True)
    documents_added = Column(Integer, default=0)
    documents_updated = Column(Integer, default=0)
    documents_failed = Column(Integer, default=0)
    bytes_synced = Column(BigInteger, default=0)
    error_message = Column(Text)
    error_details = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    connection = relationship("Connection", back_populates="sync_logs")

    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failed', 'partial', 'in_progress')", name="valid_sync_log_status"
        ),
    )


class ProcessingQueue(Base):
    __tablename__ = "processing_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    task_type = Column(String(50), nullable=False, index=True)
    status = Column(String(50), default="queued", index=True)
    priority = Column(Integer, default=5, index=True)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    error_message = Column(Text)
    error_details = Column(JSONB)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))

    document = relationship("Document", back_populates="queue_items")

    __table_args__ = (
        CheckConstraint(
            "task_type IN ('extract_text', 'ai_analysis', 'generate_thumbnail', 'embed_document', 'detect_relationships')",
            name="valid_task_type",
        ),
        CheckConstraint(
            "status IN ('queued', 'processing', 'completed', 'failed')", name="valid_queue_status"
        ),
        CheckConstraint("priority >= 1 AND priority <= 10", name="valid_priority"),
        UniqueConstraint("document_id", "task_type", name="unique_document_task"),
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number = Column(Integer, nullable=False)
    changed_fields = Column(JSONB, default=list)
    snapshot = Column(JSONB, nullable=False)
    changed_by = Column(String(50))
    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), index=True)

    document = relationship("Document", back_populates="versions")

    __table_args__ = (
        CheckConstraint(
            "changed_by IS NULL OR changed_by IN ('user', 'ai', 'sync')", name="valid_changed_by"
        ),
        UniqueConstraint("document_id", "version_number", name="unique_document_version"),
    )


class GmailImportRule(Base):
    __tablename__ = "gmail_import_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_email = Column(String(255), nullable=False, index=True)
    query = Column(String(255))
    include_attachments = Column(Boolean, default=False, nullable=False)
    max_results = Column(Integer, default=20, nullable=False)
    last_imported_at = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())


class GmailImportedMessage(Base):
    __tablename__ = "gmail_imported_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    gmail_message_id = Column(String(255), nullable=False, index=True)
    gmail_thread_id = Column(String(255))
    sender = Column(String(255))
    subject = Column(String(255))
    received_at = Column(TIMESTAMP(timezone=True))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "gmail_message_id", name="uq_gmail_imported_message_per_user"),
    )


class GmailImportedAttachment(Base):
    __tablename__ = "gmail_imported_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    gmail_message_id = Column(String(255), nullable=False, index=True)
    attachment_id = Column(String(255), nullable=False)
    filename = Column(String(255))
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "gmail_message_id", "attachment_id", name="uq_gmail_imported_attachment_per_user"),
    )
