from uuid import uuid4

from app.models.document import Document
from app.models.intelligence import DocumentActionItem
from app.models.relationships import DocumentRelationship
from app.services.document_intelligence import document_intelligence_service
from app.services.relationship_detection import RelationshipCandidate, relationship_detection_service


def _analysis():
    return {
        "summary": "Contract review complete",
        "key_points": ["k1"],
        "tags": ["contract"],
        "entities": {},
        "action_items": ["Follow up with legal"],
        "timeline_events": [{"title": "Kickoff", "date": "2026-05-01", "confidence": 0.9}],
    }


def test_repeated_processing_does_not_duplicate_timeline_events(db, sample_document):
    analysis = _analysis()
    document_intelligence_service.create_from_analysis(db, sample_document, analysis)
    document_intelligence_service.create_from_analysis(db, sample_document, analysis)
    db.refresh(sample_document)
    events = (sample_document.entities or {}).get("timeline_events", [])
    assert len(events) <= 1
    if events:
        assert events[0]["title"] == "Kickoff"


def test_repeated_processing_does_not_duplicate_structural_relationships(db, test_user):
    a = Document(
        id=uuid4(), filename="a.pdf", original_path="/tmp/a.pdf", file_type="pdf", file_size=1, mime_type="application/pdf",
        processing_status="completed", source="upload", user_id=test_user.id
    )
    b = Document(
        id=uuid4(), filename="b.pdf", original_path="/tmp/b.pdf", file_type="pdf", file_size=1, mime_type="application/pdf",
        processing_status="completed", source="upload", user_id=test_user.id
    )
    db.add_all([a, b]); db.commit()
    candidate = RelationshipCandidate(
        source_doc_id=a.id, target_doc_id=b.id, relationship_type="related_to", confidence=0.7, metadata={}
    )
    relationship_detection_service._persist_candidates(db, [candidate])
    relationship_detection_service._persist_candidates(db, [candidate])
    rows = db.query(DocumentRelationship).filter(
        DocumentRelationship.source_doc_id == a.id,
        DocumentRelationship.target_doc_id == b.id,
        DocumentRelationship.relationship_type == "related_to",
    ).all()
    assert len(rows) == 1


def test_repeated_processing_preserves_existing_summary_and_intelligence(db, sample_document):
    analysis = _analysis()
    document_intelligence_service.create_from_analysis(db, sample_document, analysis)
    document_intelligence_service.create_from_analysis(db, sample_document, analysis)
    db.refresh(sample_document)
    assert sample_document.summary == "Contract review complete"
    events = (sample_document.entities or {}).get("timeline_events", [])
    assert len(events) <= 1
    action_items = db.query(DocumentActionItem).filter(DocumentActionItem.document_id == sample_document.id).all()
    assert len(action_items) == 1
    assert action_items[0].content == "Follow up with legal"


def test_retry_path_remains_safe_for_repeated_intelligence_persistence(db, sample_document):
    analysis = _analysis()
    for _ in range(3):
        document_intelligence_service.create_from_analysis(db, sample_document, analysis)
    db.refresh(sample_document)
    assert len((sample_document.entities or {}).get("timeline_events", [])) <= 1
    assert db.query(DocumentActionItem).filter(DocumentActionItem.document_id == sample_document.id).count() == 1
