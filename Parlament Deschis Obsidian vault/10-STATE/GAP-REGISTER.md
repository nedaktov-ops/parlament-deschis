---
id: gap-register
type: gap
title: Gap Register — Vision vs Live State
description: Stable-ID register of P0/P1/P2 gaps between the documented vision and the deployed state, with evidence and next actions.
status: active
authority: canonical
tags: [type/gap, lifecycle/active, domain/project]
source_paths: [docs/GAP-ANALYSIS-2026-11-21.md, docs/COMPREHENSIVE-REVIEW-2026-11-21.md, docs/POST-INITIAL-AUDIT-2026-11-21.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Gap Register — vision vs live state

Stable IDs for tracking. Current-state summary lives in
[CURRENT-STATE](CURRENT-STATE.md); git/CI mechanics in
[GIT-POSITION](GIT-POSITION.md); definitional disputes in
[CONTRADICTIONS](CONTRADICTIONS.md). Vision baseline:
[VISION](../20-DIRECTION/VISION.md). Work breakdown:
[TASK-REGISTER](../20-DIRECTION/TASK-REGISTER.md).

## P0 — shipped state does not match intended state

| ID | Gap | Evidence | Impact | Next action | Status |
| --- | --- | --- | --- | --- | --- |
| G-P0-01 | Local fixes not deployed anywhere | `origin/main` `6b848f1`, HEAD `6fd6028` 3 ahead/unpushed; Vercel bundle hash differs; live OpenAPI lacks canonical routes | CI stays RED; canonical routes/`meta` absent; users get broken vote/ideology requests | Push branch, open PR, get CI green, then deploy backend then frontend (see [GIT-POSITION](GIT-POSITION.md)) | in-progress |
| G-P0-02 | RED CI on main + no branch protection | Failing `test` check on all six recent main pushes (`Ideology.tsx` rules-of-hooks); protection API HTTP 404, no rulesets | Seven failing commits reached main; nothing enforces the gate before merge | Land F1 hook-order fix on main; enable required checks on `main` (owner setting) | in-progress |
| G-P0-03 | Vote data — the 10× centrepiece — empty in production | `/api/votes` `total:0`; pinned asset has 18 tables and zero vote tables; vote code/fixtures only in working tree and unpushed commit | Platform still cannot answer "how did the MP vote?" | Fix source fetch, then publish a fresh dataset release containing ingested votes | blocked |
| G-P0-04 | Dataset refresh failed 11 times | Issue #14; `ConnectTimeout` fetching `www.cdep.ro/...structura2015.gp` from GitHub runners, stable across five days | Daily refresh, audit and Render trigger never run; freshness depends on manual local rebuild | Fix `cdep.ro` fetch path (retry/cache/alternate source) and make an explicit release decision | open |
| G-P0-05 | Two live switch totals and unlabelled counts | `/dashboard/stats` 2,002 vs `/export/report` and `/traseism/summary` 1,217; 7,358 raw vs 7,349 prepared memberships | Same dataset publishes contradictory headline numbers; definitions undisclosed | Add explicit labels for switch definitions and membership counts in `docs/API.md` and `README.md` (R1/R2 in [CONTRADICTIONS](CONTRADICTIONS.md)) | open |

## P1 — vision items promised but absent or partial

| ID | Gap | Evidence | Impact | Next action | Status |
| --- | --- | --- | --- | --- | --- |
| G-P1-01 | Real-time switch alerts | `PARLAMENT_POLL_INTERVAL_MIN: ""` in `render.yaml`; runtime read-only | Feature 13 in the 15-feature plan is inert | Decide: relabel alerts "on release" or enable a writing poller | open |
| G-P1-02 | Party genealogy | 0 non-null `previous_party_id`/`successor_party_id`; GraphQL has no such fields | Merger/split timeline cannot be populated | Source genealogy data or drop the feature from the vision | open |
| G-P1-03 | Senate historical profile ingest | Discovery fixed and guarded (128/134 GUIDs) but profile ingest deferred on identity risk | Senate comparison page remains partial | Resolve identity risk, then ingest profiles | open |
| G-P1-04 | Coverage is one-dimensional | "Full for all 20 scopes" covers mandates only; `votes: none`, `biographies: partial` dimensions missing | Coverage claims overstate completeness | Publish per-dimension coverage | open |
| G-P1-05 | Frontend UX phases H3–H5 | `EmptyState.tsx`/`LoadingState.tsx` have zero importers; `TimelineStrip.tsx` empty `onClick` TODO; 7 exhaustive-deps warnings | State design work incomplete despite code presence | Wire states, finish TimelineStrip, clear warnings | open |
| G-P1-06 | Design contract TBDs | Audiences/voice/icon family/TBD; de-facto inline SVG, no Lucide dependency; no formal token table, empty asset manifest, no wireframe exports | Frontend contract not authoritative | Close TBDs or align docs to de-facto implementation | open |
| G-P1-07 | Blog / SEO / donations | No blog directory, article routes or donation UI; "implementation has not started" | Whole strategy theme unshipped | Decide explicitly to drop or scope the plan (owner input: recipient) | open |
| G-P1-08 | Self-sustainability Phase 4 | Vercel Cron watchdog not configured; end-to-end Render verification and pruning pending | Hands-off operation claim incomplete | Configure cron and complete Render verification | open |
| G-P1-09 | "All 15 features complete" claim is self-contradictory | Doc says all 15 done while admitting succession/genealogy empty; audit tallied 11 PRESENT / 6 PARTIAL | Overstated status erodes trust | Relabel claim to 11 PRESENT / 6 PARTIAL (R6) | open |
| G-P1-10 | Wave 1 six NOT DONE items | Lint gate, Vercel tolerance, deploy-all quarantine, quick-win defects, production backfill, 3 UNVERIFIED | Integration blueprint not fully closed | Schedule against TASK-REGISTER | open |
| G-P1-11 | Staging deploy + load-test evidence | `scripts/load_test.py` exists but no staging deployment or recorded run | Load-test proof missing | Run load test on staging and record evidence | open |

## P2 — hygiene / documentation debt

| ID | Gap | Evidence | Impact | Next action | Status |
| --- | --- | --- | --- | --- | --- |
| G-P2-01 | Analytics `meta` not universal; TTL 300 s vs SPEC 1 h | Other `/api/analytics/*` lack `meta`; `backend/cache.py` TTL 300 s | Shape/TTL inconsistency in docs | Align docs or widen implementation | open |
| G-P2-02 | Four working-DB votes with NULL `snapshot_hash` | Importer now backfills on re-ingest; rows not repaired in shipped release | Residual provenance gaps | Repair rows on next release rebuild | open |
| G-P2-03 | Contradictory documentation | WAL vs DELETE, 7,358 vs 7,349, "no vote tables" vs populated local DBs, OpenAPI 40 vs 41 | Reconciled in CONTRADICTIONS but legacy docs still conflict | Refresh stale docs from resolved verdicts | open |
| G-P2-04 | Vite version conflict in Wave 4 recipes | R-D0.3 titled "Vite 8" but procedure says `^5.0.0`; shipped `^6.0.0` | Misleading upgrade recipe | Resolve to shipped version | open |
| G-P2-05 | Stale untracked QA reports; gitignored completion certificate | `.nedcode/qa/*` stale at `ff9d461`; `COMPLETION-CERTIFICATE.md` gitignored | Non-gate artifacts contradict gates | Mark historical or delete after migrating evidence | open |
| G-P2-06 | CSP is report-only, not enforcing | `Content-Security-Policy-Report-Only` in `vercel.json` and FastAPI | Security header present but non-blocking | Decide whether to enforce | open |
| G-P2-07 | GraphQL route probe 404 on both hosts | `/graphql` returned 404; may be routing/probe artifact | Documented feature unverified | Re-probe with browser session (NOT PROVEN either way) | open |
