"""Parser for cdep.ro committee member pages (structura.co).

A committee page carries:
* header: full committee name ("Comisia pentru ...") in the first ``<h1>`` that
  starts with "Comisia". Earlier headings on the page ("Informatii comisie",
  "Activitate comisie") and later ones ("Fosti membri ...") are not the name;
* a current-member table: ``[index, Funcţia, Deputatul, Grupul parlamentar,
  (Membru al comisiei din data)]``. Role start dates, when published, appear
  after a ``<br>`` in the deputy name cell ("preşedinte din 19 mar. 2025") or,
  on older templates, in a footnote span after the name link;
* a former-bureau table ("Fosti membri ai biroului comisiei"):
  ``[index, Funcţia, Deputatul, Grupul parlamentar, (din data), (până în data)]``.
  The section also lists bureau members still in office, so a blank date column
  is reported as None rather than inferred;
* a former-member table ("Foşti membri ai comisiei"):
  ``[index, Deputatul, Grupul parlamentar, Membru al comisiei până în data]``.

Older templates (1990s) omit the date columns, the bureau table and the
footnote spans entirely; those fields are simply left None.

The whole page is one giant table nesting smaller ones, so rows are classified
by the header of their *nearest* table rather than by the outer wrapper, and a
deputy appearing twice in the same section is reported once (deduplicated by
``idm``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag

from ..approxdate import ApproxDate, parse_ro_date
from ..normalize import canonical_group_short, normalize_org_label, strip_diacritics

# Deputy profile links, current (structura2015.mp) and legacy (structura.mp).
_MP_IDM = re.compile(r"structura(?:2015)?\.mp\?[^\"'#]*?\bidm=(\d+)")
_IDG = re.compile(r"idg=(\d+)")

_CURRENT = "current"
_FORMER = "former"
_BUREAU = "former_bureau"


def _cell_text(c: Tag) -> str:
    return " ".join(c.get_text(" ", strip=True).replace("\xa0", " ").split())


def _role_start_from_cell(c: Tag) -> ApproxDate | None:
    """Extract "din <date>" from a deputy name cell.

    Newer templates put the role start as plain text after a ``<br>`` inside
    the name cell; older ones keep it in ``<span class="footlinetext">``. The
    last "din " occurrence wins so a name containing the letters cannot fool
    the match.
    """
    footnote = c.find("span", class_="footlinetext")
    text = footnote.get_text(" ", strip=True) if footnote else _cell_text(c)
    low = text.lower()
    idx = low.rfind("din ")
    if idx < 0:
        return None
    return parse_ro_date(text[idx + len("din ") :].strip())


def _parse_name_cell(c: Tag) -> tuple[str, str | None, str | None, ApproxDate | None]:
    """Return (name, idm, profile_url, role_start) from a deputy name cell."""
    a = c.find("a")
    name = a.get_text(" ", strip=True) if a else _cell_text(c)
    href = a.get("href") if a else None
    idm = None
    if href:
        m = _MP_IDM.search(href)
        if m:
            idm = m.group(1)
    return name.strip(), idm, href, _role_start_from_cell(c)


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
    # Bureau history is a role history, not a committee membership: it is kept
    # apart so ingest never writes it as a second membership tenure. Dates are
    # copied from the page's "din data" / "pâna în data" columns verbatim
    # (blank cells -> None, never inferred), and the section also lists
    # members still in office.
    former_bureau: list[CommitteeMemberRow] = field(default_factory=list)


def _committee_name_from_h1(soup: BeautifulSoup) -> str | None:
    """Return the committee name from the ``<h1>`` that starts with "Comisia"."""
    for h1 in soup.find_all("h1"):
        text = " ".join(h1.get_text(" ", strip=True).split())
        if strip_diacritics(text).lower().startswith("comisia "):
            return text
    return None


def _extract_meta(
    soup: BeautifulSoup, chamber: str, legislature: str | None, source_url: str | None
) -> CommitteeMeta:
    full_name = _committee_name_from_h1(soup)
    if full_name is None:
        # Older templates carry the committee name in a table cell, not in an
        # <h1>. Take the first line that is a committee title ("Comisia ...",
        # including "Comisia economică"), never the "Fosti membri" headings.
        for line in soup.get_text("\n", strip=True).split("\n"):
            line = " ".join(line.split())
            norm = strip_diacritics(line).lower()
            if norm.startswith("comisia ") and not norm.startswith("fosti"):
                full_name = line
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


def _table_section(table: Tag) -> str | None:
    """Classify a member table by the header text of its first rows."""
    rows = table.find_all("tr")
    header = " ".join(_cell_text(r) for r in rows[:2])
    norm = strip_diacritics(header).lower()
    if "biroului" in norm:
        return _BUREAU
    if "pana in data" in norm:
        return _FORMER
    if "deputatul" in norm:
        return _CURRENT
    return None


def _own_cells(row: Tag) -> list[Tag]:
    """Cells of this row only, never cells of a table nested inside it."""
    return [c for c in row.find_all(["td", "th"]) if c.find_parent("tr") is row]


def _drop_index_cell(cells: list[Tag]) -> list[Tag]:
    if cells and re.fullmatch(r"\d+\.?", _cell_text(cells[0])):
        return cells[1:]
    return cells


def _identity_index(cells: list[Tag], target: Tag) -> int | None:
    """Position of ``target`` among ``cells`` by object identity.

    ``Tag.__eq__`` compares markup, so two identical empty cells compare equal;
    the name cell must be located by identity, not by value.
    """
    for i, cell in enumerate(cells):
        if cell is target:
            return i
    return None


def _cell_at(cells: list[Tag], idx: int) -> Tag | None:
    return cells[idx] if 0 <= idx < len(cells) else None


def _date_cell(cells: list[Tag], idx: int) -> ApproxDate | None:
    cell = _cell_at(cells, idx)
    return parse_ro_date(_cell_text(cell)) if cell is not None else None


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
    seen: dict[str, set[str]] = {_CURRENT: set(), _FORMER: set(), _BUREAU: set()}

    for a in soup.find_all("a", href=True):
        m = _MP_IDM.search(a["href"])
        if not m:
            continue
        idm = m.group(1)
        row = a.find_parent("tr")
        table = a.find_parent("table")
        if row is None or table is None or row.find_parent("table") is not table:
            continue
        section = _table_section(table)
        if section is None:
            continue

        cells = _drop_index_cell(_own_cells(row))
        name_cell = a.find_parent(["td", "th"])
        if name_cell is None:
            continue
        pos = _identity_index(cells, name_cell)
        if pos is None:
            continue
        name, idm_from_cell, url, role_start = _parse_name_cell(name_cell)
        if not name or (idm_from_cell and idm_from_cell != idm):
            continue
        if idm in seen[section]:
            continue
        seen[section].add(idm)

        group_idg, group_name = (None, None)
        group_cell = _cell_at(cells, pos + 1)
        if group_cell is not None:
            group_idg, group_name = _group_from_cell(group_cell)

        role: str | None = None
        role_end: ApproxDate | None = None
        if section == _CURRENT:
            role_cell = _cell_at(cells, pos - 1)
            role = _cell_text(role_cell) if role_cell is not None else None
        elif section == _BUREAU:
            role_cell = _cell_at(cells, pos - 1)
            role = _cell_text(role_cell) if role_cell is not None else None
            role_start = role_start or _date_cell(cells, pos + 2)
            role_end = _date_cell(cells, pos + 3)
        else:  # _FORMER
            role_end = _date_cell(cells, pos + 2)

        member = CommitteeMemberRow(
            name=name,
            idm=idm,
            profile_url=url,
            role=_norm_role(role),
            role_start=role_start,
            role_end=role_end,
            group_idg=group_idg,
            group_name=group_name,
        )
        getattr(ledger, section).append(member)

    return ledger
