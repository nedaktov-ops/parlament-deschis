"""Load test for the transparency endpoints (Feature 15).

Spawns 50 concurrent workers; each cycles through the three hot endpoints
(/api/parties, /api/persons/{id}, /api/analytics/switch-leaderboard) for a
fixed number of rounds. Reports p50/p95/p99/max latency per endpoint and
overall, plus error counts. Target: p95 < 500 ms.

Usage:
    uv run python scripts/load_test.py [base_url] [workers] [rounds]
"""

from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

# A person id known to exist in the corpus (Tudor IONESCU, 6 committees).
PERSON_ID = "7ff93a68-a284-46a8-8571-3c2ab6f8aae3"

ENDPOINTS = [
    ("parties", "/api/parties"),
    ("person", f"/api/persons/{PERSON_ID}"),
    ("leaderboard", "/api/analytics/switch-leaderboard?limit=20"),
]


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = (len(ordered) - 1) * pct / 100.0
    lo = int(k)
    hi = min(lo + 1, len(ordered) - 1)
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


def worker(base_url: str, rounds: int) -> list[tuple[str, float, int]]:
    """One simulated user: `rounds` passes over all endpoints."""
    results: list[tuple[str, float, int]] = []
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        for _ in range(rounds):
            for name, path in ENDPOINTS:
                start = time.perf_counter()
                try:
                    resp = client.get(path)
                    elapsed = (time.perf_counter() - start) * 1000
                    results.append((name, elapsed, resp.status_code))
                except Exception:  # noqa: BLE001 - report as failure
                    elapsed = (time.perf_counter() - start) * 1000
                    results.append((name, elapsed, -1))
    return results


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8931"
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 6

    # Warm-up: one request per endpoint so cold caches don't skew results.
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        for _, path in ENDPOINTS:
            client.get(path)

    print(f"Load test: {workers} workers x {rounds} rounds x {len(ENDPOINTS)} endpoints")
    print(f"Target: p95 < 500 ms | {base_url}")

    wall_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(worker, base_url, rounds) for _ in range(workers)]
        all_results = [r for f in futures for r in f.result()]
    wall = time.perf_counter() - wall_start

    total = len(all_results)
    errors = [r for r in all_results if r[2] != 200]
    print(
        f"\nCompleted {total} requests in {wall:.1f}s "
        f"({total / wall:.0f} req/s), errors: {len(errors)}"
    )
    if errors:
        for name, _ms, code in errors[:10]:
            print(f"  ERROR {name}: status {code}")

    ok = True
    for name, _ in ENDPOINTS:
        lat = [ms for n, ms, code in all_results if n == name and code == 200]
        if not lat:
            print(f"{name}: no successful requests")
            ok = False
            continue
        p50 = percentile(lat, 50)
        p95 = percentile(lat, 95)
        p99 = percentile(lat, 99)
        flag = "PASS" if p95 < 500 else "FAIL"
        if p95 >= 500:
            ok = False
        print(
            f"{name:>12}: n={len(lat):4d} p50={p50:7.1f} p95={p95:7.1f} "
            f"p99={p99:7.1f} max={max(lat):7.1f} ms [{flag}]"
        )

    all_lat = [ms for _, ms, code in all_results if code == 200]
    overall_p95 = percentile(all_lat, 95)
    overall_flag = "PASS" if overall_p95 < 500 else "FAIL"
    if overall_p95 >= 500:
        ok = False
    print(
        f"{'OVERALL':>12}: n={len(all_lat):4d} p50={percentile(all_lat, 50):7.1f} "
        f"p95={overall_p95:7.1f} p99={percentile(all_lat, 99):7.1f} "
        f"max={max(all_lat):7.1f} ms [{overall_flag}]"
    )
    print(f"\n{'LOAD TEST PASS' if ok and not errors else 'LOAD TEST FAIL'}")
    return 0 if ok and not errors else 1


if __name__ == "__main__":
    sys.exit(main())
