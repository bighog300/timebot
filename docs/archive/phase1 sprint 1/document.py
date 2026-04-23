"""
Document Model
SQLAlchemy model for documents table
"""

from sqlalchemy import (
    Column, String, Integer, BigInteger, Float, Boolean, Text,
    TIMESTAMP, ForeignKey, CheckConstraint, ARRAY
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Document(Base):
    """
    Core document model storing all documents from various sources
    """
    __tablename__ = "documents"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # File information
    filename = Column(String(255), nullable=False, index=True)
    original_path = Column(Text, nullable=False)
    file_type = Column(String(50), nullable=False, index=True)
    file_size = Column(BigInteger, nullable=False)
    mime_type = Column(String(100))

    # Timestamps
    upload_date = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        index=True
    )
    last_modified = Column(
        TIMESTAMP(timezone=True),
        default=func.now(),
        onupdate=func.now()
    )
    processed_date = Column(TIMESTAMP(timezone=True))

    # Content
    raw_text = Column(Text)
    page_count = Column(Integer)
    word_count = Column(Integer)

    # AI-generated content
    summary = Column(Text)
    key_points = Column(JSONB, default=list)
    entities = Column(JSONB, default=dict)  # {people: [], organizations: [], dates: [], locations: []}
    action_items = Column(JSONB, default=list)

    # Categorization
    ai_category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        index=True
    )
    ai_confidence = Column(Float)
    user_category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        index=True
    )

    # Tags
    ai_tags = Column(ARRAY(String), default=list, index=True)
    user_tags = Column(ARRAY(String), default=list, index=True)

    # Metadata from file
    extracted_metadata = Column(JSONB, default=dict)

    # Processing status
    processing_status = Column(
        String(50),
        default="pending",
        nullable=False,
        index=True
    )
    processing_error = Column(Text)

    # Source information
    source = Column(
        String(50),
        nullable=False,
        index=True
    )
    source_id = Column(String(255))  # ID from external system
    connection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("connections.id", ondelete="SET NULL"),
        index=True
    )

    # User flags
    is_favorite = Column(Boolean, default=False, index=True)
    is_archived = Column(Boolean, default=False, index=True)
    user_notes = Column(Text)

    # Full-text search
    search_vector = Column(TSVECTOR)

    # Audit timestamps
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    ai_category = relationship("Category", foreign_keys=[ai_category_id], back_populates="documents_ai")
    user_category = relationship("Category", foreign_keys=[user_category_id], back_populates="documents_user")
    connection = relationship("Connection", back_populates="documents")
    
    # Relationships to other documents
    outgoing_relationships = relationship(
        "DocumentRelationship",
        foreign_keys="DocumentRelationship.source_doc_id",
        back_populates="source_document",
        cascade="all, delete-orphan"
    )
    incoming_relationships = relationship(
        "DocumentRelationship",
        foreign_keys="DocumentRelationship.target_doc_id",
        back_populates="target_document",
        cascade="all, delete-orphan"
    )
    
    # Processing queue items
    queue_items = relationship(
        "ProcessingQueue",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    # Version history
    versions = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number.desc()"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "processing_status IN ('pending', 'processing', 'completed', 'failed')",
            name="valid_processing_status"
        ),
        CheckConstraint(
            "source IN ('upload', 'gmail', 'gdrive', 'dropbox', 'onedrive')",
            name="valid_source"
        ),
        CheckConstraint(
            "ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 1)",
            name="valid_confidence"
        ),
    )

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.processing_status}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "summary": self.summary,
            "processing_status": self.processing_status,
            "source": self.source,
            "is_favorite": self.is_favorite,
            "is_archived": self.is_archived,
            "ai_tags": self.ai_tags or [],
            "user_tags": self.user_tags or [],
            "category": {
                "id": str(self.ai_category.id),
                "name": self.ai_category.name,
                "color": self.ai_category.color
            } if self.ai_category else None,
        }

    @property
    def all_tags(self):
        """Get combined AI and user tags"""
        return list(set((self.ai_tags or []) + (self.user_tags or [])))

    @property
    def is_processed(self):
        """Check if document has been processed"""
        return self.processing_status == "completed"

    @property
    def has_error(self):
        """Check if document processing failed"""
        return self.processing_status == "failed"
