# Gate Evidence — W1.1 pre-push local gate sweep (2026-11-21)

**Recipe:** RECIPE AGENT W1-A — Wave 1 step W1.1 of
`docs/CONTINUATION-STRATEGY-2026-11-21.md` (§2 master gate table).

**Mandate (honoured):** no guessing; a check that cannot run is `NOT PROVEN`,
never PASS. No `|| true`, no `continue-on-error`, no silent skips. Every PASS
below carries a printed exit code and output line. Raw logs captured under
`/tmp/opencode/gate-logs/`.

**Baseline at execution:** HEAD `96e6fdd5d75c3f7f51a6888a693eeca40e954674`,
branch `review/completion-20261121`, working tree carried concurrent edits by
other agents in `docs/` and the Obsidian vault (not owned by this agent); no
tracked source was edited by this agent.

## Gate results table

| ID | Exact command | Exit code | Key output line | Status | Timestamp (local, +02:00) |
|---|---|---:|---|---|---|
| G01 | `.venv/bin/python -m pytest -q` | 0 | `384 passed, 1 warning in 60.01s (0:01:00)` | **PASS** | 2026-11-21T11:44:07+02:00 |
| G02 | `.venv/bin/ruff check backend pipeline scripts tests` | 0 | `All checks passed!` | **PASS** | 2026-11-21T11:45:15+02:00 |
| G03 | `cd frontend && npm run lint` | 0 | `✖ 7 problems (0 errors, 7 warnings)` | **PASS** | 2026-11-21T11:45:17+02:00 |
| G04 | `cd frontend && npm run build` | 0 | `✓ built in 9.84s` (main bundle `index-R6NL1YHG.js`) | **PASS** | 2026-11-21T11:45:33+02:00 |
| G05 | `bash scripts/check-doc-truth.sh` | 0 | `false-claims: 0` | **PASS** | 2026-11-21T11:45:54+02:00 |
| G06 | `.venv/bin/python -m pipeline.cli --db data/parlament-real.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json` | 0 | `275 known errors, 0 new errors, 0 resolved baseline findings, 0 baseline findings not evaluated` | **PASS** | 2026-11-21T11:45:56+02:00 |
| G07 | `node scripts/check_livefeed_props.mjs` | 0 | `PASS: LiveFeed props (legislature=2024, chamber=senate) reach queryFn and queryKey` | **PASS** | 2026-11-21T11:46:10+02:00 |
| G08 | `python3 scripts/ui_validate.py http://127.0.0.1:5180` | 0 | `UI VALIDATION PASS: 24 routes, 0 JS errors, 0 axe violations` | **PASS** | 2026-11-21T11:47:13+02:00 |
| G09a | `python3 scripts/vault_sync.py --check` | 0 | `vault_sync --check: clean — 5 generated notes match the source commit` | **PASS** | 2026-11-21T11:46:15+02:00 |
| G09b | `python3 scripts/vault_lint.py` | 0 | `VAULT LINT PASS: 41 notes, all links/frontmatter/vocabularies clean` | **PASS** | 2026-11-21T11:46:15+02:00 |
| G10 | `git diff --check` | 0 | *(empty output, 0 bytes)* | **PASS** | 2026-11-21T11:46:19+02:00 |
| G09a (final re-run) | `python3 scripts/vault_sync.py --check` | 0 | `vault_sync --check: clean — 5 generated notes match the source commit` | **PASS** | 2026-11-21T11:49:06+02:00 |
| G09b (final re-run) | `python3 scripts/vault_lint.py` | 0 | `VAULT LINT PASS: 41 notes, all links/frontmatter/vocabularies clean` | **PASS** | 2026-11-21T11:49:06+02:00 |
| G10 (final re-run) | `git diff --check` | 0 | *(empty output, 0 bytes)* | **PASS** | 2026-11-21T11:49:07+02:00 |

**Summary:** G01–G10 all **PASS**, 0 FAIL, 0 NOT PROVEN. G09 and G10 were
re-run at the end (11:49) after concurrent agents' edits; both remained clean.

## Raw output tails (per gate)

### G01 — pytest (tail)
```
........................................................................ [ 18%]
........................................................................ [ 37%]
........................................................................ [ 56%]
........................................................................ [ 75%]
........................................................................ [ 93%]
........................................................................ [100%]
-- Docs: https://pytest.org/en/stable/how-to/capture-warnings.html
384 passed, 1 warning in 60.01s (0:01:00)
EXIT CODE: 0
```
(Single pre-existing `StarletteDeprecationWarning` from `fastapi/testclient.py`;
not a failure.)

### G02 — ruff (full)
```
All checks passed!
EXIT CODE: 0
```

### G03 — lint (full; 0 errors, 7 pre-existing warnings)
```
> parlament-deschis-frontend@0.1.0 lint
> tsc --noEmit && eslint src --ext .ts,.tsx

src/components/AgeDistributionRadial.tsx
  55:6  warning  React Hook useMemo has missing dependencies: 'centerX', 'centerY', and 'radius'  react-hooks/exhaustive-deps
src/components/TimelineChart.tsx
  172:6  warning  React Hook useMemo has an unnecessary dependency: 'i18n.language'  react-hooks/exhaustive-deps
src/pages/CoverageView.tsx
  33:9  warning  The 'rows' logical expression could make the dependencies of useMemo Hook (at line 52) change on every render  react-hooks/exhaustive-deps
  33:9  warning  The 'rows' logical expression could make the dependencies of useMemo Hook (at line 54) change on every render  react-hooks/exhaustive-deps
  33:9  warning  The 'rows' logical expression could make the dependencies of useMemo Hook (at line 57) change on every render  react-hooks/exhaustive-deps
src/pages/MpComparison.tsx
  52:9  warning  The 'poolList' logical expression could make the dependencies of useMemo Hook (at line 105) change on every render  react-hooks/exhaustive-deps
src/pages/PartyTimeline.tsx
  58:9  warning  The 'rows' logical expression could make the dependencies of useMemo Hook (at line 87) change on every render  react-hooks/exhaustive-deps

✖ 7 problems (0 errors, 7 warnings)
EXIT CODE: 0
```
The 7 warnings are all `react-hooks/exhaustive-deps` and match the accepted
pre-existing baseline (W3.4 in the strategy doc schedules their cleanup).

### G04 — build (tail + asset hashes)
```
dist/assets/index-R6NL1YHG.js                  505.38 kB │ gzip: 154.13 kB
(!) Some chunks are larger than 500 kB after minification.
✓ built in 9.84s
EXIT CODE: 0
```
Built asset SHA-256 hashes (`frontend/dist/`, from `find | sort | sha256sum`):
```
d48edfcb2017fd5ab08e2725d857e6c5f64eaaa980cff03a9e90ea2a1050ab2b  ./assets/index-R6NL1YHG.js
88333b60077125c29badc5fcabc0a557fc97c1a7a2e1cc5fac17d49c5040aa5a  ./assets/index-BDGRixv5.css
b3747148819f2a4eda7882750bc56fa8651e2e2a0dd6d72dbd362ee95654be47  ./assets/Coalitions-BfhZVzqk.js
ae30bdcecbf34f16fac50f4fa61c86c25cfd9563694d17edc06723447866c399  ./assets/Committees-BYt8zhCN.js
364c8291f4653144943d1751d28065bfb07d1df2d2c01f591e02a693415004ff  ./assets/CoordinateSystem-C8P-Cleg.js
ea652fc92882cac99eeb02822c6db5dddd52737ca00d0d1494f31e3f6fe394cb  ./assets/CoverageView-Dk4kiPM_.js
0df47ada03c5636495039bb55843ed7ade3ed6cecda57764ff0725ca4cc80ef9  ./assets/CrossChamberFlow-CY7kOeQQ.js
681fafdd26d557ca103adbff90e221ab22594f0f04bb4277d009d8f69da55214  ./assets/DataViz-BiiVruh_.js
67be8a40294f3c66565f20fce40b26dfe7e1f4a4fba6ba6ed1dbb0c4a7d0a8bd  ./assets/Demographics-CC5otJn3.js
b5a873c1f198030d697c7d073ea8a3173cfd7d8167971ad8127897bfe60fa1b7  ./assets/ErrorState-FtzWoZ9P.js
b172fa24b8d73fcf4c0695c85a79b98bf78d26415c1f802a0cd04f1e5e371568  ./assets/Grafice-B8t2vOQm.js
51e2dba69fce2d1303404ed31b4bbad353e247c65e21a7fe12935934b83d866a  ./assets/Ideology-EdyqJ4rz.js
03ee52cd8ec2bd1bcc6e6facb5084c37f9c92085331309efb78be922142cd7b9  ./assets/install-Bfi3AO-R.js
00e0ac7c4e1d9956af66361a36c645d04fed808468f36e4655b3f88d4520780b  ./assets/install-Bym7DilC.js
5778b0e90e6a7b762a9085424fb57676a480c2bdd7430185629d20819ada1c10  ./assets/installCanvasRenderer-BoCEC6_w.js
74cde1075638c3b9a5273f78f3d8b2bb5d2ed400099cc81d5b5fd63c5fce0512  ./assets/installCommon-Cd0_vrRb.js
2d8897616352f94799a3a5c96ad883d955c2d10f71bf021a0881f041c6bbe32b  ./assets/InstitutionalView-D48gTrEJ.js
b219c43b330cfc5bc15b1f630d22649bf5453a948d29ac2453c942c2b6ba3fe2  ./assets/LegislatureDetail-PW8EepXH.js
713123222614a8d2f46c4422fe58fee5e1ed4832e635a89ac659168dfa0e0e50  ./assets/LiveDashboard-BISf25rQ.js
2e107bef122d5334cc12ce134c594276a94ad08cdcebff4dc1d870efc2d949bc  ./assets/MembershipGantt-DeuGsp0k.js
2a6f5433ee209e25ab883303be8d536d277ede70614bc9cceb580895a12a08ae  ./assets/MpComparison-Du4Ju_Zz.js
dfe3c9368d903fe4d41f1837afadaf4949972862b1d8eb6cc8270654e0293325  ./assets/Mps-ZwsghETF.js
9a72d45a39528aee28f85609a0d6665d98d49286478574e173ac913d94b21192  ./assets/Parties-B1Syp3Ke.js
47f6feae327e1af0e19e42fc8e5c2394d4b1ef4f527b11c6084dda9151d8f77a  ./assets/PartyComparison-D0lnGA7a.js
97e9e6ba82b1a393ac1b09e9997a4e328d19dbbca1efe13ff2dd8a75f227b732  ./assets/PartyNetwork-CJliU9xO.js
b1cdee4eda26b57eb9947824529077956ad8e2a7759259c67550d96f12af62e5  ./assets/PartyProfile-Cmip0clL.js
2f9db0104136059cb8599a0d3aa4b68e27e36040c2b293ff7cb91bbdca9f1535  ./assets/PartyTimeline-qqxOpKQp.js
59889ba3804c39a1aad7dd2c03b4d2ea7870afcf493d83566e202fa286e28293  ./assets/PersonDeepDive-BnY1wXeF.js
00c4dbb2ec9a4e34186264eac33b3c403537bb78f8064e5d94e8d7a133de9c8a  ./assets/points-CWcZs0ic.js
d3678e170756bf5fb5b3ab82a01dea25ee9f42b81a416a87c1d900f848ebdf9e  ./assets/Radar-Bp-50E7h.js
6327aef999f00e66be99fd404a2301bede835380cd81709cb01876d17a635c37  ./assets/Report-C1SGbaxQ.js
0d8e7c34254ff0cbf176494d1264732764204f1620e8c8b2d5a4b440f1714a77  ./assets/Skeleton-Bx_yiXe4.js
8143f25b14ebfc966f76357719ecfcba0d8c0f8c36aa6482b245bd07b892704a  ./assets/SwitchLeaderboard-5Dlg9hQ1.js
eafcf003f9bd8405b3de761deed62b87ffeb2fcde2eb375ddd9f43ce7f9e41f8  ./assets/SwitchTimeline-Dy88Oe9X.js
bd10c2fa127c044a620886b9e02b2b317c6a56bae50829a73de60b0fd414490b  ./assets/TimelineChart-Eq9JpO4q.js
985402bab01a5223f9494a56325a38b3cd15273f4192778974b62c883ccd82d2  ./assets/Topuri-BwL0W1Iu.js
f523c72c4f41a962700b994670d8b1c430fb9f089ea31f8bdf1e075b4213ba56  ./assets/Traseism-CRNFsNxJ.js
aff2ec7485db58bee8b63b8ef31c79aba73ed3f5325c48674c1e1df44d5f9830  ./assets/Voturi-Bxu7nVKJ.js
f3c0693e0e752171c3784a443033581f62049441827c969429324fe13a1d0510  ./favicon.svg
69665571d6d3a7d58eb0a6b189477e558aef641e3af75318f38228f654adf21c  ./index.html
```
Note: the built entry bundle `index-R6NL1YHG.js` differs from the live
`index-D61EXxHz.js` recorded in the strategy doc §0 — relevant to W1.7, but
not a gate assertion here.

### G05 — doc-truth (full)
```
false-claims: 0
EXIT CODE: 0
```

### G06 — strict corpus audit (tail)
```
  [WARNING] vote_evidence  : vote 35087 has incomplete member-level positions
  [WARNING] vote_evidence  : vote 35088 has incomplete member-level positions
  [WARNING] vote_evidence  : vote 35089 has incomplete member-level positions
  [WARNING] vote_evidence  : vote 35090 has incomplete member-level positions
  [WARNING] vote_evidence  : vote 35091 has incomplete member-level positions

275 errors, 234 warnings
275 known errors, 0 new errors, 0 resolved baseline findings, 0 baseline findings not evaluated
EXIT CODE: 0
```
The 234 warnings are vote-evidence advisory notices; the strict gate is the
275-known / 0-new error comparison, which is clean.

### G07 — livefeed props (full)
```
PASS: LiveFeed props (legislature=2024, chamber=senate) reach queryFn and queryKey
EXIT CODE: 0
```

### G08 — UI validation (full)
```
[OK ] overview           /                                             rendered             0 js-err  0 axe
[OK ] traseism           /traseism                                     rendered             0 js-err  0 axe
[OK ] leaderboard        /leaderboard                                  rendered             0 js-err  0 axe
[OK ] demographics       /demographics                                 rendered             0 js-err  0 axe
[OK ] committees         /committees                                   rendered             0 js-err  0 axe
[OK ] party-compare      /compare                                      rendered             0 js-err  0 axe
[OK ] coalitions         /coalitions                                   rendered             0 js-err  0 axe
[OK ] mps                /mps                                          rendered             0 js-err  0 axe
[OK ] mp-compare         /compare-mps                                  rendered             0 js-err  0 axe
[OK ] report             /report                                       rendered             0 js-err  0 axe
[OK ] party-timeline     /party-timeline                               rendered             0 js-err  0 axe
[OK ] coverage           /coverage                                     rendered             0 js-err  0 axe
[OK ] senate-history     /senate-history                               rendered             0 js-err  0 axe
[OK ] electoral          /electoral                                    rendered             0 js-err  0 axe
[OK ] institutional      /institutional                                rendered             0 js-err  0 axe
[OK ] party-profile      /party/PSD                                    rendered             0 js-err  0 axe
[OK ] person-deep-dive   /person/cb5ca84e-7bba-4d0b-bea8-91b81aa8eb53  rendered             0 js-err  0 axe
[OK ] legislature        /legislature/2024                             rendered             0 js-err  0 axe
[OK ] parties            /parties                                      rendered             0 js-err  0 axe
[OK ] votes              /Voturi                                       rendered             0 js-err  0 axe
[OK ] radar              /radar                                        rendered             0 js-err  0 axe
[OK ] grafice            /grafice                                      rendered             0 js-err  0 axe
[OK ] topuri             /topuri                                       rendered             0 js-err  0 axe
[OK ] ideology           /ideology                                     rendered             0 js-err  0 axe

--- details ---

UI VALIDATION PASS: 24 routes, 0 JS errors, 0 axe violations
EXIT CODE: 0
```
G08 was a real browser run (`scripts/ui_validate.py` via Playwright/Chromium
`/usr/bin/chromium`, axe-core at `/tmp/axe.min.js`) against a local backend and
Vite dev server — NOT a curl-only claim.

### G09 — vault sync + lint (full, initial and final re-run identical)
```
vault_sync --check: clean — 5 generated notes match the source commit
EXIT CODE: 0
VAULT LINT PASS: 41 notes, all links/frontmatter/vocabularies clean
EXIT CODE: 0
```

### G10 — git diff --check (full)
```
(empty output; 0 bytes)
EXIT CODE: 0
```

## Residuals / anomalies

- **No FAIL, no NOT PROVEN.** All ten gates are green.
- **Concurrent-work artifacts:** `git status` during the sweep showed other
  agents editing `docs/DASHBOARD-STRATEGY.md`, `docs/remediation/WAVE-4-*.md`,
  and several Obsidian vault notes (plus untracked `.nedcode/` and two new
  docs). None of these files are owned by this agent. The mandated final G09
  re-run (11:49) and a G10 re-run were both clean despite those edits, so no
  concurrent finding was observed. These files were **not** edited by me.
- **Accepted non-failures:** 1 pre-existing pytest deprecation warning; 7
  pre-existing ESLint `react-hooks/exhaustive-deps` warnings; Vite >500 kB chunk
  warning; 234 vote-evidence warnings in the strict audit. None change status.
- **Side effects only:** `frontend/dist/` rebuilt (gitignored per `.gitignore:28`);
  a DB backup copy at `/tmp/opencode/g08-parlament-real.db`; logs in
  `/tmp/opencode/gate-logs/`. No tracked source file was modified by this agent;
  no commit, push, deploy, or branch change was performed.

## Server cleanup confirmation

Local servers were started read-only for G08 with a copied DB:
- Backend: `PARLAMENT_DB=/tmp/opencode/g08-parlament-real.db .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8101`
- Vite: `PARLAMENT_API_PROXY_TARGET=http://127.0.0.1:8101 npm run dev -- --host 127.0.0.1 --port 5180 --strictPort`

Both were stopped after G08. Final verification at 2026-11-21T11:49:
- Port 8101: **free** (no listener)
- Port 5180: **free** (no listener)
- All owned server PIDs (2485070, 2485111, 2485137, 2485138): **absent**
- Other agents' servers on ports 8000, 8001, 5188 were left untouched.

**Server cleanup: CONFIRMED.**

## W1.2 / W1.3 addendum — GitHub PR evidence (2026-11-21)

After the gate sweep, the branch was pushed and PR opened (authorized scope;
no merge, no deploy, no branch-protection change):

```
git push -u origin review/completion-20261121   -> PUSH_EXIT:0, new remote branch
gh pr create --base main --head review/completion-20261121
  -> PR #48  https://github.com/nedaktov-ops/parlament-deschis/pull/48  OPEN
gh pr checks 48 --watch --interval 15
  test              pass  1m4s
  audit             pass  13s
  docker            pass  1m4s
  evidence-guards   pass  16s
  Vercel            pass  (preview deployment)
  WATCH_EXIT:0
```

**Wave 1 step W1.3 (make PR CI green) is GREEN.** Owner-only steps W1.4
(merge), W1.5 (branch protection) and W1.6/W1.7 (deploy/parity) were
deliberately NOT performed. Production therefore still serves the old bundle
and pre-fix backend — see `docs/CONTINUATION-STRATEGY-2026-11-21.md` §5.
