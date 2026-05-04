import uuid

from sqlalchemy import CheckConstraint, Column, Date, Float, ForeignKey, String, Text, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class DocumentIntelligence(Base):
    __tablename__ = "document_intelligence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    summary = Column(Text)
    key_points = Column(JSONB, default=list)
    suggested_category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    confidence = Column(String(20), nullable=False, default="low")
    suggested_tags = Column(JSONB, default=list)
    entities = Column(JSONB, default=dict)
    model_name = Column(String(100))
    model_version = Column(String(100))
    model_metadata = Column(JSONB, default=dict)
    category_status = Column(String(20), nullable=False, default="suggested", index=True)
    generated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    document = relationship("Document", back_populates="intelligence")
    suggested_category = relationship("Category")

    __table_args__ = (
        CheckConstraint("confidence IN ('low', 'medium', 'high')", name="valid_intelligence_confidence"),
        CheckConstraint(
            "category_status IN ('suggested', 'approved', 'overridden')",
            name="valid_intelligence_category_status",
        ),
    )


class DocumentReviewItem(Base):
    __tablename__ = "document_review_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    review_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="open", index=True)
    reason = Column(Text)
    payload = Column(JSONB, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    resolved_at = Column(TIMESTAMP(timezone=True))
    dismissed_at = Column(TIMESTAMP(timezone=True))

    document = relationship("Document", back_populates="review_items")

    __table_args__ = (
        CheckConstraint(
            "review_type IN ('low_confidence', 'uncategorized', 'missing_tags', 'duplicates', 'action_items', 'processing_issues')",
            name="valid_review_item_type",
        ),
        CheckConstraint("status IN ('open', 'resolved', 'dismissed')", name="valid_review_item_status"),
    )


class DocumentActionItem(Base):
    __tablename__ = "document_action_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content = Column(Text, nullable=False)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True)
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True, index=True)
    due_date = Column(Date, nullable=True, index=True)
    priority = Column(String(20), nullable=False, default="medium", index=True)
    status = Column(String(20), nullable=False, default="open", index=True)
    category = Column(String(40), nullable=False, default="admin", index=True)
    evidence_refs_json = Column(JSONB, default=list)
    source_quote = Column(Text)
    source_snippet = Column(Text)
    state = Column(String(20), nullable=False, default="open", index=True)
    source = Column(String(20), nullable=False, default="ai")
    action_metadata = Column("metadata", JSONB, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    completed_at = Column(TIMESTAMP(timezone=True))
    dismissed_at = Column(TIMESTAMP(timezone=True))

    document = relationship("Document", back_populates="structured_action_items", foreign_keys=[document_id])

    __table_args__ = (
        CheckConstraint("state IN ('suggested', 'open', 'in_progress', 'done', 'dismissed', 'rejected', 'completed')", name="valid_action_item_state"),
        CheckConstraint("source IN ('ai', 'user')", name="valid_action_item_source"),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'urgent')", name="valid_action_item_priority"),
        CheckConstraint("status IN ('suggested', 'open', 'in_progress', 'done', 'dismissed', 'rejected')", name="valid_action_item_status"),
        CheckConstraint("category IN ('legal', 'financial', 'children', 'communication', 'evidence', 'admin', 'emotional_support')", name="valid_action_item_category"),
        UniqueConstraint("document_id", "content", name="unique_document_action_item_content"),
    )


class ReviewAuditEvent(Base):
    __tablename__ = "review_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    event_type = Column(String(64), nullable=False, index=True)
    note = Column(Text)
    before_json = Column(JSONB, default=dict)
    after_json = Column(JSONB, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), index=True)

    document = relationship("Document", back_populates="review_audit_events")
    actor = relationship("User")


class DocumentRelationshipReview(Base):
    __tablename__ = "document_relationship_reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type = Column(String(20), nullable=False, index=True)
    confidence = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    reason_codes_json = Column(JSONB, default=list)
    metadata_json = Column(JSONB, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    reviewed_at = Column(TIMESTAMP(timezone=True))
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)

    source_document = relationship("Document", foreign_keys=[source_document_id])
    target_document = relationship("Document", foreign_keys=[target_document_id])
    reviewer = relationship("User")

    __table_args__ = (
        CheckConstraint("source_document_id != target_document_id", name="no_self_relationship_review"),
        CheckConstraint(
            "relationship_type IN ('duplicate', 'similar', 'related', 'thread', 'attachment')",
            name="valid_relationship_review_type",
        ),
        CheckConstraint("status IN ('pending', 'confirmed', 'dismissed')", name="valid_relationship_review_status"),
        CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="valid_relationship_review_confidence",
        ),
    )

    @staticmethod
    def _document_title(document) -> str:
        if not document:
            return ""
        for field in ("title", "filename", "original_filename", "name"):
            value = getattr(document, field, None)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return str(document.id)

    @staticmethod
    def _document_snippet(document) -> str:
        if not document:
            return ""
        if isinstance(document.summary, str) and document.summary.strip():
            return document.summary.strip()
        intelligence_summary = getattr(getattr(document, "intelligence", None), "summary", None)
        if isinstance(intelligence_summary, str) and intelligence_summary.strip():
            return intelligence_summary.strip()
        raw_text = getattr(document, "raw_text", None)
        if isinstance(raw_text, str) and raw_text.strip():
            return raw_text.strip()[:200]
        return ""

    @property
    def source_document_title(self) -> str:
        return self._document_title(self.source_document)

    @property
    def target_document_title(self) -> str:
        return self._document_title(self.target_document)

    @property
    def source_document_name(self) -> str:
        return self.source_document_title

    @property
    def target_document_name(self) -> str:
        return self.target_document_title

    @property
    def source_document_snippet(self) -> str:
        return self._document_snippet(self.source_document)

    @property
    def target_document_snippet(self) -> str:
        return self._document_snippet(self.target_document)

    @property
    def source_snippet(self) -> str:
        return self.source_document_snippet

    @property
    def target_snippet(self) -> str:
        return self.target_document_snippet
