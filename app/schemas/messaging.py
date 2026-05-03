from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    body: str
    link_url: str | None
    read_at: datetime | None
    metadata_json: dict
    created_at: datetime
    model_config = {"from_attributes": True}


class MessageCreateRequest(BaseModel):
    category: str = Field(pattern="^(bug_report|feature_request|support)$")
    subject: str
    body: str
    workspace_id: UUID | None = None


class MessageReplyRequest(BaseModel):
    body: str


class AdminThreadPatchRequest(BaseModel):
    status: str = Field(pattern="^(open|in_progress|closed)$")


class UserMessageResponse(BaseModel):
    id: UUID
    sender_user_id: UUID | None
    sender_type: str
    body: str
    created_at: datetime
    model_config = {"from_attributes": True}


class ThreadResponse(BaseModel):
    id: UUID
    user_id: UUID
    workspace_id: UUID | None
    category: str
    subject: str
    status: str
    created_at: datetime
    updated_at: datetime
    messages: list[UserMessageResponse] = []
    model_config = {"from_attributes": True}
