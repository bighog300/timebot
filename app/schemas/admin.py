from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AdminUserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminUsersPageResponse(BaseModel):
    items: list[AdminUserResponse]
    total_count: int
    limit: int
    offset: int


class AdminRoleUpdateRequest(BaseModel):
    role: str = Field(pattern="^(viewer|editor|admin)$")


class AdminAuditEventResponse(BaseModel):
    id: UUID
    actor_id: UUID | None
    actor_email: str | None
    entity_type: str
    entity_id: str
    action: str
    details: dict
    created_at: datetime


class AdminAuditPageResponse(BaseModel):
    items: list[AdminAuditEventResponse]
    total_count: int
    limit: int
    offset: int


class AdminMetricsResponse(BaseModel):
    total_users: int
    total_documents: int
    documents_processed: int
    documents_failed: int
    pending_review_items: int
    open_action_items: int
    pending_relationship_reviews: int


class AdminProcessingSummaryResponse(BaseModel):
    pending: int
    processing: int
    completed: int
    failed: int
    recently_failed: int


class ProcessingEventResponse(BaseModel):
    id: UUID
    document_id: UUID
    user_id: UUID | None
    stage: str
    event_type: str
    status: str
    message: str
    severity: str
    duration_ms: int | None
    provider: str | None
    model: str | None
    ai_call_count: int | None
    parse_retry_used: str | None
    error_type: str | None
    safe_metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}
