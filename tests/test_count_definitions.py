"""R-04 regressions: labelled counts, honest denominators, no null→0.

These are read-only API probes against the DB configured by ``PARLAMENT_DB``
(default ``data/parlament-real.db``). The lifespan must run: it disposes the
module-global ``backend.deps`` engine on exit, so these real-DB probes cannot
leak a session factory into later tests that seed their own databases.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_dashboard_stats_publishes_labelled_switch_split(client):
    data = client.get("/api/dashboard/stats").json()["data"]
    assert data["switches_all"] == data["switches_group"] + data["switches_party"]
    assert data["switches"] == data["switches_all"]
    assert set(data["definitions"]) >= {"switches_group", "switches_party", "switches_all"}
    assert data["coverage_score"] is None or isinstance(data["coverage_score"], int)


def test_report_and_dashboard_agree_on_group_switches(client):
    report = client.get("/api/export/report").json()["totals"]
    stats = client.get("/api/dashboard/stats").json()["data"]
    assert report["switches_group"] == stats["switches_group"]
    assert report["switches_all"] == stats["switches_all"]


def test_mps_total_is_not_the_page_length(client):
    body = client.get("/api/mps?limit=3&offset=0").json()
    assert len(body["data"]) <= 3
    assert body["total"] >= len(body["data"])
    assert body["definition"].startswith("total = persons matching q")


def test_coverage_summary_uses_raw_counts_and_null_denominators(client):
    body = client.get("/api/coverage/summary").json()
    t = body["totals"]
    assert t["switches_all"] == t["switches_group"] + t["switches_party"]
    p = body["percentages"]
    assert p["dated"] is None if t["memberships"] == 0 else 0 <= p["dated"] <= 100


def test_generational_shift_totals_do_not_count_unknowns_as_known(client):
    body = client.get("/api/analytics/generational-shift").json()
    t = body["totals"]
    assert t["mps_in_scope"] == t["mps_with_birth_date"] + t["mps_unknown_birth_date"]
    assert t["coverage_pct"] is None or 0 <= t["coverage_pct"] <= 100


def test_scorecard_percentages_are_null_when_denominator_is_zero(client):
    body = client.get("/api/votes/scorecard?min_votes=1&limit=5").json()
    for row in body["data"]:
        d = row["denominators"]["alignment"]
        assert (row["rebellion_pct"] is None) == (d == 0)
        assert (row["loyalty_pct"] is None) == (d == 0)


def test_traseism_payload_declares_group_only_definition(client):
    body = client.get("/api/traseism/summary").json()
    assert body["definitions"]["switches"].startswith("Group switches only")
