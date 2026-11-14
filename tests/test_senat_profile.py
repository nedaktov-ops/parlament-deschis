from datetime import date
from pathlib import Path

import pytest

from pipeline.parse.senat_grup import parse_group_roster
from pipeline.parse.senat_profile import parse_senator_profile

FX = Path(__file__).parent / "fixtures"


@pytest.fixture
def neafiliat():
    return parse_senator_profile(
        (FX / "senat_fisa.html").read_text(encoding="utf-8"),
        guid="007FDD23-B531-407E-A067-9C3796420C8C",
        profile_url="https://www.senat.ro/FisaSenator.aspx?ParlamentarID=007FDD23-B531-407E-A067-9C3796420C8C",
    )


@pytest.fixture
def udhr():
    return parse_senator_profile(
        (FX / "senat_fisa_udmr.html").read_text(encoding="utf-8"),
        guid="3354F56C-A3E7-4CEA-9DDE-E3BD730D7B7F",
    )


def test_name_and_constituency(neafiliat):
    assert neafiliat.name == "Ninel PEIA"
    assert neafiliat.constituency_nr == 31
    assert "Prahova" in neafiliat.constituency_name
    assert neafiliat.election_date.earliest == date(2024, 12, 1)
    assert neafiliat.validation_date.earliest == date(2024, 12, 21)
    assert neafiliat.legislature == "2024"


def test_unaffiliated_party(neafiliat):
    assert neafiliat.party is None
    assert neafiliat.group is not None and "neafilia" in neafiliat.group.lower()


def test_current_committee(neafiliat):
    cur = [m for m in neafiliat.memberships if m.is_current and m.org_class == "committee"]
    assert any("energie" in m.org_name for m in cur)
    energie = next(m for m in cur if "energie" in m.org_name)
    assert energie.role == "Membru"
    assert energie.start.earliest == date(2024, 12, 21)
    assert energie.end is None


def test_friendship_with_role(neafiliat):
    fr = [m for m in neafiliat.memberships if m.org_class == "friendship" and m.is_current]
    vietnam = next(m for m in fr if "Vietnam" in m.org_name)
    assert vietnam.role == "Secretar"
    assert vietnam.start.earliest == date(2025, 3, 25)


def test_bureau_history_intervals(neafiliat):
    hist = [m for m in neafiliat.memberships if m.org_class == "bureau" and not m.is_current]
    assert len(hist) == 2
    first = next(m for m in hist if m.start.earliest == date(2024, 12, 21))
    assert first.role == "Chestor"
    assert first.end.earliest == date(2025, 8, 31)


def test_committee_history_closed(neafiliat):
    hist = [m for m in neafiliat.memberships if m.org_class == "committee" and not m.is_current]
    transport = next(m for m in hist if "transporturi" in m.org_name)
    assert transport.start.earliest == date(2024, 12, 21)
    assert transport.end.earliest == date(2026, 11, 9)


def test_udmr_party_and_group(udhr):
    assert udhr.name == "TUROS Lóránd"
    assert udhr.party is not None and "Maghiară" in udhr.party
    assert udhr.group is not None and "Uniunii Democrate Maghiare" in udhr.group
    assert udhr.group_role == "Lider"


def test_multi_mandate_legislature_is_current(udhr):
    """Regression: senat.ro lists mandates oldest-first (2016, 2020, 2024).

    Taking the first match stamped every returning senator with legislature
    2016, so they vanished from the current term.
    """
    assert udhr.legislature == "2024"


def test_group_roster():
    roster = parse_group_roster((FX / "senat_grup.html").read_text(encoding="utf-8"))
    assert roster.group_name is not None and "Uniunii Democrate Maghiare" in roster.group_name
    assert len(roster.members) == 10
    assert all(m.guid and m.name for m in roster.members)
    assert any("TUROS" in m.name for m in roster.members)
