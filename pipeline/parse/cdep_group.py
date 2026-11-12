"""Parser for cdep.ro parliamentary group ledger pages (structura2015.gp).

A group page carries:
* header: full name, founding date ("Data înfiintarii:"), former name ("fost …");
* a current-member table  (Functia | Nume si prenume | Partid | Membru din);
* a former-bureau table   (Functia | Nume si prenume, with "din X – până în Y");
* a former-member table   (Nume si prenume | Membru din | Membru până).

The name cell links the MP profile (idm, per-term) and may carry a role start
date under a <br/>. The "Membru din" column is the authoritative group-join
date; empty means a founding/continuing member (start inferred at ingest).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag

from ..approxdate import ApproxDate, parse_ro_date, parse_ro_range
from ..normalize import canonical_group_short

_IDM = re.compile(r"idm=(\d+)")


@dataclass
class GroupMeta:
    name: str
    short_name: str | None
    founding_date: ApproxDate | None
    former_name: str | None
    legislature: str | None
    chamber: str
    source_url: str | None = None


@dataclass
class MemberRow:
    name: str
    idm: str | None
    profile_url: str | None
    kind: str  # current | former | former_bureau
    role: str | None = None
    role_start: ApproxDate | None = None
    role_end: ApproxDate | None = None
    party: str | None = None
    group_join: ApproxDate | None = None
    group_leave: ApproxDate | None = None


@dataclass
class GroupLedger:
    meta: GroupMeta
    current: list[MemberRow] = field(default_factory=list)
    former: list[MemberRow] = field(default_factory=list)
    former_bureau: list[MemberRow] = field(default_factory=list)


def _cell_text(c: Tag) -> str:
    return c.get_text(" ", strip=True).replace("\xa0", " ").strip()


def _parse_name_cell(c: Tag) -> tuple[str, str | None, str | None, ApproxDate | None, ApproxDate | None]:
    """Return (name, idm, profile_url, role_start, role_end) from a name cell."""
    a = c.find("a")
    name = a.get_text(" ", strip=True) if a else _cell_text(c)
    href = a.get("href") if a else None
    idm = None
    if href:
        m = _IDM.search(href)
        if m:
            idm = m.group(1)
    # Text after the link carries "din DATE" or "din X - până în Y".
    tail = _cell_text(c)
    if a:
        tail = tail.replace(a.get_text(" ", strip=True), "", 1).strip()
    role_start, role_end = parse_ro_range(tail) if tail else (None, None)
    return name.strip(), idm, href, role_start, role_end


def _headers(table: Tag) -> list[str]:
    rows = table.find_all("tr")
    if not rows:
        return []
    return [_cell_text(c).lower() for c in rows[0].find_all(["td", "th"])]


def _classify(table: Tag) -> str | None:
    h = _headers(table)
    joined = " | ".join(h)
    if "membru până" in joined or "membru pana" in joined:
        return "former"
    if "partid" in joined and "membru din" in joined:
        return "current"
    if "functia" in joined and "nume" in joined and "partid" not in joined:
        return "former_bureau"
    return None


def _extract_meta(soup: BeautifulSoup, chamber: str, legislature: str | None,
                  source_url: str | None) -> GroupMeta:
    text = soup.get_text("\n", strip=True)
    lines = [ln.strip() for ln in text.split("\n")]

    full_name = None
    for ln in lines:
        if ln.lower().startswith("grupul parlamentar"):
            full_name = ln
            break

    founding = None
    former_name = None
    for i, ln in enumerate(lines):
        low = ln.lower()
        if "înfiint" in low or "infiint" in low:
            # "Data înfiintarii: 11.05.2026"
            tail = ln.split(":", 1)[-1].strip()
            founding = parse_ro_date(tail)
        if low == "fost" and i + 1 < len(lines):
            former_name = lines[i + 1]

    # Short name from breadcrumb (last '>' segment).
    short_name = None
    bc = soup.find(string=re.compile("Sunteţi aici|Sunteti aici"))
    if bc:
        container = bc.find_parent("table") or bc.find_parent("td")
        if container:
            seg = container.get_text(" ", strip=True).split(">")[-1].strip()
            short_name = seg or None

    return GroupMeta(
        name=full_name or (short_name or "Unknown"),
        short_name=short_name,
        founding_date=founding,
        former_name=former_name,
        legislature=legislature,
        chamber=chamber,
        source_url=source_url,
    )


def parse_group_ledger(html: str, *, chamber: str = "deputies",
                       legislature: str | None = None,
                       source_url: str | None = None) -> GroupLedger:
    soup = BeautifulSoup(html, "lxml")
    meta = _extract_meta(soup, chamber, legislature, source_url)
    ledger = GroupLedger(meta=meta)

    for table in soup.find_all("table"):
        kind = _classify(table)
        if kind is None:
            continue
        rows = table.find_all("tr")[1:]  # skip header
        for r in rows:
            cells = r.find_all(["td", "th"])
            if len(cells) < 3:
                continue
            # Drop the leading index cell ("1.").
            if re.fullmatch(r"\d+\.?", _cell_text(cells[0])):
                cells = cells[1:]
            if kind == "current":
                # Functia | Nume | Partid | Membru din
                if len(cells) < 4:
                    continue
                role = _cell_text(cells[0]) or None
                name, idm, url, rs, re_ = _parse_name_cell(cells[1])
                party = _cell_text(cells[2]) or None
                join = parse_ro_date(_cell_text(cells[3]))
                if not name:
                    continue
                ledger.current.append(MemberRow(
                    name=name, idm=idm, profile_url=url, kind="current",
                    role=_norm_role(role), role_start=rs, party=party, group_join=join,
                ))
            elif kind == "former":
                # Nume | Membru din | Membru până
                if len(cells) < 3:
                    continue
                name, idm, url, _, _ = _parse_name_cell(cells[0])
                join = parse_ro_date(_cell_text(cells[1]))
                leave = parse_ro_date(_cell_text(cells[2]))
                if not name:
                    continue
                ledger.former.append(MemberRow(
                    name=name, idm=idm, profile_url=url, kind="former",
                    group_join=join, group_leave=leave,
                ))
            elif kind == "former_bureau":
                # Functia | Nume (cu interval)
                if len(cells) < 2:
                    continue
                role = _cell_text(cells[0]) or None
                name, idm, url, rs, re_ = _parse_name_cell(cells[1])
                if not name:
                    continue
                ledger.former_bureau.append(MemberRow(
                    name=name, idm=idm, profile_url=url, kind="former_bureau",
                    role=_norm_role(role), role_start=rs, role_end=re_,
                ))
    return ledger


_ROLE_MAP = {
    "lider": "leader",
    "vicelideri": "vice_leader",
    "vicelider": "vice_leader",
    "secretari": "secretary",
    "secretar": "secretary",
    "membri": "member",
    "membru": "member",
}


def _norm_role(role: str | None) -> str | None:
    if not role:
        return None
    return _ROLE_MAP.get(role.strip().lower(), role.strip().lower())


@dataclass
class GroupListItem:
    idg: str
    name: str
    count: int | None
    short_name: str | None


def parse_group_list(html: str) -> list[GroupListItem]:
    """Parse the group index page (gp?idl=1) into idg/name/count entries."""
    soup = BeautifulSoup(html, "lxml")
    items: list[GroupListItem] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=re.compile(r"idg=\d+")):
        href = a.get("href", "")
        m = re.search(r"idg=(\d+)", href)
        if not m or m.group(1) in seen:
            continue
        text = a.get_text(" ", strip=True)
        if "Membri" not in text and "neafilia" not in text.lower():
            continue
        seen.add(m.group(1))
        cm = re.match(r"(\d+)\s+Membri", text)
        count = int(cm.group(1)) if cm else None
        nm = re.search(r"(Grupul parlamentar.*?|Deputaţi neafiliaţi.*?)(?:\s+Detalii.*)?$", text)
        name = nm.group(1).strip() if nm else text
        items.append(GroupListItem(
            idg=m.group(1), name=name, count=count,
            short_name=canonical_group_short(name),
        ))
    return items