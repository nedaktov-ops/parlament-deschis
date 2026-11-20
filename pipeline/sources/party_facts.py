"""Source adapter for Party Facts (Dataverse DOI:10.7910/DVN/TJINLQ, CC0 1.0).

The Party Facts herokuapp API is decommissioned; ingestion uses the Dataverse
flat-file download (https://dataverse.harvard.edu/api/access/datafile/7675616).
No pagination, no authentication, no rate limits apply to file downloads.

The adapter downloads external-parties.csv, parses it, filters to Romania
(ISO-3 ROU), and matches rows to existing Organization records by normalized
name. Matched organizations get their partyfacts_id populated.

Traps (verified against live data):
* dataset_key='pop'  = Poll of Polls, NOT PopuList
* dataset_key='populist' = PopuList, exactly 6 ROU rows, all year_last=2019
* Four distinct Party Facts IDs: FSN=958, FDSN=276, PDSR=1034, PSD=120
* `website` and `logo` fields do not exist in the file
* `year_first`/`year_last` are integer years, not timestamps
* Country code is ISO-3 (`ROU`), not ISO-2
"""

from __future__ import annotations

import hashlib
import logging

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import Fragment, Organization
from ..normalize import normalize_name
from ..parse.party_facts import filter_rou, parse_external_parties

log = logging.getLogger("parlament.party_facts")

DATAVERSE_URL = "https://dataverse.harvard.edu/api/access/datafile/7675616"


class PartyFactsSource:
    name = "partyfacts"

    def __init__(self, client: requests.Session | None = None):
        self.client = client or requests.Session()

    def fetch_csv(self) -> str:
        """Download external-parties.csv from Dataverse."""
        resp = self.client.get(DATAVERSE_URL, timeout=60)
        resp.raise_for_status()
        return resp.text

    def ingest_partyfacts(
        self,
        session: Session,
        *,
        force: bool = False,
    ) -> dict:
        """Download, parse, and match Party Facts data to organizations.

        Returns a dict with totals: rows_seen, rows_rou, rows_matched,
        rows_unmatched, rows_updated.
        """
        run_total = {
            "rows_seen": 0,
            "rows_rou": 0,
            "rows_matched": 0,
            "rows_unmatched": 0,
            "rows_updated": 0,
        }

        csv_text = self.fetch_csv()
        rows = parse_external_parties(csv_text)
        run_total["rows_seen"] = len(rows)

        rou_rows = filter_rou(rows)
        run_total["rows_rou"] = len(rou_rows)

        # Build a lookup of existing organizations by normalized name
        orgs = session.scalars(select(Organization)).all()
        org_by_name: dict[str, list[Organization]] = {}
        for org in orgs:
            if org.normalized_name:
                org_by_name.setdefault(org.normalized_name, []).append(org)

        for row in rou_rows:
            if not row.name:
                run_total["rows_unmatched"] += 1
                continue

            norm_name = normalize_name(row.name)
            matches = org_by_name.get(norm_name, [])

            if not matches:
                # Try matching by short_name
                if row.name_short:
                    norm_short = normalize_name(row.name_short)
                    matches = org_by_name.get(norm_short, [])

            if not matches:
                run_total["rows_unmatched"] += 1
                log.debug(
                    "No org match for Party Facts row: %s (%s)",
                    row.name,
                    row.partyfacts_id,
                )
                continue

            # If multiple matches, prefer the one without partyfacts_id set
            match: Organization | None = None
            for m in matches:
                if not m.partyfacts_id:
                    match = m
                    break
            if match is None:
                match = matches[0]

            if match.partyfacts_id == row.partyfacts_id:
                # Already set, skip
                continue

            match.partyfacts_id = row.partyfacts_id
            run_total["rows_updated"] += 1
            run_total["rows_matched"] += 1
            log.info(
                "Matched Party Facts %s (%s) to organization %s (%s)",
                row.partyfacts_id,
                row.name,
                match.id,
                match.name,
            )

        return run_total

    def record_fragment(
        self,
        session: Session,
        csv_text: str,
    ) -> Fragment:
        """Archive the raw CSV as a fragment."""
        frag = Fragment(
            model="partyfacts_external_parties",
            source_name=self.name,
            source_id="external-parties.csv",
            source_url=DATAVERSE_URL,
            group_key="external-parties.csv",
            checksum=fragment_checksum(csv_text),
            data={"rows": len(csv_text.splitlines())},
            snapshot_path="dataverse-download",
        )
        session.add(frag)
        session.flush()
        return frag


def fragment_checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
