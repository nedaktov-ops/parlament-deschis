"""Regression tests for the cdep MP profile parser.

The profile's "Mandate parlamentar" block is the only stable cross-mandate
identity on cdep.ro: ``idm`` is per-mandate, so the links are what let us join
the same person across legislatures and across chambers. Fixtures are live
captures from 2026-11-13.
"""

from datetime import date
from pathlib import Path

from pipeline.parse.cdep_profile import parse_deputy_profile

FX = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FX / name).read_text(encoding="utf-8")


def test_deputy_profile_identity_and_mandate_graph():
    prof = parse_deputy_profile(
        _load("cdep_profile_deputy_2016.html"),
        idm="16",
        legislature="2016",
        chamber="deputies",
        profile_url="https://www.cdep.ro/ords/pls/parlam/structura2015.mp?idm=16&cam=2&leg=2016",
    )
    assert prof.name == "Radu BABUŞ"
    assert prof.birth_date.earliest == date(1978, 11, 18)
    assert prof.validation_date.earliest == date(2016, 12, 21)
    assert (prof.constituency_nr, prof.constituency_name) == ("14", "CONSTANŢA")
    assert prof.party == "Partidul Social Democrat"
    assert prof.group == "Grupul parlamentar al Partidului Social Democrat"
    assert prof.group_role == "Vicelider"
    # The graph must contain the current mandate and the earlier 2012 one.
    assert {m.key for m in prof.mandates} == {
        "deputies:2012:20",
        "deputies:2016:16",
    }


def test_senator_profile_links_three_mandates():
    """Bodog served 2012, 2016 and 2020: the links are per-mandate GUIDs."""
    prof = parse_deputy_profile(
        _load("cdep_profile_senator_2020.html"),
        idm="14",
        legislature="2020",
        chamber="senate",
        profile_url="https://www.cdep.ro/ords/pls/parlam/structura2015.mp?idm=14&cam=1&leg=2020",
    )
    assert prof.name == "Florian-Dorel BODOG"
    assert prof.birth_date.earliest == date(1971, 9, 6)
    assert {m.key for m in prof.mandates} == {
        "senate:2012:24",
        "senate:2016:13",
        "senate:2020:14",
    }


def test_single_mandate_profile_does_not_invent_links():
    prof = parse_deputy_profile(
        _load("cdep_profile_senator_2016.html"),
        idm="103",
        legislature="2016",
        chamber="senate",
        profile_url="https://www.cdep.ro/ords/pls/parlam/structura2015.mp?idm=103&cam=1&leg=2016",
    )
    assert prof.name == "Radu-Cosmin PREDA"
    assert {m.key for m in prof.mandates} == {"senate:2016:103"}
