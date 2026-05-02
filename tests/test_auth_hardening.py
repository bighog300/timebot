import pytest

from app.main import _sanitize_headers_for_log, _validate_auth_secret_for_environment


def test_validate_auth_secret_allows_default_outside_production(monkeypatch):
    monkeypatch.setattr("app.main.settings.APP_ENV", "development")
    monkeypatch.setattr("app.main.settings.AUTH_SECRET_KEY", "dev-insecure-change-me")
    _validate_auth_secret_for_environment()


def test_validate_auth_secret_rejects_default_in_production(monkeypatch):
    monkeypatch.setattr("app.main.settings.APP_ENV", "production")
    monkeypatch.setattr("app.main.settings.AUTH_SECRET_KEY", "dev-insecure-change-me")
    with pytest.raises(RuntimeError, match="AUTH_SECRET_KEY"):
        _validate_auth_secret_for_environment()


def test_validate_auth_secret_rejects_missing_in_prod_alias(monkeypatch):
    monkeypatch.setattr("app.main.settings.APP_ENV", "prod")
    monkeypatch.setattr("app.main.settings.AUTH_SECRET_KEY", "")
    with pytest.raises(RuntimeError, match="AUTH_SECRET_KEY"):
        _validate_auth_secret_for_environment()


@pytest.mark.parametrize("app_env", ["production", "prod", "staging"])
@pytest.mark.parametrize("placeholder", ["replace-me", "change-me", "your-secret-key", "secret"])
def test_validate_auth_secret_rejects_known_placeholders_in_production_like(monkeypatch, app_env, placeholder):
    monkeypatch.setattr("app.main.settings.APP_ENV", app_env)
    monkeypatch.setattr("app.main.settings.AUTH_SECRET_KEY", placeholder)
    with pytest.raises(RuntimeError, match="AUTH_SECRET_KEY"):
        _validate_auth_secret_for_environment()


@pytest.mark.parametrize("app_env", ["production", "prod", "staging"])
def test_validate_auth_secret_accepts_strong_non_placeholder_in_production_like(monkeypatch, app_env):
    monkeypatch.setattr("app.main.settings.APP_ENV", app_env)
    monkeypatch.setattr("app.main.settings.AUTH_SECRET_KEY", "tB0t-2026-strong-7M7_jwt_signing_key")
    _validate_auth_secret_for_environment()


def test_validate_auth_secret_treats_staging_alias_case_insensitively(monkeypatch):
    monkeypatch.setattr("app.main.settings.APP_ENV", " StAgInG ")
    monkeypatch.setattr("app.main.settings.AUTH_SECRET_KEY", " default ")
    with pytest.raises(RuntimeError, match="AUTH_SECRET_KEY"):
        _validate_auth_secret_for_environment()


def test_validate_auth_secret_allows_placeholder_in_non_production_alias(monkeypatch):
    monkeypatch.setattr("app.main.settings.APP_ENV", "qa")
    monkeypatch.setattr("app.main.settings.AUTH_SECRET_KEY", "secret")
    _validate_auth_secret_for_environment()


def test_sanitize_headers_redacts_authorization_token():
    sanitized = _sanitize_headers_for_log({"Authorization": "Bearer secret-token", "X-Test": "ok"})
    assert sanitized["Authorization"] == "[redacted]"
    assert sanitized["X-Test"] == "ok"
