import uuid

from sqlalchemy import CheckConstraint, Column, ForeignKey, String, Text, TIMESTAMP, UniqueConstraint
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
    state = Column(String(20), nullable=False, default="open", index=True)
    source = Column(String(20), nullable=False, default="ai")
    action_metadata = Column("metadata", JSONB, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    completed_at = Column(TIMESTAMP(timezone=True))
    dismissed_at = Column(TIMESTAMP(timezone=True))

    document = relationship("Document", back_populates="structured_action_items")

    __table_args__ = (
        CheckConstraint("state IN ('open', 'completed', 'dismissed')", name="valid_action_item_state"),
        CheckConstraint("source IN ('ai', 'user')", name="valid_action_item_source"),
        UniqueConstraint("document_id", "content", name="unique_document_action_item_content"),
    )
