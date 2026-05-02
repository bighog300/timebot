import uuid
from unittest.mock import patch
from unittest.mock import PropertyMock

from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.main import app
from app.models.document import Document
from app.models.relationships import DocumentRelationship
from app.models.user import User
from app.services.auth import auth_service
from app.services.relationship_detection import relationship_detection_service


def _mk_user(db, email: str, role: str = "editor") -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=auth_service.hash_password("password123"),
        display_name=email.split("@")[0],
        is_active=True,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _mk_doc(db, user_id, name, entities=None, summary="alpha roadmap update"):
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
        is_archived=False,
        summary=summary,
        entities=entities or {},
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_relationship_detect_requires_authentication(db, sample_document):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides.pop(get_current_user, None)
    with TestClient(app) as unauth_client:
        resp = unauth_client.post(f"/api/v1/search/relationships/detect/{sample_document.id}")
    app.dependency_overrides.clear()
    assert resp.status_code == 401


def test_relationship_detect_cross_user_hidden_as_not_found(client, db, test_user, grant_pro_subscription):
    grant_pro_subscription(test_user.id)
    other = _mk_user(db, "other@example.com")
    other_doc = _mk_doc(db, other.id, "other.pdf")
    resp = client.post(f"/api/v1/search/relationships/detect/{other_doc.id}")
    assert resp.status_code == 404


def test_relationship_backfill_non_admin_forbidden(db, test_user):
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as local_client:
        resp = local_client.post("/api/v1/search/relationships/backfill")
    app.dependency_overrides.clear()
    assert resp.status_code == 403


def test_relationship_backfill_admin_allowed(db, grant_pro_subscription):
    admin = _mk_user(db, "admin@example.com", role="admin")
    grant_pro_subscription(admin.id)
    _mk_doc(db, admin.id, "a.pdf")
    _mk_doc(db, admin.id, "b.pdf")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: admin
    with TestClient(app) as local_client:
        resp = local_client.post("/api/v1/search/relationships/backfill")
    app.dependency_overrides.clear()
    assert resp.status_code == 200


def test_entity_overlap_handles_string_dict_and_nested_values():
    left = {"person": " Alice  Smith ", "meta": {"team": ["Blue", {"region": "US"}]}}
    right = {"person": ["alice smith"], "meta": [{"team": {"region": "us"}}, "blue"]}
    overlap = relationship_detection_service._entity_overlap(left, right)
    assert overlap > 0.0


def test_duplicate_relationship_not_recreated(db, test_user):
    a = _mk_doc(db, test_user.id, "dup-a.pdf")
    b = _mk_doc(db, test_user.id, "dup-b.pdf")
    relationship_detection_service.detect_for_document(db, a.id)
    first_count = db.query(DocumentRelationship).count()
    relationship_detection_service.detect_for_document(db, a.id)
    second_count = db.query(DocumentRelationship).count()
    assert first_count == second_count


def test_structural_relationship_not_overwritten(db, test_user):
    a = _mk_doc(db, test_user.id, "thread-a.pdf")
    b = _mk_doc(db, test_user.id, "thread-b.pdf")
    db.add(
        DocumentRelationship(
            source_doc_id=min(a.id, b.id, key=str),
            target_doc_id=max(a.id, b.id, key=str),
            relationship_type="attachment",
            confidence=1.0,
            relationship_metadata={"gmail_message_id": "m1"},
        )
    )
    db.commit()
    relationship_detection_service.detect_for_document(db, a.id)
    generic = db.query(DocumentRelationship).filter(DocumentRelationship.relationship_type.in_(("related_to", "similar_to", "follows_up", "duplicates"))).all()
    assert generic == []


def test_semantic_lookup_cache_avoids_repeated_searches(db, test_user, monkeypatch):
    source = _mk_doc(db, test_user.id, "source.pdf")
    _mk_doc(db, test_user.id, "cand1.pdf")
    _mk_doc(db, test_user.id, "cand2.pdf")

    calls = {"count": 0}

    def _fake_find_similar_documents(document_id, limit=30):
        calls["count"] += 1
        return []

    with patch("app.services.embedding_service.EmbeddingService.enabled", new_callable=PropertyMock, return_value=True), patch(
        "app.services.relationship_detection.embedding_service.find_similar_documents", side_effect=_fake_find_similar_documents
    ):
        relationship_detection_service.detect_for_document(db, source.id)
    assert calls["count"] == 1
