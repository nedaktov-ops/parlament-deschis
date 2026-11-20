"""The licence register: what may be copied into the CC BY 4.0 dataset.

This module is the code twin of
``tests/fixtures/votes/LICENSE-APPENDIX.md``. The two must always agree -
the appendix is for humans, this file is what the database enforces.

Three classes:

* **COPY** - CC0, CC BY 4.0, OGL-ROU-1.0. The values may be stored and
  republished, with the attribution string.
* **CROSS-CHECK** - NonCommercial, ShareAlike or unverified. The values may
  be *displayed* as an external benchmark, never copied into the dataset or
  an export.
* **CONDITIONAL** - a licence that depends on a file, a version or a
  permission we do not hold yet. Treated as CROSS-CHECK until the
  permission exists in writing.

The database enforces the rule with a CHECK constraint
(``ck_source_license_redistributable``): a source can only be marked
redistributable if its licence is one of the three compatible ones.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db import SourceLicense

log = logging.getLogger("parlament.licenses")

# The licences compatible with this project's CC BY 4.0 dataset.
COMPATIBLE_LICENSES = ("CC0-1.0", "CC-BY-4.0", "OGL-ROU-1.0")


@dataclass(frozen=True)
class LicenseEntry:
    source_name: str
    license_id: str
    redistributable: bool
    license_url: str | None = None
    share_alike: bool = False
    attribution: str | None = None
    verification_url: str | None = None
    verification_quote: str | None = None
    verified_on: str | None = None
    note: str | None = None


REGISTER: tuple[LicenseEntry, ...] = (
    LicenseEntry(
        source_name="cdep_facts",
        license_id="OGL-ROU-1.0",
        redistributable=True,
        license_url="https://www.cdep.ro/",
        attribution=(
            "Camera Deputaților — official parliamentary facts "
            "(names, dates, votes), source URL per row"
        ),
        verification_url="https://www.cdep.ro/",
        verification_quote=(
            "Romanian official facts (Law 8/1996 art. 9); the cdep.ro legal "
            "notice covers creative assets, not facts"
        ),
        verified_on="2026-11-20",
    ),
    LicenseEntry(
        source_name="senat_facts",
        license_id="OGL-ROU-1.0",
        redistributable=True,
        license_url="https://www.senat.ro/",
        attribution="Senatul României — official parliamentary facts, source URL per row",
        verification_url="https://www.senat.ro/",
        verification_quote="Official parliamentary facts published by the Senate of Romania",
        verified_on="2026-11-20",
    ),
    LicenseEntry(
        source_name="ro_281",
        license_id="CC-BY-4.0",
        redistributable=True,
        license_url="https://281.ro/api",
        attribution="281.ro · Registrul neoficial al Parlamentului României",
        verification_url="https://281.ro/metodologie",
        verification_quote=("Toate datele sunt disponibile sub licență Creative Commons CC-BY 4.0"),
        verified_on="2026-11-20",
        note="The project's public repository is not reachable; the licence is self-declared.",
    ),
    LicenseEntry(
        source_name="wikidata",
        license_id="CC0-1.0",
        redistributable=True,
        license_url="https://www.wikidata.org/wiki/Wikidata:Licensing",
        attribution="Wikidata — CC0 1.0",
        verification_url="https://www.wikidata.org/wiki/Wikidata:Licensing",
        verification_quote="CC0 1.0 Universal",
        verified_on="2026-11-20",
    ),
    LicenseEntry(
        source_name="gld",
        license_id="CC0-1.0",
        redistributable=True,
        license_url="https://doi.org/10.7910/DVN/U1ZNVT",
        attribution="Global Legislators Database, doi:10.7910/DVN/U1ZNVT, CC0",
        verification_url="https://doi.org/10.7910/DVN/U1ZNVT",
        verification_quote="CC0 1.0 Universal",
        verified_on="2026-11-20",
    ),
    LicenseEntry(
        source_name="partyfacts",
        license_id="CC0-1.0",
        redistributable=True,
        license_url="https://doi.org/10.7910/DVN/TJINLQ",
        attribution="Party Facts, doi:10.7910/DVN/TJINLQ, CC0 1.0",
        verification_url="https://doi.org/10.7910/DVN/TJINLQ",
        verification_quote="CC0 1.0 Universal (Dataverse metadata)",
        verified_on="2026-11-20",
        note="The project site licence itself could not be verified; the dataset licence is CC0.",
    ),
    LicenseEntry(
        source_name="ches_eui",
        license_id="CC-BY-4.0",
        redistributable=True,
        license_url="https://hdl.handle.net/1814/69975",
        attribution="CHES, EUI archive, hdl.handle.net/1814/69975, CC BY 4.0",
        verification_url="https://hdl.handle.net/1814/69975",
        verification_quote="Creative Commons Attribution 4.0 International",
        verified_on="2026-11-20",
        note="Per-file licences on chesdata.eu still need checking before a file is ingested.",
    ),
    LicenseEntry(
        source_name="data_gov_ro",
        license_id="OGL-ROU-1.0",
        redistributable=True,
        license_url="https://data.gov.ro/",
        attribution="data.gov.ro / AEP — OGL-ROU-1.0, dataset ID per row",
        verification_url="https://data.gov.ro/",
        verification_quote="Open Government Licence (Romania) / CC BY 4.0 for datasets published after 2020",
        verified_on="2026-11-20",
    ),
    LicenseEntry(
        source_name="zenodo_3332908",
        license_id="CC-BY-4.0",
        redistributable=True,
        license_url="https://doi.org/10.5281/zenodo.3332908",
        attribution="Zenodo 3332908, CC BY 4.0",
        verification_url="https://doi.org/10.5281/zenodo.3332908",
        verification_quote="Creative Commons Attribution 4.0 International",
        verified_on="2026-11-20",
    ),
    LicenseEntry(
        source_name="vot_parlament",
        license_id="CC-BY-4.0",
        redistributable=False,
        license_url="https://vot-parlament.ro/",
        attribution="vot-parlament.ro · CC BY 4.0 · source URL per vote",
        verification_url="https://vot-parlament.ro/",
        verification_quote="CC BY 4.0",
        verified_on="2026-11-20",
        note=(
            "Cross-check only: the site serves Content-Signal: ai-train=no, use=reference "
            "and its robots.txt disallows the training bots. Every published row comes "
            "from cdep.ro."
        ),
    ),
    LicenseEntry(
        source_name="v_dem",
        license_id="CC-BY-SA-4.0",
        redistributable=False,
        license_url="https://www.v-dem.net/",
        attribution="V-Dem, CC BY-SA 4.0 — external cross-check only",
        share_alike=True,
        verified_on="2026-11-20",
    ),
    LicenseEntry(
        source_name="ipu",
        license_id="CC-BY-NC-SA-4.0",
        redistributable=False,
        license_url="https://data.ipu.org/",
        attribution="IPU Parline, CC BY-NC-SA 4.0 — external cross-check only",
        share_alike=True,
        verified_on="2026-11-20",
    ),
    LicenseEntry(
        source_name="open_sanctions",
        license_id="CC-BY-NC-4.0",
        redistributable=False,
        license_url="https://www.opensanctions.org/licenses/",
        attribution="OpenSanctions, CC BY-NC 4.0 — external cross-check only",
        verified_on="2026-11-20",
    ),
    LicenseEntry(
        source_name="populist",
        license_id="UNVERIFIED",
        redistributable=False,
        license_url="https://osf.io/",
        attribution="The PopuList — licence UNVERIFIED — conditional / external cross-check only",
        verified_on="2026-11-20",
        note="The OSF node licence is null and the project ships no LICENSE file.",
    ),
    LicenseEntry(
        source_name="ser_prom",
        license_id="CC-BY-SA-4.0",
        redistributable=False,
        license_url="https://serprom.eu/",
        attribution="SER-PROM, CC BY-SA 4.0 — cross-check until CC-BY permission obtained",
        share_alike=True,
        verified_on="2026-11-20",
    ),
)


def ensure_source_licenses(session: Session) -> int:
    """Write the register into ``source_license``; return the number of rows.

    Idempotent: an existing row is updated in place, so a changed licence
    class takes effect on the next run without a migration.
    """
    for entry in REGISTER:
        row = session.get(SourceLicense, entry.source_name)
        if row is None:
            row = SourceLicense(source_name=entry.source_name)
            session.add(row)
        row.license_id = entry.license_id
        row.license_url = entry.license_url
        row.redistributable = entry.redistributable
        row.share_alike = entry.share_alike
        row.attribution = entry.attribution
        row.verification_url = entry.verification_url
        row.verification_quote = entry.verification_quote
        row.verified_on = entry.verified_on
        row.note = entry.note
    session.commit()
    return len(REGISTER)


def redistributable_sources(session: Session) -> set[str]:
    """The sources whose values may be copied into an export."""
    rows = session.scalars(
        select(SourceLicense.source_name).where(SourceLicense.redistributable.is_(True))
    )
    return set(rows)
