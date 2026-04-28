import uuid
from datetime import datetime, timedelta, timezone

from app.models.intelligence import DocumentActionItem, DocumentReviewItem


def test_review_metrics_endpoint_returns_dashboard_aggregates(client, db, sample_document):
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)

    older_open = DocumentReviewItem(
        id=uuid.uuid4(),
        document_id=sample_document.id,
        review_type="uncategorized",
        status="open",
        payload={"priority": "high"},
        created_at=now - timedelta(hours=48),
    )
    newer_open = DocumentReviewItem(
        id=uuid.uuid4(),
        document_id=sample_document.id,
        review_type="low_confidence",
        status="open",
        payload={"priority": "low"},
        created_at=now - timedelta(hours=12),
    )
    resolved_recent = DocumentReviewItem(
        id=uuid.uuid4(),
        document_id=sample_document.id,
        review_type="missing_tags",
        status="resolved",
        resolved_at=now - timedelta(hours=2),
        created_at=now - timedelta(days=2),
    )
    dismissed_item = DocumentReviewItem(
        id=uuid.uuid4(),
        document_id=sample_document.id,
        review_type="processing_issues",
        status="dismissed",
        dismissed_at=now - timedelta(hours=1),
        created_at=now - timedelta(days=1),
    )
    db.add_all([older_open, newer_open, resolved_recent, dismissed_item])
    db.commit()

    from app.services.review_queue import review_queue_service

    original_now = review_queue_service._now
    review_queue_service._now = lambda: now
    try:
        response = client.get("/api/v1/review/metrics")
    finally:
        review_queue_service._now = original_now

    assert response.status_code == 200
    payload = response.json()
    assert payload["open_review_count"] == 2
    assert payload["resolved_review_count"] == 1
    assert payload["dismissed_review_count"] == 1
    assert payload["open_by_type"] == {"low_confidence": 1, "uncategorized": 1}
    assert payload["open_by_priority"] == {"high": 1, "low": 1}
    assert payload["average_age_hours"] == 30.0
    assert payload["recently_resolved_count"] == 1
    assert payload["low_confidence_category_count"] == 1
    assert payload["uncategorized_count"] == 1
    assert [item["id"] for item in payload["oldest_open_items"]] == [str(older_open.id), str(newer_open.id)]


def test_action_item_metrics_endpoint_includes_completion_and_overdue(client, db, sample_document):
    now = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)

    open_overdue = DocumentActionItem(
        document_id=sample_document.id,
        content="Past due",
        state="open",
        action_metadata={"due_date": "2026-04-27T10:00:00Z"},
    )
    open_not_due = DocumentActionItem(
        document_id=sample_document.id,
        content="Future due",
        state="open",
        action_metadata={"due_date": "2026-04-29T10:00:00Z"},
    )
    completed_recent = DocumentActionItem(
        document_id=sample_document.id,
        content="Recently done",
        state="completed",
        completed_at=now - timedelta(hours=3),
    )
    dismissed = DocumentActionItem(
        document_id=sample_document.id,
        content="Dismissed",
        state="dismissed",
    )
    db.add_all([open_overdue, open_not_due, completed_recent, dismissed])
    db.commit()

    from app.services.action_items import action_items_service

    original_now = action_items_service._now
    action_items_service._now = lambda: now
    try:
        response = client.get("/api/v1/action-items/metrics")
    finally:
        action_items_service._now = original_now

    assert response.status_code == 200
    payload = response.json()
    assert payload["open_count"] == 2
    assert payload["completed_count"] == 1
    assert payload["dismissed_count"] == 1
    assert payload["overdue_count"] == 1
    assert payload["completion_rate"] == 0.25
    assert payload["recently_completed_count"] == 1


def test_action_item_metrics_omits_overdue_when_due_dates_missing(client, db, sample_document):
    item = DocumentActionItem(document_id=sample_document.id, content="No due date", state="open", action_metadata={})
    db.add(item)
    db.commit()

    response = client.get("/api/v1/action-items/metrics")
    assert response.status_code == 200
    assert response.json()["overdue_count"] is None
