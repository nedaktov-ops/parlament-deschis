from datetime import date

import pytest

from pipeline.db import Organization, Person, get_session
from pipeline.reconcile import (
    MembershipWriter,
    Observation,
    collapse_observations,
)


@pytest.fixture
def session():
    s = get_session(":memory:")
    yield s
    s.close()


def _person(session, name="Test Person"):
    p = Person(canonical_name=name, normalized_name=name.lower())
    session.add(p)
    session.flush()
    return p


def _org(session, name, classification="group"):
    o = Organization(classification=classification, name=name, normalized_name=name.lower())
    session.add(o)
    session.flush()
    return o


# --- collapse_observations -------------------------------------------------
def test_collapse_basic_switch():
    obs = [
        Observation("p", "A", date(2024, 1, 1)),
        Observation("p", "A", date(2024, 2, 1)),
        Observation("p", "B", date(2024, 3, 1)),
    ]
    ivs = collapse_observations(obs)
    assert len(ivs) == 2
    a = next(i for i in ivs if i.org_key == "A")
    b = next(i for i in ivs if i.org_key == "B")
    assert a.start == date(2024, 1, 1)
    assert a.end == date(2024, 2, 29)  # day before B observed
    assert b.start == date(2024, 3, 1)
    assert b.end is None


def test_collapse_order_independent():
    obs = [
        Observation("p", "B", date(2024, 3, 1)),
        Observation("p", "A", date(2024, 1, 1)),
        Observation("p", "A", date(2024, 2, 1)),
    ]
    ivs = collapse_observations(obs)
    assert len(ivs) == 2
    assert all(i.end is None or i.start <= i.end for i in ivs)


def test_collapse_idempotent():
    obs = [Observation("p", "A", date(2024, 1, 1)), Observation("p", "B", date(2024, 3, 1))]
    once = collapse_observations(obs)
    twice = collapse_observations(obs + obs)  # duplicates
    assert len(once) == len(twice) == 2


def test_collapse_repeat_stint():
    obs = [
        Observation("p", "A", date(2024, 1, 1)),
        Observation("p", "B", date(2024, 2, 1)),
        Observation("p", "A", date(2024, 3, 1)),
    ]
    ivs = collapse_observations(obs)
    assert len(ivs) == 3  # A, B, A again — repeat stints coexist
    assert [i.org_key for i in ivs] == ["A", "B", "A"]


def test_collapse_single_open():
    ivs = collapse_observations([Observation("p", "A", date(2024, 1, 1))])
    assert len(ivs) == 1
    assert ivs[0].end is None


def test_collapse_no_inverted_intervals():
    obs = [Observation("p", "A", date(2024, 1, 1)), Observation("p", "B", date(2024, 1, 2))]
    for i in collapse_observations(obs):
        assert i.end is None or i.start <= i.end


# --- MembershipWriter authoritative ---------------------------------------
def test_authoritative_idempotent_closed(session):
    p = _person(session)
    o = _org(session, "PSD")
    w = MembershipWriter(session)
    kw = dict(
        person_id=p.id,
        org_id=o.id,
        chamber="deputies",
        start=date(2024, 12, 21),
        end=date(2025, 6, 1),
    )
    m1 = w.record_authoritative(**kw)
    session.flush()
    m2 = w.record_authoritative(**kw)
    assert m1.id == m2.id  # no duplicate


def test_authoritative_returning_member_new_id(session):
    p = _person(session)
    o = _org(session, "PSD")
    w = MembershipWriter(session)
    m1 = w.record_authoritative(
        person_id=p.id,
        org_id=o.id,
        chamber="deputies",
        start=date(2024, 1, 1),
        end=date(2024, 6, 1),
    )
    session.flush()
    # Returns later → a NEW tenure, never reopen the closed one.
    m2 = w.record_authoritative(
        person_id=p.id, org_id=o.id, chamber="deputies", start=date(2025, 1, 1), end=None
    )
    session.flush()
    assert m2.id != m1.id
    assert m1.end_date == date(2024, 6, 1)  # immutable


def test_authoritative_closes_open_tenure(session):
    p = _person(session)
    o = _org(session, "PSD")
    w = MembershipWriter(session)
    m1 = w.record_authoritative(
        person_id=p.id, org_id=o.id, chamber="deputies", start=date(2024, 1, 1), end=None
    )
    session.flush()
    m2 = w.record_authoritative(
        person_id=p.id,
        org_id=o.id,
        chamber="deputies",
        start=date(2024, 1, 1),
        end=date(2024, 6, 1),
    )
    assert m1.id == m2.id
    assert m2.end_date == date(2024, 6, 1)


def test_authoritative_clamps_inverted(session):
    p = _person(session)
    o = _org(session, "PSD")
    w = MembershipWriter(session)
    m = w.record_authoritative(
        person_id=p.id,
        org_id=o.id,
        chamber="deputies",
        start=date(2024, 6, 1),
        end=date(2024, 1, 1),
    )
    assert m.end_date >= m.start_date


# --- MembershipWriter observation -----------------------------------------
def test_observation_closes_previous_group(session):
    p = _person(session)
    a = _org(session, "PSD")
    b = _org(session, "UPR")
    w = MembershipWriter(session)
    w.record_observation(
        person_id=p.id,
        org_id=a.id,
        chamber="deputies",
        observed_on=date(2024, 12, 21),
        org_class="group",
    )
    session.flush()
    w.record_observation(
        person_id=p.id,
        org_id=b.id,
        chamber="deputies",
        observed_on=date(2026, 6, 15),
        org_class="group",
    )
    session.flush()
    from sqlalchemy import select

    from pipeline.db import Membership

    ms = list(session.scalars(select(Membership).where(Membership.person_id == p.id)))
    assert len(ms) == 2
    psd = next(m for m in ms if m.org_id == a.id)
    upr = next(m for m in ms if m.org_id == b.id)
    assert psd.end_date == date(2026, 6, 14)
    assert upr.end_date is None
    assert upr.start_date == date(2026, 6, 15)


def test_observation_same_group_idempotent(session):
    p = _person(session)
    a = _org(session, "PSD")
    w = MembershipWriter(session)
    m1 = w.record_observation(
        person_id=p.id,
        org_id=a.id,
        chamber="deputies",
        observed_on=date(2024, 12, 21),
        org_class="group",
    )
    session.flush()
    m2 = w.record_observation(
        person_id=p.id,
        org_id=a.id,
        chamber="deputies",
        observed_on=date(2025, 1, 1),
        org_class="group",
    )
    assert m1.id == m2.id


def test_observation_closure_scoped_by_legislature(session):
    from sqlalchemy import select

    from pipeline.db import Membership

    p = _person(session)
    a, b = _org(session, "PSD"), _org(session, "UPR")
    w = MembershipWriter(session)
    w.record_observation(
        person_id=p.id,
        org_id=a.id,
        chamber="deputies",
        observed_on=date(2020, 6, 1),
        org_class="group",
        legislature="2020",
    )
    session.flush()
    w.record_observation(
        person_id=p.id,
        org_id=b.id,
        chamber="deputies",
        observed_on=date(2024, 12, 21),
        org_class="group",
        legislature="2024",
    )
    session.flush()
    ms = list(session.scalars(select(Membership).where(Membership.person_id == p.id)))
    assert len(ms) == 2
    psd = next(m for m in ms if m.org_id == a.id)
    upr = next(m for m in ms if m.org_id == b.id)
    # A 2024 snapshot says nothing about an open 2020 tenure: neither closes.
    assert psd.end_date is None
    assert psd.legislature == "2020"
    assert upr.end_date is None
    assert upr.legislature == "2024"


def test_observation_closure_marks_inferred_end(session):
    from sqlalchemy import select

    from pipeline.db import Membership

    p = _person(session)
    a, b = _org(session, "PSD"), _org(session, "UPR")
    w = MembershipWriter(session)
    w.record_observation(
        person_id=p.id,
        org_id=a.id,
        chamber="deputies",
        observed_on=date(2024, 1, 1),
        org_class="group",
        legislature="2024",
    )
    session.flush()
    w.record_observation(
        person_id=p.id,
        org_id=b.id,
        chamber="deputies",
        observed_on=date(2024, 6, 15),
        org_class="group",
        legislature="2024",
    )
    session.flush()
    psd = next(
        m
        for m in session.scalars(select(Membership).where(Membership.person_id == p.id))
        if m.org_id == a.id
    )
    assert psd.end_date == date(2024, 6, 14)
    assert psd.end_precision == "inferred"
    assert psd.end_reason == "UNKNOWN"  # not a fabricated CHANGED_PARTY
