"""P4-D regression tests: GraphQL bounds, admin auth lockout, error hygiene.

Read-only probes: no test writes to ``data/*.db``. GraphQL tests point the
schema at a temporary seeded SQLite file via monkeypatch; the admin guard is
exercised directly with an injected clock.
"""

from __future__ import annotations

import time

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from backend.graphql import schema as gql_schema
from backend.main import create_app
from backend.routers import api as api_module
from pipeline.db import Person, init_db, make_engine, make_session_factory


def _seed_graphql_db(path, n_persons=250):
    engine = make_engine(path)
    init_db(engine)
    with make_session_factory(engine)() as session:
        session.add_all(
            Person(id=f"p{i:04d}", canonical_name=f"Person {i}", normalized_name=f"person {i}")
            for i in range(n_persons)
        )
        session.commit()
    return engine


def _graphql(client, query):
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == 200, response.text
    return response.json()


def test_graphql_limit_clamped_to_200(monkeypatch, tmp_path):
    """A single `limit: 10**9` must never pull the whole table."""
    engine = _seed_graphql_db(tmp_path / "gql-limit.db")
    monkeypatch.setattr(gql_schema, "make_engine", lambda: engine)
    try:
        with TestClient(create_app()) as client:
            body = _graphql(client, "{ persons(limit: 1000000000) { id } }")
            assert "errors" not in body, body
            rows = body["data"]["persons"]
            assert len(rows) == 200
            assert len({r["id"] for r in rows}) == 200

            body = _graphql(client, "{ persons(limit: -5) { id } }")
            assert "errors" not in body, body
            assert len(body["data"]["persons"]) == 1
    finally:
        engine.dispose()


def test_switch_wave_dates_nullable_in_schema():
    """SwitchWaveType dates must match REST's null handling (no serialization error)."""
    with TestClient(create_app()) as client:
        body = _graphql(
            client,
            '{ __type(name: "SwitchWaveType") { fields { name '
            "type { kind name ofType { kind name } } } } }",
        )
    assert "errors" not in body, body
    fields = {f["name"]: f["type"] for f in body["data"]["__type"]["fields"]}
    for name in ("startDate", "endDate"):
        assert fields[name]["kind"] == "SCALAR", fields[name]


def test_admin_token_fails_closed_when_unset(monkeypatch):
    monkeypatch.delenv("PARLAMENT_ADMIN_TOKEN", raising=False)
    with pytest.raises(HTTPException) as exc:
        api_module._require_admin_token("anything")
    assert exc.value.status_code == 503


def test_admin_token_lockout_with_monkeypatched_time(monkeypatch):
    monkeypatch.setenv("PARLAMENT_ADMIN_TOKEN", "correct-horse")
    monkeypatch.setattr(api_module._require_admin_token, "_auth_state", None, raising=False)
    clock = {"now": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: clock["now"])

    for _ in range(5):
        with pytest.raises(HTTPException) as exc:
            api_module._require_admin_token("guess")
        assert exc.value.status_code == 401

    with pytest.raises(HTTPException) as exc:
        api_module._require_admin_token("guess")
    assert exc.value.status_code == 429
    # Lockout is per-token: a different (including the correct) guess is not
    # blocked, so a bad actor cannot lock out the real admin by guessing.
    api_module._require_admin_token("correct-horse")
    with pytest.raises(HTTPException) as exc:
        api_module._require_admin_token("another-guess")
    assert exc.value.status_code == 401

    clock["now"] += 61.0
    with pytest.raises(HTTPException) as exc:
        api_module._require_admin_token("guess")
    assert exc.value.status_code == 401  # window expired: bucket pruned


def test_admin_poll_failure_is_generic_502(monkeypatch):
    monkeypatch.setenv("PARLAMENT_ADMIN_TOKEN", "correct-horse")
    monkeypatch.setattr(api_module._require_admin_token, "_auth_state", None, raising=False)
    secret = "/srv/internal/secret-path token=abc123"

    def boom(db, legislature):
        raise RuntimeError(secret)

    monkeypatch.setattr(api_module, "run_poll_cycle", boom)
    with TestClient(create_app()) as client:
        response = client.post("/api/admin/poll", headers={"X-Admin-Token": "correct-horse"})
    assert response.status_code == 502
    assert response.json()["detail"] == "upstream poll failed"
    assert secret not in response.text


def test_graphiql_disabled_in_production(monkeypatch):
    monkeypatch.setenv("RENDER", "true")
    with TestClient(create_app()) as client:
        response = client.get("/graphql")
    assert "graphiql" not in response.text.lower()
