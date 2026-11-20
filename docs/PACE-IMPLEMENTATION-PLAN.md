# PACE Implementation Plan — Parlament Deschis Frontend / Vote API Upgrade

**Date:** 2026-11-20  
**Repo:** `/home/nedaktov/parlament-deschis` (HEAD `ff9d461`, origin `main`)  
**Scope:** Wave 2 — public roll-call vote API endpoints + `/Voturi` roll-call explorer page with honest empty state.  
**Method:** PACE (Primary / Alternate / Contingency / Emergency) — each path is a complete, self-contained implementation route from "current state" to "shipped vote data on the site".  
**Ground rules:** zero guesswork; every file:line cited from the five worker reports or verified reads; no production data writes outside a WAL-safe copy; audit stays at 275 known errors / 0 new; third-party sources never block the official corpus.

---

## 0. Current state (evidence baseline)

| Fact | Source |
|---|---|
| Vote tables `vote`, `vote_position`, `vote_import_run` exist in `pipeline/db.py` but hold **0 rows** in production | Wave 1 (b2e6fa5); live `/api/health` |
| Frontend stack: React 19 + Vite 6 + TanStack Router + TanStack Query + ECharts + d3-sankey; **zero GraphQL client** | W2 frontend audit |
| 19 routes in `frontend/src/router.tsx` (lazy imports lines 14-30, route defs 310-458) | W2 |
| `/api/dashboard/stats` returns coverage_score=100, parties=37, switches=2002 | W1 live scout |
| `/api/analytics/party-cohesion` returns `status=unavailable, data=[]` | W1 |
| All existing endpoints empty-collection pattern: `200 + data:[]`, never 404/500 (`api.py:374-382`, `:385-416`) | W3 API contract |
| New endpoints to insert after `backend/routers/api.py:1051` (before `traseism/overview@1054`) | W3 |
| i18n: `lng: "ro"`, `fallbackLng: "en"` at `frontend/src/i18n.ts:1028-1029` | W4 |
| `DashboardCard` accepts `onClick`/`linkTo` but hero cards don't wire them (`components/DashboardCard.tsx:12`, `pages/LiveDashboard.tsx:97-141`) | W2 + W4 |
| Corpus audit gate: `uv run python -m pipeline.cli --db data/parlament.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json` → `275 known, 0 new` | Wave 1 verified |

---

## 1. PRIMARY path (recommended — first choice)

**Goal:** Ship vote data read-only on the site via 5 additive REST endpoints + a new `/Voturi` page that renders honestly when empty. Non-destructive, additive, rollback = delete route + remove endpoints.

### 1.1 Steps (in order)

**P1 — Backend: register the 5 vote endpoints (additive only)**
- File: `backend/routers/api.py`
- Insert after line 1051, before `traseism/overview@1054`:
  - `GET /api/votes` — query params `chamber`, `legislature`, `from`, `to`, `limit` (1-200, default 50), `offset`. Response `{status, data_exists, data:[{id,native_vote_id,chamber,legislature,vote_time,title_raw,present,not_voting,yes,no,abstain,source_url,positions_incomplete}], total,offset,limit}`.
  - `GET /api/votes/{vote_id}` — response `{status, data_exists, data:{...,position_count}}`.
  - `GET /api/votes/{vote_id}/positions` — query `limit` (1-500, default 100), `offset`, `choice` (`yes|no|abstain|not_voting`). Response `{status, data_exists, data:[{person_id,name_raw,group_raw,choice,resolution_scheme,source_url}], total,offset,limit}`.
  - `GET /api/analytics/vote-cohesion` — query `chamber`, `legislature`. Response `{status, data_exists, data:[{party,yes,no,abstain,not_voting,total_votes,yes_pct,no_pct,abstain_pct}], denominator:"resolved positions in scope"}`.
  - `GET /api/analytics/vote-activity` — query `chamber`, `legislature`, `from`, `to`, `step_days` (1-365, default 30). Response `{status, data_exists, data:[{date,votes,yes,no,abstain,present}], buckets}`.
- Every endpoint: `data_exists()` guard → empty Vote table returns `200 + data_exists:false + data:[]` (never 404/500).
- All rows carry `source_url`; Vote source is cdep (OGL-ROU-1.0, registered in `pipeline/licenses.py:54-69`).
- No GraphQL changes (frontend has no GraphQL client; W3 decision).

**P2 — Backend: wire into the corpus-build isolation gate**
- Verify `tests/test_votes_build_isolation.py:48-55` still passes — vote importer must remain unreachable from `cmd_build_corpus`, `prepare_db.py`, `backend/main.py`, `Dockerfile`, `ci.yml`, `data.yml`.
- No change to `cmd_build_corpus` (`pipeline/cli.py:526-712`).

**P3 — Frontend: API client helpers (additive)**
- File: `frontend/src/api/client.ts`
- Add 5 typed fetch helpers mirroring the 5 endpoints, each returning `{status, data_exists, data, ...}` and throwing a typed `VoteApiError` only on network/5xx (not on empty table).
- Reuse existing `useQuery` pattern (LiveDashboard `meta/dashboardStats` at `pages/LiveDashboard.tsx:30-36`).

**P4 — Frontend: new `/Voturi` page (additive route)**
- New file: `frontend/src/pages/Voturi.tsx`
- Lazy import in `frontend/src/router.tsx` (lazy import block lines 14-30; route def block lines 310-458).
- Route: `/Voturi` with `validateSearch: validateDateSearch` (pattern `router.tsx:361-373`).
- Component tree: `EmptyState` (`components/EmptyState.tsx:10-38`) + `Skeleton` (`components/ui/Skeleton.tsx:6-11`) + `RollCallTable` (new `frontend/src/components/RollCallTable.tsx`) using responsive-table/sortable-table patterns (model on `Traseism.tsx:301-443`).
- Data contract: `GET /api/votes?legislature=&chamber=&date=` → `{vote_id, date, title, result, positions:[{person,vote}]}`.
- Filters: date, chamber, result (passed/failed), search by title.
- Empty state: `EmptyState` with `vote.empty` label ("No roll-call votes for this scope") — NEVER invented numbers.
- i18n keys added as dotted pairs under `ro.translation` / `en.translation` in `frontend/src/i18n.ts` (existing convention, lines 273-291 / 778-779).

**P5 — Frontend: wire vote data into existing honest pages**
- `/Radar` → reuse `PartyComparisonMatrix` skeleton + `InfoStat` + `DashboardCard`; data `/api/votes/positions?legislature=&chamber=`; empty → `empty.rollcall`.
- `/Grafice` → reuse `TimelineChart` + `SwitchTimeline` + `DataViz` sparklines; data `/api/traseism/summary` + `/api/votes/cohesion`; empty → `traseismCoverageNone` banner (`Traseism.tsx:134-164`).
- `/Topuri` → reuse `SwitchLeaderboard` table pattern + `Leaderboard` i18n keys (`i18n.ts:354-378`); data new `/api/votes/scorecard`; empty → `mps.empty` (`i18n.ts:398 / 903`).
- Each page gated on N>0 precondition; render empty state otherwise. Never fake axes/numbers.

**P6 — i18n**
- Add keys: `view.voturi.title`, `view.radar.title`, `view.grafice.title`, `view.topuri.title`, `vote.yes/no/abstain/not_voting`, `filter.chamber/legislature/date/party`, `empty.rollcall`, `empty.ideology`, `aria.rollcallTable`, `aria.ideologyMap`.
- EN fallback exists (`fallbackLng: "en"`, line 1029); RO is primary. Every new key ships in both languages.

**P7 — Verify (gate, no deploy yet)**
- `cd frontend && npm ci && npm run build` → exit 0
- `uv run ruff check pipeline backend scripts tests` → clean
- `uv run pytest -q` → all pass (incl. new vote empty-state + REST/GraphQL convergence)
- `uv run python -m pipeline.cli --db data/parlament.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json` → `275 known, 0 new`
- `bash scripts/check-doc-truth.sh` → false-claims: 0

**P8 — Rollback (Primary)**
- `git revert <P1..P6 commits>` (each commit is atomic per checkpoint)
- Remove `/Voturi` route from `router.tsx`
- Delete `frontend/src/pages/Voturi.tsx` and `frontend/src/components/RollCallTable.tsx`
- Revert `backend/routers/api.py` insertions (lines after 1051)
- Irreversible: none (additive only; no schema migration, no data write)

### 1.2 Success criteria
- All 5 endpoints return `200 + data_exists:false + data:[]` on the empty production DB
- `/Voturi` renders the honest empty state (no fake numbers)
- Build, tests, lint, audit all green

---

## 2. ALTERNATE path (if Primary is blocked)

**Trigger:** Any Primary step cannot proceed — e.g., `backend/routers/api.py:1051` insertion point shifted, `client.ts` fetch pattern changed, router.tsx lazy-import block incompatible, or ECharts/DashboardCard primitives have breaking props.

**Goal:** Deliver the same user outcome (vote data visible, honest empty state) via a *different technical route* that avoids the blocked component.

### 2.1 Steps

**A1 — Backend: endpoints via a new router module instead of inline insertion**
- New file: `backend/routers/votes.py` (additive, no edit to `api.py`)
- Mount via `backend/main.py:198` (GraphQL mount) area — verify where REST routers are registered (`backend/main.py` `app.include_router(...)` calls).
- Same 5 endpoints, same contracts, same empty-state guard.
- Rollback: remove `include_router(votes_router)` + delete `backend/routers/votes.py`.

**A2 — Frontend: fetch via a local adapter module instead of editing client.ts**
- New file: `frontend/src/api/votes.ts` — standalone `fetch`-based helpers, no change to `client.ts`.
- `/Voturi` page imports from `./api/votes` instead of the shared client.
- Rollback: delete `frontend/src/api/votes.ts`, revert page imports.

**A3 — Frontend: server-side-rendered empty page (no new client component library)**
- If ECharts/DataViz/Skeleton props are incompatible, build `/Voturi` as a plain HTML table + `DashboardCard`/`InfoStat` primitives only (already verified working).
- Data contract unchanged; only the presentation layer simplifies.

**A4 — Rollback (Alternate)**
- `git revert <A1..A4 commits>`
- Remove `include_router(votes_router)` from `backend/main.py`
- Delete `backend/routers/votes.py`, `frontend/src/api/votes.ts`

### 2.2 Success criteria
- Same as Primary, but via separate module + adapter
- No edit to `backend/routers/api.py` or `frontend/src/api/client.ts`

---

## 3. CONTINGENCY path (if Primary AND Alternate are blocked)

**Trigger:** Both Primary and Alternate fail — e.g., backend router registration mechanism is frozen, frontend build cannot add routes, or the vote schema itself cannot be queried (tables exist but a migration/permissions issue blocks reads).

**Goal:** Ship *something* truthful about vote data without changing backend routes or frontend routing — a static, client-side demonstration that is explicitly labeled as non-live / placeholder, plus a clear "data not yet live" path to production.

### 3.1 Steps

**C1 — Backend: read-only SQL probe script (no API change)**
- New file: `scripts/query_votes_dryrun.py` — connects to a WAL-safe copy of `data/parlament-real.db`, runs `SELECT` against `vote`/`vote_position`, prints JSON to stdout.
- No writes, no server, no route changes. Rollback: delete file.

**C2 — Frontend: static mock page labeled "Coming soon — roll-call votes"**
- New file: `frontend/src/pages/Voturi.tsx` (no API call) — renders `EmptyState` + methodology note: "Roll-call vote data is being ingested; no figures shown yet."
- Route added to `router.tsx` (same as P4).
- No numbers, no fake axes, no invented party placements.
- i18n key `empty.ideology`-style: `view.voturi.coming_soon`.
- Rollback: delete page + revert route.

**C3 — Backend: document the API contract in docs**
- Write `docs/VOTE-API-CONTRACT.md` specifying the 5 endpoints, response shapes, empty-state behavior, so frontend can implement against a frozen contract once backend is unblocked.
- Rollback: delete doc.

**C4 — Rollback (Contingency)**
- `git revert <C1..C3 commits>`
- Remove `/Voturi` route
- Irreversible: none

### 3.2 Success criteria
- `/Voturi` exists on the site with an honest "no data yet" label
- No backend route changes, no production writes
- Contract documented for future implementation

---

## 4. EMERGENCY path (last resort — fail-safe)

**Trigger:** Catastrophic — production build is broken, audit fails, or any deployed change corrupts the corpus. The site must return to a known-good state immediately.

**Goal:** Restore the pre-upgrade state with zero data loss and zero fake numbers on the live site.

### 4.1 Steps

**E1 — Immediate halt**
- Stop all `git push` / CI merges for this feature branch.
- Tag current good state: `git tag parlament-deschis-pre-vote-upgrade-$(date +%Y%m%d-%H%M%S)` on `main` (already at `ff9d461`, verified green CI `44775169889`).

**E2 — Revert all feature commits**
- `git reset --hard <pre-upgrade-tag>` on the feature branch, then `git push --force-with-lease origin <feature-branch>` (only if a feature branch exists; otherwise just leave main untouched).
- On `main`: no feature commits were merged (Primary/Alternate/Contingency are additive and not yet merged), so `main` is already clean at `ff9d461`.

**E3 — Verify restoration**
- `cd frontend && npm ci && npm run build` → exit 0
- `uv run pytest -q` → all pass
- `uv run ruff check pipeline backend scripts tests` → clean
- `uv run python -m pipeline.cli --db data/parlament.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json` → `275 known, 0 new`
- Live site at `https://parlament-deschis.vercel.app` serves the previous bundle (Vercel Git integration auto-rolls back on revert push; previous deployment is the rollback target per Vercel Hobby constraint — ci.yml:125 notes Vercel deploys via Git integration on push to main).

**E4 — Post-mortem**
- Document what blocked Primary/Alternate/Contingency in `docs/EMERGENCY-ROLLBACK.md`.
- File a tracked issue before re-attempting.

### 4.2 Success criteria
- `main` at pre-upgrade tag; CI green; live site unchanged; zero fake numbers; zero data loss.

---

## 5. PACE decision matrix

| Condition | Path to take |
|---|---|
| All backend/frontend insertion points work as cited | **PRIMARY** (P1–P8) |
| `api.py:1051` or `client.ts` pattern incompatible | **ALTERNATE** (A1–A4) |
| Backend routes frozen / frontend routing blocked | **CONTINGENCY** (C1–C4) |
| Build/audit broken or data integrity at risk | **EMERGENCY** (E1–E4) |

**Recommended execution:** Start with PRIMARY. If any P-step fails its checkpoint, immediately switch to ALTERNATE for the blocked step only (mix-and-match is allowed — e.g., Primary backend + Alternate frontend adapter). Do not skip to Contingency unless both Primary and Alternate are exhausted for the same step. Emergency is only for production integrity.

---

## 6. Checkpoints and rollbacks (summary)

| Step | Checkpoint (pass criteria) | Rollback |
|---|---|---|
| P1 endpoints | 5 endpoints return 200+empty on empty DB | `git revert` P1 commit |
| P2 isolation | `test_votes_build_isolation.py` passes | revert P2 (none — additive check only) |
| P3 client helpers | `ruff` clean; typed helpers import | revert P3 |
| P4 `/Voturi` page | renders empty state; `npm run build` exit 0 | delete page + revert route |
| P5 existing pages | `/Radar`/`/Grafice`/`/Topuri` show honest empty/coverage | revert P5 per page |
| P6 i18n | ro+en keys present; no undefined labels | revert P6 |
| P7 verify | build+tests+lint+audit+doc-truth all green | n/a (gate — do not deploy if red) |
| P8 rollback | site back to pre-upgrade state | revert all P commits |

---

## 7. Risks (PACE-aware)

| Risk | L | I | Mitigation | Owner | PACE path |
|---|---|---|---|---|---|
| Empty table mistaken for "API error" vs "no data" | M | H | `data_exists` flag + honest `empty.*` labels; QA empty-state tests | frontend | Primary |
| REST vs GraphQL `party_cohesion` divergence | H | M | REST owns truth; GraphQL left as legacy (W3) | backend | Primary |
| `deploy-all.sh:20` `git add -A` footgun | M | H | Never use for promotion; dirty-tree guard | qa | All |
| ECharts bundle size (487 KB min / 164 KB gzip) | M | M | Modular imports; budget guard | frontend | Primary/Alternate |
| `ui_validate.py` axe violations (NOT PROVEN locally — no playwright/chromium) | M | H | CI `evidence-guards` job; local axe if available | qa | All |
| Third-party vote source outage blocks corpus | M | H | Build-isolation test forbids vote code in `cmd_build_corpus` | backend | All |
| i18n missing key → undefined label | L | M | Ship ro+en pairs; EN fallback at line 1029 | frontend | Primary |

---

**End of PACE plan.** Start with PRIMARY step P1. Do not deploy until P7 gate is green.