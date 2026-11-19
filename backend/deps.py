"""Shared backend dependencies: one app-scoped engine, one session per request.

The engine is created once (from ``backend.config.DB_PATH``) by the FastAPI
lifespan via :func:`configure` and disposed on shutdown. ``get_db`` is the
single session source for both REST routers and the GraphQL context getter, so
``app.dependency_overrides[get_db]`` overrides both surfaces.
"""

from __future__ import annotations

from backend.config import DB_PATH
from pipeline.db import init_db, make_engine, make_session_factory

_engine = None
SessionFactory = None


def configure(db_path=None, engine=None):
    """Create the app-scoped engine + session factory (idempotent).

    ``engine`` lets the app inject a factory-resolved engine — that indirection
    keeps the compatibility monkeypatch in ``backend.graphql.schema.make_engine``
    effective for the whole app.
    """
    global _engine, SessionFactory  # noqa: PLW0603
    if _engine is not None:
        return _engine
    if engine is None:
        engine = make_engine(db_path or DB_PATH)
    init_db(engine)
    _engine = engine
    SessionFactory = make_session_factory(engine)
    return _engine


def dispose() -> None:
    """Dispose the app-scoped engine on shutdown."""
    global _engine, SessionFactory  # noqa: PLW0603
    if _engine is not None:
        _engine.dispose()
    _engine = None
    SessionFactory = None


def get_db():
    # Fallback for app use without a lifespan (e.g. a plain TestClient with no
    # get_db override): configure lazily rather than at import time, so a normal
    # app still creates exactly one engine and disposes it on shutdown.
    if SessionFactory is None:
        configure()
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()
