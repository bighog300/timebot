from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud import document as crud_document
from app.schemas.document import DocumentResponse, DocumentSearchResponse, DocumentUpdate

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    include_archived: bool = False,
    db: Session = Depends(get_db),
):
    return crud_document.get_documents(db, skip=skip, limit=limit, include_archived=include_archived)


@router.get("/search", response_model=DocumentSearchResponse)
def search_documents(
    query: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    results = crud_document.search_documents(db, query=query, skip=skip, limit=limit)
    return DocumentSearchResponse(documents=results, total=len(results), query=query)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: UUID, db: Session = Depends(get_db)):
    document = crud_document.get_document(db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: UUID, document_in: DocumentUpdate, db: Session = Depends(get_db)
):
    document = crud_document.get_document(db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return crud_document.update_document(db, db_obj=document, obj_in=document_in)


@router.delete("/{document_id}")
def delete_document(document_id: UUID, db: Session = Depends(get_db)):
    document = crud_document.get_document(db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    from app.services.storage import storage
    storage.delete_file(document.original_path)
    crud_document.delete_document(db, id=document_id)
    return {"message": "Document deleted", "id": str(document_id)}


@router.post("/{document_id}/reprocess")
def reprocess_document(document_id: UUID, db: Session = Depends(get_db)):
    document = crud_document.get_document(db, id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    from app.workers.tasks import reprocess_document_task
    reprocess_document_task.apply_async(args=[str(document_id)])
    return {"message": "Reprocessing queued", "document_id": str(document_id)}
