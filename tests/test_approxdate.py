from datetime import date

import pytest

from pipeline.approxdate import parse_ro_date, parse_ro_range


@pytest.mark.parametrize("raw,iso,precision", [
    ("15 iun. 2026", "2026-06-15", "2026-06-15"),
    ("1 sep. 2026", "2026-09-01", "2026-09-01"),
    ("01.12.2024", "2024-12-01", "2024-12-01"),
    ("11.05.2026", "2026-05-11", "2026-05-11"),
    ("15 septembrie 2024", "2024-09-15", "2024-09-15"),
    ("2024-12-01", "2024-12-01", "2024-12-01"),
    ("3 feb. 2025", "2025-02-03", "2025-02-03"),
    ("2 noi. 2026", "2026-11-02", "2026-11-02"),
])
def test_exact_dates(raw, iso, precision):
    ad = parse_ro_date(raw)
    assert ad is not None
    assert ad.earliest.isoformat() == iso
    assert ad.precision == precision
    assert ad.is_exact


def test_month_precision():
    ad = parse_ro_date("mai 2026")
    assert ad.earliest == date(2026, 5, 1)
    assert ad.latest == date(2026, 5, 31)
    assert ad.precision == "2026-05"
    assert not ad.is_exact


def test_year_precision():
    ad = parse_ro_date("2024")
    assert ad.earliest == date(2024, 1, 1)
    assert ad.latest == date(2024, 12, 31)
    assert ad.precision == "2024"


def test_leading_connective():
    ad = parse_ro_date("din 11 mai 2026")
    assert ad.earliest == date(2026, 5, 11)
    ad = parse_ro_date("de la data de 21.12.2024")
    assert ad.earliest == date(2024, 12, 21)


def test_range():
    start, end = parse_ro_range("din 11 mai 2026 - până în 5 oct. 2026")
    assert start.earliest == date(2026, 5, 11)
    assert end.earliest == date(2026, 10, 5)


def test_range_en_dash():
    start, end = parse_ro_range("11 mai 2026 – 5 oct. 2026")
    assert start.earliest == date(2026, 5, 11)
    assert end.earliest == date(2026, 10, 5)


def test_single_date_range_open():
    start, end = parse_ro_range("15 iun. 2026")
    assert start.earliest == date(2026, 6, 15)
    assert end is None


def test_diacritics_month():
    # "mai" has no diacritics but ensure normalization path works for others.
    assert parse_ro_date("15 iunie 2026").earliest == date(2026, 6, 15)


def test_garbage_returns_none():
    assert parse_ro_date("") is None
    assert parse_ro_date(None) is None
    assert parse_ro_date("necunoscut") is None


def test_contains_and_overlap():
    ad = parse_ro_date("mai 2026")
    assert ad.contains(date(2026, 5, 15))
    assert not ad.contains(date(2026, 6, 1))
    other = parse_ro_date("15 mai 2026")
    assert ad.overlaps(other)