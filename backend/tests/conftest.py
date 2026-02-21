from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import models as _models  # noqa: F401 — registers ORM tables
from app.db.base import Base


@pytest.fixture
def db_engine(tmp_path):
    """In-memory SQLite engine with schema created; one per test via tmp_path."""
    url = f"sqlite+pysqlite:///{tmp_path}/test.db"
    engine = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session_factory(db_engine):
    """Session factory bound to the test DB engine."""
    return sessionmaker(
        bind=db_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
