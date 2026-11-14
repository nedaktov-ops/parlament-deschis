from sqlalchemy import select
from sqlalchemy.orm import Session

from pipeline.db import (
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
