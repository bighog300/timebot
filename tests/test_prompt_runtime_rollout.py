from pathlib import Path
from types import SimpleNamespace
import uuid

from app.models.document import Document
from app.models.prompt_template import PromptTemplate
from app.services.ai_analyzer import AIAnalyzer
from app.services.relationship_detection import relationship_detection_service


def _mk(db, user_id, name, summary=""):
    doc = Document(
        id=uuid.uuid4(),
        filename=name,
        original_path=f"/tmp/{name}",
        file_type="pdf",
        file_size=100,
        mime_type="application/pdf",
        processing_status="completed",
        source="upload",
        user_id=user_id,
        is_archived=False,
        summary=summary,
        entities={},
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_migration_defines_prompt_templates_table():
    path = Path("migrations/versions/20260501_0015_prompt_templates.py")
    assert path.exists()
    text = path.read_text()
    assert "create_table(\n        \"prompt_templates\"" in text
    assert "UniqueConstraint(\"type\", \"name\", \"version\"" in text
    assert "ix_prompt_templates_type_active_updated" in text


def test_timeline_extraction_uses_active_prompt_when_configured(monkeypatch, db):
    analyzer = AIAnalyzer()
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr("app.services.ai_analyzer.settings.AI_MAX_TOKENS", 300)
    db.add(PromptTemplate(
        type="timeline_extraction",
        name="v2",
        content='Return JSON with keys: "summary", "timeline_events", "relationships", "entities", "key_points".',
        version=2,
        is_active=True,
    ))
    db.commit()

    captured = {}
    payload = '{"summary":"ok","key_points":[],"entities":{},"tags":[],"action_items":[]}'

    class _Completions:
        def create(self, **kwargs):
            captured["user_prompt"] = kwargs["messages"][1]["content"]
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=payload))])

    monkeypatch.setattr("app.services.ai_analyzer.openai_client_service._client", SimpleNamespace(chat=SimpleNamespace(completions=_Completions())))
    analyzer.analyze_document("sample text", filename="sample.txt", file_type="txt", db=db)
    assert '"summary"' in captured["user_prompt"]


def test_timeline_extraction_invalid_active_prompt_falls_back_to_default(monkeypatch, db, caplog):
    analyzer = AIAnalyzer()
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr("app.services.ai_analyzer.settings.AI_MAX_TOKENS", 300)
    db.add(PromptTemplate(type="timeline_extraction", name="short", content="Extract dates only.", version=2, is_active=True))
    db.commit()

    captured = {}
    payload = '{"summary":"ok","key_points":[],"entities":{},"tags":[],"action_items":[]}'

    class _Completions:
        def create(self, **kwargs):
            captured["user_prompt"] = kwargs["messages"][1]["content"]
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=payload))])

    monkeypatch.setattr("app.services.ai_analyzer.openai_client_service._client", SimpleNamespace(chat=SimpleNamespace(completions=_Completions())))
    analyzer.analyze_document("sample text", filename="sample.txt", file_type="txt", db=db)
    assert "You are analyzing a document." in captured["user_prompt"]
    assert "Extract dates only." not in caplog.text


def test_relationship_detection_uses_active_prompt_when_configured(db, test_user):
    a = _mk(db, test_user.id, "one.pdf", summary="Alpha kickoff")
    _mk(db, test_user.id, "two.pdf", summary="customsignal")
    db.add(PromptTemplate(type="relationship_detection", name="v2", content="customsignal", version=2, is_active=True))
    db.commit()

    result = relationship_detection_service.detect_for_document(db, a.id)
    assert result["created"] >= 1


def test_timeline_and_relationship_fallbacks_without_active_prompt(monkeypatch, db, test_user):
    analyzer = AIAnalyzer()
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr("app.services.ai_analyzer.settings.AI_MAX_TOKENS", 300)

    captured = {}
    payload = '{"summary":"ok","key_points":[],"entities":{},"tags":[],"action_items":[]}'

    class _Completions:
        def create(self, **kwargs):
            captured["user_prompt"] = kwargs["messages"][1]["content"]
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=payload))])

    monkeypatch.setattr("app.services.ai_analyzer.openai_client_service._client", SimpleNamespace(chat=SimpleNamespace(completions=_Completions())))
    analyzer.analyze_document("sample text", filename="sample.txt", file_type="txt", db=db)
    assert "You are analyzing a document." in captured["user_prompt"]

    a = _mk(db, test_user.id, "one.pdf", summary="Alpha kickoff")
    _mk(db, test_user.id, "two.pdf", summary="Contains follow up details")
    result = relationship_detection_service.detect_for_document(db, a.id)
    assert result["created"] >= 1

def test_invalid_admin_prompt_sets_fallback_warning_metadata(monkeypatch, db, sample_document):
    analyzer = AIAnalyzer()
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr("app.services.ai_analyzer.settings.AI_MAX_TOKENS", 300)
    db.add(PromptTemplate(type="timeline_extraction", name="bad", content="dates only", version=9, is_active=True))
    db.commit()

    payload = '{"summary":"ok","key_points":[],"entities":{},"tags":[],"action_items":["Respond by Friday"]}'
    monkeypatch.setattr("app.services.ai_analyzer.openai_client_service.generate_completion", lambda _payload: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=payload))]))

    analysis = analyzer.analyze_document("sample text", filename="sample.txt", file_type="txt", db=db)
    assert analysis["prompt_source"] == "default"
    assert analysis["admin_prompt_invalid_fallback"] is True
