import atexit
import os
import tempfile

import pytest

# Point the app at a throwaway SQLite file instead of the real Postgres
# database. Must happen before any backend module is imported, since
# db.database builds its engine from settings.DATABASE_URL at import time.
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
def _cleanup_tmp_db():
    try:
        os.unlink(_tmp_db.name)
    except OSError:
        pass  # engine's connection may still be open on Windows; not worth failing the run over


atexit.register(_cleanup_tmp_db)

from fastapi.testclient import TestClient  # noqa: E402

from db.database import Base, SessionLocal, engine, get_db  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture()
def db_session():
    # Fresh schema per test: simplest way to get isolation while still
    # letting route handlers call db.commit() like they do in production.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
