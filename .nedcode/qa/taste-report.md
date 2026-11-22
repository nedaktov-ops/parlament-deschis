# Parlament Deschis — QA Sentinel report (vote-ingestion expansion verification)

Repo: /home/nedaktov/parlament-deschis (main branch, HEAD ff9d461)
Worker: @worker-qa-sentinel (read-only verification agent)
DB under test: data/parlament-real.db (78 votes, 10,307 positions; +48 Dec 10-11 2024 +26 Dec 17 2024 = 78 total)
Local API target: http://127.0.0.1:8001 (port 8000 occupied by a Docker uvicorn container returning SPA 404s — stale/different code, not the working tree)
Live API (context, not tested): https://parlament-deschis.onrender.com
Raw verify output: .nedcode/qa/verify-project.log (this report is the summary; no separate verify script exists in this repo, so the check outputs below are the raw artifacts)

GATE: CONDITIONAL-GO — pytest 355 passed / 0 failed / 0 errors ✓; audit-corpus --strict 275 known errors / 0 new errors ✓; ruff check clean, exit 0 ✓; frontend build exit 0 ✓; API 5/6 endpoints return 200 + real data ✓. OPEN FAIL (NOT waived): GET /api/votes/scorecard returns data_exists:false/data:null because backend/routers/api.py:1319 declares the route as "/api/votes/scorecard" on a router already prefixed "/api" — real scorecard data is at /api/api/votes/scorecard (double-/api prefix, pre-existing routing bug unrelated to vote ingestion). NOT PROVEN: ui_validate.py/axe scan and live render.com API (no playwright/chromium in this runner; live API not exercised). Any FAIL = NO-GO per verification-matrix.md §6; this FAIL is pre-existing and out of scope for read-only QA to fix.

## AP-1 — Full test suite (`uv run pytest -q`)
Result: 355 passed, 0 failed, 0 errors, 29.04s.
Raw artifact: terminal output, summary line `355 passed, 1 warning in 29.04s`.
Warning (pre-existing, not a failure): StarletteDeprecationWarning — `httpx` with `starlette.testclient` is deprecated; install httpx2 instead (fastapi/testclient.py:1).
Notes: Baseline in verification-matrix.md was 342 passed; the vote-ingestion work added 13 passing tests. No new failures.

## AP-2 — Audit suite (`audit-corpus --strict --baseline ...`)
Command: `uv run python -m pipeline.cli --db data/parlament-real.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json`
Result: 275 errors, 182 warnings → `275 known errors, 0 new errors, 0 resolved baseline findings, 0 baseline findings not evaluated`.
Requirement (must be): 275 known errors, 0 new errors → SATISFIED exactly.
Warnings are pre-existing "vote_evidence deputies 2020 : incomplete member-level positions" notices (e.g. votes 34537, 34540, 34542…), not new errors.

## AP-3 — Ruff check (`uv run ruff check pipeline backend scripts tests`)
Result: `All checks passed!`, exit code 0. No errors, no warnings.

## AP-4 — API endpoints (local backend on http://127.0.0.1:8001)
Started with `uv run python -m pipeline.cli serve --host 127.0.0.1 --port 8001` (pid 2370335; log /tmp/opencode/qa-backend.log), DB = data/parlament-real.db.

| Endpoint | Status | Body summary |
|---|---|---|
| GET /api/votes | 200 | `{"status":"ok","data_exists":true,"data":[...],"total":...}` — returns votes incl. native_vote_id 34545 (17.12.2024), 34543, 34541; data_exists true ✓ |
| GET /api/votes/34539 | 200 | Vote 34539 "Ordinea de zi", 17.12.2024 13:01, present 278/yes 257/no 19, positions_incomplete false, position_count 0, data_exists true ✓ |
| GET /api/votes/34539/positions | 200 | `data_exists:false,"data":[],"total":0` — vote 34539 has no stored positions (position_count 0); correct empty-shape, not 500 ✓ |
| GET /api/analytics/vote-cohesion | 200 | data_exists true; per-party rows (AUR 1847, PNL 2987, PSD 5475, Minoritati 401, Neafiliati 2205, SOS RO 12, UDMR 790, …) with yes_pct/no_pct/abstain_pct ✓ |
| GET /api/analytics/vote-activity | 200 | data_exists true; 7 buckets incl. 11.12.2024 (48 votes) and 17.12.2024 (26 votes) matching the Dec ingestion ✓ |
| GET /api/votes/scorecard | 200 | `data_exists:false,"data":null` — MISROUTED. Treats "scorecard" as `{vote_id}` under /votes/{vote_id}; no vote has native_vote_id "scorecard". Real scorecard data (loyalty/rebellion/participation per person, e.g. Cătălina CIOFU PNL 120 votes 99.2% loyalty) is at GET /api/api/votes/scorecard → 200, data_exists true. Root cause: backend/routers/api.py:1319 `@router.get("/api/votes/scorecard")` on a router already prefixed `/api` → double `/api`. Pre-existing routing bug, NOT caused by vote ingestion, NOT waived, NOT fixed (read-only). |

## AP-5 — Frontend build (`cd frontend && npm run build`)
Result: `✓ built in 6.58s`, exit code 0.
Output: ~40 chunks emitted to dist/assets/ (index-D61EXxHz.js 503.83 kB min / 153.57 kB gzip; largest installCanvasRenderer-BoCEC6_w.js 460.00 kB).
Warning only (not a failure): `(!) Some chunks are larger than 500 kB after minification` — code-split suggestion; build still exits 0.

## Open FAILs (not waived)
1. GET /api/votes/scorecard does not return real scorecard data at its documented path (double-/api prefix, backend/routers/api.py:1319). Real data reachable at /api/api/votes/scorecard.

## NOT PROVEN (could not run)
- ui_validate.py axe-core scan / JS-error check on vote routes — runner lacks playwright/chromium (verification-matrix.md §6 item 6 flags this NOT PROVEN locally).
- Live API https://parlament-deschis.onrender.com not exercised (only local backend tested).
- GraphQL ↔ REST convergence for vote-cohesion (verification-matrix.md risk #2).
- scripts/check-doc-truth.sh and scripts/ui_validate.py not run (not in the 5 ACTION POINTS).

## Assumed facts
- Working DB is data/parlament-real.db (mission-specified); verification-matrix.md baseline references data/parlament.db — audit was run against parlament-real.db per the mission.
- Port 8000 is occupied by a Docker container (uvicorn backend.main:app, image /app) returning SPA `{"detail":"not found"}` for /api/* — treated as stale/different code; local working-tree backend verified on 8001.
- Vote 34539 (Dec 17 2024) legitimately has position_count 0 / no positions; empty /positions response is correct behavior, not a bug.
- No source code, database records, or API contracts were modified (read-only).

## Voice card / deal
Parlament Deschis is the Romanian Parliament transparency tracker (dated, source-cited group/committee memberships + roll-call votes). The deal for this QA pass: after the vote-ingestion expansion (78 votes), prove the full stack still works end-to-end — tests, audit baseline, lint, API surface, frontend build — without changing anything. All five ACTION POINTS executed; four green, one pre-existing routing FAIL reported open, two items NOT PROVEN.
