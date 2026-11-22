from datetime import date

import pytest

from pipeline.analytics import (
    derive_all_switch_waves,
    derive_committee_control,
    derive_switch_waves,
    generational_shift,
)
from pipeline.db import (
    Event,
    KeyEvent,
    Membership,
    Organization,
    Person,
    SwitchWave,
    init_db,
    make_engine,
    make_session_factory,
)


def _session(tmp_path, name):
    engine = make_engine(tmp_path / name)
    init_db(engine)
    return engine, make_session_factory(engine)()


def test_derive_all_switch_waves_includes_open_legislature(tmp_path):
    engine = make_engine(tmp_path / "analytics.db")
    init_db(engine)
    session = make_session_factory(engine)()
    try:
        person = Person(
            canonical_name="Test Person",
            normalized_name="test person",
            sort_key="person test",
        )
        session.add(person)
        session.add(
            KeyEvent(
                type="legislature",
                chamber="deputies",
                label="2024",
                start_date=date(2024, 12, 21),
                end_date=None,
            )
        )
        session.flush()
        session.add_all(
            Event(
                type="switch_party",
                person_id=person.id,
                chamber="deputies",
                legislature="2024",
                event_date=event_date,
                dedup_key=f"test-switch-{event_date.isoformat()}",
            )
            for event_date in (
                date(2025, 1, 2),
                date(2025, 1, 5),
                date(2025, 1, 6),
            )
        )
        session.commit()

        assert derive_all_switch_waves(session) == 1
        assert derive_all_switch_waves(session) == 0
        waves = session.query(SwitchWave).all()
        assert len(waves) == 1
        assert waves[0].legislature == "2024"
        assert waves[0].chamber == "deputies"
        assert waves[0].switch_count == 3
    finally:
        session.close()
        engine.dispose()


def test_committee_control_excludes_not_yet_started_chairs(tmp_path):
    """A future-dated chair tenure is not active at an earlier as_of date."""
    engine, session = _session(tmp_path, "committee.db")
    try:
        reference = date(2000, 6, 1)

        def add_person(name):
            p = Person(
                canonical_name=name,
                normalized_name=name.lower(),
                sort_key=name.lower(),
            )
            session.add(p)
            session.flush()
            return p

        def add_committee(name):
            org = Organization(
                classification="committee",
                name=name,
                normalized_name=name.lower(),
                chamber="deputies",
            )
            session.add(org)
            session.flush()
            return org

        def add_chair(person, org, start, end, party):
            session.add(
                Membership(
                    person_id=person.id,
                    org_id=org.id,
                    chamber="deputies",
                    role="presedinte",
                    start_date=start,
                    end_date=end,
                    group_acronym_at_event=party,
                )
            )

        active = add_person("Active Chair")
        add_chair(
            active,
            add_committee("Health Committee"),
            date(1999, 1, 1),
            None,
            "PARTY-A",
        )

        # The audit found chairs starting in 2025-2026 counted as active in 2000.
        add_chair(
            add_person("Future Chair"),
            add_committee("Future Committee"),
            date(2025, 1, 1),
            None,
            "PARTY-B",
        )

        # End date is exclusive: ending on the reference day means not active.
        add_chair(
            add_person("Ended Chair"),
            add_committee("Ended Committee"),
            date(1999, 1, 1),
            reference,
            "PARTY-C",
        )
        session.commit()

        result = derive_committee_control(session, as_of=reference)

        assert result["as_of"] == reference.isoformat()
        assert result["total_committees"] == 1
        assert {chair["chair_person_id"] for chair in result["chairs"]} == {active.id}
        assert {row["party"] for row in result["parties"]} == {"PARTY-A"}
    finally:
        session.close()
        engine.dispose()


def test_generational_shift_excludes_departed_mps_in_legislature_scope(tmp_path):
    """Legislature-scoped age summaries must not include departed MPs."""
    engine, session = _session(tmp_path, "generations.db")
    try:
        evaluation_date = date(2026, 1, 1)
        session.add(
            KeyEvent(
                type="legislature",
                chamber="deputies",
                label="2024",
                start_date=date(2024, 12, 21),
                end_date=evaluation_date,
            )
        )
        party = Organization(
            classification="party",
            name="Demo Party",
            normalized_name="demo party",
            short_name="DP",
        )
        group = Organization(
            classification="group",
            name="DP Parliamentary Group",
            normalized_name="dp parliamentary group",
            short_name="DPG",
        )
        session.add_all([party, group])
        session.flush()

        def add_mp(name, birth_date, end_date):
            p = Person(
                canonical_name=name,
                normalized_name=name.lower(),
                sort_key=name.lower(),
                birth_date=birth_date,
            )
            session.add(p)
            session.flush()
            session.add(
                Membership(
                    person_id=p.id,
                    org_id=group.id,
                    on_behalf_of_id=party.id,
                    chamber="deputies",
                    legislature="2024",
                    role="deputat",
                    start_date=date(2024, 12, 21),
                    end_date=end_date,
                )
            )

        # Active MP, born 1980-05-15 -> age 45 at 2026-01-01.
        add_mp("Active MP", date(1980, 5, 15), None)
        # Departed before the evaluation date; born 1970, would skew the mean.
        add_mp("Departed MP", date(1970, 5, 15), date(2025, 6, 1))
        session.commit()

        evaluated, results, totals = generational_shift(session, legislature="2024")

        assert evaluated == evaluation_date
        assert len(results) == 1
        assert results[0]["party"] == "DP"
        assert results[0]["mps_with_birth_dates"] == 1
        assert results[0]["avg_age"] == 45
        assert totals["mps_with_birth_date"] == 1
        assert totals["mps_in_scope"] == 1
        assert totals["mps_unknown_birth_date"] == 0
        assert totals["coverage_pct"] == 100.0
    finally:
        session.close()
        engine.dispose()


def test_switch_waves_unknown_legislature_does_not_derive_all_eras(tmp_path):
    """An unknown legislature fails instead of silently using every event."""
    engine, session = _session(tmp_path, "unknown-leg.db")
    try:
        person = Person(
            canonical_name="Switcher",
            normalized_name="switcher",
            sort_key="switcher",
        )
        session.add(person)
        session.add(
            KeyEvent(
                type="legislature",
                chamber="deputies",
                label="2024",
                start_date=date(2024, 12, 21),
                end_date=None,
            )
        )
        session.flush()
        session.add_all(
            Event(
                type="switch_party",
                person_id=person.id,
                chamber="deputies",
                legislature="2024",
                event_date=event_date,
                dedup_key=f"unknown-leg-{event_date.isoformat()}",
            )
            for event_date in (
                date(2025, 1, 2),
                date(2025, 1, 5),
                date(2025, 1, 6),
            )
        )
        session.commit()

        with pytest.raises(ValueError, match="legislature not found"):
            derive_switch_waves(session, legislature="9999")

        assert session.query(SwitchWave).count() == 0
    finally:
        session.close()
        engine.dispose()


def test_switch_waves_labels_wave_for_open_legislature(tmp_path):
    """A NULL-ended (ongoing) legislature still labels unscoped waves."""
    engine, session = _session(tmp_path, "open-leg-label.db")
    try:
        person = Person(
            canonical_name="Switcher",
            normalized_name="switcher",
            sort_key="switcher",
        )
        session.add(person)
        session.add(
            KeyEvent(
                type="legislature",
                chamber="deputies",
                label="2024",
                start_date=date(2024, 12, 21),
                end_date=None,
            )
        )
        session.flush()
        session.add_all(
            Event(
                type="switch_party",
                person_id=person.id,
                chamber="deputies",
                legislature="2024",
                event_date=event_date,
                dedup_key=f"open-leg-{event_date.isoformat()}",
            )
            for event_date in (
                date(2025, 1, 2),
                date(2025, 1, 5),
                date(2025, 1, 6),
            )
        )
        session.commit()

        assert derive_switch_waves(session, legislature=None) == 1
        waves = session.query(SwitchWave).all()
        assert len(waves) == 1
        assert waves[0].legislature == "2024"
    finally:
        session.close()
        engine.dispose()
