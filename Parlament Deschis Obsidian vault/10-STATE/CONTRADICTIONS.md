---
id: audit-contradictions
type: decision
title: Contradiction Resolutions — R1 to R11
description: Master adjudications of 11 audited contradictions plus the register of claims that remain NOT PROVEN.
status: active
authority: canonical
tags: [type/decision, lifecycle/active, domain/research]
source_paths: [docs/AUDIT-RESOLUTIONS-2026-11-21.md, docs/POST-INITIAL-AUDIT-2026-11-21.md, docs/GAP-ANALYSIS-2026-11-21.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Contradiction resolutions — R1 to R11

Record of the master adjudications in `docs/AUDIT-RESOLUTIONS-2026-11-21.md`.
The resolution policy, in order: executable evidence over prose; scope before
conflict; newer wins on the same topic with dated historical snapshots
preserved; addendum over base body within a file; regenerate rather than
hand-edit generated artifacts; and no guessing — unresolved claims are
reported NOT PROVEN with a named resolver. The live-state consequence of each
verdict is summarised in [CURRENT-STATE](CURRENT-STATE.md).

| # | Contradiction | Verdict | Decisive evidence |
| --- | --- | --- | --- |
| R1 | Live switches 2,002 vs 1,217 | Not a defect — definitional. Stats counts `switch_group` + `switch_party`; export/traseism count `switch_group` only. Labelling gap, not a data bug. | Pinned release DB: `switch_group=1217`, `switch_party=785` (sum 2,002), 13,144 total events (`api.py:1047-1049` vs `exports.py:72`). The 785 party-switch events exist in the **pinned release asset**, not in the local working DBs a fresh agent queried (`switch_party=0`). Residual: definitions unlabelled in UI/docs (G-P0-05). |
| R2 | Memberships 7,358 vs 7,349 | Both correct for different artifacts — raw release asset vs prepared runtime DB. Current-state truth = 7,349. | Pinned asset: 7,358 memberships, DELETE journal, `user_version=1`; after `prepare_db.py` removed 9 duplicate closed stints → 7,349 served by `/api/health`. |
| R3 | SQLite WAL vs DELETE journal | Both correct at different lifecycle stages. | Shipped asset PRAGMA `journal_mode=delete` (read-only filesystem compatibility); local/working copies report `wal`. Trust release evidence for the shipped artifact. |
| R4 | "No vote tables" vs populated vote tables | Scope difference — published corpus vs gitignored working DBs. | Pinned asset: 18 tables, zero `vote%`; working DBs hold votes. Always qualify "in the published corpus". |
| R5 | OpenAPI 40 vs 41 paths, now 48 | 41 was the stale generated file; 48 is current. | `pipeline/openapi.json` regenerated from `backend.main.app` on 2026-11-21 → 48 paths including canonical vote/ideology routes. |
| R6 | "All 15 features completed" | Historical claim, withdrawn. | Fresh audit: 11 PRESENT, 6 PARTIAL, 0 wholly absent across 17 rows (two duplicates); 0 genealogy links; poller disabled. |
| R7 | Error-tracking "PASS / hook available" | Withdrawn — no such file. | No `frontend/src/hooks/`, no `useErrorBoundary` reference, no tracked file; `EVIDENCE.md` 2026-11-21 correction wins. |
| R8 | UI gate RED / 18/24 / 24/24 / NOT PROVEN | All true in scope; 24/24 current for the repo, production NOT PROVEN. | Widened gate scans 24 routes; master re-run 24/24 locally, zero JavaScript errors, zero axe; fresh agent got 23/24 against the live proxy (`/api/analytics/ideology` 404). History: [RELEASE-AND-VERIFICATION](RELEASE-AND-VERIFICATION.md). |
| R9 | CI "green" in review doc vs RED on GitHub | Review fixes are local-only. | `origin/main` `6b848f1` vs unpushed HEAD `6fd6028`; recent main runs fail on `Ideology.tsx` hooks — precisely what local HEAD fixes. |
| R10 | Release pin at earlier tag vs current pin | Chronological, not contradictory. | Tag snapshot read an earlier tag; `data/latest-release.txt` updated after publish; live `/api/health` reports `data-20261117-T213500`. Earlier tag excluded by `check-doc-truth.sh`. |
| R11 | Claim of a bare `push:` in `ci.yml` | False — corrected. | `ci.yml:3-5` has `push: branches: [main]`, plus `pull_request:` and `workflow_dispatch:`; `DEPLOYMENT.md:71` was right. |

## NOT PROVEN register

Resolvers must produce executable evidence before any of these become claims.

| Claim | Why unresolved | Required resolver |
| --- | --- | --- |
| Which database identity backs "published corpus" for local audit runs | Unlabelled DB in local audit runs | Label the DB path/queries used by each audit run |
| Real date of the "2025-11-12" research | Git first-add is 2026-11-12 (9 occurrences) | Author/source provenance for the research files |
| Whether `source_license` seeding ever runs in production | `ensure_source_licenses()` defined but uncalled; working DBs have 0 rows | Trace a startup/CLI call path in the deployed image |
| Exact Vercel build commit | Strongly inferred `6b848f1`; no deploy ID in headers | Vercel deployment ID / build log |
| Client-side rendering of SPA routes | SPA fallback proven, route rendering not | Browser session with JS enabled |
| Runtime read-only enforcement | No mutation attempted in a read-only audit | Controlled mutation attempt against a disposable instance |
| Deployment ordering (backend then frontend) | Not observed during the read-only probe | Observe a real deployment and record order |
| Live robots/licence bytes for 2026-11-20 | Offline audit could not fetch them | Re-fetch live bytes with timestamped evidence |
