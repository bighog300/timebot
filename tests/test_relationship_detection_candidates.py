import uuid

from app.models.document import Document
from app.models.intelligence import DocumentRelationshipReview
from app.models.relationships import DocumentRelationship
from app.services.relationship_detection import relationship_detection_service


def _mk(db, user_id, name, *, category=None, summary="", entities=None):
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
        ai_category_id=category,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_same_category_and_summary_overlap_creates_raw_relationship(db, test_user):
    cat = uuid.uuid4()
    a = _mk(db, test_user.id, "q1-plan.pdf", category=cat, summary="Quarterly budget planning and hiring roadmap")
    b = _mk(db, test_user.id, "q1-update.pdf", category=cat, summary="Hiring roadmap and budget planning update")

    result = relationship_detection_service.detect_for_document(db, a.id)
    assert result["created"] >= 1

    rel = db.query(DocumentRelationship).filter(DocumentRelationship.source_doc_id == min(a.id, b.id, key=str)).first()
    assert rel is not None


def test_shared_timeline_date_and_entity_creates_relationship(db, test_user):
    a = _mk(db, test_user.id, "incident-1.pdf", summary="Incident on 2026-01-05 involving Team Red", entities={"dates": ["2026-01-05"], "teams": ["Team Red"]})
    b = _mk(db, test_user.id, "incident-follow-up.pdf", summary="Follow up on 2026-01-05 for Team Red", entities={"dates": ["2026-01-05"], "teams": ["Team Red"]})

    result = relationship_detection_service.detect_for_document(db, a.id)
    assert result["created"] >= 1


def test_unrelated_docs_do_not_create_relationship(db, test_user):
    a = _mk(db, test_user.id, "gardening.pdf", summary="Tips for tomato gardening in spring")
    _mk(db, test_user.id, "taxes.pdf", summary="Corporate tax filing appendix and schedules")

    result = relationship_detection_service.detect_for_document(db, a.id)
    assert result["created"] == 0


def test_pending_review_created_from_raw_relationship(db, test_user):
    a = _mk(db, test_user.id, "alpha.pdf", summary="Alpha project roadmap launch")
    b = _mk(db, test_user.id, "alpha-update.pdf", summary="Alpha project launch roadmap update")

    relationship_detection_service.detect_for_document(db, a.id)

    rel = db.query(DocumentRelationship).filter(DocumentRelationship.source_doc_id == min(a.id, b.id, key=str)).first()
    assert rel is not None
    review = db.query(DocumentRelationshipReview).filter(DocumentRelationshipReview.source_document_id == rel.source_doc_id).first()
    assert review is not None
    assert review.status == "pending"


def test_detection_skips_when_thread_relationship_exists(db, test_user):
    a = _mk(db, test_user.id, "alpha-thread-1.pdf", summary="Alpha project roadmap launch")
    b = _mk(db, test_user.id, "alpha-thread-2.pdf", summary="Alpha project launch roadmap update")
    db.add(DocumentRelationship(
        source_doc_id=min(a.id, b.id, key=str),
        target_doc_id=max(a.id, b.id, key=str),
        relationship_type="thread",
        confidence=0.99,
        relationship_metadata={"gmail_thread_id": "t1"},
    ))
    db.commit()
    relationship_detection_service.detect_for_document(db, a.id)
    generic = db.query(DocumentRelationship).filter(
        DocumentRelationship.source_doc_id == min(a.id, b.id, key=str),
        DocumentRelationship.target_doc_id == max(a.id, b.id, key=str),
        DocumentRelationship.relationship_type.in_(("related_to", "similar_to", "follows_up", "duplicates")),
    ).all()
    assert generic == []
