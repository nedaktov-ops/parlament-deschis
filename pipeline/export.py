"""Open-data exporters: Popolo JSON and flat CSV.

Both the CLI (``parlament export``) and the read API
(``/api/export/popolo``, ``/api/export/{dataset}.csv``) share this module so
there is exactly one serialization contract.

Design rules:
* Facts only — every row keeps ``source_url`` / ``confidence`` where available.
* Diacritics are preserved verbatim (UTF-8); no lossy name transliteration.
* Scope filters (``chamber`` / ``legislature``) apply consistently to every
  section of the Popolo document so foreign keys never dangle.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import (
    Event,
    Membership,
    Organization,
    Person,
    PersonIdentifier,
    PersonName,
    Post,
)

DATA_LICENSE = "CC-BY-4.0"
CODE_LICENSE = "AGPL-3.0-or-later"
POPOLO_VERSION = "1.0"
PROJECT_URL = "https://github.com/parlament-deschis"

CSV_DATASETS = ("persons", "organizations", "posts", "memberships", "events")


def _iso(value) -> str | None:
    return value.isoformat() if value else None


def _scope_memberships(
    session: Session,
    *,
    chamber: str | None = None,
    legislature: str | None = None,
) -> list[Membership]:
    stmt = select(Membership)
    if chamber:
        stmt = stmt.where(Membership.chamber == chamber)
    if legislature:
        stmt = stmt.where(Membership.legislature == legislature)
    return list(session.scalars(stmt.order_by(Membership.start_date, Membership.id)))


def _scoped_person_ids(memberships: list[Membership]) -> set[str]:
    return {m.person_id for m in memberships}


def _person_by_id(session: Session, person_id: str) -> Person | None:
    return session.get(Person, person_id)


def _identifiers(session: Session, person_ids: set[str]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    if not person_ids:
        return out
    rows = session.scalars(
        select(PersonIdentifier).where(PersonIdentifier.person_id.in_(person_ids))
    )
    for ident in rows:
        out.setdefault(ident.person_id, []).append({
            "scheme": ident.scheme,
            "identifier": ident.identifier,
            "legislature": ident.legislature,
        })
    return out


def _aliases(session: Session, person_ids: set[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    if not person_ids:
        return out
    rows = session.scalars(
        select(PersonName).where(
            PersonName.person_id.in_(person_ids), PersonName.type == "alias"
        )
    )
    for name in rows:
        out.setdefault(name.person_id, []).append(name.name)
    return out


def build_popolo(
    session: Session,
    *,
    chamber: str | None = None,
    legislature: str | None = None,
) -> dict:
    """Build a Popolo 1.0 document scoped to the requested slice."""
    memberships = _scope_memberships(session, chamber=chamber, legislature=legislature)
    person_ids = _scoped_person_ids(memberships)
    org_ids: set[str] = set()
    post_ids: set[str] = set()
    for m in memberships:
        org_ids.add(m.org_id)
        if m.on_behalf_of_id:
            org_ids.add(m.on_behalf_of_id)
        if m.post_id:
            post_ids.add(m.post_id)

    # Include parent organizations referenced by the scoped orgs.
    orgs = list(session.scalars(select(Organization).where(Organization.id.in_(org_ids)))) if org_ids else []
    for org in list(orgs):
        if org.parent_id and org.parent_id not in org_ids:
            parent = session.get(Organization, org.parent_id)
            if parent is not None:
                orgs.append(parent)
                org_ids.add(parent.id)

    posts = list(session.scalars(select(Post).where(Post.id.in_(post_ids)))) if post_ids else []
    ids = _identifiers(session, person_ids)
    aliases = _aliases(session, person_ids)

    persons = []
    if person_ids:
        for person in session.scalars(select(Person).where(Person.id.in_(person_ids))):
            persons.append({
                "id": person.id,
                "name": person.canonical_name,
                "sort_name": person.sort_key,
                "birth_date": _iso(person.birth_date),
                "wikidata_qid": person.wikidata_qid,
                "match_status": person.match_status,
                "identifiers": ids.get(person.id, []),
                "other_names": [{"name": a, "note": "alias"} for a in aliases.get(person.id, [])],
            })

    org_payload = [{
        "id": o.id,
        "name": o.name,
        "short_name": o.short_name,
        "classification": o.classification,
        "parent_id": o.parent_id,
        "chamber": o.chamber,
        "color": o.color,
        "founding_date": _iso(o.founding_date),
        "dissolution_date": _iso(o.dissolution_date),
        "wikidata_qid": o.wikidata_qid,
        "alt_labels": o.alt_labels or [],
        "localised_labels": o.localised_labels,
    } for o in orgs]

    post_payload = [{
        "id": p.id,
        "organization_id": p.org_id,
        "label": p.label,
        "role": p.role_type,
        "importance": p.importance,
        "maximum_memberships": p.maximum_memberships,
    } for p in posts]

    membership_payload = [{
        "id": m.id,
        "person_id": m.person_id,
        "organization_id": m.org_id,
        "post_id": m.post_id,
        "on_behalf_of_id": m.on_behalf_of_id,
        "role": m.role,
        "legislative_period_id": m.legislature,
        "chamber": m.chamber,
        "start_date": _iso(m.start_date),
        "end_date": _iso(m.end_date),
        "start_precision": m.start_precision,
        "end_precision": m.end_precision,
        "start_reason": m.start_reason,
        "end_reason": m.end_reason,
        "confidence": m.confidence,
        "source_url": m.source_url,
        "group_acronym_at_event": m.group_acronym_at_event,
        "first_seen_at": _iso(m.first_seen_at),
        "last_seen_at": _iso(m.last_seen_at),
    } for m in memberships]

    ev_stmt = select(Event)
    if chamber:
        ev_stmt = ev_stmt.where(Event.chamber == chamber)
    if person_ids:
        ev_stmt = ev_stmt.where(Event.person_id.in_(person_ids) | Event.person_id.is_(None))
    events = list(session.scalars(ev_stmt.order_by(Event.event_date, Event.detected_at)))
    event_payload = [{
        "id": e.id,
        "type": e.type,
        "person_id": e.person_id,
        "chamber": e.chamber,
        "from_organization_id": e.from_org_id,
        "to_organization_id": e.to_org_id,
        "post_id": e.post_id,
        "role": e.role,
        "date": _iso(e.event_date),
        "precision": e.precision,
        "reason": e.reason,
        "confidence": e.confidence,
        "summary_ro": e.summary_ro,
        "summary_en": e.summary_en,
    } for e in events]

    return {
        "meta": {
            "generated_at": datetime.now(UTC).isoformat(),
            "generator": "Parlament Deschis",
            "project_url": PROJECT_URL,
            "popolo_version": POPOLO_VERSION,
            "code_license": CODE_LICENSE,
            "data_license": DATA_LICENSE,
            "scope": {"chamber": chamber, "legislature": legislature},
            "counts": {
                "persons": len(persons),
                "organizations": len(org_payload),
                "posts": len(post_payload),
                "memberships": len(membership_payload),
                "events": len(event_payload),
            },
        },
        "persons": persons,
        "organizations": org_payload,
        "posts": post_payload,
        "memberships": membership_payload,
        "events": event_payload,
    }


def _csv_text(rows: list[dict], fieldnames: list[str]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore",
                            lineterminator="\n")
    writer.writeheader()
    for row in rows:
        clean = {}
        for key in fieldnames:
            value = row.get(key)
            if isinstance(value, (list, dict)):
                value = json.dumps(value, ensure_ascii=False)
            clean[key] = "" if value is None else value
        writer.writerow(clean)
    return buf.getvalue()


PERSON_FIELDS = [
    "id", "name", "sort_name", "birth_date", "wikidata_qid", "match_status", "identifiers",
]
ORG_FIELDS = [
    "id", "name", "short_name", "classification", "chamber", "parent_id", "color",
    "founding_date", "dissolution_date", "wikidata_qid", "alt_labels",
]
POST_FIELDS = [
    "id", "organization_id", "label", "role", "importance", "maximum_memberships",
]
MEMBERSHIP_FIELDS = [
    "id", "person_id", "organization_id", "post_id", "on_behalf_of_id", "role",
    "legislative_period_id", "chamber", "start_date", "end_date", "start_precision",
    "end_precision", "start_reason", "end_reason", "confidence", "source_url",
    "group_acronym_at_event", "first_seen_at", "last_seen_at",
]
EVENT_FIELDS = [
    "id", "type", "person_id", "chamber", "from_organization_id", "to_organization_id",
    "post_id", "role", "date", "precision", "reason", "confidence", "summary_ro",
    "summary_en",
]


def csv_for(
    session: Session,
    dataset: str,
    *,
    chamber: str | None = None,
    legislature: str | None = None,
) -> str:
    """Return one CSV dataset as text. Raises KeyError for an unknown dataset."""
    if dataset not in CSV_DATASETS:
        raise KeyError(dataset)
    doc = build_popolo(session, chamber=chamber, legislature=legislature)
    if dataset == "persons":
        rows = []
        for p in doc["persons"]:
            rows.append({
                **p,
                "identifiers": "; ".join(
                    f"{i['scheme']}:{i['identifier']}"
                    + (f" ({i['legislature']})" if i.get("legislature") else "")
                    for i in p.get("identifiers", [])
                ),
            })
        return _csv_text(rows, PERSON_FIELDS)
    if dataset == "organizations":
        return _csv_text(doc["organizations"], ORG_FIELDS)
    if dataset == "posts":
        return _csv_text(doc["posts"], POST_FIELDS)
    if dataset == "memberships":
        return _csv_text(doc["memberships"], MEMBERSHIP_FIELDS)
    return _csv_text(doc["events"], EVENT_FIELDS)


def write_export(
    session: Session,
    out_dir: str | Path,
    *,
    chamber: str | None = None,
    legislature: str | None = None,
    formats: tuple[str, ...] = ("json", "csv"),
) -> dict:
    """Write the scoped export to ``out_dir``; returns written paths + counts."""
    directory = Path(out_dir)
    directory.mkdir(parents=True, exist_ok=True)
    doc = build_popolo(session, chamber=chamber, legislature=legislature)
    written: list[str] = []
    if "json" in formats:
        path = directory / "popolo.json"
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(str(path))
    if "csv" in formats:
        for dataset in CSV_DATASETS:
            path = directory / f"{dataset}.csv"
            path.write_text(
                csv_for(session, dataset, chamber=chamber, legislature=legislature),
                encoding="utf-8",
            )
            written.append(str(path))
    return {"files": written, "counts": doc["meta"]["counts"]}
