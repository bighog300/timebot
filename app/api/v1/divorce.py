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
from app.services.divorce_report_generation import PRO_REPORT_TYPES, generate_divorce_report
from app.services.divorce_timeline_extraction import extract_timeline_for_workspace
from app.services.subscriptions import ensure_default_free_subscription, get_user_plan

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


class DivorceTimelineUpdate(BaseModel):
    event_date: date | None = None
    date_precision: str | None = None
    title: str | None = None
    description: str | None = None
    category: str | None = None
    include_in_report: bool | None = None


class DivorceTimelineCreate(DivorceTimelineUpdate):
    title: str
    category: str = 'other'


class DivorceReportGeneratePayload(BaseModel):
    report_type: str
    title: str | None = None
    date_range: dict | None = None
    include_task_ids: list[str] | None = None
    include_timeline_item_ids: list[str] | None = None
    include_document_ids: list[str] | None = None


class DivorceReportPatchPayload(BaseModel):
    title: str | None = None
    status: str | None = None


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
    timeline_suggested = db.query(func.count(DivorceTimelineItem.id)).filter(DivorceTimelineItem.workspace_id == workspace_id, DivorceTimelineItem.review_status == 'suggested').scalar() or 0
    timeline_accepted = db.query(func.count(DivorceTimelineItem.id)).filter(DivorceTimelineItem.workspace_id == workspace_id, DivorceTimelineItem.review_status.in_(['accepted','edited'])).scalar() or 0
    timeline_high = db.query(func.count(DivorceTimelineItem.id)).filter(DivorceTimelineItem.workspace_id == workspace_id, DivorceTimelineItem.confidence >= 0.8).scalar() or 0
    recent_timeline = db.query(DivorceTimelineItem).filter(DivorceTimelineItem.workspace_id == workspace_id).order_by(DivorceTimelineItem.created_at.desc()).limit(5).all()
    failed_reports = db.query(func.count(DivorceReport.id)).filter(DivorceReport.workspace_id == workspace_id, DivorceReport.status == 'failed').scalar() or 0
    report_count = db.query(func.count(DivorceReport.id)).filter(DivorceReport.workspace_id == workspace_id).scalar() or 0
    return {'documents_uploaded': docs, 'emails_imported': 0, 'suggested_task_count': suggested, 'open_task_count': open_tasks, 'urgent_task_count': urgent, 'upcoming_due_dates': upcoming_tasks, 'recently_generated_tasks': recent, 'open_tasks': open_tasks, 'upcoming_deadlines': upcoming, 'key_timeline_events': upcoming, 'latest_reports': reports, 'report_count': report_count, 'failed_report_count': failed_reports, 'missing_information_checklist': ['Confirm jurisdiction details', 'Upload latest financial disclosure'], 'suggested_timeline_count': timeline_suggested, 'accepted_timeline_count': timeline_accepted, 'upcoming_timeline_events': upcoming, 'recent_timeline_events': recent_timeline, 'high_confidence_event_count': timeline_high}


@router.get('/reports/{workspace_id}')
def list_divorce_reports(workspace_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _verify_access(db, workspace_id, current_user.id)
    return db.query(DivorceReport).filter(DivorceReport.workspace_id == workspace_id).order_by(DivorceReport.created_at.desc()).all()


@router.post('/reports/{workspace_id}/generate')
def generate_report(workspace_id: str, payload: DivorceReportGeneratePayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _verify_access(db, workspace_id, current_user.id)
    ensure_default_free_subscription(db, current_user.id)
    plan = get_user_plan(db, current_user.id)
    if payload.report_type in PRO_REPORT_TYPES and (not plan or plan.slug == 'free'):
        raise HTTPException(status_code=402, detail='upgrade_required')
    return generate_divorce_report(db, workspace_id=workspace_id, user_id=current_user.id, report_type=payload.report_type, title=payload.title, include_task_ids=payload.include_task_ids, include_timeline_item_ids=payload.include_timeline_item_ids, include_document_ids=payload.include_document_ids, date_range=payload.date_range)


@router.get('/reports/detail/{report_id}')
def report_detail(report_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(DivorceReport).filter(DivorceReport.id == report_id).first()
    if not report: raise HTTPException(404, 'Report not found')
    _verify_access(db, str(report.workspace_id), current_user.id)
    return report


@router.patch('/reports/{report_id}')
def patch_report(report_id: str, payload: DivorceReportPatchPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(DivorceReport).filter(DivorceReport.id == report_id).first()
    if not report: raise HTTPException(404, 'Report not found')
    _verify_access(db, str(report.workspace_id), current_user.id)
    if payload.title is not None: report.title = payload.title
    if payload.status is not None: report.status = payload.status
    db.commit(); db.refresh(report); return report


@router.delete('/reports/{report_id}')
def delete_report(report_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    report = db.query(DivorceReport).filter(DivorceReport.id == report_id).first()
    if not report: raise HTTPException(404, 'Report not found')
    _verify_access(db, str(report.workspace_id), current_user.id)
    db.delete(report); db.commit(); return {'deleted': True}


@router.get('/timeline/{workspace_id}')
def list_divorce_timeline(workspace_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _verify_access(db, workspace_id, current_user.id)
    return db.query(DivorceTimelineItem).filter(DivorceTimelineItem.workspace_id == workspace_id).order_by(DivorceTimelineItem.event_date.asc().nulls_last(), DivorceTimelineItem.created_at.asc()).all()

@router.post('/timeline/extract/{workspace_id}')
def extract_divorce_timeline(workspace_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _verify_access(db, workspace_id, current_user.id)
    created = extract_timeline_for_workspace(db, workspace_id)
    return {'created_count': created}

@router.post('/timeline/{event_id}/accept')
def accept_divorce_timeline(event_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(DivorceTimelineItem).filter(DivorceTimelineItem.id == event_id).first()
    if not event: raise HTTPException(404, 'Event not found')
    _verify_access(db, str(event.workspace_id), current_user.id)
    event.review_status = 'accepted'; db.commit(); db.refresh(event); return event

@router.post('/timeline/{event_id}/reject')
def reject_divorce_timeline(event_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(DivorceTimelineItem).filter(DivorceTimelineItem.id == event_id).first()
    if not event: raise HTTPException(404, 'Event not found')
    _verify_access(db, str(event.workspace_id), current_user.id)
    event.review_status = 'rejected'; db.commit(); db.refresh(event); return event

@router.patch('/timeline/{event_id}')
def patch_divorce_timeline(event_id: str, payload: DivorceTimelineUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(DivorceTimelineItem).filter(DivorceTimelineItem.id == event_id).first()
    if not event: raise HTTPException(404, 'Event not found')
    _verify_access(db, str(event.workspace_id), current_user.id)
    if payload.event_date is not None: event.event_date = payload.event_date
    if payload.date_precision is not None: event.date_precision = payload.date_precision
    if payload.title is not None: event.title = payload.title
    if payload.description is not None: event.description = payload.description
    if payload.category is not None: event.category = payload.category
    if payload.include_in_report is not None: event.include_in_report = payload.include_in_report
    event.review_status = 'edited'
    db.commit(); db.refresh(event); return event

@router.delete('/timeline/{event_id}')
def delete_divorce_timeline(event_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event = db.query(DivorceTimelineItem).filter(DivorceTimelineItem.id == event_id).first()
    if not event: raise HTTPException(404, 'Event not found')
    _verify_access(db, str(event.workspace_id), current_user.id)
    db.delete(event); db.commit(); return {'deleted': True}

@router.post('/timeline/{workspace_id}/manual')
def create_divorce_timeline_manual(workspace_id: str, payload: DivorceTimelineCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _verify_access(db, workspace_id, current_user.id)
    item = DivorceTimelineItem(workspace_id=workspace_id, event_date=payload.event_date, date_precision=payload.date_precision or ('exact' if payload.event_date else 'unknown'), title=payload.title, description=payload.description, category=payload.category, include_in_report=True, review_status='edited', confidence=1.0, metadata_json={'source': 'manual'})
    db.add(item); db.commit(); db.refresh(item); return item
