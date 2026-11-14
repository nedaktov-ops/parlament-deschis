"""CLI smoke tests: the integrity gate and analytics entrypoint must run.

These are regressions for two hard crashes found during the audit:
* ``parlament verify`` raised UnboundLocalError (a local ``select`` import
  shadowed the module-level one) and, once that was fixed, AttributeError on
  ``args.strict`` because the flag was never registered.
* ``python -m pipeline.analytics`` raised NameError: init_db, and its argument
  parsing confused the DB path with the subcommand.
"""

from __future__ import annotations

from datetime import date

from pipeline.analytics import main as analytics_main
from pipeline.cli import main as cli_main
from pipeline.db import Membership, Organization, Person, get_session


def _db_with_membership(path):
    """A DB with one membership and no evidence row (exercises --strict)."""
    session = get_session(path)
    org = Organization(
        classification="group",
        name="Grupul Test",
        short_name="TST",
        normalized_name="grupul test",
        chamber="deputies",
    )
    person = Person(canonical_name="Test Person", normalized_name="test person")
    session.add_all([org, person])
    session.flush()
    session.add(
        Membership(
            person_id=person.id,
            org_id=org.id,
            chamber="deputies",
            start_date=date(2024, 12, 21),
        )
    )
    session.commit()
    session.close()


def test_verify_runs_on_empty_db(tmp_path):
    db = tmp_path / "cli.db"
    assert cli_main(["--db", str(db), "verify"]) == 0


def test_verify_runs_on_populated_db(tmp_path):
    """Regression: args.strict was missing from the verify subparser, so any
    DB with memberships crashed with AttributeError."""
    db = tmp_path / "cli.db"
    _db_with_membership(db)
    assert cli_main(["--db", str(db), "verify"]) == 0


def test_verify_strict_fails_without_evidence(tmp_path):
    db = tmp_path / "cli.db"
    _db_with_membership(db)
    assert cli_main(["--db", str(db), "verify", "--strict"]) == 1


def test_stats_runs(tmp_path):
    db = tmp_path / "cli.db"
    assert cli_main(["--db", str(db), "stats"]) == 0


def test_analytics_main_runs(tmp_path):
    db = tmp_path / "analytics.db"
    assert analytics_main(["--db", str(db)]) == 0


def test_analytics_subcommand(tmp_path):
    db = tmp_path / "analytics.db"
    assert analytics_main(["--db", str(db), "waves"]) == 0
