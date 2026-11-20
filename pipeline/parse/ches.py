"""Parser for Chapel Hill Expert Survey (CHES) trend file (CC BY 4.0).

Source: EUI archive DOI:10.7910/DVN/TJINLQ, mirrored at chesdata.eu.
File: 1999-2024_CHES_dataset_meansV2.csv (7 waves: 1999, 2002, 2006, 2010, 2014, 2019, 2024).
Coverage: EU-27 + NO/CH/UK; 277 parties; Romania (country code 12) from 2006 onward.

Licence: CC BY 4.0 — redistributable with attribution.
Attribution: Chapel Hill Expert Survey, EUI archive, hdl.handle.net/1814/69975, CC BY 4.0.

Field names verified from live CSV download at
https://github.com/chesdata/chesdata.github.io/releases/download/ches-trend/1999-2024_CHES_dataset_meansV2.csv
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass

COUNTRY_CODE_ROMANIA = 27


@dataclass
class ChesRow:
    """One row from the CHES trend CSV."""

    year: int | None
    country: int | None
    eastwest: int | None
    eumember: int | None
    party_id: int | None
    party: str | None
    cmp_id: int | None
    vote: float | None
    seat: float | None
    electionyear: int | None
    epvote: float | None
    family: int | None
    govt: float | None
    lrgen: float | None
    lrecon: float | None
    lrecon_salience: float | None
    lrecon_dissent: float | None
    lrecon_blur: float | None
    galtan: float | None
    galtan_salience: float | None
    galtan_dissent: float | None
    galtan_blur: float | None
    eu_position: float | None
    eu_salience: float | None
    eu_dissent: float | None
    eu_blur: float | None
    spendvtax: float | None
    spendvtax_salience: float | None
    deregulation: float | None
    dereg_salience: float | None
    redistribution: float | None
    redist_salience: float | None
    econ_interven: float | None
    civlib_laworder: float | None
    civlib_salience: float | None
    sociallifestyle: float | None
    social_salience: float | None
    womens_rights: float | None
    lgbtq_rights: float | None
    samesex_marriage: float | None
    religious_principles: float | None
    relig_salience: float | None
    immigrate_policy: float | None
    immigrate_salience: float | None
    immigrate_dissent: float | None
    multiculturalism: float | None
    multicult_salience: float | None
    multicult_dissent: float | None
    nationalism: float | None
    nationalism_salience: float | None
    ethnic_minorities: float | None
    ethnic_salience: float | None
    urban_rural: float | None
    urban_salience: float | None
    environment: float | None
    enviro_salience: float | None
    climate_change: float | None
    climate_change_salience: float | None
    protectionism: float | None
    regions: float | None
    region_salience: float | None
    international_security: float | None
    international_salience: float | None
    us: float | None
    us_salience: float | None
    eu_benefit: float | None
    eu_ep: float | None
    eu_fiscal: float | None
    eu_intmark: float | None
    eu_employ: float | None
    eu_budgets: float | None
    eu_agri: float | None
    eu_cohesion: float | None
    eu_environ: float | None
    eu_asylum: float | None
    eu_foreign: float | None
    eu_turkey: float | None
    eu_russia: float | None
    russian_interference: float | None
    anti_islam_rhetoric: float | None
    people_vs_elite: float | None
    antielite_salience: float | None
    corrupt_salience: float | None
    members_vs_leadership: float | None
    executive_power: float | None
    judicial_independence: float | None
    mip_one: float | None
    mip_two: float | None
    mip_three: float | None
    chesversion: str | None


def parse_chess_csv(csv_text: str) -> list[ChesRow]:
    """Parse the CHES trend CSV text.

    Returns all rows (all countries). Callers filter by country as needed.
    Rows with missing party or year are skipped.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    required = {"year", "country", "party_id", "party"}
    header = set(reader.fieldnames or [])
    missing = required - header
    if missing:
        raise ValueError(f"CHES CSV missing columns: {sorted(missing)}")

    rows: list[ChesRow] = []
    for row in reader:
        try:
            rows.append(
                ChesRow(
                    year=_parse_int(row.get("year")),
                    country=_parse_int(row.get("country")),
                    eastwest=_parse_int(row.get("eastwest")),
                    eumember=_parse_int(row.get("eumember")),
                    party_id=_parse_int(row.get("party_id")),
                    party=(row.get("party") or "").strip() or None,
                    cmp_id=_parse_int(row.get("cmp_id")),
                    vote=_parse_float(row.get("vote")),
                    seat=_parse_float(row.get("seat")),
                    electionyear=_parse_int(row.get("electionyear")),
                    epvote=_parse_float(row.get("epvote")),
                    family=_parse_int(row.get("family")),
                    govt=_parse_float(row.get("govt")),
                    lrgen=_parse_float(row.get("lrgen")),
                    lrecon=_parse_float(row.get("lrecon")),
                    lrecon_salience=_parse_float(row.get("lrecon_salience")),
                    lrecon_dissent=_parse_float(row.get("lrecon_dissent")),
                    lrecon_blur=_parse_float(row.get("lrecon_blur")),
                    galtan=_parse_float(row.get("galtan")),
                    galtan_salience=_parse_float(row.get("galtan_salience")),
                    galtan_dissent=_parse_float(row.get("galtan_dissent")),
                    galtan_blur=_parse_float(row.get("galtan_blur")),
                    eu_position=_parse_float(row.get("eu_position")),
                    eu_salience=_parse_float(row.get("eu_salience")),
                    eu_dissent=_parse_float(row.get("eu_dissent")),
                    eu_blur=_parse_float(row.get("eu_blur")),
                    spendvtax=_parse_float(row.get("spendvtax")),
                    spendvtax_salience=_parse_float(row.get("spendvtax_salience")),
                    deregulation=_parse_float(row.get("deregulation")),
                    dereg_salience=_parse_float(row.get("dereg_salience")),
                    redistribution=_parse_float(row.get("redistribution")),
                    redist_salience=_parse_float(row.get("redist_salience")),
                    econ_interven=_parse_float(row.get("econ_interven")),
                    civlib_laworder=_parse_float(row.get("civlib_laworder")),
                    civlib_salience=_parse_float(row.get("civlib_salience")),
                    sociallifestyle=_parse_float(row.get("sociallifestyle")),
                    social_salience=_parse_float(row.get("social_salience")),
                    womens_rights=_parse_float(row.get("womens_rights")),
                    lgbtq_rights=_parse_float(row.get("lgbtq_rights")),
                    samesex_marriage=_parse_float(row.get("samesex_marriage")),
                    religious_principles=_parse_float(row.get("religious_principles")),
                    relig_salience=_parse_float(row.get("relig_salience")),
                    immigrate_policy=_parse_float(row.get("immigrate_policy")),
                    immigrate_salience=_parse_float(row.get("immigrate_salience")),
                    immigrate_dissent=_parse_float(row.get("immigrate_dissent")),
                    multiculturalism=_parse_float(row.get("multiculturalism")),
                    multicult_salience=_parse_float(row.get("multicult_salience")),
                    multicult_dissent=_parse_float(row.get("multicult_dissent")),
                    nationalism=_parse_float(row.get("nationalism")),
                    nationalism_salience=_parse_float(row.get("nationalism_salience")),
                    ethnic_minorities=_parse_float(row.get("ethnic_minorities")),
                    ethnic_salience=_parse_float(row.get("ethnic_salience")),
                    urban_rural=_parse_float(row.get("urban_rural")),
                    urban_salience=_parse_float(row.get("urban_salience")),
                    environment=_parse_float(row.get("environment")),
                    enviro_salience=_parse_float(row.get("enviro_salience")),
                    climate_change=_parse_float(row.get("climate_change")),
                    climate_change_salience=_parse_float(row.get("climate_change_salience")),
                    protectionism=_parse_float(row.get("protectionism")),
                    regions=_parse_float(row.get("regions")),
                    region_salience=_parse_float(row.get("region_salience")),
                    international_security=_parse_float(row.get("international_security")),
                    international_salience=_parse_float(row.get("international_salience")),
                    us=_parse_float(row.get("us")),
                    us_salience=_parse_float(row.get("us_salience")),
                    eu_benefit=_parse_float(row.get("eu_benefit")),
                    eu_ep=_parse_float(row.get("eu_ep")),
                    eu_fiscal=_parse_float(row.get("eu_fiscal")),
                    eu_intmark=_parse_float(row.get("eu_intmark")),
                    eu_employ=_parse_float(row.get("eu_employ")),
                    eu_budgets=_parse_float(row.get("eu_budgets")),
                    eu_agri=_parse_float(row.get("eu_agri")),
                    eu_cohesion=_parse_float(row.get("eu_cohesion")),
                    eu_environ=_parse_float(row.get("eu_environ")),
                    eu_asylum=_parse_float(row.get("eu_asylum")),
                    eu_foreign=_parse_float(row.get("eu_foreign")),
                    eu_turkey=_parse_float(row.get("eu_turkey")),
                    eu_russia=_parse_float(row.get("eu_russia")),
                    russian_interference=_parse_float(row.get("russian_interference")),
                    anti_islam_rhetoric=_parse_float(row.get("anti_islam_rhetoric")),
                    people_vs_elite=_parse_float(row.get("people_vs_elite")),
                    antielite_salience=_parse_float(row.get("antielite_salience")),
                    corrupt_salience=_parse_float(row.get("corrupt_salience")),
                    members_vs_leadership=_parse_float(row.get("members_vs_leadership")),
                    executive_power=_parse_float(row.get("executive_power")),
                    judicial_independence=_parse_float(row.get("judicial_independence")),
                    mip_one=_parse_float(row.get("mip_one")),
                    mip_two=_parse_float(row.get("mip_two")),
                    mip_three=_parse_float(row.get("mip_three")),
                    chesversion=(row.get("chesversion") or "").strip() or None,
                )
            )
        except Exception:
            continue

    return rows


def _parse_int(value: str | None) -> int | None:
    if not value or not value.strip():
        return None
    try:
        return int(float(value.strip()))
    except (ValueError, TypeError):
        return None


def _parse_float(value: str | None) -> float | None:
    if not value or not value.strip():
        return None
    try:
        return float(value.strip())
    except (ValueError, TypeError):
        return None


def filter_romania(rows: list[ChesRow]) -> list[ChesRow]:
    """Return only Romania (country code 12) rows."""
    return [r for r in rows if r.country == COUNTRY_CODE_ROMANIA]


def ches_rows_by_party(rows: list[ChesRow]) -> dict[int, list[ChesRow]]:
    """Group CHES rows by party_id."""
    result: dict[int, list[ChesRow]] = {}
    for row in rows:
        if row.party_id is not None:
            result.setdefault(row.party_id, []).append(row)
    return result
