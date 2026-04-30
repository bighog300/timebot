from types import SimpleNamespace

from app.prompts.document_analysis import build_document_analysis_prompt
from app.services.ai_analyzer import AIAnalyzer


def test_build_document_analysis_prompt_keeps_json_keys_and_includes_document_text():
    sample_text = "This is a sample document body."

    prompt = build_document_analysis_prompt(
        filename="doc.pdf",
        file_type="pdf",
        char_limit=15000,
        text=sample_text,
        categories="contracts, finance",
    )

    assert '"title"' in prompt
    assert '"summary"' in prompt
    assert '"timeline_events"' in prompt
    assert sample_text in prompt


def test_analyze_document_reaches_openai_call_and_returns_summary(monkeypatch):
    analyzer = AIAnalyzer()

    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setattr("app.services.ai_analyzer.settings.AI_MAX_TOKENS", 300)

    response_payload = '{"summary":"Generated summary.","key_points":[],"entities":{},"tags":[],"action_items":[]}'
    mock_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=response_payload))]
    )

    class _Completions:
        def create(self, **_kwargs):
            return mock_response

    mock_client = SimpleNamespace(chat=SimpleNamespace(completions=_Completions()))
    monkeypatch.setattr("app.services.ai_analyzer.openai_client_service._client", mock_client)

    analysis = analyzer.analyze_document("sample text", filename="sample.txt", file_type="txt")

    assert analysis["summary"] == "Generated summary."
