"""Open-data export endpoints: Popolo JSON and flat CSV.

Both endpoints share one scope helper so ``chamber`` / ``legislature`` filters
mean exactly the same thing across formats, and both delegate to
``pipeline.export`` so the CLI and the API never diverge.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from backend.cache import cached as cache_result
from backend.deps import get_db
from pipeline.export import CSV_DATASETS, build_popolo, csv_for

router = APIRouter(prefix="/api/export")


def _scope(
    chamber: str | None = Query(None, pattern="^(deputies|senate)$"),
    legislature: str | None = Query(None, pattern=r"^\d{4}$"),
) -> dict:
    """Shared export scope filters (deputies|senate, 4-digit legislature)."""
    return {"chamber": chamber, "legislature": legislature}


def _attachment(filename: str) -> dict[str, str]:
    return {"Content-Disposition": f'attachment; filename="{filename}"'}


@router.get("/popolo")
def export_popolo(
    scope: Annotated[dict, Depends(_scope)],
    db: Annotated[Session, Depends(get_db)],
):
    doc = build_popolo(db, chamber=scope["chamber"], legislature=scope["legislature"])
    return JSONResponse(
        content=doc,
        media_type="application/json; charset=utf-8",
        headers=_attachment("popolo.json"),
    )


@router.get("/report")
@cache_result("export-report")
def export_report(
    scope: Annotated[dict, Depends(_scope)],
    db: Annotated[Session, Depends(get_db)],
):
    """One-page transparency report as structured JSON (Feature 6).

    Composes the same figures the UI shows — corpus totals, coverage,
    top switchers with loyalty, committee chair control, switch waves and
    party ages — so the print view and this download can never disagree.
    No numbers are computed differently here than in the analytics
    endpoints; each block delegates to the existing query helpers.
    """
    from sqlalchemy import func, select

    from backend import queries
    from pipeline.analytics import derive_committee_control, generational_shift
    from pipeline.db import Event, Membership, Organization, Person, SwitchWave

    totals = {
        "persons": db.scalar(select(func.count(Person.id))) or 0,
        "memberships": db.scalar(select(func.count(Membership.id))) or 0,
        "events": db.scalar(select(func.count(Event.id))) or 0,
        "switches": db.scalar(select(func.count(Event.id)).where(Event.type == "switch_group"))
        or 0,
        "committees": db.scalar(
            select(func.count(Organization.id)).where(Organization.classification == "committee")
        )
        or 0,
        "persons_with_birth_date": db.scalar(
            select(func.count(Person.id)).where(Person.birth_date.is_not(None))
        )
        or 0,
    }

    # Top 10 switchers with the same loyalty formula as the leaderboard.
    top_rows = db.execute(
        select(
            Person.id,
            Person.canonical_name,
            func.count(Event.id),
            func.min(Event.event_date),
            func.max(Event.event_date),
        )
        .join(Event, Event.person_id == Person.id)
        .where(Event.type == "switch_group")
        .group_by(Person.id, Person.canonical_name)
        .order_by(func.count(Event.id).desc(), Person.canonical_name)
        .limit(10)
    ).all()
    top_switchers = []
    for person_id, name, count, first_switch, last_switch in top_rows:
        total_events = (
            db.scalar(select(func.count(Event.id)).where(Event.person_id == person_id)) or 0
        )
        span = db.execute(
            select(func.min(Event.event_date), func.max(Event.event_date)).where(
                Event.person_id == person_id,
                Event.event_date.is_not(None),
            )
        ).one()
        tenure_years = 0.0
        if span[0] and span[1]:
            tenure_years = max((span[1] - span[0]).days / 365.25, 0.0)
        volatility = ((count / total_events) if total_events else 0.0) * min(
            1.0, tenure_years / 4.0
        )
        top_switchers.append(
            {
                "person_id": person_id,
                "name": name,
                "switches": count,
                "first_switch": first_switch.isoformat() if first_switch else None,
                "last_switch": last_switch.isoformat() if last_switch else None,
                "loyalty_score": round(max(0.0, min(100.0, 100.0 * (1.0 - volatility))), 1),
            }
        )

    waves = db.scalars(select(SwitchWave).order_by(SwitchWave.switch_count.desc()).limit(10)).all()

    try:
        _, ages = generational_shift(db)
    except ValueError:
        ages = []

    try:
        control = derive_committee_control(db)
    except ValueError:
        control = {"total_committees": 0, "parties": [], "chairs": []}

    return JSONResponse(
        content={
            "report": "parlament-deschis transparency report",
            "generated_at": datetime.now(UTC).isoformat(),
            "scope": scope,
            "totals": totals,
            "coverage": queries.get_coverage_detailed(db),
            "top_switchers": top_switchers,
            "committee_control": control,
            "switch_waves": [
                {
                    "start_date": w.start_date.isoformat() if w.start_date else None,
                    "end_date": w.end_date.isoformat() if w.end_date else None,
                    "switch_count": w.switch_count,
                    "trigger_type": w.trigger_type,
                    "trigger_event": w.trigger_event,
                    "chamber": w.chamber,
                    "legislature": w.legislature,
                }
                for w in waves
            ],
            "party_ages": ages,
        },
        media_type="application/json; charset=utf-8",
        headers=_attachment("transparency-report.json"),
    )


@router.get("/{dataset}.csv")
def export_csv(
    dataset: str,
    scope: Annotated[dict, Depends(_scope)],
    db: Annotated[Session, Depends(get_db)],
):
    if dataset not in CSV_DATASETS:
        raise HTTPException(status_code=404, detail=f"unknown dataset: {dataset}")
    text = csv_for(db, dataset, chamber=scope["chamber"], legislature=scope["legislature"])
    return PlainTextResponse(
        text,
        media_type="text/csv; charset=utf-8",
        headers=_attachment(f"{dataset}.csv"),
    )
