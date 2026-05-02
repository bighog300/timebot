import uuid

from app.models.document import Document
from app.models.processing_event import DocumentProcessingEvent


def test_admin_can_list_document_processing_events(client, db, test_user):
    test_user.role = "admin"
    doc = Document(
        id=uuid.uuid4(),
        filename="x.txt",
        original_path="/tmp/x.txt",
        file_type="txt",
        file_size=1,
        source="upload",
        user_id=test_user.id,
        processing_status="queued",
    )
    db.add(doc)
    db.commit()
    db.add(DocumentProcessingEvent(document_id=doc.id, user_id=test_user.id, stage="queued", event_type="upload_accepted", status="success", message="ok", severity="info", safe_metadata={}))
    db.commit()

    r = client.get(f"/api/v1/admin/documents/{doc.id}/events")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_non_admin_cannot_list_processing_events(client, db, test_user):
    test_user.role = "viewer"
    db.commit()
    r = client.get("/api/v1/admin/processing-events")
    assert r.status_code == 403
