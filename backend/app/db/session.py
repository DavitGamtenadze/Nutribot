from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

_connect_args = {}
_kwargs = {}

if settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
else:
    _kwargs = {"pool_pre_ping": True}

engine: Engine = create_engine(settings.database_url, connect_args=_connect_args, **_kwargs)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_session_factory() -> sessionmaker:
    return SessionLocal
