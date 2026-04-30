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

    processor._run_ai_analysis(_FakeDB(), document, "document text")

    assert "OPENAI_API_KEY is not configured" in (document.processing_error or "")


def test_ai_analysis_records_invalid_json_failure(monkeypatch):
    processor = DocumentProcessor()
    document = _build_document()

    monkeypatch.setattr(
        "app.services.ai_analyzer.ai_analyzer.analyze_document",
        lambda **_kwargs: (_ for _ in ()).throw(AIAnalysisError("AI enrichment failed: invalid JSON response.")),
    )

    processor._run_ai_analysis(_FakeDB(), document, "document text")

    assert "invalid JSON response" in (document.processing_error or "")
