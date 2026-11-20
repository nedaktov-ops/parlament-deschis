"""Dry-run / apply behaviour of the roll-call vote importer.

The importer is the most dangerous code in the project, because it touches
the people table. The rules it must never break:

* it **never creates a person** - an unresolved vote is quarantined, not
  invented;
* it resolves people **by identifier only** (cdep idm), never by name;
* a dry run writes **nothing at all** to the database;
* a corrupted fixture aborts the whole import before any write;
* importing twice is idempotent.

The tests run offline. No test may open a socket (asserted explicitly).
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import func, select

from pipeline.db import (
    Mandate,
    Person,
    PersonIdentifier,
    Vote,
    VoteImportRun,
    VotePosition,
    get_session,
)
from pipeline.votes import ManifestMismatch, import_votes

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures" / "votes"
REAL_DB = REPO / "data" / "parlament-real.db"


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Any socket connection during an import is a test failure."""

    def _boom(*args, **kwargs):
        raise AssertionError("the vote importer must not touch the network")

    monkeypatch.setattr(socket_module.socket, "connect", _boom)


import socket as socket_module  # noqa: E402  (imported late so the patch is obvious)


def _corpus_copy(tmp_path: Path) -> Path:
    """WAL-safe copy of the shipped corpus (never a raw file copy)."""
    target = tmp_path / "corpus.db"
    src = sqlite3.connect(f"file:{REAL_DB}?mode=ro", uri=True)
    dst = sqlite3.connect(target)
    src.backup(dst)
    dst.close()
    src.close()
    return target


def _synthetic_db(tmp_path: Path):
    """A tiny corpus with three known identity situations.

    * ``idm=1``  -> resolved through ``cdep_mandate``
    * ``idm=4``  -> resolved through ``cdep_idm`` (with a matching mandate)
    * ``idm=5``  -> ``cdep_idm`` exists but the person has no mandate in
      this chamber/legislature -> rejected (quarantined)
    * every other idm -> unknown in this corpus -> unresolved (quarantined)
    """
    session = get_session(tmp_path / "synthetic.db")
    people = {
        "1": ("deputies", "cdep_mandate", "deputies:2024:1"),
        "4": ("deputies", "cdep_idm", "4"),
        "5": ("deputies", "cdep_idm", "5"),
    }
    for idm, (chamber, scheme, identifier) in people.items():
        person = Person(canonical_name=f"Synthetic {idm}", normalized_name=f"synthetic {idm}")
        session.add(person)
        session.flush()
        session.add(
            PersonIdentifier(
                scheme=scheme, identifier=identifier, legislature="2024", person_id=person.id
            )
        )
        if idm != "5":  # idm=5 is the stub without a mandate
            session.add(
                Mandate(
                    person_id=person.id,
                    chamber=chamber,
                    legislature="2024",
                    start_date=__import__("datetime").date(2024, 12, 1),
                    source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.mp",
                )
            )
    session.commit()
    return session


def _counts(session) -> tuple[int, int, int, int]:
    return (
        session.scalar(select(func.count()).select_from(Vote)),
        session.scalar(select(func.count()).select_from(VotePosition)),
        session.scalar(select(func.count()).select_from(VoteImportRun)),
        session.scalar(select(func.count()).select_from(Person)),
    )


# --- manifest integrity -----------------------------------------------------


def test_manifest_matches_the_locked_fixtures():
    session = get_session(REPO / "data" / "parlament.db")
    report = import_votes(session, FIXTURES, dry_run=True)
    assert report.votes_seen == 1
    assert report.positions_seen == 246


def test_corrupted_fixture_aborts_before_any_write(tmp_path):
    session = _synthetic_db(tmp_path)
    fixtures = tmp_path / "fixtures"
    shutil.copytree(FIXTURES, fixtures)
    target = fixtures / "cdep_evot2015_nominal_37526.html"
    data = bytearray(target.read_bytes())
    data[100] = data[100] ^ 0x01
    target.write_bytes(bytes(data))

    with pytest.raises(ManifestMismatch):
        import_votes(session, fixtures, dry_run=True)

    votes, positions, runs, people = _counts(session)
    assert (votes, positions, runs) == (0, 0, 0)
    assert people == 3


# --- dry run ----------------------------------------------------------------


def test_dry_run_writes_nothing_at_all(tmp_path):
    session = _synthetic_db(tmp_path)
    before = _counts(session)

    report = import_votes(session, FIXTURES, dry_run=True)

    assert report.applied is False
    assert report.votes_written == 0
    assert report.positions_written == 0
    assert _counts(session) == before


def test_dry_run_reports_what_would_happen(tmp_path):
    session = _synthetic_db(tmp_path)
    report = import_votes(session, FIXTURES, dry_run=True)

    assert report.votes_seen == 1
    assert report.positions_seen == 246
    assert report.positions_resolved == 2  # idm 1 (mandate) + idm 4 (idm)
    assert report.unresolved_count == 244
    assert report.rejected_count == 1  # idm 5: idm without a mandate
    assert report.votes_written == 0
    assert report.positions_written == 0
    reasons = {q["reason"] for q in report.quarantined}
    assert "no_identifier" in reasons
    assert "mandate_check_failed" in reasons


# --- apply ------------------------------------------------------------------


def test_apply_writes_the_vote_and_the_resolved_positions(tmp_path):
    session = _synthetic_db(tmp_path)
    report = import_votes(session, FIXTURES, dry_run=False)

    assert report.applied is True
    assert report.votes_written == 1
    assert report.positions_written == 2

    vote = session.scalar(select(Vote))
    assert vote is not None
    assert vote.dedup_key == "cdep:37526"
    assert vote.source_url
    assert vote.snapshot_hash
    assert vote.present == 246
    assert vote.yes == 245
    assert vote.no == 0
    assert vote.abstain == 0
    assert vote.not_voting == 1
    assert vote.chamber == "deputies"
    assert vote.legislature == "2024"

    positions = list(session.scalars(select(VotePosition)))
    assert len(positions) == 2
    for position in positions:
        assert position.person_id
        assert position.choice in {"yes", "no", "abstain", "not_voting"}
        assert position.resolution_scheme in {"cdep_mandate", "cdep_idm", "cdep_person"}
        assert position.source_url
        assert position.dedup_key.startswith("cdep:37526:")
    assert {p.resolution_scheme for p in positions} == {"cdep_mandate", "cdep_idm"}


def test_apply_never_creates_a_person(tmp_path):
    session = _synthetic_db(tmp_path)
    people_before = session.scalar(select(func.count()).select_from(Person))

    import_votes(session, FIXTURES, dry_run=False)

    people_after = session.scalar(select(func.count()).select_from(Person))
    assert people_after == people_before == 3


def test_import_is_idempotent(tmp_path):
    session = _synthetic_db(tmp_path)
    first = import_votes(session, FIXTURES, dry_run=False)
    second = import_votes(session, FIXTURES, dry_run=False)

    assert second.votes_written == 0
    assert second.positions_written == 0
    assert second.votes_seen == first.votes_seen
    assert second.positions_seen == first.positions_seen
    votes, positions, _runs, _people = _counts(session)
    assert votes == 1
    assert positions == 2


def test_import_run_is_recorded_with_its_manifest_hash(tmp_path):
    session = _synthetic_db(tmp_path)
    import_votes(session, FIXTURES, dry_run=False)

    run = session.scalar(select(VoteImportRun))
    assert run is not None
    assert run.applied is True
    assert len(run.manifest_sha) == 64
    assert run.parser_version
    assert run.resolver_version
    assert run.policy_version
    assert run.votes_seen == 1
    assert run.positions_seen == 246


# --- resolution against the shipped corpus ----------------------------------


def test_resolution_against_the_shipped_corpus_matches_the_verified_counts(tmp_path):
    """146 cdep_mandate, 98 cdep_idm, 0 cdep_person, 2 unresolved, 1 rejected."""
    copy = _corpus_copy(tmp_path)
    session = get_session(copy)
    people_before = session.scalar(select(func.count()).select_from(Person))

    report = import_votes(session, FIXTURES, dry_run=True)

    assert report.positions_seen == 246
    assert report.resolved_by_scheme == {
        "cdep_mandate": 146,
        "cdep_idm": 98,
        "cdep_person": 0,
    }
    assert report.positions_resolved == 244
    assert report.unresolved_count == 2
    assert report.rejected_count == 1
    assert session.scalar(select(func.count()).select_from(Person)) == people_before
    assert people_before == 3388
