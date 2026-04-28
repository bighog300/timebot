from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentIntelligenceResponse(BaseModel):
    document_id: UUID
    summary: str | None = None
    key_points: list[str] = Field(default_factory=list)
    suggested_category_id: UUID | None = None
    confidence: str
    suggested_tags: list[str] = Field(default_factory=list)
    entities: dict[str, Any] = Field(default_factory=dict)
    model_name: str | None = None
    model_version: str | None = None
    model_metadata: dict[str, Any] = Field(default_factory=dict)
    category_status: str
    generated_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}


class DocumentIntelligenceUpdate(BaseModel):
    summary: str | None = None
    key_points: list[str] | None = None
    suggested_tags: list[str] | None = None
    entities: dict[str, Any] | None = None
    model_metadata: dict[str, Any] | None = None

    model_config = {"protected_namespaces": ()}


class DocumentReviewItemResponse(BaseModel):
    id: UUID
    document_id: UUID
    review_type: str
    status: str
    reason: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None = None
    dismissed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReviewResolutionRequest(BaseModel):
    note: str | None = None


class BulkMutationRequest(BaseModel):
    ids: list[UUID] = Field(default_factory=list)
    note: str | None = None


class CategoryOverrideRequest(BaseModel):
    category_id: UUID


class ActionItemResponse(BaseModel):
    id: UUID
    document_id: UUID
    content: str
    state: str
    source: str
    action_metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    dismissed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ActionItemUpdate(BaseModel):
    content: str | None = None
    action_metadata: dict[str, Any] | None = None


class BulkReviewItemMutationResponse(BaseModel):
    updated_count: int
    skipped_count: int = Field(
        description="Number of input IDs skipped because they were missing, unauthorized, or duplicated in the request."
    )
    items: list[DocumentReviewItemResponse] = Field(default_factory=list)


class BulkActionItemMutationResponse(BaseModel):
    updated_count: int
    skipped_count: int = Field(
        description="Number of input IDs skipped because they were missing, unauthorized, or duplicated in the request."
    )
    items: list[ActionItemResponse] = Field(default_factory=list)


class ReviewAuditEventResponse(BaseModel):
    id: UUID
    document_id: UUID
    actor_id: UUID | None = None
    event_type: str
    note: str | None = None
    before_json: dict[str, Any] = Field(default_factory=dict)
    after_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}


class OldestOpenReviewItemResponse(BaseModel):
    id: UUID
    document_id: UUID
    review_type: str
    priority: str
    age_hours: float
    created_at: datetime


class ReviewMetricsResponse(BaseModel):
    open_review_count: int
    resolved_review_count: int
    dismissed_review_count: int
    open_by_type: dict[str, int] = Field(default_factory=dict)
    open_by_priority: dict[str, int] = Field(default_factory=dict)
    average_age_hours: float
    oldest_open_items: list[OldestOpenReviewItemResponse] = Field(default_factory=list)
    recently_resolved_count: int
    low_confidence_category_count: int
    uncategorized_count: int


class ActionItemMetricsResponse(BaseModel):
    open_count: int
    completed_count: int
    dismissed_count: int
    overdue_count: int | None = None
    completion_rate: float
    recently_completed_count: int
