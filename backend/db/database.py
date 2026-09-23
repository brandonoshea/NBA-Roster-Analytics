from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import settings

# Engine manages the actual connection(s) to the database (pooling, dialect, etc.).
# DATABASE_URL comes from settings so the same code works across dev/test/prod.
# check_same_thread=False is only relevant for the sqlite file the test suite
# points at (see tests/conftest.py) -- FastAPI runs sync endpoints in a worker
# thread, and sqlite3 otherwise refuses to reuse a connection across threads.
_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=_connect_args)

# Factory for new Session objects, all bound to the engine above.
# autocommit=False / autoflush=False give explicit control over when changes
# are flushed/committed, instead of SQLAlchemy doing it implicitly mid-query.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that all ORM models inherit from; SQLAlchemy uses it to track
# table metadata (e.g. for Base.metadata.create_all()).
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session, closes it after the request."""
    # Generator pattern: everything before `yield` runs on request start,
    # everything after runs on teardown (even if the request raises), so the
    # session is always closed and connections are returned to the pool.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)