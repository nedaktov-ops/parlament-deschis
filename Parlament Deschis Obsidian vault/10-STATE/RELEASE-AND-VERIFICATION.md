---
id: release-verification
type: reference
title: Release Pin and Verification Gates
description: Reference for the release pin, count definitions, journal modes, audit baseline and exact gate commands with expected outputs.
status: active
authority: derived
tags: [type/reference, lifecycle/active, domain/ops]
source_paths: [docs/COMPREHENSIVE-REVIEW-2026-11-21.md, docs/AUDIT-RESOLUTIONS-2026-11-21.md, docs/POST-INITIAL-AUDIT-2026-11-21.md]
created: 2026-11-21
updated: 2026-11-22
source_commit: 6fd6028
verified: 2026-11-22
---

# Release pin and verification gates

> **Current-state addendum (2026-11-21):** the pin below was superseded by
> `data-20261121-votes-001` (sha256 `eabdb857…`, 189 votes / 24,682 positions,
> strict audit 275 known / 0 new, DELETE journal, 15 licence rows). The
> historical figures below are preserved as a dated snapshot. Evidence:
> [EXECUTION-LOG](EXECUTION-LOG-2026-11-21.md).

Authoritative measurements as of HEAD `6fd6028`. Current-state interpretation
is in [CURRENT-STATE](CURRENT-STATE.md); disputes in
[CONTRADICTIONS](CONTRADICTIONS.md).

## Release pin

- Live and local pin: `data-20261117-T213500` — the latest GitHub release and
  the value served by `/api/health` (R10). At the tag itself the pin read an
  earlier, superseded tag; the marker was updated after publication.
- Pinned asset `{sha256 7298ffd1…}` has 18 tables and **no** `vote`,
  `vote_position` or `vote_import_run` table. Votes exist only in gitignored
  working databases and have never been released.

## Raw vs prepared membership counts

- **7,358** memberships in the raw GitHub release asset.
- **7,349** memberships in the prepared runtime DB served live.
- The difference of 9 is deliberate: `prepare_db.py` removes nine duplicate
  closed stints. The prepared count is the current-state truth (R2).

## Journal modes

- Shipped asset: `journal_mode=delete` (read-only filesystem compatibility,
  `user_version=1`, header bytes 18/19 = `1,1`).
- Local/runtime working copies: `journal_mode=wal`.
- Both are correct at their lifecycle stage; trust the release evidence for
  the shipped artifact (R3).

## Switch definitions

Two measures describe the same corpus and must be labelled (G-P0-05):

- `switch_group` — **1,217** events; the only measure counted by
  `/api/export/report` and `/api/traseism/summary`.
- `switch_party` — **785** events, present in the pinned release asset (local
  working DBs report zero).
- `/dashboard/stats` reports **1,217 + 785 = 2,002** across **142** waves.
  Definitional, not a defect (R1).

## Audit baseline: 275 known / 0 new

`audit-corpus --strict` returns **275 known errors, 0 new** and exit 0. "275
known" is the accepted evidence baseline for the pinned corpus; the gate
fails only on a *new* departure. The four `vote_evidence` "no snapshot hash"
errors live in a gitignored working DB, not in the release corpus used by CI.

## UI gate history

| Snapshot | Result |
| --- | --- |
| 2026-11-19 | RED — 3 routes, React #310 hooks failure |
| Wave 1 integrated | 18/18 routes, zero JavaScript errors |
| 2026-11-21 widened gate (`scripts/ui_validate.py`) | 24/24 routes locally, zero JavaScript errors, zero axe violations |
| Fresh agent vs live API proxy | 23/24 — `/api/analytics/ideology` 404 in production |

24/24 is proven for the repository only; production remains NOT PROVEN (R8).

## Doc-truth gate

`bash scripts/check-doc-truth.sh` reports `false-claims: 0` at local HEAD. It
checks a fixed set of precise false assertions; after F8 the bare-token
pattern was narrowed so legitimate research/licence statements are not
flagged. Creative phrasings for the external Romanian civic source (ro_281)
and old release tags are intentionally excluded by the checker.

## Exact gate commands and expected outputs

Run from the repo root at HEAD `6fd6028`:

```
uv run pytest -q
  → 384 passed, 1 warning in 65.38s; EXIT 0
uv run ruff check backend pipeline scripts tests
  → All checks passed!; EXIT 0
cd frontend && npm run lint
  → 0 errors, 7 pre-existing warnings; EXIT 0
cd frontend && npm run build
  → built in 9.36s; EXIT 0
audit-corpus --strict            # against the README/pinned DB
  → 275 known errors, 0 new; EXIT 0
bash scripts/check-doc-truth.sh
  → false-claims: 0; EXIT 0
python3 scripts/ui_validate.py
  → 24/24 routes, zero JavaScript errors, zero axe; EXIT 0
workflow YAML parse
  → 5/5 parsed; EXIT 0
git diff --check
  → clean; EXIT 0
```

CI on `main` is RED despite these local results because the fixes are
unpushed — see [GIT-POSITION](GIT-POSITION.md).

## Addendum (2026-11-22) — commit and deployment parity (superseded by the Final state note at the end of this section)

- Local commit `efdbba71705d154767754766b4d4e8b6fe0603a6` contains the repair
  waves, legislature slider and Deep Dive redesign. Gates at that tree:
  `npm run lint` 0, `npm run i18n:check` 724/724 clean, `npm run build` 0,
  `pytest -q` 431 passed, all `scripts/check-*` guards 0, `vault_lint.py` pass.
- GitHub `origin/main` and the Vercel production deployment both still point at
  `618849af13d65db89c4ce585954cdd0edc79a7a8`; the Vercel alias serves bundle
  `/assets/index-DjwGQole.js`, which lacks the new section markers.
- Render health is HTTP 200 / `status ok`, but reports `persons=3381`,
  `memberships=6614`, release `data-20261121-votes-001` versus local
  `3388` / `7349` / `null`. Render's deployed SHA is NOT PROVEN without a
  Render API token.
- Therefore the local preview is **not identical** to GitHub, Vercel or Render.
  Do not treat local green as production green. Full evidence and the ordered
  next steps are in
  [DEEP-DIVE-REDESIGN-2026-11-22](../50-RESEARCH/DEEP-DIVE-REDESIGN-2026-11-22.md).
- **Update (same day):** branch pushed, PR #73 opened, and two CI fixes landed
  (`99f40d3`, `a20c419`). At head `a20c419` the required checks `test`, `audit`,
  `docker`, `evidence-guards` were all SUCCESS in GitHub Actions.
- **Final state:** PR #73 was merged into `main` as
  `39ad23ebb36ab563fc76bf5c0159c39061543398` with the owner's authorisation;
  branch protection was restored immediately afterwards. All checks on the
  merge commit, including `docker`, are SUCCESS. Vercel production deployment
  `dpl_9CKRtBH2BwwXpuesU7twUrfwMoHZ` points at `39ad23e` and serves the new
  bundle; Render serves the merged `/api/votes.scopes` field. Both hosts pass
  `scripts/check-deployment-status.sh`. The earlier parity warning is resolved
  for **code version**; Render's dataset counts still reflect the pinned
  release (`data-20261121-votes-001`), by design. Evidence:
  [DEEP-DIVE-REDESIGN-2026-11-22](../50-RESEARCH/DEEP-DIVE-REDESIGN-2026-11-22.md).

## Addendum (2026-11-22) — brand logo release

- Merged `77fa2526906eae2fe35c6bff0ce78bf2256de876` (PR #74) into `main`; all four required checks were green and branch protection was restored after the owner-authorised merge.
- Vercel production `dpl_HR5kG2rSDCnh9rSsZjbUmhydrsWX` is READY on `77fa252`; Render serves the new logo endpoints (`/api/logo/list` → 200, empty store → inline fallback) and the pinned dataset release. Both hosts pass `scripts/check-deployment-status.sh`.
- Local gates at the merged tree: pytest 434 passed, ruff clean, npm lint/build 0, i18n clean, design guard 35/35, doc-truth 0. Full `verify-deploy.sh` remains NOT PROVEN without credentials.
