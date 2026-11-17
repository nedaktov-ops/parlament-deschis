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

import pytest

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


def test_build_corpus_ingests_committees_and_derives_waves(tmp_path, monkeypatch):
    """Committees + waves are part of the shippable corpus (prod gap fix).

    The pinned release DB exposed 0 committees and 0 waves on 2026-11-17
    because build-corpus never produced them. Guard the wiring without
    touching the network: fake the collection, ingest and source clients.
    """
    from types import SimpleNamespace

    import pipeline.analytics
    import pipeline.collect
    import pipeline.ingest_corpus
    import pipeline.sources.cdep_committee
    import pipeline.sources.client

    corpus = SimpleNamespace(
        errors=[], ledgers=[], profiles={}, clusters={}, rosters=[], index_counts={}
    )
    monkeypatch.setattr(pipeline.collect, "build_corpus", lambda *a, **k: corpus)
    monkeypatch.setattr(pipeline.ingest_corpus, "ingest_corpus", lambda *a, **k: {"persons": 0})

    calls: list[tuple] = []

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def close(self):
            pass

    class FakeCommitteeSource:
        def __init__(self, client):
            self.client = client

        def ingest_committees(self, session, legislature, *, idc_filter=None):
            calls.append(("committees", legislature))
            return {
                "committees": 26,
                "current": 0,
                "former": 0,
                "persons": 0,
                "unchanged": 0,
            }

    def fake_waves(session):
        calls.append(("waves",))
        return 142

    monkeypatch.setattr(pipeline.sources.client, "PoliteClient", FakeClient)
    monkeypatch.setattr(pipeline.sources.cdep_committee, "CdepCommitteeSource", FakeCommitteeSource)
    monkeypatch.setattr(pipeline.analytics, "derive_all_switch_waves", fake_waves)

    assert (
        cli_main(["--db", str(tmp_path / "build.db"), "build-corpus", "--chamber", "deputies"]) == 0
    )
    assert calls[0][0] == "committees"
    assert calls[0][1]  # a real legislature label, e.g. "2024"
    assert ("waves",) in calls


@pytest.mark.parametrize(
    ("ingest_totals", "expected"),
    [
        # First build: every fragment changed -> pass.
        ({"committees": 26, "unchanged": 0, "status": "SUCCESS"}, 0),
        # Idempotent re-run: 0 changed, all 26 unchanged -> must still pass.
        ({"committees": 0, "unchanged": 26, "status": "SUCCESS"}, 0),
        # Empty committee source -> must fail (completeness guarantee).
        ({"committees": 0, "unchanged": 0, "status": "SUCCESS"}, 1),
        # Failed/partial ingest: some committees but status FAILURE -> must fail.
        ({"committees": 5, "unchanged": 0, "status": "FAILURE"}, 1),
    ],
)
def test_build_corpus_strict_committee_gate(tmp_path, monkeypatch, ingest_totals, expected):
    """The --strict gate must accept unchanged pages and reject failed ingests.

    Regression: ``totals["committees"]`` counts only *changed* fragments, so a
    healthy idempotent second build reported 0 and falsely failed the gate.
    """
    from types import SimpleNamespace

    import pipeline.analytics
    import pipeline.collect
    import pipeline.ingest_corpus
    import pipeline.sources.cdep_committee
    import pipeline.sources.client
    from pipeline.cli import _load_legislatures

    # A corpus that satisfies the strict collection gate: one empty ledger,
    # roster and index per (chamber, legislature) scope, with no referenced
    # mandates. This lets the test reach the *committee* strict gate.
    legs = sorted(_load_legislatures())
    ledgers = [
        SimpleNamespace(
            chamber="deputies",
            legislature=leg,
            idg="1",
            ledger=SimpleNamespace(current=[], former=[], name_only=[]),
        )
        for leg in legs
    ]
    corpus = SimpleNamespace(
        errors=[],
        ledgers=ledgers,
        profiles={},
        clusters={},
        rosters=[SimpleNamespace(chamber="deputies", legislature=leg) for leg in legs],
        index_counts={("deputies", leg): {} for leg in legs},
    )
    monkeypatch.setattr(pipeline.collect, "build_corpus", lambda *a, **k: corpus)
    monkeypatch.setattr(pipeline.ingest_corpus, "ingest_corpus", lambda *a, **k: {"persons": 0})

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        def close(self):
            pass

    totals = {"committees": 0, "current": 0, "former": 0, "persons": 0, "unchanged": 0}
    totals.update(ingest_totals)

    class FakeCommitteeSource:
        def __init__(self, client):
            self.client = client

        def ingest_committees(self, session, legislature, **kwargs):
            return dict(totals)

    monkeypatch.setattr(pipeline.sources.client, "PoliteClient", FakeClient)
    monkeypatch.setattr(pipeline.sources.cdep_committee, "CdepCommitteeSource", FakeCommitteeSource)
    monkeypatch.setattr(pipeline.analytics, "derive_all_switch_waves", lambda session: 142)

    assert (
        cli_main(
            [
                "--db",
                str(tmp_path / "gate.db"),
                "build-corpus",
                "--chamber",
                "deputies",
                "--strict",
            ]
        )
        == expected
    )


def test_build_corpus_skip_committees_still_derives_waves(tmp_path, monkeypatch):
    """Escape hatch: --skip-committees must not skip the SQL-only wave step."""
    from types import SimpleNamespace

    import pipeline.analytics
    import pipeline.collect
    import pipeline.ingest_corpus
    import pipeline.sources.cdep_committee

    corpus = SimpleNamespace(
        errors=[], ledgers=[], profiles={}, clusters={}, rosters=[], index_counts={}
    )
    monkeypatch.setattr(pipeline.collect, "build_corpus", lambda *a, **k: corpus)
    monkeypatch.setattr(pipeline.ingest_corpus, "ingest_corpus", lambda *a, **k: {"persons": 0})

    def fail_committees(*a, **k):
        raise AssertionError("committee ingest must be skipped")

    monkeypatch.setattr(
        pipeline.sources.cdep_committee,
        "CdepCommitteeSource",
        fail_committees,
    )
    waves = []
    monkeypatch.setattr(
        pipeline.analytics,
        "derive_all_switch_waves",
        lambda session: waves.append(1) or 142,
    )

    assert (
        cli_main(
            [
                "--db",
                str(tmp_path / "skip.db"),
                "build-corpus",
                "--chamber",
                "deputies",
                "--skip-committees",
            ]
        )
        == 0
    )
    assert waves == [1]
