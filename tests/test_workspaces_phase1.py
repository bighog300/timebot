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
    app.dependency_overrides.clear()
    assert accept.status_code == 200
    assert db.query(WorkspaceMember).filter(WorkspaceMember.workspace_id == ws["id"], WorkspaceMember.user_id == joiner.id).first() is not None
    member_token = auth_service.create_access_token(member_user)
    denied = client.post(f'/api/v1/workspaces/{ws["id"]}/invites', json={"email":"x@example.com","role":"member"}, headers={"Authorization": f"Bearer {member_token}"})
    assert denied.status_code == 403
    owner_remove = client.delete(f'/api/v1/workspaces/{ws["id"]}/members/{test_user.id}')
    assert owner_remove.status_code == 400


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
