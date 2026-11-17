"""GraphQL API schema and resolvers."""

from datetime import date

import strawberry
from sqlalchemy import select

from pipeline.db import (
    Event,
    Membership,
    Organization,
    Person,
    make_engine,
    make_session_factory,
)
from pipeline.queries import is_group

# The GraphQL surface has no REST-style Query(ge=..., le=...) validation, so a
# single `limit: 10**9` could otherwise pull the whole table. Bound every list
# resolver at entry. (REST caps most equivalents at 500; 200 is the safe floor.)
_MAX_RESULT_LIMIT = 200


def _clamp_limit(limit: int) -> int:
    """Coerce a GraphQL limit into [1, _MAX_RESULT_LIMIT]."""
    return max(1, min(limit, _MAX_RESULT_LIMIT))


@strawberry.type
class PartyType:
    id: str
    name: str | None
    short_name: str | None
    classification: str
    color: str | None
    wikidata_qid: str | None
    founding_date: date | None
    dissolution_date: date | None
    chamber: str | None


@strawberry.type
class PersonType:
    id: str
    canonical_name: str
    birth_date: date | None
    wikidata_qid: str | None
    match_status: str


@strawberry.type
class MembershipType:
    id: str
    person_id: str
    org_id: str
    chamber: str
    legislature: str | None
    role: str | None
    start_date: date | None
    end_date: date | None
    confidence: str


@strawberry.type
class EventType:
    id: str
    type: str
    person_id: str | None
    chamber: str | None
    from_org_id: str | None
    to_org_id: str | None
    event_date: date | None
    precision: str | None
    reason: str | None
    confidence: str
    summary_ro: str | None
    summary_en: str | None


@strawberry.type
class SwitchWaveType:
    id: str
    label: str | None
    # REST null-handles these; a NULL row must not break GraphQL serialization.
    start_date: date | None
    end_date: date | None
    switch_count: int
    trigger_type: str | None
    trigger_event: str | None
    legislature: str | None
    chamber: str | None


@strawberry.type
class AnalyticsPartyCohesionType:
    party_id: str
    party_name: str
    members: int
    switches: int
    switchers: int
    avg_tenure_years: float
    switch_rate_per_mp_per_year: float


@strawberry.type
class AnalyticsCrossChamberType:
    person_id: str
    name: str
    chambers: list[str]


@strawberry.type
class AnalyticsGenerationalShiftType:
    party: str
    mps_with_birth_dates: int
    avg_age: float
    median_age: int


@strawberry.type
class Query:
    @strawberry.field
    def person(self, id: str) -> PersonType | None:
        engine = make_engine()
        session = make_session_factory(engine)()
        try:
            p = session.get(Person, id)
            if not p:
                return None
            return PersonType(
                id=p.id,
                canonical_name=p.canonical_name,
                birth_date=p.birth_date,
                wikidata_qid=p.wikidata_qid,
                match_status=p.match_status,
            )
        finally:
            session.close()

    @strawberry.field
    def persons(
        self, q: str | None = None, chamber: str | None = None, limit: int = 50
    ) -> list[PersonType]:
        limit = _clamp_limit(limit)
        engine = make_engine()
        session = make_session_factory(engine)()
        try:
            stmt = select(Person).limit(limit)
            if q:
                stmt = stmt.where(Person.canonical_name.ilike(f"%{q}%"))
            if chamber:
                stmt = stmt.where(
                    Person.id.in_(
                        select(Membership.person_id)
                        .join(Organization, Organization.id == Membership.org_id)
                        .where(is_group(), Membership.chamber == chamber)
                    )
                )
            persons = session.scalars(stmt).all()
            return [
                PersonType(
                    id=p.id,
                    canonical_name=p.canonical_name,
                    birth_date=p.birth_date,
                    wikidata_qid=p.wikidata_qid,
                    match_status=p.match_status,
                )
                for p in persons
            ]
        finally:
            session.close()

    @strawberry.field
    def party(self, short_name: str) -> PartyType | None:
        engine = make_engine()
        session = make_session_factory(engine)()
        try:
            party = session.scalars(
                select(Organization)
                .where(Organization.short_name == short_name)
                .where(Organization.classification == "party")
            ).first()
            if not party:
                return None
            return PartyType(
                id=party.id,
                name=party.name,
                short_name=party.short_name,
                classification=party.classification,
                color=party.color,
                wikidata_qid=party.wikidata_qid,
                founding_date=party.founding_date,
                dissolution_date=party.dissolution_date,
                chamber=party.chamber,
            )
        finally:
            session.close()

    @strawberry.field
    def parties(self, classification: str | None = None, limit: int = 100) -> list[PartyType]:
        limit = _clamp_limit(limit)
        engine = make_engine()
        session = make_session_factory(engine)()
        try:
            stmt = select(Organization).limit(limit)
            if classification:
                stmt = stmt.where(Organization.classification == classification)
            parties = session.scalars(stmt).all()
            return [
                PartyType(
                    id=p.id,
                    name=p.name,
                    short_name=p.short_name,
                    classification=p.classification,
                    color=p.color,
                    wikidata_qid=p.wikidata_qid,
                    founding_date=p.founding_date,
                    dissolution_date=p.dissolution_date,
                    chamber=p.chamber,
                )
                for p in parties
            ]
        finally:
            session.close()

    @strawberry.field
    def memberships(
        self,
        person_id: str | None = None,
        org_id: str | None = None,
        chamber: str | None = None,
        limit: int = 100,
    ) -> list[MembershipType]:
        limit = _clamp_limit(limit)
        engine = make_engine()
        session = make_session_factory(engine)()
        try:
            # Group tenures only: committees are organisations too, and their
            # memberships are a separate surface (see the /committees route).
            stmt = (
                select(Membership)
                .join(Organization, Organization.id == Membership.org_id)
                .where(is_group())
            )
            if person_id:
                stmt = stmt.where(Membership.person_id == person_id)
            if org_id:
                stmt = stmt.where(Membership.org_id == org_id)
            if chamber:
                stmt = stmt.where(Membership.chamber == chamber)
            memberships = session.scalars(stmt.limit(limit)).all()
            return [
                MembershipType(
                    id=m.id,
                    person_id=m.person_id,
                    org_id=m.org_id,
                    chamber=m.chamber,
                    legislature=m.legislature,
                    role=m.role,
                    start_date=m.start_date,
                    end_date=m.end_date,
                    confidence=m.confidence,
                )
                for m in memberships
            ]
        finally:
            session.close()

    @strawberry.field
    def events(
        self,
        person_id: str | None = None,
        event_type: str | None = None,
        chamber: str | None = None,
        start: date | None = None,
        end: date | None = None,
        limit: int = 200,
    ) -> list[EventType]:
        limit = _clamp_limit(limit)
        engine = make_engine()
        session = make_session_factory(engine)()
        try:
            stmt = select(Event).limit(limit)
            if person_id:
                stmt = stmt.where(Event.person_id == person_id)
            if event_type:
                stmt = stmt.where(Event.type == event_type)
            if chamber:
                stmt = stmt.where(Event.chamber == chamber)
            if start:
                stmt = stmt.where(Event.event_date >= start)
            if end:
                stmt = stmt.where(Event.event_date <= end)
            stmt = stmt.order_by(Event.event_date.desc())
            events = session.scalars(stmt).all()
            return [
                EventType(
                    id=e.id,
                    type=e.type,
                    person_id=e.person_id,
                    chamber=e.chamber,
                    from_org_id=e.from_org_id,
                    to_org_id=e.to_org_id,
                    event_date=e.event_date,
                    precision=e.precision,
                    reason=e.reason,
                    confidence=e.confidence,
                    summary_ro=e.summary_ro,
                    summary_en=e.summary_en,
                )
                for e in events
            ]
        finally:
            session.close()

    @strawberry.field
    def switch_waves(
        self, chamber: str | None = None, legislature: str | None = None, limit: int = 100
    ) -> list[SwitchWaveType]:
        limit = _clamp_limit(limit)
        engine = make_engine()
        session = make_session_factory(engine)()
        try:
            from sqlalchemy import select

            from pipeline.db import SwitchWave

            stmt = select(SwitchWave).order_by(SwitchWave.start_date.desc()).limit(limit)
            if chamber:
                stmt = stmt.where(SwitchWave.chamber == chamber)
            if legislature:
                stmt = stmt.where(SwitchWave.legislature == legislature)
            waves = session.scalars(stmt).all()
            return [
                SwitchWaveType(
                    id=w.id,
                    label=w.label,
                    start_date=w.start_date,
                    end_date=w.end_date,
                    switch_count=w.switch_count,
                    trigger_type=w.trigger_type,
                    trigger_event=w.trigger_event,
                    legislature=w.legislature,
                    chamber=w.chamber,
                )
                for w in waves
            ]
        finally:
            session.close()

    @strawberry.field
    def party_cohesion(
        self, legislature: str | None = None, limit: int = 100
    ) -> list[AnalyticsPartyCohesionType]:
        limit = _clamp_limit(limit)
        engine = make_engine()
        session = make_session_factory(engine)()
        try:
            from collections import defaultdict

            from sqlalchemy import select

            from pipeline.db import Event, KeyEvent, Organization

            stmt = select(Event).where(Event.type == "switch_party")
            if legislature:
                leg_key = session.scalars(
                    select(KeyEvent).where(
                        KeyEvent.type == "legislature", KeyEvent.label == legislature
                    )
                ).first()
                if leg_key and leg_key.start_date and leg_key.end_date:
                    stmt = stmt.where(
                        Event.event_date >= leg_key.start_date, Event.event_date <= leg_key.end_date
                    )
            stmt = stmt.where(Event.event_date.is_not(None))

            switches = list(session.scalars(stmt))

            party_switches: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

            for sw in switches:
                if sw.to_org_id:
                    org = session.get(Organization, sw.to_org_id)
                    if org and org.classification == "party":
                        party_switches[sw.to_org_id][sw.person_id] += 1
                    elif org and is_group(org):
                        # on_behalf_of_id is a Membership column, not an Organization one.
                        m = session.scalars(
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
                party = session.get(Organization, party_id)
                if not party or party.classification != "party":
                    continue

                party_memberships = session.scalars(
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
                    total_switches / (num_members * avg_tenure)
                    if num_members * avg_tenure > 0
                    else 0
                )

                party_label = party.short_name or party.name or "Unknown"
                results.append(
                    AnalyticsPartyCohesionType(
                        party_id=party.id,
                        party_name=party_label,
                        members=num_members,
                        switches=total_switches,
                        switchers=num_switchers,
                        avg_tenure_years=round(avg_tenure, 1),
                        switch_rate_per_mp_per_year=round(switch_rate, 4),
                    )
                )

            return results[:limit]
        finally:
            session.close()

    @strawberry.field
    def cross_chamber(self) -> list[AnalyticsCrossChamberType]:
        engine = make_engine()
        session = make_session_factory(engine)()
        try:
            from sqlalchemy import select

            from pipeline.db import Membership, Person

            stmt = select(Person.id, Person.canonical_name).distinct()
            persons = list(session.execute(stmt).all())

            results = []
            for pid, name in persons:
                chs = session.scalars(
                    select(Membership.chamber)
                    .join(Organization, Organization.id == Membership.org_id)
                    .where(is_group(), Membership.person_id == pid)
                    .distinct()
                ).all()
                if len(chs) > 1:
                    results.append(
                        AnalyticsCrossChamberType(
                            person_id=pid,
                            name=name,
                            chambers=chs,
                        )
                    )

            return results
        finally:
            session.close()

    @strawberry.field
    def generational_shift(
        self, legislature: str | None = None, limit: int = 100
    ) -> list[AnalyticsGenerationalShiftType]:
        limit = _clamp_limit(limit)
        engine = make_engine()
        session = make_session_factory(engine)()
        try:
            from sqlalchemy import select

            from pipeline.db import KeyEvent, Membership, Organization, Person

            stmt = select(Person.id, Person.canonical_name, Person.birth_date)
            if legislature:
                leg_key = session.scalars(
                    select(KeyEvent).where(
                        KeyEvent.type == "legislature", KeyEvent.label == legislature
                    )
                ).first()
                if leg_key and leg_key.start_date and leg_key.end_date:
                    stmt = stmt.where(
                        Person.id.in_(
                            select(Membership.person_id)
                            .join(Organization, Organization.id == Membership.org_id)
                            .where(
                                is_group(),
                                Membership.start_date <= leg_key.end_date,
                            )
                            .where(
                                (Membership.end_date.is_(None))
                                | (Membership.end_date >= leg_key.start_date)
                            )
                        )
                    )

            persons = list(session.execute(stmt).all())
            ages_by_party: dict[str, list[int]] = {}

            for pid, _name, bdate in persons:
                if not bdate:
                    continue
                age = (date.today() - bdate).days / 365.25

                party_mems = session.scalars(
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
                        AnalyticsGenerationalShiftType(
                            party=party,
                            mps_with_birth_dates=len(ages),
                            avg_age=round(avg_age, 1),
                            median_age=median_age,
                        )
                    )

            return results[:limit]
        finally:
            session.close()


schema = strawberry.Schema(query=Query)
