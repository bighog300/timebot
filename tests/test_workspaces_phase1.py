from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_user, get_db
from app.models.workspace import Workspace, WorkspaceInvite
from app.models.document import Document
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.services.auth import auth_service


def _mk_user(db, email: str):
    user = User(email=email, password_hash=auth_service.hash_password("password123"), display_name=email.split("@")[0], is_active=True, role="editor")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_register_creates_personal_workspace(client):
    r = client.post('/api/v1/auth/register', json={'email':'ws1@example.com','display_name':'Ws1','password':'Password123!@#'})
    assert r.status_code == 201
    token = r.json()['access_token']
    me = client.get('/api/v1/workspaces', headers={'Authorization': f'Bearer {token}'})
    assert me.status_code == 200
    items = me.json()
    assert len(items) >= 1
    assert any(w['type'] == 'personal' for w in items)


def test_workspace_invite_accept_creates_membership_and_non_admin_cannot_invite_and_owner_cannot_be_removed(client, db, test_user):
    ws = client.post('/api/v1/workspaces', json={'name': 'Team'}).json()
    member_user = _mk_user(db, "member@example.com")
    db.add(WorkspaceMember(workspace_id=ws["id"], user_id=member_user.id, role="member")); db.commit()
    import hashlib, secrets
    token = secrets.token_urlsafe(16)
    db.add(WorkspaceInvite(workspace_id=ws["id"], email="joiner@example.com", role="member", token_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(), invited_by_user_id=test_user.id, expires_at=datetime.now(timezone.utc) + timedelta(days=1)))
    db.commit()
    joiner = _mk_user(db, "joiner@example.com")

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: joiner
    with TestClient(app) as local_client:
        accept = local_client.post(f'/api/v1/workspaces/invites/{token}/accept')
    assert accept.status_code == 200
    assert db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws["id"], WorkspaceMember.user_id == joiner.id).first() is not None

    app.dependency_overrides[get_current_user] = lambda: member_user
    with TestClient(app) as local_client:
        denied = local_client.post(f'/api/v1/workspaces/{ws["id"]}/invites', json={"email":"x@example.com","role":"member"})
    assert denied.status_code == 403

    app.dependency_overrides[get_current_user] = lambda: test_user
    with TestClient(app) as local_client:
        owner_remove = local_client.delete(f'/api/v1/workspaces/{ws["id"]}/members/{test_user.id}')
    assert owner_remove.status_code == 400
    app.dependency_overrides.clear()


def test_workspace_invite_email_mismatch_blocked(client, db, test_user):
    ws = client.post('/api/v1/workspaces', json={'name': 'Team'}).json()
    created = client.post(f'/api/v1/workspaces/{ws["id"]}/invites', json={"email": "a@example.com", "role": "member"})
    token = created.json()["dev_invite_link"].split("/invites/")[1].split("/accept")[0]
    other = _mk_user(db, "b@example.com")
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: other
    with TestClient(app) as local_client:
        denied = local_client.post(f'/api/v1/workspaces/invites/{token}/accept')
    assert denied.status_code == 400
    app.dependency_overrides.clear()


def test_document_access_isolation_and_membership(client, db, test_user):
    ws = client.post('/api/v1/workspaces', json={'name': 'Shared'}).json()
    other = _mk_user(db, "other@example.com")
    other_ws = Workspace(name="Other", type="team", owner_user_id=other.id); db.add(other_ws); db.flush()
    db.add(WorkspaceMember(workspace_id=other_ws.id, user_id=other.id, role="owner"))
    doc = Document(filename="x.pdf", original_path="/tmp/x", file_type="pdf", file_size=1, mime_type="application/pdf", processing_status="completed", source="upload", user_id=test_user.id, workspace_id=ws["id"])
    db.add(doc); db.commit(); db.refresh(doc)
    db.add(WorkspaceMember(workspace_id=ws["id"], user_id=other.id, role="member")); db.commit()
    other_token = auth_service.create_access_token(other)
    ok = client.get(f'/api/v1/documents/{doc.id}', headers={"Authorization": f"Bearer {other_token}", "X-Workspace-ID": ws["id"]})
    assert ok.status_code == 200
    forbidden = client.get(f'/api/v1/documents/{doc.id}', headers={"Authorization": f"Bearer {other_token}", "X-Workspace-ID": str(other_ws.id)})
    assert forbidden.status_code in (403, 404)


def test_workspace_document_crud_isolation_across_workspaces(client, db, test_user):
    ws1 = client.post('/api/v1/workspaces', json={'name': 'One'}).json()
    ws2 = client.post('/api/v1/workspaces', json={'name': 'Two'}).json()
    doc = Document(filename='a.pdf', original_path='/tmp/a', file_type='pdf', file_size=1, mime_type='application/pdf', processing_status='completed', source='upload', user_id=test_user.id, workspace_id=ws1['id'])
    db.add(doc); db.commit(); db.refresh(doc)

    listed = client.get('/api/v1/documents/', headers={'X-Workspace-ID': ws2['id']})
    assert listed.status_code == 200
    assert all(d['id'] != str(doc.id) for d in listed.json())

    for method, path, payload in [
        ('get', f'/api/v1/documents/{doc.id}', None),
        ('put', f'/api/v1/documents/{doc.id}', {'filename': 'renamed.pdf'}),
        ('delete', f'/api/v1/documents/{doc.id}', None),
    ]:
        resp = getattr(client, method)(path, headers={'X-Workspace-ID': ws2['id']}, json=payload) if payload else getattr(client, method)(path, headers={'X-Workspace-ID': ws2['id']})
        assert resp.status_code == 404


def test_upload_uses_active_workspace_header_and_personal_fallback(client, db, test_user, monkeypatch):
    captured = []

    async def fake_process_upload(db_sess, file, user, workspace_id):
        captured.append(str(workspace_id))
        return SimpleNamespace(
            id='00000000-0000-0000-0000-000000000001', filename='f.txt', original_path='/tmp/f.txt', file_type='txt', file_size=1, mime_type='text/plain',
            processing_status='completed', source='upload', upload_date=datetime.now(timezone.utc), summary=None, ai_tags=[], key_points=[], entities={}, action_items=[],
            user_id=user.id, workspace_id=workspace_id, created_at=None, updated_at=None, is_archived=False, archived_at=None,
            review_status='pending', reviewed_at=None, reviewed_by=None, override_summary=None, override_tags=None
        )

    monkeypatch.setattr('app.api.v1.upload.enforce_rate_limit', lambda *a, **k: None)
    monkeypatch.setattr('app.api.v1.upload.enforce_daily_cap', lambda *a, **k: None)
    monkeypatch.setattr('app.api.v1.upload.enforce_limit', lambda *a, **k: None)
    monkeypatch.setattr('app.api.v1.upload.record_usage', lambda *a, **k: None)
    monkeypatch.setattr('app.api.v1.upload.document_processor.process_upload', fake_process_upload)

    team_ws = client.post('/api/v1/workspaces', json={'name': 'Uploads'}).json()
    client.post('/api/v1/upload', headers={'X-Workspace-ID': team_ws['id']}, files={'file': ('a.txt', b'hello', 'text/plain')})
    client.post('/api/v1/upload', files={'file': ('b.txt', b'world', 'text/plain')})

    assert len(captured) == 2
    assert captured[0] == team_ws['id']
    personal_ws = next(w for w in client.get('/api/v1/workspaces').json() if w['type'] == 'personal')
    assert captured[1] == personal_ws['id']
