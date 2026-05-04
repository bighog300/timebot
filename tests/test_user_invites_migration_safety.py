from pathlib import Path


def test_user_invites_safety_migration_adds_auth_provider_and_google_subject():
    path = Path('migrations/versions/20260504_0039_user_invites_auth_provider_safety.py')
    text = path.read_text(encoding='utf-8')

    assert 'if "auth_provider" not in cols' in text
    assert 'sa.Column("auth_provider", sa.String(length=32), nullable=False, server_default="local")' in text
    assert 'if "google_subject" not in cols' in text
