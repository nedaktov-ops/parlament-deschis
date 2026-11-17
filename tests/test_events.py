"""Focused tests for pipeline.events derivation honesty (P3-D).

Party events must not borrow the dated group tenure's start, join reasons must
be carried from the source, and ambiguous / overlapping handoffs must be
recoverable (logged / flagged) rather than silently fabricated or hidden.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date

import pytest

from pipeline.db import (
    Event,
    KeyEvent,
    Membership,
    Organization,
    Person,
    init_db,
    make_engine,
    make_session_factory,
)
from pipeline.events import derive_group_events, derive_party_events


@pytest.fixture
def session(tmp_path):
    engine = make_engine(tmp_path / "events.db")
    init_db(engine)
    s = make_session_factory(engine)()
    try:
        yield s
    finally:
        s.close()


def _person(s, name="Test Person"):
    p = Person(canonical_name=name, normalized_name=name.lower(), sort_key=name.lower())
    s.add(p)
    s.flush()
    return p


def _org(s, name, classification="group"):
    o = Organization(
        classification=classification,
        name=name,
        normalized_name=f"{name.lower()}-{uuid.uuid4().hex[:6]}",
        short_name=name,
    )
    s.add(o)
    s.flush()
    return o


def _group_membership(
    s,
    person,
    org,
    *,
    start,
    end=None,
    start_reason=None,
    on_behalf_of_id=None,
    chamber="deputies",
    legislature="2024",
):
    m = Membership(
        person_id=person.id,
        org_id=org.id,
        chamber=chamber,
        legislature=legislature,
        start_date=start,
        end_date=end,
        start_precision=start.isoformat(),
        start_reason=start_reason,
        on_behalf_of_id=on_behalf_of_id,
        confidence="official_ledger",
    )
    s.add(m)
    s.flush()
    return m


# --- reason propagation -----------------------------------------------------
def test_join_event_carries_source_start_reason(session):
    p = _person(session)
    g = _org(session, "PSD")
    _group_membership(session, p, g, start=date(2024, 1, 1), start_reason="VALIDATION_DATE")
    derive_group_events(session)
    ev = session.query(Event).filter_by(type="join").one()
    assert ev.event_date == date(2024, 1, 1)
    assert ev.reason == "VALIDATION_DATE"


# --- party events carry no fabricated date ----------------------------------
def test_party_join_event_has_no_fabricated_date(session):
    p = _person(session)
    g = _org(session, "PSD group")
    party = _org(session, "PSD", classification="party")
    _group_membership(
        session,
        p,
        g,
        start=date(2024, 1, 1),
        start_reason="LEGISLATURE_START",
        on_behalf_of_id=party.id,
    )
    derive_party_events(session)
    ev = session.query(Event).filter_by(type="join_party").one()
    assert ev.event_date is None
    assert ev.precision == "unknown"
    assert ev.reason == "LEGISLATURE_START"  # real reason carried, not GENERAL_ELECTION
    assert "no join date" in (ev.summary_en or "")


def test_party_switch_event_has_no_fabricated_date(session):
    p = _person(session)
    g1, g2 = _org(session, "Group A"), _org(session, "Group B")
    party1 = _org(session, "Party A", classification="party")
    party2 = _org(session, "Party B", classification="party")
    _group_membership(
        session, p, g1, start=date(2024, 1, 1), end=date(2024, 6, 1), on_behalf_of_id=party1.id
    )
    _group_membership(session, p, g2, start=date(2024, 6, 1), on_behalf_of_id=party2.id)
    derive_party_events(session)
    ev = session.query(Event).filter_by(type="switch_party").one()
    assert ev.event_date is None
    assert ev.precision == "unknown"
    assert ev.reason == "CHANGED_PARTY"


# --- ambiguous / overlapping handoffs ---------------------------------------
def test_ambiguous_handoff_is_logged_not_fabricated(session, caplog):
    p = _person(session)
    g1, g2 = _org(session, "Group A"), _org(session, "Group B")
    # A multi-day overlap (start more than one day before the prior end) cannot
    # be dated from the source: no switch may be invented for it.
    _group_membership(session, p, g1, start=date(2024, 1, 1), end=date(2024, 6, 10))
    _group_membership(session, p, g2, start=date(2024, 6, 1))
    with caplog.at_level(logging.WARNING, logger="parlament.events"):
        derive_group_events(session)
    assert session.query(Event).filter_by(type="switch_group").count() == 0
    lines = [r.message for r in caplog.records if "ambiguous_membership_handoff " in r.message]
    assert lines, "ambiguous handoff must be logged with all inputs"
    payload = json.loads(lines[0].split(" ", 1)[1])
    assert payload["from_org_id"] == g1.id
    assert payload["to_org_id"] == g2.id
    assert payload["from_end_date"] == "2024-06-10"
    assert payload["to_start_date"] == "2024-06-01"


def test_one_day_overlap_switch_is_flagged(session, caplog):
    p = _person(session)
    g1, g2 = _org(session, "Group A"), _org(session, "Group B")
    _group_membership(session, p, g1, start=date(2024, 1, 1), end=date(2024, 6, 2))
    _group_membership(session, p, g2, start=date(2024, 6, 1))
    with caplog.at_level(logging.WARNING, logger="parlament.events"):
        derive_group_events(session)
    ev = session.query(Event).filter_by(type="switch_group").one()
    assert "one-day overlap" in (ev.summary_en or "")
    assert any("one_day_overlap_switch" in r.message for r in caplog.records)


# --- coverage.py -------------------------------------------------------------
# (no dedicated test_coverage.py in this work item's exclusive file set)
def _seed_key_event(s, term, chamber, start, end=None):
    s.add(
        KeyEvent(
            type="legislature",
            chamber=chamber,
            label=term,
            start_date=start,
            end_date=end,
        )
    )
    s.flush()


def _fill(s, term, chamber, n):
    g = _org(s, f"Group {term} {chamber}")
    for i in range(n):
        p = _person(s, f"{term} {chamber} member {i}")
        _group_membership(s, p, g, start=date(2024, 1, 1), chamber=chamber, legislature=term)


def test_coverage_1990_deputies_uses_396_seats(session):
    from pipeline.coverage import coverage_snapshot

    _seed_key_event(session, "1990", "deputies", date(1990, 6, 18), date(1992, 10, 8))
    _fill(session, "1990", "deputies", 300)  # > 330*0.9=297 but < 396*0.9=356.4
    row = next(r for r in coverage_snapshot(session) if r["legislature"] == "1990")
    assert row["completeness"] == "partial"
    assert "~396 seats" in row["note"]

    _fill(session, "1990", "deputies", 60)  # 360 >= 356.4 → legitimately full
    row = next(r for r in coverage_snapshot(session) if r["legislature"] == "1990")
    assert row["completeness"] == "full"


def test_coverage_unknown_seats_never_full(session):
    from pipeline.coverage import coverage_snapshot

    _seed_key_event(session, "1996", "deputies", date(1996, 11, 4), date(2000, 12, 4))
    _fill(session, "1996", "deputies", 300)
    row = next(r for r in coverage_snapshot(session) if r["legislature"] == "1996")
    assert row["completeness"] == "partial"
    assert "not known" in row["note"]


def test_coverage_modern_uses_330_seats(session):
    from pipeline.coverage import coverage_snapshot

    _seed_key_event(session, "2024", "deputies", date(2024, 12, 21))
    _fill(session, "2024", "deputies", 300)  # >= 330*0.9=297
    row = next(r for r in coverage_snapshot(session) if r["legislature"] == "2024")
    assert row["completeness"] == "full"
