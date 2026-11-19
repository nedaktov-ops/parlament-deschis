"""Shared pytest fixtures.

The API result cache (``backend.cache``) is module-global so it survives
between tests that each build their own app + tmp database. Without an
explicit clear here, a value cached by an earlier test would be served to a
later one whose fixture DB has different rows — which is exactly the stale
read the wave-recompute test exists to catch.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from backend.cache import invalidate as invalidate_result_cache

# Path to the canonical database used by most tests.
_CANONICAL_DB = Path(__file__).parent.parent / "data" / "parlament.db"


@pytest.fixture(autouse=True)
def _clear_result_cache():
    invalidate_result_cache()
    yield
    invalidate_result_cache()


@pytest.fixture
def app(tmp_path):
    """Create a test app with a deduplicated in-memory copy of the corpus DB.

    The shipped ``data/parlament.db`` contains legacy duplicate memberships
    (9 closed-stint stints slipped through before uq_stint was enforced).
    This fixture copies, deduplicates, and uses that copy for each test run,
    ensuring create_app() / init_db() can succeed without hitting UNIQUE
    constraints. See W2-C remediation plan.
    """
    test_db = tmp_path / "parlament.db"
    shutil.copy(_CANONICAL_DB, test_db)

    # Apply the same deduplication logic that prepare_db.py uses for releases:
    # delete the rowid that is NOT the minimus for each duplicate group.
    import sqlite3

    conn = sqlite3.connect(str(test_db))
    # Temporarily disable FK checks for the one-time dedupe: duplicates may have
    # orphaned evidence/event rows that would otherwise block the DELETE.
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.execute(
        """
        DELETE FROM membership
        WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM membership
            WHERE end_date IS NOT NULL
            GROUP BY org_id, person_id, COALESCE(chamber, ''),
                     COALESCE(legislature, ''), end_date,
                     COALESCE(start_date, '')
        )
        AND end_date IS NOT NULL
    """
    )
    conn.execute(
        """
        DELETE FROM membership
        WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM membership
            WHERE end_date IS NULL
            GROUP BY org_id, person_id, COALESCE(post_id, ''),
                     COALESCE(chamber, ''), COALESCE(legislature, '')
        )
        AND end_date IS NULL
    """
    )
    conn.commit()
    conn.close()

    orig = os.environ.get("PARLAMENT_DB")
    os.environ["PARLAMENT_DB"] = str(test_db)
    from backend.main import create_app

    yield create_app()
    if orig is None:
        os.environ.pop("PARLAMENT_DB", None)
    else:
        os.environ["PARLAMENT_DB"] = orig
