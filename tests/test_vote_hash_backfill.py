"""Existing votes without provenance are backfilled, not skipped forever.

Regression for the dedup short-circuit in ``cmd_ingest_votes``: before snapshot
hashing was introduced, some votes were stored with a NULL ``snapshot_hash``.
Re-running the importer found them by ``dedup_key`` and did nothing, so the
``vote_evidence`` audit reported them as new errors on every run.

The importer must fill the missing provenance from the bytes it has just
fetched, must never overwrite evidence that is already present, and must not
write anything at all in dry-run mode. Runs fully offline against fixtures.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

import pipeline.cli as cli
from pipeline.db import Vote, get_session

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures" / "votes"
DAY_FIXTURE = FIXTURES / "cdep_evot2015_day_20261118.xml"
NOMINAL_XML = FIXTURES / "cdep_evot2015_nominal_37526.xml"
NOMINAL_HTML = FIXTURES / "cdep_evot2015_nominal_37526.html"
VOTE_ID = "37526"


class _Response:
    def __init__(self, content: bytes, url: str, text: str | None = None):
        self.content = content
        self.url = url
        self.text = text if text is not None else content.decode("utf-8", errors="replace")


def _seed_vote(db: Path, *, snapshot_hash: str | None, source_url: str = "") -> None:
    session = get_session(db)
    session.add(
        Vote(
            source="cdep",
            native_vote_id=VOTE_ID,
            chamber="deputies",
            legislature="2024",
            source_url=source_url,
            snapshot_hash=snapshot_hash,
            dedup_key=f"cdep:{VOTE_ID}",
        )
    )
    session.commit()
    session.close()


@pytest.fixture
def fake_client(monkeypatch):
    """Serve the checked-in fixtures for the one day under test."""

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def get(self, url: str):
            if "par1=1" in url:
                return _Response(DAY_FIXTURE.read_bytes(), url)
            if "evot2015.xml" in url:
                return _Response(NOMINAL_XML.read_bytes(), url)
            if "evot2015.nominal" in url:
                raw = NOMINAL_HTML.read_bytes()
                return _Response(raw, url, text=raw.decode("utf-8", errors="replace"))
            raise AssertionError(f"unexpected URL: {url}")

        def close(self):
            pass

    monkeypatch.setattr(cli, "PoliteClient", FakeClient)


def _run(db: Path, *extra: str) -> int:
    return cli.main(
        [
            "--db",
            str(db),
            "ingest-votes",
            "--start-date",
            "20261118",
            "--end-date",
            "20261118",
            *extra,
        ]
    )


def test_existing_vote_gets_provenance_backfilled(tmp_path: Path, fake_client, capsys):
    db = tmp_path / "votes.db"
    _seed_vote(db, snapshot_hash=None)

    assert _run(db, "--apply") == 0
    assert "votes backfilled:     1" in capsys.readouterr().out

    session = get_session(db)
    vote = session.scalar(select(Vote).where(Vote.dedup_key == f"cdep:{VOTE_ID}"))
    assert vote is not None
    assert vote.snapshot_hash and len(vote.snapshot_hash) == 64
    assert vote.source_url
    session.close()

    # A second, idempotent run must not count or change anything.
    assert _run(db, "--apply") == 0
    assert "votes backfilled:     0" in capsys.readouterr().out


def test_existing_provenance_is_never_overwritten(tmp_path: Path, fake_client, capsys):
    db = tmp_path / "votes.db"
    original_hash = "a" * 64
    original_url = "https://example.org/original.xml"
    _seed_vote(db, snapshot_hash=original_hash, source_url=original_url)

    assert _run(db, "--apply") == 0
    assert "votes backfilled:     0" in capsys.readouterr().out

    session = get_session(db)
    vote = session.scalar(select(Vote).where(Vote.dedup_key == f"cdep:{VOTE_ID}"))
    assert vote.snapshot_hash == original_hash
    assert vote.source_url == original_url
    session.close()


def test_dry_run_does_not_write_backfill(tmp_path: Path, fake_client, capsys):
    db = tmp_path / "votes.db"
    _seed_vote(db, snapshot_hash=None)

    assert _run(db) == 0
    assert "would backfill votes: 1" in capsys.readouterr().out

    session = get_session(db)
    vote = session.scalar(select(Vote).where(Vote.dedup_key == f"cdep:{VOTE_ID}"))
    assert vote is not None
    assert vote.snapshot_hash is None
    session.close()
