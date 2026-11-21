---
id: COMPREHENSIVE-REVIEW-2026-11-21
type: evidence
title: "Comprehensive project review — fixes F1–F11 and final gates (2026-11-21)"
description: "Frozen snapshot of the review branch: root cause and gate for each of the eleven fixes, the final verification block, residuals 1–7, and the local-only/unpushed caveat."
status: active
authority: mirror
tags: [type/evidence, lifecycle/active, domain/ops]
source_paths: [docs/COMPREHENSIVE-REVIEW-2026-11-21.md, docs/POST-INITIAL-AUDIT-2026-11-21.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Comprehensive project review — 2026-11-21

> **Frozen evidence snapshot.** Mirrors `docs/COMPREHENSIVE-REVIEW-2026-11-21.md`.
> The gates below were green **on the local review branch only**. Nothing was
> pushed, deployed or merged; live production was still serving the pre-fix
> build at the time. Current reading: [CURRENT-STATE](../10-STATE/CURRENT-STATE.md).

## Scope and method

- Local tree at `6b848f1` / GitHub repository `nedaktov-ops/parlament-deschis` (default `main`, same SHA at review start). Work on isolated branch `review/completion-20261121`; **nothing pushed, deployed or merged**. Vault snapshot `6fd6028`.
- One supervising master agent + four parallel specialists with exclusive file ownership, followed by independent master verification of every claim.
- Rules: evidence before edits; smallest change that removes the root cause; deletion over refactor; no data rewrites; no weakened gates; no fabricated values.

## Repository state found

| Item | Observed |
|---|---|
| CI on HEAD (`44879894155`) | `test` job **RED**; `audit`, `evidence-guards` green; `docker` skipped |
| Root cause | 4 `react-hooks/rules-of-hooks` errors in `frontend/src/pages/Ideology.tsx` |
| Branch protection on `main` | **Absent** (HTTP 404) — 7 consecutive failing pushes reached main |
| Issue #14 | Automated dataset refresh/deployment failure; 11 failed data runs |
| Open PRs | 9 (8 dependabot, 1 deploy-sync) |
| Live API | healthy; `data-20261117-T213500`, 3,388 persons, **7,349** memberships |

## Fixes F1–F11 — root cause and gate

| ID | Component | Root cause | Fix | Gate / evidence |
|---|---|---|---|---|
| F1 | CI red | Hooks called after early returns in `Ideology.tsx` | All hooks moved above first return; no lint suppressions | `npm run lint` → **0 errors** (7 pre-existing warnings); build exit 0 |
| F2 | `GET /api/analytics/ideology`, `/api/votes/scorecard` | Only double-prefixed `/api/api/...` routes existed; scorecard shadowed by `/votes/{vote_id}` | Canonical routes added, legacy aliases kept off-schema, static route ordered first | 200 on canonical paths; 26 new convergence tests |
| F3 | Vote date filters | Raw lexicographic compare of ISO bounds against `DD.MM.YYYY` → always empty; bad bounds ignored | Calendar-date parsing; both formats; 422 on malformed/reversed ranges | Behavioural tests |
| F4 | `meta` missing on analytics | SPEC §3.6 unmet for ideology, vote-cohesion, vote-activity | `meta: {generated_at, count}`; TS interfaces updated | Tests + source inspection |
| F5 | Stale docstring | `/api/committees` claimed "not ingested yet, returns empty" while serving 23 | Corrected; `openapi.json` regenerated 41→48 paths | `grep` + regeneration output |
| F6 | Vote frontend | Error conflated with empty; missing retry; source column showed a hostname; wrong i18n entity; keyboard/colour defects | Distinct empty/error UI with retry, real linked source column, full ro/en keys, semantic table, contrast and reduced-motion fixes | `npm run lint/build`; axe 0 on `/Voturi` |
| F7 | Vote provenance backfill | Dedup short-circuit never revisited votes created before hashing → 4 votes with NULL `snapshot_hash` | Importer backfills hash/URL from just-fetched bytes, never overwrites, counts in output | `pytest tests/test_vote_hash_backfill.py` → 3 passed |
| F8 | Doc-truth gate RED | A bare external-source token pattern flagged 37 legitimate research/licence statements | Pattern narrowed to precise false assertions; other 15 strings preserved | Clean 0; seeded-false 5 → exit 1 |
| F9 | Documentation truth | `EVIDENCE.md` claimed a non-existent file; stale pin/tag/UI claims; `docs/API.md` lacked vote/ideology endpoints | Historical snapshots preserved + dated current-state corrections; 8 endpoints documented | `check-doc-truth.sh` → false-claims: 0 |
| F10 | UI gate coverage | Only 18 original routes scanned; 6 newest routes untested | 6 routes added (`/parties`, `/Voturi`, `/radar`, `/grafice`, `/topuri`, `/ideology`) | 24 routes scanned |
| F11 | Accessibility regressions from the widened gate | `nested-interactive` on dashboard cards; duplicate `landmark-unique` on `/committees`; contrast + focusable-region defects on `/radar` | Native `<Link>`/`button` instead of role+keyboard shim; unique i18n label; red-400 (5.48:1); focusable labelled region | `ui_validate.py` → **24/24, zero JavaScript errors, zero axe violations** |

## Final verification block (after all edits)

```
uv run pytest -q                    384 passed, 1 warning in 65.38s   EXIT 0
uv run ruff check backend pipeline scripts tests   All checks passed!  EXIT 0
frontend: npm run lint              0 errors, 7 pre-existing warnings  EXIT 0
frontend: npm run build             ✓ built in 9.36s                   EXIT 0
audit-corpus --strict (working DB)  275 known errors, 0 new            EXIT 0
bash scripts/check-doc-truth.sh     false-claims: 0                    EXIT 0
python3 scripts/ui_validate.py      24/24 routes, zero JavaScript errors, zero axe  EXIT 0
workflow YAML parse                 5/5 parsed                          EXIT 0
git diff --check                    clean                               EXIT 0
```

The working DB with 52 votes reports 4 `vote_evidence` "no snapshot hash" errors; the corpus used by CI and the README (a **gitignored working DB**, not the pinned release) passes 275/0. F7 prevents new occurrences; the 4 existing rows are a documented data residual, not a gate regression. Against the **live API proxy** the widened UI gate is **23/24** because the ideology endpoint 404s in production. See [RELEASE-AND-VERIFICATION](../10-STATE/RELEASE-AND-VERIFICATION.md).

## Residuals (honestly not fixed)

1. **Issue #14 root cause determined, not fixed.** All 11 failures die in `Collect and ingest`: `ConnectTimeout` fetching the source host from GitHub runners, stable across five days. The workflow fails loudly and correctly; a fix needs source-fetch/retry changes or a different acquisition path plus an explicit data-release decision.
2. **`main` has no branch protection** — owner-only setting, deliberately not changed.
3. **Deployment lag.** Live Render API still serves the old backend (canonical ideology route → 404 there). Ship backend first, then frontend.
4. **Analytics `meta` is not universal** (other `/api/analytics/*` endpoints); cache TTL 300 s in `backend/cache.py` vs 1 h in SPEC §3.6 — broader shape/TTL changes were out of scope.
5. **Unowned frontend residuals:** capitalised `/Voturi` route with no nav link; hardcoded English headings in `Grafice.tsx`, `Topuri.tsx`, `Radar.tsx`; unused `TimelineStrip.tsx` (0 importers) with an empty `onClick` TODO; unused `EmptyState.tsx`; seven pre-existing exhaustive-deps warnings.
6. **Data gaps declared elsewhere:** Senate historical profile ingest (identity risk), party genealogy (0 links), external Romanian civic source (ro_281) licensing attribution obligations — all require source/data decisions, not code edits.
7. `COMPLETION-CERTIFICATE.md` is gitignored (`.gitignore:39`); its correction exists locally but is not part of the commit. Quarantined in [COMPLETION-CERTIFICATE](../70-ARCHIVE/COMPLETION-CERTIFICATE.md).

## Local-only / unpushed

Change set: tracked files modified plus 2 new test files on `review/completion-20261121`; no data file, release pin, workflow deployment behaviour or GitHub state was mutated. Rollback: `git revert <commit>` on that branch. The fixes that make CI green exist **only in the local repository** — `origin/main` (`6b848f1`) and therefore Vercel/Render do not have them. This is why the review's "green" and GitHub's RED are both true in their own scope (R9). Full ledger: [CONTRADICTIONS](../10-STATE/CONTRADICTIONS.md).

## Dated addendum — 2026-11-21 (post-initial audit correction)

The source review reports "19 tracked files modified". The subsequent exhaustive audit checked `git show --stat 3eb3c0a` and found **22 files**; **22** is the corrected count. This addendum records the correction without altering the frozen body above.

## See also

[CURRENT-STATE](../10-STATE/CURRENT-STATE.md) · [RELEASE-AND-VERIFICATION](../10-STATE/RELEASE-AND-VERIFICATION.md) · [AUDIT-2026-11-21](AUDIT-2026-11-21.md) · [GAP-ANALYSIS-2026-11-21](GAP-ANALYSIS-2026-11-21.md) · [GAP-REGISTER](../10-STATE/GAP-REGISTER.md)
