from app.models.admin_audit import AdminAuditEvent
from app.models.messaging import Notification


def test_user_create_message_and_admin_reply_creates_notification_and_audit(client, db, test_user):
    thread = client.post('/api/v1/messages', json={'category': 'support', 'subject': 'Help', 'body': 'Need support'}).json()
    assert thread['subject'] == 'Help'

    admin = db.query(type(test_user)).filter(type(test_user).id == test_user.id).first()
    admin.role = 'admin'; db.commit()

    reply = client.post(f"/api/v1/admin/messages/{thread['id']}/reply", json={'body': 'We are on it'})
    assert reply.status_code == 200

    notif = db.query(Notification).filter(Notification.user_id == test_user.id).first()
    assert notif is not None
    ev = db.query(AdminAuditEvent).filter(AdminAuditEvent.entity_id == thread['id'], AdminAuditEvent.action == 'admin_message_reply').first()
    assert ev is not None


def test_user_cannot_read_other_users_notifications_or_threads(client, db, test_user):
    from app.models.user import User
    from app.models.messaging import UserMessageThread, Notification
    from app.services.auth import auth_service
    other = User(email='other2@example.com', password_hash=auth_service.hash_password('password123'), display_name='Other', is_active=True, role='viewer')
    db.add(other); db.commit(); db.refresh(other)
    thread = UserMessageThread(user_id=other.id, category='support', subject='private', status='open')
    note = Notification(user_id=other.id, type='admin_reply', title='p', body='p', metadata_json={})
    db.add_all([thread, note]); db.commit(); db.refresh(thread); db.refresh(note)
    assert client.get(f"/api/v1/messages/{thread.id}").status_code == 404
    assert client.post(f"/api/v1/notifications/{note.id}/read").status_code == 404


def test_notification_read_flows_and_ordering(client, db, test_user):
    from datetime import datetime, timedelta, timezone
    from app.models.messaging import Notification
    n1 = Notification(user_id=test_user.id, type='admin_reply', title='Older', body='old', metadata_json={}, created_at=datetime.now(timezone.utc) - timedelta(days=1))
    n2 = Notification(user_id=test_user.id, type='admin_reply', title='Newer', body='new', metadata_json={}, created_at=datetime.now(timezone.utc))
    db.add_all([n1, n2]); db.commit(); db.refresh(n1); db.refresh(n2)

    items = client.get('/api/v1/notifications').json()
    assert [n['id'] for n in items][:2] == [str(n2.id), str(n1.id)]
    assert items[0]['read_at'] is None

    assert client.post(f'/api/v1/notifications/{n2.id}/read').status_code == 200
    db.refresh(n2)
    assert n2.read_at is not None

    assert client.post('/api/v1/notifications/read-all').status_code == 200
    db.refresh(n1)
    assert n1.read_at is not None


def test_message_thread_permissions_admin_flows_workspace_membership(client, db, test_user):
    from app.models.workspace import Workspace, WorkspaceMember
    from app.models.user import User
    from app.services.auth import auth_service

    ws = Workspace(name='Team WS', owner_user_id=test_user.id)
    db.add(ws); db.commit(); db.refresh(ws)
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=test_user.id, role='owner')); db.commit()

    create_ok = client.post('/api/v1/messages', json={'category': 'support', 'subject': 'WS', 'body': 'body', 'workspace_id': str(ws.id)})
    assert create_ok.status_code == 201
    thread = create_ok.json()
    assert thread['workspace_id'] == str(ws.id)

    assert client.post(f"/api/v1/messages/{thread['id']}/reply", json={'body': 'user reply'}).status_code == 200

    other = User(email='other3@example.com', password_hash=auth_service.hash_password('password123'), display_name='Other3', is_active=True, role='viewer')
    db.add(other); db.commit(); db.refresh(other)
    other_ws = Workspace(name='Other WS', owner_user_id=other.id)
    db.add(other_ws); db.commit(); db.refresh(other_ws)
    denied_create = client.post('/api/v1/messages', json={'category': 'support', 'subject': 'No', 'body': 'no', 'workspace_id': str(other_ws.id)})
    assert denied_create.status_code == 403

    admin = db.query(type(test_user)).filter(type(test_user).id == test_user.id).first()
    admin.role = 'admin'; db.commit()

    admin_list = client.get('/api/v1/admin/messages')
    assert admin_list.status_code == 200
    assert any(item['id'] == thread['id'] for item in admin_list.json())
    assert client.get(f"/api/v1/admin/messages/{thread['id']}").status_code == 200
    assert client.patch(f"/api/v1/admin/messages/{thread['id']}", json={'status': 'in_progress'}).status_code == 200
    assert client.post(f"/api/v1/admin/messages/{thread['id']}/reply", json={'body': 'admin answer'}).status_code == 200

    status_event = db.query(AdminAuditEvent).filter(AdminAuditEvent.entity_id == thread['id'], AdminAuditEvent.action == 'admin_message_status_updated').first()
    reply_event = db.query(AdminAuditEvent).filter(AdminAuditEvent.entity_id == thread['id'], AdminAuditEvent.action == 'admin_message_reply').first()
    notif = db.query(Notification).filter(Notification.user_id == test_user.id, Notification.link_url.like(f"%{thread['id']}%")).first()
    assert status_event is not None
    assert reply_event is not None
    assert notif is not None
