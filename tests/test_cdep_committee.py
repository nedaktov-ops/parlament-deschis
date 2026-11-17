"""Parser tests for cdep.ro committee listing and member pages (structura.co).

All fixtures are offline. ``*_live.html`` files are trimmed copies of pages
captured from cdep.ro on 2026-11-15: the trim keeps the committee ``<h1>``
sequence and the member tables (ledgers) or the anchor list (listing) verbatim
and drops the site chrome. The trim was verified to produce a byte-identical
parse result to the untrimmed capture. The two undated fixtures are the older
page template, kept to prove the parser still accepts the legacy
``structura.co`` / ``structura.mp`` URL forms and pages without ``<h1>``.
"""

import pytest

from pipeline.parse.cdep_committee import parse_committee_ledger
from pipeline.sources.cdep_committee import parse_committee_list

FX = __import__("pathlib").Path(__file__).parent / "fixtures"

COMMITTEE_2024 = "Comisia pentru politică economică, reformă şi privatizare"


def _ledger(name, legislature):
    return parse_committee_ledger(
        (FX / name).read_text(encoding="utf-8"),
        chamber="deputies",
        legislature=legislature,
        source_url=f"https://www.cdep.ro/ords/pls/parlam/structura2015.co?cam=2&idl=1&leg={legislature}",
    )


@pytest.fixture
def econ_2024():
    """Live 2024 page, ``idc=1`` (economic policy committee)."""
    return _ledger("cdep_committee_2024_idc1_live.html", "2024")


@pytest.fixture
def ec_1990():
    """Live 1990 page, ``idc=51`` (economic committee)."""
    return _ledger("cdep_committee_1990_idc51_live.html", "1990")


@pytest.fixture
def econ_2024_legacy():
    """2024 page in the legacy ``structura.mp`` / footnote-span template."""
    return _ledger("cdep_committee_2024_idc1.html", "2024")


@pytest.fixture
def ec_1990_legacy():
    """1990 page in the legacy template (no ``<h1>``, no date columns)."""
    return _ledger("cdep_committee_1990_idc28.html", "1990")


# --- committee listing ----------------------------------------------------


def test_list_2024_live_count_and_names():
    items = parse_committee_list(
        (FX / "cdep_committee_list_2024_live.html").read_text(encoding="utf-8")
    )
    assert len(items) == 26
    assert [(i.idc, i.name) for i in items[:3]] == [
        ("1", COMMITTEE_2024),
        ("2", "Comisia pentru buget, finanţe şi bănci"),
        ("3", "Comisia pentru industrii şi servicii"),
    ]
    # De-duplicated ids, all numeric.
    assert len({i.idc for i in items}) == len(items)
    assert all(i.idc.isdigit() for i in items)


def test_list_1990_live_count_and_names():
    items = parse_committee_list(
        (FX / "cdep_committee_list_1990_live.html").read_text(encoding="utf-8")
    )
    assert len(items) == 18
    assert (items[0].idc, items[0].name) == ("51", "Comisia economică")
    # 1990 uses different idc values from 2024 for the same subject matter.
    assert "52" in {i.idc for i in items}


def test_list_legacy_url_form_still_parsed():
    """The pre-2015 ``structura.co`` listing links must keep working."""
    items = parse_committee_list((FX / "cdep_committee_list_2024.html").read_text(encoding="utf-8"))
    assert len(items) == 26
    assert items[0].name == COMMITTEE_2024
    legacy_1990 = parse_committee_list(
        (FX / "cdep_committee_list_1990.html").read_text(encoding="utf-8")
    )
    assert len(legacy_1990) == 18


def test_list_decodes_entities_and_collapses_whitespace():
    html = """
    <html><body>
      <a href="/ords/pls/parlam/structura2015.co?cam=2&amp;idl=1&amp;leg=2024&amp;idc=71">
        Comisia pentru constitu&#539;ionalitate
      </a>
      <a href="/ords/pls/parlam/structura2015.co?cam=2&amp;idl=1&amp;leg=2024&amp;idc=72">
        Comisia   pentru <b>&#537;tiin&#539;ă</b> &#537;i tehnologie
      </a>
      <a href="/ords/pls/parlam/structura2015.co?leg=2024&amp;idc=&amp;prn=1"
         title="Print"></a>
    </body></html>
    """
    items = parse_committee_list(html)
    assert [(i.idc, i.name) for i in items] == [
        ("71", "Comisia pentru constituționalitate"),
        ("72", "Comisia pentru știință și tehnologie"),
    ]


def test_list_dedupes_by_idc_keeping_first_name():
    html = """
    <html><body>
      <a href="structura.co?cam=2&amp;idl=1&amp;leg=2024&amp;idc=5">First</a>
      <a href="structura2015.co?cam=2&amp;idl=1&amp;leg=2024&amp;idc=5">Second</a>
      <a href="structura2015.co?cam=2&amp;idl=1&amp;leg=2024&amp;idc=6">Other</a>
    </body></html>
    """
    items = parse_committee_list(html)
    assert [(i.idc, i.name) for i in items] == [("5", "First"), ("6", "Other")]


def test_list_ignores_unrelated_links():
    html = """
    <html><body>
      <a href="/ords/pls/parlam/structura2015.home?leg=2024&amp;cam=2">Home</a>
      <a href="/ords/pls/parlam/structura2015.mp?idm=97&amp;cam=2&amp;leg=2024">Deputy</a>
      <a href="/ords/pls/parlam/structura2015.co?cam=2&amp;idl=1&amp;leg=2024&amp;idc=9">
        Comisia pentru învăţământ</a>
    </body></html>
    """
    assert [i.idc for i in parse_committee_list(html)] == ["9"]


# --- committee ledger: metadata -------------------------------------------


def test_meta_2024_live(econ_2024):
    m = econ_2024.meta
    assert m.name == COMMITTEE_2024
    assert m.chamber == "deputies"
    assert m.legislature == "2024"


def test_meta_1990_live(ec_1990):
    """The name is the ``<h1>`` after "Activitate comisie", not the menu."""
    m = ec_1990.meta
    assert m.name == "Comisia economică"
    assert m.legislature == "1990"


def test_meta_legacy_without_h1(econ_2024_legacy, ec_1990_legacy):
    assert econ_2024_legacy.meta.name == COMMITTEE_2024
    # "Comisia de validare" never matched the old "comisia pentru" rule.
    assert ec_1990_legacy.meta.name == "Comisia de validare"


# --- committee ledger: current members ------------------------------------


def test_current_members_2024_live(econ_2024):
    assert len(econ_2024.current) == 22
    dunava = next(m for m in econ_2024.current if "Dunava" in m.name)
    assert dunava.idm == "97"
    assert dunava.role == "presedinte"
    assert dunava.role_start.iso() == "2025-03-19"
    assert dunava.group_name == "PSD"
    assert dunava.group_idg == "1"
    assert dunava.profile_url.endswith("structura2015.mp?idm=97&cam=2&leg=2024")
    # One row per deputy: nobody is repeated in the current list.
    assert len({m.idm for m in econ_2024.current}) == len(econ_2024.current)
    # The bureau table's former office-holder is not a current member row.
    assert not any("Ponta" in m.name for m in econ_2024.current)


def test_role_start_parsed_from_text_after_br(econ_2024):
    buican = next(m for m in econ_2024.current if "Buican" in m.name)
    assert buican.role_start.iso() == "2026-10-12"


def test_current_members_1990_live(ec_1990):
    assert len(ec_1990.current) == 41
    albu = next(m for m in ec_1990.current if "Albu Alexandru" in m.name)
    assert albu.idm == "1"
    assert albu.role == "membri"
    assert albu.role_start is None  # the 1990 template publishes no start dates
    assert albu.group_name == "FSN"
    assert albu.group_idg == "1"


# --- committee ledger: former members -------------------------------------


def test_former_members_2024_live(econ_2024):
    assert len(econ_2024.former) == 2
    cadar = next(m for m in econ_2024.former if "Cadar" in m.name)
    assert cadar.idm == "49"
    assert cadar.role is None
    assert cadar.role_start is None
    assert cadar.role_end.iso() == "2026-10-14"
    assert cadar.group_name == "PNL"
    assert cadar.group_idg == "3"
    ponta = next(m for m in econ_2024.former if "Ponta" in m.name)
    assert ponta.role_end.iso() == "2025-04-02"


def test_former_members_1990_live(ec_1990):
    assert len(ec_1990.former) == 8
    bivolaru = next(m for m in ec_1990.former if "Bivolaru" in m.name)
    assert bivolaru.idm == "35"
    assert bivolaru.role_end.iso() == "1992-03-05"
    assert bivolaru.group_name == "PNL"


# --- committee ledger: bureau history -------------------------------------


def test_former_bureau_rows_carry_role_and_dates(econ_2024):
    """Bureau rows are a role history: kept out of current/former membership."""
    assert len(econ_2024.former_bureau) == 3
    by_name = {m.name: m for m in econ_2024.former_bureau}
    ponta = by_name["Ponta Victor-Viorel"]
    assert ponta.idm == "248"
    assert ponta.role_start.iso() == "2024-12-23"
    assert ponta.role_end.iso() == "2025-03-19"
    assert ponta.group_name == "UPR"
    dunava = by_name["Dunava Costel Neculai"]
    assert dunava.role == "presedinte"
    assert dunava.role_start is None  # blank "din data" cell, never inferred
    assert dunava.role_end.iso() == "2024-12-23"
    scarlat = by_name["Scarlat George"]
    assert scarlat.role == "vicepresedinti"
    assert scarlat.role_end.iso() == "2026-10-12"


def test_1990_live_page_has_no_bureau_table(ec_1990):
    assert ec_1990.former_bureau == []


# --- committee ledger: legacy template ------------------------------------


def test_legacy_template_2024(econ_2024_legacy):
    """``structura.mp`` links and footnote-span role dates still parse."""
    assert len(econ_2024_legacy.current) == 22
    assert len(econ_2024_legacy.former) == 2
    assert len(econ_2024_legacy.former_bureau) == 3
    dunava = next(m for m in econ_2024_legacy.current if "Dunava" in m.name)
    assert dunava.profile_url.startswith("/ords/pls/parlam/structura.mp?idm=97")
    assert dunava.role_start.iso() == "2025-03-19"


def test_legacy_template_1990(ec_1990_legacy):
    assert len(ec_1990_legacy.current) == 22
    assert len(ec_1990_legacy.former) == 8
    albu = next(m for m in ec_1990_legacy.current if "Albu Alexandru" in m.name)
    assert albu.role_start is None
