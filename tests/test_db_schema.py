from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pipeline.db import (
    SCHEMA_VERSION,
    Base,
    Event,
    Membership,
    Organization,
    Person,
    Post,
    ensure_schema,
    make_engine,
)


def test_legacy_cross_chamber_group_duplicates_are_merged(tmp_path):
    engine = make_engine(tmp_path / "legacy.db")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        group_data = {
            "classification": "group",
            "name": "Partidul de test",
            "normalized_name": "partidul de test",
            "short_name": "TEST",
        }
        deputies = Organization(id="deputies-group", chamber="deputies", **group_data)
        senate = Organization(id="senate-group", chamber="senate", **group_data)
        person = Person(canonical_name="Test Person", normalized_name="test person")
        session.add_all((deputies, senate, person))
        session.flush()

        post = Post(org_id=senate.id, label="Member")
        session.add_all(
            (
                post,
                Membership(
                    person_id=person.id,
                    org_id=deputies.id,
                    chamber="deputies",
                    legislature="2020",
                ),
                Membership(
                    person_id=person.id,
                    org_id=senate.id,
                    chamber="senate",
                    legislature="2020",
                ),
                Event(type="join", from_org_id=senate.id),
            )
        )
        session.commit()

    ensure_schema(engine)

    with Session(engine) as session:
        groups = list(
            session.scalars(
                select(Organization).where(Organization.normalized_name == "partidul de test")
            )
        )
        assert len(groups) == 1
        assert groups[0].chamber is None
        assert {membership.org_id for membership in session.scalars(select(Membership))} == {
            groups[0].id
        }
        assert session.scalar(select(Post.org_id)) == groups[0].id
        assert session.scalar(select(Event.from_org_id)) == groups[0].id


def _seed_legacy_group(tmp_path, name):
    """A DB with the pre-migration cross-chamber duplicate group fixture."""
    engine = make_engine(tmp_path / f"{name}.db")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        group_data = {
            "classification": "group",
            "name": "Partidul de test",
            "normalized_name": "partidul de test",
            "short_name": "TEST",
        }
        deputies = Organization(id="deputies-group", chamber="deputies", **group_data)
        senate = Organization(id="senate-group", chamber="senate", **group_data)
        person = Person(canonical_name="Test Person", normalized_name="test person")
        session.add_all((deputies, senate, person))
        session.flush()
        session.add_all(
            (
                Post(org_id=senate.id, label="Member"),
                Membership(
                    person_id=person.id,
                    org_id=deputies.id,
                    chamber="deputies",
                    legislature="2020",
                ),
                Membership(
                    person_id=person.id,
                    org_id=senate.id,
                    chamber="senate",
                    legislature="2020",
                ),
                Event(type="join", from_org_id=senate.id),
            )
        )
        session.commit()
    return engine


def test_legacy_merge_sets_user_version_and_is_idempotent(tmp_path):
    engine = _seed_legacy_group(tmp_path, "migrate")
    ensure_schema(engine)
    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA user_version").scalar() == SCHEMA_VERSION
    # A second call must be a harmless no-op, not a second merge.
    ensure_schema(engine)
    with engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA user_version").scalar() == SCHEMA_VERSION


def test_legacy_merge_gated_by_user_version(tmp_path):
    engine = _seed_legacy_group(tmp_path, "gated")
    # A shipped/read-only DB is already stamped: the destructive merge must
    # not run even though the legacy duplicate rows are still present.
    with engine.begin() as conn:
        conn.exec_driver_sql(f"PRAGMA user_version = {SCHEMA_VERSION}")
    ensure_schema(engine)

    with Session(engine) as session:
        groups = list(
            session.scalars(
                select(Organization).where(Organization.normalized_name == "partidul de test")
            )
        )
        assert len(groups) == 2  # nothing merged
        with engine.connect() as conn:
            assert conn.exec_driver_sql("PRAGMA user_version").scalar() == SCHEMA_VERSION


def test_support_indexes_exist_on_fresh_database(tmp_path):
    engine = make_engine(tmp_path / "idx.db")
    Base.metadata.create_all(engine)
    ensure_schema(engine)
    with engine.connect() as conn:
        names = {
            row[0]
            for row in conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='index'")
        }
    for expected in (
        "ux_membership_closed_stint",
        "ix_membership_on_behalf_of",
        "ix_event_from_org_id",
        "ix_event_to_org_id",
    ):
        assert expected in names


def test_closed_stint_partial_unique_index(tmp_path):
    engine = make_engine(tmp_path / "closed.db")
    Base.metadata.create_all(engine)
    ensure_schema(engine)

    with Session(engine) as session:
        session.add_all(
            (
                Organization(id="g", classification="group", name="G", normalized_name="g"),
                Person(id="p", canonical_name="P", normalized_name="p"),
            )
        )
        session.flush()

        def closed(end_date, legislature="2020"):
            return Membership(
                person_id="p",
                org_id="g",
                chamber="deputies",
                legislature=legislature,
                end_date=end_date,
            )

        session.add(closed(date(2020, 6, 1)))
        session.commit()

        # An exact duplicate of a closed stint is now rejected.
        session.add(closed(date(2020, 6, 1)))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        # The index is partial: an open stint with the same scope is allowed.
        session.add(
            Membership(
                person_id="p", org_id="g", chamber="deputies", legislature="2020", end_date=None
            )
        )
        session.commit()

        # So is a closed stint with the same key in a different legislature.
        session.add(closed(date(2020, 6, 1), legislature="2016"))
        session.commit()


def test_ensure_schema_tolerates_legacy_duplicate_closed_stints(tmp_path):
    engine = make_engine(tmp_path / "residual.db")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            (
                Organization(id="g", classification="group", name="G", normalized_name="g"),
                Person(id="p", canonical_name="P", normalized_name="p"),
            )
        )
        session.flush()
        common = dict(
            person_id="p",
            org_id="g",
            chamber="deputies",
            legislature="2020",
            end_date=date(2020, 6, 1),
        )
        session.add_all((Membership(**common), Membership(**common)))
        session.commit()

    # The partial unique index cannot be created on these legacy duplicates;
    # ensure_schema must report it and continue without deleting either row.
    ensure_schema(engine)
    with Session(engine) as session:
        assert len(list(session.scalars(select(Membership)))) == 2
