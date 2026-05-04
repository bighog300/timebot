from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.system_intelligence import SystemIntelligenceWebReference
from app.services.system_intelligence_ingest import hash_bytes

ALLOWED_LEGAL_SOURCE_DOMAINS = {
    "saflii.org",
    "judiciary.org.za",
    "justice.gov.za",
    "gov.za",
    "concourt.org.za",
    "lawlibrary.org.za",
}


@dataclass
class LegalWebReferenceCaptureInput:
    title: str
    url: str
    canonical_url: str | None = None
    source_domain: str | None = None
    jurisdiction: str | None = None
    court_or_institution: str | None = None
    document_type: str | None = None
    legal_area: str | None = None
    summary: str | None = None
    key_points_json: list | dict | None = None
    citation_text: str | None = None


class LegalWebReferenceCaptureService:
    @staticmethod
    def _normalize_domain(domain: str | None) -> str | None:
        return (domain or "").strip().lower() or None

    @classmethod
    def _is_trusted_domain(cls, domain: str | None) -> bool:
        normalized = cls._normalize_domain(domain)
        if not normalized:
            return False
        return any(normalized == allowed or normalized.endswith(f".{allowed}") for allowed in ALLOWED_LEGAL_SOURCE_DOMAINS)

    @staticmethod
    def _extract_domain(url: str) -> str | None:
        parsed = urlparse(url)
        return (parsed.netloc or "").lower() or None

    @classmethod
    def capture_candidate_reference(cls, db: Session, payload: LegalWebReferenceCaptureInput) -> SystemIntelligenceWebReference:
        resolved_domain = cls._normalize_domain(payload.source_domain) or cls._extract_domain(payload.canonical_url or payload.url)
        content_basis = "\n".join(
            [payload.title.strip(), payload.summary or "", payload.citation_text or "", str(payload.key_points_json or "")]
        )
        content_hash = hash_bytes(content_basis.encode("utf-8"))

        existing = db.query(SystemIntelligenceWebReference).filter(
            or_(
                SystemIntelligenceWebReference.canonical_url == (payload.canonical_url or None),
                (SystemIntelligenceWebReference.url == payload.url) & (SystemIntelligenceWebReference.content_hash == content_hash),
            )
        ).first()
        if existing:
            return existing

        status = "candidate" if cls._is_trusted_domain(resolved_domain) else "untrusted"
        now = datetime.now(timezone.utc)
        ref = SystemIntelligenceWebReference(
            title=payload.title,
            url=payload.url,
            canonical_url=payload.canonical_url,
            source_domain=resolved_domain,
            jurisdiction=payload.jurisdiction,
            court_or_institution=payload.court_or_institution,
            document_type=payload.document_type,
            legal_area=payload.legal_area,
            summary=payload.summary,
            key_points_json=payload.key_points_json,
            citation_text=payload.citation_text,
            retrieved_at=now,
            last_checked_at=now,
            content_hash=content_hash,
            status=status,
        )
        db.add(ref)
        db.flush()
        return ref
