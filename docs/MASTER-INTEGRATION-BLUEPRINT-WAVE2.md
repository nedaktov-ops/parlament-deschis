# Master Integration Blueprint — Wave 2 (Frontend / Vote API)

**Date:** 2026-11-20  
**Repo:** `/home/nedaktov/parlament-deschis` (HEAD `752eff6`, origin `main`)  
**Author:** Master Supervisor (integrated from five worker reports)  
**Status:** Wave 2 PRIMARY path complete and pushed; Waves 2-P5 / 3 / 4 planned below.  
**Method:** PACE (Primary / Alternate / Contingency / Emergency); zero guesswork; every file:line cited from verified worker evidence or direct reads.

---

## 0. Ground-truth baseline (from worker reports + direct reads)

| Fact | Evidence |
|---|---|
| Vote tables `vote`, `vote_position`, `vote_import_run` exist; 0 rows in production | Wave 1 (b2e6fa5); live `/api/health` |
| Live site `https://parlament-deschis.vercel.app` — SPA shell; all routes return client-rendered shell | W1 live-ui-scout |
| 13 API endpoints on render; `/api/dashboard/stats`: persons=3388, memberships=7349, switches=2002, committees=26, legislatures=20, parties=37, coverage_score=100 | W1 |
| `/api/parties`: 37 parties with `total_members`, `switches_in`, `color` (PSD=1023) | W1 |
| `/api/traseism/overview`, `/summary`, `/switches` (1217 rows); `/api/analytics/switch-leaderboard` | W1 |
| `/api/committees`: 26 but all `party=null` (shell-only) | W1 |
| `/api/analytics/party-cohesion`: `status=unavailable, data=[]` | W1 |
| Routes `/Județe`, `/Legi`, `/Pensii`, `/Quiz`, `/Întreabă 281`, `/Ghid`, `/press` have NO matching API endpoints (dead/unimplemented) | W1 |
| Frontend: React 19 + Vite 6 + TanStack Router + TanStack Query + ECharts + d3-sankey; **zero GraphQL client** | W2 |
| 19 routes in `frontend/src/router.tsx` (lazy imports lines 14-30, route defs 310-458, routeTree 460-480) | W2 |
| `LiveDashboard.tsx` hero cards 97-141: `DashboardCard` accepts `onClick`/`linkTo` (line 12) but cards don't wire them | W2 + W4 |
| Reusable primitives: `PartyComparisonMatrix`, `SankeyFlow`, `TimelineChart`, `MembershipGantt`, `SwitchTimeline`, `DataViz`, `PartyNetwork`, `Hemicycle`, `AgeDistributionRadial`, `DashboardCard`, `InfoStat` | W2 |
| `frontend/src/api/client.ts`: plain `fetch` (line 268-287), TanStack Query | W2 |
| `frontend/src/i18n.ts`: `lng: "ro"`, `fallbackLng: "en"` (lines 1028-1029) | W2 / P4 |
| Corpus audit baseline: `275 known errors, 0 new` (includes new `vote_evidence` check) | Wave 1 verified |
| Build-isolation test forbids vote code in `cmd_build_corpus`, `prepare_db.py`, `backend/main.py`, `Dockerfile`, `ci.yml`, `data.yml` | Wave 1 |
| `.gitignore`: `data/parlament.db`, `data/parlament-real.db` are gitignored release artifacts | Wave 1 |

---

## 1. Red-team corrections (assumptions overturned by evidence)

| # | Old assumption | Verified truth | Consequence |
|---|---|---|---|
| RC-01 | Frontend uses GraphQL | **Zero GraphQL client** (grep → 0); plain `fetch` + TanStack Query | All new vote endpoints are REST-only under `/api`; GraphQL left frozen |
| RC-02 | `/Radar`, `/Grafice`, `/Topuri` routes exist | **Missing from `router.tsx`** — not in route table | New routes must be added (lazy import + route def + routeTree) |
| RC-03 | `/api/analytics/party-cohesion` available | Returns `status=unavailable, data=[]` | REST owns truth; GraphQL `party_cohesion` left as legacy |
| RC-04 | `data/parlament-real.db` is in the repo | **Gitignored release artifact** | CI creates empty DB as side effect; corpus-based tests must skip when absent |
| RC-05 | `Vote.id` / `VotePosition.id` are Integer PKs | Repo uses `String(36)` UUID PKs throughout | Models follow repo convention |
| RC-06 | Nominal token `-` means abstain | Vote 37526: `NU_AU_VOTAT=1`, `AU_VOTAT_AB=0`, exactly one `-` → **present but did not vote** | `normalize_choice("-") == "not_voting"` |
| RC-07 | cdep XML is ISO-8859-2 | Prolog claims ISO-8859-2 but **bytes are UTF-8** | `decode_xml_bytes()` tries UTF-8 first |
| RC-08 | cdep day fixture 5,394 bytes | Live page **5,174 bytes** | Manifest SHA-256 is authority, not hardcoded sizes |
| RC-09 | 281.ro is the target repo | **Separate live product; no local codebase** | All implementation targets `parlament-deschis`; 281.ro = external CC-BY source only |

---

## 2. Agent Operating Recipes

Each recipe is copy-paste-ready as a system prompt for its agent. All workers were already executed read-only; recipes are retained for reuse across waves.

### 2.1 @supervisor-architect (Master Supervisor)

**Role:** Integrates worker output into blueprints; owns red-team corrections, wave roadmap, checkpoints, rollbacks; gates every checkpoint.

**Mission:** Produce the integrated execution document; verify every worker claim against actual files/lines; assign ownership of each checkpoint; decide PACE path per step; record the execution record.

**Exact inputs:** worker reports (W1–W5), repo at `/home/nedaktov/parlament-deschis`, `docs/MASTER-INTEGRATION-BLUEPRINT.md` (Wave 1), `docs/PACE-IMPLEMENTATION-PLAN.md`.

**Files/lines to read (before finalizing):** `backend/routers/api.py:961-1051` (dashboard stats, insertion point at 1051), `frontend/src/router.tsx:310-480` (route table), `frontend/src/api/client.ts:266-334` (api object), `frontend/src/i18n.ts:385-414 & 915-927` (i18n blocks), `pipeline/db.py:351-434` (vote models), `pipeline/votes.py` (importer), `pipeline/licenses.py` (register), `tests/test_votes_build_isolation.py:48-55` (isolation).

**Tool protocol:** read-only for reconnaissance; for implementation, use `write`/`edit` only on exact cited lines; run `uv run ruff`, `uv run pytest -q`, `cd frontend && npm ci && npm run build` as gates; never `git add -A`.

**Prohibited assumptions:** GraphQL client exists; vote table has rows; `/Radar`/`/Grafice`/`Topuri` routes exist; `data/parlament-real.db` is tracked.

**I/O contract:** Output = Markdown blueprint with sections: red-team corrections, recipes, wave roadmap (Wave→Phase→Action Point→Checkpoint→Rollback), risk register, day-1 checklist. No TBD placeholders.

**Verification checklist:** every file:line cited from an actual read; every checkpoint has raw-evidence expectations + exact rollback; every external table gated by licence CHECK + export guard.

**Decision rights:** selects PACE path per step; approves merge to main only after P7 gate green.

**Definition of done:** blueprint file written; Wave 2 PRIMARY implemented + pushed + CI green; Waves 2-P5/3/4 roadmap complete.

**Escalation triggers:** build/audit broken; production data integrity at risk; third-party outage threatens corpus build.

**Reusable prompt:** "You are @supervisor-architect. Integrate the five worker reports into docs/MASTER-INTEGRATION-BLUEPRINT-WAVE2.md. Cite exact file:line. No TBD. PACE method. Zero guesswork."

---

### 2.2 @worker-live-ui-scout (UX researcher)

**Role:** Live-site reconnaissance.

**Mission:** Inventory the live user-facing surface of Parlament Deschis so the team can design statistical views that expose enriched data.

**Exact inputs:** `https://parlament-deschis.vercel.app`, `https://parlament-deschis.onrender.com`, `/openapi.json`, `/docs`.

**Files/URLs to read:** site shell + each route; OpenAPI spec (30 paths); API endpoints behind each widget.

**Tool protocol:** `webfetch` read-only on the two hosts only; no network beyond; record real Romanian labels and actual JSON keys.

**Prohibited assumptions:** what a page "probably" shows; Cmd+K search behaviour (unobservable from shell); dead/unimplemented routes (verify by fetching).

**I/O contract:** max 110 lines: route→sections→API→metric labels table; widget inventory (name, number, denominator, honest vs misleading); nav + Cmd+K; gaps with URLs; 10 high-value view-addition spots.

**Verification checklist:** every claim backed by a fetched URL; unfetched marked UNVERIFIED with reason.

**Decision rights:** none (recon only).

**Definition of done:** report delivered within line cap; no speculation.

**Escalation triggers:** endpoint returns non-200; OpenAPI unavailable.

**Reusable prompt:** "You are @worker-live-ui-scout. READ-ONLY. Fetch https://parlament-deschis.vercel.app routes and https://parlament-deschis.onrender.com API/OpenAPI. Deliver max-110-line inventory table. No speculation."

---

### 2.3 @worker-frontend-code-audit (explore)

**Role:** Local frontend exact-line audit.

**Mission:** Map the exact frontend code surface (routes, pages, components, chart primitives, API client, i18n, defects) so the team knows exactly which files/lines to touch.

**Exact inputs:** all paths under `frontend/src/`.

**Files/lines to read:** `router.tsx` (14-480), `pages/LiveDashboard.tsx` (97-216), `pages/*.tsx` (18 files), `components/` primitives, `api/client.ts`, `i18n.ts`.

**Tool protocol:** read-only; grep for chart usage (ECharts, d3-sankey, recharts → 0); cite exact file:line.

**Prohibited assumptions:** GraphQL exists; page sections not read in full are verified.

**I/O contract:** max 110 lines: route table; pages inventory; chart primitives inventory with props; API client shape; i18n structure; defects with file:line; insertion points for new routes.

**Verification checklist:** every claim backed by file:line actually read; unread marked UNVERIFIED.

**Decision rights:** none.

**Definition of done:** audit delivered; all 18 pages listed; all primitives catalogued.

**Escalation triggers:** cannot read a file; build fails on read.

**Reusable prompt:** "You are @worker-frontend-code-audit. READ-ONLY. Map frontend/src exactly: router.tsx routes, pages, components, api/client.ts, i18n.ts. Cite file:line. Max 110 lines."

---

### 2.4 @worker-stats-api-contract (backend architect)

**Role:** REST API contract design.

**Mission:** Design the REST contracts exposing enriched vote/statistical datasets, with exact insertion points and honest-coverage rules.

**Exact inputs:** `backend/routers/api.py`, `backend/graphql/schema.py`, `pipeline/db.py`, `pipeline/votes.py`, `pipeline/licenses.py`, `frontend/src/api/client.ts`.

**Files/lines to read:** `api.py:961-1051` (insertion point 1051), `:374-382 & :385-416` (empty-collection pattern), `:804-822` (party-cohesion unavailable), `schema.py:371-466 & :583` (GraphQL), `client.ts:266-334` (fetch pattern).

**Tool protocol:** read-only; cite exact file:line; no guessed table columns (Vote/VotePosition fields known from `db.py:351-412`).

**Prohibited assumptions:** GraphQL client will be adopted; endpoint paths are free-form; empty table → 404/500.

**I/O contract:** max 110 lines: GraphQL stay-REST decision justified; 5 endpoints with path/method/params/response schema/insertion line; honest-coverage contract; party-cohesion divergence fix; endpoint→page mapping.

**Verification checklist:** every path/line/key from actual reads; empty-table → `200 + data_exists:false + data:[]`.

**Decision rights:** adopts stay-REST (matches existing stack).

**Definition of done:** contract design delivered; insertion point exact.

**Escalation triggers:** `api.py:1051` shifted; frontend build cannot add routes.

**Reusable prompt:** "You are @worker-stats-api-contract. READ-ONLY. Design 5 REST vote endpoints inserted after api.py:1051. Empty table → 200+empty. Stay REST-only. Max 110 lines."

---

### 2.5 @worker-ui-visual-design (UI designer)

**Role:** Statistical view design.

**Mission:** Specify new statistical views exposing enriched data, with component trees, layout, colour semantics, filters, accessibility, RO/EN i18n, and data preconditions.

**Exact inputs:** `frontend/src/components/ui/`, `frontend/src/components/` primitives, `frontend/src/pages/{Radar,Grafice,Topuri,Traseism}.tsx`, `frontend/src/i18n.ts`, `frontend/src/router.tsx`, W1 report.

**Files/lines to read:** primitive props (`PartyComparisonMatrix.tsx:7-17`, `TimelineChart.tsx:35-57`, `DataViz.tsx:1-155`, `DashboardCard.tsx:12 & 99-102`, `InfoStat.tsx:20-32`), `EmptyState.tsx:10-38`, `Skeleton.tsx:6-11`.

**Tool protocol:** read-only; cite file:line for reuse points.

**Prohibited assumptions:** vote data exists (tables empty); new type scale needed; party hexes invented.

**I/O contract:** max 110 lines: design anchors; 5 view specs (name, route, purpose, component tree, data contract, filters, empty state, a11y, responsive); precondition per view; pages needing no change vs fix; i18n plan.

**Verification checklist:** every component path from actual reads; every view lists data precondition (N>0); no fake numbers; concrete a11y requirements.

**Decision rights:** none (recommends; supervisor decides).

**Definition of done:** spec delivered; preconditions explicit; colour semantics reuse `party.color`.

**Escalation triggers:** primitive props incompatible; i18n key collision.

**Reusable prompt:** "You are @worker-ui-visual-design. READ-ONLY. Spec 5 statistical views with component trees, data contracts, preconditions (N>0), a11y, i18n keys. Max 110 lines."

---

### 2.6 @worker-qa-evidence (QA reviewer)

**Role:** Verification matrix.

**Mission:** Build the verification matrix: what to test, a11y/performance regression risk, exact rollback per step.

**Exact inputs:** `tests/` structure, `.github/workflows/ci.yml`, `scripts/verify-deploy.sh`, `scripts/deploy-all.sh:20-21`, `frontend/` test setup.

**Files/lines to read:** `ci.yml` jobs; `deploy-all.sh:20-21` (git add -A footgun + hardcoded commit); `test_graphql_convergence.py:221` (empty DB → `[]`); `test_votes_build_isolation.py:48-55`; `ui_validate.py:1-147` (axe-core target 0).

**Tool protocol:** read-only; cite file:line.

**Prohibited assumptions:** data exists in production (vote tables empty); playwright/chromium available locally (NOT PROVEN).

**I/O contract:** max 110 lines: test matrix table; a11y checks; performance budget; risk register (≥8 risks); rollback per step; go/no-go gate with numeric criteria.

**Verification checklist:** every test path from actual reads; rollback commands are real git/cli commands; every gate numeric.

**Decision rights:** none (recommends gate).

**Definition of done:** matrix delivered; gate line explicit; NOT PROVEN items marked.

**Escalation triggers:** ui_validate cannot run locally; audit baseline drifts.

**Reusable prompt:** "You are @worker-qa-evidence. READ-ONLY. Build verification matrix: test matrix, a11y, perf, risk register, rollback per step, go/no-go gate. Max 110 lines."

---

## 3. Wave-based execution roadmap

Exactly four waves. Wave 1 done. Wave 2 PRIMARY complete; P5 pending. Waves 3–4 planned.

### Wave 1 (DONE) — Governance, licence register, vote importer (dry-run)
- Commits `b2e6fa5`..`ff9d461`; docs committed `0b4b7c1`; implemented `a8af8a2`..`b40aa7b`
- Gate: `uv run pytest -q` 342 passed; `ruff` clean; audit `275/0`; frontend build exit 0

### Wave 2 — Public vote API + `/Voturi` page (PRIMARY done; P5 pending)

**Goal:** Ship vote data read-only on the site via additive REST endpoints + honest empty-state page. Non-destructive.

**Dependency graph:** Wave 1 (vote tables exist) → Wave 2 P1 (endpoints) → P3 (client) → P4 (page) → P5 (existing pages).

**Phases → Action Points → Checkpoints → Rollbacks:**

**P0 — Verify baseline** (done)
- AP-2.01: `cd frontend && npm ci && npm run build` → exit 0 ✅
- AP-2.02: `uv run ruff check pipeline backend scripts tests` → clean ✅
- AP-2.03: `uv run pytest -q` → all pass ✅
- AP-2.04: audit `--strict --baseline` → `275/0` ✅
- Rollback: none (read-only)

**P1 — Backend: 5 vote endpoints** (done, commit `03bd1b1`)
- AP-2.05: insert endpoints after `api.py:1051` before `traseism/overview@1054` ✅
- AP-2.06: `data_exists()` guard on every endpoint ✅ (verified live: 200+empty)
- Rollback: `git revert 03bd1b1` backend portion

**P3 — Frontend: API client helpers** (done, commit `03bd1b1`)
- AP-2.07: add typed fetch helpers + interfaces to `client.ts` ✅
- Rollback: `git revert 03bd1b1` frontend portion

**P4 — Frontend: `/Voturi` page** (done, commit `752eff6`)
- AP-2.08: new `frontend/src/pages/Voturi.tsx` + `components/RollCallTable.tsx` ✅
- AP-2.09: lazy import + route def + routeTree entry in `router.tsx` ✅
- AP-2.10: i18n keys ro+en in `i18n.ts` ✅
- Rollback: `git revert 752eff6`

**P5 — Wire vote data into existing pages** (PENDING — next slice)
- AP-2.11: `/Radar` → alignment matrix via `/api/votes/positions?legislature=&chamber=`; empty → `empty.rollcall` (precondition N>0)
- AP-2.12: `/Grafice` → cohesion timeline via `/api/traseism/summary` + `/api/votes/cohesion`; empty → `traseismCoverageNone` banner (`Traseism.tsx:134-164`)
- AP-2.13: `/Topuri` → MP scorecard via new `/api/votes/scorecard`; empty → `mps.empty` (`i18n.ts:398 / 903`)
- Rollback: revert per page; each page renders empty state otherwise

**P6 — i18n** (done with P4)
- AP-2.14: ro+en key pairs shipped ✅

**P7 — Verify gate** (done)
- AP-2.15: build+tests+lint+audit+doc-truth all green ✅

**Irreversible:** none (additive only; no schema migration; no production data write).

### Wave 3 — Upgrade /Radar, /Grafice, /Topuri (gated on N>0)

**Goal:** Upgrade the three priority pages to statistical visualizations once vote data exists.

**Dependency graph:** Wave 2 complete → production vote backfill (Wave 2-P5 data or Wave 3 P0) → page upgrades.

**Phases:**
- P0: backfill production votes (dry-run → apply on copy → release)
- P1: `/Radar` → roll-call alignment matrix (`PartyComparisonMatrix` skeleton + `InfoStat` + `DashboardCard`; new `components/RadarMatrix.tsx`)
- P2: `/Grafice` → party-cohesion/defection timeline (`TimelineChart` + `SwitchTimeline` + `DataViz` sparklines; new `components/CohesionLine.tsx`)
- P3: `/Topuri` → MP behavioural scorecard (`SwitchLeaderboard` table pattern + `Leaderboard` i18n keys; new `components/ScoreRow.tsx`)
- P4: each page gated on N>0 precondition; render empty state otherwise
- P5: verify build + tests + audit

**Checkpoints:** CP-3.01 backfill dry-run writes nothing; CP-3.02 each page renders honest empty state when N=0; CP-3.03 each page renders real data when N>0.

**Rollbacks:** `git revert` per page commit; release tag restore (`data-latest-release.txt` pin revert).

### Wave 4 — `/Ideology` placeholder + CHES/PopuList prep + coverage fixes

**Goal:** Ideological spatial map placeholder (no data yet) + covariate ingest prep + remaining coverage fixes.

**Phases:**
- P0: `/Ideology` page rendering `EmptyState` + methodology note; no chart library yet (ECharts available but data absent); precondition: external covariates endpoint non-empty
- P1: CHES / PopuList / Party Facts / V-Party covariates ingest (licence-gated: CC0/CC-BY/OGL only; CC BY-SA/NC/SA → cross-check only)
- P2: committee histories / speeches / election benchmarks mapping to existing tables vs new tables
- P3: coverage fixes for dead routes (`/Județe`, `/Legi`, `/Pensii`, `/Quiz`, `/Întreabă 281`, `/Ghid`, `/press`)
- P4: deprecated GraphQL `party_cohesion` cleanup documentation

**Checkpoints:** CP-4.01 `/Ideology` shows `empty.ideology` (no fake axes); CP-4.02 licence register updated for each covariate source; CP-4.03 audit still `275/0`.

**Rollbacks:** revert page + route; remove source licence row (database CHECK prevents bad values).

---

## 4. Selected first slice (implement now)

**Decision:** Continue with **Wave 2 P5** — wire vote data into `/Radar`, `/Grafice`, `/Topuri` — gated on N>0 precondition.

**Justification:** Vote tables exist (Wave 1) and endpoints are live (Wave 2 PRIMARY). These pages already exist in the route table but show no vote data today. Adding the data contract is additive, non-destructive, and each page renders an honest empty state when N=0. Rollback = revert the page commit.

**Justification for NOT doing Wave 3 yet:** production vote tables are empty; upgrading pages to show real data requires the backfill first (Wave 3 P0), which is a separate decision requiring source licence sign-off.

---

## 5. Risk register (≥8) + day-1 checklist

| # | Risk | L | I | Mitigation | Owner |
|---|------|---|---|---|---|
| R-01 | Empty table mistaken for API error vs no data | M | H | `data_exists` flag + honest `empty.*` labels; QA empty-state tests | frontend |
| R-02 | REST vs GraphQL `party_cohesion` divergence | H | M | REST owns truth; GraphQL left legacy | backend |
| R-03 | `deploy-all.sh:20` `git add -A` footgun + `:21` hardcoded commit | M | H | Never use for promotion; dirty-tree guard | qa |
| R-04 | ECharts bundle (487 KB min / 164 KB gzip) | M | M | Modular imports; budget guard | frontend |
| R-05 | `ui_validate.py` axe violations NOT PROVEN locally (no playwright/chromium) | M | H | CI `evidence-guards` job | qa |
| R-06 | Third-party vote outage blocks corpus | M | H | Build-isolation test forbids vote code in `cmd_build_corpus` | backend |
| R-07 | i18n missing key → undefined label | L | M | Ship ro+en pairs; EN fallback at line 1029 | frontend |
| R-08 | `data/parlament-real.db` absent in CI | M | M | Corpus tests skip when artifact missing | qa |

### Day-1 checklist (before any Wave 2-P5 code)
- [ ] `cd frontend && npm ci && npm run build` → exit 0
- [ ] `uv run ruff check pipeline backend scripts tests` → clean
- [ ] `uv run pytest -q` → all pass
- [ ] `uv run python -m pipeline.cli --db data/parlament.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json` → `275/0`
- [ ] `bash scripts/check-doc-truth.sh` → false-claims: 0
- [ ] Record MCP counts with live discovery (33 chrome-devtools / 8 opencode / 7 shadcn = 48 stable; prompt-optimizer conditional)
- [ ] State repo-scope rule: NedCode4 `just *` only in `/home/nedaktov/Desktop/NedCode4`; product commands only in `/home/nedaktov/parlament-deschis`

---

**End of Wave 2 blueprint.** Next: implement Wave 2 P5 (wire vote data into `/Radar`, `/Grafice`, `/Topuri`).