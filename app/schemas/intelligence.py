from typing import Any, Dict, List

from pydantic import BaseModel


class TimelineBucket(BaseModel):
    period: str
    count: int
    events: List[Dict[str, Any]]


class TimelineResponse(BaseModel):
    group_by: str
    total_documents: int
    total_events: int
    buckets: List[TimelineBucket]


class InsightsResponse(BaseModel):
    generated_at: str
    lookback_days: int
    volume_trends: List[Dict[str, Any]]
    category_distribution: List[Dict[str, Any]]
    source_distribution: Dict[str, int]
    action_item_summary: Dict[str, Any]
    duplicate_clusters: List[List[str]]
    relationship_summary: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


class CategoryIntelligenceResponse(BaseModel):
    analytics: List[Dict[str, Any]]
    merge_recommendations: List[Dict[str, Any]]
    refinement_suggestions: List[Dict[str, Any]]
