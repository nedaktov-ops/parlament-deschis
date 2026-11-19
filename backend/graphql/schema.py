"""GraphQL API schema and resolvers.

Every resolver reads its SQLAlchemy session from ``info.context["db"]``. The
session is created once per HTTP request by the ``get_db`` FastAPI dependency
(which the GraphQL ``context_getter`` delegates to), so:

* a multi-field query shares one session and one engine — no per-field
  ``make_engine()`` calls, no leaked engines;
* ``app.dependency_overrides[get_db]`` works for GraphQL exactly as it does
  for REST;
* the engine is the app-scoped one built from ``backend.config.DB_PATH`` and
  disposed on shutdown, not pipeline's unrelated ``DEFAULT_DB_PATH``.

``make_engine`` is kept as a module symbol for backwards compatibility with
existing monkeypatches (see ``tests/test_security_hardening.py``); the app's
engine builder resolves through it so a patched factory is still honoured.
"""

from datetime import date

import strawberry
from sqlalchemy import or_, select
from sqlalchemy.orm import aliased

from backend.config import DB_PATH as _CONFIG_DB_PATH
from pipeline.db import (
    Event,
    KeyEvent,
    Mandate,
    Membership,
    Organization,
    Person,
    SwitchWave,
)
from pipeline.db import (
    make_engine as _pipeline_make_engine,
)
from pipeline.queries import is_group

# The GraphQL surface has no REST-style Query(ge=..., le=...) validation, so a
# single `limit: 10**9` could otherwise pull the whole table. Bound every list
# resolver at entry. (REST caps most equivalents at 500; 200 is the safe floor.)
_MAX_RESULT_LIMIT = 200


def _clamp_limit(limit: int) -> int:
    """Coerce a GraphQL limit into [1, _MAX_RESULT_LIMIT]."""
    return max(1, min(limit, _MAX_RESULT_LIMIT))


def make_engine(db_path=None, echo=False):
    """Compatibility engine factory — defaults to the config DB path.

    Resolvers no longer call this directly; it is the single factory the app's
    lifespan-scoped engine builder uses, so an existing monkeypatch (e.g. the
    limit-clamp regression test) still swaps in its own seeded engine.
    """
    return _pipeline_make_engine(db_path if db_path is not None else _CONFIG_DB_PATH, echo=echo)


def _session(info: strawberry.Info):
    """Return the per-request session injected by the GraphQL context getter."""
    return info.context["db"]


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
    def person(self, info: strawberry.Info, id: str) -> PersonType | None:
        session = _session(info)
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

    @strawberry.field
    def persons(
        self,
        info: strawberry.Info,
        q: str | None = None,
        chamber: str | None = None,
        limit: int = 50,
    ) -> list[PersonType]:
        limit = _clamp_limit(limit)
        session = _session(info)
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

    @strawberry.field
    def party(self, info: strawberry.Info, short_name: str) -> PartyType | None:
        session = _session(info)
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

    @strawberry.field
    def parties(
        self,
        info: strawberry.Info,
        classification: str | None = None,
        limit: int = 100,
    ) -> list[PartyType]:
        limit = _clamp_limit(limit)
        session = _session(info)
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

    @strawberry.field
    def memberships(
        self,
        info: strawberry.Info,
        person_id: str | None = None,
        org_id: str | None = None,
        chamber: str | None = None,
        limit: int = 100,
    ) -> list[MembershipType]:
        limit = _clamp_limit(limit)
        session = _session(info)
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

    @strawberry.field
    def events(
        self,
        info: strawberry.Info,
        person_id: str | None = None,
        event_type: str | None = None,
        chamber: str | None = None,
        start: date | None = None,
        end: date | None = None,
        limit: int = 200,
    ) -> list[EventType]:
        limit = _clamp_limit(limit)
        session = _session(info)
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

    @strawberry.field
    def switch_waves(
        self,
        info: strawberry.Info,
        chamber: str | None = None,
        legislature: str | None = None,
        limit: int = 100,
    ) -> list[SwitchWaveType]:
        limit = _clamp_limit(limit)
        session = _session(info)
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

    @strawberry.field
    def party_cohesion(
        self,
        info: strawberry.Info,
        legislature: str | None = None,
        limit: int = 100,
    ) -> list[AnalyticsPartyCohesionType]:
        limit = _clamp_limit(limit)
        session = _session(info)
        from collections import defaultdict

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
                total_switches / (num_members * avg_tenure) if num_members * avg_tenure > 0 else 0
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

    @strawberry.field
    def cross_chamber(
        self, info: strawberry.Info, as_of: date | None = None
    ) -> list[AnalyticsCrossChamberType]:
        """People with mandates in both chambers — same Mandate-based source of
        truth as ``GET /api/analytics/cross-chamber``.

        One batched SQL statement replaces the old per-person N+1 (3,389
        statements) and the 233 group-tenure count that disagreed with REST's 39.
        """
        session = _session(info)
        reference = as_of or date.today()
        rows = session.execute(
            select(Person.id, Person.canonical_name, Mandate.chamber)
            .join(Mandate, Mandate.person_id == Person.id)
            .where(
                Mandate.chamber.in_(("deputies", "senate")),
                Mandate.start_date.is_not(None),
                Mandate.start_date <= reference,
            )
            .order_by(Person.canonical_name, Mandate.chamber)
        ).all()

        careers: dict[str, dict] = {}
        for person_id, name, chamber in rows:
            career = careers.setdefault(person_id, {"name": name, "chambers": set()})
            career["chambers"].add(chamber)

        return [
            AnalyticsCrossChamberType(
                person_id=person_id,
                name=career["name"],
                chambers=sorted(career["chambers"]),
            )
            for person_id, career in careers.items()
            if len(career["chambers"]) == 2
        ]

    @strawberry.field
    def generational_shift(
        self,
        info: strawberry.Info,
        legislature: str | None = None,
        as_of: date | None = None,
        limit: int = 100,
    ) -> list[AnalyticsGenerationalShiftType]:
        """Party age summaries, joined through ``Membership.on_behalf_of_id``.

        Mirrors ``pipeline.analytics.generational_shift`` (the REST source of
        truth): parties live in ``on_behalf_of_id``, never in ``org_id``, so the
        old ``org_id``+party filter always returned an empty array. Deduping by
        ``(person_id, party)`` and batching the join into one statement also kills
        the old 3,115-statement N+1.
        """
        limit = _clamp_limit(limit)
        session = _session(info)
        evaluation_date = as_of or date.today()
        if legislature and as_of is None:
            keys = session.scalars(
                select(KeyEvent).where(
                    KeyEvent.type == "legislature", KeyEvent.label == legislature
                )
            ).all()
            starts = [key.start_date for key in keys if key.start_date]
            if not starts:
                return []
            evaluation_date = max(key.end_date or date.today() for key in keys)

        group = aliased(Organization)
        party = aliased(Organization)
        stmt = (
            select(Person.id, Person.birth_date, party.id, party.short_name, party.name)
            .join(Membership, Membership.person_id == Person.id)
            .join(group, group.id == Membership.org_id)
            .join(party, party.id == Membership.on_behalf_of_id)
            .where(
                Person.birth_date.is_not(None),
                is_group(group),
                party.classification == "party",
                Membership.start_date <= evaluation_date,
                or_(Membership.end_date.is_(None), Membership.end_date > evaluation_date),
            )
        )
        if legislature:
            stmt = stmt.where(Membership.legislature == legislature)

        ages_by_party: dict[str, dict[str, int]] = {}
        party_names: dict[str, str] = {}
        for person_id, birth_date, party_id, short_name, party_name in session.execute(stmt):
            age = evaluation_date.year - birth_date.year
            if (evaluation_date.month, evaluation_date.day) < (birth_date.month, birth_date.day):
                age -= 1
            if age < 0:
                continue
            ages_by_party.setdefault(party_id, {})[person_id] = age
            party_names[party_id] = short_name or party_name

        results = []
        for party_id, ages in ages_by_party.items():
            if not ages:
                continue
            values = list(ages.values())
            sorted_ages = sorted(values)
            results.append(
                AnalyticsGenerationalShiftType(
                    party=party_names[party_id],
                    mps_with_birth_dates=len(ages),
                    avg_age=round(sum(values) / len(values), 1),
                    median_age=sorted_ages[len(sorted_ages) // 2],
                )
            )
        results.sort(key=lambda r: r.party)
        return results[:limit]


schema = strawberry.Schema(query=Query)
