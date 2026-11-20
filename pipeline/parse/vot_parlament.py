"""Readers for the vot-parlament.ro public contract.

vot-parlament.ro is a **cross-check**, never the origin of a published row.
This module only reads its public shape so that a change can be detected
early; the values it returns are compared against the official cdep.ro
totals, never copied into the dataset on their own.

The contract (verified 2026-11-20, see ``tests/fixtures/votes/FIELD-MAP.md``):

* ``/votes/export.csv`` - 22 columns, UTF-8 **with a BOM**;
* ``/votes/<id>.json``  - 8 top-level keys, 12 keys per position;
* ``/api/votes/<id>``   - HTTP 404; there is no JSON API under ``/api/``.
"""

from __future__ import annotations

import csv
import io
import json

EXPORT_COLUMNS = (
    "platform_vote_id",
    "native_vote_id",
    "chamber",
    "vote_time",
    "native_title",
    "native_bill_code",
    "native_bill_number",
    "native_bill_year",
    "native_bill_title",
    "outcome",
    "official_present",
    "official_yes",
    "official_no",
    "official_abstain",
    "official_not_voted",
    "nominal_unknown_rows",
    "official_vote_url",
    "source_fetched_at",
    "native_bill_url",
    "linked_bill_key",
    "linked_bill_url",
    "truth_contract_version",
)

JSON_TOP_LEVEL_KEYS = frozenset(
    {
        "bill",
        "cache",
        "group_breakdown",
        "matter",
        "official_group_summary",
        "party_breakdown",
        "positions",
        "vote",
    }
)


class ContractError(RuntimeError):
    """The remote contract changed (or the body is not what it claims to be)."""


def parse_export_csv(text: str) -> tuple[list[str], list[dict[str, str]]]:
    """Return ``(header, rows)`` of the vote export.

    The file starts with a UTF-8 BOM, so it is read as ``utf-8-sig``.
    """
    reader = csv.reader(io.StringIO(text.lstrip("\ufeff")))
    rows = list(reader)
    if not rows:
        raise ContractError("the vote export is empty")
    header = rows[0]
    if tuple(header) != EXPORT_COLUMNS:
        raise ContractError(f"unexpected vote export header: {header}")
    records = [dict(zip(header, row, strict=False)) for row in rows[1:] if row]
    return header, records


def parse_vote_json(text: str) -> dict:
    """Parse the per-vote JSON document, enforcing the known shape."""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContractError(f"the vote document is not JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ContractError("the vote document is not a JSON object")
    keys = set(payload)
    if keys != JSON_TOP_LEVEL_KEYS:
        missing = sorted(JSON_TOP_LEVEL_KEYS - keys)
        extra = sorted(keys - JSON_TOP_LEVEL_KEYS)
        raise ContractError(f"vote JSON contract drifted (missing={missing}, extra={extra})")
    return payload
