from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from datetime import datetime

from app.api.deps import get_current_user, get_db, require_editor_or_admin
from app.models.user import User
from app.schemas.review_workflow import (
    BulkMutationRequest,
    BulkReviewItemMutationResponse,
    DocumentReviewItemResponse,
    PaginatedReviewItemsResponse,
    RelationshipReviewDecisionRequest,
    RelationshipReviewResponse,
    RelationshipReviewStatus,
    ReviewAuditEventResponse,
    ReviewItemStatus,
    ReviewMetricsResponse,
    ReviewResolutionRequest,
)
from app.services.review_audit import review_audit_service
from app.services.relationship_review import relationship_review_service
from app.services.review_queue import review_queue_service

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/items", response_model=PaginatedReviewItemsResponse)
def list_review_items(
    status: ReviewItemStatus | None = Query(default=None),
    review_type: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    document_id: UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="asc"),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total_count = review_queue_service.list_items(db, current_user.id, status=status.value if status else None, review_type=review_type, priority=priority, document_id=document_id, date_from=date_from, date_to=date_to, sort_by=sort_by, sort_order=sort_order, limit=limit, offset=offset)
    return {"items": items, "total_count": total_count, "limit": limit, "offset": offset}


@router.get("/metrics", response_model=ReviewMetricsResponse)
def get_review_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return review_queue_service.get_metrics(db, user_id=current_user.id)


@router.get("/items/{item_id}", response_model=DocumentReviewItemResponse)
def get_review_item(item_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    item = review_queue_service.get_item(db, item_id=item_id, user_id=current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    return item


@router.post("/items/{item_id}/resolve", response_model=DocumentReviewItemResponse)
def resolve_review_item(
    item_id: UUID,
    request: ReviewResolutionRequest,
    _: str = Depends(require_editor_or_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = review_queue_service.get_item(db, item_id=item_id, user_id=current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    try:
        return review_queue_service.resolve_item(db, item=item, note=request.note, actor_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/items/{item_id}/dismiss", response_model=DocumentReviewItemResponse)
def dismiss_review_item(
    item_id: UUID,
    request: ReviewResolutionRequest,
    _: str = Depends(require_editor_or_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = review_queue_service.get_item(db, item_id=item_id, user_id=current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    try:
        return review_queue_service.dismiss_item(db, item=item, note=request.note, actor_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/items/bulk-resolve", response_model=BulkReviewItemMutationResponse)
def bulk_resolve_review_items(
    request: BulkMutationRequest,
    _: str = Depends(require_editor_or_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, skipped_count = review_queue_service.bulk_resolve_items(
        db,
        user_id=current_user.id,
        item_ids=request.ids,
        note=request.note,
        actor_id=current_user.id,
    )
    return {"updated_count": len(items), "skipped_count": skipped_count, "items": items}


@router.post("/items/bulk-dismiss", response_model=BulkReviewItemMutationResponse)
def bulk_dismiss_review_items(
    request: BulkMutationRequest,
    _: str = Depends(require_editor_or_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, skipped_count = review_queue_service.bulk_dismiss_items(
        db,
        user_id=current_user.id,
        item_ids=request.ids,
        note=request.note,
        actor_id=current_user.id,
    )
    return {"updated_count": len(items), "skipped_count": skipped_count, "items": items}


@router.get("/audit", response_model=list[ReviewAuditEventResponse])
def list_review_audit_events(
    event_type: str | None = Query(default=None),
    document_id: UUID | None = Query(default=None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return review_audit_service.list_events(
        db,
        user_id=current_user.id,
        event_type=event_type,
        document_id=document_id,
        skip=skip,
        limit=limit,
    )


@router.get("/relationships", response_model=list[RelationshipReviewResponse])
def list_relationship_reviews(
    status: RelationshipReviewStatus = Query(RelationshipReviewStatus.PENDING),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return relationship_review_service.list_items(db, user_id=current_user.id, status=status)


@router.get("/relationships/{relationship_id}", response_model=RelationshipReviewResponse)
def get_relationship_review(
    relationship_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = relationship_review_service.get_item(db, relationship_id=relationship_id, user_id=current_user.id)
    if not review:
        raise HTTPException(status_code=404, detail="Relationship review not found")
    return review


@router.post("/relationships/{relationship_id}/confirm", response_model=RelationshipReviewResponse)
def confirm_relationship_review(
    relationship_id: UUID,
    request: RelationshipReviewDecisionRequest,
    _: str = Depends(require_editor_or_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = relationship_review_service.get_item(db, relationship_id=relationship_id, user_id=current_user.id)
    if not review:
        raise HTTPException(status_code=404, detail="Relationship review not found")
    try:
        return relationship_review_service.confirm(
            db,
            relationship_review=review,
            reviewer_id=current_user.id,
            reason_codes_json=request.reason_codes_json,
            metadata_json=request.metadata_json,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/relationships/{relationship_id}/dismiss", response_model=RelationshipReviewResponse)
def dismiss_relationship_review(
    relationship_id: UUID,
    request: RelationshipReviewDecisionRequest,
    _: str = Depends(require_editor_or_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = relationship_review_service.get_item(db, relationship_id=relationship_id, user_id=current_user.id)
    if not review:
        raise HTTPException(status_code=404, detail="Relationship review not found")
    try:
        return relationship_review_service.dismiss(
            db,
            relationship_review=review,
            reviewer_id=current_user.id,
            reason_codes_json=request.reason_codes_json,
            metadata_json=request.metadata_json,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
