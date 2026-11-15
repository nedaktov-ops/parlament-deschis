"""Tests for SenatSource discovery and ingest wiring (sitemap + historical).

Covers:
* :meth:`SenatSource.fetch_historical_guids` returns GUIDs for a known
  legislature via the ``FisaSenatori.aspx`` POST path.
* :meth:`SenatSource.ingest_profiles` with ``legislatures=...` ingests
  historical senators, de-dupes against the sitemap, and falls back to
  sitemap-only (current senators) when ``legislatures`` is ``None``.

All network access is faked: no request is ever made to senat.ro.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from pipeline.db import get_session
from pipeline.sources.senat import SenatSource

FX = Path(__file__).parent / "fixtures"

CURRENT_GUID_A = "007FDD23-B531-407E-A067-9C3796420C8C"  # also in the historical page
CURRENT_GUID_B = "3354F56C-A3E7-4CEA-9DDE-E3BD730D7B7F"
HIST_GUID_C = "11111111-2222-3333-4444-555555555555"


@dataclass
class FakeResult:
    url: str
    status: int = 200
    text: str = ""


class FakeClient:
    """Records get/post calls and returns canned responses. Never touches the network."""

    def __init__(self, sitemap_text: str, historical_text: str, fisa_page_text: str = ""):
        self.get_calls: list[str] = []
        self.post_calls: list[tuple[str, dict]] = []
        self.sitemap_text = sitemap_text
        self.historical_text = historical_text
        self.fisa_page_text = fisa_page_text

    def get(self, url, **kwargs):
        self.get_calls.append(url)
        if url.endswith("/sitemap.xml"):
            return FakeResult(url, 200, self.sitemap_text)
        if url.endswith("/FisaSenatori.aspx"):
            return FakeResult(url, 200, self.fisa_page_text)
        return FakeResult(url, 200, "<html></html>")

    def post(self, url, *, data=None, **kwargs):
        self.post_calls.append((url, dict(data or {})))
        return FakeResult(url, 200, self.historical_text)

    def close(self):
        pass


@pytest.fixture
def session():
    s = get_session(":memory:")
    yield s
    s.close()


def _install_ingest_stubs(monkeypatch, seen: list[str]):
    def fake_parse(text, *, guid, profile_url):
        seen.append(guid)
        return SimpleNamespace(name=f"Sen {guid[:4]}")

    def fake_record_fragment(
        session, *, model, source_name, group_key, content, source_id, source_url, data, force
    ):
        return None, True

    def fake_ingest(session, prof, snapshot_hash=None):
        return {"memberships": 0}

    monkeypatch.setattr("pipeline.sources.senat.parse_senator_profile", fake_parse)
    monkeypatch.setattr("pipeline.sources.senat.record_fragment", fake_record_fragment)
    monkeypatch.setattr("pipeline.sources.senat.ingest_senator_profile", fake_ingest)


def _sitemap(*guids: str) -> str:
    return "\n".join(
        f"<loc>https://www.senat.ro/FisaSenator.aspx?ParlamentarID={g}</loc>" for g in guids
    )


def test_fetch_historical_guids_returns_guids_for_known_legislature(monkeypatch):
    historical = (FX / "senat_fisa_senatori_1990.html").read_text(encoding="utf-8")
    client = FakeClient("", historical)
    source = SenatSource(client=client)

    guids = source.fetch_historical_guids(["1990"])

    assert CURRENT_GUID_A in guids
    assert HIST_GUID_C in guids
    # POSTed to the historical search page with the requested legislature.
    assert any(
        url.endswith("/FisaSenatori.aspx") and data.get("ddlLegislatura") == "1990"
        for url, data in client.post_calls
    )


def test_fetch_historical_guids_none_discovers_labels_from_page(monkeypatch):
    """``legislatures=None`` reads the legislature dropdown then fetches each."""
    fisa_page = '<select><option value="1990">1990 - 1992</option><option value="2024">2024 - present</option></select>'
    historical = f'<a href="FisaSenator.aspx?ParlamentarID={HIST_GUID_C}">C</a>'
    client = FakeClient("", historical, fisa_page_text=fisa_page)
    source = SenatSource(client=client)

    guids = source.fetch_historical_guids()

    assert HIST_GUID_C in guids
    # One GET to read the dropdown, then one POST per discovered legislature.
    assert sum(1 for u, _ in client.post_calls) == 2
    assert {data.get("ddlLegislatura") for _, data in client.post_calls} == {"1990", "2024"}


def test_ingest_profiles_with_legislatures_ingests_historical_and_dedupes(monkeypatch, session):
    client = FakeClient(
        _sitemap(CURRENT_GUID_A, CURRENT_GUID_B),
        (FX / "senat_fisa_senatori_1990.html").read_text(encoding="utf-8"),
    )
    source = SenatSource(client=client)
    seen: list[str] = []
    _install_ingest_stubs(monkeypatch, seen)

    totals = source.ingest_profiles(session, legislatures=["1990"])

    # Sitemap guids first, then historical; the overlapping guid (A) is ingested once.
    assert seen == [CURRENT_GUID_A, CURRENT_GUID_B, HIST_GUID_C]
    assert totals["profiles"] == 3
    assert totals["unchanged"] == 0
    # Historical discovery was triggered via POST to FisaSenatori.aspx.
    assert any(
        url.endswith("/FisaSenatori.aspx") and data.get("ddlLegislatura") == "1990"
        for url, data in client.post_calls
    )


def test_ingest_profiles_without_legislatures_is_sitemap_only(monkeypatch, session):
    client = FakeClient(_sitemap(CURRENT_GUID_A), "")
    source = SenatSource(client=client)
    seen: list[str] = []
    _install_ingest_stubs(monkeypatch, seen)

    totals = source.ingest_profiles(session)

    assert seen == [CURRENT_GUID_A]
    assert totals["profiles"] == 1
    # No historical discovery when legislatures is None.
    assert client.post_calls == []


def test_ingest_profiles_legacy_signature_still_works(monkeypatch, session):
    """Calling without the new keyword behaves exactly as before."""
    client = FakeClient(_sitemap(CURRENT_GUID_A), "")
    source = SenatSource(client=client)
    seen: list[str] = []
    _install_ingest_stubs(monkeypatch, seen)

    totals = source.ingest_profiles(session, force=True, limit=1)

    assert seen == [CURRENT_GUID_A]
    assert totals["profiles"] == 1
    assert client.post_calls == []
