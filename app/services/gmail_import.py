from __future__ import annotations

from datetime import datetime, timezone
import base64
import re
import httpx
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.relationships import Connection, GmailImportedMessage
from app.models.user import User
from app.services.connectors.token_crypto import connector_token_crypto
from app.services.document_processor import document_processor

class GmailImportService:
    scope = "https://www.googleapis.com/auth/gmail.readonly"

    def _conn(self, db: Session, user: User) -> Connection:
        conn = db.query(Connection).filter(Connection.user_id == user.id, Connection.type == "gmail").first()
        if not conn or not conn.access_token:
            raise ValueError("Gmail is not connected")
        if self.scope not in (conn.token_scopes or []):
            raise ValueError("Gmail connection missing readonly scope")
        return conn

    def preview(self, db: Session, user: User, sender_email: str, max_results: int = 20):
        conn = self._conn(db, user)
        token = connector_token_crypto.decrypt(conn.access_token)
        headers={"Authorization": f"Bearer {token}"}
        q=f"from:{sender_email}"
        with httpx.Client(timeout=20) as c:
            res=c.get("https://gmail.googleapis.com/gmail/v1/users/me/messages", params={"q": q, "maxResults": max_results}, headers=headers); res.raise_for_status()
            out=[]
            for item in res.json().get("messages", []):
                m=c.get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{item['id']}", params={"format":"metadata"}, headers=headers).json()
                imported = db.query(GmailImportedMessage).filter(GmailImportedMessage.user_id==user.id, GmailImportedMessage.gmail_message_id==item['id']).first() is not None
                out.append({"gmail_message_id": item['id'], "sender": sender_email, "subject": m.get("snippet","")[:80], "received_at": None, "snippet": m.get("snippet", ""), "already_imported": imported, "attachments": []})
        return {"messages": out}

    def import_messages(self, db: Session, user: User, sender_email: str, message_ids: list[str]):
        conn = self._conn(db, user); token = connector_token_crypto.decrypt(conn.access_token); headers={"Authorization": f"Bearer {token}"}
        imported_count=0
        with httpx.Client(timeout=20) as c:
            for mid in message_ids:
                if db.query(GmailImportedMessage).filter(GmailImportedMessage.user_id==user.id, GmailImportedMessage.gmail_message_id==mid).first():
                    continue
                m=c.get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{mid}", params={"format":"full"}, headers=headers); m.raise_for_status(); payload=m.json()
                raw=payload.get("snippet","")
                doc=Document(filename=f"Email - {raw[:50] or 'No Subject'}", original_path=f"gmail://{mid}", file_type="txt", file_size=len(raw.encode()), mime_type="text/plain", source="gmail", source_id=mid, connection_id=conn.id, user_id=user.id, processing_status="queued", raw_text=raw, extracted_metadata={"source":"gmail","sender":sender_email,"gmail_message_id":mid,"gmail_thread_id":payload.get("threadId")})
                db.add(doc); db.commit(); db.refresh(doc)
                document_processor._process_sync(db, doc)
                db.add(GmailImportedMessage(user_id=user.id,gmail_message_id=mid,gmail_thread_id=payload.get("threadId"),sender=sender_email,subject=doc.filename,received_at=datetime.now(timezone.utc),document_id=doc.id)); db.commit()
                imported_count += 1
        return {"imported_count": imported_count}

gmail_import_service = GmailImportService()
