import json
import logging
import re
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.prompts.document_analysis import (
    DOCUMENT_ANALYSIS_SYSTEM,
    build_document_analysis_prompt,
    build_default_summary_prompt,
)
from app.services.openai_client import APIError, openai_client_service
from app.services.prompt_templates import get_active_prompt_content, get_prompt_for_purpose, run_prompt_with_fallback

logger = logging.getLogger(__name__)

MAX_TEXT_CHARS = 15_000  # ~3 750 tokens
_ANALYSIS_REQUIRED_PROMPT_TOKENS = ("summary", "timeline_events", "relationships", "entities", "key_points")


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
            analyze_start = time.perf_counter()
            ai_calls = 0
            categories_str = ", ".join(existing_categories) if existing_categories else "none yet"
            prompt_source = "default"
            try:
                prompt = self.get_prompt_template(
                    "timeline_extraction",
                    db=db,
                    filename=filename,
                    file_type=file_type,
                    text=text[:MAX_TEXT_CHARS],
                    char_limit=MAX_TEXT_CHARS,
                    categories=categories_str,
                )
                prompt_source = self.last_prompt_source
            except Exception as render_exc:
                logger.error(
                    "AI prompt rendering failed: exception_type=%s message=%s",
                    type(render_exc).__name__,
                    render_exc,
                )
                raise

            logger.info(
                "ai_summary_prompt_used prompt_type=%s provider_used=%s prompt_source=%s prompt_length=%s",
                "timeline_extraction",
                openai_client_service.selected_provider_name,
                prompt_source,
                len(prompt),
            )
            ai_calls += 1
            active_template = get_prompt_for_purpose(db, "timeline_extraction") if db is not None else None
            if active_template is not None and prompt_source == "admin":
                result = run_prompt_with_fallback(active_template, f"{DOCUMENT_ANALYSIS_SYSTEM}\n\n{prompt}", db, None)
                content = result["output"]
            else:
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
            analysis, parse_retry_used, degraded_output = self._parse_and_normalize(content, filename=filename)
            if parse_retry_used:
                ai_calls += 1
            duration_ms = round((time.perf_counter() - analyze_start) * 1000, 2)
            provider_name = openai_client_service.selected_provider_name
            logger.info(
                "ai_analysis_complete filename=%s timeline_event_count=%s ai_call_count=%s duration_ms=%s parse_retry_used=%s provider=%s model=%s",
                filename,
                len(analysis.get("timeline_events", [])),
                ai_calls,
                duration_ms,
                parse_retry_used,
                provider_name,
                settings.OPENAI_MODEL,
            )
            summary = (analysis.get("summary") or "").strip()
            if not summary:
                raise AIAnalysisError("AI enrichment failed: summary missing from model response.")
            analysis["json_parse_retry_used"] = parse_retry_used
            analysis["ai_analysis_degraded"] = degraded_output
            analysis["ai_call_count"] = ai_calls
            analysis["ai_provider"] = provider_name
            analysis["ai_model"] = settings.OPENAI_MODEL
            analysis["ai_duration_ms"] = duration_ms
            analysis["prompt_source"] = prompt_source
            analysis["admin_prompt_invalid_fallback"] = bool(self.last_prompt_invalid)
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
        categories: str = "none yet",
    ) -> str:
        self.last_prompt_source = "default"
        self.last_prompt_invalid = False
        default_prompt = self._get_default_prompt(
            prompt_type, filename, file_type, text, char_limit, categories
        )
        if db is None:
            return default_prompt
        # A DB-stored template may contain the same {placeholder} tokens as the
        # default template. Render them so the model receives real values, not
        # literal brace strings.
        raw = get_active_prompt_content(db, prompt_type, default_prompt)
        if raw is default_prompt:
            return default_prompt
        rendered = self._render_db_prompt(raw, filename, file_type, text, char_limit, categories)
        if self._is_valid_analysis_prompt(rendered):
            self.last_prompt_source = "admin"
            return rendered
        self.last_prompt_invalid = True
        logger.warning(
            "ai_prompt_template_invalid prompt_type=%s prompt_source=admin prompt_length=%s fallback_source=default",
            prompt_type,
            len(rendered),
        )
        return default_prompt

    def _is_valid_analysis_prompt(self, prompt: str) -> bool:
        compact = (prompt or "").strip().lower()
        if not compact:
            return False
        return all(token in compact for token in _ANALYSIS_REQUIRED_PROMPT_TOKENS)

    def _get_default_prompt(
        self,
        prompt_type: str,
        filename: str,
        file_type: str,
        text: str,
        char_limit: int,
        categories: str = "none yet",
    ) -> str:
        if prompt_type == "timeline_extraction":
            return build_default_summary_prompt(
                filename=filename,
                file_type=file_type,
                char_limit=char_limit,
                text=text,
            )
        raise AIAnalysisError(f"AI enrichment failed: unsupported prompt type '{prompt_type}'.")

    def _render_db_prompt(
        self,
        template: str,
        filename: str,
        file_type: str,
        text: str,
        char_limit: int,
        categories: str,
    ) -> str:
        """Substitute known placeholders in an admin-supplied prompt template."""
        replacements = {
            "{filename}": filename,
            "{file_type}": file_type,
            "{char_limit}": str(char_limit),
            "{text}": text,
            "{categories}": categories,
        }
        result = template
        for token, value in replacements.items():
            result = result.replace(token, value)
        return result

    def _parse_and_normalize(self, content: str, *, filename: str) -> tuple[Dict[str, Any], bool, bool]:
        try:
            analysis = self._normalize_analysis(self._parse_json(content))
            logger.info("ai_summary_parse_success filename=%s parse_success=true", filename)
            return analysis, False, False
        except AIAnalysisError:
            logger.warning("ai_summary_parse_failure filename=%s parse_success=false", filename)
            retry_content = self._retry_json_only(content)
            if retry_content is not None:
                try:
                    analysis = self._normalize_analysis(self._parse_json(retry_content))
                    logger.info("ai_summary_parse_success filename=%s parse_success=true retry=true", filename)
                    return analysis, True, False
                except AIAnalysisError:
                    logger.warning("ai_summary_parse_failure filename=%s parse_success=false retry=true", filename)

            fallback_summary = (content or "").strip()[:500]
            return self._normalize_analysis({"summary": fallback_summary, "timeline_events": [], "relationships": []}), True, True

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
            derived_title = self._derive_timeline_title(title=title, description=description, date_value=date_value, start_value=start_value, end_value=end_value)
            output.append(
                {
                    "title": derived_title,
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


    def _derive_timeline_title(self, *, title: Any, description: Any, date_value: Optional[str], start_value: Optional[str], end_value: Optional[str]) -> str:
        candidate = str(title or "").strip()
        if candidate and candidate.lower() != "untitled event":
            return candidate
        desc = re.sub(r"\s+", " ", str(description or "").strip())
        if desc:
            words = desc.split()
            snippet = " ".join(words[:8]).strip(" ,.;:-")
            if snippet:
                return snippet[:96]
        if date_value:
            return f"Event on {date_value}"
        if start_value and end_value:
            return f"Event from {start_value} to {end_value}"
        if start_value:
            return f"Event starting {start_value}"
        return "Document event"

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
