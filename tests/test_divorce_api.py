from fastapi.testclient import TestClient
from app.main import app


def test_divorce_routes_exist():
    client = TestClient(app)
    assert client.get('/health').status_code == 200
