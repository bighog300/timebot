import uuid
from unittest.mock import patch

from app.models.document import Document


def test_queue_stats_returns_200(client):
    with patch('app.api.v1.queue.inspect_workers', return_value={'active_tasks': 0, 'reserved_tasks': 0}):
        response = client.get('/api/v1/queue/stats')
    assert response.status_code == 200


def test_queue_stats_response_shape(client):
    with patch('app.api.v1.queue.inspect_workers', return_value={'active_tasks': 0, 'reserved_tasks': 0}):
        data = client.get('/api/v1/queue/stats').json()
    for key in ('queued', 'processing', 'completed', 'failed', 'total'):
        assert key in data


def test_queue_stats_counts_documents(client, sample_document, db):
    sample_document.processing_status = 'completed'
    db.add(sample_document)
    db.commit()

    with patch('app.api.v1.queue.inspect_workers', return_value={'active_tasks': 0, 'reserved_tasks': 0}):
        data = client.get('/api/v1/queue/stats').json()
    assert data['completed'] >= 1


def test_queue_items_returns_200(client):
    response = client.get('/api/v1/queue/items')
    assert response.status_code == 200


def test_queue_items_returns_list(client):
    data = client.get('/api/v1/queue/items').json()
    assert isinstance(data, list)


def test_retry_failed_returns_200(client):
    with patch('app.workers.tasks.process_document_task.apply_async'):
        response = client.post('/api/v1/queue/retry-failed')
    assert response.status_code == 200


def test_retry_failed_requeues_failed_documents(client, test_user, db):
    doc = Document(
        id=uuid.uuid4(),
        filename='failed.pdf',
        original_path='/tmp/failed.pdf',
        file_type='pdf',
        file_size=123,
        mime_type='application/pdf',
        processing_status='failed',
        source='upload',
        user_id=test_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    with patch('app.workers.tasks.process_document_task.apply_async'):
        response = client.post('/api/v1/queue/retry-failed')
    assert response.status_code == 200

    refreshed = client.get(f'/api/v1/documents/{doc.id}').json()
    assert refreshed['processing_status'] != 'failed'


def test_queue_stats_reports_worker_unavailable_when_ping_fails(client):
    with patch('app.api.v1.queue.inspect_workers', side_effect=RuntimeError('worker offline')):
        data = client.get('/api/v1/queue/stats').json()

    assert data['worker_online'] is False
    assert data['broker_reachable'] is False
    assert data['worker_error'] == 'worker offline'


def test_queue_stats_reports_worker_available(client):
    with patch('app.api.v1.queue.inspect_workers', return_value={'active_tasks': 1, 'reserved_tasks': 2, 'worker_count': 1}):
        data = client.get('/api/v1/queue/stats').json()

    assert data['worker_online'] is True
    assert data['broker_reachable'] is True
    assert data['worker_count'] == 1
