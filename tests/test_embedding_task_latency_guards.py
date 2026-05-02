from uuid import uuid4

from app.models.document import Document
from app.workers import tasks


class _FakeDocQuery:
    def __init__(self, doc):
        self._doc = doc

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._doc


class _FakeDB:
    def __init__(self, doc):
        self._doc = doc

    def query(self, _model):
        return _FakeDocQuery(self._doc)

    def add(self, _obj):
        return None

    def commit(self):
        return None

    def close(self):
        return None


def _doc(summary: str = "summary", raw_text: str = "text", metadata: dict | None = None) -> Document:
    return Document(
        id=uuid4(),
        filename="sample.pdf",
        original_path="/tmp/sample.pdf",
        file_type="pdf",
        file_size=1,
        source="upload",
        summary=summary,
        raw_text=raw_text,
        extracted_metadata=metadata or {},
    )


def test_embed_task_skips_when_text_hash_unchanged(monkeypatch):
    document = _doc()
    text = f"{document.filename} {document.summary or ''} {document.raw_text or ''}"
    import hashlib
    document.extracted_metadata = {"embedding_text_hash": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    db = _FakeDB(document)

    monkeypatch.setattr("app.db.base.SessionLocal", lambda: db)
    called = {"count": 0}
    monkeypatch.setattr("app.services.embedding_service.embedding_service.store_document_embedding", lambda **_kwargs: called.__setitem__("count", called["count"] + 1))

    result = tasks.embed_document_task(str(document.id))
    assert result["status"] == "skipped"
    assert called["count"] == 0
    assert document.extracted_metadata["embedding_skipped"] is True


def test_embed_task_regenerates_when_text_changes(monkeypatch):
    document = _doc(summary="new summary", metadata={"embedding_text_hash": "old-hash"})
    db = _FakeDB(document)
    monkeypatch.setattr("app.db.base.SessionLocal", lambda: db)
    called = {"count": 0}
    monkeypatch.setattr("app.services.embedding_service.embedding_service.store_document_embedding", lambda **_kwargs: called.__setitem__("count", called["count"] + 1))

    tasks.embed_document_task(str(document.id))
    assert called["count"] == 1
    assert document.extracted_metadata["embedding_skipped"] is False
    assert "embedding_text_hash" in document.extracted_metadata


def test_embed_task_failure_marks_degraded_and_does_not_raise(monkeypatch):
    document = _doc(raw_text="sensitive text")
    db = _FakeDB(document)
    monkeypatch.setattr("app.db.base.SessionLocal", lambda: db)
    monkeypatch.setattr(
        "app.services.embedding_service.embedding_service.store_document_embedding",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    captured = {}

    def _capture(*_args, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr("app.workers.tasks._finalize_enrichment_if_ready", _capture)

    result = tasks.embed_document_task(str(document.id))
    assert result["status"] == "degraded"
    assert captured["task_status"] == "degraded"
    assert "RuntimeError" in captured["warning"]


def test_embed_task_failure_log_omits_raw_text(monkeypatch, caplog):
    raw_text = "SUPER_SECRET_DOCUMENT_TEXT"
    document = _doc(raw_text=raw_text)
    db = _FakeDB(document)
    monkeypatch.setattr("app.db.base.SessionLocal", lambda: db)
    monkeypatch.setattr(
        "app.services.embedding_service.embedding_service.store_document_embedding",
        lambda **_kwargs: (_ for _ in ()).throw(ValueError("bad embedding")),
    )

    tasks.embed_document_task(str(document.id))
    assert "embedding_generation_failed" in caplog.text
    assert "error_type=ValueError" in caplog.text
    assert raw_text not in caplog.text
