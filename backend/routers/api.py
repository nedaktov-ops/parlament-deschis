"""Read API endpoints for the dashboard."""

from __future__ import annotations

import json
import os
import secrets
import threading
from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from backend import queries
from backend.cache import cached as cache_result
from backend.cache import invalidate as invalidate_result_cache
from backend.config import APP_VERSION, DATASET_METADATA_PATH
from backend.deps import get_db
from pipeline.analytics import derive_all_switch_waves, derive_switch_waves
from pipeline.db import Evidence
from pipeline.export import (
    CODE_LICENSE,
    DATA_LICENSE,
    PROJECT_URL,
)
from pipeline.poller import run_poll_cycle, source_health

router = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------
# In-memory cache for the traseism overview. The DB is read-only at runtime
# so this result is immutable for the lifetime of the process. A lock guards
# the lazy-init so only one thread runs the expensive computation.
# ---------------------------------------------------------------------------
_traseism_overview_cache: list | None = None
_traseism_overview_lock = threading.Lock()


def invalidate_traseism_overview_cache() -> None:
    """Drop the memoised overview after the underlying data changes."""
    global _traseism_overview_cache
    with _traseism_overview_lock:
        _traseism_overview_cache = None


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
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"invalid date: {s}") from exc


def _require_admin_token(token: str | None, operation: str = "admin operations") -> None:
    """Fail-closed token check with a small in-process per-token lockout.

    State is held on the function object so the helper owns it (no module
    globals, no new dependencies). Only a saltless SHA-256 fingerprint of the
    guess is retained — raw secret values are never stored or logged. There is
    no request object in this helper's scope, so the key is per-token rather
    than per-IP; see the P4-D report for that residual.
    """
    import hashlib
    import logging
    import time

    state = getattr(_require_admin_token, "_auth_state", None)
    if state is None:
        state = {"lock": threading.Lock(), "failures": {}}
        _require_admin_token._auth_state = state
    lock = state["lock"]
    failures: dict[str, list[float]] = state["failures"]
    window_s = 60.0
    max_failures = 5
    log = logging.getLogger("parlament.api")

    expected = os.environ.get("PARLAMENT_ADMIN_TOKEN", "")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail=f"{operation} disabled (set PARLAMENT_ADMIN_TOKEN)",
        )

    fingerprint = hashlib.sha256((token or "").encode("utf-8")).hexdigest()[:16]
    with lock:
        now = time.monotonic()
        recent = [t for t in failures.get(fingerprint, ()) if now - t < window_s]
        if len(recent) >= max_failures:
            log.warning(
                "admin auth lockout: operation=%s fingerprint=%s failures=%d",
                operation,
                fingerprint,
                len(recent),
            )
            raise HTTPException(
                status_code=429, detail="too many failed admin attempts; try again later"
            )
        # compare_digest on bytes keeps this constant-time and avoids the
        # TypeError that str inputs with non-ASCII characters would trigger.
        if not token or not secrets.compare_digest(token.encode("utf-8"), expected.encode("utf-8")):
            recent.append(now)
            failures[fingerprint] = recent
            log.warning(
                "admin auth failure: operation=%s fingerprint=%s failures=%d",
                operation,
                fingerprint,
                len(recent),
            )
            raise HTTPException(status_code=401, detail="invalid admin token")
        failures.pop(fingerprint, None)


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
    include_switches: bool = Query(False),
    db: Session = Depends(get_db),
):
    today = date.today()
    s = _parse_date(start, date(today.year, 1, 1))
    e = _parse_date(end, today)
    if e < s:
        raise HTTPException(status_code=422, detail="to must be >= from")
    return queries.get_timeline(db, chamber, s, e, step_days, include_switches=include_switches)


@router.get("/persons")
@cache_result("persons")
def persons(
    q: str | None = None,
    chamber: str | None = Query(None, pattern="^(deputies|senate)$"),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return queries.search_persons(db, q, chamber, limit)


@router.get("/mps")
@cache_result("mps")
def mps_cards(
    q: str | None = Query(None, max_length=200),
    limit: int = Query(60, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort: str = Query("name", pattern="^(name|age|switches|committees)$"),
    db: Session = Depends(get_db),
):
    """MP biography cards (Feature 8): person + party + switches + committees.

    Each row is one person with the aggregates a voter scans for: current
    party group, observed switch count, committee tenures and age from the
    recorded birth date. Read-only over existing tables; persons without a
    birth date show age as null rather than a guess.
    """
    from sqlalchemy import func, select

    from pipeline.db import Event, Membership, Organization, Person

    base = select(Person.id, Person.canonical_name, Person.birth_date)
    if q:
        base = base.where(Person.normalized_name.like(f"%{q.lower()}%"))

    # Aggregates over the whole corpus, grouped by person.
    switches = (
        select(Event.person_id, func.count(Event.id).label("n"))
        .where(Event.type == "switch_group")
        .group_by(Event.person_id)
        .subquery()
    )
    committees = (
        select(Membership.person_id, func.count(func.distinct(Membership.org_id)).label("n"))
        .join(Organization, Organization.id == Membership.org_id)
        .where(Organization.classification == "committee")
        .group_by(Membership.person_id)
        .subquery()
    )
    # Most recent party affiliation: latest group membership carrying a party.
    # ROW_NUMBER dedupes to one row per person so the outer join cannot
    # multiply biography cards.
    latest_party = (
        select(
            Membership.person_id,
            Organization.short_name.label("party"),
            func.row_number()
            .over(
                partition_by=Membership.person_id,
                order_by=func.coalesce(Membership.start_date, date(1900, 1, 1)).desc(),
            )
            .label("rn"),
        )
        .join(Organization, Organization.id == Membership.on_behalf_of_id)
        .where(Organization.classification == "party")
        .subquery()
    )

    stmt = (
        base.add_columns(
            func.coalesce(switches.c.n, 0).label("switches"),
            func.coalesce(committees.c.n, 0).label("committees"),
            latest_party.c.party,
        )
        .outerjoin(switches, switches.c.person_id == Person.id)
        .outerjoin(committees, committees.c.person_id == Person.id)
        .outerjoin(latest_party, (latest_party.c.person_id == Person.id) & (latest_party.c.rn == 1))
    )
    if sort == "switches":
        stmt = stmt.order_by(func.coalesce(switches.c.n, 0).desc(), Person.canonical_name)
    elif sort == "committees":
        stmt = stmt.order_by(func.coalesce(committees.c.n, 0).desc(), Person.canonical_name)
    elif sort == "age":
        stmt = stmt.order_by(Person.birth_date.asc().nullslast(), Person.canonical_name)
    else:
        stmt = stmt.order_by(Person.canonical_name)
    stmt = stmt.offset(offset).limit(limit)

    today = date.today()
    cards = []
    for person_id, name, birth_date, n_switches, n_committees, party in db.execute(stmt):
        age = None
        if birth_date:
            age = (
                today.year
                - birth_date.year
                - ((today.month, today.day) < (birth_date.month, birth_date.day))
            )
        cards.append(
            {
                "id": person_id,
                "name": name,
                "birth_date": birth_date.isoformat() if birth_date else None,
                "age": age,
                "party": party,
                "switches": n_switches,
                "committees": n_committees,
            }
        )
    return {"status": "ok", "data": cards, "offset": offset, "limit": limit}


@router.get("/persons/{person_id}/history")
def person_history(person_id: str, db: Annotated[Session, Depends(get_db)]):
    data = queries.get_person_history(db, person_id)
    if data is None:
        raise HTTPException(status_code=404, detail="person not found")
    return data


@router.get("/persons/{person_id}")
@cache_result("person")
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
def recent_events(
    limit: int = Query(50, ge=1, le=500),
    chamber: str | None = Query(None, pattern="^(deputies|senate)$"),
    legislature: str | None = Query(None, pattern=r"^\d{4}$"),
    db: Session = Depends(get_db),
):
    return queries.get_recent_events(db, limit, chamber=chamber, legislature=legislature)


@router.get("/coverage")
def coverage(db: Session = Depends(get_db)):
    return queries.get_coverage(db)


@router.get("/coverage/detailed")
def coverage_detailed(db: Session = Depends(get_db)):
    """Detailed coverage matrix with per-scope data quality stats."""
    return queries.get_coverage_detailed(db)


@router.get("/committees")
@cache_result("committees")
def committees(as_of: str | None = None, db: Session = Depends(get_db)):
    """Committee list with active dated memberships, when committee data exists.

    Committee tenures are not ingested yet, so the current corpus returns an
    empty list instead of a fabricated composition or a missing-route error.
    """
    from sqlalchemy import or_, select

    from pipeline.db import Membership, Organization

    reference_date = _parse_date(as_of, date.today())
    active_membership = (
        select(Membership.id)
        .where(
            Membership.org_id == Organization.id,
            Membership.start_date.is_not(None),
            Membership.start_date <= reference_date,
            or_(Membership.end_date.is_(None), Membership.end_date >= reference_date),
        )
        .exists()
    )
    rows = db.scalars(
        select(Organization)
        .where(
            Organization.classification == "committee",
            active_membership,
        )
        .order_by(Organization.name)
    ).all()
    return [{"id": o.id, "name": o.name, "chamber": o.chamber, "party": None} for o in rows]


@router.get("/committees/{committee_id}/members")
@cache_result("committee-members")
def committee_members(
    committee_id: str,
    as_of: str | None = None,
    db: Session = Depends(get_db),
):
    """Dated member ledger of one committee: current and former members.

    Every row carries the member's name, party group at entry, role and the
    observed start/end dates from the official cdep.ro ledger.
    """
    from sqlalchemy import select

    from pipeline.db import Membership, Organization, Person

    committee = db.get(Organization, committee_id)
    if committee is None or committee.classification != "committee":
        raise HTTPException(status_code=404, detail="committee not found")

    reference_date = _parse_date(as_of, date.today())
    stmt = (
        select(Membership, Person.canonical_name)
        .join(Person, Person.id == Membership.person_id)
        .where(Membership.org_id == committee_id)
        .order_by(
            # Active members first, then by name.
            (Membership.end_date.is_(None)).desc(),
            Person.canonical_name,
        )
    )
    rows = db.execute(stmt).all()

    members = []
    for m, name in rows:
        is_active = (m.start_date is None or m.start_date <= reference_date) and (
            m.end_date is None or m.end_date >= reference_date
        )
        members.append(
            {
                "person_id": m.person_id,
                "name": name,
                "role": m.role,
                "group": m.group_acronym_at_event,
                "start_date": m.start_date.isoformat() if m.start_date else None,
                "end_date": m.end_date.isoformat() if m.end_date else None,
                "start_precision": m.start_precision,
                "end_precision": m.end_precision,
                "active": is_active,
                "source_url": m.source_url,
            }
        )

    return {
        "committee": {
            "id": committee.id,
            "name": committee.name,
            "chamber": committee.chamber,
            "legislature": committee.legislature,
        },
        "as_of": reference_date.isoformat(),
        "members": members,
        "active_count": sum(1 for m in members if m["active"]),
        "total_count": len(members),
    }


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


@router.get("/parties")
@cache_result("parties")
def parties_list(db: Session = Depends(get_db)):
    """All parties with size and switch-flow stats, for comparison UI.

    Size = distinct persons with a group membership on behalf of the party;
    flows count observed switch_group events whose destination group maps to
    the party. Read-only over existing tables.
    """
    from sqlalchemy import func, select

    from pipeline.db import Event, Membership, Organization

    party_rows = db.execute(
        select(
            Organization.id,
            Organization.short_name,
            Organization.name,
            Organization.color,
            func.count(func.distinct(Membership.person_id)).label("total_members"),
        )
        .select_from(Organization)
        .outerjoin(
            Membership,
            (Membership.on_behalf_of_id == Organization.id)
            & (Membership.chamber.in_(["deputies", "senate"])),
        )
        .where(Organization.classification == "party")
        .group_by(Organization.id)
        .order_by(func.count(func.distinct(Membership.person_id)).desc())
    ).all()

    # One grouped query instead of one per party (was37 serial queries —
    # measured260 ms serial, the endpoint's whole cost).
    switch_counts = dict(
        db.execute(
            select(Organization.short_name, func.count(Event.id))
            .join(Event, Event.to_org_id == Organization.id)
            .where(
                Event.type == "switch_group",
                Organization.classification == "group",
            )
            .group_by(Organization.short_name)
        ).all()
    )

    result = []
    for org_id, short_name, name, color, total_members in party_rows:
        # Switches in: observed switch_group events whose destination GROUP
        # carries this party's acronym. Groups and parties are separate org
        # rows sharing the short_name (several PSD groups + one PSD party),
        # so match on the acronym, not the id — the grouped query above
        # already aggregates every group sharing the acronym.
        switches_in = switch_counts.get(short_name, 0)
        result.append(
            {
                "id": org_id,
                "short_name": short_name,
                "name": name,
                "color": color,
                "total_members": total_members or 0,
                "switches_in": switches_in,
            }
        )
    return {"status": "ok", "data": result}


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
    _require_admin_token(x_admin_token, "admin polling")
    try:
        results = run_poll_cycle(db, legislature)
    except Exception:  # noqa: BLE001 - upstream failure is reported generically
        import logging

        logging.getLogger("parlament.api").exception("admin poll cycle failed")
        raise HTTPException(status_code=502, detail="upstream poll failed") from None
    invalidate_traseism_overview_cache()
    invalidate_result_cache()
    return {"status": "ok", "legislature": legislature, "results": results}


@router.get("/health")
def health(db: Session = Depends(get_db)):
    return {
        "status": "ok",
        "database": _database_health(db),
        "dataset": _dataset_metadata(),
        "sources": source_health(db),
    }


@router.get("/health/live")
def health_live():
    return {"status": "ok"}


@router.get("/health/ready")
def health_ready(db: Session = Depends(get_db)):
    return {"status": "ok", "database": _database_health(db)}


def _database_health(db: Session) -> dict:
    from sqlalchemy import func, select

    from pipeline.db import Membership, Person

    return {
        "status": "ok",
        "persons": db.scalar(select(func.count()).select_from(Person)),
        "memberships": db.scalar(select(func.count()).select_from(Membership)),
    }


def _dataset_metadata() -> dict:
    try:
        metadata = json.loads(DATASET_METADATA_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        metadata = {}
    if not isinstance(metadata, dict):
        raise ValueError(f"dataset metadata must be a JSON object: {DATASET_METADATA_PATH}")
    return {
        "release_tag": metadata.get("release_tag"),
        "published_at": metadata.get("published_at"),
        "asset_sha256": metadata.get("asset_sha256"),
    }


@router.post("/analytics/waves")
def analytics_waves(
    chamber: str | None = Query(None, pattern="^(deputies|senate)$"),
    legislature: str | None = Query(None, pattern=r"^\d{4}$"),
    window_days: int = Query(30, ge=1, le=180),
    min_switches: int = Query(3, ge=1, le=100),
    x_admin_token: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
):
    """Detect and persist party switch waves in the given scope."""
    _require_admin_token(x_admin_token)
    count = derive_switch_waves(
        db,
        chamber=chamber,
        legislature=legislature,
        window_days=window_days,
        min_switches=min_switches,
    )
    db.commit()
    # Waves changed — drop cached analytics and the traseism overview so the
    # next GET is fresh, matching the other admin write paths (/admin/poll,
    # /waves/recompute).
    invalidate_result_cache()
    invalidate_traseism_overview_cache()
    return {"status": "ok", "created": count}


@router.get("/analytics/waves", include_in_schema=False)
def analytics_waves_get_not_allowed():
    raise HTTPException(status_code=405, detail="use POST to derive switch waves")


@router.post("/analytics/waves/recompute")
def analytics_waves_recompute(
    x_admin_token: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
):
    """Delete and rebuild switch waves from the current event ledger."""
    _require_admin_token(x_admin_token)
    from sqlalchemy import delete

    from pipeline.db import SwitchWave

    db.execute(delete(SwitchWave))
    count = derive_all_switch_waves(db)
    db.commit()
    # Waves changed — drop cached analytics so the next GET is fresh.
    invalidate_result_cache()
    return {"status": "ok", "created": count}


@router.get("/analytics/waves/recompute", include_in_schema=False)
def analytics_waves_recompute_get_not_allowed():
    raise HTTPException(status_code=405, detail="use POST to recompute switch waves")


@router.get("/analytics/switch-waves")
@cache_result("switch-waves")
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
    """Estimate party switching rates from dated party and group memberships."""
    from pipeline.analytics import party_switching_rates

    try:
        results = party_switching_rates(db, legislature)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not results:
        return {
            "status": "unavailable",
            "data": [],
            "reason": "No dated party-switch events can be attributed to party memberships.",
        }
    return {"status": "ok", "data": results}


@router.get("/analytics/cross-chamber")
def get_cross_chamber(
    as_of: str | None = None,
    db: Session = Depends(get_db),
):
    """Get people with mandates in both chambers by the requested date."""
    reference_date = _parse_date(as_of, date.today())
    results = queries.get_cross_chamber_careers(db, reference_date)
    return {
        "status": "ok",
        "as_of": reference_date.isoformat(),
        "count": len(results),
        "data": results,
    }


@router.get("/analytics/committee-control")
@cache_result("committee-control")
def get_committee_control(
    legislature: str | None = Query(None, pattern=r"^\d{4}$"),
    as_of: str | None = None,
    db: Session = Depends(get_db),
):
    """Which party chairs which committees (source-backed, dated)."""
    from pipeline.analytics import derive_committee_control

    try:
        result = derive_committee_control(
            db,
            legislature=legislature,
            as_of=_parse_date(as_of, date.today()) if as_of else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if result["total_committees"] == 0:
        return {
            "status": "unavailable",
            "reason": "No dated committee chair rows in the corpus yet.",
            "data": result,
        }
    return {"status": "ok", "data": result}


@router.get("/analytics/generational-shift")
@cache_result("generational-shift")
def get_generational_shift(
    legislature: str | None = Query(None, pattern=r"^\d{4}$"),
    as_of: str | None = None,
    db: Session = Depends(get_db),
):
    """Get party age summaries from group memberships and their party affiliation."""
    from pipeline.analytics import generational_shift

    try:
        evaluation_date, results = generational_shift(
            db,
            legislature=legislature,
            as_of=_parse_date(as_of, date.today()) if as_of else None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok", "as_of": evaluation_date.isoformat(), "data": results}


# --- Traseism statistics ---------------------------------------------------
# The public view of party/group switching. Every number here is a count of
# OBSERVED movement taken from the chambers' own dated group ledgers.


@router.get("/analytics/party-timeline")
@cache_result("party-timeline")
def get_party_timeline_analytics(
    db: Session = Depends(get_db),
):
    """Observed presence span of every party in parliament (Feature 10).

    One row per party: the first and last dated join (``membership.start_date``
    on behalf of the party) plus its declared founding date when the corpus
    records one. This is an OBSERVED SPAN, not a merger/split graph — the
    corpus carries 0 predecessor/successor links, so succession between rows
    (e.g. PDSR ending then PSD starting) is shown, never asserted.
    """
    from sqlalchemy import func, select

    from pipeline.db import Membership, Organization

    rows = db.execute(
        select(
            Organization.short_name,
            Organization.name,
            Organization.founding_date,
            func.min(Membership.start_date).label("first_join"),
            func.max(Membership.start_date).label("last_join"),
            func.count(Membership.id).label("dated_joins"),
        )
        .join(Membership, Membership.on_behalf_of_id == Organization.id)
        .where(
            Organization.classification == "party",
            Membership.start_date.is_not(None),
        )
        .group_by(Organization.id)
        .order_by(func.min(Membership.start_date))
    ).all()

    data = [
        {
            "party": short_name,
            "name": name,
            "founding_date": founding.isoformat() if founding else None,
            "first_join": first.isoformat() if first else None,
            "last_join": last.isoformat() if last else None,
            "dated_joins": dated_joins,
        }
        for short_name, name, founding, first, last, dated_joins in rows
    ]
    return {
        "status": "ok",
        "data": data,
        "gaps": {
            "predecessor_links": 0,
            "successor_links": 0,
            "dissolution_dates": db.scalar(
                select(func.count(Organization.id)).where(
                    Organization.classification == "party",
                    Organization.dissolution_date.is_not(None),
                )
            )
            or 0,
            "note": (
                "Merger/split succession is not machine-declared in this "
                "corpus; spans show observed presence only."
            ),
        },
    }


@router.get("/traseism/overview")
def traseism_overview(db: Session = Depends(get_db)):
    """One row per chamber and legislature: members, switches, switchers, rate."""
    global _traseism_overview_cache
    if _traseism_overview_cache is None:
        with _traseism_overview_lock:
            if _traseism_overview_cache is None:
                from pipeline.traseism import traseism_overview as _overview

                _traseism_overview_cache = _overview(db)
    return _traseism_overview_cache


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


@router.get("/analytics/switch-leaderboard")
@cache_result("switch-leaderboard")
def switch_leaderboard(
    limit: int = Query(20, ge=1, le=100),
    legislature: str | None = Query(None, pattern=r"^\d{4}$"),
    chamber: str | None = Query(None, pattern=r"^(deputies|senate)$"),
    db: Session = Depends(get_db),
):
    """Top party switchers: one row per person, ranked by switch count.

    Every count is an observed switch_group event from the chambers' own
    dated group ledgers. Rows carry the person id so the UI can link to
    the deep-dive page. When ``chamber``/``legislature`` are supplied, the
    ranking AND every loyalty ingredient are restricted to that same scope.
    """
    from sqlalchemy import func, select

    from pipeline.db import Event, Organization, Person

    # P3-B: one scope shared by the ranking and all three loyalty queries.
    # Previously only switch_count was scoped while total_events, span and
    # parties counted the person's entire career, so the loyalty/party columns
    # did not describe the filtered ranking. Scoping every input keeps the
    # documented formula (volatility = switch_count / total_events *
    # tenure_weight) intact but makes the numerator, denominator, span and
    # party list come from the same chamber/legislature as the switch count.
    scope = []
    if legislature:
        scope.append(Event.legislature == legislature)
    if chamber:
        scope.append(Event.chamber == chamber)

    stmt = (
        select(
            Person.id,
            Person.canonical_name,
            func.count(Event.id).label("switch_count"),
            func.min(Event.event_date).label("first_switch"),
            func.max(Event.event_date).label("last_switch"),
        )
        .join(Event, Event.person_id == Person.id)
        .where(Event.type == "switch_group", *scope)
        .group_by(Person.id, Person.canonical_name)
        .order_by(func.count(Event.id).desc(), Person.canonical_name)
        .limit(limit)
    )

    rows = db.execute(stmt).all()

    # Batch the loyalty ingredients for the whole page in 3 grouped queries
    # instead of 3 queries per row (was 60+ round-trips at limit=20).
    top_ids = [r[0] for r in rows]
    parties_by_person: dict[str, list[str]] = {pid: [] for pid in top_ids}
    totals_by_person: dict[str, int] = {}
    span_by_person: dict[str, tuple] = {}
    if top_ids:
        # Per-person destination parties, ordered by count desc within the
        # person (the trailing count is consumed by the ORDER BY only).
        for pid, short_name, _n in db.execute(
            select(
                Event.person_id,
                Organization.short_name,
                func.count(Event.id),
            )
            .join(Organization, Organization.id == Event.to_org_id)
            .where(
                Event.person_id.in_(top_ids),
                Event.type == "switch_group",
                Organization.short_name.is_not(None),
                *scope,
            )
            .group_by(Event.person_id, Organization.short_name)
            .order_by(Event.person_id, func.count(Event.id).desc())
        ):
            parties_by_person.setdefault(pid, []).append(short_name)
        totals_by_person = dict(
            db.execute(
                select(Event.person_id, func.count(Event.id))
                .where(Event.person_id.in_(top_ids), *scope)
                .group_by(Event.person_id)
            ).all()
        )
        # 3-column rows: (person_id, min, max) — dict() needs pairs, so
        # fold manually.
        span_by_person = {
            pid: (first, last)
            for pid, first, last in db.execute(
                select(
                    Event.person_id,
                    func.min(Event.event_date),
                    func.max(Event.event_date),
                )
                .where(
                    Event.person_id.in_(top_ids),
                    Event.event_date.is_not(None),
                    *scope,
                )
                .group_by(Event.person_id)
            ).all()
        }

    # Loyalty score (Feature 10):
    #   volatility = (switch_group_count / total_events) * tenure_weight
    #   loyalty    = 100 * (1 - volatility), clipped to [0, 100]
    # tenure_weight scales short careers down (a 6-month MP with 1 switch
    # is noisier than a 10-year MP with the same ratio): min(1, years/4).
    leaderboard = []
    for person_id, name, count, first_switch, last_switch in rows:
        total_events = totals_by_person.get(person_id, 0)
        span = span_by_person.get(person_id)
        tenure_years = 0.0
        if span and span[0] and span[1]:
            tenure_years = max((span[1] - span[0]).days / 365.25, 0.0)
        tenure_weight = min(1.0, tenure_years / 4.0)
        switch_ratio = (count / total_events) if total_events else 0.0
        volatility = switch_ratio * tenure_weight
        loyalty = round(max(0.0, min(100.0, 100.0 * (1.0 - volatility))), 1)

        leaderboard.append(
            {
                "person_id": person_id,
                "name": name,
                "switch_count": count,
                "first_switch": first_switch.isoformat() if first_switch else None,
                "last_switch": last_switch.isoformat() if last_switch else None,
                "parties": parties_by_person.get(person_id, []),
                "total_events": total_events,
                "tenure_years": round(tenure_years, 1),
                "loyalty_score": loyalty,
            }
        )

    # Declare the scope so the UI's loyalty label is truthful: every number in
    # ``data`` now describes exactly this chamber/legislature combination.
    if chamber and legislature:
        score_scope = f"{chamber}:{legislature}"
    elif chamber:
        score_scope = chamber
    elif legislature:
        score_scope = legislature
    else:
        score_scope = "all_chambers_all_legislatures"

    return {"status": "ok", "score_scope": score_scope, "data": leaderboard}


# P3-B: export endpoints live only in backend/routers/exports.py. They were
# duplicated here under /api/export with identical path/operation IDs; because
# api_router is registered first, these shadows won route resolution while
# OpenAPI advertised a dead duplicate. exports.py is now the single source.
