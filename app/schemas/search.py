from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.document import DocumentResponse


class SearchFilters(BaseModel):
    categories: Optional[List[UUID]] = None
    sources: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    file_types: Optional[List[str]] = None
    date_range: Optional[Dict[str, date]] = None
    is_favorite: Optional[bool] = None


class SearchRequest(BaseModel):
    query: str
    filters: Optional[SearchFilters] = None
    skip: int = 0
    limit: int = 50


class SearchResultItem(BaseModel):
    document: DocumentResponse
    relevance: float
    highlights: List[str]


class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    total: int
    query: str
    filters: Optional[Dict[str, Any]] = None
    page: int
    pages: int


class SemanticSearchResult(BaseModel):
    document: DocumentResponse
    similarity_score: float
    metadata: Optional[Dict[str, Any]] = None


class SemanticSearchResponse(BaseModel):
    query: str
    results: List[SemanticSearchResult]
    total: int
