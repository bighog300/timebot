from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class MappingRulePatch(BaseModel):
    selector_override: str | None = None
    parse_override: str | None = None
    transform_override: str | None = None
    notes: str | None = None
    enabled: bool | None = None


class BulkMappingRulePatch(MappingRulePatch):
    rule_id: UUID


class BulkRulePatchRequest(BaseModel):
    patches: list[BulkMappingRulePatch] = Field(default_factory=list)


class MappingRuleResponse(BaseModel):
    id: UUID
    rule_order: int
    family_key: str
    sample_url: str
    selector_suggestion: str | None
    parse_suggestion: str | None
    transform_suggestion: str | None
    selector_override: str | None
    parse_override: str | None
    transform_override: str | None
    notes: str | None
    enabled: bool

    model_config = {"from_attributes": True}


class MappingDraftResponse(BaseModel):
    id: UUID
    source_id: str
    source_profile_id: UUID
    status: str
    approved_at: datetime | None
    approved_by: str | None
    created_at: datetime
    updated_at: datetime
    rules: list[MappingRuleResponse]

    model_config = {"from_attributes": True}


class ActiveSourceMappingResponse(BaseModel):
    id: UUID
    source_id: str
    mapping_draft_id: UUID
    compiled_mapping: dict[str, Any]
    activated_at: datetime
    activated_by: str | None

    model_config = {"from_attributes": True}


class CrawlRunCreateResponse(BaseModel):
    id: UUID
    source_id: str
    active_mapping_id: UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    stats_json: dict[str, Any]
    created_by: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CrawlDecisionResponse(BaseModel):
    id: UUID
    decision_type: str
    matched_rule_id: str | None
    reason_codes_json: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class CrawlPageResponse(BaseModel):
    id: UUID
    url: str
    normalized_url: str
    depth: int
    parent_url: str | None
    status: str
    http_status: int | None
    content_type: str | None
    content_hash: str | None
    extracted_text: str | None
    created_at: datetime
    decisions: list[CrawlDecisionResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class CrawlRunDetailResponse(CrawlRunCreateResponse):
    pages: list[CrawlPageResponse] = Field(default_factory=list)
