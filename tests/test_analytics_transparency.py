"""P4-A: the audit's key transparency endpoints are covered and return 200.

``/api/analytics/switch-leaderboard`` is exercised in depth in
``tests/test_api.py``; this module adds the two previously untested key
endpoints (``committee-control``, ``party-timeline``) and asserts the full
three-endpoint set returns 200 against a seeded, isolated DB. No network and
no ``data/*.db`` access — every test builds a temp DB and overrides ``get_db``.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

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

KEY_ENDPOINTS = (
    "/api/analytics/switch-leaderboard",
    "/api/analytics/committee-control",
    "/api/analytics/party-timeline",
)


def _seed(session) -> None:
    person = Person(
        canonical_name="Ana Deputat",
        normalized_name="ana deputat",
        sort_key="deputat ana",
        birth_date=date(1980, 1, 2),
    )
    party = Organization(
        classification="party",
        name="Partidul Democrat",
        short_name="PD",
        normalized_name="partidul democrat",
        chamber="deputies",
    )
    group = Organization(
        classification="group",
        name="Grupul PD",
        short_name="PD",
        normalized_name="grupul pd",
        chamber="deputies",
    )
    committee = Organization(
        classification="committee",
        name="Comisia de Finanțe",
        short_name="CF",
        normalized_name="comisia de finante",
        chamber="deputies",
        legislature="2024",
    )
    session.add_all([person, party, group, committee])
    session.flush()

    session.add_all(
        [
            # Dated party affiliation -> a row for party-timeline.
            Membership(
                person_id=person.id,
                org_id=group.id,
                on_behalf_of_id=party.id,
                chamber="deputies",
                legislature="2024",
                role="member",
                start_date=date(2024, 1, 1),
            ),
            # Active committee chair -> a row for committee-control.
            Membership(
                person_id=person.id,
                org_id=committee.id,
                chamber="deputies",
                legislature="2024",
                role="presedinte",
                group_acronym_at_event="PD",
                start_date=date(2024, 2, 1),
            ),
        ]
    )
    session.add(
        Event(
            type="switch_group",
            person_id=person.id,
            chamber="deputies",
            legislature="2024",
            event_date=date(2024, 3, 1),
            dedup_key="p4a:transparency:switch",
        )
    )
    session.commit()


@pytest.fixture()
def api(tmp_path, monkeypatch):
    monkeypatch.delenv("PARLAMENT_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("PARLAMENT_POLL_INTERVAL_MIN", raising=False)

    db_path = tmp_path / "transparency.db"
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
    yield SimpleNamespace(client=client, app=app)
    client.close()


@pytest.mark.parametrize("endpoint", KEY_ENDPOINTS)
def test_key_transparency_endpoint_returns_200(api, endpoint):
    response = api.client.get(endpoint)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_committee_control_reports_the_seeded_chair(api):
    body = api.client.get("/api/analytics/committee-control").json()
    assert body["data"]["total_committees"] == 1
    assert body["data"]["parties"][0]["party"] == "PD"


def test_party_timeline_reports_the_seeded_party(api):
    body = api.client.get("/api/analytics/party-timeline").json()
    assert any(row["party"] == "PD" for row in body["data"])
