from __future__ import annotations

import re
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.divorce import DivorceTimelineItem

CATEGORIES = ["legal", "financial", "children", "communication", "evidence", "court", "admin", "safety", "other"]
CATEGORY_BY_KEYWORD = {"court": "court", "hearing": "court", "filed": "legal", "motion": "legal", "bank": "financial", "payment": "financial", "tuition": "children", "custody": "children", "email": "communication", "text": "communication", "photo": "evidence", "exhibit": "evidence", "threat": "safety", "police": "safety"}
DATE_PATTERNS = [r"\b(\d{4}-\d{2}-\d{2})\b", r"\b(\d{1,2}/\d{1,2}/\d{4})\b"]


def _parse_date(value: str):
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    return None


def _category(text: str) -> str:
    lowered = text.lower()
    for k, v in CATEGORY_BY_KEYWORD.items():
        if k in lowered:
            return v
    return "other"


def _confidence(text: str, has_date: bool) -> float:
    score = 0.45
    if has_date:
        score += 0.3
    if len(text) > 30:
        score += 0.1
    if any(k in text.lower() for k in ["court", "hearing", "filed", "custody", "payment"]):
        score += 0.1
    return min(score, 0.95)


def extract_timeline_for_workspace(db: Session, workspace_id: str) -> int:
    docs = db.query(Document).filter(Document.workspace_id == workspace_id).all()
    created = 0
    for doc in docs:
        corpus = "\n".join([doc.raw_text or "", doc.summary or "", *doc.action_item_texts])
        for line in re.split(r"[\n\.]", corpus):
            line = line.strip()
            if not line:
                continue
            found = None
            for pat in DATE_PATTERNS:
                m = re.search(pat, line)
                if m:
                    found = m.group(1)
                    break
            if not found and not any(k in line.lower() for k in ["hearing", "filed", "served", "emailed", "payment"]):
                continue
            parsed = _parse_date(found) if found else None
            precision = "exact" if parsed else ("inferred" if found else "unknown")
            title = line[:120]
            snippet = line[:280]
            exists = db.query(DivorceTimelineItem).filter(
                DivorceTimelineItem.workspace_id == workspace_id,
                DivorceTimelineItem.source_document_id == doc.id,
                DivorceTimelineItem.event_date == parsed,
                DivorceTimelineItem.title == title,
                DivorceTimelineItem.source_snippet == snippet,
                DivorceTimelineItem.review_status == "suggested",
            ).first()
            if exists:
                continue
            db.add(DivorceTimelineItem(
                workspace_id=doc.workspace_id,
                event_date=parsed,
                date_precision=precision,
                title=title,
                description=line,
                category=_category(line),
                source_document_id=doc.id,
                source_quote=snippet,
                source_snippet=snippet,
                confidence=_confidence(line, bool(parsed)),
                review_status="suggested",
                include_in_report=True,
                metadata_json={"source": "timeline_extraction_v1"},
            ))
            created += 1
    db.commit()
    return created
