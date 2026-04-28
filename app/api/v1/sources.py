from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud import source_mapping as source_mapping_crud
from app.models.user import User
from app.schemas.source_mapping import (
    ActiveSourceMappingResponse,
    BulkRulePatchRequest,
    MappingDraftResponse,
    MappingRulePatch,
    MappingRuleResponse,
)
from app.services.source_mapper import source_mapper_service

router = APIRouter(tags=["source-mapper"])


@router.post("/api/sources/{source_id}/mapping-drafts/from-profile/{profile_id}", response_model=MappingDraftResponse)
def create_mapping_draft_from_profile(
    source_id: str,
    profile_id: UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return source_mapper_service.generate_draft_from_profile(db, source_id=source_id, profile_id=profile_id)


@router.get("/api/sources/{source_id}/mapping-drafts", response_model=list[MappingDraftResponse])
def list_mapping_drafts(
    source_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return source_mapping_crud.get_source_drafts(db, source_id)


@router.get("/api/sources/{source_id}/mapping-drafts/{draft_id}", response_model=MappingDraftResponse)
def get_mapping_draft(
    source_id: str,
    draft_id: UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return source_mapper_service.get_draft_or_404(db, source_id=source_id, draft_id=draft_id)


@router.patch("/api/sources/{source_id}/mapping-drafts/{draft_id}/rules/{rule_id}", response_model=MappingRuleResponse)
def patch_mapping_rule(
    source_id: str,
    draft_id: UUID,
    rule_id: UUID,
    payload: MappingRulePatch,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return source_mapper_service.patch_rule(
        db,
        source_id=source_id,
        draft_id=draft_id,
        rule_id=rule_id,
        patch=payload.model_dump(exclude_unset=True),
    )


@router.patch("/api/sources/{source_id}/mapping-drafts/{draft_id}/rules", response_model=MappingDraftResponse)
def patch_mapping_rules_bulk(
    source_id: str,
    draft_id: UUID,
    payload: BulkRulePatchRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    patches = [patch.model_dump(exclude_unset=True) for patch in payload.patches]
    return source_mapper_service.bulk_patch_rules(db, source_id=source_id, draft_id=draft_id, patches=patches)


@router.post("/api/sources/{source_id}/mapping-drafts/{draft_id}/approve", response_model=MappingDraftResponse)
def approve_mapping_draft(
    source_id: str,
    draft_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return source_mapper_service.approve_draft(
        db,
        source_id=source_id,
        draft_id=draft_id,
        approved_by=current_user.email,
    )


@router.post("/api/sources/{source_id}/mapping-drafts/{draft_id}/activate", response_model=ActiveSourceMappingResponse)
def activate_mapping_draft(
    source_id: str,
    draft_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return source_mapper_service.activate_draft(
        db,
        source_id=source_id,
        draft_id=draft_id,
        activated_by=current_user.email,
    )


@router.get("/api/sources/{source_id}/mapping-active", response_model=ActiveSourceMappingResponse)
def get_active_mapping(
    source_id: str,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    active = source_mapping_crud.get_active_mapping(db, source_id)
    if not active:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active mapping not found")
    return active
