from unittest.mock import patch


def test_keyword_search_returns_200(client):
    with patch('app.api.v1.search.search_service.search_documents', return_value={'results': [], 'total': 0, 'query': 'test', 'page': 1, 'pages': 0}):
        response = client.post('/api/v1/search/?query=test')
    assert response.status_code == 200


def test_keyword_search_response_shape(client):
    payload = {'results': [], 'total': 0, 'query': 'test', 'page': 1, 'pages': 0, 'degraded': False, 'debug': {}}
    with patch('app.api.v1.search.search_service.search_documents', return_value=payload):
        data = client.post('/api/v1/search/?query=test').json()
    assert 'total' in data and 'query' in data
    assert ('documents' in data) or ('results' in data)


def test_keyword_search_empty_results(client):
    payload = {'results': [], 'total': 0, 'query': 'test', 'page': 1, 'pages': 0, 'degraded': False, 'debug': {}}
    with patch('app.api.v1.search.search_service.search_documents', return_value=payload):
        data = client.post('/api/v1/search/?query=test').json()
    items = data.get('documents', data.get('results', []))
    assert items == []
    assert data['total'] == 0


def test_keyword_search_with_seeded_document(client, sample_document):
    payload = {
        'results': [],
        'total': 1,
        'query': 'budget',
        'page': 1,
        'pages': 1,
    }
    with patch('app.api.v1.search.search_service.search_documents', return_value=payload):
        data = client.post('/api/v1/search/?query=budget').json()
    assert data['total'] >= 1


def test_search_suggestions_returns_200(client):
    with patch('app.api.v1.search.search_service.get_search_suggestions', return_value=['test', 'team']):
        response = client.get('/api/v1/search/suggestions?q=te')
    assert response.status_code == 200


def test_search_suggestions_returns_list(client):
    with patch('app.api.v1.search.search_service.get_search_suggestions', return_value=['test', 'team']):
        data = client.get('/api/v1/search/suggestions?q=te').json()
    suggestions = data if isinstance(data, list) else data.get('suggestions', [])
    assert isinstance(suggestions, list)


def test_search_facets_returns_200(client):
    response = client.get('/api/v1/search/facets')
    assert response.status_code == 200


def test_search_facets_response_shape(client):
    data = client.get('/api/v1/search/facets').json()
    assert isinstance(data, dict)
    assert len(data.keys()) >= 1

def test_hybrid_search_uses_configured_expensive_read_limits(client):
    payload = {'results': [], 'total': 0, 'query': 'test', 'page': 1, 'pages': 0, 'degraded': False, 'debug': {}}
    with patch('app.api.v1.search.configured_rate_limit', return_value=9), patch('app.api.v1.search.enforce_rate_limit') as erl, patch('app.api.v1.search.record_usage'), patch('app.api.v1.search.search_service.hybrid_search_documents', return_value=payload):
        response = client.post('/api/v1/search/hybrid?query=test')
    assert response.status_code == 200
    assert erl.call_args.kwargs['max_calls'] == 9
