from types import SimpleNamespace

from app.prompts.document_analysis import build_default_summary_prompt
from app.services.ai_analyzer import AIAnalyzer


def test_summary_succeeds_with_openai_response_shape(monkeypatch):
    analyzer = AIAnalyzer()
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr("app.services.ai_analyzer.settings.AI_MAX_TOKENS", 300)

    response_payload = '{"summary":"Generated summary.","timeline_events":[],"relationships":[]}'
    mock_response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=response_payload))])
    monkeypatch.setattr("app.services.ai_analyzer.openai_client_service.generate_completion", lambda _payload: mock_response)

    analysis = analyzer.analyze_document("sample text", filename="sample.txt", file_type="txt")
    assert analysis["summary"] == "Generated summary."


def test_summary_succeeds_with_gemini_mock_shape(monkeypatch):
    analyzer = AIAnalyzer()
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr("app.services.ai_analyzer.settings.AI_MAX_TOKENS", 300)

    response = SimpleNamespace(text='{"summary":"Gemini summary","timeline_events":[],"relationships":[]}')
    monkeypatch.setattr("app.services.ai_analyzer.openai_client_service.generate_completion", lambda _payload: response)

    analysis = analyzer.analyze_document("sample text", filename="sample.txt", file_type="txt")
    assert analysis["summary"] == "Gemini summary"


def test_summary_succeeds_with_claude_mock_shape(monkeypatch):
    analyzer = AIAnalyzer()
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr("app.services.ai_analyzer.settings.AI_MAX_TOKENS", 300)

    response = SimpleNamespace(content=[SimpleNamespace(text='{"summary":"Claude summary","timeline_events":[],"relationships":[]}')])
    monkeypatch.setattr("app.services.ai_analyzer.openai_client_service.generate_completion", lambda _payload: response)

    analysis = analyzer.analyze_document("sample text", filename="sample.txt", file_type="txt")
    assert analysis["summary"] == "Claude summary"


def test_malformed_json_fallback_summary_used(monkeypatch):
    analyzer = AIAnalyzer()
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr("app.services.ai_analyzer.settings.AI_MAX_TOKENS", 300)

    calls = {"n": 0}

    def _mock_completion(_payload):
        calls["n"] += 1
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="not json"))])

    monkeypatch.setattr("app.services.ai_analyzer.openai_client_service.generate_completion", _mock_completion)
    analysis = analyzer.analyze_document("sample text", filename="sample.txt", file_type="txt")
    assert calls["n"] == 2
    assert analysis["summary"] == "not json"


def test_no_admin_template_uses_default_prompt(db):
    analyzer = AIAnalyzer()
    default = build_default_summary_prompt(filename="sample.txt", file_type="txt", char_limit=100, text="x")
    prompt = analyzer.get_prompt_template("timeline_extraction", default, db=db)
    assert prompt == default
