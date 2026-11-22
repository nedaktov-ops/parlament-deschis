"""P3-C: the transparency report is a truthful whole-corpus snapshot.

The report used to accept ``chamber`` / ``legislature`` scope, echo it in the
payload, and then return whole-corpus figures for every block. These tests pin
the honest contract: the report declares ``scope: "all"``, its totals equal the
full corpus (including rows from every chamber/legislature), and no scoped
query parameters are advertised for this endpoint.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from backend.deps import get_db
from backend.main import create_app
from pipeline.db import (
    Event,
    Membership,
    Organization,
    Person,
    get_session,
    make_engine,
    make_session_factory,
)

EXPECTED_TOTALS = {
    "persons": 2,
    "memberships": 2,
    "events": 2,
    "switches": 1,
    # R-04: labelled switch definitions (additive). The fixture has one
    # switch_group event and no switch_party events.
    "switches_group": 1,
    "switches_party": 0,
    "switches_all": 1,
    "committees": 1,
    "persons_with_birth_date": 2,
}


def _seed(session) -> None:
    """Two people in different chambers/legislatures, plus one committee."""
    deputy = Person(
        canonical_name="Ana Deputat",
        normalized_name="ana deputat",
        sort_key="deputat ana",
        birth_date=date(1980, 1, 2),
    )
    senator = Person(
        canonical_name="Bogdan Senator",
        normalized_name="bogdan senator",
        sort_key="senator bogdan",
        birth_date=date(1970, 5, 6),
    )
    session.add_all([deputy, senator])
    session.flush()

    group_deputies = Organization(
        classification="group",
        name="Grup Deputați",
        short_name="GD",
        normalized_name="grup deputati",
        chamber="deputies",
        color="#E63946",
    )
    group_senate = Organization(
        classification="group",
        name="Grup Senat",
        short_name="GS",
        normalized_name="grup senat",
        chamber="senate",
        color="#1D3557",
    )
    party = Organization(
        classification="party",
        name="PSD",
        short_name="PSD",
        normalized_name="psd",
        chamber="deputies",
    )
    committee = Organization(
        classification="committee",
        name="Comisie",
        short_name="C",
        normalized_name="comisie",
        chamber="deputies",
    )
    session.add_all([group_deputies, group_senate, party, committee])
    session.flush()

    session.add_all(
        [
            Membership(
                person_id=deputy.id,
                org_id=group_deputies.id,
                on_behalf_of_id=party.id,
                chamber="deputies",
                legislature="2024",
                role="member",
                start_date=date(2024, 12, 21),
                confidence="official_ledger",
                source_url="https://example.org/a",
            ),
            Membership(
                person_id=senator.id,
                org_id=group_senate.id,
                chamber="senate",
                legislature="2020",
                role="member",
                start_date=date(2020, 12, 21),
                confidence="official_ledger",
                source_url="https://example.org/b",
            ),
        ]
    )
    session.add_all(
        [
            Event(
                type="switch_group",
                person_id=deputy.id,
                chamber="deputies",
                legislature="2024",
                from_org_id=party.id,
                to_org_id=group_deputies.id,
                event_date=date(2025, 1, 1),
                dedup_key="switch:report-deputy",
                source_url="https://example.org/ea",
            ),
            Event(
                type="membership",
                person_id=senator.id,
                chamber="senate",
                legislature="2020",
                event_date=date(2021, 1, 1),
                dedup_key="other:report-senator",
            ),
        ]
    )
    session.commit()


@pytest.fixture()
def api(tmp_path, monkeypatch):
    monkeypatch.delenv("PARLAMENT_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("PARLAMENT_POLL_INTERVAL_MIN", raising=False)

    db_path = tmp_path / "report.db"
    seed_session = get_session(db_path)
    _seed(seed_session)
    seed_session.close()

    factory = make_session_factory(make_engine(db_path))

    def override():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_db] = override
    client = TestClient(app)
    yield SimpleNamespace(client=client, factory=factory, app=app)
    client.close()


def _unfiltered_totals(factory) -> dict:
    """Recompute the report totals directly from the DB, with no filters."""
    session = factory()
    try:
        switch_group = (
            session.scalar(select(func.count(Event.id)).where(Event.type == "switch_group")) or 0
        )
        switch_party = (
            session.scalar(select(func.count(Event.id)).where(Event.type == "switch_party")) or 0
        )
        return {
            "persons": session.scalar(select(func.count(Person.id))) or 0,
            "memberships": session.scalar(select(func.count(Membership.id))) or 0,
            "events": session.scalar(select(func.count(Event.id))) or 0,
            "switches": switch_group,
            # R-04: labelled switch definitions (additive).
            "switches_group": switch_group,
            "switches_party": switch_party,
            "switches_all": switch_group + switch_party,
            "committees": session.scalar(
                select(func.count(Organization.id)).where(
                    Organization.classification == "committee"
                )
            )
            or 0,
            "persons_with_birth_date": session.scalar(
                select(func.count(Person.id)).where(Person.birth_date.is_not(None))
            )
            or 0,
        }
    finally:
        session.close()


def test_report_declares_whole_corpus_scope(api):
    response = api.client.get("/api/export/report")
    assert response.status_code == 200
    assert response.json()["scope"] == "all"


def test_report_totals_equal_full_corpus(api):
    body = api.client.get("/api/export/report").json()
    assert body["totals"] == EXPECTED_TOTALS
    assert body["totals"] == _unfiltered_totals(api.factory)


def test_scoped_params_are_ignored_not_honored(api):
    """Legacy ?chamber=&legislature= URLs still work but cannot lie about scope."""
    plain = api.client.get("/api/export/report").json()
    scoped = api.client.get(
        "/api/export/report", params={"chamber": "senate", "legislature": "1990"}
    )
    assert scoped.status_code == 200
    body = scoped.json()
    assert body["scope"] == "all"
    assert body["totals"] == plain["totals"] == EXPECTED_TOTALS


def test_report_advertises_no_scope_parameters(api):
    schema = api.app.openapi()
    params = schema["paths"]["/api/export/report"]["get"].get("parameters", [])
    names = {p["name"] for p in params}
    assert "chamber" not in names
    assert "legislature" not in names


def test_other_exports_keep_their_scope_parameters(api):
    """Removing scope from /report must not break the shared scope helper."""
    schema = api.app.openapi()
    for path in ("/api/export/popolo", "/api/export/{dataset}.csv"):
        names = {p["name"] for p in schema["paths"][path]["get"].get("parameters", [])}
        assert {"chamber", "legislature"} <= names
