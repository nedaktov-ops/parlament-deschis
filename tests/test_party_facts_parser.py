"""Parser tests for Party Facts external-parties.csv (Dataverse DOI:10.7910/DVN/TJINLQ, CC0 1.0).

Tests run offline against a captured fixture. The fixture is a truncated
version of the real Dataverse file containing only ROU rows plus a few
non-ROU rows to verify filtering.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.parse.party_facts import (
    filter_rou,
    is_populist_dataset,
    parse_external_parties,
    partyfacts_ids_for_country,
)

FX = Path(__file__).parent / "fixtures" / "party_facts"


@pytest.fixture
def rou_csv():
    """A small CSV with ROU rows plus non-ROU rows for filtering tests."""
    return (
        "country,dataset_key,dataset_party_id,name_short,name,name_english,year_first,year_last,share,share_year,description,comment,created,modified,external_id,partyfacts_id,linked\n"
        'ROU,manifesto,93524,FSR,Frontul Salvării României,,1990,1996,,,,,"2013-01-01 18:18:05.413000+00:00","2023-06-05 10:39:57.075788+00:00",,958,\n'
        'ROU,parlgov,642000039,FDSN,Frontul Democrat Salvării Național,,1990,2006,,,,,"2013-01-01 18:18:05.413000+00:00","2023-06-05 10:39:57.075788+00:00",,276,\n'
        'ROU,populist,rou-ppd,PPDD,Partidul Poporului Dan Diaconescu,,1989,2019,,,,,"2013-01-01 18:18:05.413000+00:00","2023-06-05 10:39:57.075788+00:00",,2474,\n'
        'DEU,manifesto,12345,CDU,Christlich Demokratische Union Deutschlands,,1945,,,,,"2013-01-01 18:18:05.413000+00:00","2023-06-05 10:39:57.075788+00:00",,100,\n'
    )


def test_parse_external_parties_header_validation(rou_csv):
    """Parser validates required columns and rejects missing ones."""
    rows = parse_external_parties(rou_csv)
    # 3 ROU + 1 DEU = 4 rows
    assert len(rows) == 4


def test_parse_external_parties_rou_rows(rou_csv):
    """Parser correctly extracts all fields from ROU rows."""
    rows = parse_external_parties(rou_csv)
    rou = filter_rou(rows)
    assert len(rou) == 3

    fsr = [r for r in rou if r.partyfacts_id == "958"][0]
    assert fsr.country == "ROU"
    assert fsr.dataset_key == "manifesto"
    assert fsr.dataset_party_id == "93524"
    assert fsr.name_short == "FSR"
    assert fsr.name == "Frontul Salvării României"
    assert fsr.year_first == 1990
    assert fsr.year_last == 1996


def test_filter_rou_excludes_non_rou(rou_csv):
    """filter_rou keeps only ISO-3 ROU rows."""
    rows = parse_external_parties(rou_csv)
    rou = filter_rou(rows)
    assert all(r.country == "ROU" for r in rou)
    assert len(rou) == 3


def test_partyfacts_ids_for_country(rou_csv):
    """partyfacts_ids_for_country returns unique IDs per country."""
    rows = parse_external_parties(rou_csv)
    ids = partyfacts_ids_for_country(rows, "ROU")
    assert len(ids) == 3
    assert "958" in ids
    assert "276" in ids
    assert "2474" in ids


def test_is_populist_dataset():
    """is_populist_dataset distinguishes PopuList from Poll of Polls."""
    assert is_populist_dataset("populist") is True
    assert is_populist_dataset("pop") is False  # Poll of Polls, NOT PopuList
    assert is_populist_dataset("manifesto") is False
    assert is_populist_dataset(None) is False


def test_parse_external_parties_missing_columns():
    """Parser raises ValueError when required columns are missing."""
    bad_csv = "country,dataset_key,dataset_party_id,name_short,name\nROU,manifesto,123,FSR,Frontul Salvării României\n"
    with pytest.raises(ValueError):
        parse_external_parties(bad_csv)


def test_parse_external_parties_empty():
    """Parser handles empty CSV (header only)."""
    empty_csv = "country,dataset_key,dataset_party_id,name_short,name,name_english,year_first,year_last,share,share_year,description,comment,created,modified,external_id,partyfacts_id,linked\n"
    rows = parse_external_parties(empty_csv)
    assert rows == []
