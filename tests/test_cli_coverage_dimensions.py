"""Coverage CLI prints the honest dimension view additively (W2.2 follow-up).

The ``coverage`` subcommand must keep its mandate-only lines byte-identical for
compatibility, while appending a per-scope mandates / votes / biographies view.
Votes are never reported as ``full`` because there is no published expected
total for them.
"""

from __future__ import annotations

from datetime import date

from pipeline.cli import main as cli_main
from pipeline.db import Membership, Organization, Person, Vote, get_session
from pipeline.ingest import seed_key_events


def _seed_scope(db, *, with_votes: bool) -> None:
    """One deputy group tenure + person, optionally with two in-scope votes."""
    session = get_session(db)
    seed_key_events(session)
    org = Organization(
        classification="group",
        name="Grupul Test",
        short_name="TST",
        normalized_name="grupul test",
        chamber="deputies",
    )
    person = Person(
        canonical_name="Test Person",
        normalized_name="test person",
        birth_date=date(1990, 5, 5),
    )
    session.add_all([org, person])
    session.flush()
    session.add(
        Membership(
            person_id=person.id,
            org_id=org.id,
            chamber="deputies",
            legislature="2024",
            start_date=date(2024, 12, 21),
        )
    )
    if with_votes:
        session.add_all(
            [
                Vote(
                    source="cdep",
                    native_vote_id="v-1",
                    chamber="deputies",
                    legislature="2024",
                    source_url="https://www.cdep.ro/v1",
                    dedup_key="vote:w22:1",
                ),
                Vote(
                    source="cdep",
                    native_vote_id="v-2",
                    chamber="deputies",
                    legislature="2024",
                    source_url="https://www.cdep.ro/v2",
                    dedup_key="vote:w22:2",
                ),
            ]
        )
    session.commit()
    session.close()


def test_coverage_prints_dimensions_without_a_flag(tmp_path, capsys):
    db = tmp_path / "coverage.db"
    _seed_scope(db, with_votes=True)

    assert cli_main(["--db", str(db), "coverage"]) == 0
    out = capsys.readouterr().out

    # The original mandate-only output is untouched.
    assert "persons=   1  1 of ~330 seats ingested." in out
    # The additive dimension section is present and honest.
    assert "Coverage dimensions (mandates / votes / biographies):" in out
    assert "mandates=partial(1)" in out
    assert "votes=partial(2)" in out
    assert "biographies=full(1/1)" in out
    # Votes must never be upgraded to "full".
    assert "votes=full" not in out


def test_coverage_votes_none_without_vote_rows(tmp_path, capsys):
    db = tmp_path / "coverage.db"
    _seed_scope(db, with_votes=False)

    assert cli_main(["--db", str(db), "coverage"]) == 0
    out = capsys.readouterr().out
    assert "votes=none(0)" in out
    assert "votes=full" not in out


def test_coverage_empty_db_exits_zero(tmp_path, capsys):
    db = tmp_path / "empty.db"
    assert cli_main(["--db", str(db), "coverage"]) == 0
    out = capsys.readouterr().out
    assert "Coverage dimensions (mandates / votes / biographies):" in out


def test_coverage_help_still_works(capsys):
    try:
        cli_main(["coverage", "--help"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("coverage --help must exit via argparse")
    assert "--refresh" in capsys.readouterr().out
