"""Unit tests for the read-only result cache (P0-F).

These exercise the generation guard that stops a slow, in-flight query from
writing a stale value back into the cache after an admin ``invalidate()``.
No DB or HTTP layer is involved.
"""

from __future__ import annotations

import backend.cache as cache


class _Clock:
    """Minimal stand-in for ``cache.time`` with a controlled monotonic clock."""

    def __init__(self, t: float) -> None:
        self.t = t

    def monotonic(self) -> float:
        return self.t


def test_invalidate_during_compute_suppresses_stale_write_back(monkeypatch):
    """A result computed before an invalidate() must not be cached afterwards.

    Reproduces the TOCTOU: the wrapper snapshots the generation under the lock,
    computes outside it, and only stores if the generation is unchanged. An
    admin write in between must leave the cache empty so the next GET recomputes
    against the new data.
    """
    cache.invalidate()
    clock = _Clock(1000.0)
    monkeypatch.setattr(cache, "time", clock)

    # 1) Seed a value at t=1000.
    assert cache.cached("gen-unit")(lambda: "old")() == "old"

    # 2) Let it expire so the next call is forced to recompute.
    clock.t += cache.TTL_SECONDS + 1

    # 3) A slow recompute during which an admin write calls invalidate().
    def slow_compute():
        cache.invalidate()  # admin write lands mid-flight
        return "stale"

    # This caller still receives its own computed value...
    assert cache.cached("gen-unit")(slow_compute)() == "stale"

    # ...but the stale value must NOT be cached: the next GET recomputes "new".
    assert cache.cached("gen-unit")(lambda: "new")() == "new"


def test_cached_keeps_ttl_semantics(monkeypatch):
    """The generation guard must not change normal TTL expiry behaviour."""
    cache.invalidate()
    clock = _Clock(1000.0)
    monkeypatch.setattr(cache, "time", clock)

    calls = {"n": 0}

    def compute():
        calls["n"] += 1
        return calls["n"]

    fn = cache.cached("ttl-unit")(compute)
    assert fn() == 1
    assert fn() == 1  # served from cache
    assert calls["n"] == 1

    clock.t += cache.TTL_SECONDS + 1
    assert fn() == 2  # expired -> recompute
    assert calls["n"] == 2
