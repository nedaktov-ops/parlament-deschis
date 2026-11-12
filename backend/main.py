"""FastAPI application factory for Parlament Deschis."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import APP_VERSION, DB_PATH, FRONTEND_DIST, SNAPSHOT_DIR
from backend.routers.api import router as api_router
from backend.routers.exports import router as exports_router
from pipeline.poller import start_poller

log = logging.getLogger("parlament.api")

# First path segments that must never fall through to the SPA index.
SPA_EXCLUDED = ("api", "docs", "openapi.json", "redoc", "snapshots")

# Module-level guard so a second app instance (e.g. repeated create_app calls
# in one process) never starts a duplicate background scheduler.
_scheduler = None


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
            _scheduler = start_poller(minutes, db_path=DB_PATH)
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
    app.include_router(api_router)
    app.include_router(exports_router)

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
