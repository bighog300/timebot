import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.document_processor import document_processor
from app.services.cost_protection import enforce_daily_cap, enforce_rate_limit
from app.services.limit_enforcement import enforce_limit
from app.services.usage import record_usage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=DocumentResponse, status_code=202)
@router.post("/", response_model=DocumentResponse, status_code=202)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        enforce_rate_limit(db, user_id=current_user.id, metric="upload_requests_rate", max_calls=10)
        enforce_daily_cap(db, user_id=current_user.id, metric="uploads_daily", cap=250)
        enforce_limit(db, current_user.id, "documents_per_month", quantity=1)
        document = await document_processor.process_upload(db, file, current_user)
        record_usage(db, user_id=current_user.id, metric="upload_requests_rate", quantity=1)
        record_usage(db, user_id=current_user.id, metric="uploads_daily", quantity=1)
        db.commit()
        return document
    except ValueError as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail=str(e))
