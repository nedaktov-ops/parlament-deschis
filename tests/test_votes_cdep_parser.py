"""Parser tests for the official cdep.ro roll-call vote feeds.

Everything here runs offline against the locked fixtures in
``tests/fixtures/votes/`` (captured 2026-11-20, SHA-256 in ``manifest.json``).
The assertions are the **exact** values verified in
``tests/fixtures/votes/FIELD-MAP.md`` - they exist to catch a change in the
upstream format or in our interpretation of it.

Three traps are locked here on purpose:

* the XML prolog claims ISO-8859-2 while the bytes are UTF-8;
* the nominal token ``-`` means *present but did not vote*, not abstain;
* the group label differs between the HTML page and the XML list for some
  members, so it cannot be part of the join key.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from pipeline.parse.cdep_votes import (
    DAY_FIELDS,
    NOMINAL_FIELDS,
    chamber_for_cam,
    decode_xml_bytes,
    join_nominal,
    normalize_choice,
    parse_day_index,
    parse_nominal_list,
    parse_nominal_page,
)

FX = Path(__file__).parent / "fixtures" / "votes"

DAY_20261118 = FX / "cdep_evot2015_day_20261118.xml"
DAY_20261110 = FX / "cdep_evot2015_day_20261110.xml"
NOMINAL_37526_XML = FX / "cdep_evot2015_nominal_37526.xml"
NOMINAL_37526_HTML = FX / "cdep_evot2015_nominal_37526.html"
NOMINAL_37492_HTML = FX / "cdep_evot2015_nominal_37492.html"


# --- encoding ---------------------------------------------------------------


def test_xml_bytes_decode_as_utf8_even_though_the_prolog_claims_latin2():
    raw = NOMINAL_37526_XML.read_bytes()
    assert b'encoding="ISO-8859-2"' in raw[:80]  # the prolog lies
    text = decode_xml_bytes(raw)
    assert "Drăgoescu" in text  # UTF-8 bytes, decoded as UTF-8
    assert "DrÄgoescu" not in text  # the latin-2 mojibake must not appear


def test_decode_xml_bytes_falls_back_to_latin2_when_utf8_is_impossible():
    raw = b"<x>Dr\xe3goescu</x>"  # 0xe3 cannot start a UTF-8 sequence
    assert "Drăgoescu" in decode_xml_bytes(raw)


# --- day index --------------------------------------------------------------


@pytest.fixture
def day_20261118():
    return parse_day_index(DAY_20261118.read_bytes())


def test_day_index_has_the_exact_nine_verified_fields(day_20261118):
    assert DAY_FIELDS == (
        "VOTID",
        "TIME_VOT",
        "DESCRIERE",
        "CAMERA",
        "PREZENTI",
        "NU_AU_VOTAT",
        "AU_VOTAT_DA",
        "AU_VOTAT_NU",
        "AU_VOTAT_AB",
    )
    assert len(day_20261118) == 16
    record = day_20261118[0]
    assert record.vote_id
    assert record.time_vote
    assert record.description
    assert record.camera is not None


def test_day_index_counts_are_integers_and_reconcile(day_20261118):
    for record in day_20261118:
        assert isinstance(record.present, int)
        assert isinstance(record.yes, int)
        assert isinstance(record.no, int)
        assert isinstance(record.abstain, int)
        assert isinstance(record.not_voting, int)
        # present == yes + no + abstain + did not vote
        assert record.present == record.yes + record.no + record.abstain + record.not_voting


def test_anchor_vote_37526_has_the_verified_official_counts(day_20261118):
    record = next(r for r in day_20261118 if r.vote_id == "37526")
    assert record.description == "PL-x 594/2026 - Vot final adoptare"
    assert record.camera == "2"
    assert record.present == 246
    assert record.yes == 245
    assert record.no == 0
    assert record.abstain == 0
    assert record.not_voting == 1


def test_joint_sitting_day_is_marked_with_camera_zero():
    records = parse_day_index(DAY_20261110.read_bytes())
    assert len(records) == 13
    assert {r.camera for r in records} == {"0"}


# --- nominal list (XML) -----------------------------------------------------


@pytest.fixture
def nominal_37526():
    return parse_nominal_list(NOMINAL_37526_XML.read_bytes())


def test_nominal_list_has_the_exact_six_verified_fields(nominal_37526):
    assert NOMINAL_FIELDS == ("VOTID", "NUME", "PRENUME", "GRUP", "CAMERA", "VOT")
    assert len(nominal_37526) == 246
    assert {r.vote_id for r in nominal_37526} == {"37526"}
    assert {r.camera for r in nominal_37526} == {"2"}


def test_nominal_list_vote_tokens_are_da_and_did_not_vote(nominal_37526):
    assert Counter(r.vote for r in nominal_37526) == Counter({"DA": 245, "-": 1})


def test_nominal_list_names_are_decoded(nominal_37526):
    names = {f"{r.given_name} {r.family_name}" for r in nominal_37526}
    assert "Drăgoescu Cezar-Mihail" in names
    assert "Găl Károly" in names


# --- nominal page (HTML) ----------------------------------------------------


def test_nominal_page_exposes_the_official_person_id_for_every_voter():
    rows = parse_nominal_page(NOMINAL_37526_HTML.read_text(encoding="utf-8"))
    assert len(rows) == 246
    assert len({r.idm for r in rows}) == 246
    assert {r.cam for r in rows} == {"2"}
    assert {r.legislature for r in rows} == {"2024"}
    assert rows[0].idm == "1"
    assert rows[0].name_raw == "Adomnicăi Mirela Elena"
    assert rows[0].group_raw == "PSD"
    assert rows[0].vote_raw == "DA"


def test_joint_vote_page_carries_both_chambers():
    rows = parse_nominal_page(NOMINAL_37492_HTML.read_text(encoding="utf-8"))
    assert len(rows) == 218
    assert Counter(r.cam for r in rows) == Counter({"2": 161, "1": 57})


# --- join -------------------------------------------------------------------


def test_every_nominal_row_joins_to_exactly_one_page_row():
    xml_rows = parse_nominal_list(NOMINAL_37526_XML.read_bytes())
    page_rows = parse_nominal_page(NOMINAL_37526_HTML.read_text(encoding="utf-8"))
    result = join_nominal(xml_rows, page_rows)

    assert len(result.positions) == 246
    assert result.unmatched_xml == []
    assert result.ambiguous_names == []
    assert result.disagreements == []


def test_joined_positions_carry_the_idm_and_the_verified_vote_token():
    xml_rows = parse_nominal_list(NOMINAL_37526_XML.read_bytes())
    page_rows = parse_nominal_page(NOMINAL_37526_HTML.read_text(encoding="utf-8"))
    result = join_nominal(xml_rows, page_rows)

    by_idm = {p.idm: p for p in result.positions}
    assert by_idm["1"].name_raw == "Adomnicăi Mirela Elena"
    assert by_idm["1"].vote_raw == "DA"
    assert by_idm["1"].legislature == "2024"
    # the member who did not vote carries the "-" token
    not_voters = [p for p in result.positions if p.vote_raw == "-"]
    assert len(not_voters) == 1


def test_group_label_differences_between_the_two_views_do_not_break_the_join():
    """cdep publishes 'neafiliat' in the XML and 'Neafiliati' in the page."""
    xml_rows = parse_nominal_list(NOMINAL_37526_XML.read_bytes())
    page_rows = parse_nominal_page(NOMINAL_37526_HTML.read_text(encoding="utf-8"))
    result = join_nominal(xml_rows, page_rows)

    differing = [
        p for p in result.positions if p.group_xml and p.group_html and p.group_xml != p.group_html
    ]
    assert len(differing) == 20
    assert len(result.positions) == 246  # every row still joined


def test_ambiguous_name_is_quarantined_instead_of_guessed():
    xml_rows = parse_nominal_list(NOMINAL_37526_XML.read_bytes())
    page_rows = parse_nominal_page(NOMINAL_37526_HTML.read_text(encoding="utf-8"))
    # duplicate a page row under the same name with a different idm
    duplicate = page_rows[0]
    from pipeline.parse.cdep_votes import NominalRow

    page_rows.append(
        NominalRow(
            idm="999",
            cam=duplicate.cam,
            legislature=duplicate.legislature,
            name_raw=duplicate.name_raw,
            group_raw=duplicate.group_raw,
            vote_raw=duplicate.vote_raw,
        )
    )
    result = join_nominal(xml_rows, page_rows)

    assert len(result.positions) == 245
    assert len(result.ambiguous_names) == 1


# --- semantics --------------------------------------------------------------


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("DA", "yes"),
        ("NU", "no"),
        ("AB", "abstain"),
        ("-", "not_voting"),
        (None, "unknown"),
        ("", "unknown"),
        ("whatever", "unknown"),
    ],
)
def test_choice_normalisation(token, expected):
    assert normalize_choice(token) == expected


@pytest.mark.parametrize(
    ("cam", "expected"),
    [("2", "deputies"), ("1", "senate"), ("0", None), (None, None), ("9", None)],
)
def test_chamber_code_mapping(cam, expected):
    assert chamber_for_cam(cam) == expected
