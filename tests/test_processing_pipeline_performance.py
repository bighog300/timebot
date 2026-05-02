from unittest.mock import patch

from app.workers.tasks import process_document_task


def test_timing_logs_include_duration_fields(db, sample_document, caplog):
    from app.services.document_processor import DocumentProcessor

    caplog.set_level("INFO")
    processor = DocumentProcessor()
    with patch.object(processor, "_load_or_extract_text", return_value="Hello world"), patch(
        "app.services.document_processor.text_extractor.extract", return_value=("Hello world", 1, 2)
    ), patch("app.services.document_processor.thumbnail_generator.generate", return_value=None), patch(
        "app.services.document_processor.storage.save_text"
    ), patch(
        "app.services.document_processor.settings.ENABLE_AUTO_CATEGORIZATION", False
    ):
        processor.process_document(db, sample_document)

    joined = "\n".join(caplog.messages)
    assert "extraction_duration_ms=" in joined
    assert "total_processing_duration_ms=" in joined


def test_celery_flow_defers_inline_relationship_detection(db, sample_document, monkeypatch):
    sample_document.processing_status = "queued"

    calls = {"process_flags": [], "detect_calls": 0}

    def fake_process(db_session, document, run_relationship_detection=True):
        calls["process_flags"].append(run_relationship_detection)
        document.processing_status = "completed"

    monkeypatch.setattr("app.services.document_processor.document_processor.process_document", fake_process)
    monkeypatch.setattr("app.workers.tasks.embed_document_task.delay", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.workers.tasks.detect_relationships_task.delay", lambda *_args, **_kwargs: calls.__setitem__("detect_calls", calls["detect_calls"] + 1))

    class _FakeQuery:
        def __init__(self, document):
            self._document = document

        def filter(self, *_args, **_kwargs):
            return self

        def first(self):
            return self._document

    class _FakeSession:
        def query(self, model):
            if model.__name__ == "Document":
                return _FakeQuery(sample_document)
            return _FakeQuery(None)

        def close(self):
            return None

    monkeypatch.setattr("app.db.base.SessionLocal", lambda: _FakeSession())
    monkeypatch.setattr("app.workers.tasks._ensure_queue_entry", lambda *_args, **_kwargs: type("Q", (), {"id": "q1", "attempts": 0})())
    monkeypatch.setattr("app.workers.tasks._update_queue_entry", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.workers.tasks._notify", lambda *_args, **_kwargs: None)

    process_document_task(str(sample_document.id))

    assert calls["process_flags"] == [False]
    assert calls["detect_calls"] == 1
