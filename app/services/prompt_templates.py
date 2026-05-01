from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.prompt_template import PromptTemplate

PROMPT_TYPES = {"chat", "retrieval", "report", "timeline_extraction", "relationship_detection"}


def get_active_prompt_content(db: Session, prompt_type: str, default_content: str) -> str:
    if prompt_type not in PROMPT_TYPES:
        return default_content
    row = (
        db.query(PromptTemplate)
        .filter(PromptTemplate.type == prompt_type, PromptTemplate.is_active.is_(True))
        .order_by(PromptTemplate.updated_at.desc())
        .first()
    )
    return row.content if row else default_content


def activate_prompt_template(db: Session, template: PromptTemplate) -> PromptTemplate:
    (
        db.query(PromptTemplate)
        .filter(PromptTemplate.type == template.type, PromptTemplate.id != template.id, PromptTemplate.is_active.is_(True))
        .update({PromptTemplate.is_active: False}, synchronize_session=False)
    )
    template.is_active = True
    db.add(template)
    return template
