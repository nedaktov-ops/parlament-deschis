"""Parser for senat.ro FisaSenator.aspx profile pages.

A profile is a sequence of <h5> section headers each followed by a table:
party/group, current bureau/committees/friendship/delegations, and "Istoric …"
history sections with closed intervals. Role cells read
"<Role>, de la data de <START>[ până la data de <END>]".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from ..approxdate import ApproxDate, parse_ro_date
from ..normalize import strip_diacritics

_GUID = re.compile(r"ParlamentarID=([0-9A-Fa-f-]{36})")
_CONST = re.compile(r"nr\.?\s*(\d+)\s+(.+?)(?:\s+în data de|\s+in data de|$)", re.I)
_ELECT = re.compile(r"(?:în|in) data de\s*([0-9.]{8,10})", re.I)
_VALID = re.compile(r"validat (?:în|in) data de\s*([0-9.]{8,10})", re.I)
_LEGIS = re.compile(r"Legislatura\s+(\d{4})\s*-\s*(\d{4})", re.I)
_ROLE_CELL = re.compile(
    r"^(.*?),\s*de la data de\s*(.+?)(?:\s*până la data de\s*(.+))?$", re.I | re.S
)
_GROUP_ROLE = re.compile(r"\(([^)]+)\)\s*$")


@dataclass
class SenateMembership:
    org_name: str
    org_class: str
    role: str | None
    start: ApproxDate | None
    end: ApproxDate | None
    is_current: bool


@dataclass
class SenatorProfile:
    name: str
    guid: str | None
    profile_url: str | None
    constituency_nr: int | None = None
    constituency_name: str | None = None
    election_date: ApproxDate | None = None
    validation_date: ApproxDate | None = None
    party: str | None = None
    group: str | None = None
    group_role: str | None = None
    legislature: str | None = None
    memberships: list[SenateMembership] = field(default_factory=list)


def _norm(s: str) -> str:
    return strip_diacritics(s).lower().strip()


def _parse_role_cell(text: str) -> tuple[str | None, ApproxDate | None, ApproxDate | None]:
    text = text.replace("\xa0", " ").strip()
    m = _ROLE_CELL.match(text)
    if not m:
        return None, None, None
    role = m.group(1).strip() or None
    start = parse_ro_date(m.group(2).strip())
    end = parse_ro_date(m.group(3).strip()) if m.group(3) else None
    return role, start, end


def _classify_section(header: str) -> tuple[str, bool] | None:
    """Return (org_class, is_current) for an h5 section header."""
    h = _norm(header)
    is_current = not h.startswith("istoric")
    if "activitate parlamentara" in h:
        return None  # mandate history handled separately
    if "biroul permanent" in h:
        return "bureau", is_current
    if "comisii permanente" in h:
        return "committee", is_current
    if "comisii comune" in h:
        return "joint_committee", is_current
    if "comisii speciale" in h:
        return "special_committee", is_current
    if "comisii de ancheta" in h or "comisii ancheta" in h:
        return "inquiry_committee", is_current
    if "grupuri de prietenie" in h:
        return "friendship", is_current
    if "delegatiile" in h:
        return "delegation", is_current
    return None


def _parse_party_group(soup: BeautifulSoup) -> tuple[str | None, str | None, str | None]:
    el = soup.find(string=re.compile(r"Formaţiunea politică|Formatiunea politica"))
    if not el:
        return None, None, None
    table = el.find_parent("table")
    if not table:
        return None, None, None
    cells = [c.get_text(" ", strip=True) for c in table.find_all("td")]
    cells = [c for c in cells if c]
    party = group = group_role = None
    for c in cells:
        if _norm(c).startswith("formatiunea politica"):
            party = c.split(":", 1)[-1].strip()
            if party in ("-", ""):
                party = None
        elif _norm(c).startswith("grupul parlamentar"):
            grp = c.split(":", 1)[-1].strip()
            m = _GROUP_ROLE.search(grp)
            if m:
                group_role = m.group(1).strip()
                grp = grp[: m.start()].strip()
            group = grp
        elif party is None and group is None and c:
            # Unaffiliated: a bare group label like "Senatori neafiliați".
            group = c
    return party, group, group_role


def parse_senator_profile(html: str, *, guid: str | None = None,
                          profile_url: str | None = None) -> SenatorProfile:
    soup = BeautifulSoup(html, "lxml")
    if guid is None and profile_url:
        m = _GUID.search(profile_url)
        guid = m.group(1) if m else None

    h2 = soup.find("h2")
    name = h2.get_text(" ", strip=True) if h2 else ""

    prof = SenatorProfile(name=name, guid=guid, profile_url=profile_url)

    text = soup.get_text("\n", strip=True)
    lm = _LEGIS.search(text)
    if lm:
        prof.legislature = lm.group(1)

    # Constituency + election/validation from the "Senator ales" h5.
    ales = soup.find(string=re.compile(r"Senator ales"))
    if ales:
        h5 = ales.find_parent("h5") or ales.find_parent("div")
        block = h5.get_text(" ", strip=True) if h5 else str(ales)
        cm = _CONST.search(block)
        if cm:
            prof.constituency_nr = int(cm.group(1))
            prof.constituency_name = cm.group(2).strip()
        em = _ELECT.search(block)
        if em:
            prof.election_date = parse_ro_date(em.group(1))
        vm = _VALID.search(block)
        if vm:
            prof.validation_date = parse_ro_date(vm.group(1))

    prof.party, prof.group, prof.group_role = _parse_party_group(soup)

    container = soup.find("div", class_="senator-details-container") or soup
    for h5 in container.find_all("h5"):
        header = h5.get_text(" ", strip=True)
        cls = _classify_section(header)
        if cls is None:
            continue
        org_class, is_current = cls
        table = h5.find_next("table")
        if table is None:
            continue
        for r in table.find_all("tr"):
            cells = [c for c in r.find_all("td") if c.get_text(strip=True)]
            if len(cells) < 2:
                continue
            org_name = cells[0].get_text(" ", strip=True)
            role, start, end = _parse_role_cell(cells[1].get_text(" ", strip=True))
            if not org_name:
                continue
            prof.memberships.append(SenateMembership(
                org_name=org_name, org_class=org_class, role=role,
                start=start, end=end, is_current=is_current,
            ))
    return prof