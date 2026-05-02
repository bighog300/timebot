import uuid
from sqlalchemy import (
    Column, String, Integer, BigInteger, Float, Boolean, Text,
    TIMESTAMP, ForeignKey, CheckConstraint, ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    filename = Column(String(255), nullable=False, index=True)
    original_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False, index=True)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))

    upload_date = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), index=True)
    last_modified = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())
    processed_date = Column(TIMESTAMP(timezone=True))

    raw_text = Column(Text)
    page_count = Column(Integer)
    word_count = Column(Integer)

    summary = Column(Text)
    key_points = Column(JSONB, default=list)
    entities = Column(JSONB, default=dict)
    action_items = Column(JSONB, default=list)

    ai_category_id = Column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )
    ai_confidence = Column(Float)
    review_status = Column(String(50), nullable=False, default="pending", index=True)
    reviewed_at = Column(TIMESTAMP(timezone=True))
    reviewed_by = Column(String(255))
    override_summary = Column(Text)
    override_tags = Column(JSONB, default=list)
    user_category_id = Column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True
    )

    ai_tags = Column(ARRAY(String), default=list)
    user_tags = Column(ARRAY(String), default=list)
    extracted_metadata = Column(JSONB, default=dict)

    processing_status = Column(String(50), default="pending", nullable=False, index=True)
    processing_error = Column(Text)

    source = Column(String(50), nullable=False, index=True)
    source_id = Column(String(255))
    connection_id = Column(
        UUID(as_uuid=True), ForeignKey("connections.id", ondelete="SET NULL"), index=True
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)

    is_favorite = Column(Boolean, default=False, index=True)
    is_archived = Column(Boolean, default=False, index=True)
    user_notes = Column(Text)

    search_vector = Column(TSVECTOR)

    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    ai_category = relationship("Category", foreign_keys=[ai_category_id], back_populates="documents_ai")
    user_category = relationship("Category", foreign_keys=[user_category_id], back_populates="documents_user")
    connection = relationship("Connection", back_populates="documents")
    owner = relationship("User", back_populates="documents")
    outgoing_relationships = relationship(
        "DocumentRelationship",
        foreign_keys="DocumentRelationship.source_doc_id",
        back_populates="source_document",
        cascade="all, delete-orphan",
    )
    incoming_relationships = relationship(
        "DocumentRelationship",
        foreign_keys="DocumentRelationship.target_doc_id",
        back_populates="target_document",
        cascade="all, delete-orphan",
    )
    queue_items = relationship("ProcessingQueue", back_populates="document", cascade="all, delete-orphan")
    intelligence = relationship("DocumentIntelligence", back_populates="document", uselist=False, cascade="all, delete-orphan")
    review_items = relationship("DocumentReviewItem", back_populates="document", cascade="all, delete-orphan")
    structured_action_items = relationship(
        "DocumentActionItem",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    review_audit_events = relationship(
        "ReviewAuditEvent",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    versions = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number.desc()",
    )

    __table_args__ = (
        CheckConstraint(
            "processing_status IN ('pending', 'queued', 'processing', 'completed', 'failed')",
            name="valid_processing_status",
        ),
        CheckConstraint(
            "source IN ('upload', 'gmail', 'gdrive', 'dropbox', 'onedrive')",
            name="valid_source",
        ),
        CheckConstraint(
            "ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 1)",
            name="valid_confidence",
        ),
        CheckConstraint(
            "review_status IN ('pending', 'approved', 'rejected', 'edited')",
            name="valid_review_status",
        ),
    )


    @property
    def enrichment_status(self) -> str:
        metadata = self.extracted_metadata if isinstance(self.extracted_metadata, dict) else {}
        status = metadata.get("enrichment_status")
        if isinstance(status, str) and status in {"pending", "complete", "degraded"}:
            return status
        return "pending" if metadata.get("enrichment_pending") else "complete"

    @property
    def enrichment_pending(self) -> bool:
        return self.enrichment_status == "pending"

    @property
    def intelligence_warnings(self) -> list[str]:
        metadata = self.extracted_metadata if isinstance(self.extracted_metadata, dict) else {}
        warnings = metadata.get("intelligence_warnings")
        if isinstance(warnings, list):
            return [str(item) for item in warnings if str(item).strip()]
        return []

    @property
    def ai_analysis_degraded(self) -> bool:
        metadata = self.extracted_metadata if isinstance(self.extracted_metadata, dict) else {}
        return bool(metadata.get("ai_analysis_degraded"))

    @property
    def json_parse_retry_used(self) -> bool:
        metadata = self.extracted_metadata if isinstance(self.extracted_metadata, dict) else {}
        return bool(metadata.get("json_parse_retry_used"))

    def __repr__(self):
        return f"<Document(filename='{self.filename}', status='{self.processing_status}')>"

    @property
    def all_tags(self):
        return list(set((self.ai_tags or []) + (self.user_tags or [])))

    @property
    def processing_stage(self) -> str:
        metadata = self.extracted_metadata if isinstance(self.extracted_metadata, dict) else {}
        stage = metadata.get("processing_stage")
        if isinstance(stage, str) and stage:
            return stage
        if self.processing_status == "queued":
            return "queued"
        if self.processing_status == "processing":
            return "extracting"
        if self.processing_status == "completed":
            return "completed"
        if self.processing_status == "failed":
            return "failed"
        return "uploading"

    @property
    def processing_progress(self) -> int:
        metadata = self.extracted_metadata if isinstance(self.extracted_metadata, dict) else {}
        progress = metadata.get("processing_progress")
        if isinstance(progress, int):
            return max(0, min(progress, 100))
        defaults = {
            "uploading": 0,
            "queued": 5,
            "extracting": 15,
            "analyzing": 45,
            "enriching": 70,
            "embedding": 85,
            "completed": 100,
            "failed": 0,
        }
        return defaults.get(self.processing_stage, 0)
