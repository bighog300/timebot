from typing import List, Optional

from pydantic import BaseModel


class TimelineEvent(BaseModel):
    title: str
    description: Optional[str] = None
    date: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    confidence: Optional[float] = None
    signal_strength: Optional[str] = None
    source_quote: Optional[str] = None
    page_number: Optional[int] = None
    document_id: str
    document_title: str
    category: Optional[str] = None
    source: Optional[str] = "extracted"


class TimelineGap(BaseModel):
    start_date: str
    end_date: str
    gap_duration_days: int


class TimelineResponse(BaseModel):
    total_documents: int
    total_events: int
    events: List[TimelineEvent]
    gaps: Optional[List[TimelineGap]] = None


class InsightsResponse(BaseModel):
    generated_at: str
    lookback_days: int
    volume_trends: List[dict]
    category_distribution: List[dict]
    source_distribution: dict
    action_item_summary: dict
    duplicate_clusters: List[List[str]]
    relationship_summary: dict
    recent_activity: List[dict]


class StructuredInsight(BaseModel):
    id: str
    type: str
    title: str
    description: str
    severity: str
    related_document_ids: List[str]
    related_event_ids: List[str] = []
    evidence: List[str] = []
    created_at: str


class StructuredInsightsResponse(BaseModel):
    generated_at: str
    count: int
    insights: List[StructuredInsight]


class CategoryIntelligenceResponse(BaseModel):
    analytics: List[dict]
    merge_recommendations: List[dict]
    refinement_suggestions: List[dict]
