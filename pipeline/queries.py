"""Core temporal (as-of) queries shared by the API and tests.

The time-slider primitive: a membership is active on date D when
start_date <= D AND (end_date IS NULL OR end_date > D). End is exclusive so a
same-day switch resolves to the new group.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Membership, Organization, Person

#: The classification value that marks a parliamentary group.
#: Committees are organisations too (``classification="committee"``, OpenStates
#: OSEP #4 / Popolo), and their memberships are *not* party/group tenures.
GROUP_CLASSIFICATION = "group"


def is_group(org=Organization):
    """Predicate for parliamentary-group organisations.

    This is the single source of truth for "this organisation is a group".
    Every read that means *party/group membership* must state it, otherwise a
    committee membership silently inflates member counts, fills coverage gaps,
    contradicts an overlap check or leaks into an API payload.

    Accepts the ``Organization`` model, an ``aliased(Organization)`` or a
    loaded instance, so the same predicate reads naturally in a ``where()``
    clause and in Python. When given an instance it returns a plain bool.
    """
    return org.classification == GROUP_CLASSIFICATION


def _active(stmt, on_date: date):
    return stmt.where(
        Membership.start_date <= on_date,
        (Membership.end_date.is_(None)) | (Membership.end_date > on_date),
    )


def memberships_at(
    session: Session, *, org_class: str, chamber: str | None, on_date: date
) -> list[Membership]:
    stmt = (
        select(Membership)
        .join(Organization, Organization.id == Membership.org_id)
        .where(Organization.classification == org_class)
    )
    if chamber:
        stmt = stmt.where(Membership.chamber == chamber)
    return list(session.scalars(_active(stmt, on_date)))


def person_group_at(session: Session, person_id: str, on_date: date) -> Membership | None:
    stmt = (
        select(Membership)
        .join(Organization, Organization.id == Membership.org_id)
        .where(
            is_group(),
            Membership.person_id == person_id,
        )
    )
    return session.scalars(_active(stmt, on_date)).first()


def chamber_composition(
    session: Session, chamber: str, on_date: date, legislature: str | None = None
) -> dict:
    """Return {group_short: {count, members:[{person_id,name}]}} active on date.

    When ``legislature`` is given, only memberships in that legislature are
    counted. This prevents historical memberships with open-ended end dates
    from inflating the count for a date in a different legislature.
    """
    stmt = (
        select(
            Membership.org_id,
            Membership.person_id,
            Membership.role,
            Organization.short_name,
            Organization.name,
            Person.canonical_name,
        )
        .join(Organization, Organization.id == Membership.org_id)
        .outerjoin(Person, Person.id == Membership.person_id)
        .where(
            is_group(),
            Membership.chamber == chamber,
            Membership.start_date <= on_date,
            (Membership.end_date.is_(None)) | (Membership.end_date > on_date),
        )
    )
    if legislature is not None:
        stmt = stmt.where(Membership.legislature == legislature)

    rows = session.execute(stmt).all()
    out: dict[str, dict] = {}
    for org_id, person_id, role, org_short_name, org_name, person_name in rows:
        key = (org_short_name or org_name) if (org_short_name or org_name) else "?"
        bucket = out.setdefault(key, {"org_id": org_id, "count": 0, "members": []})
        bucket["count"] += 1
        bucket["members"].append(
            {
                "person_id": person_id,
                "name": person_name if person_name else "?",
                "role": role,
            }
        )
    return out
