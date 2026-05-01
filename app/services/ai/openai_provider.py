from __future__ import annotations

from typing import Any, Iterable, Optional

from openai import OpenAI

from app.config import settings
from app.services.ai.base import AIClient


class OpenAIProvider(AIClient):
    def __init__(self):
        self._client: Optional[OpenAI] = None

    @property
    def enabled(self) -> bool:
        return bool(settings.OPENAI_API_KEY)

    @property
    def client(self) -> OpenAI:
        if not self.enabled:
            raise ValueError("OPENAI_API_KEY not configured")
        if self._client is None:
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    def generate_completion(self, payload: dict[str, Any]) -> Any:
        return self.client.chat.completions.create(**payload)

    def stream_completion(self, payload: dict[str, Any]) -> Iterable[Any]:
        return self.client.chat.completions.create(**payload, stream=True)
