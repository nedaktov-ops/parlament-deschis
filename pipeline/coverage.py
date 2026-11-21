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

from sqlalchemy import case, func, inspect, select
from sqlalchemy.orm import Session

from .db import Coverage, KeyEvent, Membership, Organization, Person, Vote
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


# --- Honest multi-dimension view -------------------------------------------
# ``coverage_snapshot`` (and therefore the legacy /api/coverage responses)
# describes mandates only. Reporting ``full`` for all 20 scopes without saying
# what it measures invites the reader to assume votes and biographies are also
# complete. The functions below add a separate, dimension-aware read derived
# entirely from the rows actually present. They do not change any legacy shape.


def _vote_counts(session: Session) -> tuple[dict[tuple[str, str | None], int], bool]:
    """Vote rows per (chamber, legislature); the flag is ``False`` with no table.

    A release database may predate the vote schema. With no vote table there
    can be no vote rows, so the honest answer is ``none`` for every scope — not
    an exception, and certainly not an invented ``full``.
    """
    if not inspect(session.get_bind()).has_table(Vote.__tablename__):
        return {}, False
    rows = session.execute(
        select(Vote.chamber, Vote.legislature, func.count(Vote.id)).group_by(
            Vote.chamber, Vote.legislature
        )
    ).all()
    return {(row[0], row[1]): row[2] for row in rows}, True


def _biography_counts(session: Session) -> dict[tuple[str, str | None], tuple[int, int]]:
    """(persons, persons_with_birth_date) per group-membership scope.

    Uses the same group predicate and person set as ``_distinct_persons`` so the
    biography denominator means exactly what the mandate denominator means.
    Committee memberships stay excluded by ``is_group()``.
    """
    rows = session.execute(
        select(
            Membership.chamber,
            Membership.legislature,
            func.count(func.distinct(Membership.person_id)),
            func.count(func.distinct(case((Person.birth_date.is_not(None), Person.id)))),
        )
        .join(Organization, Organization.id == Membership.org_id)
        .join(Person, Person.id == Membership.person_id)
        .where(is_group())
        .group_by(Membership.chamber, Membership.legislature)
    ).all()
    return {(row[0], row[1]): (row[2] or 0, row[3] or 0) for row in rows}


def coverage_dimensions(session: Session) -> list[dict]:
    """Per-scope coverage for mandates, votes and biographies — from real rows.

    Statuses are ``none`` / ``partial`` / ``full``. Nothing is inferred from a
    headline number:

    * mandates reuse ``coverage_snapshot`` unchanged (distinct group persons
      against a verified seat bar only where one is known);
    * votes are counted from the ``vote`` table. No rows — or no table — means
      ``none``. There is no published expected vote total, so this dimension
      is never marked ``full``;
    * biographies are counted from ``person.birth_date`` over the same persons
      the mandate count uses. ``full`` is reserved for 100% coverage, which is
      stricter than the mandate ratio and so cannot overstate completeness.
    """
    vote_counts, vote_table_present = _vote_counts(session)
    bio_counts = _biography_counts(session)
    out: list[dict] = []
    for scope in coverage_snapshot(session):
        key = (scope["chamber"], scope["legislature"])
        votes = vote_counts.get(key, 0)
        bio_total, bio_known = bio_counts.get(key, (0, 0))

        if votes == 0:
            vote_status = "none"
            vote_note = (
                "Vote table is not present in this database."
                if not vote_table_present
                else "No votes ingested in this scope."
            )
        else:
            vote_status = "partial"
            vote_note = (
                f"{votes} vote(s) ingested in this scope; no published expected-total "
                "bar exists for votes, so 'full' is never claimed."
            )

        if bio_total == 0:
            bio_status, bio_note = "none", "No persons with group memberships in this scope."
        elif bio_known == 0:
            bio_status, bio_note = "none", "No birth dates known for persons in this scope."
        elif bio_known >= bio_total:
            bio_status, bio_note = "full", f"Birth date known for all {bio_total} persons in scope."
        else:
            bio_status = "partial"
            bio_note = f"{bio_known} of {bio_total} persons in scope have a known birth date."

        out.append(
            {
                "chamber": scope["chamber"],
                "legislature": scope["legislature"],
                "period_start": scope["period_start"],
                "period_end": scope["period_end"],
                "mandates": {
                    "status": scope["completeness"],
                    "count": scope["persons"],
                    "note": scope["note"],
                },
                "votes": {"status": vote_status, "count": votes, "note": vote_note},
                "biographies": {
                    "status": bio_status,
                    "count": bio_known,
                    "total": bio_total,
                    "note": bio_note,
                },
            }
        )
    return out
