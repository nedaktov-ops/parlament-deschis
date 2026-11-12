"""API query + serialization helpers built on the temporal core."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from pipeline.coverage import coverage_snapshot
from pipeline.db import (
    Coverage,
    Event,
    Evidence,
    Fragment,
    KeyEvent,
    Membership,
    Organization,
    Person,
    PersonIdentifier,
)
from pipeline.queries import chamber_composition


def _label(org: Organization | None) -> str | None:
    """Human-facing label for an organisation (short name, else full name)."""
    if org is None:
        return None
    return org.short_name or org.name


def _snapshot_url(session: Session, snapshot_hash: str | None,
                  source_url: str | None = None) -> str | None:
    """Resolve an archived-copy URL for an evidence row.

    Prefer the explicit snapshot checksum; fall back to matching a fragment by
    source URL (older ingests stored the URL but not the hash). Returns None when
    no snapshot exists — the UI then offers only the live original, never a
    fabricated archive link.
    """
    frag = None
    if snapshot_hash:
        frag = session.scalars(
            select(Fragment).where(Fragment.checksum == snapshot_hash).limit(1)
        ).first()
    if frag is None and source_url:
        frag = session.scalars(
            select(Fragment).where(Fragment.source_url == source_url)
            .order_by(Fragment.timestamp.desc()).limit(1)
        ).first()
    if frag and frag.snapshot_path:
        # data/snapshots/<source>/<hash>.html -> /snapshots/<source>/<hash>.html
        path = frag.snapshot_path.replace("data/snapshots/", "", 1)
        return f"/snapshots/{path}"
    return None


def _org_brief(session: Session, org_id: str | None) -> dict | None:
    if not org_id:
        return None
    o = session.get(Organization, org_id)
    if not o:
        return None
    return {
        "id": o.id, "name": o.name, "short_name": o.short_name,
        "classification": o.classification, "color": o.color,
        "localised_labels": o.localised_labels,
    }


def serialize_membership(session: Session, m: Membership) -> dict:
    return {
        "id": m.id,
        "org": _org_brief(session, m.org_id),
        "party": _org_brief(session, m.on_behalf_of_id),
        "chamber": m.chamber,
        "legislature": m.legislature,
        "role": m.role,
        "start_date": m.start_date.isoformat() if m.start_date else None,
        "end_date": m.end_date.isoformat() if m.end_date else None,
        "start_precision": m.start_precision,
        "end_precision": m.end_precision,
        "confidence": m.confidence,
        "source_url": m.source_url,
    }


def serialize_event(session: Session, e: Event) -> dict:
    person = session.get(Person, e.person_id) if e.person_id else None
    return {
        "id": e.id, "type": e.type,
        "person": {"id": person.id, "name": person.canonical_name} if person else None,
        "chamber": e.chamber,
        "from_org": _org_brief(session, e.from_org_id),
        "to_org": _org_brief(session, e.to_org_id),
        "event_date": e.event_date.isoformat() if e.event_date else None,
        "precision": e.precision,
        "reason": e.reason, "confidence": e.confidence,
        "summary_ro": e.summary_ro, "summary_en": e.summary_en,
        "detected_at": e.detected_at.isoformat() if e.detected_at else None,
    }


def get_chamber(session: Session, chamber: str, as_of: date) -> dict:
    comp = chamber_composition(session, chamber, as_of)
    groups = []
    for short, bucket in comp.items():
        org = session.get(Organization, bucket["org_id"])
        groups.append({
            "short_name": short,
            "org": _org_brief(session, bucket["org_id"]),
            "count": bucket["count"],
            "members": bucket["members"],
            "color": org.color if org else None,
        })
    groups.sort(key=lambda g: -g["count"])
    return {"chamber": chamber, "as_of": as_of.isoformat(),
            "total": sum(g["count"] for g in groups), "groups": groups}


def _daterange(start: date, end: date, step_days: int):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=step_days)


def get_timeline(session: Session, chamber: str, start: date, end: date,
                 step_days: int = 30) -> dict:
    dates = list(_daterange(start, end, step_days))
    if dates and dates[-1] != end:
        dates.append(end)
    series: dict[str, list[int]] = {}
    totals = []
    for d in dates:
        comp = chamber_composition(session, chamber, d)
        totals.append(sum(b["count"] for b in comp.values()))
        for short, bucket in comp.items():
            series.setdefault(short, [0] * len(dates))
        for short in series:
            series[short][len(totals) - 1] = comp.get(short, {"count": 0})["count"]
    # Switch events in range.
    evs = session.scalars(
        select(Event).where(
            Event.chamber == chamber, Event.type == "switch_group",
            Event.event_date >= start, Event.event_date <= end,
        ).order_by(Event.event_date)
    ).all()
    return {
        "chamber": chamber,
        "dates": [d.isoformat() for d in dates],
        "totals": totals,
        "groups": series,
        "switches": [serialize_event(session, e) for e in evs],
    }


def search_persons(session: Session, q: str | None, chamber: str | None,
                   limit: int = 50) -> list[dict]:
    stmt = select(Person)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(
            Person.normalized_name.like(like),
            Person.canonical_name.like(like),
        ))
    people = list(session.scalars(stmt.limit(limit)))
    out = []
    for p in people:
        ms = list(session.scalars(
            select(Membership).where(Membership.person_id == p.id)
        ))
        chambers = sorted({m.chamber for m in ms})
        if chamber and chamber not in chambers:
            continue
        out.append({
            "id": p.id, "name": p.canonical_name, "birth_date":
            p.birth_date.isoformat() if p.birth_date else None,
            "wikidata_qid": p.wikidata_qid, "chambers": chambers,
            "match_status": p.match_status,
        })
    return out


def get_person(session: Session, person_id: str) -> dict | None:
    p = session.get(Person, person_id)
    if not p:
        return None
    ms = list(session.scalars(
        select(Membership).where(Membership.person_id == person_id)
        .order_by(Membership.start_date)
    ))
    events = list(session.scalars(
        select(Event).where(Event.person_id == person_id).order_by(Event.event_date)
    ))
    idents = list(session.scalars(
        select(PersonIdentifier).where(PersonIdentifier.person_id == person_id)
    ))
    evidence = []
    for m in ms:
        for ev in session.scalars(select(Evidence).where(Evidence.membership_id == m.id)):
            evidence.append({
                "id": ev.id, "membership_id": m.id, "type": ev.type,
                "source_url": ev.source_url, "snapshot_hash": ev.snapshot_hash,
                "snapshot_url": _snapshot_url(session, ev.snapshot_hash, ev.source_url),
                "note": ev.note,
                "observed_at": ev.observed_at.isoformat() if ev.observed_at else None,
            })
    return {
        "id": p.id, "name": p.canonical_name,
        "birth_date": p.birth_date.isoformat() if p.birth_date else None,
        "wikidata_qid": p.wikidata_qid, "match_status": p.match_status,
        "identifiers": [{"scheme": i.scheme, "identifier": i.identifier,
                         "legislature": i.legislature} for i in idents],
        "memberships": [serialize_membership(session, m) for m in ms],
        "events": [serialize_event(session, e) for e in events],
        "evidence": evidence,
    }


def get_person_history(session: Session, person_id: str) -> dict | None:
    """Deterministic change history derived from stored tenures + events.

    Only three table reads happen regardless of tenure count (one for the
    person, one joined membership/organisation scan, one for the referenced
    organisations, one for movements), so this stays memory-safe for people with
    long careers.

    Derived rows come from consecutive tenures; explicit ``Event`` rows for
    group/party switches are only added when no derived row already covers the
    same ``field+date+from+to`` tuple.
    """
    person = session.get(Person, person_id)
    if person is None:
        return None

    rows = session.execute(
        select(Membership, Organization)
        .join(Organization, Organization.id == Membership.org_id)
        .where(Membership.person_id == person_id)
        .order_by(
            Membership.start_date.is_(None),
            Membership.start_date,
            Membership.id,
        )
    ).all()

    events = list(session.scalars(
        select(Event)
        .where(
            Event.person_id == person_id,
            Event.type.in_(["switch_group", "switch_party"]),
        )
        .order_by(Event.event_date.is_(None), Event.event_date, Event.id)
    ))

    org_ids = {m.on_behalf_of_id for m, _ in rows if m.on_behalf_of_id}
    org_ids.update(e.from_org_id for e in events if e.from_org_id)
    org_ids.update(e.to_org_id for e in events if e.to_org_id)
    orgs = (
        {o.id: o for o in session.scalars(
            select(Organization).where(Organization.id.in_(org_ids))
        )}
        if org_ids else {}
    )

    history: list[dict] = []
    seen: set[tuple[str, str | None, str | None, str | None]] = set()

    def _emit(row: dict) -> None:
        history.append(row)
        seen.add((row["field"], row["date"], row["from"], row["to"]))

    prev_group: Organization | None = None
    prev_party_id: str | None = None
    role_by_org: dict[str, str | None] = {}

    for m, org in rows:
        start = m.start_date.isoformat() if m.start_date else None

        if org.classification == "group":
            if prev_group is not None and prev_group.id != org.id:
                _emit({
                    "field": "group",
                    "from": _label(prev_group),
                    "to": _label(org),
                    "date": start,
                    "org": _label(org),
                    "event_type": "switch_group",
                    "source_url": m.source_url,
                })
            prev_group = org

            party_id = m.on_behalf_of_id
            if party_id and prev_party_id and party_id != prev_party_id:
                _emit({
                    "field": "party",
                    "from": _label(orgs.get(prev_party_id)),
                    "to": _label(orgs.get(party_id)),
                    "date": start,
                    "org": _label(org),
                    "event_type": "switch_party",
                    "source_url": m.source_url,
                })
            if party_id:
                prev_party_id = party_id

        if org.id in role_by_org and role_by_org[org.id] != m.role:
            _emit({
                "field": "role",
                "from": role_by_org[org.id],
                "to": m.role,
                "date": start,
                "org": _label(org),
                "event_type": "role_change",
                "source_url": m.source_url,
            })
        role_by_org[org.id] = m.role

    for e in events:
        field = "group" if e.type == "switch_group" else "party"
        date = e.event_date.isoformat() if e.event_date else None
        key = (
            field,
            date,
            _label(orgs.get(e.from_org_id)) if e.from_org_id else None,
            _label(orgs.get(e.to_org_id)) if e.to_org_id else None,
        )
        if key in seen:
            continue
        seen.add(key)
        history.append({
            "field": field,
            "from": key[2],
            "to": key[3],
            "date": date,
            "event_type": e.type,
            "source_url": None,
        })

    # Newest first; null dates last; stable for equal dates.
    history.sort(key=lambda r: r["date"] or "", reverse=True)
    history.sort(key=lambda r: r["date"] is None)
    return {"person_id": person_id, "history": history}


def get_movements(session: Session, person_id: str | None, chamber: str | None,
                  start: date | None, end: date | None, limit: int = 200) -> list[dict]:
    stmt = select(Event).where(Event.type.in_(["switch_group", "switch_party"]))
    if person_id:
        stmt = stmt.where(Event.person_id == person_id)
    if chamber:
        stmt = stmt.where(Event.chamber == chamber)
    if start:
        stmt = stmt.where(Event.event_date >= start)
    if end:
        stmt = stmt.where(Event.event_date <= end)
    evs = session.scalars(stmt.order_by(Event.event_date.desc()).limit(limit)).all()
    return [serialize_event(session, e) for e in evs]


def get_recent_events(session: Session, limit: int = 50) -> list[dict]:
    evs = session.scalars(
        select(Event).order_by(Event.event_date.desc(), Event.detected_at.desc()).limit(limit)
    ).all()
    return [serialize_event(session, e) for e in evs]


def get_coverage(session: Session) -> list[dict]:
    """Coverage matrix, preferring persisted rows but keeping person counts live.

    Persisted ``Coverage`` rows are the cheap source of truth for completeness.
    When they exist we enrich each matching row with the derived distinct-person
    count (a key the frontend tolerates). When none have been persisted yet we
    return the derived snapshot so the dashboard still shows honest coverage.
    """
    derived = coverage_snapshot(session)
    by_key = {(r["chamber"], r["legislature"]): r for r in derived}
    rows = list(session.scalars(select(Coverage)))
    if rows:
        out = []
        for c in rows:
            item = {
                "chamber": c.chamber, "legislature": c.legislature,
                "period_start": c.period_start.isoformat() if c.period_start else None,
                "period_end": c.period_end.isoformat() if c.period_end else None,
                "completeness": c.completeness, "note": c.note,
            }
            snap = by_key.get((c.chamber, c.legislature))
            if snap is not None:
                item["persons"] = snap["persons"]
            out.append(item)
        return out
    return derived


def get_meta(session: Session) -> dict:
    legs = {}
    for ke in session.scalars(select(KeyEvent).where(KeyEvent.type == "legislature")):
        legs.setdefault(ke.label, {
            "label": ke.label,
            "start": ke.start_date.isoformat() if ke.start_date else None,
            "end": ke.end_date.isoformat() if ke.end_date else None,
        })
    groups = [_org_brief(session, o.id) for o in session.scalars(
        select(Organization).where(Organization.classification == "group")
    )]
    return {"legislatures": legs, "groups": groups}

def get_party_profile(session: Session, short_name: str, as_of: date) -> dict:
    """Get party profile with membership counts and switch stats for a given date."""
    org = session.scalars(
        select(Organization).where(
            Organization.short_name == short_name,
            Organization.classification == "party"
        )
    ).first()
    if not org:
        raise HTTPException(status_code=404, detail="party not found")

    # Current members at as_of
    group_memberships = session.scalars(
        select(Membership)
        .join(Organization, Organization.id == Membership.org_id)
        .where(
            Organization.classification == "group",
            Membership.on_behalf_of_id == org.id,
            Membership.chamber.in_(["deputies", "senate"]),
        )
    ).all()

    current_members = 0
    for m in group_memberships:
        if m.start_date and m.start_date <= as_of and (m.end_date is None or m.end_date > as_of):
            current_members += 1

    # Switch stats for this party (all time)
    from sqlalchemy import func
    switches_in = session.scalar(
        select(func.count()).select_from(
            select(Event).where(
                Event.type == "switch_party",
                Event.to_org_id == org.id
            ).subquery()
        )
    ) or 0

    switches_out = session.scalar(
        select(func.count()).select_from(
            select(Event).where(
                Event.type == "switch_party",
                Event.from_org_id == org.id
            ).subquery()
        )
    ) or 0

    return {
        "id": org.id,
        "name": org.name,
        "short_name": org.short_name,
        "color": org.color,
        "wikidata_qid": org.wikidata_qid,
        "current_members": current_members,
        "switches_in": switches_in,
        "switches_out": switches_out,
        "net_change": switches_in - switches_out,
    }


def get_party_movements(session: Session, short_name: str, as_of: date, limit: int = 50) -> list[dict]:
    """Get movements (join/switch_party/leave) for a specific party."""
    org = session.scalars(
        select(Organization).where(
            Organization.short_name == short_name,
            Organization.classification == "party"
        )
    ).first()
    if not org:
        raise HTTPException(status_code=404, detail="party not found")

    stmt = select(Event).where(
        Event.type.in_(["switch_party", "join", "leave"]),
        Event.event_date is not None,
        (Event.from_org_id == org.id) | (Event.to_org_id == org.id)
    ).order_by(Event.event_date.desc()).limit(limit)

    evs = session.scalars(stmt).all()
    return [serialize_event(session, e) for e in evs]


def get_party_timeline(session: Session, short_name: str, from_date: date, to_date: date) -> dict:
    """Get group size timeline for a specific party over a date range."""
    org = session.scalars(
        select(Organization).where(
            Organization.short_name == short_name,
            Organization.classification == "party"
        )
    ).first()
    if not org:
        raise HTTPException(status_code=404, detail="party not found")

    from pipeline.queries import chamber_composition
    from datetime import timedelta

    dates = []
    d = from_date
    step = 30
    while d <= to_date:
        dates.append(d)
        d += timedelta(days=step)
    if dates[-1] != to_date:
        dates.append(to_date)

    groups_series: dict[str, list[int]] = {}
    totals = []

    for d in dates:
        comp = chamber_composition(session, "deputies", d)
        totals.append(sum(b["count"] for b in comp.values()))
        for short, bucket in comp.items():
            # Check if this group's party matches our target party by looking up membership
            m = session.scalars(
                select(Membership).where(
                    Membership.org_id == bucket["org_id"],
                    Membership.on_behalf_of_id == org.id,
                    Membership.chamber == "deputies",
                    Membership.start_date <= d,
                    (Membership.end_date.is_(None)) | (Membership.end_date > d),
                )
            ).first()
            if m:
                groups_series.setdefault(short, [0] * len(dates))
                groups_series[short][len(totals) - 1] = bucket["count"]

    return {
        "dates": [d.isoformat() for d in dates],
        "total": totals,
        "groups": groups_series,
    }
