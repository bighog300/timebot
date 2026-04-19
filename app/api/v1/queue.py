from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.queue import QueueStatsResponse

router = APIRouter(prefix="/queue", tags=["queue"])


@router.get("/stats", response_model=QueueStatsResponse)
def queue_stats(db: Session = Depends(get_db)):
    from app.models.document import Document

    status_counts = dict(
        db.query(Document.processing_status, func.count(Document.id))
        .group_by(Document.processing_status)
        .all()
    )

    stats = QueueStatsResponse(
        queued=status_counts.get("queued", 0),
        processing=status_counts.get("processing", 0),
        completed=status_counts.get("completed", 0),
        failed=status_counts.get("failed", 0),
        total=sum(status_counts.values()),
    )

    # Celery inspect (best-effort, 2-second timeout)
    try:
        from app.workers.celery_app import celery_app

        inspect = celery_app.control.inspect(timeout=2)
        active = inspect.active() or {}
        reserved = inspect.reserved() or {}
        stats.celery_active = sum(len(v) for v in active.values())
        stats.celery_reserved = sum(len(v) for v in reserved.values())
    except Exception:
        pass

    return stats


@router.post("/retry-failed")
def retry_failed(db: Session = Depends(get_db)):
    from app.models.document import Document
    from app.workers.tasks import process_document_task

    failed = db.query(Document).filter(Document.processing_status == "failed").all()
    for doc in failed:
        doc.processing_status = "queued"
        doc.processing_error = None
        db.add(doc)
        process_document_task.apply_async(args=[str(doc.id)])

    db.commit()
    return {"message": f"Queued {len(failed)} documents for reprocessing"}
