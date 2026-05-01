from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable


class AIClient(ABC):
    @property
    @abstractmethod
    def enabled(self) -> bool:
        """Whether provider is configured and usable."""

    @abstractmethod
    def generate_completion(self, payload: dict[str, Any]) -> Any:
        """Generate a non-streaming completion."""

    @abstractmethod
    def stream_completion(self, payload: dict[str, Any]) -> Iterable[Any]:
        """Generate a streaming completion iterator."""
