from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta

import pytest

from pipeline.collect import fetch_cached
from pipeline.sources.client import FetchResult, PoliteClient


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
    monkeypatch.setattr(
        collect, "collect_roster", lambda *_args, **_kwargs: object()
    )
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
