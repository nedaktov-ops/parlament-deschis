---
id: LINK-REPAIR-CONSISTENCY-STEPS
type: runbook
title: "Actionable steps for staying faithful to the repair recommendations (2026-11-22)"
description: "Actionable steps, a reviewer checklist and six scoped mini-recipes for keeping any post-programme follow-up faithful in form and evidence standard to the 2026-11-22 link-repair recommendations; a procedure note, not a repair claim or a new verdict."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/frontend]
source_paths: [20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md, 20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md, 20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md, 40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Actionable steps for staying faithful to the repair recommendations (2026-11-22)

## 1. Purpose and scope

This note converts the already-canonical repair recommendations into executable
steps. It exists so that any **further repair or follow-up work** stays
**similar to** — that is, faithful in **form** (recipe shape, ownership,
checkpoints, rollback, sign-off) and in **evidence standard** (recorded commands,
exit codes, separated browser/code evidence, honest NOT PROVEN) — the programme
that produced all eight GREEN waves.

It is a **procedure note, not a new repair claim**. It does not reopen any wave,
change a verdict, authorise a merge, push, deployment or data edit, and it does
not convert any open follow-up into a defect. The reference standard remains the
source notes, not this summary:

- [CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) §3–§6 and §7 (repair hand-off order).
- [LINK-REPAIR-STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §2 principles, §4.1 ownership register, §5 backup/rollback, §6 gates, §9 GitHub policy.
- [LINK-REPAIR-RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) (recipe shape and shared side-quest policy).
- [LINK-REPAIR-SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §B (S-01…S-16), §C RED/AMBER/GREEN, §D checklist, §E rubric, §F sign-off, §I escalation, §J open follow-ups.
- [LINK-REPAIR-JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) (wave records and sign-offs).

Where this note and a source note disagree, the **source note wins** and the
restrictive reading applies: an unlisted file is outside scope, an unrunnable
check is NOT PROVEN, and a two-owner file is RED
([SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §A.4). Every command below
is run from the repository root `/home/nedaktov/parlament-deschis` unless a
`cd` is shown; frontend commands use the absolute frontend working directory
per the corrected convention ([RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) global
convention, supervisor S-07).

## 2. Recommendation → actionable step mapping table

| # | Prior recommendation (exact note + section/ID) | Concrete step it implies | Artifact produced | Command / gate that proves it | Stop condition |
|---:|---|---|---|---|---|
| 1 | [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §2.1 evidence-only scope + §3; [RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) "Shared side-quest policy"; [CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) §3–§5 | Change only defects already evidenced in the investigation; no data, release pin, workflow, branch protection, dependency or deployment edit | Plan whose every change cites an evidence anchor | `git diff --name-only` ⊆ enumerated exclusive list; `bash scripts/check-doc-truth.sh` exit 0 | RED if any out-of-list path changes or a new recipe is invented without supervisor approval (R6) |
| 2 | [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §2.2 and §4.1 (S-01, S-05 resolved) | Assign each file to exactly one recipe and one agent per wave; if two recipes need one file, one agent emits two atomic commits | File-ownership row per wave in the wave note | `git diff --name-only` hunks map to one named owner; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §D item 3 | RED if two agents or recipes leave hunks in the same file in one wave (R5) |
| 3 | [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §4.1 i18n register (S-02); [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §H.1 S-02 | Name exactly one sole `frontend/src/i18n.ts` owner per wave with an explicit key list; every other recipe declares it read-only | Key-owner row (wave → recipe → keys) | `cd /home/nedaktov/parlament-deschis/frontend && npm run i18n:check` exit 0 and keys match the register | RED if an `i18n.ts` hunk comes from a non-owner recipe or a wave that owns no keys (R1) |
| 4 | [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §5; [RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) L-00 step 3; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §C G2, §D item 2, R3, S-14 | Create and verify bundle + `pre.sha` + `pre.status` + worktree archive + `SHA256SUMS` **before** the first edit | Backup ROOT and verbatim three verification outputs committed in the vault wave note | `git bundle verify`, `tar -tzf`, `sha256sum -c` all exit 0 | RED if the manifest is missing, unverified, has ellipses, or its output is not committed before the edit (R3) |
| 5 | [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §2.5; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §C G8, §D item 4, N-1 | One logical change per commit; message states recipe ID, evidence anchor, gate output and rollback SHA | Checkpoint SHA plus message fields in the wave note | `git log --oneline` for the wave; all four message fields present | AMBER if metadata missing; RED if concerns are mixed in one commit |
| 6 | [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §2.3 and §5; [RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) L-00 rollback; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) S-09 | Roll back with `git revert <checkpoint-sha>` only; no reset, force-push or tag move; delete a just-made branch with `-d` first | Additive rollback command matching the recorded checkpoint SHA | `git log --oneline` shows only additive commits; `git bundle verify …/pre.bundle` exit 0 | RED if rollback is destructive or the bundle was never verified (R3 / S-09) |
| 7 | [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §6 and §10; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §D item 6 (G7); [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) W0 gate results | Run the four vault gates from repo root and record exit code and output excerpt | Gate table in the vault note | `python3 scripts/vault_lint.py`; `python3 scripts/vault_sync.py --check`; `bash scripts/check-doc-truth.sh`; `git diff --check` | RED if any gate exits non-zero or was not actually run (R4 / A1) |
| 8 | [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §6: browser spot-check rules; [RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) global convention (S-12); [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §C G6, A2, §D item 7 | Write two explicitly titled subsections, **Code evidence** and **Browser evidence**, each with scope, raw capture path, result and limits | Those two subsections in every wave/follow-up note | Both headings present; raw capture paths named; unavailable browser item marked AMBER/NOT PROVEN with a resolver | AMBER for that acceptance item if the browser check cannot run; RED if a browser fact is claimed without an observation (R7) |
| 9 | [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §2.8; [RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) L-12 decision procedure; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §D item 8 | If inspection shows the item is already correct or a fix would trade one defect for another, record a NO-CHANGE decision with code citations | NO-CHANGE block with `file:line` citations | Acceptance table row pointing to the inspection that justified it | RED if a change is invented where inspection showed none; AMBER if the decision is uncited |
| 10 | [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §7 and §4 integration rule; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §C G1–G8, §F, §A | Supply audit items 1–9 and explicitly request a verdict; integrate only on the exact GREEN sentence | Completed §F sign-off block in the journey note | §F authorisation sentence present verbatim with all citations filled | No merge if verdict is AMBER/RED or the authorisation sentence is absent |
| 11 | [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §9; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §A.2 and §F; [RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) L-17 step 3 | Push only GREEN `repair/links-*` branches; never push `main`, open a merge PR, deploy or change protection | Owner decision note (explicitly not taken) | `git branch --show-current` = `repair/…`; no `main` push or deploy recorded | RED if `main` is touched or a deploy happens; push/PR/deploy always remain owner gates |
| 12 | [RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) L-00 step 1; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) S-08 | Enumerate the working tree by exact path at run time and decide the disposition of any modified tracked file | Exact-path list in the wave note | `git status --short` reproduced path by path; no count test | RED if a count replaces the list or any path is unexplained |
| 13 | [RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) L-00 step 3 and checkpoint; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) S-14 | Expand every path to an absolute path in recorded commands; no ellipses | Command block with `/home/nedaktov/…` and `/tmp/opencode/…` paths | Re-run the recorded command verbatim; exit 0 | AMBER/NOT PROVEN if a recorded command contains an ellipsis or cannot run as written (A1) |
| 14 | [MAINTENANCE-PROTOCOL](../00-START/MAINTENANCE-PROTOCOL.md) §6; [AGENTS](../00-START/AGENTS.md) NEVER; `scripts/vault_lint.py` banned-list check; `scripts/check-doc-truth.sh` | Describe banned strings only by category; never paste them into a note | Note prose using categories, never the literals | `python3 scripts/vault_lint.py` exit 0; `bash scripts/check-doc-truth.sh` prints zero false-claims | RED if any banned literal appears (gate exits non-zero) |
| 15 | [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §10; [AGENTS](../00-START/AGENTS.md) NEVER; [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) W1 regeneration note | Regenerate `_generated/*` with the sync script; never hand-edit those files | Regenerated files plus a clean drift check | `python3 scripts/vault_sync.py --check` exit 0 | RED if a generated file was hand-edited (drift, or the edit is overwritten on regeneration) |

## 3. Numbered actionable steps S1…S14

Each step is executable by a future agent without guessing. "Failure" means the
stated expected output is not observed.

### S1 — Re-verify entry identity

- **Objective:** prove which branch/HEAD the follow-up starts from.
- **Command:** `cd /home/nedaktov/parlament-deschis && git branch --show-current && git rev-parse HEAD && git rev-parse origin/main && git status --short`
- **Expected:** branch is a `repair/…` branch (or `main` only for a vault-only note like this one); HEAD and `origin/main` are printed as full SHAs; `git status --short` is enumerated, not counted. Exit 0.
- **On failure:** stop; record RED if the branch or HEAD does not match the wave plan, or if unexplained product-code changes are present at entry (R9). Do not edit anything.

### S2 — Re-read the governing sections

- **Objective:** ground the follow-up in the source notes, not in this summary.
- **Command:** `cd /home/nedaktov/parlament-deschis && grep -n "^## " "Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md" "Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md" "Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md" "Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md"`
- **Expected:** exit 0 and a list of section headings; then read §2/§4.1/§5/§6/§9 of [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md), the single recipe that matches the follow-up in [RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md), and §C/§D/§F of [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) in full.
- **On failure:** if a source note is missing or unreadable, stop and report NOT PROVEN with the missing artifact named; do not proceed from memory.

### S3 — Enumerate scope by exact path

- **Objective:** make scope objectively decidable (S-06/S-08).
- **Command/file edit:** write a scope block in the new wave/follow-up note listing every in-scope path as a full repo-relative path; paste the verbatim `git status --short` output beside it.
- **Expected:** no placeholders, no "affected components", no count; the modified tracked file (if any) has an explicit disposition.
- **On failure:** if any path is vague or any working-tree path is unexplained, stop and RED (S-06/S-08).

### S4 — Write the recipe-shaped plan before editing

- **Objective:** preserve the recipe form exactly.
- **File edit:** create a plan containing, as separate labelled fields: **Objective**, **Evidence anchor**, **Exclusive files**, **Steps**, **Checkpoint**, **Rollback**, **Acceptance**, **Side-quest policy**. Use the shape of [RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) L-01…L-17.
- **Expected:** all eight fields present and non-empty; the evidence anchor cites a `note §` or `file:line`, not an assertion.
- **On failure:** an empty or guessed field makes the plan AMBER; fill it from source before any edit.

### S5 — Assign ownership

- **Objective:** satisfy one owner per file and the sole-i18n-owner rule (§2, §4.1).
- **File edit:** add an ownership row: wave ID → exclusive file list → single agent → sole `i18n.ts` owner (or "none / read-only") → keys that owner may add.
- **Expected:** each file appears once; where two recipes need one file, the row says "one agent, two atomic commits" with each commit's recipe ID.
- **On failure:** any two-owner collision is RED (R1/R5); re-plan before editing.

### S6 — Verify the backup before the first edit

- **Objective:** make rollback possible before any product change (G2/R3).
- **Command:** create a wave ROOT under `/tmp/opencode/backups/link-repair/` and run, with fully expanded absolute paths (no ellipses):

  ```bash
  mkdir -p /tmp/opencode/backups/link-repair/<WAVE_ID>
  git bundle create /tmp/opencode/backups/link-repair/<WAVE_ID>/pre.bundle --all
  git rev-parse HEAD > /tmp/opencode/backups/link-repair/<WAVE_ID>/pre.sha
  git status --porcelain > /tmp/opencode/backups/link-repair/<WAVE_ID>/pre.status
  tar -czf /tmp/opencode/backups/link-repair/<WAVE_ID>/worktree.tgz -C /home/nedaktov/parlament-deschis --exclude=.git --exclude=node_modules --exclude=.venv --exclude=.next --exclude=dist .
  (cd /tmp/opencode/backups/link-repair/<WAVE_ID> && sha256sum pre.bundle pre.sha pre.status worktree.tgz > SHA256SUMS)
  git bundle verify /tmp/opencode/backups/link-repair/<WAVE_ID>/pre.bundle
  tar -tzf /tmp/opencode/backups/link-repair/<WAVE_ID>/worktree.tgz >/dev/null
  (cd /tmp/opencode/backups/link-repair/<WAVE_ID> && sha256sum -c SHA256SUMS)
  ```

- **Expected:** all three verification commands exit 0; commit the verbatim outputs in the vault wave note **before** the first edit.
- **On failure:** RED; do not edit product code; do not delete a branch whose bundle failed to verify (S-09).

### S7 — Apply only the listed edits, or record NO-CHANGE

- **Objective:** minimal, evidence-driven diff (§2.1, §2.8).
- **File edit:** change only files in the exclusive list, following the numbered steps of the chosen recipe; if inspection shows the item already correct or the fix would trade one defect for another, write a NO-CHANGE block with `file:line` citations and make no edit (L-12 is the prescribed model).
- **Expected:** `git diff --name-only` is a non-empty subset of the exclusive list, or empty for a recorded NO-CHANGE.
- **On failure:** any out-of-list hunk or invented change → RED, revert the hunk (additively) and re-plan.

### S8 — Run the wave gates from the correct working directory

- **Objective:** satisfy G4 without the broken path of S-07.
- **Command:** `cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build && npm run i18n:check` then `cd /home/nedaktov/parlament-deschis && node scripts/check_i18n_keys.mjs && node scripts/check_routes_nav.mjs`
- **Expected:** every command exit 0; record working directory, exact command, exit code and an output excerpt for each.
- **On failure:** a non-zero exit is RED (R4); an unrun or wrong-directory command is AMBER/NOT PROVEN (A1), never PASS.

### S9 — Run the four vault gates

- **Objective:** satisfy G7 and complete the vault write-back.
- **Command:** `cd /home/nedaktov/parlament-deschis && python3 scripts/vault_lint.py && python3 scripts/vault_sync.py --check && bash scripts/check-doc-truth.sh && git diff --check`
- **Expected:** exit 0 for each; output excerpts recorded (lint PASS line, sync `--check` clean line, doc-truth zero false-claims line, empty `git diff --check` output).
- **On failure:** stop and fix the note; regenerate rather than hand-edit `_generated/*`; an unrun check is NOT PROVEN.

### S10 — Separate Code evidence from Browser evidence

- **Objective:** satisfy S-12 / G6 / §D item 7.
- **File edit:** add two titled subsections **Code evidence** and **Browser evidence**; each states scope, raw capture path where applicable, observed result and limits. If no browser action applies, say so explicitly; if a browser check could not run, mark only that acceptance item AMBER/NOT PROVEN with a named resolver.
- **Expected:** both headings exist; no browser prose is used as the sole basis for a code defect; no console/network fact is claimed without an observation.
- **On failure:** missing headings → AMBER (evidence discipline); a claimed-but-unobserved browser fact → RED (R7).

### S11 — Commit atomically with rollback metadata

- **Objective:** satisfy §2.5 / G8.
- **Command:** `cd /home/nedaktov/parlament-deschis && git add -- <explicit file paths> && git commit -m "<recipe ID>: <what> — evidence <anchor>; gate <exit summary>; rollback <sha>"` and record the SHA plus the additive rollback command `git revert <checkpoint-sha>` in the note.
- **Expected:** one logical change per commit; message contains recipe ID, evidence anchor, gate output and rollback SHA; `git log --oneline` shows additive commits only.
- **On failure:** mixed concerns or missing metadata → AMBER; destructive rollback commands → RED.

### S12 — Request the supervisor verdict before integrating

- **Objective:** satisfy §7 / §F / the §4 integration rule.
- **File edit/command:** append a §F sign-off block with items 1–9 filled and citations, then ask explicitly for GREEN / AMBER / RED. Re-run the four vault gates after adding it.
- **Expected:** a verdict with citations; GREEN integration is authorised **only** by the exact §F sentence.
- **On failure:** AMBER → HOLD with named remediation; RED → STOP, revert the wave's checkpoints additively, never merge.

### S13 — Keep push and deploy behind the owner gate

- **Objective:** satisfy §9 / §A.2.
- **Command (only after GREEN):** `cd /home/nedaktov/parlament-deschis && git checkout repair/links-base && git merge --ff-only repair/links-<wave>` and push only the GREEN `repair/links-*` branch. Never push `main`, open a merge PR, deploy, or change protection.
- **Expected:** `git log --oneline` shows only additive commits; `main` and `origin/main` unchanged; an owner decision note records that PR/merge/deploy was not taken.
- **On failure:** any `main` push, merge PR or deploy is RED and outside this note's authority; stop and escalate to the owner.

### S14 — Final banned-string and regeneration self-check

- **Objective:** satisfy row 14 and row 15 of the mapping table.
- **Command:** `cd /home/nedaktov/parlament-deschis && python3 scripts/vault_lint.py && python3 scripts/vault_sync.py --check && bash scripts/check-doc-truth.sh && git diff --check`
- **Expected:** all exit 0; no banned literal in the note (describe categories only, per [MAINTENANCE-PROTOCOL](../00-START/MAINTENANCE-PROTOCOL.md) §6); no hand-edited generated file.
- **On failure:** a banned-string or drift finding is RED; remove the literal or regenerate with `python3 scripts/vault_sync.py` and re-run until all four gates are green.

## 4. Similarity / consistency checklist (reviewer fill-in)

Answer YES/NO for each item against the proposed follow-up. Any NO in items 1–4
or 9–12 is disqualifying (RED/AMBER per [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §E);
a NO elsewhere needs a recorded remediation before a GREEN verdict.

| # | Consistency item | Y/N | Evidence pointer |
|---:|---|:---:|---|
| 1 | A recipe-shaped plan exists with all eight fields: Objective, Evidence anchor, Exclusive files, Steps, Checkpoint, Rollback, Acceptance, Side-quest policy. | ☐ | |
| 2 | Every change cites an evidence anchor in the investigation (master §3–§5 or a C-0x `file:line`); no opportunistic refactor. | ☐ | |
| 3 | Diff is a non-empty subset of an enumerated exclusive file list (or empty with a cited NO-CHANGE); no placeholders. | ☐ | |
| 4 | One owner per file per wave; `frontend/src/i18n.ts` has exactly one named owner per wave with an explicit key list, or is read-only. | ☐ | |
| 5 | Backup manifest (bundle, `pre.sha`, `pre.status`, worktree archive, `SHA256SUMS`) verified **before** the first edit and output committed in the vault note. | ☐ | |
| 6 | Recorded commands use fully expanded absolute paths, no ellipses, correct working directory; frontend `npm` commands run from `/home/nedaktov/parlament-deschis/frontend`. | ☐ | |
| 7 | Checkpoint commit message states recipe ID, evidence anchor, gate output and rollback SHA; one logical change per commit. | ☐ | |
| 8 | Rollback is additive (`git revert`), matches the recorded SHA, and the bundle was verified first; no reset/force-push. | ☐ | |
| 9 | The four vault gates were actually run with exit codes and output excerpts: `vault_lint.py`, `vault_sync.py --check`, `check-doc-truth.sh`, `git diff --check`. | ☐ | |
| 10 | Wave/follow-up note has separate titled **Code evidence** and **Browser evidence** subsections with scope, raw capture paths and limits. | ☐ | |
| 11 | Unavailable or unverifiable checks are marked AMBER/NOT PROVEN with a named resolver — never PASS; no browser/network/axe fact claimed without observation. | ☐ | |
| 12 | Supervisor verdict with citations exists; integration only on the exact §F GREEN sentence; no push to `main`, PR merge or deploy. | ☐ | |
| 13 | `_generated/*` was regenerated with `vault_sync.py`, never hand-edited; relative Markdown links only; frontmatter complete and valid. | ☐ | |
| 14 | No banned literal string appears — categories only, per [MAINTENANCE-PROTOCOL](../00-START/MAINTENANCE-PROTOCOL.md) §6. | ☐ | |
| 15 | `updated` was bumped to the real date, and the note is linked from at least one other note so it is not an orphan. | ☐ | |

## 5. Application to the six open §J follow-ups

Each mini-recipe below is **NOT PROVEN until its resolver actually runs and the
gate output is recorded**. None reopens a GREEN wave; none is a repair claim.
"Exact first command" re-reads the anchor and is executable now; the resolver is
the runtime action that would turn the item into evidence.

### F1 — EmptyState CTA chain

- **Evidence anchor to re-read:** [C-05](../40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md) F2 (C05-017 / C05-060), especially the importer greps showing no page supplies `onEmptyCta`/`emptyCtaLabel`; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §J follow-up 1.
- **Exclusive file(s):** to be enumerated exactly in a new scoped recipe; candidate set is `frontend/src/components/ui/AsyncState.tsx` plus the one call site that needs recovery (e.g. `frontend/src/pages/LiveDashboard.tsx`). `frontend/src/i18n.ts` read-only unless a sole owner is assigned. L-15 declined this because the file exceeded its exclusive list.
- **Exact first command:** `cd /home/nedaktov/parlament-deschis && grep -rn "onEmptyCta\|emptyCtaLabel" frontend/src`
- **Expected gate:** the importer grep still shows declarations/forwarding only; after a scoped recipe, `cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build` exit 0 plus a raw browser capture of the CTA click performing recovery.
- **Resolver:** a scoped future recipe with a browser click on local dev. **Status: NOT PROVEN** until that recipe runs and its gate output is recorded.

### F2 — AgeDistributionRadial arc plumbing

- **Evidence anchor to re-read:** [C-05](../40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md) F7 (C05-057): the sole caller `AgeDistributionSection.tsx:40` omits `onCohortClick`, so `interactive` is false and the arc controls never render; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §J follow-up 2.
- **Exclusive file(s):** `frontend/src/components/ui/AgeDistributionSection.tsx` (the call site) is the fix file outside L-15's list; a decision to remove the dead branch instead would additionally own `frontend/src/components/AgeDistributionRadial.tsx`, but not both as an unrecorded guess — use the L-12 NO-CHANGE/wire-vs-remove decision procedure.
- **Exact first command:** `cd /home/nedaktov/parlament-deschis && grep -rn "onCohortClick" frontend/src`
- **Expected gate:** `cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build` exit 0; keyboard probe shows arcs focusable with Enter/Space activating, **or** a documented NO-CHANGE with code citations.
- **Resolver:** a scoped future recipe with a keyboard/browser pass. **Status: NOT PROVEN** until that recipe runs and its gate output is recorded.

### F3 — Production `/ideology` behaviour

- **Evidence anchor to re-read:** [browser observations](../60-EVIDENCE/CLICK-BROWSER-OBSERVATIONS-2026-11-22.md) B4 (the Vercel page rendered a loading state with zero selects); [investigation](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) §6 NOT PROVEN register; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §J follow-up 3.
- **Exclusive file(s):** none — this is a runtime evidence task; no code change is authorised unless a defect is first proven and a scoped recipe assigned.
- **Exact first command (anchor re-read):** `cd /home/nedaktov/parlament-deschis && grep -n "ideology\|NOT PROVEN\|resolver" "Parlament Deschis Obsidian vault/60-EVIDENCE/CLICK-BROWSER-OBSERVATIONS-2026-11-22.md"`
- **Expected gate:** a loaded production `/ideology` response with a raw capture and the year control present; the four vault gates still exit 0 after the evidence note is written. Local dev success does **not** substitute for production ([AGENTS](../00-START/AGENTS.md) NEVER).
- **Resolver:** a loaded production ideology response. **Status: NOT PROVEN** until that response is captured.

### F4 — External URL reachability

- **Evidence anchor to re-read:** [C-06](../40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md) §3 external-URL table, rows E01–E03, and its §7 coverage statement (no network calls made); [investigation](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) §6; [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §J follow-up 4. The HTTP probe quoted in [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §1 remains a **note claim**, not supervisor-verified.
- **Exclusive file(s):** none — a network probe, not a code edit; a broken URL would need its own scoped recipe.
- **Exact first command (anchor re-read):** `cd /home/nedaktov/parlament-deschis && grep -n "E01\|E02\|E03\|NOT PROVEN" "Parlament Deschis Obsidian vault/40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md"`
- **Expected gate:** a recorded probe per URL with HTTP status and probe date; the four vault gates exit 0 after the evidence note is written.
- **Resolver:** a network probe. **Status: NOT PROVEN** until the probe is run and recorded.

### F5 — Raw console captures for W3/W4/W6

- **Evidence anchor to re-read:** [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §J follow-up 5 and §C A2 / §D item 7; [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) W1 and W2B sections, which do record console observations, contrasted with W3/W4/W6.
- **Exclusive file(s):** vault evidence only — the relevant wave sections in [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) and/or a new note under `60-EVIDENCE/`; **no product code**.
- **Exact first command:** `cd /home/nedaktov/parlament-deschis && grep -n "list_console_messages" "Parlament Deschis Obsidian vault/50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md"`
- **Expected gate:** a raw `list_console_messages` artifact attached per wave (W3/W4/W6), with scope and limits in the Browser evidence section; the four vault gates exit 0 after the write-back.
- **Resolver:** a future wave attaching a raw console-capture artifact. **Status: NOT PROVEN** until those artifacts exist.

### F6 — pytest / audit / Docker evidence in CI

- **Evidence anchor to re-read:** [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §6 (pytest and the strict audit replayed at W7 only if the environment can run them, otherwise AMBER/NOT PROVEN), §1 and §9 (required CI checks: test, audit, docker, evidence-guards); [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §J follow-up 6.
- **Exclusive file(s):** none — CI is the resolver; editing CI workflows is a side quest and forbidden by the shared policy. An evidence note may record the CI result only.
- **Exact first command (anchor re-read):** `cd /home/nedaktov/parlament-deschis && grep -n "pytest\|audit\|docker\|resolver" "Parlament Deschis Obsidian vault/20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md"`
- **Expected gate:** recorded CI run with the four required checks and their outcomes; if any check cannot run here, mark AMBER/NOT PROVEN with the CI resolver — never a local pass.
- **Resolver:** CI required checks. **Status: NOT PROVEN** until a CI run is recorded.

## 6. Verification of this note

From the repository root `/home/nedaktov/parlament-deschis`, run all four and
record the exit codes:

```bash
cd /home/nedaktov/parlament-deschis
python3 scripts/vault_lint.py
python3 scripts/vault_sync.py --check
bash scripts/check-doc-truth.sh
git diff --check
```

Expected: `VAULT LINT PASS…` (exit 0), `vault_sync --check: clean…` (exit 0),
`false-claims: 0` (exit 0), and no output from `git diff --check` (exit 0).
This note is valid only if all four were **actually run** with those results;
an unrun check is **NOT PROVEN**, never PASS
([STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §2.6 and §6,
[SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §C A1/G4). Because this is a
vault-only note, it changes no product code, no git state beyond the working
tree, no data, no config, no workflow and no deployment; no regeneration of
`_generated/*` should be needed, and a clean `vault_sync.py --check` proves it.

## See also

[STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) ·
[RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) ·
[SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) ·
[CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) ·
[LINK-REPAIR-JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) ·
[MAINTENANCE-PROTOCOL](../00-START/MAINTENANCE-PROTOCOL.md)
