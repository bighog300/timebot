from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user
from app.api.v1.queue import queue_stats
from app.schemas.document import DocumentResponse
from app.services.document_processor import DocumentProcessor


def _doc(**kwargs):
    defaults = {
        "id": uuid4(),
        "filename": "review-me.pdf",
        "file_type": "pdf",
        "file_size": 123,
        "source": "upload",
        "upload_date": datetime.now(timezone.utc),
        "processing_status": "completed",
        "processing_error": None,
        "summary": "AI summary",
        "key_points": ["point"],
        "entities": {"orgs": ["Acme"]},
        "action_items": ["follow up"],
        "ai_tags": ["tag1"],
        "user_tags": [],
        "ai_confidence": 0.42,
        "review_status": "pending",
        "reviewed_at": None,
        "reviewed_by": None,
        "override_summary": None,
        "override_tags": None,
        "is_favorite": False,
        "is_archived": False,
        "user_notes": None,
        "page_count": None,
        "word_count": None,
        "ai_category": None,
        "user_category": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_get_review_queue_returns_pending_only(monkeypatch):
    docs = [_doc(review_status="pending", ai_confidence=0.2)]

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), email="reviewer@example.com")
    monkeypatch.setattr("app.api.v1.documents.crud_document.get_review_queue", lambda db, user, status, skip, limit: docs)

    with TestClient(app) as client:
        response = client.get("/api/v1/documents/review-queue")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["review_status"] == "pending"
    app.dependency_overrides.clear()


def test_document_response_schema_includes_review_fields():
    fields = DocumentResponse.model_fields.keys()
    assert "review_status" in fields
    assert "reviewed_at" in fields
    assert "reviewed_by" in fields
    assert "override_summary" in fields
    assert "override_tags" in fields


def test_review_endpoint_approve_sets_review_fields(monkeypatch):
    doc = _doc()

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), email="editor@example.com")
    monkeypatch.setattr("app.api.v1.documents.crud_document.get_document", lambda db, id, user: doc)

    def _update(db, db_obj, **kwargs):
        for key, value in kwargs.items():
            setattr(db_obj, key, value)
        return db_obj

    monkeypatch.setattr("app.api.v1.documents.crud_document.update_document_fields", _update)

    with TestClient(app) as client:
        response = client.post(f"/api/v1/documents/{doc.id}/review", json={"action": "approve"})

    assert response.status_code == 200
    data = response.json()
    assert data["review_status"] == "approved"
    assert data["reviewed_by"] == "editor@example.com"
    app.dependency_overrides.clear()
    assert data["reviewed_at"] is not None


def test_review_endpoint_edit_stores_overrides(monkeypatch):
    doc = _doc()

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), email="reviewer@example.com")
    monkeypatch.setattr("app.api.v1.documents.crud_document.get_document", lambda db, id, user: doc)

    def _update(db, db_obj, **kwargs):
        for key, value in kwargs.items():
            setattr(db_obj, key, value)
        return db_obj

    monkeypatch.setattr("app.api.v1.documents.crud_document.update_document_fields", _update)

    body = {
        "action": "edit",
        "override_summary": "Human corrected summary",
        "override_tags": ["corrected", "important"],
    }
    with TestClient(app) as client:
        response = client.post(f"/api/v1/documents/{doc.id}/review", json=body)

    assert response.status_code == 200
    data = response.json()
    assert data["review_status"] == "edited"
    assert data["override_summary"] == "Human corrected summary"
    assert data["override_tags"] == ["corrected", "important"]
    assert data["reviewed_by"] == "reviewer@example.com"
    app.dependency_overrides.clear()


def test_low_confidence_documents_enter_pending_review(monkeypatch):
    processor = DocumentProcessor()
    document = _doc(ai_confidence=None, review_status=None)

    monkeypatch.setattr(
        "app.services.ai_analyzer.ai_analyzer.analyze_document",
        lambda **kwargs: {
            "summary": "short summary",
            "key_points": [],
            "entities": {},
            "action_items": [],
            "tags": [],
        },
    )
    monkeypatch.setattr("app.services.categorizer.categorizer.apply_category", lambda db, document, analysis: None)

    class FakeCategoryQuery:
        def all(self):
            return []

    class FakeDB:
        def query(self, _model):
            return FakeCategoryQuery()

    processor._run_ai_analysis(FakeDB(), document, "source text")

    assert document.ai_confidence is not None
    assert document.ai_confidence < 0.75
    assert document.review_status == "pending"


def test_queue_stats_includes_pending_review_count():
    class FakeGroupedQuery:
        def filter(self, *_args, **_kwargs):
            return self

        def group_by(self, *_args, **_kwargs):
            return self

        def all(self):
            return [("queued", 2), ("processing", 1)]

    class FakeScalarQuery:
        def filter(self, *_args, **_kwargs):
            return self

        def scalar(self):
            return 4

    class FakeDB:
        def __init__(self):
            self.calls = 0

        def query(self, *_args, **_kwargs):
            self.calls += 1
            return FakeGroupedQuery() if self.calls == 1 else FakeScalarQuery()

    stats = queue_stats(FakeDB(), SimpleNamespace(id=uuid4()))
    assert stats.pending_review_count == 4
    assert stats.queued == 2
