"""Parse the alphabetical roster of a legislature.

The roster (``structura2015.de?par=A&cam=…&leg=…``) lists every member of a
chamber in one legislature with their constituency, their parliamentary group
and the dates of that membership. It is published from the same database as
the group ledgers but through a different view, which makes it a genuine
cross-check: a member who appears in the roster but in no group ledger is a
member the ledgers lost.

Two tables are published: the members currently sitting in the legislature,
and the members who have left their group.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

from .cdep_group import parse_ro_date


@dataclass
class RosterRow:
    """One member as published by the roster."""

    idm: str | None
    name: str
    constituency: str | None
    group: str | None
    # The group the chamber publishes as a link carries the group id in its
    # href (".../structura2015.gp?idg=11&leg=1992"). That id is the exact
    # join key between this view and the group ledgers; the visible label
    # varies between the legislature templates (a name in some, the bare
    # number in others).
    group_id: str | None = None
    join: object | None = None  # ApproxDate | None
    leave: object | None = None  # ApproxDate | None


@dataclass
class Roster:
    chamber: str
    legislature: str
    source_url: str
    current: list[RosterRow]
    former: list[RosterRow]


def _cells(row_html: str) -> list[str]:
    return [
        html.unescape(" ".join(re.sub(r"<[^>]+>", " ", c).split()))
        for c in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", row_html)
    ]


def _cell_html(row_html: str) -> list[str]:
    """The raw HTML of every cell, so a link inside a cell can be read."""
    return re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", row_html)


def _idm_from_row(row_html: str) -> str | None:
    m = re.search(r"(?i)idm=(\d+)", row_html)
    return m.group(1) if m else None


def _group_id_from_cell(cell_html: str) -> str | None:
    """The group id, read from the link the chamber publishes in the cell."""
    m = re.search(r"(?i)idg=(\d+)", cell_html)
    return m.group(1) if m else None


def parse_roster(page: str, *, chamber: str, legislature: str, source_url: str) -> Roster:
    """Parse the roster page into current and former member rows."""
    current: list[RosterRow] = []
    former: list[RosterRow] = []
    for tbl in re.findall(r"(?is)<table[^>]*>.*?</table>", page):
        rows = re.findall(r"(?is)<tr[^>]*>(.*?)</tr>", tbl)
        header: list[str] | None = None
        data: list[tuple[list[str], str]] = []
        for row_html in rows:
            cells = _cells(row_html)
            if not any(cells):
                continue
            if header is None:
                header = cells
                continue
            data.append((cells, row_html))
        if not header:
            continue
        joined = " ".join(header).lower()
        if "nume" not in joined or "grup" not in joined:
            continue
        has_leave = "până" in joined or "pana" in joined
        target = former if has_leave else current
        for cells, row_html in data:
            # Skip the repeated "Nr. / Denumire" caption row.
            if len(cells) > 1 and cells[1].strip().lower().startswith("nr."):
                continue
            if len(cells) < 2:
                continue
            name = cells[1].strip()
            if not name:
                continue
            constituency = cells[2].strip() if len(cells) > 2 else None
            # The group cell is the one that links to the group ledger, and
            # the link carries the group id. The legislature templates differ:
            # most publish the group in the fourth cell, but the 2012-2016
            # template puts a bare number in the fourth cell and the group
            # (with its link) in the fifth.
            cell_html = _cell_html(row_html)
            group_idx = None
            for idx in range(3, len(cells)):
                if "structura2015.gp" in cell_html[idx] or "idg=" in cell_html[idx]:
                    group_idx = idx
                    break
            if group_idx is None:
                group_idx = 3 if len(cells) > 3 else None
            if group_idx is None:
                continue

            group = cells[group_idx].strip()
            group_id = _group_id_from_cell(cell_html[group_idx])
            join_idx = group_idx + 1
            join_txt = cells[join_idx].strip() if len(cells) > join_idx else ""
            leave_idx = group_idx + 2
            leave_txt = cells[leave_idx].strip() if len(cells) > leave_idx else ""
            target.append(
                RosterRow(
                    idm=_idm_from_row(row_html),
                    name=name,
                    constituency=constituency or None,
                    group=group or None,
                    group_id=group_id,
                    join=parse_ro_date(join_txt) if join_txt else None,
                    leave=parse_ro_date(leave_txt) if leave_txt else None,
                )
            )
    return Roster(
        chamber=chamber,
        legislature=legislature,
        source_url=source_url,
        current=current,
        former=former,
    )
