import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

from app.models.chat import ChatMessage, ChatSession, GeneratedReport
from app.models.document import Document
from app.services.billing import BillingService
from app.services.monetization import ActionType, ensure_user_limit, refresh_usage_counters


def _mk_document(db, user_id, name='test.pdf'):
    doc = Document(
        id=uuid.uuid4(),
        filename=name,
        original_path=f"/tmp/{name}",
        file_type='pdf',
        file_size=100,
        mime_type='application/pdf',
        processing_status='completed',
        source='upload',
        user_id=user_id,
    )
    db.add(doc)
    db.commit()
    return doc


def test_usage_increments_on_document_upload(db, test_user):
    assert test_user.documents_uploaded_count == 0
    _mk_document(db, test_user.id, 'u1.pdf')
    refresh_usage_counters(db, test_user)
    db.commit()
    assert test_user.documents_uploaded_count == 1


def test_usage_increments_on_report_generation(db, test_user):
    assert test_user.reports_generated_count == 0
    report = GeneratedReport(
        id=uuid.uuid4(),
        title='r',
        prompt='p',
        content_markdown='c',
        source_document_ids=[],
        source_refs=[],
        created_at=datetime.now(timezone.utc),
        created_by_id=test_user.id,
    )
    db.add(report)
    db.commit()
    refresh_usage_counters(db, test_user)
    db.commit()
    assert test_user.reports_generated_count == 1


def test_usage_increments_on_chat_message(db, test_user):
    session = ChatSession(id=uuid.uuid4(), title='s', user_id=test_user.id)
    db.add(session)
    db.commit()
    msg = ChatMessage(id=uuid.uuid4(), session_id=session.id, role='user', content='hi', created_at=datetime.now(timezone.utc))
    db.add(msg)
    db.commit()
    refresh_usage_counters(db, test_user)
    db.commit()
    assert test_user.chat_messages_count == 1


def test_free_plan_blocks_document_upload_at_limit(db, test_user):
    test_user.plan = 'free'
    db.add(test_user)
    db.commit()
    for i in range(25):
        _mk_document(db, test_user.id, f'd{i}.pdf')
    try:
        ensure_user_limit(db, test_user, ActionType.UPLOAD_DOCUMENT)
        assert False, 'expected limit exception'
    except Exception as exc:
        assert getattr(exc, 'status_code', None) == 429


def test_free_plan_blocks_report_generation_at_limit(db, test_user):
    test_user.plan = 'free'
    db.add(test_user)
    db.commit()
    for i in range(10):
        db.add(GeneratedReport(id=uuid.uuid4(), title=f'r{i}', prompt='p', content_markdown='c', source_document_ids=[], source_refs=[], created_by_id=test_user.id))
    db.commit()
    try:
        ensure_user_limit(db, test_user, ActionType.GENERATE_REPORT)
        assert False, 'expected limit exception'
    except Exception as exc:
        assert getattr(exc, 'status_code', None) == 429


def test_free_plan_blocks_chat_at_limit(db, test_user):
    test_user.plan = 'free'
    db.add(test_user)
    db.commit()
    session = ChatSession(id=uuid.uuid4(), title='s', user_id=test_user.id)
    db.add(session)
    db.commit()
    for i in range(200):
        db.add(ChatMessage(id=uuid.uuid4(), session_id=session.id, role='user', content=f'm{i}'))
    db.commit()
    try:
        ensure_user_limit(db, test_user, ActionType.SEND_CHAT)
        assert False, 'expected limit exception'
    except Exception as exc:
        assert getattr(exc, 'status_code', None) == 429


def test_pro_plan_allows_higher_usage(db, test_user):
    test_user.plan = 'pro'
    db.add(test_user)
    db.commit()
    for i in range(40):
        _mk_document(db, test_user.id, f'p{i}.pdf')
    ensure_user_limit(db, test_user, ActionType.UPLOAD_DOCUMENT)


def test_checkout_session_creation_returns_expected_payload(client):
    res = client.post('/api/v1/billing/checkout', json={'plan': 'pro'})
    assert res.status_code == 200
    body = res.json()
    assert body['plan'] == 'pro'
    assert body['checkout_session_id'].startswith('stub_')
    assert body['checkout_url'].startswith('https://billing.stub/checkout/')


def test_webhook_updates_user_plan(db, test_user):
    svc = BillingService('x', 'y')
    event = {'type': 'checkout.session.completed', 'data': {'object': {'client_reference_id': str(test_user.id), 'metadata': {'plan': 'pro'}}}}
    assert svc.handle_webhook(db, event) is True
    db.refresh(test_user)
    assert test_user.plan == 'pro'


def test_invalid_webhook_handled_safely(client):
    res = client.post('/api/v1/billing/webhook', json={'type': 'unexpected'})
    assert res.status_code == 400
    assert res.json()['detail'] == 'Invalid webhook'


def test_get_usage_returns_expected_counters_and_limits(db, client, test_user):
    _mk_document(db, test_user.id, 'usage.pdf')
    db.add(GeneratedReport(id=uuid.uuid4(), title='r', prompt='p', content_markdown='c', source_document_ids=[], source_refs=[], created_by_id=test_user.id))
    s = ChatSession(id=uuid.uuid4(), title='s', user_id=test_user.id)
    db.add(s)
    db.commit()
    db.add(ChatMessage(id=uuid.uuid4(), session_id=s.id, role='user', content='hello'))
    db.commit()

    res = client.get('/api/v1/usage')
    assert res.status_code == 200
    data = res.json()
    assert data['plan'] == 'free'
    assert data['documents'] == {'used': 1, 'limit': 25}
    assert data['reports'] == {'used': 1, 'limit': 10}
    assert data['chat_messages'] == {'used': 1, 'limit': 200}
