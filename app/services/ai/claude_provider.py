from __future__ import annotations

from typing import Any, Iterable

from app.config import settings
from app.services.ai.base import AIClient


class ClaudeProvider(AIClient):
    @property
    def enabled(self) -> bool:
        return bool(settings.ANTHROPIC_API_KEY)

    def _get_client(self) -> Any:
        if not self.enabled:
            raise ValueError("ANTHROPIC_API_KEY not configured")
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise RuntimeError("Anthropic SDK not installed. Install `anthropic` to enable ClaudeProvider.") from exc
        return Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            timeout=settings.AI_PROVIDER_TIMEOUT_SECONDS,
        )

    def generate_completion(self, payload: dict[str, Any]) -> Any:
        client = self._get_client()
        return client.messages.create(model=settings.ANTHROPIC_MODEL, **payload)

    def stream_completion(self, payload: dict[str, Any]) -> Iterable[Any]:
        client = self._get_client()
        return client.messages.stream(model=settings.ANTHROPIC_MODEL, **payload)
