"""Parser for cdep.ro parliamentary group ledger pages (structura2015.gp).

A group page carries:
* header: full name, founding date ("Data înfiintarii:"), former name ("fost …");
* a current-member table;
* a former-bureau table;
* a former-member table.

The templates differ per legislature, per chamber and per group, so the columns
are mapped from the **header row**, never from the number of cells:

    Functia | Nume | Partid | Membru din     current roster (Chamber, full)
    Functia | Nume | Membru din              current roster (no party column)
    Functia | Nume | Partid                  current roster (no dates at all)
    Functia | Nume                           current roster (Senate template:
                                             the role interval is in the name
                                             cell) or former bureau
    Nume | Membru din | Membru până          former members (3 columns)
    Nume | Membru până                       former members (2 columns)
    Nume | Neafiliat din / până              unaffiliated roster (Chamber)
    Nume                                    unaffiliated roster (Senate, no dates)

The name cell links the MP profile (idm, per-mandate) and may carry a role
start date under a <br/>. The "Membru din" column is the authoritative
group-join date; empty means a founding/continuing member (start inferred at
ingest from the profile's validation date, never invented).
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
    # True when the source lists the member but publishes no dates (the Senate
    # unaffiliated roster). The dates must then be inferred from neighbouring
    # group ledgers — never invented.
    dates_missing: bool = False


@dataclass
class GroupLedger:
    meta: GroupMeta
    current: list[MemberRow] = field(default_factory=list)
    former: list[MemberRow] = field(default_factory=list)
    former_bureau: list[MemberRow] = field(default_factory=list)
    name_only: list[MemberRow] = field(default_factory=list)


def _cell_text(c: Tag) -> str:
    return c.get_text(" ", strip=True).replace("\xa0", " ").strip()


def _parse_name_cell(
    c: Tag,
) -> tuple[str, str | None, str | None, ApproxDate | None, ApproxDate | None]:
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


@dataclass(frozen=True)
class TableShape:
    """Header-driven description of one table on a group page."""

    kind: str
    has_party: bool = False
    has_join: bool = False


def _classify(table: Tag) -> TableShape | None:
    """Map a table to its template using the header row only."""
    joined = " | ".join(_headers(table))
    if not joined:
        return None
    has_join = "membru din" in joined
    if "neafiliat până" in joined or "neafiliat pana" in joined:
        return TableShape("former_unaffiliated", has_join="neafiliat din" in joined)
    if "neafiliat din" in joined:
        return TableShape("current_unaffiliated", has_join=True)
    if "membru până" in joined or "membru pana" in joined:
        return TableShape("former", has_join=has_join)
    if "partid" in joined and "nume" in joined:
        # Current roster. The join column is optional (the 1990 pages omit it).
        return TableShape("current", has_party=True, has_join=has_join)
    if "functia" in joined and "nume" in joined:
        if has_join:
            return TableShape("current", has_party=False, has_join=True)
        # Functia | Nume: current roster on the Senate template (the role
        # interval sits in the name cell) or the former bureau. The caller
        # settles it by document order.
        return TableShape("bureau")
    if "nume" in joined and "membru" not in joined and "neafiliat" not in joined:
        # A bare name list. The Senate publishes its unaffiliated roster this
        # way: names only, no join/leave dates.
        return TableShape("name_only")
    return None


def _is_unaffiliated_page(soup: BeautifulSoup) -> bool:
    title = soup.title.get_text(" ", strip=True).lower() if soup.title else ""
    return "neafilia" in title


def _extract_meta(
    soup: BeautifulSoup, chamber: str, legislature: str | None, source_url: str | None
) -> GroupMeta:
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

    # The breadcrumb carries a display label ("PRO România", "Neafiliaţi")
    # that is not always the canonical acronym. Prefer the canonical form so
    # that the same group is always the same organisation, and only fall back
    # to the breadcrumb when the title is not in the reference table.
    canonical = canonical_group_short(full_name or "") or canonical_group_short(short_name or "")
    if canonical:
        short_name = canonical

    return GroupMeta(
        name=full_name or (short_name or "Unknown"),
        short_name=short_name,
        founding_date=founding,
        former_name=former_name,
        legislature=legislature,
        chamber=chamber,
        source_url=source_url,
    )


def _all_rows_ended(table: Tag) -> bool:
    """Does every data row of this table state an end ("până în ...")?"""
    rows = table.find_all("tr")[1:]
    saw_row = False
    for r in rows:
        cells = r.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        if re.fullmatch(r"\d+\.?", _cell_text(cells[0])):
            cells = cells[1:]
        if not cells:
            continue
        name_cell = _cell_text(cells[1]) if len(cells) > 1 else ""
        if not name_cell:
            continue
        saw_row = True
        low = name_cell.lower()
        if "până" not in low and "pana" not in low:
            return False
    return saw_row


def parse_group_ledger(
    html: str,
    *,
    chamber: str = "deputies",
    legislature: str | None = None,
    source_url: str | None = None,
) -> GroupLedger:
    soup = BeautifulSoup(html, "lxml")
    meta = _extract_meta(soup, chamber, legislature, source_url)
    ledger = GroupLedger(meta=meta)
    unaffiliated_page = _is_unaffiliated_page(soup)
    seen_current_table = False

    for table in soup.find_all("table"):
        shape = _classify(table)
        if shape is None:
            continue
        kind = shape.kind
        # A "Functia | Nume | Membru din" table is the current roster only if
        # some of its rows are still serving. When EVERY row states an end
        # ("... până în 10 feb. 2020") the table is the former bureau, whose
        # dates belong to the ROLE, not to the group membership. The 2016-2020
        # Deputies ALDE page (a group that dissolved) is published exactly
        # that way, and reading the role end as the membership end truncates
        # the membership (Cupă Ion: role ended 10 feb. 2020, membership ended
        # 28 ian. 2020).
        if kind == "current" and not shape.has_party and _all_rows_ended(table):
            kind = "bureau"
        # A "Functia | Nume" table is the current roster only if no current
        # roster has been seen yet on this page.
        table_is_roster = kind == "bureau" and not seen_current_table
        if kind == "current" or table_is_roster:
            seen_current_table = True

        for r in table.find_all("tr")[1:]:  # skip header
            cells = r.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            # Drop the leading index cell ("1.").
            if re.fullmatch(r"\d+\.?", _cell_text(cells[0])):
                cells = cells[1:]
            if not cells:
                continue
            # Every table needs a name column; the name-only roster has
            # nothing else.
            if kind not in ("name_only",) and len(cells) < 2:
                continue

            if kind == "current":
                # Functia | Nume | [Partid] | [Membru din]
                role = _cell_text(cells[0]) or None
                name, idm, url, rs, re_ = _parse_name_cell(cells[1])
                if not name:
                    continue
                idx = 2
                party = None
                if shape.has_party and idx < len(cells):
                    party = _cell_text(cells[idx]) or None
                    idx += 1
                join = (
                    parse_ro_date(_cell_text(cells[idx]))
                    if shape.has_join and idx < len(cells)
                    else None
                )
                if re_ is not None:
                    # The name cell carries the end of the ROLE ("... până în
                    # 10 feb. 2020"), not the end of the membership. The
                    # member is still serving in the group, so the tenure
                    # stays open and the role interval is kept as such.
                    ledger.current.append(
                        MemberRow(
                            name=name,
                            idm=idm,
                            profile_url=url,
                            kind="current",
                            role=_norm_role(role),
                            role_start=rs,
                            role_end=re_,
                            party=party,
                            group_join=join,
                        )
                    )
                    continue
                ledger.current.append(
                    MemberRow(
                        name=name,
                        idm=idm,
                        profile_url=url,
                        kind="current",
                        role=_norm_role(role),
                        role_start=rs,
                        party=party,
                        group_join=join,
                    )
                )
            elif kind == "bureau":
                # Functia | Nume. On the Senate template this table is the
                # current roster (the role interval sits in the name cell); on
                # the Chamber template it is the former bureau. Document order
                # settles it, and "până în" always marks a former-bureau row.
                role = _cell_text(cells[0]) or None
                name, idm, url, rs, re_ = _parse_name_cell(cells[1])
                if not name:
                    continue
                tail = _cell_text(cells[1]).lower()
                is_former = "până" in tail or "pana" in tail
                if table_is_roster and not is_former:
                    ledger.current.append(
                        MemberRow(
                            name=name,
                            idm=idm,
                            profile_url=url,
                            kind="current",
                            role=_norm_role(role),
                            role_start=rs,
                        )
                    )
                else:
                    ledger.former_bureau.append(
                        MemberRow(
                            name=name,
                            idm=idm,
                            profile_url=url,
                            kind="former_bureau",
                            role=_norm_role(role),
                            role_start=rs,
                            role_end=re_,
                        )
                    )
            elif kind == "former":
                # Nume | [Membru din] | Membru până
                name, idm, url, _, _ = _parse_name_cell(cells[0])
                if not name:
                    continue
                join = (
                    parse_ro_date(_cell_text(cells[1]))
                    if shape.has_join and len(cells) >= 3
                    else None
                )
                leave = parse_ro_date(_cell_text(cells[-1]))
                ledger.former.append(
                    MemberRow(
                        name=name,
                        idm=idm,
                        profile_url=url,
                        kind="former",
                        group_join=join,
                        group_leave=leave,
                    )
                )
            elif kind == "current_unaffiliated":
                # Nume | Neafiliat din
                name, idm, url, _, _ = _parse_name_cell(cells[0])
                join = parse_ro_date(_cell_text(cells[1]))
                if not name:
                    continue
                ledger.current.append(
                    MemberRow(
                        name=name,
                        idm=idm,
                        profile_url=url,
                        kind="current",
                        party=None,
                        group_join=join,
                    )
                )
            elif kind == "former_unaffiliated":
                # Nume | [Neafiliat din] | Neafiliat până
                name, idm, url, _, _ = _parse_name_cell(cells[0])
                join = (
                    parse_ro_date(_cell_text(cells[1]))
                    if shape.has_join and len(cells) >= 3
                    else None
                )
                leave = parse_ro_date(_cell_text(cells[-1]))
                if not name:
                    continue
                ledger.former.append(
                    MemberRow(
                        name=name,
                        idm=idm,
                        profile_url=url,
                        kind="former",
                        group_join=join,
                        group_leave=leave,
                    )
                )
            elif kind == "name_only":
                # Bare name list (Senate unaffiliated roster): the names are
                # published, the dates are not. Keep them flagged so the
                # ingest can infer dates from the neighbouring group ledgers.
                if not unaffiliated_page:
                    continue
                name, idm, url, _, _ = _parse_name_cell(cells[0])
                if not name:
                    continue
                ledger.name_only.append(
                    MemberRow(
                        name=name,
                        idm=idm,
                        profile_url=url,
                        kind="current",
                        party=None,
                        dates_missing=True,
                    )
                )
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
    """Parse the group index page (gp?idl=1) into idg/name/count entries.

    The anchor text mixes the seat count, the group name and a trailing
    "Detalii grup parlamentar" link, and the Senate calls the unaffiliated
    bucket "Senatori neafiliaţi" where the Chamber says "Deputaţi neafiliaţi".
    Strip both so the name is the group name and nothing else.
    """
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
        name = re.sub(r"^\d+\s+Membri\s+", "", text)
        name = re.sub(r"\s+Detalii\b.*$", "", name).strip()
        items.append(
            GroupListItem(
                idg=m.group(1),
                name=name,
                count=count,
                short_name=canonical_group_short(name),
            )
        )
    return items
