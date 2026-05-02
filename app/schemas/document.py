from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class CategoryInfo(BaseModel):
    id: UUID
    name: str
    color: str
    icon: Optional[str] = None

    model_config = {"from_attributes": True}


class DocumentCreate(BaseModel):
    filename: str
    original_path: str
    file_type: str
    file_size: int
    mime_type: Optional[str] = None
    source: str = "upload"


class DocumentUpdate(BaseModel):
    user_category_id: Optional[UUID] = None
    user_tags: Optional[List[str]] = None
    user_notes: Optional[str] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    file_type: str
    file_size: int
    source: str
    upload_date: datetime
    processing_status: str
    processing_stage: str = "uploading"
    processing_progress: int = 0
    processing_message: str | None = None
    stage_started_at: datetime | None = None
    stage_updated_at: datetime | None = None
    processing_error: Optional[str] = None
    enrichment_status: str = "complete"
    enrichment_pending: bool = False
    intelligence_warnings: List[str] = []
    ai_analysis_degraded: bool = False
    json_parse_retry_used: bool = False
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    entities: Optional[Dict[str, Any]] = None
    action_items: Optional[List[str]] = None
    ai_tags: List[str] = []
    user_tags: List[str] = []
    ai_confidence: Optional[float] = None
    review_status: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    override_summary: Optional[str] = None
    override_tags: Optional[List[str]] = None
    is_favorite: bool = False
    is_archived: bool = False
    user_notes: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    ai_category: Optional[CategoryInfo] = None
    user_category: Optional[CategoryInfo] = None

    model_config = {"from_attributes": True}


class DocumentSearchResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
    query: str


class DocumentClusterResponse(BaseModel):
    cluster_id: str
    document_ids: List[str]
    document_titles: List[str]
    relationship_count: int
    dominant_signals: List[str] = []


class DocumentReviewRequest(BaseModel):
    action: str
    override_summary: Optional[str] = None
    override_tags: Optional[List[str]] = None
    reviewed_by: Optional[str] = None
