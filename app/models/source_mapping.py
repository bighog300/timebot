import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, TIMESTAMP, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class SourceProfile(Base):
    __tablename__ = "source_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String(255), nullable=False, index=True)
    profile_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="ready", index=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    url_families = relationship(
        "UrlFamily",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="UrlFamily.family_order.asc()",
    )


class UrlFamily(Base):
    __tablename__ = "url_families"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_profile_id = Column(UUID(as_uuid=True), ForeignKey("source_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    family_key = Column(String(255), nullable=False)
    sample_url = Column(Text, nullable=False)
    locator_hint = Column(String(255))
    suggestion = Column(JSONB, nullable=False, default=dict)
    family_order = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())

    profile = relationship(
        "SourceProfile",
        back_populates="url_families",
    )


class MappingDraft(Base):
    __tablename__ = "mapping_drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String(255), nullable=False, index=True)
    source_profile_id = Column(UUID(as_uuid=True), ForeignKey("source_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="draft", index=True)
    approved_at = Column(TIMESTAMP(timezone=True))
    approved_by = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    rules = relationship(
        "MappingRule",
        back_populates="draft",
        cascade="all, delete-orphan",
        order_by="MappingRule.rule_order.asc()",
    )


class MappingRule(Base):
    __tablename__ = "mapping_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    draft_id = Column(UUID(as_uuid=True), ForeignKey("mapping_drafts.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(String(255), nullable=False, index=True)
    rule_order = Column(Integer, nullable=False, default=0)
    family_key = Column(String(255), nullable=False)
    sample_url = Column(Text, nullable=False)
    selector_suggestion = Column(String(255))
    parse_suggestion = Column(String(255))
    transform_suggestion = Column(String(255))
    selector_override = Column(String(255))
    parse_override = Column(String(255))
    transform_override = Column(String(255))
    notes = Column(Text)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    draft = relationship(
        "MappingDraft",
        back_populates="rules",
    )

    __table_args__ = (UniqueConstraint("draft_id", "family_key", name="uq_mapping_rules_draft_family"),)


class ActiveSourceMapping(Base):
    __tablename__ = "active_source_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String(255), nullable=False, unique=True, index=True)
    mapping_draft_id = Column(UUID(as_uuid=True), ForeignKey("mapping_drafts.id", ondelete="CASCADE"), nullable=False, index=True)
    compiled_mapping = Column(JSONB, nullable=False, default=dict)
    activated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    activated_by = Column(String(255))
