from datetime import date
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.document import Document
from app.models.divorce import DivorceReport, DivorceTimelineItem
from app.models.intelligence import DocumentActionItem
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember

router = APIRouter(prefix='/divorce', tags=['divorce'])

class DivorceWorkspaceCreate(BaseModel):
    case_title: str
    jurisdiction: str
    current_stage: str
    children_involved: bool
    financial_disclosure_started: bool
    lawyer_involved: bool

@router.post('/setup')
def create_divorce_workspace(payload: DivorceWorkspaceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ws = Workspace(name=payload.case_title.strip(), type='team', workspace_type='divorce_case', owner_user_id=current_user.id, matter_title=payload.case_title.strip(), jurisdiction=payload.jurisdiction, key_dates_json={'current_stage': payload.current_stage, 'children_involved': payload.children_involved, 'financial_disclosure_started': payload.financial_disclosure_started, 'lawyer_involved': payload.lawyer_involved})
    db.add(ws); db.flush(); db.add(WorkspaceMember(workspace_id=ws.id, user_id=current_user.id, role='owner')); db.commit(); db.refresh(ws)
    return ws

@router.get('/dashboard/{workspace_id}')
def divorce_dashboard(workspace_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member = db.query(WorkspaceMember).filter_by(workspace_id=workspace_id, user_id=current_user.id).first()
    if not member: raise HTTPException(status_code=403, detail='Forbidden')
    docs = db.query(func.count(Document.id)).filter(Document.workspace_id == workspace_id).scalar() or 0
    open_tasks = db.query(func.count(DocumentActionItem.id)).join(Document, Document.id == DocumentActionItem.document_id).filter(Document.workspace_id == workspace_id, DocumentActionItem.state == 'open').scalar() or 0
    upcoming = db.query(DivorceTimelineItem).filter(DivorceTimelineItem.workspace_id == workspace_id, DivorceTimelineItem.event_date >= date.today()).order_by(DivorceTimelineItem.event_date.asc()).limit(5).all()
    reports = db.query(DivorceReport).filter_by(workspace_id=workspace_id).order_by(DivorceReport.created_at.desc()).limit(5).all()
    return {'documents_uploaded': docs, 'emails_imported': 0, 'open_tasks': open_tasks, 'upcoming_deadlines': upcoming, 'key_timeline_events': upcoming, 'latest_reports': reports, 'missing_information_checklist': ['Confirm jurisdiction details', 'Upload latest financial disclosure']}
