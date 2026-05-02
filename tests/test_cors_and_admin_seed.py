from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy.exc import ProgrammingError

from app.config import Settings
from app.main import app
from app.models.user import User
from app.services.admin_seed import seed_initial_admin


def _preflight(client: TestClient, origin: str):
    return client.options(
        '/api/v1/auth/register',
        headers={
            'Origin': origin,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type,authorization',
        },
    )


def test_cors_preflight_localhost_origin_allowed():
    with TestClient(app) as client:
        response = _preflight(client, 'http://localhost:5174')

    assert response.status_code == 200
    assert response.headers.get('access-control-allow-origin') == 'http://localhost:5174'


def test_allowed_origins_parser_trims_and_includes_lan_origin():
    config = Settings(ALLOWED_ORIGINS=' http://localhost:5174, , http://192.168.88.212:5174  ')
    assert config.allowed_origins == ['http://localhost:5174', 'http://192.168.88.212:5174']


def test_register_login_without_openai_key(client, monkeypatch):
    monkeypatch.setattr('app.services.openai_client.settings.OPENAI_API_KEY', '')
    email = 'smoke-auth@example.com'
    password = 'password123'

    register = client.post('/api/v1/auth/register', json={'email': email, 'password': password, 'display_name': 'Smoke'})
    assert register.status_code == 201

    login = client.post('/api/v1/auth/login', json={'email': email, 'password': password})
    assert login.status_code == 200
    assert login.json().get('access_token')


def test_seed_initial_admin_skips_when_migrations_not_applied(monkeypatch, caplog):
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_EMAIL', 'admin@example.com')
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_PASSWORD', 'password12345')

    db = Mock()
    db.query.side_effect = ProgrammingError('SELECT role FROM users', {}, Exception('UndefinedColumn: column users.role does not exist'))

    assert seed_initial_admin(db) is False
    db.rollback.assert_called_once()
    assert 'Skipping initial admin seed because migrations are not applied' in caplog.text


def test_seed_initial_admin_is_idempotent_and_promotes_admin(db, monkeypatch):
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_EMAIL', 'admin@example.com')
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_PASSWORD', 'password12345')
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_NAME', 'Admin User')

    assert seed_initial_admin(db) is True
    assert seed_initial_admin(db) is True

    users = db.query(User).filter(User.email == 'admin@example.com').all()
    assert len(users) == 1
    assert users[0].role == 'admin'


def test_seed_initial_admin_does_not_overwrite_existing_password_by_default(db, monkeypatch):
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_EMAIL', 'admin2@example.com')
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_PASSWORD', 'password12345')
    monkeypatch.setattr('app.services.admin_seed.settings.RESET_INITIAL_ADMIN_PASSWORD', False)

    assert seed_initial_admin(db) is True
    user = db.query(User).filter(User.email == 'admin2@example.com').first()
    original_hash = user.password_hash

    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_PASSWORD', 'new-password-123')
    assert seed_initial_admin(db) is True

    user = db.query(User).filter(User.email == 'admin2@example.com').first()
    assert user.password_hash == original_hash


def test_seed_initial_admin_can_reset_password_in_non_production_when_flag_enabled(db, monkeypatch):
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_EMAIL', 'admin3@example.com')
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_PASSWORD', 'password12345')
    monkeypatch.setattr('app.services.admin_seed.settings.RESET_INITIAL_ADMIN_PASSWORD', False)
    monkeypatch.setattr('app.services.admin_seed.settings.APP_ENV', 'development')

    assert seed_initial_admin(db) is True
    user = db.query(User).filter(User.email == 'admin3@example.com').first()
    original_hash = user.password_hash

    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_PASSWORD', 'new-password-123')
    monkeypatch.setattr('app.services.admin_seed.settings.RESET_INITIAL_ADMIN_PASSWORD', True)

    assert seed_initial_admin(db) is True
    user = db.query(User).filter(User.email == 'admin3@example.com').first()
    assert user.password_hash != original_hash


def test_seed_initial_admin_does_not_reset_password_in_production(db, monkeypatch):
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_EMAIL', 'admin4@example.com')
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_PASSWORD', 'password12345')
    monkeypatch.setattr('app.services.admin_seed.settings.RESET_INITIAL_ADMIN_PASSWORD', False)

    assert seed_initial_admin(db) is True
    user = db.query(User).filter(User.email == 'admin4@example.com').first()
    original_hash = user.password_hash

    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_PASSWORD', 'new-password-123')
    monkeypatch.setattr('app.services.admin_seed.settings.RESET_INITIAL_ADMIN_PASSWORD', True)
    monkeypatch.setattr('app.services.admin_seed.settings.APP_ENV', 'production')

    assert seed_initial_admin(db) is True
    user = db.query(User).filter(User.email == 'admin4@example.com').first()
    assert user.password_hash == original_hash
