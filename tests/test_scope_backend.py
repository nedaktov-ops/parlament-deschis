"""Backend contract for the additive scope params (R-03 §5.5)."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(app):
    return TestClient(app)  # canonical read-only corpus; no seeding needed


def test_person_as_of_echoes_scope_and_filters_events(client):
    pid = client.get("/api/mps", params={"limit": 1}).json()["data"][0]["id"]
    full = client.get(f"/api/persons/{pid}").json()
    scoped = client.get(f"/api/persons/{pid}", params={"as_of": "2000-01-01"}).json()
    assert scoped["as_of"] == "2000-01-01" and full.get("as_of") is None
    assert all(e["event_date"] and e["event_date"] <= "2000-01-01" for e in scoped["events"])
    assert len(scoped["events"]) <= len(full["events"])


def test_person_invalid_as_of_is_422(client):
    pid = client.get("/api/mps", params={"limit": 1}).json()["data"][0]["id"]
    assert client.get(f"/api/persons/{pid}", params={"as_of": "yesterday"}).status_code == 422


def test_mps_scope_is_echoed_and_invalid_date_rejected(client):
    r = client.get(
        "/api/mps", params={"as_of": "2024-06-30", "chamber": "deputies", "legislature": "2024"}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["scope"] == {"as_of": "2024-06-30", "chamber": "deputies", "legislature": "2024"}
    assert body["total"] >= len(body["data"])
    assert client.get("/api/mps", params={"as_of": "not-a-date"}).status_code == 422


def test_export_report_still_advertises_no_scope(client):
    params = client.app.openapi()["paths"]["/api/export/report"]["get"].get("parameters", [])
    assert not ({"chamber", "legislature", "as_of"} & {p["name"] for p in params})
