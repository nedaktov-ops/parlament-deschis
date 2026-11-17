from __future__ import annotations

import sqlite3

import pytest

from pipeline.db import SCHEMA_VERSION
from scripts.prepare_db import prepare


def _valid_source(path):
    with sqlite3.connect(path) as connection:
        for table in ("person", "organization", "mandate", "membership", "event", "evidence"):
            connection.execute(f'CREATE TABLE "{table}" (id INTEGER PRIMARY KEY)')
            connection.execute(f'INSERT INTO "{table}" DEFAULT VALUES')


def test_prepare_creates_verified_single_file_without_sidecars(tmp_path):
    source = tmp_path / "source.db"
    target = tmp_path / "prepared.db"
    _valid_source(source)

    prepare(source, target)

    with sqlite3.connect(target) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    assert not (tmp_path / "prepared.db-wal").exists()
    assert not (tmp_path / "prepared.db-shm").exists()


def test_prepare_stamps_schema_version_so_runtime_never_replays_migration(tmp_path):
    """A shipped DB must carry user_version so the one-off destructive
    legacy merge (pipeline.db.SCHEMA_VERSION gate) never runs at runtime."""
    source = tmp_path / "source.db"
    target = tmp_path / "prepared.db"
    _valid_source(source)

    prepare(source, target)

    with sqlite3.connect(target) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION


def test_prepare_failure_preserves_existing_target(tmp_path):
    source = tmp_path / "corrupt.db"
    source.write_bytes(b"not a sqlite database")
    target = tmp_path / "prepared.db"
    target.write_bytes(b"last known good")

    with pytest.raises(sqlite3.DatabaseError):
        prepare(source, target)

    assert target.read_bytes() == b"last known good"


def test_prepare_rejects_source_with_fk_violations(tmp_path):
    source = tmp_path / "orphan.db"
    with sqlite3.connect(source) as connection:
        for table in ("person", "organization", "mandate", "membership", "event"):
            connection.execute(f'CREATE TABLE "{table}" (id INTEGER PRIMARY KEY)')
            connection.execute(f'INSERT INTO "{table}" DEFAULT VALUES')
        connection.execute(
            "CREATE TABLE evidence (id INTEGER PRIMARY KEY, "
            "membership_id INTEGER REFERENCES membership(id))"
        )
        connection.execute("INSERT INTO evidence DEFAULT VALUES")
        connection.execute("INSERT INTO evidence (membership_id) VALUES (999)")  # orphan

    target = tmp_path / "prepared.db"
    target.write_bytes(b"last known good")

    with pytest.raises(SystemExit, match="foreign key violations"):
        prepare(source, target)

    assert target.read_bytes() == b"last known good"


def test_prepared_output_has_clean_foreign_keys(tmp_path):
    source = tmp_path / "source.db"
    target = tmp_path / "prepared.db"
    _valid_source(source)

    prepare(source, target)

    with sqlite3.connect(target) as connection:
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_prepare_rejects_empty_dataset_without_replacing_target(tmp_path):
    source = tmp_path / "empty.db"
    with sqlite3.connect(source) as connection:
        for table in ("person", "organization", "mandate", "membership", "event", "evidence"):
            connection.execute(f'CREATE TABLE "{table}" (id INTEGER PRIMARY KEY)')
    target = tmp_path / "prepared.db"
    target.write_bytes(b"last known good")

    with pytest.raises(SystemExit, match="empty required tables"):
        prepare(source, target)

    assert target.read_bytes() == b"last known good"
