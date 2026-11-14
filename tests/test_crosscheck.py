"""Cross-check of current membership against the roster and the index count.

Uses the real cached pages:

* deputies 2020, AUR group_4: the page lists 25 current members, the index
  publishes 23. Dămureanu Ringo (idm=89) and Scripnic Lilian (idm=261) sit
  in the page with an empty party cell; the roster puts both in idg=0
  (Neafiliați). 25 − 2 = 23 = published, so both stale rows are removed.
* senate 2020, PNL group_2: the page lists 35 current members, the index
  publishes 34. Voiculescu Liviu-Dumitru (idm=134) sits in the page with a
  PSD party cell; the roster puts him in idg=1 (PSD). 35 − 1 = 34 =
  published, so the stale row is removed.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pipeline.collect import Corpus, LedgerRecord
from pipeline.crosscheck import reconcile_current_membership
from pipeline.parse.cdep_group import parse_group_ledger
from pipeline.parse.cdep_roster import parse_roster

CACHE = Path("data/cache/cdep")


def _ledger(chamber: str, legislature: str, idg: str) -> LedgerRecord:
    cam = {"deputies": "2", "senate": "1"}[chamber]
    html = (CACHE / chamber / legislature / f"group_{idg}.html").read_text(encoding="utf-8")
    ledger = parse_group_ledger(
        html,
        chamber=chamber,
        legislature=legislature,
        source_url=(
            f"https://www.cdep.ro/ords/pls/parlam/structura2015.gp"
            f"?cam={cam}&leg={legislature}&idg={idg}"
        ),
    )
    return LedgerRecord(
        chamber=chamber,
        legislature=legislature,
        idg=idg,
        url=(
            f"https://www.cdep.ro/ords/pls/parlam/structura2015.gp"
            f"?cam={cam}&leg={legislature}&idg={idg}"
        ),
        sha256="test",
        ledger=ledger,
        fetched_at=datetime.now(UTC),
    )


def _roster(chamber: str, legislature: str):
    cam = {"deputies": "2", "senate": "1"}[chamber]
    html = (CACHE / chamber / legislature / "roster.html").read_text(encoding="utf-8")
    return parse_roster(
        html,
        chamber=chamber,
        legislature=legislature,
        source_url=(
            f"https://www.cdep.ro/ords/pls/parlam/structura2015.de"
            f"?par=A&cam={cam}&leg={legislature}"
        ),
    )


def test_reconcile_removes_exactly_the_stale_rows():
    corpus = Corpus()
    corpus.ledgers = [
        _ledger("deputies", "2020", "4"),  # AUR
        _ledger("senate", "2020", "2"),  # PNL
    ]
    corpus.rosters = [
        _roster("deputies", "2020"),
        _roster("senate", "2020"),
    ]
    # The group index publishes these counts; new template uses aria-label so
    # parse_group_list does not extract them — construct the map directly.
    corpus.index_counts = {
        ("deputies", "2020"): {"4": 23},  # AUR publishes 23
        ("senate", "2020"): {"2": 34},  # PNL publishes 34
    }

    report = reconcile_current_membership(corpus)

    # Both groups had agree == published, so both are reconciled.
    assert report.checked_groups == 2
    assert report.reconciled_groups == 2
    assert report.unresolved == []

    # Exactly three stale rows removed.
    assert len(report.exclusions) == 3
    excluded_names = {e.name for e in report.exclusions}
    assert "Dămureanu Ringo" in excluded_names
    assert "Scripnic Lilian" in excluded_names
    assert "Voiculescu Liviu-Dumitru" in excluded_names

    # All removals come from the current table (not name_only).
    for e in report.exclusions:
        assert e.reason, f"exclusion {e.name} has no reason"
        assert e.chamber in ("deputies", "senate")
        assert e.legislature == "2020"

    # The AUR page no longer contains the two removed rows.
    aur = next(r for r in corpus.ledgers if r.idg == "4")
    remaining_names = {row.name for row in aur.ledger.current if row.name}
    assert "Dămureanu Ringo" not in remaining_names
    assert "Scripnic Lilian" not in remaining_names

    # The PNL page no longer contains the removed row.
    pnl = next(r for r in corpus.ledgers if r.idg == "2")
    remaining_names = {row.name for row in pnl.ledger.current if row.name}
    assert "Voiculescu Liviu-Dumitru" not in remaining_names
