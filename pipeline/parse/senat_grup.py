"""Parser for senat.ro ComponentaGrupuri.aspx group roster pages."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup

_GUID = re.compile(r"ParlamentarID=([0-9A-Fa-f-]{36})")


@dataclass
class RosterEntry:
    name: str
    guid: str
    profile_url: str


@dataclass
class GroupRoster:
    group_name: str | None
    members: list[RosterEntry] = field(default_factory=list)


def parse_group_roster(html: str, *, source_url: str | None = None) -> GroupRoster:
    soup = BeautifulSoup(html, "lxml")
    group_name = None
    for h in soup.find_all(["h1", "h2", "h3"]):
        t = h.get_text(" ", strip=True)
        if "Grupul parlamentar" in t:
            group_name = t
            break
    members: list[RosterEntry] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=_GUID):
        href = a.get("href")
        m = _GUID.search(href)
        if not m:
            continue
        guid = m.group(1)
        if guid in seen:
            continue
        seen.add(guid)
        name = a.get_text(" ", strip=True)
        if not name:
            continue
        members.append(RosterEntry(name=name, guid=guid, profile_url=href))
    return GroupRoster(group_name=group_name, members=members)