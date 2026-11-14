"""Prepare a database for shipping inside a container image.

The app is read-only at runtime and the SQLite file is baked into the image,
so the database must be a single file that needs no side-car ``-wal``/``-shm``
files: a WAL database cannot even be opened on a read-only filesystem.

This script rewrites the working database into a clean, verified copy:

* ``VACUUM INTO`` rewrites it into one file with no free pages;
* ``journal_mode=DELETE`` removes the WAL side-cars;
* ``PRAGMA integrity_check`` proves the copy is sound.

Usage:
    python scripts/prepare_db.py <source.db> <target.db>
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


def prepare(source: Path, target: Path) -> None:
    if not source.exists():
        raise SystemExit(
            f"database not found: {source}\n"
            "Build it first:\n"
            "  .venv/bin/python -m pipeline.cli --db data/parlament.db build-corpus "
            "--chamber both --cache data/cache/cdep"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()

    conn = sqlite3.connect(source)
    try:
        status = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if status != "ok":
            raise SystemExit(f"source database is corrupt: {status}")
        tables = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        conn.execute("VACUUM INTO ?", (str(target),))
    finally:
        conn.close()

    out = sqlite3.connect(target)
    try:
        out.execute("PRAGMA journal_mode=DELETE")
        out.execute("PRAGMA integrity_check").fetchone()
        mode = out.execute("PRAGMA journal_mode").fetchone()[0]
        if mode.lower() != "delete":
            raise SystemExit(f"could not switch journal mode (still {mode})")
        # A read-only runtime must not be able to write.
        out.execute("PRAGMA query_only=ON")
        rows = out.execute("SELECT count(*) FROM sqlite_master").fetchone()[0]
    finally:
        out.close()

    size = target.stat().st_size
    print(
        f"prepared {target} ({size / 1024:.0f} KiB, {tables} tables, "
        f"{rows} schema rows, journal_mode=DELETE)"
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: prepare_db.py <source.db> <target.db>")
    prepare(Path(sys.argv[1]), Path(sys.argv[2]))
