from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.relationships import Connection, SyncLog
from app.models.user import User
from app.services.connectors.base import SyncResult
from app.services.connectors.registry import get_provider, list_provider_types
from app.services.connectors.token_crypto import connector_token_crypto


class ConnectorService:
    """Connector management for current single-workspace deployment."""

    def _get_or_create(self, db: Session, provider_type: str, user: User) -> Connection:
        conn = db.query(Connection).filter(Connection.type == provider_type, Connection.user_id == user.id).first()
        if conn:
            return conn

        provider = get_provider(provider_type)
        conn = Connection(type=provider_type, display_name=provider.display_name, status="disconnected", user_id=user.id)
        db.add(conn)
        db.commit()
        db.refresh(conn)
        return conn

    def list_connections(self, db: Session, user: User) -> list[Connection]:
        for provider_type in list_provider_types():
            self._get_or_create(db, provider_type, user)
        return db.query(Connection).filter(Connection.user_id == user.id).order_by(Connection.type.asc()).all()

    def provider_config_status(self, provider_type: str) -> dict[str, str | bool | None]:
        provider = get_provider(provider_type)
        config_error = getattr(provider, "oauth_configuration_error", None)
        return {
            "provider_is_configured": config_error is None,
            "provider_config_error": config_error,
        }

    def start_oauth(self, db: Session, provider_type: str, user: User) -> dict:
        provider = get_provider(provider_type)
        conn = self._get_or_create(db, provider_type, user)
        state = secrets.token_urlsafe(24)
        result = provider.build_authorization_url(state=state)

        conn.oauth_state = state
        conn.oauth_state_expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        conn.status = "auth_pending"
        conn.last_error_message = None
        db.add(conn)
        db.commit()

        return {
            "provider": provider_type,
            "authorization_url": result.authorization_url,
            "state": state,
        }

    def handle_callback(self, db: Session, provider_type: str, *, code: str, state: str, user: User) -> Connection:
        provider = get_provider(provider_type)
        conn = self._get_or_create(db, provider_type, user)

        if not conn.oauth_state or conn.oauth_state != state:
            raise ValueError("Invalid OAuth state")
        if conn.oauth_state_expires_at and conn.oauth_state_expires_at < datetime.now(timezone.utc):
            raise ValueError("OAuth state expired")

        token_result = provider.exchange_code_for_tokens(code=code)

        conn.status = "connected"
        conn.is_authenticated = True
        conn.email = token_result.account_email
        conn.external_account_id = token_result.account_id
        conn.access_token = connector_token_crypto.encrypt(token_result.access_token)

        existing_refresh_token = connector_token_crypto.decrypt(conn.refresh_token)
        next_refresh_token = token_result.refresh_token or existing_refresh_token
        conn.refresh_token = connector_token_crypto.encrypt(next_refresh_token)
        conn.token_expires_at = token_result.expires_at
        conn.token_scopes = token_result.scopes
        conn.oauth_state = None
        conn.oauth_state_expires_at = None
        conn.last_error_message = None
        conn.last_error_at = None
        db.add(conn)
        db.commit()
        db.refresh(conn)
        return conn

    def disconnect(self, db: Session, provider_type: str, user: User) -> Connection:
        conn = self._get_or_create(db, provider_type, user)
        conn.status = "disconnected"
        conn.is_authenticated = False
        conn.access_token = None
        conn.refresh_token = None
        conn.token_expires_at = None
        conn.oauth_state = None
        conn.oauth_state_expires_at = None
        db.add(conn)
        db.commit()
        db.refresh(conn)
        return conn

    def sync_connection(self, db: Session, provider_type: str, user: User) -> tuple[Connection, SyncLog, SyncResult]:
        provider = get_provider(provider_type)
        conn = self._get_or_create(db, provider_type, user)
        if not conn.access_token:
            raise ValueError("Connection has no access token")

        access_token = connector_token_crypto.decrypt(conn.access_token)
        if access_token is None:
            raise ValueError("Connection has no access token")

        if not connector_token_crypto.is_encrypted(conn.access_token):
            # Legacy plaintext token row; re-encrypt in place once key material is configured.
            conn.access_token = connector_token_crypto.encrypt(access_token)
            db.add(conn)

        started = datetime.now(timezone.utc)
        conn.status = "syncing"
        conn.sync_progress = 5
        conn.last_sync_status = "in_progress"
        db.add(conn)

        log = SyncLog(connection_id=conn.id, start_time=started, status="in_progress")
        db.add(log)
        db.commit()

        try:
            remote_files = provider.list_remote_files(access_token=access_token)
            added, updated, failed, bytes_synced = self._upsert_documents(db, conn, remote_files, user)

            conn.status = "connected"
            conn.sync_progress = 100
            conn.last_sync_date = datetime.now(timezone.utc)
            conn.last_sync_status = "success" if failed == 0 else "partial"
            conn.document_count = db.query(Document).filter(Document.connection_id == conn.id, Document.user_id == user.id).count()
            conn.total_size = bytes_synced
            conn.last_error_message = None
            conn.last_error_at = None

            log.end_time = datetime.now(timezone.utc)
            log.status = conn.last_sync_status
            log.documents_added = added
            log.documents_updated = updated
            log.documents_failed = failed
            log.bytes_synced = bytes_synced

            result = SyncResult(added=added, updated=updated, failed=failed, bytes_synced=bytes_synced, files_seen=len(remote_files))
        except Exception as exc:
            conn.status = "error"
            conn.sync_progress = 0
            conn.last_sync_status = "failed"
            conn.last_sync_date = datetime.now(timezone.utc)
            conn.last_error_message = str(exc)
            conn.last_error_at = datetime.now(timezone.utc)

            log.end_time = datetime.now(timezone.utc)
            log.status = "failed"
            log.error_message = str(exc)
            result = SyncResult(added=0, updated=0, failed=0, bytes_synced=0, files_seen=0)

        db.add(conn)
        db.add(log)
        db.commit()
        db.refresh(conn)
        db.refresh(log)
        return conn, log, result

    def _upsert_documents(self, db: Session, conn: Connection, remote_files: list[dict], user: User) -> tuple[int, int, int, int]:
        added = 0
        updated = 0
        failed = 0
        bytes_synced = 0

        for remote in remote_files:
            try:
                source_id = remote["id"]
                size = int(remote.get("size") or 0)
                doc = db.query(Document).filter(
                    Document.source == conn.type,
                    Document.source_id == source_id,
                    Document.user_id == user.id,
                ).first()

                metadata = {
                    "provider": conn.type,
                    "provider_file_id": source_id,
                    "provider_modified_time": remote.get("modifiedTime"),
                    "provider_created_time": remote.get("createdTime"),
                    "web_view_link": remote.get("webViewLink"),
                    "ingestion_mode": "metadata_only",
                    "ingestion_note": "Binary download/import not implemented yet.",
                }
                if doc:
                    doc.filename = remote.get("name") or doc.filename
                    doc.file_size = size
                    doc.mime_type = remote.get("mimeType")
                    doc.extracted_metadata = metadata
                    updated += 1
                else:
                    db.add(
                        Document(
                            filename=remote.get("name") or f"gdrive-{source_id}",
                            original_path=f"gdrive://{source_id}",
                            file_type=self._file_type_from_mime(remote.get("mimeType")),
                            file_size=size,
                            mime_type=remote.get("mimeType"),
                            source=conn.type,
                            source_id=source_id,
                            connection_id=conn.id,
                            user_id=user.id,
                            processing_status="completed",
                            extracted_metadata=metadata,
                        )
                    )
                    added += 1

                bytes_synced += size
            except Exception:
                failed += 1

        return added, updated, failed, bytes_synced

    @staticmethod
    def _file_type_from_mime(mime_type: str | None) -> str:
        if not mime_type:
            return "unknown"
        if "pdf" in mime_type:
            return "pdf"
        if "document" in mime_type:
            return "docx"
        if "spreadsheet" in mime_type:
            return "xlsx"
        if "presentation" in mime_type:
            return "pptx"
        if "text" in mime_type:
            return "txt"
        return "unknown"


connector_service = ConnectorService()
