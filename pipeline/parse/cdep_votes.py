"""Parsers for the official cdep.ro roll-call vote feeds.

Two official views describe the same vote:

* ``evot2015.xml?par1=1&par2=YYYYMMDD`` - the **day index**: one row per
  vote with the official totals (present / did not vote / yes / no / abstain);
* ``evot2015.nominal?idv=VOTID&idl=1`` - the **nominal page**: one row per
  voting member, and the only place the person's official id (``idm``) is
  published;
* ``evot2015.xml?par1=2&par2=VOTID`` - the **nominal list**: the same voters
  in machine-readable form, with the surname and given name separated.

Everything in this module is pure: no network, no database. The verified
semantics (and the two traps - the UTF-8 bytes behind an ISO-8859-2 prolog,
and the ``-`` token meaning *present but did not vote*) are documented in
``tests/fixtures/votes/FIELD-MAP.md``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from xml.etree import ElementTree

from ..normalize import normalize_name

# The exact element names published in each feed (verified 2026-11-20).
DAY_FIELDS = (
    "VOTID",
    "TIME_VOT",
    "DESCRIERE",
    "CAMERA",
    "PREZENTI",
    "NU_AU_VOTAT",
    "AU_VOTAT_DA",
    "AU_VOTAT_NU",
    "AU_VOTAT_AB",
)

NOMINAL_FIELDS = ("VOTID", "NUME", "PRENUME", "GRUP", "CAMERA", "VOT")

# ``structura2015.mp?idm=<id>&cam=<chamber>&leg=<legislature>``
_PROFILE_LINK = re.compile(
    r"/ords/pls/parlam/structura2015\.mp\?idm=(\d+)&cam=(\d+)&leg=(\d+)\"[^>]*>([^<]+)<"
)

# Vote tokens published in the nominal list.
_CHOICES = {
    "DA": "yes",
    "NU": "no",
    "AB": "abstain",
    "-": "not_voting",
}


@dataclass(frozen=True)
class DayVote:
    """One row of the day index: the official totals of a vote."""

    vote_id: str
    time_vote: str | None
    description: str | None
    camera: str | None
    present: int | None
    not_voting: int | None
    yes: int | None
    no: int | None
    abstain: int | None


@dataclass(frozen=True)
class NominalVote:
    """One row of the machine-readable nominal list."""

    vote_id: str
    family_name: str
    given_name: str
    group: str | None
    camera: str | None
    vote: str | None


@dataclass(frozen=True)
class NominalRow:
    """One row of the nominal HTML page - the only carrier of ``idm``."""

    idm: str
    cam: str
    legislature: str
    name_raw: str
    group_raw: str | None
    vote_raw: str | None


@dataclass(frozen=True)
class JoinedPosition:
    """A nominal list row joined to its page row (identity + vote)."""

    idm: str
    cam: str
    legislature: str
    name_raw: str
    group_html: str | None
    group_xml: str | None
    vote_raw: str | None
    camera_xml: str | None


@dataclass
class JoinResult:
    positions: list[JoinedPosition] = field(default_factory=list)
    unmatched_xml: list[NominalVote] = field(default_factory=list)
    ambiguous_names: list[str] = field(default_factory=list)
    disagreements: list[dict] = field(default_factory=list)


def decode_xml_bytes(raw: bytes) -> str:
    """Decode cdep XML bytes.

    The prolog claims ISO-8859-2 but the server sends UTF-8 (verified
    2026-11-20). Trusting the prolog produces mojibake, so UTF-8 is tried
    first and ISO-8859-2 is the fallback.
    """
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("iso-8859-2")


def _int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _rows(raw: bytes) -> list[dict[str, str]]:
    root = ElementTree.fromstring(decode_xml_bytes(raw))
    rows: list[dict[str, str]] = []
    for row in root.findall("ROW"):
        rows.append({child.tag: (child.text or "").strip() for child in row})
    return rows


def parse_day_index(raw: bytes) -> list[DayVote]:
    """Parse the day index (``par1=1``)."""
    votes: list[DayVote] = []
    for row in _rows(raw):
        votes.append(
            DayVote(
                vote_id=row.get("VOTID", ""),
                time_vote=row.get("TIME_VOT"),
                description=row.get("DESCRIERE"),
                camera=row.get("CAMERA"),
                present=_int(row.get("PREZENTI")),
                not_voting=_int(row.get("NU_AU_VOTAT")),
                yes=_int(row.get("AU_VOTAT_DA")),
                no=_int(row.get("AU_VOTAT_NU")),
                abstain=_int(row.get("AU_VOTAT_AB")),
            )
        )
    return votes


def parse_nominal_list(raw: bytes) -> list[NominalVote]:
    """Parse the machine-readable nominal list (``par1=2``)."""
    votes: list[NominalVote] = []
    for row in _rows(raw):
        votes.append(
            NominalVote(
                vote_id=row.get("VOTID", ""),
                family_name=row.get("NUME", ""),
                given_name=row.get("PRENUME", ""),
                group=row.get("GRUP"),
                camera=row.get("CAMERA"),
                vote=row.get("VOT"),
            )
        )
    return votes


def parse_nominal_page(html: str) -> list[NominalRow]:
    """Parse the nominal HTML page, which carries the official ``idm``.

    The page renders one table row per voter::

        <a href=".../structura2015.mp?idm=1&cam=2&leg=2024">Adomnicăi Mirela Elena</a>
        <td align="center">PSD</td>
        <td align="center" nowrap>DA</td>
    """
    rows: list[NominalRow] = []
    for match in _PROFILE_LINK.finditer(html):
        idm, cam, legislature, name_raw = match.groups()
        group_raw, vote_raw = _row_cells(html, match.end())
        rows.append(
            NominalRow(
                idm=idm,
                cam=cam,
                legislature=legislature,
                name_raw=name_raw.strip(),
                group_raw=group_raw,
                vote_raw=vote_raw,
            )
        )
    return rows


def _row_cells(html: str, start: int) -> tuple[str | None, str | None]:
    """Read the group and vote cells that follow a profile link."""
    tail = html[start : start + 600]
    cells = re.findall(r"<td[^>]*>(.*?)</td>", tail, flags=re.DOTALL)
    values = [re.sub(r"<[^>]+>", "", cell).strip() for cell in cells[:2]]
    group_raw = values[0] if values else None
    vote_raw = values[1] if len(values) > 1 else None
    return (group_raw or None, vote_raw or None)


def join_nominal(xml_rows: list[NominalVote], page_rows: list[NominalRow]) -> JoinResult:
    """Join the nominal list to the nominal page.

    The join key is the normalized name: the XML stores surname and given
    name separately and prints them given-first, while the page prints
    surname-first. The group label is deliberately **not** part of the key -
    cdep publishes ``neafiliat`` in the list and ``Neafiliati`` on the page,
    and ``PSD`` versus ``PSD(afiliat)``, for the same member.

    A name that matches more than one page row is ambiguous: it is
    quarantined, never guessed.
    """
    by_name: dict[str, list[NominalRow]] = {}
    for row in page_rows:
        by_name.setdefault(normalize_name(row.name_raw), []).append(row)

    result = JoinResult()
    for xml_row in xml_rows:
        key = normalize_name(f"{xml_row.family_name} {xml_row.given_name}")
        candidates = by_name.get(key, [])
        if not candidates:
            result.unmatched_xml.append(xml_row)
            continue
        if len(candidates) > 1:
            result.ambiguous_names.append(key)
            continue
        page_row = candidates[0]
        if page_row.vote_raw and xml_row.vote and page_row.vote_raw != xml_row.vote:
            result.disagreements.append(
                {
                    "name": key,
                    "idm": page_row.idm,
                    "xml_vote": xml_row.vote,
                    "page_vote": page_row.vote_raw,
                }
            )
            continue
        result.positions.append(
            JoinedPosition(
                idm=page_row.idm,
                cam=page_row.cam,
                legislature=page_row.legislature,
                name_raw=page_row.name_raw,
                group_html=page_row.group_raw,
                group_xml=xml_row.group,
                vote_raw=page_row.vote_raw or xml_row.vote,
                camera_xml=xml_row.camera,
            )
        )
    return result


def chamber_for_cam(cam: str | None) -> str | None:
    """Map the published chamber code to our chamber names.

    ``2`` = Camera Deputaților, ``1`` = Senat. ``0`` marks a joint sitting and
    is not a chamber on its own.
    """
    if cam == "2":
        return "deputies"
    if cam == "1":
        return "senate"
    return None


def normalize_choice(token: str | None) -> str:
    """Map a published vote token to a stable choice.

    ``-`` means *present but did not vote* (verified against vote 37526:
    ``NU_AU_VOTAT=1``, ``AU_VOTAT_AB=0`` and exactly one ``-``).
    """
    if token is None:
        return "unknown"
    return _CHOICES.get(token.strip(), "unknown")
