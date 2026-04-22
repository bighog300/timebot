from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.api.deps import get_current_user, get_db
from app.main import app
from app.services.connectors.service import ConnectorService
from app.services.connectors.token_crypto import connector_token_crypto


class FakeQuery:
    def __init__(self, items):
        self.items = items

    def filter(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def limit(self, n):
        return FakeQuery(self.items[:n])

    def all(self):
        return self.items

    def first(self):
        return self.items[0] if self.items else None

    def count(self):
        return len(self.items)


class FakeDB:
    def __init__(self):
        self.connections = []
        self.documents = []
        self.logs = []

    def query(self, model):
        name = getattr(model, "__name__", "")
        if name == "Connection":
            return FakeQuery(self.connections)
        if name == "Document":
            return FakeQuery(self.documents)
        if name == "SyncLog":
            return FakeQuery(self.logs)
        return FakeQuery([])

    def add(self, item):
        if getattr(item, "__tablename__", "") == "connections" and item not in self.connections:
            if not getattr(item, "id", None):
                item.id = uuid4()
            self.connections.append(item)
        if getattr(item, "__tablename__", "") == "documents" and item not in self.documents:
            if not getattr(item, "id", None):
                item.id = uuid4()
            self.documents.append(item)
        if getattr(item, "__tablename__", "") == "sync_logs" and item not in self.logs:
            if not getattr(item, "id", None):
                item.id = uuid4()
            self.logs.append(item)

    def commit(self):
        return None

    def refresh(self, _item):
        return None


def _set_encryption_key(key: str):
    settings.CONNECTOR_TOKEN_ENCRYPTION_KEY = key
    connector_token_crypto._fernet = None


def test_connection_list_initializes_google_drive_only():
    db = FakeDB()
    service = ConnectorService()

    user = SimpleNamespace(id=uuid4(), email="u@example.com")
    rows = service.list_connections(db, user)

    assert len(rows) == 1
    assert rows[0].type == "gdrive"


def test_oauth_callback_happy_path(monkeypatch):
    _set_encryption_key("Q6iMLfJ8sNy0DV1N7s9fM2NnV7Jvn0BLPw6EB0fXxHg=")
    db = FakeDB()
    service = ConnectorService()

    monkeypatch.setattr(
        "app.services.connectors.google_drive.GoogleDriveProvider.build_authorization_url",
        lambda self, state: SimpleNamespace(authorization_url="https://example.test/auth", state=state),
    )
    user = SimpleNamespace(id=uuid4(), email="u@example.com")
    start = service.start_oauth(db, "gdrive", user)

    monkeypatch.setattr(
        "app.services.connectors.google_drive.GoogleDriveProvider.exchange_code_for_tokens",
        lambda self, code: SimpleNamespace(
            account_email="user@example.com",
            account_id="acct-123",
            access_token="token-1",
            refresh_token="refresh-1",
            expires_at=datetime.now(timezone.utc),
            scopes=["scope-a"],
        ),
    )

    conn = service.handle_callback(db, "gdrive", code="abc", state=start["state"], user=user)
    assert conn.status == "connected"
    assert conn.access_token != "token-1"
    assert conn.access_token.startswith("enc:v1:")
    assert connector_token_crypto.decrypt(conn.access_token) == "token-1"
    assert conn.email == "user@example.com"


def test_sync_happy_path_and_failure_persistence(monkeypatch):
    _set_encryption_key("Q6iMLfJ8sNy0DV1N7s9fM2NnV7Jvn0BLPw6EB0fXxHg=")
    db = FakeDB()
    service = ConnectorService()
    user = SimpleNamespace(id=uuid4(), email="u@example.com")
    conn = service._get_or_create(db, "gdrive", user)
    conn.access_token = connector_token_crypto.encrypt("token")

    monkeypatch.setattr(
        "app.services.connectors.google_drive.GoogleDriveProvider.list_remote_files",
        lambda self, access_token: [
            {"id": "f1", "name": "doc1.pdf", "mimeType": "application/pdf", "size": "100"},
            {"id": "f2", "name": "sheet", "mimeType": "application/vnd.google-apps.spreadsheet", "size": "50"},
        ],
    )

    synced_conn, _log, result = service.sync_connection(db, "gdrive", user)
    assert result.files_seen == 2
    assert synced_conn.last_sync_status in {"success", "partial"}

    monkeypatch.setattr(
        "app.services.connectors.google_drive.GoogleDriveProvider.list_remote_files",
        lambda self, access_token: (_ for _ in ()).throw(RuntimeError("google unavailable")),
    )

    failed_conn, failed_log, _ = service.sync_connection(db, "gdrive", user)
    assert failed_conn.status == "error"
    assert "google unavailable" in (failed_conn.last_error_message or "")
    assert failed_log.status == "failed"


def test_callback_route_returns_connection(monkeypatch):
    class DummyDB:
        pass

    app.dependency_overrides[get_db] = lambda: iter([DummyDB()])
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), email="u@example.com")

    conn = SimpleNamespace(
        id=uuid4(),
        type="gdrive",
        status="connected",
        display_name="Google Drive",
        email="user@example.com",
        external_account_id="acct",
        last_sync_date=None,
        last_sync_status=None,
        last_error_message=None,
        last_error_at=None,
        sync_progress=0,
        document_count=0,
        total_size=0,
        auto_sync=True,
        sync_interval=15,
        is_authenticated=True,
    )
    monkeypatch.setattr("app.api.v1.connections.connector_service.handle_callback", lambda db, provider_type, code, state, user: conn)

    with TestClient(app) as client:
        response = client.get("/api/v1/connections/gdrive/connect/callback", params={"code": "abc", "state": "s1"})

    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["type"] == "gdrive"


def test_sync_reencrypts_legacy_plaintext_access_token(monkeypatch):
    _set_encryption_key("Q6iMLfJ8sNy0DV1N7s9fM2NnV7Jvn0BLPw6EB0fXxHg=")
    db = FakeDB()
    service = ConnectorService()
    user = SimpleNamespace(id=uuid4(), email="u@example.com")
    conn = service._get_or_create(db, "gdrive", user)
    conn.access_token = "legacy-plaintext"

    monkeypatch.setattr(
        "app.services.connectors.google_drive.GoogleDriveProvider.list_remote_files",
        lambda self, access_token: [],
    )

    synced_conn, _log, _result = service.sync_connection(db, "gdrive", user)
    assert synced_conn.access_token.startswith("enc:v1:")
    assert connector_token_crypto.decrypt(synced_conn.access_token) == "legacy-plaintext"


def test_callback_fails_when_encryption_key_missing(monkeypatch):
    _set_encryption_key("")
    db = FakeDB()
    service = ConnectorService()

    monkeypatch.setattr(
        "app.services.connectors.google_drive.GoogleDriveProvider.build_authorization_url",
        lambda self, state: SimpleNamespace(authorization_url="https://example.test/auth", state=state),
    )
    user = SimpleNamespace(id=uuid4(), email="u@example.com")
    start = service.start_oauth(db, "gdrive", user)

    monkeypatch.setattr(
        "app.services.connectors.google_drive.GoogleDriveProvider.exchange_code_for_tokens",
        lambda self, code: SimpleNamespace(
            account_email="user@example.com",
            account_id="acct-123",
            access_token="token-1",
            refresh_token="refresh-1",
            expires_at=datetime.now(timezone.utc),
            scopes=["scope-a"],
        ),
    )

    with pytest.raises(RuntimeError, match="CONNECTOR_TOKEN_ENCRYPTION_KEY"):
        service.handle_callback(db, "gdrive", code="abc", state=start["state"], user=user)
