import uuid
from unittest.mock import patch

from app.models.document import Document
from app.models.relationships import ProcessingQueue
from app.services.document_processor import DocumentProcessor


def test_processing_failure_stores_safe_reason(db, sample_document):
    processor = DocumentProcessor()
    sample_document.processing_status = "processing"
    db.add(sample_document)
    db.commit()

    with patch.object(processor, "_load_or_extract_text", side_effect=RuntimeError("summary: top secret document text api_key=abc123")):
        processor.process_document(db, sample_document)

    db.refresh(sample_document)
    assert sample_document.processing_status == "failed"
    assert sample_document.processing_error == "Processing failed due to an internal error."


def test_status_api_exposes_safe_error_reason(client, db, test_user):
    doc = Document(
        id=uuid.uuid4(),
        filename="failed.pdf",
        original_path="/tmp/failed.pdf",
        file_type="pdf",
        file_size=123,
        mime_type="application/pdf",
        source="upload",
        user_id=test_user.id,
        processing_status="failed",
        processing_error="Processing failed due to an internal error.",
    )
    db.add(doc)
    db.commit()
    queue_item = ProcessingQueue(
        document_id=doc.id,
        task_type="extract_text",
        status="failed",
        error_message=doc.processing_error,
    )
    db.add(queue_item)
    db.commit()

    payload = client.get("/api/v1/queue/items").json()
    failed_item = next(item for item in payload if item["document_id"] == str(doc.id))
    assert failed_item["status"] == "failed"
    assert failed_item["error_message"] == "Processing failed due to an internal error."
    assert failed_item["completed_at"] is None or isinstance(failed_item["completed_at"], str)


def test_raw_document_content_not_in_failure_reason():
    processor = DocumentProcessor()
    doc = Document(id=uuid.uuid4(), filename="a.pdf", original_path="/tmp/a.pdf", file_type="pdf", file_size=1, source="upload")
    processor._append_processing_warning(doc, "Failed. snippet: customer ssn 123-45-6789 and summary of the document text.")
    assert doc.processing_error == "Processing failed due to an internal error."
    assert "customer ssn" not in (doc.processing_error or "").lower()


def test_successful_processing_behavior_unchanged(db, sample_document):
    processor = DocumentProcessor()

    with patch.object(processor, "_load_or_extract_text", return_value="Hello world"), patch(
        "app.services.document_processor.text_extractor.extract", return_value=("Hello world", 1, 2)
    ), patch("app.services.document_processor.thumbnail_generator.generate", return_value=None), patch(
        "app.services.document_processor.storage.save_text"
    ), patch(
        "app.services.document_processor.settings.ENABLE_AUTO_CATEGORIZATION", False
    ):
        processor.process_document(db, sample_document)

    db.refresh(sample_document)
    assert sample_document.processing_status == "completed"
    assert sample_document.processing_error is None


def test_empty_extracted_text_fails_without_ai_call(db, sample_document, tmp_path):
    processor = DocumentProcessor()
    src = tmp_path / "empty.pdf"
    src.write_bytes(b"%PDF-1.4 test")
    sample_document.original_path = str(src)
    db.add(sample_document)
    db.commit()

    with patch(
        "app.services.document_processor.text_extractor.extract", return_value=("", 1, 0)
    ), patch("app.services.document_processor.thumbnail_generator.generate", return_value=None), patch(
        "app.services.document_processor.storage.save_text"
    ) as save_text, patch.object(
        processor, "_run_ai_analysis"
    ) as run_ai:
        processor.process_document(db, sample_document)

    db.refresh(sample_document)
    assert sample_document.processing_status == "failed"
    assert (
        sample_document.processing_error
        == "No readable text could be extracted from this document. It may be scanned, image-only, encrypted, or unsupported."
    )
    assert sample_document.extracted_metadata["extraction_status"] == "empty"
    assert sample_document.extracted_metadata["extracted_text_length"] == 0
    assert sample_document.extracted_metadata["extraction_error"] == "OCR support is required for scanned PDFs."
    run_ai.assert_not_called()
    save_text.assert_not_called()


def test_extraction_failure_records_sanitized_metadata(db, sample_document, tmp_path):
    processor = DocumentProcessor()
    src = tmp_path / "sample.txt"
    src.write_text("placeholder", encoding="utf-8")
    sample_document.original_path = str(src)
    sample_document.file_type = "txt"
    db.add(sample_document)
    db.commit()

    with patch(
        "app.services.document_processor.text_extractor.extract",
        return_value=(None, None, None),
    ):
        processor.process_document(db, sample_document)

    db.refresh(sample_document)
    assert sample_document.processing_status == "failed"
    assert sample_document.extracted_metadata["extraction_status"] == "failed"
    assert sample_document.extracted_metadata["extracted_text_length"] == 0
    assert sample_document.extracted_metadata["extraction_error"] == "Text extraction failed."


def test_extraction_called_once_when_original_exists(db, sample_document, tmp_path):
    processor = DocumentProcessor()
    src = tmp_path / "once.txt"
    src.write_text("hello", encoding="utf-8")
    sample_document.original_path = str(src)
    sample_document.file_type = "txt"
    db.add(sample_document)
    db.commit()

    with patch("app.services.document_processor.text_extractor.extract", return_value=("Hello world", 1, 2)) as extract, patch(
        "app.services.document_processor.thumbnail_generator.generate", return_value=None
    ), patch("app.services.document_processor.storage.save_text"), patch(
        "app.services.document_processor.settings.ENABLE_AUTO_CATEGORIZATION", False
    ):
        processor.process_document(db, sample_document)

    db.refresh(sample_document)
    assert sample_document.processing_status == "completed"
    assert extract.call_count == 1


def test_whitespace_extracted_text_fails_without_ai_call(db, sample_document, tmp_path):
    processor = DocumentProcessor()
    src = tmp_path / "empty-space.pdf"
    src.write_bytes(b"%PDF-1.4 test")
    sample_document.original_path = str(src)
    db.add(sample_document)
    db.commit()

    with patch("app.services.document_processor.text_extractor.extract", return_value=("   \n\t  ", 1, 0)), patch(
        "app.services.document_processor.thumbnail_generator.generate", return_value=None
    ), patch("app.services.document_processor.storage.save_text") as save_text, patch.object(
        processor, "_run_ai_analysis"
    ) as run_ai:
        processor.process_document(db, sample_document)

    db.refresh(sample_document)
    assert sample_document.processing_status == "failed"
    assert sample_document.extracted_metadata["extraction_status"] == "empty"
    assert sample_document.extracted_metadata["extracted_text_length"] == 0
    run_ai.assert_not_called()
    save_text.assert_not_called()
