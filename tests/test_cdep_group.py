from datetime import date
from pathlib import Path

import pytest

from pipeline.parse.cdep_group import parse_group_ledger

FX = Path(__file__).parent / "fixtures"


@pytest.fixture
def upr():
    return parse_group_ledger(
        (FX / "cdep_group_upr.html").read_text(encoding="utf-8"),
        chamber="deputies", legislature="2024",
        source_url="https://www.cdep.ro/ords/pls/parlam/structura2015.gp?cam=2&leg=2024&idg=9",
    )


@pytest.fixture
def psd():
    return parse_group_ledger(
        (FX / "cdep_group_psd.html").read_text(encoding="utf-8"),
        chamber="deputies", legislature="2024",
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