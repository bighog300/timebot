from typing import Iterable
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.source_mapping import ActiveSourceMapping, MappingDraft, MappingRule, SourceProfile


def get_profile_for_source(db: Session, source_id: str, profile_id: UUID) -> SourceProfile | None:
    return (
        db.query(SourceProfile)
        .options(joinedload(SourceProfile.url_families))
        .filter(SourceProfile.id == profile_id, SourceProfile.source_id == source_id)
        .first()
    )


def create_mapping_draft(db: Session, source_id: str, profile_id: UUID) -> MappingDraft:
    draft = MappingDraft(source_id=source_id, source_profile_id=profile_id)
    db.add(draft)
    db.flush()
    return draft


def create_mapping_rules(db: Session, rules: Iterable[MappingRule]) -> None:
    db.add_all(list(rules))


def get_source_drafts(db: Session, source_id: str) -> list[MappingDraft]:
    return (
        db.query(MappingDraft)
        .options(joinedload(MappingDraft.rules))
        .filter(MappingDraft.source_id == source_id)
        .order_by(MappingDraft.created_at.desc(), MappingDraft.id.desc())
        .all()
    )


def get_source_draft(db: Session, source_id: str, draft_id: UUID) -> MappingDraft | None:
    return (
        db.query(MappingDraft)
        .options(joinedload(MappingDraft.rules))
        .filter(MappingDraft.id == draft_id, MappingDraft.source_id == source_id)
        .first()
    )


def get_draft_rule(db: Session, source_id: str, draft_id: UUID, rule_id: UUID) -> MappingRule | None:
    return (
        db.query(MappingRule)
        .filter(MappingRule.id == rule_id, MappingRule.draft_id == draft_id, MappingRule.source_id == source_id)
        .first()
    )


def upsert_active_mapping(
    db: Session,
    *,
    source_id: str,
    draft_id: UUID,
    compiled_mapping: dict,
    activated_by: str | None,
) -> ActiveSourceMapping:
    existing = db.query(ActiveSourceMapping).filter(ActiveSourceMapping.source_id == source_id).first()
    if existing:
        existing.mapping_draft_id = draft_id
        existing.compiled_mapping = compiled_mapping
        existing.activated_by = activated_by
        db.add(existing)
        db.flush()
        return existing

    active = ActiveSourceMapping(
        source_id=source_id,
        mapping_draft_id=draft_id,
        compiled_mapping=compiled_mapping,
        activated_by=activated_by,
    )
    db.add(active)
    db.flush()
    return active


def get_active_mapping(db: Session, source_id: str) -> ActiveSourceMapping | None:
    return db.query(ActiveSourceMapping).filter(ActiveSourceMapping.source_id == source_id).first()
