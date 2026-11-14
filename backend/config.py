"""Project-root configuration shared by the API, data paths and static files.

All paths resolve relative to the repository root (the parent of ``backend/``)
so the API behaves the same regardless of the process working directory.
Environment overrides may be absolute or relative to the project root.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_VERSION = "0.1.0"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _rooted(env_name: str, default: str) -> Path:
    """Return a path from ``env_name`` or the project-root default."""
    raw = os.environ.get(env_name)
    if raw:
        path = Path(raw).expanduser()
        return path if path.is_absolute() else (PROJECT_ROOT / path)
    return PROJECT_ROOT / default


DB_PATH = _rooted("PARLAMENT_DB", "data/parlament-real.db")
SNAPSHOT_DIR = _rooted("PARLAMENT_SNAPSHOT_DIR", "data/snapshots")
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
