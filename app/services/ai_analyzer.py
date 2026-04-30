import json
import logging
from typing import Any, Dict, List, Optional

from app.config import settings
from app.prompts.document_analysis import DOCUMENT_ANALYSIS_SYSTEM, build_document_analysis_prompt
from app.services.openai_client import APIError, openai_client_service

logger = logging.getLogger(__name__)

MAX_TEXT_CHARS = 15_000  # ~3 750 tokens


class AIAnalysisError(RuntimeError):
    """Raised when AI analysis is unavailable or returns invalid output."""


class AIAnalyzer:
    def analyze_document(
        self,
        text: str,
        filename: str,
        file_type: str = "unknown",
        existing_categories: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if not text or not text.strip():
            raise AIAnalysisError("AI enrichment failed: document text is empty.")
        if not openai_client_service.enabled:
            raise AIAnalysisError("AI enrichment unavailable: OPENAI_API_KEY is not configured.")

        try:
            categories_str = ", ".join(existing_categories) if existing_categories else "none yet"
            try:
                prompt = build_document_analysis_prompt(
                    filename=filename,
                    file_type=file_type,
                    char_limit=MAX_TEXT_CHARS,
                    text=text[:MAX_TEXT_CHARS],
                    categories=categories_str,
                )
            except Exception as render_exc:
                logger.error(
                    "AI prompt rendering failed: exception_type=%s message=%s",
                    type(render_exc).__name__,
                    render_exc,
                )
                raise

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
            analysis = self._normalize_analysis(self._parse_json(content))
            summary = (analysis.get("summary") or "").strip()
            if not summary:
                raise AIAnalysisError("AI enrichment failed: summary missing from model response.")
            return analysis

        except APIError as e:
            logger.error("OpenAI API error: %s", e)
            raise AIAnalysisError(f"AI enrichment failed: OpenAI API error: {e}") from e
        except AIAnalysisError:
            raise
        except Exception as e:
            logger.error("AI analysis error: %s", e)
            raise AIAnalysisError(f"AI enrichment failed: {e}") from e

    def _parse_json(self, content: str) -> Dict[str, Any]:
        content = content.strip()
        if content.startswith("```"):
            lines = content.splitlines()
            content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("JSON parse error in AI response: %s", e)
            raise AIAnalysisError("AI enrichment failed: invalid JSON response.") from e

    def _normalize_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(analysis or {})
        summary = normalized.get("summary")
        if not summary:
            summary = (
                normalized.get("document_summary")
                or normalized.get("executive_summary")
                or (normalized.get("analysis") or {}).get("summary")
            )
        normalized["summary"] = (summary or "").strip()
        normalized["key_points"] = normalized.get("key_points") or []
        normalized["tags"] = normalized.get("tags") or []
        normalized["entities"] = normalized.get("entities") or {}
        timeline_events = normalized.get("timeline_events") or []
        if not isinstance(timeline_events, list):
            timeline_events = []
        normalized["timeline_events"] = timeline_events
        normalized["action_items"] = normalized.get("action_items") or []
        return normalized

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
