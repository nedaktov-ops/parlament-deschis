"""Parser for cdep.ro MP profile pages (structura2015.mp).

A profile page is the only place the site exposes a stable cross-mandate
identity: the "Mandate parlamentar" block links every mandate the person has
held, each with its own ``idm`` (per-mandate), ``leg`` and ``cam``. That graph
is what lets us link the same person across legislatures and across chambers.

The page also carries:
* the person's name and birth date (``n. 18 noi. 1978``);
* the mandate validation date (``data validării: 21 decembrie 2016``);
* the constituency (``ales deputat/senator în circumscriptia electorala nr.14``);
* the current party and parliamentary group (single current value, not history —
  dated group transitions come from the per-group ledgers).

Nothing here is inferred: a missing value stays ``None``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from ..approxdate import ApproxDate, parse_ro_date

CHAMBER_BY_CAM = {"1": "senate", "2": "deputies"}
CAM_BY_CHAMBER = {v: k for k, v in CHAMBER_BY_CAM.items()}

_BIRTH = re.compile(r"\bn\.\s*(\d{1,2}\s+[A-Za-zĂÂÎȘȚăâîșț]+\.?\s+\d{4})")
_VALIDATION = re.compile(r"data valid[ăa]rii:\s*(\d{1,2}\s+[A-Za-zĂÂÎȘȚăâîșț]+\.?\s+\d{4})")
_MANDATE_LABEL = re.compile(r"(deputat|senator)\s*[-–]?\s*(\d{4})\s*[-–]\s*(\d{4}|prezent)", re.I)
_CONSTITUENCY = re.compile(
    r"ales\s+(deputat|senator)\s+[îi]n\s+circumscriptia\s+electorala\s+nr\.?\s*(\d+)\s*(.*)",
    re.I | re.S,
)


def chamber_from_cam(cam: str | int | None) -> str | None:
    return CHAMBER_BY_CAM.get(str(cam)) if cam is not None else None


@dataclass(frozen=True, order=True)
class MandateRef:
    """One parliamentary mandate. ``idm`` is per-mandate, not per-person."""

    chamber: str
    legislature: str
    idm: str

    @property
    def key(self) -> str:
        return f"{self.chamber}:{self.legislature}:{self.idm}"


@dataclass
class DeputyProfile:
    name: str
    chamber: str
    legislature: str
    idm: str
    profile_url: str
    birth_date: ApproxDate | None = None
    validation_date: ApproxDate | None = None
    constituency_nr: str | None = None
    constituency_name: str | None = None
    party: str | None = None
    party_url: str | None = None
    group: str | None = None
    group_url: str | None = None
    group_role: str | None = None
    mandates: list[MandateRef] = field(default_factory=list)

    @property
    def mandate(self) -> MandateRef:
        return MandateRef(self.chamber, self.legislature, self.idm)


def _clean(text: str | None) -> str | None:
    if text is None:
        return None
    text = re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()
    return text or None


def _mandate_ref_from_href(href: str) -> MandateRef | None:
    qs = parse_qs(urlparse(href).query)
    idm = (qs.get("idm") or [None])[0]
    leg = (qs.get("leg") or [None])[0]
    cam = (qs.get("cam") or [None])[0]
    chamber = chamber_from_cam(cam)
    if not (idm and leg and chamber):
        return None
    return MandateRef(chamber, leg, idm)


def _mandates(soup: BeautifulSoup, current: MandateRef) -> list[MandateRef]:
    """Extract every mandate linked from the "Mandate parlamentar" block.

    The current mandate is an ``<a class="btn-primary">`` without an href, so it
    must be supplied by the caller. If the block is absent the person still has
    the current mandate.
    """
    found: set[MandateRef] = {current}
    heading = soup.find(
        lambda tag: (
            tag.name == "h1" and "mandate parlamentar" in tag.get_text(" ", strip=True).lower()
        )
    )
    scope = heading.find_parent("details") if heading is not None else None
    container = None
    if scope is not None:
        container = scope.find("div", class_="buttons-container")
    if container is not None:
        for a in container.find_all("a", class_="btn-primary"):
            ref = _mandate_ref_from_href(a.get("href") or "")
            if ref is not None:
                found.add(ref)
            else:
                # Fallback for a href-less current button: read its label.
                m = _MANDATE_LABEL.search(a.get_text(" ", strip=True))
                if m:
                    found.add(MandateRef(current.chamber, m.group(2), current.idm))
    return sorted(found)


def _info_box(soup: BeautifulSoup, heading_re: str) -> tuple[str | None, str | None]:
    h4 = soup.find(
        lambda tag: tag.name == "h4" and re.search(heading_re, tag.get_text(" ", strip=True), re.I)
    )
    if h4 is None:
        return None, None
    box = h4.find_parent("div", class_="mp-info-box2025") or h4.parent
    a = box.find("a") if box is not None else None
    if a is None:
        return None, None
    return _clean(a.get_text(" ", strip=True)), a.get("href")


def _group_role(soup: BeautifulSoup) -> str | None:
    h4 = soup.find(
        lambda tag: (
            tag.name == "h4" and "grupul parlamentar" in tag.get_text(" ", strip=True).lower()
        )
    )
    if h4 is None:
        return None
    box = h4.find_parent("div", class_="mp-info-box2025") or h4.parent
    if box is None:
        return None
    row = box.find("tr")
    if row is None:
        return None
    cells = row.find_all("td")
    # cells: [group link, spacer, role, interval]
    if len(cells) >= 3:
        role = _clean(cells[2].get_text(" ", strip=True))
        return role or None
    return None


def parse_deputy_profile(
    html: str,
    *,
    idm: str,
    legislature: str,
    chamber: str,
    profile_url: str,
) -> DeputyProfile:
    soup = BeautifulSoup(html, "lxml")
    current = MandateRef(chamber, legislature, idm)

    name_el = soup.select_one("h1.mp-profile-name2025")
    name = _clean(name_el.get_text(" ", strip=True)) if name_el is not None else None
    if not name:
        name = f"Unknown ({chamber} {legislature} idm={idm})"

    birth = None
    for div in soup.find_all("div", class_="mp-contact-item2025"):
        m = _BIRTH.search(div.get_text(" ", strip=True))
        if m:
            birth = parse_ro_date(m.group(1))
            break

    page_text = soup.get_text(" ", strip=True)
    validation = None
    m = _VALIDATION.search(page_text)
    if m:
        validation = parse_ro_date(m.group(1))

    constituency_nr = constituency_name = None
    # Restrict to the <li> that holds the constituency sentence; running the
    # regex over the whole page greedily swallowed every later section.
    li = soup.find(
        lambda tag: (
            tag.name == "li"
            and "circumscriptia electorala" in tag.get_text(" ", strip=True).lower()
        )
    )
    if li is not None:
        m = _CONSTITUENCY.search(li.get_text(" ", strip=True))
        if m:
            constituency_nr = m.group(2)
            constituency_name = _clean(m.group(3)) or None

    party, party_url = _info_box(soup, r"Forma[țţt]iunea politic")
    group, group_url = _info_box(soup, r"Grupul parlamentar")

    return DeputyProfile(
        name=name,
        chamber=chamber,
        legislature=legislature,
        idm=idm,
        profile_url=profile_url,
        birth_date=birth,
        validation_date=validation,
        constituency_nr=constituency_nr,
        constituency_name=constituency_name,
        party=party,
        party_url=party_url,
        group=group,
        group_url=group_url,
        group_role=_group_role(soup),
        mandates=_mandates(soup, current),
    )
