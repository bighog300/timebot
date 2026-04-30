from pathlib import Path

from app.models.intelligence import DocumentIntelligence
from app.services.document_processor import document_processor


def test_reprocess_endpoint_queues_task(client, sample_document, monkeypatch):
    captured = {}

    class _TaskResult:
        id = "task-123"

    def _apply_async(*, args):
        captured["args"] = args
        return _TaskResult()

    monkeypatch.setattr("app.workers.tasks.reprocess_document_task.apply_async", _apply_async)

    resp = client.post(f"/api/v1/documents/{sample_document.id}/reprocess")
    assert resp.status_code == 200
    assert resp.json()["task_id"] == "task-123"
    assert captured["args"] == [str(sample_document.id)]


def test_process_document_uses_saved_text_when_original_missing(db, sample_document, monkeypatch, tmp_path):
    sample_document.original_path = str(tmp_path / "missing.pdf")
    sample_document.file_type = "pdf"
    sample_document.raw_text = None
    db.add(sample_document)
    db.commit()

    text_dir = tmp_path / "artifacts" / "extracted_text" / "2026" / "01" / "01"
    text_dir.mkdir(parents=True)
    (text_dir / f"{sample_document.id}.txt").write_text("Saved extracted text", encoding="utf-8")

    monkeypatch.setattr("app.services.document_processor.storage.text_path", tmp_path / "artifacts" / "extracted_text")
    monkeypatch.setattr("app.services.document_processor.text_extractor.extract", lambda *_: (None, None, None))
    monkeypatch.setattr("app.services.document_processor.thumbnail_generator.generate", lambda *_: None)
    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.analyze_document", lambda **_: {"summary": "S", "key_points": [], "tags": [], "entities": {}, "action_items": []})
    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.compute_confidence", lambda _: 0.9)

    document_processor.process_document(db, sample_document)
    db.refresh(sample_document)
    assert sample_document.summary == "S"
    assert sample_document.processing_status == "completed"


def test_existing_intelligence_is_updated_not_duplicated(db, sample_document):
    existing = DocumentIntelligence(document_id=sample_document.id, summary="old", key_points=[], suggested_tags=[], entities={})
    db.add(existing)
    db.commit()

    from app.services.document_intelligence import document_intelligence_service

    document_intelligence_service.create_from_analysis(
        db,
        sample_document,
        {"summary": "new", "key_points": ["k"], "tags": ["t"], "entities": {}, "action_items": []},
    )
    rows = db.query(DocumentIntelligence).filter(DocumentIntelligence.document_id == sample_document.id).all()
    assert len(rows) == 1
    assert rows[0].summary == "new"
