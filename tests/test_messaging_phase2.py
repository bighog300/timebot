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
    t1 = client.post('/api/v1/messages', json={'category': 'bug_report', 'subject': 'Bug', 'body': 'broken'}).json()
    from app.models.user import User
    from app.services.auth import auth_service
    other = User(email='other2@example.com', password_hash=auth_service.hash_password('password123'), display_name='Other', is_active=True, role='viewer')
    db.add(other); db.commit(); db.refresh(other)
    tok = auth_service.create_access_token({'sub': str(other.id), 'email': other.email})
    h={'Authorization': f'Bearer {tok}'}
    assert client.get(f"/api/v1/messages/{t1['id']}", headers=h).status_code == 404
    assert client.get('/api/v1/notifications', headers=h).status_code == 200
