import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db, get_current_user
from app.models.document import Document
from app.models.system_intelligence import SystemIntelligenceAuditLog, SystemIntelligenceChunk, SystemIntelligenceDocument, SystemIntelligenceWebReference
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.services.auth import auth_service
from app.services.legal_web_reference_capture import LegalWebReferenceCaptureInput, LegalWebReferenceCaptureService
from app.services.chat_retrieval import retrieve_chat_context


def _client_with_user(db, user):
    def override_get_db():
        yield db
    def override_get_current_user():
        return user
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    return TestClient(app)


def _mk_user(db, email: str, role: str):
    u = User(id=uuid.uuid4(), email=email, password_hash=auth_service.hash_password('pw123456'), display_name=email.split('@')[0], is_active=True, role=role)
    db.add(u); db.commit(); db.refresh(u); return u


def _mk_doc(db, user: User, text: str = "sample content", workspace_id=None):
    d = Document(filename='doc.txt', original_path='/tmp/doc.txt', file_type='txt', file_size=len(text), mime_type='text/plain', source='upload', user_id=user.id, workspace_id=workspace_id, processing_status='completed', raw_text=text)
    db.add(d); db.commit(); db.refresh(d); return d


def test_submission_access_and_duplicate_rules(db):
    owner = _mk_user(db, 'owner@example.com', 'editor')
    other = _mk_user(db, 'other@example.com', 'editor')
    doc = _mk_doc(db, owner)
    with _client_with_user(db, other) as c:
        denied = c.post('/api/v1/system-intelligence/submissions', json={'source_document_id': str(doc.id), 'title': 'x'})
        assert denied.status_code == 403
    with _client_with_user(db, owner) as c:
        ok = c.post('/api/v1/system-intelligence/submissions', json={'source_document_id': str(doc.id), 'title': 'Rec', 'reason': 'helpful'})
        assert ok.status_code == 200
        dup = c.post('/api/v1/system-intelligence/submissions', json={'source_document_id': str(doc.id), 'title': 'Rec2'})
        assert dup.status_code == 409


def test_workspace_member_can_recommend(db):
    owner = _mk_user(db, 'owner2@example.com', 'editor')
    member = _mk_user(db, 'member@example.com', 'editor')
    ws = Workspace(name='Team', type='team', owner_user_id=owner.id)
    db.add(ws); db.flush()
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=owner.id, role='owner'))
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=member.id, role='member'))
    db.commit()
    doc = _mk_doc(db, owner, workspace_id=ws.id)
    with _client_with_user(db, member) as c:
        resp = c.post('/api/v1/system-intelligence/submissions', json={'source_document_id': str(doc.id), 'title': 'Team Rec'})
        assert resp.status_code == 200


def test_admin_approval_creates_system_doc_and_chunks_and_audit(db):
    user = _mk_user(db, 'user@example.com', 'editor')
    admin = _mk_user(db, 'admin@example.com', 'admin')
    doc = _mk_doc(db, user, text='policy guidance ' * 200)
    with _client_with_user(db, user) as c:
        sub = c.post('/api/v1/system-intelligence/submissions', json={'source_document_id': str(doc.id), 'title': 'User Rec', 'reason': 'good'}).json()
    with _client_with_user(db, admin) as c:
        approved = c.post(f"/api/v1/admin/system-intelligence/submissions/{sub['id']}/approve", json={'admin_notes': 'ok'}).json()
        assert approved['status'] == 'approved'
    sid = approved['resulting_system_document_id']
    assert db.query(SystemIntelligenceDocument).filter(SystemIntelligenceDocument.id == sid).first() is not None
    assert db.query(SystemIntelligenceChunk).join(SystemIntelligenceDocument, SystemIntelligenceChunk.system_document_id == SystemIntelligenceDocument.id).filter(SystemIntelligenceDocument.id == sid).count() > 0
    assert db.query(SystemIntelligenceAuditLog).filter(SystemIntelligenceAuditLog.action == 'submission_approved').count() > 0


def test_approval_fails_if_missing_source_content(db):
    user = _mk_user(db, 'user3@example.com', 'editor')
    admin = _mk_user(db, 'admin3@example.com', 'admin')
    doc = _mk_doc(db, user, text='')
    with _client_with_user(db, user) as c:
        sub = c.post('/api/v1/system-intelligence/submissions', json={'source_document_id': str(doc.id), 'title': 'User Rec'}).json()
    with _client_with_user(db, admin) as c:
        resp = c.post(f"/api/v1/admin/system-intelligence/submissions/{sub['id']}/approve", json={'admin_notes': 'ok'})
        assert resp.status_code == 400


def test_admin_rejection_requires_notes_and_stores_fields(db):
    user = _mk_user(db, 'user2@example.com', 'editor')
    admin = _mk_user(db, 'admin2@example.com', 'admin')
    doc = _mk_doc(db, user)
    with _client_with_user(db, user) as c:
        sub = c.post('/api/v1/system-intelligence/submissions', json={'source_document_id': str(doc.id), 'title': 'User Rec'}).json()
    with _client_with_user(db, admin) as c:
        bad = c.post(f"/api/v1/admin/system-intelligence/submissions/{sub['id']}/reject", json={'admin_notes': ''})
        assert bad.status_code == 400
        rejected = c.post(f"/api/v1/admin/system-intelligence/submissions/{sub['id']}/reject", json={'admin_notes': 'not relevant'}).json()
        assert rejected['status'] == 'rejected'
        assert rejected['admin_notes'] == 'not relevant'
        assert rejected['reviewed_by_admin_id'] == str(admin.id)
        assert rejected['reviewed_at'] is not None


def test_capture_creates_candidate_and_dedupes(db):
    payload = LegalWebReferenceCaptureInput(
        title="ConCourt ruling",
        url="https://www.concourt.org.za/ruling",
        canonical_url="https://www.concourt.org.za/ruling",
        source_domain="concourt.org.za",
        jurisdiction="ZA",
        summary="summary",
    )
    created = LegalWebReferenceCaptureService.capture_candidate_reference(db, payload)
    db.commit()
    assert created.status == "candidate"
    duplicate = LegalWebReferenceCaptureService.capture_candidate_reference(db, payload)
    assert duplicate.id == created.id


def test_capture_marks_untrusted_domain(db):
    payload = LegalWebReferenceCaptureInput(
        title="Random blog",
        url="https://example.com/post",
        source_domain="example.com",
        summary="s",
    )
    created = LegalWebReferenceCaptureService.capture_candidate_reference(db, payload)
    db.commit()
    assert created.status == "untrusted"


def test_web_reference_admin_approval_and_retrieval_filters(db):
    admin = _mk_user(db, "admin-si@example.com", "admin")
    user = _mk_user(db, "user-si@example.com", "editor")
    with _client_with_user(db, admin) as c:
        candidate = c.post("/api/v1/admin/system-intelligence/web-references", json={"title": "A", "url": "https://justice.gov.za/a", "source_domain": "justice.gov.za"}).json()
        archived = c.post("/api/v1/admin/system-intelligence/web-references", json={"title": "B", "url": "https://justice.gov.za/b", "source_domain": "justice.gov.za"}).json()
        c.post(f"/api/v1/admin/system-intelligence/web-references/{candidate['id']}/approve")
        c.post(f"/api/v1/admin/system-intelligence/web-references/{archived['id']}/archive")
    untrusted = SystemIntelligenceWebReference(title="U", url="https://bad.example/u", source_domain="bad.example", status="untrusted")
    db.add(untrusted)
    db.commit()
    ctx = retrieve_chat_context(
        db=db,
        user_id=str(user.id),
        query="legal",
        document_ids=[],
        include_timeline=False,
        include_full_text=False,
        max_documents=5,
    )
    urls = {item["url"] for item in ctx["legal_web_refs"]}
    assert "https://justice.gov.za/a" in urls
    assert "https://justice.gov.za/b" not in urls
    assert "https://bad.example/u" not in urls
