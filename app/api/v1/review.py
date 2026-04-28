from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.review_workflow import DocumentReviewItemResponse, ReviewResolutionRequest
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
    return review_queue_service.resolve_item(db, item=item, note=request.note)


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
    return review_queue_service.dismiss_item(db, item=item, note=request.note)
