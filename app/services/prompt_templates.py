from __future__ import annotations

import logging
import time

from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.orm import Session

from app.models.prompt_template import PromptTemplate
from app.services.default_prompt_templates import DEFAULT_PROMPT_TEMPLATES

PROMPT_TYPES = {"chat", "retrieval", "report", "timeline_extraction", "relationship_detection"}

logger = logging.getLogger(__name__)


def get_active_prompt_content(db: Session, prompt_type: str, default_content: str) -> str:
    if prompt_type not in PROMPT_TYPES:
        return default_content
    row = (
        db.query(PromptTemplate)
        .filter(PromptTemplate.type == prompt_type, PromptTemplate.is_active.is_(True))
        .order_by(PromptTemplate.updated_at.desc())
        .first()
    )
    if not row:
        return default_content
    content = row.content if isinstance(row.content, str) else ""
    return content if content.strip() else default_content


def get_active_prompt_template(db: Session, prompt_type: str) -> PromptTemplate | None:
    return get_prompt_for_purpose(db, prompt_type)


def activate_prompt_template(db: Session, template: PromptTemplate) -> PromptTemplate:
    (
        db.query(PromptTemplate)
        .filter(PromptTemplate.type == template.type, PromptTemplate.id != template.id, PromptTemplate.is_active.is_(True))
        .update({PromptTemplate.is_active: False}, synchronize_session=False)
    )
    template.is_active = True
    db.add(template)
    return template


def clear_default_for_purpose(db: Session, *, prompt_type: str, exclude_id: str | None = None) -> None:
    query = db.query(PromptTemplate).filter(
        PromptTemplate.type == prompt_type,
        PromptTemplate.is_default.is_(True),
    )
    if exclude_id is not None:
        query = query.filter(PromptTemplate.id != exclude_id)
    query.update({PromptTemplate.is_default: False}, synchronize_session=False)


def get_prompt_for_purpose(db: Session, prompt_type: str) -> PromptTemplate | None:
    if prompt_type not in PROMPT_TYPES:
        return None

    default_prompt = (
        db.query(PromptTemplate)
        .filter(
            PromptTemplate.type == prompt_type,
            PromptTemplate.enabled.is_(True),
            PromptTemplate.is_default.is_(True),
        )
        .order_by(
            PromptTemplate.is_active.desc(),
            PromptTemplate.updated_at.desc(),
            PromptTemplate.created_at.desc(),
        )
        .first()
    )
    if default_prompt:
        return default_prompt

    return (
        db.query(PromptTemplate)
        .filter(
            PromptTemplate.type == prompt_type,
            PromptTemplate.enabled.is_(True),
        )
        .order_by(
            PromptTemplate.is_active.desc(),
            PromptTemplate.version.desc(),
            PromptTemplate.created_at.desc(),
            PromptTemplate.updated_at.desc(),
        )
        .first()
    )



def seed_default_prompt_templates(db: Session) -> int:
    created = 0
    try:
        for default in DEFAULT_PROMPT_TEMPLATES:
            exists = (
                db.query(PromptTemplate.id)
                .filter(PromptTemplate.type == default.type)
                .first()
            )
            if exists:
                continue
            db.add(PromptTemplate(
                type=default.type,
                name=default.name,
                content=default.content,
                version=default.version,
                is_active=default.is_active,
            ))
            created += 1
        if created:
            db.commit()
    except (ProgrammingError, OperationalError):
        db.rollback()
        logger.warning("Skipping default prompt template seed because migrations are not applied")
        return 0
    return created


def normalize_llm_error(error: Exception) -> str:
    message = f"{type(error).__name__}: {error}"
    redacted = message
    for marker in ("sk-", "AIza", "api_key", "authorization", "bearer "):
        if marker.lower() in redacted.lower():
            return f"{type(error).__name__}: request failed"
    return redacted[:300]


def run_prompt_with_fallback(prompt_template: PromptTemplate, user_input: str, db: Session | None, user_id: str | None = None) -> dict:
    from app.services.openai_client import openai_client_service

    request_payload = {
        "model": prompt_template.model,
        "temperature": prompt_template.temperature,
        "max_tokens": prompt_template.max_tokens,
        "top_p": prompt_template.top_p,
        "messages": [{"role": "system", "content": "You are Timebot."}, {"role": "user", "content": user_input}],
    }

    started = time.perf_counter()
    primary_error = None
    try:
        response = openai_client_service.generate_completion_for_provider(prompt_template.provider, request_payload)
        return {
            "output": openai_client_service.extract_response_text(response),
            "provider_used": prompt_template.provider,
            "model_used": prompt_template.model,
            "fallback_used": False,
            "primary_error": None,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "token_usage": getattr(getattr(response, "usage", None), "total_tokens", None),
        }
    except Exception as exc:
        primary_error = normalize_llm_error(exc)

    if not prompt_template.fallback_enabled:
        raise RuntimeError(primary_error)

    fallback_provider = prompt_template.fallback_provider or prompt_template.provider
    fallback_model = prompt_template.fallback_model or prompt_template.model
    fallback_payload = {**request_payload, "model": fallback_model}
    try:
        response = openai_client_service.generate_completion_for_provider(fallback_provider, fallback_payload)
        return {
            "output": openai_client_service.extract_response_text(response),
            "provider_used": fallback_provider,
            "model_used": fallback_model,
            "fallback_used": True,
            "primary_error": primary_error,
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "token_usage": getattr(getattr(response, "usage", None), "total_tokens", None),
        }
    except Exception as fallback_exc:
        raise RuntimeError(f"primary={primary_error}; fallback={normalize_llm_error(fallback_exc)}") from fallback_exc
