from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ConnectionResponse(BaseModel):
    id: UUID
    type: str
    status: str
    display_name: str
    email: Optional[str] = None
    external_account_id: Optional[str] = None
    last_sync_date: Optional[datetime] = None
    last_sync_status: Optional[str] = None
    last_error_message: Optional[str] = None
    last_error_at: Optional[datetime] = None
    sync_progress: int
    document_count: int
    total_size: int
    auto_sync: bool
    sync_interval: int
    is_authenticated: bool

    model_config = {"from_attributes": True}


class OAuthStartResponse(BaseModel):
    provider: str
    authorization_url: str
    state: str


class SyncRunResponse(BaseModel):
    message: str
    files_seen: int
    documents_added: int
    documents_updated: int
    documents_failed: int
    bytes_synced: int
    connection: ConnectionResponse


class SyncLogResponse(BaseModel):
    id: UUID
    connection_id: UUID
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str
    documents_added: int
    documents_updated: int
    documents_failed: int
    bytes_synced: int
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}
