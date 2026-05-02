from __future__ import annotations

import logging

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


def activate_prompt_template(db: Session, template: PromptTemplate) -> PromptTemplate:
    (
        db.query(PromptTemplate)
        .filter(PromptTemplate.type == template.type, PromptTemplate.id != template.id, PromptTemplate.is_active.is_(True))
        .update({PromptTemplate.is_active: False}, synchronize_session=False)
    )
    template.is_active = True
    db.add(template)
    return template



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
