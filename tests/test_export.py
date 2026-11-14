"""Export contract tests: Popolo JSON + CSV stay internally consistent."""

from datetime import date

import pytest

from pipeline.db import Event, Membership, Organization, Person, PersonIdentifier, get_session
from pipeline.export import CSV_DATASETS, build_popolo, csv_for, write_export


@pytest.fixture
def session(tmp_path):
    s = get_session(tmp_path / "test.db")
    person = Person(
        canonical_name="Ion Popescu",
        normalized_name="ion popescu",
        sort_key="ion popescu",
        birth_date=date(1980, 1, 2),
    )
    s.add(person)
    s.flush()
    s.add(
        PersonIdentifier(
            person_id=person.id, scheme="cdep_idm", identifier="42", legislature="2024"
        )
    )
    group = Organization(
        classification="group",
        name="Grupul PSD",
        short_name="PSD",
        normalized_name="grupul psd",
        chamber="deputies",
        color="#E63946",
    )
    party = Organization(
        classification="party",
        name="PSD",
        short_name="PSD",
        normalized_name="psd",
        chamber="deputies",
    )
    s.add_all([group, party])
    s.flush()
    s.add(
        Membership(
            person_id=person.id,
            org_id=group.id,
            on_behalf_of_id=party.id,
            chamber="deputies",
            legislature="2024",
            start_date=date(2024, 12, 21),
            confidence="official_ledger",
            source_url="https://example.test/g",
        )
    )
    s.add(
        Event(
            type="switch_group",
            person_id=person.id,
            chamber="deputies",
            from_org_id=party.id,
            to_org_id=group.id,
            event_date=date(2025, 1, 1),
            dedup_key="switch:test",
        )
    )
    s.commit()
    yield s
    s.close()


def test_popolo_shape_and_scope(session):
    doc = build_popolo(session, chamber="deputies", legislature="2024")
    assert doc["meta"]["data_license"] == "CC-BY-4.0"
    assert doc["meta"]["counts"] == {
        "persons": 1,
        "organizations": 2,
        "posts": 0,
        "memberships": 1,
        "events": 1,
    }
    assert doc["persons"][0]["identifiers"][0]["scheme"] == "cdep_idm"
    assert doc["memberships"][0]["on_behalf_of_id"] is not None
    assert doc["events"][0]["type"] == "switch_group"


def test_empty_scope_is_valid(session):
    doc = build_popolo(session, chamber="senate", legislature="1990")
    assert doc["meta"]["counts"]["memberships"] == 0
    assert doc["persons"] == []


def test_csv_datasets(session):
    for dataset in CSV_DATASETS:
        text = csv_for(session, dataset, chamber="deputies", legislature="2024")
        assert text
        assert "\n" in text
    membership_csv = csv_for(session, "memberships", chamber="deputies")
    assert "official_ledger" in membership_csv
    assert "Ion Popescu" in csv_for(session, "persons", chamber="deputies")


def test_unknown_dataset_rejected(session):
    with pytest.raises(KeyError):
        csv_for(session, "nope")


def test_write_export_files(session, tmp_path):
    result = write_export(session, tmp_path / "out", chamber="deputies")
    assert result["counts"]["persons"] == 1
    written = {p.rsplit("/", 1)[-1] for p in result["files"]}
    assert {"popolo.json", "persons.csv", "memberships.csv", "events.csv"} <= written
    assert (tmp_path / "out" / "popolo.json").exists()
