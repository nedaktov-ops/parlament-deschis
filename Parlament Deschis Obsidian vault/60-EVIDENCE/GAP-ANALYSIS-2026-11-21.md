---
id: GAP-ANALYSIS-2026-11-21
type: evidence
title: "Documentation vision vs. live deployment — gap analysis (2026-11-21)"
description: "Frozen snapshot of the vision-vs-live probe: GitHub, Vercel and Render state, P0/P1/P2 gaps, aligned elements, recommended work order, and the recorded R11 correction."
status: active
authority: mirror
tags: [type/evidence, lifecycle/active, domain/project]
source_paths: [docs/GAP-ANALYSIS-2026-11-21.md, docs/AUDIT-RESOLUTIONS-2026-11-21.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Vision vs. live deployment — gap analysis (2026-11-21)

> **Frozen evidence snapshot.** This note mirrors the 2026-11-21 gap analysis.
> Live numbers move; the gap ledger is maintained in [GAP-REGISTER](../10-STATE/GAP-REGISTER.md),
> and current truth in [CURRENT-STATE](../10-STATE/CURRENT-STATE.md).

## Method and snapshot

- Six coordinated agents: four partitioned all 60 project Markdown files (A: vision/strategy; B: data/methodology/verification; C: operations/status; D: frontend design contract), one verified GitHub state read-only (E), one probed Vercel + Render read-only (F). The master agent cross-checked decisive claims.
- No product file was edited; no deploy, workflow trigger or GitHub mutation was performed.
- Local HEAD `221cf78` (branch `review/completion-20261121`, unpushed); the review above was taken at `3eb3c0a`; `origin/main` and GitHub default branch `6b848f1`. Probe window 2026-11-21 ~08:20–08:23 UTC. The vault snapshot is pinned at `6fd6028`.

## Vision stated in the docs

| Theme | Aspiration | Source |
|---|---|---|
| 10× platform | From "who changed group, when?" to trustworthy statistics on how MPs voted, party beliefs, constituency base and international comparison. Highest-value move = roll-call votes as first-class dated events. | `docs/MASTER-STRATEGY.md:98-102` |
| Trust invariants | Source URL + confidence + date precision + `dedup_key` on every row, per-source licence gate, strict audit, **no attendance score**. | `docs/MASTER-STRATEGY.md:102,172-174` |
| 15 transparency features | Leaderboard, commitment tracker, Senate gap, demographics, committee control, party comparison, PDF export, bios, deep-dive, loyalty, wave detection, merger/split, real-time alerts, coalition stability, MP comparison, load test. | `docs/STRATEGY-TRANSPARENCY.md:58-89` |
| Frontend F→G→H | Deep audit before repair, modern-web-guidance, dark calm civic design, one effect and 1–2 moments per page, no new pages in Phase F. | `docs/FRONTEND-IMPROVEMENT-STRATEGY.md:11-13`; `docs/FRONTEND-UX-10X-STRATEGY.md:26-31` |
| Self-sustainability | Hands-off, observable, recoverable free-tier operation — not a 100% uptime promise. | `docs/SELF-SUSTAINABILITY-ARCHITECTURE.md:5-15` |
| Blog / SEO / donations | 30 bilingual evidence-led articles, canonical Vercel hosting, verified donation path — **strategy only, implementation not started**. | `docs/BLOG-SEO-AND-HOSTING-STRATEGY.md:3,14-16` |

**Supersession matters.** `STRATEGY.md`, `SPEC.md`, `ACTION_PLAN.md` and `STRATEGY-TRANSPARENCY.md` carry historical banners; `MASTER-INTEGRATION-BLUEPRINT.md` supersedes `MASTER-STRATEGY.md`, and the Wave 2 blueprint supersedes it again. The chain is quarantined in [STRATEGY-BLUEPRINTS-HISTORICAL](../70-ARCHIVE/STRATEGY-BLUEPRINTS-HISTORICAL.md); newest state document is `docs/COMPREHENSIVE-REVIEW-2026-11-21.md` (mirrored in [COMPREHENSIVE-REVIEW-2026-11-21](COMPREHENSIVE-REVIEW-2026-11-21.md)).

## State claimed by the docs (newest snapshot)

- One-way pipeline: polite fetch → SHA-256 fragments → parse → identity resolution → bitemporal tenures → events → as-of API → static React dashboard; runtime read-only, DB baked into the image.
- API: ~48 OpenAPI paths, three distinct committee counts (26 orgs / 23 active / 9 chairs), REST + GraphQL in docs, token-protected admin poll.
- Gates: strict audit **275 known / 0 new**; UI validation widened to **24 routes, zero JavaScript errors, zero axe violations**; pytest 384 passed; doc-truth 0.
- Dataset pin `data-20261117-T213500`; 3,388 persons / **7,349** prepared memberships.
- Residuals: issue #14 (11 failed data runs from source timeouts), no branch protection, deployment lag, 0 genealogy links, Senate historical profile ingest deferred, analytics `meta` not universal, cache TTL 300 s vs SPEC's 1 h.

## Live state observed

### GitHub

- `origin/main` = default branch = `6b848f1`; local HEAD one unpushed commit ahead, zero behind; no remote branch contains the local commit.
- Recent `main` CI runs: `test` **failure** (`react-hooks/rules-of-hooks` in `Ideology.tsx`, 4 errors / 10 warnings), `audit` success, `evidence-guards` success, `docker` skipped, `Deploy verify` skipped. All six most recent main runs failed.
- `main` has **no branch protection** (HTTP 404, no rulesets). Two open PRs with failing checks remain mergeable. Issue #14 is open with 11 failed data runs; logs prove `ConnectTimeout` to the source host. Open PRs: 9 (8 dependabot, 1 deploy-sync).
- Latest release `data-20261117-T213500` matches the local pin; at the tag itself the pin read an earlier, superseded tag. The pinned asset has **18 tables and no vote tables**.

### Vercel (frontend)

- `GET /` 200; SPA fallback proven (`/Voturi`, `/ideology`, `/radar` and a nonsense path all return the same shell — rewrite proven, route rendering **NOT PROVEN**).
- Live assets `/assets/index-D61EXxHz.js` / `index-4FXD2Kh9.css` differ from the local HEAD build (`index-R6NL1YHG.js` / `index-BDGRixv5.css`).
- Live bundle double-prefixes two calls at runtime (`/api/api/...`) because a helper prepends `/api` to literals already carrying it. Local HEAD uses canonical single-prefix literals.
- CSP is byte-equal across config and backend (226 B) but is **Report-Only**, i.e. non-enforcing.

### Render (API)

- `/api/health` 200: release `data-20261117-T213500`, 3,388 persons, 7,349 memberships, sources `never_run`.
- `/dashboard/stats` 200: switches 2,002, committees 26, legislatures 20, parties 37, cross_chamber 39, coverage 100 — while `/export/report` and `/traseism/summary` say switches **1,217**. Adjudicated as definitional under R1, not a data defect.
- `/api/votes` → `data_exists:false, total:0`. **No vote data in production** — the 10× centrepiece is not shipped. Scope note: local, gitignored working DBs do hold votes, never released.
- `/api/analytics/ideology` → **404**; legacy double-prefixed path → 200 without `meta`. Scorecard path → 200 but wrong handler (shadowed).
- Live `/openapi.json` has 48 paths including legacy aliases and zero `meta`/`generated_at`/`count` — decisive proof the deployed backend is pre-fix. HSTS exists only on Vercel.

## Gap register (summary)

### P0 — shipped state ≠ intended state

| Gap | Consequence |
|---|---|
| Local fixes deployed nowhere | CI stays RED on main; canonical routes and `meta` absent in production; users get broken vote/ideology requests. |
| CI RED on main + no branch protection | Seven failing commits reached main; nothing forces the gate before merge. |
| Vote data empty in production | Platform still cannot answer "how did the MP vote?", the stated highest-value move. |
| Dataset refresh failed 11 times | Daily refresh, audit and Render trigger never run; freshness depends on a manual local rebuild. |
| Two live switch totals | Contradictory headline numbers for one dataset (R1 labels, not a code defect). |

### P1 — vision promised but absent or partial

Real-time switch alerts (poller disabled / runtime read-only) · party genealogy (0 links) · Senate historical profile ingest deferred · one-dimensional coverage (mandates only) · frontend H3–H5 (`EmptyState`/`LoadingState` unused, `TimelineStrip` empty `onClick`, exhaustive-deps warnings) · design-contract TBDs (audiences, voice, icon family — Lucide absent, de-facto inline SVG; token table; assets; wireframes; stale axe baseline) · blog/SEO/donations not started · self-sustainability Phase 4 watchdog not configured · "all 15 complete" self-contradiction · Wave 1 six NOT DONE items · staging deploy + load-test evidence absent.

### P2 — hygiene / documentation debt

Analytics `meta` not universal; cache TTL 300 s vs SPEC §3.6's 1 h; four working-DB votes with NULL `snapshot_hash`; contradictory docs (WAL vs DELETE, 7,358 vs 7,349, "no vote tables" vs local votes, OpenAPI 40/41 baseline); Wave-4 Vite recipe conflict; untracked QA reports stale; completion certificate gitignored; CSP report-only; GraphQL documented but `/graphql` 404 on both hosts in this probe (**NOT PROVEN** either way).

## What *is* aligned

- Documented topology holds: Vercel SPA, `/api/*` rewritten to Render, Render API with pinned dataset, GitHub Actions as data control plane.
- Release pin matches everywhere: `data-20261117-T213500`, 3,388 persons, 7,349 memberships, 26 committees.
- Security headers match byte-for-byte across `vercel.json`, FastAPI, Vercel and Render.
- Strict audit and provenance discipline are real and enforced locally (275 known / 0 new).
- The 2026-11-21 fixes are real **in the repository** (384 tests, 24/24 UI validation, lint/build/doc-truth green) — they simply have not been released.

## Recommended order of work

1. Push the review branch, open a PR, get CI green on main, enable branch protection with required checks.
2. Deploy the **backend first** (canonical routes and `meta`), then the frontend (single-prefix paths); verify the live ideology endpoint and both bundle hashes.
3. Fix the source-fetch path in the data workflow (retry/cache/alternate), then publish a release containing the ingested votes.
4. Reconcile and label the two switch totals before any further release.
5. Close P1 gaps in dependency order: genealogy data, Senate profiles, multi-dimensional coverage, then H3–H5 states; decide explicitly to drop or scope the blog/donation plan.
6. Refresh stale docs from the new live state, mirroring the licence/robots/version corrections already made.

## Recorded correction R11

An earlier version of this analysis claimed `ci.yml` had a **bare `push:` with no branch filter**. That is **false** and has been corrected: `ci.yml:3-5` declares `push: branches: [main]`, plus `pull_request:` and `workflow_dispatch:`. `docs/DEPLOYMENT.md:71` was right. Full adjudication in [CONTRADICTIONS](../10-STATE/CONTRADICTIONS.md).

**Explicitly NOT PROVEN in this read-only pass:** runtime read-only enforcement, deployment ordering, client-side rendering of any SPA route, whether the switch discrepancy is a defect (resolved later as definitional by R1), and the exact Vercel build commit (strongly inferred `6b848f1`).

## See also

[GAP-REGISTER](../10-STATE/GAP-REGISTER.md) · [CONTRADICTIONS](../10-STATE/CONTRADICTIONS.md) · [GIT-POSITION](../10-STATE/GIT-POSITION.md) · [AUDIT-2026-11-21](AUDIT-2026-11-21.md) · [CURRENT-STATE](../10-STATE/CURRENT-STATE.md)
