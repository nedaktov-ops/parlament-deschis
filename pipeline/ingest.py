"""Ingest orchestration: parsed source records → identity → organizations →
membership tenures → evidence → derived events.

Official dated ledgers are authoritative. Where a join date is not published
(founding/continuing members), the start is inferred from the group founding
date or the legislature start, and flagged as such — never fabricated as an
exact published day.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .approxdate import ApproxDate
from .db import Evidence, KeyEvent, Membership, Organization
from .events import derive_group_events, derive_org_events
from .identity import PersonResolver
from .normalize import canonical_group_short, normalize_org_label
from .parse.cdep_committee import CommitteeLedger
from .parse.cdep_group import GroupLedger
from .parse.senat_profile import SenatorProfile
from .reconcile import MembershipWriter

REF_DIR = Path("data/reference")


def _load_reference(name: str) -> dict:
    path = REF_DIR / name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


LEGI = _load_reference("legislatures.json")
GROUPS = _load_reference("groups.json")


def legislature_start(legislature: str | None) -> date | None:
    if legislature and legislature in LEGI:
        return date.fromisoformat(LEGI[legislature]["start"])
    return None


def seed_key_events(session: Session) -> None:
    for leg, info in LEGI.items():
        for chamber in ("deputies", "senate"):
            exists = session.scalars(
                select(KeyEvent).where(
                    KeyEvent.type == "legislature",
                    KeyEvent.chamber == chamber,
                    KeyEvent.label == leg,
                )
            ).first()
            if exists:
                continue
            session.add(
                KeyEvent(
                    type="legislature",
                    chamber=chamber,
                    label=leg,
                    start_date=date.fromisoformat(info["start"]),
                    end_date=date.fromisoformat(info["end"]) if info["end"] else None,
                )
            )
    session.flush()


def get_or_create_org(
    session: Session,
    *,
    classification: str,
    name: str,
    short_name: str | None = None,
    chamber: str | None = None,
    founding_date: date | None = None,
    former_name: str | None = None,
    parent_id: str | None = None,
) -> Organization:
    norm = normalize_org_label(name)
    stmt = select(Organization).where(
        Organization.classification == classification,
        Organization.normalized_name == norm,
    )
    org = session.scalars(stmt).first()
    if org is not None:
        if short_name and not org.short_name:
            org.short_name = short_name
        if founding_date and not org.founding_date:
            org.founding_date = founding_date
        if former_name:
            alts = org.alt_labels or []
            if former_name not in alts:
                org.alt_labels = alts + [former_name]
        return org

    ref = GROUPS.get(short_name or "", {})
    alt_labels = [former_name] if former_name else (ref.get("alt_labels") or None)
    org = Organization(
        classification=classification,
        name=name,
        normalized_name=norm,
        short_name=short_name,
        chamber=chamber,
        founding_date=founding_date,
        alt_labels=alt_labels,
        color=ref.get("color"),
        parent_id=parent_id,
        localised_labels={"name": {"ro": ref.get("name_ro", name), "en": ref.get("name_en", name)}}
        if ref
        else None,
    )
    session.add(org)
    session.flush()
    return org


def _add_evidence(
    session,
    membership: Membership,
    *,
    type: str,
    source_url: str | None,
    note: str | None = None,
    snapshot_hash: str | None = None,
):
    session.add(
        Evidence(
            membership_id=membership.id,
            type=type,
            source_url=source_url,
            note=note,
            snapshot_hash=snapshot_hash,
        )
    )


def _resolve_start(
    row_join: ApproxDate | None, founding: ApproxDate | None, leg_start: date | None
) -> tuple[date | None, str | None, bool]:
    """Return (start_date, precision, inferred)."""
    if row_join is not None:
        return row_join.earliest, row_join.precision, False
    if founding is not None:
        return founding.earliest, founding.precision, True
    if leg_start is not None:
        return leg_start, leg_start.isoformat(), True
    return None, None, True


def ingest_cdep_group_ledger(
    session: Session, ledger: GroupLedger, *, legislature: str, snapshot_hash: str | None = None
) -> dict:
    meta = ledger.meta
    short = meta.short_name or canonical_group_short(meta.name)
    group = get_or_create_org(
        session,
        classification="group",
        name=meta.name,
        short_name=short,
        chamber=meta.chamber,
        founding_date=meta.founding_date.earliest if meta.founding_date else None,
        former_name=meta.former_name,
    )
    derive_org_events(session, group)
    resolver = PersonResolver(session)
    writer = MembershipWriter(session)
    leg_start = legislature_start(legislature)
    stats = {"current": 0, "former": 0, "bureau": 0, "persons": 0}

    def party_org(party_label: str | None):
        if not party_label or party_label.strip() in ("-", ""):
            return None
        pshort = canonical_group_short(party_label)
        return get_or_create_org(
            session,
            classification="party",
            name=party_label,
            short_name=pshort,
            chamber=meta.chamber,
        )

    for row in ledger.current:
        if not row.idm:
            continue
        person, created = resolver.resolve(
            scheme="cdep_idm",
            identifier=row.idm,
            name=row.name,
            legislature=legislature,
        )
        stats["persons"] += created
        porg = party_org(row.party)
        start, prec, inferred = _resolve_start(row.group_join, meta.founding_date, leg_start)
        m = writer.record_authoritative(
            person_id=person.id,
            org_id=group.id,
            chamber=meta.chamber,
            start=start,
            end=None,
            on_behalf_of_id=porg.id if porg else None,
            legislature=legislature,
            role=row.role,
            start_precision=prec,
            start_reason="GENERAL_ELECTION",
            confidence="official_ledger",
            source_url=meta.source_url,
            group_acronym=short,
        )
        if m:
            _add_evidence(
                session,
                m,
                type="official_ledger",
                source_url=meta.source_url,
                snapshot_hash=snapshot_hash,
                note="start inferred (founding/continuing member)" if inferred else None,
            )
        stats["current"] += 1

    for row in ledger.former:
        if not row.idm:
            continue
        person, created = resolver.resolve(
            scheme="cdep_idm",
            identifier=row.idm,
            name=row.name,
            legislature=legislature,
        )
        stats["persons"] += created
        start, prec, inferred = _resolve_start(row.group_join, meta.founding_date, leg_start)
        end = row.group_leave.earliest if row.group_leave else None
        end_prec = row.group_leave.precision if row.group_leave else None
        m = writer.record_authoritative(
            person_id=person.id,
            org_id=group.id,
            chamber=meta.chamber,
            start=start,
            end=end,
            legislature=legislature,
            start_precision=prec,
            end_precision=end_prec,
            start_reason="GENERAL_ELECTION",
            end_reason="UNKNOWN",
            confidence="official_ledger",
            source_url=meta.source_url,
            group_acronym=short,
        )
        if m:
            _add_evidence(
                session,
                m,
                type="official_ledger",
                source_url=meta.source_url,
                snapshot_hash=snapshot_hash,
                note="start inferred (founding/continuing member)" if inferred else None,
            )
        stats["former"] += 1

    # --- Former bureau members ------------------------------------------------
    # The group ledger's former-bureau table lists people who held a dated role
    # in the group's bureau (president, vice-president, secretary, chestor).
    # Each row carries role_start / role_end dates from the source.
    bureau_org = get_or_create_org(
        session,
        classification="bureau",
        name=f"Birou {short}",
        short_name=f"B.{short}",
        chamber=meta.chamber,
        parent_id=group.id,
    )
    for row in ledger.former_bureau:
        if not row.idm:
            continue
        person, created = resolver.resolve(
            scheme="cdep_idm",
            identifier=row.idm,
            name=row.name,
            legislature=legislature,
        )
        stats["persons"] += created
        start = row.role_start.earliest if row.role_start else None
        start_prec = row.role_start.precision if row.role_start else None
        end = row.role_end.earliest if row.role_end else None
        end_prec = row.role_end.precision if row.role_end else None
        m = writer.record_authoritative(
            person_id=person.id,
            org_id=bureau_org.id,
            chamber=meta.chamber,
            start=start,
            end=end,
            legislature=legislature,
            role=row.role,
            start_precision=start_prec,
            end_precision=end_prec,
            start_reason="GENERAL_ELECTION",
            end_reason="UNKNOWN",
            confidence="official_ledger",
            source_url=meta.source_url,
            group_acronym=short,
        )
        if m:
            _add_evidence(
                session,
                m,
                type="official_ledger",
                source_url=meta.source_url,
                snapshot_hash=snapshot_hash,
            )
        stats["bureau"] += 1

    session.flush()
    stats["events"] = derive_group_events(session, chamber=meta.chamber)
    return stats


def ingest_cdep_committee_ledger(
    session: Session, ledger: CommitteeLedger, *, legislature: str, snapshot_hash: str | None = None
) -> dict:
    """Ingest a committee member ledger: create committee org, write dated
    memberships for current and former members with evidence rows.

    Current members may carry a role start date (footnote span on newer
    templates). Former members carry an end date ("până în data") but no
    join date — start is left None.
    """
    meta = ledger.meta
    committee = get_or_create_org(
        session,
        classification="committee",
        name=meta.name,
        short_name=meta.short_name,
        chamber=meta.chamber,
    )
    resolver = PersonResolver(session)
    writer = MembershipWriter(session)
    stats = {"current": 0, "former": 0, "persons": 0}

    def group_org(group_name: str | None):
        if not group_name or group_name.strip() in ("-", ""):
            return None
        return get_or_create_org(
            session,
            classification="group",
            name=group_name,
            short_name=canonical_group_short(group_name),
            chamber=meta.chamber,
        )

    for row in ledger.current:
        if not row.idm:
            continue
        person, created = resolver.resolve(
            scheme="cdep_idm",
            identifier=row.idm,
            name=row.name,
            legislature=legislature,
        )
        stats["persons"] += created
        gorg = group_org(row.group_name)
        start = row.role_start.earliest if row.role_start else None
        start_prec = row.role_start.precision if row.role_start else None
        # A current member with no start date (start=None, end=None) already has
        # a tenure for this person+org+chamber when re-ingesting (the previous
        # ingest left a start=None tenure, open or closed). record_authoritative
        # cannot match a closed start=None tenure, so skip creating a duplicate
        # open tenure — the existing one already covers this membership.
        if start is None:
            existing = session.scalars(
                select(Membership).where(
                    Membership.person_id == person.id,
                    Membership.org_id == committee.id,
                    Membership.chamber == meta.chamber,
                    Membership.start_date.is_(None),
                )
            ).first()
            if existing is not None:
                stats["current"] += 1
                continue
        m = writer.record_authoritative(
            person_id=person.id,
            org_id=committee.id,
            chamber=meta.chamber,
            start=start,
            end=None,
            on_behalf_of_id=gorg.id if gorg else None,
            legislature=legislature,
            role=row.role,
            start_precision=start_prec,
            start_reason="GENERAL_ELECTION",
            confidence="official_ledger",
            source_url=meta.source_url,
            group_acronym=row.group_name,
        )
        if m:
            _add_evidence(
                session,
                m,
                type="official_ledger",
                source_url=meta.source_url,
                snapshot_hash=snapshot_hash,
            )
        stats["current"] += 1

    for row in ledger.former:
        if not row.idm:
            continue
        person, created = resolver.resolve(
            scheme="cdep_idm",
            identifier=row.idm,
            name=row.name,
            legislature=legislature,
        )
        stats["persons"] += created
        gorg = group_org(row.group_name)
        end = row.role_end.earliest if row.role_end else None
        end_prec = row.role_end.precision if row.role_end else None
        m = writer.record_authoritative(
            person_id=person.id,
            org_id=committee.id,
            chamber=meta.chamber,
            start=None,
            end=end,
            legislature=legislature,
            role=row.role,
            end_precision=end_prec,
            start_reason=None,
            end_reason="UNKNOWN",
            confidence="official_ledger",
            source_url=meta.source_url,
            group_acronym=row.group_name,
        )
        if m:
            _add_evidence(
                session,
                m,
                type="official_ledger",
                source_url=meta.source_url,
                snapshot_hash=snapshot_hash,
            )
        stats["former"] += 1

    session.flush()
    return stats


def ingest_senator_profile(
    session: Session, prof: SenatorProfile, *, snapshot_hash: str | None = None
) -> dict:
    resolver = PersonResolver(session)
    writer = MembershipWriter(session)
    legislature = prof.legislature
    stats = {"memberships": 0, "person_created": False}
    if not prof.guid:
        return stats
    person, created = resolver.resolve(
        scheme="senat_guid",
        identifier=prof.guid,
        name=prof.name,
        legislature=legislature,
    )
    stats["person_created"] = created

    # Party + group from the profile header.
    porg = None
    if prof.party:
        porg = get_or_create_org(
            session,
            classification="party",
            name=prof.party,
            short_name=canonical_group_short(prof.party),
            chamber="senate",
        )
    if prof.group:
        gshort = canonical_group_short(prof.group)
        gorg = get_or_create_org(
            session, classification="group", name=prof.group, short_name=gshort, chamber="senate"
        )
        start = (
            prof.validation_date.earliest
            if prof.validation_date
            else legislature_start(legislature)
        )
        m = writer.record_authoritative(
            person_id=person.id,
            org_id=gorg.id,
            chamber="senate",
            start=start,
            end=None,
            on_behalf_of_id=porg.id if porg else None,
            legislature=legislature,
            role=prof.group_role,
            start_precision=start.isoformat() if start else None,
            start_reason="GENERAL_ELECTION",
            confidence="official_profile",
            source_url=prof.profile_url,
            group_acronym=gshort,
        )
        if m:
            _add_evidence(
                session, m, type="profile", source_url=prof.profile_url, snapshot_hash=snapshot_hash
            )
        stats["memberships"] += 1

    # Committees / bureau / friendship / delegations (current + history).
    for sm in prof.memberships:
        oorg = get_or_create_org(
            session,
            classification=_senate_org_class(sm.org_class),
            name=sm.org_name,
            chamber="senate",
        )
        start = sm.start.earliest if sm.start else None
        end = sm.end.earliest if sm.end else None
        m = writer.record_authoritative(
            person_id=person.id,
            org_id=oorg.id,
            chamber="senate",
            start=start,
            end=end,
            legislature=legislature,
            role=sm.role,
            start_precision=sm.start.precision if sm.start else None,
            end_precision=sm.end.precision if sm.end else None,
            confidence="official_profile",
            source_url=prof.profile_url,
        )
        if m:
            _add_evidence(
                session, m, type="profile", source_url=prof.profile_url, snapshot_hash=snapshot_hash
            )
        stats["memberships"] += 1

    session.flush()
    return stats


def _senate_org_class(org_class: str) -> str:
    return {
        "committee": "committee",
        "joint_committee": "committee",
        "special_committee": "committee",
        "inquiry_committee": "committee",
        "bureau": "bureau",
        "friendship": "friendship",
        "delegation": "delegation",
    }.get(org_class, "other")
