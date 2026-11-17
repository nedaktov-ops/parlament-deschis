# 1. In-process result cache for hot API endpoints

- **Status:** Accepted (implemented)
- **Date:** 2026-11-17
- **Deciders:** backend pipeline owners
- **Related:** `backend/cache.py`, `backend/routers/api.py`, `backend/routers/exports.py`,
  `docs/STRATEGY-TRANSPARENCY.md` (performance validation)

## Context

Several analytics endpoints are synchronous FastAPI handlers that run in a
threadpool behind uvicorn's GIL. Measured on 8 cores, a cold `/api/parties` took
260 ms and throughput saturated near 30 req/s, so 50 concurrent users queued
past a 500 ms p95 target. The bottleneck is repeated SQL over a dataset that is
**pinned per release and read-only at runtime** — the same value is recomputed
for every request.

A subset of results is mutable only when an admin explicitly triggers a
recompute (waves, exports). Those writes can race with an in-flight compute: a
slow calculation started before invalidation must not be written back with a
fresh timestamp afterwards and served for another full TTL window (TOCTOU).

HTTP edge caching is a separate concern. Mutable analytics responses use
`no-store` headers; this decision concerns the in-process application cache,
not CDN behaviour.

## Decision

Use a small in-process TTL cache (`backend/cache.py`, exposed as `cache_result`)
for read-only endpoint results:

- A parameterised key: decorator label plus every argument except the SQL
  `Session`, so scopes such as `?legislature=2024` never collide.
- `TTL_SECONDS = 300`, `MAX_ENTRIES = 512`; when full, drop the oldest third
  (dict insertion order).
- Exceptions are never cached — a failing compute stays failing until it
  succeeds.
- A generation counter guarded by a lock: a compute captures the generation
  under the lock and writes back only if no invalidation landed in between.
  `invalidate()` bumps the generation and clears the store; every admin write
  path must call it.
- A release restarts the process, which empties the cache, so it can never
  serve data from a different release.

## Consequences

**Positive**

- SQL work leaves the hot path; serialization of the small payload remains
  per-request. Validation measured p95 332 ms at 50 concurrent users (from
  5262 ms before batching plus caching), 900 requests, 0 errors.
- The generation guard prevents a stale in-flight result from surviving an
  admin write.
- Zero new infrastructure; safe on the free-tier single-process deployment.

**Negative / obligations**

- Up to 5 minutes of staleness is possible after an admin recompute if a write
  path forgets to call `invalidate()`. This is a correctness obligation, not
  an optional optimization.
- Cache state is per process and is not shared across replicas; each replica
  maintains its own copy.
- Memory is bounded but nonzero; entries hold the full response payload.
- "On release" freshness, not real-time: a release restart is the hard cache
  boundary, the TTL only bounds staleness between admin writes.

## Alternatives

- **No cache (recompute per request):** rejected — measured p95 5262 ms, far
  above the 500 ms target.
- **HTTP/CDN caching only:** rejected — mutable admin-triggered results would
  be cached at the edge; mutable analytics are deliberately `no-store`.
- **Shared persistent store (e.g. Redis):** rejected — extra service and cost
  on constrained hosts for a read-only, single-process dataset.
- **Longer TTL:** rejected — lengthens the staleness window after writes.
- **Per-request cache-busting query strings:** rejected — defeats caching
  without fixing cacheability semantics (remediation strategy §4).
