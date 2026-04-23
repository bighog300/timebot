"""
Additional Models
DocumentRelationship, Connection, SyncLog, ProcessingQueue, DocumentVersion
"""

from sqlalchemy import (
    Column, String, Integer, BigInteger, Float, Boolean, Text,
    TIMESTAMP, ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


# ============================================================================
# DOCUMENT RELATIONSHIPS
# ============================================================================

class DocumentRelationship(Base):
    """
    Relationships between documents (similar, references, etc.)
    """
    __tablename__ = "document_relationships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    source_doc_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    target_doc_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    relationship_type = Column(String(50), nullable=False, index=True)
    confidence = Column(Float)
    metadata = Column(JSONB, default=dict)

    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    # Relationships
    source_document = relationship(
        "Document",
        foreign_keys=[source_doc_id],
        back_populates="outgoing_relationships"
    )
    target_document = relationship(
        "Document",
        foreign_keys=[target_doc_id],
        back_populates="incoming_relationships"
    )

    __table_args__ = (
        CheckConstraint(
            "relationship_type IN ('similar_to', 'references', 'follows_up', 'related_to', 'duplicates')",
            name="valid_relationship_type"
        ),
        CheckConstraint(
            "source_doc_id != target_doc_id",
            name="no_self_reference"
        ),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="valid_relationship_confidence"
        ),
        UniqueConstraint(
            "source_doc_id", "target_doc_id", "relationship_type",
            name="unique_relationship"
        ),
    )

    def __repr__(self):
        return f"<DocumentRelationship({self.relationship_type}: {self.source_doc_id} -> {self.target_doc_id})>"


# ============================================================================
# CONNECTIONS (Cloud Services)
# ============================================================================

class Connection(Base):
    """
    Cloud service connections (Gmail, Google Drive, Dropbox, etc.)
    """
    __tablename__ = "connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Connection details
    type = Column(String(50), nullable=False, index=True)
    status = Column(String(50), default="disconnected", index=True)

    display_name = Column(String(255), nullable=False)
    email = Column(String(255))

    # Sync information
    last_sync_date = Column(TIMESTAMP(timezone=True), index=True)
    last_sync_status = Column(String(50))
    sync_progress = Column(Integer, default=0)

    # Statistics
    document_count = Column(Integer, default=0)
    total_size = Column(BigInteger, default=0)

    # Settings
    auto_sync = Column(Boolean, default=True)
    sync_interval = Column(Integer, default=15)  # minutes

    # Authentication
    is_authenticated = Column(Boolean, default=False)
    token_expires_at = Column(TIMESTAMP(timezone=True))

    # Sync state for incremental syncing
    sync_state = Column(JSONB, default=dict)

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    documents = relationship("Document", back_populates="connection")
    sync_logs = relationship(
        "SyncLog",
        back_populates="connection",
        cascade="all, delete-orphan",
        order_by="SyncLog.start_time.desc()"
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('gmail', 'gdrive', 'dropbox', 'onedrive')",
            name="valid_connection_type"
        ),
        CheckConstraint(
            "status IN ('connected', 'disconnected', 'error', 'syncing')",
            name="valid_connection_status"
        ),
        CheckConstraint(
            "last_sync_status IS NULL OR last_sync_status IN ('success', 'failed', 'partial', 'in_progress')",
            name="valid_sync_status"
        ),
        CheckConstraint(
            "sync_progress >= 0 AND sync_progress <= 100",
            name="valid_sync_progress"
        ),
        UniqueConstraint("type", name="unique_connection_type"),
    )

    def __repr__(self):
        return f"<Connection(type={self.type}, status={self.status}, email={self.email})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "type": self.type,
            "status": self.status,
            "display_name": self.display_name,
            "email": self.email,
            "last_sync_date": self.last_sync_date.isoformat() if self.last_sync_date else None,
            "last_sync_status": self.last_sync_status,
            "sync_progress": self.sync_progress,
            "document_count": self.document_count,
            "is_authenticated": self.is_authenticated,
        }


# ============================================================================
# SYNC LOGS
# ============================================================================

class SyncLog(Base):
    """
    Audit log of sync operations
    """
    __tablename__ = "sync_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    connection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    start_time = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    end_time = Column(TIMESTAMP(timezone=True))

    status = Column(String(50), default="in_progress", index=True)

    # Statistics
    documents_added = Column(Integer, default=0)
    documents_updated = Column(Integer, default=0)
    documents_failed = Column(Integer, default=0)
    bytes_synced = Column(BigInteger, default=0)

    # Error information
    error_message = Column(Text)
    error_details = Column(JSONB)

    created_at = Column(TIMESTAMP(timezone=True), default=func.now())

    # Relationships
    connection = relationship("Connection", back_populates="sync_logs")

    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failed', 'partial', 'in_progress')",
            name="valid_sync_log_status"
        ),
    )

    def __repr__(self):
        return f"<SyncLog(connection={self.connection_id}, status={self.status}, added={self.documents_added})>"


# ============================================================================
# PROCESSING QUEUE
# ============================================================================

class ProcessingQueue(Base):
    """
    Queue for background document processing tasks
    """
    __tablename__ = "processing_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    task_type = Column(String(50), nullable=False, index=True)
    status = Column(String(50), default="queued", index=True)
    priority = Column(Integer, default=5, index=True)

    # Retry logic
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)

    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSONB)

    # Timing
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    started_at = Column(TIMESTAMP(timezone=True))
    completed_at = Column(TIMESTAMP(timezone=True))

    # Relationships
    document = relationship("Document", back_populates="queue_items")

    __table_args__ = (
        CheckConstraint(
            "task_type IN ('extract_text', 'ai_analysis', 'generate_thumbnail', 'embed_document', 'detect_relationships')",
            name="valid_task_type"
        ),
        CheckConstraint(
            "status IN ('queued', 'processing', 'completed', 'failed')",
            name="valid_queue_status"
        ),
        CheckConstraint(
            "priority >= 1 AND priority <= 10",
            name="valid_priority"
        ),
        UniqueConstraint(
            "document_id", "task_type",
            name="unique_document_task"
        ),
    )

    def __repr__(self):
        return f"<ProcessingQueue(task={self.task_type}, status={self.status}, doc={self.document_id})>"


# ============================================================================
# DOCUMENT VERSIONS
# ============================================================================

class DocumentVersion(Base):
    """
    Version history for documents
    """
    __tablename__ = "document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    version_number = Column(Integer, nullable=False)

    # Change tracking
    changed_fields = Column(JSONB, default=list)
    snapshot = Column(JSONB, nullable=False)
    changed_by = Column(String(50))

    created_at = Column(TIMESTAMP(timezone=True), default=func.now(), index=True)

    # Relationships
    document = relationship("Document", back_populates="versions")

    __table_args__ = (
        CheckConstraint(
            "changed_by IS NULL OR changed_by IN ('user', 'ai', 'sync')",
            name="valid_changed_by"
        ),
        UniqueConstraint(
            "document_id", "version_number",
            name="unique_document_version"
        ),
    )

    def __repr__(self):
        return f"<DocumentVersion(doc={self.document_id}, version={self.version_number})>"
