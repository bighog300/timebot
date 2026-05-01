from app.models.document import Document
from app.services.document_intelligence import document_intelligence_service


def _mk_gmail_doc(db, user_id, name, summary, thread_id=None):
    metadata = {}
    if thread_id:
        metadata["gmail_thread_id"] = thread_id
    doc = Document(
        filename=name,
        original_path=f"/tmp/{name}",
        file_type="txt",
        file_size=10,
        mime_type="text/plain",
        processing_status="completed",
        source="gmail",
        user_id=user_id,
        extracted_metadata=metadata,
        raw_text=f"raw text for {name}",
        summary=summary,
        entities={},
        key_points=[],
        action_items=[],
        ai_tags=[],
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_same_thread_gets_shared_thread_summary(db, test_user):
    a = _mk_gmail_doc(db, test_user.id, "a.eml", "Initial customer request", thread_id="thread-1")
    b = _mk_gmail_doc(db, test_user.id, "b.eml", "Follow-up with resolution steps", thread_id="thread-1")

    analysis = {"summary": "Follow-up with resolution steps", "key_points": [], "tags": [], "entities": {}, "action_items": []}
    document_intelligence_service.create_from_analysis(db, b, analysis)
    db.refresh(a)
    db.refresh(b)

    assert a.extracted_metadata.get("thread_summary")
    assert a.extracted_metadata.get("thread_summary") == b.extracted_metadata.get("thread_summary")


def test_unrelated_emails_do_not_share_thread_summary(db, test_user):
    a = _mk_gmail_doc(db, test_user.id, "a.eml", "Budget discussion", thread_id="thread-a")
    b = _mk_gmail_doc(db, test_user.id, "b.eml", "Hiring discussion", thread_id="thread-b")

    analysis = {"summary": "Budget discussion", "key_points": [], "tags": [], "entities": {}, "action_items": []}
    document_intelligence_service.create_from_analysis(db, a, analysis)
    db.refresh(a)
    db.refresh(b)

    assert a.extracted_metadata.get("thread_summary") is None
    assert b.extracted_metadata.get("thread_summary") is None


def test_missing_gmail_thread_id_does_not_crash(db, test_user):
    doc = _mk_gmail_doc(db, test_user.id, "solo.eml", "One-off email", thread_id=None)

    analysis = {"summary": "One-off email", "key_points": [], "tags": [], "entities": {}, "action_items": []}
    document_intelligence_service.create_from_analysis(db, doc, analysis)
    db.refresh(doc)

    assert "thread_summary" not in (doc.extracted_metadata or {})


def test_individual_summary_preserved_with_thread_summary(db, test_user):
    _mk_gmail_doc(db, test_user.id, "a.eml", "Kickoff notes", thread_id="thread-9")
    b = _mk_gmail_doc(db, test_user.id, "b.eml", "Status update", thread_id="thread-9")

    analysis = {"summary": "Status update", "key_points": [], "tags": [], "entities": {}, "action_items": []}
    document_intelligence_service.create_from_analysis(db, b, analysis)
    db.refresh(b)

    assert b.summary == "Status update"
    assert b.extracted_metadata.get("thread_summary")
