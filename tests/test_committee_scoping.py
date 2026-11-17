"""Committee rows must never contaminate group/party reads.

Committees are stored as ``Organization(classification="committee")`` rows and
membership of a committee is a ``Membership`` row to that organisation
(OpenStates OSEP #4 / Popolo). Every read that means "party/group membership"
therefore filters ``Organization.classification == "group"`` through the single
predicate ``pipeline.queries.is_group``.

This test proves the invariant the hard way: it snapshots every group-facing
output, inserts committee organisations + memberships that would change those
outputs if the filter were missing, and asserts the snapshots are identical.
The committee rows are deliberately adversarial:

* Alice's committee tenure spans the **gap** between her two group tenures, so
  an unfiltered ``check_mandate_coverage`` would stop reporting the gap.
* Alice's committee tenure **overlaps** both group tenures, so an unfiltered
  ``check_overlaps`` would report a contradiction.
* Bob has **only** a committee membership, so an unfiltered coverage or
  ``scope_totals`` count would invent a member who holds no group seat.
"""

from __future__ import annotations

from datetime import date

import pytest
from sqlalchemy import func, select

from backend.queries import (
    get_coverage_detailed,
    get_person,
    get_person_history,
    search_persons,
)
from pipeline.audit import (
    check_mandate_coverage,
    check_overlaps,
    check_scope_totals,
    scope_totals,
)
from pipeline.db import (
    KeyEvent,
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
    engine = make_engine(tmp_path / "committee_scoping.db")
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


def _organization(session, short_name: str, classification: str = "group") -> Organization:
    org = Organization(
        classification=classification,
        name=short_name,
        normalized_name=f"{classification} {short_name}".lower(),
        short_name=short_name,
        chamber="deputies",
        legislature="2024",
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
    role: str | None = None,
    chamber: str = "deputies",
    legislature: str = "2024",
) -> Membership:
    membership = Membership(
        person_id=person.id,
        org_id=org.id,
        chamber=chamber,
        legislature=legislature,
        role=role,
        start_date=start,
        end_date=end,
        source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.gp",
        confidence="official_ledger",
    )
    session.add(membership)
    session.flush()
    return membership


def _seed_group_corpus(session):
    """Alice holds two group tenures with a deliberate gap; Bob holds none."""
    session.add(
        KeyEvent(
            type="legislature",
            chamber="deputies",
            label="2024",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
    )
    psd = _organization(session, "PSD")
    pnl = _organization(session, "PNL")
    alice = _person(session, "Alice Ionescu")
    bob = _person(session, "Bob Popescu")

    session.add(
        Mandate(
            person_id=alice.id,
            chamber="deputies",
            legislature="2024",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.mp?idm=1",
            confidence="official_profile",
        )
    )
    # Group A ends 2024-03-01, group B starts 2024-07-01: a 122-day gap.
    _membership(session, alice, psd, start=date(2024, 1, 1), end=date(2024, 3, 1))
    _membership(session, alice, pnl, start=date(2024, 7, 1), end=date(2024, 12, 31))
    session.commit()
    return alice, bob, psd, pnl


def _snapshot(session, alice: Person, bob: Person) -> dict:
    """Every output that means "party/group membership"."""
    return {
        "scope_totals": scope_totals(session),
        "audit_scope_totals": [f.as_dict() for f in check_scope_totals(session)],
        "mandate_coverage": [f.as_dict() for f in check_mandate_coverage(session)],
        "overlaps": [f.as_dict() for f in check_overlaps(session)],
        "coverage_detailed": get_coverage_detailed(session),
        "alice_memberships": get_person(session, alice.id)["memberships"],
        "alice_history": get_person_history(session, alice.id),
        "bob_memberships": get_person(session, bob.id)["memberships"],
        "search": search_persons(session, None, None),
    }


def test_committee_rows_do_not_change_group_outputs(session):
    alice, bob, _psd, _pnl = _seed_group_corpus(session)
    before = _snapshot(session, alice, bob)

    # The fixture must be meaningful: one uncovered gap is reported.
    assert [f["check"] for f in before["mandate_coverage"]] == ["mandate_coverage"]
    assert "gap in group membership" in before["mandate_coverage"][0]["detail"]
    assert "days" in before["mandate_coverage"][0]["context"]
    assert before["overlaps"] == []

    # Adversarial committee data: Alice's tenure spans the gap and overlaps
    # both group tenures; Bob holds a committee seat and no group seat.
    committee = _organization(session, "Comisia buget", classification="committee")
    other_committee = _organization(session, "Comisia juridică", classification="committee")
    _membership(
        session,
        alice,
        committee,
        start=date(2024, 2, 1),
        end=date(2024, 9, 1),
        role="member",
    )
    _membership(
        session,
        bob,
        other_committee,
        start=date(2024, 1, 1),
        end=date(2024, 12, 31),
        role="secretary",
    )
    session.commit()

    # The rows exist — the assertion below must fail for a real reason.
    assert session.scalar(select(func.count()).select_from(Membership)) == 4
    committee_rows = session.scalar(
        select(func.count())
        .select_from(Membership)
        .join(Organization, Organization.id == Membership.org_id)
        .where(Organization.classification == "committee")
    )
    assert committee_rows == 2

    after = _snapshot(session, alice, bob)

    assert after == before


def test_committee_membership_is_not_a_group_tenure(session):
    alice, bob, _psd, _pnl = _seed_group_corpus(session)
    committee = _organization(session, "Comisia buget", classification="committee")
    _membership(
        session,
        alice,
        committee,
        start=date(2024, 2, 1),
        end=date(2024, 9, 1),
        role="member",
    )
    _membership(
        session,
        bob,
        committee,
        start=date(2024, 1, 1),
        end=date(2024, 12, 31),
        role="secretary",
    )
    session.commit()

    totals = scope_totals(session)
    assert totals == [
        {
            "chamber": "deputies",
            "legislature": "2024",
            "members": 1,  # Alice; Bob holds only a committee seat
            "memberships": 2,  # the two group tenures, not the two committee ones
            "switches": 0,
        }
    ]

    coverage = get_coverage_detailed(session)
    assert [row["total_memberships"] for row in coverage] == [2]
    assert [row["persons"] for row in coverage] == [1]

    alice_memberships = get_person(session, alice.id)["memberships"]
    assert [m["org"]["classification"] for m in alice_memberships] == ["group", "group"]
    assert get_person(session, bob.id)["memberships"] == []

    history = get_person_history(session, alice.id)["history"]
    assert all(row["field"] in {"group", "party", "role"} for row in history)
    assert all("Comisia" not in (row.get("org") or "") for row in history)
