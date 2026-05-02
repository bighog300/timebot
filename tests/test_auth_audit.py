import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.main import app
from app.models.document import Document
from app.models.user import User
from app.services.auth import auth_service
from app.config import settings


def _client_with_db(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_login_success_payload_hides_password_hash_and_sets_subject(db):
    password = "secret-pass-123"
    user = User(id=uuid.uuid4(), email="auth-success@example.com", password_hash=auth_service.hash_password(password), display_name="Auth User", is_active=True)
    db.add(user)
    db.commit()

    with _client_with_db(db) as client:
        response = client.post("/api/v1/auth/login", json={"email": user.email, "password": password})

    assert response.status_code == 200
    body = response.json()
    assert "password_hash" not in str(body)
    assert body["user"]["email"] == user.email
    claims = auth_service.decode_token(body["access_token"])
    assert claims["sub"] == str(user.id)


def test_login_bad_credentials_safe_error(db):
    with _client_with_db(db) as client:
        response = client.post("/api/v1/auth/login", json={"email": "missing@example.com", "password": "wrong"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_inactive_user_cannot_login(db):
    user = User(id=uuid.uuid4(), email="inactive@example.com", password_hash=auth_service.hash_password("abc12345"), display_name="Inactive", is_active=False)
    db.add(user)
    db.commit()
    with _client_with_db(db) as client:
        response = client.post("/api/v1/auth/login", json={"email": user.email, "password": "abc12345"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_me_requires_auth(db):
    with _client_with_db(db) as client:
        response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_expired_and_malformed_tokens_are_rejected(db, test_user):
    expired = jwt.encode(
        {
            "sub": str(test_user.id),
            "email": test_user.email,
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        },
        settings.AUTH_SECRET_KEY,
        algorithm=settings.AUTH_ALGORITHM,
    )

    with _client_with_db(db) as client:
        expired_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
        malformed_resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})

    assert expired_resp.status_code == 401
    assert malformed_resp.status_code == 401


def test_non_admin_rejected_from_admin_endpoint(client):
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 403


def test_user_cannot_access_another_users_document(client, db, test_user):
    other_user = User(id=uuid.uuid4(), email="other@example.com", password_hash=auth_service.hash_password("otherpass123"), display_name="Other", is_active=True)
    db.add(other_user)
    db.flush()
    document = Document(
        id=uuid.uuid4(),
        filename="other.pdf",
        original_path="/tmp/other.pdf",
        file_type="pdf",
        file_size=123,
        mime_type="application/pdf",
        processing_status="completed",
        source="upload",
        user_id=other_user.id,
    )
    db.add(document)
    db.commit()

    response = client.get(f"/api/v1/documents/{document.id}")
    assert response.status_code == 404
