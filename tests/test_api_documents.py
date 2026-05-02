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


def test_list_and_detail_include_processing_and_enrichment_fields(client, sample_document, db):
    sample_document.extracted_metadata = {
        "processing_stage": "enriching",
        "processing_progress": 75,
        "processing_message": "Running enrichment",
        "enrichment_status": "pending",
        "enrichment_pending": True,
        "intelligence_warnings": ["Relationships pending"],
        "ai_analysis_degraded": True,
        "json_parse_retry_used": True,
    }
    db.add(sample_document)
    db.commit()
    fields = {
        "processing_stage",
        "processing_progress",
        "processing_message",
        "enrichment_status",
        "enrichment_pending",
        "intelligence_warnings",
        "ai_analysis_degraded",
        "json_parse_retry_used",
    }
    list_item = client.get('/api/v1/documents/').json()[0]
    detail_item = client.get(f'/api/v1/documents/{sample_document.id}').json()
    assert fields.issubset(list_item.keys())
    assert fields.issubset(detail_item.keys())
    for field in fields:
        assert list_item[field] == detail_item[field]


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
