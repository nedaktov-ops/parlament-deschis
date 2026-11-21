# Documentation Vision vs. Live Deployment — Gap Analysis (2026-11-21)

**Method.** Six coordinated agents: four partitioned all 60 project Markdown files
(A: vision/strategy; B: data/methodology/verification; C: operations/status;
D: frontend design contract), one verified GitHub state read-only (E), one probed
Vercel + Render read-only (F). The master agent independently cross-checked the
decisive claims. No file in the product tree was edited by the fleet; no deploy,
workflow trigger or GitHub mutation was performed. GitHub-side claims were
**confirmed** by Agent E; the post-initial audit later corrected one claim here
about the `ci.yml` branch filter (see `AUDIT-RESOLUTIONS-2026-11-21.md`).

**Snapshot.** Local HEAD `221cf78` (branch `review/completion-20261121`, unpushed);
the review above was taken at `3eb3c0a` and the gap analysis was committed at `221cf78`;
`origin/main` and GitHub default branch `6b848f1`; probe window 2026-11-21
~08:20–08:23 UTC.

---

## 1. Vision stated in the documentation

| Theme | What the docs aspire to | Source |
|---|---|---|
| 10× platform | From "who changed group, when?" to trustworthy statistics answering how MPs voted, party beliefs, constituency base and international comparison. Single highest-value move = roll-call votes as first-class dated events; supporting axes = biographies, party covariates, committee histories/speeches, elections/benchmarks. | `docs/MASTER-STRATEGY.md:98-102` |
| Trust invariants | Source URL + confidence + date precision + `dedup_key` on every row, per-source licence gate, strict audit, **no attendance score**. | `docs/MASTER-STRATEGY.md:102,172-174` |
| 15 transparency features | Leaderboard, commitment tracker, Senate gap page, demographics, committee control, party comparison, PDF export, biography cards, person deep-dive, loyalty score, wave detection, merger/split timeline, real-time alerts, coalition stability, MP comparison, load test. | `docs/STRATEGY-TRANSPARENCY.md:58-89` |
| Frontend F→G→H | Deep audit before repair; modern-web-guidance; dark, calm, civic design with one effect and 1–2 moments per page; no new pages in Phase F. | `docs/FRONTEND-IMPROVEMENT-STRATEGY.md:11-13`; `docs/FRONTEND-UX-10X-STRATEGY.md:26-31` |
| Self-sustainability | Hands-off, observable and recoverable free-tier operation; explicitly not a 100%-uptime promise. | `docs/SELF-SUSTAINABILITY-ARCHITECTURE.md:5-15` |
| Blog/SEO/donations | 30 bilingual evidence-led articles, canonical Vercel hosting, verified donation path — "strategy only; implementation has not started". | `docs/BLOG-SEO-AND-HOSTING-STRATEGY.md:3,14-16` |

**Supersession chain matters:** `STRATEGY.md`, `SPEC.md`, `ACTION_PLAN.md` and
`STRATEGY-TRANSPARENCY.md` carry banners declaring their status labels historical;
`MASTER-INTEGRATION-BLUEPRINT.md` supersedes `MASTER-STRATEGY.md`, and the Wave 2
blueprint supersedes it again. The newest state document is
`docs/COMPREHENSIVE-REVIEW-2026-11-21.md`.

---

## 2. State claimed by the documentation (newest snapshot)

- One-way pipeline: polite fetch → SHA-256 fragments → parse → identity resolution → bitemporal tenures → events → as-of API → static React dashboard; runtime read-only, DB baked into the image. (`docs/ARCHITECTURE.md:3-10`; `docs/DEPLOYMENT.md:11-19`)
- API: ~48 OpenAPI paths, three distinct committee counts (26 orgs / 23 with active memberships / 9 with a chair), REST + GraphQL, token-protected admin poll. (`docs/API.md:159-171,341-357`)
- Gates: strict audit **275 known / 0 new**; UI validation widened to **24 routes, zero JavaScript errors, zero axe violations**; pytest 384 passed; doc-truth 0. (`docs/COMPREHENSIVE-REVIEW-2026-11-21.md:49-59`)
- Dataset pin `data-20261117-T213500`; 3,388 persons / **7,349** memberships live. (`docs/COMPREHENSIVE-REVIEW-2026-11-21.md:25`)
- Declared residuals: issue #14 (11 failed data runs from `cdep.ro` ConnectTimeout), no branch protection on `main`, deployment lag, party genealogy 0 links, Senate historical profile ingest deferred, analytics `meta` not universal, cache TTL 300 s vs SPEC 1 h. (`docs/COMPREHENSIVE-REVIEW-2026-11-21.md:68-91`; `docs/METHODOLOGY.md:316-318,500`)

---

## 3. Live state (GitHub, Vercel, Render)

### GitHub
- `origin/main` = GitHub default branch = `6b848f1`; local HEAD `3eb3c0a` is **one unpushed commit ahead, zero behind** on branch `review/completion-20261121`; no remote branch contains the local commit.
- CI on recent `main` pushes: `test` **failure**, `audit` success, `evidence-guards` success, `docker` skipped; `Deploy verify` **skipped**. The failing step is "Frontend lint, type-check and build" (hooks-after-return in `Ideology.tsx`, `✖ 14 problems (4 errors, 10 warnings)`) — precisely what local HEAD fixes. All six most recent CI runs on main are failures.
- `main` has **no branch protection** (HTTP 404; no rulesets). Two open PRs (#29, #9, #6) have failing CI checks and are still mergeable — the absence of enforcement is observable.
- Issue #14 **open** with 11 failed data runs; its body records only "release not published", while run `44729831051`'s log proves `requests.exceptions.ConnectTimeout` to `www.cdep.ro` in "Collect and ingest".
- Open PRs: 9 (8 dependabot, 1 deploy-sync), ages 1–6 days.
- Latest GitHub release `data-20261117-T213500` matches the local pin. Nuance: at the tag itself the pin read an earlier, superseded tag; the marker was updated after the release was published. The pinned asset (sha256 `7298ffd1…`) has **18 tables and no `vote` / `vote_position` / `vote_import_run` table**.
- `docs/DEPLOYMENT.md:71` matches `ci.yml:3-5`: `push` is filtered to `branches: [main]` and CI also runs on PRs and `workflow_dispatch`. (An earlier version of this analysis incorrectly claimed a bare `push:` with no filter; corrected after re-reading the file.)

### Vercel (frontend)
- `GET /` 200, serves `index.html` (940 B) with assets `/assets/index-D61EXxHz.js` and `/assets/index-4FXD2Kh9.css`; JS 503,825 B, immutable cache, served from Vercel cache.
- Local HEAD build produces `index-R6NL1YHG.js` / `index-BDGRixv5.css` — **different bundle**.
- SPA fallback proven: `/Voturi`, `/ideology`, `/radar` and a nonsense path all return the same shell (proves rewrite, not that routes render).
- Live bundle requests **double-prefixed** paths at runtime: helper `VC="/api"` prepends to literal `/api/analytics/ideology` and `/api/votes/scorecard` → `/api/api/...`. Local HEAD uses canonical single-prefix literals.
- CSP is byte-equal between `vercel.json` and `backend/main.py` (226 B), but it is `Content-Security-Policy-**Report-Only**` — non-enforcing.

### Render (API)
- `/api/health` 200: release `data-20261117-T213500`, persons 3,388, memberships 7,349, sources `never_run`; `/health/live` and `/health/ready` 200.
- `/dashboard/stats` 200: switches 2,002, committees 26, legislatures 20, parties 37, cross_chamber 39, coverage 100 — but `/export/report` and `/traseism/summary` both say switches **1,217** (one dataset, two live numbers).
- `/api/votes` → `data_exists:false, total:0` — **no vote data in production**, confirming the 10× "highest-value move" is not actually shipped to users. Scope note: the local, gitignored working databases *do* hold votes (`data/parlament-real.db` 177 votes / 28,800 positions; `data/parlament.db` 52 votes / 7,127 positions), but they have never been released. "No vote data" always refers to the published corpus only.
- `/api/analytics/ideology` → **404**; legacy `/api/api/analytics/ideology` → 200 without `meta`.
- `/api/votes/scorecard` → 200 but wrong handler (`data:null`, shadowed by `/votes/{vote_id}`); legacy `/api/api/votes/scorecard` → votes-list shape.
- Live `/openapi.json` has 48 paths including the legacy double-prefixed routes and **zero** occurrences of `meta` / `generated_at` / `count` — decisive proof the deployed backend is pre-fix.
- All analytics endpoints live lack `meta`. Vercel + Render CSP and five other security headers match byte-for-byte; HSTS exists only on Vercel.

---

## 4. Gap register — missing elements and incomplete tasks

### P0 — shipped state does not match the intended state

| Gap | Evidence | Consequence |
|---|---|---|
| Local fixes are not deployed anywhere | `origin/main` = `6b848f1`; local HEAD `3eb3c0a` unpushed; Vercel bundle hash differs; live OpenAPI lacks canonical routes | CI stays RED because the hook-order fix is not on main; canonical routes/`meta` absent in production; users still get broken vote/ideology requests |
| CI RED on main + no branch protection | failing `test` check on recent main pushes; 404 from branch-protection API | Seven failing commits reached main; nothing forces the gate before merge |
| Vote data — the 10× centrepiece — is empty in production | Live `/api/votes` `total:0`, all vote analytics `data_exists:false`; downloaded pinned release asset has 18 tables and **zero vote tables**; vote code/fixtures exist only in the working tree and unpushed commit | The platform still cannot answer "how did the MP vote?", the stated single highest-value move |
| Dataset refresh has failed 11 times | issue #14; `ConnectTimeout` to `www.cdep.ro/...structura2015.gp?idl=1&cam=2&leg=1990` from GitHub runners | Daily refresh, audit and Render trigger never run; freshness depends on manual local rebuild |
| Two different live switch totals | 2,002 in `/dashboard/stats` vs 1,217 in `/export/report` and `/traseism/summary` | The same dataset publishes contradictory headline numbers |

### P1 — vision items promised but absent or partial

| Gap | Evidence |
|---|---|
| Real-time switch alerts | `PARLAMENT_POLL_INTERVAL_MIN: ""` in `render.yaml:28`; runtime read-only; no live alerts despite feature 13 in the 15-feature plan |
| Party genealogy | 0 non-null `previous_party_id` / `successor_party_id` in the corpus; GraphQL has no such fields (`docs/METHODOLOGY.md:316-318,341-346`; master DB query = 0) |
| Senate historical profile ingest | discovery fixed and guarded (128/134 GUIDs) but profile ingest deferred on identity risk (`docs/DATA-COMPLETENESS-RECOVERY.md:54-58`) |
| Coverage is one-dimensional | "full for all 20 scopes" covers only mandates; `votes: none`, `biographies: partial` dimensions missing (`docs/DATA-ENRICHMENT-RESEARCH.md:85,281-287`) |
| Frontend UX phases H3–H5 | `EmptyState.tsx` and `LoadingState.tsx` have zero importers; `TimelineStrip.tsx` has an empty `onClick` TODO; 7 exhaustive-deps warnings remain (`docs/FRONTEND-UX-10X-STRATEGY.md:247-320`) |
| Design contract TBDs | audiences/personas, brand voice, icon family (Lucide absent — de-facto inline SVG), formal token table (docs use literal hex, code uses `rgb(var(--…))`), asset manifest empty, wireframe exports absent, axe QA baseline at stale commit (`frontend/docs/design/*`) |
| Blog / SEO / donations | no blog directory, no article routes, no donation UI — "implementation has not started" (`docs/BLOG-SEO-AND-HOSTING-STRATEGY.md:3`) |
| Self-sustainability Phase 4 | Vercel Cron watchdog not configured; end-to-end Render verification and pruning pending (`docs/SELF-SUSTAINABILITY-ARCHITECTURE.md:193-206`) |
| 15-feature "all complete" claim is self-contradictory | `STRATEGY-TRANSPARENCY.md:472-478` says all 15 done while admitting succession/genealogy still empty |
| Wave 1 six NOT DONE items | lint gate, Vercel tolerance, deploy-all quarantine, quick-win defects, production backfill, 3 UNVERIFIED (`docs/MASTER-INTEGRATION-BLUEPRINT.md:1011-1023`) |
| Staging deploy + load test evidence | `scripts/load_test.py` exists, but no staging deployment or recorded load-test run (`docs/STRATEGY-TRANSPARENCY.md:86-89`) |

### P2 — hygiene / documentation debt

- Analytics `meta` not universal; cache TTL 300 s vs SPEC §3.6's 1 h.
- Working DB has 4 votes with NULL `snapshot_hash`; importer now backfills on re-ingest but the rows are not repaired in the shipped release.
- Contradictory docs: SQLite WAL vs prepared DELETE mode; 7,358 vs 7,349 memberships; "no vote tables" vs populated local vote tables; OpenAPI 40 vs 41 baseline.
- `WAVE-4-RECIPES.md` R-D0.3 titled "Vite 8" but procedure says `^5.0.0`.
- `.nedcode/qa/*` untracked QA reports are stale at HEAD `ff9d461`; `COMPLETION-CERTIFICATE.md` is gitignored.
- CSP is report-only, not enforcing.
- GraphQL is documented but `/graphql` returned 404 on both hosts in this probe (may be routing/probe artifact — NOT PROVEN either way).

---

## 5. What *is* aligned

- Documented topology holds: Vercel SPA, `/api/*` rewritten to Render, Render API with pinned dataset, GitHub Actions as data control plane.
- Release pin matches everywhere: `data-20261117-T213500`, 3,388 persons, 7,349 memberships, 26 committees.
- Security headers match byte-for-byte across `vercel.json`, FastAPI, Vercel and Render.
- Strict audit and provenance discipline are real and enforced locally (275 known / 0 new; no invented days; licence gating via `source_license` DB constraint).
- The 2026-11-21 fixes are real *in the repository* (384 tests, 24/24 UI validation, lint/build/doc-truth green) — they simply have not been released.

---

## 6. Recommended order of work

1. Push `review/completion-20261121` and open a PR; get CI green on main; enable branch protection with required checks.
2. Deploy the backend first (canonical routes and `meta`), then the frontend (single-prefix paths); verify live `/api/analytics/ideology` 200 and both bundles' hashes.
3. Fix the `cdep.ro` fetch path in the data workflow (retry/cache/alternate source), then publish a fresh dataset release containing the ingested votes so the 10× centrepiece is actually visible.
4. Reconcile the two switch totals (2,002 vs 1,217) before any further release.
5. Close the P1 vision gaps in dependency order: genealogy data, Senate profiles, multi-dimensional coverage, then H3–H5 frontend states; decide explicitly to drop or scope the blog/donation plan.
6. Refresh stale docs from the new live state, mirroring the licence/robots/version corrections already made.

**Explicitly NOT PROVEN in this read-only pass:** runtime read-only enforcement, deployment ordering, client-side rendering of any SPA route, whether the switch discrepancy is definitional or a defect, and which exact commit Vercel built from (strongly inferred as `6b848f1`).
