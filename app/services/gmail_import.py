from __future__ import annotations

import base64
import binascii
import html
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import httpx
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.intelligence import DocumentRelationshipReview
from app.models.relationships import Connection, DocumentRelationship, GmailImportedAttachment, GmailImportedMessage
from app.models.user import User
from app.services.connectors.token_crypto import connector_token_crypto
from app.services.document_processor import document_processor
from app.services.storage import storage


class _HTMLToTextParser(HTMLParser):
    BLOCK_TAGS = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs):
        t = tag.lower()
        if t in {"script", "style"}:
            self._skip_depth += 1
            return
        if self._skip_depth == 0 and t in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str):
        t = tag.lower()
        if t in {"script", "style"} and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if self._skip_depth == 0 and t in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str):
        if self._skip_depth == 0:
            self.parts.append(data)


class GmailImportService:
    scope = "https://www.googleapis.com/auth/gmail.readonly"
    SUPPORTED_ATTACHMENT_EXTS = {"pdf", "doc", "docx", "txt", "xls", "xlsx", "ppt", "pptx", "png", "jpg", "jpeg"}

    def _ensure_relationship(self, db: Session, *, source_doc_id, target_doc_id, relationship_type: str, confidence: float, metadata: dict) -> None:
        existing = db.query(DocumentRelationship).filter(
            DocumentRelationship.source_doc_id == source_doc_id,
            DocumentRelationship.target_doc_id == target_doc_id,
            DocumentRelationship.relationship_type == relationship_type,
        ).first()
        if not existing:
            db.add(DocumentRelationship(
                source_doc_id=source_doc_id,
                target_doc_id=target_doc_id,
                relationship_type=relationship_type,
                confidence=confidence,
                relationship_metadata=metadata,
            ))

        review = db.query(DocumentRelationshipReview).filter(
            DocumentRelationshipReview.source_document_id == source_doc_id,
            DocumentRelationshipReview.target_document_id == target_doc_id,
            DocumentRelationshipReview.relationship_type == relationship_type,
        ).first()
        if not review:
            db.add(DocumentRelationshipReview(
                source_document_id=source_doc_id,
                target_document_id=target_doc_id,
                relationship_type=relationship_type,
                confidence=confidence,
                status="confirmed",
                reason_codes_json=["gmail_import_linkage"],
                metadata_json=metadata,
            ))

    def _conn(self, db: Session, user: User) -> Connection:
        conn = db.query(Connection).filter(Connection.user_id == user.id, Connection.type == "gmail").first()
        if not conn or not conn.access_token:
            raise ValueError("Gmail is not connected")
        if self.scope not in (conn.token_scopes or []):
            raise ValueError("Gmail connection missing readonly scope")
        return conn

    def _headers_to_map(self, payload: dict) -> dict[str, str]:
        hdrs = payload.get("payload", {}).get("headers", [])
        return {h.get("name", "").lower(): h.get("value", "") for h in hdrs if h.get("name")}

    def _decode_body_data(self, data: str | None) -> str:
        if not data:
            return ""
        try:
            pad = "=" * (-len(data) % 4)
            return base64.urlsafe_b64decode((data + pad).encode("utf-8")).decode("utf-8", errors="replace")
        except (binascii.Error, ValueError):
            return ""

    def _extract_parts(self, part: dict) -> tuple[str, str, list[dict]]:
        mime = (part.get("mimeType") or "").lower()
        body = self._decode_body_data((part.get("body") or {}).get("data"))
        plain, rich = "", ""
        atts: list[dict] = []
        if part.get("filename") and ((part.get("body") or {}).get("attachmentId") or body):
            atts.append(part)

        for child in part.get("parts", []) or []:
            c_plain, c_rich, c_atts = self._extract_parts(child)
            plain = plain or c_plain
            rich = rich or c_rich
            atts.extend(c_atts)

        if mime == "text/plain" and body:
            plain = plain or body
        elif mime == "text/html" and body:
            rich = rich or body
        return plain, rich, atts

    def _html_to_text(self, content: str) -> str:
        parser = _HTMLToTextParser()
        parser.feed(content)
        text = html.unescape("".join(parser.parts))
        text = re.sub(r"\r\n?", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[\t ]+", " ", text)
        return text.strip()

    def _strip_noise(self, text: str) -> str:
        out = text
        out = re.sub(r"\n--\s*\n[\s\S]{0,300}$", "", out)
        out = re.sub(r"\nSent from my iPhone\s*$", "", out, flags=re.IGNORECASE)
        out = re.sub(r"\nSent from Outlook\s*$", "", out, flags=re.IGNORECASE)
        out = re.sub(r"\nOn .+ wrote:\n[\s\S]*$", "", out, flags=re.IGNORECASE)
        out = re.sub(r"\nFrom: .+\nSent: .+\nTo: .+\nSubject: .+[\s\S]*$", "", out, flags=re.IGNORECASE)
        out = re.sub(r"\n>.*$", "", out, flags=re.MULTILINE)
        sign = re.search(r"\n(Regards|Best),\s*\n(?:[^\n]{0,80}\n){1,4}$", out, flags=re.IGNORECASE)
        if sign:
            out = out[: sign.start()]
        disclaimer = re.search(r"\n(?:confidential|privileged|intended recipient).{250,}$", out, flags=re.IGNORECASE | re.DOTALL)
        if disclaimer:
            out = out[: disclaimer.start()]
        out = re.sub(r"\n{3,}", "\n\n", out)
        return out.strip()

    def _body_and_attachments(self, payload: dict) -> tuple[str, list[dict]]:
        plain, rich, atts = self._extract_parts(payload.get("payload", {}))
        body = plain or self._html_to_text(rich)
        return self._strip_noise(body), atts

    def preview(self, db: Session, user: User, sender_email: str, max_results: int = 20):
        conn = self._conn(db, user)
        token = connector_token_crypto.decrypt(conn.access_token)
        headers = {"Authorization": f"Bearer {token}"}
        q = f"from:{sender_email}"
        with httpx.Client(timeout=20) as c:
            res = c.get("https://gmail.googleapis.com/gmail/v1/users/me/messages", params={"q": q, "maxResults": max_results}, headers=headers)
            res.raise_for_status()
            out = []
            for item in res.json().get("messages", []):
                m = c.get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{item['id']}", params={"format": "full"}, headers=headers).json()
                imported = db.query(GmailImportedMessage).filter(GmailImportedMessage.user_id == user.id, GmailImportedMessage.gmail_message_id == item["id"]).first() is not None
                body, atts = self._body_and_attachments(m)
                hdr = self._headers_to_map(m)
                out.append({"gmail_message_id": item["id"], "sender": hdr.get("from", sender_email), "subject": hdr.get("subject", m.get("snippet", "")[:80]), "received_at": hdr.get("date"), "snippet": body[:240] or m.get("snippet", ""), "already_imported": imported, "attachments": [a.get("filename") for a in atts if a.get("filename")]})
        return {"messages": out}

    def import_messages(self, db: Session, user: User, sender_email: str, message_ids: list[str], include_attachments: bool = False):
        conn = self._conn(db, user)
        token = connector_token_crypto.decrypt(conn.access_token)
        headers = {"Authorization": f"Bearer {token}"}
        imported_email_count = imported_attachment_count = skipped_attachment_count = duplicate_message_count = 0
        created_document_ids = []
        skipped_attachments = []
        with httpx.Client(timeout=20) as c:
            for mid in message_ids:
                if db.query(GmailImportedMessage).filter(GmailImportedMessage.user_id == user.id, GmailImportedMessage.gmail_message_id == mid).first():
                    duplicate_message_count += 1
                    continue
                m = c.get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{mid}", params={"format": "full"}, headers=headers)
                m.raise_for_status()
                payload = m.json()
                hdr = self._headers_to_map(payload)
                body, atts = self._body_and_attachments(payload)
                recipients = hdr.get("to", "")
                subject = hdr.get("subject", "No Subject")
                composed = f"Subject: {subject}\nFrom: {hdr.get('from', sender_email)}\nTo: {recipients}\nDate: {hdr.get('date', '')}\n\nBody:\n{body}".strip()
                doc = Document(filename=f"Email - {subject[:50]}", original_path=f"gmail://{mid}", file_type="txt", file_size=len(composed.encode()), mime_type="text/plain", source="gmail", source_id=mid, connection_id=conn.id, user_id=user.id, processing_status="queued", raw_text=composed, extracted_metadata={"source": "gmail", "sender": hdr.get("from", sender_email), "recipients": recipients, "subject": subject, "received_at": hdr.get("date"), "gmail_message_id": mid, "gmail_thread_id": payload.get("threadId"), "has_attachments": bool(atts), "attachment_count": len([a for a in atts if a.get('filename')])})
                db.add(doc)
                db.commit()
                db.refresh(doc)
                document_processor._process_sync(db, doc)
                db.add(GmailImportedMessage(user_id=user.id, gmail_message_id=mid, gmail_thread_id=payload.get("threadId"), sender=hdr.get("from", sender_email), subject=subject, received_at=datetime.now(timezone.utc), document_id=doc.id))
                thread_id = payload.get("threadId")
                if thread_id:
                    peers = db.query(GmailImportedMessage).filter(
                        GmailImportedMessage.user_id == user.id,
                        GmailImportedMessage.gmail_thread_id == thread_id,
                        GmailImportedMessage.document_id != doc.id,
                    ).all()
                    for peer in peers:
                        source_id, target_id = (doc.id, peer.document_id) if str(doc.id) < str(peer.document_id) else (peer.document_id, doc.id)
                        self._ensure_relationship(
                            db,
                            source_doc_id=source_id,
                            target_doc_id=target_id,
                            relationship_type="thread",
                            confidence=0.99,
                            metadata={"gmail_thread_id": thread_id},
                        )
                db.commit()
                imported_email_count += 1
                created_document_ids.append(str(doc.id))

                if include_attachments:
                    for part in atts:
                        filename = part.get("filename") or "attachment"
                        ext = Path(filename).suffix.lstrip(".").lower()
                        if ext not in self.SUPPORTED_ATTACHMENT_EXTS:
                            skipped_attachment_count += 1
                            skipped_attachments.append({"filename": filename, "reason": "unsupported attachment type"})
                            continue
                        attachment_id = (part.get("body") or {}).get("attachmentId") or filename
                        if db.query(GmailImportedAttachment).filter(GmailImportedAttachment.user_id == user.id, GmailImportedAttachment.gmail_message_id == mid, GmailImportedAttachment.attachment_id == attachment_id).first():
                            skipped_attachment_count += 1
                            skipped_attachments.append({"filename": filename, "reason": "already imported"})
                            continue
                        if (part.get("body") or {}).get("attachmentId"):
                            ar = c.get(f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{mid}/attachments/{attachment_id}", headers=headers)
                            ar.raise_for_status()
                            binary = base64.urlsafe_b64decode(ar.json().get("data", "") + "===")
                        else:
                            binary = base64.urlsafe_b64decode(((part.get("body") or {}).get("data") or "") + "===")
                        safe = f"gmail_{mid}_{attachment_id}_{Path(filename).name}"
                        dest = storage._dated_dir(storage.upload_path) / safe
                        dest.write_bytes(binary)
                        att_doc = Document(filename=f"Email Attachment - {filename}", original_path=str(dest), file_type=ext, file_size=len(binary), mime_type=storage.get_mime_type(dest), source="gmail", source_id=f"{mid}:{attachment_id}", connection_id=conn.id, user_id=user.id, processing_status="queued", extracted_metadata={"source": "gmail_attachment", "parent_gmail_message_id": mid, "parent_document_id": str(doc.id), "sender": hdr.get("from", sender_email), "subject": subject, "attachment_filename": filename})
                        db.add(att_doc)
                        db.commit()
                        db.refresh(att_doc)
                        document_processor._process_sync(db, att_doc)
                        db.add(GmailImportedAttachment(user_id=user.id, gmail_message_id=mid, attachment_id=attachment_id, filename=filename, document_id=att_doc.id))
                        self._ensure_relationship(
                            db,
                            source_doc_id=doc.id,
                            target_doc_id=att_doc.id,
                            relationship_type="attachment",
                            confidence=1.0,
                            metadata={"filename": filename, "gmail_message_id": mid},
                        )
                        db.commit()
                        imported_attachment_count += 1
                        created_document_ids.append(str(att_doc.id))

        return {"imported_count": imported_email_count, "imported_email_count": imported_email_count, "imported_attachment_count": imported_attachment_count, "skipped_attachment_count": skipped_attachment_count, "skipped_attachments": skipped_attachments, "duplicate_message_count": duplicate_message_count, "created_document_ids": created_document_ids}


gmail_import_service = GmailImportService()
