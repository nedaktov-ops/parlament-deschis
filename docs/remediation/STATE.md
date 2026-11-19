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
