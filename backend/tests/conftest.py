"""Shared pytest fixtures.

A throwaway temp SQLite DB is configured via EDUVAPT_DATABASE_URL *before* any
app module is imported, so the whole test run is isolated from the real
eduvapt.db and never touches the network unless a test explicitly asks it to.
"""
import os
import tempfile

import pytest

# Must be set before importing anything under app.* (config/database read it
# at import time and bind the engine to whatever URL is present).
_TMP_DB_FD, _TMP_DB_PATH = tempfile.mkstemp(prefix="eduvapt_test_", suffix=".db")
os.close(_TMP_DB_FD)
os.environ["EDUVAPT_DATABASE_URL"] = f"sqlite:///{_TMP_DB_PATH}"

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import VaptSession  # noqa: E402

Base.metadata.create_all(bind=engine)


def pytest_sessionfinish(session, exitstatus):
    try:
        os.remove(_TMP_DB_PATH)
    except OSError:
        pass


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_session(db):
    s = VaptSession(name="test", target_ip="127.0.0.1")
    db.add(s)
    db.commit()
    db.refresh(s)
    yield s
    db.delete(s)
    db.commit()
