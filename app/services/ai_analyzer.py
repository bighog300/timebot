import json
import logging
from typing import Any, Dict, List, Optional

import anthropic

from app.config import settings
from app.prompts.document_analysis import DOCUMENT_ANALYSIS_SYSTEM, DOCUMENT_ANALYSIS_TEMPLATE

logger = logging.getLogger(__name__)

MAX_TEXT_CHARS = 15_000  # ~3 750 tokens


class AIAnalyzer:
    def __init__(self):
        self._client: Optional[anthropic.Anthropic] = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    def analyze_document(
        self,
        text: str,
        filename: str,
        file_type: str = "unknown",
        existing_categories: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not text or not text.strip():
            return None
        if not settings.ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY not configured — skipping AI analysis")
            return None

        try:
            categories_str = ", ".join(existing_categories) if existing_categories else "none yet"
            prompt = DOCUMENT_ANALYSIS_TEMPLATE.format(
                filename=filename,
                file_type=file_type,
                char_limit=MAX_TEXT_CHARS,
                text=text[:MAX_TEXT_CHARS],
                categories=categories_str,
            )

            response = self.client.messages.create(
                model=settings.AI_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                system=[
                    {
                        "type": "text",
                        "text": DOCUMENT_ANALYSIS_SYSTEM,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": prompt}],
            )

            return self._parse_json(response.content[0].text)

        except anthropic.APIError as e:
            logger.error("Anthropic API error: %s", e)
            return None
        except Exception as e:
            logger.error("AI analysis error: %s", e)
            return None

    def _parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        content = content.strip()
        # Strip markdown fences if present
        if content.startswith("```"):
            lines = content.splitlines()
            content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("JSON parse error in AI response: %s", e)
            return None

    def compute_confidence(self, analysis: Dict[str, Any]) -> float:
        confidence = 1.0

        summary = (analysis.get("summary") or "").strip()
        if len(summary.split()) < 20:
            confidence -= 0.15

        for field_name in ("key_points", "entities", "tags"):
            value = analysis.get(field_name)
            if not value:
                confidence -= 0.1

        if not analysis.get("action_items"):
            confidence -= 0.2

        return max(0.0, min(1.0, confidence))


ai_analyzer = AIAnalyzer()
