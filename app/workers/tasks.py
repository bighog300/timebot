import logging

from celery.exceptions import MaxRetriesExceededError

from app.workers.celery_app import celery_app
from app.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.process_document_task",
    max_retries=settings.CELERY_TASK_MAX_RETRIES,
    default_retry_delay=60,
)
def process_document_task(self, document_id: str):
    from app.db.base import SessionLocal
    from app.models.document import Document
    from app.services.document_processor import document_processor

    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error("Document %s not found", document_id)
            return {"status": "error", "message": "Document not found"}

        document_processor.process_document(db, document)

        _notify(document_id, document.processing_status)
        return {"status": "success", "document_id": document_id}

    except Exception as exc:
        logger.error("Task failed for document %s: %s", document_id, exc)
        try:
            raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            _mark_failed(db, document_id, str(exc))
            return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.reprocess_document_task")
def reprocess_document_task(document_id: str):
    from app.db.base import SessionLocal
    from app.models.document import Document

    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.processing_status = "queued"
            doc.processing_error = None
            db.add(doc)
            db.commit()
    finally:
        db.close()

    return process_document_task.apply_async(args=[document_id])


@celery_app.task(name="app.workers.tasks.cleanup_old_tasks")
def cleanup_old_tasks():
    from datetime import datetime, timedelta, timezone

    from sqlalchemy import and_

    from app.db.base import SessionLocal
    from app.models.relationships import ProcessingQueue

    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        deleted = (
            db.query(ProcessingQueue)
            .filter(
                and_(
                    ProcessingQueue.status == "completed",
                    ProcessingQueue.completed_at < cutoff,
                )
            )
            .delete()
        )
        db.commit()
        return {"deleted": deleted}
    finally:
        db.close()


def _notify(document_id: str, status: str):
    try:
        import asyncio

        from app.services.notification import manager

        asyncio.run(
            manager.send(
                document_id,
                {"type": "processing_update", "document_id": document_id, "status": status},
            )
        )
    except Exception:
        pass  # Notifications are best-effort


def _mark_failed(db, document_id: str, error: str):
    from app.models.document import Document

    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc:
        doc.processing_status = "failed"
        doc.processing_error = error
        db.add(doc)
        db.commit()
