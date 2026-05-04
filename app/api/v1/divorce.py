from datetime import date
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
from app.services.divorce_task_extraction import extract_tasks_for_workspace

router = APIRouter(prefix='/divorce', tags=['divorce'])

class DivorceWorkspaceCreate(BaseModel):
    case_title: str
    jurisdiction: str
    current_stage: str
    children_involved: bool
    financial_disclosure_started: bool
    lawyer_involved: bool

class DivorceTaskUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    due_date: date | None = None


def _verify_access(db: Session, workspace_id: str, user_id):
    member = db.query(WorkspaceMember).filter_by(workspace_id=workspace_id, user_id=user_id).first()
    if not member:
        raise HTTPException(status_code=403, detail='Forbidden')

@router.post('/setup')
def create_divorce_workspace(payload: DivorceWorkspaceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ws = Workspace(name=payload.case_title.strip(), type='team', workspace_type='divorce_case', owner_user_id=current_user.id, matter_title=payload.case_title.strip(), jurisdiction=payload.jurisdiction, key_dates_json={'current_stage': payload.current_stage, 'children_involved': payload.children_involved, 'financial_disclosure_started': payload.financial_disclosure_started, 'lawyer_involved': payload.lawyer_involved})
    db.add(ws); db.flush(); db.add(WorkspaceMember(workspace_id=ws.id, user_id=current_user.id, role='owner')); db.commit(); db.refresh(ws)
    return ws

@router.get('/tasks/{workspace_id}')
def list_divorce_tasks(workspace_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _verify_access(db, workspace_id, current_user.id)
    return db.query(DocumentActionItem).filter(DocumentActionItem.workspace_id == workspace_id).order_by(DocumentActionItem.created_at.desc()).all()

@router.post('/tasks/{task_id}/accept')
def accept_divorce_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(DocumentActionItem).filter(DocumentActionItem.id == task_id).first()
    if not task: raise HTTPException(404, 'Task not found')
    _verify_access(db, str(task.workspace_id), current_user.id)
    task.status = 'open'; task.state = 'open'; db.commit(); db.refresh(task); return task

@router.post('/tasks/{task_id}/reject')
def reject_divorce_task(task_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(DocumentActionItem).filter(DocumentActionItem.id == task_id).first()
    if not task: raise HTTPException(404, 'Task not found')
    _verify_access(db, str(task.workspace_id), current_user.id)
    task.status = 'rejected'; task.state = 'rejected'; db.commit(); db.refresh(task); return task

@router.patch('/tasks/{task_id}')
def patch_divorce_task(task_id: str, payload: DivorceTaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(DocumentActionItem).filter(DocumentActionItem.id == task_id).first()
    if not task: raise HTTPException(404, 'Task not found')
    _verify_access(db, str(task.workspace_id), current_user.id)
    if payload.status is not None: task.status = payload.status; task.state = payload.status
    if payload.priority is not None: task.priority = payload.priority
    if payload.due_date is not None: task.due_date = payload.due_date
    db.commit(); db.refresh(task); return task

@router.post('/tasks/extract/{workspace_id}')
def extract_divorce_tasks(workspace_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _verify_access(db, workspace_id, current_user.id)
    created = extract_tasks_for_workspace(db, workspace_id)
    return {'created_count': created}

@router.get('/dashboard/{workspace_id}')
def divorce_dashboard(workspace_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _verify_access(db, workspace_id, current_user.id)
    docs = db.query(func.count(Document.id)).filter(Document.workspace_id == workspace_id).scalar() or 0
    suggested = db.query(func.count(DocumentActionItem.id)).filter(DocumentActionItem.workspace_id == workspace_id, DocumentActionItem.status == 'suggested').scalar() or 0
    open_tasks = db.query(func.count(DocumentActionItem.id)).filter(DocumentActionItem.workspace_id == workspace_id, DocumentActionItem.status.in_(['open','in_progress'])).scalar() or 0
    urgent = db.query(func.count(DocumentActionItem.id)).filter(DocumentActionItem.workspace_id == workspace_id, DocumentActionItem.priority == 'urgent', DocumentActionItem.status.in_(['suggested','open','in_progress'])).scalar() or 0
    upcoming_tasks = db.query(DocumentActionItem).filter(DocumentActionItem.workspace_id == workspace_id, DocumentActionItem.due_date.isnot(None), DocumentActionItem.status.in_(['suggested','open','in_progress'])).order_by(DocumentActionItem.due_date.asc()).limit(5).all()
    recent = db.query(DocumentActionItem).filter(DocumentActionItem.workspace_id == workspace_id).order_by(DocumentActionItem.created_at.desc()).limit(5).all()
    upcoming = db.query(DivorceTimelineItem).filter(DivorceTimelineItem.workspace_id == workspace_id, DivorceTimelineItem.event_date >= date.today()).order_by(DivorceTimelineItem.event_date.asc()).limit(5).all()
    reports = db.query(DivorceReport).filter_by(workspace_id=workspace_id).order_by(DivorceReport.created_at.desc()).limit(5).all()
    return {'documents_uploaded': docs, 'emails_imported': 0, 'suggested_task_count': suggested, 'open_task_count': open_tasks, 'urgent_task_count': urgent, 'upcoming_due_dates': upcoming_tasks, 'recently_generated_tasks': recent, 'open_tasks': open_tasks, 'upcoming_deadlines': upcoming, 'key_timeline_events': upcoming, 'latest_reports': reports, 'missing_information_checklist': ['Confirm jurisdiction details', 'Upload latest financial disclosure']}
