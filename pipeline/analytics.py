"""Analytical layer: switch wave detection, party cohesion, committee control, etc."""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from .db import (
    Event,
    KeyEvent,
    Mandate,
    Membership,
    Organization,
    Person,
    SwitchWave,
    init_db,
    make_engine,
    make_session_factory,
)

# Known trigger dates for Romanian elections and government formations
# These help label detected waves
TRIGGER_DATES = {
    # National elections
    date(1990, 5, 20): ("election", "1990 General Election"),
    date(1992, 9, 27): ("election", "1992 General Election"),
    date(1996, 11, 3): ("election", "1996 General Election"),
    date(2000, 11, 26): ("election", "2000 General Election"),
    date(2004, 11, 28): ("election", "2004 General Election"),
    date(2008, 11, 30): ("election", "2008 General Election"),
    date(2012, 12, 9): ("election", "2012 General Election"),
    date(2016, 12, 11): ("election", "2016 General Election"),
    date(2020, 12, 6): ("election", "2020 General Election"),
    date(2024, 12, 1): ("election", "2024 General Election"),
    # Government formations (approximate dates when new PM took office)
    date(1990, 6, 28): ("government_formation", "Petre Roman Government"),
    date(1991, 10, 16): ("government_formation", "Theodor Stolojan Government"),
    date(1992, 11, 19): ("government_formation", "Nicolae Văcăroiu Government"),
    date(1996, 12, 12): ("government_formation", "Victor Ciorbea Government"),
    date(1998, 4, 14): ("government_formation", "Radu Vasile Government"),
    date(1999, 12, 22): ("government_formation", "Mugur Isărescu Government"),
    date(2000, 12, 28): ("government_formation", "Adrian Năstase Government"),
    date(2004, 12, 29): ("government_formation", "Călin Popescu-Tăriceanu Government I"),
    date(2007, 4, 5): ("government_formation", "Călin Popescu-Tăriceanu Government II"),
    date(2008, 12, 22): ("government_formation", "Emil Boc Government I"),
    date(2009, 10, 23): ("government_formation", "Emil Boc Government II"),
    date(2012, 5, 7): ("government_formation", "Victor Ponta Government I"),
    date(2012, 12, 21): ("government_formation", "Victor Ponta Government II"),
    date(2015, 11, 17): ("government_formation", "Dacian Cioloș Government"),
    date(2017, 1, 4): ("government_formation", "Sorin Grindeanu Government"),
    date(2017, 6, 29): ("government_formation", "Mihai Tudose Government"),
    date(2018, 1, 29): ("government_formation", "Viorica Dăncilă Government"),
    date(2019, 11, 4): ("government_formation", "Ludovic Orban Government I"),
    date(2020, 3, 14): ("government_formation", "Ludovic Orban Government II"),
    date(2020, 12, 23): ("government_formation", "Florin Cîțu Government"),
    date(2021, 11, 25): ("government_formation", "Nicolae Ciucă Government"),
    date(2023, 6, 15): ("government_formation", "Marcel Ciolacu Government"),
    # Party congresses (major ones known to cause switches)
    date(2001, 6, 15): ("party_congress", "PSD Congress 2001"),
    date(2005, 6, 20): ("party_congress", "PSD Congress 2005"),
    date(2010, 2, 20): ("party_congress", "PSD Congress 2010"),
    date(2015, 10, 10): ("party_congress", "PSD Congress 2015"),
    date(2019, 11, 15): ("party_congress", "PSD Congress 2019"),
    date(2022, 11, 5): ("party_congress", "PSD Congress 2022"),
    # Coalition breakups
    date(2007, 4, 1): ("coalition_breakup", "DA-PUR Coalition Breakup"),
    date(2014, 2, 1): ("coalition_breakup", "USL Coalition Breakup"),
    date(2019, 8, 26): ("coalition_breakup", "PSD-ALDE Coalition Breakup"),
    date(2021, 9, 7): ("coalition_breakup", "CNR Coalition Breakup"),
}


def _find_trigger(wave_start: date, wave_end: date) -> tuple[str | None, str | None]:
    """Find the closest known trigger event within or near the wave window."""
    best_trigger: tuple[str | None, str | None] = (None, None)
    best_distance = float("inf")
    for t_date, (t_type, t_desc) in TRIGGER_DATES.items():
        # Check if trigger is within wave window or within 90 days before start
        if wave_start - timedelta(days=90) <= t_date <= wave_end:
            distance = (wave_start - t_date).days
            if abs(distance) < best_distance:
                best_distance = abs(distance)
                best_trigger = (t_type, t_desc)
    return best_trigger


def _get_wave_signature(
    wave_start: date, wave_end: date, chamber: str, legislature: str | None
) -> str:
    """Generate a unique signature for deduplication."""
    leg = legislature or "any"
    return f"{wave_start.isoformat()}:{wave_end.isoformat()}:{chamber}:{leg}"


def derive_switch_waves(
    session: Session,
    chamber: str | None = None,
    legislature: str | None = None,
    window_days: int = 30,
    min_switches: int = 3,
) -> int:
    """
    Detect switch waves by clustering switch_party events in sliding windows.

    Args:
        session: Database session
        chamber: Filter by chamber (deputies/senate) or None for both
        legislature: Filter by legislature label or None for all
        window_days: Sliding window size in days (default 30)
        min_switches: Minimum switches to form a wave (default 3)

    Returns:
        Number of newly created SwitchWave records
    """
    # Get all switch_party events, optionally filtered
    stmt = select(Event).where(Event.type == "switch_party")
    if chamber:
        stmt = stmt.where(Event.chamber == chamber)
    stmt = stmt.where(Event.event_date.is_not(None)).order_by(Event.event_date)

    events = list(session.scalars(stmt))

    if legislature:
        # Filter events by legislature
        leg_key_events = session.scalars(
            select(KeyEvent).where(KeyEvent.type == "legislature", KeyEvent.label == legislature)
        ).first()
        if leg_key_events:
            leg_start = leg_key_events.start_date
            leg_end = leg_key_events.end_date or date.today()
            events = [e for e in events if e.event_date and leg_start <= e.event_date <= leg_end]

    if not events:
        return 0

    # Group events by chamber if not filtered
    by_chamber: dict[str, list[Event]] = {}
    for e in events:
        ch = e.chamber or "unknown"
        by_chamber.setdefault(ch, []).append(e)

    created = 0
    seen_signatures: set[str] = set()

    # Pre-load existing wave signatures to avoid duplicates
    existing_waves = session.scalars(select(SwitchWave)).all()
    for w in existing_waves:
        sig = _get_wave_signature(w.start_date, w.end_date, w.chamber, w.legislature)
        seen_signatures.add(sig)

    for ch, evs in by_chamber.items():
        evs.sort(key=lambda e: e.event_date)

        # Sliding window detection
        i = 0
        while i < len(evs):
            window_start = evs[i].event_date
            window_end = window_start + timedelta(days=window_days)

            # Find all events in this window
            window_events = [
                e for e in evs if e.event_date and window_start <= e.event_date <= window_end
            ]

            if len(window_events) >= min_switches:
                # Determine legislature label
                leg_label = None
                if legislature:
                    leg_label = legislature
                else:
                    # Try to find legislature from key events
                    for ke in session.scalars(
                        select(KeyEvent).where(KeyEvent.type == "legislature")
                    ):
                        if ke.start_date and ke.end_date:
                            if (
                                ke.start_date
                                <= window_events[-1].event_date
                                <= (ke.end_date or date.today())
                            ):
                                leg_label = ke.label
                                break

                # Check for existing wave using signature
                sig = _get_wave_signature(window_start, window_end, ch, leg_label)
                if sig in seen_signatures:
                    i += len(window_events)
                    continue

                # Find trigger
                trigger_type, trigger_desc = _find_trigger(window_start, window_end)

                wave = SwitchWave(
                    label=f"Wave {window_start.isoformat()} to {window_end.isoformat()}",
                    start_date=window_start,
                    end_date=window_end,
                    switch_count=len(window_events),
                    trigger_type=trigger_type,
                    trigger_event=trigger_desc,
                    legislature=leg_label,
                    chamber=ch,
                )
                session.add(wave)
                created += 1
                seen_signatures.add(sig)

                # Skip ahead to avoid overlapping detection of same cluster
                i += len(window_events)
            else:
                i += 1

    session.flush()
    return created


def derive_all_switch_waves(session: Session) -> int:
    """Derive switch waves for all chambers and legislatures."""
    total = 0
    # For each legislature
    for ke in session.scalars(select(KeyEvent).where(KeyEvent.type == "legislature")):
        if ke.start_date:
            leg_label = ke.label
            # For each chamber
            for ch in ("deputies", "senate"):
                total += derive_switch_waves(
                    session, chamber=ch, legislature=leg_label, window_days=30, min_switches=3
                )
    return total


def _legislature_period(session: Session, legislature: str) -> tuple[date, date]:
    keys = session.scalars(
        select(KeyEvent).where(
            KeyEvent.type == "legislature",
            KeyEvent.label == legislature,
        )
    ).all()
    starts = [key.start_date for key in keys if key.start_date]
    if not starts:
        raise ValueError(f"legislature not found: {legislature}")
    return min(starts), max(key.end_date or date.today() for key in keys)


def party_switching_rates(
    session: Session,
    legislature: str | None = None,
) -> list[dict]:
    """Calculate dated party-switch rates over observed group-membership years."""
    from collections import defaultdict

    period_start, period_end = (
        _legislature_period(session, legislature)
        if legislature
        else (date.min, date.today())
    )
    event_stmt = select(Event).where(
        Event.type == "switch_party",
        Event.event_date.is_not(None),
        Event.event_date >= period_start,
        Event.event_date <= period_end,
    )
    switches = session.scalars(event_stmt).all()
    party_switches: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for switch in switches:
        if not switch.event_date:
            continue

        affected_parties: set[str] = set()
        for org_id in (switch.from_org_id, switch.to_org_id):
            if not org_id:
                continue
            org = session.get(Organization, org_id)
            if not org:
                continue
            party_id = org.id if org.classification == "party" else None
            if org.classification == "group":
                membership_stmt = select(Membership.on_behalf_of_id).where(
                    Membership.person_id == switch.person_id,
                    Membership.org_id == org.id,
                    Membership.on_behalf_of_id.is_not(None),
                    Membership.start_date <= switch.event_date,
                    or_(Membership.end_date.is_(None), Membership.end_date >= switch.event_date),
                )
                if legislature:
                    membership_stmt = membership_stmt.where(
                        Membership.legislature == legislature
                    )
                party_id = session.scalar(
                    membership_stmt.order_by(Membership.start_date.desc()).limit(1)
                )
            if party_id:
                affected_parties.add(party_id)

        for party_id in affected_parties:
            party_switches[party_id][switch.person_id] += 1

    group = aliased(Organization)
    party_org = aliased(Organization)
    results = []
    for party_id, person_switches in party_switches.items():
        party = session.get(Organization, party_id)
        if not party or party.classification != "party":
            continue
        membership_filters = [
            Membership.on_behalf_of_id == party_id,
            group.classification == "group",
            party_org.classification == "party",
            Membership.start_date <= period_end,
            or_(Membership.end_date.is_(None), Membership.end_date >= period_start),
        ]
        if legislature:
            membership_filters.append(Membership.legislature == legislature)
        memberships = session.execute(
            select(Membership.person_id, Membership.start_date, Membership.end_date)
            .join(group, group.id == Membership.org_id)
            .join(party_org, party_org.id == Membership.on_behalf_of_id)
            .where(*membership_filters)
        ).all()

        member_ids: set[str] = set()
        tenure_days: dict[str, int] = defaultdict(int)
        for person_id, start, end in memberships:
            member_ids.add(person_id)
            if not start:
                continue
            clipped_start = max(start, period_start)
            clipped_end = min(end or period_end, period_end)
            if clipped_end >= clipped_start:
                tenure_days[person_id] += (clipped_end - clipped_start).days

        total_person_years = sum(tenure_days.values()) / 365.25
        if not member_ids or total_person_years <= 0:
            continue
        total_switches = sum(person_switches.values())
        results.append(
            {
                "party_id": party.id,
                "party_name": party.short_name or party.name,
                "members": len(member_ids),
                "switches": total_switches,
                "switchers": len(person_switches),
                "avg_tenure_years": round(
                    sum(tenure_days.values()) / len(tenure_days) / 365.25, 1
                ),
                "switch_rate_per_mp_per_year": round(
                    total_switches / total_person_years, 4
                ),
            }
        )
    return sorted(results, key=lambda result: result["party_name"])


def generational_shift(
    session: Session,
    legislature: str | None = None,
    as_of: date | None = None,
) -> tuple[date, list[dict]]:
    """Calculate age summaries by party from dated group memberships."""
    from statistics import median

    evaluation_date = as_of or date.today()
    if legislature and not as_of:
        _, evaluation_date = _legislature_period(session, legislature)

    group = aliased(Organization)
    party = aliased(Organization)
    stmt = (
        select(
            Person.id,
            Person.birth_date,
            party.id,
            party.short_name,
            party.name,
        )
        .join(Membership, Membership.person_id == Person.id)
        .join(group, group.id == Membership.org_id)
        .join(party, party.id == Membership.on_behalf_of_id)
        .where(
            Person.birth_date.is_not(None),
            group.classification == "group",
            party.classification == "party",
            Membership.start_date <= evaluation_date,
        )
    )
    if legislature:
        stmt = stmt.where(Membership.legislature == legislature)
    else:
        stmt = stmt.where(
            or_(Membership.end_date.is_(None), Membership.end_date >= evaluation_date)
        )

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

    results = [
        {
            "party": party_names[party_id],
            "mps_with_birth_dates": len(ages),
            "avg_age": round(sum(ages.values()) / len(ages), 1),
            "median_age": median(ages.values()),
        }
        for party_id, ages in ages_by_party.items()
        if ages
    ]
    results.sort(key=lambda result: result["party"])
    return evaluation_date, results


def derive_party_cohesion(
    session: Session,
    legislature: str | None = None,
) -> int:
    """Report party switching rates and return the number of parties measured."""
    results = party_switching_rates(session, legislature)
    for result in results:
        print(
            f"Party {result['party_name']}: {result['members']} members, "
            f"{result['switches']} switches, avg_tenure={result['avg_tenure_years']:.1f}y, "
            f"switch_rate={result['switch_rate_per_mp_per_year']:.4f}/MP/year"
        )
    if not results:
        print("No dated, attributable party-switch data is available.")
    return len(results)


def derive_committee_control(
    session: Session,
    legislature: str | None = None,
) -> None:
    """Return no result until source-backed committee chair data is available."""
    if legislature and not session.scalar(
        select(KeyEvent.id)
        .where(
            KeyEvent.type == "legislature",
            KeyEvent.label == legislature,
        )
        .limit(1)
    ):
        raise ValueError(f"legislature not found: {legislature}")
    # Committee chair data is not present in the current corpus.
    return None


def derive_cross_chamber_careers(session: Session, as_of: date | None = None) -> int:
    """
    Identify persons with mandates in both chambers by the requested date.
    """
    as_of = as_of or date.today()
    persons = session.execute(
        select(Person.canonical_name)
        .join(Mandate, Mandate.person_id == Person.id)
        .where(
            Mandate.chamber.in_(("deputies", "senate")),
            Mandate.start_date.is_not(None),
            Mandate.start_date <= as_of,
        )
        .group_by(Person.id, Person.canonical_name)
        .having(func.count(func.distinct(Mandate.chamber)) == 2)
        .order_by(Person.canonical_name)
    ).all()
    for (name,) in persons:
        print(f"Cross-chamber MP: {name}")
    return len(persons)


def derive_generational_shift(
    session: Session,
    legislature: str | None = None,
) -> int:
    """Report party age summaries and return the number of parties measured."""
    evaluation_date, results = generational_shift(session, legislature)
    for result in results:
        print(
            f"Party {result['party']}: {result['mps_with_birth_dates']} MPs with birth dates, "
            f"avg={result['avg_age']:.1f}, median={result['median_age']} "
            f"(as of {evaluation_date.isoformat()})"
        )
    if not results:
        print("No party memberships with birth-date data are available.")
    return len(results)


def main(argv: list[str] | None = None) -> int:
    """Run one analytics derivation (or all of them) against a SQLite DB.

    Usage: ``python -m pipeline.analytics [--db PATH] [waves|cohesion|cross-chamber|generations|all]``
    """
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pipeline.analytics")
    parser.add_argument("--db", default=None, help="SQLite DB path (default data/parlament.db)")
    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        choices=["all", "waves", "cohesion", "cross-chamber", "generations"],
    )
    args = parser.parse_args(argv)

    engine = make_engine(args.db)
    init_db(engine)
    session = make_session_factory(engine)()
    try:
        if args.command in ("all", "waves"):
            print(f"Created {derive_all_switch_waves(session)} switch waves")
        if args.command in ("all", "cohesion"):
            derive_party_cohesion(session)
        if args.command in ("all", "cross-chamber"):
            derive_cross_chamber_careers(session)
        if args.command in ("all", "generations"):
            derive_generational_shift(session)
        session.commit()
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
