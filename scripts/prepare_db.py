"""Prepare a database for shipping inside a container image.

The app is read-only at runtime and the SQLite file is baked into the image,
so the database must be a single file that needs no side-car ``-wal``/``-shm``
files: a WAL database cannot even be opened on a read-only filesystem.

This script rewrites the working database into a clean, verified copy:

* ``VACUUM INTO`` rewrites it into one file with no free pages;
* ``journal_mode=DELETE`` removes the WAL side-cars;
* ``PRAGMA integrity_check`` proves the copy is structurally sound;
* ``PRAGMA foreign_key_check`` proves referential integrity, on both the
  source and the prepared copy (integrity_check alone does not check FKs);
* the copy is stamped with the schema version (``PRAGMA user_version``) that
  ``pipeline.db.ensure_schema`` uses as the gate for one-off destructive
  migrations — a shipped DB therefore never replays the legacy merge at
  runtime (see ``pipeline.db.SCHEMA_VERSION``).

Usage:
    python scripts/prepare_db.py <source.db> <target.db>
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

from pipeline.db import SCHEMA_VERSION


def _check_foreign_keys(conn: sqlite3.Connection, label: str) -> None:
    """Abort if the database has any dangling foreign-key references."""
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    if violations:
        sample = ", ".join(f"{row[0]}(rowid={row[1]}) -> {row[2]}" for row in violations[:5])
        suffix = "" if len(violations) <= 5 else f" (+{len(violations) - 5} more)"
        raise SystemExit(
            f"{label} has foreign key violations: {len(violations)} [{sample}]{suffix}"
        )


def prepare(source: Path, target: Path) -> None:
    if not source.exists():
        raise SystemExit(
            f"database not found: {source}\n"
            "Build it first:\n"
            "  .venv/bin/python -m pipeline.cli --db data/parlament.db build-corpus "
            "--chamber both --cache data/cache/cdep"
        )
    if source.resolve() == target.resolve():
        raise SystemExit("source and target database paths must be different")
    target.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(source)
    try:
        status = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if status != "ok":
            raise SystemExit(f"source database is corrupt: {status}")
        _check_foreign_keys(conn, "source database")
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        required_tables = {"person", "organization", "mandate", "membership", "event", "evidence"}
        missing_tables = required_tables - tables
        if missing_tables:
            raise SystemExit(
                f"source database is missing required tables: {', '.join(sorted(missing_tables))}"
            )
        counts = {
            table: conn.execute(f'SELECT count(*) FROM "{table}"').fetchone()[0]
            for table in ("person", "organization", "mandate", "membership", "event", "evidence")
        }
        empty_tables = [table for table, count in counts.items() if count == 0]
        if empty_tables:
            raise SystemExit(
                f"source database has empty required tables: {', '.join(empty_tables)}"
            )
    finally:
        conn.close()

    with tempfile.TemporaryDirectory(prefix=f".{target.name}.", dir=target.parent) as temp_dir:
        temporary_target = Path(temp_dir) / target.name
        source_conn = sqlite3.connect(source)
        try:
            source_conn.execute("VACUUM INTO ?", (str(temporary_target),))
        finally:
            source_conn.close()

        out = sqlite3.connect(temporary_target)
        try:
            out.execute("PRAGMA journal_mode=DELETE")
            status = out.execute("PRAGMA integrity_check").fetchone()[0]
            if status != "ok":
                raise SystemExit(f"prepared database is corrupt: {status}")
            _check_foreign_keys(out, "prepared database")
            mode = out.execute("PRAGMA journal_mode").fetchone()[0]
            if mode.lower() != "delete":
                raise SystemExit(f"could not switch journal mode (still {mode})")
            # Stamp the schema version so a shipped/read-only database never
            # replays the one-off destructive legacy merge at runtime
            # (pipeline.db.SCHEMA_VERSION gates _merge_legacy_cross_chamber_groups).
            out.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            out.execute("PRAGMA query_only=ON")
            rows = out.execute("SELECT count(*) FROM sqlite_master").fetchone()[0]
        finally:
            out.close()

        os.replace(temporary_target, target)

    size = target.stat().st_size
    print(
        f"prepared {target} ({size / 1024:.0f} KiB, {len(tables)} tables, "
        f"{rows} schema rows, journal_mode=DELETE)"
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: prepare_db.py <source.db> <target.db>")
    prepare(Path(sys.argv[1]), Path(sys.argv[2]))
