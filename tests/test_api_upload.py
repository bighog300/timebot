import io
from pathlib import Path
from unittest.mock import patch


def _upload(client, filename='test.pdf', content_type='application/pdf', payload=b'%PDF-1.4 fake content'):
    files = {'file': (filename, io.BytesIO(payload), content_type)}
    return client.post('/api/v1/upload/', files=files)


def test_upload_valid_pdf_returns_202(client):
    with patch('app.services.storage.storage.save_upload', return_value=(Path('/tmp/test.pdf'), 22)), patch(
        'app.workers.tasks.process_document_task.apply_async'
    ):
        response = _upload(client)
    assert response.status_code == 202


def test_upload_returns_document_shape(client):
    with patch('app.services.storage.storage.save_upload', return_value=(Path('/tmp/test.pdf'), 22)), patch(
        'app.workers.tasks.process_document_task.apply_async'
    ):
        data = _upload(client).json()
    for key in ('id', 'filename', 'processing_status'):
        assert key in data


def test_upload_sets_processing_status_queued(client):
    with patch('app.services.storage.storage.save_upload', return_value=(Path('/tmp/test.pdf'), 22)), patch(
        'app.workers.tasks.process_document_task.apply_async'
    ):
        data = _upload(client).json()
    assert data['processing_status'] in ('queued', 'pending')


def test_upload_unsupported_file_type_returns_400(client):
    files = {'file': ('malware.exe', io.BytesIO(b'fake'), 'application/octet-stream')}
    response = client.post('/api/v1/upload/', files=files)
    assert response.status_code == 400


def test_upload_enqueues_expected_task_payload(client):
    with patch('app.services.storage.storage.save_upload', return_value=(Path('/tmp/test.pdf'), 22)), patch(
        'app.workers.tasks.process_document_task.apply_async'
    ) as apply_async:
        response = _upload(client)

    assert response.status_code == 202
    doc_id = response.json()['id']
    apply_async.assert_called_once()
    assert apply_async.call_args.kwargs['args'] == [doc_id]

def test_upload_uses_configured_cost_limits(client):
    with patch('app.api.v1.upload.configured_rate_limit', return_value=7), patch('app.api.v1.upload.hard_daily_caps', return_value={'uploads_daily': 123}), patch('app.api.v1.upload.enforce_rate_limit') as erl, patch('app.api.v1.upload.enforce_daily_cap') as edc, patch('app.services.storage.storage.save_upload', return_value=(Path('/tmp/test.pdf'), 22)), patch('app.workers.tasks.process_document_task.apply_async'):
        response = _upload(client)

    assert response.status_code == 202
    assert erl.call_args.kwargs['max_calls'] == 7
    assert edc.call_args.kwargs['cap'] == 123
