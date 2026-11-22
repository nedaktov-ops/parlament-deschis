"""R-08 feature-honesty regressions.

Static source assertions pin the honest copy; API assertions pin the additive
response fields (`trigger_provenance`, `/votes.scopes`, `/movements.legislature`)
without changing or removing any existing field. All DB fixtures are temp
files; no data/ DB is written.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.graphql import schema as gql_schema
from backend.main import create_app
from pipeline.db import (
    Person,
    Vote,
    VotePosition,
    init_db,
    make_engine,
    make_session_factory,
)

ROOT = Path(__file__).resolve().parents[1]


def _src(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


@pytest.fixture()
def client(app):
    """Canonical read-only corpus copy via the shared fixture (no seeding)."""
    return TestClient(app)


# --- W1: trigger provenance -------------------------------------------------


def test_switch_waves_trigger_provenance_is_additive(client):
    rows = client.get("/api/analytics/switch-waves").json()
    assert isinstance(rows, list) and rows
    required = {
        "id",
        "label",
        "start_date",
        "end_date",
        "switch_count",
        "trigger_type",
        "trigger_event",
        "legislature",
        "chamber",
        "created_at",
        "trigger_provenance",
    }
    for row in rows:
        assert required <= set(row)
        if row["trigger_event"]:
            assert row["trigger_provenance"]
            assert "editor-curated" in row["trigger_provenance"]
            assert "no per-event source URL" in row["trigger_provenance"]
        else:
            assert row["trigger_provenance"] is None


# --- W2: Bureau declared gap ------------------------------------------------


def test_bureau_gap_copy_is_explicit():
    assert "bureauDataUnavailable" not in _src("frontend/src/i18n.ts")
    assert "bureauGap" in _src("frontend/src/pages/InstitutionalView.tsx")


# --- W3: Ideology -----------------------------------------------------------


def test_ideology_has_no_poplist_claim_or_null_as_zero():
    page = _src("frontend/src/pages/Ideology.tsx")
    i18n = _src("frontend/src/i18n.ts")
    for text in (page, i18n):
        assert "PopuList data" not in text
        for axis in ("lrgen", "galtan", "eu_position"):
            assert f"d.{axis} ?? 0" not in text
    assert 'PartyIdeology.source == "ches"' in _src("backend/routers/api.py")
    # The not-yet-ingested copy is only the dataExists=false empty state.
    assert "dataExists" in page and "view.ideology.noYear" in page


# --- W4: SenateHistory ------------------------------------------------------


def test_senate_history_stats_and_licence_are_honest():
    page = _src("frontend/src/pages/SenateHistory.tsx")
    assert "coverage.data?.reduce" not in page
    assert "CC-BY 4.0" not in page
    assert "senate.history.hold" in page
    assert "allRows.reduce" in page
    i18n = _src("frontend/src/i18n.ts")
    assert "OGL-ROU-1.0" in i18n
    assert "134 GUID" not in i18n


# --- W5: Report -------------------------------------------------------------


def test_report_en_footer_distinguishes_derived_counts():
    i18n = _src("frontend/src/i18n.ts")
    assert "Every figure above is an observed count" not in i18n
    assert "Counts are observed; the loyalty score and mean/median age are derived" in i18n
    page = _src("frontend/src/pages/Report.tsx")
    assert 'c === "partial" ? 60' not in page
    assert "deputies in the corpus" not in i18n


# --- W6: CoverageView -------------------------------------------------------


def test_coverage_view_uses_dimensions_without_overall_percentage():
    page = _src("frontend/src/pages/CoverageView.tsx")
    assert "api.coverageDimensions" in page
    assert "overallPct" not in page
    assert "datedMemberships" not in page
    assert "coverageDimensions" in _src("frontend/src/api/client.ts")


# --- W7: movements legislature filter --------------------------------------


def test_movements_legislature_filter_scopes_events(client):
    unscoped = client.get("/api/movements", params={"limit": 1000}).json()
    scoped = client.get("/api/movements", params={"legislature": "1990", "limit": 1000}).json()
    assert scoped
    assert all(e.get("legislature") == "1990" for e in scoped)
    assert len(scoped) <= len(unscoped)
    # Invalid year is rejected by the shared Query pattern.
    assert client.get("/api/movements", params={"legislature": "20xx"}).status_code == 422


def test_legislature_detail_guards_unknown_year():
    page = _src("frontend/src/pages/LegislatureDetail.tsx")
    assert "yearUnknown" in page and "enabled: scoped" in page
    assert "legislature: year" in page
    assert "legislatureUnknown" in _src("frontend/src/i18n.ts")


# --- W8: votes scopes -------------------------------------------------------


def test_votes_scopes_are_data_derived_and_additive(client):
    body = client.get("/api/votes", params={"limit": 5}).json()
    assert "scopes" in body
    scopes = body["scopes"]
    assert isinstance(scopes, list) and scopes
    assert sum(s["total"] for s in scopes) == body["total"]
    assert all(set(s) == {"chamber", "legislature", "total"} for s in scopes)
    assert all(set(row) >= {"positions_incomplete"} for row in body["data"])
    assert all(isinstance(row["positions_incomplete"], bool) for row in body["data"])


# --- W9: Radar error isolation ---------------------------------------------


def test_radar_does_not_blank_on_failed_positions():
    page = _src("frontend/src/pages/Radar.tsx")
    assert "positionQueries.some((q) => q.isError)" not in page
    assert "failedPositions" in page
    assert "view.radar.failedPositions" in _src("frontend/src/i18n.ts")


# --- W10: Grafice/Topuri ----------------------------------------------------


def test_vote_pages_do_not_hardcode_2024():
    grafice = _src("frontend/src/pages/Grafice.tsx")
    assert 'traseismSummary("2024"' not in grafice
    assert 'voteCohesion("deputies", "2024"' not in grafice
    assert 'legislature="2024"' not in grafice
    topuri = _src("frontend/src/pages/Topuri.tsx")
    assert "api.scorecard(legislature, chamber, limit, offset, minVotes)" in topuri
    assert "disabled={offset + limit >= total}" in topuri


@pytest.fixture()
def seed_client(tmp_path, monkeypatch):
    """Seed one vote with a yes majority, one rebel and one abstainer."""
    engine = make_engine(tmp_path / "r08.db")
    init_db(engine)
    with make_session_factory(engine)() as s:
        for pid, name in (
            ("p1", "Loyal One"),
            ("p2", "Loyal Two"),
            ("p3", "Abstainer"),
            ("p4", "Rebel"),
        ):
            s.add(Person(id=pid, canonical_name=name, normalized_name=name.lower()))
        s.add(
            Vote(
                source="cdep",
                native_vote_id="v-r08",
                chamber="deputies",
                legislature="2020",
                vote_time="03.01.2020 11:30",
                title_raw="Vote R08",
                source_url="https://cdep.ro/v-r08.xml",
                official_vote_url="https://cdep.ro/v-r08.html",
                snapshot_hash="sha-r08",
                truth_contract_version="votes-v1",
                present=4,
                yes=2,
                no=1,
                abstain=1,
                not_voting=0,
                dedup_key="cdep:v-r08",
            )
        )
        s.flush()
        vote = s.query(Vote).filter_by(native_vote_id="v-r08").one()
        for pid, choice in (
            ("p1", "yes"),
            ("p2", "yes"),
            ("p3", "abstain"),
            ("p4", "no"),
        ):
            s.add(
                VotePosition(
                    vote_id=vote.id,
                    person_id=pid,
                    name_raw=pid,
                    group_raw="PSD",
                    choice=choice,
                    resolution_scheme="cdep_mandate",
                    source_url="https://cdep.ro/v-r08.xml",
                    dedup_key=f"cdep:v-r08:{pid}",
                )
            )
        s.commit()
    # deps.configure() is idempotent; earlier plain TestClients may have left
    # a canonical engine installed. Drop it so the lifespan picks our seed DB.
    from backend import deps

    deps.dispose()
    monkeypatch.setattr(gql_schema, "make_engine", lambda: engine)
    with TestClient(create_app()) as c:
        yield c
    deps.dispose()
    engine.dispose()


def test_abstain_against_majority_is_neither_loyal_nor_rebel(seed_client):
    body = seed_client.get(
        "/api/votes/scorecard",
        params={"legislature": "2020", "chamber": "deputies", "min_votes": 1},
    ).json()
    by_name = {e["canonical_name"]: e for e in body["data"]}
    assert "Abstainer" in by_name, body
    abstainer = by_name["Abstainer"]
    # R-04 semantics: no yes/no alignment position -> null, never a fabricated 0.
    assert abstainer["loyalty_pct"] is None
    assert abstainer["rebellion_pct"] is None
    assert abstainer["participation_pct"] > 0
    rebel = by_name["Rebel"]
    assert rebel["rebellion_pct"] == 100.0
    assert rebel["loyalty_pct"] == 0.0
    assert rebel["participation_pct"] > 0
