import json
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from pipeline.audit import (
    Finding,
    audit,
    check_index_reconciliation,
    check_mandate_coverage,
    check_roster_reconciliation,
    finding_fingerprint,
    scope_totals,
)
from pipeline.cli import cmd_audit_corpus
from pipeline.db import (
    Event,
    Evidence,
    Mandate,
    Membership,
    Organization,
    Person,
    init_db,
    make_engine,
    make_session_factory,
)


@pytest.fixture
def session(tmp_path):
    engine = make_engine(tmp_path / "audit.db")
    init_db(engine)
    session = make_session_factory(engine)()
    try:
        yield session
    finally:
        session.close()


def _person(session, name):
    person = Person(
        canonical_name=name,
        normalized_name=name.lower(),
        sort_key=name.lower(),
    )
    session.add(person)
    session.flush()
    return person


def _organization(session, short_name):
    organization = Organization(
        classification="group",
        name=short_name,
        normalized_name=short_name.lower(),
        short_name=short_name,
    )
    session.add(organization)
    session.flush()
    return organization


def _membership(
    session,
    person,
    organization,
    *,
    start,
    end=None,
    source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.gp",
):
    membership = Membership(
        person_id=person.id,
        org_id=organization.id,
        chamber="deputies",
        legislature="2024",
        start_date=start,
        end_date=end,
        source_url=source_url,
        confidence="official_ledger",
    )
    session.add(membership)
    session.flush()
    session.add(
        Evidence(
            membership_id=membership.id,
            type="official_ledger",
            source_url=source_url,
        )
    )
    session.flush()
    return membership


def _mandate(session, person, *, start, end=None):
    mandate = Mandate(
        person_id=person.id,
        chamber="deputies",
        legislature="2024",
        start_date=start,
        end_date=end,
        source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.mp?idm=1",
        confidence="official_profile",
    )
    session.add(mandate)
    session.flush()
    return mandate


def _seed_clean_database(session):
    psd = _organization(session, "PSD")
    pro = _organization(session, "PRO")
    alice = _person(session, "Alice Ionescu")
    bob = _person(session, "Bob Popescu")

    _mandate(session, alice, start=date(2024, 1, 1), end=date(2024, 12, 31))
    _mandate(session, bob, start=date(2024, 1, 1), end=date(2024, 12, 31))
    _membership(session, alice, psd, start=date(2024, 1, 1), end=date(2024, 6, 1))
    _membership(session, alice, pro, start=date(2024, 6, 1), end=date(2024, 12, 31))
    _membership(session, bob, psd, start=date(2024, 1, 1), end=date(2024, 12, 31))

    session.add(
        Event(
            type="switch_group",
            person_id=alice.id,
            chamber="deputies",
            legislature="2024",
            from_org_id=psd.id,
            to_org_id=pro.id,
            event_date=date(2024, 6, 1),
            source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.gp?idg=8",
            reason="CHANGED_GROUP",
        )
    )
    session.commit()
    return alice, bob, psd, pro


def test_clean_database_has_no_audit_errors(session, monkeypatch):
    _seed_clean_database(session)
    monkeypatch.chdir(Path(session.get_bind().url.database).parent)

    report = audit(session)

    assert report.errors == []
    assert {check["name"] for check in report.checks} == {
        "mandate_coverage",
        "overlap",
        "evidence",
        "switch_event",
        "scope_totals",
        "roster_reconciliation",
        "index_reconciliation",
        "interval_order",
        "missing_start",
        "batched_dates",
        "vote_evidence",
    }


def test_index_reconciliation_warns_when_source_cache_is_missing(session, tmp_path, monkeypatch):
    _seed_clean_database(session)
    monkeypatch.chdir(tmp_path)

    findings = check_index_reconciliation(session)

    assert len(findings) == 1
    assert findings[0].severity == "warning"
    assert "not evaluated" in findings[0].detail
    assert findings[0].context["not_evaluated"] is True
    assert findings[0].context["missing_scopes"]


def test_overlap_in_two_groups_is_an_error(session, monkeypatch):
    alice, _bob, psd, pro = _seed_clean_database(session)
    _membership(session, alice, pro, start=date(2024, 3, 1), end=date(2024, 5, 1))
    session.commit()
    monkeypatch.chdir(Path(session.get_bind().url.database).parent)

    report = audit(session)

    overlap_errors = [finding for finding in report.errors if finding.check == "overlap"]
    assert len(overlap_errors) == 1
    assert overlap_errors[0].person_id == alice.id
    assert "PSD" in overlap_errors[0].detail
    assert "PRO" in overlap_errors[0].detail


def test_membership_without_source_url_is_an_error(session, monkeypatch):
    alice, _bob, psd, _pro = _seed_clean_database(session)
    membership = session.query(Membership).filter(Membership.person_id == alice.id).first()
    membership.source_url = None
    session.commit()
    monkeypatch.chdir(Path(session.get_bind().url.database).parent)

    report = audit(session)

    evidence_errors = [finding for finding in report.errors if finding.check == "evidence"]
    assert any("no source URL" in finding.detail for finding in evidence_errors)


def test_mandate_coverage_gap_is_an_error(session, monkeypatch):
    alice, _bob, psd, _pro = _seed_clean_database(session)
    membership = session.query(Membership).filter(Membership.person_id == alice.id).first()
    membership.end_date = date(2024, 3, 1)
    session.commit()
    monkeypatch.chdir(Path(session.get_bind().url.database).parent)

    report = audit(session)

    coverage_errors = [finding for finding in report.errors if finding.check == "mandate_coverage"]
    assert len(coverage_errors) == 1
    assert coverage_errors[0].person_id == alice.id
    assert "gap in group membership" in coverage_errors[0].detail
    assert coverage_errors[0].context["days"] == 92


def test_person_scoped_finding_checks_carry_the_person_name(session, monkeypatch):
    """Fingerprints rely on names; every person-scoped check must populate it.

    Otherwise two findings for two different people with the same detail
    collapse into one fingerprint and the gate can miss a real regression.
    """
    alice, bob, psd, _pro = _seed_clean_database(session)

    event = session.query(Event).filter(Event.person_id == alice.id).one()
    event.source_url = None

    first = session.query(Membership).filter(Membership.person_id == alice.id).first()
    first.start_date = date(2024, 6, 1)
    first.end_date = date(2024, 1, 1)

    _membership(session, bob, psd, start=None, end=date(2024, 12, 31))
    session.commit()
    monkeypatch.chdir(Path(session.get_bind().url.database).parent)

    report = audit(session)

    scoped = [
        finding
        for finding in report.errors
        if finding.check in {"switch_event", "interval_order", "missing_start"}
    ]
    assert {finding.check for finding in scoped} == {
        "switch_event",
        "interval_order",
        "missing_start",
    }
    assert all(finding.name for finding in scoped)


def test_finding_fingerprint_is_stable_across_person_id_regeneration():
    """Person ids are random UUIDs; the baseline must survive a re-ingest."""
    first = Finding(
        check="mandate_coverage",
        severity="error",
        chamber="senate",
        legislature="2004",
        person_id="11111111-1111-1111-1111-111111111111",
        name="Şerban-Cezar STRĂTILĂ",
        detail="gap in group membership between 2006-12-19 and 2007-12-17",
        context={"days": 363},
    )
    second = Finding(
        check="mandate_coverage",
        severity="error",
        chamber="senate",
        legislature="2004",
        person_id="22222222-2222-2222-2222-222222222222",
        name="Serban-Cezar Stratila",
        detail="gap in group membership between 2006-12-19 and 2007-12-17",
        context={"days": 363},
    )

    assert finding_fingerprint(first) == finding_fingerprint(second)


def test_finding_fingerprint_separates_different_findings():
    base = dict(
        check="overlap",
        severity="error",
        chamber="deputies",
        legislature="2016",
        person_id="11111111-1111-1111-1111-111111111111",
        name="Ion POPESCU",
        detail="sits in PSD and PRO at the same time",
        context={"overlap_days": 524},
    )

    same_shape = Finding(**base)
    other_person = Finding(**{**base, "name": "Maria IONESCU"})
    other_detail = Finding(**{**base, "detail": "sits in PSD and PNL at the same time"})

    assert finding_fingerprint(same_shape) != finding_fingerprint(other_person)
    assert finding_fingerprint(same_shape) != finding_fingerprint(other_detail)


def test_scope_totals_count_distinct_people_and_switch_events(session, monkeypatch):
    _seed_clean_database(session)
    monkeypatch.chdir(Path(session.get_bind().url.database).parent)

    totals = scope_totals(session)

    assert totals == [
        {
            "chamber": "deputies",
            "legislature": "2024",
            "members": 2,
            "memberships": 3,
            "switches": 1,
        }
    ]


# --- P0-3: strict audit gate must be symmetric -------------------------------
# A reviewed baseline error that silently disappears (data loss, a skipped
# source) must fail --strict just as loudly as a brand-new error. These tests
# use tiny synthetic databases so they never touch data/*.db or the real cache.


def _write_baseline(path: Path, findings: list[Finding]) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "error_findings": len(findings),
                "findings": [finding.as_dict() for finding in findings],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _run_gate(db_path: Path, baseline: Path | None, *, strict: bool = True) -> int:
    return cmd_audit_corpus(
        SimpleNamespace(
            db=str(db_path),
            baseline=str(baseline) if baseline is not None else None,
            strict=strict,
            json=None,
        )
    )


def test_skipped_checks_are_reported_as_not_evaluated(session, monkeypatch, tmp_path):
    """The two silent early returns now emit explicit not-evaluated findings."""
    coverage = check_mandate_coverage(session)  # no mandates seeded
    assert len(coverage) == 1
    assert coverage[0].context["not_evaluated"] is True
    assert coverage[0].context["reason"] == "no_mandates"

    monkeypatch.chdir(tmp_path)  # no data/cache/cdep
    roster = check_roster_reconciliation(session)
    assert len(roster) == 1
    assert roster[0].context["not_evaluated"] is True
    assert roster[0].context["reason"] == "cache_missing"


def test_strict_gate_passes_when_baseline_matches(session, tmp_path, monkeypatch):
    """Intact data + a fully reproduced baseline -> EXIT 0 (no false positive)."""
    monkeypatch.chdir(tmp_path)
    db_path = Path(session.get_bind().url.database)
    psd = _organization(session, "PSD")
    alice = _person(session, "Alice Ionescu")
    _mandate(session, alice, start=date(2024, 1, 1), end=date(2024, 12, 31))
    _membership(
        session, alice, psd, start=date(2024, 1, 1), end=date(2024, 12, 31), source_url=None
    )
    session.commit()

    errors = audit(session).errors
    assert len(errors) == 1 and errors[0].check == "evidence"
    baseline = tmp_path / "baseline.json"
    _write_baseline(baseline, errors)

    assert _run_gate(db_path, baseline, strict=True) == 0


def test_strict_gate_fails_when_a_baseline_finding_resolves(session, tmp_path, monkeypatch, capsys):
    """A reviewed error that disappears is a FAIL, naming the affected check."""
    monkeypatch.chdir(tmp_path)
    db_path = Path(session.get_bind().url.database)
    psd = _organization(session, "PSD")
    alice = _person(session, "Alice Ionescu")
    _mandate(session, alice, start=date(2024, 1, 1), end=date(2024, 12, 31))
    membership = _membership(
        session, alice, psd, start=date(2024, 1, 1), end=date(2024, 12, 31), source_url=None
    )
    session.commit()

    baseline = tmp_path / "baseline.json"
    _write_baseline(baseline, audit(session).errors)

    # Remove the defect that produced the reviewed finding.
    membership.source_url = "https://www.cdep.ro/ords/pls/parlam/structura2015.gp?idg=8"
    session.commit()

    exit_code = _run_gate(db_path, baseline, strict=True)
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "STRICT AUDIT FAILED" in out
    assert "evidence" in out


def test_strict_gate_fails_when_all_mandates_deleted(tmp_path, monkeypatch, capsys):
    """The regression for the proven defect: DELETE FROM mandate must not pass."""
    monkeypatch.chdir(tmp_path)
    db_path = tmp_path / "deleted.db"
    init_db(make_engine(db_path))
    seed = make_session_factory(make_engine(db_path))()
    bob = _person(seed, "Bob Popescu")
    _mandate(seed, bob, start=date(2024, 1, 1), end=date(2024, 12, 31))  # no membership
    seed.commit()

    errors = audit(seed).errors
    assert len(errors) == 1 and errors[0].check == "mandate_coverage"
    baseline = tmp_path / "baseline.json"
    _write_baseline(baseline, errors)
    seed.close()

    # Sanity: the matching baseline passes on the intact scratch DB.
    assert _run_gate(db_path, baseline, strict=True) == 0

    # Destructive step runs only on this tmp copy, never on data/*.db.
    writer = make_session_factory(make_engine(db_path))()
    writer.execute(text("DELETE FROM mandate"))
    writer.commit()
    writer.close()

    exit_code = _run_gate(db_path, baseline, strict=True)
    out = capsys.readouterr().out
    assert exit_code == 1
    assert "STRICT AUDIT FAILED" in out
    assert "mandate_coverage" in out
    assert "not evaluated" in out.lower()


def test_strict_gate_still_fails_on_new_errors(session, tmp_path, monkeypatch, capsys):
    """The original gate behaviour is preserved, not weakened."""
    monkeypatch.chdir(tmp_path)
    db_path = Path(session.get_bind().url.database)
    psd = _organization(session, "PSD")
    alice = _person(session, "Alice Ionescu")
    _mandate(session, alice, start=date(2024, 1, 1), end=date(2024, 12, 31))
    _membership(
        session, alice, psd, start=date(2024, 1, 1), end=date(2024, 12, 31), source_url=None
    )
    session.commit()

    empty_baseline = tmp_path / "empty.json"
    _write_baseline(empty_baseline, [])

    assert _run_gate(db_path, empty_baseline, strict=True) == 1
    assert "new error" in capsys.readouterr().out


def test_non_strict_gate_never_fails(session, tmp_path, monkeypatch):
    """Without --strict the command stays a pure report."""
    monkeypatch.chdir(tmp_path)
    db_path = Path(session.get_bind().url.database)
    psd = _organization(session, "PSD")
    alice = _person(session, "Alice Ionescu")
    _mandate(session, alice, start=date(2024, 1, 1), end=date(2024, 12, 31))
    _membership(
        session, alice, psd, start=date(2024, 1, 1), end=date(2024, 12, 31), source_url=None
    )
    session.commit()

    empty_baseline = tmp_path / "empty.json"
    _write_baseline(empty_baseline, [])

    assert _run_gate(db_path, empty_baseline, strict=False) == 0
