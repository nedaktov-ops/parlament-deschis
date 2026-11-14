"""Parser tests for cdep.ro committee member pages (structura.co)."""


import pytest

from pipeline.parse.cdep_committee import parse_committee_ledger

FX = __import__("pathlib").Path(__file__).parent / "fixtures"


@pytest.fixture
def econ_2024():
    return parse_committee_ledger(
        (FX / "cdep_committee_2024_idc1.html").read_text(encoding="utf-8"),
        chamber="deputies",
        legislature="2024",
        source_url="https://www.cdep.ro/ords/pls/parlam/structura.co?idc=1&leg=2024",
    )


@pytest.fixture
def ec_1990():
    return parse_committee_ledger(
        (FX / "cdep_committee_1990_idc28.html").read_text(encoding="utf-8"),
        chamber="deputies",
        legislature="1990",
        source_url="https://www.cdep.ro/ords/pls/parlam/structura.co?idc=28&leg=1990",
    )


def test_meta_2024(econ_2024):
    m = econ_2024.meta
    assert m.name == "Comisia pentru politică economică, reformă şi privatizare"
    assert m.chamber == "deputies"
    assert m.legislature == "2024"


def test_meta_1990(ec_1990):
    m = ec_1990.meta
    assert m.chamber == "deputies"
    assert m.legislature == "1990"


def test_current_members_2024(econ_2024):
    assert len(econ_2024.current) == 25
    dunava = next(m for m in econ_2024.current if "Dunava" in m.name)
    assert dunava.idm == "97"
    assert dunava.role == "presedinte"
    assert dunava.role_start.iso() == "2025-03-19"
    assert dunava.group_name == "PSD"
    assert dunava.group_idg == "1"


def test_current_members_1990(ec_1990):
    assert len(ec_1990.current) == 22
    albu = next(m for m in ec_1990.current if "Albu" in m.name)
    assert albu.idm == "1"
    assert albu.role == "membri"
    assert albu.role_start is None  # 1990 template has no role start dates
    assert albu.group_name == "FSN"
    assert albu.group_idg == "1"


def test_former_members_2024(econ_2024):
    assert len(econ_2024.former) == 2
    cadar = next(m for m in econ_2024.former if "Cadar" in m.name)
    assert cadar.idm == "49"
    assert cadar.role_end.iso() == "2026-10-14"
    assert cadar.group_name == "PNL"
    assert cadar.group_idg == "3"


def test_former_members_1990(ec_1990):
    assert len(ec_1990.former) == 8
    albu = next(m for m in ec_1990.former if "Albu Gheorghe" in m.name)
    assert albu.idm == "2"
    assert albu.role_end.iso() == "1992-05-25"
    assert albu.group_name == "FSN"
    assert albu.group_idg == "1"
