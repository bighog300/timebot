from unittest.mock import patch


def test_list_documents_returns_200(client, sample_document):
    response = client.get('/api/v1/documents/')
    assert response.status_code == 200


def test_list_documents_returns_list(client, sample_document):
    data = client.get('/api/v1/documents/').json()
    assert isinstance(data, list)


def test_list_documents_includes_seeded_document(client, sample_document):
    data = client.get('/api/v1/documents/').json()
    assert any(item['id'] == str(sample_document.id) for item in data)


def test_get_document_by_id_returns_200(client, sample_document):
    response = client.get(f'/api/v1/documents/{sample_document.id}')
    assert response.status_code == 200


def test_get_document_by_id_returns_correct_document(client, sample_document):
    data = client.get(f'/api/v1/documents/{sample_document.id}').json()
    assert data['filename'] == sample_document.filename


def test_get_document_not_found_returns_404(client):
    response = client.get('/api/v1/documents/00000000-0000-0000-0000-000000000000')
    assert response.status_code == 404


def test_update_document_returns_200(client, sample_document):
    response = client.put(f'/api/v1/documents/{sample_document.id}', json={'user_notes': 'updated note'})
    assert response.status_code == 200


def test_update_document_persists_change(client, sample_document):
    client.put(f'/api/v1/documents/{sample_document.id}', json={'user_notes': 'updated note'})
    data = client.get(f'/api/v1/documents/{sample_document.id}').json()
    assert data['user_notes'] == 'updated note'


def test_delete_document_returns_200_or_204(client, sample_document):
    with patch('app.services.storage.storage.delete_file'):
        response = client.delete(f'/api/v1/documents/{sample_document.id}')
    assert response.status_code in (200, 204)


def test_delete_document_removes_from_list(client, sample_document):
    with patch('app.services.storage.storage.delete_file'):
        client.delete(f'/api/v1/documents/{sample_document.id}')
    data = client.get('/api/v1/documents/').json()
    assert all(item['id'] != str(sample_document.id) for item in data)
