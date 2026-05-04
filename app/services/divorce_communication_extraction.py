from __future__ import annotations

import re
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.divorce import DivorceCommunication


CATEGORY_RULES = {
    "lawyer": ["esq", "attorney", "counsel", "law firm", "lawyer"],
    "spouse_or_other_party": ["spouse", "husband", "wife", "respondent", "petitioner"],
    "court": ["court", "judge", "hearing", "docket", "clerk"],
    "financial": ["bank", "account", "payment", "support", "asset", "income"],
    "children": ["child", "custody", "visitation", "parenting"],
    "school": ["school", "teacher", "principal", "tuition"],
    "mediator": ["mediator", "mediation"],
}

TONE_RULES = {
    "threatening": ["i will ruin", "take you to court", "threat", "restraining order"],
    "urgent": ["urgent", "immediately", "asap", "deadline"],
    "hostile": ["angry", "unacceptable", "refuse", "blame"],
    "cooperative": ["agree", "cooperate", "work together", "thank you"],
    "neutral": [],
}


def _norm(value: str | None) -> str:
    return (value or "").strip()


def _parse_sent_at(value: str | None):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y"):
        try:
            return datetime.strptime(value[:19], fmt)
        except ValueError:
            continue
    return None


def _pick_rule(text: str, mapping: dict[str, list[str]], default: str) -> str:
    lowered = text.lower()
    for label, keys in mapping.items():
        if any(key in lowered for key in keys):
            return label
    return default


def _extract_lines(text: str, keys: list[str]) -> list[str]:
    out: list[str] = []
    for line in re.split(r"[\n\.]", text):
        s = line.strip()
        if s and any(k in s.lower() for k in keys):
            out.append(s[:280])
    return out


def extract_communications_for_workspace(db: Session, workspace_id: str) -> int:
    docs = db.query(Document).filter(Document.workspace_id == workspace_id).all()
    created = 0
    for doc in docs:
        meta = doc.extracted_metadata if isinstance(doc.extracted_metadata, dict) else {}
        sender = _norm(meta.get("sender") or meta.get("from"))
        recipient = _norm(", ".join(meta.get("recipients") or []) if isinstance(meta.get("recipients"), list) else meta.get("recipients"))
        subject = _norm(meta.get("subject") or doc.filename)
        sent_at = _parse_sent_at(meta.get("received_at") or meta.get("date"))
        source_email_id = _norm(meta.get("gmail_message_id") or doc.source_id) or None

        corpus = "\n".join([subject, doc.summary or "", doc.raw_text or ""])
        category = _pick_rule(corpus + " " + sender + " " + recipient, CATEGORY_RULES, "unknown")
        tone = _pick_rule(corpus, TONE_RULES, "unclear")
        deadlines = _extract_lines(corpus, ["deadline", "by ", "due", "hearing", "court date"])
        offers = _extract_lines(corpus, ["offer", "settlement", "propose"])
        allegations = _extract_lines(corpus, ["allege", "accuse", "claim"])
        commitments = _extract_lines(corpus, ["will", "promise", "commit"])
        issues = {
            "child_related": _extract_lines(corpus, ["child", "custody", "visitation", "school"]),
            "financial": _extract_lines(corpus, ["support", "payment", "asset", "income", "bank"]),
            "legal": _extract_lines(corpus, ["court", "hearing", "order", "judge", "filing"]),
            "commitments": commitments,
        }
        exists = db.query(DivorceCommunication).filter(
            DivorceCommunication.workspace_id == workspace_id,
            DivorceCommunication.source_document_id == doc.id,
            DivorceCommunication.sender == sender,
            DivorceCommunication.subject == subject,
            DivorceCommunication.sent_at == sent_at,
        ).first()
        if exists:
            continue
        db.add(DivorceCommunication(
            workspace_id=workspace_id,
            source_document_id=doc.id,
            source_email_id=source_email_id,
            sender=sender,
            recipient=recipient,
            subject=subject,
            sent_at=sent_at,
            communication_type="email" if doc.source in {"gmail"} else "document",
            category=category,
            tone=tone,
            extracted_issues_json=issues,
            extracted_deadlines_json=deadlines,
            extracted_offers_json=offers,
            extracted_allegations_json=allegations,
            confidence=0.72,
            review_status="suggested",
            metadata_json={"source": "communication_extraction_v1", "source_snippet": (doc.raw_text or "")[:300], "inference": {"tone": tone, "category": category}},
        ))
        created += 1
    db.commit()
    return created
