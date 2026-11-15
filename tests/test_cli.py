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


def test_audit_strict_allows_only_fingerprinted_baseline_findings(tmp_path, monkeypatch):
    import json

    from pipeline.audit import audit

    monkeypatch.chdir(tmp_path)
    db = tmp_path / "audit.db"
    _db_with_membership(db)
    session = get_session(db)
    try:
        known_findings = [error.as_dict() for error in audit(session).errors]
    finally:
        session.close()

    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps({"schema_version": 1, "findings": known_findings}),
        encoding="utf-8",
    )
    assert cli_main(["--db", str(db), "audit-corpus", "--strict", "--baseline", str(baseline)]) == 0

    baseline.write_text(json.dumps({"schema_version": 1, "findings": []}), encoding="utf-8")
    assert cli_main(["--db", str(db), "audit-corpus", "--strict", "--baseline", str(baseline)]) == 1


def test_audit_baseline_survives_person_id_regeneration(tmp_path, monkeypatch):
    """Regression: random person ids made every release fail the audit gate.

    Two independent ingests of the same corpus produce different UUIDs. A
    reviewed baseline must still recognise the same findings on the second
    ingest, otherwise the gate fails on every release and protects nothing.
    """
    import json

    from pipeline.audit import audit

    monkeypatch.chdir(tmp_path)
    first_db = tmp_path / "first.db"
    _db_with_membership(first_db)
    session = get_session(first_db)
    try:
        findings = [error.as_dict() for error in audit(session).errors]
    finally:
        session.close()
    assert findings  # the fixture membership has no evidence row

    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps({"schema_version": 1, "findings": findings}),
        encoding="utf-8",
    )

    second_db = tmp_path / "second.db"
    _db_with_membership(second_db)  # fresh uuid4 person/org/membership ids

    assert (
        cli_main(["--db", str(second_db), "audit-corpus", "--strict", "--baseline", str(baseline)])
        == 0
    )


def test_audit_does_not_count_unevaluated_baseline_findings_as_resolved(
    tmp_path, monkeypatch, capsys
):
    import json

    from pipeline.audit import Finding, audit

    monkeypatch.chdir(tmp_path)
    db = tmp_path / "audit.db"
    _db_with_membership(db)
    session = get_session(db)
    try:
        baseline_findings = [error.as_dict() for error in audit(session).errors]
    finally:
        session.close()
    baseline_findings.append(
        Finding(
            check="index_reconciliation",
            severity="error",
            chamber="deputies",
            legislature="2024",
            detail="reviewed finding from source pages unavailable to this audit",
        ).as_dict()
    )
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "error_findings": len(baseline_findings),
                "findings": baseline_findings,
            }
        ),
        encoding="utf-8",
    )

    assert cli_main(["--db", str(db), "audit-corpus", "--strict", "--baseline", str(baseline)]) == 0
    assert (
        "0 resolved baseline findings, 1 baseline findings not evaluated" in capsys.readouterr().out
    )


def test_build_corpus_strict_stops_before_ingesting_partial_sources(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import pytest

    import pipeline.collect
    import pipeline.ingest_corpus

    corpus = SimpleNamespace(
        errors=["profile request timed out"],
        ledgers=[],
        profiles={},
        clusters={},
        rosters=[],
        index_counts={},
    )
    monkeypatch.setattr(pipeline.collect, "build_corpus", lambda *args, **kwargs: corpus)
    monkeypatch.setattr(
        pipeline.ingest_corpus,
        "ingest_corpus",
        lambda *_args, **_kwargs: pytest.fail("partial corpus must not be ingested"),
    )

    assert (
        cli_main(
            [
                "--db",
                str(tmp_path / "strict.db"),
                "build-corpus",
                "--chamber",
                "deputies",
                "--strict",
            ]
        )
        == 1
    )


def test_build_corpus_strict_rejects_empty_legislature_selection(tmp_path):
    assert (
        cli_main(
            [
                "--db",
                str(tmp_path / "empty.db"),
                "build-corpus",
                "--chamber",
                "deputies",
                "--from",
                "9999",
                "--strict",
            ]
        )
        == 1
    )
