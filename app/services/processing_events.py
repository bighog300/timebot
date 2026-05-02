import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.processing_event import DocumentProcessingEvent
from app.services.error_sanitizer import sanitize_processing_error


_STAGE_PROGRESS = {
    "uploading": 0,
    "queued": 5,
    "extracting": 15,
    "analyzing": 45,
    "enriching": 70,
    "embedding": 85,
    "completed": 100,
}


class ProcessingEventService:
    def sanitize_event_metadata(self, metadata: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(metadata, dict):
            return {}
        blocked_keys = {"text", "raw_text", "prompt", "response", "content", "api_key", "authorization", "payload"}
        safe: dict[str, Any] = {}
        for key, value in metadata.items():
            key_l = str(key).lower()
            if any(token in key_l for token in blocked_keys):
                continue
            if isinstance(value, (str, int, float, bool)) or value is None:
                safe[key] = value
        return safe

    def update_progress(self, db: Session, document: Document, *, stage: str, message: str, failed: bool = False):
        metadata = dict(document.extracted_metadata or {})
        now_iso = datetime.now(timezone.utc).isoformat()
        previous_stage = metadata.get("processing_stage")
        if previous_stage != stage:
            metadata["stage_started_at"] = now_iso
        metadata["processing_stage"] = stage
        if stage != "failed":
            metadata["processing_progress"] = _STAGE_PROGRESS.get(stage, metadata.get("processing_progress", 0))
        metadata["processing_message"] = sanitize_processing_error(message)
        metadata["stage_updated_at"] = now_iso
        document.extracted_metadata = metadata
        if failed:
            document.processing_status = "failed"
        if hasattr(db, "add"):
            db.add(document)
        if hasattr(db, "commit"):
            db.commit()

    def record_processing_event(self, db: Session, *, document: Document, stage: str, event_type: str, status: str, message: str, severity: str = "info", duration_ms: int | None = None, provider: str | None = None, model: str | None = None, ai_call_count: int | None = None, parse_retry_used: bool | None = None, error_type: str | None = None, safe_metadata: dict[str, Any] | None = None):
        event = DocumentProcessingEvent(
            document_id=document.id,
            user_id=getattr(document, "user_id", None),
            stage=stage,
            event_type=event_type,
            status=status,
            message=sanitize_processing_error(message),
            severity=severity,
            duration_ms=duration_ms,
            provider=provider,
            model=model,
            ai_call_count=ai_call_count,
            parse_retry_used=str(parse_retry_used).lower() if parse_retry_used is not None else None,
            error_type=error_type,
            safe_metadata=self.sanitize_event_metadata(safe_metadata),
        )
        if hasattr(db, "add"):
            db.add(event)
        if hasattr(db, "commit"):
            db.commit()

processing_event_service = ProcessingEventService()
