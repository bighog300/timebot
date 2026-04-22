import json
import logging
from typing import Any, Dict, List, Optional

from app.config import settings
from app.prompts.document_analysis import DOCUMENT_ANALYSIS_SYSTEM, DOCUMENT_ANALYSIS_TEMPLATE
from app.services.openai_client import APIError, openai_client_service

logger = logging.getLogger(__name__)

MAX_TEXT_CHARS = 15_000  # ~3 750 tokens


class AIAnalyzer:
    def analyze_document(
        self,
        text: str,
        filename: str,
        file_type: str = "unknown",
        existing_categories: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not text or not text.strip():
            return None
        if not openai_client_service.enabled:
            logger.warning("OPENAI_API_KEY not configured — skipping AI analysis")
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

            response = openai_client_service.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                max_tokens=settings.AI_MAX_TOKENS,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": DOCUMENT_ANALYSIS_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            )
            content = (response.choices[0].message.content or "").strip()
            return self._parse_json(content)

        except APIError as e:
            logger.error("OpenAI API error: %s", e)
            return None
        except Exception as e:
            logger.error("AI analysis error: %s", e)
            return None

    def _parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        content = content.strip()
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
