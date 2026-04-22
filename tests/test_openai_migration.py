from app.config import Settings


def test_openai_defaults_present():
    settings = Settings()

    assert settings.OPENAI_MODEL == "gpt-4o-mini"
    assert settings.OPENAI_EMBEDDING_MODEL == "text-embedding-3-small"
    assert settings.OPENAI_API_KEY == ""
