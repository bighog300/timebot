from datetime import datetime, timezone

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_role, get_db
from app.models.system_intelligence import (
    SystemIntelligenceAuditLog,
    SystemIntelligenceDocument,
    SystemIntelligenceSubmission,
    SystemIntelligenceWebReference,
)
from app.models.user import User
from app.schemas.system_intelligence import *
from app.services.storage import storage
from app.services.system_intelligence_ingest import hash_bytes, ingest_document

router = APIRouter(tags=["system-intelligence"])


def _require_admin(role: str = Depends(get_current_user_role)):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


def _audit(db: Session, actor: User, action: str, target_type: str, target_id: str, metadata: dict | None = None):
    db.add(SystemIntelligenceAuditLog(actor=actor.email, action=action, target_type=target_type, target_id=target_id, metadata_json=metadata or {}))


@router.get('/admin/system-intelligence/documents', response_model=list[SystemIntelligenceDocumentResponse], dependencies=[Depends(_require_admin)])
def list_docs(db: Session = Depends(get_db)):
    return db.query(SystemIntelligenceDocument).order_by(SystemIntelligenceDocument.created_at.desc()).all()

@router.post('/admin/system-intelligence/documents', response_model=SystemIntelligenceDocumentResponse, dependencies=[Depends(_require_admin)])
async def create_doc(title: str = Form(...), description: str | None = Form(None), category: str | None = Form(None), jurisdiction: str | None = Form(None), source_type: str = Form("admin_upload"), file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    allowed = {".pdf": "application/pdf", ".txt": "text/plain", ".md": "text/markdown", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    max_size = 10 * 1024 * 1024
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File exceeds max size (10MB)")
    await file.seek(0)
    saved_path, file_size = await storage.save_upload(file)
    mime_type = file.content_type or allowed[suffix]
    doc = SystemIntelligenceDocument(source_type=source_type, title=title, description=description, category=category, jurisdiction=jurisdiction, status='draft', storage_uri=str(saved_path), mime_type=mime_type, content_hash=hash_bytes(content), original_filename=Path(file.filename or "upload").name, size_bytes=file_size)
    db.add(doc); db.flush(); ingest_document(db, doc); _audit(db,user,'document_created','document',str(doc.id),{'title':doc.title}); db.commit(); db.refresh(doc); return doc

@router.get('/admin/system-intelligence/documents/{doc_id}', response_model=SystemIntelligenceDocumentResponse, dependencies=[Depends(_require_admin)])
def get_doc(doc_id: str, db: Session = Depends(get_db)):
    doc = db.query(SystemIntelligenceDocument).filter(SystemIntelligenceDocument.id == doc_id).first()
    if not doc: raise HTTPException(404, 'Not found')
    return doc

@router.patch('/admin/system-intelligence/documents/{doc_id}', response_model=SystemIntelligenceDocumentResponse, dependencies=[Depends(_require_admin)])
def patch_doc(doc_id: str, payload: SystemIntelligenceDocumentPatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(SystemIntelligenceDocument).filter(SystemIntelligenceDocument.id == doc_id).first()
    if not doc: raise HTTPException(404, 'Not found')
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(doc,k,v)
    _audit(db,user,'document_updated','document',str(doc.id),payload.model_dump(exclude_unset=True)); db.commit(); db.refresh(doc); return doc

@router.delete('/admin/system-intelligence/documents/{doc_id}', dependencies=[Depends(_require_admin)])
def delete_doc(doc_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(SystemIntelligenceDocument).filter(SystemIntelligenceDocument.id == doc_id).first()
    if not doc: raise HTTPException(404, 'Not found')
    doc.status='deleted'; _audit(db,user,'document_deleted','document',str(doc.id)); db.commit(); return {'ok':True}

@router.post('/admin/system-intelligence/documents/{doc_id}/archive', response_model=SystemIntelligenceDocumentResponse, dependencies=[Depends(_require_admin)])
def archive_doc(doc_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(SystemIntelligenceDocument).filter(SystemIntelligenceDocument.id == doc_id).first()
    if not doc: raise HTTPException(404, 'Not found')
    doc.status='archived'; _audit(db,user,'document_archived','document',str(doc.id)); db.commit(); db.refresh(doc); return doc

@router.post('/admin/system-intelligence/documents/{doc_id}/activate', response_model=SystemIntelligenceDocumentResponse, dependencies=[Depends(_require_admin)])
def activate_doc(doc_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(SystemIntelligenceDocument).filter(SystemIntelligenceDocument.id == doc_id).first()
    if not doc: raise HTTPException(404, 'Not found')
    doc.status='active'; _audit(db,user,'document_activated','document',str(doc.id)); db.commit(); db.refresh(doc); return doc

@router.post('/admin/system-intelligence/documents/{doc_id}/reindex', response_model=SystemIntelligenceDocumentResponse, dependencies=[Depends(_require_admin)])
def reindex_doc(doc_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doc = db.query(SystemIntelligenceDocument).filter(SystemIntelligenceDocument.id == doc_id).first()
    if not doc: raise HTTPException(404, 'Not found')
    ingest_document(db, doc)
    _audit(db,user,'document_reindexed','document',str(doc.id)); db.commit(); db.refresh(doc); return doc

@router.post('/system-intelligence/submissions', response_model=SystemIntelligenceSubmissionResponse)
def submit(payload: SystemIntelligenceSubmissionCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sub = SystemIntelligenceSubmission(user_id=user.id, status='pending', **payload.model_dump())
    db.add(sub); db.commit(); db.refresh(sub); return sub

@router.get('/system-intelligence/submissions/mine', response_model=list[SystemIntelligenceSubmissionResponse])
def my_submissions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(SystemIntelligenceSubmission).filter(SystemIntelligenceSubmission.user_id == user.id).all()

@router.delete('/system-intelligence/submissions/{submission_id}')
def withdraw(submission_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sub = db.query(SystemIntelligenceSubmission).filter(SystemIntelligenceSubmission.id == submission_id, SystemIntelligenceSubmission.user_id == user.id).first()
    if not sub: raise HTTPException(404, 'Not found')
    sub.status='withdrawn'; db.commit(); return {'ok':True}

@router.get('/admin/system-intelligence/submissions', response_model=list[SystemIntelligenceSubmissionResponse], dependencies=[Depends(_require_admin)])
def list_subs(db: Session = Depends(get_db)):
    return db.query(SystemIntelligenceSubmission).all()

@router.post('/admin/system-intelligence/submissions/{submission_id}/approve', response_model=SystemIntelligenceSubmissionResponse, dependencies=[Depends(_require_admin)])
def approve_sub(submission_id: str, payload: SystemIntelligenceSubmissionModeration, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sub = db.query(SystemIntelligenceSubmission).filter(SystemIntelligenceSubmission.id == submission_id).first()
    if not sub: raise HTTPException(404, 'Not found')
    doc = SystemIntelligenceDocument(source_type='user_recommendation', status='active', title=sub.title, category=sub.suggested_category, jurisdiction=sub.suggested_jurisdiction)
    db.add(doc); db.flush()
    sub.status='approved'; sub.admin_notes=payload.admin_notes; sub.reviewed_by_admin_id=user.id; sub.resulting_system_document_id=doc.id
    _audit(db,user,'submission_approved','submission',str(sub.id),{'document_id':str(doc.id)})
    db.commit(); db.refresh(sub); return sub

@router.post('/admin/system-intelligence/submissions/{submission_id}/reject', response_model=SystemIntelligenceSubmissionResponse, dependencies=[Depends(_require_admin)])
def reject_sub(submission_id: str, payload: SystemIntelligenceSubmissionModeration, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sub = db.query(SystemIntelligenceSubmission).filter(SystemIntelligenceSubmission.id == submission_id).first()
    if not sub: raise HTTPException(404, 'Not found')
    sub.status='rejected'; sub.admin_notes=payload.admin_notes; sub.reviewed_by_admin_id=user.id
    _audit(db,user,'submission_rejected','submission',str(sub.id))
    db.commit(); db.refresh(sub); return sub

@router.get('/admin/system-intelligence/web-references', response_model=list[SystemIntelligenceWebReferenceResponse], dependencies=[Depends(_require_admin)])
def list_refs(db: Session = Depends(get_db)):
    return db.query(SystemIntelligenceWebReference).all()

@router.post('/admin/system-intelligence/web-references', response_model=SystemIntelligenceWebReferenceResponse, dependencies=[Depends(_require_admin)])
def create_ref(payload: SystemIntelligenceWebReferenceCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ref = SystemIntelligenceWebReference(**payload.model_dump(), status='candidate')
    db.add(ref); db.flush(); _audit(db,user,'web_reference_created','web_reference',str(ref.id)); db.commit(); db.refresh(ref); return ref

@router.patch('/admin/system-intelligence/web-references/{ref_id}', response_model=SystemIntelligenceWebReferenceResponse, dependencies=[Depends(_require_admin)])
def patch_ref(ref_id: str, payload: SystemIntelligenceWebReferencePatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ref = db.query(SystemIntelligenceWebReference).filter(SystemIntelligenceWebReference.id == ref_id).first()
    if not ref: raise HTTPException(404, 'Not found')
    for k,v in payload.model_dump(exclude_unset=True).items(): setattr(ref,k,v)
    _audit(db,user,'web_reference_updated','web_reference',str(ref.id)); db.commit(); db.refresh(ref); return ref

@router.post('/admin/system-intelligence/web-references/{ref_id}/approve', response_model=SystemIntelligenceWebReferenceResponse, dependencies=[Depends(_require_admin)])
def approve_ref(ref_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ref = db.query(SystemIntelligenceWebReference).filter(SystemIntelligenceWebReference.id == ref_id).first()
    if not ref: raise HTTPException(404, 'Not found')
    ref.status='active'; _audit(db,user,'web_reference_approved','web_reference',str(ref.id)); db.commit(); db.refresh(ref); return ref

@router.post('/admin/system-intelligence/web-references/{ref_id}/archive', response_model=SystemIntelligenceWebReferenceResponse, dependencies=[Depends(_require_admin)])
def archive_ref(ref_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ref = db.query(SystemIntelligenceWebReference).filter(SystemIntelligenceWebReference.id == ref_id).first()
    if not ref: raise HTTPException(404, 'Not found')
    ref.status='archived'; _audit(db,user,'web_reference_archived','web_reference',str(ref.id)); db.commit(); db.refresh(ref); return ref

@router.delete('/admin/system-intelligence/web-references/{ref_id}', dependencies=[Depends(_require_admin)])
def delete_ref(ref_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ref = db.query(SystemIntelligenceWebReference).filter(SystemIntelligenceWebReference.id == ref_id).first()
    if not ref: raise HTTPException(404, 'Not found')
    db.delete(ref); _audit(db,user,'web_reference_deleted','web_reference',str(ref.id)); db.commit(); return {'ok':True}

@router.get('/admin/system-intelligence/audit-log', response_model=list[SystemIntelligenceAuditLogResponse], dependencies=[Depends(_require_admin)])
def audit_logs(db: Session = Depends(get_db)):
    return db.query(SystemIntelligenceAuditLog).order_by(SystemIntelligenceAuditLog.created_at.desc()).all()
