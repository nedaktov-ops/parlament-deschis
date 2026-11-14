"""check_overlaps must not flag open-ended memberships as overlapping.

An open-ended tenure (no published leave date) is an inference artifact: the
chamber published the member in the group without dates. It cannot be treated
as covering forever, because the member demonstrably sat elsewhere afterwards.
It is capped at the day before the next tenure starts.
"""

from __future__ import annotations

from datetime import date

import pytest

from pipeline.audit import check_overlaps
from pipeline.db import (
    Membership,
    Organization,
    Person,
    init_db,
    make_engine,
    make_session_factory,
)


@pytest.fixture
def session(tmp_path):
    engine = make_engine(tmp_path / "audit_overlap.db")
    init_db(engine)
    session = make_session_factory(engine)()
    try:
        yield session
    finally:
        session.close()


def _person(session, name: str) -> Person:
    person = Person(
        canonical_name=name,
        normalized_name=name.lower(),
        sort_key=name.lower(),
    )
    session.add(person)
    session.flush()
    return person


def _org(session, short_name: str) -> Organization:
    org = Organization(
        classification="group",
        name=short_name,
        normalized_name=short_name.lower(),
        short_name=short_name,
    )
    session.add(org)
    session.flush()
    return org


def _membership(
    session,
    person: Person,
    org: Organization,
    *,
    start: date,
    end: date | None,
    chamber: str = "deputies",
    legislature: str = "2020",
    source_url: str = "https://www.cdep.ro/ords/pls/parlam/structura2015.gp",
) -> Membership:
    m = Membership(
        person_id=person.id,
        org_id=org.id,
        chamber=chamber,
        legislature=legislature,
        start_date=start,
        end_date=end,
        source_url=source_url,
        confidence="official_ledger",
    )
    session.add(m)
    session.flush()
    return m


def test_open_ended_tenure_is_capped_not_flagged(session):
    """Group A (open-ended) followed by Group B (open-ended) → no overlap."""
    alice = _person(session, "Alice Pop")
    psd = _org(session, "PSD")
    pnl = _org(session, "PNL")

    _membership(session, alice, psd, start=date(2020, 1, 1), end=None)
    _membership(session, alice, pnl, start=date(2020, 6, 1), end=None)
    session.commit()

    findings = check_overlaps(session)
    assert findings == []


def test_closed_tenure_overlapping_next_is_flagged(session):
    """Group A ends 2020-07-01 while Group B starts 2020-06-01 → overlap."""
    alice = _person(session, "Alice Pop")
    psd = _org(session, "PSD")
    pnl = _org(session, "PNL")

    _membership(session, alice, psd, start=date(2020, 1, 1), end=date(2020, 7, 1))
    _membership(session, alice, pnl, start=date(2020, 6, 1), end=None)
    session.commit()

    findings = check_overlaps(session)
    assert len(findings) == 1
    assert findings[0].check == "overlap"
    assert findings[0].person_id == alice.id
    assert "PSD" in findings[0].detail
    assert "PNL" in findings[0].detail
    assert findings[0].context["overlap_days"] > 1
