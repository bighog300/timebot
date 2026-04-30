from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.gmail_import import gmail_import_service

router = APIRouter(prefix="/imports/gmail", tags=["gmail-import"])

class PreviewReq(BaseModel):
    sender_email: str
    max_results: int = 20
    include_attachments: bool = False

class ImportReq(BaseModel):
    sender_email: str
    message_ids: list[str]
    include_attachments: bool = False

@router.post('/preview')
def preview(req: PreviewReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try: return gmail_import_service.preview(db, current_user, req.sender_email, req.max_results)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc))

@router.post('/import')
def import_selected(req: ImportReq, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try: return gmail_import_service.import_messages(db, current_user, req.sender_email, req.message_ids, req.include_attachments)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc))
