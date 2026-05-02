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
from app.services.storage import storage
from app.services.text_extractor import text_extractor
from app.services.thumbnail_generator import thumbnail_generator

logger = logging.getLogger(__name__)

_ALLOWED = set(settings.ALLOWED_FILE_TYPES.split(","))
_MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
_EMPTY_TEXT_ERROR_MESSAGE = (
    "No readable text could be extracted from this document. "
    "It may be scanned, image-only, encrypted, or unsupported."
)
_OCR_REQUIRED_MESSAGE = "OCR support is required for scanned PDFs."


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
        db.add(document)
        db.commit()

        try:
            file_path = Path(document.original_path)
            text = ""

            extraction_start = time.perf_counter()
            if file_path.exists():
                extracted_text, page_count, word_count = text_extractor.extract(file_path, document.file_type)
                text = (extracted_text or "").strip()
                extraction_status = "success"
                extraction_error = None
                if extracted_text is None:
                    extraction_status = "failed"
                    extraction_error = "Text extraction failed."
                elif not text:
                    extraction_status = "empty"
                    if document.file_type == "pdf":
                        extraction_error = _OCR_REQUIRED_MESSAGE

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
                self._run_ai_analysis(db, document, text, run_relationship_detection=run_relationship_detection)

            document.processing_status = "completed"
            document.processed_date = datetime.now(timezone.utc)

        except Exception as e:
            logger.error("Document processing error for %s: %s", document.id, e)
            document.processing_status = "failed"
            document.processing_error = sanitize_processing_error(str(e))

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
            logger.info("AI analysis completed doc_id=%s ai_analysis_duration_ms=%s", document.id, ai_analysis_duration_ms)
            if run_relationship_detection:
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
        text_file = next(storage.text_path.rglob(f"{document_id}.txt"), None)
        if text_file and text_file.exists():
            return text_file.read_text(encoding="utf-8")
        return ""

    def _append_processing_warning(self, document: Document, message: str) -> None:
        safe_message = sanitize_processing_error(message)
        if not safe_message:
            return
        if not document.processing_error:
            document.processing_error = safe_message
            return
        if safe_message in document.processing_error:
            return
        document.processing_error = f"{document.processing_error} | {safe_message}"

    def _record_extraction_metadata(self, document: Document, *, text: str, status: str, error: str | None = None) -> None:
        metadata = document.extracted_metadata if isinstance(document.extracted_metadata, dict) else {}
        updated_metadata = dict(metadata)
        updated_metadata["extracted_text_length"] = len(text or "")
        updated_metadata["extraction_status"] = status
        safe_error = sanitize_processing_error(error) if error else None
        if safe_error:
            updated_metadata["extraction_error"] = safe_error
        else:
            updated_metadata.pop("extraction_error", None)
        document.extracted_metadata = updated_metadata


document_processor = DocumentProcessor()
