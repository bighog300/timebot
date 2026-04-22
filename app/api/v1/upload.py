from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.document_processor import document_processor

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/", response_model=DocumentResponse, status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        document = await document_processor.process_upload(db, file, current_user)
        return document
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
