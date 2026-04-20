from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.category import Category
from app.models.document import Document
from app.schemas.search import SearchResponse, SemanticSearchResponse
from app.services.search_service import search_service

router = APIRouter(prefix="/search", tags=["search"])


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
):
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

    return search_service.search_documents(
        db=db,
        query=query,
        filters=filters,
        skip=skip,
        limit=limit,
    )


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
):
    return {"query": q, "suggestions": search_service.get_search_suggestions(db, q, limit)}


@router.get("/popular")
async def get_popular_searches(
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    return {"popular_searches": search_service.get_popular_searches(db, limit)}


@router.get("/facets")
async def get_search_facets(query: Optional[str] = None, db: Session = Depends(get_db)):
    base_query = db.query(Document).filter(Document.is_archived.is_(False))

    if query:
        base_query = base_query.filter(
            Document.search_vector.op("@@")(func.plainto_tsquery("english", query))
        )

    category_facets = (
        db.query(Category.id, Category.name, func.count(Document.id).label("count"))
        .join(
            Document,
            or_(Document.ai_category_id == Category.id, Document.user_category_id == Category.id),
        )
        .group_by(Category.id, Category.name)
        .all()
    )

    source_facets = (
        base_query.with_entities(Document.source, func.count(Document.id).label("count"))
        .group_by(Document.source)
        .all()
    )

    file_type_facets = (
        base_query.with_entities(Document.file_type, func.count(Document.id).label("count"))
        .group_by(Document.file_type)
        .all()
    )

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
):
    from app.services.embedding_service import embedding_service

    vector_results = embedding_service.semantic_search(query=query, limit=limit, score_threshold=threshold)

    document_ids = [r["document_id"] for r in vector_results]
    if not document_ids:
        return {"query": query, "results": [], "total": 0}

    documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
    documents_by_id = {str(doc.id): doc for doc in documents}

    results = []
    for match in vector_results:
        doc = documents_by_id.get(match["document_id"])
        if doc:
            results.append(
                {
                    "document": doc,
                    "similarity_score": match["score"],
                    "metadata": match.get("metadata"),
                }
            )

    return {"query": query, "results": results, "total": len(results)}


@router.get("/documents/{document_id}/similar", response_model=SemanticSearchResponse)
async def find_similar_documents(
    document_id: UUID,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    from app.services.embedding_service import embedding_service

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    similar = embedding_service.find_similar_documents(document_id=str(document_id), limit=limit)
    doc_ids = [s["document_id"] for s in similar]
    if not doc_ids:
        return {"query": str(document_id), "results": [], "total": 0}

    documents = db.query(Document).filter(Document.id.in_(doc_ids)).all()
    documents_by_id = {str(doc.id): doc for doc in documents}

    results = []
    for item in similar:
        doc = documents_by_id.get(item["document_id"])
        if doc:
            results.append(
                {
                    "document": doc,
                    "similarity_score": item["score"],
                    "metadata": item.get("metadata"),
                }
            )

    return {"query": str(document_id), "results": results, "total": len(results)}
