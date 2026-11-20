"""Tests for the licence register.

The register is the mechanism that keeps non-commercial, ShareAlike and
unverified values out of a CC BY 4.0 dataset. These tests are deliberately
strict: a source that cannot be proven free is not free.
"""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError

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
