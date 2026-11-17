"""Read-only result cache for hot API endpoints.

The dataset is pinned per release and the API database is read-only at
runtime (the same invariant the traseism overview cache in
``backend/routers/api.py`` relies on). A short TTL therefore only bounds
staleness after an admin-triggered recompute — it never serves data from a
different release, because a release restarts the process and empties the
cache.

Why this exists: the endpoints are synchronous FastAPI handlers running in
a threadpool behind uvicorn's GIL. Measured on 8 cores, a cold
``/api/parties`` took 260 ms and throughput saturated near 30 req/s, so 50
concurrent users queued past a 500 ms p95. Serving a cached dict removes
the SQL work from the hot path; serialization of the (small) payload stays
per-request and is measured well inside budget.
"""

from __future__ import annotations

import functools
import threading
import time
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

TTL_SECONDS = 300.0
MAX_ENTRIES = 512

_lock = threading.Lock()
_store: dict[str, tuple[float, Any]] = {}
# Monotonic generation bumped by invalidate(). A compute captures it under the
# lock and only writes its result back if no invalidation landed in between.
_generation = 0


def cached(label: str) -> Callable:
    """Cache an endpoint handler's return value under a parameterised key.

    The key is ``label`` plus every argument except the DB session, so
    different scopes (``?legislature=2024``) never collide. Exceptions are
    never cached — a failing compute stays failing until it succeeds.
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            parts = [repr(a) for a in args if not isinstance(a, Session)] + [
                f"{k}={v!r}" for k, v in sorted(kwargs.items()) if k != "db"
            ]
            key = f"{label}:" + "|".join(parts)
            now = time.monotonic()
            with _lock:
                hit = _store.get(key)
                if hit is not None and now - hit[0] < TTL_SECONDS:
                    return hit[1]
                # Snapshot under the lock: if an admin write invalidates while
                # the (slow) compute runs outside it, this generation goes
                # stale and the write-back below is suppressed (TOCTOU fix).
                generation = _generation
            value = fn(*args, **kwargs)
            with _lock:
                if generation == _generation:
                    if len(_store) >= MAX_ENTRIES:
                        # Dicts preserve insertion order: drop the oldest third.
                        for stale in list(_store)[: MAX_ENTRIES // 3]:
                            del _store[stale]
                    _store[key] = (time.monotonic(), value)
            return value

        return wrapper

    return decorator


def invalidate() -> None:
    """Drop every cached value (call after any admin write).

    Bumping the generation also discards any value computed *before* this call
    that is still in flight, so it cannot be stored with a fresh timestamp
    afterwards and served for another TTL window.
    """
    global _generation
    with _lock:
        _generation += 1
        _store.clear()
