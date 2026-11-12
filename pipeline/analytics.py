"""Analytical layer: switch wave detection, party cohesion, committee control, etc."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Literal

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .db import (
    Base,
    Event,
    KeyEvent,
    Membership,
    Organization,
    Person,
    SwitchWave,
    make_engine,
    make_session_factory,
    WAVE_TRIGGERS,
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


def _get_wave_signature(wave_start: date, wave_end: date, chamber: str, legislature: str | None) -> str:
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
            events = [
                e for e in events
                if e.event_date and leg_start <= e.event_date <= leg_end
            ]
    
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
            window_events = [e for e in evs if e.event_date and window_start <= e.event_date <= window_end]
            
            if len(window_events) >= min_switches:
                # Determine legislature label
                leg_label = None
                if legislature:
                    leg_label = legislature
                else:
                    # Try to find legislature from key events
                    for ke in session.scalars(select(KeyEvent).where(KeyEvent.type == "legislature")):
                        if ke.start_date and ke.end_date:
                            if ke.start_date <= window_events[-1].event_date <= (ke.end_date or date.today()):
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
        if ke.start_date and ke.end_date:
            leg_label = ke.label
            # For each chamber
            for ch in ("deputies", "senate"):
                total += derive_switch_waves(
                    session, 
                    chamber=ch, 
                    legislature=leg_label,
                    window_days=30,
                    min_switches=3
                )
    return total


def derive_party_cohesion(
    session: Session,
    legislature: str | None = None,
) -> int:
    """
    Calculate party cohesion index per party per legislature.
    
    Cohesion = 1 - (std_dev(switch_rate_per_mp) / mean(switch_rate_per_mp))
    where switch_rate_per_mp = number of party switches / tenure_duration_years
    
    Returns:
        Number of newly created cohesion records
    """
    from sqlalchemy import func
    
    # Get all party switches - these are already derived from party memberships
    # so the to_org_id should be a party
    stmt = select(Event).where(Event.type == "switch_party")
    if legislature:
        leg_key = session.scalars(
            select(KeyEvent).where(KeyEvent.type == "legislature", KeyEvent.label == legislature)
        ).first()
        if leg_key and leg_key.start_date and leg_key.end_date:
            stmt = stmt.where(
                Event.event_date >= leg_key.start_date,
                Event.event_date <= leg_key.end_date
            )
    stmt = stmt.where(Event.event_date.is_not(None))
    
    switches = list(session.scalars(stmt))
    
    # Group by party (to_org) and count switches per person
    # The to_org_id should be a party since these are switch_party events
    from collections import defaultdict
    party_switches: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    
    for sw in switches:
        if sw.to_org_id:
            # Verify this is a party
            org = session.get(Organization, sw.to_org_id)
            if org and org.classification == "party":
                party_switches[sw.to_org_id][sw.person_id] += 1
            else:
                # If it's not a party, try to find the party through the group's on_behalf_of_id
                if org and org.classification == "group" and org.on_behalf_of_id:
                    party_switches[org.on_behalf_of_id][sw.person_id] += 1
    
    # Get party memberships to calculate tenure
    created = 0
    for party_id, person_switches in party_switches.items():
        party = session.get(Organization, party_id)
        if not party or party.classification != "party":
            continue
        
        # Get all party memberships for this party
        party_memberships = session.scalars(
            select(Membership)
            .join(Organization, Organization.id == Membership.org_id)
            .where(Organization.id == party_id)
        ).all()
        
        # Calculate average tenure and switch rate
        total_switches = sum(person_switches.values())
        num_switchers = len(person_switches)
        num_members = len(set(m.person_id for m in party_memberships))
        
        if num_members == 0:
            continue
        
        # Calculate tenure durations in years
        total_tenure_years = 0
        for m in party_memberships:
            if m.start_date and m.end_date:
                total_tenure_years += (m.end_date - m.start_date).days / 365.25
            elif m.start_date:
                total_tenure_years += (date.today() - m.start_date).days / 365.25
        
        avg_tenure = total_tenure_years / num_members if num_members > 0 else 0
        
        if avg_tenure == 0:
            continue
        
        # Switch rate per MP = total switches / (num_members * avg_tenure)
        switch_rate = total_switches / (num_members * avg_tenure) if num_members * avg_tenure > 0 else 0
        
        # Calculate cohesion for this party
        # For now, just log it - in a full implementation we'd store in a table
        party_label = party.short_name or party.name or "Unknown"
        print(f"Party {party_label}: {num_members} members, {total_switches} switches, "
              f"avg_tenure={avg_tenure:.1f}y, switch_rate={switch_rate:.3f}/MP/year")
    
    return 0  # Placeholder


def derive_committee_control(
    session: Session,
    legislature: str | None = None,
) -> int:
    """
    Calculate committee control index per party per legislature.
    
    Index = party_chairs / total_committees per legislature per party
    """
    # TODO: Implement when committee chair data is available
    return 0


def derive_cross_chamber_careers(session: Session) -> int:
    """
    Identify persons with memberships in both chambers.
    """
    # Find persons who have memberships in both deputies and senate
    stmt = select(Person.id, Person.canonical_name).distinct()
    persons = list(session.execute(stmt).all())
    
    cross_chamber = 0
    for pid, name in persons:
        chs = session.scalars(
            select(Membership.chamber)
            .where(Membership.person_id == pid)
            .distinct()
        ).all()
        if len(chs) > 1:
            cross_chamber += 1
            print(f"Cross-chamber MP: {name} (chambers: {', '.join(chs)})")
    
    return cross_chamber


def derive_generational_shift(
    session: Session,
    legislature: str | None = None,
) -> int:
    """
    Calculate avg/median age per party per legislature from Wikidata birth dates.
    """
    # Get all persons with birth dates
    stmt = select(Person.id, Person.canonical_name, Person.birth_date)
    if legislature:
        # Filter by legislature memberships
        leg_key = session.scalars(
            select(KeyEvent).where(KeyEvent.type == "legislature", KeyEvent.label == legislature)
        ).first()
        if leg_key and leg_key.start_date and leg_key.end_date:
            stmt = stmt.where(
                Person.id.in_(
                    select(Membership.person_id)
                    .where(Membership.start_date <= leg_key.end_date)
                    .where((Membership.end_date.is_(None)) | (Membership.end_date >= leg_key.start_date))
                )
            )
    
    persons = list(session.execute(stmt).all())
    ages_by_party: dict[str, list[int]] = {}
    
    for pid, name, bdate in persons:
        if not bdate:
            continue
        age = (date.today() - bdate).days / 365.25
        
        # Get party memberships for this person
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
    
    for party, ages in ages_by_party.items():
        if ages:
            avg_age = sum(ages) / len(ages)
            sorted_ages = sorted(ages)
            median_age = sorted_ages[len(sorted_ages) // 2]
            print(f"Party {party}: {len(ages)} MPs with birth dates, avg={avg_age:.1f}, median={median_age}")
    
    return 0


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else None
    engine = make_engine(db_path)
    init_db(engine)
    session = make_session_factory(engine)()
    
    if sys.argv[1:]:
        if sys.argv[1] == "waves":
            count = derive_all_switch_waves(session)
            print(f"Created {count} switch waves")
        elif sys.argv[1] == "cohesion":
            derive_party_cohesion(session)
        elif sys.argv[1] == "cross-chamber":
            derive_cross_chamber_careers(session)
        elif sys.argv[1] == "generations":
            derive_generational_shift(session)
    else:
        # Default: run all
        count = derive_all_switch_waves(session)
        print(f"Created {count} switch waves")
        derive_party_cohesion(session)
        derive_cross_chamber_careers(session)
        derive_generational_shift(session)
    
    session.commit()