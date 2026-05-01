import json
import logging
import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.prompts.document_analysis import DOCUMENT_ANALYSIS_SYSTEM, build_default_summary_prompt
from app.services.openai_client import APIError, openai_client_service
from app.services.prompt_templates import get_active_prompt_content

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
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        if not text or not text.strip():
            raise AIAnalysisError("AI enrichment failed: document text is empty.")
        if not openai_client_service.enabled:
            raise AIAnalysisError("AI enrichment unavailable: OPENAI_API_KEY is not configured.")

        try:
            categories_str = ", ".join(existing_categories) if existing_categories else "none yet"
            try:
                prompt = self.get_prompt_template(
                    "timeline_extraction",
                    db=db,
                    filename=filename,
                    file_type=file_type,
                    text=text[:MAX_TEXT_CHARS],
                    char_limit=MAX_TEXT_CHARS,
                )
            except Exception as render_exc:
                logger.error(
                    "AI prompt rendering failed: exception_type=%s message=%s",
                    type(render_exc).__name__,
                    render_exc,
                )
                raise

            logger.info("ai_summary_prompt_used prompt_type=%s provider_used=%s", "timeline_extraction", openai_client_service.selected_provider_name)
            response = openai_client_service.generate_completion({
                "model": settings.OPENAI_MODEL,
                "max_tokens": settings.AI_MAX_TOKENS,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": DOCUMENT_ANALYSIS_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
            })
            content = openai_client_service.extract_response_text(response)
            analysis = self._parse_and_normalize(content, filename=filename)
            logger.info("ai_analysis_complete filename=%s timeline_event_count=%s", filename, len(analysis.get("timeline_events", [])))
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

    def get_prompt_template(
        self,
        prompt_type: str,
        *,
        db: Optional[Session] = None,
        filename: str,
        file_type: str,
        text: str,
        char_limit: int,
    ) -> str:
        default_prompt = self._get_default_prompt(prompt_type, filename, file_type, text, char_limit)
        if db is None:
            return default_prompt
        return get_active_prompt_content(db, prompt_type, default_prompt)

    def _get_default_prompt(self, prompt_type: str, filename: str, file_type: str, text: str, char_limit: int) -> str:
        if prompt_type == "timeline_extraction":
            return build_default_summary_prompt(
                filename=filename,
                file_type=file_type,
                char_limit=char_limit,
                text=text,
            )
        raise AIAnalysisError(f"AI enrichment failed: unsupported prompt type '{prompt_type}'.")

    def _parse_and_normalize(self, content: str, *, filename: str) -> Dict[str, Any]:
        try:
            analysis = self._normalize_analysis(self._parse_json(content))
            logger.info("ai_summary_parse_success filename=%s parse_success=true", filename)
            return analysis
        except AIAnalysisError:
            logger.warning("ai_summary_parse_failure filename=%s parse_success=false", filename)
            retry_content = self._retry_json_only(content)
            if retry_content is not None:
                try:
                    analysis = self._normalize_analysis(self._parse_json(retry_content))
                    logger.info("ai_summary_parse_success filename=%s parse_success=true retry=true", filename)
                    return analysis
                except AIAnalysisError:
                    logger.warning("ai_summary_parse_failure filename=%s parse_success=false retry=true", filename)

            fallback_summary = (content or "").strip()[:500]
            return self._normalize_analysis({"summary": fallback_summary, "timeline_events": [], "relationships": []})

    def _retry_json_only(self, content: str) -> Optional[str]:
        response = openai_client_service.generate_completion({
            "model": settings.OPENAI_MODEL,
            "max_tokens": settings.AI_MAX_TOKENS,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": DOCUMENT_ANALYSIS_SYSTEM},
                {"role": "user", "content": f"Return ONLY valid JSON. No extra text.\n\n{content}"},
            ],
        })
        return openai_client_service.extract_response_text(response)

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
        timeline_events = self._extract_timeline_events(normalized)
        normalized["timeline_events"] = self._normalize_timeline_events(timeline_events)
        normalized["action_items"] = normalized.get("action_items") or []
        return normalized

    def _extract_timeline_events(self, normalized: Dict[str, Any]) -> List[Dict[str, Any]]:
        aliases = ["timeline_events", "events", "important_dates", "dates", "milestones", "deadlines"]
        candidates: List[Any] = []
        for key in aliases:
            value = normalized.get(key)
            if isinstance(value, list):
                candidates.extend(value)
        nested = normalized.get("analysis")
        if isinstance(nested, dict):
            nested_events = nested.get("timeline_events")
            if isinstance(nested_events, list):
                candidates.extend(nested_events)
        return [item for item in candidates if isinstance(item, dict)]

    def _normalize_timeline_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        output: List[Dict[str, Any]] = []
        for event in events:
            title = event.get("title") or event.get("name") or event.get("event_title")
            description = event.get("description") or event.get("details")
            source_quote = event.get("source_quote") or event.get("evidence") or event.get("quote")
            page_number = event.get("page_number") or event.get("page")
            raw_date = event.get("date") or event.get("event_date") or event.get("due_date") or event.get("effective_date")
            raw_start = event.get("start_date") or event.get("from") or event.get("start")
            raw_end = event.get("end_date") or event.get("to") or event.get("end")

            date_value, _ = self._normalize_date(raw_date)
            start_value, start_approx = self._normalize_date(raw_start)
            end_value, end_approx = self._normalize_date(raw_end)
            date_approx = False
            if not date_value and raw_date and isinstance(raw_date, str):
                quarter = self._quarter_to_range(raw_date)
                if quarter:
                    start_value, end_value = quarter
                    date_approx = True
            if not (date_value or start_value or end_value):
                continue
            output.append(
                {
                    "title": (title or "Untitled event").strip(),
                    "description": description,
                    "date": date_value,
                    "start_date": start_value,
                    "end_date": end_value,
                    "approximate": bool(date_approx or start_approx or end_approx),
                    "confidence": float(event.get("confidence") or 0.4),
                    "source_quote": source_quote,
                    "page_number": int(page_number) if isinstance(page_number, (int, float, str)) and str(page_number).isdigit() else None,
                    "category": event.get("category"),
                    "source": event.get("source", "extracted"),
                }
            )
        return output

    def _normalize_date(self, value: Any) -> tuple[Optional[str], bool]:
        if isinstance(value, date):
            return value.isoformat(), False
        if not isinstance(value, str) or not value.strip():
            return None, False
        s = value.strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
            return s, False
        formats = ("%B %d, %Y", "%d %B %Y", "%m/%d/%Y", "%d/%m/%Y")
        for fmt in formats:
            try:
                return datetime.strptime(s, fmt).date().isoformat(), False
            except ValueError:
                pass
        month_year = re.fullmatch(r"([A-Za-z]+)\s+(\d{4})", s)
        if month_year:
            try:
                return datetime.strptime(s, "%B %Y").date().replace(day=1).isoformat(), True
            except ValueError:
                return None, False
        return None, False

    def _quarter_to_range(self, value: str) -> Optional[tuple[str, str]]:
        match = re.fullmatch(r"Q([1-4])\s+(\d{4})", value.strip(), flags=re.IGNORECASE)
        if not match:
            return None
        quarter = int(match.group(1))
        year = int(match.group(2))
        start_month = (quarter - 1) * 3 + 1
        start = date(year, start_month, 1)
        if quarter == 4:
            end = date(year, 12, 31)
        else:
            next_start = date(year, start_month + 3, 1)
            end = next_start.fromordinal(next_start.toordinal() - 1)
        return start.isoformat(), end.isoformat()

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
