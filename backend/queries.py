"""API query + serialization helpers built on the temporal core."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from pipeline.coverage import coverage_snapshot
from pipeline.db import (
    Coverage,
    Event,
    Evidence,
    Fragment,
    KeyEvent,
    Mandate,
    Membership,
    Organization,
    Person,
    PersonIdentifier,
)
from pipeline.queries import chamber_composition, is_group


def _label(org: Organization | None) -> str | None:
    """Human-facing label for an organisation (short name, else full name)."""
    if org is None:
        return None
    return org.short_name or org.name


def _snapshot_url(
    session: Session, snapshot_hash: str | None, source_url: str | None = None
) -> str | None:
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
            select(Fragment)
            .where(Fragment.source_url == source_url)
            .order_by(Fragment.timestamp.desc())
            .limit(1)
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
        "id": o.id,
        "name": o.name,
        "short_name": o.short_name,
        "classification": o.classification,
        "color": o.color,
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
        "id": e.id,
        "type": e.type,
        "person": {"id": person.id, "name": person.canonical_name} if person else None,
        "chamber": e.chamber,
        "legislature": e.legislature,
        "from_org": _org_brief(session, e.from_org_id),
        "to_org": _org_brief(session, e.to_org_id),
        "event_date": e.event_date.isoformat() if e.event_date else None,
        "precision": e.precision,
        "reason": e.reason,
        "confidence": e.confidence,
        "summary_ro": e.summary_ro,
        "summary_en": e.summary_en,
        "detected_at": e.detected_at.isoformat() if e.detected_at else None,
        "source_url": e.source_url,
    }


def get_chamber(session: Session, chamber: str, as_of: date) -> dict:
    leg_label = _legislature_for(session, as_of)
    comp = chamber_composition(session, chamber, as_of, legislature=leg_label)
    groups = []
    for short, bucket in comp.items():
        org = session.get(Organization, bucket["org_id"])
        groups.append(
            {
                "short_name": short,
                "org": _org_brief(session, bucket["org_id"]),
                "count": bucket["count"],
                "members": bucket["members"],
                "color": org.color if org else None,
            }
        )
    groups.sort(key=lambda g: -g["count"])
    return {
        "chamber": chamber,
        "as_of": as_of.isoformat(),
        "legislature": leg_label,
        "total": sum(g["count"] for g in groups),
        "groups": groups,
    }


def _legislature_for(session: Session, on_date: date) -> str | None:
    """Return the legislature label active on ``on_date``, or None."""
    from pipeline.db import KeyEvent

    row = session.scalars(
        select(KeyEvent).where(
            KeyEvent.type == "legislature",
            KeyEvent.start_date <= on_date,
            (KeyEvent.end_date.is_(None)) | (KeyEvent.end_date > on_date),
        )
    ).first()
    return row.label if row else None


def _daterange(start: date, end: date, step_days: int):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=step_days)


def get_timeline(
    session: Session,
    chamber: str,
    start: date,
    end: date,
    step_days: int = 30,
    include_switches: bool = False,
) -> dict:
    dates = list(_daterange(start, end, step_days))
    if dates and dates[-1] != end:
        dates.append(end)

    membership_rows = session.execute(
        select(
            Membership.start_date,
            Membership.end_date,
            Membership.legislature,
            Organization.short_name,
            Organization.name,
        )
        .join(Organization, Organization.id == Membership.org_id)
        .where(
            Membership.chamber == chamber,
            is_group(),
            Membership.start_date <= end,
            or_(Membership.end_date.is_(None), Membership.end_date > start),
        )
    ).all()
    # (start, end, legislature, group); a None end means "still open".
    memberships = [
        (m_start, m_end, m_leg, short_name or name)
        for m_start, m_end, m_leg, short_name, name in membership_rows
    ]

    legislatures = session.execute(
        select(KeyEvent.label, KeyEvent.start_date, KeyEvent.end_date)
        .where(
            KeyEvent.type == "legislature",
            KeyEvent.start_date <= end,
            or_(KeyEvent.end_date.is_(None), KeyEvent.end_date > start),
        )
        .order_by(KeyEvent.start_date)
    ).all()
    rev_legislatures = list(reversed(legislatures))

    # ONE sweep over the sampled dates: increment a group's count when a
    # membership's start is reached, decrement it when its (exclusive) end is
    # reached. This is O(memberships + dates) instead of the old
    # O(memberships * dates) nested loop that made step_days=1 over several
    # years take seconds.
    from collections import Counter, defaultdict

    active_by_leg: dict[str | None, Counter[str]] = defaultdict(Counter)
    active_all: Counter[str] = Counter()
    additions = sorted(memberships, key=lambda m: m[0])
    removals = sorted((m for m in memberships if m[1] is not None), key=lambda m: m[1])
    add_i = rem_i = 0
    counts_by_date: list[dict[str, int]] = []
    for day in dates:
        while add_i < len(additions) and additions[add_i][0] <= day:
            _, _, leg, group = additions[add_i]
            active_by_leg[leg][group] += 1
            active_all[group] += 1
            add_i += 1
        while rem_i < len(removals) and removals[rem_i][1] <= day:
            _, _, leg, group = removals[rem_i]
            bucket = active_by_leg[leg]
            bucket[group] -= 1
            if bucket[group] <= 0:
                del bucket[group]
            active_all[group] -= 1
            if active_all[group] <= 0:
                del active_all[group]
            rem_i += 1

        active_legislature = next(
            (
                label
                for label, k_start, k_end in rev_legislatures
                if k_start <= day and (k_end is None or k_end > day)
            ),
            None,
        )
        counts = active_all if active_legislature is None else active_by_leg.get(active_legislature)
        counts_by_date.append(dict(counts) if counts else {})

    group_names = sorted({name for counts in counts_by_date for name in counts})
    series = {name: [counts.get(name, 0) for counts in counts_by_date] for name in group_names}
    totals = [sum(counts.values()) for counts in counts_by_date]

    if include_switches:
        evs = session.scalars(
            select(Event)
            .where(
                Event.chamber == chamber,
                Event.type == "switch_group",
                Event.event_date >= start,
                Event.event_date <= end,
            )
            .order_by(Event.event_date)
        ).all()
        switches = [serialize_event(session, e) for e in evs]
    else:
        switches = []

    return {
        "chamber": chamber,
        "dates": [d.isoformat() for d in dates],
        "totals": totals,
        "groups": series,
        "switches": switches,
    }


def search_persons(
    session: Session, q: str | None, chamber: str | None, limit: int = 50
) -> list[dict]:
    stmt = select(Person)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                Person.normalized_name.like(like),
                Person.canonical_name.like(like),
            )
        )
    # P3-B: push the chamber filter into SQL *before* LIMIT. Filtering in Python
    # after ``limit`` rows were taken made ``?chamber=senate`` return arbitrary,
    # too-few results (and silently depend on table order).
    if chamber:
        stmt = stmt.where(
            Person.id.in_(
                select(Membership.person_id)
                .join(Organization, Organization.id == Membership.org_id)
                .where(is_group(), Membership.chamber == chamber)
            )
        )
    # Deterministic order before LIMIT so pages are stable across runs.
    people = list(session.scalars(stmt.order_by(Person.canonical_name, Person.id).limit(limit)))
    out = []
    for p in people:
        ms = list(
            session.scalars(
                select(Membership)
                .join(Organization, Organization.id == Membership.org_id)
                .where(is_group(), Membership.person_id == p.id)
            )
        )
        chambers = sorted({m.chamber for m in ms})
        out.append(
            {
                "id": p.id,
                "name": p.canonical_name,
                "birth_date": p.birth_date.isoformat() if p.birth_date else None,
                "wikidata_qid": p.wikidata_qid,
                "chambers": chambers,
                "match_status": p.match_status,
            }
        )
    return out


def get_person(session: Session, person_id: str, as_of: date | None = None) -> dict | None:
    p = session.get(Person, person_id)
    if not p:
        return None
    ms = list(
        session.scalars(
            select(Membership)
            .join(Organization, Organization.id == Membership.org_id)
            .where(is_group(), Membership.person_id == person_id)
            .order_by(Membership.start_date)
        )
    )
    # Committee tenures are a separate axis from party/group tenures: they are
    # exposed as their own field so existing `memberships` consumers (party
    # flow, coverage ratios, gantt) keep their exact current semantics.
    committee_ms = list(
        session.scalars(
            select(Membership)
            .join(Organization, Organization.id == Membership.org_id)
            .where(
                Organization.classification == "committee",
                Membership.person_id == person_id,
            )
            .order_by(Membership.start_date)
        )
    )
    events = list(
        session.scalars(
            select(Event).where(Event.person_id == person_id).order_by(Event.event_date)
        )
    )
    if as_of is not None:
        events = [e for e in events if e.event_date is not None and e.event_date <= as_of]

        def _active(m: Membership) -> bool:
            return (
                m.start_date is not None
                and m.start_date <= as_of
                and (m.end_date is None or m.end_date > as_of)
            )

        ms = [m for m in ms if _active(m)]
        committee_ms = [m for m in committee_ms if _active(m)]
    idents = list(
        session.scalars(select(PersonIdentifier).where(PersonIdentifier.person_id == person_id))
    )
    evidence = []
    for m in ms:
        for ev in session.scalars(select(Evidence).where(Evidence.membership_id == m.id)):
            evidence.append(
                {
                    "id": ev.id,
                    "membership_id": m.id,
                    "type": ev.type,
                    "source_url": ev.source_url,
                    "snapshot_hash": ev.snapshot_hash,
                    "snapshot_url": _snapshot_url(session, ev.snapshot_hash, ev.source_url),
                    "note": ev.note,
                    "observed_at": ev.observed_at.isoformat() if ev.observed_at else None,
                }
            )
    return {
        "id": p.id,
        "name": p.canonical_name,
        "birth_date": p.birth_date.isoformat() if p.birth_date else None,
        "wikidata_qid": p.wikidata_qid,
        "match_status": p.match_status,
        "identifiers": [
            {"scheme": i.scheme, "identifier": i.identifier, "legislature": i.legislature}
            for i in idents
        ],
        "memberships": [serialize_membership(session, m) for m in ms],
        "committee_memberships": [serialize_membership(session, m) for m in committee_ms],
        "events": [serialize_event(session, e) for e in events],
        "evidence": evidence,
        "as_of": as_of.isoformat() if as_of else None,
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
        .where(is_group(), Membership.person_id == person_id)
        .order_by(
            Membership.start_date.is_(None),
            Membership.start_date,
            Membership.id,
        )
    ).all()

    events = list(
        session.scalars(
            select(Event)
            .where(
                Event.person_id == person_id,
                Event.type.in_(["switch_group", "switch_party"]),
            )
            .order_by(Event.event_date.is_(None), Event.event_date, Event.id)
        )
    )

    org_ids = {m.on_behalf_of_id for m, _ in rows if m.on_behalf_of_id}
    org_ids.update(e.from_org_id for e in events if e.from_org_id)
    org_ids.update(e.to_org_id for e in events if e.to_org_id)
    orgs = (
        {o.id: o for o in session.scalars(select(Organization).where(Organization.id.in_(org_ids)))}
        if org_ids
        else {}
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

        if is_group(org):
            if prev_group is not None and prev_group.id != org.id:
                _emit(
                    {
                        "field": "group",
                        "from": _label(prev_group),
                        "to": _label(org),
                        "date": start,
                        "org": _label(org),
                        "event_type": "switch_group",
                        "source_url": m.source_url,
                    }
                )
            prev_group = org

            party_id = m.on_behalf_of_id
            if party_id and prev_party_id and party_id != prev_party_id:
                _emit(
                    {
                        "field": "party",
                        "from": _label(orgs.get(prev_party_id)),
                        "to": _label(orgs.get(party_id)),
                        "date": start,
                        "org": _label(org),
                        "event_type": "switch_party",
                        "source_url": m.source_url,
                    }
                )
            if party_id:
                prev_party_id = party_id

        if org.id in role_by_org and role_by_org[org.id] != m.role:
            _emit(
                {
                    "field": "role",
                    "from": role_by_org[org.id],
                    "to": m.role,
                    "date": start,
                    "org": _label(org),
                    "event_type": "role_change",
                    "source_url": m.source_url,
                }
            )
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
        history.append(
            {
                "field": field,
                "from": key[2],
                "to": key[3],
                "date": date,
                "event_type": e.type,
                "source_url": None,
            }
        )

    # Newest first; null dates last; stable for equal dates.
    history.sort(key=lambda r: r["date"] or "", reverse=True)
    history.sort(key=lambda r: r["date"] is None)
    return {"person_id": person_id, "history": history}


def get_movements(
    session: Session,
    person_id: str | None,
    chamber: str | None,
    start: date | None,
    end: date | None,
    limit: int = 200,
    legislature: str | None = None,
) -> list[dict]:
    stmt = select(Event).where(Event.type.in_(["switch_group", "switch_party"]))
    if person_id:
        stmt = stmt.where(Event.person_id == person_id)
    if chamber:
        stmt = stmt.where(Event.chamber == chamber)
    if legislature:
        stmt = stmt.where(Event.legislature == legislature)
    if start:
        stmt = stmt.where(Event.event_date >= start)
    if end:
        stmt = stmt.where(Event.event_date <= end)
    evs = session.scalars(stmt.order_by(Event.event_date.desc()).limit(limit)).all()
    return [serialize_event(session, e) for e in evs]


def get_recent_events(
    session: Session,
    limit: int = 50,
    chamber: str | None = None,
    legislature: str | None = None,
) -> list[dict]:
    stmt = select(Event)
    # P3-B: the client sends chamber/legislature on /events/recent; honour them
    # here instead of silently ignoring them in the router.
    if chamber:
        stmt = stmt.where(Event.chamber == chamber)
    if legislature:
        stmt = stmt.where(Event.legislature == legislature)
    evs = session.scalars(
        stmt.order_by(Event.event_date.desc(), Event.detected_at.desc()).limit(limit)
    ).all()
    return [serialize_event(session, e) for e in evs]


def get_cross_chamber_careers(session: Session, as_of: date) -> list[dict]:
    """Return people with a recorded mandate in both chambers by the given date."""
    rows = session.execute(
        select(
            Person.id,
            Person.canonical_name,
            Mandate.chamber,
            Mandate.legislature,
        )
        .join(Mandate, Mandate.person_id == Person.id)
        .where(
            Mandate.chamber.in_(("deputies", "senate")),
            Mandate.start_date.is_not(None),
            Mandate.start_date <= as_of,
        )
        .order_by(Person.canonical_name, Mandate.chamber, Mandate.legislature)
    ).all()

    careers: dict[str, dict] = {}
    for person_id, name, chamber, legislature in rows:
        career = careers.setdefault(
            person_id,
            {
                "person_id": person_id,
                "name": name,
                "chambers": set(),
                "deputies": set(),
                "senate": set(),
            },
        )
        career["chambers"].add(chamber)
        if legislature:
            career[chamber].add(legislature)

    return [
        {
            "person_id": career["person_id"],
            "name": career["name"],
            "chambers": sorted(career["chambers"]),
            "deputies": sorted(career["deputies"]),
            "senate": sorted(career["senate"]),
        }
        for career in careers.values()
        if len(career["chambers"]) == 2
    ]


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
                "chamber": c.chamber,
                "legislature": c.legislature,
                "period_start": c.period_start.isoformat() if c.period_start else None,
                "period_end": c.period_end.isoformat() if c.period_end else None,
                "completeness": c.completeness,
                "note": c.note,
            }
            snap = by_key.get((c.chamber, c.legislature))
            if snap is not None:
                item["persons"] = snap["persons"]
            out.append(item)
        return out
    return derived


def get_coverage_detailed(session: Session) -> list[dict]:
    """Detailed coverage matrix with per-scope data quality stats.

    For each chamber/legislature scope: total memberships, % dated
    (start_date present), % with source URL, % of switch events with
    source URL, and last refresh timestamp.

    Optimised: two GROUP BY queries replace N×5 per-scope scalar queries.
    """
    derived = coverage_snapshot(session)
    by_key = {(r["chamber"], r["legislature"]): r for r in derived}
    persisted_rows = list(session.scalars(select(Coverage)))
    scopes = (
        [
            {
                "chamber": c.chamber,
                "legislature": c.legislature,
                "period_start": c.period_start,
                "period_end": c.period_end,
                "completeness": c.completeness,
                "note": c.note,
            }
            for c in persisted_rows
        ]
        if persisted_rows
        else derived
    )

    # --- Batched membership stats (1 query) ---
    # Group semantics: committee memberships are not party/group tenures and
    # must not inflate "total memberships" or skew the dated/sourced ratios.
    mem_rows = session.execute(
        select(
            Membership.chamber,
            Membership.legislature,
            func.count(Membership.id).label("total"),
            func.sum(case((Membership.start_date.is_not(None), 1), else_=0)).label("dated"),
            func.sum(case((Membership.source_url.is_not(None), 1), else_=0)).label("sourced"),
        )
        .join(Organization, Organization.id == Membership.org_id)
        .where(is_group())
        .group_by(Membership.chamber, Membership.legislature)
    ).all()
    mem_stats: dict[tuple, tuple] = {
        (r.chamber, r.legislature): (r.total or 0, r.dated or 0, r.sourced or 0) for r in mem_rows
    }

    # --- Batched event stats (1 query) ---
    # ``last_refresh`` keeps its original meaning: the newest event of ANY type
    # in the scope. Only the switch counters are restricted to switch events,
    # so those are computed with conditional aggregates.
    switch_types = ("switch_group", "switch_party")
    is_switch = Event.type.in_(switch_types)
    ev_rows = session.execute(
        select(
            Event.chamber,
            Event.legislature,
            func.sum(case((is_switch, 1), else_=0)).label("total"),
            func.sum(case((and_(is_switch, Event.source_url.is_not(None)), 1), else_=0)).label(
                "sourced"
            ),
            func.max(Event.detected_at).label("last_refresh"),
        ).group_by(Event.chamber, Event.legislature)
    ).all()
    ev_stats: dict[tuple, tuple] = {
        (r.chamber, r.legislature): (r.total or 0, r.sourced or 0, r.last_refresh) for r in ev_rows
    }

    out = []
    for c in scopes:
        chamber = c["chamber"]
        legislature = c["legislature"]
        key = (chamber, legislature)
        snap = by_key.get(key)

        total_memberships, dated_memberships, sourced_memberships = mem_stats.get(key, (0, 0, 0))
        total_switches, sourced_switches, last_refresh = ev_stats.get(key, (0, 0, None))

        item = {
            "chamber": chamber,
            "legislature": legislature,
            "period_start": c["period_start"].isoformat()
            if isinstance(c["period_start"], date)
            else c["period_start"],
            "period_end": c["period_end"].isoformat()
            if isinstance(c["period_end"], date)
            else c["period_end"],
            "completeness": c["completeness"],
            "note": c["note"],
            "persons": snap["persons"] if snap else c.get("persons", 0),
            "total_memberships": total_memberships,
            "dated_pct": round(100 * dated_memberships / total_memberships, 1)
            if total_memberships
            else None,
            "sourced_pct": round(100 * sourced_memberships / total_memberships, 1)
            if total_memberships
            else None,
            "total_switches": total_switches,
            "sourced_switches_pct": round(100 * sourced_switches / total_switches, 1)
            if total_switches
            else None,
            "last_refresh": last_refresh.isoformat() if last_refresh else None,
        }
        out.append(item)
    return out


def get_meta(session: Session) -> dict:
    legs = {}
    for ke in session.scalars(select(KeyEvent).where(KeyEvent.type == "legislature")):
        legs.setdefault(
            ke.label,
            {
                "label": ke.label,
                "start": ke.start_date.isoformat() if ke.start_date else None,
                "end": ke.end_date.isoformat() if ke.end_date else None,
            },
        )
    groups = [
        _org_brief(session, o.id) for o in session.scalars(select(Organization).where(is_group()))
    ]
    return {"legislatures": legs, "groups": groups}


def get_party_profile(session: Session, short_name: str, as_of: date) -> dict:
    """Get party profile with membership counts and switch stats for a given date."""
    org = session.scalars(
        select(Organization).where(
            Organization.short_name == short_name, Organization.classification == "party"
        )
    ).first()
    if not org:
        raise HTTPException(status_code=404, detail="party not found")

    # Current members belong to the legislature active on as_of. Historical
    # ledger rows may have no end date, so date-only filtering counts them too.
    legislature = _legislature_for(session, as_of)
    current_members = (
        session.scalar(
            select(func.count(func.distinct(Membership.person_id)))
            .select_from(Membership)
            .join(Organization, Organization.id == Membership.org_id)
            .where(
                is_group(),
                Membership.on_behalf_of_id == org.id,
                Membership.chamber.in_(["deputies", "senate"]),
                Membership.legislature == legislature,
                Membership.start_date <= as_of,
                (Membership.end_date.is_(None)) | (Membership.end_date > as_of),
            )
        )
        if legislature
        else 0
    ) or 0

    # Distinguish an observed zero from a corpus with no dated party-switch data.
    has_dated_party_switches = (
        session.scalar(
            select(func.count(Event.id)).where(
                Event.type == "switch_party",
                Event.event_date.is_not(None),
            )
        )
        or 0
    ) > 0
    if has_dated_party_switches:
        switches_in = (
            session.scalar(
                select(func.count()).select_from(
                    select(Event)
                    .where(
                        Event.type == "switch_party",
                        Event.to_org_id == org.id,
                        Event.event_date.is_not(None),
                        Event.event_date <= as_of,
                    )
                    .subquery()
                )
            )
            or 0
        )

        switches_out = (
            session.scalar(
                select(func.count()).select_from(
                    select(Event)
                    .where(
                        Event.type == "switch_party",
                        Event.from_org_id == org.id,
                        Event.event_date.is_not(None),
                        Event.event_date <= as_of,
                    )
                    .subquery()
                )
            )
            or 0
        )
        net_change = switches_in - switches_out
    else:
        switches_in = switches_out = net_change = None

    return {
        "id": org.id,
        "name": org.name,
        "short_name": org.short_name,
        "color": org.color,
        "wikidata_qid": org.wikidata_qid,
        "current_members": current_members,
        "switches_in": switches_in,
        "switches_out": switches_out,
        "net_change": net_change,
    }


def get_party_movements(
    session: Session, short_name: str, as_of: date, limit: int = 50
) -> list[dict]:
    """Get movements (join/switch_party/leave) for a specific party."""
    org = session.scalars(
        select(Organization).where(
            Organization.short_name == short_name, Organization.classification == "party"
        )
    ).first()
    if not org:
        raise HTTPException(status_code=404, detail="party not found")

    stmt = (
        select(Event)
        .where(
            Event.type.in_(["switch_party", "join", "leave"]),
            Event.event_date.is_not(None),
            Event.event_date <= as_of,
            (Event.from_org_id == org.id) | (Event.to_org_id == org.id),
        )
        .order_by(Event.event_date.desc())
        .limit(limit)
    )

    evs = session.scalars(stmt).all()
    return [serialize_event(session, e) for e in evs]


def get_party_timeline(session: Session, short_name: str, from_date: date, to_date: date) -> dict:
    """Get group size timeline for a specific party over a date range."""
    org = session.scalars(
        select(Organization).where(
            Organization.short_name == short_name, Organization.classification == "party"
        )
    ).first()
    if not org:
        raise HTTPException(status_code=404, detail="party not found")

    from datetime import timedelta

    from pipeline.queries import chamber_composition

    dates = []
    d = from_date
    step = 30
    while d <= to_date:
        dates.append(d)
        d += timedelta(days=step)
    if not dates:
        # from_date > to_date: no valid range, return an empty series instead of
        # raising IndexError (the HTTP route already rejects this with 422).
        return {"dates": [], "total": [], "groups": {}}
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
