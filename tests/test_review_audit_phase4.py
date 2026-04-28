import uuid
from datetime import datetime, timedelta, timezone

from app.models.category import Category
from app.models.intelligence import DocumentActionItem, DocumentIntelligence, DocumentReviewItem, ReviewAuditEvent


def _event_types(db):
    return [event.event_type for event in db.query(ReviewAuditEvent).all()]


def test_review_item_mutations_create_audit_events(client, db, sample_document):
    item = DocumentReviewItem(
        id=uuid.uuid4(),
        document_id=sample_document.id,
        review_type="missing_tags",
        status="open",
        reason="needs tags",
    )
    db.add(item)
    db.commit()

    resolve_resp = client.post(f"/api/v1/review/items/{item.id}/resolve", json={"note": "handled"})
    assert resolve_resp.status_code == 200

    item2 = DocumentReviewItem(
        id=uuid.uuid4(),
        document_id=sample_document.id,
        review_type="processing_issues",
        status="open",
        reason="something happened",
    )
    db.add(item2)
    db.commit()

    dismiss_resp = client.post(f"/api/v1/review/items/{item2.id}/dismiss", json={"note": "ignore"})
    assert dismiss_resp.status_code == 200

    assert "review_item_resolved" in _event_types(db)
    assert "review_item_dismissed" in _event_types(db)


def test_action_item_mutations_create_audit_events(client, db, sample_document):
    item = DocumentActionItem(document_id=sample_document.id, content="Follow up")
    db.add(item)
    db.commit()
    db.refresh(item)

    update_resp = client.patch(f"/api/v1/action-items/{item.id}", json={"content": "Updated follow-up"})
    assert update_resp.status_code == 200

    complete_resp = client.post(f"/api/v1/action-items/{item.id}/complete")
    assert complete_resp.status_code == 200

    item2 = DocumentActionItem(document_id=sample_document.id, content="Dismiss me")
    db.add(item2)
    db.commit()
    db.refresh(item2)

    dismiss_resp = client.post(f"/api/v1/action-items/{item2.id}/dismiss")
    assert dismiss_resp.status_code == 200

    assert "action_item_updated" in _event_types(db)
    assert "action_item_completed" in _event_types(db)
    assert "action_item_dismissed" in _event_types(db)


def test_intelligence_category_mutations_create_audit_events(client, db, sample_document):
    suggested = Category(name="Suggested", slug="suggested-a")
    chosen = Category(name="Chosen", slug="chosen-a")
    db.add(suggested)
    db.add(chosen)
    db.commit()

    intelligence = DocumentIntelligence(
        document_id=sample_document.id,
        suggested_category_id=suggested.id,
        confidence="high",
        category_status="suggested",
        summary="old",
    )
    db.add(intelligence)
    db.commit()

    patch_resp = client.patch(
        f"/api/v1/documents/{sample_document.id}/intelligence",
        json={"summary": "new summary"},
    )
    assert patch_resp.status_code == 200

    approve_resp = client.post(f"/api/v1/documents/{sample_document.id}/category/approve")
    assert approve_resp.status_code == 200

    override_resp = client.post(
        f"/api/v1/documents/{sample_document.id}/category/override",
        json={"category_id": str(chosen.id)},
    )
    assert override_resp.status_code == 200

    assert "intelligence_updated" in _event_types(db)
    assert "category_approved" in _event_types(db)
    assert "category_overridden" in _event_types(db)


def test_review_audit_endpoints_return_filtered_and_ordered_events(client, db, sample_document, test_user):
    older = ReviewAuditEvent(
        document_id=sample_document.id,
        actor_id=test_user.id,
        event_type="review_item_resolved",
        note="older",
        created_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    newer = ReviewAuditEvent(
        document_id=sample_document.id,
        actor_id=test_user.id,
        event_type="action_item_completed",
        note="newer",
        created_at=datetime.now(timezone.utc),
    )
    db.add(older)
    db.add(newer)
    db.commit()

    resp = client.get("/api/v1/review/audit")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload[0]["note"] == "newer"
    assert payload[1]["note"] == "older"

    filtered = client.get("/api/v1/review/audit", params={"event_type": "review_item_resolved"})
    assert filtered.status_code == 200
    filtered_payload = filtered.json()
    assert len(filtered_payload) == 1
    assert filtered_payload[0]["event_type"] == "review_item_resolved"

    by_document = client.get(f"/api/v1/documents/{sample_document.id}/review-audit")
    assert by_document.status_code == 200
    assert len(by_document.json()) == 2
