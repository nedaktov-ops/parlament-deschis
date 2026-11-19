"""W2-A regressions: GraphQL/REST convergence, shared session, DI, headers.

All data is synthetic and lives in a tmp SQLite file — this suite never reads
or writes ``data/*.db``.
"""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.engine import Engine

from backend import cache as cache_mod
from backend.deps import get_db
from backend.graphql import schema as gql_schema
from backend.main import ON_CYCLE_INVALIDATE, create_app
from backend.routers import api as api_mod
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

_LEG_END = date(2029, 12, 31)


def _seed(path):
    """Two parties, two group memberships on on_behalf_of_id, one cross-chamber MP."""
    engine = make_engine(path)
    init_db(engine)
    with make_session_factory(engine)() as s:
        psd = Organization(
            id="o-psd", classification="party", name="PSD", normalized_name="psd", short_name="PSD"
        )
        pnl = Organization(
            id="o-pnl", classification="party", name="PNL", normalized_name="pnl", short_name="PNL"
        )
        g_psd = Organization(
            id="g-psd", classification="group", name="Group PSD", normalized_name="group psd"
        )
        g_pnl = Organization(
            id="g-pnl", classification="group", name="Group PNL", normalized_name="group pnl"
        )
        s.add_all([psd, pnl, g_psd, g_pnl])
        s.add(
            KeyEvent(
                id="ke-2024",
                type="legislature",
                label="2024",
                start_date=date(2024, 1, 1),
                end_date=_LEG_END,
            )
        )
        s.add_all(
            [
                Person(
                    id="p1",
                    canonical_name="Cross Both",
                    normalized_name="cross both",
                    birth_date=date(1980, 1, 1),
                ),
                Person(
                    id="p2",
                    canonical_name="Only Deputy",
                    normalized_name="only deputy",
                    birth_date=date(1970, 1, 1),
                ),
                Person(id="p3", canonical_name="No Birth", normalized_name="no birth"),
            ]
        )
        s.add_all(
            [
                Membership(
                    id="m1",
                    person_id="p1",
                    org_id="g-psd",
                    on_behalf_of_id="o-psd",
                    chamber="deputies",
                    legislature="2024",
                    start_date=date(2024, 1, 1),
                    end_date=None,
                ),
                Membership(
                    id="m2",
                    person_id="p2",
                    org_id="g-pnl",
                    on_behalf_of_id="o-pnl",
                    chamber="deputies",
                    legislature="2024",
                    start_date=date(2024, 1, 1),
                    end_date=None,
                ),
                Membership(
                    id="m3",
                    person_id="p3",
                    org_id="g-psd",
                    on_behalf_of_id="o-psd",
                    chamber="deputies",
                    legislature="2024",
                    start_date=date(2024, 1, 1),
                    end_date=None,
                ),
            ]
        )
        s.add_all(
            [
                Mandate(
                    id="md1",
                    person_id="p1",
                    chamber="deputies",
                    legislature="2024",
                    start_date=date(2024, 1, 1),
                ),
                Mandate(
                    id="md2",
                    person_id="p1",
                    chamber="senate",
                    legislature="2024",
                    start_date=date(2024, 1, 1),
                ),
                Mandate(
                    id="md3",
                    person_id="p2",
                    chamber="deputies",
                    legislature="2024",
                    start_date=date(2024, 1, 1),
                ),
            ]
        )
        s.commit()
    return engine


@pytest.fixture()
def seeded_client(tmp_path, monkeypatch):
    engine = _seed(tmp_path / "gql.db")
    monkeypatch.setattr(gql_schema, "make_engine", lambda: engine)
    with TestClient(create_app()) as client:
        yield client
    engine.dispose()


def _gql(client, query):
    r = client.post("/graphql", json={"query": query})
    assert r.status_code == 200, r.text
    return r.json()


def test_generational_shift_joins_on_behalf_of_and_is_non_empty(seeded_client):
    body = _gql(
        seeded_client,
        '{ generationalShift(legislature:"2024") { party mpsWithBirthDates avgAge medianAge } }',
    )
    assert "errors" not in body, body
    rows = {r["party"]: r for r in body["data"]["generationalShift"]}
    # Party lives in on_behalf_of_id; org_id is the group. The old resolver
    # filtered party org_id -> always [].
    assert set(rows) == {"PSD", "PNL"}
    assert rows["PSD"]["mpsWithBirthDates"] == 1  # p3 has no birth date
    assert rows["PNL"]["mpsWithBirthDates"] == 1


def test_cross_chamber_matches_rest(seeded_client):
    gql = _gql(seeded_client, "{ crossChamber { personId name chambers } }")
    rest = seeded_client.get("/api/analytics/cross-chamber").json()
    assert "errors" not in gql, gql
    assert len(gql["data"]["crossChamber"]) == rest["count"] == 1
    assert gql["data"]["crossChamber"][0]["personId"] == "p1"


@pytest.mark.parametrize(
    ("query", "field"),
    [
        ("{ crossChamber { personId } }", "crossChamber"),
        ('{ generationalShift(legislature:"2024") { party } }', "generationalShift"),
    ],
)
def test_sql_statements_per_field_under_20(seeded_client, query, field):
    statements = {"n": 0}

    def _count(*args):
        statements["n"] += 1

    event.listen(Engine, "before_cursor_execute", _count)
    try:
        body = _gql(seeded_client, query)
    finally:
        event.remove(Engine, "before_cursor_execute", _count)
    assert "errors" not in body, body
    assert body["data"][field], body
    assert statements["n"] < 20, statements["n"]


def test_one_engine_created_per_app_lifespan(tmp_path, monkeypatch):
    db_path = tmp_path / "engine.db"
    engine = _seed(db_path)
    calls = {"n": 0}
    real_make = make_engine

    def _counting():
        calls["n"] += 1
        return real_make(db_path)

    monkeypatch.setattr(gql_schema, "make_engine", _counting)
    with TestClient(create_app()) as client:
        # Two fields in one request must not create another engine.
        body = _gql(client, "{ persons(limit:1) { id } parties(limit:1) { id } }")
        assert "errors" not in body, body
        assert calls["n"] == 1, calls["n"]
    engine.dispose()


def test_empty_overridden_db_yields_empty_rest_and_graphql(tmp_path, monkeypatch):
    """get_db override controls both surfaces — proof of real DI."""
    seeded = _seed(tmp_path / "seeded.db")
    empty = make_engine(tmp_path / "empty.db")
    init_db(empty)
    monkeypatch.setattr(gql_schema, "make_engine", lambda: seeded)

    def override():
        s = make_session_factory(empty)()
        try:
            yield s
        finally:
            s.close()

    app = create_app()
    app.dependency_overrides[get_db] = override
    with TestClient(app) as client:
        rest = client.get("/api/persons").json()
        gql = _gql(client, "{ persons { id } }")
    assert rest == []
    assert gql["data"]["persons"] == []
    assert "errors" not in gql, gql
    seeded.dispose()
    empty.dispose()


def test_security_headers_and_no_store_on_graphql(seeded_client):
    h = seeded_client.get("/api/health")
    assert h.headers["x-content-type-options"] == "nosniff"
    assert h.headers["x-frame-options"] == "DENY"
    assert h.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert h.headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
    assert "default-src" in h.headers["content-security-policy-report-only"]

    g = seeded_client.post("/graphql", json={"query": "{ persons(limit:1) { id } }"})
    assert "no-store" in g.headers["cache-control"]


def test_poller_on_cycle_invalidates_both_caches():
    @cache_mod.cached("w2a-probe")
    def _value(x):
        return x

    assert _value("a") == "a"
    assert cache_mod._store, "result cache not populated"
    api_mod._traseism_overview_cache = ["sentinel"]

    ON_CYCLE_INVALIDATE()

    assert not cache_mod._store, "result cache not invalidated"
    assert api_mod._traseism_overview_cache is None, "traseism cache not invalidated"
