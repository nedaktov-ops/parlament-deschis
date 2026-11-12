"""Coverage bookkeeping: honest per-chamber/per-legislature completeness.

The dashboard must never imply full historical coverage when the pipeline has
only ingested part of a term. Coverage is derived from the rows actually in the
database and persisted in the ``coverage`` table so the API and exports can
report it cheaply.

Seat thresholds are constitutional maxima for the modern era. Legislatures
before 2004 had different sizes (e.g. 1990–1992: 396 deputies / 119 senators),
so a term is only marked ``full`` when the ingested distinct-person count meets
the modern threshold; everything else is ``partial`` or ``none``.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import Coverage, KeyEvent, Membership

# Modern (2004+) chamber sizes. Used as a conservative "full" bar.
SEATS = {"deputies": 330, "senate": 136}
FULL_RATIO = 0.9


def _distinct_persons(session: Session, chamber: str, legislature: str) -> int:
    return int(session.scalar(
        select(func.count(func.distinct(Membership.person_id))).where(
            Membership.chamber == chamber,
            Membership.legislature == legislature,
        )
    ) or 0)


def coverage_snapshot(session: Session) -> list[dict]:
    """Derive the current coverage matrix without writing to the DB."""
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    key_events = session.scalars(
        select(KeyEvent).where(KeyEvent.type == "legislature").order_by(KeyEvent.start_date)
    ).all()
    for ke in key_events:
        if not ke.label or not ke.chamber:
            continue
        key = (ke.chamber, ke.label)
        if key in seen:
            continue
        seen.add(key)
        count = _distinct_persons(session, ke.chamber, ke.label)
        seats = SEATS.get(ke.chamber, 0)
        if count == 0:
            completeness, note = "none", "No memberships ingested yet."
        elif seats and count >= seats * FULL_RATIO:
            completeness, note = "full", None
        else:
            completeness, note = "partial", (
                f"{count} of ~{seats} seats ingested." if seats else f"{count} memberships."
            )
        rows.append({
            "chamber": ke.chamber,
            "legislature": ke.label,
            "period_start": ke.start_date.isoformat() if ke.start_date else None,
            "period_end": ke.end_date.isoformat() if ke.end_date else None,
            "completeness": completeness,
            "note": note,
            "persons": count,
        })
    return rows


def refresh_coverage(session: Session) -> int:
    """Upsert the derived coverage matrix. Returns the number of rows written."""
    snapshot = coverage_snapshot(session)
    existing = {
        (c.chamber, c.legislature): c
        for c in session.scalars(select(Coverage))
    }
    written = 0
    for row in snapshot:
        key = (row["chamber"], row["legislature"])
        cov = existing.get(key)
        if cov is None:
            cov = Coverage(chamber=row["chamber"], legislature=row["legislature"])
            session.add(cov)
        cov.period_start = _parse(row["period_start"])
        cov.period_end = _parse(row["period_end"])
        cov.completeness = row["completeness"]
        cov.note = row["note"]
        written += 1
    session.flush()
    return written


def _parse(iso: str | None):
    if not iso:
        return None
    from datetime import date
    return date.fromisoformat(iso)
