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


def test_validate_auth_secret_rejects_missing_in_production(monkeypatch):
    monkeypatch.setattr("app.main.settings.APP_ENV", "production")
    monkeypatch.setattr("app.main.settings.AUTH_SECRET_KEY", "")
    with pytest.raises(RuntimeError, match="AUTH_SECRET_KEY"):
        _validate_auth_secret_for_environment()


def test_sanitize_headers_redacts_authorization_token():
    sanitized = _sanitize_headers_for_log({"Authorization": "Bearer secret-token", "X-Test": "ok"})
    assert sanitized["Authorization"] == "[redacted]"
    assert sanitized["X-Test"] == "ok"
