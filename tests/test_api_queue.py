from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.main import app


def test_queue_stats_endpoint_shape(monkeypatch):
    user = SimpleNamespace(id=uuid4(), email='queue@example.com')
    app.dependency_overrides[get_current_user] = lambda: user

    class FakeGroupedQuery:
        def filter(self, *_args, **_kwargs):
            return self

        def group_by(self, *_args, **_kwargs):
            return self

        def all(self):
            return [('queued', 1), ('completed', 2)]

    class FakeScalarQuery:
        def filter(self, *_args, **_kwargs):
            return self

        def scalar(self):
            return 1

    class FakeDB:
        def __init__(self):
            self.calls = 0

        def query(self, *_args, **_kwargs):
            self.calls += 1
            return FakeGroupedQuery() if self.calls == 1 else FakeScalarQuery()

    app.dependency_overrides[get_db] = lambda: iter([FakeDB()])
    monkeypatch.setattr('app.api.v1.queue.inspect_workers', lambda timeout=2: {'active_tasks': 0, 'reserved_tasks': 0})

    with TestClient(app) as client:
        response = client.get('/api/v1/queue/stats')

    app.dependency_overrides.clear()
    assert response.status_code == 200
    payload = response.json()
    assert payload['pending_review_count'] == 1
    assert payload['total'] == 3


def test_retry_failed_endpoint(monkeypatch):
    user = SimpleNamespace(id=uuid4(), email='queue@example.com')
    app.dependency_overrides[get_current_user] = lambda: user

    class Doc(SimpleNamespace):
        pass

    docs = [Doc(id=uuid4(), processing_status='failed', processing_error='err')]

    class FakeQuery:
        def filter(self, *_args, **_kwargs):
            return self

        def all(self):
            return docs

    class FakeDB:
        def query(self, _model):
            return FakeQuery()

        def add(self, _obj):
            return None

        def commit(self):
            return None

    app.dependency_overrides[get_db] = lambda: iter([FakeDB()])
    monkeypatch.setattr('app.workers.tasks.process_document_task.apply_async', lambda *args, **kwargs: None)

    with TestClient(app) as client:
        response = client.post('/api/v1/queue/retry-failed')

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert 'Queued' in response.json()['message']
