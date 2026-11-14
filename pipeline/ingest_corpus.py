"""Ingest a collected cdep.ro corpus into the temporal store.

The corpus is the *official* record: dated group ledgers plus the MP profile
graph. This module turns it into people, organisations, dated tenures,
evidence and coverage — without inventing a single date.

Rules that keep the statistics honest:

* A published "Membru din" date is used as-is. When it is absent the start is
  **inferred**, in this order: the person's own mandate validation date
  ("data validării"), then the group's founding date, then the legislature
  start. Inferred tenures are marked and carry a lower confidence.
* A published "Membru până" date closes the tenure. The chamber publishes no
  *reason* for a departure, so the reason is classified afterwards from what
  the rest of the record shows — never asserted at ingest time.
* The person's identity comes from the profile mandate graph, never from a
  name match.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from .collect import Corpus, LedgerRecord
from .db import (
    Coverage,
    Evidence,
    Fragment,
    Mandate,
    Membership,
    Organization,
    Person,
    PersonIdentifier,
    PersonName,
)
from .events import derive_group_events, derive_org_events
from .ingest import get_or_create_org, legislature_start, seed_key_events
from .normalize import canonical_group_short, name_sort_key, normalize_name
from .parse.cdep_profile import MandateRef

log = logging.getLogger("parlament.ingest_corpus")

_ACRONYM = re.compile(r"^[A-ZĂÂÎȘȚ][A-ZĂÂÎȘȚ0-9.\- ]{1,12}$")

# Groups that are not a party in themselves.
_NON_PARTY_GROUPS = {"NEAFILIATI", "MINORITATI", "MINORITĂŢI", "PROGRESSIVE", "PROGRESIST"}


def party_short(label: str | None) -> str | None:
    """Canonical acronym for a party label.

    The ledger's ``Partid`` column is normally already an acronym ("PSD",
    "FDSN"), including for historical parties the reference file has never
    heard of, so an upper-case token is accepted as-is.
    """
    if not label:
        return None
    text = label.strip()
    if not text:
        return None
    known = canonical_group_short(text)
    if known:
        return known
    if _ACRONYM.match(text):
        return text.replace(".", "").replace(" ", "").upper()
    return None


def _leg_end(legislature: str | None) -> date | None:
    from .ingest import LEGI

    if legislature and legislature in LEGI:
        raw = LEGI[legislature].get("end")
        return date.fromisoformat(raw) if raw else None
    return None


class CorpusIngestor:
    """Write one collected corpus into the database."""

    def __init__(self, session: Session, corpus: Corpus):
        self.session = session
        self.corpus = corpus
        self.group_orgs: dict[tuple[str, str, str], Organization] = {}
        self.party_orgs: dict[str, Organization] = {}
        self.persons: dict[str, Person] = {}
        self.stats = {
            "persons": 0,
            "memberships": 0,
            "inferred_starts": 0,
            "inferred_unaffiliated": 0,
            "evidence": 0,
            "events": 0,
            "ambiguous": 0,
            "duplicate_stints": 0,
        }

    # --- organisations ---------------------------------------------------
    def _party_org(self, label: str | None) -> Organization | None:
        short = party_short(label)
        if not short:
            return None
        if short in self.party_orgs:
            return self.party_orgs[short]
        org = get_or_create_org(
            self.session,
            classification="party",
            name=short,
            short_name=short,
            chamber=None,
        )
        self.party_orgs[short] = org
        return org

    def _group_org(self, rec: LedgerRecord) -> Organization:
        key = (rec.chamber, rec.legislature, rec.idg)
        if key in self.group_orgs:
            return self.group_orgs[key]
        meta = rec.ledger.meta
        short = canonical_group_short(meta.short_name or "") or meta.short_name
        short = canonical_group_short(meta.name) or short
        if short:
            short = short.upper()
        org = get_or_create_org(
            self.session,
            classification="group",
            name=meta.name,
            short_name=short,
            chamber=rec.chamber,
            founding_date=meta.founding_date.earliest if meta.founding_date else None,
            former_name=meta.former_name,
        )
        self.group_orgs[key] = org
        return org

    # --- people ----------------------------------------------------------
    def _person(self, mandate: MandateRef, fallback_name: str) -> Person:
        cluster = self.corpus.clusters.get(mandate)
        if cluster is None:
            cluster = f"cdep-person:{mandate.key}"
        person = self.persons.get(cluster)
        if person is not None:
            return person
        ident = self.session.scalars(
            select(PersonIdentifier).where(
                PersonIdentifier.scheme == "cdep_person",
                PersonIdentifier.identifier == cluster,
            )
        ).first()
        if ident is not None:
            person = self.session.get(Person, ident.person_id)
        else:
            record = self.corpus.profiles.get(mandate)
            profile = record.profile if record else None
            name = (profile.name if profile else fallback_name) or fallback_name
            birth = profile.birth_date.earliest if profile and profile.birth_date else None
            person = Person(
                canonical_name=name,
                normalized_name=normalize_name(name),
                sort_key=name_sort_key(name),
                birth_date=birth,
                match_status="auto",
            )
            self.session.add(person)
            self.session.flush()
            self.session.add(
                PersonIdentifier(
                    person_id=person.id,
                    scheme="cdep_person",
                    identifier=cluster,
                    legislature=None,
                )
            )
            self.session.add(
                PersonName(
                    person_id=person.id,
                    type="name",
                    name=name,
                    normalized_name=normalize_name(name),
                    sort_key=name_sort_key(name),
                )
            )
            self.stats["persons"] += 1
        self.persons[cluster] = person

        # The per-mandate identifier is scoped to its legislature.
        mandate_id = f"{mandate.chamber}:{mandate.legislature}:{mandate.idm}"
        existing = self.session.scalars(
            select(PersonIdentifier).where(
                PersonIdentifier.scheme == "cdep_mandate",
                PersonIdentifier.identifier == mandate_id,
                PersonIdentifier.legislature == mandate.legislature,
            )
        ).first()
        if existing is None:
            self.session.add(
                PersonIdentifier(
                    person_id=person.id,
                    scheme="cdep_mandate",
                    identifier=mandate_id,
                    legislature=mandate.legislature,
                )
            )
        return person

    # --- tenures ---------------------------------------------------------
    def _write_mandate(self, mandate: MandateRef, person: Person) -> None:
        """Persist the published mandate: the person's validation date.

        The group ledgers say who sat where; the profile page says when the
        mandate itself began. Storing both lets the reconciliation check
        prove that the ledgers cover the whole mandate.
        """
        record = self.corpus.profiles.get(mandate)
        profile = record.profile if record else None
        if profile is None:
            return
        existing = self.session.scalars(
            select(Mandate).where(
                Mandate.person_id == person.id,
                Mandate.chamber == mandate.chamber,
                Mandate.legislature == mandate.legislature,
            )
        ).first()
        if existing is not None:
            return
        start = profile.validation_date.earliest if profile.validation_date else None
        precision = profile.validation_date.precision if profile.validation_date else None
        self.session.add(
            Mandate(
                person_id=person.id,
                chamber=mandate.chamber,
                legislature=mandate.legislature,
                start_date=start,
                end_date=_leg_end(mandate.legislature),
                start_precision=precision,
                end_precision="day",
                constituency=getattr(profile, "constituency", None),
                role=getattr(profile, "role", None),
                source_url=record.url if record else None,
                snapshot_hash=record.sha256 if record else None,
                confidence="official_profile" if start else "derived",
            )
        )

    def _start_for(self, mandate: MandateRef, join, founding, leg_start):
        """Return (start_date, precision, reason, inferred)."""
        if join is not None:
            return join.earliest, join.precision, "PUBLISHED", False
        record = self.corpus.profiles.get(mandate)
        profile = record.profile if record else None
        if profile is not None and profile.validation_date is not None:
            return (
                profile.validation_date.earliest,
                profile.validation_date.precision,
                "VALIDATION_DATE",
                True,
            )
        if founding is not None:
            return founding.earliest, founding.precision, "FOUNDING_DATE", True
        if leg_start is not None:
            return leg_start, leg_start.isoformat(), "LEGISLATURE_START", True
        return None, None, "UNKNOWN", True

    def _write_membership(
        self,
        *,
        person: Person,
        group: Organization,
        party: Organization | None,
        rec: LedgerRecord,
        mandate: MandateRef,
        join,
        leave,
        role: str | None,
        short: str | None,
        member_party_label: str | None = None,
        name: str | None = None,
    ) -> Membership | None:
        meta = rec.ledger.meta
        leg_start = legislature_start(rec.legislature)
        start, precision, start_reason, inferred = self._start_for(
            mandate, join, meta.founding_date, leg_start
        )
        end = leave.earliest if leave is not None else None
        end_precision = leave.precision if leave is not None else None
        confidence = "derived" if inferred else "official_ledger"
        membership = Membership(
            person_id=person.id,
            org_id=group.id,
            chamber=rec.chamber,
            legislature=rec.legislature,
            role=role,
            start_date=start,
            end_date=end,
            start_precision=precision,
            end_precision=end_precision,
            start_reason=start_reason,
            end_reason=None,
            confidence=confidence,
            source_url=rec.url,
            on_behalf_of_id=party.id if party is not None else None,
            group_acronym_at_event=short,
            member_party_label=member_party_label,
            member_name=name,
        )
        self.session.add(membership)
        self.session.flush()
        self.session.add(
            Evidence(
                membership_id=membership.id,
                type="official_ledger",
                source_url=rec.url,
                snapshot_hash=rec.sha256,
                note=(
                    "start inferred from the member's mandate validation date"
                    if start_reason == "VALIDATION_DATE"
                    else "start inferred from the legislature start"
                    if start_reason == "LEGISLATURE_START"
                    else None
                ),
            )
        )
        self.stats["memberships"] += 1
        self.stats["evidence"] += 1
        if inferred:
            self.stats["inferred_starts"] += 1
        return membership

    # --- main ------------------------------------------------------------
    def run(self) -> dict:
        session = self.session
        seed_key_events(session)

        # 1. Organisations and the party behind each group.
        for rec in self.corpus.ledgers:
            group = self._group_org(rec)
            derive_org_events(session, group)
            short = group.short_name
            if short and short.upper() not in _NON_PARTY_GROUPS:
                self._party_org(short)
        session.flush()

        # 2. Dated tenures from every ledger.
        #
        # The same stint is often published twice: once in the group's current
        # table (with the departure written inside the name cell) and once in
        # its former table. Writing both would give the member two overlapping
        # tenures and a phantom conflict, so the rows are collapsed first,
        # keeping the one that publishes a join date.
        #
        # The collapse is a separate pass on purpose: the winner of a pair is
        # decided by the whole set of rows, not by the order they happen to
        # arrive in. A row without a join date must never shadow a row that
        # has one, and the reverse must be true as well.
        chosen: dict[
            tuple[str, str, str, str, date | None, date | None],
            tuple[LedgerRecord, object, object, object],
        ] = {}
        for rec in self.corpus.ledgers:
            group = self._group_org(rec)
            for row in rec.ledger.current + rec.ledger.former:
                if not row.idm:
                    continue
                mandate = MandateRef(rec.chamber, rec.legislature, row.idm)
                person = self._person(mandate, row.name)
                key = (
                    person.id,
                    group.id,
                    rec.chamber,
                    rec.legislature,
                    row.group_join.earliest if row.group_join else None,
                    row.group_leave.earliest if row.group_leave else None,
                )
                current = chosen.get(key)
                if current is None:
                    chosen[key] = (rec, row, person, group)
                    continue
                self.stats["duplicate_stints"] += 1
                _, old_row, _, _ = current
                if old_row.group_join is None and row.group_join is not None:
                    chosen[key] = (rec, row, person, group)

        for (
            person_id,
            group_id,
            _chamber,
            _legislature,
            _join,
            _leave,
        ), (
            rec,
            row,
            person,
            group,
        ) in chosen.items():
            mandate = MandateRef(rec.chamber, rec.legislature, row.idm)
            short = group.short_name
            self._write_mandate(mandate, person)
            # The party behind the group comes from the group's own
            # published title ("Grupul parlamentar al Partidului X"), which
            # names one party for the whole legislature. The row's
            # "Partid" cell is the *member's* party: it is missing from
            # several group tables and it is not dated, so it is stored
            # as evidence but never used as the group's affiliation.
            party = None
            if short and short.upper() not in _NON_PARTY_GROUPS:
                party = self.party_orgs.get(short.upper())
            self._write_membership(
                person=person,
                group=group,
                party=party,
                rec=rec,
                mandate=mandate,
                join=row.group_join,
                leave=row.group_leave,
                role=row.role,
                short=short,
                member_party_label=row.party,
                name=row.name,
            )
        session.flush()

        # 2b. Constrain the inferred starts by the dated hand-offs.
        #
        # Many ledgers publish the end of a tenure but not its beginning. The
        # start is then inferred (from the mandate validation date or the
        # legislature start), which places the member in the new group from
        # the beginning of the legislature. That is wrong, and it hides the
        # switch: a deputy who left PSD on 4 feb. 2019 and whose PRO row
        # carries no join date would appear to have been in PRO since 2016,
        # so the move would never be counted.
        #
        # A member sits in exactly one group at a time, so a tenure cannot
        # begin before the previous tenure ended. The inferred start is
        # therefore raised to the end of the latest closed tenure that
        # precedes it in the same scope.
        self._constrain_starts()
        session.flush()

        #    the interval from the neighbouring group ledgers of the same
        #    person, and say so in the evidence note.
        self._ingest_name_only()
        session.flush()

        # 4. Classify the reason for each departure from the rest of the record.
        self._classify_end_reasons()
        session.flush()

        # 5. Snapshots and coverage.
        self._record_fragments()
        self._record_coverage()
        session.flush()

        # 6. Events.
        self.stats["events"] = derive_group_events(session)
        session.flush()
        return self.stats

    def _constrain_starts(self) -> None:
        """Raise an inferred start to the end of the previous closed tenure.

        Only tenures whose start was *inferred* are moved: a published join
        date is the source's own statement and is never touched. The new
        value is recorded, so a reader can see that the start is a bound
        derived from the neighbouring handoff and not a published fact.
        """
        session = self.session
        rows = list(
            session.scalars(
                select(Membership).where(
                    Membership.start_date.is_not(None),
                    Membership.end_date.is_not(None),
                )
            )
        )
        by_person: dict[tuple[str, str | None, str | None], list[Membership]] = defaultdict(list)
        for m in rows:
            by_person[(m.person_id, m.chamber, m.legislature)].append(m)

        moved = 0
        for items in by_person.values():
            for m in items:
                if m.start_reason == "PUBLISHED":
                    continue
                latest_end = None
                for other in items:
                    if other.id == m.id or other.end_date is None:
                        continue
                    if other.end_date > m.end_date:
                        continue
                    if other.end_date == m.end_date and other.start_date == m.start_date:
                        # the same interval published twice
                        continue
                    if latest_end is None or other.end_date > latest_end:
                        latest_end = other.end_date
                if latest_end is not None and m.start_date < latest_end:
                    m.start_date = latest_end
                    m.start_precision = latest_end.isoformat()
                    m.start_reason = "CONSTRAINED_BY_HANDOFF"
                    m.confidence = "derived"
                    moved += 1
        if moved:
            self.stats["constrained_starts"] = moved
            log.info("%d inferred starts were raised to the previous hand-off", moved)

    def _ingest_name_only(self) -> None:
        session = self.session
        for rec in self.corpus.ledgers:
            if not rec.ledger.name_only:
                continue
            group = self._group_org(rec)
            short = group.short_name
            leg_start = legislature_start(rec.legislature)
            leg_end = _leg_end(rec.legislature)
            for row in rec.ledger.name_only:
                if not row.idm:
                    continue
                mandate = MandateRef(rec.chamber, rec.legislature, row.idm)
                person = self._person(mandate, row.name)
                others = list(
                    session.scalars(
                        select(Membership).where(
                            Membership.person_id == person.id,
                            Membership.chamber == rec.chamber,
                            Membership.legislature == rec.legislature,
                        )
                    )
                )
                others.sort(key=lambda m: (m.start_date or date.min, m.end_date or date.max))
                # The chamber publishes this roster without dates, so the
                # intervals are read off the member's other tenures: every
                # stretch of the mandate that is not covered by a dated group
                # was spent unaffiliated. A member who joined a party in 1993
                # and came back in 1995 was unaffiliated twice, and both
                # stretches are recorded.
                covered: list[tuple[date, date | None]] = []
                for m in others:
                    if m.org_id == group.id or m.start_date is None:
                        continue
                    covered.append((m.start_date, m.end_date))
                covered.sort(key=lambda iv: iv[0])

                spans: list[tuple[date, date | None]] = []
                cursor = leg_start
                for start, end in covered:
                    if cursor is None:
                        break
                    if start > cursor:
                        spans.append((cursor, start))
                    if end is None:
                        cursor = None
                    elif end > cursor:
                        cursor = end
                if cursor is not None and leg_end is not None and cursor < leg_end:
                    spans.append((cursor, leg_end))
                if not covered and leg_start is not None and leg_end is not None:
                    # No dated tenure at all: the whole mandate was
                    # unaffiliated.
                    spans.append((leg_start, leg_end))

                for start, end in spans:
                    membership = Membership(
                        person_id=person.id,
                        org_id=group.id,
                        chamber=rec.chamber,
                        legislature=rec.legislature,
                        start_date=start,
                        end_date=end,
                        start_precision=start.isoformat() if start else None,
                        end_precision=end.isoformat() if end else None,
                        start_reason="INFERRED_UNAFFILIATED",
                        end_reason=None,
                        confidence="derived",
                        source_url=rec.url,
                        group_acronym_at_event=short,
                        member_name=row.name,
                    )
                    session.add(membership)
                    session.flush()
                    session.add(
                        Evidence(
                            membership_id=membership.id,
                            type="official_ledger",
                            source_url=rec.url,
                            snapshot_hash=rec.sha256,
                            note=(
                                "the chamber publishes this unaffiliated roster without "
                                "dates; the interval is the part of the member's mandate "
                                "that no dated group tenure covers"
                            ),
                        )
                    )
                    self.stats["memberships"] += 1
                    self.stats["evidence"] += 1
                    self.stats["inferred_unaffiliated"] += 1

    def _classify_end_reasons(self) -> None:
        """Give each closed tenure an honest reason.

        The ledgers publish *when* a member left a group, never *why*. The
        reason is therefore read off the rest of the record: a successor group
        tenure means the member changed group; a departure at the end of the
        legislature means the term ended; anything else stays UNKNOWN.
        """
        session = self.session
        memberships = list(
            session.scalars(
                select(Membership)
                .join(Organization, Organization.id == Membership.org_id)
                .where(Organization.classification == "group")
                .where(Membership.end_date.isnot(None))
            )
        )
        by_person: dict[str, list[Membership]] = defaultdict(list)
        for m in memberships:
            by_person[m.person_id].append(m)
        for series in by_person.values():
            series.sort(key=lambda m: (m.start_date or date.min, m.end_date or date.max))
            for i, m in enumerate(series):
                successor = series[i + 1] if i + 1 < len(series) else None
                leg_end = _leg_end(m.legislature)
                if successor is not None and successor.org_id != m.org_id:
                    if successor.start_date is not None and successor.start_date >= m.end_date:
                        m.end_reason = "CHANGED_GROUP"
                        continue
                if leg_end is not None and abs((leg_end - m.end_date).days) <= 45:
                    m.end_reason = "END_OF_TERM"
                    continue
                m.end_reason = "UNKNOWN"

    def _record_fragments(self) -> None:
        session = self.session
        for rec in self.corpus.ledgers:
            group_key = f"{rec.chamber}:{rec.legislature}:{rec.idg}"
            exists = session.scalars(
                select(Fragment).where(
                    Fragment.model == "group_ledger",
                    Fragment.group_key == group_key,
                    Fragment.checksum == rec.sha256,
                )
            ).first()
            if exists is not None:
                continue
            session.add(
                Fragment(
                    model="group_ledger",
                    source_name="cdep",
                    source_id=rec.idg,
                    source_url=rec.url,
                    group_key=group_key,
                    checksum=rec.sha256,
                    data={
                        "chamber": rec.chamber,
                        "legislature": rec.legislature,
                        "short_name": rec.ledger.meta.short_name,
                        "current": len(rec.ledger.current),
                        "former": len(rec.ledger.former),
                        "name_only": len(rec.ledger.name_only),
                        "fetched_at": rec.fetched_at.isoformat(),
                    },
                )
            )

    def _record_coverage(self) -> None:
        session = self.session
        grouped: dict[tuple[str, str], list[LedgerRecord]] = defaultdict(list)
        for rec in self.corpus.ledgers:
            grouped[(rec.chamber, rec.legislature)].append(rec)
        for (chamber, legislature), recs in grouped.items():
            members = sum(len(r.ledger.current) + len(r.ledger.name_only) for r in recs)
            former = sum(len(r.ledger.former) for r in recs)
            profile_errors = sum(
                1
                for rec in recs
                for row in rec.ledger.current + rec.ledger.former + rec.ledger.name_only
                if row.idm
                and (
                    MandateRef(chamber, legislature, row.idm) in self.corpus.profiles
                    and self.corpus.profiles[MandateRef(chamber, legislature, row.idm)].error
                )
            )
            complete = profile_errors == 0 and len(recs) > 0
            note = (
                f"{len(recs)} group ledgers; {members} current members, {former} former; "
                f"{profile_errors} profile(s) unavailable"
            )
            exists = session.scalars(
                select(Coverage).where(
                    Coverage.chamber == chamber, Coverage.legislature == legislature
                )
            ).first()
            if exists is None:
                session.add(
                    Coverage(
                        chamber=chamber,
                        legislature=legislature,
                        period_start=legislature_start(legislature),
                        period_end=_leg_end(legislature),
                        completeness="full" if complete else "partial",
                        note=note,
                    )
                )
            else:
                exists.completeness = "full" if complete else "partial"
                exists.note = note


def ingest_corpus(session: Session, corpus: Corpus) -> dict:
    """Write a collected corpus into the database and return ingest statistics."""
    return CorpusIngestor(session, corpus).run()
