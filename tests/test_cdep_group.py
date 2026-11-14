from datetime import date
from pathlib import Path

import pytest

from pipeline.parse.cdep_group import parse_group_ledger

FX = Path(__file__).parent / "fixtures"


@pytest.fixture
def upr():
    return parse_group_ledger(
        (FX / "cdep_group_upr.html").read_text(encoding="utf-8"),
        chamber="deputies",
        legislature="2024",
        source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.gp?cam=2&leg=2024&idg=9",
    )


@pytest.fixture
def psd():
    return parse_group_ledger(
        (FX / "cdep_group_psd.html").read_text(encoding="utf-8"),
        chamber="deputies",
        legislature="2024",
    )


@pytest.fixture
def unaffiliated():
    return parse_group_ledger(
        (FX / "cdep_group_unaffiliated.html").read_text(encoding="utf-8"),
        chamber="deputies",
        legislature="2024",
    )


def test_upr_meta(upr):
    m = upr.meta
    assert m.short_name == "UPR"
    assert "Uniţi pentru România" in m.name or "Uniti" in m.name
    assert m.founding_date.earliest == date(2026, 5, 11)
    assert m.former_name is not None and "POT" in m.former_name


def test_upr_ponta_switch(upr):
    ponta = next(r for r in upr.current if "Ponta" in r.name)
    assert ponta.idm is not None
    assert ponta.party == "PSD"  # elected on PSD list, now in UPR group
    assert ponta.group_join.earliest == date(2026, 6, 15)


def test_upr_founder_leader(upr):
    leader = next(r for r in upr.current if r.role == "leader")
    assert "Chiriţă" in leader.name or "Chirita" in leader.name
    assert leader.role_start.earliest == date(2026, 5, 11)
    # Founder: no explicit join date (inferred at ingest from founding date).
    assert leader.group_join is None


def test_upr_former_member_intervals(upr):
    enachi = next(r for r in upr.former if "Enachi" in r.name)
    assert enachi.group_join.earliest == date(2026, 6, 15)
    assert enachi.group_leave.earliest == date(2026, 9, 14)
    # A founder who left: join empty, leave explicit.
    csillag = next(r for r in upr.former if "Csillag" in r.name)
    assert csillag.group_join is None
    assert csillag.group_leave.earliest == date(2026, 6, 2)


def test_upr_former_bureau(upr):
    groza = next(r for r in upr.former_bureau if "Groza" in r.name)
    assert groza.role == "secretary"
    assert groza.role_start.earliest == date(2026, 5, 11)
    assert groza.role_end.earliest == date(2026, 10, 5)


def test_psd_current_joiner(psd):
    chilat = next(r for r in psd.current if "Chilat" in r.name)
    assert chilat.group_join.earliest == date(2026, 9, 1)


def test_psd_former_ciolacu(psd):
    ciolacu = next(r for r in psd.former if "Ciolacu" in r.name)
    assert ciolacu.group_leave.earliest == date(2025, 12, 18)
    assert ciolacu.idm is not None


def test_psd_counts(psd):
    # Sanity: a large group has many current members and some former.
    assert len(psd.current) > 50
    assert len(psd.former) >= 3


def test_all_current_have_idm(upr):
    assert all(r.idm for r in upr.current)


def test_unaffiliated_deputies_are_ingested(unaffiliated):
    """Regression: the idg=0 page uses "Neafiliat din/până" headers.

    The classifier used to ignore that template, silently dropping all 15
    unaffiliated deputies (330 of 331 seats ingested). Counts come from the
    live page captured 2026-11-13.
    """
    assert len(unaffiliated.current) == 15
    assert len(unaffiliated.former) == 17
    assert all(r.party is None for r in unaffiliated.current)
    assert all(r.idm for r in unaffiliated.current)
    albu = next(r for r in unaffiliated.current if "Albu" in r.name)
    assert albu.group_join.earliest == date(2025, 5, 21)


@pytest.fixture
def fsn_1990():
    return parse_group_ledger(
        (FX / "cdep_group_1990_fsn.html").read_text(encoding="utf-8"),
        chamber="deputies",
        legislature="1990",
        source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.gp?cam=2&leg=1990&idg=1",
    )


@pytest.fixture
def psd_2020():
    return parse_group_ledger(
        (FX / "cdep_group_2020_psd.html").read_text(encoding="utf-8"),
        chamber="deputies",
        legislature="2020",
        source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.gp?cam=2&leg=2020&idg=1",
    )


def test_1990_two_column_former_table(fsn_1990):
    """Regression: the 1990/2020 former table has only Nume | Membru până.

    The parser required three cells and silently dropped every former member
    (55 in the 1990 FSN group). Counts are from the live page captured
    2026-11-13.
    """
    assert fsn_1990.meta.short_name == "FSN"
    assert len(fsn_1990.current) == 245
    assert len(fsn_1990.former) == 55
    assert fsn_1990.former[0].group_leave.earliest == date(1992, 5, 25)
    assert fsn_1990.former[0].group_join is None


def test_2020_two_column_former_table(psd_2020):
    """The 2020 PSD ledger uses the same two-column former shape as 1990."""
    assert psd_2020.meta.short_name == "PSD"
    assert len(psd_2020.current) == 103
    assert len(psd_2020.former) == 23
    assert all(r.group_leave is not None for r in psd_2020.former)
    assert all(r.group_join is None for r in psd_2020.former)
