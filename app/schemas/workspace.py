from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class WorkspaceMemberResponse(BaseModel):
    user_id: UUID
    email: EmailStr | None = None
    display_name: str | None = None
    role: str
    created_at: datetime


class WorkspaceInviteResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    email: EmailStr
    role: str
    status: str
    created_at: datetime
    accepted_at: datetime | None = None
    expires_at: datetime
    canceled_at: datetime | None = None
    dev_invite_link: str | None = None


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    type: str
    owner_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class WorkspaceDetailResponse(WorkspaceResponse):
    members: list[WorkspaceMemberResponse]
    invites: list[WorkspaceInviteResponse] = []
