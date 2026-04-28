from typing import Iterable
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models.source_mapping import ActiveSourceMapping, MappingDraft, MappingRule, SourceProfile
from app.models.source_mapping import CrawlDecision, CrawlError, CrawlPage, CrawlRun


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


def source_exists(db: Session, source_id: str) -> bool:
    return db.query(SourceProfile.id).filter(SourceProfile.source_id == source_id).first() is not None


def create_crawl_run(db: Session, *, source_id: str, active_mapping_id: UUID, created_by: str | None) -> CrawlRun:
    crawl_run = CrawlRun(source_id=source_id, active_mapping_id=active_mapping_id, status="pending", created_by=created_by)
    db.add(crawl_run)
    db.flush()
    return crawl_run


def list_crawl_runs(db: Session, source_id: str) -> list[CrawlRun]:
    return (
        db.query(CrawlRun)
        .filter(CrawlRun.source_id == source_id)
        .order_by(CrawlRun.created_at.desc(), CrawlRun.id.desc())
        .all()
    )


def get_crawl_run(db: Session, source_id: str, run_id: UUID) -> CrawlRun | None:
    return (
        db.query(CrawlRun)
        .options(joinedload(CrawlRun.pages).joinedload(CrawlPage.decisions))
        .filter(CrawlRun.id == run_id, CrawlRun.source_id == source_id)
        .first()
    )


def get_crawl_run_shallow(db: Session, source_id: str, run_id: UUID) -> CrawlRun | None:
    return db.query(CrawlRun).filter(CrawlRun.id == run_id, CrawlRun.source_id == source_id).first()


def create_crawl_page(
    db: Session,
    *,
    crawl_run_id: UUID,
    url: str,
    normalized_url: str,
    depth: int,
    parent_url: str | None,
    status: str,
    http_status: int | None = None,
    content_type: str | None = None,
    content_hash: str | None = None,
    extracted_text: str | None = None,
) -> CrawlPage:
    page = CrawlPage(
        crawl_run_id=crawl_run_id,
        url=url,
        normalized_url=normalized_url,
        depth=depth,
        parent_url=parent_url,
        status=status,
        http_status=http_status,
        content_type=content_type,
        content_hash=content_hash,
        extracted_text=extracted_text,
    )
    db.add(page)
    db.flush()
    return page


def create_crawl_decision(
    db: Session,
    *,
    crawl_page_id: UUID,
    decision_type: str,
    matched_rule_id: str | None,
    reason_codes_json: list[str],
) -> CrawlDecision:
    decision = CrawlDecision(
        crawl_page_id=crawl_page_id,
        decision_type=decision_type,
        matched_rule_id=matched_rule_id,
        reason_codes_json=reason_codes_json,
    )
    db.add(decision)
    db.flush()
    return decision


def create_crawl_error(db: Session, *, crawl_page_id: UUID, error_type: str, error_message: str) -> CrawlError:
    err = CrawlError(crawl_page_id=crawl_page_id, error_type=error_type, error_message=error_message)
    db.add(err)
    db.flush()
    return err
