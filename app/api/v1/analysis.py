from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.category_discovery import category_discovery

router = APIRouter(prefix="/analysis", tags=["analysis"], dependencies=[Depends(get_current_user)])


@router.post("/categories/discover")
def discover_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return category_discovery.discover_categories(db)


@router.post("/documents/{document_id}/analyze")
def analyze_document(document_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.crud.document import get_document
    from app.models.category import Category
    from app.services.ai_analyzer import ai_analyzer
    from app.services.document_intelligence import document_intelligence_service

    document = get_document(db, id=document_id, user=current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    if not document.raw_text:
        raise HTTPException(status_code=400, detail="Document has no extracted text")

    categories = db.query(Category).all()
    analysis = ai_analyzer.analyze_document(
        text=document.raw_text,
        filename=document.filename,
        file_type=document.file_type,
        existing_categories=[c.name for c in categories],
    )
    if not analysis:
        raise HTTPException(status_code=500, detail="AI analysis failed")

    document_intelligence_service.create_from_analysis(db, document, analysis)

    return {"document_id": str(document_id), "analysis": analysis, "status": "completed"}
