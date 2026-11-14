"""Read API endpoints for the dashboard."""

from __future__ import annotations

import os
import secrets
from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from backend import queries
from backend.config import APP_VERSION
from backend.deps import get_db
from pipeline.analytics import derive_all_switch_waves, derive_switch_waves
from pipeline.db import Evidence
from pipeline.export import CODE_LICENSE, DATA_LICENSE, PROJECT_URL
from pipeline.poller import run_poll_cycle, source_health

router = APIRouter(prefix="/api")

METHODOLOGY_RO = [
    "Fiecare mandat are date de început/sfârșit, precizie temporală și un nivel "
    "de încredere (ledger oficial, profil oficial, derivat, comunitate).",
    "Fiecare afirmație trimite la o sursă primară datată (cdep.ro, senat.ro) sau "
    "la un identificator Wikidata; nu publicăm inferențe fără sursă.",
    "Acoperirea este raportată onest per cameră și legislatură, cu numărul de "
    "persoane ingerate și starea completitudinii (full/partial/none).",
    "Sursa de adevăr este baza de date temporală: istoricul se recalculează "
    "determinist din fapte stocate, nu din text narativ.",
]

METHODOLOGY_EN = [
    "Every tenure carries start/end dates, temporal precision and a confidence "
    "level (official ledger, official profile, derived, community).",
    "Every claim points to a dated primary source (cdep.ro, senat.ro) or a "
    "Wikidata identifier; no source-free inference is published.",
    "Coverage is reported honestly per chamber and legislature, with ingested "
    "person counts and a completeness state (full/partial/none).",
    "The temporal database is the source of truth: history is recomputed "
    "deterministically from stored facts, never from narrative text.",
]


def _parse_date(s: str | None, default: date) -> date:
    if not s:
        return default
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"invalid date: {s}")


@router.get("/meta")
def meta(db: Session = Depends(get_db)):
    return queries.get_meta(db)


@router.get("/chamber")
def chamber(
    as_of: str | None = None,
    chamber: str = Query("deputies", pattern="^(deputies|senate)$"),
    db: Session = Depends(get_db),
):
    d = _parse_date(as_of, date.today())
    return queries.get_chamber(db, chamber, d)


@router.get("/timeline")
def timeline(
    chamber: str = Query("deputies", pattern="^(deputies|senate)$"),
    start: str | None = Query(None, alias="from"),
    end: str | None = Query(None, alias="to"),
    step_days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    today = date.today()
    s = _parse_date(start, date(today.year, 1, 1))
    e = _parse_date(end, today)
    if e < s:
        raise HTTPException(status_code=422, detail="to must be >= from")
    return queries.get_timeline(db, chamber, s, e, step_days)


@router.get("/persons")
def persons(
    q: str | None = None,
    chamber: str | None = Query(None, pattern="^(deputies|senate)$"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return queries.search_persons(db, q, chamber, limit)


@router.get("/persons/{person_id}/history")
def person_history(person_id: str, db: Annotated[Session, Depends(get_db)]):
    data = queries.get_person_history(db, person_id)
    if data is None:
        raise HTTPException(status_code=404, detail="person not found")
    return data


@router.get("/persons/{person_id}")
def person(person_id: str, db: Session = Depends(get_db)):
    data = queries.get_person(db, person_id)
    if data is None:
        raise HTTPException(status_code=404, detail="person not found")
    return data


@router.get("/movements")
def movements(
    person_id: str | None = None,
    chamber: str | None = Query(None, pattern="^(deputies|senate)$"),
    start: str | None = Query(None, alias="from"),
    end: str | None = Query(None, alias="to"),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    s = _parse_date(start, date(1990, 1, 1))
    e = _parse_date(end, date.today())
    return queries.get_movements(db, person_id, chamber, s, e, limit)


@router.get("/events/recent")
def recent_events(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    return queries.get_recent_events(db, limit)


@router.get("/coverage")
def coverage(db: Session = Depends(get_db)):
    return queries.get_coverage(db)


@router.get("/committees")
def committees(as_of: str | None = None, db: Session = Depends(get_db)):
    """Committee list with its controlling party, when committee data exists.

    Committee tenures are not ingested yet, so this returns an empty list (the
    UI renders its honest "no data" state) instead of the 404 the frontend used
    to receive. The endpoint exists so the contract is stable once committee
    memberships are loaded.
    """
    from sqlalchemy import select

    from pipeline.db import Organization

    _parse_date(as_of, date.today())  # validate as_of when supplied
    rows = db.scalars(
        select(Organization)
        .where(Organization.classification == "committee")
        .order_by(Organization.name)
    ).all()
    return [{"id": o.id, "name": o.name, "party": None} for o in rows]


@router.get("/evidence/{evidence_id}")
def evidence(evidence_id: str, db: Session = Depends(get_db)):
    ev = db.get(Evidence, evidence_id)
    if ev is None:
        raise HTTPException(status_code=404, detail="evidence not found")
    return {
        "id": ev.id,
        "membership_id": ev.membership_id,
        "type": ev.type,
        "source_url": ev.source_url,
        "snapshot_hash": ev.snapshot_hash,
        "snapshot_url": queries._snapshot_url(db, ev.snapshot_hash, ev.source_url),
        "note": ev.note,
        "observed_at": ev.observed_at.isoformat() if ev.observed_at else None,
    }


@router.get("/about")
def about(db: Annotated[Session, Depends(get_db)]):
    return {
        "name": "Parlament Deschis",
        "version": APP_VERSION,
        "description": "Romanian Parliament transparency tracker — party/group/committee "
        "memberships 1990→present, dated and source-cited.",
        "project_url": PROJECT_URL,
        "methodology": {"ro": METHODOLOGY_RO, "en": METHODOLOGY_EN},
        "sources": [
            {
                "name": "Camera Deputaților",
                "url": "https://www.cdep.ro",
                "note": "Group membership ledgers and deputy profiles (official).",
            },
            {
                "name": "Senatul României",
                "url": "https://www.senat.ro",
                "note": "Senator profiles and parliamentary group listings (official).",
            },
            {
                "name": "Wikidata",
                "url": "https://www.wikidata.org",
                "note": "Cross-chamber person identity reconciliation (community).",
            },
        ],
        "licenses": {
            "code": CODE_LICENSE,
            "data": DATA_LICENSE,
            "code_url": "https://www.gnu.org/licenses/agpl-3.0.html",
            "data_url": "https://creativecommons.org/licenses/by/4.0/",
        },
        "coverage": queries.get_coverage(db),
        "freshness": source_health(db),
        "generated_at": datetime.now(UTC).isoformat(),
    }


@router.get("/party/{short_name}")
def party_profile(
    short_name: str,
    as_of: str | None = None,
    db: Session = Depends(get_db),
):
    d = _parse_date(as_of, date.today())
    return queries.get_party_profile(db, short_name, d)


@router.get("/party/{short_name}/movements")
def party_movements(
    short_name: str,
    as_of: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    d = _parse_date(as_of, date.today())
    return queries.get_party_movements(db, short_name, d, limit)


@router.get("/party/{short_name}/timeline")
def party_timeline(
    short_name: str,
    from_date: str = Query(..., alias="from"),
    to: str = Query(..., alias="to"),
    db: Session = Depends(get_db),
):
    s = _parse_date(from_date, date(2024, 12, 21))
    e = _parse_date(to, date.today())
    if e < s:
        raise HTTPException(status_code=422, detail="to must be >= from")
    return queries.get_party_timeline(db, short_name, s, e)


@router.post("/admin/poll")
def admin_poll(
    db: Annotated[Session, Depends(get_db)],
    legislature: str = Query("2024", pattern=r"^\d{4}$"),
    x_admin_token: Annotated[str | None, Header()] = None,
):
    """Run one poll cycle synchronously. Token-guarded; disabled by default."""
    expected = os.environ.get("PARLAMENT_ADMIN_TOKEN", "")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="admin polling disabled (set PARLAMENT_ADMIN_TOKEN)",
        )
    if not x_admin_token or not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=401, detail="invalid admin token")
    try:
        results = run_poll_cycle(db, legislature)
    except Exception as exc:  # noqa: BLE001 - report upstream failure as 502
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"status": "ok", "legislature": legislature, "results": results}


@router.get("/health")
def health(db: Session = Depends(get_db)):
    return {"status": "ok", "sources": source_health(db)}


@router.get("/analytics/waves")
def analytics_waves(
    chamber: str | None = Query(None, pattern="^(deputies|senate)$"),
    legislature: str | None = Query(None, pattern=r"^\d{4}$"),
    window_days: int = Query(30, ge=1, le=180),
    min_switches: int = Query(3, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Detect party switch waves in the given chamber/legislature."""
    count = derive_switch_waves(
        db,
        chamber=chamber,
        legislature=legislature,
        window_days=window_days,
        min_switches=min_switches,
    )
    return {"status": "ok", "created": count}


@router.get("/analytics/waves/recompute")
def analytics_waves_recompute(
    db: Session = Depends(get_db),
):
    """Recompute all switch waves from scratch."""

    count = derive_all_switch_waves(db)
    return {"status": "ok", "created": count}


@router.get("/analytics/switch-waves")
def get_switch_waves(
    chamber: str | None = Query(None, pattern="^(deputies|senate)$"),
    legislature: str | None = Query(None, pattern=r"^\d{4}$"),
    db: Session = Depends(get_db),
):
    """Get stored switch waves."""
    from sqlalchemy import select

    from pipeline.db import SwitchWave

    stmt = select(SwitchWave).order_by(SwitchWave.start_date.desc())
    if chamber:
        stmt = stmt.where(SwitchWave.chamber == chamber)
    if legislature:
        stmt = stmt.where(SwitchWave.legislature == legislature)

    waves = db.scalars(stmt).all()
    return [
        {
            "id": w.id,
            "label": w.label,
            "start_date": w.start_date.isoformat() if w.start_date else None,
            "end_date": w.end_date.isoformat() if w.end_date else None,
            "switch_count": w.switch_count,
            "trigger_type": w.trigger_type,
            "trigger_event": w.trigger_event,
            "legislature": w.legislature,
            "chamber": w.chamber,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in waves
    ]


@router.get("/analytics/party-cohesion")
def get_party_cohesion(
    legislature: str | None = Query(None, pattern=r"^\d{4}$"),
    db: Session = Depends(get_db),
):
    """Get party cohesion index per party per legislature."""

    # Run the analysis and return results
    from collections import defaultdict

    from sqlalchemy import select

    from pipeline.db import Event, KeyEvent, Membership, Organization

    stmt = select(Event).where(Event.type == "switch_party")
    if legislature:
        leg_key = db.scalars(
            select(KeyEvent).where(KeyEvent.type == "legislature", KeyEvent.label == legislature)
        ).first()
        if leg_key and leg_key.start_date and leg_key.end_date:
            stmt = stmt.where(
                Event.event_date >= leg_key.start_date, Event.event_date <= leg_key.end_date
            )
    stmt = stmt.where(Event.event_date.is_not(None))

    switches = list(db.scalars(stmt))

    party_switches: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for sw in switches:
        if sw.to_org_id:
            org = db.get(Organization, sw.to_org_id)
            if org and org.classification == "party":
                party_switches[sw.to_org_id][sw.person_id] += 1
            elif org and org.classification == "group":
                # on_behalf_of_id is a Membership column, not an Organization one.
                m = db.scalars(
                    select(Membership)
                    .where(
                        Membership.person_id == sw.person_id,
                        Membership.org_id == org.id,
                        Membership.on_behalf_of_id.is_not(None),
                    )
                    .order_by(Membership.start_date.desc())
                ).first()
                if m and m.on_behalf_of_id:
                    party_switches[m.on_behalf_of_id][sw.person_id] += 1

    results = []
    for party_id, person_switches in party_switches.items():
        party = db.get(Organization, party_id)
        if not party or party.classification != "party":
            continue

        party_memberships = db.scalars(
            select(Membership)
            .join(Organization, Organization.id == Membership.org_id)
            .where(Organization.id == party_id)
        ).all()

        total_switches = sum(person_switches.values())
        num_switchers = len(person_switches)
        num_members = len(set(m.person_id for m in party_memberships))

        if num_members == 0:
            continue

        total_tenure_years = 0
        for m in party_memberships:
            if m.start_date and m.end_date:
                total_tenure_years += (m.end_date - m.start_date).days / 365.25
            elif m.start_date:
                total_tenure_years += (date.today() - m.start_date).days / 365.25

        avg_tenure = total_tenure_years / num_members if num_members > 0 else 0

        if avg_tenure == 0:
            continue

        switch_rate = (
            total_switches / (num_members * avg_tenure) if num_members * avg_tenure > 0 else 0
        )

        party_label = party.short_name or party.name or "Unknown"
        results.append(
            {
                "party_id": party.id,
                "party_name": party_label,
                "members": num_members,
                "switches": total_switches,
                "switchers": num_switchers,
                "avg_tenure_years": round(avg_tenure, 1),
                "switch_rate_per_mp_per_year": round(switch_rate, 4),
            }
        )

    return {"status": "ok", "data": results}


@router.get("/analytics/cross-chamber")
def get_cross_chamber(
    db: Session = Depends(get_db),
):
    """Get MPs with memberships in both chambers."""
    from sqlalchemy import select

    from pipeline.db import Membership, Person

    stmt = select(Person.id, Person.canonical_name).distinct()
    persons = list(db.execute(stmt).all())

    results = []
    for pid, name in persons:
        chs = db.scalars(
            select(Membership.chamber).where(Membership.person_id == pid).distinct()
        ).all()
        if len(chs) > 1:
            results.append(
                {
                    "person_id": pid,
                    "name": name,
                    "chambers": chs,
                }
            )

    return {"status": "ok", "count": len(results), "data": results}


@router.get("/analytics/generational-shift")
def get_generational_shift(
    legislature: str | None = Query(None, pattern=r"^\d{4}$"),
    db: Session = Depends(get_db),
):
    """Get generational shift data per party."""
    from sqlalchemy import select

    from pipeline.db import KeyEvent, Membership, Organization, Person

    stmt = select(Person.id, Person.canonical_name, Person.birth_date)
    if legislature:
        leg_key = db.scalars(
            select(KeyEvent).where(KeyEvent.type == "legislature", KeyEvent.label == legislature)
        ).first()
        if leg_key and leg_key.start_date and leg_key.end_date:
            stmt = stmt.where(
                Person.id.in_(
                    select(Membership.person_id)
                    .where(Membership.start_date <= leg_key.end_date)
                    .where(
                        (Membership.end_date.is_(None))
                        | (Membership.end_date >= leg_key.start_date)
                    )
                )
            )

    persons = list(db.execute(stmt).all())
    ages_by_party: dict[str, list[int]] = {}

    for pid, name, bdate in persons:
        if not bdate:
            continue
        age = (date.today() - bdate).days / 365.25

        party_mems = db.scalars(
            select(Membership)
            .join(Organization, Organization.id == Membership.org_id)
            .where(Membership.person_id == pid)
            .where(Organization.classification == "party")
        ).all()

        for pm in party_mems:
            if pm.org and pm.org.short_name:
                party_key = pm.org.short_name
                ages_by_party.setdefault(party_key, []).append(int(age))

    results = []
    for party, ages in ages_by_party.items():
        if ages:
            avg_age = sum(ages) / len(ages)
            sorted_ages = sorted(ages)
            median_age = sorted_ages[len(sorted_ages) // 2]
            results.append(
                {
                    "party": party,
                    "mps_with_birth_dates": len(ages),
                    "avg_age": round(avg_age, 1),
                    "median_age": median_age,
                }
            )

    return {"status": "ok", "data": results}


# --- Traseism statistics ---------------------------------------------------
# The public view of party/group switching. Every number here is a count of
# OBSERVED movement taken from the chambers' own dated group ledgers.


@router.get("/traseism/overview")
def traseism_overview(db: Session = Depends(get_db)):
    """One row per chamber and legislature: members, switches, switchers, rate."""
    from pipeline.traseism import traseism_overview as _overview

    return _overview(db)


@router.get("/traseism/summary")
def traseism_summary(
    legislature: str | None = Query(None, pattern=r"^\d{4}$"),
    chamber: str | None = Query(None, pattern=r"^(deputies|senate)$"),
    db: Session = Depends(get_db),
):
    """The full statistical summary for one scope (both scopes optional)."""
    from pipeline.traseism import traseism_summary as _summary

    return _summary(db, chamber=chamber, legislature=legislature)


@router.get("/traseism/switches")
def traseism_switches(
    legislature: str | None = Query(None, pattern=r"^\d{4}$"),
    chamber: str | None = Query(None, pattern=r"^(deputies|senate)$"),
    group: str | None = Query(None, description="filter by group acronym (from or to)"),
    person: str | None = Query(None, description="filter by person name substring"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """The switch ledger. Every row carries the official source URL."""
    from pipeline.traseism import traseism_switches as _switches

    return _switches(
        db,
        chamber=chamber,
        legislature=legislature,
        group=group,
        person=person,
        limit=limit,
        offset=offset,
    )
