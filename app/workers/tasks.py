import logging

from celery.exceptions import MaxRetriesExceededError

from app.config import settings
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.workers.tasks.process_document_task",
    max_retries=settings.CELERY_TASK_MAX_RETRIES,
    default_retry_delay=settings.CELERY_TASK_DEFAULT_RETRY_DELAY,
)
def process_document_task(self, document_id: str):
    from app.db.base import SessionLocal
    from app.models.document import Document
    from app.models.relationships import ProcessingQueue
    from app.services.document_processor import document_processor

    logger.info("Process task received task_id=%s document_id=%s worker=%s openai_configured=%s", self.request.id, document_id, self.request.hostname, bool(settings.OPENAI_API_KEY))
    db = SessionLocal()
    queue_entry = _ensure_queue_entry(db, document_id)

    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error("Document %s not found", document_id)
            _update_queue_entry(db, queue_entry, status="failed", error_message="Document not found")
            return {"status": "error", "message": "Document not found"}

        logger.info("Process task starting task_id=%s document_id=%s queue_entry_id=%s", self.request.id, document_id, queue_entry.id)
        _update_queue_entry(
            db,
            queue_entry,
            status="processing",
            attempts=queue_entry.attempts + 1,
            started_at=True,
            error_message=None,
        )
        _notify(document_id, "processing", progress=5)

        document_processor.process_document(db, document)

        if document.processing_status == "completed":
            logger.info("Process task completed task_id=%s document_id=%s summary_length=%s", self.request.id, document_id, len(document.summary or ""))
            _update_queue_entry(db, queue_entry, status="completed", completed_at=True)
            embed_document_task.delay(document_id)
            detect_relationships_task.delay(document_id)
            _notify(document_id, "completed", progress=100)
        else:
            _update_queue_entry(
                db,
                queue_entry,
                status="failed",
                completed_at=True,
                error_message=document.processing_error,
            )
            _notify(document_id, "failed", progress=100, error=document.processing_error)

        return {"status": "success", "document_id": document_id}

    except Exception as exc:
        logger.error("Task failed for document %s: %s", document_id, exc)
        try:
            _update_queue_entry(
                db,
                queue_entry,
                status="queued",
                error_message=str(exc),
            )
            _notify(document_id, "queued", error=str(exc))
            raise self.retry(
                exc=exc,
                countdown=settings.CELERY_TASK_DEFAULT_RETRY_DELAY * (self.request.retries + 1),
            )
        except MaxRetriesExceededError:
            _mark_failed(db, document_id, str(exc))
            _update_queue_entry(
                db,
                queue_entry,
                status="failed",
                completed_at=True,
                error_message=str(exc),
            )
            _notify(document_id, "failed", progress=100, error=str(exc))
            return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.reprocess_document_task")
def reprocess_document_task(document_id: str):
    logger.info("Reprocess worker task started document_id=%s", document_id)
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
        else:
            logger.error("Reprocess worker task missing document_id=%s", document_id)
    finally:
        db.close()

    result = process_document_task.apply_async(args=[document_id])
    logger.info("Reprocess delegated document_id=%s process_task_id=%s", document_id, result.id)
    return {"document_id": document_id, "process_task_id": result.id}




@celery_app.task(name="app.workers.tasks.detect_relationships_task")
def detect_relationships_task(document_id: str):
    from app.db.base import SessionLocal
    from app.services.relationship_detection import relationship_detection_service

    db = SessionLocal()
    try:
        return relationship_detection_service.detect_for_document(db=db, document_id=document_id)
    finally:
        db.close()


@celery_app.task(name="app.workers.tasks.backfill_relationships_task")
def backfill_relationships_task(limit: int | None = None):
    from app.db.base import SessionLocal
    from app.services.relationship_detection import relationship_detection_service

    db = SessionLocal()
    try:
        return relationship_detection_service.backfill_relationships(db=db, limit=limit)
    finally:
        db.close()

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


@celery_app.task(name="app.workers.tasks.embed_document_task")
def embed_document_task(document_id: str):
    from app.db.base import SessionLocal
    from app.models.document import Document
    from app.services.embedding_service import embedding_service

    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error("Document %s not found for embedding", document_id)
            return

        text_to_embed = f"{document.filename} {document.summary or ''} {document.raw_text or ''}"
        metadata = {
            "filename": document.filename,
            "category": document.ai_category.name if document.ai_category else None,
            "tags": (document.ai_tags or []) + (document.user_tags or []),
            "upload_date": document.upload_date.isoformat() if document.upload_date else None,
        }

        embedding_service.store_document_embedding(
            document_id=str(document.id),
            text=text_to_embed,
            metadata=metadata,
        )
    finally:
        db.close()


def _notify(document_id: str, status: str, progress: int | None = None, error: str | None = None):
    try:
        import asyncio

        from app.services.notification import manager

        from datetime import datetime, timezone

        payload = {
            "type": "processing_update",
            "event_version": "1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "document_id": document_id,
            "status": status,
        }
        if progress is not None:
            payload["progress"] = progress
        if error:
            payload["error"] = error

        asyncio.run(manager.send(document_id, payload))
        asyncio.run(manager.send("__all__", payload))
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


def _ensure_queue_entry(db, document_id: str):
    from app.models.relationships import ProcessingQueue

    queue_entry = (
        db.query(ProcessingQueue)
        .filter(
            ProcessingQueue.document_id == document_id,
            ProcessingQueue.task_type == "extract_text",
        )
        .first()
    )
    if queue_entry:
        return queue_entry

    queue_entry = ProcessingQueue(
        document_id=document_id,
        task_type="extract_text",
        status="queued",
        priority=5,
    )
    db.add(queue_entry)
    db.commit()
    db.refresh(queue_entry)
    return queue_entry


def _update_queue_entry(
    db,
    queue_entry,
    *,
    status: str,
    attempts: int | None = None,
    started_at: bool = False,
    completed_at: bool = False,
    error_message: str | None = None,
):
    from datetime import datetime, timezone

    queue_entry.status = status
    if attempts is not None:
        queue_entry.attempts = attempts
    if started_at:
        queue_entry.started_at = datetime.now(timezone.utc)
    if completed_at:
        queue_entry.completed_at = datetime.now(timezone.utc)
    queue_entry.error_message = error_message

    db.add(queue_entry)
    db.commit()
