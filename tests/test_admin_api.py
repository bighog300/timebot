import uuid

from app.models.admin_audit import AdminAuditEvent
from app.models.user import User


def test_admin_can_list_users(client, test_user, db):
    test_user.role = 'admin'; db.commit()
    r = client.get('/api/v1/admin/users')
    assert r.status_code == 200
    assert r.json()['total_count'] >= 1


def test_non_admin_cannot_list_users(client, test_user, db):
    test_user.role = 'viewer'; db.commit()
    r = client.get('/api/v1/admin/users')
    assert r.status_code == 403


def test_admin_can_update_role_and_audit(client, test_user, db):
    test_user.role='admin';
    target=User(id=uuid.uuid4(), email='u2@example.com', password_hash='x', display_name='U2', is_active=True, role='viewer')
    db.add(target); db.commit()
    r=client.patch(f'/api/v1/admin/users/{target.id}/role', json={'role':'editor'})
    assert r.status_code==200
    db.refresh(target)
    assert target.role=='editor'
    ev=db.query(AdminAuditEvent).filter(AdminAuditEvent.entity_id==str(target.id)).first()
    assert ev is not None


def test_invalid_role_rejected(client, test_user, db):
    test_user.role='admin'; db.commit()
    r=client.patch(f'/api/v1/admin/users/{test_user.id}/role', json={'role':'bad'})
    assert r.status_code==422


def test_last_admin_cannot_be_demoted(client, test_user, db):
    test_user.role='admin'; db.commit()
    r=client.patch(f'/api/v1/admin/users/{test_user.id}/role', json={'role':'viewer'})
    assert r.status_code==400


def test_admin_metrics_works(client, test_user, db):
    test_user.role='admin'; db.commit()
    r=client.get('/api/v1/admin/metrics')
    assert r.status_code==200
    assert 'total_users' in r.json()
