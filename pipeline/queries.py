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


def _active(stmt, on_date: date):
    return stmt.where(
        Membership.start_date <= on_date,
        (Membership.end_date.is_(None)) | (Membership.end_date > on_date),
    )


def memberships_at(session: Session, *, org_class: str, chamber: str | None,
                   on_date: date) -> list[Membership]:
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
            Organization.classification == "group",
            Membership.person_id == person_id,
        )
    )
    return session.scalars(_active(stmt, on_date)).first()


def chamber_composition(session: Session, chamber: str, on_date: date) -> dict:
    """Return {group_short: {count, members:[{person_id,name}]}} active on date."""
    ms = memberships_at(session, org_class="group", chamber=chamber, on_date=on_date)
    out: dict[str, dict] = {}
    for m in ms:
        org = session.get(Organization, m.org_id)
        person = session.get(Person, m.person_id)
        key = (org.short_name or org.name) if org else "?"
        bucket = out.setdefault(key, {"org_id": m.org_id, "count": 0, "members": []})
        bucket["count"] += 1
        bucket["members"].append({
            "person_id": m.person_id,
            "name": person.canonical_name if person else "?",
            "role": m.role,
        })
    return out