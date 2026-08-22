import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from db.sqlite_models import get_session, init_db
from db.postgres_models import get_session as pg_get_session, init_db as pg_init_db

# A plain "sqlite:///:memory:" engine hands out a fresh, empty database per new
# connection/thread. StaticPool pins the whole engine to one shared connection,
# which both keeps state visible across calls in a test AND is required for
# FastAPI's TestClient, which runs the app in a different thread than the test.
_MEMORY_SQLITE_KWARGS = dict(connect_args={"check_same_thread": False}, poolclass=StaticPool)


@pytest.fixture
def sqlite_engine():
    engine = create_engine("sqlite:///:memory:", **_MEMORY_SQLITE_KWARGS)
    init_db(engine)
    return engine


@pytest.fixture
def sqlite_session(sqlite_engine):
    session = get_session(sqlite_engine)
    yield session
    session.close()


@pytest.fixture
def pg_engine():
    # SQLite in-memory stands in for Postgres in unit tests -- the schema uses no
    # Postgres-only types, so this is safe and keeps tests fast/credential-free.
    engine = create_engine("sqlite:///:memory:", **_MEMORY_SQLITE_KWARGS)
    pg_init_db(engine)
    return engine


@pytest.fixture
def pg_session(pg_engine):
    session = pg_get_session(pg_engine)
    yield session
    session.close()


@pytest.fixture(autouse=True)
def _jwt_secret_for_tests(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", "test-only-secret-do-not-use-in-prod")


@pytest.fixture
def auth_token_factory():
    from api.auth.security import create_access_token

    return create_access_token


@pytest.fixture
def client(pg_session):
    from fastapi.testclient import TestClient

    from api.deps import get_db
    from api.main import app

    app.dependency_overrides[get_db] = lambda: pg_session
    yield TestClient(app)
    app.dependency_overrides.clear()


class FakeNeo4jResult:
    def __init__(self, rows):
        self._rows = rows

    def __iter__(self):
        return iter(self._rows)

    def data(self):
        return list(self._rows)


class FakeNeo4jSession:
    def __init__(self, rows):
        self._rows = rows
        self.last_query = None
        self.last_params = None

    def run(self, query, params=None):
        self.last_query = query
        self.last_params = params
        return FakeNeo4jResult(self._rows)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeNeo4jDriver:
    def __init__(self, rows):
        self._rows = rows
        self.closed = False

    def session(self):
        return FakeNeo4jSession(self._rows)

    def close(self):
        self.closed = True


@pytest.fixture
def fake_neo4j_driver_factory():
    return FakeNeo4jDriver
