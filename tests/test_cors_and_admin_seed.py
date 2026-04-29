from fastapi.testclient import TestClient

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


def test_seed_initial_admin_is_idempotent(db, monkeypatch):
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_EMAIL', 'admin@example.com')
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_PASSWORD', 'password12345')
    monkeypatch.setattr('app.services.admin_seed.settings.INITIAL_ADMIN_NAME', 'Admin User')

    assert seed_initial_admin(db) is True
    assert seed_initial_admin(db) is True

    users = db.query(User).filter(User.email == 'admin@example.com').all()
    assert len(users) == 1
    assert users[0].role == 'editor'
