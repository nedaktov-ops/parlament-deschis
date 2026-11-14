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

    def ingest_profiles(
        self, session: Session, *, force: bool = False, limit: int | None = None
    ) -> dict:
        run = PipelineRun(source=self.name, status="SUCCESS", idempotency_key="profiles")
        session.add(run)
        session.flush()
        totals = {"profiles": 0, "memberships": 0, "unchanged": 0}
        try:
            discovery = self.fetch_sitemap()
            guids = discovery["guids"][:limit] if limit else discovery["guids"]
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
