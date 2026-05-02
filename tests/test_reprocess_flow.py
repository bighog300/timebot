from pathlib import Path
import os

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


def test_process_document_uses_latest_saved_text_when_multiple_exist(db, sample_document, monkeypatch, tmp_path):
    sample_document.original_path = str(tmp_path / "missing.pdf")
    sample_document.file_type = "pdf"
    sample_document.raw_text = None
    db.add(sample_document)
    db.commit()

    old_dir = tmp_path / "artifacts" / "extracted_text" / "2026" / "01" / "01"
    new_dir = tmp_path / "artifacts" / "extracted_text" / "2026" / "01" / "02"
    old_dir.mkdir(parents=True)
    new_dir.mkdir(parents=True)
    old_path = old_dir / f"{sample_document.id}.txt"
    new_path = new_dir / f"{sample_document.id}.txt"
    old_path.write_text("Older text", encoding="utf-8")
    new_path.write_text("Newer text", encoding="utf-8")
    os.utime(old_path, (1_600_000_000, 1_600_000_000))
    os.utime(new_path, (1_700_000_000, 1_700_000_000))

    monkeypatch.setattr("app.services.document_processor.storage.text_path", tmp_path / "artifacts" / "extracted_text")
    monkeypatch.setattr("app.services.document_processor.text_extractor.extract", lambda *_: (None, None, None))
    monkeypatch.setattr("app.services.document_processor.thumbnail_generator.generate", lambda *_: None)
    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.analyze_document", lambda **_: {"summary": "S", "key_points": [], "tags": [], "entities": {}, "action_items": []})
    monkeypatch.setattr("app.services.ai_analyzer.ai_analyzer.compute_confidence", lambda _: 0.9)

    document_processor.process_document(db, sample_document)
    db.refresh(sample_document)
    assert sample_document.raw_text == "Newer text"


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


def test_reprocess_updates_blank_document_and_intelligence_summary(db, sample_document):
    from app.services.document_intelligence import document_intelligence_service

    sample_document.summary = ""
    existing = DocumentIntelligence(document_id=sample_document.id, summary="", key_points=[], suggested_tags=[], entities={})
    db.add(existing)
    db.add(sample_document)
    db.commit()

    document_intelligence_service.create_from_analysis(
        db,
        sample_document,
        {"summary": "Expected non-empty summary", "key_points": ["k"], "tags": ["t"], "entities": {}, "action_items": []},
    )
    db.expire_all()
    refreshed_doc = db.query(type(sample_document)).filter(type(sample_document).id == sample_document.id).first()
    refreshed_intel = db.query(DocumentIntelligence).filter(DocumentIntelligence.document_id == sample_document.id).first()
    assert refreshed_doc.summary == "Expected non-empty summary"
    assert refreshed_intel.summary == "Expected non-empty summary"


def test_process_task_registered():
    from app.workers.celery_app import celery_app

    registered = celery_app.tasks.keys()
    assert "app.workers.tasks.process_document_task" in registered
    assert "app.workers.tasks.reprocess_document_task" in registered


def test_reprocess_sets_enrichment_pending(client, sample_document, db, monkeypatch):
    sample_document.extracted_metadata = {"enrichment_status": "complete", "enrichment_pending": False}
    db.add(sample_document)
    db.commit()

    class _TaskResult:
        id = "task-rp"

    monkeypatch.setattr("app.workers.tasks.reprocess_document_task.apply_async", lambda *_, **__: _TaskResult())
    resp = client.post(f"/api/v1/documents/{sample_document.id}/reprocess")
    assert resp.status_code == 200
    db.refresh(sample_document)
    assert sample_document.enrichment_status == "pending"
    assert sample_document.enrichment_pending is True
