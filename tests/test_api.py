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
    Mandate,
    Membership,
    Organization,
    Person,
    PipelineRun,
    SwitchWave,
    get_session,
    make_engine,
    make_session_factory,
)


def _seed(session) -> SimpleNamespace:
    psd = Organization(
        classification="group",
        name="Grupul PSD",
        short_name="PSD",
        normalized_name="grupul psd",
        chamber="deputies",
        color="#E63946",
    )
    pnl = Organization(
        classification="group",
        name="Grupul PNL",
        short_name="PNL",
        normalized_name="grupul pnl",
        chamber="deputies",
        color="#F4C430",
    )
    psd_party = Organization(
        classification="party",
        name="Partidul Social Democrat",
        short_name="PSD",
        normalized_name="partidul social democrat",
        chamber="deputies",
    )
    pnl_party = Organization(
        classification="party",
        name="Partidul Național Liberal",
        short_name="PNL",
        normalized_name="partidul national liberal",
        chamber="deputies",
    )
    session.add_all([psd, pnl, psd_party, pnl_party])
    session.flush()

    p1 = Person(
        canonical_name="Ion Ștefan Popescu",
        normalized_name="ion stefan popescu",
        sort_key="popescu ion",
        birth_date=date(1980, 1, 2),
        wikidata_qid="Q100",
        match_status="auto",
    )
    p2 = Person(
        canonical_name="Maria Ionescu",
        normalized_name="maria ionescu",
        sort_key="ionescu maria",
        match_status="unmatched",
    )
    session.add_all([p1, p2])
    session.flush()

    session.add_all(
        [
            Membership(
                person_id=p1.id,
                org_id=psd.id,
                on_behalf_of_id=psd_party.id,
                chamber="deputies",
                legislature="2024",
                role="member",
                start_date=date(2024, 1, 1),
                end_date=date(2024, 6, 1),
                confidence="official_ledger",
                source_url="https://www.cdep.ro/m1",
            ),
            Membership(
                person_id=p1.id,
                org_id=psd.id,
                on_behalf_of_id=psd_party.id,
                chamber="deputies",
                legislature="2024",
                role="leader",
                start_date=date(2024, 6, 1),
                end_date=date(2024, 12, 1),
                confidence="official_ledger",
                source_url="https://www.cdep.ro/m2",
            ),
            Membership(
                person_id=p1.id,
                org_id=pnl.id,
                on_behalf_of_id=pnl_party.id,
                chamber="deputies",
                legislature="2024",
                role="member",
                start_date=date(2024, 12, 1),
                confidence="official_ledger",
                source_url="https://www.cdep.ro/m3",
            ),
            Membership(
                person_id=p2.id,
                org_id=psd.id,
                on_behalf_of_id=psd_party.id,
                chamber="deputies",
                legislature="2024",
                role="member",
                start_date=date(2024, 12, 21),
                confidence="official_profile",
                source_url="https://www.cdep.ro/m4",
            ),
        ]
    )
    session.add_all(
        [
            Event(
                type="switch_group",
                person_id=p1.id,
                chamber="deputies",
                from_org_id=psd.id,
                to_org_id=pnl.id,
                event_date=date(2024, 12, 1),
                reason="CHANGED_PARTY",
                dedup_key="evt:switch:group:p1",
            ),
            Event(
                type="switch_party",
                person_id=p2.id,
                chamber="deputies",
                from_org_id=psd_party.id,
                to_org_id=pnl_party.id,
                event_date=date(2025, 1, 10),
                dedup_key="evt:switch:party:p2",
            ),
        ]
    )
    session.add_all(
        [
            KeyEvent(
                type="legislature",
                chamber="deputies",
                label="2024",
                start_date=date(2024, 12, 21),
                end_date=None,
            ),
            KeyEvent(
                type="legislature",
                chamber="senate",
                label="2024",
                start_date=date(2024, 12, 20),
                end_date=None,
            ),
        ]
    )
    session.add_all(
        [
            PipelineRun(
                source="cdep",
                status="SUCCESS",
                started_at=datetime(2026, 11, 12, 8, 0),
                finished_at=datetime(2026, 11, 12, 8, 1),
                rows=42,
            ),
            PipelineRun(
                source="senat",
                status="FAILURE",
                started_at=datetime(2026, 11, 12, 8, 0),
                finished_at=datetime(2026, 11, 12, 8, 0, 30),
                rows=0,
                error="boom",
            ),
        ]
    )
    session.commit()
    return SimpleNamespace(
        p1=p1.id,
        p2=p2.id,
        psd=psd.id,
        pnl=pnl.id,
        psd_party=psd_party.id,
        pnl_party=pnl_party.id,
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
    response = api.client.get("/api/chamber", params={"chamber": "deputies", "as_of": "2025-01-01"})
    assert response.status_code == 200
    body = response.json()
    assert body["chamber"] == "deputies"
    assert body["total"] == 2
    counts = {g["short_name"]: g["count"] for g in body["groups"]}
    assert counts == {"PSD": 1, "PNL": 1}


def test_timeline_preserves_temporal_membership_scope(api):
    response = api.client.get(
        "/api/timeline",
        params={
            "chamber": "deputies",
            "from": "2024-12-21",
            "to": "2025-01-10",
            "step_days": 20,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["dates"] == ["2024-12-21", "2025-01-10"]
    assert body["totals"] == [2, 2]
    assert body["groups"] == {"PNL": [1, 1], "PSD": [1, 1]}
    assert body["switches"] == []


def test_timeline_include_switches(api):
    response = api.client.get(
        "/api/timeline",
        params={
            "chamber": "deputies",
            "from": "2024-12-21",
            "to": "2025-01-10",
            "step_days": 20,
            "include_switches": "true",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "switches" in body
    assert isinstance(body["switches"], list)


def test_cache_control_isolates_health_and_writes(api):
    """Mutable API reads, health, writes and errors must never be cached.

    P0-B: the old contract allowed a 24h CDN cache on all /api GETs, which
    made the 60s switch-alert poll and the freshness indicator stale. Reads
    are now no-store at the origin (and the Vercel CDN rule matches).
    """
    read = api.client.get("/api/chamber", params={"chamber": "deputies", "as_of": "2025-01-01"})
    assert "no-store" in read.headers.get("cache-control", "")

    live = api.client.get("/api/health/live")
    assert "no-store" in live.headers.get("cache-control", "")

    missing = api.client.get("/api/not-a-route")
    assert missing.status_code == 404
    assert "no-store" in missing.headers.get("cache-control", "")

    write = api.client.post("/api/admin/poll")
    assert "no-store" in write.headers.get("cache-control", "")


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
    assert [h["date"] for h in history] == sorted((h["date"] for h in history), reverse=True)
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


def test_coverage_detailed_derives_metrics_without_persisted_rows(api):
    session = api.factory()
    session.add(
        Event(
            type="switch_group",
            person_id=api.ids.p1,
            chamber="deputies",
            legislature="2024",
            event_date=date(2025, 1, 1),
            dedup_key="coverage-detail:switch",
        )
    )
    session.commit()
    session.close()

    response = api.client.get("/api/coverage/detailed")
    assert response.status_code == 200
    rows = {row["chamber"]: row for row in response.json()}

    deputies = rows["deputies"]
    assert deputies["total_memberships"] == 4
    assert deputies["dated_pct"] == 100
    assert deputies["sourced_pct"] == 100
    assert deputies["total_switches"] == 1
    assert deputies["sourced_switches_pct"] == 0

    senate = rows["senate"]
    assert senate["total_memberships"] == 0
    assert senate["dated_pct"] is None
    assert senate["sourced_pct"] is None
    assert senate["total_switches"] == 0
    assert senate["sourced_switches_pct"] is None


def test_coverage_last_refresh_sees_non_switch_events(api):
    """``last_refresh`` must reflect the newest event of any type, while the
    switch counters stay restricted to switch events."""
    session = api.factory()
    session.add(
        Event(
            type="switch_group",
            person_id=api.ids.p1,
            chamber="deputies",
            legislature="2024",
            event_date=date(2025, 1, 1),
            detected_at=datetime(2025, 1, 1, 1, 0, 0),
            dedup_key="coverage-detail:switch",
        )
    )
    session.add(
        Event(
            type="mandate_start",
            person_id=api.ids.p1,
            chamber="deputies",
            legislature="2024",
            event_date=date(2025, 2, 3),
            detected_at=datetime(2030, 2, 3, 4, 5, 6),
            dedup_key="coverage-detail:non-switch",
        )
    )
    session.commit()
    session.close()

    rows = {row["chamber"]: row for row in api.client.get("/api/coverage/detailed").json()}
    deputies = rows["deputies"]
    assert deputies["last_refresh"] == "2030-02-03T04:05:06"
    assert deputies["total_switches"] == 1


def test_coverage_persisted_rows_enriched(api):
    session = api.factory()
    session.add(
        Coverage(
            chamber="deputies", legislature="2024", completeness="partial", note="Persisted row"
        )
    )
    session.commit()
    session.close()

    response = api.client.get("/api/coverage")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["note"] == "Persisted row"
    assert rows[0]["completeness"] == "partial"
    assert rows[0]["persons"] == 2

    detailed = api.client.get("/api/coverage/detailed")
    assert detailed.status_code == 200
    detailed_rows = detailed.json()
    assert len(detailed_rows) == 1
    assert detailed_rows[0]["total_memberships"] == 4
    assert detailed_rows[0]["dated_pct"] == 100


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
    assert body["database"] == {
        "status": "ok",
        "persons": 2,
        "memberships": 4,
    }
    assert body["dataset"] == {
        "release_tag": None,
        "published_at": None,
        "asset_sha256": None,
    }


def test_health_separates_liveness_readiness_and_dataset_metadata(api, tmp_path, monkeypatch):
    import json

    from backend.routers import api as api_router

    metadata_path = tmp_path / "dataset-metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "release_tag": "data-123-1",
                "published_at": "2026-11-14T10:55:25Z",
                "asset_sha256": "a" * 64,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(api_router, "DATASET_METADATA_PATH", metadata_path)

    live = api.client.get("/api/health/live")
    assert live.status_code == 200
    assert live.json() == {"status": "ok"}

    ready = api.client.get("/api/health/ready")
    assert ready.status_code == 200
    assert ready.json()["database"]["status"] == "ok"

    health = api.client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["dataset"] == {
        "release_tag": "data-123-1",
        "published_at": "2026-11-14T10:55:25Z",
        "asset_sha256": "a" * 64,
    }


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
    assert response.json()["detail"] == ("admin polling disabled (set PARLAMENT_ADMIN_TOKEN)")


def test_admin_poll_rejects_wrong_token(api, monkeypatch):
    monkeypatch.setenv("PARLAMENT_ADMIN_TOKEN", "s3cret")
    response = api.client.post("/api/admin/poll", headers={"X-Admin-Token": "wrong-token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid admin token"

    missing = api.client.post("/api/admin/poll")
    assert missing.status_code == 401


# --- Regressions -----------------------------------------------------------


def test_party_not_found_returns_404(api):
    """Regression: HTTPException was referenced without being imported, so the
    missing-party path returned 500 instead of 404."""
    paths = [
        "/api/party/NOPE",
        "/api/party/NOPE/movements",
        "/api/party/NOPE/timeline?from=2024-01-01&to=2025-01-01",
    ]
    for path in paths:
        response = api.client.get(path)
        assert response.status_code == 404, (path, response.status_code, response.text)


def test_committees_endpoint_returns_empty_list(api):
    response = api.client.get("/api/committees", params={"as_of": "2025-01-01"})
    assert response.status_code == 200
    assert response.json() == []


def test_cross_chamber_uses_date_scoped_mandates(api):
    session = api.factory()
    session.add_all(
        [
            Mandate(
                person_id=api.ids.p1,
                chamber="deputies",
                legislature="2000",
                start_date=date(2000, 1, 1),
            ),
            Mandate(
                person_id=api.ids.p1,
                chamber="senate",
                legislature="2004",
                start_date=date(2004, 1, 1),
            ),
            Mandate(
                person_id=api.ids.p2,
                chamber="deputies",
                legislature="2024",
                start_date=date(2024, 12, 21),
            ),
            Mandate(
                person_id=api.ids.p2,
                chamber="senate",
                legislature="2028",
                start_date=date(2025, 2, 1),
            ),
        ]
    )
    session.commit()
    session.close()

    response = api.client.get(
        "/api/analytics/cross-chamber",
        params={"as_of": "2025-01-14"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["as_of"] == "2025-01-14"
    assert body["count"] == 1
    assert body["data"][0] == {
        "person_id": api.ids.p1,
        "name": "Ion Ștefan Popescu",
        "chambers": ["deputies", "senate"],
        "deputies": ["2000"],
        "senate": ["2004"],
    }


def test_party_cohesion_handles_group_target(api):
    """Regression: the code read `Organization.on_behalf_of_id`, a column that
    lives on Membership. A switch_party event whose target is a group crashed
    the endpoint with AttributeError."""
    session = api.factory()
    session.add(
        Event(
            type="switch_party",
            person_id=api.ids.p2,
            chamber="deputies",
            from_org_id=api.ids.pnl_party,
            to_org_id=api.ids.psd,  # a group, not a party
            event_date=date(2025, 2, 1),
            dedup_key="evt:switch:party:group-target",
        )
    )
    session.commit()
    session.close()

    response = api.client.get("/api/analytics/party-cohesion")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    result = next(row for row in body["data"] if row["party_name"] == "PSD")
    assert result["members"] == 2
    assert result["switches"] == 2
    assert result["switchers"] == 1


def test_party_cohesion_reports_missing_switch_data(api):
    session = api.factory()
    for event in session.query(Event).filter(Event.type == "switch_party").all():
        session.delete(event)
    session.commit()
    session.close()

    response = api.client.get("/api/analytics/party-cohesion")
    assert response.status_code == 200
    assert response.json() == {
        "status": "unavailable",
        "data": [],
        "reason": "No dated party-switch events can be attributed to party memberships.",
    }


def test_generational_shift_uses_group_party_and_historical_age(api):
    response = api.client.get(
        "/api/analytics/generational-shift",
        params={"legislature": "2024", "as_of": "2025-01-14"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["as_of"] == "2025-01-14"
    assert body["data"] == [
        {
            "party": "PNL",
            "mps_with_birth_dates": 1,
            "avg_age": 45.0,
            "median_age": 45,
        },
        {
            "party": "PSD",
            "mps_with_birth_dates": 1,
            "avg_age": 45.0,
            "median_age": 45,
        },
    ]


def test_analytics_wave_mutations_are_post_and_admin_protected(api, monkeypatch):
    monkeypatch.delenv("PARLAMENT_ADMIN_TOKEN", raising=False)
    path = "/api/analytics/waves?chamber=deputies&legislature=2024"
    assert api.client.get(path).status_code == 405
    assert api.client.get("/api/analytics/waves/recompute").status_code == 405
    assert api.client.post(path).status_code == 503

    monkeypatch.setenv("PARLAMENT_ADMIN_TOKEN", "test-token")
    session = api.factory()
    session.add_all(
        [
            Event(
                type="switch_party",
                person_id=api.ids.p1,
                chamber="deputies",
                event_date=date(2025, 1, 11),
                dedup_key="evt:wave:test:1",
            ),
            Event(
                type="switch_party",
                person_id=api.ids.p2,
                chamber="deputies",
                event_date=date(2025, 1, 12),
                dedup_key="evt:wave:test:2",
            ),
        ]
    )
    session.commit()
    session.close()

    response = api.client.post(path, headers={"X-Admin-Token": "test-token"})
    assert response.status_code == 200
    assert response.json()["created"] == 1
    assert len(api.client.get("/api/analytics/switch-waves").json()) == 1


def test_analytics_wave_recompute_removes_stale_rows(api, monkeypatch):
    monkeypatch.setenv("PARLAMENT_ADMIN_TOKEN", "test-token")
    session = api.factory()
    session.add(
        SwitchWave(
            label="stale",
            start_date=date(1990, 1, 1),
            end_date=date(1990, 1, 30),
            switch_count=9,
            chamber="deputies",
            legislature="1990",
        )
    )
    session.commit()
    session.close()

    response = api.client.post(
        "/api/analytics/waves/recompute",
        headers={"X-Admin-Token": "test-token"},
    )
    assert response.status_code == 200
    assert response.json()["created"] == 0
    assert api.client.get("/api/analytics/switch-waves").json() == []


def test_analytics_waves_post_invalidates_seeded_cache(api, monkeypatch):
    """P0-F regression: the waves POST wrote rows but never invalidated the
    result cache, so a GET seeded before the write kept serving stale data.
    """
    monkeypatch.setenv("PARLAMENT_ADMIN_TOKEN", "test-token")
    session = api.factory()
    session.add_all(
        [
            Event(
                type="switch_party",
                person_id=api.ids.p1,
                chamber="deputies",
                event_date=date(2025, 1, 11),
                dedup_key="evt:wave:invalidate:1",
            ),
            Event(
                type="switch_party",
                person_id=api.ids.p2,
                chamber="deputies",
                event_date=date(2025, 1, 12),
                dedup_key="evt:wave:invalidate:2",
            ),
        ]
    )
    session.commit()
    session.close()

    path = "/api/analytics/switch-waves"
    # Seed the cache BEFORE the write: no waves yet -> [] is cached.
    assert api.client.get(path).json() == []

    response = api.client.post(
        "/api/analytics/waves?chamber=deputies&legislature=2024",
        headers={"X-Admin-Token": "test-token"},
    )
    assert response.status_code == 200
    assert response.json()["created"] == 1

    # Fresh GET must see the new wave, not the seeded stale [].
    assert len(api.client.get(path).json()) == 1


def test_analytics_waves_post_calls_both_invalidators(api, monkeypatch):
    """The waves POST must clear both the result cache and the traseism
    overview cache, like the other admin write paths."""
    monkeypatch.setenv("PARLAMENT_ADMIN_TOKEN", "test-token")
    from backend.routers import api as api_router

    calls = {"result": 0, "traseism": 0}

    def mark_result():
        calls["result"] += 1

    def mark_traseism():
        calls["traseism"] += 1

    monkeypatch.setattr(api_router, "invalidate_result_cache", mark_result)
    monkeypatch.setattr(api_router, "invalidate_traseism_overview_cache", mark_traseism)

    response = api.client.post(
        "/api/analytics/waves?chamber=deputies&legislature=2024",
        headers={"X-Admin-Token": "test-token"},
    )
    assert response.status_code == 200
    assert calls == {"result": 1, "traseism": 1}


def test_movements_excludes_undated_events(api):
    """Regression: `Event.event_date is not None` was a Python identity test
    (always True), so the SQL date filter was silently dropped."""
    session = api.factory()
    session.add(
        Event(
            type="switch_party",
            person_id=api.ids.p1,
            chamber="deputies",
            from_org_id=api.ids.psd_party,
            to_org_id=api.ids.pnl_party,
            event_date=None,
            dedup_key="evt:switch:party:undated",
        )
    )
    session.commit()
    session.close()

    response = api.client.get("/api/party/PSD/movements")
    assert response.status_code == 200
    assert all(row["event_date"] is not None for row in response.json())


def test_party_movements_respects_as_of_date(api):
    before_switch = api.client.get(
        "/api/party/PNL/movements",
        params={"as_of": "2025-01-09"},
    )
    on_switch_date = api.client.get(
        "/api/party/PNL/movements",
        params={"as_of": "2025-01-10"},
    )
    assert before_switch.status_code == 200
    assert before_switch.json() == []
    assert on_switch_date.status_code == 200
    assert any(event["event_date"] == "2025-01-10" for event in on_switch_date.json())


def test_party_profile_counts_only_active_legislature_and_dated_switches(api):
    session = api.factory()
    session.add_all(
        [
            Membership(
                person_id=api.ids.p1,
                org_id=api.ids.psd,
                on_behalf_of_id=api.ids.psd_party,
                chamber="deputies",
                legislature="2020",
                start_date=date(2020, 1, 1),
                confidence="official_ledger",
            ),
        ]
    )
    session.commit()
    session.close()

    before_switch = api.client.get(
        "/api/party/PSD",
        params={"as_of": "2025-01-09"},
    ).json()
    on_switch_date = api.client.get(
        "/api/party/PSD",
        params={"as_of": "2025-01-10"},
    ).json()
    pnl_before_switch = api.client.get(
        "/api/party/PNL",
        params={"as_of": "2025-01-09"},
    ).json()
    pnl_on_switch_date = api.client.get(
        "/api/party/PNL",
        params={"as_of": "2025-01-10"},
    ).json()

    assert before_switch["current_members"] == 1
    assert before_switch["switches_out"] == 0
    assert on_switch_date["current_members"] == 1
    assert on_switch_date["switches_out"] == 1
    assert pnl_before_switch["switches_in"] == 0
    assert pnl_on_switch_date["switches_in"] == 1


def test_party_profile_reports_missing_switch_data_as_unavailable(api):
    session = api.factory()
    session.query(Event).filter(Event.type == "switch_party").delete()
    session.commit()
    session.close()

    response = api.client.get(
        "/api/party/PSD",
        params={"as_of": "2025-01-09"},
    )
    assert response.status_code == 200
    assert response.json()["switches_in"] is None
    assert response.json()["switches_out"] is None
    assert response.json()["net_change"] is None
