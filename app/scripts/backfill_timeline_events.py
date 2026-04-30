from __future__ import annotations

from app.db.base import SessionLocal
from app.models.document import Document
from app.services.ai_analyzer import ai_analyzer


def main() -> int:
    db = SessionLocal()
    scanned = 0
    created = 0
    try:
        docs = db.query(Document).filter(Document.is_archived.is_(False)).all()
        for doc in docs:
            scanned += 1
            existing = ((doc.entities or {}).get("timeline_events", []) if isinstance(doc.entities, dict) else []) or []
            normalized_existing = ai_analyzer._normalize_timeline_events(existing)
            if normalized_existing:
                doc.entities = dict(doc.entities or {})
                doc.entities["timeline_events"] = normalized_existing
                created += len(normalized_existing)
            db.add(doc)
        db.commit()
        print(f"documents_scanned={scanned}")
        print(f"timeline_events_created={created}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
