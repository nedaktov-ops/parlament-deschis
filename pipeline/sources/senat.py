"""Live adapter for senat.ro (Senat).

Discovers senator profile GUIDs and group ids from sitemap.xml (plain GET, no
browser), fetches each FisaSenator profile, archives fragments, and ingests.
"""

from __future__ import annotations

import html as html_mod
import logging
import re
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from ..db import PipelineRun
from ..fragments import record_fragment
from ..ingest import ingest_senator_profile
from ..parse.senat_grup import parse_group_roster
from ..parse.senat_profile import parse_senator_profile
from .client import PoliteClient

log = logging.getLogger("parlament.senat")

BASE = "https://www.senat.ro"
CHAMBER = "senate"
_GUID = re.compile(r"ParlamentarID=([0-9A-Fa-f-]{36})")
_GRUP = re.compile(r"GrupID=([0-9A-Fa-f-]{36})")
_HIDDEN = re.compile(
    r'<input[^>]+?\bname=["\'](?P<name>[^"\']+)["\'][^>]*?\bvalue=["\'](?P<value>[^"\']*)',
    re.I,
)
_OPTION = re.compile(
    r'<option[^>]+?\bvalue=["\'](?P<val>[^"\']*)["\'][^>]*>(?P<label>.*?)</option>',
    re.I | re.S,
)
_YEAR = re.compile(r"^(19|20)\d{2}$")
_FISA_SENATORI = f"{BASE}/FisaSenatori.aspx"
# ASP.NET WebForms field names on FisaSenatori.aspx. Confirm against the live
# form before running against senat.ro; the client never bypasses robots/CAPTCHA.
_VIEWSTATE_FIELD = "__VIEWSTATE"
_EVENTVALIDATION_FIELD = "__EVENTVALIDATION"
_LEGISLATURE_FIELD = "ddlLegislatura"
_SEARCH_BUTTON = "btnSearch"


class HistoricalDiscoveryError(RuntimeError):
    """Raised when historical discovery cannot reliably separate legislatures."""


class SenatSource:
    name = "senat"

    def __init__(self, client: PoliteClient | None = None):
        self.client = client or PoliteClient()

    def profile_url(self, guid: str) -> str:
        return f"{BASE}/FisaSenator.aspx?ParlamentarID={guid}"

    def fetch_sitemap(self) -> dict:
        res = self.client.get(f"{BASE}/sitemap.xml")
        locs = [html_mod.unescape(u) for u in re.findall(r"<loc>(.*?)</loc>", res.text)]
        guids, grup_ids = [], []
        seen_g, seen_gr = set(), set()
        for u in locs:
            if "FisaSenator" in u:
                m = _GUID.search(u)
                if m and m.group(1) not in seen_g:
                    seen_g.add(m.group(1))
                    guids.append(m.group(1))
            elif "ComponentaGrupuri" in u:
                m = _GRUP.search(u)
                if m and m.group(1) not in seen_gr:
                    seen_gr.add(m.group(1))
                    grup_ids.append(m.group(1))
        return {"guids": guids, "grup_ids": grup_ids}

    def _input_value(self, text: str, name: str) -> str:
        """Return the value of a hidden <input> field, or ``""`` if absent."""
        for m in _HIDDEN.finditer(text):
            if m.group("name") == name:
                return html_mod.unescape(m.group("value"))
        return ""

    def _historical_legislature_labels(self) -> dict[str, str]:
        """Map leading year → ``ddLegislatura`` GUID value from the live page.

        The live page's ``<select name="ctl00$B_Center$ddLegislatura">`` lists
        options where ``value`` is a GUID and the displayed label is a range
        ``"1990-1992"`` etc. We return a dict ``{"1990": "<guid>", ...}`` so
        callers pass the exact GUID rather than relying on year-anchored label
        matching, which was a silent wrong-data bug (the field was ignored and the
        default current legislature was always returned).
        """
        res = self.client.get(_FISA_SENATORI)
        mapping: dict[str, str] = {}
        for m in _OPTION.finditer(res.text):
            val = html_mod.unescape(m.group("val")).strip()
            label = re.sub(r"\s+", " ", html_mod.unescape(m.group("label"))).strip()
            y = re.search(r"^(19|20)\d{2}", label)
            if y and val not in mapping:
                mapping[y.group(0)] = val
        return mapping

    def fetch_historical_guids(self, legislatures: list[str] | None = None) -> list[str]:
        """Discover historical senator GUIDs via the two-step FisaSenatori.aspx flow.

        Step 1: GET the page and POST the legislature GUID (no search button).
        The response repopulates ``ddSesiune`` (session) with session‑specific
        GUIDs.
        Step 2: For each session, POST the session GUID together with the
        ``__EVENTTARGET=ctl00$B_Center$cmdSearch`` to render the senator cards.

        Each legislature is expected to yield a **different** GUID set from every
        other requested legislature. If two legislatures produce identical GUID
        sets the guard raises :class:`HistoricalDiscoveryError`; if a legislature
        yields zero GUIDs the guard also raises.

        ``legislatures`` is a list of leading-year strings (e.g. ``["1990", "2024"]``).
        ``None`` means all legislatures found on the live page.

        Returns GUIDs in discovery order, de-duped across all sessions of all
        requested legislatures.

        Raises :class:`HistoricalDiscoveryError` if any requested legislature
        yields zero GUIDs or if two requested legislatures yield identical GUID
        sets (silent wrong‑data guard).
        """
        if legislatures is None:
            mapping = self._historical_legislature_labels()
            legislatures = sorted(mapping.keys())

        # Per-legislature GUID sets, for the cross-legislature guard.
        leg_sets: dict[str, set[str]] = {}

        all_guids: list[str] = []

        for leg in legislatures:
            if leg not in self._historical_legislature_labels():
                raise HistoricalDiscoveryError(
                    f"Legislature {leg!r} not found on FisaSenatori.aspx"
                )
            page = self.client.get(_FISA_SENATORI)
            vs = self._input_value(page.text, "_VIEWSTATE")
            ev = self._input_value(page.text, "__EVENTVALIDATION")
            leg_guid = self._historical_legislature_labels()[leg]

            # Step 1: POST legislature GUID only (no search button).
            # This is the ASP.NET AutoPostBack equivalent that refreshes the
            # session dropdown.
            data = {
                "_VIEWSTATE": vs,
                "__EVENTVALIDATION": ev,
                "ctl00$B_Center$ddLegislatura": leg_guid,
            }
            p1 = self.client.post(_FISA_SENATORI, data=data)

            # Parse session dropdown.
            sel = re.search(
                r'<select[^>]*name="[^"]*ddSesiune"[^>]*>.*?</select>',
                p1.text,
                re.S | re.I,
            )
            if not sel:
                raise HistoricalDiscoveryError(
                    f"Could not find ddSesiune after legislature POST for {leg!r}"
                )
            # Extract option values and labels.
            session_opts: list[tuple[str, str]] = []
            for o in re.finditer(
                r'<option[^>]*value=["\'](?P<v>[^"\']*)["\'][^>]*>(?P<l>.*?)</option>',
                sel.group(0),
                re.I | re.S,
            ):
                val = o.group("v")
                lbl = re.sub(r"\s+", " ", html_mod.unescape(o.group("l"))).strip()
                session_opts.append((val, lbl))

            if not session_opts:
                raise HistoricalDiscoveryError(f"No sessions found for legislature {leg!r}")

            leg_guids: set[str] = set()

            # Step 2: For each session, POST session GUID + search.
            for sv, _sl in session_opts:
                sdata = {
                    "_VIEWSTATE": self._input_value(p1.text, "_VIEWSTATE"),
                    "__EVENTVALIDATION": self._input_value(p1.text, "__EVENTVALIDATION"),
                    "ctl00$B_Center$ddLegislatura": leg_guid,
                    "ctl00$B_Center$ddSesiune": sv,
                    "__EVENTTARGET": "ctl00$B_Center$cmdSearch",
                    "__EVENTARGUMENT": "",
                }
                p2 = self.client.post(_FISA_SENATORI, data=sdata)

                # Parse senator cards: <a href="...ParlamentarID=GUID">Name</a>
                for m in re.finditer(
                    r'<a[^>]+?href=["\']([^"\']*ParlamentarID=([0-9A-Fa-f-]{36}))["\'][^>]*>(.*?)</a>',
                    p2.text,
                    re.I | re.S,
                ):
                    g = m.group(2)
                    if g not in leg_guids:
                        leg_guids.add(g)

            if not leg_guids:
                raise HistoricalDiscoveryError(
                    f"Legislature {leg!r} yielded zero GUIDs — "
                    f"historical discovery returned no senators."
                )

            leg_sets[leg] = leg_guids
            all_guids.extend(sorted(leg_guids))

        # Cross-legislature guard: if any two legislatures produce identical GUID
        # sets, raise — this was the silent bug: the old code returned the same
        # 134 GUIDs for 2024, 2020, 2016 and 1990.
        leg_fingerprints: dict[str, frozenset[str]] = {}
        for leg in legislatures:
            fp = frozenset(leg_sets[leg])
            if leg in leg_fingerprints and leg_fingerprints[leg] == fp:
                raise HistoricalDiscoveryError(
                    f"Legislatures {leg!r} and {next(k for k, v in leg_fingerprints.items() if v == fp)!r} "
                    f"yield identical GUID sets — historical discovery cannot "
                    f"separate them; this is a silent data‑corruption risk."
                )
            leg_fingerprints[leg] = fp

        return all_guids

    def ingest_profiles(
        self,
        session: Session,
        *,
        force: bool = False,
        limit: int | None = None,
        legislatures: list[str] | None = None,
    ) -> dict:
        run = PipelineRun(source=self.name, status="SUCCESS", idempotency_key="profiles")
        session.add(run)
        session.flush()
        totals = {"profiles": 0, "memberships": 0, "unchanged": 0}
        try:
            discovery = self.fetch_sitemap()
            guids = list(discovery["guids"])
            if legislatures is not None:
                # Sitemap lists only current senators. Historical legislatures
                # are discovered via FisaSenatori.aspx POST; de-dupe GUIDs so a
                # senator present in both the sitemap and the historical
                # discovery is ingested once.
                seen = set(guids)
                for guid in self.fetch_historical_guids(legislatures):
                    if guid not in seen:
                        seen.add(guid)
                        guids.append(guid)
            guids = guids[:limit] if limit is not None else guids
            for guid in guids:
                url = self.profile_url(guid)
                res = self.client.get(url)
                prof = parse_senator_profile(res.text, guid=guid, profile_url=url)
                frag, changed = record_fragment(
                    session,
                    model="senator_profile",
                    source_name=self.name,
                    group_key=guid,
                    content=res.text,
                    source_id=guid,
                    source_url=url,
                    data={"name": prof.name},
                    force=force,
                )
                if not changed and not force:
                    totals["unchanged"] += 1
                    continue
                stats = ingest_senator_profile(
                    session,
                    prof,
                    snapshot_hash=frag.checksum if frag else None,
                )
                totals["profiles"] += 1
                totals["memberships"] += stats["memberships"]
                session.commit()
            run.status = "SUCCESS"
        except Exception as exc:  # noqa: BLE001
            log.exception("senat ingest failed")
            session.rollback()
            run.status = "FAILURE"
            run.error = str(exc)
        finally:
            run.finished_at = datetime.now(UTC)
            run.rows = totals["profiles"]
            session.commit()
        return totals

    def ingest_group_rosters(self, session: Session, *, force: bool = False) -> dict:
        """Fetch group rosters (group name + member GUIDs) for cross-checking."""
        totals = {"rosters": 0}
        discovery = self.fetch_sitemap()
        for gid in discovery["grup_ids"]:
            url = f"{BASE}/ComponentaGrupuri.aspx?GrupID={gid}"
            res = self.client.get(url)
            roster = parse_group_roster(res.text, source_url=url)
            record_fragment(
                session,
                model="group_roster",
                source_name=self.name,
                group_key=f"roster:{gid}",
                content=res.text,
                source_id=gid,
                source_url=url,
                data={"group_name": roster.group_name, "members": len(roster.members)},
                force=force,
            )
            totals["rosters"] += 1
            session.commit()
        return totals
