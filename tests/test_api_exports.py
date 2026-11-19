"""Export API contract tests: headers, scope, and CSV/JSON body shape."""

from __future__ import annotations

import time
from datetime import date
from types import SimpleNamespace

import pytest
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

import backend.cache as cache
from backend.deps import get_db
from backend.main import create_app
from pipeline.db import (
    Event,
    Membership,
    Organization,
    Person,
    PersonIdentifier,
    get_session,
    make_engine,
    make_session_factory,
)


def _seed(session) -> SimpleNamespace:
    person = Person(
        canonical_name="Ștefan Popescu",
        normalized_name="stefan popescu",
        sort_key="popescu stefan",
        birth_date=date(1980, 1, 2),
    )
    session.add(person)
    session.flush()
    session.add(
        PersonIdentifier(
            person_id=person.id, scheme="cdep_idm", identifier="42", legislature="2024"
        )
    )

    group = Organization(
        classification="group",
        name="Grupul PSD",
        short_name="PSD",
        normalized_name="grupul psd",
        chamber="deputies",
        color="#E63946",
    )
    party = Organization(
        classification="party",
        name="PSD",
        short_name="PSD",
        normalized_name="psd",
        chamber="deputies",
    )
    session.add_all([group, party])
    session.flush()

    session.add(
        Membership(
            person_id=person.id,
            org_id=group.id,
            on_behalf_of_id=party.id,
            chamber="deputies",
            legislature="2024",
            role="member",
            start_date=date(2024, 12, 21),
            confidence="official_ledger",
            source_url="https://www.cdep.ro/example",
        )
    )
    session.add(
        Event(
            type="switch_group",
            person_id=person.id,
            chamber="deputies",
            from_org_id=party.id,
            to_org_id=group.id,
            event_date=date(2025, 1, 1),
            dedup_key="switch:export",
        )
    )
    session.commit()
    return SimpleNamespace(person=person.id, group=group.id, party=party.id)


@pytest.fixture()
def api(tmp_path, monkeypatch):
    monkeypatch.delenv("PARLAMENT_ADMIN_TOKEN", raising=False)
    monkeypatch.delenv("PARLAMENT_POLL_INTERVAL_MIN", raising=False)

    db_path = tmp_path / "exports.db"
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
    client = TestClient(app)
    yield SimpleNamespace(client=client, ids=ids, factory=factory)
    client.close()


def test_popolo_headers_and_shape(api):
    response = api.client.get(
        "/api/export/popolo", params={"chamber": "deputies", "legislature": "2024"}
    )
    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="popolo.json"'
    assert "application/json" in response.headers["content-type"]
    assert "utf-8" in response.headers["content-type"].lower()

    body = response.json()
    assert body["meta"]["scope"] == {"chamber": "deputies", "legislature": "2024"}
    assert body["meta"]["counts"] == {
        "persons": 1,
        "organizations": 2,
        "posts": 0,
        "memberships": 1,
        "events": 1,
    }
    assert body["meta"]["data_license"] == "CC-BY-4.0"
    # UTF-8 diacritics survive serialization.
    assert body["persons"][0]["name"] == "Ștefan Popescu"


def test_popolo_empty_scope_is_valid(api):
    response = api.client.get(
        "/api/export/popolo", params={"chamber": "senate", "legislature": "1990"}
    )
    assert response.status_code == 200
    assert response.json()["meta"]["counts"]["memberships"] == 0


def test_memberships_csv_headers_and_content(api):
    response = api.client.get("/api/export/memberships.csv", params={"chamber": "deputies"})
    assert response.status_code == 200
    assert response.headers["content-disposition"] == ('attachment; filename="memberships.csv"')
    assert response.headers["content-type"] == "text/csv; charset=utf-8"

    text = response.text
    lines = text.splitlines()
    assert lines[0].startswith("id,person_id,organization_id,post_id")
    assert api.ids.person in text
    assert "official_ledger" in text
    assert "https://www.cdep.ro/example" in text


def test_report_has_fresh_timestamp_and_never_caches_response(api):
    """Consecutive report downloads carry different ``generated_at`` values.

    The expensive aggregation is cached as a plain dict, but the timestamp and
    the ``JSONResponse`` wrapper must be rebuilt per request — a cached
    Response object would freeze ``generated_at`` for the whole TTL window.
    """
    cache.invalidate()
    r1 = api.client.get("/api/export/report")
    time.sleep(0.002)  # guarantee distinct microsecond stamps
    r2 = api.client.get("/api/export/report")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.headers["content-disposition"] == 'attachment; filename="transparency-report.json"'
    g1 = r1.json()["generated_at"]
    g2 = r2.json()["generated_at"]
    assert g1 != g2
    assert r1.json()["scope"] == "all"
    assert r2.json()["totals"] == r1.json()["totals"]

    cached = [
        value for key, (_ts, value) in cache._store.items() if key.startswith("export-report:")
    ]
    assert cached, "report data should be cached as plain data"
    assert isinstance(cached[0], dict)
    assert not isinstance(cached[0], JSONResponse)
    assert "generated_at" not in cached[0]


def test_unknown_dataset_is_404(api):
    response = api.client.get("/api/export/nope.csv")
    assert response.status_code == 404
    assert "unknown dataset" in response.json()["detail"]


def test_csv_out_of_scope_has_only_header(api):
    response = api.client.get(
        "/api/export/persons.csv", params={"chamber": "senate", "legislature": "1990"}
    )
    assert response.status_code == 200
    assert (
        response.text.strip()
        == "id,name,sort_name,birth_date,wikidata_qid,match_status,identifiers"
    )
