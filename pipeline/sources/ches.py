"""Source adapter for Chapel Hill Expert Survey (CHES, CC BY 4.0).

Downloads the CHES trend CSV from Dataverse via chesdata.eu GitHub releases,
parses it, filters to Romania (country code 12), and matches rows to existing
Organization records by normalized name. Matched organizations get their
ideology covariates stored in the party_ideology table.

Source: Chapel Hill Expert Survey, EUI archive DOI:10.7910/DVN/TJINLQ, CC BY 4.0.
File: https://github.com/chesdata/chesdata.github.io/releases/download/ches-trend/1999-2024_CHES_dataset_meansV2.csv
"""

from __future__ import annotations

import hashlib
import logging

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import Fragment, Organization, PartyIdeology
from ..normalize import normalize_name
from ..parse.ches import filter_romania, parse_chess_csv

log = logging.getLogger("parlament.ches")

CHES_CSV_URL = (
    "https://github.com/chesdata/chesdata.github.io/releases/download/"
    "ches-trend/1999-2024_CHES_dataset_meansV2.csv"
)


class ChesSource:
    name = "ches"

    def __init__(self, client: requests.Session | None = None):
        self.client = client or requests.Session()

    def fetch_csv(self) -> str:
        """Download the CHES trend CSV from GitHub releases."""
        resp = self.client.get(CHES_CSV_URL, timeout=60)
        resp.raise_for_status()
        return resp.text

    def ingest_ches(
        self,
        session: Session,
        *,
        force: bool = False,
    ) -> dict:
        """Download, parse, and match CHES data to organizations.

        Returns a dict with totals: rows_seen, rows_romania, rows_matched,
        rows_unmatched, rows_updated.
        """
        run_total = {
            "rows_seen": 0,
            "rows_romania": 0,
            "rows_matched": 0,
            "rows_unmatched": 0,
            "rows_updated": 0,
        }

        csv_text = self.fetch_csv()
        rows = parse_chess_csv(csv_text)
        run_total["rows_seen"] = len(rows)

        rou_rows = filter_romania(rows)
        run_total["rows_romania"] = len(rou_rows)

        # Build lookup of existing organizations by normalized name
        orgs = session.scalars(select(Organization)).all()
        org_by_name: dict[str, list[Organization]] = {}
        for org in orgs:
            if org.normalized_name:
                org_by_name.setdefault(org.normalized_name, []).append(org)
            if org.name:
                org_by_name.setdefault(normalize_name(org.name), []).append(org)

        for row in rou_rows:
            if not row.party:
                run_total["rows_unmatched"] += 1
                continue

            norm_name = normalize_name(row.party)
            matches = org_by_name.get(norm_name, [])

            if not matches:
                run_total["rows_unmatched"] += 1
                log.debug(
                    "No org match for CHES row: %s (party_id=%s)",
                    row.party,
                    row.party_id,
                )
                continue

            # Prefer match without existing ideology for this year
            match = None
            existing_year = row.year
            for m in matches:
                existing = session.scalars(
                    select(PartyIdeology).where(
                        PartyIdeology.organization_id == m.id,
                        PartyIdeology.survey_year == existing_year,
                        PartyIdeology.source == "ches",
                    )
                ).first()
                if not existing:
                    match = m
                    break
            if match is None:
                match = matches[0]

            dedup_key = f"ches:{row.party_id}:{row.year}"

            # Check if already exists
            existing = session.scalars(
                select(PartyIdeology).where(PartyIdeology.dedup_key == dedup_key)
            ).first()
            if existing:
                continue

            ideology = PartyIdeology(
                organization_id=match.id,
                survey_year=row.year,
                source="ches",
                lrgen=row.lrgen,
                lrecon=row.lrecon,
                galtan=row.galtan,
                eu_position=row.eu_position,
                antielite_salience=row.antielite_salience,
                people_vs_elite=row.people_vs_elite,
                source_url=CHES_CSV_URL,
                snapshot_hash=hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
                dedup_key=dedup_key,
            )
            session.add(ideology)
            run_total["rows_updated"] += 1
            run_total["rows_matched"] += 1
            log.info(
                "Matched CHES %s (%s, year %d) to organization %s (%s)",
                row.party_id,
                row.party,
                row.year,
                match.id,
                match.name,
            )

        session.commit()
        return run_total

    def record_fragment(
        self,
        session: Session,
        csv_text: str,
    ) -> Fragment:
        """Archive the raw CSV as a fragment."""
        frag = Fragment(
            model="ches_trend_csv",
            source_name=self.name,
            source_id="ches-trend-csv",
            source_url=CHES_CSV_URL,
            group_key="ches-trend-csv",
            checksum=hashlib.sha256(csv_text.encode("utf-8")).hexdigest(),
            data={"rows": len(csv_text.splitlines())},
            snapshot_path="ches-download",
        )
        session.add(frag)
        session.flush()
        return frag
