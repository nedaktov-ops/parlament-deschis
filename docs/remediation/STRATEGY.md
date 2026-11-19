# Remediation Strategy — Parlament Deschis

**Version:** 1.0 · **Date:** 2026-11-19 · **Baseline commit:** `eb069d2b1de953a89489245ef6418a66a7b652ba`
**Status:** ACTIVE — Wave 1 initiated after this file is written.
**Companion files:** `RECIPES.md`, `SUPERVISOR-RECIPE.md`, `STATE.md`

> This document is the single source of truth for all remediation work. No agent may
> change anything outside the scope defined here. The Supervisor compares the
> investigation report, this strategy, and the actual work — and rejects drift.

---

## 0. Governing principles (non-negotiable)

1. **Evidence over assertion.** A fix is done only when a command prints the
   before/after truth. "Should work" is not a checkpoint. No guessing, assuming,
   or presuming — the whole failure mode of this project was vibe-coding.
2. **Non-destructive.** Every change is reversible through the backup layer (§2).
   No `git push`, no force-push, no deploy triggers, no secret use, no deletion
   of data or history. All work happens on isolated branches/worktrees.
3. **Red→Green proof for every bug fix.** First reproduce the failure with a
   command, capture the output, then fix, then re-run the same command and
   capture the pass. Both outputs go into the checkpoint log.
4. **One owner per file.** Agents work in isolated worktrees; file ownership is
   disjoint per wave (§3). The Supervisor checks for out-of-scope edits.
5. **Atomic, conventional commits.** One logical fix = one commit with a message
   like `fix(P0-1): move hooks above early returns (#310)`. No bundling.
6. **Never trust a green test that didn't run.** CI skips are treated as gaps,
   not passes. Verification scripts must be executed, not referenced.
7. **Supervisor is adversarial.** It defaults to REJECT until given raw output.

---

## 1. What I need from the project owner (and the defaults I am using)

I will not block on these — I proceed with the safe default listed. Correct me
any time and the strategy is revised before the affected wave starts.

| # | Decision needed | Safe default I am using | Why |
|---|---|---|---|
| 1 | Confirmation I may write to `/home/nedaktov/parlament-deschis` | "Initiate the process" = yes | Backups make every step reversible |
| 2 | Manual Vercel/Render deploy triggers in `ci.yml` — keep or remove? | **Remove** manual POST steps; rely on Vercel Git integration + Render `checksPass`; keep `deploy-verify.yml` as proof | The current triggers are broken and unchecked (A4); Git integration demonstrably serves current assets |
| 3 | GraphQL — fix or delete? | **Fix and keep** | It is documented, public, and the data is already there; deleting is destructive |
| 4 | "469 current MPs from 281.ro API" claim — implement or remove? | **Remove the false claim** | No code/data source exists; NOT PROVEN as a real integration |
| 5 | Release tag literals in docs | **Replace with a pointer to `data/latest-release.txt`** | Eliminates the recurring stale-tag class of bug |
| 6 | Credentials (Vercel/Render tokens) | **Not needed and not requested** | All verification uses public GET endpoints; no secrets touched |
| 7 | Scope of this run | **Wave 1 = all P0 (critical) parts** | Highest-value, lowest-risk; later waves continue after checkpoint review |

If you want a different answer for #2–#5, say so before Wave 2.

---

## 2. Backups and rollback (created and verified before any edit — §0.2)

**These exist now** (output captured 2026-11-19 09:24):

| Artifact | Value |
|---|---|
| Annotated git tag | `pre-remediation-2026-11-19` → `eb069d2b1de953a89489245ef6418a66a7b652ba` |
| Base branch | `remediation/base` → same commit |
| Physical snapshot | `/tmp/opencode/pd-backups/parlament-deschis-pre-remediation-2026-11-19.tar.gz` (152 MB) |
| Snapshot SHA-256 | `7f9e486d8139444de93c53375881d2fe664f583e136a9309898b95c0d5477986` |
| Manifest | `/tmp/opencode/pd-backups/SHA256SUMS.txt` |

**Rollback commands (memorise these):**

```bash
# Per-file / per-commit rollback on main:
cd /home/nedaktov/parlament-deschis
git show pre-remediation-2026-11-19:<path> > <path>          # restore one file

# Roll back ALL tracked files to baseline:
git checkout pre-remediation-2026-11-19 -- .

# Full restore including the ignored database (DESTRUCTIVE — last resort):
cd /home/nedaktov/parlament-deschis
rm -rf ./*
tar -xzf /tmp/opencode/pd-backups/parlament-deschis-pre-remediation-2026-11-19.tar.gz -C .
```

**Rule:** before integrating any wave, the Supervisor verifies the tag still
resolves to the baseline commit and the snapshot checksum still matches.

---

## 3. Work execution model

1. Each implementation agent gets an isolated git worktree:
   `/tmp/opencode/wt-<PART-ID>`, branch `remediation/<PART-ID>` from
   `remediation/base`.
2. The agent commits atomically on its branch and reports the commit SHA.
3. The lead integrates with `git cherry-pick <sha>` into `main`'s working tree
   **only after** the Supervisor's PASS for that part.
4. After each integration: full `uv run pytest -q`, `npm run build`, and the
   part-specific red→green checkpoint are re-run on the integrated tree.
5. `STATE.md` is updated after every part: status, commit, checkpoint outputs,
   supervisor verdict.

**File ownership map (disjoint within Wave 1):**

| Part | Owns (and may only edit) |
|---|---|
| P0-1 | `frontend/src/components/CrossChamberFlow.tsx`, `frontend/src/pages/PartyProfile.tsx`, `frontend/src/pages/PersonDeepDive.tsx` |
| P0-2 | `frontend/src/router.tsx`, `frontend/src/index.css`, all `frontend/src/pages/*.tsx` table wrappers |
| P0-3 | `backend/cli.py` → actually `pipeline/cli.py`, `pipeline/audit.py`, `tests/test_audit*.py`, `tests/test_analytics_transparency.py` |
| P0-4 | `.github/workflows/ci.yml` |
| P0-5 | `scripts/verify-deploy.sh`, `scripts/verify-dashboard.sh`, `scripts/check-deployment-status.sh`, `scripts/deploy-dashboard.sh` |
| P0-6 | All `*.md` files (root + `docs/**` + `docs/adr/**`) — **no code files** |

> Note: `pipeline/cli.py:611-614` and `backend/routers/api.py:337-341` contain
> false comments. The `cli.py` comment is owned by P0-3; the `api.py` comment is
> fixed by the lead in the integration step (no agent owns `api.py` in Wave 1).

---

## 3b. Wave 2 ownership (REVISED — authoritative; supersedes §6 where they conflict)

The original §6 table assigned `backend/routers/api.py`, `backend/queries.py`,
`backend/main.py` and `vercel.json` to several parts each. That breaks rule §0.5
(one owner per file) and would create cherry-pick conflicts. The eight P1 findings
are therefore regrouped into **five disjoint agents**:

| Agent | Absorbs | Owns (and may only edit) |
|---|---|---|
| `W2-A` GraphQL + app wiring | P1-1, P1-6(poller/headers part), P1-7(FastAPI headers part) | `backend/graphql/schema.py`, `backend/main.py`, `pipeline/poller.py`, `backend/deps.py`, `tests/test_security_hardening.py`, new `tests/test_graphql_convergence.py` |
| `W2-B` REST API hardening | P1-3, P1-4, P1-5 | `backend/routers/api.py`, `backend/queries.py`, `tests/test_api.py`, `tests/test_analytics_transparency.py`, new `tests/test_admin_lockout.py` |
| `W2-C` DB dedup | P1-2 | `scripts/prepare_db.py`, `pipeline/db.py`, `tests/test_db_schema.py` |
| `W2-D` Cache freshness | P1-6(exports/cache part) | `backend/routers/exports.py`, `backend/cache.py`, `tests/test_cache.py`, `tests/test_api_exports.py` |
| `W2-E` Edge/platform config | P1-7(vercel/render part), P1-8 | `vercel.json`, `render.yaml`, `Dockerfile`, `.github/workflows/*.yml` |

**Interface contracts between agents (no direct file sharing):**
- `W2-D` adds `invalidate_all()` to `backend/cache.py`; `W2-A` wires it into
  `backend/main.py`'s `start_poller(on_cycle=...)`.
- `W2-A` adds `SecurityHeadersMiddleware` in `backend/main.py`; `W2-E` adds the
  matching headers in `vercel.json`. Both layers must agree.
- `W2-A` adds the `/graphql` rewrite requirement; `W2-E` writes it into `vercel.json`.
- `W2-B` keeps `_require_admin_token` signature change inside `api.py` and tests it
  in a NEW file (`tests/test_admin_lockout.py`), leaving `test_security_hardening.py`
  to `W2-A` so the existing GraphQL monkeypatch test keeps working.

**Base for Wave 2:** current integrated `main` (`c7cdbe0`), tagged
`pre-wave2-2026-11-19`, branch `remediation/wave2-base`. All W2 worktrees branch from it.

---

## 4. Master wave plan

| Wave | Parts | Theme | Gate to advance |
|---|---|---|---|
| 1 | P0-1 … P0-6 | Stop the production bleeding | All P0 checkpoints PASS + Supervisor PASS + full suite green |
| 2 | P1-1 … P1-8 | Correctness, integrity, security | Same, plus live REST vs GraphQL agreement |
| 3 | C-1, C-2 | Looks and accessibility | Browser screenshots at 1440/390 + axe clean + reflow assertion |
| 4 | D-1 … D-4 | Modernization | Dependency upgrades green; generated contracts diff-clean |
| 5 | Final | Full re-verification and doc regeneration | Fresh forensic re-run comparing to the original investigation |

---

## 5. PART A — P0 critical action plans

### P0-1 — Three routes crash with React #310 (conditional hooks)

**Investigation evidence:** `ui_validate.py` live → 3 FAIL routes with `Minified React error #310`; three exact sites quoted in the audit (`CrossChamberFlow.tsx:24-52`, `PartyProfile.tsx:16-75`, `PersonDeepDive.tsx:32-77`). Error boundary at `router.tsx:66` leaks raw framework text; CI skips the validator (`ci.yml:108,116`).

**Goal / done:** all 18 routes render with 0 `console.error`; error boundary never shows raw `error.message`; regression lint rule added.

**Action plan:**
1. Move **every** `useMemo`/`useCallback`/`useState` above the first early `return` in the three owned files; keep JSX guards only.
2. Add `eslint-plugin-react-hooks` as a devDependency and a `lint` script that runs both `tsc --noEmit` and `eslint src`.
3. In `router.tsx` (owned by P0-2 — coordinate, do not edit): P0-2 will handle the friendly error text; P0-1 only verifies it does not leak.
4. Red→green: run the local dev server with the live API proxy and execute `ui_validate.py` against it.

**Checkpoints (exact commands + expected output):**
- CP-P0-1.1 (RED, before fix, captured from investigation): `python3 scripts/ui_validate.py https://parlament-deschis.vercel.app` → `UI VALIDATION FAIL`, 3 routes with `1 js-err`.
- CP-P0-1.2 (GREEN, after fix): `PARLAMENT_API_PROXY_TARGET=https://parlament-deschis.onrender.com npm run dev -- --host 127.0.0.1 --port 5173` in background, then `python3 scripts/ui_validate.py http://127.0.0.1:5173` → `UI VALIDATION PASS`, 18 routes, 0 js-err.
- CP-P0-1.3: `npm run build` → exit 0; `npm run lint` → exit 0 with `rules-of-hooks` enabled.
- CP-P0-1.4: source assertion script prints `hooks-after-return: 0` for the three owned files.

**Rollback:** `git checkout pre-remediation-2026-11-19 -- <the three files> frontend/package.json frontend/package-lock.json`.

**Owner recipe:** `RECIPES.md` → `R-P0-1`.

### P0-2 — Mobile reflow + error boundary layout

**Investigation evidence:** `/traseism` 390px `scrollWidth 737` vs `innerWidth 390` (+347); `/coverage` +435; `/leaderboard` +337; chain `MAIN#main-content 737 (minWidth:auto)` from `router.tsx:285`; two `<h1>` via `router.tsx:212`; `bg-panel/50` sticky header.

**Goal / done:** `scrollWidth <= innerWidth` at 320px on every route; one `<h1>` in `<main>`; opaque header; friendly error text inside `RootLayout`.

**Action plan:**
1. Add `min-w-0` to `main`, `.wrap`, and page `section` ancestors; add `max-w-full` to every `role="region"` `overflow-x-auto` wrapper.
2. Change header brand `h1` → `<div>`; ensure exactly one page `h1`.
3. Replace `bg-panel/50` with `bg-[#0f172a]/95 backdrop-blur-sm`.
4. Replace `router.tsx:66` raw `error?.message` with translated friendly text; log details to console only.
5. Keep header/nav/footer rendered in the error state.

**Checkpoints:**
- CP-P0-2.1: browser evaluate at 320×768 on `/traseism`, `/coverage`, `/leaderboard`, `/demographics`, `/report`: `documentElement.scrollWidth <= innerWidth` → `true` for all.
- CP-P0-2.2: DOM sweep on 15 working routes: `h1count === 1` inside `<main>`.
- CP-P0-2.3: force the error boundary (navigate to a crashing route before P0-1 is integrated, or temporarily throw in a test build): body text does NOT contain `Minified React error`; `header/nav/footer` count ≥ 1.
- CP-P0-2.4: `npm run build` exit 0.

**Rollback:** `git checkout pre-remediation-2026-11-19 -- frontend/src/router.tsx frontend/src/index.css` and the touched page files.

**Owner recipe:** `RECIPES.md` → `R-P0-2`.

### P0-3 — Strict audit gate passes total data loss

**Investigation evidence:** deleting all 5,273 mandates → `audit-corpus --strict` exit 0 with `223 resolved baseline findings`; only gate is `cli.py:436`; silent early returns `audit.py:150-151,496-498`.

**Goal / done:** the same deletion experiment exits non-zero; resolved/unevaluated findings fail the gate.

**Action plan:**
1. In `pipeline/cli.py`, extend the strict condition to fail on `sum(resolved_baseline_findings.values()) > 0` and `sum(unevaluated_baseline.values()) > 0`.
2. Convert the silent early returns in `pipeline/audit.py` into explicit `not_evaluated` findings.
3. Add tests asserting the gate fails on a deleted-table copy and passes on the intact DB.
4. Fix the false comment at `pipeline/cli.py:611-614` (0 committees/0 waves → real values or removal).

**Checkpoints:**
- CP-P0-3.1 (RED): on a `/tmp` copy, `DELETE FROM mandate`; `audit-corpus --strict --baseline …; echo EXIT:$?` → `EXIT:0` (captured in investigation).
- CP-P0-3.2 (GREEN): same command after fix → `EXIT:1`, output names the lost check.
- CP-P0-3.3: intact DB → `--strict` still `EXIT:0` (no false positives).
- CP-P0-3.4: `uv run pytest -q` → 259+ passed (new tests included), 0 failed.

**Rollback:** `git checkout pre-remediation-2026-11-19 -- pipeline/cli.py pipeline/audit.py tests/test_audit.py tests/test_audit_overlap.py tests/test_analytics_transparency.py`.

**Owner recipe:** `RECIPES.md` → `R-P0-3`.

### P0-4 — CI deploy theater

**Investigation evidence:** wrong `git.uid`, unchecked curls, secret/var confusion, silent `exit 0` (quoted in A4).

**Goal / done:** `ci.yml` contains no unchecked platform POST and no silent skip; a green deploy job implies an actually verified deploy.

**Action plan:**
1. Delete the manual Vercel POST step and the Render hook/API POST steps (owner decision #2). Keep `deploy-verify.yml` and `render.yaml:autoDeployTrigger: checksPass`.
2. If any platform call remains, it must use `-w '%{http_code}' -o <file>` + a status test + `exit 1` on non-2xx (pattern from `platform-rollback.yml:82-106`).
3. Add a comment block documenting the single deploy source of truth.

**Checkpoints:**
- CP-P0-4.1: `grep -nE 'curl .*api\.(vercel|render)' .github/workflows/ci.yml` → 0 matches.
- CP-P0-4.2: `grep -n 'exit 0' .github/workflows/ci.yml` → 0 matches in the deploy job.
- CP-P0-4.3: actionlint/yamllint or `python3 -c 'import yaml; yaml.safe_load(open(...))'` → valid YAML; `git diff --check` clean.
- CP-P0-4.4: live `/api/health` still serves `data-20261117-T213500` (no regression) — GET only.

**Rollback:** `git checkout pre-remediation-2026-11-19 -- .github/workflows/ci.yml`.

**Owner recipe:** `RECIPES.md` → `R-P0-4`.

### P0-5 — False-green deployment scripts + missing freshness alert

**Investigation evidence:** `check-deployment-status.sh:38,55` `head -1` false positives; `verify-dashboard.sh:48` hardcoded nonexistent bundle; no freshness check.

**Goal / done:** scripts fail when the thing they check is absent; a stale dataset produces a loud failure.

**Action plan:**
1. Replace `curl | grep | head -1 && echo ✅` with `grep -q` / `test -n "$(…)"` and `exit 1` on absence.
2. Resolve the real asset filename from the served `index.html` instead of glob-literal URLs.
3. Remove hardcoded bundle hashes/sizes; print measured values.
4. Add to `scripts/verify-deploy.sh` an assertion: `dataset.published_at` age ≤ 7 days (configurable), failing loudly otherwise.
5. These are local helper scripts — do not wire them into CI in this wave.

**Checkpoints:**
- CP-P0-5.1: run `bash scripts/check-deployment-status.sh` against a URL serving an empty shell → non-zero exit and no false ✅.
- CP-P0-5.2: run it against the live URL → real asset filename detected.
- CP-P0-5.3: feed `verify-deploy.sh` a synthetic health JSON with `published_at` 30 days old → non-zero exit; with today's date → zero exit.

**Rollback:** `git checkout pre-remediation-2026-11-19 -- scripts/*.sh`.

**Owner recipe:** `RECIPES.md` → `R-P0-5`.

### P0-6 — Documentation truthfulness

**Investigation evidence:** 41 false claims (full table in audit), including UI-PASS, test counts 193/199 vs 259, DASHBOARD-VERIFICATION 7/9 wrong, stale tags, `ignoreCommand`, marker→CI, 281.ro.

**Goal / done:** 0 verifiably false claims; every number traced to a generated artifact or a command; no "current release" literal in docs.

**Action plan:**
1. Remove/replace all `data-20261117-T060923` (and other stale tags) with a pointer to `data/latest-release.txt`.
2. Replace UI-validation PASS claims with "currently failing — see issue" until P0-1/P0-2 land; then regenerate from actual output.
3. Replace 193/199/273 with 259/275 and delete "3 expected failures".
4. Rewrite `docs/DASHBOARD-VERIFICATION.md` from a fresh `curl /api/dashboard/stats` and fresh build output; remove "Ready for Deployment" until checkboxes are ticked with evidence; remove `npm run test` instructions.
5. Delete `DEPLOYMENT.md` "Vercel build skipping" section; correct marker→CI claims.
6. Remove 281.ro rows and "Pending: none" contradiction; add historical banner to `ACTION_PLAN.md`.
7. Fix GraphQL example, RFC 7807 claim, committee count, and add the 11 undocumented endpoints.
8. Add a CI-ready check script `scripts/check-doc-truth.sh` that greps for stale tags and known-false strings and fails.

**Checkpoints:**
- CP-P0-6.1: `bash scripts/check-doc-truth.sh` → exit 0 with `false-claims: 0` printed.
- CP-P0-6.2: `grep -rn 'data-20261117-T060923\|193 passed\|199 pytest\|281\.ro\|0 JS errors\|Ready for Deployment' --include='*.md' .` → 0 matches.
- CP-P0-6.3: spot-check 5 regenerated values against live GET output with `jq -e` equality.
- CP-P0-6.4: all doc links resolve (`lychee`/custom checker).

**Rollback:** docs are tracked — `git checkout pre-remediation-2026-11-19 -- '*.md' docs/`.

**Owner recipe:** `RECIPES.md` → `R-P0-6`.

---

## 6. PART B — P1 high action plans (Wave 2, summary — full recipes in RECIPES.md)

| ID | Goal (done condition) | Key checkpoint | Owner recipe |
|---|---|---|---|
| P1-1 | GraphQL `generationalShift` non-empty; `crossChamber` == REST 39; 1 engine/request; resolvers batched | [LIVE] GraphQL and REST return identical arrays; SQL statement count < 20/field | `R-P1-1` |
| P1-2 | 0 duplicate memberships; `ux_membership_closed_stint` exists | [RUN] SQL `dup_groups = 0`, index present, no startup warning | `R-P1-2` |
| P1-3 | `/api/timeline` step_days=1 full range < 0.5 s or 422 | [RUN] same curl as investigation → time < 0.5 s | `R-P1-3` |
| P1-4 | Admin lockout keyed by IP; N distinct guesses → 429 | [RUN] new regression test passes | `R-P1-4` |
| P1-5 | Uniform date parsing + half-open interval everywhere | [RUN] boundary probe: chamber == committees on end date | `R-P1-5` |
| P1-6 | Fresh `generated_at` per export; both caches invalidated by poller | [RUN] two requests → different timestamps | `R-P1-6` |
| P1-7 | Security headers on Vercel + FastAPI; HSTS on Render path | [LIVE] `curl -I` shows CSP/nosniff/XFO | `R-P1-7` |
| P1-8 | All actions SHA-pinned; `--locked` in Docker; immutable asset caching | [RUN] `grep '@v[0-9]'` in workflows → 0; headers restored | `R-P1-8` |

---

## 7. PART C — Looks & accessibility (Wave 3, summary)

| ID | Goal | Key checkpoint | Recipe |
|---|---|---|---|
| C-1 | Design tokens unified; hero colored + translated; header opaque; nav grouped; charts paletted; dead code removed | Browser screenshots 1440/390 + computed styles + `grep` dead imports = 0 | `R-C1` |
| C-2 | WCAG 2.2 AA on all routes | axe 0 violations; `lang` correct; one h1; reflow; 0 unnamed controls | `R-C2` |

---

## 8. PART D — Modernization (Wave 4, summary)

| ID | Goal | Recipe |
|---|---|---|
| D-1 | Dependency upgrades green (React 19, Vite 8, ECharts 6, Tailwind 4, i18next 27) | `R-D1` |
| D-2 | Data decoupled from image (loader at boot / Postgres dual-write) | `R-D2` |
| D-3 | Generated OpenAPI client + `docs/API.md`; CI diff-clean | `R-D3` |
| D-4 | `/api/metrics`, frontend error tracking, freshness alert | `R-D4` |

---

## 9. Supervisor protocol

The Supervisor (`SUPERVISOR-RECIPE.md`) runs:
- **Before a wave:** re-reads investigation + this strategy + backups; verifies tag/checksum.
- **During a wave:** checks each agent's commit diff for (a) in-scope files only, (b) no data deletion, (c) no secrets, (d) no new unchecked shell/HTTP calls, (e) red→green evidence present.
- **After a wave:** independently re-runs every checkpoint command. Defaults to **REJECT** until raw output proves PASS. Issues `STATE.md` verdict with evidence and either `APPROVE_INTEGRATE` or `REJECT + reasons`.

Drift detection: if an agent edits a file not in its ownership map, or produces a claim without command output, that part is REJECTED and reworked — not negotiated.

---

## 10. Definition of done (final, Wave 5)

- Same forensic checks re-run from scratch and compared to the investigation baseline.
- `uv run pytest -q` green; `npm run build` + `npm run lint` green; `ui_validate.py` green.
- Strict audit green AND fails on the deletion experiment.
- `check-doc-truth.sh` green.
- Live REST vs GraphQL agreement; live security headers present; release tag consistent.
- `STATE.md` shows every part APPROVE with commit SHA + checkpoint outputs.
- Zero secrets, zero pushes, zero destructive operations in the audit log.
