import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud import document as crud_document
from app.models.user import User
from app.schemas.document import (
    DocumentClusterResponse,
    DocumentResponse,
    DocumentReviewRequest,
    DocumentSearchResponse,
    DocumentUpdate,
)
from app.services.document_clusters import document_cluster_service
from app.services.limit_enforcement import enforce_feature, enforce_limit
from app.services.cost_protection import enforce_daily_cap, enforce_rate_limit, hard_daily_caps
from app.services.usage import record_usage
from app.schemas.review_workflow import (
    CategoryOverrideRequest,
    DocumentRelationshipListItemResponse,
    DocumentIntelligenceResponse,
    DocumentIntelligenceUpdate,
    RelationshipReviewStatus,
    ReviewAuditEventResponse,
)
from app.services.document_intelligence import document_intelligence_service
from app.services.openai_client import openai_client_service
from app.services.relationship_review import relationship_review_service
from app.services.review_audit import review_audit_service

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_document.get_documents(db, user=current_user, skip=skip, limit=limit, include_archived=include_archived)


@router.get("/search", response_model=DocumentSearchResponse)
def search_documents(
    query: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    results = crud_document.search_documents(db, user=current_user, query=query, skip=skip, limit=limit)
    return DocumentSearchResponse(documents=results, total=len(results), query=query)


@router.get("/clusters", response_model=List[DocumentClusterResponse])
def list_document_clusters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return document_cluster_service.list_clusters_for_user(db, user_id=current_user.id)


@router.get("/review-queue", response_model=List[DocumentResponse])
def get_review_queue(
    status: str = Query("pending"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud_document.get_review_queue(db, user=current_user, status=status, skip=skip, limit=limit)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = crud_document.get_document(db, id=document_id, user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/relationships", response_model=List[DocumentRelationshipListItemResponse])
def list_document_relationships(
    document_id: UUID,
    include_dismissed: bool = Query(False),
    status: RelationshipReviewStatus | None = Query(default=None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = crud_document.get_document(db, id=document_id, user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    items = relationship_review_service.list_for_document(
        db,
        document_id=document_id,
        user_id=current_user.id,
        include_dismissed=include_dismissed,
        status=status,
        limit=limit,
    )
    payload: list[DocumentRelationshipListItemResponse] = []
    for item in items:
        is_source = str(item.source_document_id) == str(document_id)
        related_doc = item.target_document if is_source else item.source_document
        payload.append(
            DocumentRelationshipListItemResponse(
                id=item.id,
                status=item.status,
                relationship_type=item.relationship_type,
                confidence=item.confidence,
                related_document_id=related_doc.id,
                related_document_title=item._document_title(related_doc),
                related_document_name=item._document_title(related_doc),
                related_document_snippet=item._document_snippet(related_doc),
                direction="source" if is_source else "target",
                created_at=item.created_at,
                updated_at=item.reviewed_at,
                explanation_metadata=(item.metadata_json or {}).get("explanation", {}),
            )
        )
    return payload


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: UUID, document_in: DocumentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    document = crud_document.get_document(db, id=document_id, user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return crud_document.update_document(db, db_obj=document, obj_in=document_in)


@router.delete("/{document_id}")
def delete_document(document_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = crud_document.get_document(db, id=document_id, user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    from app.services.storage import storage
    storage.delete_file(document.original_path)
    crud_document.delete_document(db, id=document_id, user=current_user)
    return {"message": "Document deleted", "id": str(document_id)}


@router.post("/{document_id}/reprocess")
def reprocess_document(document_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = crud_document.get_document(db, id=document_id, user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    caps = hard_daily_caps()
    enforce_rate_limit(db, user_id=current_user.id, metric="processing_requests_rate", max_calls=20)
    enforce_daily_cap(db, user_id=current_user.id, metric="processing_jobs_daily", cap=caps["processing_jobs_daily"])
    enforce_limit(db, current_user.id, "processing_jobs_per_month", quantity=1)
    logger.info("Reprocess requested document_id=%s actor_id=%s", document_id, current_user.id)
    document.processing_status = "queued"
    document.processing_error = None
    metadata = document.extracted_metadata if isinstance(document.extracted_metadata, dict) else {}
    updated = dict(metadata)
    updated["enrichment_status"] = "pending"
    updated["enrichment_pending"] = True
    updated["enrichment_tasks"] = {"relationships": "pending", "embeddings": "pending"}
    updated["intelligence_stale"] = True
    document.extracted_metadata = updated
    db.add(document)
    db.commit()

    from app.workers.tasks import reprocess_document_task
    task_result = reprocess_document_task.apply_async(args=[str(document_id)])
    record_usage(db, user_id=current_user.id, metric="processing_requests_rate", quantity=1)
    record_usage(db, user_id=current_user.id, metric="processing_jobs_daily", quantity=1, metadata={"source": "api_reprocess"})
    db.commit()
    logger.info("Reprocess queued document_id=%s actor_id=%s task_id=%s queue=ingestion", document_id, current_user.id, task_result.id)
    return {"message": "Reprocessing queued", "document_id": str(document_id), "task_id": task_result.id}


@router.post("/{document_id}/review", response_model=DocumentResponse)
def review_document(
    document_id: UUID,
    review_in: DocumentReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = crud_document.get_document(db, id=document_id, user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    action_map = {"approve": "approved", "reject": "rejected", "edit": "edited"}
    if review_in.action not in action_map:
        raise HTTPException(status_code=422, detail="Invalid review action")

    updates = {
        "review_status": action_map[review_in.action],
        "reviewed_at": datetime.now(timezone.utc),
        "reviewed_by": current_user.email,
    }
    if review_in.action == "edit":
        if review_in.override_summary is not None:
            updates["override_summary"] = review_in.override_summary
        if review_in.override_tags is not None:
            updates["override_tags"] = review_in.override_tags

    return crud_document.update_document_fields(db, db_obj=document, **updates)


@router.get("/{document_id}/intelligence", response_model=DocumentIntelligenceResponse | None)
def get_document_intelligence(document_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = crud_document.get_document(db, id=document_id, user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    intelligence = document_intelligence_service.get_for_document(db, document)
    return intelligence


@router.post("/{document_id}/intelligence/regenerate", response_model=DocumentIntelligenceResponse)
def regenerate_document_intelligence(document_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = crud_document.get_document(db, id=document_id, user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not openai_client_service.enabled:
        raise HTTPException(
            status_code=503,
            detail="AI enrichment unavailable: configure OPENAI_API_KEY and retry regeneration.",
        )
    enforce_feature(db, current_user.id, "insights_enabled")
    try:
        return document_intelligence_service.regenerate(db, document)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/{document_id}/intelligence", response_model=DocumentIntelligenceResponse)
def patch_document_intelligence(
    document_id: UUID,
    intelligence_in: DocumentIntelligenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = crud_document.get_document(db, id=document_id, user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    intelligence = document_intelligence_service.get_for_document(db, document)
    if not intelligence:
        raise HTTPException(status_code=404, detail="Document intelligence not found")
    return document_intelligence_service.update_intelligence(
        db,
        intelligence,
        intelligence_in.model_dump(exclude_unset=True),
        actor_id=current_user.id,
    )


@router.post("/{document_id}/category/approve", response_model=DocumentResponse)
def approve_document_category(document_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    document = crud_document.get_document(db, id=document_id, user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    intelligence = document_intelligence_service.get_for_document(db, document)
    if not intelligence:
        raise HTTPException(status_code=404, detail="Document intelligence not found")
    try:
        return document_intelligence_service.approve_category(db, document, intelligence, actor_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "message": str(exc),
                "document_id": str(document.id),
                "suggested_category_id": str(intelligence.suggested_category_id) if intelligence.suggested_category_id else None,
                "document_ai_category_id": str(document.ai_category_id) if document.ai_category_id else None,
            },
        ) from exc


@router.post("/{document_id}/category/override", response_model=DocumentResponse)
def override_document_category(
    document_id: UUID,
    override_in: CategoryOverrideRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = crud_document.get_document(db, id=document_id, user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    intelligence = document_intelligence_service.get_for_document(db, document)
    if not intelligence:
        raise HTTPException(status_code=404, detail="Document intelligence not found")
    return document_intelligence_service.override_category(
        db,
        document,
        intelligence,
        override_in.category_id,
        actor_id=current_user.id,
    )


@router.get("/{document_id}/review-audit", response_model=List[ReviewAuditEventResponse])
def get_document_review_audit(
    document_id: UUID,
    event_type: str | None = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = crud_document.get_document(db, id=document_id, user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return review_audit_service.list_events(
        db,
        user_id=current_user.id,
        event_type=event_type,
        document_id=document_id,
        skip=skip,
        limit=limit,
    )
