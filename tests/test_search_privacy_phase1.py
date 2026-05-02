import uuid

from app.models.category import Category
from app.models.document import Document
from app.models.user import User
from app.services.auth import auth_service


def _mk_user(db, email: str, role: str = "editor") -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=auth_service.hash_password("password123"),
        display_name=email,
        is_active=True,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _mk_doc(db, user_id, name: str, ai_category_id=None, entities=None):
    doc = Document(
        id=uuid.uuid4(),
        filename=name,
        original_path=f"/tmp/{name}",
        file_type="pdf",
        file_size=100,
        mime_type="application/pdf",
        processing_status="completed",
        source="upload",
        user_id=user_id,
        summary="Risk and urgent timeline update",
        is_archived=False,
        entities=entities or {"timeline_events": [{"title": "Owner milestone", "date": "2026-06-01", "confidence": 0.9}]},
        ai_category_id=ai_category_id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_facets_timeline_and_insight_endpoints_are_user_scoped(client, db, test_user, grant_pro_subscription):
    grant_pro_subscription(test_user.id)
    other = _mk_user(db, "other-privacy@example.com")
    owner_cat = Category(name="Owner Category", slug="owner-category")
    other_cat = Category(name="Other Category", slug="other-category")
    db.add_all([owner_cat, other_cat])
    db.commit()

    _mk_doc(db, test_user.id, "owner.pdf", ai_category_id=owner_cat.id)
    _mk_doc(db, other.id, "other.pdf", ai_category_id=other_cat.id, entities={"timeline_events": [{"title": "Other secret", "date": "2026-06-01", "confidence": 0.9}]})

    facets = client.get("/api/v1/search/facets")
    assert facets.status_code == 200
    category_names = {row["name"] for row in facets.json().get("categories", [])}
    assert "Owner Category" in category_names
    assert "Other Category" not in category_names

    timeline = client.get("/api/v1/search/timeline")
    assert timeline.status_code == 200
    titles = {event["title"] for event in timeline.json().get("events", [])}
    assert "Owner milestone" in titles
    assert "Other secret" not in titles

    insights = client.get("/api/v1/search/insights")
    assert insights.status_code == 200
    recent_ids = {row["document_id"] for row in insights.json().get("recent_activity", [])}
    assert len(recent_ids) == 1

    intelligence = client.get("/api/v1/search/category-intelligence")
    assert intelligence.status_code == 200
    analytics = intelligence.json().get("analytics", [])
    total_docs = sum(row.get("document_count", 0) for row in analytics)
    assert total_docs <= 1


def test_relationship_detect_forbidden_for_other_users_document(client, db, test_user, grant_pro_subscription):
    grant_pro_subscription(test_user.id)
    other = _mk_user(db, "other-detect@example.com")
    other_doc = _mk_doc(db, other.id, "hidden.pdf")
    resp = client.post(f"/api/v1/search/relationships/detect/{other_doc.id}")
    assert resp.status_code == 404


def test_relationship_backfill_non_admin_rejected(client):
    resp = client.post("/api/v1/search/relationships/backfill")
    assert resp.status_code == 403
