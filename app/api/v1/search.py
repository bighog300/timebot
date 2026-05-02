from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.category import Category
from app.models.document import Document
from app.schemas.intelligence import CategoryIntelligenceResponse, InsightsResponse, TimelineResponse
from app.schemas.search import HybridSearchResponse, SearchResponse, SemanticSearchResponse
from app.models.user import User
from app.services.category_intelligence import category_intelligence_service
from app.services.insights_service import insights_service
from app.services.relationship_detection import relationship_detection_service
from app.services.limit_enforcement import enforce_feature, enforce_limit
from app.services.cost_protection import configured_rate_limit, enforce_rate_limit
from app.services.usage import record_usage
from app.services.search_service import search_service
from app.services.timeline_service import timeline_service

router = APIRouter(prefix="/search", tags=["search"], dependencies=[Depends(get_current_user)])


def _require_doc_access_or_admin(db: Session, document_id: UUID, current_user: User) -> Document:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role != "admin" and doc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.post("/", response_model=SearchResponse)
async def search_documents(
    query: str = Query(..., min_length=2, description="Search query"),
    categories: Optional[List[UUID]] = Query(None),
    sources: Optional[List[str]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    file_types: Optional[List[str]] = Query(None),
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    is_favorite: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enforce_rate_limit(db, user_id=current_user.id, metric="expensive_reads_rate", max_calls=configured_rate_limit("expensive_reads_rate"))
    record_usage(db, user_id=current_user.id, metric="expensive_reads_rate", quantity=1)
    db.commit()
    filters = {}
    if categories:
        filters["categories"] = categories
    if sources:
        filters["sources"] = sources
    if tags:
        filters["tags"] = tags
    if file_types:
        filters["file_types"] = file_types
    if date_start or date_end:
        filters["date_range"] = {"start": date_start, "end": date_end}
    if is_favorite is not None:
        filters["is_favorite"] = is_favorite
    filters["user_id"] = str(current_user.id)

    return search_service.search_documents(db=db, query=query, filters=filters, skip=skip, limit=limit)


@router.post("/hybrid", response_model=HybridSearchResponse)
async def hybrid_search_documents(
    query: str = Query(..., min_length=2),
    categories: Optional[List[UUID]] = Query(None),
    sources: Optional[List[str]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    file_types: Optional[List[str]] = Query(None),
    date_start: Optional[date] = None,
    date_end: Optional[date] = None,
    is_favorite: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    lexical_weight: float = Query(0.6, ge=0.0, le=1.0),
    semantic_weight: float = Query(0.4, ge=0.0, le=1.0),
    semantic_threshold: float = Query(0.35, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enforce_rate_limit(db, user_id=current_user.id, metric="expensive_reads_rate", max_calls=configured_rate_limit("expensive_reads_rate"))
    record_usage(db, user_id=current_user.id, metric="expensive_reads_rate", quantity=1)
    db.commit()
    filters = {}
    if categories:
        filters["categories"] = categories
    if sources:
        filters["sources"] = sources
    if tags:
        filters["tags"] = tags
    if file_types:
        filters["file_types"] = file_types
    if date_start or date_end:
        filters["date_range"] = {"start": date_start, "end": date_end}
    if is_favorite is not None:
        filters["is_favorite"] = is_favorite
    filters["user_id"] = str(current_user.id)

    if lexical_weight + semantic_weight <= 0:
        lexical_weight, semantic_weight = 0.6, 0.4

    return search_service.hybrid_search_documents(
        db=db,
        user_id=current_user.id,
        query=query,
        filters=filters,
        skip=skip,
        limit=limit,
        lexical_weight=lexical_weight,
        semantic_weight=semantic_weight,
        semantic_threshold=semantic_threshold,
    )


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"query": q, "suggestions": search_service.get_search_suggestions(db, q, limit, user_id=str(current_user.id))}


@router.get("/popular")
async def get_popular_searches(
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return {"popular_searches": search_service.get_popular_searches(db, limit)}


@router.get("/facets")
async def get_search_facets(query: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    base_query = db.query(Document).filter(Document.is_archived.is_(False), Document.user_id == current_user.id)

    if query:
        base_query = base_query.filter(Document.search_vector.op("@@")(func.plainto_tsquery("english", query)))

    category_facets = (
        base_query.with_entities(Category.id, Category.name, func.count(Document.id).label("count"))
        .join(Category, or_(Document.ai_category_id == Category.id, Document.user_category_id == Category.id))
        .group_by(Category.id, Category.name)
        .all()
    )

    source_facets = base_query.with_entities(Document.source, func.count(Document.id).label("count")).group_by(Document.source).all()

    file_type_facets = base_query.with_entities(Document.file_type, func.count(Document.id).label("count")).group_by(Document.file_type).all()

    return {
        "categories": [{"id": str(i), "name": n, "count": c} for i, n, c in category_facets],
        "sources": [{"source": s, "count": c} for s, c in source_facets],
        "file_types": [{"type": t, "count": c} for t, c in file_type_facets],
    }


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    query: str = Query(..., min_length=3),
    limit: int = Query(10, ge=1, le=50),
    threshold: float = Query(0.5, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    enforce_rate_limit(db, user_id=current_user.id, metric="expensive_reads_rate", max_calls=configured_rate_limit("expensive_reads_rate"))
    record_usage(db, user_id=current_user.id, metric="expensive_reads_rate", quantity=1)
    db.commit()
    from app.services.embedding_service import embedding_service

    vector_results = embedding_service.semantic_search(query=query, limit=limit, score_threshold=threshold)

    document_ids = [r["document_id"] for r in vector_results]
    if not document_ids:
        return {"query": query, "results": [], "total": 0}

    documents = db.query(Document).filter(Document.id.in_(document_ids), Document.user_id == current_user.id).all()
    documents_by_id = {str(doc.id): doc for doc in documents}

    results = []
    for match in vector_results:
        doc = documents_by_id.get(match["document_id"])
        if doc:
            results.append({"document": doc, "similarity_score": match["score"], "metadata": match.get("metadata")})

    return {"query": query, "results": results, "total": len(results)}


@router.get("/documents/{document_id}/similar", response_model=SemanticSearchResponse)
async def find_similar_documents(document_id: UUID, limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enforce_rate_limit(db, user_id=current_user.id, metric="expensive_reads_rate", max_calls=configured_rate_limit("expensive_reads_rate"))
    record_usage(db, user_id=current_user.id, metric="expensive_reads_rate", quantity=1)
    db.commit()
    from app.services.embedding_service import embedding_service

    document = db.query(Document).filter(Document.id == document_id, Document.user_id == current_user.id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    similar = embedding_service.find_similar_documents(document_id=str(document_id), limit=limit)
    doc_ids = [s["document_id"] for s in similar]
    if not doc_ids:
        return {"query": str(document_id), "results": [], "total": 0}

    documents = db.query(Document).filter(Document.id.in_(doc_ids), Document.user_id == current_user.id).all()
    documents_by_id = {str(doc.id): doc for doc in documents}

    results = []
    for item in similar:
        doc = documents_by_id.get(item["document_id"])
        if doc:
            results.append({"document": doc, "similarity_score": item["score"], "metadata": item.get("metadata")})

    return {"query": str(document_id), "results": results, "total": len(results)}


@router.post("/relationships/detect/{document_id}")
async def detect_relationships(document_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enforce_rate_limit(db, user_id=current_user.id, metric="relationship_detection_rate", max_calls=configured_rate_limit("relationship_detection_rate"))
    enforce_feature(db, current_user.id, "relationship_detection_enabled")
    enforce_limit(db, current_user.id, "processing_jobs_per_month", quantity=1)
    _require_doc_access_or_admin(db=db, document_id=document_id, current_user=current_user)
    result = relationship_detection_service.detect_for_document(db=db, document_id=document_id)
    record_usage(db, user_id=current_user.id, metric="relationship_detection_rate", quantity=1)
    db.commit()
    return result


@router.post("/relationships/backfill")
async def backfill_relationships(
    limit: Optional[int] = Query(None, ge=1, le=2000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if (current_user.role or "viewer").lower() != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    enforce_rate_limit(db, user_id=current_user.id, metric="relationship_detection_rate", max_calls=configured_rate_limit("relationship_detection_rate"))
    enforce_feature(db, current_user.id, "relationship_detection_enabled")
    enforce_limit(db, current_user.id, "processing_jobs_per_month", quantity=1)
    result = relationship_detection_service.backfill_relationships(db=db, limit=limit)
    record_usage(db, user_id=current_user.id, metric="relationship_detection_rate", quantity=1)
    db.commit()
    return result


@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(
    categories: Optional[List[str]] = Query(None),
    sources: Optional[List[str]] = Query(None),
    file_types: Optional[List[str]] = Query(None),
    document_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return timeline_service.build_timeline(
        db=db,
        user_id=current_user.id,
        category_ids=categories,
        sources=sources,
        file_types=file_types,
        document_id=document_id,
        start_date=start_date,
        end_date=end_date,
        category=category,
        min_confidence=min_confidence,
        limit=limit,
    )


@router.get("/insights", response_model=InsightsResponse)
async def get_insights(lookback_days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enforce_rate_limit(db, user_id=current_user.id, metric="expensive_reads_rate", max_calls=configured_rate_limit("expensive_reads_rate"))
    enforce_feature(db, current_user.id, "insights_enabled")
    result = insights_service.build_dashboard(db=db, lookback_days=lookback_days, user_id=current_user.id)
    record_usage(db, user_id=current_user.id, metric="expensive_reads_rate", quantity=1)
    db.commit()
    return result


@router.get("/category-intelligence", response_model=CategoryIntelligenceResponse)
async def get_category_intelligence(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    enforce_rate_limit(db, user_id=current_user.id, metric="expensive_reads_rate", max_calls=configured_rate_limit("expensive_reads_rate"))
    enforce_feature(db, current_user.id, "category_intelligence_enabled")
    result = category_intelligence_service.build_intelligence(db, user_id=current_user.id)
    record_usage(db, user_id=current_user.id, metric="expensive_reads_rate", quantity=1)
    db.commit()
    return result
