import uuid

from sqlalchemy import Boolean, Column, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    role = Column(String(20), nullable=False, default="viewer")
    plan = Column(String(20), nullable=False, default="free")
    documents_uploaded_count = Column(Integer, nullable=False, default=0)
    reports_generated_count = Column(Integer, nullable=False, default=0)
    chat_messages_count = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    documents = relationship("Document", back_populates="owner")
    connections = relationship("Connection", back_populates="owner")

    def __repr__(self):
        return f"<User(email='{self.email}', active={self.is_active})>"
