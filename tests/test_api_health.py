def test_health_returns_200(client):
    response = client.get('/health')
    assert response.status_code == 200


def test_health_response_shape(client):
    data = client.get('/health').json()
    for key in ('status', 'service', 'version', 'database'):
        assert key in data


def test_health_status_value(client):
    data = client.get('/health').json()
    assert data['status'] == 'healthy'


def test_root_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200


def test_root_response_shape(client):
    data = client.get('/').json()
    for key in ('message', 'docs', 'health', 'version'):
        assert key in data
