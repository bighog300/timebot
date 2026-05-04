import uuid
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.auth import auth_service


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


def test_non_admin_blocked(db):
    editor = _mk_user(db, 'editor@example.com', 'editor')
    with _client_with_user(db, editor) as c:
        assert c.get('/api/v1/admin/system-intelligence/documents').status_code == 403


def test_admin_document_lifecycle_and_audit(db):
    admin = _mk_user(db, 'admin@example.com', 'admin')
    with _client_with_user(db, admin) as c:
        created = c.post('/api/v1/admin/system-intelligence/documents', data={'source_type':'admin_upload','title':'Doc A'}, files={'file': ('doc.txt', b'hello extraction text', 'text/plain')}).json()
        doc_id = created['id']
        assert created['mime_type'] == 'text/plain'
        assert created['original_filename'] == 'doc.txt'
        assert created['extraction_status'] == 'extracted'
        assert created['index_status'] == 'indexed'
        assert c.post(f'/api/v1/admin/system-intelligence/documents/{doc_id}/archive').json()['status'] == 'archived'
        assert c.post(f'/api/v1/admin/system-intelligence/documents/{doc_id}/activate').json()['status'] == 'active'
        assert c.delete(f'/api/v1/admin/system-intelligence/documents/{doc_id}').status_code == 200
        logs = c.get('/api/v1/admin/system-intelligence/audit-log').json()
        assert any(l['action'] == 'document_created' for l in logs)


def test_upload_rejects_unsupported_type(db):
    admin = _mk_user(db, 'admin4@example.com', 'admin')
    with _client_with_user(db, admin) as c:
        resp = c.post('/api/v1/admin/system-intelligence/documents', data={'source_type':'admin_upload','title':'Doc Bad'}, files={'file': ('malware.exe', b'X', 'application/octet-stream')})
        assert resp.status_code == 400


def test_reindex_rebuilds_chunks(db):
    from app.models.system_intelligence import SystemIntelligenceChunk
    admin = _mk_user(db, 'admin5@example.com', 'admin')
    with _client_with_user(db, admin) as c:
        created = c.post('/api/v1/admin/system-intelligence/documents', data={'source_type':'admin_upload','title':'Doc A'}, files={'file': ('doc.txt', b'hello extraction text again', 'text/plain')}).json()
        doc_id = created['id']
        before = db.query(SystemIntelligenceChunk).count()
        c.post(f'/api/v1/admin/system-intelligence/documents/{doc_id}/reindex')
        after = db.query(SystemIntelligenceChunk).count()
        assert after >= before


def test_submission_and_moderation(db):
    user = _mk_user(db, 'user@example.com', 'editor')
    admin = _mk_user(db, 'admin2@example.com', 'admin')
    with _client_with_user(db, user) as c:
        sub = c.post('/api/v1/system-intelligence/submissions', json={'title':'User Rec','reason':'good'}).json()
        assert sub['status'] == 'pending'
    with _client_with_user(db, admin) as c:
        approved = c.post(f"/api/v1/admin/system-intelligence/submissions/{sub['id']}/approve", json={'admin_notes':'ok'}).json()
        assert approved['status'] == 'approved'
        rejected = c.post(f"/api/v1/admin/system-intelligence/submissions/{sub['id']}/reject", json={'admin_notes':'no'}).json()
        assert rejected['status'] == 'rejected'


def test_web_reference_flow(db):
    admin = _mk_user(db, 'admin3@example.com', 'admin')
    with _client_with_user(db, admin) as c:
        ref = c.post('/api/v1/admin/system-intelligence/web-references', json={'title':'Case','url':'https://saflii.org/x'}).json()
        rid = ref['id']
        assert c.post(f'/api/v1/admin/system-intelligence/web-references/{rid}/approve').json()['status'] == 'active'
        assert c.post(f'/api/v1/admin/system-intelligence/web-references/{rid}/archive').json()['status'] == 'archived'
