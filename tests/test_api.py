"""Read API contract tests against an isolated, seeded SQLite database.

The suite never touches ``data/parlament.db``: every test builds a temp-file DB,
seeds deterministic facts, and overrides the ``get_db`` dependency. Background
polling stays off (no lifespan context), so nothing hits the network.
"""

from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.config import APP_VERSION
from backend.deps import get_db
from backend.main import create_app
from pipeline.db import (
    Coverage,
    Event,
    KeyEvent,
    Membership,
    Organization,
    Person,
    PipelineRun,
    get_session,
    make_engine,
    make_session_factory,
)


def _seed(session) -> SimpleNamespace:
    psd = Organization(classification="group", name="Grupul PSD", short_name="PSD",
                       normalized_name="grupul psd", chamber="deputies", color="#E63946")
    pnl = Organization(classification="group", name="Grupul PNL", short_name="PNL",
                       normalized_name="grupul pnl", chamber="deputies", color="#F4C430")
    psd_party = Organization(classification="party", name="Partidul Social Democrat",
                             short_name="PSD", normalized_name="partidul social democrat",
                             chamber="deputies")
    pnl_party = Organization(classification="party", name="Partidul Național Liberal",
                             short_name="PNL", normalized_name="partidul national liberal",
                             chamber="deputies")
    session.add_all([psd, pnl, psd_party, pnl_party])
    session.flush()

    p1 = Person(canonical_name="Ion Ștefan Popescu", normalized_name="ion stefan popescu",
                sort_key="popescu ion", birth_date=date(1980, 1, 2), wikidata_qid="Q100",
                match_status="auto")
    p2 = Person(canonical_name="Maria Ionescu", normalized_name="maria ionescu",
                sort_key="ionescu maria", match_status="unmatched")
    session.add_all([p1, p2])
    session.flush()

    session.add_all([
        Membership(person_id=p1.id, org_id=psd.id, on_behalf_of_id=psd_party.id,
                   chamber="deputies", legislature="2024", role="member",
                   start_date=date(2024, 1, 1), end_date=date(2024, 6, 1),
                   confidence="official_ledger", source_url="https://www.cdep.ro/m1"),
        Membership(person_id=p1.id, org_id=psd.id, on_behalf_of_id=psd_party.id,
                   chamber="deputies", legislature="2024", role="leader",
                   start_date=date(2024, 6, 1), end_date=date(2024, 12, 1),
                   confidence="official_ledger", source_url="https://www.cdep.ro/m2"),
        Membership(person_id=p1.id, org_id=pnl.id, on_behalf_of_id=pnl_party.id,
                   chamber="deputies", legislature="2024", role="member",
                   start_date=date(2024, 12, 1), confidence="official_ledger",
                   source_url="https://www.cdep.ro/m3"),
        Membership(person_id=p2.id, org_id=psd.id, on_behalf_of_id=psd_party.id,
                   chamber="deputies", legislature="2024", role="member",
                   start_date=date(2024, 12, 21), confidence="official_profile",
                   source_url="https://www.cdep.ro/m4"),
    ])
    session.add_all([
        Event(type="switch_group", person_id=p1.id, chamber="deputies",
              from_org_id=psd.id, to_org_id=pnl.id, event_date=date(2024, 12, 1),
              reason="CHANGED_PARTY", dedup_key="evt:switch:group:p1"),
        Event(type="switch_party", person_id=p2.id, chamber="deputies",
              from_org_id=psd_party.id, to_org_id=pnl_party.id,
              event_date=date(2025, 1, 10), dedup_key="evt:switch:party:p2"),
    ])
    session.add_all([
        KeyEvent(type="legislature", chamber="deputies", label="2024",
                 start_date=date(2024, 12, 21), end_date=None),
        KeyEvent(type="legislature", chamber="senate", label="2024",
                 start_date=date(2024, 12, 20), end_date=None),
    ])
    session.add_all([
        PipelineRun(source="cdep", status="SUCCESS",
                    started_at=datetime(2026, 11, 12, 8, 0),
                    finished_at=datetime(2026, 11, 12, 8, 1), rows=42),
        PipelineRun(source="senat", status="FAILURE",
                    started_at=datetime(2026, 11, 12, 8, 0),
                    finished_at=datetime(2026, 11, 12, 8, 0, 30),
                    rows=0, error="boom"),
    ])
    session.commit()
    return SimpleNamespace(
        p1=p1.id, p2=p2.id, psd=psd.id, pnl=pnl.id,
        psd_party=psd_party.id, pnl_party=pnl_party.id,
    )


@pytest.fixture()
def api(tmp_path, monkeypatch):
    monkeypatch.delenv("PARLAMENT_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("PARLAMENT_POLL_INTERVAL_MIN", raising=False)

    db_path = tmp_path / "api.db"
    seed_session = get_session(db_path)
    ids = _seed(seed_session)
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
    client = TestClient(app)  # plain client: lifespan (poller) never starts
    yield SimpleNamespace(client=client, db_path=db_path, ids=ids, factory=factory)
    client.close()


def test_meta(api):
    response = api.client.get("/api/meta")
    assert response.status_code == 200
    body = response.json()
    assert "2024" in body["legislatures"]
    assert {g["short_name"] for g in body["groups"]} == {"PSD", "PNL"}


def test_chamber_composition(api):
    response = api.client.get(
        "/api/chamber", params={"chamber": "deputies", "as_of": "2025-01-01"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["chamber"] == "deputies"
    assert body["total"] == 2
    counts = {g["short_name"]: g["count"] for g in body["groups"]}
    assert counts == {"PSD": 1, "PNL": 1}


def test_persons_search(api):
    response = api.client.get("/api/persons", params={"q": "popescu"})
    assert response.status_code == 200
    people = response.json()
    assert [p["id"] for p in people] == [api.ids.p1]
    assert people[0]["chambers"] == ["deputies"]


def test_person_detail(api):
    response = api.client.get(f"/api/persons/{api.ids.p1}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == api.ids.p1
    assert len(body["memberships"]) == 3
    assert len(body["events"]) == 1
    assert {m["chamber"] for m in body["memberships"]} == {"deputies"}


def test_person_history_derived_and_deduped(api):
    response = api.client.get(f"/api/persons/{api.ids.p1}/history")
    assert response.status_code == 200
    body = response.json()
    assert body["person_id"] == api.ids.p1
    history = body["history"]

    rows = {(h["field"], h["date"], h["event_type"]) for h in history}
    assert ("group", "2024-12-01", "switch_group") in rows
    assert ("party", "2024-12-01", "switch_party") in rows
    assert ("role", "2024-06-01", "role_change") in rows
    # Newest first.
    assert history[0]["date"] == "2024-12-01"
    assert [h["date"] for h in history] == sorted(
        (h["date"] for h in history), reverse=True
    )
    # The explicit Event is covered by the derived row -> not duplicated.
    group_rows = [h for h in history if h["field"] == "group"]
    assert len(group_rows) == 1
    assert group_rows[0]["from"] == "PSD"
    assert group_rows[0]["to"] == "PNL"
    assert group_rows[0]["source_url"] == "https://www.cdep.ro/m3"


def test_person_history_includes_explicit_events(api):
    response = api.client.get(f"/api/persons/{api.ids.p2}/history")
    assert response.status_code == 200
    history = response.json()["history"]
    assert len(history) == 1
    row = history[0]
    assert row["field"] == "party"
    assert row["from"] == "PSD"
    assert row["to"] == "PNL"
    assert row["date"] == "2025-01-10"
    assert row["event_type"] == "switch_party"
    assert row["source_url"] is None


def test_person_history_missing_person(api):
    response = api.client.get("/api/persons/does-not-exist/history")
    assert response.status_code == 404


def test_movements(api):
    response = api.client.get("/api/movements")
    assert response.status_code == 200
    movements = response.json()
    assert len(movements) == 2
    assert movements[0]["type"] == "switch_party"  # newest first
    assert {m["type"] for m in movements} == {"switch_group", "switch_party"}


def test_recent_events(api):
    response = api.client.get("/api/events/recent")
    assert response.status_code == 200
    events = response.json()
    assert len(events) == 2
    assert events[0]["event_date"] == "2025-01-10"


def test_coverage_derived(api):
    response = api.client.get("/api/coverage")
    assert response.status_code == 200
    rows = {row["chamber"]: row for row in response.json()}
    assert set(rows) == {"deputies", "senate"}
    assert rows["deputies"]["legislature"] == "2024"
    assert rows["deputies"]["persons"] == 2
    assert rows["deputies"]["completeness"] == "partial"
    assert "2 of ~330" in rows["deputies"]["note"]
    assert rows["senate"]["persons"] == 0
    assert rows["senate"]["completeness"] == "none"


def test_coverage_persisted_rows_enriched(api):
    session = api.factory()
    session.add(Coverage(chamber="deputies", legislature="2024",
                         completeness="partial", note="Persisted row"))
    session.commit()
    session.close()

    response = api.client.get("/api/coverage")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["note"] == "Persisted row"
    assert rows[0]["completeness"] == "partial"
    assert rows[0]["persons"] == 2


def test_health(api):
    response = api.client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["sources"]["cdep"]["status"] == "SUCCESS"
    assert body["sources"]["cdep"]["rows"] == 42
    assert body["sources"]["senat"]["status"] == "FAILURE"
    assert body["sources"]["senat"]["error"] == "boom"
    assert "checked_at" in body["sources"]


def test_about(api):
    response = api.client.get("/api/about")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Parlament Deschis"
    assert body["version"] == APP_VERSION
    assert body["project_url"] == "https://github.com/parlament-deschis"
    assert 3 <= len(body["methodology"]["ro"]) <= 5
    assert 3 <= len(body["methodology"]["en"]) <= 5
    assert body["licenses"] == {
        "code": "AGPL-3.0-or-later",
        "data": "CC-BY-4.0",
        "code_url": "https://www.gnu.org/licenses/agpl-3.0.html",
        "data_url": "https://creativecommons.org/licenses/by/4.0/",
    }
    source_names = {src["name"] for src in body["sources"]}
    assert {"Camera Deputaților", "Senatul României", "Wikidata"} <= source_names
    assert len(body["coverage"]) == 2
    assert body["freshness"]["cdep"]["status"] == "SUCCESS"
    assert datetime.fromisoformat(body["generated_at"]).tzinfo is not None


def test_admin_poll_disabled_when_token_unset(api):
    response = api.client.post("/api/admin/poll")
    assert response.status_code == 503
    assert response.json()["detail"] == (
        "admin polling disabled (set PARLAMENT_ADMIN_TOKEN)"
    )


def test_admin_poll_rejects_wrong_token(api, monkeypatch):
    monkeypatch.setenv("PARLAMENT_ADMIN_TOKEN", "s3cret")
    response = api.client.post(
        "/api/admin/poll", headers={"X-Admin-Token": "wrong-token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid admin token"

    missing = api.client.post("/api/admin/poll")
    assert missing.status_code == 401
