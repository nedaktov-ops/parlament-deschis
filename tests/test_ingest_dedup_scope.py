"""The dedup key must include scope (chamber + legislature).

The same person in the same group (PDSR) in two different legislatures
(deputies 1992 and deputies 1996) must produce TWO membership rows, not one
collapsed row. The dedup key is (person, group, chamber, legislature, join,
leave); since the group organisation and the legislature differ, the keys
differ and both rows are written.

Uses real cached pages: deputies 1992 group_11 (PDSR) and deputies 1996
group_2 (PDSR). Năstase Adrian sits in PDSR in both legislatures (idm=1 in
1992, idm=208 in 1996).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import select

from pipeline.collect import Corpus, LedgerRecord, MandateRef
from pipeline.db import (
    Membership,
    PersonIdentifier,
    init_db,
    make_engine,
    make_session_factory,
)
from pipeline.ingest_corpus import CorpusIngestor
from pipeline.parse.cdep_group import parse_group_ledger

CACHE = Path("data/cache/cdep")

_REQUIRED_PAGES = (
    CACHE / "deputies" / "1992" / "group_11.html",
    CACHE / "deputies" / "1996" / "group_2.html",
)
if not all(path.exists() for path in _REQUIRED_PAGES):
    # P5-F: intentional skip - data/cache/cdep is gitignored and no trimmed
    # fixture is checked in; the optional archived cdep corpus is required.
    pytest.skip("requires the optional archived cdep corpus", allow_module_level=True)


def _ledger(legislature: str, idg: str) -> LedgerRecord:
    html = (CACHE / "deputies" / legislature / f"group_{idg}.html").read_text(encoding="utf-8")
    ledger = parse_group_ledger(
        html,
        chamber="deputies",
        legislature=legislature,
        source_url=(
            f"https://www.cdep.ro/ords/pls/parlam/structura2015.gp"
            f"?cam=2&leg={legislature}&idg={idg}"
        ),
    )
    return LedgerRecord(
        chamber="deputies",
        legislature=legislature,
        idg=idg,
        url=(
            f"https://www.cdep.ro/ords/pls/parlam/structura2015.gp"
            f"?cam=2&leg={legislature}&idg={idg}"
        ),
        sha256="test",
        ledger=ledger,
        fetched_at=datetime.now(UTC),
    )


def test_same_person_two_legislatures_two_membership_rows():
    corpus = Corpus()
    corpus.ledgers = [
        _ledger("1992", "11"),  # PDSR, 1992
        _ledger("1996", "2"),  # PDSR, 1996
    ]
    # Both mandates resolve to the same person cluster. Without this, the
    # per-mandate fallback key would differ by legislature and the two rows
    # would be trivially separate — this tests that scope is what keeps them
    # apart even when the identity is shared.
    shared_cluster = "cdep-person:test-nastase-adrian"
    corpus.clusters = {
        MandateRef("deputies", "1992", "1"): shared_cluster,
        MandateRef("deputies", "1996", "208"): shared_cluster,
    }
    # Profiles are optional for membership ingest; _write_mandate returns
    # early when there is no profile. Empty is fine here.
    corpus.profiles = {}
    corpus.index_counts = {}

    engine = make_engine(":memory:")
    init_db(engine)
    session = make_session_factory(engine)()
    try:
        CorpusIngestor(session, corpus).run()

        # Find the person that both mandates resolve to via the shared
        # cluster identifier stored on PersonIdentifier.
        ident = session.scalars(
            select(PersonIdentifier).where(
                PersonIdentifier.scheme == "cdep_person",
                PersonIdentifier.identifier == "cdep-person:test-nastase-adrian",
            )
        ).first()
        assert ident is not None, "shared cluster person was not created"
        person_id = ident.person_id

        ms = list(session.scalars(select(Membership).where(Membership.person_id == person_id)))
        assert len(ms) == 2, f"expected 2 membership rows, got {len(ms)}"
        legislatures = {m.legislature for m in ms}
        assert legislatures == {"1992", "1996"}, legislatures
    finally:
        session.close()
