# Agent Recipes — Parlament Deschis Remediation

**Companion to:** `STRATEGY.md` (source of truth) · `SUPERVISOR-RECIPE.md` · `STATE.md`
**Rule:** an agent may only do what its recipe says, only inside its named worktree, and
only on files listed in `STRATEGY.md §3`. Everything else is a side-quest and is REJECTED.

---

## 0. Universal recipe template (applies to every recipe below)

Every implementation recipe has these fields. If any is missing, the agent must stop
and ask rather than improvise.

```
ID / ROLE        unique part id + senior-engineer specialization
INPUTS           absolute paths: project root, worktree path, branch, strategy file, recipe file
SCOPE            exact files owned; explicit "do not touch" list
BACKUP ASSUMPTION tag pre-remediation-2026-11-19 exists; verify before starting
RULES            evidence-only; red→green; atomic commit; no push/deploy/secrets
PROCEDURE        numbered steps; each step names the command to run
CHECKPOINTS      exact command + expected output; capture BEFORE and AFTER
EVIDENCE LOG     table: command → raw output → PASS/FAIL
ROLLBACK         exact git checkout command for owned files
OUTPUT           commit SHA, diff stat, checkpoint table, self-verdict (PASS/REJECT)
```

**Universal command preamble for every agent:**
```bash
cd /home/nedaktov/parlament-deschis
git worktree add -b remediation/<PART-ID> /tmp/opencode/wt-<PART-ID> remediation/base
cd /tmp/opencode/wt-<PART-ID>
git config user.name "Remediation Bot"; git config user.email "bot@local"
# Python venv and node_modules are created on demand inside the worktree:
uv sync --extra dev --locked && cd frontend && npm ci && cd ..
```

**Universal prohibitions:** no `git push`, no `git tag -d`, no deploy/rollback API call,
no reading or writing secrets, no editing another part's files, no deleting data, no
changing the audit baseline, no weakening a test to make it pass. If a checkpoint
cannot be run, report `NOT PROVEN` — never claim PASS.

---

## R-P0-1 — React #310 hook-order fix

**Role:** Senior React engineer (hooks, error boundaries).
**Worktree:** `/tmp/opencode/wt-P0-1`, branch `remediation/P0-1`.
**Scope:** `frontend/src/components/CrossChamberFlow.tsx`, `frontend/src/pages/PartyProfile.tsx`, `frontend/src/pages/PersonDeepDive.tsx`, `frontend/package.json`, `frontend/package-lock.json`. **Do not touch** `router.tsx` or `index.css` (P0-2 owns them).

**Rules:** (1) No hook may appear after a top-level `return`. (2) No behaviour change beyond hook ordering and the lint rule. (3) `t()` defaults remain as-is (i18n is P0-6/Wave 3 territory). (4) Red→green must be shown.

**Procedure:**
1. Verify backup: `git rev-parse pre-remediation-2026-11-19` == `eb069d2b…`.
2. Read the three files; list every hook call and every early `return` with line numbers. Print the list (this is the red evidence).
3. Move all hooks above the first early return in each file. Keep `data?.length`/`isLoading`/`isError` guards as JSX-only conditions. Derive `p`/`data` as plain variables before hooks; use optional chaining inside the hooks.
4. Add `eslint`, `eslint-plugin-react-hooks`, `@eslint/js`, `typescript-eslint` as devDependencies; add `.eslintrc` (or flat config) with `react-hooks/rules-of-hooks: error`; change `lint` script to `tsc --noEmit && eslint src --ext .ts,.tsx`.
5. Write a tiny script `scripts/check-hook-order.mjs` that asserts no hook call appears after an early `return` in the three files; it must exit 1 on the pre-fix source (prove by running against the baseline copy in `/tmp`) and 0 after.
6. `npm run lint && npm run build`.
7. Start the app locally proxied to the live API and run the validator against localhost.
8. Commit atomically: `fix(P0-1): move hooks above early returns to stop React #310`.

**Checkpoints:**
- BEFORE: `python3 scripts/check-hook-order.mjs <baseline copy>` → `hooks-after-return: 3` exit 1.
- AFTER: `node scripts/check-hook-order.mjs` → `hooks-after-return: 0` exit 0.
- `PARLAMENT_API_PROXY_TARGET=https://parlament-deschis.onrender.com npm run dev -- --host 127.0.0.1 --port 5173` (background) → `python3 scripts/ui_validate.py http://127.0.0.1:5173` → `UI VALIDATION PASS`, 18 routes, 0 js-err.
- `npm run build` exit 0; `npm run lint` exit 0.

**Rollback:** `git checkout pre-remediation-2026-11-19 -- frontend/src/components/CrossChamberFlow.tsx frontend/src/pages/PartyProfile.tsx frontend/src/pages/PersonDeepDive.tsx frontend/package.json frontend/package-lock.json`.

**Output:** commit SHA, hook-order before/after outputs, ui_validate output, self-verdict.

---

## R-P0-2 — Reflow + error-boundary layout

**Role:** Senior CSS/layout engineer (flexbox min-width, accessible landmarks).
**Worktree:** `/tmp/opencode/wt-P0-2`, branch `remediation/P0-2`.
**Scope:** `frontend/src/router.tsx`, `frontend/src/index.css`, `frontend/src/pages/*.tsx` (only `overflow-x-auto`/`role="region"` wrappers and `min-h-screen` hero classes). **Do not touch** the three P0-1 files.

**Rules:** no visual redesign (that is C-1); only structural min-width, header opacity, h1 count, and error text.

**Procedure:**
1. Add `min-w-0` to `main#main-content` and the `.wrap`/`section` ancestors; `max-w-full` on every table scroll region.
2. Header brand `h1` → `<div className="text-base font-semibold tracking-tight">`; keep one page `h1` per route (verify `/compare` already has one — do not remove it).
3. `bg-panel/50` → `bg-[#0f172a]/95 backdrop-blur-sm`.
4. `router.tsx:66`: replace `{error?.message || t(...)}` with `t("routeErrorBody", "Ne pare rău, datele nu pot fi afișate.")`; keep `console.error(error)` for diagnostics; render the boundary inside `RootLayout` so header/nav/footer persist.
5. Add a Playwright script `scripts/check-reflow.mjs` (or Python via chrome-devtools) that loads 15 routes at 320×768 and asserts `documentElement.scrollWidth <= innerWidth`, `h1count === 1` in `<main>`, and no raw "Minified React error" text.

**Checkpoints:** `check-reflow.mjs` → `overflow-ok: 15/15`, `h1-ok: 15/15`, `raw-error-leak: 0`; `npm run build` exit 0.

**Rollback:** `git checkout pre-remediation-2026-11-19 -- frontend/src/router.tsx frontend/src/index.css frontend/src/pages/`.

**Output:** commit SHA, reflow table (route → scrollWidth/innerWidth before and after), self-verdict.

---

## R-P0-3 — Make the strict audit gate symmetric

**Role:** Senior data-engineer / test engineer.
**Worktree:** `/tmp/opencode/wt-P0-3`, branch `remediation/P0-3`.
**Scope:** `pipeline/cli.py`, `pipeline/audit.py`, `tests/test_audit.py`, `tests/test_audit_overlap.py`, `tests/test_analytics_transparency.py`.

**Rules:** never weaken a check; never edit `data/reference/corpus-audit-baseline.json`; all experiments on `/tmp` copies of the DB only.

**Procedure:**
1. Reproduce red: copy `data/parlament.db` to `/tmp/pd-audit-red.db`, `DELETE FROM mandate`, run `audit-corpus --strict --baseline …`, capture `EXIT:0` + `223 resolved baseline findings`.
2. Extend the strict gate at `cli.py:436` to fail on resolved and unevaluated baseline findings; print a clear reason.
3. Convert silent early returns in `audit.py:150-151,496-498,611` into explicit `not_evaluated` findings.
4. Add regression tests: (a) deletion copy → non-zero exit; (b) intact DB → zero exit; (c) resolved finding causes failure.
5. Fix the false comment at `cli.py:611-614`.
6. `uv run pytest -q`, `uv run ruff check pipeline tests`.

**Checkpoints:** CP-P0-3.1..3.4 from `STRATEGY.md §5`.

**Rollback:** `git checkout pre-remediation-2026-11-19 -- pipeline/cli.py pipeline/audit.py tests/test_audit.py tests/test_audit_overlap.py tests/test_analytics_transparency.py`.

**Output:** commit SHA, before/after exit codes with raw output, test count, self-verdict.

---

## R-P0-4 — CI deploy honesty

**Role:** Senior DevOps/platform engineer.
**Worktree:** `/tmp/opencode/wt-P0-4`, branch `remediation/P0-4`.
**Scope:** `.github/workflows/ci.yml` only.

**Rules:** no deploy calls of any kind during the work; no secrets; validate YAML.

**Procedure:**
1. Remove the entire `Trigger Vercel Deployment` and `Trigger Render Deploy (Hook or API)` steps (owner decision #2). Keep the `deploy` job only if it still performs a useful check; otherwise remove the job and adjust `needs` so nothing dangles.
2. Document in a comment: Vercel Git integration + Render `checksPass` are the only deploy paths; `deploy-verify.yml` is the independent proof.
3. If any platform call remains: use `-w '%{http_code}' -o <file>`, echo code, `jq -r`, `test` code in 200/201, `exit 1` otherwise.
4. Validate: `python3 -c 'import yaml; yaml.safe_load(open(".github/workflows/ci.yml"))'`.

**Checkpoints:** CP-P0-4.1..4.4.

**Rollback:** `git checkout pre-remediation-2026-11-19 -- .github/workflows/ci.yml`.

**Output:** commit SHA, grep counts, YAML validation output, self-verdict.

---

## R-P0-5 — Deployment helper scripts tell the truth

**Role:** Senior SRE/tooling engineer.
**Worktree:** `/tmp/opencode/wt-P0-5`, branch `remediation/P0-5`.
**Scope:** `scripts/verify-deploy.sh`, `scripts/verify-dashboard.sh`, `scripts/check-deployment-status.sh`, `scripts/deploy-dashboard.sh`.

**Procedure:** implement CP-P0-5.1..5.3 from `STRATEGY.md §5`. Use `grep -q`/`test -n`; resolve real asset filename from served HTML; remove hardcoded hashes; add `published_at` freshness assertion (default 7 days, env-overridable) with clear failure text.

**Checkpoints:** CP-P0-5.1..5.3; `bash -n` on all four scripts.

**Rollback:** `git checkout pre-remediation-2026-11-19 -- scripts/`.

**Output:** commit SHA, before/after script outputs (including a deliberately false URL), self-verdict.

---

## R-P0-6 — Documentation truthfulness

**Role:** Technical writer + evidence auditor.
**Worktree:** `/tmp/opencode/wt-P0-6`, branch `remediation/P0-6`.
**Scope:** all `*.md` under the repo root, `docs/`, `docs/adr/`. Add `scripts/check-doc-truth.sh`. **No code files.**

**Procedure:** follow `STRATEGY.md §5 P0-6` steps 1–8 exactly. Generate numbers from live GETs and commands, never from memory. Quote raw output into the docs.

**Checkpoints:** CP-P0-6.1..6.4.

**Rollback:** `git checkout pre-remediation-2026-11-19 -- '*.md' docs/ scripts/check-doc-truth.sh`.

**Output:** commit SHA, `check-doc-truth.sh` output, list of changed docs with the exact false claim each removed, self-verdict.

---

## Wave 2 recipes (REVISION 2 — authoritative; replaces the P1-* summary)

See `STRATEGY.md §3b` for the revised disjoint ownership map. Universal template §0 applies.

### R-W2-A — GraphQL convergence + app wiring
**Role:** Senior Python/GraphQL/FastAPI engineer.
**Owns:** `backend/graphql/schema.py`, `backend/main.py`, `pipeline/poller.py`, `backend/deps.py`, `tests/test_security_hardening.py`, new `tests/test_graphql_convergence.py`.
**Do not touch:** `api.py`, `queries.py`, `exports.py`, `cache.py`, `vercel.json`, `Dockerfile`, workflows.

Proven defects: `generationalShift` filters `Membership.org_id` to party instead of `on_behalf_of_id` → always `[]`; `crossChamber` = 233 vs REST 39; resolvers call `make_engine()` per field (2 engines/request, never disposed, ignores `get_db`); N+1 with 3,389 SQL statements; poller invalidates only one cache; no security headers on FastAPI; `/graphql` missing from no-store middleware.

1. Preserve a compatible `make_engine` symbol so the existing monkeypatch test in `test_security_hardening.py` keeps working, but resolvers must use `info.context["db"]` from `GraphQLRouter(schema, context_getter=...)`.
2. Create ONE engine at app/lifespan scope from the same `DB_PATH` as `backend/config.py`; dispose on shutdown; `context_getter` yields one session per request via a `get_db`-compatible factory.
3. `generationalShift`: join on `Membership.on_behalf_of_id`, dedupe `(person_id, party)`; `crossChamber`: delegate to `queries.get_cross_chamber_careers(session, as_of)` or identical Mandate-based logic; batch with GROUP BY so SQL per field < 20.
4. `main.py`: wire `on_cycle=invalidate_all()` (contract from W2-D) into `start_poller`; add `SecurityHeadersMiddleware` (CSP Report-Only, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`) matching W2-E's `vercel.json`; widen no-store path match to include `/graphql`.
5. Tests: GraphQL non-empty; REST==GraphQL cross-chamber; SQL statements < 20; one engine/request; headers present; both caches invalidated.

**Checkpoints:** `POST /graphql {generationalShift}` non-empty (live Render + local TestClient); `crossChamber count == REST count (39)`; engine creations == 1; SQL statements < 20; `curl -sS -D - <local>/api/health` shows all security headers; pytest green; ruff clean.
**Rollback:** `git checkout pre-wave2-2026-11-19 -- backend/graphql/schema.py backend/main.py pipeline/poller.py backend/deps.py tests/test_security_hardening.py` and delete new test file.

### R-W2-B — REST API hardening (timeline + admin lockout + dates)
**Role:** Senior FastAPI/security engineer.
**Owns:** `backend/routers/api.py`, `backend/queries.py`, `tests/test_api.py`, `tests/test_analytics_transparency.py`, new `tests/test_admin_lockout.py`.
**Do not touch:** `main.py`, `graphql/`, `exports.py`, `cache.py`, `deps.py`, `poller.py`, docs, workflows.

1. `/api/timeline`: cap date buckets (~400) with 422; add `@cache_result("timeline")`; rewrite `get_timeline` to one sweep into per-day buckets. Full-range `step_days=1` must drop from 5.8 s to < 0.5 s OR return 422.
2. `_require_admin_token`: pass `Request`, key failures on client host with a global counter backstop, keep `secrets.compare_digest`, keep 503 fail-closed. Prove N distinct wrong guesses from one IP → 429.
3. Uniform date parsing: `_parse_date`/annotated date everywhere; `/api/dashboard/stats?as_of=garbage` → 422; half-open interval `[start, end)` (`end_date > as_of`) in `api.py:353,404` and `queries.py:769`. Boundary probe: chamber and committees agree on end date.

**Checkpoints:** full-range timeline < 0.5 s or 422; `?as_of=garbage` → 422; boundary probe equal; 10 distinct guesses → 429; pytest + ruff green.
**Rollback:** `git checkout pre-wave2-2026-11-19 -- backend/routers/api.py backend/queries.py tests/test_api.py tests/test_analytics_transparency.py`.

### R-W2-C — DB dedup and fail-fast index
**Role:** Senior data engineer. **Owns:** `scripts/prepare_db.py`, `pipeline/db.py`, `tests/test_db_schema.py`.
1. Deduplicate the 9 legacy closed-stint duplicates in `prepare_db.py` on `(org_id, person_id, chamber, legislature, start_date, end_date)`.
2. Create `ux_membership_closed_stint` FAIL-FAST (no silent `try/except` swallow); express `uq_stint` via `COALESCE(post_id,'')` partial index.
3. Assert dup count = 0, index present, `journal_mode=DELETE`, `integrity_check=ok`.
**Checkpoints:** on a `/tmp` copy → dup_groups 0, index present, no startup warning; counts 3388/7358/5273 unchanged; **never modify `data/parlament.db` itself**.
**Rollback:** `git checkout pre-wave2-2026-11-19 -- scripts/prepare_db.py pipeline/db.py tests/test_db_schema.py`.

### R-W2-D — Cache freshness
**Role:** Senior backend performance engineer. **Owns:** `backend/routers/exports.py`, `backend/cache.py`, `tests/test_cache.py`, `tests/test_api_exports.py`.
1. `/api/export/report`: remove `@cache_result` OR cache only the plain data dict and build a fresh `JSONResponse` (fresh `generated_at`) per request.
2. Add `invalidate_all()` to `backend/cache.py` calling both invalidators — contract W2-A wires into the poller.
3. Never cache mutable `Response` objects.
**Checkpoints:** two `GET /api/export/report` → different `generated_at`; cached value is dict not `JSONResponse`; `invalidate_all()` clears both; pytest + ruff green.
**Rollback:** `git checkout pre-wave2-2026-11-19 -- backend/routers/exports.py backend/cache.py tests/test_cache.py tests/test_api_exports.py`.

### R-W2-E — Edge/platform config
**Role:** Senior platform/security engineer. **Owns:** `vercel.json`, `render.yaml`, `Dockerfile`, `.github/workflows/*.yml`.
1. `vercel.json`: `/graphql` rewrite to Render origin BEFORE catch-all; security headers for `/(.*)` matching W2-A's middleware (nosniff, XFO, Referrer-Policy, Permissions-Policy, CSP Report-Only); restore immutable asset caching for `/assets/(.*)`; keep `no-store` on `/api/*`.
2. `Dockerfile`: `--locked` on both `uv sync` lines; pin uv version.
3. Workflows: SHA-pin all 8 floating `uses:` (7 in `data.yml`, 1 in `deploy-verify.yml`) via `git ls-remote`; leave `ci.yml` untouched.
4. **No deploy / no live POST.** Live header verification requires owner-approved deployment → mark `config-verified, live-pending-deploy`.
**Checkpoints:** `/graphql` rewrite present in jq; immutable asset cache present; `grep -rn '@v[0-9]' .github/workflows/` → 0; both `uv sync` lines have `--locked`; JSON/YAML valid; `git diff --check` clean.
**Rollback:** `git checkout pre-wave2-2026-11-19 -- vercel.json render.yaml Dockerfile .github/workflows/`.

## Wave 3 recipes (summary)

- **R-C1 Visual system:** own `frontend/src/index.css`, `tailwind.config.js`, `HeroGraphic.tsx`, chart components, `index.html`. Done: screenshots + computed styles prove tokens applied, hero colored (`text-amber-400`/style color), header opaque, nav grouped, one palette module, 0 dead imports.
- **R-C2 Accessibility:** own remaining a11y markup; Done: axe 0 on all routes, `lang` correct + persisted, one h1, reflow, every control named.

## Wave 4 recipes (summary)

- **R-D1 Upgrades:** dependency bumps with full build/test/axe re-run after each major.
- **R-D2 Data decoupling:** loader at boot into mounted volume; Postgres dual-write behind flag; rollback always available.
- **R-D3 Generated contracts:** `openapi.json` + `schema.graphql` committed; generated TS client + `docs/API.md`; CI diff-clean.
- **R-D4 Observability:** `/api/metrics`, frontend error tracking, freshness alert.
