from datetime import date

import pytest

from pipeline.db import Person, PersonIdentifier, PersonName, get_session
from pipeline.identity import PersonResolver, merge_persons, revert_merge, score_match
from pipeline.normalize import name_sort_key, normalize_name


@pytest.fixture
def session():
    s = get_session(":memory:")
    yield s
    s.close()


def test_normalize_diacritics():
    assert normalize_name("Chiriţă Răzvan-Mirel") == "chirita razvan mirel"
    assert normalize_name("Șerban Ciprian-Constantin") == "serban ciprian constantin"
    assert normalize_name("Ţintă Ştefan") == "tinta stefan"


def test_name_order_insensitive_key():
    assert name_sort_key("Popescu Ion") == name_sort_key("Ion Popescu")


def test_resolve_creates_then_finds_by_identifier(session):
    r = PersonResolver(session)
    p1, created = r.resolve(scheme="cdep_idm", identifier="55", name="Chiriţă Răzvan-Mirel",
                            legislature="2024")
    assert created
    p2, created2 = r.resolve(scheme="cdep_idm", identifier="55", name="Chiriţă Răzvan-Mirel",
                             legislature="2024")
    assert not created2
    assert p1.id == p2.id


def test_resolve_per_term_ids_distinct(session):
    r = PersonResolver(session)
    # Same idm number in different legislatures, different people → distinct.
    p1, _ = r.resolve(scheme="cdep_idm", identifier="55", name="Person Alpha", legislature="2020")
    p2, _ = r.resolve(scheme="cdep_idm", identifier="55", name="Person Beta", legislature="2024")
    assert p1.id != p2.id
    # The identifier rows are scoped per legislature.
    idents = session.query(PersonIdentifier).filter_by(scheme="cdep_idm", identifier="55").all()
    assert {i.legislature for i in idents} == {"2020", "2024"}


def test_resolve_unique_name_fallback(session):
    r = PersonResolver(session)
    p1, _ = r.resolve(scheme="cdep_idm", identifier="1", name="Unique Person", legislature="2024")
    # A different source id but a unique matching name → same person.
    p2, created = r.resolve(scheme="senat_guid", identifier="GUID-X", name="Unique Person",
                            legislature="2024")
    assert not created
    assert p1.id == p2.id


def test_resolve_ambiguous_name_creates_new(session):
    r = PersonResolver(session)
    r.resolve(scheme="cdep_idm", identifier="1", name="Ion Popescu", legislature="2024")
    r.resolve(scheme="cdep_idm", identifier="2", name="Ion Popescu", legislature="2024")
    # Ambiguous name → never guess; a new id is created.
    p3, created = r.resolve(scheme="senat_guid", identifier="G", name="Ion Popescu",
                            legislature="2024")
    assert created


def test_merge_and_revert(session):
    r = PersonResolver(session)
    a, _ = r.resolve(scheme="cdep_idm", identifier="1", name="Ion Popescu", legislature="2024")
    b, _ = r.resolve(scheme="wikidata", identifier="Q123", name="Ionel Popescu", legislature="2024")
    b.birth_date = date(1970, 1, 1)
    session.flush()
    audit = merge_persons(session, a.id, b.id)
    session.flush()
    # b's identifier now points to a; b's name is an alias of a.
    ident = session.query(PersonIdentifier).filter_by(scheme="wikidata", identifier="Q123").one()
    assert ident.person_id == a.id
    assert a.birth_date == date(1970, 1, 1)
    aliases = session.query(PersonName).filter_by(person_id=a.id, type="alias").all()
    assert any(pn.name == "Ionel Popescu" for pn in aliases)
    # Revert.
    revert_merge(session, audit.id)
    session.flush()
    ident = session.query(PersonIdentifier).filter_by(scheme="wikidata", identifier="Q123").one()
    assert ident.person_id == b.id
    assert audit.reverted


def test_score_match_qid():
    a = Person(canonical_name="Ion Popescu", normalized_name="ion popescu", wikidata_qid="Q1")
    b = Person(canonical_name="Ion Popescu", normalized_name="ion popescu", wikidata_qid="Q1")
    assert score_match(a, b) == 100.0
    b.wikidata_qid = "Q2"
    assert score_match(a, b) == 0.0