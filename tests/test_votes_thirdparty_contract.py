"""Contract tests for vot-parlament.ro.

vot-parlament.ro is a **cross-check**, never the origin of a published row.
These tests lock the shape of its public contract so that a silent change is
detected: if the contract drifts, the importer must report
``DATA_UNAVAILABLE`` and write nothing, not silently publish wrong numbers.

The cdep.ro day index and the vot-parlament export must agree on the official
counts for the same vote - that equality is the whole point of keeping a
second source.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.parse.cdep_votes import parse_day_index
from pipeline.parse.vot_parlament import (
    EXPORT_COLUMNS,
    ContractError,
    parse_export_csv,
    parse_vote_json,
)

FX = Path(__file__).parent / "fixtures" / "votes"

CSV_HEAD = FX / "vot_parlament_votes_export_head.csv"
JSON_37526 = FX / "vot_parlament_vote_37526.json"
API_404 = FX / "vot_parlament_api_votes_37526_404.html"
DAY_20261118 = FX / "cdep_evot2015_day_20261118.xml"


def test_export_header_is_the_exact_22_column_contract():
    header, _rows = parse_export_csv(CSV_HEAD.read_text(encoding="utf-8"))
    assert header == list(EXPORT_COLUMNS)
    assert len(header) == 22


def test_export_header_survives_the_utf8_bom():
    raw = CSV_HEAD.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")  # the BOM is really there
    header, _rows = parse_export_csv(raw.decode("utf-8"))
    assert header[0] == "platform_vote_id"


def test_export_row_for_vote_37526_carries_the_official_counts():
    _header, rows = parse_export_csv(CSV_HEAD.read_text(encoding="utf-8"))
    row = next(r for r in rows if r["native_vote_id"] == "37526")
    assert row["chamber"] == "Camera Deputatilor"
    assert row["official_present"] == "246"
    assert row["official_yes"] == "245"
    assert row["official_no"] == "0"
    assert row["official_abstain"] == "0"
    assert row["official_not_voted"] == "1"
    assert row["truth_contract_version"] == "votes-v1"
    assert row["official_vote_url"] == (
        "https://cdep.ro/ords/pls/steno/evot2015.nominal?idv=37526&idl=1"
    )


def test_cdep_official_counts_equal_the_vot_parlament_cross_check():
    """The two independent sources must agree on the same vote."""
    records = parse_day_index(DAY_20261118.read_bytes())
    cdep = next(r for r in records if r.vote_id == "37526")
    _header, rows = parse_export_csv(CSV_HEAD.read_text(encoding="utf-8"))
    other = next(r for r in rows if r["native_vote_id"] == "37526")

    assert cdep.present == int(other["official_present"])
    assert cdep.yes == int(other["official_yes"])
    assert cdep.no == int(other["official_no"])
    assert cdep.abstain == int(other["official_abstain"])
    assert cdep.not_voting == int(other["official_not_voted"])


def test_vote_json_has_the_exact_eight_top_level_keys():
    payload = parse_vote_json(JSON_37526.read_text(encoding="utf-8"))
    assert set(payload) == {
        "bill",
        "cache",
        "group_breakdown",
        "matter",
        "official_group_summary",
        "party_breakdown",
        "positions",
        "vote",
    }
    assert len(payload["positions"]) == 246


def test_vote_json_position_has_the_exact_twelve_keys():
    payload = parse_vote_json(JSON_37526.read_text(encoding="utf-8"))
    position = payload["positions"][0]
    assert set(position) == {
        "chamber",
        "family_name",
        "given_name",
        "is_duplicate_politician_in_vote",
        "official_person_id",
        "party",
        "party_normalized",
        "politician_key",
        "politician_name",
        "raw_vote_choice",
        "row_number",
        "vote_choice",
    }
    assert position["official_person_id"].startswith("camera:2024:")


def test_api_route_does_not_exist_and_its_body_is_not_json():
    body = API_404.read_text(encoding="utf-8")
    with pytest.raises(ContractError):
        parse_vote_json(body)
