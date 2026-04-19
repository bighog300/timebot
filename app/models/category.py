import re
import uuid
from sqlalchemy import Column, String, Integer, Boolean, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    color = Column(String(7), default="#3B82F6")
    icon = Column(String(50))
    ai_generated = Column(Boolean, default=True, index=True)
    created_by_user = Column(Boolean, default=False)
    document_count = Column(Integer, default=0, index=True)
    last_used = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), default=func.now(), onupdate=func.now())

    documents_ai = relationship(
        "Document", foreign_keys="Document.ai_category_id", back_populates="ai_category"
    )
    documents_user = relationship(
        "Document", foreign_keys="Document.user_category_id", back_populates="user_category"
    )

    def __repr__(self):
        return f"<Category(name='{self.name}', count={self.document_count})>"

    @staticmethod
    def generate_slug(name: str) -> str:
        slug = name.lower().replace(" ", "-").replace("&", "and")
        slug = re.sub(r"[^a-z0-9-]", "-", slug)
        return re.sub(r"-+", "-", slug).strip("-")
