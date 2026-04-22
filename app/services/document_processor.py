import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document
from app.services.storage import storage
from app.services.text_extractor import text_extractor
from app.services.thumbnail_generator import thumbnail_generator

logger = logging.getLogger(__name__)

_ALLOWED = set(settings.ALLOWED_FILE_TYPES.split(","))
_MAX_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


class DocumentProcessor:
    async def process_upload(
        self, db: Session, file: UploadFile, source: str = "upload"
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
            processing_status="queued",
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # Queue background task; fall back to sync if Celery unavailable
        try:
            from app.workers.tasks import process_document_task

            process_document_task.apply_async(args=[str(document.id)], priority=5)
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
            document.processing_error = str(e)
            db.add(document)
            db.commit()

    def process_document(self, db: Session, document: Document):
        document.processing_status = "processing"
        db.add(document)
        db.commit()

        try:
            file_path = Path(document.original_path)

            # Step 1: extract text
            text, page_count, word_count = text_extractor.extract(file_path, document.file_type)
            if text:
                document.raw_text = text
                document.page_count = page_count
                document.word_count = word_count
                storage.save_text(str(document.id), text)

            # Step 2: thumbnail
            thumb = thumbnail_generator.generate(file_path, document.file_type)
            if thumb:
                storage.save_thumbnail(str(document.id), thumb)

            # Step 3: AI analysis
            if text and settings.ENABLE_AUTO_CATEGORIZATION:
                self._run_ai_analysis(db, document, text)

            document.processing_status = "completed"
            document.processed_date = datetime.now(timezone.utc)

        except Exception as e:
            logger.error("Document processing error for %s: %s", document.id, e)
            document.processing_status = "failed"
            document.processing_error = str(e)

        db.add(document)
        db.commit()
        db.refresh(document)

    def _run_ai_analysis(self, db: Session, document: Document, text: str):
        from app.models.category import Category
        from app.services.ai_analyzer import ai_analyzer
        from app.services.categorizer import categorizer

        categories = db.query(Category).all()
        analysis = ai_analyzer.analyze_document(
            text=text,
            filename=document.filename,
            file_type=document.file_type,
            existing_categories=[c.name for c in categories],
        )
        if analysis:
            confidence = ai_analyzer.compute_confidence(analysis)
            document.summary = analysis.get("summary")
            document.key_points = analysis.get("key_points", [])
            document.entities = analysis.get("entities", {})
            document.action_items = analysis.get("action_items", [])
            document.ai_tags = analysis.get("tags", [])
            document.ai_confidence = confidence
            document.review_status = (
                "pending"
                if confidence < settings.REVIEW_CONFIDENCE_THRESHOLD
                else "approved"
            )
            categorizer.apply_category(db, document, analysis)


document_processor = DocumentProcessor()
