from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.billing import Plan


class FakeQuery:
    def __init__(self, first_result=None):
        self._first = first_result

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._first

    def order_by(self, *_args, **_kwargs):
        return self


class FakeDB:
    def __init__(self, first_result=None):
        self.first_result = first_result
        self.added = []

    def query(self, model):
        if model is Plan:
            return FakeQuery(SimpleNamespace(id=uuid4(), slug="free", is_active=True))
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
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as client:
        response = client.post('/api/v1/auth/register', json={'email': 'new@example.com', 'password': 'password123', 'display_name': 'New'})

    app.dependency_overrides.clear()
    assert response.status_code == 201
    assert response.json()['user']['email'] == 'new@example.com'


def test_register_duplicate_email_returns_400():
    db = FakeDB(first_result=SimpleNamespace(id=uuid4(), email='dup@example.com'))
    app.dependency_overrides[get_db] = lambda: db

    with TestClient(app) as client:
        response = client.post('/api/v1/auth/register', json={'email': 'dup@example.com', 'password': 'password123', 'display_name': 'Dup'})

    app.dependency_overrides.clear()
    assert response.status_code == 400


def test_login_success_and_invalid_credentials(monkeypatch):
    user = SimpleNamespace(id=uuid4(), email='user@example.com', display_name='User', is_active=True, created_at=datetime.now(timezone.utc))
    db = FakeDB()
    app.dependency_overrides[get_db] = lambda: db

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
    app.dependency_overrides[get_db] = lambda: SimpleNamespace()

    from app.api.v1.documents import crud_document
    original = crud_document.get_review_queue
    crud_document.get_review_queue = lambda *_args, **_kwargs: []
    with TestClient(app) as client:
        allowed = client.get('/api/v1/documents/review-queue')
    crud_document.get_review_queue = original
    app.dependency_overrides.clear()

    assert allowed.status_code == 200


def test_inactive_user_cannot_log_in(client, test_user, db):
    test_user.is_active = False
    db.commit()
    response = client.post('/api/v1/auth/login', json={'email': test_user.email, 'password': 'password123'})
    assert response.status_code == 403


def test_invite_accept_success_and_states(client, test_user, db):
    from app.models.user import UserInvite, User
    import hashlib, secrets
    test_user.role = 'admin'; db.commit()
    token = secrets.token_urlsafe(16)
    invite = UserInvite(email='accept@example.com', role='editor', token_hash=hashlib.sha256(token.encode('utf-8')).hexdigest(), invited_by_user_id=test_user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=1))
    db.add(invite); db.commit()
    resp = client.post('/api/v1/auth/invites/accept', json={'token': token, 'password': 'password123', 'display_name': 'Accepted'})
    assert resp.status_code == 200
    db.refresh(invite)
    assert invite.accepted_at is not None
    assert db.query(User).filter(User.email == 'accept@example.com').first() is not None


def test_expired_and_canceled_invite_rejected(client, test_user, db):
    from app.models.user import UserInvite
    import hashlib, secrets
    test_user.role = 'admin'; db.commit()
    t1 = secrets.token_urlsafe(16)
    expired = UserInvite(email='expired@example.com', role='viewer', token_hash=hashlib.sha256(t1.encode('utf-8')).hexdigest(), invited_by_user_id=test_user.id, expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    t2 = secrets.token_urlsafe(16)
    canceled = UserInvite(email='canceled@example.com', role='viewer', token_hash=hashlib.sha256(t2.encode('utf-8')).hexdigest(), invited_by_user_id=test_user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=1), canceled_at=datetime.now(timezone.utc))
    db.add_all([expired, canceled]); db.commit()
    assert client.post('/api/v1/auth/invites/accept', json={'token': t1, 'password': 'password123', 'display_name': 'X'}).status_code == 400
    assert client.post('/api/v1/auth/invites/accept', json={'token': t2, 'password': 'password123', 'display_name': 'Y'}).status_code == 400


def test_duplicate_email_invite_and_accept_rejected(client, test_user, db):
    from app.models.user import UserInvite
    import hashlib, secrets
    test_user.role = 'admin'; db.commit()
    assert client.post('/api/v1/admin/users/invite', json={'email': test_user.email, 'role': 'viewer', 'expires_in_days': 7}).status_code == 400
    token = secrets.token_urlsafe(16)
    invite = UserInvite(email=test_user.email, role='viewer', token_hash=hashlib.sha256(token.encode('utf-8')).hexdigest(), invited_by_user_id=test_user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=1))
    db.add(invite); db.commit()
    assert client.post('/api/v1/auth/invites/accept', json={'token': token, 'password': 'password123', 'display_name': 'Dup'}).status_code == 400
