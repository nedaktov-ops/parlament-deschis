"""Live poller: periodically re-fetch current-legislature sources, diff via
fragment checksums, reconcile tenures, and derive events. Failure-isolated per
source; exposes health for the UI live indicator.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import PipelineRun, get_session
from .events import derive_group_events
from .sources.cdep import CdepSource
from .sources.client import PoliteClient
from .sources.senat import SenatSource

log = logging.getLogger("parlament.poller")

DEFAULT_LEGISLATURE = "2024"


def run_poll_cycle(session: Session, legislature: str = DEFAULT_LEGISLATURE,
                   client: PoliteClient | None = None) -> dict:
    client = client or PoliteClient()
    results = {}
    cdep = CdepSource(client)
    senat = SenatSource(client)
    try:
        results["cdep"] = cdep.ingest_groups(session, legislature)
    except Exception as exc:  # noqa: BLE001
        log.exception("cdep poll failed")
        results["cdep"] = {"error": str(exc)}
    try:
        results["senat"] = senat.ingest_profiles(session)
    except Exception as exc:  # noqa: BLE001
        log.exception("senat poll failed")
        results["senat"] = {"error": str(exc)}
    results["new_events"] = derive_group_events(session)
    session.commit()
    return results


def source_health(session: Session) -> dict:
    """Latest pipeline run per source for the UI live indicator."""
    out = {}
    for source in ("cdep", "senat"):
        run = session.scalars(
            select(PipelineRun).where(PipelineRun.source == source)
            .order_by(PipelineRun.started_at.desc()).limit(1)
        ).first()
        if run is None:
            out[source] = {"status": "never_run"}
        else:
            out[source] = {
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
                "rows": run.rows,
                "error": run.error,
            }
    out["checked_at"] = datetime.now(timezone.utc).isoformat()
    return out


def start_poller(interval_minutes: int = 30, legislature: str = DEFAULT_LEGISLATURE,
                 db_path=None) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()

    def _job():
        session = get_session(db_path)
        try:
            run_poll_cycle(session, legislature)
        finally:
            session.close()

    scheduler.add_job(_job, "interval", minutes=interval_minutes,
                      next_run_time=datetime.now(timezone.utc))
    scheduler.start()
    log.info("poller started (every %s min)", interval_minutes)
    return scheduler