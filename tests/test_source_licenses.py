"""Tests for the licence register.

The register is the mechanism that keeps non-commercial, ShareAlike and
unverified values out of a CC BY 4.0 dataset. These tests are deliberately
strict: a source that cannot be proven free is not free.
"""

from __future__ import annotations

import inspect

import pytest
from sqlalchemy.exc import IntegrityError

from pipeline.cli import cmd_build_corpus, main
from pipeline.db import SourceLicense, get_session
from pipeline.licenses import (
    COMPATIBLE_LICENSES,
    REGISTER,
    ensure_source_licenses,
    redistributable_sources,
)

CROSS_CHECK_ONLY = ("vot_parlament", "v_dem", "ipu", "open_sanctions", "populist", "ser_prom")
COPY_ALLOWED = (
    "cdep_facts",
    "senat_facts",
    "ro_281",
    "wikidata",
    "gld",
    "partyfacts",
    "ches_eui",
    "data_gov_ro",
    "zenodo_3332908",
)


@pytest.fixture
def session(tmp_path):
    return get_session(tmp_path / "licenses.db")


def test_register_covers_every_source_of_the_appendix(session):
    ensure_source_licenses(session)
    stored = {row.source_name: row for row in session.query(SourceLicense).all()}
    assert set(stored) == {entry.source_name for entry in REGISTER}
    assert len(REGISTER) == 15


def test_only_compatible_licences_are_redistributable(session):
    for entry in REGISTER:
        if entry.redistributable:
            assert entry.license_id in COMPATIBLE_LICENSES, entry.source_name
        else:
            assert (
                entry.license_id not in COMPATIBLE_LICENSES or entry.source_name == "vot_parlament"
            )


def test_cross_check_only_sources_cannot_be_redistributed(session):
    ensure_source_licenses(session)
    allowed = redistributable_sources(session)
    for name in CROSS_CHECK_ONLY:
        assert name not in allowed, f"{name} must stay display-only"
    for name in COPY_ALLOWED:
        assert name in allowed, f"{name} may be copied"


def test_the_281_attribution_string_is_exact(session):
    ensure_source_licenses(session)
    row = session.get(SourceLicense, "ro_281")
    assert row.attribution == "281.ro · Registrul neoficial al Parlamentului României"
    assert row.license_id == "CC-BY-4.0"
    assert row.redistributable is True


def test_vot_parlament_is_a_cross_check_not_a_source(session):
    ensure_source_licenses(session)
    row = session.get(SourceLicense, "vot_parlament")
    assert row.redistributable is False
    assert "ai-train=no" in row.note


def test_the_database_rejects_a_forged_redistributable_licence(session):
    """A ShareAlike source may never be marked redistributable."""
    session.add(
        SourceLicense(
            source_name="forged",
            license_id="CC-BY-SA-4.0",
            redistributable=True,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_seeding_twice_changes_nothing(session):
    ensure_source_licenses(session)
    first = {row.source_name: row.license_id for row in session.query(SourceLicense).all()}
    ensure_source_licenses(session)
    second = {row.source_name: row.license_id for row in session.query(SourceLicense).all()}
    assert first == second
    assert session.query(SourceLicense).count() == len(REGISTER)


# --- W2.1: the CLI path that actually seeds the register before release -------
# These drive the real argparse entry point (not just the helper), so a broken
# subcommand wiring or a missing commit is a test failure, not a silent no-op.


def _seed_via_cli(db_path) -> int:
    return main(["--db", str(db_path), "licenses-seed"])


_SNAPSHOT_COLUMNS = (
    "source_name",
    "license_id",
    "license_url",
    "redistributable",
    "share_alike",
    "attribution",
    "verification_url",
    "verification_quote",
    "verified_on",
    "note",
)


def _snapshot(db_path) -> list[tuple]:
    session = get_session(db_path)
    try:
        rows = session.query(SourceLicense).order_by(SourceLicense.source_name).all()
        return [tuple(getattr(row, column) for column in _SNAPSHOT_COLUMNS) for row in rows]
    finally:
        session.close()


def test_cli_seeds_exactly_fifteen_rows_on_an_empty_db(tmp_path, capsys):
    db = tmp_path / "cli-empty.db"
    assert _seed_via_cli(db) == 0
    assert "15 entries written, 15 rows in source_license" in capsys.readouterr().out
    session = get_session(db)
    try:
        assert session.query(SourceLicense).count() == 15
    finally:
        session.close()


def test_cli_reseeding_changes_nothing(tmp_path):
    db = tmp_path / "cli-reseed.db"
    assert _seed_via_cli(db) == 0
    first = _snapshot(db)
    assert _seed_via_cli(db) == 0
    assert _snapshot(db) == first
    assert len(first) == len(REGISTER)


def test_cli_seeded_cross_check_sources_stay_non_redistributable(tmp_path):
    db = tmp_path / "cli-crosscheck.db"
    assert _seed_via_cli(db) == 0
    session = get_session(db)
    try:
        rows = {row.source_name: row for row in session.query(SourceLicense).all()}
        for name in CROSS_CHECK_ONLY:
            assert rows[name].redistributable is False, f"{name} must stay display-only"
        assert redistributable_sources(session) == set(COPY_ALLOWED)
    finally:
        session.close()


def test_cli_seeded_db_still_rejects_a_forged_sa_row(tmp_path):
    db = tmp_path / "cli-forged.db"
    assert _seed_via_cli(db) == 0
    session = get_session(db)
    try:
        session.add(
            SourceLicense(
                source_name="forged",
                license_id="CC-BY-SA-4.0",
                redistributable=True,
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert session.query(SourceLicense).count() == len(REGISTER)
        assert session.get(SourceLicense, "forged") is None
    finally:
        session.close()


def test_init_also_seeds_the_register(tmp_path):
    """Fresh DBs get the register at init time, not only via the new command."""
    db = tmp_path / "cli-init.db"
    assert main(["--db", str(db), "init"]) == 0
    session = get_session(db)
    try:
        assert session.query(SourceLicense).count() == len(REGISTER)
    finally:
        session.close()


def test_build_corpus_seeds_before_it_writes_corpus_rows():
    """data.yml prepares the release from the DB this command writes."""
    source = inspect.getsource(cmd_build_corpus)
    assert "ensure_source_licenses" in source
    assert source.index("ensure_source_licenses") < source.index("stats = ingest_corpus(")
