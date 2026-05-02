import logging
import hashlib

from celery.exceptions import MaxRetriesExceededError

from app.config import settings
from app.services.error_sanitizer import sanitize_processing_error
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_REQUIRED_ENRICHMENT_TASKS = ("relationships", "embeddings")


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

        document_processor.process_document(db, document, run_relationship_detection=False)

        if document.processing_status == "completed":
            _set_document_enrichment_status(db, document_id, "pending")
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
                error_message=sanitize_processing_error(str(exc)),
            )
            _notify(document_id, "queued", error=sanitize_processing_error(str(exc)))
            raise self.retry(
                exc=exc,
                countdown=settings.CELERY_TASK_DEFAULT_RETRY_DELAY * (self.request.retries + 1),
            )
        except MaxRetriesExceededError:
            safe_error = sanitize_processing_error(str(exc))
            _mark_failed(db, document_id, safe_error)
            _update_queue_entry(
                db,
                queue_entry,
                status="failed",
                completed_at=True,
                error_message=safe_error,
            )
            _notify(document_id, "failed", progress=100, error=safe_error)
            return {"status": "failed", "error": safe_error}
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
        result = relationship_detection_service.detect_for_document(db=db, document_id=document_id)
        _finalize_enrichment_if_ready(db, document_id, task_name="relationships", task_status="complete")
        return result
    except Exception as exc:
        _finalize_enrichment_if_ready(
            db,
            document_id,
            task_name="relationships",
            task_status="degraded",
            warning=f"Relationship generation failed: {exc}",
        )
        raise
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
        text_hash = hashlib.sha256(text_to_embed.encode("utf-8")).hexdigest()
        metadata_blob = document.extracted_metadata if isinstance(document.extracted_metadata, dict) else {}
        if metadata_blob.get("embedding_text_hash") == text_hash:
            logger.info("Embedding skipped document_id=%s reason=text_hash_unchanged", document_id)
            updated_metadata = dict(metadata_blob)
            updated_metadata["embedding_skipped"] = True
            document.extracted_metadata = updated_metadata
            db.add(document)
            db.commit()
            _set_document_enrichment_status(
                db,
                document_id,
                "complete",
                task_name="embeddings",
            )
            return {"status": "skipped", "reason": "text_hash_unchanged"}
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
        updated_metadata = dict(metadata_blob)
        updated_metadata["embedding_text_hash"] = text_hash
        updated_metadata["embedding_skipped"] = False
        document.extracted_metadata = updated_metadata
        db.add(document)
        db.commit()
        _finalize_enrichment_if_ready(db, document_id, task_name="embeddings", task_status="complete")
    except Exception as exc:
        _finalize_enrichment_if_ready(
            db,
            document_id,
            task_name="embeddings",
            task_status="degraded",
            warning=f"Embedding generation failed: {exc}",
        )
        raise
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


def _set_document_enrichment_status(
    db,
    document_id: str,
    status: str,
    warning: str | None = None,
    task_name: str | None = None,
):
    from app.models.document import Document
    from app.services.error_sanitizer import sanitize_processing_error
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        return
    metadata = doc.extracted_metadata if isinstance(doc.extracted_metadata, dict) else {}
    updated = dict(metadata)
    task_state = updated.get("enrichment_tasks") if isinstance(updated.get("enrichment_tasks"), dict) else {}

    if status == "pending":
        for required in _REQUIRED_ENRICHMENT_TASKS:
            task_state[required] = "pending"
    elif task_name in _REQUIRED_ENRICHMENT_TASKS and status in {"complete", "degraded"}:
        task_state[task_name] = status

    if task_state:
        updated["enrichment_tasks"] = task_state

    statuses = [task_state.get(required) for required in _REQUIRED_ENRICHMENT_TASKS]
    has_pending = any(value == "pending" for value in statuses)
    has_degraded = any(value == "degraded" for value in statuses)
    all_complete = all(value == "complete" for value in statuses)

    derived_status = status
    if has_pending:
        derived_status = "pending"
    elif all_complete:
        derived_status = "complete"
    elif has_degraded:
        derived_status = "degraded"

    updated["enrichment_status"] = derived_status
    updated["enrichment_pending"] = derived_status == "pending"
    if warning:
        safe = sanitize_processing_error(warning)
        warnings = updated.get("intelligence_warnings") if isinstance(updated.get("intelligence_warnings"), list) else []
        if safe and safe not in warnings:
            warnings.append(safe)
            updated["intelligence_warnings"] = warnings
    doc.extracted_metadata = updated
    if hasattr(db, "add"):
        db.add(doc)
    if hasattr(db, "commit"):
        db.commit()



def _finalize_enrichment_if_ready(
    db,
    document_id: str,
    *,
    task_name: str,
    task_status: str,
    warning: str | None = None,
):
    _set_document_enrichment_status(db, document_id, task_status, warning=warning, task_name=task_name)
