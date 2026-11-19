# Remediation State Ledger

**Baseline:** `eb069d2b1de953a89489245ef6418a66a7b652ba` · **Tag:** `pre-remediation-2026-11-19`
**Backup SHA-256:** `7f9e486d8139444de93c53375881d2fe664f583e136a9309898b95c0d5477986`
**Started:** 2026-11-19
**Supervisor pass:** 2026-11-19 (adversarial verification of Wave 1, raw output below)

## Wave status

| Wave | Theme | Status |
|---|---|---|
| 0 | Backups + strategy + recipes | DONE — tag, branch, 152 MB snapshot, checksum verified |
| 1 | P0 critical fixes | VERIFIED — 7/7 parts `APPROVE_INTEGRATE`; integrated gate green (axe-only C-2 residuals remain) |
| 2 | P1 correctness/security | PENDING |
| 3 | Looks + accessibility | PENDING — C-2 must absorb the 5 new/recurring axe residuals logged below |
| 4 | Modernization | PENDING |
| 5 | Fresh forensic re-verification | PENDING |

## Part ledger

| Part | Branch | Commit | Supervisor | Integrated |
|---|---|---|---|---|
| P0-1 React #310 | `remediation/P0-1` | `1fcd577` | APPROVE_INTEGRATE | yes (`remediation/INTEGRATION-SUP`, HEAD `58ec23f`) |
| P0-2 Reflow/error UI | `remediation/P0-2` | `d7fb3c7` | APPROVE_INTEGRATE | yes |
| P0-3 Strict audit gate | `remediation/P0-3` | `74f20f7` | APPROVE_INTEGRATE | yes |
| P0-4 CI deploy honesty | `remediation/P0-4` | `d56456c` | APPROVE_INTEGRATE | yes |
| P0-5 Script truth | `remediation/P0-5` | `f46c660` | APPROVE_INTEGRATE | yes |
| P0-6 Doc truth | `remediation/P0-6` | `76ed275` | APPROVE_INTEGRATE | yes |
| P0-7 Unmasked SVG/NaN | `remediation/P0-7` | `2aa5401` | APPROVE_INTEGRATE | yes |

**Integration:** all 7 commits based directly on `remediation/base` (`eb069d2`); cherry-picked in
order 1→7 with **zero conflicts** into `/tmp/opencode/wt-INTEGRATE` (branch
`remediation/INTEGRATION-SUP`, HEAD `58ec23f`). No production file in
`/home/nedaktov/parlament-deschis` was edited by the Supervisor; only this `STATE.md`.

---

## Backup integrity (STEP 2 — raw output)

```
$ git -C /home/nedaktov/parlament-deschis rev-parse 'pre-remediation-2026-11-19^{}'
eb069d2b1de953a89489245ef6418a66a7b652ba
EXIT:0

$ cd /tmp/opencode/pd-backups && sha256sum -c SHA256SUMS.txt
parlament-deschis-pre-remediation-2026-11-19.tar.gz: OK
EXIT:0

$ git rev-parse remediation/base
eb069d2b1de953a89489245ef6418a66a7b652ba
```

Backup integrity: **PASS**. All 7 commit parents verified = `eb069d2`.

**Data integrity (rule 5):**
```
integrity_check: ok
person=3388  membership=7358  mandate=5273  switch_wave=142
```
Matches STRATEGY §SUPERVISOR rule 5 exactly. No tracked data/reference file deleted in any diff.

---

## Evidence log (per-part verdicts, format from SUPERVISOR-RECIPE §4)

### PART: P0-1 | BRANCH: remediation/P0-1 | SHA: 1fcd577 | TIME: 2026-11-19
```
SCOPE:        PASS — files: frontend/eslint.config.js (A, recipe step 4),
              frontend/package.json, frontend/package-lock.json,
              frontend/src/components/CrossChamberFlow.tsx,
              frontend/src/pages/PartyProfile.tsx,
              frontend/src/pages/PersonDeepDive.tsx,
              scripts/check-hook-order.mjs (A, recipe step 5).
              All within STRATEGY §3 + recipe additions. No out-of-scope file.
DELIVERABLE:  PASS — every useMemo/useState above the first early return in all
              3 owned files; react-hooks/rules-of-hooks enabled as error.
RED/GREEN:    PASS
  baseline copies verified byte-identical to remediation/base (all 3: MATCHES baseline).
  BASELINE: hooks-after-return: 3 ; files-affected: 3/3 ; RESULT: FAIL ; EXIT:1
    CrossChamberFlow.tsx: useMemo@48 ; PartyProfile.tsx: useMemo@59,useMemo@67 ;
    PersonDeepDive.tsx: useMemo@77
  FIXED:    hooks-after-return: 0 ; files-affected: 0/3 ; RESULT: PASS ; EXIT:0
CHECKPOINTS:
  CP-P0-1.1 RED (investigation): 3 routes, 1 js-err each, Minified React error #310 (captured).
  CP-P0-1.2 GREEN (INTEGRATED tree, live API proxy on 5183): 18 routes rendered,
            0 js-err on ALL 18 routes. (People/overview crashes cleared by P0-7.)
  CP-P0-1.3 npm run lint -> EXIT 0 (0 errors, 7 exhaustive-deps WARNINGS configured as warn);
            npm run build -> EXIT 0 (built in 8.83s).
  CP-P0-1.4 node scripts/check-hook-order.mjs -> hooks-after-return: 0, EXIT 0.
  grep -c '#310\|Minified React error' /tmp/opencode/p0-1-ui-validate.log = 0.
INTEGRATION:  pytest 259 passed / 4 skipped (pre-existing) / 0 failed ; build 0 ;
              lint 0 errors ; ui_validate 18 routes, 0 js-err (axe-only residuals).
NO-WEAKENING: PASS — only hook reordering + new lint rule; no test touched.
NO-DATA-LOSS: PASS — no data file in diff.
BACKUP:       PASS (tag + checksum ok)
SIDE-QUESTS:  none
VERDICT:      APPROVE_INTEGRATE
RATIONALE:    Checker truly returns 3 on genuine baseline and 0 on the fix; the agent's
              self-REJECT was only because P0-7's SVG/NaN errors remained in isolation —
              on the integrated tree those clear and all 18 routes render with 0 js-err,
              so the in-scope React #310 fix is proven.
```

### PART: P0-2 | BRANCH: remediation/P0-2 | SHA: d7fb3c7 | TIME: 2026-11-19
```
SCOPE:        PASS — files: frontend/src/index.css, frontend/src/router.tsx and 12
              frontend/src/pages/*.tsx wrappers. All in ownership. (Recipe's
              scripts/check-reflow.mjs is optional "or Python via chrome-devtools";
              Supervisor ran its own 320px browser probe instead.)
DELIVERABLE:  PASS — main/wrap/section get min-w-0; main also w-full; every
              overflow-x-auto region gets max-w-full; header h1->div;
              bg-panel/50 -> bg-[#0f172a]/95 backdrop-blur-sm; raw error.message
              replaced with friendly t(...) + console.error in useEffect;
              defaultErrorComponent=RouteError keeps header/nav/footer mounted.
CHECKPOINTS:  (Supervisor browser probe at 320x768, self-run on integrated tree)
  CP-P0-2.1 REFLOW 15/15 PASS — every route scrollWidth=320 <= innerWidth=320:
    /traseism /coverage /leaderboard /demographics /report / /compare
    /committees /mps /party/PSD /person/... /party-timeline /senate-history
    /institutional /legislature/2024
    (Baseline was /traseism scrollWidth 737 vs 390 — now contained.)
  CP-P0-2.2 H1-ok 15/15 PASS — main h1 == 1 on all 15 routes. (/coverage initially
    read 0 during loading; re-probe after full load -> main-h1=1, confirmed.)
  CP-P0-2.3 raw-error-leak: 0 — no "Minified React error" text on any route.
  CP-P0-2.4 npm run build -> EXIT 0 (integrated tree).
INTEGRATION:  build 0 ; lint 0 errors ; ui_validate 0 js-err on 18 routes.
NO-WEAKENING: PASS — structural CSS/markup only.
NO-DATA-LOSS: PASS — no data file in diff.
BACKUP:       PASS
SIDE-QUESTS:  none
C-2 FLAG:     P0-2 introduced a NEW axe `landmark-unique` violation: it added a
              2nd same-labeled landmark at frontend/src/pages/Committees.tsx:271
              (role="region" aria-label=t("control.title")), duplicating the
              existing <section aria-label> at line 257. Baseline had only one.
              Per lead directive axe residuals are Wave-3 C-2, NOT a Wave-1 REJECT;
              C-2 MUST remove the duplicate label/region.
VERDICT:      APPROVE_INTEGRATE
RATIONALE:    Reflow and single-h1 checkpoints pass at 320px on all routes and the
              error boundary no longer leaks framework text; the one new axe finding
              is tracked as a C-2 residual per the lead's explicit classification rule.
```

### PART: P0-3 | BRANCH: remediation/P0-3 | SHA: 74f20f7 | TIME: 2026-11-19
```
SCOPE:        PASS — files: pipeline/audit.py, pipeline/cli.py, tests/test_audit.py
              (subset of STRATEGY §3 ownership — no out-of-scope file).
DELIVERABLE:  PASS — strict gate extended to resolved/unevaluated baseline findings;
              silent early returns in audit.py emit explicit `not_evaluated`
              findings; 6 regression tests added; false comment at cli.py corrected
              to real values (23 committees / 142 switch waves).
RED/GREEN:    PASS — Supervisor ran the deletion experiment ITSELF on /tmp copies
  RED (remediation/base code + DELETE FROM mandate):
    50 errors, 17 warnings / 50 known errors, 0 new errors,
    223 resolved baseline findings, 2 baseline findings not evaluated
    RED_BASELINE_EXIT:0
  GREEN (fixed code + DELETE FROM mandate):
    STRICT AUDIT FAILED: 223 reviewed baseline finding(s) were not evaluated
      because a source was empty in check(s): mandate_coverage
    GREEN_FIXED_EXIT:1
  INTACT (fixed code + untouched DB):
    275 errors, 61 warnings / 0 resolved / 0 not evaluated
    INTACT_FIXED_EXIT:0
CHECKPOINTS:  CP-P0-3.1/3.2/3.3 proven above (0 -> 1 -> 0).
  CP-P0-3.4 uv run pytest -q (worktree) -> 265 passed, 0 failed, EXIT 0.
  (integration tree -> 259 passed, 4 skipped, 0 failed.)
INTEGRATION:  pytest 259 passed / 4 skipped / 0 failed ; build 0 ; lint 0 errors.
NO-WEAKENING: PASS — tests only ADDED (167 lines); none deleted/skipped/xfail'd.
NO-DATA-LOSS: PASS — DELETE FROM ran only on /tmp copies of data/parlament.db;
              source DB re-verified 5273 mandates, integrity ok.
BACKUP:       PASS
SIDE-QUESTS:  none
VERDICT:      APPROVE_INTEGRATE
RATIONALE:    Independently reproduced the exact proven defect (baseline EXIT 0 with
              "223 resolved") and its fix (EXIT 1 naming mandate_coverage), with no
              false positive on the intact DB; all tests additive and green.
```

### PART: P0-4 | BRANCH: remediation/P0-4 | SHA: d56456c | TIME: 2026-11-19
```
SCOPE:        PASS — .github/workflows/ci.yml only.
DELIVERABLE:  PASS — entire `deploy` job (Vercel POST + Render hook/API POST) removed;
              comment block documents Vercel Git integration + Render checksPass +
              deploy-verify.yml as the single source of truth.
CHECKPOINTS:
  CP-P0-4.1 grep -nE 'curl .*api\.(vercel|render)' -> 0 matches.
            (remaining curls are local GET http://127.0.0.1:8000/api/health* only)
  CP-P0-4.2 grep -n 'exit 0' -> 0 matches.
  CP-P0-4.3 python3 yaml.safe_load -> YAML OK; jobs: test, audit, docker,
            evidence-guards. Only needs: [test, audit] (line 65, docker) — both
            exist, no dangling `needs: deploy`. git diff --check -> EXIT 0.
  CP-P0-4.4 curl -fsS https://parlament-deschis.onrender.com/api/health ->
            "release_tag":"data-20261117-T213500" (GET only), EXIT 0.
INTEGRATION:  ci.yml change independent of runtime gates.
NO-WEAKENING: PASS ; NO-DATA-LOSS: PASS ; BACKUP: PASS
SIDE-QUESTS:  none
VERDICT:      APPROVE_INTEGRATE
RATIONALE:    Deploy theater removed cleanly with valid YAML, no unchecked platform
              POST, no silent skip, no dangling dependency, and live health intact.
```

### PART: P0-5 | BRANCH: remediation/P0-5 | SHA: f46c660 | TIME: 2026-11-19
```
SCOPE:        PASS — 4 scripts: verify-deploy.sh, verify-dashboard.sh (M),
              check-deployment-status.sh, deploy-dashboard.sh (A, adopted from
              previously-untracked — acceptable per lead note). No out-of-scope file.
DELIVERABLE:  PASS — grep -q/test -n assertions; real asset resolved from served
              index.html; hardcoded hash/size removed, measured values printed;
              published_at freshness gate added (default 7 days, env-overridable).
CHECKPOINTS:
  bash -n on all 4 -> "syntax OK" x4.
  CP-P0-5.1 empty local HTML server (127.0.0.1:5271) ->
    RESULT: FAIL - 4 check(s) did not find the thing they check for.
    EMPTY_SCRIPT_EXIT:1. The single ✅ was a genuine HTTP-200 "Main page LIVE"
    pass (the trailing ✅ is explanatory text), no false deployment ✅.
  CP-P0-5.2 live Vercel URL -> Resolved asset /assets/index-7xwk9fe-.js
    (HTTP 200, 410929 bytes, LiveDashboard marker present), RESULT: PASS, EXIT 0.
  CP-P0-5.3 freshness fixture (FRESHNESS_NOW=2026-11-19):
    stale (2026-10-20, 30d) -> "DATASET STALE ... age=30d exceeds maximum of 7d",
    STALE_EXIT:1 ; fresh (2026-11-19) -> "Dataset freshness OK ... age=0d",
    FRESH_EXIT:0.
INTEGRATION:  scripts independent of runtime gates.
NO-WEAKENING: PASS ; NO-DATA-LOSS: PASS ; BACKUP: PASS
SECRETS/DESTR: PASS — token vars are presence guards (:?) in the full verify path
              only; NO secret values read, NO git push, NO deploy API call in any
              script; `trap 'rm -rf "$tmpdir"'` targets only a mktemp -d dir.
SIDE-QUESTS:  none
VERDICT:      APPROVE_INTEGRATE
RATIONALE:    All three checkpoints reproduced independently: empty shell fails with
              no false success, live shell resolves the real asset, and the freshness
              gate is symmetric (stale 1 / fresh 0). No destructive or secret ops.
```

### PART: P0-6 | BRANCH: remediation/P0-6 | SHA: 76ed275 | TIME: 2026-11-19
```
SCOPE:        PASS — 19 tracked *.md files + scripts/check-doc-truth.sh (A).
              No code file. All within ownership.
DELIVERABLE:  PASS — stale tags/counts/sources/claims removed; API.md rewritten from
              live GETs; DASHBOARD-VERIFICATION.md regenerated from fresh curl/build;
              check-doc-truth.sh added.
CHECKPOINTS:
  CP-P0-6.1 bash scripts/check-doc-truth.sh -> "false-claims: 0", EXIT 0
            (integrated tree also: false-claims: 0, EXIT 0).
            Checker pattern independently verified to still contain all 6 core
            strategy strings (data-20261117-T060923, 193 passed, 199 pytest,
            281.ro, 0 JS errors, Ready for Deployment) — not weakened.
  CP-P0-6.2 exact strategy grep over *.md -> 0 matches; excluding
            docs/remediation/* -> 0 matches.
  CP-P0-6.3 live /api/dashboard/stats vs documented values, 8/8 MATCH:
            persons 3388, memberships 7358, switches 2002, committees 26,
            legislatures 20, parties 37, cross_chamber 39, coverage_score 100.
  CP-P0-6.4 custom internal-link checker over git-tracked .md -> 31 links, 0 broken.
            (lychee available but external-URL sweep not run this pass.)
INTEGRATION:  doc-truth 0 ; no effect on build/tests.
NO-WEAKENING: PASS ; NO-DATA-LOSS: PASS ; BACKUP: PASS
SIDE-QUESTS:  none
TRUTH NOTE:   DASHBOARD-VERIFICATION.md still labels UI validation RED (3 routes,
              #310) — accurate for its dated 2026-11-19 snapshot taken before the
              P0-1/P0-2/P0-7 integration; not a false claim. Owner may regenerate
              from the integrated ui_validate output post-merge.
VERDICT:      APPROVE_INTEGRATE
RATIONALE:    check-doc-truth prints false-claims: 0, all stale strings gone, and
              8 documented numbers match the live API exactly; checker itself unweakened.
```

### PART: P0-7 | BRANCH: remediation/P0-7 | SHA: 2aa5401 | TIME: 2026-11-19
```
SCOPE:        PASS — frontend/scripts/check-sparkline-no-nan.mjs (A, acceptable new
              checker), frontend/src/components/DataViz.tsx,
              frontend/src/components/SwitchTimeline.tsx. No out-of-scope file.
DELIVERABLE:  PASS — DataViz.tsx uses denominator = Math.max(1, data.length - 1)
              (kills 0/0 -> NaN in <polyline points>); SwitchTimeline.tsx wraps
              <g>/<line>/<text>/<rect> in an <svg> so React uses the SVG namespace.
RED/GREEN:    PASS — checker on FIXED source:
              "sparkline-no-nan: PASS (6 cases, 0 NaN)", EXIT 0.
              Checker on genuine BASELINE DataViz.tsx (git show remediation/base,
              isolated copy): TypeError: sparklinePoints is not a function, EXIT 1
              — prover that the checker is not rigged to always pass.
CHECKPOINTS:  integrated ui_validate -> overview and /person/... both 0 js-err
              (these were the 2 remaining JS-error routes in the P0-1 isolated log).
INTEGRATION:  ui_validate 0 js-err on all 18 routes ; build 0 ; lint 0 errors.
NO-WEAKENING: PASS ; NO-DATA-LOSS: PASS ; BACKUP: PASS
SIDE-QUESTS:  none
VERDICT:      APPROVE_INTEGRATE
RATIONALE:    Both crash sources fixed at source level; the no-NaN checker genuinely
              fails on baseline and passes on the fix, and the integrated UI gate
              shows zero JS errors on the two previously failing routes.
```

---

## Integration gate (STEP 4 — raw output)

```
Cherry-picks onto remediation/base in /tmp/opencode/wt-INTEGRATE:
  1fcd577 -> 63d4df0  P0-1   (7 files)
  d7fb3c7 -> 7e8ee49  P0-2   (14 files)
  74f20f7 -> b077066  P0-3   (3 files)
  d56456c -> a0123ae  P0-4   (1 file)
  f46c660 -> 2eeeee5  P0-5   (4 files)
  76ed275 -> 1e1bb3e  P0-6   (20 files)
  2aa5401 -> 58ec23f  P0-7   (3 files)
CONFLICTS: NONE — all 7 applied cleanly (non-overlapping ownership confirmed).

$ uv run pytest -q
........................................................................ [ 27%]
........................................................................ [ 55%]
........................................................................ [ 83%]
...........................................                              [100%]
259 passed, 4 skipped, 1 warning in 31.08s
PYTEST_EXIT:0
(4 skips = pre-existing "requires the optional archived cdep corpus", identical
 to baseline; NO new skip introduced by remediation.)

$ cd frontend && npm run build
✓ built in 12.19s   BUILD_EXIT:0
$ cd frontend && npm run lint
✖ 7 problems (0 errors, 7 warnings)   LINT_EXIT:0
(7 warnings = pre-existing react-hooks/exhaustive-deps, configured as warn.)

UI VALIDATION (dev server :5183, PARLAMENT_API_PROXY_TARGET=live onrender):
  PARLAMENT_API_PROXY_TARGET=https://parlament-deschis.onrender.com npm run dev \
    -- --host 127.0.0.1 --port 5183 --strictPort   -> VITE ready, HTTP 200
$ python3 scripts/ui_validate.py http://127.0.0.1:5183
  18/18 routes rendered
  18/18 routes 0 js-err            <-- WAVE-1 UI GATE: PASS
  Result line: "UI VALIDATION FAIL"  <-- due to axe residuals ONLY (see below)
  UIVALIDATE_EXIT:1

$ bash scripts/check-doc-truth.sh
false-claims: 0
DOC_TRUTH_EXIT:0
```

### Axe residuals (Wave-3 C-2, NOT Wave-1 REJECT) — exact file:line

Supervisor re-ran axe on the integrated tree at 1280px to capture exact targets:

| Route | Violation | Impact | Source file:line |
|---|---|---|---|
| `/` | `aria-allowed-role` (4 nodes) — `role="link"` on `<article>` | minor | `frontend/src/components/DashboardCard.tsx:81` |
| `/` | `color-contrast` (1) — "39 in both" `text-slate-200` | serious | `frontend/src/components/CrossChamberFlow.tsx:86-87` |
| `/` | `heading-order` (1) — `Members of Parliament` `<h3>` | moderate | `frontend/src/components/DashboardCard.tsx:100` (title from `LiveDashboard.tsx:93`) |
| `/` | `scrollable-region-focusable` (2) — `max-h-64/max-h-32 overflow-y-auto` | serious | `frontend/src/components/Hemicycle.tsx:133`, `PartyListTable.tsx:55`, `CommitteeControl.tsx:136`, `CrossChamberFlow.tsx:113` |
| `/committees` | `landmark-unique` (1) — duplicate `aria-label=t("control.title")` | moderate | `frontend/src/pages/Committees.tsx:271` (NEW, added by P0-2; duplicates `:257`) |

All are accessibility-only; none is a JS error or a functional crash. Per the lead's
STEP-4 directive these are classified as Wave-3 C-2 residuals, not a Wave-1 REJECT.

---

## Audit log (destructive-operation watch)

| Time | Operation | By | Verdict |
|---|---|---|---|
| 2026-11-19 09:24 | `git tag -a pre-remediation-2026-11-19` | lead | OK — additive |
| 2026-11-19 09:24 | `git branch remediation/base` | lead | OK — additive |
| 2026-11-19 09:24 | `tar` snapshot to `/tmp/opencode/pd-backups/` | lead | OK — additive |
| 2026-11-19 (supervisor pass) | 7 cherry-picks into `/tmp/opencode/wt-INTEGRATE` (branch `remediation/INTEGRATION-SUP`) | supervisor | OK — isolated worktree, 0 conflicts |
| 2026-11-19 (supervisor pass) | `DELETE FROM mandate` on `/tmp/opencode/sup-red-*.db` only (RED/GREEN experiment) | supervisor | OK — /tmp copies only; source DB untouched (5273 mandates, integrity ok) |
| 2026-11-19 (supervisor pass) | ONLY `docs/remediation/STATE.md` edited in the project | supervisor | OK — no production code or other doc touched |
| — | **no push / no deploy / no secret access / no data deletion** | all | OK — verified across all 7 diffs and the integration run |

---

# WAVE 2 — Supervisor verdicts (adversarial verification, 2026-11-19)

**Role:** Supervisor / adversarial QA lead. Default REJECT until raw output proves PASS.
**Recipe followed:** `docs/remediation/SUPERVISOR-RECIPE.md` (all sections), `STRATEGY.md`
(§0, §2, §3b, §6), `RECIPES.md` (R-W2-A..E). No production file edited — only this
`STATE.md` and isolated worktrees under `/tmp/opencode/`.

**Wave 2 status:** PARTIAL — W2-A/B/C/D `APPROVE_INTEGRATE`; **W2-E `REJECT`**
(CSP interface-contract mismatch, see below). All static integration gates green;
live (deployed) verification not possible without an owner-approved deploy → PENDING.

## Backup integrity (STEP 2 — raw output)

```
$ git -C /home/nedaktov/parlament-deschis rev-parse 'pre-wave2-2026-11-19^{}'
f1a45083c4e14ba50883ed7bc681ced1f4087978      EXIT:0
$ git rev-parse 'pre-remediation-2026-11-19^{}'
eb069d2b1de953a89489245ef6418a66a7b652ba      EXIT:0
$ git rev-parse 'remediation/wave2-base^{}'
f1a45083c4e14ba50883ed7bc681ced1f4087978      EXIT:0
$ cd /tmp/opencode/pd-backups && sha256sum -c SHA256SUMS.txt
parlament-deschis-pre-remediation-2026-11-19.tar.gz: OK   EXIT:0
```
Backup integrity: **PASS**. All 5 commit parents verified = `f1a4508`.

## Scope police (STEP 3 — `git diff --name-only remediation/wave2-base..remediation/<b>`)

| Part | Files in diff | In §3b ownership? |
|---|---|---|
| W2-A | `backend/deps.py`, `backend/graphql/schema.py`, `backend/main.py`, `tests/test_graphql_convergence.py` (new) | YES (poller.py + test_security_hardening.py unchanged — allowed) |
| W2-B | `backend/queries.py`, `backend/routers/api.py`, `tests/test_admin_lockout.py` (new), `tests/test_api.py` | YES (test_analytics_transparency.py unchanged — allowed) |
| W2-C | `pipeline/db.py`, `scripts/prepare_db.py`, `tests/test_db_schema.py` | YES |
| W2-D | `backend/cache.py`, `backend/routers/exports.py`, `tests/test_api_exports.py`, `tests/test_cache.py` | YES |
| W2-E | `.github/workflows/data.yml`, `.github/workflows/deploy-verify.yml`, `Dockerfile`, `vercel.json` | YES (render.yaml + ci.yml untouched — correct) |

**Zero out-of-scope files in any part.** No deleted/skipped/xfail'd test, no secret value,
no push/deploy API call in any added line. `git diff --check` clean on all 5 branches.
(W2-C's `DELETE FROM membership WHERE id=?` operates on the *temporary prepared copy*
after repointing evidence rows; its `DROP INDEX ux_membership_closed_stint` is inside a
test on a `tmp_path` synthetic DB — both are the intended dedup/test-isolation logic,
not destructive ops on the source.)

## Per-part verdicts (format from SUPERVISOR-RECIPE §4)

```
PART: W2-A | BRANCH: remediation/W2-A | SHA: 7ae8a3f | TIME: 2026-11-19
SCOPE:        PASS — backend/deps.py, backend/graphql/schema.py, backend/main.py,
              tests/test_graphql_convergence.py (new). All in §3b; no out-of-scope file.
DELIVERABLE:  PASS — make_engine symbol preserved (schema.py:51);
              generationalShift 0 -> 30 rows; crossChamber 39 == REST 39;
              1 SQL statement/field (<20); 1 engine/app; 5 security headers on
              /api/health; /graphql no-store; poller on_cycle clears both caches.
RED/GREEN:    PASS — supervisor real-data probe (TestClient, /tmp copy of
              data/parlament.db): "make_engine symbol present: True",
              "generationalShift ... rows: 30", "crossChamber ... count: 39",
              "REST cross-chamber count: 39", "EQUAL gql==rest: True",
              "SQL generationalShift: 1 SQL crossChamber: 1 both<20: True",
              "engine creations after lifespan: 1" and still 1 after 2 fields.
CHECKPOINTS:  generationalShift non-empty PASS (30); crossChamber==REST PASS (39==39);
              SQL<20 PASS (1); engine==1 PASS; headers PASS (CSP-RO/nosniff/DENY/
              strict-origin-when-cross-origin/camera=(),microphone=(),geolocation=());
              /graphql cache-control "no-store, no-cache, must-revalidate" PASS;
              both caches invalidated PASS (ON_CYCLE_INVALIDATE test);
              uv run pytest -q -> 267 passed, 4 skipped (pre-existing), 0 failed;
              uv run ruff check backend pipeline -> "All checks passed!".
INTEGRATION:  see integrated gate below (280 passed / ruff clean / build 0 / lint 0).
NO-WEAKENING: PASS — test file is entirely new (271 lines); no baseline test changed.
NO-DATA-LOSS: PASS — no data file in diff; source DB SHA unchanged.
BACKUP:       PASS (pre-wave2 tag + both checksums ok).
SIDE-QUESTS:  none.
VERDICT:      APPROVE_INTEGRATE
RATIONALE:    Independently reproduced all six claims on real data with a local
              TestClient: 30 generational rows, GraphQL==REST cross-chamber 39,
              1 SQL/field, exactly 1 engine, all headers and no-store present,
              make_engine intact; additive tests and clean ruff.
```

```
PART: W2-B | BRANCH: remediation/W2-B | SHA: 3f7a17e | TIME: 2026-11-19
SCOPE:        PASS — backend/queries.py, backend/routers/api.py,
              tests/test_admin_lockout.py (new), tests/test_api.py. All in §3b.
DELIVERABLE:  PASS — MAX_TIMELINE_BUCKETS=400 + @cache_result("timeline") +
              O(n+m) one-sweep get_timeline; IP-keyed _require_admin_token with
              global backstop (compare_digest + 503 fail-closed kept);
              uniform _parse_date (invalid as_of -> 422); half-open [start,end)
              in api.py:353/404 and queries.py:769.
RED/GREEN:    PASS — supervisor real-data probe:
              "full-range timeline HTTP: 422 time_s: 0.0308 ... 2515 date buckets;
              maximum is 400", "as_of=garbage HTTP: 422", "as_of=valid HTTP: 200",
              "admin guess codes: [401,401,401,401,401,429,429,429,429,429]",
              "10th guess is 429: True".
CHECKPOINTS:  full-range timeline 422 in 0.03s (<0.5s) PASS; as_of garbage 422 PASS;
              boundary probe PASS (agent test test_chamber_and_committees_agree_on_exact_end_date:
              chamber_total == committee_active == 0 on exact end date);
              10 distinct guesses -> 429 PASS;
              uv run pytest -q -> 268 passed, 4 skipped, 0 failed; ruff clean.
INTEGRATION:  integrated gate below green.
NO-WEAKENING: PASS — 2 new files + additive tests only; none deleted/skipped/xfail.
NO-DATA-LOSS: PASS — no data file in diff.
BACKUP:       PASS.
SIDE-QUESTS:  none.
VERDICT:      APPROVE_INTEGRATE
RATIONALE:    All three bug fixes independently reproduced: an oversized timeline
              is now a 30ms 422, garbage as_of is a 422, and the 10th distinct
              wrong guess from one IP is a 429; the boundary probe agrees.
```

```
PART: W2-C | BRANCH: remediation/W2-C | SHA: c975735 | TIME: 2026-11-19
SCOPE:        PASS — pipeline/db.py, scripts/prepare_db.py, tests/test_db_schema.py.
DELIVERABLE:  PASS — 9 legacy closed-stint duplicates deduped on the prepared copy
              with evidence repointed to the survivor; uq_stint re-expressed as a
              COALESCE(...) expression index; ux_membership_closed_stint FAIL-FAST
              (try/except swallow removed from ensure_schema).
RED/GREEN:    PASS — supervisor ran prepare_db.py itself on a /tmp COPY:
              "prepared ... (23164 KiB, 18 tables, 88 schema rows,
              journal_mode=DELETE, deduped_memberships=9)".
CHECKPOINTS:  prepared DB -> dup_groups: 0; uq_stint: True;
              ux_membership_closed_stint: True; integrity: ok; journal_mode: delete;
              person 3388 / membership 7349 / mandate 5273 / switch_wave 142;
              source DB SHA before==after==71fd14063d688d47ed5900cff718f501cd6adf08a55521a554a753782faa51b2;
              uv run pytest -q -> 261 passed, 4 skipped, 0 failed; ruff clean.
INTEGRATION:  integrated gate below green. NOTE: with fail-fast integrated, starting
              the app against the RAW data/parlament.db (still 9 dupes) now aborts
              startup on uq_stint — this is the intended W2-C contract; the runtime
              DB must be produced by prepare_db.py first. Live curls used the prepared DB.
NO-WEAKENING: PASS — the legacy-tolerance test was STRENGTHENED to expect
              IntegrityError, not loosened; all additions.
NO-DATA-LOSS: PASS — source DB byte-identical; deletion only on temp prepared copy.
BACKUP:       PASS.
SIDE-QUESTS:  none.
VERDICT:      APPROVE_INTEGRATE
RATIONALE:    On a /tmp copy the dedup removed exactly 9 duplicates (7358->7349),
              both unique indexes are present, integrity ok, all other counts
              unchanged, and the source DB SHA is unchanged.
```

```
PART: W2-D | BRANCH: remediation/W2-D | SHA: 2bbb85e | TIME: 2026-11-19
SCOPE:        PASS — backend/cache.py, backend/routers/exports.py,
              tests/test_api_exports.py, tests/test_cache.py. All in §3b.
DELIVERABLE:  PASS — /api/export/report caches only the plain data dict
              (_build_report_payload) and builds a fresh JSONResponse +
              generated_at per request; invalidate_all() clears both the result
              cache and the traseism overview cache.
RED/GREEN:    PASS — supervisor real-data probe (two GET /api/export/report):
              "generated_at1: 2026-11-19T16:07:31.639225+00:00",
              "generated_at2: 2026-11-19T16:07:31.649691+00:00",
              "DIFFERENT: True", "totals equal: True".
CHECKPOINTS:  two requests -> different generated_at PASS; cached value is a
              dict (not JSONResponse) PASS (agent test asserts isinstance dict,
              not Response, no generated_at key); invalidate_all clears both PASS
              (agent test test_invalidate_all_clears_both_caches);
              uv run pytest -q -> 261 passed, 4 skipped, 0 failed; ruff clean.
INTEGRATION:  integrated gate below green (live curl also confirms DIFFERENT).
NO-WEAKENING: PASS — additive tests only.
NO-DATA-LOSS: PASS — no data file in diff.
BACKUP:       PASS.
SIDE-QUESTS:  none.
VERDICT:      APPROVE_INTEGRATE
RATIONALE:    Consecutive downloads carry distinct microsecond timestamps while
              totals stay equal; the cache holds a plain dict and invalidate_all
              clears both caches, all reproduced independently.
```

```
PART: W2-E | BRANCH: remediation/W2-E | SHA: b32e0f0 | TIME: 2026-11-19
SCOPE:        PASS — .github/workflows/data.yml, .github/workflows/deploy-verify.yml,
              Dockerfile, vercel.json. All in §3b; ci.yml/render.yaml untouched.
DELIVERABLE:  PASS for all config checkpoints; FAIL for the cross-layer contract.
              /graphql rewrite present BEFORE catch-all (rewrites order:
              /api/:path*, /graphql, /(.*)); /assets/(.*) immutable
              (public, max-age=31536000, immutable); /.(*) security headers
              present; grep '@v[0-9]' -> 0; both uv sync lines have --locked and
              uv==0.13.1; vercel.json + all 5 workflow YAMLs valid; git diff --check
              clean; 8 action pins (5 unique repos) all 40-hex and MATCH git ls-remote
              of their annotated tags: checkout@v4=11d5960a..., setup-uv@v5=d4b2f3b6...,
              cache@v4=0057852b..., gh-release@v2=3bb12739..., github-script@v7=f28e40c7...
RED/GREEN:    N/A (config part).
CHECKPOINTS:  all R-W2-E config checkpoints PASS, EXCEPT the interface contract.
CSP-MISMATCH: FAIL — STRATEGY §3b: "W2-A adds SecurityHeadersMiddleware in
              backend/main.py; W2-E adds the matching headers in vercel.json.
              Both layers must agree." Raw values:
              FASTAPI_CSP: default-src 'self'; base-uri 'self'; object-src 'none';
                script-src 'self'; style-src 'self' 'unsafe-inline';
                img-src 'self' data:; font-src 'self' data:; connect-src 'self'
              VERCEL_CSP : default-src 'self'; script-src 'self' 'unsafe-inline'
                'unsafe-eval'; style-src 'self' 'unsafe-inline';
                img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'
              EQUAL: False. Vercel omits base-uri/object-src/font-src, adds
              'unsafe-inline' 'unsafe-eval' to script-src, and adds frame-ancestors;
              FastAPI is stricter. Report-Only in both layers, so no blocking
              impact, but the strategy contract is violated.
INTEGRATION:  integrated gate below green. LIVE header verification on the deployed
              Vercel origin: NOT POSSIBLE without deploy -> config-verified,
              live-pending-deploy (per R-W2-E step 4).
NO-WEAKENING: PASS — config-only; no test touched.
NO-DATA-LOSS: PASS — no data file in diff.
BACKUP:       PASS.
SIDE-QUESTS:  none.
VERDICT:      REJECT(CSP Report-Only value in vercel.json does not match W2-A's
              FastAPI SecurityHeadersMiddleware CSP — violates STRATEGY §3b
              interface contract "Both layers must agree"; one-line fix: make the
              vercel.json CSP string byte-equal to backend/main.py's CSP string).
RATIONALE:    Every config checkpoint passes and all 8 SHA pins verify against
              remote tags, but the two security layers emit materially different
              CSP policies, which the authoritative strategy forbids.
```

## Integration gate (STEP 4 — raw output)

```
Cherry-picks onto remediation/wave2-base (f1a4508) in /tmp/opencode/wt-INTEGRATE2
(branch remediation/INTEGRATION-SUP2), in order:
  7ae8a3f -> 83556af  W2-A   (4 files)   EXIT:0
  3f7a17e -> 6dffa63  W2-B   (4 files)   EXIT:0
  c975735 -> 12d68f8  W2-C   (3 files)   EXIT:0
  2bbb85e -> 5c52cbd  W2-D   (4 files)   EXIT:0
  b32e0f0 -> 587307d  W2-E   (4 files)   EXIT:0
CONFLICTS: NONE — all 5 applied cleanly (disjoint §3b ownership confirmed).
Integrated HEAD: 587307d.

$ uv run pytest -q
280 passed, 4 skipped, 1 warning in 30.03s   PYTEST_EXIT:0
(4 skips = pre-existing "requires the optional archived cdep corpus":
 test_cdep_roster.py, test_crosscheck.py, test_group_discovery.py,
 test_ingest_dedup_scope.py; NO new skip introduced.)

$ uv run ruff check backend pipeline scripts tests
All checks passed!   RUFF_EXIT:0

$ cd frontend && npm run build
✓ built in 8.27s   BUILD_EXIT:0
$ cd frontend && npm run lint
✖ 7 problems (0 errors, 7 warnings)   LINT_EXIT:0
(7 warnings = pre-existing react-hooks/exhaustive-deps, configured as warn.)

$ bash scripts/check-doc-truth.sh
false-claims: 0   DOC_TRUTH_EXIT:0   (docs untouched by all 5 branches)

LIVE local uvicorn (127.0.0.1:5188, PARLAMENT_DB=data/parlament.db = prepared DB):
  GET /api/health -> HTTP 200; headers: cache-control "no-store, no-cache,
    must-revalidate"; content-security-policy-report-only (FastAPI value above);
    x-content-type-options nosniff; x-frame-options DENY;
    referrer-policy strict-origin-when-cross-origin;
    permissions-policy camera=(), microphone=(), geolocation=()   PASS
  POST /graphql {generationalShift} -> 200, errors: None, rows: 30   PASS
  GET /api/export/report x2 -> generated_at
    2026-11-19T16:16:26.884826+00:00 vs 2026-11-19T16:16:26.893927+00:00,
    DIFFERENT: True   PASS
  GET /api/timeline?from=2020-01-01&to=2026-11-19&step_days=1
    -> HTTP:422 TIME:0.002160s
    {"detail":"timeline range produces 2515 date buckets; maximum is 400 ..."}   PASS

LIVE deployed verification (Vercel/Render public URL): NOT RUN — requires
owner-approved deploy; all live claims remain PENDING, none asserted as passing.
```

## Wave 2 audit log (destructive-operation watch)

| Time | Operation | By | Verdict |
|---|---|---|---|
| 2026-11-19 (w2 supervisor pass) | `git worktree add` + 5 cherry-picks into `/tmp/opencode/wt-INTEGRATE2` (`remediation/INTEGRATION-SUP2`) | supervisor | OK — isolated worktree, 0 conflicts |
| 2026-11-19 (w2 supervisor pass) | `prepare_db.py` on `/tmp/opencode/w2-sup-logs/pd-source.db` -> `pd-prepared.db` (9 dupes removed on the copy) | supervisor | OK — /tmp copy only; source DB SHA unchanged |
| 2026-11-19 (w2 supervisor pass) | local uvicorn on 127.0.0.1:5188 against the prepared DB in the worktree | supervisor | OK — localhost only, no deploy |
| 2026-11-19 (w2 supervisor pass) | ONLY `docs/remediation/STATE.md` edited in the project | supervisor | OK — no production code or other doc touched |
| — | **no push / no deploy / no secret access / no data deletion / no forced action** | all 5 parts + integration | OK — verified across all 5 diffs, the SHA pins (verified, not guessed) and the integration run |

---

# WAVE 2 RE-CHECK — Supervisor verdicts (2026-11-19, second pass)

**Trigger:** lead changed both CSP layers to one canonical string after W2-E was REJECTED.
**New tips:** W2-A `d43bd35` (was `7ae8a3f`), W2-E `7444c7b` (was `b32e0f0`); W2-B/C/D unchanged.
**Scope:** re-verify W2-A and W2-E, plus a full 5-part integration on `remediation/wave2-base` (`f1a4508`).
**Edits:** only this `STATE.md`; all builds/tests in `/tmp/opencode/`.

## 1. CSP equality (raw)

```
FASTAPI_CSP (/tmp/opencode/wt-W2-A/backend/main.py):
  default-src 'self'; base-uri 'self'; object-src 'none'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'
VERCEL_CSP (/tmp/opencode/wt-W2-E/vercel.json):
  default-src 'self'; base-uri 'self'; object-src 'none'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'
EQUAL: True
both == canonical: True / True
```

Other security headers (FastAPI vs vercel.json) — all MATCH:

```
X-Content-Type-Options : nosniff == nosniff                          MATCH: True
X-Frame-Options        : DENY    == DENY                             MATCH: True
Referrer-Policy        : strict-origin-when-cross-origin == same     MATCH: True
Permissions-Policy     : camera=(), microphone=(), geolocation=() == same MATCH: True
```

CSP is Report-Only in both layers. FastAPI also forces `cache-control: no-store` on `/api/*`
and `/graphql`; vercel.json carries `CDN-Cache-Control: no-store` on `/api/(.*)` and `/api/health(.*)`.

## 2. W2-A re-verdict

```
$ cd /tmp/opencode/wt-W2-A && git diff 7ae8a3f..d43bd35 --name-only
backend/main.py
$ git diff --stat 7ae8a3f..d43bd35
 backend/main.py | 4 +---   (1 file changed, 1 insertion(+), 3 deletions(-))
$ uv run pytest -q
267 passed, 4 skipped, 1 warning in 25.48s   PYTEST_EXIT:0
$ uv run ruff check backend pipeline
All checks passed!   RUFF_EXIT:0
```

Re-verdict: **APPROVE_INTEGRATE** — CSP now byte-equal to the edge layer; only `backend/main.py`
changed (the CSP line); 267 passed / 0 failed; ruff clean.

## 3. W2-E re-verdict

```
$ cd /tmp/opencode/wt-W2-E && git diff b32e0f0..7444c7b --name-only
vercel.json
$ git diff --stat b32e0f0..7444c7b
 vercel.json | 2 +-
$ jq -r '.rewrites | map(.source) | @json' vercel.json
["/api/:path*","/graphql","/(.*)"]
$ jq -r '[.rewrites | map(.source) | index("/graphql"), index("/(.*)")] | @json'
[1,2]                      # /graphql before catch-all: PASS
$ jq -r '.headers[] | select(.source=="/assets/(.*)") | .headers[] | select(.key=="Cache-Control") | .value'
public, max-age=31536000, immutable        # PASS
$ jq -r '.headers[] | select(.source=="/api/(.*)") | .headers[] | select(.key=="CDN-Cache-Control") | .value'
no-store                                   # PASS
security headers: nosniff / DENY / strict-origin-when-cross-origin /
  camera=(), microphone=(), geolocation=() / CSP-RO (canonical)   # PASS
```

Re-verdict: **APPROVE_INTEGRATE** — CSP now byte-equal to FastAPI; only `vercel.json` changed;
all jq assertions pass.

## 4. Full integration (raw)

**Conflict found (process note, not a part defect).** The new tips are *stacked*, not rebased:
`d43bd35^ == 7ae8a3f` and `7444c7b^ == b32e0f0`. Cherry-picking only the five listed tips onto
`f1a4508` therefore conflicts on `backend/main.py` (the W2-A delta's context is the block its
parent `7ae8a3f` introduced) and would silently omit the parent feature commits (W2-E's
workflows/Dockerfile). Resolution: integrate the **full branch contents**
`7ae8a3f d43bd35 3f7a17e c975735 2bbb85e b32e0f0 7444c7b`; the resulting tree is byte-identical
to every branch tip for the owned files (`git diff <tip> HEAD -- <files>` = empty for all 5).

```
$ git worktree add /tmp/opencode/wt-INTEGRATE3 -b remediation/INTEGRATION-SUP3 remediation/wave2-base
HEAD f1a4508
$ git cherry-pick 7ae8a3f d43bd35 3f7a17e c975735 2bbb85e b32e0f0 7444c7b
7 picks, EXIT:0 each
CONFLICTS: NONE (0 conflicts across all 7 picks)
Integrated HEAD: 0a42bea

$ uv sync --extra dev && uv run pytest -q
280 passed, 4 skipped, 1 warning in 31.45s   PYTEST_EXIT:0
$ uv run ruff check backend pipeline scripts tests
All checks passed!   RUFF_EXIT:0
$ cd frontend && npm ci && npm run build
✓ built in 8.38s   BUILD_EXIT:0
$ npm run lint
✖ 7 problems (0 errors, 7 warnings)   LINT_EXIT:0   (pre-existing exhaustive-deps)
$ bash scripts/check-doc-truth.sh
false-claims: 0   DOCTRUTH_EXIT:0

LIVE uvicorn 127.0.0.1:5190, PARLAMENT_DB=data/parlament.db (copy of source DB prepared by
scripts/prepare_db.py: 23164 KiB, 18 tables, 88 schema rows, journal_mode=DELETE, deduped_memberships=9):
  GET /api/health -> 200
    cache-control: no-store, no-cache, must-revalidate
    content-security-policy-report-only: <canonical string>   PASS
    x-content-type-options: nosniff ; x-frame-options: DENY
    referrer-policy: strict-origin-when-cross-origin
    permissions-policy: camera=(), microphone=(), geolocation=()   PASS
  POST /graphql { generationalShift { party mpsWithBirthDates avgAge medianAge } }
    -> HTTP 200, errors: None, rows: 30, NON_EMPTY: True   PASS
  GET /api/export/report x2 -> generated_at
    2026-11-19T16:34:47.785130+00:00 vs 2026-11-19T16:34:47.796738+00:00
    DIFFERENT: True ; totals_equal: True   PASS
  GET /api/timeline?from=2020-01-01&to=2026-11-19&step_days=1
    -> HTTP:422 TIME:0.014140s
    {"detail":"timeline range produces 2515 date buckets; maximum is 400 ..."}   PASS
```

## 5. Verdict

| Part | Tip | Re-verdict |
|---|---|---|
| W2-A | `d43bd35` | **APPROVE_INTEGRATE** |
| W2-B | `3f7a17e` | APPROVE_INTEGRATE (unchanged; re-confirmed in integration) |
| W2-C | `c975735` | APPROVE_INTEGRATE (unchanged; re-confirmed in integration) |
| W2-D | `2bbb85e` | APPROVE_INTEGRATE (unchanged; re-confirmed in integration) |
| W2-E | `7444c7b` | **APPROVE_INTEGRATE** (prior REJECT resolved: CSP now byte-equal) |

**Integration gate: PASS** — 280 passed / 0 failed, ruff clean, build 0, lint 0 errors,
doc-truth 0, and all four live probes green against the prepared DB. The earlier W2-E REJECT
is lifted. Live deployed (Vercel/Render) verification remains PENDING (needs owner-approved deploy).

## 6. Audit log note (re-check)

| Time | Operation | By | Verdict |
|---|---|---|---|
| 2026-11-19 (re-check) | `git worktree add /tmp/opencode/wt-INTEGRATE3` + 7 cherry-picks (full branch contents) | supervisor | OK — isolated worktree, 0 conflicts |
| 2026-11-19 (re-check) | `prepare_db.py` on a **copy** of `data/parlament.db` inside the worktree | supervisor | OK — source DB untouched (SHA `71fd1406…` unchanged) |
| 2026-11-19 (re-check) | local uvicorn on 127.0.0.1:5190 against the prepared copy | supervisor | OK — localhost only, stopped after probes |
| 2026-11-19 (re-check) | ONLY `docs/remediation/STATE.md` edited in the project | supervisor | OK — no production code or other doc touched |
| — | no push / no deploy / no secret access / no data deletion | re-check | OK |

**Process finding for the lead:** the replacement tips are stacked on the old commits rather than
rebased onto `f1a4508`. A tip-only cherry-pick list cannot reproduce the branch content; the
integration above used the full branch contents and verified byte-identity to each tip.
