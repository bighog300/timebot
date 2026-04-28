from app.models.intelligence import DocumentReviewItem
from app.services.review_queue import review_queue_service


def test_create_or_refresh_open_review_item_avoids_duplicates(db, sample_document):
    first = review_queue_service.create_or_refresh_open_item(
        db,
        document_id=sample_document.id,
        review_type="low_confidence",
        reason="Low confidence",
    )
    second = review_queue_service.create_or_refresh_open_item(
        db,
        document_id=sample_document.id,
        review_type="low_confidence",
        reason="Still low confidence",
    )

    items = (
        db.query(DocumentReviewItem)
        .filter(DocumentReviewItem.document_id == sample_document.id, DocumentReviewItem.review_type == "low_confidence")
        .all()
    )

    assert first.id == second.id
    assert len(items) == 1
    assert items[0].reason == "Still low confidence"
