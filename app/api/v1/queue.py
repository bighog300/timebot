from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.queue import QueueItemResponse, QueueStatsResponse
from app.workers.monitoring import inspect_workers

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("/items", response_model=list[QueueItemResponse])
def list_queue_items(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.document import Document
    from app.models.relationships import ProcessingQueue

    return (
        db.query(ProcessingQueue)
        .join(Document, ProcessingQueue.document_id == Document.id)
        .filter(Document.user_id == current_user.id)
        .order_by(ProcessingQueue.priority.asc(), ProcessingQueue.created_at.asc())
        .limit(200)
        .all()
    )


@router.get("/stats", response_model=QueueStatsResponse)
def queue_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.document import Document

    status_counts = dict(
        db.query(Document.processing_status, func.count(Document.id))
        .filter(Document.user_id == current_user.id)
        .group_by(Document.processing_status)
        .all()
    )

    stats = QueueStatsResponse(
        queued=status_counts.get("queued", 0),
        processing=status_counts.get("processing", 0),
        completed=status_counts.get("completed", 0),
        failed=status_counts.get("failed", 0),
        total=sum(status_counts.values()),
        pending_review_count=(
            db.query(func.count(Document.id))
            .filter(Document.review_status == "pending", Document.user_id == current_user.id)
            .scalar()
            or 0
        ),
    )

    try:
        worker_stats = inspect_workers(timeout=2)
        stats.celery_active = worker_stats["active_tasks"]
        stats.celery_reserved = worker_stats["reserved_tasks"]
    except Exception:
        pass

    return stats


@router.get("/health")
def queue_health():
    try:
        worker_stats = inspect_workers(timeout=2)
        return {"status": "healthy", **worker_stats}
    except Exception as exc:
        return {"status": "degraded", "error": str(exc)}


@router.post("/retry-failed")
def retry_failed(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.document import Document
    from app.workers.tasks import process_document_task

    failed = db.query(Document).filter(Document.processing_status == "failed", Document.user_id == current_user.id).all()
    for doc in failed:
        doc.processing_status = "queued"
        doc.processing_error = None
        db.add(doc)
        process_document_task.apply_async(args=[str(doc.id)])

    db.commit()
    return {"message": f"Queued {len(failed)} documents for reprocessing"}
