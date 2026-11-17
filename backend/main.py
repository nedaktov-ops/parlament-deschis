"""FastAPI application factory for Parlament Deschis."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from strawberry.fastapi import GraphQLRouter

from backend.config import APP_VERSION, DB_PATH, FRONTEND_DIST, SNAPSHOT_DIR
from backend.graphql.schema import schema
from backend.routers.api import invalidate_traseism_overview_cache
from backend.routers.api import router as api_router
from backend.routers.exports import router as exports_router
from pipeline.poller import start_poller

log = logging.getLogger("parlament.api")

# First path segments that must never fall through to the SPA index.
SPA_EXCLUDED = ("api", "docs", "openapi.json", "redoc", "snapshots")

# Module-level guard so a second app instance (e.g. repeated create_app calls
# in one process) never starts a duplicate background scheduler.
_scheduler = None

# ---------------------------------------------------------------------------
# Cache-Control middleware
# ---------------------------------------------------------------------------
# Every /api/* response MUST be no-store. All API data is derived from the DB
# and mutated by admin writes that invalidate only process memory, so any
# shared/CDN cache hit can serve stale data (the "real-time" feed and the
# freshness timestamps on /api/about must reflect current state).
# Health probes, non-GET writes and error responses stay no-store as before.
_NO_STORE = "no-store, no-cache, must-revalidate"
_HEALTH_PATHS = {"/api/health", "/api/health/live", "/api/health/ready"}
_CACHEABLE_METHODS = {"GET", "HEAD"}


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Attach Cache-Control headers to API responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        uncacheable = (
            path.startswith("/api/")
            or path in _HEALTH_PATHS
            or request.method not in _CACHEABLE_METHODS
            or response.status_code >= 400
        )
        if uncacheable:
            # Override any endpoint-set value so no-store always wins.
            response.headers["Cache-Control"] = _NO_STORE
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the live poller only when explicitly enabled, then shut it down."""
    global _scheduler
    raw = os.environ.get("PARLAMENT_POLL_INTERVAL_MIN", "").strip()
    minutes = 0
    if raw:
        try:
            minutes = int(raw)
        except ValueError:
            log.warning("PARLAMENT_POLL_INTERVAL_MIN is not an integer: %r", raw)
    if minutes > 0 and _scheduler is None:
        try:
            _scheduler = start_poller(
                minutes, db_path=DB_PATH, on_cycle=invalidate_traseism_overview_cache
            )
            app.state.poller = _scheduler
            log.info("background poller enabled (every %s min)", minutes)
        except Exception:  # noqa: BLE001 - never let polling break serving
            log.exception("failed to start background poller")
    try:
        yield
    finally:
        if _scheduler is not None:
            _scheduler.shutdown(wait=False)
            _scheduler = None


def create_app() -> FastAPI:
    app = FastAPI(
        title="Parlament Deschis API",
        description="Romanian Parliament transparency tracker — as-of memberships, "
        "movements, and source-cited evidence.",
        version=APP_VERSION,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Compress JSON responses ≥ 1 KB before they hit the network
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(CacheControlMiddleware)
    app.include_router(api_router)
    app.include_router(exports_router)

    # GraphQL endpoint. GraphiQL is a supported Strawberry flag (graphql_ide):
    # turn it off on hosted production (Render/Vercel) or via the explicit flag.
    # Introspection itself has no clean toggle in strawberry 0.341.2 — residual.
    _prod = bool(os.environ.get("RENDER")) or os.environ.get("VERCEL_ENV") == "production"
    _ide_off = _prod or os.environ.get("PARLAMENT_GRAPHQL_IDE", "1").strip().lower() in {
        "0",
        "false",
        "off",
    }
    graphql_app = GraphQLRouter(schema, graphql_ide=None if _ide_off else "graphiql")
    app.include_router(graphql_app, prefix="/graphql")

    if SNAPSHOT_DIR.exists():
        app.mount("/snapshots", StaticFiles(directory=str(SNAPSHOT_DIR)), name="snapshots")

    index = FRONTEND_DIST / "index.html"
    if index.exists():
        assets = FRONTEND_DIST / "assets"
        if assets.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa(full_path: str):
            first = full_path.split("/", 1)[0]
            if first in SPA_EXCLUDED:
                raise HTTPException(status_code=404, detail="not found")
            return FileResponse(index, media_type="text/html")
    else:

        @app.get("/")
        def root():
            return {"name": "Parlament Deschis", "docs": "/docs", "api": "/api"}

    return app


app = create_app()
