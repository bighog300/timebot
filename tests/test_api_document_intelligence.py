import uuid

from app.models.category import Category
from app.models.intelligence import DocumentActionItem, DocumentIntelligence, DocumentReviewItem


def test_get_document_intelligence_returns_payload(client, db, sample_document):
    intelligence = DocumentIntelligence(
        document_id=sample_document.id,
        summary="AI summary",
        key_points=["k1"],
        suggested_tags=["finance"],
        entities={"orgs": ["Acme"]},
        confidence="medium",
        category_status="suggested",
    )
    db.add(intelligence)
    db.commit()

    response = client.get(f"/api/v1/documents/{sample_document.id}/intelligence")
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == "AI summary"
    assert payload["document_id"] == str(sample_document.id)


def test_patch_document_intelligence_updates_fields(client, db, sample_document):
    intelligence = DocumentIntelligence(
        document_id=sample_document.id,
        summary="old",
        key_points=["old"],
        confidence="low",
        category_status="suggested",
    )
    db.add(intelligence)
    db.commit()

    response = client.patch(
        f"/api/v1/documents/{sample_document.id}/intelligence",
        json={"summary": "new summary", "suggested_tags": ["important"]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == "new summary"
    assert payload["suggested_tags"] == ["important"]


def test_category_approve_assigns_user_category_and_resolves_uncategorized(client, db, sample_document):
    category = Category(name="Finance", slug="finance")
    db.add(category)
    db.commit()
    db.refresh(category)

    intelligence = DocumentIntelligence(
        document_id=sample_document.id,
        suggested_category_id=category.id,
        confidence="high",
        category_status="suggested",
    )
    review = DocumentReviewItem(
        document_id=sample_document.id,
        review_type="uncategorized",
        status="open",
        reason="needs category",
    )
    db.add(intelligence)
    db.add(review)
    db.commit()

    response = client.post(f"/api/v1/documents/{sample_document.id}/category/approve")
    assert response.status_code == 200

    db.refresh(intelligence)
    db.refresh(review)
    db.refresh(sample_document)
    assert sample_document.user_category_id == category.id
    assert intelligence.category_status == "approved"
    assert review.status == "resolved"


def test_category_override_assigns_selected_category(client, db, sample_document):
    suggested = Category(name="Suggested", slug="suggested")
    chosen = Category(name="Chosen", slug="chosen")
    db.add(suggested)
    db.add(chosen)
    db.commit()
    db.refresh(chosen)

    intelligence = DocumentIntelligence(
        document_id=sample_document.id,
        suggested_category_id=suggested.id,
        confidence="high",
        category_status="suggested",
    )
    db.add(intelligence)
    db.commit()

    response = client.post(
        f"/api/v1/documents/{sample_document.id}/category/override",
        json={"category_id": str(chosen.id)},
    )
    assert response.status_code == 200

    db.refresh(sample_document)
    db.refresh(intelligence)
    assert sample_document.user_category_id == chosen.id
    assert intelligence.category_status == "overridden"


def test_review_items_list_get_and_resolve(client, db, sample_document):
    review_item = DocumentReviewItem(
        id=uuid.uuid4(),
        document_id=sample_document.id,
        review_type="missing_tags",
        status="open",
        reason="No tags",
    )
    db.add(review_item)
    db.commit()

    list_resp = client.get("/api/v1/review/items")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    get_resp = client.get(f"/api/v1/review/items/{review_item.id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["review_type"] == "missing_tags"

    resolve_resp = client.post(f"/api/v1/review/items/{review_item.id}/resolve", json={"note": "resolved"})
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "resolved"


def test_action_item_endpoints_complete_and_dismiss(client, db, sample_document):
    action_item = DocumentActionItem(document_id=sample_document.id, content="Follow up with finance")
    db.add(action_item)
    db.commit()
    db.refresh(action_item)

    list_resp = client.get("/api/v1/action-items")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    doc_list_resp = client.get(f"/api/v1/documents/{sample_document.id}/action-items")
    assert doc_list_resp.status_code == 200
    assert len(doc_list_resp.json()) == 1

    patch_resp = client.patch(f"/api/v1/action-items/{action_item.id}", json={"content": "Updated follow-up"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["content"] == "Updated follow-up"

    complete_resp = client.post(f"/api/v1/action-items/{action_item.id}/complete")
    assert complete_resp.status_code == 200
    assert complete_resp.json()["state"] == "completed"

    dismiss_resp = client.post(f"/api/v1/action-items/{action_item.id}/dismiss")
    assert dismiss_resp.status_code == 200
    assert dismiss_resp.json()["state"] == "dismissed"
