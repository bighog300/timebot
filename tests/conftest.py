import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import JSON, Text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import TypeDecorator

# Ensure repo root importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Patch PostgreSQL-specific types before importing app models/Base
import sqlalchemy
import sqlalchemy.dialects.postgresql as pg_dialect
import sqlalchemy.sql.sqltypes as sqltypes


class SQLiteUUID(TypeDecorator):
    impl = Text
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__()

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None

    def process_result_value(self, value, dialect):
        return value


class SQLiteArray(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, *args, **kwargs):
        super().__init__()


pg_dialect.UUID = SQLiteUUID
pg_dialect.JSONB = JSON
pg_dialect.TSVECTOR = Text
pg_dialect.ARRAY = SQLiteArray
sqlalchemy.ARRAY = SQLiteArray
sqltypes.ARRAY = SQLiteArray


@pytest.fixture(scope="session")
def engine():
    from app.db.base import Base
    import app.models  # noqa: F401

    sqlite_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=sqlite_engine)
    yield sqlite_engine
    Base.metadata.drop_all(bind=sqlite_engine)


@pytest.fixture(scope="function")
def db(engine):
    connection = engine.connect()
    transaction = connection.begin()
    TestingSession = sessionmaker(bind=connection)
    session = TestingSession()
    yield session
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def fake_redis():
    """In-memory Redis replacement for tests and CI."""
    fakeredis = pytest.importorskip("fakeredis")
    return fakeredis.FakeStrictRedis(decode_responses=True)


@pytest.fixture(scope="function", autouse=True)
def mock_celery(monkeypatch):
    """Run Celery tasks eagerly in-process so tests never need a live broker."""
    from app.workers.celery_app import celery_app

    previous_always_eager = celery_app.conf.task_always_eager
    previous_eager_propagates = celery_app.conf.task_eager_propagates
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield
    celery_app.conf.task_always_eager = previous_always_eager
    celery_app.conf.task_eager_propagates = previous_eager_propagates


@pytest.fixture(scope="function")
def test_user(db):
    from app.models.user import User
    from app.services.auth import auth_service

    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=auth_service.hash_password("password123"),
        display_name="Test User",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_token(test_user):
    from app.services.auth import auth_service

    return auth_service.create_access_token(test_user)


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def client(db, test_user):
    from app.api.deps import get_current_user, get_db
    from app.main import app

    def override_get_db():
        yield db

    def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_document(db, test_user):
    from app.models.document import Document

    doc = Document(
        id=uuid.uuid4(),
        filename="test.pdf",
        original_path="/tmp/test.pdf",
        file_type="pdf",
        file_size=1024,
        mime_type="application/pdf",
        processing_status="completed",
        source="upload",
        summary="Test document summary",
        ai_tags=["test", "fixture"],
        key_points=["point one", "point two"],
        entities={"people": [], "orgs": []},
        action_items=[],
        user_id=test_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc
