"""Coverage bookkeeping: honest per-chamber/per-legislature completeness.

The dashboard must never imply full historical coverage when the pipeline has
only ingested part of a term. Coverage is derived from the rows actually in the
database and persisted in the ``coverage`` table so the API and exports can
report it cheaply.

Seat thresholds are constitutional maxima for the modern era. Legislatures
before 2004 had different sizes (e.g. the 1990–1992 chamber: 396 deputies /
119 senators), so each term is checked against its own verified seat count when
known. A term with no known seat count is never claimed ``full`` - it is
reported ``partial`` with the raw count and an explicit "seat count unknown"
note. Everything else is ``partial`` or ``none``.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .db import Coverage, KeyEvent, Membership, Organization
from .queries import is_group

# Modern (2004+) chamber sizes. Used as a conservative "full" bar only for
# 2004+ legislatures: applying 330/136 to an older term would mark it "full"
# far too early (the 1990 chamber had 396 deputies / 119 senators).
SEATS = {"deputies": 330, "senate": 136}
FULL_RATIO = 0.9
_FIRST_MODERN_LEGISLATURE = 2004

# Verified historical chamber sizes. Legislatures not listed here and older
# than 2004 have NO trusted seat count: we must not claim "full" for them.
SEATS_BY_LEGISLATURE: dict[tuple[str, str], int] = {
    ("deputies", "1990"): 396,
    ("senate", "1990"): 119,
}


def _seat_count(chamber: str, legislature: str | None) -> int | None:
    """Known seat count for a chamber/legislature, or None when unknown."""
    if legislature is None:
        return None
    key = (chamber, legislature)
    if key in SEATS_BY_LEGISLATURE:
        return SEATS_BY_LEGISLATURE[key]
    try:
        year = int(legislature[:4])
    except (TypeError, ValueError):
        return None
    return SEATS.get(chamber) if year >= _FIRST_MODERN_LEGISLATURE else None


def _distinct_persons(session: Session, chamber: str, legislature: str) -> int:
    """Distinct people who held a *group* tenure in the scope.

    Committee memberships are organisations too; counting them here would
    report seats that do not exist and could mark a term "full" on committee
    rows alone.
    """
    return int(
        session.scalar(
            select(func.count(func.distinct(Membership.person_id)))
            .join(Organization, Organization.id == Membership.org_id)
            .where(
                is_group(),
                Membership.chamber == chamber,
                Membership.legislature == legislature,
            )
        )
        or 0
    )


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
        seats = _seat_count(ke.chamber, ke.label)
        if count == 0:
            completeness, note = "none", "No memberships ingested yet."
        elif seats and count >= seats * FULL_RATIO:
            completeness, note = "full", None
        elif seats:
            completeness, note = "partial", f"{count} of ~{seats} seats ingested."
        else:
            # No verified seat count for this legislature: never claim "full"
            # on a guessed bar. Report the raw count and the gap honestly.
            completeness, note = (
                "partial",
                f"{count} memberships ingested; seat count for this legislature is not known.",
            )
        rows.append(
            {
                "chamber": ke.chamber,
                "legislature": ke.label,
                "period_start": ke.start_date.isoformat() if ke.start_date else None,
                "period_end": ke.end_date.isoformat() if ke.end_date else None,
                "completeness": completeness,
                "note": note,
                "persons": count,
            }
        )
    return rows


def refresh_coverage(session: Session) -> int:
    """Upsert the derived coverage matrix. Returns the number of rows written."""
    snapshot = coverage_snapshot(session)
    existing = {(c.chamber, c.legislature): c for c in session.scalars(select(Coverage))}
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
