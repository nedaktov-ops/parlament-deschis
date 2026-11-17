# Remediation Strategy — Audit Findings → Verified Fixes

**Status:** active reference. Every change made after `2026-11-17` must be checked against this document before and after implementation. **Source of findings:** the 20-agent read-only audit (recipes at `/tmp/opencode/parlament-audit-recipes.md`, consolidated report delivered `2026-11-17`). **Web-standard source:** Chrome `modern-web-guidance` skill version `2026_11_10-47b4c80e`, retrieved guides: `accessibility`, `responsive-table`, `dialog`, `persistent-toast-notifications`; project browser policy in `AGENTS.md`.

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
2. `uv run pytest tests/ -q` — no new failures; baseline currently 199 passed.
3. `npm run build` — passes (tsc + vite).
4. `python3 scripts/ui_validate.py http://127.0.0.1:5174` — 18 routes, 0 JS errors, 0 axe violations, for any frontend change.
5. PR CI (`test`, `audit`, `docker`) green; squash-merge; production health + endpoints still serving pinned release `data-20261117-T060923` until a data change is explicitly approved.
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
