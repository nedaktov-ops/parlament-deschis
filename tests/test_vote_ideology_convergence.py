"""Vote + ideology API completeness: canonical routes, honest empties, meta.

All data is synthetic and lives in a tmp SQLite file — this suite never reads
or writes ``data/*.db``. The tests pin the contract the frontend and SPEC rely
on: documented single-prefix paths, ``meta.generated_at``/``meta.count`` on
analytics responses, loud 422 for malformed bounds, and an honest empty payload
(instead of 500 or fabricated rows) when the corpus has no votes/ideology.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from backend.graphql import schema as gql_schema
from backend.main import create_app
from pipeline.db import (
    Organization,
    PartyIdeology,
    Person,
    Vote,
    VotePosition,
    init_db,
    make_engine,
    make_session_factory,
)


def _client(tmp_path, monkeypatch, name="v.db", seed=None):
    engine = make_engine(tmp_path / name)
    init_db(engine)
    if seed is not None:
        with make_session_factory(engine)() as s:
            seed(s)
            s.commit()
    # The app lifespan resolves its engine through this factory, so patching it
    # makes both REST (get_db) and GraphQL read the same tmp database.
    monkeypatch.setattr(gql_schema, "make_engine", lambda: engine)
    with TestClient(create_app()) as client:
        yield client
    engine.dispose()


@pytest.fixture()
def empty_client(tmp_path, monkeypatch):
    yield from _client(tmp_path, monkeypatch, name="empty.db")


def _seed_votes(s):
    s.add(
        Person(
            id="p1",
            canonical_name="Ion Popescu",
            normalized_name="ion popescu",
        )
    )
    s.add(
        Organization(
            id="o-psd",
            classification="party",
            name="Partidul Social Democrat",
            normalized_name="partidul social democrat",
            short_name="PSD",
        )
    )
    # Deliberately non-chronological string order: 25.12.2025 sorts before
    # 03.01.2026 lexicographically, but not chronologically.
    for vid, when in (
        ("v-old", "25.12.2025 10:00"),
        ("v-new", "03.01.2026 11:30"),
        ("v-mid", "15.06.2026 09:15"),
    ):
        s.add(
            Vote(
                source="cdep",
                native_vote_id=vid,
                chamber="deputies",
                legislature="2024",
                vote_time=when,
                title_raw=f"Vote {vid}",
                source_url=f"https://cdep.ro/{vid}.xml",
                official_vote_url=f"https://cdep.ro/{vid}.html",
                snapshot_hash=f"sha-{vid}",
                truth_contract_version="votes-v1",
                present=100,
                yes=60,
                no=30,
                abstain=5,
                not_voting=5,
                dedup_key=f"cdep:{vid}",
            )
        )
    s.add(
        PartyIdeology(
            organization_id="o-psd",
            survey_year=2024,
            source="ches",
            lrgen=3.5,
            lrecon=4.0,
            galtan=5.0,
            eu_position=6.0,
            source_url="https://ches.eu/2024",
            snapshot_hash="sha-ches-2024",
            dedup_key="ches:o-psd:2024",
        )
    )


@pytest.fixture()
def seeded_client(tmp_path, monkeypatch):
    def _seed(s):
        _seed_votes(s)
        # VotePosition.vote_id is a FK to Vote.id (a UUID generated on flush),
        # so resolve it after the votes are persisted.
        from sqlalchemy import select

        vote = s.scalar(select(Vote).where(Vote.native_vote_id == "v-old"))
        s.add(
            VotePosition(
                vote_id=vote.id,
                person_id="p1",
                name_raw="Ion Popescu",
                group_raw="PSD",
                choice="yes",
                resolution_scheme="cdep_mandate",
                source_url="https://cdep.ro/v-old.html",
                dedup_key="cdep:v-old:p1",
            )
        )

    yield from _client(tmp_path, monkeypatch, name="seeded.db", seed=_seed)


def _iso_stamp(value):
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None, value
    return parsed


# --- Canonical paths --------------------------------------------------------


def test_documented_paths_exist_and_legacy_aliases_still_work(empty_client):
    """SPEC documents single-prefix routes; keep the old ones for the client."""
    for path in ("/api/analytics/ideology", "/api/api/analytics/ideology"):
        r = empty_client.get(path)
        assert r.status_code == 200, (path, r.text)
        assert r.json()["data"] == []
    for path in ("/api/votes/scorecard", "/api/api/votes/scorecard"):
        r = empty_client.get(path)
        assert r.status_code == 200, (path, r.text)
        assert r.json()["data"] == []


# --- Honest empty states ----------------------------------------------------


def test_ideology_empty_reports_absence_with_real_meta(empty_client):
    r = empty_client.get("/api/analytics/ideology")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    assert body["data_exists"] is False
    assert body["data"] == []
    assert "meta" in body
    assert body["meta"]["count"] == 0
    _iso_stamp(body["meta"]["generated_at"])


def test_ideology_year_filter_empty_is_honest(empty_client):
    r = empty_client.get("/api/analytics/ideology", params={"year": "2024"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["data_exists"] is False
    assert body["data"] == []
    assert body["meta"]["count"] == 0


@pytest.mark.parametrize(
    ("path", "data_key"),
    [
        ("/api/votes", "data"),
        ("/api/votes/nonexistent/positions", "data"),
        ("/api/analytics/vote-cohesion", "data"),
        ("/api/analytics/vote-activity", "data"),
        ("/api/votes/scorecard", "data"),
    ],
)
def test_empty_vote_surfaces_return_200_and_empty_payload(empty_client, path, data_key):
    r = empty_client.get(path)
    assert r.status_code == 200, (path, r.text)
    body = r.json()
    assert body["status"] == "ok"
    assert body["data_exists"] is False
    assert body[data_key] == []


def test_unknown_vote_detail_is_honest_null(empty_client):
    r = empty_client.get("/api/votes/nonexistent")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["data_exists"] is False
    assert body["data"] is None


def test_vote_analytics_carry_meta_on_empty(empty_client):
    for path in ("/api/analytics/vote-cohesion", "/api/analytics/vote-activity"):
        body = empty_client.get(path).json()
        assert "meta" in body, path
        assert body["meta"]["count"] == 0
        _iso_stamp(body["meta"]["generated_at"])


# --- Validation: reject, never silently ignore ------------------------------


@pytest.mark.parametrize(
    ("path", "params"),
    [
        ("/api/votes", {"chamber": "assembly"}),
        ("/api/votes", {"legislature": "24"}),
        ("/api/votes", {"limit": 0}),
        ("/api/votes", {"limit": 1000}),
        ("/api/votes", {"offset": -1}),
        ("/api/votes", {"from": "not-a-date"}),
        ("/api/votes", {"to": "32.13.2026"}),
        ("/api/votes/nope/positions", {"choice": "maybe"}),
        ("/api/analytics/ideology", {"year": "24"}),
    ],
)
def test_invalid_params_are_rejected(empty_client, path, params):
    r = empty_client.get(path, params=params)
    assert r.status_code == 422, (path, params, r.status_code, r.text)


def test_reversed_date_range_is_rejected(empty_client):
    r = empty_client.get("/api/votes", params={"from": "2026-06-01", "to": "2026-01-01"})
    assert r.status_code == 422, r.text


# --- Non-empty contract -----------------------------------------------------


def test_ideology_rows_and_meta(seeded_client):
    r = seeded_client.get("/api/analytics/ideology")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["data_exists"] is True
    assert len(body["data"]) == 1
    assert body["data"][0]["party_name"] == "Partidul Social Democrat"
    assert body["data"][0]["lrgen"] == 3.5
    assert body["meta"]["count"] == 1
    _iso_stamp(body["meta"]["generated_at"])


def test_vote_detail_surfaces_evidence(seeded_client):
    r = seeded_client.get("/api/votes/v-old")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["data_exists"] is True
    data = body["data"]
    assert data["snapshot_hash"] == "sha-v-old"
    assert data["official_vote_url"] == "https://cdep.ro/v-old.html"
    assert data["truth_contract_version"] == "votes-v1"
    assert data["position_count"] == 1


def test_vote_list_pagination_and_iso_date_bounds(seeded_client):
    all_rows = seeded_client.get("/api/votes", params={"limit": 200}).json()["data"]
    assert len(all_rows) == 3

    paged = seeded_client.get("/api/votes", params={"limit": 2, "offset": 1}).json()
    assert paged["limit"] == 2
    assert paged["offset"] == 1
    assert paged["total"] == 3
    assert len(paged["data"]) == 2

    # ISO bounds must be compared as calendar dates, not lexicographically
    # against the published DD.MM.YYYY value.
    bounded = seeded_client.get(
        "/api/votes", params={"from": "2026-01-01", "to": "2026-12-31"}
    ).json()
    assert {v["native_vote_id"] for v in bounded["data"]} == {"v-new", "v-mid"}

    cdep_bounds = seeded_client.get(
        "/api/votes", params={"from": "01.01.2026", "to": "31.12.2026"}
    ).json()
    assert {v["native_vote_id"] for v in cdep_bounds["data"]} == {"v-new", "v-mid"}


def test_vote_activity_honors_date_bounds_and_meta(seeded_client):
    body = seeded_client.get("/api/analytics/vote-activity", params={"from": "2026-01-01"}).json()
    assert body["data_exists"] is True
    assert {b["date"] for b in body["data"]} == {"03.01.2026", "15.06.2026"}
    assert body["buckets"] == 2
    assert body["meta"]["count"] == 2


# --- REST / GraphQL convergence boundary ------------------------------------


def test_graphql_exposes_no_divergent_vote_or_ideology_contract(empty_client):
    """GraphQL has no vote/ideology field, so there is no second contract."""
    body = empty_client.post(
        "/graphql",
        json={"query": '{ __type(name: "Query") { fields { name } } }'},
    ).json()
    assert "errors" not in body, body
    names = {f["name"] for f in body["data"]["__type"]["fields"]}
    assert not any("vote" in n.lower() or "ideolog" in n.lower() for n in names), names
    # The REST surface does carry them — documented single-prefix paths.
    assert empty_client.get("/api/votes").status_code == 200
    assert empty_client.get("/api/analytics/ideology").status_code == 200


def test_meta_generated_at_is_fresh_and_no_fabricated_as_of(empty_client):
    """Only meta carries a real, fresh timestamp; no invented `as_of` field."""
    r1 = empty_client.get("/api/analytics/ideology").json()
    r2 = empty_client.get("/api/analytics/ideology").json()
    assert _iso_stamp(r1["meta"]["generated_at"]) <= _iso_stamp(r2["meta"]["generated_at"])
    assert "as_of" not in r1
