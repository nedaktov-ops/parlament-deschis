"""Open-data export endpoints: Popolo JSON and flat CSV.

Both endpoints share one scope helper so ``chamber`` / ``legislature`` filters
mean exactly the same thing across formats, and both delegate to
``pipeline.export`` so the CLI and the API never diverge.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

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
