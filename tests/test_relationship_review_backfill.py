from app.models.document import Document
from app.models.intelligence import DocumentRelationshipReview
from app.models.relationships import DocumentRelationship
from app.scripts.backfill_relationship_reviews import backfill_relationship_reviews
from app.services.relationship_detection import RelationshipCandidate, relationship_detection_service


def _make_target(db, source, filename: str) -> Document:
    target = Document(
        filename=filename,
        original_path=f"/tmp/{filename}",
        file_type="pdf",
        file_size=100,
        user_id=source.user_id,
        processing_status="completed",
        source="upload",
        is_archived=False,
        entities=source.entities,
        upload_date=source.upload_date,
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def test_existing_relationship_without_review_gets_pending_review_on_reprocess(db, sample_document):
    target = _make_target(db, sample_document, "existing-no-review.pdf")
    rel = DocumentRelationship(
        source_doc_id=min(sample_document.id, target.id, key=str),
        target_doc_id=max(sample_document.id, target.id, key=str),
        relationship_type="follows_up",
        confidence=0.55,
        relationship_metadata={"signals": {"date_adjacency": 1.0}},
    )
    db.add(rel)
    db.commit()

    candidate = RelationshipCandidate(
        source_doc_id=rel.source_doc_id,
        target_doc_id=rel.target_doc_id,
        relationship_type="follows_up",
        confidence=0.77,
        metadata={"signals": {"date_adjacency": 1.0}},
    )
    relationship_detection_service._persist_candidates(db, [candidate])

    pending = (
        db.query(DocumentRelationshipReview)
        .filter(
            DocumentRelationshipReview.source_document_id == rel.source_doc_id,
            DocumentRelationshipReview.target_document_id == rel.target_doc_id,
            DocumentRelationshipReview.relationship_type == "related",
            DocumentRelationshipReview.status == "pending",
        )
        .all()
    )
    assert len(pending) == 1


def test_backfill_relationship_reviews_creates_missing_pending_reviews(db, sample_document):
    target = _make_target(db, sample_document, "backfill-target.pdf")
    rel = DocumentRelationship(
        source_doc_id=min(sample_document.id, target.id, key=str),
        target_doc_id=max(sample_document.id, target.id, key=str),
        relationship_type="follows_up",
        confidence=0.66,
        relationship_metadata={"source": "seed"},
    )
    db.add(rel)
    db.commit()

    scanned, refreshed, skipped = backfill_relationship_reviews(db)

    assert scanned >= 1
    assert refreshed >= 1
    assert skipped == 0

    reviews = (
        db.query(DocumentRelationshipReview)
        .filter(
            DocumentRelationshipReview.source_document_id == rel.source_doc_id,
            DocumentRelationshipReview.target_document_id == rel.target_doc_id,
            DocumentRelationshipReview.relationship_type == "related",
            DocumentRelationshipReview.status == "pending",
        )
        .all()
    )
    assert len(reviews) == 1
