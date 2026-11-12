"""Derive typed movement events from membership intervals.

Events are never invented: they are computed from the dated tenures already
stored (official ledger dates preferred). Derivation is idempotent via a
dedup_key, so re-running never duplicates events.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Event, Membership, Organization, Person


def _group_memberships(session: Session, chamber: str | None) -> list[Membership]:
    stmt = (
        select(Membership)
        .join(Organization, Organization.id == Membership.org_id)
        .where(Organization.classification == "group")
    )
    if chamber:
        stmt = stmt.where(Membership.chamber == chamber)
    return list(session.scalars(stmt))


def _summary_ro(kind: str, person: str, frm: str | None, to: str | None) -> str:
    if kind == "switch_group":
        return f"{person} a trecut de la {frm} la {to}"
    if kind == "join":
        return f"{person} a aderat la {to}"
    if kind == "leave":
        return f"{person} a părăsit {frm}"
    return f"{person}: {kind}"


def _summary_en(kind: str, person: str, frm: str | None, to: str | None) -> str:
    if kind == "switch_group":
        return f"{person} moved from {frm} to {to}"
    if kind == "join":
        return f"{person} joined {to}"
    if kind == "leave":
        return f"{person} left {frm}"
    return f"{person}: {kind}"


def _upsert_event(session: Session, *, dedup_key: str, **fields) -> Event | None:
    existing = session.scalars(
        select(Event).where(Event.dedup_key == dedup_key)
    ).first()
    if existing is not None:
        return None
    ev = Event(dedup_key=dedup_key, **fields)
    session.add(ev)
    return ev


def derive_group_events(session: Session, chamber: str | None = None) -> int:
    """Compute join/switch_group/leave events from group tenures. Returns count
    of newly created events."""
    memberships = _group_memberships(session, chamber)
    by_person: dict[str, list[Membership]] = {}
    for m in memberships:
        by_person.setdefault(m.person_id, []).append(m)

    org_cache: dict[str, Organization] = {}
    person_cache: dict[str, Person] = {}

    def org_name(oid):
        if oid not in org_cache:
            org_cache[oid] = session.get(Organization, oid)
        o = org_cache[oid]
        return (o.short_name or o.name) if o else "?"

    def person_name(pid):
        if pid not in person_cache:
            person_cache[pid] = session.get(Person, pid)
        p = person_cache[pid]
        return p.canonical_name if p else "?"

    created = 0
    for pid, ms in by_person.items():
        ms = [m for m in ms if m.start_date is not None]
        ms.sort(key=lambda m: (m.start_date, m.end_date or date.max))
        pname = person_name(pid)
        for i, m in enumerate(ms):
            to_label = org_name(m.org_id)
            prev = ms[i - 1] if i > 0 else None
            # A switch: previous tenure ended and this one begins.
            if prev is not None and prev.org_id != m.org_id:
                frm_label = org_name(prev.org_id)
                key = f"switch:{pid}:{prev.org_id}:{m.org_id}:{m.start_date.isoformat()}"
                ev = _upsert_event(
                    session, dedup_key=key, type="switch_group", person_id=pid,
                    chamber=m.chamber, from_org_id=prev.org_id, to_org_id=m.org_id,
                    event_date=m.start_date, precision=m.start_precision,
                    reason="CHANGED_PARTY", confidence=m.confidence,
                    group_acronym_at_event=to_label,
                    summary_ro=_summary_ro("switch_group", pname, frm_label, to_label),
                    summary_en=_summary_en("switch_group", pname, frm_label, to_label),
                )
                created += ev is not None
            elif prev is None:
                key = f"join:{pid}:{m.org_id}:{m.start_date.isoformat()}"
                ev = _upsert_event(
                    session, dedup_key=key, type="join", person_id=pid,
                    chamber=m.chamber, to_org_id=m.org_id, event_date=m.start_date,
                    precision=m.start_precision, reason="GENERAL_ELECTION",
                    confidence=m.confidence, group_acronym_at_event=to_label,
                    summary_ro=_summary_ro("join", pname, None, to_label),
                    summary_en=_summary_en("join", pname, None, to_label),
                )
                created += ev is not None
            # A leave: this tenure closed and no later tenure in the same group.
            if m.end_date is not None:
                successor = ms[i + 1] if i + 1 < len(ms) else None
                if successor is None or successor.org_id != m.org_id:
                    key = f"leave:{pid}:{m.org_id}:{m.end_date.isoformat()}"
                    ev = _upsert_event(
                        session, dedup_key=key, type="leave", person_id=pid,
                        chamber=m.chamber, from_org_id=m.org_id, event_date=m.end_date,
                        precision=m.end_precision, reason=m.end_reason or "UNKNOWN",
                        confidence=m.confidence, group_acronym_at_event=to_label,
                        summary_ro=_summary_ro("leave", pname, to_label, None),
                        summary_en=_summary_en("leave", pname, to_label, None),
                    )
                    created += ev is not None
    session.flush()
    return created


def derive_org_events(session: Session, org: Organization) -> int:
    """Emit group_founded / group_renamed events from organization metadata."""
    created = 0
    label = org.short_name or org.name
    if org.founding_date:
        key = f"founded:{org.id}:{org.founding_date.isoformat()}"
        ev = _upsert_event(
            session, dedup_key=key, type="group_founded", to_org_id=org.id,
            chamber=org.chamber, event_date=org.founding_date,
            precision=org.founding_date.isoformat(), confidence="official_ledger",
            group_acronym_at_event=label,
            summary_ro=f"Grupul {label} a fost înființat",
            summary_en=f"The {label} group was founded",
        )
        created += ev is not None
    if org.alt_labels:
        for old in org.alt_labels:
            key = f"renamed:{org.id}:{old}"
            ev = _upsert_event(
                session, dedup_key=key, type="group_renamed", to_org_id=org.id,
                chamber=org.chamber, event_date=org.founding_date,
                confidence="official_ledger", group_acronym_at_event=label,
                summary_ro=f"Grupul {old} a fost redenumit {label}",
                summary_en=f"The {old} group was renamed to {label}",
            )
            created += ev is not None
    session.flush()
    return created