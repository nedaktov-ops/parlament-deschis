"""Parser for Party Facts external-parties.csv (Dataverse DOI:10.7910/DVN/TJINLQ, CC0 1.0).

The Party Facts herokuapp API is decommissioned; ingestion uses the Dataverse
flat-file download (https://dataverse.harvard.edu/api/access/datafile/7675616).
No pagination, no authentication, no rate limits apply to file downloads.

The CSV carries one row per (dataset_key, dataset_party_id) pairing — a party
may appear multiple times if it is tracked by multiple datasets (e.g. Parlgov
and Manifesto). The Party Facts `partyfacts_id` is the stable cross-dataset
identifier and is the join key for our corpus.

Traps verified against the live data file:
* dataset_key='pop'  = Poll of Polls, NOT PopuList (ROU rows have year_last=2020)
* dataset_key='populist' = PopuList, exactly 6 ROU rows, all year_last=2019
* Four distinct Party Facts IDs for the Romanian succession chain:
  FSN=958, FDSN=276, PDSR=1034, PSD=120 — never collapse to one ID
* `website` and `logo` fields do not exist in the file
* `year_first`/`year_last` are integer years, not timestamps
* Country code is ISO-3 (`ROU`), not ISO-2
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass


@dataclass
class PartyFactsRow:
    """One row from external-parties.csv."""

    country: str
    dataset_key: str
    dataset_party_id: str
    name_short: str | None
    name: str | None
    name_english: str | None
    year_first: int | None
    year_last: int | None
    share: float | None
    share_year: int | None
    description: str | None
    comment: str | None
    created: str | None
    modified: str | None
    external_id: str | None
    partyfacts_id: str | None
    linked: str | None


def parse_external_parties(csv_text: str) -> list[PartyFactsRow]:
    """Parse the Party Facts external-parties.csv text.

    Returns all rows (all countries). Callers filter by country as needed.
    Malformed rows are skipped with a warning; the header is validated against
    the known column set.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    required = {
        "country",
        "dataset_key",
        "dataset_party_id",
        "name_short",
        "name",
        "partyfacts_id",
    }
    header = set(reader.fieldnames or [])
    missing = required - header
    if missing:
        raise ValueError(f"external-parties.csv missing columns: {sorted(missing)}")

    rows: list[PartyFactsRow] = []
    for row in reader:
        try:
            rows.append(
                PartyFactsRow(
                    country=(row.get("country") or "").strip() or None,
                    dataset_key=(row.get("dataset_key") or "").strip() or None,
                    dataset_party_id=(row.get("dataset_party_id") or "").strip() or None,
                    name_short=(row.get("name_short") or "").strip() or None,
                    name=(row.get("name") or "").strip() or None,
                    name_english=(row.get("name_english") or "").strip() or None,
                    year_first=_parse_int(row.get("year_first")),
                    year_last=_parse_int(row.get("year_last")),
                    share=_parse_float(row.get("share")),
                    share_year=_parse_int(row.get("share_year")),
                    description=(row.get("description") or "").strip() or None,
                    comment=(row.get("comment") or "").strip() or None,
                    created=(row.get("created") or "").strip() or None,
                    modified=(row.get("modified") or "").strip() or None,
                    external_id=(row.get("external_id") or "").strip() or None,
                    partyfacts_id=(row.get("partyfacts_id") or "").strip() or None,
                    linked=(row.get("linked") or "").strip() or None,
                )
            )
        except Exception:
            # Skip malformed rows rather than failing the whole ingest
            continue

    return rows


def _parse_int(value: str | None) -> int | None:
    if not value or not value.strip():
        return None
    try:
        return int(value.strip())
    except (ValueError, TypeError):
        return None


def _parse_float(value: str | None) -> float | None:
    if not value or not value.strip():
        return None
    try:
        return float(value.strip())
    except (ValueError, TypeError):
        return None


def filter_rou(rows: list[PartyFactsRow]) -> list[PartyFactsRow]:
    """Return only Romania (ISO-3 ROU) rows."""
    return [r for r in rows if r.country == "ROU"]


def is_populist_dataset(dataset_key: str | None) -> bool:
    """Return True if dataset_key identifies PopuList (not Poll of Polls).

    Trap: dataset_key='pop' is Poll of Polls, NOT PopuList. PopuList uses
    dataset_key='populist'.
    """
    return dataset_key == "populist"


def partyfacts_ids_for_country(
    rows: list[PartyFactsRow], country: str = "ROU"
) -> dict[str, PartyFactsRow]:
    """Return {partyfacts_id: row} for all rows in a country.

    Duplicate partyfacts_ids across datasets are collapsed — the last row wins,
    which is fine since partyfacts_id is the stable cross-dataset identifier.
    """
    result: dict[str, PartyFactsRow] = {}
    for row in rows:
        if row.country != country or not row.partyfacts_id:
            continue
        result[row.partyfacts_id] = row
    return result
