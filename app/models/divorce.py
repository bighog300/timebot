import uuid
from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from app.db.base import Base

class DivorceTimelineItem(Base):
    __tablename__ = 'divorce_timeline_items'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    event_date = Column(Date, nullable=True)
    date_precision = Column(String(20), nullable=False, default='unknown')
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False, default='admin')
    source_document_id = Column(UUID(as_uuid=True), ForeignKey('documents.id', ondelete='SET NULL'), nullable=True)
    source_quote = Column(Text)
    source_snippet = Column(Text)
    confidence = Column(Float)
    review_status = Column(String(20), nullable=False, default='suggested')
    metadata_json = Column(JSONB, nullable=False, default=dict)
    include_in_report = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

class DivorceReport(Base):
    __tablename__ = 'divorce_reports'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True)
    report_type = Column(String(80), nullable=False)
    title = Column(String(255), nullable=False)
    content_markdown = Column(Text, nullable=False)
    evidence_refs_json = Column(JSONB, nullable=False, default=list)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
