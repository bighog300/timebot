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
