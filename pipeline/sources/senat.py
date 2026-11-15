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

    def _historical_legislature_labels(self) -> list[str]:
        """Discover the legislature labels published on FisaSenatori.aspx."""
        res = self.client.get(_FISA_SENATORI)
        labels: list[str] = []
        for m in _OPTION.finditer(res.text):
            val = html_mod.unescape(m.group("val")).strip()
            label = re.sub(r"\s+", " ", html_mod.unescape(m.group("label"))).strip()
            if _YEAR.match(val) or _YEAR.search(label):
                if val not in labels:
                    labels.append(val)
        return labels

    def fetch_historical_guids(self, legislatures: list[str] | None = None) -> list[str]:
        """Discover historical senator GUIDs via ``FisaSenatori.aspx`` POST.

        ``FisaSenatori.aspx`` is senat.ro's ASP.NET WebForms search page for
        historical legislatures. For each requested legislature label we GET
        the page (to capture ``__VIEWSTATE``/``__EVENTVALIDATION`` and honor
        pacing/robots via :class:`PoliteClient`), then POST the legislature
        selection back and parse ``FisaSenator.aspx?ParlamentarID={guid}``
        links from the result.

        ``legislatures`` is a list of legislature labels (e.g.
        ``["1990", "1992"]``). ``None`` means "all legislatures published on
        the page": we GET once and read the legislature dropdown options.

        Returns GUIDs in discovery order, de-duped. Never bypasses CAPTCHA or
        robots: :meth:`PoliteClient.post` raises :class:`CaptchaError` on a
        challenge and :class:`RobotsDisallowed` when robots.txt forbids it.
        """
        if legislatures is None:
            legislatures = self._historical_legislature_labels()
        guids: list[str] = []
        seen: set[str] = set()
        for leg in legislatures:
            page = self.client.get(_FISA_SENATORI)
            data = {
                _VIEWSTATE_FIELD: self._input_value(page.text, _VIEWSTATE_FIELD),
                _EVENTVALIDATION_FIELD: self._input_value(page.text, _EVENTVALIDATION_FIELD),
                _LEGISLATURE_FIELD: leg,
                _SEARCH_BUTTON: "Caută",
            }
            res = self.client.post(_FISA_SENATORI, data=data)
            for m in _GUID.finditer(res.text):
                guid = m.group(1)
                if guid not in seen:
                    seen.add(guid)
                    guids.append(guid)
        return guids

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
