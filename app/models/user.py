import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, TIMESTAMP
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
    # DEPRECATED: legacy monetization field; enforcement must use Subscription/Plan.
    # TODO: remove users.plan in a future migration after all legacy billing paths are retired.
    plan = Column(String(20), nullable=False, default="free")
    documents_uploaded_count = Column(Integer, nullable=False, default=0)
    reports_generated_count = Column(Integer, nullable=False, default=0)
    chat_messages_count = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    documents = relationship("Document", back_populates="owner")
    connections = relationship("Connection", back_populates="owner")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    invites_sent = relationship("UserInvite", back_populates="invited_by_user")

    def __repr__(self):
        return f"<User(email='{self.email}', active={self.is_active})>"


class UserInvite(Base):
    __tablename__ = "user_invites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="viewer")
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    invited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    accepted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    canceled_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())

    invited_by_user = relationship("User", back_populates="invites_sent")
