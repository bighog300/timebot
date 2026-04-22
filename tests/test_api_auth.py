from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.main import app


class FakeQuery:
    def __init__(self, first_result=None):
        self._first = first_result

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._first


class FakeDB:
    def __init__(self, first_result=None):
        self.first_result = first_result
        self.added = []

    def query(self, _model):
        return FakeQuery(self.first_result)

    def add(self, item):
        self.added.append(item)

    def commit(self):
        return None

    def refresh(self, item):
        if not getattr(item, 'id', None):
            item.id = uuid4()
        if not getattr(item, 'created_at', None):
            item.created_at = datetime.now(timezone.utc)


def test_register_success():
    db = FakeDB(first_result=None)
    app.dependency_overrides[get_db] = lambda: iter([db])

    with TestClient(app) as client:
        response = client.post('/api/v1/auth/register', json={'email': 'new@example.com', 'password': 'password123', 'display_name': 'New'})

    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json()['user']['email'] == 'new@example.com'


def test_register_duplicate_email_returns_400():
    db = FakeDB(first_result=SimpleNamespace(id=uuid4(), email='dup@example.com'))
    app.dependency_overrides[get_db] = lambda: iter([db])

    with TestClient(app) as client:
        response = client.post('/api/v1/auth/register', json={'email': 'dup@example.com', 'password': 'password123', 'display_name': 'Dup'})

    app.dependency_overrides.clear()
    assert response.status_code == 400


def test_login_success_and_invalid_credentials(monkeypatch):
    user = SimpleNamespace(id=uuid4(), email='user@example.com', display_name='User', is_active=True, created_at=datetime.now(timezone.utc))
    db = FakeDB()
    app.dependency_overrides[get_db] = lambda: iter([db])

    monkeypatch.setattr('app.api.v1.auth.auth_service.authenticate_user', lambda *_args, **_kwargs: user)
    with TestClient(app) as client:
        ok = client.post('/api/v1/auth/login', json={'email': 'user@example.com', 'password': 'password123'})
    assert ok.status_code == 200

    monkeypatch.setattr('app.api.v1.auth.auth_service.authenticate_user', lambda *_args, **_kwargs: None)
    with TestClient(app) as client:
        bad = client.post('/api/v1/auth/login', json={'email': 'user@example.com', 'password': 'bad'})
    app.dependency_overrides.clear()
    assert bad.status_code == 401


def test_auth_me():
    user = SimpleNamespace(id=uuid4(), email='me@example.com', display_name='Me', is_active=True, created_at=datetime.now(timezone.utc))
    app.dependency_overrides[get_current_user] = lambda: user

    with TestClient(app) as client:
        response = client.get('/api/v1/auth/me')

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()['email'] == 'me@example.com'


def test_protected_route_requires_auth_and_allows_when_authenticated():
    with TestClient(app) as client:
        denied = client.get('/api/v1/documents/review-queue')
    assert denied.status_code == 401

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), email='ok@example.com')
    app.dependency_overrides[get_db] = lambda: iter([SimpleNamespace()])

    from app.api.v1.documents import crud_document
    original = crud_document.get_review_queue
    crud_document.get_review_queue = lambda *_args, **_kwargs: []
    with TestClient(app) as client:
        allowed = client.get('/api/v1/documents/review-queue')
    crud_document.get_review_queue = original
    app.dependency_overrides.clear()

    assert allowed.status_code == 200
