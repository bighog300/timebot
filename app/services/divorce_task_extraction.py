from __future__ import annotations

import re
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.intelligence import DocumentActionItem

PRIORITY_BY_KEYWORD = {
    "urgent": "urgent",
    "immediately": "urgent",
    "asap": "high",
    "deadline": "high",
    "court": "high",
    "child": "high",
    "financial": "medium",
}

CATEGORY_BY_KEYWORD = {
    "court": "legal",
    "legal": "legal",
    "disclosure": "financial",
    "bank": "financial",
    "child": "children",
    "school": "children",
    "email": "communication",
    "message": "communication",
    "evidence": "evidence",
}


def _guess_priority(text: str) -> str:
    lowered = text.lower()
    for key, value in PRIORITY_BY_KEYWORD.items():
        if key in lowered:
            return value
    return "medium"


def _guess_category(text: str) -> str:
    lowered = text.lower()
    for key, value in CATEGORY_BY_KEYWORD.items():
        if key in lowered:
            return value
    return "admin"


def extract_tasks_for_workspace(db: Session, workspace_id: str) -> int:
    docs = db.query(Document).filter(Document.workspace_id == workspace_id).all()
    created = 0
    for doc in docs:
        items = list(doc.action_item_texts)
        text = (doc.raw_text or "")[:5000]
        for line in re.split(r"[\n\.]", text):
            line = line.strip()
            if not line:
                continue
            if any(token in line.lower() for token in ["deadline", "must", "required", "urgent", "submit", "file", "respond"]):
                items.append(line)
        seen = set()
        for content in items:
            key = content.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            exists = db.query(DocumentActionItem).filter(
                DocumentActionItem.document_id == doc.id,
                DocumentActionItem.content == content,
                DocumentActionItem.state == "suggested",
            ).first()
            if exists:
                continue
            due_date = date.today() + timedelta(days=14 if "urgent" not in key else 3)
            db.add(DocumentActionItem(
                document_id=doc.id,
                workspace_id=doc.workspace_id,
                source_document_id=doc.id,
                content=content,
                source_snippet=content[:280],
                due_date=due_date,
                priority=_guess_priority(content),
                status="suggested",
                state="suggested",
                category=_guess_category(content),
                evidence_refs_json=[{"document_id": str(doc.id), "snippet": content[:120]}],
                source="ai",
            ))
            created += 1
    db.commit()
    return created
