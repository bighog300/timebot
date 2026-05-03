from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.email import EmailProviderConfig, EmailSendLog
from app.services.email_secrets import email_secret_crypto

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def sanitize_provider_error(message: str) -> str:
    cleaned = re.sub(r"(?i)(api[_-]?key|authorization)\s*[:=]\s*[^\n]+", "[redacted]", message)
    cleaned = re.sub(r"(?i)bearer\s+[A-Za-z0-9._-]+", "Bearer [redacted]", cleaned)
    return cleaned[:500]


class ResendEmailAdapter:
    def __init__(self, http_post=None):
        self.http_post = http_post or requests.post

    def send(self, *, api_key: str, to_email: str, subject: str, html_body: str, text_body: str | None, from_email: str, from_name: str | None, reply_to: str | None) -> str | None:
        from_value = f"{from_name} <{from_email}>" if from_name else from_email
        payload: dict[str, Any] = {"from": from_value, "to": [to_email], "subject": subject, "html": html_body}
        if text_body:
            payload["text"] = text_body
        if reply_to:
            payload["reply_to"] = reply_to
        r = self.http_post("https://api.resend.com/emails", json=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, timeout=10)
        if r.status_code >= 400:
            raise RuntimeError(sanitize_provider_error(r.text or f"Resend error {r.status_code}"))
        return (r.json() or {}).get("id")


class SendGridEmailAdapter:
    def __init__(self, http_post=None):
        self.http_post = http_post or requests.post

    def send(self, *, api_key: str, to_email: str, subject: str, html_body: str, text_body: str | None, from_email: str, from_name: str | None, reply_to: str | None) -> str | None:
        content = [{"type": "text/html", "value": html_body}]
        if text_body:
            content.append({"type": "text/plain", "value": text_body})
        payload: dict[str, Any] = {"personalizations": [{"to": [{"email": to_email}]}], "from": {"email": from_email, "name": from_name}, "subject": subject, "content": content}
        if reply_to:
            payload["reply_to"] = {"email": reply_to}
        r = self.http_post("https://api.sendgrid.com/v3/mail/send", json=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, timeout=10)
        if r.status_code >= 400:
            raise RuntimeError(sanitize_provider_error(r.text or f"SendGrid error {r.status_code}"))
        return r.headers.get("X-Message-Id")


class EmailDeliveryService:
    def __init__(self, db: Session, resend_adapter: ResendEmailAdapter | None = None, sendgrid_adapter: SendGridEmailAdapter | None = None):
        self.db = db
        self.adapters = {"resend": resend_adapter or ResendEmailAdapter(), "sendgrid": sendgrid_adapter or SendGridEmailAdapter()}

    def _resolve_provider(self, provider: str | None) -> EmailProviderConfig:
        q = self.db.query(EmailProviderConfig)
        cfg = q.filter(EmailProviderConfig.provider == provider).first() if provider else q.filter(EmailProviderConfig.enabled.is_(True), EmailProviderConfig.api_key_encrypted.isnot(None)).order_by(EmailProviderConfig.created_at.asc()).first()
        if not cfg:
            raise HTTPException(status_code=400, detail="No enabled configured email provider")
        if not cfg.enabled:
            raise HTTPException(status_code=400, detail="Provider is disabled")
        if not cfg.api_key_encrypted:
            raise HTTPException(status_code=400, detail="Provider missing API key")
        return cfg

    def send_email(self, *, provider: str | None, to_email: str, subject: str, html_body: str, text_body: str | None = None, from_email: str | None = None, from_name: str | None = None, reply_to: str | None = None, template_id=None, metadata: dict | None = None) -> dict:
        if not EMAIL_RE.match(to_email):
            raise HTTPException(status_code=422, detail="Invalid recipient email")
        cfg = self._resolve_provider(provider)
        api_key = email_secret_crypto.decrypt(cfg.api_key_encrypted) if hasattr(email_secret_crypto, 'decrypt') else None
        if not api_key:
            raise HTTPException(status_code=400, detail="Provider missing API key")
        resolved_from = from_email or cfg.from_email
        resolved_name = from_name if from_name is not None else cfg.from_name
        resolved_reply = reply_to if reply_to is not None else cfg.reply_to
        log = EmailSendLog(provider=cfg.provider, recipient_email=to_email, from_email=resolved_from, from_name=resolved_name, reply_to=resolved_reply, subject=subject, template_id=template_id, status="queued", metadata_json=metadata or {})
        self.db.add(log)
        self.db.flush()
        try:
            msg_id = self.adapters[cfg.provider].send(api_key=api_key, to_email=to_email, subject=subject, html_body=html_body, text_body=text_body, from_email=resolved_from, from_name=resolved_name, reply_to=resolved_reply)
            log.status = "sent"; log.provider_message_id = msg_id; log.sent_at = datetime.now(timezone.utc)
        except Exception as exc:
            log.status = "failed"; log.failed_at = datetime.now(timezone.utc); log.error_message_sanitized = sanitize_provider_error(str(exc))
            self.db.commit()
            raise HTTPException(status_code=502, detail="Email provider send failed")
        self.db.commit()
        return {"status": log.status, "provider": log.provider, "provider_message_id": log.provider_message_id, "log_id": str(log.id)}
