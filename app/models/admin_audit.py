import uuid

from sqlalchemy import Column, ForeignKey, String, TIMESTAMP, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class AdminAuditEvent(Base):
    __tablename__ = "admin_audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Text, nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)
    details = Column(JSONB, default=dict)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), index=True)

    actor = relationship("User")
