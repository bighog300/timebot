from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from datetime import datetime

from app.api.deps import get_current_user, get_db, require_editor_or_admin
from app.models.user import User
from app.schemas.review_workflow import (
    ActionItemMetricsResponse,
    ActionItemResponse,
    ActionItemState,
    ActionItemUpdate,
    PaginatedActionItemsResponse,
    BulkActionItemMutationResponse,
    BulkMutationRequest,
)
from app.services.action_items import action_items_service

router = APIRouter(tags=["action-items"])


@router.get("/action-items", response_model=PaginatedActionItemsResponse)
def list_action_items(
    status: ActionItemState | None = Query(default=None),
    document_id: UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, total_count = action_items_service.list_items(db, user_id=current_user.id, state=status.value if status else None, document_id=document_id, date_from=date_from, date_to=date_to, sort_by=sort_by, sort_order=sort_order, limit=limit, offset=offset)
    return {"items": items, "total_count": total_count, "limit": limit, "offset": offset}


@router.get("/action-items/metrics", response_model=ActionItemMetricsResponse)
def get_action_item_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return action_items_service.get_metrics(db, user_id=current_user.id)


@router.get("/documents/{document_id}/action-items", response_model=list[ActionItemResponse])
def list_document_action_items(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return action_items_service.list_document_items(db, user_id=current_user.id, document_id=document_id)


@router.patch("/action-items/{action_item_id}", response_model=ActionItemResponse)
def update_action_item(
    action_item_id: UUID,
    action_in: ActionItemUpdate,
    _: str = Depends(require_editor_or_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = action_items_service.get_item(db, user_id=current_user.id, action_item_id=action_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    return action_items_service.update_item(
        db,
        item,
        content=action_in.content,
        metadata=action_in.action_metadata,
        actor_id=current_user.id,
    )


@router.post("/action-items/{action_item_id}/complete", response_model=ActionItemResponse)
def complete_action_item(
    action_item_id: UUID,
    _: str = Depends(require_editor_or_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = action_items_service.get_item(db, user_id=current_user.id, action_item_id=action_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    try:
        return action_items_service.complete_item(db, item, actor_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/action-items/{action_item_id}/dismiss", response_model=ActionItemResponse)
def dismiss_action_item(
    action_item_id: UUID,
    _: str = Depends(require_editor_or_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = action_items_service.get_item(db, user_id=current_user.id, action_item_id=action_item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    try:
        return action_items_service.dismiss_item(db, item, actor_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/action-items/bulk-complete", response_model=BulkActionItemMutationResponse)
def bulk_complete_action_items(
    request: BulkMutationRequest,
    _: str = Depends(require_editor_or_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, skipped_count = action_items_service.bulk_complete_items(
        db,
        user_id=current_user.id,
        item_ids=request.ids,
        note=request.note,
        actor_id=current_user.id,
    )
    return {"updated_count": len(items), "skipped_count": skipped_count, "items": items}


@router.post("/action-items/bulk-dismiss", response_model=BulkActionItemMutationResponse)
def bulk_dismiss_action_items(
    request: BulkMutationRequest,
    _: str = Depends(require_editor_or_admin),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items, skipped_count = action_items_service.bulk_dismiss_items(
        db,
        user_id=current_user.id,
        item_ids=request.ids,
        note=request.note,
        actor_id=current_user.id,
    )
    return {"updated_count": len(items), "skipped_count": skipped_count, "items": items}
