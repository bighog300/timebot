from app.models.prompt_template import PromptTemplate
from app.services.prompt_templates import get_prompt_for_purpose


def test_get_prompt_for_purpose_prefers_enabled_default(db):
    newer_non_default = PromptTemplate(type='chat', name='n1', content='new', version=2, enabled=True, is_default=False)
    default_prompt = PromptTemplate(type='chat', name='d1', content='default', version=1, enabled=True, is_default=True)
    db.add_all([default_prompt, newer_non_default])
    db.commit()

    selected = get_prompt_for_purpose(db, 'chat')
    assert selected is not None
    assert selected.id == default_prompt.id


def test_get_prompt_for_purpose_skips_disabled_default(db):
    disabled_default = PromptTemplate(type='report', name='d1', content='default', version=1, enabled=False, is_default=True)
    enabled_non_default = PromptTemplate(type='report', name='n1', content='enabled', version=2, enabled=True, is_default=False)
    db.add_all([disabled_default, enabled_non_default])
    db.commit()

    selected = get_prompt_for_purpose(db, 'report')
    assert selected is not None
    assert selected.id == enabled_non_default.id


def test_get_prompt_for_purpose_falls_back_to_newest_enabled(db):
    older = PromptTemplate(type='retrieval', name='old', content='old', version=1, enabled=True, is_default=False)
    newer = PromptTemplate(type='retrieval', name='new', content='new', version=2, enabled=True, is_default=False)
    db.add_all([older, newer])
    db.commit()

    selected = get_prompt_for_purpose(db, 'retrieval')
    assert selected is not None
    assert selected.id == newer.id


def test_get_prompt_for_purpose_never_returns_disabled(db):
    only_disabled = PromptTemplate(type='timeline_extraction', name='off', content='off', version=1, enabled=False, is_default=True)
    db.add(only_disabled)
    db.commit()

    selected = get_prompt_for_purpose(db, 'timeline_extraction')
    assert selected is None
