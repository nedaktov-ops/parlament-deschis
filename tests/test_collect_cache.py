from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

import pytest
import requests

from pipeline.collect import fetch_cached
from pipeline.sources.client import (
    BACKOFF_BASE,
    BACKOFF_MAX,
    DEFAULT_CONNECT_RETRIES,
    DEFAULT_SLEEP,
    FetchResult,
    PoliteClient,
)


class NotModifiedClient:
    def __init__(self):
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FetchResult(
            url,
            304,
            kwargs["cached_text"],
            from_cache=True,
            etag=kwargs["etag"],
            last_modified=kwargs["last_modified"],
        )


def _write_cache(path, *, checked_at):
    text = "<html>cached source</html>"
    fetched_at = datetime.now(UTC) - timedelta(days=10)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.with_suffix(".meta.json").write_text(
        json.dumps(
            {
                "url": "https://source.example/page",
                "sha256": hashlib.sha256(text.encode()).hexdigest(),
                "fetched_at": fetched_at.isoformat(),
                "last_checked_at": checked_at.isoformat(),
                "etag": '"source-v1"',
                "last_modified": "Fri, 01 Nov 2026 10:00:00 GMT",
            }
        ),
        encoding="utf-8",
    )
    return text, fetched_at


def test_offline_cache_with_crlf_is_not_treated_as_corrupt(tmp_path):
    """Regression: universal-newline reads change the hash of CRLF pages."""
    path = tmp_path / "crlf.html"
    text = "<html>line one\r\nline two\r\n</html>"
    fetched_at = datetime.now(UTC) - timedelta(days=10)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(text)
    path.with_suffix(".meta.json").write_text(
        json.dumps(
            {
                "url": "https://source.example/page",
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "fetched_at": fetched_at.isoformat(),
                "last_checked_at": fetched_at.isoformat(),
            }
        ),
        encoding="utf-8",
    )

    cached, digest, returned_at = fetch_cached(
        None,
        "https://source.example/page",
        path,
        offline=True,
        cache_ttl=timedelta(hours=1),
    )
    assert cached == text
    assert digest == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert returned_at == fetched_at


def test_stale_cache_is_conditionally_revalidated_and_keeps_source_date(tmp_path):
    path = tmp_path / "source.html"
    text, fetched_at = _write_cache(
        path,
        checked_at=datetime.now(UTC) - timedelta(days=2),
    )
    client = NotModifiedClient()

    cached_text, digest, observed_at = fetch_cached(
        client,
        "https://source.example/page",
        path,
        cache_ttl=timedelta(days=1),
    )

    assert cached_text == text
    assert digest == hashlib.sha256(text.encode()).hexdigest()
    assert observed_at == fetched_at
    assert client.calls[0][1]["etag"] == '"source-v1"'
    assert datetime.fromisoformat(
        json.loads(path.with_suffix(".meta.json").read_text())["last_checked_at"]
    ) > datetime.now(UTC) - timedelta(minutes=1)


def test_offline_mode_uses_old_cache_without_network(tmp_path):
    path = tmp_path / "source.html"
    text, _ = _write_cache(path, checked_at=datetime.now(UTC) - timedelta(days=2))

    cached_text, _digest, _fetched = fetch_cached(
        NotModifiedClient(),
        "https://source.example/page",
        path,
        offline=True,
    )

    assert cached_text == text


def test_offline_mode_fails_when_cache_is_missing(tmp_path):
    with pytest.raises(RuntimeError, match="no cached source page"):
        fetch_cached(
            NotModifiedClient(),
            "https://source.example/page",
            tmp_path / "missing.html",
            offline=True,
        )


def test_http_client_uses_cached_validators_for_304(monkeypatch):
    client = PoliteClient(sleep=0, respect_robots=False)
    captured = {}

    class NotModifiedResponse:
        status_code = 304
        headers = {"ETag": '"source-v2"'}

    def fake_get(url, *, headers, timeout):
        captured.update(headers)
        return NotModifiedResponse()

    monkeypatch.setattr(client.session, "get", fake_get)
    result = client.get(
        "https://source.example/page",
        cached_text="<html>cached</html>",
        etag='"source-v1"',
    )

    assert captured["If-None-Match"] == '"source-v1"'
    assert result.status == 304
    assert result.text == "<html>cached</html>"
    assert result.etag == '"source-v2"'
    client.close()


def test_build_corpus_revalidates_current_scope_and_resets_only_manifest(tmp_path, monkeypatch):
    import pipeline.collect as collect

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    (cache_dir / "manifest.jsonl").write_text("stale manifest\n", encoding="utf-8")
    cached_page = cache_dir / "cached-page.html"
    cached_page.write_text("source archive remains", encoding="utf-8")
    observed_ttls = {}

    def collect_legislature(_client, _chamber, legislature, **kwargs):
        observed_ttls[legislature] = kwargs["cache_ttl"]
        return []

    monkeypatch.setattr(collect, "collect_legislature", collect_legislature)
    monkeypatch.setattr(collect, "collect_roster", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(collect, "collect_index_counts", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(collect, "collect_profiles", lambda *_args, **_kwargs: {})

    collect.build_corpus(
        object(),
        ["deputies"],
        ["1990", "2024"],
        cache_dir=cache_dir,
        current_legislature="2024",
        current_cache_ttl=timedelta(days=1),
        historical_cache_ttl=timedelta(days=30),
    )

    assert observed_ttls == {
        "1990": timedelta(days=30),
        "2024": timedelta(days=1),
    }
    assert (cache_dir / "manifest.jsonl").read_text(encoding="utf-8") == ""
    assert cached_page.read_text(encoding="utf-8") == "source archive remains"


# --- W2.3 / issue #14: connection-level retry policy (no real network) -------


class _FakeResponse:
    """The minimal response surface PoliteClient.get/post actually touch."""

    def __init__(self, text="ok"):
        self.status_code = 200
        self.text = text
        self.content = text.encode("utf-8")
        self.encoding = "utf-8"
        self.headers: dict[str, str] = {}

    def raise_for_status(self):
        return None


_CDEP_URL = "https://www.cdep.ro/ords/pls/parlam/structura2015.gp?idl=1&cam=2&leg=1990"


@pytest.mark.parametrize("method", ["get", "post"])
def test_connect_failures_retry_with_exponential_backoff(monkeypatch, method):
    client = PoliteClient(sleep=0, respect_robots=False, connect_retries=4, connect_backoff=2.0)
    sleeps: list[float] = []
    calls: list[str] = []

    # Deterministic jitter and no real sleeps: the test never opens a socket.
    monkeypatch.setattr("pipeline.sources.client.time.sleep", sleeps.append)
    monkeypatch.setattr("pipeline.sources.client.random.uniform", lambda _a, _b: 0.0)

    def fake_request(url, **_kwargs):
        calls.append(url)
        if len(calls) < 4:
            raise requests.ConnectTimeout("simulated cdep connect timeout")
        return _FakeResponse()

    monkeypatch.setattr(client.session, method, fake_request)
    result = getattr(client, method)(_CDEP_URL)

    assert len(calls) == 4
    assert sleeps == [2.0, 4.0, 8.0]
    assert result.status == 200
    assert result.text == "ok"
    client.close()


def test_connect_retry_budget_is_exhausted_then_the_last_error_is_raised(monkeypatch):
    client = PoliteClient(sleep=0, respect_robots=False, connect_retries=3, connect_backoff=2.0)
    sleeps: list[float] = []
    calls: list[str] = []
    failure = requests.ConnectTimeout("simulated persistent cdep outage")

    monkeypatch.setattr("pipeline.sources.client.time.sleep", sleeps.append)
    monkeypatch.setattr("pipeline.sources.client.random.uniform", lambda _a, _b: 0.0)

    def always_fails(url, **_kwargs):
        calls.append(url)
        raise failure

    monkeypatch.setattr(client.session, "get", always_fails)

    with pytest.raises(requests.ConnectTimeout) as caught:
        client.get(_CDEP_URL)

    assert caught.value is failure
    assert len(calls) == 3  # bounded: no extra retries past the configured budget
    assert sleeps == [2.0, 4.0]
    client.close()


def test_backoff_stays_within_the_documented_ceiling_with_jitter(monkeypatch):
    client = PoliteClient(
        sleep=0, respect_robots=False, connect_retries=8, connect_backoff=BACKOFF_BASE
    )
    sleeps: list[float] = []
    calls: list[str] = []

    monkeypatch.setattr("pipeline.sources.client.time.sleep", sleeps.append)
    monkeypatch.setattr("pipeline.sources.client.random.uniform", lambda _a, _b: 0.2)

    def fails_then_succeeds(url, **_kwargs):
        calls.append(url)
        if len(calls) < 8:
            raise requests.ConnectTimeout("simulated cdep connect timeout")
        return _FakeResponse()

    monkeypatch.setattr(client.session, "get", fails_then_succeeds)
    client.get(_CDEP_URL)

    assert len(sleeps) == 7
    # _jitter() adds random.uniform(0, backoff * JITTER) to the base; the mock
    # returns 0.2 s directly, so the first sleep is 2.0 + 0.2 = 2.2 s.
    assert sleeps[0] == pytest.approx(BACKOFF_BASE + 0.2)
    assert all(value <= BACKOFF_MAX for value in sleeps)
    assert sleeps[-1] == BACKOFF_MAX  # capped, not unbounded
    client.close()


def test_default_cdep_connect_policy_is_documented_and_polite():
    # Pinned values: issue #14 showed six 25 s timeouts exhausting the old
    # budget, so a future blind change must fail review, not pass silently.
    assert DEFAULT_CONNECT_RETRIES == 8
    assert BACKOFF_MAX == 45.0
    assert DEFAULT_SLEEP >= 1.0  # <=1 request per second per host

    client = PoliteClient()
    assert client.connect_retries == DEFAULT_CONNECT_RETRIES
    assert client.connect_backoff == BACKOFF_BASE
    client.close()
