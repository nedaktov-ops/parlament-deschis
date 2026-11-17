"""Shared pytest fixtures.

The API result cache (``backend.cache``) is module-global so it survives
between tests that each build their own app + tmp database. Without an
explicit clear here, a value cached by an earlier test would be served to a
later one whose fixture DB has different rows — which is exactly the stale
read the wave-recompute test exists to catch.
"""

from __future__ import annotations

import pytest

from backend.cache import invalidate as invalidate_result_cache


@pytest.fixture(autouse=True)
def _clear_result_cache():
    invalidate_result_cache()
    yield
    invalidate_result_cache()
