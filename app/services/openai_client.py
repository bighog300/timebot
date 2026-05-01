from openai import APIError

from app.config import settings
from app.services.ai.openai_provider import OpenAIProvider


openai_client_service = OpenAIProvider()

__all__ = ["openai_client_service", "APIError"]
