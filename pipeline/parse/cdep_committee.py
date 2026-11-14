"""Parser for cdep.ro committee member pages (structura.co).

A committee page carries:
* header: full committee name ("Comisia pentru ...");
* a current-member table: Funcţia | Deputatul | Grupul parlamentar |
  [Membru al comisiei din data]. Role start dates, when published, appear in
  footnote spans after the deputy name link
  ("<span class="footlinetext">preşedinte din 19 mar. 2025</span>");
* a committee bureau table (same shape as current, roles like Preşedinte of
  the committee bureau);
* a former-member table ("Foşti membri ai comisiei"):
  Deputatul | Grupul parlamentar | Membru al comisiei până în data.

Older templates (1990s) omit the date columns and footnote spans entirely;
those fields are simply left None.

The page is one giant nested table, so we find deputy links and extract
context from their parent rows rather than classifying tables by header.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag

from ..approxdate import ApproxDate, parse_ro_date
from ..normalize import canonical_group_short, normalize_org_label

_IDM = re.compile(r"idm=(\d+)")
_IDG = re.compile(r"idg=(\d+)")


def _cell_text(c: Tag) -> str:
    return c.get_text(" ", strip=True).replace("\xa0", " ").strip()


def _parse_name_cell(c: Tag) -> tuple[str, str | None, str | None, ApproxDate | None]:
    """Return (name, idm, profile_url, role_start) from a deputy name cell.

    The role start date, when published, sits in a footnote span after the
    name link: ``<span class="footlinetext">preşedinte din 19 mar. 2025</span>``.
    """
    a = c.find("a")
    name = a.get_text(" ", strip=True) if a else _cell_text(c)
    href = a.get("href") if a else None
    idm = None
    if href:
        m = _IDM.search(href)
        if m:
            idm = m.group(1)
    role_start: ApproxDate | None = None
    footnote = c.find("span", class_="footlinetext")
    if footnote:
        fs = footnote.get_text(" ", strip=True)
        m2 = re.search(r"din\s+(.+)$", fs)
        if m2:
            role_start = parse_ro_date(m2.group(1).strip())
    return name.strip(), idm, href, role_start


@dataclass
class CommitteeMeta:
    name: str
    short_name: str | None
    legislature: str | None
    chamber: str
    source_url: str | None = None


@dataclass
class CommitteeMemberRow:
    name: str
    idm: str | None
    profile_url: str | None
    role: str | None
    role_start: ApproxDate | None
    role_end: ApproxDate | None
    group_idg: str | None
    group_name: str | None


@dataclass
class CommitteeLedger:
    meta: CommitteeMeta
    current: list[CommitteeMemberRow] = field(default_factory=list)
    former: list[CommitteeMemberRow] = field(default_factory=list)


def _extract_meta(
    soup: BeautifulSoup, chamber: str, legislature: str | None, source_url: str | None
) -> CommitteeMeta:
    text = soup.get_text("\n", strip=True)
    lines = [ln.strip() for ln in text.split("\n")]

    full_name = None
    for ln in lines:
        low = ln.lower()
        if low.startswith("comisia pentru"):
            full_name = ln
            break

    short_name = canonical_group_short(full_name or "") if full_name else None

    return CommitteeMeta(
        name=full_name or (short_name or "Unknown"),
        short_name=short_name,
        legislature=legislature,
        chamber=chamber,
        source_url=source_url,
    )


def _norm_role(role: str | None) -> str | None:
    if role is None:
        return None
    role = role.strip()
    if not role:
        return None
    return normalize_org_label(role)


def _group_from_cell(c: Tag) -> tuple[str | None, str | None]:
    """Return (idg, name) from a group link cell, or (None, None)."""
    a = c.find("a")
    if not a:
        return None, None
    href = a.get("href")
    idg = None
    if href:
        m = _IDG.search(href)
        if m:
            idg = m.group(1)
    return idg, a.get_text(" ", strip=True)


def parse_committee_ledger(
    html: str,
    *,
    chamber: str = "deputies",
    legislature: str | None = None,
    source_url: str | None = None,
) -> CommitteeLedger:
    """Parse a cdep.ro committee member page."""
    soup = BeautifulSoup(html, "lxml")
    meta = _extract_meta(soup, chamber, legislature, source_url)
    ledger = CommitteeLedger(meta=meta)

    # Find all deputy profile links and classify each by its parent row shape.
    # Current row: [role_cell, deputy_cell, group_cell, (join_date_cell)]
    # Former row:  [deputy_cell, group_cell, end_date_cell]
    for a in soup.find_all("a", href=lambda h: h and "structura.mp?idm=" in h):
        idm = _IDM.search(a["href"]).group(1) if _IDM.search(a["href"]) else None
        name = a.get_text(" ", strip=True)
        if not name or not idm:
            continue

        row = a.find_parent("tr")
        if row is None:
            continue
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        # Drop the leading index cell ("1.").
        if re.fullmatch(r"\d+\.?", _cell_text(cells[0])):
            cells = cells[1:]
        if not cells:
            continue

        # Determine if this is a current or former member row.
        # Current: [role_cell, deputy_cell, group_cell, (join_date_cell)]
        # Former:  [deputy_cell, group_link, end_date_cell]
        first_cell = cells[0]
        first_has_link = first_cell.find("a") is not None

        if first_has_link:
            # Former member row: deputy link is in the first cell.
            name_cell = first_cell
            name2, idm2, url, _ = _parse_name_cell(name_cell)
            if not name2 or idm2 != idm:
                continue
            idx = 1
            group_idg, group_name = (
                _group_from_cell(cells[idx]) if idx < len(cells) else (None, None)
            )
            role_end: ApproxDate | None = None
            idx2 = 2
            if idx2 < len(cells):
                role_end = parse_ro_date(_cell_text(cells[idx2]))
            ledger.former.append(
                CommitteeMemberRow(
                    name=name2,
                    idm=idm2,
                    profile_url=url,
                    role=None,
                    role_start=None,
                    role_end=role_end,
                    group_idg=group_idg,
                    group_name=group_name,
                )
            )
        else:
            # Current member row: role in first cell, deputy in second.
            role = _cell_text(cells[0]) or None
            name_cell = cells[1] if len(cells) > 1 else None
            if name_cell is None:
                continue
            name2, idm2, url, role_start = _parse_name_cell(name_cell)
            if not name2 or idm2 != idm:
                continue
            idx = 2
            group_idg, group_name = (
                _group_from_cell(cells[idx]) if idx < len(cells) else (None, None)
            )
            ledger.current.append(
                CommitteeMemberRow(
                    name=name2,
                    idm=idm2,
                    profile_url=url,
                    role=_norm_role(role),
                    role_start=role_start,
                    role_end=None,
                    group_idg=group_idg,
                    group_name=group_name,
                )
            )

    return ledger
