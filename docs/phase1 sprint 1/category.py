"""
Category Model
SQLAlchemy model for categories table
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, Text, TIMESTAMP, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Category(Base):
    """
    Document categories - both AI-discovered and user-created
    """
    __tablename__ = "categories"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic information
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)

    # Visual styling
    color = Column(String(7), default="#3B82F6")  # Hex color code
    icon = Column(String(50))  # Emoji or icon name

    # Origin tracking
    ai_generated = Column(Boolean, default=True, index=True)
    created_by_user = Column(Boolean, default=False)

    # Statistics
    document_count = Column(Integer, default=0, index=True)
    last_used = Column(TIMESTAMP(timezone=True))

    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    documents_ai = relationship(
        "Document",
        foreign_keys="Document.ai_category_id",
        back_populates="ai_category"
    )
    documents_user = relationship(
        "Document",
        foreign_keys="Document.user_category_id",
        back_populates="user_category"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', count={self.document_count})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "ai_generated": self.ai_generated,
            "document_count": self.document_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate URL-friendly slug from category name"""
        return name.lower().replace(" ", "-").replace("&", "and")

    @property
    def is_active(self):
        """Check if category has documents"""
        return self.document_count > 0
