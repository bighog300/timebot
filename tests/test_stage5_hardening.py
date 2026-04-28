import uuid

from app.models.intelligence import DocumentReviewItem, ReviewAuditEvent
from app.services.review_queue import review_queue_service


def test_review_items_endpoint_rejects_invalid_status_enum(client):
    response = client.get('/api/v1/review/items', params={'status': 'not_a_real_status'})
    assert response.status_code == 422


def test_action_items_endpoint_rejects_invalid_state_enum(client):
    response = client.get('/api/v1/action-items', params={'state': 'not_a_real_state'})
    assert response.status_code == 422


def test_create_or_refresh_open_review_item_deduplicates_existing_open_rows(db, sample_document):
    original = DocumentReviewItem(
        id=uuid.uuid4(),
        document_id=sample_document.id,
        review_type='missing_tags',
        status='open',
        reason='first',
    )
    duplicate = DocumentReviewItem(
        id=uuid.uuid4(),
        document_id=sample_document.id,
        review_type='missing_tags',
        status='open',
        reason='second',
    )
    db.add_all([original, duplicate])
    db.commit()

    item = review_queue_service.create_or_refresh_open_item(
        db,
        document_id=sample_document.id,
        review_type='missing_tags',
        reason='refreshed reason',
        payload={'priority': 'high'},
    )

    assert item.id == original.id

    rows = (
        db.query(DocumentReviewItem)
        .filter(
            DocumentReviewItem.document_id == sample_document.id,
            DocumentReviewItem.review_type == 'missing_tags',
        )
        .order_by(DocumentReviewItem.created_at.asc(), DocumentReviewItem.id.asc())
        .all()
    )
    assert [row.status for row in rows] == ['open', 'dismissed']
    assert rows[1].payload['deduplicated_to'] == str(original.id)


def test_single_item_mutation_persists_audit_event_with_state_change(client, db, sample_document):
    item = DocumentReviewItem(
        id=uuid.uuid4(),
        document_id=sample_document.id,
        review_type='processing_issues',
        status='open',
        reason='needs review',
    )
    db.add(item)
    db.commit()

    response = client.post(f'/api/v1/review/items/{item.id}/resolve', json={'note': 'handled'})
    assert response.status_code == 200

    db.refresh(item)
    assert item.status == 'resolved'
    event = db.query(ReviewAuditEvent).filter(ReviewAuditEvent.document_id == sample_document.id).order_by(ReviewAuditEvent.created_at.desc()).first()
    assert event is not None
    assert event.event_type == 'review_item_resolved'
