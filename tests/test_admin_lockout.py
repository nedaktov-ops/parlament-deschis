"""W2-B: the admin lockout must be keyed by client IP, not by the guessed token.

The old helper fingerprinted the *guessed token*, so ten different wrong
guesses from one address were ten first attempts and never produced a 429.
These tests hit the real endpoints (so a ``Request`` reaches the helper) and
prove that distinct wrong guesses from one IP now accumulate into a lockout.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from backend.deps import get_db
from backend.main import create_app
from backend.routers import api as api_module
from pipeline.db import get_session, make_engine, make_session_factory


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("PARLAMENT_ADMIN_TOKEN", "correct-horse")
    monkeypatch.delenv("PARLAMENT_POLL_INTERVAL_MIN", raising=False)
    # Start every test with clean per-IP / global auth buckets.
    monkeypatch.setattr(api_module._require_admin_token, "_auth_state", None, raising=False)
    # Avoid any network access on the success path.
    monkeypatch.setattr(api_module, "run_poll_cycle", lambda db, legislature: {"ok": True})

    db_path = tmp_path / "lockout.db"
    seed = get_session(db_path)
    seed.close()
    factory = make_session_factory(make_engine(db_path))

    def override():
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_db] = override
    test_client = TestClient(app)
    yield test_client
    test_client.close()
    monkeypatch.setattr(api_module._require_admin_token, "_auth_state", None, raising=False)


def test_ten_distinct_wrong_guesses_from_one_ip_lock_out(client):
    codes = [
        client.post("/api/admin/poll", headers={"X-Admin-Token": f"wrong-{i}"}).status_code
        for i in range(10)
    ]
    # max_failures = 5: the first five are 401, from the sixth onward 429.
    assert codes[:5] == [401] * 5
    assert codes[5:] == [429] * 5
    # The tenth distinct guess must be 429 — the exact defect that previously
    # returned 401 for every one of the ten.
    assert codes[-1] == 429


def test_valid_token_succeeds_and_clears_the_ip_bucket(client):
    assert client.post("/api/admin/poll", headers={"X-Admin-Token": "bad-1"}).status_code == 401
    assert client.post("/api/admin/poll", headers={"X-Admin-Token": "bad-2"}).status_code == 401
    assert (
        client.post("/api/admin/poll", headers={"X-Admin-Token": "correct-horse"}).status_code
        == 200
    )
    # Success clears that IP's failures: a further wrong guess is 401 again,
    # not a stale 429.
    assert client.post("/api/admin/poll", headers={"X-Admin-Token": "bad-3"}).status_code == 401


def test_lockout_is_scoped_to_the_client_ip(client):
    """A second address must start with a clean bucket of its own."""

    def request_from(host: str) -> Request:
        return Request({"type": "http", "client": (host, 12345), "headers": []})

    first = request_from("10.0.0.1")
    second = request_from("10.0.0.2")
    for i in range(5):
        with pytest.raises(Exception) as exc:
            api_module._require_admin_token(f"bad-{i}", request=first)
        assert exc.value.status_code == 401

    # Same IP is now locked out.
    with pytest.raises(Exception) as exc:
        api_module._require_admin_token("bad-0", request=first)
    assert exc.value.status_code == 429

    # A different IP is not affected by the first one's failures.
    with pytest.raises(Exception) as exc:
        api_module._require_admin_token("bad-0", request=second)
    assert exc.value.status_code == 401


def test_no_token_keeps_fail_closed(client, monkeypatch):
    monkeypatch.delenv("PARLAMENT_ADMIN_TOKEN", raising=False)
    response = client.post("/api/admin/poll", headers={"X-Admin-Token": "anything"})
    assert response.status_code == 503
