from __future__ import annotations

from typing import Any, Iterable

from app.config import settings
from app.services.ai.base import AIClient


class GeminiProvider(AIClient):
    @property
    def enabled(self) -> bool:
        return bool(settings.GEMINI_API_KEY)

    def _get_client(self) -> Any:
        if not self.enabled:
            raise ValueError("GEMINI_API_KEY not configured")
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError(
                "Gemini SDK not installed. Install `google-generativeai` to enable GeminiProvider."
            ) from exc
        genai.configure(api_key=settings.GEMINI_API_KEY)
        return genai.GenerativeModel(settings.GEMINI_MODEL)

    def generate_completion(self, payload: dict[str, Any]) -> Any:
        model = self._get_client()
        return model.generate_content(**payload)

    def stream_completion(self, payload: dict[str, Any]) -> Iterable[Any]:
        model = self._get_client()
        return model.generate_content(**payload, stream=True)
