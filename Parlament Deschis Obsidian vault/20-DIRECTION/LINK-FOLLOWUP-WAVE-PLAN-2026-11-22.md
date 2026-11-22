---
id: LINK-FOLLOWUP-WAVE-PLAN
type: runbook
title: "Follow-up wave plan — ranking and recipes for the open §J items (2026-11-22)"
description: "Supervisor ranking of the six open follow-ups, with compact recipe-shaped plans for the four selected evidence waves W8-W10, their gates, verdict conditions and explicit NOT PROVEN resolvers; a planning note, not an execution or a new repair claim."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/frontend]
source_paths: [20-DIRECTION/LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md, 20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md, 20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md, 20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md, 50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Follow-up wave plan — open §J items (2026-11-22)

**This is a planning note.** It ranks the six open follow-ups and specifies
recipes for the selected ones. It does **not** execute them, reopen any GREEN
wave, change a verdict, authorise a merge to `main`, open a PR or deploy. The
lead executes; the supervisor audits. Governing references:
[CONSISTENCY-STEPS](LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md) §2–§5,
[SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §C/§D/§F/§J,
[STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §2/§4/§5/§6/§9,
[RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) (shape and side-quest policy),
[JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) W0–W7 records and
sign-offs. An unrun check is **NOT PROVEN**, never PASS.

## 1. Ranking and ruling

Criteria, in the order applied: (a) **risk if left open**, (b) **ability to
close with evidence the lead can obtain here** (network probe, chrome-devtools,
local gates), (c) **code-change risk**, (d) **owner-gate constraints**. Selected:
**F4, F3, F6, F5** (at most four). Deferred: **F1, F2**.

| Rank | Follow-up (§J ID) | Risk if left open | Closable here? | Code-change risk | Owner gate | Ruling |
|---:|---|---|---|---|---|---|
| 1 | **F4 external URL reachability** (§J 4) | **High honesty exposure.** [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §1 already states an HTTP result as fact, but [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §B reading record calls it a *note claim, not re-run*; [C-06](../40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md) §3 rows E01–E06 and §7 record no network call and reachability NOT PROVEN. A canonical note asserting an unverified reachability fact is the programme's demonstrated false-pass failure mode (R7). | **Yes** — lead runs a dated `curl` status probe; the probe pattern already exists in STRAT §1. | **None** — evidence only. A broken result would need a *new* recipe, not an opportunistic edit. | None — probe is read-only. | **SELECT → W8 / L-19** |
| 2 | **F3 production `/ideology` behaviour** (§J 3) | **High verification gap.** Browser note B4 observed a loading state with zero selects in production; [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) W1 proved the B1 fix only on local dev. The flagship repair's production effect, and which SHA production serves ([investigation](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) §6), remain unverified. Local green is not production green ([AGENTS](../00-START/AGENTS.md) NEVER). | **Mostly** — lead can retry chrome-devtools on the production page; if it still does not load, the attempt is recorded and the item stays NOT PROVEN with a named resolver. | **None** for evidence. | Reading production is fine; no deploy. A production defect would need a new recipe plus an owner decision. | **SELECT → W9 / L-20** |
| 3 | **F6 pytest / audit / Docker evidence in CI** (§J 6) | **Medium verification gap.** W7 :1035-1037 and sign-off :1090 record these required checks as explicitly NOT RUN, with CI as resolver; no pass is claimed. Verification completeness at hand-off is incomplete. | **Partly** — lead can read existing CI runs on the pushed `repair/links-base` branch with the `gh` CLI (derive the repo slug from `git remote -v`, do not guess). If none exist, resolver is an owner-opened PR, so the item remains NOT PROVEN. | **None** — evidence only; no workflow edit. | Opening the PR is an owner gate (W7 :1063-1069); reading CI is not. | **SELECT → W10 / L-21** |
| 4 | **F5 raw console captures for W3/W4/W6** (§J 5) | **Low–medium, evidence discipline only.** W3 sign-off :828 and W4 :890 explicitly note console status was not recorded; W6 :1002 notes the state-probe result had no separate raw file. W1 :564 and W2B :717 did record it. No defect is implied. | **Yes, with an honest limit** — lead attaches fresh captures on current integrated code and labels them as **new observations**, not retroactive wave captures. | **None** — vault evidence only. | None. | **SELECT → W10 / L-22** |
| 5 | **F1 EmptyState CTA chain** (§J 1) | **Low** — a defined-but-unreachable control, "no user-visible break, but a future trap" ([investigation](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) §4.4); W5 L-15 declined it for scope (JOURNEY :910-915). | No — needs a new scoped recipe plus a browser click. | **Highest of the six**: touches `AsyncState.tsx` forwarding and one call site; a wrong edit can break the type gate. | None, but a code change needs supervisor approval via side-quest policy. | **DEFER — NOT PROVEN.** Resolver: an approved scoped recipe with a local-dev click capture. |
| 6 | **F2 AgeDistributionRadial arc plumbing** (§J 2) | **Low** — same dead-control class as F1; W5 declined it (JOURNEY :911-914). | No — needs a new scoped recipe plus a keyboard pass. | **High**: wire-vs-remove is a real design decision requiring the L-12 NO-CHANGE procedure. | None beyond recipe approval. | **DEFER — NOT PROVEN.** Resolver: an approved scoped recipe with a keyboard/browser pass. |

**Decisive conclusion:** the four items closable by the lead with read-only
probes and evidence write-backs are selected; the two code-changing dead-control
items are deferred because their risk-if-left-open is low while their
code-change risk is the highest of the six. No selected recipe edits product
code, data, config, workflows or deployments.

## 2. Wave and branch naming

| Wave | Branch (from `repair/links-base`) | Recipe | Item | Files owned |
|---|---|---|---|---|
| W8 | `repair/links-w8` | L-19 | F4 external URL reachability | vault evidence only (new note under `60-EVIDENCE/`, W8 section in [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md)) |
| W9 | `repair/links-w9` | L-20 | F3 production `/ideology` | vault evidence only (new note under `60-EVIDENCE/`, W9 section in JOURNEY) |
| W10 | `repair/links-w10` | L-21 then L-22 (one vault-writer agent, two atomic commits) | F6 CI evidence, then F5 console captures | vault evidence only (two new notes under `60-EVIDENCE/`, shared W10 section in JOURNEY) |

W10 merges L-21 and L-22 into one wave because both write the same JOURNEY
section; the L-04+L-05 precedent (one agent, two atomic commits, one shared
gate) applies — each commit message carries its own recipe ID, evidence anchor,
gate output and rollback SHA. Waves are serialised; W9 starts only after W8 is
GREEN, W10 only after W9 is GREEN.

## 3. Recipe L-19 — external URL reachability (wave W8)

- **Objective.** Replace the unverified reachability note claim with a dated,
  recorded HTTP probe for the external URL literals, without changing any code.
- **Evidence anchor.** [C-06](../40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md) §3 rows E01–E03 and §7; [investigation](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) §6; [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §1 note claim; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §J follow-up 4.
- **Exclusive files.** New `60-EVIDENCE/LINK-URL-REACHABILITY-2026-11-22.md` and the W8 section of [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md). `frontend/src/config/links.ts` and all product code are **out of scope**.
- **Steps (exact commands from repo root `/home/nedaktov/parlament-deschis`).**
  1. Re-read the anchor: `cd /home/nedaktov/parlament-deschis && grep -n "E01\|E02\|E03\|NOT PROVEN" "Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md"`
  2. Create and verify the W8 backup with fully expanded paths per [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §5 at `/tmp/opencode/backups/link-repair/W8` (`git bundle verify`, `tar -tzf`, `sha256sum -c` all exit 0); commit the verbatim outputs in the W8 vault section **before** the probe.
  3. Probe each literal with a date stamp and save the raw capture:
     ```bash
     date -u +%Y-%m-%dT%H:%M:%SZ | tee /tmp/opencode/w8-url-probe.txt
     for URL in \
       https://github.com/nedaktov-ops/parlament-deschis \
       https://github.com/parlament-deschis \
       https://github.com/nedaktov-ops/parlament-deschis/blob/main/docs/METHODOLOGY.md \
       https://www.wikidata.org/wiki/Q42 \
       https://www.gnu.org/licenses/agpl-3.0.html \
       https://creativecommons.org/licenses/by/4.0/ ; do
       curl -L -o /dev/null -s -w "%{http_code} %{url_effective} $URL\n" "$URL" | tee -a /tmp/opencode/w8-url-probe.txt
     done
     ```
     The Wikidata line uses a sample QID only to test host reachability and must be labelled as such in the note; no API-payload claim is made.
  4. Write the evidence note: one row per URL with HTTP status, effective URL, probe timestamp and raw capture path; state that a result is a **dated snapshot** and that any broken result becomes a new recipe after supervisor approval, never an opportunistic edit. Explicitly record whether the STRAT §1 claim is corroborated or corrected, with a citation.
  5. Vault write-back with titled **Code evidence** (probe commands, output, limits) and **Browser evidence** ("N/A — network probe, not a browser action" is an acceptable statement). Run the four vault gates.
- **Checkpoint.** `cd /home/nedaktov/parlament-deschis && python3 scripts/vault_lint.py && python3 scripts/vault_sync.py --check && bash scripts/check-doc-truth.sh && git diff --check` → all exit 0; `cat /tmp/opencode/w8-url-probe.txt` shows every probed URL with a status.
- **Rollback.** `git revert <W8-checkpoint-sha>`; bundle at `/tmp/opencode/backups/link-repair/W8/pre.bundle`. No reset, force-push or tag move.
- **Acceptance.** Every probed literal has a recorded status and timestamp; the STRAT §1 claim is corroborated or corrected with a citation; no product code changed; four vault gates exit 0.
- **Side-quest policy.** No edit to `config/links.ts`, sources, data, release pin, workflows, branch protection or deployment; no browser/network fact claimed without the raw capture; a broken URL is a new recipe, not a fix in this wave.

## 4. Recipe L-20 — production `/ideology` behaviour (wave W9)

- **Objective.** Obtain a loaded production ideology response, or record an honest NOT PROVEN with a named resolver. No code change is authorised.
- **Evidence anchor.** [browser observations](../60-EVIDENCE/CLICK-BROWSER-OBSERVATIONS-2026-11-22.md) B4 (loading state, zero selects); [investigation](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) §6; [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) W1 :547-564 (local-dev success only); [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §J follow-up 3.
- **Exclusive files.** New `60-EVIDENCE/PROD-IDEOLOGY-2026-11-22.md` and the W9 section of [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md). No product code, no production config.
- **Steps (exact commands).**
  1. Re-read the anchor: `cd /home/nedaktov/parlament-deschis && grep -n "ideology\|NOT PROVEN\|resolver" "Parlament Deschis Obsidian vault/60-EVIDENCE/CLICK-BROWSER-OBSERVATIONS-2026-11-22.md"`
  2. Create and verify the W9 backup per §5 at `/tmp/opencode/backups/link-repair/W9` before any evidence write; commit the outputs in the W9 vault section.
  3. Lead (browser tool, not the supervisor) locates the production page via chrome-devtools `list_pages`, navigates to the production `/ideology?date=2026-11-22`, waits for a loaded response, and records the year `<select>` count/options, visible rows and `list_console_messages` into `/tmp/opencode/w9-prod-ideology.json`. Use the production host already recorded in the vault evidence, never a guessed URL.
  4. If loaded and the year control is present, mark the item PASS with the raw capture. If it still shows a loading state or zero selects, mark **NOT PROVEN** with resolver "a loaded production ideology response plus deployment metadata identifying the served SHA"; do **not** mark PASS, do not open a defect, do not edit code.
  5. Vault write-back with **Code evidence** (anchor re-read, backup, gates) and **Browser evidence** (production scope, raw capture path, result or NOT PROVEN limit). Run the four vault gates.
- **Checkpoint.** Four vault gates exit 0; raw capture file exists and is cited; the evidence note states PASS **or** NOT PROVEN with the named resolver.
- **Rollback.** `git revert <W9-checkpoint-sha>`; bundle at `/tmp/opencode/backups/link-repair/W9/pre.bundle`.
- **Acceptance.** A loaded production response with the year control, or an explicit NOT PROVEN with resolver; local dev not substituted; no product code changed; four gates exit 0.
- **Side-quest policy.** No code, deploy, release-pin or production-config change; no axe or console claim beyond the capture; a production defect needs a new recipe plus an owner decision.

## 5. Recipe L-21 — CI evidence for pytest / audit / Docker (wave W10, commit 1 of 2)

- **Objective.** Record the outcome of the required CI checks, or mark the item NOT PROVEN with the CI/owner resolver. No local pass is claimed.
- **Evidence anchor.** [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) W7 :1035-1037 and sign-off :1090; [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §1 and §9 (required checks: test, audit, docker, evidence-guards); [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §J follow-up 6.
- **Exclusive files.** New `60-EVIDENCE/CI-REQUIRED-CHECKS-2026-11-22.md` and the W10 section of [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md). **No CI workflow edit.**
- **Steps (exact commands).**
  1. Re-read the anchor: `cd /home/nedaktov/parlament-deschis && grep -n "pytest\|audit\|docker\|resolver" "Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md"`
  2. Create and verify the shared W10 backup per §5 at `/tmp/opencode/backups/link-repair/W10` before the first evidence write; commit the outputs in the W10 vault section.
  3. Derive the repo slug from the recorded remote, do not guess it:
     ```bash
     cd /home/nedaktov/parlament-deschis && git remote -v
     gh run list --repo <slug-from-remote> --branch repair/links-base --limit 20
     gh run view <run-id> --repo <slug-from-remote>
     ```
     Save the job conclusions for the required checks into `/tmp/opencode/w10-ci-checks.txt`.
  4. If runs exist, record each required check's conclusion with run ID and URL. If none exist or a check is absent, mark **NOT PROVEN** with resolver "owner opens a PR from `repair/links-base` → required CI checks run" (W7 :1036). Never convert a local frontend gate into a CI pass.
  5. Commit 1 of 2 with this recipe's ID, anchor, gate output and rollback SHA; run the four vault gates.
- **Checkpoint.** Four vault gates exit 0; evidence note gives each check a conclusion with run ID, or an explicit NOT PROVEN with the named resolver.
- **Rollback.** `git revert <L-21-checkpoint-sha>`; bundle at `/tmp/opencode/backups/link-repair/W10/pre.bundle`.
- **Acceptance.** No workflow edited, no PR opened, no local pass claimed; every check evidenced with a run ID or honestly NOT PROVEN; four gates exit 0.
- **Side-quest policy.** No CI workflow/Dockerfile/render/Vercel edit, no PR merge, no push to `main`, no deploy.

## 6. Recipe L-22 — raw console captures for W3/W4/W6 (wave W10, commit 2 of 2)

- **Objective.** Close the "no dedicated raw console capture" documentation gap for W3/W4/W6 without retroactively changing any GREEN wave record.
- **Evidence anchor.** [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §J follow-up 5; [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) W3 sign-off :828, W4 :890, W6 :1002, contrasted with W1 :564 and W2B :717.
- **Exclusive files.** New `60-EVIDENCE/CONSOLE-CAPTURES-2026-11-22.md` and the shared W10 section of [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md). No product code.
- **Steps (exact commands).**
  1. Re-read the anchor: `cd /home/nedaktov/parlament-deschis && grep -n "list_console_messages" "Parlament Deschis Obsidian vault/50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md"`
  2. The W10 backup from L-21 is reused; do not create a second manifest in the same wave.
  3. Lead runs chrome-devtools on local dev serving current integrated `repair/links-base` code and attaches three raw `list_console_messages` artifacts for the W3/W4/W6-relevant pages (e.g. `/Voturi`, `/topuri`, and the retry-state probe route): `/tmp/opencode/w10-console-w3.json`, `/tmp/opencode/w10-console-w4.json`, `/tmp/opencode/w10-console-w6.json`.
  4. Write the evidence note stating explicitly that these are **new observations on integrated HEAD**, not the original wave captures, and that no GREEN wave's record is altered. If a browser run is unavailable, mark **NOT PROVEN** with resolver "browser pass on local dev with a raw capture artifact".
  5. Commit 2 of 2; run the four vault gates.
- **Checkpoint.** Four vault gates exit 0; all three raw files exist and are cited; the new-observation limitation is stated in the note.
- **Rollback.** `git revert <L-22-checkpoint-sha>`; if both W10 commits must be undone, revert L-22 then L-21 in reverse order.
- **Acceptance.** Three referenced raw captures (or honest NOT PROVEN with resolver); no GREEN wave record changed; four gates exit 0.
- **Side-quest policy.** No product code, no axe/network claim, no claim that a fresh capture is original wave evidence.

## 7. Gates for W8–W10

Backups: each wave creates and verifies a bundle, `pre.sha`, `pre.status`,
worktree archive and `SHA256SUMS` under `/tmp/opencode/backups/link-repair/<WAVE>`
with fully expanded absolute paths before its first evidence write
([STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §5).

Applicable gates (no product code changes in these waves, so no frontend
lint/build/i18n/routes gate is required; if the lead runs one anyway, record it,
and an unrun frontend gate is NOT PROVEN rather than a wave failure — the W5
precedent at JOURNEY :921-923 applies):

```bash
cd /home/nedaktov/parlament-deschis
python3 scripts/vault_lint.py
python3 scripts/vault_sync.py --check
bash scripts/check-doc-truth.sh
git diff --check
```

Each wave also has its item-specific evidence gate: W8 the curl raw capture,
W9 the production raw capture (or explicit NOT PROVEN), W10 the CI conclusions
(or explicit NOT PROVEN) and the three console raw captures (or explicit NOT
PROVEN). `_generated/*` is regenerated with `python3 scripts/vault_sync.py`,
never hand-edited.

## 8. Supervisor verdict conditions

Applied per wave with citations, using [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §C/§D/§F.

- **GREEN** requires all of: backup verified before the first evidence write;
  diff ⊆ the stated vault-evidence file list; every applicable gate actually
  ran with working directory, command, exit code and output excerpt; raw probe
  or capture artifacts exist and are cited; every acceptance item is PASS or an
  explicitly NOT PROVEN item with a named resolver under §C A2/A5 (the W3
  precedent: three AMBER items, wave still GREEN); a completed §F sign-off with
  citations; no product code, data, config, workflow or deployment change. Only
  the exact §F GREEN sentence authorises integration, and integration is
  `--ff-only` into `repair/links-base` **only**.
- **AMBER / HOLD** when a resolver-dependent item cannot be obtained here (no
  CI runs, production still loading, browser unavailable): mark only that item
  AMBER/NOT PROVEN, name the resolver, and do not merge that wave until the
  supervisor and owner both approve.
- **RED / STOP** when any product-code or out-of-list file changes, a browser,
  network or CI fact is claimed without a recorded artifact, a NOT PROVEN item
  is promoted to PASS or to a defect, a banned literal appears in the vault, a
  gate is unrun or claimed green with a command that cannot run as recorded
  (A1/R4), or any push to `main`, PR merge or deploy occurs (R6/§9).

## 9. Explicitly NOT PROVEN items and resolvers

| Item | Status | Resolver |
|---|---|---|
| F1 EmptyState CTA chain | **NOT PROVEN — deferred, not scheduled in W8–W10** | An approved scoped recipe plus a local-dev click capture ([CONSISTENCY-STEPS](LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md) §5 F1) |
| F2 AgeDistributionRadial arc plumbing | **NOT PROVEN — deferred, not scheduled in W8–W10** | An approved scoped recipe plus a keyboard/browser pass, using the L-12 wire-vs-remove decision procedure (§5 F2) |
| F4 URL reachability | **NOT PROVEN until the dated probe runs** | The `curl` probe in L-19 step 3 |
| F3 production `/ideology` | **NOT PROVEN until a loaded production response is captured** | A loaded production response plus deployment metadata (L-20 step 4) |
| F6 CI required checks | **NOT PROVEN until a CI run is recorded** | Existing CI runs on `repair/links-base`, else an owner-opened PR (L-21 step 4) |
| F5 console raw captures | **NOT PROVEN until the raw artifacts exist** | A local-dev browser pass attaching three `list_console_messages` files (L-22 step 3) |

No item above is a remediation of any GREEN wave; none reopens W0–W7.

## 10. Owner gates (explicitly outside this plan)

**No merge to `main`, no pull-request merge, no deployment and no
branch-protection change is included or authorised here.** After a GREEN
verdict the lead may integrate the wave into the integration branch only:
`cd /home/nedaktov/parlament-deschis && git checkout repair/links-base && git merge --ff-only repair/links-w8` (substitute `w9`/`w10`). Pushing a GREEN
`repair/links-*` branch is permitted by [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §9; pushing `main`, opening a PR or deploying remains an owner decision recorded in the vault (JOURNEY W7 :1063-1069).

## See also

[CONSISTENCY-STEPS](LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md) ·
[SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) ·
[STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) ·
[RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) ·
[JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) ·
[CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md)
