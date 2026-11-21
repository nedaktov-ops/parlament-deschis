"""Statistical view of traseism: who moved between parliamentary groups.

The unit of observation is a **group switch**: the same person changes
parliamentary group inside the SAME chamber and the SAME legislature, where
the previous tenure has a published leave date and the next tenure starts on
or after it. These are recorded as ``switch_group`` events by
:func:`pipeline.events.derive_group_events`, which enforces exactly that rule.

The denominator is **members at risk**: distinct people who held a
parliamentary-group seat in the scope. Membership *rows* are never used as a
head-count, because one member contributes several rows.

Everything here is a count of **observed movement**. It says nothing about
motives, and a switch into "unaffiliated" is a loss for the party and a move
to the unaffiliated group, not a gain for a rival.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from .db import Coverage, Event, KeyEvent, Membership, Organization, Person
from .queries import is_group

DAYS_PER_MONTH = 30.44

# The unaffiliated bucket is a parliamentary status, not a party. A member who
# leaves a party, sits unaffiliated and then joins another party has made ONE
# party change, not two.
NO_PARTY = {"NEAFILIATI", "NEAFILIAȚI", "NEAFILIAŢI", "INDEPENDENT", "NEAFILIAT"}


def _switch_query(chamber: str | None, legislature: str | None):
    stmt = select(Event).where(Event.type == "switch_group")
    if chamber:
        stmt = stmt.where(Event.chamber == chamber)
    if legislature:
        stmt = stmt.where(Event.legislature == legislature)
    return stmt


def _member_query(chamber: str | None, legislature: str | None):
    stmt = (
        select(func.count(func.distinct(Membership.person_id)))
        .join(Organization, Organization.id == Membership.org_id)
        .where(is_group())
    )
    if chamber:
        stmt = stmt.where(Membership.chamber == chamber)
    if legislature:
        stmt = stmt.where(Membership.legislature == legislature)
    return stmt


def _period(session: Session, chamber: str | None, legislature: str | None):
    """Start and end of the scope, from the legislature key events."""
    stmt = select(KeyEvent).where(KeyEvent.type == "legislature")
    if legislature:
        stmt = stmt.where(KeyEvent.label == legislature)
    rows = list(session.scalars(stmt))
    if not rows:
        return None, None
    starts = [r.start_date for r in rows if r.start_date]
    ends = [r.end_date for r in rows if r.end_date]
    start = min(starts) if starts else None
    end = max(ends) if ends else date.today()
    return start, end


def _org_map(session: Session, ids: set[str]) -> dict[str, str]:
    if not ids:
        return {}
    orgs = list(session.scalars(select(Organization).where(Organization.id.in_(ids))))
    return {o.id: (o.short_name or o.name) for o in orgs}


def _seats_at(session: Session, org_id: str, on: date | None, chamber, legislature) -> int:
    if on is None:
        return 0
    stmt = select(func.count(func.distinct(Membership.person_id))).where(
        Membership.org_id == org_id,
        Membership.start_date <= on,
    )
    stmt = stmt.where((Membership.end_date.is_(None)) | (Membership.end_date > on))
    if chamber:
        stmt = stmt.where(Membership.chamber == chamber)
    if legislature:
        stmt = stmt.where(Membership.legislature == legislature)
    return int(session.scalar(stmt) or 0)


def traseism_summary(
    session: Session, *, chamber: str | None = None, legislature: str | None = None
) -> dict:
    """The statistical summary for one scope (both scopes optional)."""
    events = list(session.scalars(_switch_query(chamber, legislature)))
    members = int(session.scalar(_member_query(chamber, legislature)) or 0)
    switchers = len({e.person_id for e in events})
    start, end = _period(session, chamber, legislature)

    # Collect org_ids only from the current scope (legislature + chamber).
    # Events are already filtered by legislature/chamber in _switch_query.
    org_ids = {e.from_org_id for e in events if e.from_org_id}
    org_ids |= {e.to_org_id for e in events if e.to_org_id}
    # Add groups that have members in this scope even if no switches.
    org_ids |= set(
        session.scalars(
            select(Membership.org_id)
            .join(Organization, Organization.id == Membership.org_id)
            .where(
                is_group(),
                Membership.chamber == chamber,
                Membership.legislature == legislature,
            )
        )
    )
    labels = _org_map(session, org_ids)

    # Build per-party movement table. Multiple groups can share a party
    # label (e.g. several groups all called "AUR"), so merge entries by
    # party label instead of emitting one row per group org_id.
    by_party_map: dict[str, dict] = {}
    for org_id in org_ids:
        label = labels.get(org_id, org_id) or "?"
        entry = by_party_map.get(label)
        if entry is None:
            entry = {
                "party": label,
                "gains": 0,
                "losses": 0,
                "net": 0,
                "seats_start": 0,
                "seats_end": 0,
            }
            by_party_map[label] = entry
        gains = sum(1 for e in events if e.to_org_id == org_id)
        losses = sum(1 for e in events if e.from_org_id == org_id)
        entry["gains"] += gains
        entry["losses"] += losses
        entry["net"] = entry["gains"] - entry["losses"]
        entry["seats_start"] += _seats_at(session, org_id, start, chamber, legislature) or 0
        entry["seats_end"] += _seats_at(session, org_id, end, chamber, legislature) or 0

    by_party = sorted(
        by_party_map.values(), key=lambda e: (-(e["gains"] + e["losses"]), e["party"])
    )

    matrix: dict[tuple[str, str], int] = {}
    for e in events:
        key = (labels.get(e.from_org_id, "?"), labels.get(e.to_org_id, "?"))
        matrix[key] = matrix.get(key, 0) + 1

    per_person: dict[str, int] = {}
    for e in events:
        per_person[e.person_id] = per_person.get(e.person_id, 0) + 1
    repeat = [n for n in per_person.values() if n >= 2]

    months: list[float] = []
    month_counts: dict[int, int] = {}
    for e in events:
        if e.event_date is None or start is None:
            continue
        delta = (e.event_date - start).days
        m = max(0, round(delta / DAYS_PER_MONTH, 1))
        months.append(m)
        month_counts[int(m)] = month_counts.get(int(m), 0) + 1

    cov_stmt = select(Coverage)
    if chamber:
        cov_stmt = cov_stmt.where(Coverage.chamber == chamber)
    if legislature:
        cov_stmt = cov_stmt.where(Coverage.legislature == legislature)
    coverage_rows = list(session.scalars(cov_stmt))
    if coverage_rows:
        completeness = coverage_rows[0].completeness
        note = coverage_rows[0].note
    else:
        completeness, note = "unknown", None

    return {
        "legislature": legislature,
        "chamber": chamber,
        "period": {
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
        },
        "members": members,
        "switches": len(events),
        "switchers": switchers,
        "switch_rate": (switchers / members) if members else 0.0,
        "switches_per_100_members": (len(events) / members * 100) if members else 0.0,
        "party": party_summary(session, chamber=chamber, legislature=legislature),
        "by_party": by_party,
        "matrix": [
            {"from": frm, "to": to, "count": count}
            for (frm, to), count in sorted(matrix.items(), key=lambda kv: -kv[1])
        ],
        "repeat_switchers": {
            "people": len(repeat),
            "max_switches": max(repeat) if repeat else 0,
        },
        "timing": {
            "median_months": round(statistics.median(months), 1) if months else None,
            "by_month": [{"month": m, "count": c} for m, c in sorted(month_counts.items())],
        },
        "coverage": {"completeness": completeness, "note": note},
        "definitions": {
            "switches": "Group switches only (Event.type='switch_group'); this is NOT the dashboard all-events total.",
            "party.switches": "Party changes with the unaffiliated bucket skipped, derived from dated group memberships.",
            "members": "Distinct persons holding a parliamentary-group seat in scope.",
            "switch_rate": "switchers / members (distinct people, not events).",
            "switches_per_100_members": "switches / members * 100.",
        },
    }


def traseism_switches(
    session: Session,
    *,
    chamber: str | None = None,
    legislature: str | None = None,
    group: str | None = None,
    person: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """The switch ledger: one row per observed switch, with its source."""
    stmt = _switch_query(chamber, legislature)
    events = list(session.scalars(stmt.order_by(Event.event_date, Event.person_id)))
    labels = _org_map(session, {e.from_org_id for e in events} | {e.to_org_id for e in events})
    names = (
        {
            p.id: p.canonical_name
            for p in session.scalars(
                select(Person).where(Person.id.in_({e.person_id for e in events}))
            )
        }
        if events
        else {}
    )

    rows = []
    for e in events:
        label_from = labels.get(e.from_org_id, "")
        label_to = labels.get(e.to_org_id, "")
        if group and group not in (label_from, label_to):
            continue
        if person and person.lower() not in (names.get(e.person_id, "") or "").lower():
            continue
        rows.append(
            {
                "person_id": e.person_id,
                "name": names.get(e.person_id, ""),
                "from_group": label_from,
                "to_group": label_to,
                "date": e.event_date.isoformat() if e.event_date else None,
                "legislature": e.legislature,
                "chamber": e.chamber,
                "source_url": e.source_url,
                "precision": e.precision,
            }
        )
    return {"rows": rows[offset : offset + limit], "total": len(rows)}


def traseism_overview(session: Session) -> list[dict]:
    """One summary row per chamber/legislature that has data."""
    pairs = session.execute(
        select(Membership.chamber, Membership.legislature)
        .join(Organization, Organization.id == Membership.org_id)
        .where(is_group())
        .distinct()
    ).all()
    rows = []
    for chamber, legislature in sorted(pairs, key=lambda p: (p[1] or "", p[0] or "")):
        summary = traseism_summary(session, chamber=chamber, legislature=legislature)
        rows.append(
            {
                "legislature": summary["legislature"],
                "chamber": summary["chamber"],
                "period": summary["period"],
                "members": summary["members"],
                "switches": summary["switches"],
                "switchers": summary["switchers"],
                "switch_rate": summary["switch_rate"],
                "switches_per_100_members": summary["switches_per_100_members"],
                "party": summary["party"],
                "by_party": summary["by_party"],
                "matrix": summary["matrix"],
                "repeat_switchers": summary["repeat_switchers"],
                "timing": summary["timing"],
                "coverage": summary["coverage"],
                "definitions": summary["definitions"],
            }
        )
    return rows


# --- Party-level view ------------------------------------------------------
# A *group* switch is every change of parliamentary group, including a step
# into or out of the unaffiliated bucket. A *party* switch is a change of the
# party the member belonged to. The two differ whenever a member passes
# through the unaffiliated bucket, which is the usual way a defection is
# recorded in the official ledgers.


def _party_label(raw: str | None) -> str | None:
    if not raw:
        return None
    label = raw.strip()
    if not label or label.upper() in NO_PARTY:
        return None
    return label.upper()


def _party_rows(session: Session, chamber: str | None, legislature: str | None):
    """Memberships with the party behind the group, scoped."""
    party_org = aliased(Organization)
    stmt = (
        select(
            Membership.person_id,
            Membership.chamber,
            Membership.legislature,
            Membership.org_id,
            Membership.start_date,
            Membership.end_date,
            Membership.source_url,
            Membership.confidence,
            party_org.short_name.label("party_short_name"),
            Organization.short_name.label("group_short_name"),
        )
        .join(Organization, Organization.id == Membership.org_id)
        .outerjoin(party_org, party_org.id == Membership.on_behalf_of_id)
        .where(is_group())
    )
    if chamber:
        stmt = stmt.where(Membership.chamber == chamber)
    if legislature:
        stmt = stmt.where(Membership.legislature == legislature)
    return session.execute(stmt).all()


def party_switches(
    session: Session, *, chamber: str | None = None, legislature: str | None = None
) -> list[dict]:
    """Every observed party change, with the dates and sources that prove it.

    The unaffiliated bucket is skipped, so ``PSD -> unaffiliated -> PRO`` is
    one party switch (PSD -> PRO) dated at the PRO join.
    """
    rows = _party_rows(session, chamber, legislature)
    by_person: dict[tuple[str, str, str], list] = defaultdict(list)
    for r in rows:
        key = (r.person_id, r.chamber or "", r.legislature or "")
        by_person[key].append(r)

    out: list[dict] = []
    for (person_id, ch, leg), items in by_person.items():
        items.sort(
            key=lambda r: (
                r.start_date or date.min,
                r.end_date or date.max,
                r.org_id,
            )
        )
        # Collapse into party episodes, dropping the unaffiliated stretches.
        episodes: list[dict] = []
        for r in items:
            party = _party_label(r.party_short_name)
            if party is None:
                continue
            if episodes and episodes[-1]["party"] == party:
                # Same party again: extend the episode.
                episodes[-1]["end_date"] = r.end_date
                continue
            episodes.append(
                {
                    "party": party,
                    "start_date": r.start_date,
                    "end_date": r.end_date,
                    "source_url": r.source_url,
                    "group": r.group_short_name,
                    "confidence": r.confidence,
                }
            )
        for prev, nxt in zip(episodes, episodes[1:], strict=False):
            if prev["party"] == nxt["party"]:
                continue
            out.append(
                {
                    "person_id": person_id,
                    "chamber": ch,
                    "legislature": leg,
                    "from_party": prev["party"],
                    "to_party": nxt["party"],
                    "date": nxt["start_date"],
                    "from_date": prev["end_date"],
                    "source_url": nxt["source_url"],
                    "from_source_url": prev["source_url"],
                    "confidence": nxt["confidence"],
                }
            )
    out.sort(key=lambda e: (e["date"] or date.min, e["person_id"]))
    return out


def party_summary(
    session: Session, *, chamber: str | None = None, legislature: str | None = None
) -> dict:
    """Party-level counters: switches, switchers, entries and exits."""
    switches = party_switches(session, chamber=chamber, legislature=legislature)
    switchers = len({s["person_id"] for s in switches})

    rows = _party_rows(session, chamber, legislature)
    by_person: dict[tuple[str, str, str], list] = defaultdict(list)
    for r in rows:
        by_person[(r.person_id, r.chamber or "", r.legislature or "")].append(r)

    entries = 0
    exits = 0
    for items in by_person.values():
        items.sort(key=lambda r: (r.start_date or date.min, r.end_date or date.max))
        parties = [_party_label(r.party_short_name) for r in items]
        real = [p for p in parties if p]
        if not real:
            continue
        # A member who was unaffiliated first and then joined a party.
        if parties[0] is None and real[0] is not None:
            first_party_idx = parties.index(real[0])
            if first_party_idx > 0:
                entries += 1
        # A member whose last party was followed only by unaffiliated.
        if parties[-1] is None and real[-1] is not None:
            exits += 1

    members = int(session.scalar(_member_query(chamber, legislature)) or 0)
    matrix: dict[tuple[str, str], int] = defaultdict(int)
    for s in switches:
        matrix[(s["from_party"], s["to_party"])] += 1

    return {
        "switches": len(switches),
        "switchers": switchers,
        "switch_rate": (switchers / members) if members else 0.0,
        "switches_per_100_members": (len(switches) / members * 100) if members else 0.0,
        "entries": entries,
        "exits": exits,
        "matrix": [
            {"from": frm, "to": to, "count": count}
            for (frm, to), count in sorted(matrix.items(), key=lambda kv: -kv[1])
        ],
    }
