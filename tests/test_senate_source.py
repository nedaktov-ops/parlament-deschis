"""Behavioural tests for Senate historical discovery.

The previous version of this module was vacuous: it asserted bare class
objects (``assert HistoricalDiscoveryError``) and used ``pass``, so it could
never fail no matter how broken discovery became. Every test here drives
:class:`SenatSource` through the no-network ``FakeClient`` defined in
``tests/test_senat_source.py`` and checks the GUIDs and two-step POST flow that
actually come back. The captured 1990 fixture holds two senator cards, not the
128/134 live counts, so cross-legislature distinctness is asserted from fakes.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from pipeline.sources.senat import HistoricalDiscoveryError, SenatSource
from tests.test_senat_source import (
    CURRENT_GUID_A,
    FISA_PAGE,
    HIST_GUID_C,
    HIST_GUID_D,
    FakeClient,
)

GUID_RE = re.compile(r"^[0-9A-Fa-f-]{36}$")
FIXTURE_1990 = (Path(__file__).parent / "fixtures" / "senat_fisa_senatori_1990.html").read_text(
    encoding="utf-8"
)
PAGE_2024 = f'<a href="FisaSenator.aspx?ParlamentarID={HIST_GUID_D}">D</a>'
BY_LEG = {"1990": FIXTURE_1990, "2024": PAGE_2024}


def test_historical_discovery_error_is_raisable_and_catchable():
    """The guard class is a real, catchable RuntimeError subclass."""
    with pytest.raises(HistoricalDiscoveryError, match="sentinel"):
        raise HistoricalDiscoveryError("sentinel")


def test_1990_guids_live_provenance():
    """The captured 1990 FisaSenatori page yields exactly its senator GUIDs."""
    client = FakeClient("", FIXTURE_1990, fisa_page_text=FISA_PAGE)
    guids = SenatSource(client=client).fetch_historical_guids(["1990"])

    # Behavioural: the two distinct senator-card GUIDs in the fixture come back,
    # and every returned id is GUID-shaped (no labels, no empty rows).
    assert set(guids) == {CURRENT_GUID_A, HIST_GUID_C}
    assert len(guids) == 2
    assert all(GUID_RE.match(g) for g in guids)
    # The two-step flow really ran for the requested legislature.
    assert any(
        data.get("ctl00$B_Center$ddLegislatura") == "1990" and "__EVENTTARGET" not in data
        for _, data in client.post_calls
    )
    assert any("__EVENTTARGET" in data for _, data in client.post_calls)


def test_2024_guids_live_provenance():
    """2024 resolves to its own GUID set; 1990's senators do not leak in."""
    client = FakeClient("", BY_LEG, fisa_page_text=FISA_PAGE)
    guids = SenatSource(client=client).fetch_historical_guids(["2024"])

    assert set(guids) == {HIST_GUID_D}
    assert HIST_GUID_C not in guids
    assert all(GUID_RE.match(g) for g in guids)
    assert any(data.get("ctl00$B_Center$ddLegislatura") == "2024" for _, data in client.post_calls)


def test_cross_legislature_guids_differ():
    """Two legislatures from the same fakes return disjoint GUID sets.

    The old bug returned one legislature's 134 GUIDs for every year; if the
    sets were identical the production guard must fire. Here they differ, so
    no guard is raised and each set is the other's complement.
    """
    client = FakeClient("", BY_LEG, fisa_page_text=FISA_PAGE)
    source = SenatSource(client=client)
    guids_1990 = set(source.fetch_historical_guids(["1990"]))
    guids_2024 = set(source.fetch_historical_guids(["2024"]))

    assert guids_1990 == {CURRENT_GUID_A, HIST_GUID_C}
    assert guids_2024 == {HIST_GUID_D}
    assert guids_1990.isdisjoint(guids_2024)

    # Same-card fakes (the silent wrong-data scenario) must raise the guard.
    same = f'<a href="FisaSenator.aspx?ParlamentarID={HIST_GUID_C}">C</a>'
    with pytest.raises(HistoricalDiscoveryError):
        SenatSource(client=FakeClient("", same, fisa_page_text=FISA_PAGE)).fetch_historical_guids(
            ["1990", "2024"]
        )


def test_source_instantiates_with_injected_client():
    """The source can be constructed with a client and exposes the flow."""
    client = FakeClient("", BY_LEG, fisa_page_text=FISA_PAGE)
    source = SenatSource(client=client)
    assert source.client is client


def test_labels_return_year_to_post_value_dict():
    """``_historical_legislature_labels`` maps years to dropdown values."""
    source = SenatSource(client=FakeClient("", FIXTURE_1990, fisa_page_text=FISA_PAGE))
    mapping = source._historical_legislature_labels()

    assert isinstance(mapping, dict)
    assert mapping == {"1990": "1990", "2024": "2024"}
