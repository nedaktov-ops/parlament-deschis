# Remediation Strategy — Audit Findings → Verified Fixes

**Status:** active reference. Every change made after `2026-11-17` must be checked against this document before and after implementation. **Source of findings:** the 20-agent read-only audit (recipes at `/tmp/opencode/parlament-audit-recipes.md`, consolidated report delivered `2026-11-17`). Phase 1 (P0–P4) was implemented and merged (`5134231`, `1f4df92`); **Phase 2 (P5) below covers the evidence-verified residuals.** **Web-standard source:** Chrome `modern-web-guidance` skill version `2026_11_10-47b4c80e`, retrieved guides: `accessibility`, `responsive-table`, `dialog`, `persistent-toast-notifications`; project browser policy in `AGENTS.md`.

---

## 1. Non-negotiable principles

1. **Evidence before edits.** Every finding must be re-read in the current code (`path:line`) before a fix is written. If the code changed since the audit, re-verify the finding or drop it. No fix based on an agent's memory.
2. **Smarter alternative before code.** For each finding, ask: is the right fix a config change, a data-shape correction, a deletion of dead code, or documentation? Prefer the smallest change that removes the root cause. Do not paper over caching with cache-busting query strings; do not translate a UI by hardcoding strings in components; do not "fix" a feature by hiding it.
3. **Non-destructive execution.** One branch per phase, one checkpoint commit per work item, `--no-verify` only for checkpoint commits (CI gate runs on PR). Keep DB backups (`data/*.bak-*`) untouched. Never rewrite the pinned dataset or production release during code work.
4. **Verification loops.** After each work item: targeted test/build → full gate (`uv run ruff check pipeline backend scripts tests`, `uv run pytest tests/ -q`, `npm run build`) → evidence in commit message. UI changes additionally: `python3 scripts/ui_validate.py <dev-server>` (Playwright + axe).
5. **Rollback is a path, not a promise.** Each checkpoint commit is independently revertable; config changes record the previous value in the commit message; no schema/data rewrites in this remediation.
6. **Honesty is a feature.** Never present a derived value as observed, a stale value as current, an empty result as "no data" when it may be an error, or a 24h-cached response as "real-time". Fix the label or fix the mechanism.

## 2. Web-guidance constraints (verified quotes, applied where relevant)

- `accessibility`: "**Do use the `scope` attribute on `<th>` elements**" → all data tables get `scope="col"`/`scope="row"`.
- `accessibility`: "**Provide skip links** prior to repeated content like site headers with navigation" with target `<h1 id="content" tabindex="-1">` → add one skip link, target the route's `<h1>`.
- `accessibility`: "**Update single-page application (SPA) titles during page transitions**" and "**Do declare changes in the page's human language**" → on route change set `document.title`; on language toggle set `document.documentElement.lang`.
- `accessibility`: "**Manage focus correctly to and from updated content** … focus immediately moves to the dialog box, is restricted to the contents … returns to the element that originally triggered" → dialogs use the existing trap/restore pattern; no new hand-rolled dialogs.
- `accessibility`: "**Use `:focus-visible` when styling focus indicators** … Prefer `outline` … Pair custom focus outlines with `outline-offset`" → unify focus rings; no `outline:none` without replacement.
- `responsive-table`: use a `.table-wrapper` with `tabindex="0"`, `role="region"`, an accessible name, and `@container` queries for narrow containers — not ad-hoc `overflow-x-auto` everywhere.
- `persistent-toast-notifications`: "**Toast notifications must be used to provide non-critical, supplemental information** … Notifications that require immediate attention should instead use … inline banners" → switch alerts remain an inline `role="alert"` banner (already correct); do **not** rewrite them as toasts. The guide's `popover="manual"` rules apply only if toasts are introduced later (they are not).
- Project browser policy (`AGENTS.md`): Baseline-widely-available features need no fallback; `popover` needs feature-detect + `@oddbird/popover-polyfill` only when missing; all buttons need `type="button"`; verify WCAG AA contrast on touched UI.

## 3. Phase plan and fleet recipes

Each recipe below is written for one subagent with **exclusive file ownership**. Agents run in parallel only on disjoint files. Every agent prompt must include: project path, "READ current code before editing", the exact file list, the specific root cause from the audit, the guide quote that applies, the verification command, and "report evidence, no claims".

### P0 — Correctness blockers (must be green beforeUI polish)

| ID | Fleet recipe (exclusive ownership) | Root cause / intended fix | Gate |
|---|---|---|---|
| P0-A | `frontend/src/components/LiveFeed.tsx` only | Two-argument component drops `chamber`/`legislature` props → one props object; add `cache:"no-store"` only if CDN rule (P0-B) cannot cover it. | `npm run build`; dev-server probe via Playwright |
| P0-B | `vercel.json`, `backend/main.py` headers only | Mutable analytics cached 24h at edge → `no-store` for `/api/events/recent`, `/api/about`, `/api/analytics/*`, `/api/export/*`; keep immutable static assets cached. Record previous header strings in commit message. | `grep` header diff; `ui_validate.py` |
| P0-C | `frontend/src/components/Hemicycle.tsx` only | Infinite loop at 1–2 members → bound rows to `n`, remove clamp-driven deadlock; add a unit-testable pure helper. | `npm run build`; Node/tsx assertion script |
| P0-D | `pipeline/sources/cdep_committee.py`, `pipeline/cli.py` committee gate only | Strict gate counts changed fragments, so idempotent re-runs fail → gate on `committees + unchanged` or explicit failure count. | `pytest tests/test_cdep_committee.py tests/test_cli.py -q` |
| P0-E | `backend/queries.py` `serialize_event` only | `source_url` typed/consumed but never returned → add the field from evidence. | targeted API test |
| P0-F | `backend/cache.py`, `api.py` waves POST only | TOCTOU stale write-back + waves POST without invalidation → generation counter or in-lock store; invalidate on every write path. | new cache unit tests |

### P1 — Romanian-first and navigation

| ID | Fleet recipe | Root cause / fix | Gate |
|---|---|---|---|
| P1-A | `frontend/src/i18n.ts` only | ~200 namespaced keys absent → add `ro` + `en` entries for every `t("ns.key", "default")` call; no component edits; measure with a script that diffs keys used vs defined. | key-diff script = 0 missing; `npm run build` |
| P1-B | `frontend/src/router.tsx` only | Orphan routes, wrong GitHub URL, missing focus/title/language sync, no skip link, nav crowding → link Senate/Legislature/Party routes, correct URL, add `notFoundComponent`, SPA title+lang effect, skip link, "More" nav tier. | `ui_validate.py`; key-diff; build |
| P1-C | `frontend/src/pages/*.tsx` (data fidelity subset) | Hardcoded 3381/3113/638/108/6 → derive from API totals or remove literals; Senate fallback must never show deputy rows; loyalty scope column honesty. | `ui_validate.py`; grep for stale literals |

### P2 — Accessibility beyond axe

| ID | Fleet recipe | Root cause / fix | Gate |
|---|---|---|---|
| P2-A | `frontend/src/pages/*.tsx`, `components/*.tsx` table and control semantics | `scope` on all `<th>`; wrappers with `tabindex=0`/`role=region`/name; labels for repeated links; remove `aria-label` on generic spans; About modal focus trap. | `ui_validate.py` + static `scope` audit |
| P2-B | `frontend/src/index.css` only | Global overrides collapse slate-500/600 and shrink arbitrary text sizes → remove blunt overrides, express muted colour as one token, restore true font sizes; unify focus ring; delete dead CSS. | visual diff via Playwright screenshots before/after |

### P3 — Backend / data correctness

| ID | Fleet recipe | Root cause / fix | Gate |
|---|---|---|---|
| P3-A | `pipeline/analytics.py` only | Committee-control future chairs; generational-shift missing active filter; wave unknown-legislature handling. | new pytest cases with seeded data |
| P3-B | `backend/routers/api.py` only | Leaderboard scope mixing; search LIMIT-before-filter; duplicate export endpoints; unsupported `/events/recent` params. | endpoint tests |
| P3-C | `backend/routers/exports.py` only | Report ignores scope → apply filters to all blocks or drop params; no-store headers for attachments. | scope parity test vs analytics endpoints |
| P3-D | `pipeline/events.py`, `reconcile.py`, `identity.py`, `coverage.py` only | Fabricated party dates/end reasons, cross-legislature closure, identity merges, "full" coverage with wrong seat counts → carry source reasons, scope by legislature, wire review path, per-legislature seats. | pipeline tests; no data rewrite |

### P4 — Credibility, tests, docs, infra

| ID | Fleet recipe | Root cause / fix | Gate |
|---|---|---|---|
| P4-A | `tests/` only | Vacuous Senate tests, zero export-report/leaderboard/control/timeline tests, untested cache → behavioural tests with FakeClient and seeded DB; frontend smoke test script. | `pytest -q` green with new tests |
| P4-B | `docs/` and root `*.md` only | Stale 3381/6623, old release tag, "not yet computed" claims, party genealogy claimed populated, Senate gap disproven → align with current DB/API; add ADRs for caching and manual release. | doc grep for stale literals; read-through |
| P4-C | `.github/workflows/`, `Dockerfile`, `render.yaml`, `vercel.json` only (coordinated with P0-B on vercel.json) | GITHUB_TOKEN pin push can't trigger deploy; cache lost on failure; failure issues never close; CI unauthenticated download; action pinning; rollback dry-run smoke. | workflow lint; dry-run |

## 4. Decision rules for "fix vs smarter alternative"

- **Real-time alerts:** if events never change at runtime (`render.yaml` poller disabled), the honest fix is either enable a poller with DB write rights or relabel "real-time" as "on release". Do not keep a 60s poll against immutable data.
- **Loyalty score:** if inputs are not defensible, rename to "observed switch rate" and show the numerator/denominator rather than inventing vote-based data. A transparent index with visible inputs beats a moral label.
- **Empty features:** if a data gap cannot be filled (party genealogy, mandate roles), remove the dead UI or label the gap; never fabricate links.
- **i18n:** if ~200 keys are missing, fix the dictionary once; do not add per-component translations.
- **Caching:** fix cacheability semantics at the HTTP layer; do not add per-request random query strings to defeat caches.

## 5. Global acceptance gates (every phase)

1. `uv run ruff check pipeline backend scripts tests` — clean.
2. `uv run pytest -q` — no new failures; latest integration-tree run 2026-11-19: 259 passed.
3. `npm run build` — passes (tsc + vite).
4. `python3 scripts/ui_validate.py http://127.0.0.1:5174` — target: 18 routes with no console errors and no axe violations, for any frontend change. As of 2026-11-19 the production run FAILS on 3 routes (React #310), so this gate is RED until P0-1/P0-2 land.
5. PR CI (`test`, `audit`, `docker`) green; squash-merge; production health + endpoints still serving the release pinned in `data/latest-release.txt` until a data change is explicitly approved.
6. Every commit message states: finding ID, root cause, evidence, gate output, rollback (revert hash).

## 6. Rollback matrix

| Change type | Rollback |
|---|---|
| Code commit | `git revert <checkpoint-sha>` |
| Header/config change | commit records old value; revert restores it |
| Data/workflow change | never in phases P0–P4 except explicit approval; `git revert` pin commit + previous GitHub release remains available |
| Translation dictionary | revert single commit; no runtime data affected |

## 7. Traceability (audit finding → phase)

P0: #1 F2/F8, #2 F2/B4/I1/X1, #3 F4/X1 (P1-A for dictionary), #4 F6, #5 B4, #6 B4, #7 I1 (P4-C), #8 P1, #9 P1, #10 B3 (P4-C/B hardening), #11 P3 (verify release asset, do not rewrite), #12 F2.
P1: F1 orphan routes, X1 English-first, F3 stale numbers.
P2: F7 skip/focus/scope/modal, F5 CSS/print.
P3: B2/B1 analytics, P1 parsers, P2 business logic.
P4: T1 tests, D1/Q1 docs, I1 infra, X1 product labels.

**This document is the reference point: before each change, state which phase/ID it belongs to and after each change, record the gate evidence.**

---

## 8. Phase 2 (P5) — evidence-verified residuals

Re-verified on merged `main` (`1f4df92`) on 2026-11-17, not assumed. Each item below was checked with a concrete command; if a follow-up agent finds the evidence stale, it must report and drop the item, not force a change.

| ID | Fleet recipe (exclusive ownership) | Verified evidence | Intended change / smarter alternative | Gate |
|---|---|---|---|---|
| P5-A | `frontend/src/pages/ElectoralDynamics.tsx`, `components/{DefectionSankey,DefectionSankeyCurrent,DefectionsList,PartyFlowDetail,CurrentLegislatureView}.tsx`, `frontend/package.json`, `frontend/package-lock.json` | grep: 5 page/component modules have **0 importers**; the 2 Sankey components are imported **only** by the dead `CurrentLegislatureView`; `d3`, `@types/d3`, `@tanstack/router-devtools` have no imports (source uses `d3-scale`, `d3-scale-chromatic`, `d3-sankey`) | Delete dead modules and unused deps; keep `@types/d3-sankey` (verify it is actually needed). Deleting is the smarter alternative — no refactor, no rewrite. Confirm `/electoral` still redirects and 18 routes still render after removal. | `npm run build`; `ui_validate.py`; grep 0 dangling imports |
| P5-B | `frontend/src/components/TimeSlider.tsx`, `frontend/tsconfig.json`, `frontend/src/router.tsx` (TimelineChart import line only) | `TimeSlider` effect deps `[playing, value, maxMs, onChange]` recreate the 300 ms interval on every tick; `tsconfig` has `strict` but lacks `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`; ECharts chunk 487 kB is on the **initial** route via `LiveDashboard` | Use refs for the latest `value`/`onChange` so the interval depends only on `[playing, maxMs]`; enable stricter tsc flags **only if tsc stays green** (fix genuine errors, do not add `any`/suppressions); lazy-load the chart below the fold if it is imported eagerly. No new dependencies. | `npx tsc --noEmit`; `npm run build`; node assertion that interval setup count is stable across ticks |
| P5-C | `frontend/src/pages/Report.tsx` + ONLY live components containing `text-[10px]`/`text-[11px]` (PartyProfile, Traseism, PersonDeepDive, MembershipGantt, About, PersonDrawer) | `Report.tsx:175,281` tables lack the overflow wrapper used elsewhere; 10/11 px classes render small (P2-B removed the override hacks, so they are literally 10/11 px) | Add `overflow-x-auto` + keyboard scroll wrapper (`tabindex=0 role=region aria-label`) to Report tables; bump 10/11 px to 12 px in live components using the existing class names (no new CSS, no dead-file edits) | `ui_validate.py`; Playwright print emulation of `/report` |
| P5-D | `pipeline/db.py`, `scripts/prepare_db.py`, `tests/test_db_schema.py`, `tests/test_prepare_db.py` | ~7 unindexed FKs; `uq_stint` includes `post_id` (100 % NULL) and admits duplicate closed stints; `user_version=0`, no migration gate; `ensure_schema` + destructive legacy merge run at startup; `prepare_db` skips `foreign_key_check` | Add indexes on the FK columns actually queried; add a partial unique index for closed stints; add `foreign_key_check` to `prepare_db`; gate the one-off legacy merge behind a `user_version` check so a read-only runtime never mutates. **No data rewrite, no change to shipped DB files.** | `uv run pytest tests/test_db_schema.py tests/test_prepare_db.py -q`; read-only PRAGMA on a copy |
| P5-E | `.github/workflows/ci.yml`, `Dockerfile`, `scripts/download_dataset.py`, `tests/test_dataset_download.py` | actions pinned to mutable tags; Dockerfile in-build dataset download unauthenticated; dataset digest self-attested by the release. Action SHA pinning requires resolvable hashes — **do not guess**; if unavailable read-only, document as residual | Pass `GITHUB_TOKEN` to the Dockerfile download if the build step supports secrets, otherwise document; pin action SHAs only from a resolvable source; add a test proving a tampered digest is rejected (already partly covered). No new secrets invented. | YAML parse; `ruff`; `pytest tests/test_dataset_download.py -q` |
| P5-F | `tests/` (files not owned by earlier phases), `scripts/` standalone guards | 6 tests skip in CI because `data/cache/cdep` is gitignored; standalone guards (`ui_validate.py`, `check_livefeed_props.mjs`) are not wired into CI | Decide per skipped test: check in a **trimmed** fixture only if it preserves the parser contract, otherwise keep skip with an explicit reason comment. Add the two standalone guards to a CI job as non-blocking evidence (do not require Playwright if the runner lacks it — print SKIPPED instead of failing). | `pytest -q`; workflow YAML valid; CI green |

### Phase 2 decision rules
- **Deletion over refactor:** dead code with 0 importers is deleted, not modernised (strategy §1.2).
- **Strictness over suppression:** if a tsc flag surfaces errors, fix the types; if that is disproportionate, revert the flag and document why — never `any` cascades.
- **No data churn:** the pinned release asset is still WAL-mode; the entrypoint guard now fails loudly on a future bad asset. Republishing the 22 MB dataset is NOT part of Phase 2 — it needs an explicit data-release decision with its own verification.
- **No guessed hashes/secrets:** action SHAs and new credentials are only introduced with a resolvable source.

### Phase 2 acceptance
All §5 global gates stay mandatory; additionally: 0 dead-module imports, 0 missing i18n keys (`/tmp/i18n-extract.mjs`), `ui_validate.py` 18/18 is the target but is RED today (3 routes fail with React #310), PR CI `test`+`audit`+`docker` green, production health unchanged until an explicit data release.

### Phase 2.5 — Fresh dataset release (P3-D propagation) — delivered 2026-11-17

**Goal:** propagate the P3-D pipeline-honesty fixes into the shipped database (party switch events were absent / pre-fix values).

**Execution (evidence-led):**
1. First attempt: Data workflow `44147411835` via `workflow_dispatch` → failed at Collect (empty runner cache → live fetch → `ConnectTimeout` to `www.cdep.ro`). Cache restore hit an effectively empty entry.
2. Local rebuild attempts failed strict (live `cdp.ro` profile fetch errors; invalid cache entries → offline fallback also failed).
3. Offline re-derivation on a copy of the verified local corpus (`derive_group_events`, `derive_party_events`, `derive_all_switch_waves`) → fresh derived state: 13,144 events (incl. 785 `switch_party` + related party events), waves 142.
4. `audit-corpus --strict` on the fresh DB → **exit 0**, 275 known errors, **0 new**.
5. `scripts/prepare_db.py` on fresh DB → `journal_mode=delete`, `user_version=1`, `integrity ok`, `foreign_key_check` clean, **header bytes 18/19 = 1,1 (DELETE)**.
6. Published release `data-20261117-T213500` (assets: `parlament.db` sha256 `7298ffd…`, `manifest.jsonl`, `audit-report.json`).
7. Pinned via PR #31 → merged (`b8701f8`) → Render deploy picked it up → prod `/api/health` now reports `data-20261117-T213500`.

**Gates:** strict audit exit 0 · prepare verified · prod health ok on new release · prod endpoints serving new data (committees, waves, events).

**Residual:** scheduled/automated data refresh remains best-effort pending `cdp.ro` availability; recovery path = local rebuild + publish (as executed).

---

## 9. Known residuals — false source comments (documentation-only pass)

The documentation-truthfulness pass (P0-6) does not own code files, so the two
verifiably false comments below are recorded here for their code owners instead
of being silently left in place. Both were read directly on 2026-11-19.

| Location | False text | Verified truth | Owner |
|---|---|---|---|
| `pipeline/cli.py:611-614` | "verified on the 2026-11-17 release: `/api/committees = 0`, `/api/analytics/switch-waves = 0`" | Live 2026-11-19: `/api/committees` returns 23 entries; `/api/analytics/switch-waves` returns 142. Zeroes were true only of the *first* release. | P0-3 |
| `backend/routers/api.py:337-341` (docstring of `committees()`) | "Committee tenures are not ingested yet, so the current corpus returns an empty list" | Live 2026-11-19: the route returns 23 committees with active dated memberships. | Lead at integration (no Wave 1 owner) |

No code was modified by P0-6. Re-check these comments after the owning parts
land; remove them from this table only when the source has been corrected.
