from __future__ import annotations

import argparse
from uuid import UUID

from app.db.session import SessionLocal
from app.models.document import Document
from app.services.relationship_detection import relationship_detection_service


def inspect(document_id: UUID, limit: int = 50) -> int:
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            print(f"document not found: {document_id}")
            return 1

        print(f"doc={doc.id}")
        print(f"title={doc.filename}")
        print(f"category user={doc.user_category_id} ai={doc.ai_category_id}")
        print(f"summary_len={len(doc.summary or '')}")
        print(f"entity_keys={sorted((doc.entities or {}).keys())}")

        compare_docs = (
            db.query(Document)
            .filter(
                Document.id != document_id,
                Document.user_id == doc.user_id,
                Document.is_archived.is_(False),
                Document.processing_status == "completed",
            )
            .limit(limit)
            .all()
        )
        print(f"comparison_docs={len(compare_docs)}")

        scored = []
        for other in compare_docs:
            cand = relationship_detection_service._score_pair(doc, other, log_prefix="inspect")
            scored.append((other, cand))

        ranked = sorted([x for x in scored if x[1] is not None], key=lambda x: x[1].confidence, reverse=True)
        for other, cand in ranked[:10]:
            print(f"candidate={other.id} score={cand.confidence} type={cand.relationship_type} signals={cand.metadata.get('signals', {})}")

        skipped = [other for other, cand in scored if cand is None]
        print(f"skipped_candidates={len(skipped)}")
        for other in skipped[:10]:
            print(f"skipped={other.id} title={other.filename}")
        return 0
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect relationship candidates for a document")
    parser.add_argument("document_id", type=UUID)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    raise SystemExit(inspect(args.document_id, args.limit))


if __name__ == "__main__":
    main()
