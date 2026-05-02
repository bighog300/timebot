import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.models.user import User
from app.services.error_sanitizer import sanitize_processing_error
from app.services.limit_enforcement import enforce_limit
from app.services.storage import storage
from app.services.artifact_lookup import latest_artifact
from app.services.text_extractor import text_extractor
from app.services.thumbnail_generator import thumbnail_generator
from app.services.processing_events import processing_event_service
from app.services.usage import record_usage

logger = logging.getLogger(__name__)

_ALLOWED = set(settings.ALLOWED_FILE_TYPES.split(","))
_MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
_EMPTY_TEXT_ERROR_MESSAGE = (
    "No readable text could be extracted from this document. "
    "It may be scanned, image-only, encrypted, or unsupported."
)
_OCR_REQUIRED_MESSAGE = "OCR support is required for scanned PDFs."
_LEGACY_OFFICE_UNSUPPORTED_MESSAGE = "Legacy Office formats (.doc, .xls, .ppt) are unsupported. Please upload modern Office files (.docx, .xlsx, .pptx)."
_NON_PDF_EMPTY_TEXT_MESSAGE = "No readable text was extracted from this file type."
_IMAGE_EMPTY_TEXT_MESSAGE = "No readable text was extracted from this image."


class DocumentProcessor:
    async def process_upload(
        self, db: Session, file: UploadFile, user: User, source: str = "upload"
    ) -> Document:
        self._validate(file)

        file_path, file_size = await storage.save_upload(file)

        if file_size > _MAX_BYTES:
            storage.delete_file(str(file_path))
            raise ValueError(
                f"File too large ({file_size / 1024 / 1024:.1f} MB). Max: {settings.MAX_UPLOAD_SIZE_MB} MB"
            )

        enforce_limit(db, user.id, "storage_bytes", quantity=max(int(file_size), 0))

        file_type = Path(file.filename).suffix.lstrip(".").lower()
        mime_type = storage.get_mime_type(file_path)

        document = Document(
            filename=file.filename,
            original_path=str(file_path),
            file_type=file_type,
            file_size=file_size,
            mime_type=mime_type,
            source=source,
            user_id=user.id,
            processing_status="queued",
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        processing_event_service.update_progress(db, document, stage="queued", message="Upload accepted and queued for processing.")
        processing_event_service.record_processing_event(
            db,
            document=document,
            stage="queued",
            event_type="upload_accepted",
            status="success",
            message="Document upload accepted and queued.",
        )
        record_usage(
            db,
            user_id=user.id,
            metric="documents_per_month",
            metadata={"document_id": str(document.id), "filename": document.filename, "source": source},
        )
        record_usage(
            db,
            user_id=user.id,
            metric="storage_bytes",
            quantity=max(int(file_size), 0),
            metadata={"document_id": str(document.id), "filename": document.filename, "source": source},
        )

        # Queue background task; fall back to sync if Celery unavailable
        try:
            from app.workers.tasks import process_document_task

            task_result = process_document_task.apply_async(args=[str(document.id)], priority=5)
            logger.info("Upload queued document_id=%s user_id=%s task_id=%s queue=ingestion", document.id, user.id, task_result.id)
        except Exception as e:
            logger.warning("Celery unavailable (%s); processing synchronously", e)
            self._process_sync(db, document)

        return document

    def _validate(self, file: UploadFile):
        if not file.filename:
            raise ValueError("No filename provided")
        ext = Path(file.filename).suffix.lstrip(".").lower()
        if ext not in _ALLOWED:
            raise ValueError(f"Unsupported file type: .{ext}")

    def _process_sync(self, db: Session, document: Document):
        try:
            self.process_document(db, document)
        except Exception as e:
            logger.error("Sync processing failed: %s", e)
            document.processing_status = "failed"
            document.processing_error = sanitize_processing_error(str(e))
            db.add(document)
            db.commit()

    def process_document(self, db: Session, document: Document, run_relationship_detection: bool = True):
        total_start = time.perf_counter()
        document.processing_status = "processing"
        self._set_enrichment_status(document, "pending")
        db.add(document)
        db.commit()
        processing_event_service.update_progress(db, document, stage="extracting", message="Extracting readable text from the document.")
        if document.user_id is not None:
            record_usage(
                db,
                user_id=document.user_id,
                metric="document_processing_started",
                metadata={"document_id": str(document.id)},
            )

        try:
            file_path = Path(document.original_path)
            text = ""

            extraction_start = time.perf_counter()
            processing_event_service.record_processing_event(db, document=document, stage="extracting", event_type="extraction_started", status="started", message="Text extraction started.")
            if file_path.exists():
                extracted_text, page_count, word_count = text_extractor.extract(file_path, document.file_type)
                text = (extracted_text or "").strip()
                extraction_status = "success"
                extraction_error = None
                if extracted_text is None:
                    extraction_status = "failed"
                    if document.file_type in {"doc", "xls", "ppt"}:
                        extraction_error = _LEGACY_OFFICE_UNSUPPORTED_MESSAGE
                    else:
                        extraction_error = "Text extraction failed."
                elif not text:
                    extraction_status = "empty"
                    if document.file_type == "pdf":
                        extraction_error = _OCR_REQUIRED_MESSAGE
                    elif document.file_type in {"jpg", "jpeg", "png", "gif", "tiff", "bmp"}:
                        extraction_error = _IMAGE_EMPTY_TEXT_MESSAGE
                    else:
                        extraction_error = _NON_PDF_EMPTY_TEXT_MESSAGE

                self._record_extraction_metadata(
                    document,
                    text=text,
                    status=extraction_status,
                    error=extraction_error,
                )

                if extraction_status == "success":
                    document.raw_text = text
                    document.page_count = page_count
                    document.word_count = word_count
                    storage.save_text(str(document.id), text)
            else:
                text = (self._load_or_extract_text(document.id, file_path, document.file_type) or "").strip()
                if text:
                    self._record_extraction_metadata(
                        document,
                        text=text,
                        status="success",
                    )
                    document.raw_text = text
                    document.page_count = None
                    document.word_count = len(text.split())
                else:
                    self._record_extraction_metadata(
                        document,
                        text="",
                        status="failed",
                        error="Original uploaded file is missing from storage.",
                    )
                    raise ValueError("Cannot reprocess: original uploaded file is missing from storage")

            extraction_duration_ms = int((time.perf_counter() - extraction_start) * 1000)
            processing_event_service.record_processing_event(db, document=document, stage="extracting", event_type="extraction_finished", status="success", message="Text extraction completed.", duration_ms=extraction_duration_ms)
            logger.info(
                "Document extraction completed doc_id=%s extraction_duration_ms=%s",
                document.id,
                extraction_duration_ms,
            )

            if not text:
                raise ValueError(_EMPTY_TEXT_ERROR_MESSAGE)

            # Step 2: thumbnail
            thumb = thumbnail_generator.generate(file_path, document.file_type)
            if thumb:
                storage.save_thumbnail(str(document.id), thumb)

            # Step 3: AI analysis
            if settings.ENABLE_AUTO_CATEGORIZATION:
                processing_event_service.update_progress(db, document, stage="analyzing", message="Analyzing document with AI.")
                self._run_ai_analysis(db, document, text, run_relationship_detection=run_relationship_detection)

            document.processing_status = "completed"
            document.processed_date = datetime.now(timezone.utc)
            processing_event_service.update_progress(db, document, stage="completed", message="Document processing complete.")
            processing_event_service.record_processing_event(db, document=document, stage="completed", event_type="processing_finished", status="success", message="Document processing completed successfully.")
            if document.user_id is not None:
                record_usage(
                    db,
                    user_id=document.user_id,
                    metric="document_processing_completed",
                    metadata={"document_id": str(document.id)},
                )
            if document.user_id is not None:
                record_usage(db, user_id=document.user_id, metric="processing_jobs_per_month", quantity=1, metadata={"document_id": str(document.id)})
            if run_relationship_detection:
                if document.enrichment_status not in {"degraded", "pending"}:
                    self._set_enrichment_status(document, "complete")
            else:
                self._set_enrichment_status(document, "pending")

        except Exception as e:
            safe_error = sanitize_processing_error(str(e))
            logger.error(
                "document_processing_failed document_id=%s stage=%s event_type=%s error_type=%s error=%s",
                document.id,
                "failed",
                "processing_failed",
                type(e).__name__,
                safe_error,
            )
            document.processing_status = "failed"
            document.processing_error = safe_error
            processing_event_service.update_progress(db, document, stage="failed", message=document.processing_error or "Processing failed.", failed=True)
            processing_event_service.record_processing_event(db, document=document, stage="failed", event_type="processing_failed", status="failed", message=document.processing_error or "Processing failed.", severity="error", error_type=type(e).__name__)

        db.add(document)
        db.commit()
        db.refresh(document)
        total_processing_duration_ms = int((time.perf_counter() - total_start) * 1000)
        logger.info(
            "Document processing finished doc_id=%s total_processing_duration_ms=%s",
            document.id,
            total_processing_duration_ms,
        )

    def _run_ai_analysis(self, db: Session, document: Document, text: str, run_relationship_detection: bool = True):
        logger.info("AI analysis started doc_id=%s text_length=%s model=%s", document.id, len(text), settings.OPENAI_MODEL)
        from app.models.category import Category
        from app.services.ai_analyzer import AIAnalysisError, ai_analyzer
        from app.services.document_intelligence import document_intelligence_service
        from app.services.relationship_detection import relationship_detection_service

        categories = db.query(Category).all()
        ai_start = time.perf_counter()
        try:
            analysis = ai_analyzer.analyze_document(
                text=text,
                filename=document.filename,
                file_type=document.file_type,
                existing_categories=[c.name for c in categories],
                db=db,
            )
            confidence = ai_analyzer.compute_confidence(analysis)
            logger.info("AI analysis succeeded doc_id=%s summary_length=%s timeline_events=%s action_items=%s", document.id, len(analysis.get("summary") or ""), len(analysis.get("timeline_events") or []), len(analysis.get("action_items") or []))
            logger.info(
                "AI summary preview doc_id=%s preview=%s",
                document.id,
                (analysis.get("summary") or "")[:80],
            )
            document.review_status = (
                "pending"
                if confidence < settings.REVIEW_CONFIDENCE_THRESHOLD
                else "approved"
            )
            logger.info("Persisting intelligence doc_id=%s", document.id)
            self._persist_ai_analysis_markers(document, analysis)
            intelligence = document_intelligence_service.create_from_analysis(db, document, analysis)
            if hasattr(db, "refresh"):
                db.refresh(document)
                if intelligence is not None:
                    db.refresh(intelligence)
            logger.info(
                "Persistence complete doc_id=%s document_summary_length=%s intelligence_summary_length=%s",
                document.id,
                len(document.summary or ""),
                len((getattr(intelligence, "summary", "") or "")),
            )
            ai_analysis_duration_ms = int((time.perf_counter() - ai_start) * 1000)
            processing_event_service.record_processing_event(db, document=document, stage="analyzing", event_type="ai_finished", status="success", message="AI analysis completed.", duration_ms=ai_analysis_duration_ms, model=settings.OPENAI_MODEL)
            document_user_id = getattr(document, "user_id", None)
            if document_user_id is not None:
                record_usage(
                    db,
                    user_id=document_user_id,
                    metric="ai_call",
                    quantity=max(int(analysis.get("ai_call_count") or 1), 1),
                    metadata={
                        "document_id": str(document.id),
                        "provider": analysis.get("ai_provider"),
                        "model": analysis.get("ai_model") or settings.OPENAI_MODEL,
                    },
                )
            logger.info("AI analysis completed doc_id=%s ai_analysis_duration_ms=%s", document.id, ai_analysis_duration_ms)
            if document_user_id is not None:
                record_usage(db, user_id=document_user_id, metric="processing_jobs_per_month", quantity=1, metadata={"document_id": str(document.id)})
            if run_relationship_detection:
                processing_event_service.update_progress(db, document, stage="enriching", message="Enriching with relationship detection.")
                relationship_start = time.perf_counter()
                try:
                    logger.info("Starting relationship detection for document %s", document.id)
                    relationship_result = relationship_detection_service.detect_for_document(
                        db=db,
                        document_id=document.id,
                    )
                    relationship_detection_duration_ms = int((time.perf_counter() - relationship_start) * 1000)
                    logger.info(
                        "Relationship detection completed for document %s: scanned=%s created=%s updated=%s relationship_detection_duration_ms=%s",
                        document.id,
                        relationship_result.get("scanned", 0),
                        relationship_result.get("created", 0),
                        relationship_result.get("updated", 0),
                        relationship_detection_duration_ms,
                    )
                except Exception as exc:
                    logger.exception("Relationship detection failed for document %s", document.id)
                    self._append_processing_warning(
                        document,
                        f"Relationship generation failed: {exc}",
                    )
                    self._set_enrichment_status(document, "degraded")
        except AIAnalysisError as exc:
            self._append_processing_warning(document, str(exc))
            logger.warning("AI analysis failed doc_id=%s error=%s", document.id, exc)
            raise

    def _load_or_extract_text(self, document_id: UUID, file_path: Path, file_type: str) -> str:
        try:
            text, _page_count, _word_count = text_extractor.extract(file_path, file_type)
            if text:
                storage.save_text(str(document_id), text)
                return text
        except Exception:
            if file_path.exists():
                raise
        candidates = list(storage.text_path.rglob(f"{document_id}.txt"))
        latest = latest_artifact(candidates)
        if latest:
            return latest.read_text(encoding="utf-8")
        return ""

    def _append_processing_warning(self, document: Document, message: str) -> None:
        safe_message = sanitize_processing_error(message)
        if not safe_message:
            return
        metadata_value = getattr(document, "extracted_metadata", None)
        metadata = metadata_value if isinstance(metadata_value, dict) else {}
        updated = dict(metadata)
        warnings = updated.get("intelligence_warnings") if isinstance(updated.get("intelligence_warnings"), list) else []
        if safe_message not in warnings:
            warnings.append(safe_message)
        updated["intelligence_warnings"] = warnings
        setattr(document, "extracted_metadata", updated)
        if not document.processing_error:
            document.processing_error = safe_message
            return
        if safe_message in document.processing_error:
            return
        document.processing_error = f"{document.processing_error} | {safe_message}"

    def _record_extraction_metadata(self, document: Document, *, text: str, status: str, error: str | None = None) -> None:
        metadata_value = getattr(document, "extracted_metadata", None)
        metadata = metadata_value if isinstance(metadata_value, dict) else {}
        updated_metadata = dict(metadata)
        updated_metadata["extracted_text_length"] = len(text or "")
        updated_metadata["extraction_status"] = status
        safe_error = sanitize_processing_error(error) if error else None
        if safe_error:
            updated_metadata["extraction_error"] = safe_error
        else:
            updated_metadata.pop("extraction_error", None)
        document.extracted_metadata = updated_metadata

    def _set_enrichment_status(self, document: Document, status: str) -> None:
        metadata_value = getattr(document, "extracted_metadata", None)
        metadata = metadata_value if isinstance(metadata_value, dict) else {}
        updated = dict(metadata)
        updated["enrichment_status"] = status
        updated["enrichment_pending"] = status == "pending"
        setattr(document, "extracted_metadata", updated)

    def _persist_ai_analysis_markers(self, document: Document, analysis: dict) -> None:
        metadata_value = getattr(document, "extracted_metadata", None)
        metadata = metadata_value if isinstance(metadata_value, dict) else {}
        updated = dict(metadata)
        updated["json_parse_retry_used"] = bool(analysis.get("json_parse_retry_used"))
        updated["ai_analysis_degraded"] = bool(analysis.get("ai_analysis_degraded"))
        updated["ai_call_count"] = int(analysis.get("ai_call_count") or 0)
        updated["ai_provider"] = analysis.get("ai_provider")
        updated["ai_model"] = analysis.get("ai_model")
        updated["ai_analysis_duration_ms"] = analysis.get("ai_duration_ms")
        updated["prompt_source"] = analysis.get("prompt_source")
        if analysis.get("admin_prompt_invalid_fallback"):
            warnings = updated.get("intelligence_warnings") if isinstance(updated.get("intelligence_warnings"), list) else []
            msg = "Admin timeline_extraction prompt invalid; default AI prompt used."
            if msg not in warnings:
                warnings.append(msg)
            updated["intelligence_warnings"] = warnings
        setattr(document, "extracted_metadata", updated)


document_processor = DocumentProcessor()
