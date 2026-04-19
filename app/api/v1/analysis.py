from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.category_discovery import category_discovery

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/categories/discover")
def discover_categories(db: Session = Depends(get_db)):
    return category_discovery.discover_categories(db)


@router.post("/documents/{document_id}/analyze")
def analyze_document(document_id: UUID, db: Session = Depends(get_db)):
    from app.crud.document import get_document
    from app.models.category import Category
    from app.services.ai_analyzer import ai_analyzer
    from app.services.categorizer import categorizer

    document = get_document(db, id=document_id)
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

    document.summary = analysis.get("summary")
    document.key_points = analysis.get("key_points", [])
    document.entities = analysis.get("entities", {})
    document.action_items = analysis.get("action_items", [])
    document.ai_tags = analysis.get("tags", [])
    categorizer.apply_category(db, document, analysis)
    db.add(document)
    db.commit()
    db.refresh(document)

    return {"document_id": str(document_id), "analysis": analysis, "status": "completed"}
