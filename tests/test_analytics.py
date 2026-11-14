from datetime import date

from pipeline.analytics import derive_all_switch_waves
from pipeline.db import (
    Event,
    KeyEvent,
    Person,
    SwitchWave,
    init_db,
    make_engine,
    make_session_factory,
)


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
