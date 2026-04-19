from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class QueueItemResponse(BaseModel):
    id: UUID
    document_id: UUID
    task_type: str
    status: str
    priority: int
    attempts: int
    max_attempts: int
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class QueueStatsResponse(BaseModel):
    queued: int
    processing: int
    completed: int
    failed: int
    total: int
    celery_active: Optional[int] = None
    celery_reserved: Optional[int] = None
