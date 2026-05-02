import uuid

from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.document import Document
from app.models.user import User
from app.services.auth import auth_service


def _user(email: str) -> User:
    return User(
        id=uuid.uuid4(),
        email=email,
        password_hash=auth_service.hash_password("password123"),
        display_name=email,
        is_active=True,
        role="editor",
    )


def _doc(user_id, title: str) -> Document:
    return Document(
        id=uuid.uuid4(),
        filename=f"{title}.pdf",
        original_path=f"/tmp/{title}.pdf",
        file_type="pdf",
        file_size=100,
        mime_type="application/pdf",
        processing_status="completed",
        source="upload",
        entities={"timeline_events": [{"title": title, "date": "2026-06-01", "confidence": 0.9}]},
        action_items=[],
        user_id=user_id,
    )


def test_timeline_endpoint_scopes_to_current_user(db):
    owner = _user("owner@example.com")
    other = _user("other@example.com")
    db.add_all([owner, other])
    db.commit()

    owner_doc = _doc(owner.id, "Owner event")
    other_doc = _doc(other.id, "Other event")
    db.add_all([owner_doc, other_doc])
    db.commit()

    def override_db():
        yield db

    def override_user():
        return owner

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user

    with TestClient(app) as client:
        response = client.get("/api/v1/search/timeline")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_documents"] == 1
    assert payload["total_events"] == 1
    assert payload["events"][0]["title"] == "Owner event"


def test_timeline_excludes_archived_and_deleted_documents(db):
    owner = _user("owner2@example.com")
    db.add(owner)
    db.commit()

    active = _doc(owner.id, "Active event")
    archived = _doc(owner.id, "Archived event")
    archived.is_archived = True
    deleted = _doc(owner.id, "Deleted event")
    db.add_all([active, archived, deleted])
    db.commit()
    db.delete(deleted)
    db.commit()

    def override_db():
        yield db

    def override_user():
        return owner

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = override_user

    with TestClient(app) as client:
        response = client.get("/api/v1/search/timeline")

    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    titles = [event["title"] for event in payload["events"]]
    assert "Active event" in titles
    assert "Archived event" not in titles
    assert "Deleted event" not in titles
