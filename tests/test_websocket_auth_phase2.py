import uuid

import pytest
from starlette.websockets import WebSocketDisconnect

from app.models.document import Document
from app.models.user import User
from app.services.auth import auth_service


def _create_document(db, user):
    doc = Document(
        id=uuid.uuid4(), filename="ws-test.pdf", original_path="/tmp/ws-test.pdf", file_type="pdf", file_size=1,
        mime_type="application/pdf", processing_status="completed", source="upload", user_id=user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _assert_ws_rejected(client, path: str):
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(path) as websocket:
            websocket.send_text("ping")
            websocket.receive_text()


def test_ws_document_rejects_missing_token(client, sample_document, monkeypatch, db):
    monkeypatch.setattr("app.api.v1.websocket._get_ws_db", lambda: db)
    _assert_ws_rejected(client, f"/api/v1/ws/documents/{sample_document.id}")


def test_ws_document_rejects_invalid_token(client, sample_document, monkeypatch, db):
    monkeypatch.setattr("app.api.v1.websocket._get_ws_db", lambda: db)
    _assert_ws_rejected(client, f"/api/v1/ws/documents/{sample_document.id}?token=not-a-token")


def test_ws_document_accepts_valid_token_for_owner(client, sample_document, auth_token, monkeypatch, db):
    monkeypatch.setattr("app.api.v1.websocket._get_ws_db", lambda: db)
    with client.websocket_connect(f"/api/v1/ws/documents/{sample_document.id}?token={auth_token}") as websocket:
        websocket.send_text("ping")


def test_ws_document_rejects_valid_token_for_other_user(client, db, test_user, monkeypatch):
    monkeypatch.setattr("app.api.v1.websocket._get_ws_db", lambda: db)
    owner = User(id=uuid.uuid4(), email="owner@example.com", password_hash=auth_service.hash_password("pw"), display_name="Owner", is_active=True, role="editor")
    db.add(owner)
    db.commit()
    owned_doc = _create_document(db, owner)

    token = auth_service.create_access_token(test_user)
    _assert_ws_rejected(client, f"/api/v1/ws/documents/{owned_doc.id}?token={token}")


def test_ws_all_rejects_non_admin(client, auth_token, monkeypatch, db):
    monkeypatch.setattr("app.api.v1.websocket._get_ws_db", lambda: db)
    _assert_ws_rejected(client, f"/api/v1/ws/all?token={auth_token}")


def test_ws_all_accepts_admin(client, db, test_user, monkeypatch):
    monkeypatch.setattr("app.api.v1.websocket._get_ws_db", lambda: db)
    test_user.role = "admin"
    db.commit()
    admin_token = auth_service.create_access_token(test_user)
    with client.websocket_connect(f"/api/v1/ws/all?token={admin_token}") as websocket:
        websocket.send_text("ping")
