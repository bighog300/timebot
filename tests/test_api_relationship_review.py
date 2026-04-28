import uuid

from app.models.intelligence import DocumentRelationshipReview, ReviewAuditEvent
from app.services.relationship_review import relationship_review_service


def test_relationship_review_endpoints_list_get_confirm_dismiss(client, db, sample_document):
    target = type(sample_document)(
        id=uuid.uuid4(),
        filename="target.pdf",
        original_path="/tmp/target.pdf",
        file_type="pdf",
        file_size=512,
        mime_type="application/pdf",
        processing_status="completed",
        source="upload",
        user_id=sample_document.user_id,
    )
    db.add(target)
    db.commit()

    review = DocumentRelationshipReview(
        source_document_id=sample_document.id,
        target_document_id=target.id,
        relationship_type="duplicate",
        confidence=0.95,
        reason_codes_json=["model_detection"],
        metadata_json={"signals": {"title_similarity": 0.8}},
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    list_resp = client.get("/api/v1/review/relationships")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    get_resp = client.get(f"/api/v1/review/relationships/{review.id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["relationship_type"] == "duplicate"

    confirm_resp = client.post(
        f"/api/v1/review/relationships/{review.id}/confirm",
        json={"reason_codes_json": ["human_validated"]},
    )
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["status"] == "confirmed"

    dismiss_resp = client.post(
        f"/api/v1/review/relationships/{review.id}/dismiss",
        json={"reason_codes_json": ["false_positive"]},
    )
    assert dismiss_resp.status_code == 409

    events = db.query(ReviewAuditEvent).all()
    assert len([event for event in events if event.event_type == "relationship_review_confirmed"]) == 1


def test_create_or_refresh_pending_relationship_review_prevents_duplicates(db, sample_document):
    target = type(sample_document)(
        id=uuid.uuid4(),
        filename="target-2.pdf",
        original_path="/tmp/target-2.pdf",
        file_type="pdf",
        file_size=2048,
        mime_type="application/pdf",
        processing_status="completed",
        source="upload",
        user_id=sample_document.user_id,
    )
    db.add(target)
    db.commit()

    first = relationship_review_service.create_or_refresh_pending(
        db,
        source_document_id=sample_document.id,
        target_document_id=target.id,
        relationship_type="similar",
        confidence=0.71,
        reason_codes_json=["model_detection"],
    )
    db.commit()
    db.refresh(first)

    second = relationship_review_service.create_or_refresh_pending(
        db,
        source_document_id=sample_document.id,
        target_document_id=target.id,
        relationship_type="similar",
        confidence=0.88,
        reason_codes_json=["rescored"],
    )
    db.commit()
    db.refresh(second)

    reviews = (
        db.query(DocumentRelationshipReview)
        .filter(
            DocumentRelationshipReview.source_document_id == sample_document.id,
            DocumentRelationshipReview.target_document_id == target.id,
            DocumentRelationshipReview.relationship_type == "similar",
            DocumentRelationshipReview.status == "pending",
        )
        .all()
    )

    assert first.id == second.id
    assert len(reviews) == 1
    assert reviews[0].confidence == 0.88
    assert reviews[0].reason_codes_json == ["rescored"]
