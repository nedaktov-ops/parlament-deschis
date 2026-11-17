from pathlib import Path

import pytest

from pipeline.parse.cdep_roster import parse_roster

ROSTER = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "cache"
    / "cdep"
    / "deputies"
    / "2016"
    / "roster.html"
)

if not ROSTER.exists():
    # P5-F: intentional skip - data/cache/cdep is gitignored and no trimmed
    # fixture is checked in; the optional archived cdep corpus is required.
    pytest.skip("requires the optional archived cdep corpus", allow_module_level=True)


def test_parse_cached_2016_deputy_roster():
    roster = parse_roster(
        ROSTER.read_text(encoding="utf-8", errors="replace"),
        chamber="deputies",
        legislature="2016",
        source_url=("https://www.cdep.ro/ords/pls/parlam/structura2015.de?par=A&cam=2&leg=2016"),
    )

    assert roster.chamber == "deputies"
    assert roster.legislature == "2016"
    assert roster.current
    assert roster.former
    assert all(row.group for row in roster.current)
    assert all(row.group for row in roster.former)
    assert any(row.join is not None for row in roster.current)
    assert all(row.leave is not None for row in roster.former)
    assert all(row.leave is None for row in roster.current)


def test_known_member_is_present_with_group_and_dates():
    roster = parse_roster(
        ROSTER.read_text(encoding="utf-8", errors="replace"),
        chamber="deputies",
        legislature="2016",
        source_url=("https://www.cdep.ro/ords/pls/parlam/structura2015.de?par=A&cam=2&leg=2016"),
    )

    anton = next(row for row in roster.current if row.name == "Anton Anton")
    assert anton.idm == "11"
    assert anton.group == "PSD"
    assert anton.constituency == "42 / BUCUREŞTI"

    ampleev = next(row for row in roster.current if row.name == "Ampleev Andrian")
    assert ampleev.group == "Minoritati"
    assert ampleev.join is not None
    assert ampleev.join.earliest.isoformat() == "2018-09-12"
