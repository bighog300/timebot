import logging
import time
from collections.abc import Iterable
from typing import Any

from openai import APIError

from app.config import settings
from app.services.ai.base import AIClient
from app.services.ai.claude_provider import ClaudeProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_provider import OpenAIProvider


logger = logging.getLogger(__name__)


class AIProviderExecutionError(RuntimeError):
    pass


class InvalidAIPayloadError(ValueError):
    pass



class AIClientRouter(AIClient):
    def __init__(self):
        self._registry: dict[str, AIClient] = {
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
            "claude": ClaudeProvider(),
        }

    @property
    def enabled(self) -> bool:
        return self._registry.get(self.selected_provider_name, self._registry["openai"]).enabled

    @property
    def selected_provider_name(self) -> str:
        return (settings.DEFAULT_AI_PROVIDER or "openai").strip().lower() or "openai"

    @property
    def fallback_provider_names(self) -> list[str]:
        raw = settings.AI_PROVIDER_FALLBACKS or "openai"
        return [p.strip().lower() for p in raw.split(",") if p.strip()]

    def get_provider(self, name: str) -> AIClient:
        provider = self._registry.get(name)
        if provider is None:
            raise ValueError(f"Unknown AI provider: {name}")
        return provider

    def _execute_with_fallbacks(self, fn_name: str, payload: dict[str, Any]) -> Any:
        if not isinstance(payload, dict):
            raise InvalidAIPayloadError("AI completion payload must be a dict")

        order: list[str] = []
        for name in [self.selected_provider_name, *self.fallback_provider_names]:
            if name and name not in order:
                order.append(name)

        errors: list[str] = []
        for idx, name in enumerate(order):
            provider = self.get_provider(name)
            fn = getattr(provider, fn_name)
            start = time.perf_counter()
            model_name = payload.get("model")
            try:
                result = fn(payload)
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                logger.info(
                    "ai_provider_call success=true selected_provider=%s provider=%s fallback_provider=%s model=%s fn=%s duration_ms=%s",
                    self.selected_provider_name,
                    name,
                    None if idx == 0 else name,
                    model_name,
                    fn_name,
                    elapsed_ms,
                )
                return result
            except InvalidAIPayloadError:
                raise
            except Exception as exc:
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                logger.warning(
                    "ai_provider_call success=false selected_provider=%s provider=%s fallback_provider=%s model=%s fn=%s duration_ms=%s error_type=%s",
                    self.selected_provider_name,
                    name,
                    name,
                    model_name,
                    fn_name,
                    elapsed_ms,
                    type(exc).__name__,
                )
                errors.append(f"{name}: {type(exc).__name__}: {exc}")
                continue
        raise AIProviderExecutionError("All AI providers failed. " + " | ".join(errors))

    def generate_completion(self, payload: dict[str, Any]) -> Any:
        return self._execute_with_fallbacks("generate_completion", payload)

    def stream_completion(self, payload: dict[str, Any]) -> Iterable[Any]:
        return self._execute_with_fallbacks("stream_completion", payload)

    def extract_response_text(self, response: Any) -> str:
        if response is None:
            return ""

        choices = getattr(response, "choices", None)
        if isinstance(choices, list) and choices:
            message = getattr(choices[0], "message", None)
            content = getattr(message, "content", None)
            if isinstance(content, str):
                return content.strip()

        text = getattr(response, "text", None)
        if isinstance(text, str):
            return text.strip()

        content = getattr(response, "content", None)
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            chunks: list[str] = []
            for item in content:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    chunks.append(item["text"])
                elif hasattr(item, "text") and isinstance(item.text, str):
                    chunks.append(item.text)
            if chunks:
                return "\n".join(chunks).strip()

        return str(response).strip()

    @property
    def _client(self) -> Any:
        current = self._registry.get(self.selected_provider_name)
        return getattr(current, "_client", None)

    @_client.setter
    def _client(self, value: Any) -> None:
        current = self._registry.get(self.selected_provider_name)
        if current is not None:
            setattr(current, "_client", value)

openai_client_service = AIClientRouter()

__all__ = ["openai_client_service", "APIError", "AIClientRouter", "AIProviderExecutionError", "InvalidAIPayloadError"]
