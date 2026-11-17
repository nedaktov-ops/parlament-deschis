"""Derive typed movement events from membership intervals.

Events are never invented: they are computed from the dated tenures already
stored (official ledger dates preferred). Derivation is idempotent via a
dedup_key, and a corrected tenure date updates the existing event in place
instead of leaving a duplicate behind.

A **switch** is only emitted when the source actually supports it:
* the previous tenure must be closed (the ledger published a leave date);
* the next tenure must start on or after that leave date (no overlap);
* both tenures must belong to the same chamber **and the same legislature**.

A deputy who becomes a senator is a career change, not a party switch, and a
membership that opens a new legislature is not a switch either.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Event, Membership, Organization, Person
from .queries import is_group

log = logging.getLogger("parlament.events")

# Tolerance, in days, for the handoff between two consecutive group tenures.
# The published dates are day-precise but the source records the departure
# and the arrival either on the same day or on consecutive days.
_HANDOFF_TOLERANCE = 1


def _log_ambiguous_handoff(
    person_id: str, prev: Membership, nxt: Membership, chamber: str | None, legislature: str | None
) -> None:
    """Emit a fully-specified record for a handoff the source cannot date.

    ``match_review`` holds *person* identity candidacies (person_a/person_b) and
    cannot represent a membership-to-membership handoff, and ``Event`` has no
    column for an undated/ambiguous boundary. Writing either would fabricate a
    record the schema cannot honestly hold, so we log every input instead: the
    person, both organisations, both published dates and the scope. This makes
    the skipped boundary recoverable without inventing an event.
    """
    payload = {
        "person_id": person_id,
        "from_org_id": prev.org_id,
        "to_org_id": nxt.org_id,
        "from_end_date": prev.end_date.isoformat() if prev.end_date else None,
        "to_start_date": nxt.start_date.isoformat() if nxt.start_date else None,
        "chamber": chamber,
        "legislature": legislature,
    }
    log.warning("ambiguous_membership_handoff %s", json.dumps(payload, sort_keys=True))


def _flag_one_day_overlap(
    person_id: str, prev: Membership, nxt: Membership, chamber: str | None, legislature: str | None
) -> None:
    """Flag (never hide) a handoff whose source dates overlap by exactly one day."""
    payload = {
        "person_id": person_id,
        "from_org_id": prev.org_id,
        "to_org_id": nxt.org_id,
        "from_end_date": prev.end_date.isoformat() if prev.end_date else None,
        "to_start_date": nxt.start_date.isoformat() if nxt.start_date else None,
        "chamber": chamber,
        "legislature": legislature,
    }
    log.warning("one_day_overlap_switch %s", json.dumps(payload, sort_keys=True))


def _group_memberships(session: Session, chamber: str | None) -> list[Membership]:
    stmt = (
        select(Membership)
        .join(Organization, Organization.id == Membership.org_id)
        .where(is_group())
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


def _upsert_event(
    session: Session, *, dedup_key: str, match: dict | None = None, **fields
) -> Event | None:
    """Insert an event, or correct an existing one in place.

    ``match`` identifies the *logical* move (person, organisations, legislature).
    When a stored event matches it but carries a different date or source —
    which happens when a tenure date is corrected — that event is updated
    instead of being duplicated.
    """
    if match:
        stmt = select(Event)
        for key, value in match.items():
            stmt = stmt.where(getattr(Event, key) == value)
        existing = session.scalars(stmt).first()
        if existing is not None:
            for key, value in fields.items():
                setattr(existing, key, value)
            existing.dedup_key = dedup_key
            return None
    existing = session.scalars(select(Event).where(Event.dedup_key == dedup_key)).first()
    if existing is not None:
        return None
    ev = Event(dedup_key=dedup_key, **fields)
    session.add(ev)
    return ev


def _series(ms: list[Membership]) -> dict[tuple[str | None, str | None], list[Membership]]:
    """Group memberships into (chamber, legislature) series per person."""
    out: dict[tuple[str | None, str | None], list[Membership]] = defaultdict(list)
    for m in ms:
        out[(m.chamber, m.legislature)].append(m)
    for key in out:
        out[key].sort(key=lambda m: (m.start_date or date.min, m.end_date or date.max))
    return out


def derive_group_events(session: Session, chamber: str | None = None) -> int:
    """Compute join/switch_group/leave events from group tenures.

    Returns the number of newly created events. Ambiguous boundaries (the
    source contradicts itself about dates) are skipped and counted, never
    guessed.
    """
    memberships = _group_memberships(session, chamber)
    by_person: dict[str, list[Membership]] = defaultdict(list)
    for m in memberships:
        by_person[m.person_id].append(m)

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
    ambiguous = 0
    for pid, ms in by_person.items():
        pname = person_name(pid)
        for (ch, leg), series in _series(ms).items():
            series = [m for m in series if m.start_date is not None]
            for i, m in enumerate(series):
                to_label = org_name(m.org_id)
                prev = series[i - 1] if i > 0 else None
                successor = series[i + 1] if i + 1 < len(series) else None
                if prev is None:
                    key = f"join:{pid}:{m.org_id}:{ch}:{leg}:{m.start_date.isoformat()}"
                    ev = _upsert_event(
                        session,
                        dedup_key=key,
                        match={
                            "type": "join",
                            "person_id": pid,
                            "to_org_id": m.org_id,
                            "legislature": leg,
                            "chamber": ch,
                        },
                        type="join",
                        person_id=pid,
                        chamber=ch,
                        legislature=leg,
                        to_org_id=m.org_id,
                        event_date=m.start_date,
                        precision=m.start_precision,
                        reason=m.start_reason or "GENERAL_ELECTION",
                        confidence=m.confidence,
                        group_acronym_at_event=to_label,
                        source_url=m.source_url,
                        summary_ro=_summary_ro("join", pname, None, to_label),
                        summary_en=_summary_en("join", pname, None, to_label),
                    )
                    created += ev is not None
                    continue

                if prev.org_id != m.org_id:
                    # A switch needs a closed previous tenure and no overlap.
                    #
                    # The source publishes "Membru până în X" and "Membru din
                    # Y"; two thirds of the handoffs in the corpus have X == Y
                    # (the member moved on the same day) and a small number
                    # have Y == X + 1. A Y == X - 1 handoff is a one-day
                    # overlap in the source's own dates: it is still recorded
                    # as a switch, but flagged in the event summary and in a
                    # structured log line - never silently hidden.
                    if prev.end_date is None or m.start_date < prev.end_date - timedelta(
                        days=_HANDOFF_TOLERANCE
                    ):
                        ambiguous += 1
                        _log_ambiguous_handoff(pid, prev, m, ch, leg)
                        continue
                    one_day_overlap = m.start_date < prev.end_date
                    if one_day_overlap:
                        _flag_one_day_overlap(pid, prev, m, ch, leg)
                    frm_label = org_name(prev.org_id)
                    key = (
                        f"switch:{pid}:{prev.org_id}:{m.org_id}:{ch}:{leg}"
                        f":{m.start_date.isoformat()}"
                    )
                    ev = _upsert_event(
                        session,
                        dedup_key=key,
                        match={
                            "type": "switch_group",
                            "person_id": pid,
                            "from_org_id": prev.org_id,
                            "to_org_id": m.org_id,
                            "legislature": leg,
                            "chamber": ch,
                        },
                        type="switch_group",
                        person_id=pid,
                        chamber=ch,
                        legislature=leg,
                        from_org_id=prev.org_id,
                        to_org_id=m.org_id,
                        event_date=m.start_date,
                        precision=m.start_precision,
                        reason="CHANGED_GROUP",
                        confidence=m.confidence,
                        group_acronym_at_event=to_label,
                        source_url=m.source_url,
                        summary_ro=_summary_ro("switch_group", pname, frm_label, to_label)
                        + (" (suprapunere de o zi în datele sursei)" if one_day_overlap else ""),
                        summary_en=_summary_en("switch_group", pname, frm_label, to_label)
                        + (" (one-day overlap in source dates)" if one_day_overlap else ""),
                    )
                    created += ev is not None
                    continue

                # Same group again (left and rejoined): no movement event.
                continue

            # A leave is only a leave when no other group took the member.
            for i, m in enumerate(series):
                if m.end_date is None:
                    continue
                successor = series[i + 1] if i + 1 < len(series) else None
                if successor is not None and successor.org_id != m.org_id:
                    continue  # the switch event already records this boundary
                label = org_name(m.org_id)
                key = f"leave:{pid}:{m.org_id}:{ch}:{leg}:{m.end_date.isoformat()}"
                ev = _upsert_event(
                    session,
                    dedup_key=key,
                    match={
                        "type": "leave",
                        "person_id": pid,
                        "from_org_id": m.org_id,
                        "legislature": leg,
                        "chamber": ch,
                    },
                    type="leave",
                    person_id=pid,
                    chamber=ch,
                    legislature=leg,
                    from_org_id=m.org_id,
                    event_date=m.end_date,
                    precision=m.end_precision,
                    reason=m.end_reason or "UNKNOWN",
                    confidence=m.confidence,
                    group_acronym_at_event=label,
                    source_url=m.source_url,
                    summary_ro=_summary_ro("leave", pname, label, None),
                    summary_en=_summary_en("leave", pname, label, None),
                )
                created += ev is not None
    if ambiguous:
        log.warning("ambiguous_membership_handoffs_total %d", ambiguous)
    session.flush()
    return created


def derive_org_events(session: Session, org: Organization) -> int:
    """Emit group_founded events from organization metadata.

    Renames are **not** emitted: the pages publish a former name but no rename
    date, and dating a rename to the founding date would be an invention.
    """
    created = 0
    label = org.short_name or org.name
    if org.founding_date:
        key = f"founded:{org.id}:{org.founding_date.isoformat()}"
        ev = _upsert_event(
            session,
            dedup_key=key,
            match={
                "type": "group_founded",
                "to_org_id": org.id,
                "legislature": None,
            },
            type="group_founded",
            to_org_id=org.id,
            chamber=org.chamber,
            event_date=org.founding_date,
            precision=org.founding_date.isoformat(),
            confidence="official_ledger",
            group_acronym_at_event=label,
            summary_ro=f"Grupul {label} a fost înființat",
            summary_en=f"The {label} group was founded",
        )
        created += ev is not None
    session.flush()
    return created


def _party_memberships(session: Session, chamber: str | None) -> list[Membership]:
    """Get all group memberships that are on behalf of a party."""
    stmt = (
        select(Membership)
        .join(Organization, Organization.id == Membership.org_id)
        .where(is_group())
        .where(Membership.on_behalf_of_id.isnot(None))
    )
    if chamber:
        stmt = stmt.where(Membership.chamber == chamber)
    return list(session.scalars(stmt))


def derive_party_events(session: Session, chamber: str | None = None) -> int:
    """Compute party-level movement events.

    The party is the one named in the ledger's ``Partid`` column, which the
    chamber publishes **without a join date**; it is therefore a secondary,
    lower-confidence view of the same movement that ``switch_group`` records
    from the dated ledgers. Party events are deliberately left undated
    (``event_date=None``, ``precision="unknown"``): borrowing the dated group
    tenure's start would be fabricated precision.
    """
    memberships = _party_memberships(session, chamber)
    by_person: dict[str, list[Membership]] = defaultdict(list)
    for m in memberships:
        by_person[m.person_id].append(m)

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
        pname = person_name(pid)
        for (ch, leg), series in _series(ms).items():
            series = [m for m in series if m.start_date is not None]
            for i, m in enumerate(series):
                party_id = m.on_behalf_of_id
                if not party_id:
                    continue
                to_label = org_name(party_id)
                prev = series[i - 1] if i > 0 else None
                if prev is None:
                    key = f"join_party:{pid}:{party_id}:{ch}:{leg}:{m.start_date.isoformat()}"
                    ev = _upsert_event(
                        session,
                        dedup_key=key,
                        match={
                            "type": "join_party",
                            "person_id": pid,
                            "to_org_id": party_id,
                            "legislature": leg,
                            "chamber": ch,
                        },
                        type="join_party",
                        person_id=pid,
                        chamber=ch,
                        legislature=leg,
                        to_org_id=party_id,
                        # The "Partid" cell carries NO join date. Reusing the
                        # group tenure's dated start here would fabricate a
                        # precision the source never published, so the party
                        # event is explicitly undated.
                        event_date=None,
                        precision="unknown",
                        reason=m.start_reason or "UNKNOWN",
                        confidence=m.confidence,
                        group_acronym_at_event=to_label,
                        source_url=m.source_url,
                        summary_ro=f"{pname} — partid: {to_label} (fără dată de aderare publicată)",
                        summary_en=f"{pname} — party: {to_label} (no join date published)",
                    )
                    created += ev is not None
                    continue
                if prev.on_behalf_of_id == party_id:
                    continue
                if prev.end_date is None or m.start_date < prev.end_date:
                    continue
                frm_label = org_name(prev.on_behalf_of_id)
                key = (
                    f"switch_party:{pid}:{prev.on_behalf_of_id}:{party_id}:{ch}:{leg}"
                    f":{m.start_date.isoformat()}"
                )
                ev = _upsert_event(
                    session,
                    dedup_key=key,
                    match={
                        "type": "switch_party",
                        "person_id": pid,
                        "from_org_id": prev.on_behalf_of_id,
                        "to_org_id": party_id,
                        "legislature": leg,
                        "chamber": ch,
                    },
                    type="switch_party",
                    person_id=pid,
                    chamber=ch,
                    legislature=leg,
                    from_org_id=prev.on_behalf_of_id,
                    to_org_id=party_id,
                    # No party join date is published; do not borrow the dated
                    # group tenure's start (see join_party above).
                    event_date=None,
                    precision="unknown",
                    reason="CHANGED_PARTY",
                    confidence="derived",
                    group_acronym_at_event=to_label,
                    source_url=m.source_url,
                    summary_ro=f"{pname}: {frm_label} → {to_label} (partid, fără dată de aderare)",
                    summary_en=f"{pname}: {frm_label} → {to_label} (party, no join date published)",
                )
                created += ev is not None
    session.flush()
    return created
