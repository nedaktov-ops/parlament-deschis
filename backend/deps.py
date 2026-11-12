"""Shared backend dependencies: DB session factory."""

from __future__ import annotations

from backend.config import DB_PATH
from pipeline.db import init_db, make_engine, make_session_factory

_engine = make_engine(DB_PATH)
init_db(_engine)
SessionFactory = make_session_factory(_engine)


def get_db():
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
