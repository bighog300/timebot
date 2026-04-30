from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.base import SessionLocal
from app.models.relationships import DocumentRelationship
from app.services.relationship_review import relationship_review_service


def _to_review_type(relationship_type: str) -> str | None:
    return {
        "duplicates": "duplicate",
        "similar_to": "similar",
        "related_to": "related",
        "follows_up": "related",
    }.get(relationship_type)


def backfill_relationship_reviews(db: Session) -> tuple[int, int, int]:
    relationships = db.query(DocumentRelationship).all()
    scanned = len(relationships)
    refreshed = 0
    skipped = 0

    for relationship in relationships:
        review_type = _to_review_type(relationship.relationship_type)
        if not review_type:
            skipped += 1
            continue

        relationship_review_service.create_or_refresh_pending(
            db,
            source_document_id=relationship.source_doc_id,
            target_document_id=relationship.target_doc_id,
            relationship_type=review_type,
            confidence=relationship.confidence,
            reason_codes_json=["relationship_backfill"],
            metadata_json=relationship.relationship_metadata or {"source": "relationship_backfill"},
        )
        refreshed += 1

    db.commit()
    return scanned, refreshed, skipped


def main() -> None:
    db = SessionLocal()
    try:
        scanned, refreshed, skipped = backfill_relationship_reviews(db)
        print(f"relationships scanned: {scanned}")
        print(f"reviews created/refreshed: {refreshed}")
        print(f"skipped/unmapped: {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
