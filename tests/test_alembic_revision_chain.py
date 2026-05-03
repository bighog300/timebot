from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


EXPECTED_REVISION = "20260502_0021_add_subscription_admin_fields"


def _load_migration(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_subscription_admin_fields_revision_metadata_is_consistent():
    text = _load_migration("migrations/versions/20260502_0021_add_subscription_admin_fields.py")
    assert 'Revision ID: 20260502_0021_add_subscription_admin_fields' in text
    assert 'Revises: 20260502_0020' in text
    assert 'revision = "20260502_0021_add_subscription_admin_fields"' in text
    assert 'down_revision = "20260502_0020"' in text


def test_prompt_template_provider_fields_revises_subscription_admin_fields_revision():
    text = _load_migration("migrations/versions/20260503_0022_prompt_template_provider_fields.py")
    assert f"Revises: {EXPECTED_REVISION}" in text
    assert f'down_revision = "{EXPECTED_REVISION}"' in text
    assert 'Revises: 20260502_0021\n' not in text
    assert 'down_revision = "20260502_0021"' not in text


def test_alembic_has_single_head():
    config = Config("alembic.ini")
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    assert len(heads) == 1, f"Expected one alembic head, found {heads}"
