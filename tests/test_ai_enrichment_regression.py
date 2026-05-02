import pytest
from uuid import uuid4

from app.models.document import Document
from app.services.ai_analyzer import AIAnalysisError
from app.services.document_processor import DocumentProcessor


def _build_document():
    return Document(
        id=uuid4(),
        filename="sample.pdf",
        original_path="/tmp/sample.pdf",
        file_type="pdf",
        file_size=1234,
        mime_type="application/pdf",
        source="upload",
        processing_status="processing",
    )


class _FakeCategoryQuery:
    def all(self):
        return []


class _FakeDB:
    def query(self, _model):
        return _FakeCategoryQuery()


def test_ai_analysis_persists_document_and_intelligence_summary(monkeypatch):
    processor = DocumentProcessor()
    document = _build_document()

    analysis = {
        "summary": "Concise summary from model.",
        "key_points": ["k1"],
        "entities": {"people": []},
        "action_items": [],
        "tags": ["tag-a"],
    }

    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.analyze_document", lambda **_kwargs: analysis)
    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.compute_confidence", lambda _analysis: 0.9)

    captured = {}

    def _create_from_analysis(_db, doc, payload):
        doc.summary = payload["summary"]
        captured["intelligence_summary"] = payload["summary"]

    monkeypatch.setattr(
        "app.services.document_intelligence.document_intelligence_service.create_from_analysis",
        _create_from_analysis,
    )
    monkeypatch.setattr(
        "app.services.relationship_detection.relationship_detection_service.detect_for_document",
        lambda **_kwargs: {"scanned": 0, "created": 0, "updated": 0},
    )

    processor._run_ai_analysis(_FakeDB(), document, "document text")

    assert document.summary == "Concise summary from model."
    assert captured["intelligence_summary"] == "Concise summary from model."


def test_ai_analysis_records_clear_error_when_key_missing(monkeypatch):
    processor = DocumentProcessor()
    document = _build_document()

    monkeypatch.setattr(
        "app.services.ai_analyzer.ai_analyzer.analyze_document",
        lambda **_kwargs: (_ for _ in ()).throw(
            AIAnalysisError("AI enrichment unavailable: OPENAI_API_KEY is not configured.")
        ),
    )

    with pytest.raises(AIAnalysisError):
        processor._run_ai_analysis(_FakeDB(), document, "document text")

    assert "OPENAI_API_KEY is not configured" in (document.processing_error or "")


def test_ai_analysis_records_invalid_json_failure(monkeypatch):
    processor = DocumentProcessor()
    document = _build_document()

    monkeypatch.setattr(
        "app.services.ai_analyzer.ai_analyzer.analyze_document",
        lambda **_kwargs: (_ for _ in ()).throw(AIAnalysisError("AI enrichment failed: invalid JSON response.")),
    )

    with pytest.raises(AIAnalysisError):
        processor._run_ai_analysis(_FakeDB(), document, "document text")

    assert "invalid JSON response" in (document.processing_error or "")


def test_ai_analysis_passes_db_to_analyzer(monkeypatch):
    processor = DocumentProcessor()
    document = _build_document()
    fake_db = _FakeDB()
    captured = {}

    def _analyze_document(**kwargs):
        captured["db"] = kwargs.get("db")
        return {"summary": "ok", "key_points": [], "entities": {}, "action_items": [], "tags": []}

    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.analyze_document", _analyze_document)
    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.compute_confidence", lambda _analysis: 0.9)
    monkeypatch.setattr(
        "app.services.document_intelligence.document_intelligence_service.create_from_analysis",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "app.services.relationship_detection.relationship_detection_service.detect_for_document",
        lambda **_kwargs: {"scanned": 0, "created": 0, "updated": 0},
    )

    processor._run_ai_analysis(fake_db, document, "document text")

    assert captured["db"] is fake_db


def test_process_document_fails_when_ai_analysis_errors(db, sample_document, tmp_path):
    processor = DocumentProcessor()
    src = tmp_path / "sample.txt"
    src.write_text("document text", encoding="utf-8")
    sample_document.original_path = str(src)
    sample_document.file_type = "txt"
    db.add(sample_document)
    db.commit()

    monkeypatch = __import__("pytest").MonkeyPatch()
    try:
        monkeypatch.setattr(
            "app.services.document_processor.text_extractor.extract",
            lambda *_args, **_kwargs: ("document text", 1, 2),
        )
        monkeypatch.setattr("app.services.document_processor.thumbnail_generator.generate", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(
            "app.services.ai_analyzer.ai_analyzer.analyze_document",
            lambda **_kwargs: (_ for _ in ()).throw(AIAnalysisError("AI enrichment failed: summary missing from model response.")),
        )
        processor.process_document(db, sample_document)
    finally:
        monkeypatch.undo()

    db.refresh(sample_document)
    assert sample_document.processing_status == "failed"
    assert sample_document.processing_error == "AI analysis did not return required summary field."


def test_ai_fallback_markers_are_persisted(monkeypatch):
    processor = DocumentProcessor()
    document = _build_document()

    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.analyze_document", lambda **_kwargs: {
        "summary": "fallback summary", "key_points": [], "entities": {}, "action_items": [], "tags": [],
        "json_parse_retry_used": True, "ai_analysis_degraded": True,
    })
    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.compute_confidence", lambda _analysis: 0.9)
    monkeypatch.setattr("app.services.document_intelligence.document_intelligence_service.create_from_analysis", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.services.relationship_detection.relationship_detection_service.detect_for_document", lambda **_kwargs: {"scanned": 0, "created": 0, "updated": 0})

    processor._run_ai_analysis(_FakeDB(), document, "document text")

    assert document.ai_analysis_degraded is True
    assert document.json_parse_retry_used is True


def test_ai_call_count_is_persisted(monkeypatch):
    processor = DocumentProcessor()
    document = _build_document()

    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.analyze_document", lambda **_kwargs: {
        "summary": "ok", "key_points": [], "entities": {}, "action_items": [], "tags": [],
        "ai_call_count": 2, "ai_provider": "openai", "ai_model": "gpt-test", "ai_duration_ms": 123.4,
    })
    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.compute_confidence", lambda _analysis: 0.9)
    monkeypatch.setattr("app.services.document_intelligence.document_intelligence_service.create_from_analysis", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("app.services.relationship_detection.relationship_detection_service.detect_for_document", lambda **_kwargs: {"scanned": 0, "created": 0, "updated": 0})

    processor._run_ai_analysis(_FakeDB(), document, "document text")
    assert document.extracted_metadata["ai_call_count"] == 2


def test_relationship_failure_persists_warning_without_raise(monkeypatch):
    processor = DocumentProcessor()
    document = _build_document()

    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.analyze_document", lambda **_kwargs: {"summary": "ok", "key_points": [], "entities": {}, "action_items": [], "tags": []})
    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.compute_confidence", lambda _analysis: 0.9)
    monkeypatch.setattr("app.services.document_intelligence.document_intelligence_service.create_from_analysis", lambda *_args, **_kwargs: None)

    def _boom(**_kwargs):
        raise RuntimeError("relationships down")

    monkeypatch.setattr("app.services.relationship_detection.relationship_detection_service.detect_for_document", _boom)

    processor._run_ai_analysis(_FakeDB(), document, "document text")

    assert document.enrichment_status == "degraded"
    assert any("Relationship generation failed" in warning for warning in document.intelligence_warnings)
