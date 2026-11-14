"""Live adapter for cdep.ro (Camera Deputaților).

Fetches the group index and per-group dated ledgers via the polite client,
archives each as a fragment, and ingests into the temporal store.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from ..db import PipelineRun
from ..fragments import record_fragment
from ..ingest import ingest_cdep_group_ledger
from ..parse.cdep_group import parse_group_ledger, parse_group_list
from .client import PoliteClient

log = logging.getLogger("parlament.cdep")

BASE = "https://www.cdep.ro/ords/pls/parlam/structura2015"
CHAMBER = "deputies"


class CdepSource:
    name = "cdep"

    def __init__(self, client: PoliteClient | None = None):
        self.client = client or PoliteClient()

    def group_list_url(self, legislature: str) -> str:
        return f"{BASE}.gp?idl=1&cam=2&leg={legislature}"

    def group_ledger_url(self, legislature: str, idg: str) -> str:
        return f"{BASE}.gp?cam=2&leg={legislature}&idg={idg}"

    def fetch_group_list(self, legislature: str):
        res = self.client.get(self.group_list_url(legislature))
        return parse_group_list(res.text)

    def ingest_groups(
        self,
        session: Session,
        legislature: str,
        *,
        force: bool = False,
        idg_filter: list[str] | None = None,
    ) -> dict:
        run = PipelineRun(
            source=self.name, status="SUCCESS", idempotency_key=f"groups:{legislature}"
        )
        session.add(run)
        session.flush()
        totals = {"groups": 0, "current": 0, "former": 0, "events": 0, "unchanged": 0}
        try:
            items = self.fetch_group_list(legislature)
            for item in items:
                if idg_filter and item.idg not in idg_filter:
                    continue
                url = self.group_ledger_url(legislature, item.idg)
                res = self.client.get(url)
                ledger = parse_group_ledger(
                    res.text, chamber=CHAMBER, legislature=legislature, source_url=url
                )
                frag, changed = record_fragment(
                    session,
                    model="group_ledger",
                    source_name=self.name,
                    group_key=f"{legislature}:{item.idg}",
                    content=res.text,
                    source_id=item.idg,
                    source_url=url,
                    data={"short_name": ledger.meta.short_name},
                    force=force,
                )
                if not changed and not force:
                    totals["unchanged"] += 1
                    continue
                stats = ingest_cdep_group_ledger(
                    session,
                    ledger,
                    legislature=legislature,
                    snapshot_hash=frag.checksum if frag else None,
                )
                totals["groups"] += 1
                totals["current"] += stats["current"]
                totals["former"] += stats["former"]
                totals["events"] += stats["events"]
                session.commit()
            run.status = "SUCCESS"
        except Exception as exc:  # noqa: BLE001 - isolate per-source failure
            log.exception("cdep ingest failed")
            session.rollback()
            run.status = "FAILURE"
            run.error = str(exc)
        finally:
            run.finished_at = datetime.now(UTC)
            run.rows = totals["current"] + totals["former"]
            session.commit()
        return totals
