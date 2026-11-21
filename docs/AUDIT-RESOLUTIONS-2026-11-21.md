# Audit contradiction resolutions — 2026-11-21

Companion to `docs/GAP-ANALYSIS-2026-11-21.md`. Records contradictions surfaced
by the documentation review and their adjudication under the policy below.

## Resolution policy (applied in order)

1. **Executable evidence beats prose.** Current source, database queries, API
   responses, CI/CLI output and generated artifacts outrank any document claim.
2. **Scope before conflict.** If two numbers differ, first check whether they
   describe different artifacts or definitions. Only call a defect when both
   describe the same thing.
3. **Newer wins on the same topic** — but an explicitly labelled historical
   snapshot is preserved as history, not used to override current state.
4. **In-document addendum/base rules.** A dated "current-state banner" or
   addendum overrides the body of the same file.
5. **Generated artifacts derive from source.** Never hand-edit `openapi.json`;
   regenerate it.
6. **No guessing.** If evidence is unavailable, report NOT PROVEN and name the
   required resolver.

## Resolved contradictions

| # | Contradiction | Verdict | Decisive evidence |
|---|---|---|---|
| R1 | Live switches **2,002** (`/api/dashboard/stats`) vs **1,217** (`/api/export/report`, `/api/traseism/summary`) | **Not a defect — definitional.** Stats counts `switch_group` + `switch_party`; export/traseism count `switch_group` only. | Pinned release DB queried read-only: `switch_group=1217`, `switch_party=785` (sum 2,002), total events 13,144. Source: `backend/routers/api.py:1047-1049` vs `backend/routers/exports.py:72`. A fresh audit agent queried only the *local* DBs (`switch_party=0`) and therefore could not derive 2,002 — the 785 party-switch events exist in the pinned release, not in those local copies. **Residual:** UI/docs do not label the two definitions — add explicit labels and a `docs/API.md` note. |
| R2 | Memberships **7,358** (README, older docs, release asset) vs **7,349** (live API, newest docs) | **Both correct for different artifacts.** 7,358 = raw GitHub release asset; 7,349 = DB after `prepare_db.py` dedupe (9 duplicate closed stints) served at runtime. | Pinned asset `parlament.db`: 7,358 memberships, `journal_mode=delete`, `user_version=1`, header bytes 18/19 = `1,1`. Live `/api/health` and `/api/dashboard/stats`: 7,349. **Current-state truth = 7,349.** |
| R3 | SQLite **WAL** (`docs/ARCHITECTURE.md:385-388`) vs **DELETE** journal mode (prepared release) | **Both correct at different stages.** Release asset is DELETE (read-only filesystem compatibility); local/runtime copies open in WAL. | Pinned asset PRAGMA `journal_mode=delete`; local `data/parlament-real.db` and `data/parlament.db` report `wal`. Trust the release evidence for the shipped artifact. |
| R4 | "No vote tables" (`docs/DATA-ENRICHMENT-RESEARCH.md:28`, `docs/API.md:178-181`) vs populated vote tables in working DBs | **Scope difference.** Pinned release has no vote tables; local working DBs do. | Pinned asset: 18 tables, zero `vote%`. Local `parlament-real.db` has vote tables; working `parlament.db` has 52 votes. Always qualify with "in the published corpus". |
| R5 | OpenAPI **40** vs **41** paths at 2026-11-19, **48** now | **41 was the stale generated file; 48 is current.** | `pipeline/openapi.json` regenerated from `backend.main.app` on 2026-11-21 → 48 paths, including canonical vote/ideology routes; live Render OpenAPI also shows 48 paths but with legacy aliases. |
| R6 | "All 15 features completed" (`docs/STRATEGY-TRANSPARENCY.md:472`) vs genealogy 0 links, poller disabled, no blog/donation UI | **Historical claim, withdrawn.** Fresh audit tallied **11 PRESENT, 6 PARTIAL, 0 wholly absent** across the document's 17 rows (two duplicates), so "all 15 completed" is unsupported. | Feature-by-feature source check in `POST-INITIAL-AUDIT-2026-11-21.md` §3; master checks: 0 non-null genealogy columns; `render.yaml:28` `PARLAMENT_POLL_INTERVAL_MIN: ""`. |
| R7 | Error-tracking "PASS / hook available" (`EVIDENCE.md`, `WAVE-4-COMPLETION.md`) vs no such file | **Withdrawn.** No `frontend/src/hooks/`, no `useErrorBoundary` references, no tracked file. | `EVIDENCE.md:3-17` (2026-11-21 correction) plus master `ls` / `grep` / `git ls-files` checks. |
| R8 | UI gate RED (3 routes, React #310) vs 18/18 vs 24/24 vs "NOT PROVEN" | **All true in their scope; 24/24 is current for the repo, production remains NOT PROVEN.** | 2026-11-19 snapshot RED; Wave 1 integrated 18/18 zero JS errors; 2026-11-21 widened `scripts/ui_validate.py` to 24 routes; master re-ran it locally: 24/24, zero JavaScript errors, zero axe violations. A fresh agent repeated it: 24/24 with a local backend, but 23/24 against the live API proxy because `/api/analytics/ideology` 404s. The `DASHBOARD-VERIFICATION.md` addendum is correct **for its own audit only**. |
| R9 | CI "green" in review doc vs RED on GitHub | **Review fixes are local-only.** | `origin/main = 6b848f1`; local HEAD `3eb3c0a` unpushed; all six recent main CI runs failed on `Ideology.tsx` rules-of-hooks. Both statements are correct in their scope. |
| R10 | Release pin at an earlier tag vs current `data-20261117-T213500` | **Chronological, not contradictory.** | Tag snapshot vs `data/latest-release.txt` updated after publish; live `/api/health` reports `T213500`. The earlier tag remains in historical docs and is intentionally excluded by `scripts/check-doc-truth.sh`. |
| R11 | Claim that `ci.yml` has a bare `push:` with no branch filter | **False — corrected.** | `ci.yml:3-5` has `push: branches: [main]`, plus `pull_request:` and `workflow_dispatch:`. `docs/DEPLOYMENT.md:71` was right; the earlier GAP-ANALYSIS line was wrong and has been corrected. |

## Still open (NOT PROVEN / needs owner decision)

- Which exact commit Vercel built from: strongly inferred `6b848f1`, no deploy ID in headers.
- Runtime read-only enforcement: no mutation attempted in a read-only audit.
- Client-side rendering of SPA routes: requires a browser session.
- Blog/SEO/donations and self-sustainability Phase 4: strategy only; owner inputs (recipient, cron config) outstanding.
