import logging
from typing import Optional

from openai import APIError, OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIClientService:
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


openai_client_service = OpenAIClientService()

__all__ = ["openai_client_service", "APIError"]
