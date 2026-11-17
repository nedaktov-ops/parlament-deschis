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
from pipeline.sources.senat import HistoricalDiscoveryError, SenatSource

FX = Path(__file__).parent / "fixtures"

CURRENT_GUID_A = "007FDD23-B531-407E-A067-9C3796420C8C"  # also in the historical page
CURRENT_GUID_B = "3354F56C-A3E7-4CEA-9DDE-E3BD730D7B7F"
HIST_GUID_C = "11111111-2222-3333-4444-555555555555"
# A second legislature must yield a DIFFERENT GUID set: the cross-legislature
# guard raises HistoricalDiscoveryError when two sets are identical (the
# silent wrong-data bug this flow exists to prevent).
HIST_GUID_D = "22222222-3333-4444-5555-666666666666"

# Legislature dropdown as the live FisaSenatori.aspx page publishes it: the
# option VALUE is what gets POSTed (a GUID on the live site), the LABEL's
# leading year is the key callers use ("1990").
FISA_PAGE = (
    '<select name="ctl00$B_Center$ddLegislatura">'
    '<option value="1990">1990 - 1992</option>'
    '<option value="2024">2024 - present</option>'
    "</select>"
)
# Step 1 (legislature POST) repopulates the session dropdown.
SESSION_PAGE = (
    '<select name="ctl00$B_Center$ddSesiune"><option value="sess-1">1990 - 1992</option></select>'
)


@dataclass
class FakeResult:
    url: str
    status: int = 200
    text: str = ""


class FakeClient:
    """Records get/post calls and returns canned responses. Never touches the network.

    FisaSenatori.aspx POSTs follow the live two-step flow the source now
    implements:

    * step 1 — legislature GUID, no ``__EVENTTARGET``: the response must
      repopulate ``ddSesiune`` (session dropdown);
    * step 2 — session GUID + ``__EVENTTARGET`` search: the response carries
      the senator-card links.

    ``historical_text`` may be a str (same cards for every legislature) or a
    dict keyed by the posted legislature — the cross-legislature guard raises
    when two legislatures yield identical GUID sets, so tests that request two
    legislatures must hand back distinct sets.
    """

    def __init__(
        self,
        sitemap_text: str,
        historical_text: str | dict[str, str],
        fisa_page_text: str = "",
        session_page_text: str | None = None,
    ):
        self.get_calls: list[str] = []
        self.post_calls: list[tuple[str, dict]] = []
        self.sitemap_text = sitemap_text
        self.historical_text = historical_text
        self.fisa_page_text = fisa_page_text
        self.session_page_text = session_page_text or SESSION_PAGE

    def get(self, url, **kwargs):
        self.get_calls.append(url)
        if url.endswith("/sitemap.xml"):
            return FakeResult(url, 200, self.sitemap_text)
        if url.endswith("/FisaSenatori.aspx"):
            return FakeResult(url, 200, self.fisa_page_text)
        return FakeResult(url, 200, "<html></html>")

    def post(self, url, *, data=None, **kwargs):
        data = dict(data or {})
        self.post_calls.append((url, data))
        if url.endswith("/FisaSenatori.aspx"):
            if "__EVENTTARGET" in data:  # step 2: render the senator cards
                leg = data.get("ctl00$B_Center$ddLegislatura", "")
                body = (
                    self.historical_text.get(leg, "")
                    if isinstance(self.historical_text, dict)
                    else self.historical_text
                )
                return FakeResult(url, 200, body)
            return FakeResult(url, 200, self.session_page_text)  # step 1
        return FakeResult(
            url,
            200,
            self.historical_text if isinstance(self.historical_text, str) else "",
        )

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
    client = FakeClient("", historical, fisa_page_text=FISA_PAGE)
    source = SenatSource(client=client)

    guids = source.fetch_historical_guids(["1990"])

    assert CURRENT_GUID_A in guids
    assert HIST_GUID_C in guids
    # Step 1 POSTed the legislature dropdown value (option value "1990").
    assert any(
        url.endswith("/FisaSenatori.aspx")
        and data.get("ctl00$B_Center$ddLegislatura") == "1990"
        and "__EVENTTARGET" not in data
        for url, data in client.post_calls
    )
    # Step 2 triggered the search via __EVENTTARGET (the live two-step flow).
    assert any("__EVENTTARGET" in data for _, data in client.post_calls)


def test_fetch_historical_guids_none_discovers_labels_from_page(monkeypatch):
    """``legislatures=None`` reads the legislature dropdown then runs the
    two-step flow for each discovered legislature."""
    historical = {
        "1990": f'<a href="FisaSenator.aspx?ParlamentarID={HIST_GUID_C}">C</a>',
        "2024": f'<a href="FisaSenator.aspx?ParlamentarID={HIST_GUID_D}">D</a>',
    }
    client = FakeClient("", historical, fisa_page_text=FISA_PAGE)
    source = SenatSource(client=client)

    guids = source.fetch_historical_guids()

    assert HIST_GUID_C in guids
    assert HIST_GUID_D in guids
    # Two legislatures x two steps (refresh + search) = 4 POSTs.
    assert len(client.post_calls) == 4
    # Both discovered legislature values were POSTed in step 1.
    step1_legs = {
        data.get("ctl00$B_Center$ddLegislatura")
        for _, data in client.post_calls
        if "__EVENTTARGET" not in data
    }
    assert step1_legs == {"1990", "2024"}


def test_fetch_historical_guids_identical_sets_raise(monkeypatch):
    """The cross-legislature guard: identical GUID sets = silent wrong-data."""
    same = f'<a href="FisaSenator.aspx?ParlamentarID={HIST_GUID_C}">C</a>'
    # Both legislatures return the SAME card page — exactly the bug the guard
    # exists for (old flow returned one legislature's senators for every year).
    client = FakeClient("", same, fisa_page_text=FISA_PAGE)
    source = SenatSource(client=client)

    with pytest.raises(HistoricalDiscoveryError):
        source.fetch_historical_guids(["1990", "2024"])


def test_ingest_profiles_with_legislatures_ingests_historical_and_dedupes(monkeypatch, session):
    historical = (FX / "senat_fisa_senatori_1990.html").read_text(encoding="utf-8")
    client = FakeClient(
        _sitemap(CURRENT_GUID_A, CURRENT_GUID_B),
        historical,
        fisa_page_text=FISA_PAGE,
    )
    source = SenatSource(client=client)
    seen: list[str] = []
    _install_ingest_stubs(monkeypatch, seen)

    totals = source.ingest_profiles(session, legislatures=["1990"])

    # Sitemap guids first, then historical; the overlapping guid (A) is ingested once.
    assert seen == [CURRENT_GUID_A, CURRENT_GUID_B, HIST_GUID_C]
    assert totals["profiles"] == 3
    assert totals["unchanged"] == 0
    # Historical discovery ran the two-step FisaSenatori flow for 1990.
    assert any(
        url.endswith("/FisaSenatori.aspx") and data.get("ctl00$B_Center$ddLegislatura") == "1990"
        for url, data in client.post_calls
    )
    assert any("__EVENTTARGET" in data for _, data in client.post_calls)


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
