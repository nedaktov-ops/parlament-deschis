# Comprehensive Project Review — 2026-11-21

**Scope:** `/home/nedaktov/parlament-deschis` (local tree at `6b848f1`) and the
associated GitHub repository `nedaktov-ops/parlament-deschis` (default branch
`main`, same SHA). Work was performed on isolated branch
`review/completion-20261121`; nothing was pushed, deployed, or merged.

**Method:** one supervising master agent + four parallel specialist agents with
exclusive file ownership, followed by independent master verification of every
claim. Rules applied (from `docs/REMEDIATION-STRATEGY.md`): evidence before
edits, smallest change that removes the root cause, deletion over refactor,
no data rewrites, no weakened gates, no fabricated values.

---

## 1. GitHub/repository state found

| Item | Observed |
| --- | --- |
| CI on HEAD (`44879894155`) | `test` job **RED**; `audit`, `evidence-guards` green; `docker` skipped |
| Root cause | 4 `react-hooks/rules-of-hooks` errors in `frontend/src/pages/Ideology.tsx` |
| Branch protection on `main` | **Absent** (`gh api …/branches/main/protection` → HTTP 404) — 7 consecutive failing pushes reached main |
| Open issue #14 | Automated dataset refresh/deployment failure; 11 failed data runs |
| Open PRs | 9 (8 dependabot, 1 deploy-sync) |
| Live API | healthy; `data-20261117-T213500`, 3,388 persons, **7,349** memberships (docs said 7,358) |

---

## 2. Incomplete components fixed

| ID | Component | Root cause | Fix | Gate/evidence |
| --- | --- | --- | --- | --- |
| F1 | CI red | Hooks called after early returns in `Ideology.tsx` | All hooks moved above first return; no lint suppressions | `npm run lint` → **0 errors** (7 pre-existing warnings); build exit 0 |
| F2 | `GET /api/analytics/ideology`, `/api/votes/scorecard` | Only double-prefixed `/api/api/...` routes existed; scorecard also shadowed by `/votes/{vote_id}` | Canonical routes added, legacy aliases kept off-schema, static route ordered first | 200 on canonical paths; 26 new convergence tests |
| F3 | Vote date filters | Raw lexicographic compare of ISO bounds against `DD.MM.YYYY` → always empty; bad bounds silently ignored | Calendar-date parsing, accepts both formats, 422 on malformed/reversed ranges | behavioural tests |
| F4 | `meta` missing on analytics | SPEC §3.6 unmet for ideology, vote-cohesion, vote-activity | `meta: {generated_at, count}` added; TS interfaces updated | tests + source inspection |
| F5 | Stale docstring | `/api/committees` claimed "not ingested yet, returns empty" while serving 23 | Corrected; generated `openapi.json` regenerated 41→48 paths | `grep` + regeneration output |
| F6 | Vote frontend | Error conflated with empty; missing retry; source column showed a hostname instead of a count/link; wrong i18n entity; keyboard/color defects | Distinct empty/error UI with retry, real columns and linked source, full ro/en keys, semantic table, contrast and reduced-motion fixes | `npm run lint/build`; axe 0 on `/Voturi` |
| F7 | Vote provenance backfill | Dedup short-circuit never revisited votes created before hashing → 4 votes with NULL `snapshot_hash` | Importer backfills missing hash/URL from just-fetched bytes, never overwrites, counted in output; 3 new offline tests | `pytest tests/test_vote_hash_backfill.py` → 3 passed |
| F8 | Doc-truth gate RED | `281\.ro` bare-token pattern flagged 37 legitimate research/licence statements | Pattern narrowed to precise false assertions; all other 15 strings preserved | clean 0, seeded-false 5 → exit 1 |
| F9 | Documentation truth | `EVIDENCE.md` claimed a file that does not exist; stale pin/tag/UI-gate claims; `docs/API.md` had no vote/ideology endpoints | Historical snapshots preserved + dated current-state corrections; 8 endpoints documented | `check-doc-truth.sh` → false-claims: 0 |
| F10 | UI gate coverage | Only 18 original routes scanned; 6 newest routes untested | 6 routes added (`/parties`, `/Voturi`, `/radar`, `/grafice`, `/topuri`, `/ideology`) | 24 routes scanned |
| F11 | Accessibility regressions found by the widened gate | `nested-interactive` on dashboard cards, duplicate `landmark-unique` label on `/committees`, `color-contrast` + `scrollable-region-focusable` on `/radar` | Native `<Link>`/`button` instead of role+keyboard shim; unique i18n label; red-400 (5.48:1); focusable labelled region | `ui_validate.py` → **24/24, 0 JS errors, 0 axe violations** |

---

## 3. Verification evidence (final, after all edits)

```
uv run pytest -q                 384 passed, 1 warning in 65.38s   EXIT 0
uv run ruff check backend pipeline scripts tests   All checks passed!  EXIT 0
frontend: npm run lint           0 errors, 7 pre-existing warnings    EXIT 0
frontend: npm run build          ✓ built in 9.36s                     EXIT 0
audit-corpus --strict (README DB) 275 known errors, 0 new              EXIT 0
bash scripts/check-doc-truth.sh  false-claims: 0                       EXIT 0
python3 scripts/ui_validate.py   24/24 routes, 0 JS errors, 0 axe      EXIT 0
workflow YAML parse              5/5 parsed                            EXIT 0
git diff --check                 clean                                 EXIT 0
```

Note: `data/parlament.db` (working DB, 52 votes) reports 4 `vote_evidence`
"no snapshot hash" errors; the pinned release corpus used by CI and the README
(`data/parlament-real.db`) passes 275/0. F7 prevents new occurrences; the 4
existing rows are a documented data residual, not a gate regression.

---

## 4. Residuals (honestly not fixed)

1. **Issue #14 root cause determined, not fixed.** All 11 failures die in
   `Collect and ingest`: `requests.exceptions.ConnectTimeout` fetching
   `www.cdep.ro/.../structura2015.gp?idl=1&cam=2&leg=1990` from GitHub runners,
   stable across five days. The workflow fails loudly and correctly; fixing
   requires source-fetch/retry changes or a different acquisition path and an
   explicit data-release decision.
2. **`main` has no branch protection** — owner-only setting; deliberately not
   changed.
3. **Deployment lag.** Live Render API still serves the old backend (canonical
   `/api/analytics/ideology` → 404 there). Ship backend first, then frontend.
4. **Analytics `meta` is not universal** (other `/api/analytics/*` endpoints)
   and cache TTL is 300 s in `backend/cache.py` vs the 1 h in SPEC §3.6 —
   broader shape/TTL changes were out of scope.
5. **Unowned frontend residuals:** capitalised `/Voturi` route with no nav
   link; hardcoded English headings in `Grafice.tsx`, `Topuri.tsx`, `Radar.tsx`;
   unused `TimelineStrip.tsx` (0 importers) with an empty `onClick` TODO;
   `EmptyState.tsx` unused. Seven pre-existing exhaustive-deps warnings remain.
6. **Data gaps declared elsewhere:** Senate historical profile ingest (identity
   risk), party genealogy (0 links), 281.ro licensing attribution obligations —
   all require source/data decisions, not code edits.
7. `COMPLETION-CERTIFICATE.md` is gitignored (`.gitignore:39`); its correction
   exists locally but is not part of the commit.

---

## 5. Change set

19 tracked files modified, 2 new test files added (see `git diff --stat` on the
branch). No data file, release pin, workflow deployment behaviour, or GitHub
state was mutated. Rollback: `git revert <commit>` on branch
`review/completion-20261121`.
