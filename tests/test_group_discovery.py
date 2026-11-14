from pathlib import Path

import pytest

from pipeline.collect import _is_group_ledger_page
from pipeline.parse.cdep_group import parse_group_ledger, parse_group_list

CACHE = Path(__file__).resolve().parents[1] / "data" / "cache" / "cdep" / "deputies" / "2016"

if not (CACHE / "group_5.html").exists() or not (CACHE / "list.html").exists():
    pytest.skip("requires the optional archived cdep corpus", allow_module_level=True)


def test_real_group_page_is_not_mistaken_for_generic_index():
    group_page = (CACHE / "group_5.html").read_text(encoding="utf-8", errors="replace")
    index_page = (CACHE / "list.html").read_text(encoding="utf-8", errors="replace")

    assert _is_group_ledger_page(group_page) is True
    assert _is_group_ledger_page(index_page) is False


def test_2016_index_omits_alde_but_cached_ledger_contains_its_members():
    index_page = (CACHE / "list.html").read_text(encoding="utf-8", errors="replace")
    index_items = parse_group_list(index_page)
    assert "5" not in {item.idg for item in index_items}
    assert all(item.short_name != "ALDE" for item in index_items)

    group_page = (CACHE / "group_5.html").read_text(encoding="utf-8", errors="replace")
    ledger = parse_group_ledger(
        group_page,
        chamber="deputies",
        legislature="2016",
        source_url=str(CACHE / "group_5.html"),
    )

    # Exact counts observed in the cached page captured from cdep.ro:
    # 40 former-member rows, 25 distinct former members, 15 former-bureau rows,
    # and no current-member rows after the group ceased activity.
    assert ledger.meta.short_name == "ALDE"
    assert len(ledger.current) == 0
    assert len(ledger.former) == 40
    assert len({row.idm for row in ledger.former if row.idm}) == 25
    assert len(ledger.former_bureau) == 15
