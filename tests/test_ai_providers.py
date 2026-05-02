from __future__ import annotations

import types

import pytest

from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.claude_provider import ClaudeProvider
from app.services.ai.base import AIClient
from app.services.ai.openai_provider import OpenAIProvider
from app.services.openai_client import AIClientRouter, AIProviderExecutionError




def test_openai_provider_passes_timeout_to_client(monkeypatch):
    provider = OpenAIProvider()
    monkeypatch.setattr("app.services.ai.openai_provider.settings.OPENAI_API_KEY", "openai-key")
    monkeypatch.setattr("app.services.ai.openai_provider.settings.AI_PROVIDER_TIMEOUT_SECONDS", 25)

    called = {}

    class DummyOpenAI:
        def __init__(self, api_key, timeout):
            called["api_key"] = api_key
            called["timeout"] = timeout
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda **kwargs: {"ok": True}))

    monkeypatch.setattr("app.services.ai.openai_provider.OpenAI", DummyOpenAI)

    provider.generate_completion({"model": "x", "messages": []})
    assert called["api_key"] == "openai-key"
    assert called["timeout"] == 25

def test_gemini_provider_builds_completion_request(monkeypatch):
    provider = GeminiProvider()
    monkeypatch.setattr("app.services.ai.gemini_provider.settings.GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.ai.gemini_provider.settings.GEMINI_MODEL", "gemini-test")

    called = {}

    class DummyModel:
        def __init__(self, model_name):
            called["model_name"] = model_name

        def generate_content(self, **kwargs):
            called["kwargs"] = kwargs
            return {"ok": True}

    fake_genai = types.SimpleNamespace(
        configure=lambda api_key: called.setdefault("api_key", api_key),
        GenerativeModel=DummyModel,
    )
    monkeypatch.setitem(__import__("sys").modules, "google.generativeai", fake_genai)

    payload = {"contents": "hello"}
    response = provider.generate_completion(payload)

    assert response == {"ok": True}
    assert called["api_key"] == "test-key"
    assert called["model_name"] == "gemini-test"
    assert called["kwargs"]["contents"] == payload["contents"]
    assert called["kwargs"]["request_options"]["timeout"] == 60


def test_gemini_provider_missing_api_key(monkeypatch):
    provider = GeminiProvider()
    monkeypatch.setattr("app.services.ai.gemini_provider.settings.GEMINI_API_KEY", "")

    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        provider.generate_completion({"contents": "hello"})


def test_gemini_provider_stream_completion(monkeypatch):
    provider = GeminiProvider()
    monkeypatch.setattr("app.services.ai.gemini_provider.settings.GEMINI_API_KEY", "test-key")

    class DummyModel:
        def __init__(self, model_name):
            self.model_name = model_name

        def generate_content(self, **kwargs):
            assert kwargs["stream"] is True
            return iter(["chunk1", "chunk2"])

    fake_genai = types.SimpleNamespace(configure=lambda api_key: None, GenerativeModel=DummyModel)
    monkeypatch.setitem(__import__("sys").modules, "google.generativeai", fake_genai)

    chunks = list(provider.stream_completion({"contents": "hello"}))
    assert chunks == ["chunk1", "chunk2"]




def test_gemini_provider_applies_default_timeout(monkeypatch):
    provider = GeminiProvider()
    monkeypatch.setattr("app.services.ai.gemini_provider.settings.GEMINI_API_KEY", "test-key")
    monkeypatch.setattr("app.services.ai.gemini_provider.settings.AI_PROVIDER_TIMEOUT_SECONDS", 42)

    called = {}

    class DummyModel:
        def __init__(self, model_name):
            pass

        def generate_content(self, **kwargs):
            called["kwargs"] = kwargs
            return {"ok": True}

    fake_genai = types.SimpleNamespace(configure=lambda api_key: None, GenerativeModel=DummyModel)
    monkeypatch.setitem(__import__("sys").modules, "google.generativeai", fake_genai)

    provider.generate_completion({"contents": "hello"})
    assert called["kwargs"]["request_options"]["timeout"] == 42


def test_claude_provider_passes_timeout_to_client(monkeypatch):
    provider = ClaudeProvider()
    monkeypatch.setattr("app.services.ai.claude_provider.settings.ANTHROPIC_API_KEY", "anthropic-key")
    monkeypatch.setattr("app.services.ai.claude_provider.settings.ANTHROPIC_MODEL", "claude-test")
    monkeypatch.setattr("app.services.ai.claude_provider.settings.AI_PROVIDER_TIMEOUT_SECONDS", 33)

    called = {}

    class DummyMessages:
        def create(self, **kwargs):
            return {"ok": True}

    class DummyAnthropic:
        def __init__(self, api_key, timeout):
            called["api_key"] = api_key
            called["timeout"] = timeout
            self.messages = DummyMessages()

    monkeypatch.setitem(__import__("sys").modules, "anthropic", types.SimpleNamespace(Anthropic=DummyAnthropic))

    provider.generate_completion({"max_tokens": 10, "messages": [{"role": "user", "content": "Hi"}]})
    assert called["api_key"] == "anthropic-key"
    assert called["timeout"] == 33

def test_claude_provider_builds_completion_request(monkeypatch):
    provider = ClaudeProvider()
    monkeypatch.setattr("app.services.ai.claude_provider.settings.ANTHROPIC_API_KEY", "anthropic-key")
    monkeypatch.setattr("app.services.ai.claude_provider.settings.ANTHROPIC_MODEL", "claude-test")

    called = {}

    class DummyMessages:
        def create(self, **kwargs):
            called["kwargs"] = kwargs
            return {"ok": True}

    class DummyAnthropic:
        def __init__(self, api_key, timeout):
            called["api_key"] = api_key
            called["timeout"] = timeout
            self.messages = DummyMessages()

    monkeypatch.setitem(__import__("sys").modules, "anthropic", types.SimpleNamespace(Anthropic=DummyAnthropic))

    response = provider.generate_completion({"max_tokens": 10, "messages": [{"role": "user", "content": "Hi"}]})
    assert response == {"ok": True}
    assert called["api_key"] == "anthropic-key"
    assert called["kwargs"]["model"] == "claude-test"


def test_claude_provider_missing_api_key(monkeypatch):
    provider = ClaudeProvider()
    monkeypatch.setattr("app.services.ai.claude_provider.settings.ANTHROPIC_API_KEY", "")
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        provider.generate_completion({"messages": []})


def test_claude_provider_stream_completion(monkeypatch):
    provider = ClaudeProvider()
    monkeypatch.setattr("app.services.ai.claude_provider.settings.ANTHROPIC_API_KEY", "anthropic-key")
    monkeypatch.setattr("app.services.ai.claude_provider.settings.ANTHROPIC_MODEL", "claude-test")

    class DummyMessages:
        def stream(self, **kwargs):
            assert kwargs["model"] == "claude-test"
            return iter(["a", "b"])

    class DummyAnthropic:
        def __init__(self, api_key, timeout):
            self.messages = DummyMessages()

    monkeypatch.setitem(__import__("sys").modules, "anthropic", types.SimpleNamespace(Anthropic=DummyAnthropic))
    assert list(provider.stream_completion({"messages": []})) == ["a", "b"]


class _Provider(AIClient):
    def __init__(self, *, ok_value=None, error: Exception | None = None):
        self.ok_value = ok_value
        self.error = error

    @property
    def enabled(self) -> bool:
        return True

    def generate_completion(self, payload):
        if self.error:
            raise self.error
        return self.ok_value

    def stream_completion(self, payload):
        if self.error:
            raise self.error
        return iter([self.ok_value])


def test_default_provider_is_openai(monkeypatch):
    router = AIClientRouter()
    monkeypatch.setattr("app.services.openai_client.settings.DEFAULT_AI_PROVIDER", "openai")
    assert router.selected_provider_name == "openai"


def test_selecting_gemini(monkeypatch):
    router = AIClientRouter()
    monkeypatch.setattr("app.services.openai_client.settings.DEFAULT_AI_PROVIDER", "gemini")
    assert isinstance(router.get_provider(router.selected_provider_name), GeminiProvider)


def test_selecting_claude(monkeypatch):
    router = AIClientRouter()
    monkeypatch.setattr("app.services.openai_client.settings.DEFAULT_AI_PROVIDER", "claude")
    assert isinstance(router.get_provider(router.selected_provider_name), ClaudeProvider)


def test_fallback_uses_next_provider(monkeypatch):
    router = AIClientRouter()
    router._registry = {
        "gemini": _Provider(error=RuntimeError("gemini down")),
        "openai": _Provider(ok_value={"ok": 1}),
    }
    monkeypatch.setattr("app.services.openai_client.settings.DEFAULT_AI_PROVIDER", "gemini")
    monkeypatch.setattr("app.services.openai_client.settings.AI_PROVIDER_FALLBACKS", "openai")
    assert router.generate_completion({"x": 1}) == {"ok": 1}


def test_fallback_stops_on_first_success(monkeypatch):
    router = AIClientRouter()
    hits = []

    class HitProvider(_Provider):
        def generate_completion(self, payload):
            hits.append(self.ok_value)
            return super().generate_completion(payload)

    router._registry = {
        "gemini": HitProvider(error=RuntimeError("fail"), ok_value="gemini"),
        "claude": HitProvider(ok_value="claude"),
        "openai": HitProvider(ok_value="openai"),
    }
    monkeypatch.setattr("app.services.openai_client.settings.DEFAULT_AI_PROVIDER", "gemini")
    monkeypatch.setattr("app.services.openai_client.settings.AI_PROVIDER_FALLBACKS", "claude,openai")
    assert router.generate_completion({"x": 1}) == "claude"
    assert hits == ["gemini", "claude"]


def test_all_provider_failure_raises_clear_error(monkeypatch):
    router = AIClientRouter()
    router._registry = {"gemini": _Provider(error=RuntimeError("nope")), "openai": _Provider(error=ValueError("bad"))}
    monkeypatch.setattr("app.services.openai_client.settings.DEFAULT_AI_PROVIDER", "gemini")
    monkeypatch.setattr("app.services.openai_client.settings.AI_PROVIDER_FALLBACKS", "openai")
    with pytest.raises(AIProviderExecutionError, match="All AI providers failed"):
        router.generate_completion({"x": 1})


def test_router_generate_embedding_uses_openai_provider_without_client_property_on_router(monkeypatch):
    router = AIClientRouter()

    class DummyEmbeddings:
        def create(self, **kwargs):
            assert kwargs["model"] == "text-embedding-3-small"
            assert kwargs["input"] == "hello"
            return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[0.1, 0.2])])

    class DummyOpenAIProvider(_Provider):
        @property
        def client(self):
            return types.SimpleNamespace(embeddings=DummyEmbeddings())

    router._registry["openai"] = DummyOpenAIProvider(ok_value=None)

    embedding = router.generate_embedding(model="text-embedding-3-small", input_text="hello")
    assert embedding == [0.1, 0.2]
