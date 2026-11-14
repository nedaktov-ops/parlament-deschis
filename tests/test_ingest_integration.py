"""End-to-end P0 gate: ingest real cdep ledger fixtures → dated memberships,
identity linking, and derived movement events in the DB.
"""

from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import select

from pipeline.db import Event, Membership, Organization, Person, get_session
from pipeline.ingest import ingest_cdep_group_ledger, seed_key_events
from pipeline.parse.cdep_group import parse_group_ledger
from pipeline.queries import chamber_composition, person_group_at

FX = Path(__file__).parent / "fixtures"


@pytest.fixture
def session():
    s = get_session(":memory:")
    seed_key_events(s)
    upr = parse_group_ledger(
        (FX / "cdep_group_upr.html").read_text(encoding="utf-8"),
        chamber="deputies",
        legislature="2024",
        source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.gp?cam=2&leg=2024&idg=9",
    )
    psd = parse_group_ledger(
        (FX / "cdep_group_psd.html").read_text(encoding="utf-8"),
        chamber="deputies",
        legislature="2024",
        source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.gp?cam=2&leg=2024&idg=1",
    )
    ingest_cdep_group_ledger(s, upr, legislature="2024")
    ingest_cdep_group_ledger(s, psd, legislature="2024")
    yield s
    s.close()


def test_upr_org_founding_and_rename(session):
    upr = session.scalars(
        select(Organization).where(
            Organization.short_name == "UPR", Organization.classification == "group"
        )
    ).one()
    assert upr.founding_date == date(2026, 5, 11)
    assert upr.alt_labels and any("POT" in a for a in upr.alt_labels)
    types = {e.type for e in session.scalars(select(Event))}
    assert "group_founded" in types
    # No rename event: the page publishes the former name but no rename date,
    # so dating a rename (to the founding date, as before) would be an
    # invention. The former name is preserved on the organization instead.
    assert "group_renamed" not in types


def test_ponta_single_person_two_tenures(session):
    ponta = session.scalars(select(Person).where(Person.canonical_name.like("%Ponta%"))).one()
    ms = list(session.scalars(select(Membership).where(Membership.person_id == ponta.id)))
    groups = [m for m in ms if session.get(Organization, m.org_id).classification == "group"]
    assert len(groups) == 2
    psd = next(m for m in groups if session.get(Organization, m.org_id).short_name == "PSD")
    upr = next(m for m in groups if session.get(Organization, m.org_id).short_name == "UPR")
    assert psd.end_date == date(2026, 6, 15)
    assert upr.start_date == date(2026, 6, 15)
    assert upr.end_date is None
    # UPR membership carries PSD as the party behind it (on_behalf_of).
    assert upr.on_behalf_of_id is not None
    assert session.get(Organization, upr.on_behalf_of_id).short_name == "PSD"


def test_ponta_switch_event(session):
    ponta = session.scalars(select(Person).where(Person.canonical_name.like("%Ponta%"))).one()
    ev = session.scalars(
        select(Event).where(Event.person_id == ponta.id, Event.type == "switch_group")
    ).one()
    assert ev.event_date == date(2026, 6, 15)
    assert "UPR" in ev.summary_ro
    # A group movement is not a party change: Ponta stayed on the PSD list.
    assert ev.reason == "CHANGED_GROUP"
    # The event must be citable.
    assert ev.source_url
    assert ev.legislature == "2024"


def test_group_at_time_slider(session):
    ponta = session.scalars(select(Person).where(Person.canonical_name.like("%Ponta%"))).one()
    before = person_group_at(session, ponta.id, date(2026, 6, 14))
    after = person_group_at(session, ponta.id, date(2026, 6, 15))
    assert session.get(Organization, before.org_id).short_name == "PSD"
    assert session.get(Organization, after.org_id).short_name == "UPR"


def test_enachi_former_interval(session):
    enachi = session.scalars(select(Person).where(Person.canonical_name.like("%Enachi%"))).one()
    ms = list(session.scalars(select(Membership).where(Membership.person_id == enachi.id)))
    upr = next(m for m in ms if session.get(Organization, m.org_id).short_name == "UPR")
    assert upr.start_date == date(2026, 6, 15)
    assert upr.end_date == date(2026, 9, 14)


def test_composition_counts(session):
    comp = chamber_composition(session, "deputies", date(2026, 11, 1))
    assert "UPR" in comp
    assert comp["UPR"]["count"] >= 10
    # Ponta counted in UPR, not PSD, on this date.
    names = [m["name"] for m in comp["UPR"]["members"]]
    assert any("Ponta" in n for n in names)


def test_idempotent_reingest(session):
    upr = parse_group_ledger(
        (FX / "cdep_group_upr.html").read_text(encoding="utf-8"),
        chamber="deputies",
        legislature="2024",
    )
    n_before = len(list(session.scalars(select(Membership))))
    ingest_cdep_group_ledger(session, upr, legislature="2024")
    n_after = len(list(session.scalars(select(Membership))))
    assert n_before == n_after  # no duplicate tenures
