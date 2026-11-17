"""Source adapter for cdep.ro committee pages (structura.co).

Fetches the committee listing and per-committee member ledgers via the polite
client, archives each as a fragment, and ingests into the temporal store.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from html import unescape

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from ..db import PipelineRun
from ..fragments import record_fragment
from ..ingest import ingest_cdep_committee_ledger
from ..parse.cdep_committee import parse_committee_ledger
from .client import PoliteClient

log = logging.getLogger("parlament.cdep_committees")

BASE = "https://www.cdep.ro/ords/pls/parlam/structura2015"
CHAMBER = "deputies"

# Committee listing links, current (structura2015.co) and legacy (structura.co).
_LIST_IDC = re.compile(r"structura(?:2015)?\.co\?[^\"'#]*?\bidc=(\d+)")


class CommitteeItem:
    """A committee discovered on the listing page."""

    def __init__(self, idc: str, name: str):
        self.idc = idc
        self.name = name


class CdepCommitteeSource:
    name = "cdep_committees"

    def __init__(self, client: PoliteClient | None = None):
        self.client = client or PoliteClient()

    def committee_list_url(self, legislature: str) -> str:
        return f"{BASE}.co?cam=2&idl=1&leg={legislature}"

    def committee_ledger_url(self, legislature: str, idc: str) -> str:
        return f"{BASE}.co?cam=2&idc={idc}&leg={legislature}"

    def fetch_committee_list(self, legislature: str) -> list[CommitteeItem]:
        res = self.client.get(self.committee_list_url(legislature))
        return parse_committee_list(res.text)

    def fetch_committee_ledger(self, legislature: str, idc: str):
        url = self.committee_ledger_url(legislature, idc)
        res = self.client.get(url)
        ledger = parse_committee_ledger(
            res.text, chamber=self.CHAMBER, legislature=legislature, source_url=url
        )
        return ledger, res.text

    def ingest_committees(
        self,
        session: Session,
        legislature: str,
        *,
        force: bool = False,
        idc_filter: list[str] | None = None,
    ) -> dict:
        run = PipelineRun(
            source=self.name,
            status="SUCCESS",
            idempotency_key=f"committees:{legislature}",
        )
        session.add(run)
        session.flush()
        totals = {
            "committees": 0,
            "current": 0,
            "former": 0,
            "persons": 0,
            "unchanged": 0,
        }
        try:
            items = self.fetch_committee_list(legislature)
            for item in items:
                if idc_filter and item.idc not in idc_filter:
                    continue
                url = self.committee_ledger_url(legislature, item.idc)
                res = self.client.get(url)
                ledger = parse_committee_ledger(
                    res.text, chamber=self.CHAMBER, legislature=legislature, source_url=url
                )
                frag, changed = record_fragment(
                    session,
                    model="committee_ledger",
                    source_name=self.name,
                    group_key=f"{legislature}:{item.idc}",
                    content=res.text,
                    source_id=item.idc,
                    source_url=url,
                    data={"short_name": ledger.meta.short_name, "name": item.name},
                    force=force,
                )
                if not changed and not force:
                    totals["unchanged"] += 1
                    continue
                stats = ingest_cdep_committee_ledger(
                    session,
                    ledger,
                    legislature=legislature,
                    snapshot_hash=frag.checksum if frag else None,
                )
                totals["committees"] += 1
                totals["current"] += stats["current"]
                totals["former"] += stats["former"]
                totals["persons"] += stats["persons"]
                session.commit()
            run.status = "SUCCESS"
        except Exception as exc:  # noqa: BLE001 - isolate per-source failure
            log.exception("committee ingest failed")
            session.rollback()
            run.status = "FAILURE"
            run.error = str(exc)
        finally:
            run.finished_at = datetime.now(UTC)
            run.rows = totals["current"] + totals["former"]
            session.commit()
        return totals


def parse_committee_list(html: str) -> list[CommitteeItem]:
    """Extract committee items (idc, name) from the listing page.

    Every committee is one ``<a>`` whose href carries ``idc``; the name is the
    anchor text (entities already decoded, e.g. ``constitu&#539;ionalitate``).
    The page also carries an "print" link with an empty ``idc`` — that is not a
    committee. Items are de-duplicated by ``idc``, keeping document order.
    """
    soup = BeautifulSoup(html, "lxml")
    items: dict[str, CommitteeItem] = {}
    for a in soup.find_all("a", href=True):
        m = _LIST_IDC.search(a["href"])
        if not m:
            continue
        idc = m.group(1)
        name = " ".join(unescape(a.get_text(" ", strip=True)).split())
        if not name or idc in items:
            continue
        items[idc] = CommitteeItem(idc=idc, name=name)
    return list(items.values())
