---
id: R-09-VERIFICATION-ROLLOUT
type: repair-recipe
title: "R-09 — Master verification & rollout envelope for repair recipes R-01..R-08"
description: "Wave plan, dependency order, per-wave GREEN/AMBER/RED gates, backups, browser/axe/320px/keyboard proof, i18n key-diff, API contracts, vault maintenance, rollback and stop conditions for the 2026-11-21 frontend repair programme."
status: ready-for-implementation
authority: proposal
baseline: eb693b4d9faf558b22925fdb07ba6d118d7f6cef
created: 2026-11-21
inputs:
  - "Parlament Deschis Obsidian vault/40-FRONTEND/TRIAD-AUDIT-2026-11-21.md"
  - "Parlament Deschis Obsidian vault/40-FRONTEND/FRONTEND-AUDIT-2026-11-21.md"
  - docs/CONTINUATION-STRATEGY-2026-11-21.md
  - docs/GATE-EVIDENCE-2026-11-21.md
  - .github/workflows/ci.yml
  - scripts/ui_validate.py
  - scripts/vault_sync.py
  - scripts/vault_lint.py
  - scripts/check-doc-truth.sh
  - docs/repair-recipes/R-01-design-system.md
  - docs/repair-recipes/R-02-layout.md
  - docs/repair-recipes/R-03-scope.md
source_paths:
  - docs/repair-recipes
  - .github/workflows
  - scripts
---

# R-09 — Master verification & rollout envelope (coordinates R-01..R-08)

> **READ-ONLY DECLARATION.** The authoring subagent was **read-only on product
> code**. This document is a strategy + verification recipe, **not an implementation
> and not an execution**. No product file, workflow, script, branch, PR, tag,
> deployment or setting was created or changed to produce it. Every command below
> is specified for the implementer; the outputs quoted are the *expected* outputs
> derived from the cited evidence, not observed results of this authoring session.
> **An unrun check is `NOT PROVEN` — never PASS.** (§15, §19.)

---

## 0. Objective

Provide one evidence-based envelope inside which the eight repair recipes
`R-01..R-08` can land **non-destructively**, in a **defensible dependency order**,
with **one gate vocabulary** and **one truth rule**: no wave advances on an
unproven gate, no recipe edits outside its exclusive file list, and no claim of
browser/axe/320 px/keyboard correctness until a real browser run prints it.

Concretely R-09 delivers:

1. A **recipe inventory + reconciliation gate** (§2): the authoritative scope of
   each recipe is its own §3 exclusive-file list and §10 dependencies, not this
   document. R-09 detects collisions between recipes (§1.4) and refuses to start
   a wave that contains an unreconciled overlap.
2. A **wave plan** (§3) that orders the recipes by dependency, not by convenience:
   visual foundation → shared hooks/state → content honesty → i18n/semantics →
   integration.
3. A **master gate catalogue** (§4) and **per-wave gate tables** (§5) with exact
   command, exact expected output and exact exit code, plus an explicit
   GREEN / AMBER / RED decision for every wave.
4. A **backup + checksum procedure before every wave** (§6) with a restore drill,
   additive only (no force-push, no tag delete, no history rewrite).
5. A **branch / PR / checkpoint protocol** (§7) matching the repo's practice:
   required checks `test`, `audit`, `docker`, `evidence-guards`, **1 approval**,
   **no force push**, owner-only merge/protection/deploy/release actions.
6. **Specifications for the verification scripts to add/update** (§8): the i18n
   key-diff gate, the API contract gate, the extended browser gate (axe + 320 px
   + keyboard + screenshots), and the wave orchestrator that *enforces* the
   `NOT PROVEN` rule.
7. Detailed plans for the currently **NOT PROVEN** areas (§9–§13): browser/axe,
   320 px reflow, keyboard walk, visual regression, i18n key diff, API contract,
   vault sync/lint.
8. **Per-wave rollback** (§14), **stop conditions** (§15), acceptance criteria
   (§16), dependencies (§17), side-quest policy (§18) and an explicit NOT PROVEN
   register (§19).

**Non-goals:** R-09 does not fix any visual, data, i18n or interaction defect; it
does not duplicate any recipe's code changes; it does not merge, deploy, change
branch protection, or touch product files. It only defines *how the other recipes
are proven and released*.

---

## 1. Evidence

### 1.1 Baseline identity (verified by this author, re-verify at execution)

```
$ cd /home/nedaktov/parlament-deschis
$ git rev-parse eb693b4^{tree}
02ac065d7326df6d801242d17998c9d207a1cb43
$ git rev-parse HEAD^{tree}                 # HEAD was 80d91a9, branch docs/triad-audit
02ac065d7326df6d801242d17998c9d207a1cb43
$ git diff --stat eb693b4 HEAD -- frontend backend pipeline scripts tests .github
(empty)
```

Consequence: the **product tree at the briefing baseline `eb693b4` and at the
authoring HEAD `80d91a9` is byte-identical**. Every `path:line` in the input
recipes is valid for both commits. The implementer MUST re-run these three
commands before Wave 0; if the tree hash differs or the product diff is non-empty,
**stop** and re-baseline all recipes (§15 RED condition R-3).

### 1.2 Inputs read (evidence trail)

| Input | What it establishes |
|---|---|
| `TRIAD-AUDIT-2026-11-21.md:19,87-89` | All findings are static-code evidence; browser, axe, touch, print, contrast and runtime claims explicitly **NOT PROVEN**. §4 gives the 8-step enhancement order. |
| `FRONTEND-AUDIT-2026-11-21.md:22-23,109-114` | Same NOT PROVEN rule; X1–X8 content-honesty defects; recommended order. |
| `docs/CONTINUATION-STRATEGY-2026-11-21.md` | §0 verified baseline; §1 governing rules (evidence over assertion, never force-push/reset/tag move, 🔒 owner actions); §2 master gates G01–G12; §3 backup/rollback; §9 GitHub hardening sequence (required checks, 1 approval, no force-push); §11 agent recipe template. |
| `docs/GATE-EVIDENCE-2026-11-21.md` | Last full sweep: G01 384 passed; G02 clean; G03 0 errors / 7 pre-existing warnings; G04 exit 0; G05 `false-claims: 0`; G06 275 known / 0 new; G07 PASS; G08 `UI VALIDATION PASS: 24 routes, zero JavaScript errors, zero axe violations` from a **real Playwright/Chromium run**; G09/G10 clean; PR #48 checks 4/4 SUCCESS. |
| `.github/workflows/ci.yml` | Required check jobs: `test` (ruff + pytest + frontend lint/build), `audit` (strict corpus audit), `docker` (image build + health/route proof), `evidence-guards` (LiveFeed props guard + **probe-only** Playwright check). `evidence-guards:107-123` *reports* whether Playwright/Chromium are available and **skips the live UI check** otherwise — CI does not prove axe. |
| `scripts/ui_validate.py` | 24 routes; axe-core injected from `/tmp/axe.min.js`; hard-coded `/usr/bin/chromium`; exits 1 on any navigation error, console error, page error, axe violation or axe scan error. **No viewport sweep, no keyboard walk, no screenshot capture today.** |
| `scripts/vault_sync.py` | Regenerates 5 notes from git objects at the last non-vault source commit; `--check` detects byte drift and stale files. |
| `scripts/vault_lint.py` | 11 checks: frontmatter, closed vocabularies, relative links, banned literals, orphans, generated-note banners. |
| `scripts/check-doc-truth.sh` | Scans tracked Markdown with `git grep`; excludes `docs/remediation/*`; 14 precise false-claim patterns + stale-tag + false-assertion checks; prints `false-claims: 0` on clean. |
| `docs/repair-recipes/R-01-design-system.md`, `R-02-layout.md`, `R-03-scope.md` | The three recipes available at authoring time: their §3 exclusive files, §9/§8 gate sets and §10/§12 dependencies define the concrete wave assignment for those IDs. |

### 1.3 Current proof status (do not upgrade without a run)

At authoring time: `/tmp/axe.min.js` **absent**; `/usr/bin/chromium` present;
system `python3` imports `playwright`; git identity is `Remediation Bot`.
Consequences:

- `scripts/ui_validate.py` cannot run now (axe script absent) → **G08 is NOT
  PROVEN for every wave** until axe is installed and the gate is executed with a
  live dev server + API proxy.
- **320 px / 768 px / 1024 px reflow, keyboard walk, focus-order, visual
  regression and light/dark screenshots are NOT PROVEN** — no tooling exists in
  the repo and no run was performed.
- The last recorded real browser pass is in `GATE-EVIDENCE-2026-11-21.md:198-200`
  (2026-11-21, local backend + Vite), and it proves only the default viewport,
  axe and JS errors — **not** the new checks R-09 adds.

### 1.4 Coordination findings that MUST be reconciled before Wave 1

These are real contradictions between the sibling recipes, found by reading them.
R-09 does not fix them; it blocks waves until an owner resolves them.

| ID | Finding | Evidence | Required resolution |
|---|---|---|---|
| CO-1 | **Duplicate CSS utility ownership.** R-01 §1.5/AC-9 adds `.surface`, `.page-title`, `.moment-value`, `.badge`, `.stat`, `.data-table` and `.data-bar-fill--*` in `index.css`; R-02 §6 Step 1 + AC also adds `.page-title`, `.moment-value`, `.data-table` in `index.css`. Two recipes claiming the same selectors in the same file. | `R-01-design-system.md:49,1089`, `R-02-layout.md:320-341,825` | One owner per selector. **Recommended:** R-01 owns all definitions in `index.css`; R-02 owns only call-site migration and MUST NOT redefine them. Confirm in both recipes' §3 before Wave 1. |
| CO-2 | **Canvas/ECharts palette ownership.** R-01 §11 defers AP-7 canvas hexes to "R-02"; the actual R-02 is layout and lists canvas colours as out of scope (§11 item 1/3). The work may be orphaned. | `R-01-design-system.md:1040-1041`, `R-02-layout.md:850-857` | Owner decides: assign AP-7 to a specific recipe (likely R-04/R-08) or record an explicit accepted gap. No silent drop. |
| CO-3 | **Exclusive-file overlaps beyond CSS.** R-01 owns `Grafice.tsx`, `Topuri.tsx` (DataBar call sites); R-02 owns all 23 `pages/*.tsx` including those two. | `R-01-design-system.md:125-151`, `R-02-layout.md:181-217` | Split by concern: R-01 edits only the DataBar/type props in those files **before** R-02's class-string migration; or R-02 excludes those files. Sequence within Wave 1 as R-01 → R-02 and use G16 diff-scope gate per commit. |
| CO-4 | **Recipe inventory incomplete at authoring.** Only R-01, R-02, R-03 existed when this was written; R-04..R-08 were still being authored in parallel. | `docs/repair-recipes/` listing at authoring time | Wave 0 step W0.2 reconciles the final §3/§10 of all eight recipes and re-runs the assignment rule in §3.2. Until then, the R-04..R-08 rows in §3.1 are **inferred** and carry no authority. |

---

## 2. Recipe inventory & reconciliation (authoritative scope lives in each recipe)

### 2.1 Inventory at authoring time

| ID | Title / scope | Status at authoring | Authoritative scope source |
|---|---|---|---|
| R-01 | Design-system primitives (HeroGraphic colour, DataBar paint API, ProgressRing, AgeDistributionRadial, token utilities) | Recipe written | `R-01-design-system.md` §3 (7 files + new guard script) |
| R-02 | Layout, containers & type scale (one gutter owner, shared hero, title/moment/table grammar) | Recipe written | `R-02-layout.md` §3 (26 files) |
| R-03 | Unified `useScope()` hook + date scope controls + two additive backend extensions | Recipe written | `R-03-scope.md` §3 |
| R-04 | Inferred: shared state system / component-level tables (LoadingState, EmptyState, ErrorState, About/RollCallTable/TimelineChart) | Not present at authoring | **That recipe's own §3/§10** |
| R-05 | Inferred: i18n sweep + key-diff gate (X4) | Not present at authoring | **That recipe's own §3/§10** |
| R-06 | Inferred: honest counts / denominators / canonical switch definition (X1, FN-2, FN-3, FN-9) | Not present at authoring | **That recipe's own §3/§10** |
| R-07 | Inferred: provenance at the table layer + vote-scope correction (X6, FN-6, FN-8) | Not present at authoring | **That recipe's own §3/§10** |
| R-08 | Inferred: tactile/keyboard semantics, canvas theming, or docs/vault truth (TA-*, AP-7) | Not present at authoring | **That recipe's own §3/§10** |

> The inferred rows are a **planning aid only**. The parent/supervisor must map
> the actual R-04..R-08 files into §3.2's rule at Wave 0. If an actual recipe's
> scope differs from the inference, **the recipe wins**; only the wave assignment
> is recomputed. R-09 never defines another recipe's file list.

### 2.2 Reconciliation gate (Wave 0, W0.2 — executable)

```bash
cd /home/nedaktov/parlament-deschis
ls -1 docs/repair-recipes/R-0[1-8]-*.md | sort          # expect exactly 8 lines
for f in docs/repair-recipes/R-0[1-8]-*.md; do
  echo "=== $f ==="
  grep -nE '^## (3\.|10\.|12\.)|Exclusive file|Dependencies|Side-quest' "$f" | head -20
done
git diff --check                                        # -> empty, exit 0
```

**Expected:** exactly 8 recipe files; each has an exclusive file list and a
dependencies section. **Exit 0.** Any missing recipe, missing section, or an
unresolved CO-1..CO-4 collision → **RED**, no wave starts (§15).

---

## 3. Wave plan & dependency order

### 3.1 Wave table

| Wave | Name | Recipes (default assignment) | Entry condition | Exit / GREEN condition | Owner-only steps |
|---|---|---|---|---|---|
| **W0** | Safety, inventory, tooling | none (no product mutation) | Baseline identity re-verified (§1.1) | Backup + restore drill green; 8 recipes reconciled; R-09 scripts specified/added; G05/G09/G10 green | none |
| **W1** | Visual foundation | R-01, R-02 (CO-1/CO-3 resolved first) | W0 GREEN; CO-1..CO-3 resolved; no other agent editing the owned files | R-01 atomic commit then R-02 atomic commit; G01–G10 + G13 + G15 + G16 green per commit | none |
| **W2** | Shared scope & state | R-03 plus the state-system recipe (per §3.2 rule) | W1 GREEN; both commits on integration branch | Scope/state commits land; G01–G10 + G14 (offline) + G16 green; API params/query keys asserted | none |
| **W3** | Content honesty | count/label + provenance + vote-scope recipes (per §3.2) | W2 GREEN; R-03 hook consumed by the pages being relabelled | All label/provenance/scope commits land; G01–G10 + G06 + G14 + G16 green; audit still 275/0 | none |
| **W4** | i18n & semantics | i18n-sweep recipe LAST + tactile/semantics + any AP-7 canvas recipe | W3 GREEN; every `t()`-adding recipe has landed | i18n key-diff G13 reaches 0 (or dated owner waiver); keyboard walk G15 green; G01–G10 + G16 green | none |
| **W5** | Integration & rollout | integration of all eight | W0–W4 GREEN; full sweep printed; PR checks 4/4 | 🔒 merge to integration branch then main; 🔒 branch protection; 🔒 deploy; `verify-deploy.sh` proof recorded | **merge, protection, deploy, release, policy decisions** |

### 3.2 Assignment rule (deterministic; apply at W0 to R-04..R-08)

Assign each recipe to the **earliest** wave whose preconditions its §10 declares:

1. If its exclusive files are confined to `index.css`, `tailwind.config.js`,
   and presentational components/pages with **no** query-key, API-param, data-label,
   i18n-key or keyboard-semantics change → **W1**.
2. If it introduces a shared hook/context/state component consumed by data pages
   → **W2**.
3. If it changes rendered labels, denominators, provenance or vote scope on data
   pages → **W3** (depends on W2's hook/state).
4. If it adds or changes i18n keys → **W4, after every other key-adding recipe**,
   so the G13 key-diff gate is final. If it changes keyboard/focus/tooltip
   semantics → **W4** (after W1 visual and W2 state components exist).
5. Anything requiring 🔒 owner authority (deploy, protection, release, product
   policy) → **W5** only, and agents STOP and ask.

A recipe whose §10 declares a dependency on a *later* wave is a **cycle** → RED.

### 3.3 Dependency graph (default)

```
W0 ──> W1 (R-01 → R-02) ──> W2 (R-03 + state) ──> W3 (counts/provenance/vote)
                                      └──────────────> W4 (i18n + semantics) ──> W5
```

- R-01 and R-02 are **presentation-only**: no runtime dependency on data recipes
  (R-01 §12). They can be authored in parallel but **landed sequentially** because
  of CO-1/CO-3.
- R-03 is the **data-foundation**: scope must be real before counts/provenance are
  relabelled, otherwise labels describe an unscoped number.
- i18n is **last** because every other recipe can add `t()` keys; a key sweep run
  earlier is invalidated by later work (A-13 already recorded the gate RED).

---

## 4. Master gate catalogue (command + expected + exit)

Notation: **exit 0** is required unless stated. `NOT PROVEN` is a **failure** of a
required gate, never a pass. "Owner waiver" is a dated, written decision in the
vault — never a silent skip, never `|| true`, never `continue-on-error`.

| ID | Exact command | Expected output (key line) | Exit | Waves | Waiver |
|---|---|---|---|---:|---|
| **G00** | `sha256sum -c /tmp/opencode/R-09-wave-<N>/MANIFEST.sha256` | one `OK` line per artifact | 0 | all | none |
| **G01** | `.venv/bin/python -m pytest -q` | `0 failed` (last full sweep: `384 passed`); count may rise when recipes add tests | 0 | all | none |
| **G02** | `.venv/bin/ruff check backend pipeline scripts tests` | `All checks passed!` | 0 | all | owner, dated |
| **G03** | `cd frontend && npm run lint` | `0 errors` (7 pre-existing `react-hooks/exhaustive-deps` warnings accepted) | 0 | all | owner |
| **G04** | `cd frontend && npm run build` | `✓ built in …s`, exit 0 | 0 | all | owner |
| **G05** | `bash scripts/check-doc-truth.sh` | `false-claims: 0` | 0 | all | **none** |
| **G06** | `.venv/bin/python -m pipeline.cli --db data/parlament-real.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json` | `275 known errors, 0 new errors, 0 resolved baseline findings, 0 baseline findings not evaluated` | 0 | all | none |
| **G07** | `node scripts/check_livefeed_props.mjs` | `PASS: LiveFeed props … reach queryFn and queryKey` | 0 | all | owner |
| **G08** | `python3 scripts/ui_validate.py http://127.0.0.1:5174` | `UI VALIDATION PASS: 24 routes, zero JavaScript errors, zero axe violations` | 0 | W1+ | **never waive a deliverable route**; tool/server missing → NOT PROVEN |
| **G09** | `python3 scripts/vault_sync.py --check && python3 scripts/vault_lint.py` | `vault_sync --check: clean — 5 generated notes match the source commit`; `VAULT LINT PASS: … notes, all links/frontmatter/vocabularies clean` | 0 | all | owner |
| **G10** | `git diff --check` | empty (0 bytes) | 0 | all | none |
| **G11** | restore drill (§6.3): clone bundle into sandbox, compare HEAD | restored HEAD == frozen baseline SHA | 0 | W0, per wave | none |
| **G12** | `gh pr checks <PR> --watch --interval 15` | `test`, `audit`, `docker`, `evidence-guards` all `pass` (4/4 SUCCESS) | 0 | W1+ | owner |
| **G13** | `python3 scripts/check_i18n_keys.py` | `i18n key-diff: 0 missing ro, 0 missing en, 0 raw keys` (transition: missing count must not increase vs frozen baseline) | 0 | W1+ | owner, **dated**, only for remaining keys |
| **G14** | `python3 scripts/generate_openapi.py && python3 scripts/check_api_contract.py --offline` | `API CONTRACT PASS: <N> endpoints documented, 0 undocumented, 0 missing` | 0 | W2+ | none (offline) |
| **G14-live** | `TARGET_SHA=<sha> EXPECTED_RELEASE=$(cat data/latest-release.txt) bash scripts/verify-deploy.sh` | script's final success line + exit 0 | 0 | W5 | 🔒 owner/deploy; tokens absent → NOT PROVEN |
| **G15** | `python3 scripts/ui_validate.py http://127.0.0.1:5174 --widths 320,768,1024 --keyboard --screenshot-dir /tmp/opencode/R-09/screenshots/<wave>` | `EDGE PROBE PASS: 72/72 checks`; `KEYBOARD WALK PASS: …`; screenshot manifest written | 0 | W1+ (targeted), W5 (full) | none; unrun → NOT PROVEN |
| **G16** | `git diff <base>..HEAD --name-only` ⊆ declared exclusive files of recipes in the wave | empty `comm -23` against allowlist | 0 | all | none |

Gate vocabulary:

- **GREEN** — every required gate for the wave printed PASS with exit 0 and raw
  output archived (§7.3). No `NOT PROVEN` in a required gate.
- **AMBER** — every runnable gate green, but a 🔒 owner decision or an unavailable
  *environment prerequisite* blocks the next step (e.g. deploy tokens, axe install
  approval, product-policy call). The wave does **not** advance; the blocker is
  named and dated. AMBER is **not** a pass.
- **RED** — any required gate FAIL, any backup/restore failure, any exclusive-file
  violation, any new audit error, any i18n regression, any unresolved CO-* item.
  **Stop; do not start the next wave; rollback per §14.**

---

## 5. Per-wave gate tables (exact command → expected → exit → decision)

### 5.1 Wave 0 — safety, inventory, tooling

| Step | Command | Expected | Exit | Decision |
|---|---|---|---:|---|
| W0.1 baseline | `git rev-parse eb693b4^{tree} && git rev-parse HEAD^{tree} && git diff --stat eb693b4 HEAD -- frontend backend pipeline scripts tests .github` | tree `02ac065…` twice; diff empty | 0 | mismatch → RED R-3 |
| W0.2 inventory | see §2.2 | 8 recipe files; CO-* resolved | 0 | missing/overlap → RED R-7 |
| W0.3 backup | §6.1 with `<N>=W0` | manifest lines all `OK` | 0 | mismatch → RED R-1 |
| W0.4 restore drill | §6.3 | restored HEAD = `eb693b4…` | 0 | mismatch → RED R-1 |
| W0.5 docs/vault | G05, G09, G10 | `false-claims: 0`; vault clean; empty diff | 0 | any finding → RED |
| W0.6 tooling | §8 scripts present and `--help`/dry-run exit 0 | each script exits 0 on help | 0 | missing tool → AMBER (NOT PROVEN) |

**W0 GREEN** = W0.1–W0.5 all exit 0 and W0.6 scripts available. W0.6 unavailable
→ AMBER with named resolver, no product wave starts.

### 5.2 Wave 1 — visual foundation (R-01 then R-02)

Run the gate set **after each atomic commit**. Commands (all from repo root unless
noted):

```bash
cd /home/nedaktov/parlament-deschis
G="bash scripts/check_wave_gate.sh W1"   # §8.4 orchestrator; prints the table below
$G
```

| Gate | Command | Expected | Exit |
|---|---|---|---:|
| backup | G00 | all `OK` | 0 |
| static guard (R-01) | `node scripts/check-design-primitives.mjs` | `N/N PASS`, pre-fix RED evidence retained | 0 |
| static counts (R-02) | CP-R02-02 → CP-R02-07 | exact values in `R-02-layout.md` §7 | 0 |
| lint | G03 | 0 errors | 0 |
| build | G04 | exit 0 | 0 |
| UI / axe | G08 | `UI VALIDATION PASS: 24 routes, zero JavaScript errors, zero axe violations` | 0 |
| edge/keyboard/screens | G15 | `EDGE PROBE PASS: 72/72 checks`; `KEYBOARD WALK PASS`; manifest | 0 |
| scope | G16 | only R-01 files (commit 1) / only R-02 files (commit 2) | 0 |
| i18n | G13 | missing count ≤ frozen baseline | 0 |
| docs/vault | G05, G09, G10 | clean | 0 |

**GREEN** = all exit 0. **AMBER** = G08/G15 NOT PROVEN (axe absent) *only if* an
owner has dated the environment gap and accepts that the visual claims stay NOT
PROVEN; the commit may land but must be labelled unverified. **RED** = any FAIL,
CO-1/CO-3 unresolved, or a file outside the recipe's §3 changed.

### 5.3 Wave 2 — shared scope & state

| Gate | Command | Expected | Exit |
|---|---|---|---:|
| backup | G00 | all `OK` | 0 |
| tests | G01 | `0 failed` | 0 |
| lint/ruff/build | G02, G03, G04 | clean / 0 errors / exit 0 | 0 |
| API contract (offline) | G14 | `API CONTRACT PASS…` | 0 |
| URL scope assertions | `python3 scripts/check_api_contract.py --base http://127.0.0.1:8101 --scope` | every declared scope param returns 200 + expected keys | 0 |
| UI / axe | G08 | 24 routes, zero axe | 0 |
| docs/vault | G05, G09, G10 | clean | 0 |
| scope | G16 | only W2 recipes' files | 0 |

**GREEN** = all exit 0. **AMBER** = G14-live not runnable (owner/deploy token).
**RED** = a scope control that silently does nothing, an API param sent to an
endpoint that does not support it, a new audit error, or a diff-scope violation.

### 5.4 Wave 3 — content honesty

| Gate | Command | Expected | Exit |
|---|---|---|---:|
| backup | G00 | all `OK` | 0 |
| tests (incl. label/state tests) | G01 | `0 failed` | 0 |
| strict audit | G06 | `275 known errors, 0 new errors` | 0 |
| lint/build | G03, G04 | clean / exit 0 | 0 |
| API contract | G14 | `API CONTRACT PASS…` | 0 |
| UI / axe | G08 | 24 routes, zero axe | 0 |
| doc truth | G05, G09, G10 | `false-claims: 0`; vault clean | 0 |
| scope | G16 | only W3 recipes' files | 0 |

**RED** = a headline count still presented without a definition/denominator, a
page-local cap labelled as a corpus total, a fabricated null→0 value, or any
audit regression.

### 5.5 Wave 4 — i18n & semantics (i18n recipe LAST)

| Gate | Command | Expected | Exit |
|---|---|---|---:|
| backup | G00 | all `OK` | 0 |
| i18n key diff | G13 | `0 missing ro, 0 missing en, 0 raw keys` (or dated owner waiver for named keys) | 0 |
| keyboard walk | G15 (`--keyboard`) | `KEYBOARD WALK PASS` | 0 |
| 320 px probe | G15 (`--widths 320,768,1024`) | `EDGE PROBE PASS: 72/72 checks` | 0 |
| lint/build/tests | G03, G04, G01 | clean / exit 0 / `0 failed` | 0 |
| UI / axe | G08 | 24 routes, zero axe | 0 |
| doc truth | G05, G09, G10 | clean | 0 |
| scope | G16 | only W4 recipes' files | 0 |

**RED** = G13 count increases vs baseline, a raw key rendered in Romanian, a
keyboard-inert pointer affordance, or a focus trap. **AMBER** = named owner
waiver for residual keys with a dated decision.

### 5.6 Wave 5 — integration & rollout (owner gate)

| Gate | Command | Expected | Exit | Owner |
|---|---|---|---:|---|
| full sweep | G00, G01–G11, G13, G14, G15, G16 | all PASS, raw output archived | 0 | agent runs, supervisor reads |
| PR checks | G12 | 4/4 SUCCESS (`test`, `audit`, `docker`, `evidence-guards`) | 0 | — |
| pre-merge tag | `git tag -a repair-w5-before-merge -m "…" && git push origin repair-w5-before-merge` | tag exists, additive | 0 | 🔒 owner |
| merge integration → main | `gh pr merge <PR> --merge` | main SHA changes, checks green | 0 | **🔒 owner** |
| branch protection | required checks `test/audit/docker/evidence-guards`, 1 approval, block force-push + deletion, require PR | protection API 200 | 0 | **🔒 owner** |
| deploy proof | G14-live (`verify-deploy.sh`) | success line, exit 0 | 0 | **🔒 deploy** |
| evidence record | G05 + G09 + G10 + archived bundle hashes | clean | 0 | agent |

No agent performs the 🔒 rows. If they are not performed, the programme ends
**AMBER — prepared, not shipped**; production still serves the pre-fix bundle.

---

## 6. Backup + checksum procedure BEFORE every wave (mandatory, additive only)

### 6.1 Full-wave backup

```bash
cd /home/nedaktov/parlament-deschis
N=<W0|W1|W2|W3|W4|W5>
BK=/tmp/opencode/R-09-wave-$N
mkdir -p "$BK"

# 1. freeze identity
git rev-parse HEAD                         | tee "$BK/BASE_SHA"
git rev-parse HEAD^{tree}                  | tee "$BK/BASE_TREE"
git rev-list --left-right --count origin/main...HEAD | tee "$BK/DIVERGENCE"
git log -1 --format='%H %cI %s'            | tee "$BK/HEAD_INFO"
cat data/latest-release.txt                | tee "$BK/RELEASE_PIN"
gh pr list --state open                    > "$BK/PRS.txt"

# 2. quiesce SQLite, then copy DBs (never raw cp of a live WAL db)
sqlite3 data/parlament-real.db "PRAGMA wal_checkpoint(TRUNCATE);"
sqlite3 data/parlament.db       "PRAGMA wal_checkpoint(TRUNCATE);"

# 3. additive git bundle of ALL refs
git bundle create "$BK/pre-$N.bundle" --all
git bundle verify "$BK/pre-$N.bundle"

# 4. copy mutable artifacts
cp -a data/parlament-real.db data/parlament.db data/latest-release.txt "$BK/"
cp -a "Parlament Deschis Obsidian vault" "$BK/vault"
cp -a frontend/dist "$BK/dist" 2>/dev/null || true   # build output only, gitignored

# 5. per-recipe manifests stay intact (do not overwrite the siblings' backups)
for f in /tmp/opencode/R-01/eb693b4/SHA256SUMS \
         /tmp/opencode/R-02-backup/manifest.sha256; do
  [ -f "$f" ] && cp -a "$f" "$BK/$(basename "$(dirname "$f")")-$(basename "$f")"
done

# 6. seal
find "$BK" -type f ! -name 'MANIFEST.sha256' -print0 | sort -z | xargs -0 sha256sum > "$BK/MANIFEST.sha256"
sha256sum -c "$BK/MANIFEST.sha256"          # every line OK
```

### 6.2 Backup acceptance (G00)

- `git bundle verify` prints `The bundle contains these N refs` and exit 0.
- `sha256sum -c "$BK/MANIFEST.sha256"` prints one `OK` per line, exit 0.
- `wc -l < "$BK/MANIFEST.sha256"` equals the file count in `$BK` minus 1.
- Any `FAILED`, missing artifact, or non-zero exit → **RED R-1**; no edits.

> The manifest is a **verification artifact**, not a restore source. Restore from
> the bundle / git, never by copying individual files into a dirty tree.

### 6.3 Restore drill (G11, before the first edit of every wave)

```bash
BK=/tmp/opencode/R-09-wave-$N
git clone --no-local "$BK/pre-$N.bundle" /tmp/opencode/pd-restore-$N
git -C /tmp/opencode/pd-restore-$N rev-parse HEAD        # must equal BASE_SHA
git -C /tmp/opencode/pd-restore-$N status --porcelain    # empty
```

Exit 0 and exact SHA match → drill GREEN. Any mismatch → **RED R-1**.

---

## 7. Branch / PR / checkpoint protocol (non-destructive)

### 7.1 Branch topology

```
main (eb693b4)
  └── repair/frontend-2026-11-21        (integration branch, off baseline)
        ├── repair/R-01-design-system   (atomic commit, exclusive files)
        ├── repair/R-02-layout
        ├── repair/R-03-scope
        └── … one branch per recipe, PR → integration
integration → main                       (single final PR, 🔒 owner merges)
```

Rules:

1. One atomic commit per recipe, on a branch cut from the **frozen baseline** or
   from the integration branch at the previous wave's GREEN head.
2. **Never** `git push --force`, `git reset --hard`, `git tag -d`, branch deletion,
   or `git add -A` (the `deploy-all.sh` footgun). Rollback is `git revert` or an
   additive pin/tag (§14).
3. Every PR targets the integration branch; only the final PR targets `main`.
4. Commit message format: `fix(R-0N): <scope>`; record `git rev-parse HEAD` into
   `/tmp/opencode/R-09-wave-<N>/R0N_SHA` immediately after commit.
5. Product-policy decisions, merge to main, branch-protection changes, secrets,
   releases, deploys and workflow_dispatch are **🔒 owner-only**; agents stop and
   ask (CONTINUATION-STRATEGY §1.4).

### 7.2 PR / branch-protection practice (from repo evidence + strategy §9)

Required on `main` and the integration branch before merge:

| Protection | Setting | Evidence / source |
|---|---|---|
| Required checks | `test`, `audit`, `docker`, `evidence-guards` | `ci.yml` jobs; PR #48 passed 4/4 (`GATE-EVIDENCE:252-261`) |
| Approvals | **1 approval** required | CONTINUATION-STRATEGY §9 step (6) |
| Force push | **blocked** | §9 step (5); §1 rule 3 |
| Branch deletion | **blocked** | §9 step (5) |
| PR required | yes, incl. admins (strict) | §9 steps (6), (8) |
| `data.yml` checks | **not** required on PRs (scheduled/dispatch-only) | §9 final sentence |
| Actions | SHA-pinned; `permissions: contents: read` default | `ci.yml:13-15,20-23` |

Ordering note (§9): backup refs → PR → CI green → triage PRs → block force-push →
require PR + 1 approval → add required checks "loose" after 7 green days → strict.
Agents do not enable protection themselves.

### 7.3 Checkpoint protocol

A **checkpoint** is the archived raw output of a gate — command, stdout+stderr,
exit code, timestamp, HEAD SHA, and the backup manifest hash used. Store under:

```
/tmp/opencode/R-09/evidence/<wave>/<gate-id>.<n>.log
/tmp/opencode/R-09/evidence/<wave>/INDEX.md     # gate → status → log path
```

Rules:

- A gate without an archived log is **NOT PROVEN** even if it was run.
- `INDEX.md` must list every required gate with status PASS / FAIL / NOT PROVEN.
- The final evidence record is committed as a doc-only commit (vault regenerated,
  G05/G09/G10 green) — never mixed with a product commit.

---

## 8. Verification scripts to add/update (specified here; implemented by assignees)

> R-09 does **not** create these files. They are the deliverables of the
> verification implementer and must land in W0 (tooling) before product waves.
> Each script must obey: no `|| true`, no silent skip, explicit exit codes, and a
> `NOT PROVEN`/`SKIP` result that **fails** a required gate when a prerequisite is
> missing.

### 8.1 NEW `scripts/check_i18n_keys.py` — i18n key-diff gate (G13)

Behaviour:

1. Parse `frontend/src/i18n.ts` and extract the **ro** and **en** translation key
   sets from the `resources` object (lines 4, 5, 1049 region).
2. Scan all `frontend/src/**/*.{ts,tsx}` for literal keys in `t("…")`,
   `t('…')`, `i18n.t("…")` and the second argument of `t(key, "English…")`.
3. Report three lists: `missing_ro`, `missing_en`, `raw_keys` (a rendered key that
   equals its own identifier). Also print `default_only` keys (call-site has an
   inline English default but no locale entry) as advisory.
4. Exit 0 only when all three lists are empty. Print exactly:

```
i18n key-diff: 0 missing ro, 0 missing en, 0 raw keys
EXIT CODE: 0
```

Transition mode: with `--baseline <file>` the gate exits 0 if the missing count
is **≤** the frozen baseline (the prior sweep recorded 64 missing keys in
`ACTION-PLAN.md:53` / A-13) **and** no recipe in the current wave increased it.
Final mode (W4) requires 0 or a dated owner waiver listing each residual key.
No network, deterministic, stdlib only.

### 8.2 NEW `scripts/check_api_contract.py` — API contract gate (G14)

Modes:

- `--offline`: run `scripts/generate_openapi.py`, read `pipeline/openapi.json`,
  compare its path set against a maintained allowlist in `docs/API.md` (parse the
  documented endpoint headings). Assert: no undocumented live endpoint, no
  documented endpoint missing from the schema, and required keys for the scope
  endpoints documented by R-03 (`as_of`/`date`, `chamber`, `legislature`).
  Print `API CONTRACT PASS: <N> endpoints documented, 0 undocumented, 0 missing`.
- `--base http://127.0.0.1:8101 [--scope]`: probe a live local backend; assert
  `/api/health`, `/api/health/ready`, `/api/traseism/overview` and the scope
  endpoints return 200 with expected JSON keys; with `--scope` assert each
  declared param is accepted and reflected (deep-link round trip).
- `--live`: called by W5 only via `verify-deploy.sh`; if env tokens absent, print
  `NOT PROVEN: deploy tokens unavailable` and **exit 1**.

Never fabricate a payload; a 500 or a shape mismatch is a FAIL.

### 8.3 UPDATE `scripts/ui_validate.py` — extend the browser gate (G08/G15)

Keep the existing 24-route default behaviour **unchanged** (the `UI VALIDATION
PASS: 24 routes…` line is a stable gate). Add **opt-in** flags:

| Flag | Effect | New assertion |
|---|---|---|
| `--widths 320,768,1024` | for each route, set viewport width; read `document.documentElement.scrollWidth` vs `innerWidth`, and the left/right padding of the sole container | no horizontal overflow (`scrollWidth <= innerWidth + 1`); symmetric gutters 16/24/32 px (±1) |
| `--keyboard` | Tab-walk each route; collect focused elements; assert focus reaches every native button/link/input and that no element has positive `tabindex`; activate chart controls via Enter/Space | `KEYBOARD WALK PASS: <n> routes, 0 focus traps, 0 inert affordances` |
| `--screenshot-dir <dir>` | capture a full-page PNG per route per width into `<dir>` with a stable filename `<route>__<width>.png` | write `<dir>/MANIFEST.sha256` of all PNGs |
| `--axe-path <path>` | allow overriding `/tmp/axe.min.js` | axe scan runs at each width, not just default |

If axe is absent or a required browser prerequisite is missing, print
`NOT PROVEN: axe/browser prerequisite missing` and **exit 1** — do not degrade to
a curl-only check. Route list must include all 24 current routes (it already
does); any recipe adding a route must add it to `ROUTES` in the same commit.

### 8.4 NEW `scripts/check_wave_gate.sh` — wave orchestrator

Usage: `bash scripts/check_wave_gate.sh <W0|W1|W2|W3|W4|W5> [--commit]`.

- Reads the wave's gate list from §5 (embedded table or a small `waves/` manifest).
- Runs each gate in order, capturing stdout+stderr to
  `/tmp/opencode/R-09/evidence/<wave>/<gate>.log` and its exit code.
- Prints one line per gate: `Gxx | command | exit=<n> | PASS|FAIL|NOT PROVEN`.
- Classifies a gate as `NOT PROVEN` when a prerequisite probe fails (axe absent,
  server unreachable, token missing, tool not found); treats that as failure for
  required gates.
- Writes `/tmp/opencode/R-09/evidence/<wave>/INDEX.md` and exits 0 only if every
  required gate is PASS; exits 1 on any FAIL/NOT PROVEN. **`--commit` is refused
  unless exit 0** — this is the mechanical enforcement of the no-false-green rule.

### 8.5 Existing scripts kept as gates (do not weaken)

`scripts/check-doc-truth.sh` (G05), `scripts/vault_sync.py --check` + `vault_lint.py`
(G09), `scripts/check_livefeed_props.mjs` (G07), `scripts/generate_openapi.py`
(G14 helper), `scripts/verify-deploy.sh` (G14-live, owner-only), and each recipe's
own static guard (e.g. R-01 `scripts/check-design-primitives.mjs`, R-02 CP-R02-*).
Never add `|| true` to any of them; never relax a pattern to make a gate green.

---

## 9. Browser / axe / 320 px / keyboard verification plan (currently NOT PROVEN)

### 9.1 Prerequisites (must be printed before G08/G15)

```bash
python3 -c 'import playwright; print("playwright OK")'     # currently OK
test -x /usr/bin/chromium && echo "chromium OK"           # currently OK
test -s /tmp/axe.min.js && echo "axe OK" || echo "AXE ABSENT — G08/G15 NOT PROVEN"
# if absent, fetch once (network permitting):
curl -fsSL https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js -o /tmp/axe.min.js
```

If the fetch fails, record **NOT PROVEN** with the command and error; G08/G15 fail
their wave. No waiver for a deliverable route (CONTINUATION-STRATEGY §2 G08).

### 9.2 Local server stack (read-only, copied DB)

```bash
cp -a data/parlament-real.db /tmp/opencode/R-09/serve-db.sqlite
PARLAMENT_DB=/tmp/opencode/R-09/serve-db.sqlite \
  .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8101
PARLAMENT_API_PROXY_TARGET=http://127.0.0.1:8101 \
  npm --prefix frontend run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

### 9.3 Gate sequence

```bash
python3 scripts/ui_validate.py http://127.0.0.1:5174 \
  | tee /tmp/opencode/R-09/evidence/<wave>/G08.log
python3 scripts/ui_validate.py http://127.0.0.1:5174 \
  --widths 320,768,1024 --keyboard \
  --screenshot-dir /tmp/opencode/R-09/screenshots/<wave> \
  | tee /tmp/opencode/R-09/evidence/<wave>/G15.log
```

Assertions (all must print):

- `UI VALIDATION PASS: 24 routes, zero JavaScript errors, zero axe violations`
  → **0** navigation errors, **0** `console.error`, **0** `pageerror`, **0** axe
  violations, **0** axe scan errors across all 24 routes.
- `EDGE PROBE PASS: 72/72 checks` (24 routes × 3 widths) → no horizontal overflow
  at 320 px, symmetric gutters 16/24/32 px, no clipped hero ring.
- `KEYBOARD WALK PASS: 24 routes, 0 focus traps, 0 inert affordances` → every
  pointer affordance is a native `button`/`a` or a keyboard-activatable control;
  the global `:focus-visible` ring is visible; no positive `tabindex`; scrollable
  wide tables carry `tabindex=0 role=region aria-label`; dialogs trap Tab, close
  on Escape and restore focus.
- Screenshot manifest written with one PNG per route per width and a sealed
  SHA-256 manifest (§10).

### 9.4 Server cleanup (no side effects)

After the gates, stop only the owned PIDs, then verify ports free:

```bash
ss -ltnp | grep -E ':(8101|5174)\b' || echo "PORTS FREE"
```

Other agents' servers on other ports are left untouched (per GATE-EVIDENCE:239-243).

---

## 10. Visual regression approach (new; NOT PROVEN until first capture)

There is **no screenshot-baseline infrastructure** in the repo today (search of
`frontend/package.json`, `frontend/scripts`, `scripts` finds only `ui_validate.py`).
Introduce a lightweight, honest approach — **evidence + human sign-off, not
auto-accept**:

1. **Capture.** `--screenshot-dir` (§8.3) writes stable-name full-page PNGs for
   all 24 routes at 320/768/1024 for each wave. Deterministic conditions: pinned
   Chromium, `--no-sandbox`, disabled animations via `prefers-reduced-motion`,
   fixed viewport/device-scale, network idle + bounded settle (the existing
   `ui_validate.py:99-103` settle logic).
2. **Seal.** `sha256sum` manifest per wave under
   `/tmp/opencode/R-09/screenshots/<wave>/MANIFEST.sha256`. Checksums are
   corruption evidence, **not** a diff.
3. **Compare.** A helper (`scripts/compare_screenshots.py`, advisory) computes a
   perceptual difference between wave N and N-1 per route/width using Pillow and
   reports `changed`/`unchanged` with a documented tolerance. A change is a
   **review trigger**, not a failure by itself.
4. **Review.** For every changed frame, a human records in the wave `INDEX.md`
   whether the change is intended (e.g. R-01 hero colour, R-02 gutters) or a
   regression. Unintended change → **RED** for that wave.
5. **Baselines.** Approved baselines live outside the repo (gitignored artifacts)
   with their manifest; if the team later wants committed golden images, that is a
   separate owner decision (storage/size), not assumed here.
6. **Theme pass.** Because the audits' key visual claims are theme-dependent,
   capture dark **and** light for at least the routes touched by R-01/R-02
   (HeroGraphic, DataBar, ProgressRing, AgeDistributionRadial, gutters). The
   manual CP10 tables in those recipes are the accept/reject record.

Until step 1 actually runs, every visual claim in R-01/R-02 remains **NOT PROVEN**
(as their own §14/§12 state).

---

## 11. i18n key-diff gate (X4, G13)

- **Problem:** `FRONTEND-AUDIT:42` (X4) and A-13 record dozens of `t(key, "English…")`
  calls with no ro/en entry, raw keys such as `nav.parties`, and a key sweep that
  was RED with 64 missing keys. Widespread English fallbacks breach the
  Romanian-first vision.
- **Gate:** `scripts/check_i18n_keys.py` (§8.1) runs G13 at **every** wave.
  - Waves 1–3: missing count must **not increase** vs the frozen baseline recorded
    at W0 (`--baseline`). A recipe that adds `t()` keys must add the **ro+en pair
    in the same atomic commit** (KEY ADD RULE).
  - Wave 4: the i18n sweep recipe drives the count to 0 (or a dated owner waiver
    naming each residual key).
  - Raw keys and English-only keys are never acceptable in Romanian UI.
- **No false green:** the gate compares **literal** keys only where statically
  resolvable and lists dynamic keys as advisory with the file:line; an unresolved
  dynamic key is **NOT PROVEN**, never PASS.

---

## 12. API contract checks (G14 / G14-live)

- **Offline (every wave from W2):** `generate_openapi.py` → `pipeline/openapi.json`;
  `check_api_contract.py --offline` asserts the documented path set in `docs/API.md`
  matches the running app's schema and that scope params introduced by R-03 are
  documented. This catches the REST/GraphQL and label discrepancies noted in X2/S3
  before they reach the UI.
- **Local live (W2–W4):** `check_api_contract.py --base … --scope` proves each
  scope param is accepted and reflected; a param silently ignored is a **FAIL**
  (the exact defect FN-1/X2).
- **Production (W5, 🔒 owner):** `verify-deploy.sh` with `TARGET_SHA` and
  `EXPECTED_RELEASE`, asserting the SPA, `/api` rewrite, health, pinned release
  and read-only routes. Absent tokens or an unreachable host → **NOT PROVEN**,
  exit 1. The CI `docker` job's `/api/health/ready` + release check and `jq`
  assertion (`ci.yml:82-92`) are the pre-deploy contract proof; `evidence-guards`
  is **not** an axe proof (§1.2).

---

## 13. Vault sync / lint / doc-truth maintenance

After **every** doc or vault edit and before every wave checkpoint:

```bash
python3 scripts/vault_sync.py            # regenerate 5 notes from source commit
python3 scripts/vault_sync.py --check    # G09a: clean, exit 0
python3 scripts/vault_lint.py            # G09b: PASS, exit 0
bash scripts/check-doc-truth.sh          # G05: false-claims: 0, exit 0
git diff --check                         # G10: empty, exit 0
```

Rules:

1. Generated notes are anchored to the **last non-vault source commit**; after a
   product commit the `source_commit` changes, so regenerate in the **same** doc
   commit and re-run `--check`. Never hand-edit `_generated/*.md`.
2. Hand-written vault notes need valid frontmatter, closed-vocabulary tags,
   resolvable relative links and at least one inbound link (no orphans).
3. `check-doc-truth.sh` scans tracked Markdown (excluding `docs/remediation/*`).
   **This recipe lives in `docs/repair-recipes/`, so it IS scanned** — it must not
   contain banned false-claim literals; the gate must stay `false-claims: 0`.
4. One fact, one home: status lives in the hubs; recipes state their own status
   and link, never duplicate another note's live status.
5. A G05/G09/G10 finding is **RED** for the wave; fix the doc/vault in the same
   commit, never waive the gate.

---

## 14. Rollback per wave (non-destructive, additive)

### 14.1 Recipe commit not yet merged (normal case)

```bash
SHA=$(cat /tmp/opencode/R-09-wave-$N/R0N_SHA)
git rev-parse --verify "$SHA"
git revert --no-edit "$SHA"                       # new commit, history preserved
echo "revert_exit=$?"                              # expect 0
git log -3 --format='%h %s'                        # newest = Revert "fix(R-0N)…"
```

Then re-run the wave's gates; recipe static guards must return to their **RED**
pre-fix state (that is proof the revert undid the fix). Verify backup integrity
with `sha256sum -c` on both the wave manifest and the recipe's own manifest.

### 14.2 Failure during implementation (no commit made)

```bash
BASE=$(cat /tmp/opencode/R-09-wave-$N/BASE_SHA)
git restore --source="$BASE" -- <only the recipe's §3 exclusive files>
git status --porcelain | wc -l                     # -> 0 for owned paths
```

Never copy files back from a manifest; manifests verify, git restores.

### 14.3 Whole wave / already-merged on integration branch

Revert each recipe commit in reverse order with `git revert --no-edit <sha>`; if
merged via a merge commit, `git revert -m 1 <merge-sha>`. Keep the additive
pre-wave tag (`repair-wN-before-merge`) as the rollback anchor. **Never** rewrite
shared history, move tags, or force-push.

### 14.4 Dataset / release marker rollback (only if a wave touches data)

New commit restoring the previous `data/latest-release.txt` value from
`$BK/RELEASE_PIN`; never edit or delete an immutable release tag.

### 14.4 Deployed rollback (W5, 🔒 owner)

Platform rollback (Render/Vercel) by the owner, then re-run G14-live to prove the
served release; agents prepare the runbook, do not execute it.

---

## 15. Stop conditions (GREEN / AMBER / RED)

**RED — stop immediately, rollback per §14, do not start the next wave:**

- R-1 Backup bundle verify or `sha256sum -c` fails; restore drill SHA mismatch.
- R-2 Any required gate FAILs or its log is missing (⇒ NOT PROVEN).
- R-3 Baseline identity mismatch: tree hash ≠ `02ac065…`, or product diff
  `eb693b4..HEAD` non-empty at W0.
- R-4 A recipe commit changes a file outside its §3 exclusive list (G16).
- R-5 Strict audit reports any **new** error beyond 275 known / 0 new (G06).
- R-6 i18n missing-key count increases vs baseline (G13).
- R-7 A recipe is missing, has no §3/§10, or an unresolved CO-1..CO-4 collision.
- R-8 Any force-push/reset-hard/tag-delete/`git add -A` attempted.
- R-9 Unintended visual-regression change (§10) or a keyboard/focus regression.
- R-10 A new audit error, fabricated null→0, or an unlabelled headline count.

**AMBER — do not advance; name the blocker and date it (not a pass):**

- Axe absent / browser server unreachable (G08/G15 NOT PROVEN) without a dated
  owner acceptance that visual claims remain unproven.
- Deploy tokens, Vercel/Render access or staging URL unavailable (G14-live).
- 🔒 owner decision pending: merge, branch protection, product policy, waiver of
  named residual i18n keys, AP-7 canvas orphan (CO-2), deploy.
- A required check on a PR is still running; wait for 4/4 result.

**GREEN — advance only when:** every required gate for the wave printed PASS with
exit 0 and archived log, backups verified, diff scope clean, and no `NOT PROVEN`
in a required gate.

**The governing rule (repeat at every checkpoint):** *Evidence over assertion;
`NOT PROVEN` beats a guessed PASS. An unavailable check fails a required gate.
No `|| true`, no `continue-on-error`, no silent skip, no auto-accepted baseline.*
(CONTINUATION-STRATEGY §1.1/§1.5; GATE-EVIDENCE header; both audits §NOT PROVEN.)

---

## 16. Acceptance criteria

1. **AC-1** All eight recipes exist with §3 exclusive files and §10 dependencies;
   CO-1..CO-4 resolved and recorded; wave assignment computed by §3.2.
2. **AC-2** Every wave has an archived backup (bundle + DB + vault + manifest), a
   passing `sha256sum -c`, and a restore drill matching the frozen SHA.
3. **AC-3** Every wave's gate table (§5) is all PASS with printed command, output
   and exit code in `/tmp/opencode/R-09/evidence/<wave>/INDEX.md`.
4. **AC-4** G01–G10, G13, G14, G15 and G16 green at W5 full sweep; G12 shows 4/4
   SUCCESS (`test`, `audit`, `docker`, `evidence-guards`).
5. **AC-5** Browser proof: 24/24 routes rendered; zero JS errors; zero axe
   violations; `EDGE PROBE PASS: 72/72` at 320/768/1024; `KEYBOARD WALK PASS`;
   screenshots + manifest archived and reviewed.
6. **AC-6** i18n `0 missing ro, 0 missing en, 0 raw keys` at W4 (or dated, named
   owner waiver); no wave increases the baseline count.
7. **AC-7** API contract offline + local-scope gates green at W2/W3/W4; G14-live
   green at W5 by the owner (else programme ends AMBER, not shipped).
8. **AC-8** Vault sync/lint/doc-truth clean after every doc change; generated
   notes regenerated in the same commit; no hand-edited generated note.
9. **AC-9** One atomic commit per recipe, sequential wave order, no force-push,
   no history rewrite, no `git add -A`; rollback SHAs recorded.
10. **AC-10** Every item still unrun at hand-off is listed in §19 as NOT PROVEN
    with a named resolver; no claim is upgraded without a printed gate.

---

## 17. Dependencies

**Before R-09 execution:**

- Baseline `eb693b4` (tree `02ac065…`) re-verified; clean product tree.
- All eight recipe documents present and reconciled (§2).
- Tooling available: `.venv` (pytest/ruff), Node/npm locked, system `python3` +
  `playwright`, `/usr/bin/chromium`, `/tmp/axe.min.js`, `sqlite3`, `git`, `gh`,
  `curl`, `jq`; a reachable API for browser gates.
- Backup space under `/tmp/opencode/` (outside the repo, cannot be committed).

**Ordering dependencies:**

- W1 needs CO-1/CO-3 resolved and R-01 landed before R-02 (CSS utility ownership).
- W2 needs W1 GREEN; W3 needs W2's scope hook; W4 needs all key-adding recipes
  landed before the i18n sweep; W5 needs W0–W4 GREEN.
- 🔒 owner actions (merge, protection, deploy, release, policy) gate W5 only.

**No new runtime dependency** is introduced by R-09; `check_i18n_keys.py`,
`check_api_contract.py`, `check_wave_gate.sh` and the browser extensions use
stdlib / already-installed tools (Pillow only for the advisory screenshot diff,
and only if the owner accepts that dependency).

---

## 18. Side-quest policy (REJECT on sight)

R-09 must not:

1. Edit any product file, workflow, script, branch, tag, PR or deployment.
2. Define, expand or "fix" another recipe's exclusive file list or code changes —
   that authority stays with each recipe's §3.
3. Perform 🔒 owner actions: merge to main, enable branch protection, set secrets,
   release, deploy, workflow_dispatch, or decide product policy.
4. Weaken any gate: add `|| true`, `continue-on-error`, silent skips, or relax a
   doc-truth/vault/audit pattern to make a gate green.
5. Start a wave out of order, advance on AMBER, or claim a PASS without an
   archived printed checkpoint.
6. Change the baseline, move tags, delete branches, or rewrite history.
7. Duplicate the sibling recipes' fix content; quote only their §3/§8/§10/§12/§14
   as coordination inputs.
8. "Drive-by" fix a CO-* collision inside product code; record it and stop.

If noticed while executing, record an anomaly in the wave `INDEX.md` and continue
only if it is out of scope and does not affect a gate; otherwise stop (§15).

---

## 19. NOT PROVEN (must be stated, not inferred)

At authoring time the following are **NOT PROVEN** and must not be claimed until a
gate prints evidence:

1. **Browser rendering of any recipe** — no render was performed by this author.
   R-01/R-02/R-03 findings are static-code evidence; their audits say so
   (`TRIAD:19,87-89`; `FRONTEND:22-23,109-114`).
2. **axe / WCAG-AA** — `/tmp/axe.min.js` was absent; G08 cannot run now. Resolver:
   install axe and run §9 with a live server.
3. **320/768/1024 reflow, 72/72 gutters, no horizontal overflow** — no probe run;
   the 16/24/32 px values are arithmetic from `px-4 sm:px-6 lg:px-8`.
4. **Keyboard walk / focus traps / inert affordances** — no tooling and no run;
   G15 is a proposed check only.
5. **Visual regression / dark-light screenshot acceptability** — no baseline, no
   capture, no comparison performed.
6. **i18n key-diff result** — `check_i18n_keys.py` does not exist yet; the prior
   64-missing figure is from A-13 and must be re-measured at W0.
7. **API contract offline/live** — `check_api_contract.py` does not exist yet;
   G14-live needs 🔒 owner tokens and was not run.
8. **The R-04..R-08 scope assignments in §2/§3** — those recipes were still being
   authored; only their own final §3/§10 are authoritative (CO-4).
9. **vault sync / lint / doc-truth for this document as committed** — the scripts
   were read, not executed against the final committed tree; the implementer must
   run G05/G09/G10 and keep them green.
10. **Branch protection state, PR checks, merge and deploy** — no PR, merge,
    protection change or deploy was performed by this author; §5.6 rows are a
    runbook. If they are not executed, the programme ends **AMBER — prepared,
    not shipped**.

Every resolver above is named; none is waived by this document.

---

## 20. Output / evidence log (implementer must return this)

```
ID / ROLE              R-09 — master verification & rollout envelope
BASELINE               eb693b4 (tree 02ac065…); authoring HEAD 80d91a9 (same tree)
RECIPES RECONCILED     <R-01..R-08 file list + CO-1..CO-4 resolutions>
WAVE ASSIGNMENT        <per §3.2 rule, with each recipe's §10 dependency cited>
BACKUP                 /tmp/opencode/R-09-wave-<N>/MANIFEST.sha256 (all OK)
RESTORE DRILL          <restored SHA per wave == BASE_SHA>
GATES                  G00..G16 → command | raw output | exit | PASS/FAIL/NOT PROVEN
EVIDENCE INDEX         /tmp/opencode/R-09/evidence/<wave>/INDEX.md per wave
BROWSER                G08 raw log; G15 edge/keyboard logs; screenshot manifest
i18n                   G13 raw output (missing counts per wave)
API                    G14 offline + --scope logs; G14-live owner result or NOT PROVEN
VAULT/DOCS             G05/G09/G10 raw output after every doc change
COMMITS                <one atomic SHA per recipe, in wave order>
ROLLBACK SHAs          <R0N_SHA files; revert drill result>
SELF-VERDICT           GREEN only if every required gate is PASS with printed
                       evidence; otherwise AMBER (owner/deploy blocked) or RED
NOT PROVEN             list every unrun gate from §19 with its resolver
```

---

## See also

`R-01-design-system.md` · `R-02-layout.md` · `R-03-scope.md` ·
`docs/CONTINUATION-STRATEGY-2026-11-21.md` (§2 gates, §3 backups, §9 GitHub hardening) ·
`docs/GATE-EVIDENCE-2026-11-21.md` · `.github/workflows/ci.yml` ·
`scripts/ui_validate.py` · `scripts/vault_sync.py` · `scripts/vault_lint.py` ·
`scripts/check-doc-truth.sh` ·
`Parlament Deschis Obsidian vault/40-FRONTEND/TRIAD-AUDIT-2026-11-21.md` ·
`Parlament Deschis Obsidian vault/40-FRONTEND/FRONTEND-AUDIT-2026-11-21.md`
