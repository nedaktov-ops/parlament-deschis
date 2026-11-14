from datetime import date
from pathlib import Path

import pytest

from pipeline.audit import audit, scope_totals
from pipeline.db import (
    Evidence,
    Event,
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
    }


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
