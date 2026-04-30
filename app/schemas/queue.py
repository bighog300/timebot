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
    broker_reachable: bool = False
    worker_online: bool = False
    worker_count: int = 0
    worker_error: Optional[str] = None
    queued: int
    processing: int
    completed: int
    failed: int
    total: int
    pending_review_count: int = 0
    celery_active: Optional[int] = None
    celery_reserved: Optional[int] = None
