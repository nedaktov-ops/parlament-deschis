from datetime import date

import pytest
from sqlalchemy import select

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
from pipeline.traseism import (
    party_summary,
    party_switches,
    traseism_overview,
    traseism_summary,
    traseism_switches,
)


@pytest.fixture
def session(tmp_path):
    engine = make_engine(tmp_path / "traseism.db")
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


def _organization(session, short_name, classification="group"):
    organization = Organization(
        classification=classification,
        name=f"{short_name} ({classification})",
        normalized_name=f"{short_name.lower()} {classification}",
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
    party=None,
    source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.gp",
):
    membership = Membership(
        person_id=person.id,
        org_id=organization.id,
        on_behalf_of_id=party.id if party else None,
        chamber="deputies",
        legislature="2024",
        start_date=start,
        end_date=end,
        source_url=source_url,
        confidence="official_ledger",
    )
    session.add(membership)
    session.flush()
    return membership


def _switch_event(
    session,
    person,
    from_org,
    to_org,
    event_date,
    *,
    source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.gp",
):
    event = Event(
        type="switch_group",
        person_id=person.id,
        chamber="deputies",
        legislature="2024",
        from_org_id=from_org.id,
        to_org_id=to_org.id,
        event_date=event_date,
        precision="day",
        source_url=source_url,
        reason="CHANGED_GROUP",
    )
    session.add(event)
    session.flush()
    return event


def _seed_switch_data(session):
    session.add(
        KeyEvent(
            type="legislature",
            chamber="deputies",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            label="2024",
        )
    )

    psd = _organization(session, "PSD")
    unaffiliated = _organization(session, "NEAFILIATI")
    pro = _organization(session, "PRO")
    psd_party = _organization(session, "PSD", "party")
    pro_party = _organization(session, "PRO", "party")

    alice = _person(session, "Alice Ionescu")
    bob = _person(session, "Bob Popescu")
    carol = _person(session, "Carol Dumitru")

    _membership(
        session,
        alice,
        psd,
        start=date(2024, 1, 1),
        end=date(2024, 6, 1),
        party=psd_party,
    )
    _membership(
        session,
        alice,
        unaffiliated,
        start=date(2024, 6, 1),
        end=date(2024, 8, 1),
    )
    _membership(
        session,
        alice,
        pro,
        start=date(2024, 8, 1),
        party=pro_party,
    )
    _switch_event(session, alice, psd, unaffiliated, date(2024, 6, 1))
    _switch_event(session, alice, unaffiliated, pro, date(2024, 8, 1))

    _membership(
        session,
        bob,
        psd,
        start=date(2024, 1, 1),
        end=date(2024, 5, 1),
        party=psd_party,
    )
    _membership(
        session,
        bob,
        pro,
        start=date(2024, 5, 1),
        party=pro_party,
    )
    _switch_event(session, bob, psd, pro, date(2024, 5, 1))

    _membership(
        session,
        bob,
        psd,
        start=date(2024, 9, 1),
        party=psd_party,
    )
    _switch_event(session, bob, pro, psd, date(2024, 9, 1))

    # Carol has two rows but only one distinct person in the denominator.
    _membership(
        session,
        carol,
        psd,
        start=date(2024, 1, 1),
        end=date(2024, 5, 1),
        party=psd_party,
    )
    _membership(
        session,
        carol,
        pro,
        start=date(2024, 5, 1),
        party=pro_party,
    )
    _switch_event(
        session,
        carol,
        psd,
        pro,
        date(2024, 5, 1),
        source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.gp?idg=8",
    )
    session.commit()


def test_summary_counts_switches_and_distinct_person_denominator(session):
    _seed_switch_data(session)

    summary = traseism_summary(session, chamber="deputies", legislature="2024")

    assert summary["members"] == 3
    assert summary["switches"] == 5
    assert summary["switchers"] == 3
    assert summary["switch_rate"] == pytest.approx(1.0)
    assert summary["switches_per_100_members"] == pytest.approx(500 / 3)
    assert summary["repeat_switchers"] == {"people": 2, "max_switches": 2}
    assert {(row["from"], row["to"]): row["count"] for row in summary["matrix"]} == {
        ("PSD", "PRO"): 2,
        ("PSD", "NEAFILIATI"): 1,
        ("NEAFILIATI", "PRO"): 1,
        ("PRO", "PSD"): 1,
    }


def test_party_view_collapses_unaffiliated_passage_to_one_switch(session):
    _seed_switch_data(session)

    switches = party_switches(session, chamber="deputies", legislature="2024")
    alice = session.scalars(select(Person).where(Person.canonical_name == "Alice Ionescu")).one()

    alice_switches = [row for row in switches if row["person_id"] == alice.id]
    assert len(alice_switches) == 1
    assert alice_switches[0]["from_party"] == "PSD"
    assert alice_switches[0]["to_party"] == "PRO"
    assert alice_switches[0]["date"] == date(2024, 8, 1)
    assert alice_switches[0]["from_source_url"].endswith("structura2015.gp")
    assert alice_switches[0]["source_url"].endswith("structura2015.gp")

    summary = party_summary(session, chamber="deputies", legislature="2024")
    assert summary["switches"] == 4
    assert summary["switchers"] == 3
    assert {(row["from"], row["to"]): row["count"] for row in summary["matrix"]} == {
        ("PSD", "PRO"): 3,
        ("PRO", "PSD"): 1,
    }


def test_switch_ledger_keeps_event_source_url(session):
    _seed_switch_data(session)

    ledger = traseism_switches(session, chamber="deputies", legislature="2024")

    assert ledger["total"] == 5
    assert len(ledger["rows"]) == 5
    carol_rows = [row for row in ledger["rows"] if row["name"] == "Carol Dumitru"]
    assert len(carol_rows) == 1
    assert carol_rows[0]["source_url"].endswith("structura2015.gp?idg=8")
    assert carol_rows[0]["from_group"] == "PSD"
    assert carol_rows[0]["to_group"] == "PRO"


def test_overview_contains_scope_and_party_counts(session):
    _seed_switch_data(session)

    rows = traseism_overview(session)

    assert len(rows) == 1
    assert rows[0]["chamber"] == "deputies"
    assert rows[0]["legislature"] == "2024"
    assert rows[0]["members"] == 3
    assert rows[0]["switches"] == 5
    assert rows[0]["party_switches"] == 4
