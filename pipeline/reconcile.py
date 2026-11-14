"""Temporal reconciliation: turn observations and authoritative ledgers into
immutable, non-overlapping membership tenures.

Two paths:
* Authoritative (official ledger with explicit join/leave dates) → upsert the
  interval directly; closed tenures are never reopened.
* Derived (current-only roster snapshots) → collapse "seen in org X on date D"
  observations into intervals (votro-style), idempotent and order-independent.

Invariants enforced here:
* Closed tenures are immutable; a returning member gets a NEW membership id.
* Repeat stints coexist (unique org/person/post/end).
* Rebuilds never invert intervals (start <= end).
"""

from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import Membership


@dataclass
class Observation:
    person_key: str
    org_key: str
    observed_on: date
    source_url: str | None = None


@dataclass
class Interval:
    person_key: str
    org_key: str
    start: date
    end: date | None
    confidence: str = "derived"
    source_url: str | None = None


def collapse_observations(observations: list[Observation]) -> list[Interval]:
    """Merge per-person observations into consecutive same-org runs.

    Order-independent and idempotent: exact duplicates are dropped, runs are
    sorted by date, and a run closes the day before the next different-org
    observation. The final run stays open (end=None).
    """
    by_person: dict[str, list[Observation]] = defaultdict(list)
    for o in observations:
        by_person[o.person_key].append(o)

    out: list[Interval] = []
    for person, items in by_person.items():
        dedup: dict[tuple[str, date], Observation] = {}
        for o in items:
            dedup[(o.org_key, o.observed_on)] = o
        ordered = sorted(dedup.values(), key=lambda o: (o.observed_on, o.org_key))

        run_org: str | None = None
        run_start: date | None = None
        run_url: str | None = None
        for o in ordered:
            if run_org is None:
                run_org, run_start, run_url = o.org_key, o.observed_on, o.source_url
            elif o.org_key == run_org:
                continue  # extend the current run
            else:
                out.append(
                    Interval(
                        person,
                        run_org,
                        run_start,
                        o.observed_on - timedelta(days=1),
                        source_url=run_url,
                    )
                )
                run_org, run_start, run_url = o.org_key, o.observed_on, o.source_url
        if run_org is not None:
            out.append(Interval(person, run_org, run_start, None, source_url=run_url))
    return out


def _same_tenure(m: Membership, start: date | None, end: date | None, post_id) -> bool:
    return m.start_date == start and m.end_date == end and m.post_id == post_id


class MembershipWriter:
    """Upserts memberships while preserving tenure immutability."""

    def __init__(self, session: Session):
        self.session = session

    def _existing(self, person_id: str, org_id: str, post_id: str | None) -> list[Membership]:
        stmt = select(Membership).where(
            Membership.person_id == person_id,
            Membership.org_id == org_id,
        )
        if post_id is None:
            stmt = stmt.where(Membership.post_id.is_(None))
        else:
            stmt = stmt.where(Membership.post_id == post_id)
        return list(self.session.scalars(stmt))

    def record_authoritative(
        self,
        *,
        person_id: str,
        org_id: str,
        chamber: str,
        start: date | None,
        end: date | None,
        post_id: str | None = None,
        on_behalf_of_id: str | None = None,
        legislature: str | None = None,
        role: str | None = None,
        importance: int = 0,
        start_precision: str | None = None,
        end_precision: str | None = None,
        start_reason: str | None = None,
        end_reason: str | None = None,
        confidence: str = "official_ledger",
        source_url: str | None = None,
        group_acronym: str | None = None,
    ) -> Membership | None:
        """Insert or update a dated interval. Never reopens a closed tenure.

        Returns the membership written, or None if an identical closed tenure
        already exists (idempotent no-op).
        """
        if start and end and end < start:
            # Never persist an inverted interval; clamp defensively.
            end = start
        existing = self._existing(person_id, org_id, post_id)

        # Exact match (same start/end) → idempotent; refresh last_seen only.
        for m in existing:
            if _same_tenure(m, start, end, post_id):
                m.last_seen_at = _utcnow()
                if source_url and not m.source_url:
                    m.source_url = source_url
                return m

        # An open tenure with the same start can be closed / enriched.
        # When start is None and end is None (current member), match any open
        # tenure for this person+org to avoid duplicate open tenures.
        # When start is None and end is not None (former member with unknown
        # start), match an open tenure that also has start None and close it.
        # When start is not None (former member with known start date), match
        # open tenure with same start date to close it.
        matched: Membership | None = None
        for m in existing:
            if m.end_date is None:
                if start is None:
                    if end is None:
                        # Current member matching open current tenure → idempotent
                        matched = m
                        break
                    if m.start_date is None:
                        # Former member with unknown start closing open tenure
                        matched = m
                        break
                elif m.start_date == start:
                    # Former member with known start date closing open tenure
                    matched = m
                    break

        if matched is not None:
            m = matched
            if end is not None:
                m.end_date = end
                m.end_precision = end_precision
                m.end_reason = end_reason or m.end_reason
            if on_behalf_of_id:
                m.on_behalf_of_id = on_behalf_of_id
            if role:
                m.role = role
            m.last_seen_at = _utcnow()
            if source_url:
                m.source_url = source_url
            if confidence and _rank(confidence) < _rank(m.confidence):
                m.confidence = confidence
            return m

        # Otherwise create a new tenure (repeat stints coexist).
        m = Membership(
            id=str(uuid.uuid4()),
            person_id=person_id,
            org_id=org_id,
            post_id=post_id,
            on_behalf_of_id=on_behalf_of_id,
            chamber=chamber,
            legislature=legislature,
            role=role,
            importance=importance,
            start_date=start,
            end_date=end,
            start_precision=start_precision,
            end_precision=end_precision,
            start_reason=start_reason,
            end_reason=end_reason,
            confidence=confidence,
            source_url=source_url,
            group_acronym_at_event=group_acronym,
        )
        self.session.add(m)
        self.session.flush()
        return m

    def record_observation(
        self,
        *,
        person_id: str,
        org_id: str,
        chamber: str,
        observed_on: date,
        org_class: str,
        post_id: str | None = None,
        legislature: str | None = None,
        source_url: str | None = None,
    ) -> Membership:
        """Current-only roster: ensure an open membership for (person, org).

        Closes any other open membership of the same org_class for this person
        at observed_on - 1 day. Derived confidence.
        """
        existing = self._existing(person_id, org_id, post_id)
        open_match = next((m for m in existing if m.end_date is None), None)

        # Close other open memberships of the same class (person moved).
        others = self.session.scalars(
            select(Membership)
            .join(_Org, _Org.id == Membership.org_id)
            .where(
                Membership.person_id == person_id,
                Membership.end_date.is_(None),
                Membership.org_id != org_id,
                _Org.classification == org_class,
                Membership.chamber == chamber,
            )
        )
        for m in others:
            m.end_date = observed_on - timedelta(days=1)
            m.end_reason = "CHANGED_PARTY" if org_class == "group" else "UNKNOWN"
            m.last_seen_at = _utcnow()

        if open_match is not None:
            open_match.last_seen_at = _utcnow()
            return open_match

        m = Membership(
            id=str(uuid.uuid4()),
            person_id=person_id,
            org_id=org_id,
            post_id=post_id,
            chamber=chamber,
            legislature=legislature,
            start_date=observed_on,
            end_date=None,
            start_precision=observed_on.isoformat(),
            confidence="derived",
            source_url=source_url,
        )
        self.session.add(m)
        self.session.flush()
        return m


def _rank(confidence: str) -> int:
    from .db import CONFIDENCE_RANK

    return CONFIDENCE_RANK.get(confidence, 99)


def _utcnow():
    from datetime import datetime

    return datetime.now(UTC)


# Import Organization under an alias to avoid a circular import at module load.
from .db import Organization as _Org  # noqa: E402
