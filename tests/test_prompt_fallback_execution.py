from types import SimpleNamespace

import pytest

from app.models.prompt_template import PromptTemplate
from app.services.ai_analyzer import AIAnalyzer
from app.services.prompt_templates import run_prompt_with_fallback


class MockLLMError(Exception):
    pass


def _template(**kwargs):
    base = dict(type="timeline_extraction", name="t", content="summary timeline_events relationships entities key_points", provider="openai", model="gpt-4o-mini", temperature=0.2, max_tokens=200, top_p=1.0, fallback_enabled=True, fallback_provider="gemini", fallback_model="gemini-1.5-flash", is_active=True)
    base.update(kwargs)
    return PromptTemplate(**base)


def test_run_prompt_primary_success(monkeypatch):
    monkeypatch.setattr("app.services.openai_client.openai_client_service.generate_completion_for_provider", lambda *_: SimpleNamespace(text="ok"))
    res = run_prompt_with_fallback(_template(), "hello", db=None)
    assert res["fallback_used"] is False
    assert res["provider_used"] == "openai"


def test_run_prompt_fallback_after_primary_failure(monkeypatch):
    calls = []

    def fake(provider, _payload):
        calls.append(provider)
        if provider == "openai":
            raise MockLLMError("mock failure")
        return SimpleNamespace(text="fallback ok")

    monkeypatch.setattr("app.services.openai_client.openai_client_service.generate_completion_for_provider", fake)
    res = run_prompt_with_fallback(_template(), "hello", db=None)
    assert res["fallback_used"] is True
    assert calls == ["openai", "gemini"]


def test_run_prompt_no_fallback_raises(monkeypatch):
    monkeypatch.setattr("app.services.openai_client.openai_client_service.generate_completion_for_provider", lambda *_: (_ for _ in ()).throw(MockLLMError("mock failure")))
    with pytest.raises(RuntimeError):
        run_prompt_with_fallback(_template(fallback_enabled=False), "hello", db=None)


def test_run_prompt_dual_failure_raises(monkeypatch):
    monkeypatch.setattr("app.services.openai_client.openai_client_service.generate_completion_for_provider", lambda *_: (_ for _ in ()).throw(MockLLMError("mock failure")))
    with pytest.raises(RuntimeError):
        run_prompt_with_fallback(_template(), "hello", db=None)


def test_run_prompt_fallback_respects_max_attempts_zero(monkeypatch):
    monkeypatch.setattr("app.services.openai_client.openai_client_service.generate_completion_for_provider", lambda *_: (_ for _ in ()).throw(MockLLMError("provider failure")))
    with pytest.raises(RuntimeError):
        run_prompt_with_fallback(_template(max_fallback_attempts=0), "hello", db=None)


def test_run_prompt_fallback_respects_retry_flags(monkeypatch):
    monkeypatch.setattr("app.services.openai_client.openai_client_service.generate_completion_for_provider", lambda *_: (_ for _ in ()).throw(MockLLMError("validation error")))
    with pytest.raises(RuntimeError):
        run_prompt_with_fallback(_template(retry_on_provider_errors=False, retry_on_validation_error=False), "hello", db=None)


def test_run_prompt_fallback_reason_recorded(db, monkeypatch):
    calls = []
    t = _template()
    db.add(t)
    db.commit()
    def fake(provider, _payload):
        calls.append(provider)
        if provider == "openai":
            raise MockLLMError("provider failure")
        return SimpleNamespace(text="ok")
    monkeypatch.setattr("app.services.openai_client.openai_client_service.generate_completion_for_provider", fake)
    run_prompt_with_fallback(t, "hello", db=db, user_id=None, source="test", purpose="chat")
    from app.models.prompt_execution_log import PromptExecutionLog
    row = db.query(PromptExecutionLog).order_by(PromptExecutionLog.created_at.desc()).first()
    assert row.fallback_used is True
    assert row.fallback_reason == "primary_error"


def test_runtime_path_uses_fallback_template_provider(db, monkeypatch):
    analyzer = AIAnalyzer()
    monkeypatch.setattr("app.services.ai_analyzer.settings.OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.ai_analyzer.settings.AI_MAX_TOKENS", 300)
    t = _template(is_default=True, enabled=True)
    db.add(t)
    db.commit()

    def fake(provider, _payload):
        if provider == "openai":
            raise MockLLMError("mock failure")
        return SimpleNamespace(text='{"summary":"ok","timeline_events":[],"relationships":[]}')

    monkeypatch.setattr("app.services.openai_client.openai_client_service.generate_completion_for_provider", fake)
    analysis = analyzer.analyze_document("sample", filename="f.txt", file_type="txt", db=db)
    assert analysis["summary"] == "ok"



def test_estimate_llm_cost_known_model():
    from app.services.llm_pricing import estimate_llm_cost

    result = estimate_llm_cost('openai', 'gpt-4o-mini', 1000000, 1000000)
    assert result['pricing_known'] is True
    assert float(result['estimated_cost_usd']) == 0.75


def test_estimate_llm_cost_unknown_model():
    from app.services.llm_pricing import estimate_llm_cost

    result = estimate_llm_cost('openai', 'unknown-model', 100, 100)
    assert result['pricing_known'] is False
    assert result['estimated_cost_usd'] is None
