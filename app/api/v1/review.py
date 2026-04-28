from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.review_workflow import DocumentReviewItemResponse, ReviewAuditEventResponse, ReviewResolutionRequest
from app.services.review_audit import review_audit_service
from app.services.review_queue import review_queue_service

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/items", response_model=list[DocumentReviewItemResponse])
def list_review_items(
    status: str = Query("open"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return review_queue_service.list_items(db, current_user.id, status=status)


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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = review_queue_service.get_item(db, item_id=item_id, user_id=current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    return review_queue_service.resolve_item(db, item=item, note=request.note, actor_id=current_user.id)


@router.post("/items/{item_id}/dismiss", response_model=DocumentReviewItemResponse)
def dismiss_review_item(
    item_id: UUID,
    request: ReviewResolutionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = review_queue_service.get_item(db, item_id=item_id, user_id=current_user.id)
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    return review_queue_service.dismiss_item(db, item=item, note=request.note, actor_id=current_user.id)


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
