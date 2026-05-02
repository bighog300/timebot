import uuid

from app.models.document import Document
from app.models.relationships import DocumentRelationship


def _mk_doc(db, user_id, filename, *, summary="", entities=None):
    doc = Document(
        id=uuid.uuid4(),
        filename=filename,
        original_path=f"/tmp/{filename}",
        file_type="txt",
        file_size=1,
        mime_type="text/plain",
        processing_status="completed",
        source="upload",
        user_id=user_id,
        summary=summary,
        entities=entities or {},
        is_archived=False,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_structured_risk_and_milestone_generated(client, db, test_user, grant_pro_subscription):
    grant_pro_subscription(test_user.id)
    _mk_doc(
        db,
        test_user.id,
        "roadmap.txt",
        summary="There is a project risk due to an urgent dependency.",
        entities={"timeline_events": [{"title": "Q3 Milestone", "date": "2026-08-01", "category": "milestone"}]},
    )
    res = client.get("/api/v1/insights/structured")
    assert res.status_code == 200
    data = res.json()
    types = {i["type"] for i in data["insights"]}
    assert "risk" in types
    assert "milestone" in types


def test_structured_missing_information_generated_conservatively(client, db, test_user, grant_pro_subscription):
    grant_pro_subscription(test_user.id)
    _mk_doc(
        db,
        test_user.id,
        "missing-date.txt",
        entities={"timeline_events": [{"title": "Kickoff event"}]},
    )
    res = client.get("/api/v1/insights/structured")
    assert res.status_code == 200
    missing = [i for i in res.json()["insights"] if i["type"] == "missing_information"]
    assert missing


def test_structured_insights_user_isolation(client, db, test_user, grant_pro_subscription):
    grant_pro_subscription(test_user.id)
    mine = _mk_doc(db, test_user.id, "mydoc.txt", summary="deadline tomorrow")
    other_user_id = uuid.uuid4()
    other_doc = _mk_doc(db, other_user_id, "other.txt", summary="urgent risk")
    res = client.get("/api/v1/insights/structured")
    assert res.status_code == 200
    related = {doc_id for i in res.json()["insights"] for doc_id in i["related_document_ids"]}
    assert str(mine.id) in related
    assert str(other_doc.id) not in related


def test_structured_no_insight_without_evidence(client, db, test_user, grant_pro_subscription):
    grant_pro_subscription(test_user.id)
    _mk_doc(db, test_user.id, "plain.txt", summary="Routine status update.", entities={"timeline_events": [{"title": "General update", "date": "2026-01-01"}]})
    res = client.get("/api/v1/insights/structured")
    assert res.status_code == 200
    assert res.json()["count"] == 0


def test_structured_inconsistency_from_conflicting_thread_outcomes(client, db, test_user, grant_pro_subscription):
    grant_pro_subscription(test_user.id)
    left = _mk_doc(db, test_user.id, "a.txt")
    right = _mk_doc(db, test_user.id, "b.txt")
    db.add(DocumentRelationship(source_doc_id=left.id, target_doc_id=right.id, relationship_type="thread", relationship_metadata={"thread_outcome": "approved", "reason": "message says approved"}))
    db.add(DocumentRelationship(source_doc_id=right.id, target_doc_id=left.id, relationship_type="thread", relationship_metadata={"thread_outcome": "rejected", "reason": "message says rejected"}))
    db.commit()
    res = client.get("/api/v1/insights/structured")
    assert res.status_code == 200
    assert any(i["type"] == "inconsistency" for i in res.json()["insights"])
