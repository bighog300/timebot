import uuid
from datetime import datetime, timedelta, timezone

from app.models.admin_audit import AdminAuditEvent
from app.models.document import Document
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


def test_admin_can_retrieve_processing_summary(client, test_user, db):
    test_user.role = "admin"
    db.commit()
    r = client.get('/api/v1/admin/processing-summary')
    assert r.status_code == 200
    assert "pending" in r.json()


def test_non_admin_cannot_retrieve_processing_summary(client, test_user, db):
    test_user.role = "viewer"
    db.commit()
    r = client.get('/api/v1/admin/processing-summary')
    assert r.status_code == 403


def test_processing_summary_counts_are_accurate(client, test_user, db):
    test_user.role = "admin"
    db.commit()
    now = datetime.now(timezone.utc)
    docs = [
        Document(id=uuid.uuid4(), filename="p1.pdf", original_path="/tmp/p1.pdf", file_type="pdf", file_size=1, mime_type="application/pdf", processing_status="pending", source="upload", user_id=test_user.id),
        Document(id=uuid.uuid4(), filename="q1.pdf", original_path="/tmp/q1.pdf", file_type="pdf", file_size=1, mime_type="application/pdf", processing_status="queued", source="upload", user_id=test_user.id),
        Document(id=uuid.uuid4(), filename="pr1.pdf", original_path="/tmp/pr1.pdf", file_type="pdf", file_size=1, mime_type="application/pdf", processing_status="processing", source="upload", user_id=test_user.id),
        Document(id=uuid.uuid4(), filename="c1.pdf", original_path="/tmp/c1.pdf", file_type="pdf", file_size=1, mime_type="application/pdf", processing_status="completed", source="upload", user_id=test_user.id),
        Document(id=uuid.uuid4(), filename="f_recent.pdf", original_path="/tmp/f_recent.pdf", file_type="pdf", file_size=1, mime_type="application/pdf", processing_status="failed", source="upload", user_id=test_user.id, updated_at=now - timedelta(hours=2)),
        Document(id=uuid.uuid4(), filename="f_old.pdf", original_path="/tmp/f_old.pdf", file_type="pdf", file_size=1, mime_type="application/pdf", processing_status="failed", source="upload", user_id=test_user.id, updated_at=now - timedelta(days=3)),
    ]
    db.add_all(docs)
    db.commit()
    r = client.get('/api/v1/admin/processing-summary')
    assert r.status_code == 200
    payload = r.json()
    assert payload["pending"] == 2
    assert payload["processing"] == 1
    assert payload["completed"] == 1
    assert payload["failed"] == 2
    assert payload["recently_failed"] == 1
