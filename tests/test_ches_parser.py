"""Parser tests for Chapel Hill Expert Survey (CHES) trend CSV (CC BY 4.0).

Tests run offline against a captured fixture. The fixture contains a few ROU
rows plus non-ROU rows to verify filtering.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.parse.ches import (
    filter_romania,
    parse_chess_csv,
)

FX = Path(__file__).parent / "fixtures" / "ches"


@pytest.fixture
def ches_csv():
    """A small CHES CSV with ROU rows plus non-ROU rows for filtering tests."""
    return (
        "year,country,eastwest,eumember,party_id,party,cmp_id,vote,seat,electionyear,epvote,family,govt,lrgen,lrecon,lrecon_salience,lrecon_dissent,lrecon_blur,galtan,galtan_salience,galtan_dissent,galtan_blur,eu_position,eu_salience,eu_dissent,eu_blur,spendvtax,spendvtax_salience,deregulation,dereg_salience,redistribution,redist_salience,econ_interven,civlib_laworder,civlib_salience,sociallifestyle,social_salience,womens_rights,lgbtq_rights,samesex_marriage,religious_principles,relig_salience,immigrate_policy,immigrate_salience,immigrate_dissent,multiculturalism,multicult_salience,multicult_dissent,nationalism,nationalism_salience,ethnic_minorities,ethnic_salience,urban_rural,urban_salience,environment,enviro_salience,climate_change,climate_change_salience,protectionism,regions,region_salience,international_security,international_salience,us,us_salience,eu_benefit,eu_ep,eu_fiscal,eu_intmark,eu_employ,eu_budgets,eu_agri,eu_cohesion,eu_environ,eu_asylum,eu_foreign,eu_turkey,eu_russia,russian_interference,anti_islam_rhetoric,people_vs_elite,antielite_salience,corrupt_salience,members_vs_leadership,executive_power,judicial_independence,mip_one,mip_two,mip_three,chesversion\n"
        "1999,12,1,1,1206,PSD,35313,32.3,35.2,1999,31.1,3,0,5.6,6,,,,6.8,,,,6.6,7.5,1.5,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,4.75,5.33,,5.666666507720947,,,,6.4,6.666666507720947,5.33,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,2025.1\n"
        "2006,12,1,1,1206,PSD,35313,28.8,32.6,2005,33.3,3,1,6.7,7,,,,7,,,,6.6,6.3333335,3,,6.199999809265137,7.400000095367432,7,6.800000190734863,5.599999904632568,5.699999809265137,,6.400000095367432,5.599999904632568,6.599999904632568,5,,,,6.21999979019165,5.5,6,6,,5.6300001,,,5,3.78,5.139999866485596,5,5.429999828338623,4.289999961853027,,,,,,5.25,5.2199998,,,6.4000001,4.8899999,,6,,6.11,,,,6.78,,,5.63,4.71,,,,,,,,,,,,,,,,,,2025.1\n"
        "2010,12,1,1,815,PDL,32061,38.2,43.8,2008,35.3,2,1,7.55555534362793,7.55555534362793,,,,8.44444465637207,,,,4.666666507720947,3.7037039,4.5,,8.55555534362793,6.333333492279053,7.44444465637207,6.333333492279053,8.333333015441895,4.333333492279053,,7.625,8.111110687255859,8,5.875,,,,7.5,6.75,8.25,7.875,,8.1428576,6.4285712,,,,8.375,5.333333492279053,3.666666746139526,2.166666746139526,8.875,2.125,,,,3.5,5.625,2.25,6.125,,,1.2222222,4.375,,5.375,,,,6.142857074737549,,,5.625,5.125,,,,,,,,,,,,,2025.1\n"
        "1999,8,1,1,807,PSDI,,,,1996,2.16,5,0,4.5,4,,,,4.599999904632568,,,,6.199999809265137,3.5000002,1.5,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,5.599999904632568,5.599999904632568,,5.25,,,6,5.199999809265137,5.199999809265137,6,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,2025.1\n"
    )


def test_parse_chess_csv_header_validation(ches_csv):
    """Parser validates required columns and rejects missing ones."""
    rows = parse_chess_csv(ches_csv)
    # 3 ROU (country 12) + 1 non-ROU (country 8) = 4 rows
    assert len(rows) == 4


def test_parse_chess_csv_rou_rows(ches_csv):
    """Parser correctly extracts all fields from ROU rows."""
    rows = parse_chess_csv(ches_csv)
    rou = filter_romania(rows)
    assert len(rou) == 3

    psd = [r for r in rou if r.party_id == 1206 and r.year == 1999][0]
    assert psd.country == 12
    assert psd.party == "PSD"
    assert psd.lrgen == 5.6
    assert psd.galtan == 6.8
    assert psd.eu_position == 6.6


def test_filter_romania_excludes_non_rou(ches_csv):
    """filter_romania keeps only country code 12 rows."""
    rows = parse_chess_csv(ches_csv)
    rou = filter_romania(rows)
    assert all(r.country == 12 for r in rou)
    assert len(rou) == 3


def test_ches_rows_by_party(ches_csv):
    """ches_rows_by_party groups rows by party_id."""
    rows = parse_chess_csv(ches_csv)
    grouped = {}
    for row in rows:
        if row.party_id is not None:
            grouped.setdefault(row.party_id, []).append(row)
    assert 1206 in grouped  # PSD appears in 1999 and 2006
    assert len(grouped[1206]) == 2


def test_parse_chess_csv_missing_columns():
    """Parser raises ValueError when required columns are missing."""
    bad_csv = "year,country,party_id,name\n1999,12,1206,PSD\n"
    with pytest.raises(ValueError):
        parse_chess_csv(bad_csv)


def test_parse_chess_csv_empty():
    """Parser handles empty CSV (header only)."""
    empty_csv = "year,country,eastwest,eumember,party_id,party,cmp_id,vote,seat,electionyear,epvote,family,govt,lrgen,lrecon,lrecon_salience,lrecon_dissent,lrecon_blur,galtan,galtan_salience,galtan_dissent,galtan_blur,eu_position,eu_salience,eu_dissent,eu_blur,spendvtax,spendvtax_salience,deregulation,dereg_salience,redistribution,redist_salience,econ_interven,civlib_laworder,civlib_salience,sociallifestyle,social_salience,womens_rights,lgbtq_rights,samesex_marriage,religious_principles,relig_salience,immigrate_policy,immigrate_salience,immigrate_dissent,multiculturalism,multicult_salience,multicult_dissent,nationalism,nationalism_salience,ethnic_minorities,ethnic_salience,urban_rural,urban_salience,environment,enviro_salience,climate_change,climate_change_salience,protectionism,regions,region_salience,international_security,international_salience,us,us_salience,eu_benefit,eu_ep,eu_fiscal,eu_intmark,eu_employ,eu_budgets,eu_agri,eu_cohesion,eu_environ,eu_asylum,eu_foreign,eu_turkey,eu_russia,russian_interference,anti_islam_rhetoric,people_vs_elite,antielite_salience,corrupt_salience,members_vs_leadership,executive_power,judicial_independence,mip_one,mip_two,mip_three,chesversion\n"
    rows = parse_chess_csv(empty_csv)
    assert rows == []
