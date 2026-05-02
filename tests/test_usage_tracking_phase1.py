import io
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from app.models.document import Document
from app.models.usage_event import UsageEvent
from app.services.document_processor import document_processor
from app.services.usage import get_usage_summary


def _upload(client, filename='test.pdf', content_type='application/pdf', payload=b'%PDF-1.4 fake content'):
    files = {'file': (filename, io.BytesIO(payload), content_type)}
    return client.post('/api/v1/upload/', files=files)


def test_usage_event_recorded_on_upload(client, db, test_user):
    with patch('app.services.storage.storage.save_upload', return_value=(Path('/tmp/test.pdf'), 128)), patch(
        'app.workers.tasks.process_document_task.apply_async'
    ):
        response = _upload(client)

    assert response.status_code == 202
    events = db.query(UsageEvent).filter(UsageEvent.user_id == test_user.id).all()
    metrics = {event.metric: event.quantity for event in events}
    assert metrics['document_upload'] == 1
    assert metrics['storage_bytes'] == 128


def test_usage_event_recorded_on_processing(db, test_user):
    doc = Document(
        id=uuid.uuid4(),
        filename='process.pdf',
        original_path='/tmp/process.pdf',
        file_type='pdf',
        file_size=1024,
        source='upload',
        user_id=test_user.id,
        processing_status='queued',
    )
    db.add(doc)
    db.commit()

    with patch('pathlib.Path.exists', return_value=False), patch.object(document_processor, '_load_or_extract_text', return_value='hello world'), patch(
        'app.services.thumbnail_generator.thumbnail_generator.generate', return_value=None
    ), patch.object(document_processor, '_run_ai_analysis', return_value=None):
        document_processor.process_document(db, doc)

    metrics = [row.metric for row in db.query(UsageEvent).filter(UsageEvent.user_id == test_user.id).all()]
    assert 'document_processing_started' in metrics
    assert 'document_processing_completed' in metrics


def test_usage_summary_aggregates_by_user_and_period(db, test_user):
    now = datetime.now(timezone.utc)
    db.add_all([
        UsageEvent(user_id=test_user.id, metric='document_upload', quantity=1, metadata_json={}, created_at=now - timedelta(days=1)),
        UsageEvent(user_id=test_user.id, metric='document_upload', quantity=2, metadata_json={}, created_at=now - timedelta(hours=1)),
        UsageEvent(user_id=test_user.id, metric='ai_call', quantity=3, metadata_json={}, created_at=now - timedelta(hours=2)),
    ])
    db.commit()

    summary = get_usage_summary(db, test_user.id, now - timedelta(days=2), now + timedelta(minutes=1))
    assert summary['document_upload'] == 3
    assert summary['ai_call'] == 3


def test_usage_summary_is_user_scoped(db, test_user):
    other_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    db.add_all([
        UsageEvent(user_id=test_user.id, metric='document_upload', quantity=1, metadata_json={}, created_at=now),
        UsageEvent(user_id=other_id, metric='document_upload', quantity=10, metadata_json={}, created_at=now),
    ])
    db.commit()

    summary = get_usage_summary(db, test_user.id, now - timedelta(days=1), now + timedelta(days=1))
    assert summary['document_upload'] == 1
