---
id: LINK-REPAIR-SUPERVISION
type: runbook
title: "Repair programme supervision protocol (2026-11-22)"
description: "Read-only supervision protocol for the 2026-11-22 link-and-button repair programme: authority, critical strategy audit, RED/AMBER/GREEN criteria, per-wave audit checklist, agent-behaviour rubric, sign-off template and Wave 0 preconditions."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/frontend]
source_paths: [20-DIRECTION/LINK-REPAIR-STRATEGY-2026-11-22.md, 20-DIRECTION/LINK-REPAIR-RECIPES-2026-11-22.md, 40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Repair programme supervision protocol (2026-11-22)

This note governs every wave of the repair programme defined by
[LINK-REPAIR-STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) and
[LINK-REPAIR-RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md), against the defects in
the [master clickable investigation](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md),
its [journey](../50-RESEARCH/CLICK-INVESTIGATION-JOURNEY-2026-11-22.md) and the
[browser observations](../60-EVIDENCE/CLICK-BROWSER-OBSERVATIONS-2026-11-22.md).
Governing vault rules: [AGENTS](../00-START/AGENTS.md) and
[MAINTENANCE-PROTOCOL](../00-START/MAINTENANCE-PROTOCOL.md), especially §1
(executable evidence outranks prose; no guessing → NOT PROVEN).

**Reading record (honesty).** Strategy, recipes, master investigation, journey
and browser evidence were read in full. C-05 and C-03 were read in full;
C-01, C-02, C-06 and C-07 were spot-checked at the cited lines only. No network
call, browser tool, code edit, commit, merge or deployment was performed by the
supervisor. Code citations below are read-only observations at commit
`88112168237e5c37841b785dccd2375f6cc40115` (verified by `git rev-parse HEAD` at
authoring). The HTTP probe recorded at STRAT §1:35 is cited as a *note claim*;
it was not re-run here. An unrun check is never recorded as a pass by this note.

**Citation shorthand in §B:** `STRAT` = [strategy](LINK-REPAIR-STRATEGY-2026-11-22.md),
`REC` = [recipes](LINK-REPAIR-RECIPES-2026-11-22.md),
`MASTER` = [master investigation](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md),
`Cxx` = the corresponding C-0x note under `40-FRONTEND/`.

## A. Authority and scope

1. **What I decide.** The supervisor decides only the *verdict* on a wave —
   GREEN, AMBER (HOLD) or RED (STOP) — with citations, and the per-wave
   remediation list that must be closed before a later verdict. This is the
   contract at STRAT §2.7 and §7:53-54, §7:138-145.
2. **What I cannot decide or do.** I cannot authorise a merge to `main`, a push
   to `main`, a pull-request merge, a branch-protection change, a deployment, a
   data or release-pin edit, or a CI workflow edit. Those are explicitly owner
   gates (STRAT §3:65-68, §7:145, §9:163-167; REC L-17:423-435). I am read-only
   on product code, git state, data, config, workflows and deployments. I run no
   network or browser tools. I write exactly one artefact: this note (and my
   verdict sections in it).
3. **Division of labour.** The **lead executes** (backups, branch, edits,
   checkpoints, gates, browser spot-checks, vault write-back); the **supervisor
   audits** the evidence the lead produces and issues the verdict. "The lead
   executed it" is not evidence; "the gate output is in the wave note with exit
   code and working directory" is.
4. **Precedence.** Executable evidence and exact `file:line` citations outrank
   any recipe prose (MAINTENANCE-PROTOCOL §1). Where a recipe contradicts the
   investigation or another recipe, the contradiction is recorded in §B and the
   restrictive reading applies until the lead resolves it with evidence: an
   unlisted file is **outside** the exclusive list, an unrunnable gate is **NOT
   PROVEN**, and a two-owner file is **RED**.
5. **Scope of judgement.** I judge scope, evidence, honesty, minimal diff,
   side-quest avoidance and rollback metadata (§E). I do not re-implement or
   redesign the repair and I do not substitute my reading of a screenshot for a
   recorded gate.

## B. Initial strategy audit

Sixteen findings. ADEQUATE means the check is sound as written and is retained;
GAP means a required artifact or rule is missing; RISK means the text can lead
to a defect or a false pass. Every GAP/RISK carries a concrete requirement.

| ID | Note + section assessed | Verdict | Citation | Concrete requirement |
|---|---|---|---|---|
| S-01 | STRAT §4 wave table (W2) vs §2.2 "one owner per file per wave"; REC L-04 and L-05 | **RISK** | STRAT §2.2:42-43 and W2 row :76; REC L-04 exclusive file `frontend/src/pages/LiveDashboard.tsx` at :161 and L-05 same file at :189. Two recipes in one wave own the same file. | Before W2 starts, either merge L-04/L-05 into one recipe with one agent and one checkpoint, or move one to its own wave. Any W2 diff showing `LiveDashboard.tsx` changed from two checkpoints is RED until this is resolved. |
| S-02 | STRAT §4 file-ownership column (W1–W5) vs every i18n-editing recipe | **RISK** | STRAT W1 :75 lists `i18n.ts` but REC L-01 :56 and L-02 :93 never edit it; REC L-03 :140 adds `footer.sourceCode` to "both `i18n.ts` locales — this recipe owns that key" while W2 :76 omits `i18n.ts`; REC L-07 :240, L-08 :260, L-09 :278 each add an i18n key while W3 :77 omits `i18n.ts` (three recipes, one file, one wave); W4 :78 lists `i18n.ts` but REC L-13 :354 and L-14 :369 both edit it. | Publish a single i18n key registry: each new key assigned to exactly one recipe in exactly one wave, with one agent and one checkpoint; correct the §4 file lists to match. Until then, two recipes producing `i18n.ts` hunks in one wave is RED, and a lone `i18n.ts` hunk in W2/W3 is AMBER (file not in that wave's list). |
| S-03 | REC L-02 "Alternative if supervisor rejects adding UI" vs REC L-15 step 4 | **RISK** | REC L-02 :117-118 allows deleting both `mps.compareLink` keys; REC L-15 :391 states "Do not remove `mps.compareLink` keys — L-02 now uses them." The two branches are mutually exclusive and unreconciled. The gate cannot catch the stale pair: `scripts/check_i18n_keys.mjs:87-105` checks missing, asymmetric and duplicate keys, **not** unused keys. | The supervisor must record which L-02 branch was taken before L-15 runs, and L-15 step 4 must be rewritten conditional on that record. If keys were deleted, L-15 must not re-add or preserve them; if the link was rendered, L-15 must not delete them. The wave note must name the chosen branch and the `grep compareLink` output. |
| S-04 | REC L-15 exclusive files (`i18n.ts` read-only parenthetical); briefed worry "L-15 deletes a file L-02 needs" | **GAP** | REC L-15 :382 permits i18n.ts edits "unless removing the `mps.compareLink` keys"; L-02 depends on `i18n.ts:520/1266` (C03 :75, :130), `/compare-mps` at `router.tsx:458` and the existing `Link` import at `Mps.tsx:4` (verified). None of those files is in L-15's deletion set, so the literal deletion claim is **not borne out by code**; the real defect is the permissive parenthetical. | Change L-15's i18n.ts entry to "read-only — no key may be removed; key removal is a separate recipe". Require the step-1 importer greps and their output in the wave note before any file deletion. |
| S-05 | STRAT §4 wave table (W3) vs REC L-09 | **RISK** | REC L-09 :273 owns both `frontend/src/components/CommitteeControl.tsx` and `frontend/src/pages/LiveDashboard.tsx`; STRAT W3 :77 does not list `LiveDashboard.tsx` ("Files owned": Voturi, RollCallTable, CommitteeControl, PartyProfile, PartyComparison). | Move the `LiveDashboard.tsx:227` guard edit into the W2 owner of that file, or add it explicitly to W3's list with a single owner. Any W3 hunk in `LiveDashboard.tsx` is RED until resolved. |
| S-06 | STRAT §4 (W4/W5) and REC L-14/L-15 exclusive-file wording | **GAP** | STRAT W4 :78 "affected components"; W5 :79 "dead-control files"; REC L-14 :368-369 "the three component files named in C-05 F8"; REC L-15 :380-382 bare filenames. C-05 F8 :180 actually names five files (SwitchTimeline, PartyNetwork, PartyListTable, PartyComparisonMatrix, CommitteeControl), so "the three" is ambiguous on its face. | Enumerate every exclusive file as a full repo-relative path before the wave's agent starts. The RED rule "a file changed outside the recipe list" is not objectively decidable while the list contains placeholders. |
| S-07 | Gate commands in REC checkpoints vs STRAT §6 and the real package script | **RISK** | REC L-03 :146, L-07 :243, L-08 :264, L-09 :282, L-13 :360, L-14 :372, L-15 :393 all run `node scripts/check_i18n_keys.mjs`; STRAT §6 :121-129 runs it only after `cd ..` from `frontend/`. `frontend/scripts/` contains only `check-sparkline-no-nan.mjs`; the root script exists (`scripts/check_i18n_keys.mjs`) and `frontend/package.json:11` defines the correct `i18n:check` = `node ../scripts/check_i18n_keys.mjs`. From `frontend/` the recipe command fails; from repo root `npm run lint` fails (no root script). | Replace every such checkpoint with an explicit working directory and either `npm run i18n:check` from `frontend/` or `node scripts/check_i18n_keys.mjs` from repo root after `cd ..`. A gate recorded with the literal broken command is AMBER/NOT PROVEN regardless of the exit code claimed. |
| S-08 | STRAT §1 baseline and REC L-00 step 1 ("11 investigation vault notes") | **RISK** | STRAT §1:30; REC L-00 :35-37. At authoring `git status --short` returns 14 entries: 13 untracked vault notes **plus a modified tracked file** `00-START/START-HERE.md`; HEAD is the expected `8811216…`. A count test will fail, and the tracked modification is not "an investigation note" at all. This note adds a further untracked file. | L-00 must enumerate exact expected paths at run time (not a count), state the disposition of the modified `START-HERE.md` (commit with baseline or explain/revert), and include this supervision note in the expected set. |
| S-09 | REC L-00 rollback vs STRAT §2.3 / §5 additive-rollback rule | **RISK** | REC L-00 :44-46 accepts `git branch -D`; STRAT §2.3 :44-45 requires non-destructive git and §5 :105 says rollback is additive, "never reset". | Require `git branch -d` first; `-D` only on the just-created, never-merged `repair/links-base`, and only after `git bundle verify` and `sha256sum -c` both exit 0, with both outputs recorded. Never delete a branch whose bundle has not verified. |
| S-10 | L-01 sentinel vs `api.py` year pattern — **checked, sound** | **ADEQUATE** | `backend/routers/api.py:1747` `year: str \| None = Query(None, pattern=r"^\d{4}$")`; `frontend/src/api/client.ts:1003-1008` sets `year` only when truthy; `Ideology.tsx:64` calls `ideology(chesYear)`; REC L-01 :69-72 makes `all` → `undefined` before the call and keeps the query key; `router.tsx:550-554` drops undefined keys but keeps the string `all`. This is consistent with MASTER B1 :55. | Retain. The single failure mode to verify in the W1 diff is the *absence* of REC L-01 step 3: without it, `year=all` reaches the API and is rejected. Acceptance must state "API received no `year` parameter for `all`". |
| S-11 | L-04 scope map vs C02 F1's suggested `scope.searchFor` — **checked, sound** | **ADEQUATE** | `useScope.ts:40,47` makes `date` always a string; `useScope.ts:69-72` returns a `ScopeSearch` with possibly-undefined `chamber`/`legislature`; REC L-04 :164-173 builds `cardSearch: Record<string,string>` with conditional spreads and forbids a prop-type change. C02 :128 had suggested `searchParams={scope.searchFor({date: clamped})}` with a possible type widening; L-04 avoids it correctly. | Retain. Verify the W2 diff keeps the conditional spreads and does not widen `DashboardCardProps`. |
| S-12 | Browser-vs-code evidence separation in gate definitions | **GAP** | STRAT §6 :131-132 calls the browser spot-check "supplementary evidence"; REC acceptance criteria require browser assertions (e.g. L-01 :83-84, L-03 :146-149, L-05 :197-200). No artifact format is defined. Production `/ideology` never loaded in the browser note (B4 :83-85), so some browser assertions cannot be satisfied. | Every wave note must contain two explicitly titled subsections, **Code evidence** and **Browser evidence**, each with scope, raw capture path and limits. If a browser check cannot run, mark that acceptance item AMBER/NOT PROVEN with a named resolver — never PASS, never GREEN for that item. |
| S-13 | REC L-16 step 1 vs C-07 G1 | **GAP** | REC L-16 :406-408 adds `<Link to>` and `navigate({to})` only; C-07 G1 :59 requires a third pattern for internal `<a href="/...">` anchors. L-03 converts four footer anchors in W2, but the guard should still catch future native anchors. | Require all three patterns, or a recorded NO-CHANGE with evidence explaining why the anchor pattern was dropped. L-16 must also record the pre/post `nav_links` count and the guard's exit-code contract. |
| S-14 | Backup evidence format in STRAT §5 / REC L-00 checkpoint | **GAP** | STRAT §5 :91 uses `WAVE=W1` hard-coded; REC L-00 :43 uses literal ellipses (`…/W0/pre.bundle`), which is not an executable command. | Each wave note must record the fully expanded absolute `ROOT`, the exact commands, `git bundle verify` output, `tar -tzf` result and `sha256sum -c` output, committed in the vault wave note before the first edit. No ellipsis in a recorded command. |
| S-15 | REC L-05 wave-click handler; C02 F2 | **RISK** | REC L-05 :192 uses `wave.start_date ?? clamped` with no guard on `wave` itself; C02 F2 :147 asks the handler to guard `wave` for the synthetic `{id:"all"}` object from `SwitchTimeline.tsx:218-227`, and C05-031 :59 shows the synthetic object is passed. The keyboard path passes a real wave (C05-030 :58). | Use `wave?.start_date ?? clamped` (or an explicit synthetic-wave branch) so a no-argument callback cannot throw; record the synthetic-wave navigation in the W2 browser evidence. |
| S-16 | STRAT §7 supervisor contract; REC L-17 | **ADEQUATE** | STRAT §7:145 "It does not merge or deploy", §3:65-68 and §9:163-167; REC L-17:423-435 restricts the lead to repair branches with an owner decision note. The authority boundary in §A of this note matches it. | Retain unchanged. No merge, PR, push to `main` or deploy may be authorised by a supervisor verdict. |

### Explicit contradictions (for the lead)

- **S-01:** L-04 and L-05 both own `frontend/src/pages/LiveDashboard.tsx` in W2,
  contradicting STRAT §2.2:42-43.
- **S-02:** i18n.ts is listed as W1-owned but edited in W2 (L-03), W3
  (L-07/L-08/L-09) and W4 (L-13/L-14); W3 has three simultaneous owners.
- **S-03:** L-02's delete-keys alternative contradicts L-15 step 4.
- **S-05:** L-09 edits `LiveDashboard.tsx` in W3, but W3's file list omits it.
- **S-07:** seven recipe checkpoints use an i18n gate path that does not exist
  from the directory those checkpoints imply.

## C. RED / AMBER / GREEN criteria

Verdicts are applied to one wave at a time. RED → **STOP** (revert the wave's
checkpoints; never merge). AMBER → **HOLD** (no merge without both supervisor
and owner approval). GREEN → integration authorised by §F only.

### GREEN — every one of G1–G8 must hold

| # | Observable condition |
|---|---|
| G1 | Entry and exit git identity recorded: exact branch (`repair/links-wN`), exact HEAD SHA, `git status --short` at entry, recipe and agent identity. |
| G2 | Backup manifest exists, verifies, and its verification output is **committed in the vault wave note** before the first edit: `git bundle verify`, `tar -tzf`, `sha256sum -c` all exit 0, absolute paths expanded. |
| G3 | Exact diff (`git diff --name-only`, `git status --short`) is a non-empty subset of that recipe's **exclusive** file list (or an empty diff for a recorded NO-CHANGE); no file listed in §B as disputed is touched. |
| G4 | Every gate command for the wave actually ran, with recorded working directory, exact command, exit code `0` and an output excerpt. An unrun check is NOT PROVEN (STRAT §2.6, §6:115). |
| G5 | Each recipe acceptance criterion is checked one by one and marked PASS with a pointer to evidence. |
| G6 | Browser section exists and records **no new console error and no broken route**; or the wave has no browser-dependent criterion and says so explicitly. |
| G7 | Vault write-back complete: journey wave section updated, real `updated` date, `vault_sync.py --check`, `vault_lint.py`, doc-truth gate and `git diff --check` all green with output recorded. |
| G8 | Checkpoint SHA(s), commit message contents (recipe ID, evidence anchor, gate output, rollback SHA) and the additive rollback command are recorded. |

### AMBER — HOLD, never PASS

- A1: any gate command not actually run, or run with the broken path from S-07 →
  AMBER/NOT PROVEN; name the check and its resolver. **Never PASS.**
- A2: a browser check could not run (no dev server, production never loaded) →
  AMBER for that acceptance item only; code-level items may still be GREEN.
- A3: gate ran with exit 0 but the output excerpt or working directory is
  missing → AMBER for evidence discipline.
- A4: an ownership ambiguity in §B (S-01/S-02/S-05/S-06) still affects the diff →
  AMBER until resolved, unless a RED condition applies.
- A5: an acceptance item is data-dependent and no live payload was obtained
  (per C03 NOT PROVEN register) → AMBER/NOT PROVEN with the named resolver.

### RED — STOP and revert

- **R1:** any file changed outside a recipe's exclusive list, including
  `i18n.ts` in a wave that does not own it, or a second recipe's file in a
  two-owner collision (S-01/S-02/S-05).
- **R2:** any **new console error** or **broken route** observed in the browser
  during the wave, including one produced by the repair itself.
- **R3:** uncommitted backup manifest failure — missing manifest, failed
  `git bundle verify` / `tar -tzf` / `sha256sum -c`, expanded paths absent, or
  verification output not committed in the vault wave note before the first edit.
- **R4:** any required gate exits non-zero, or a gate is claimed green with a
  command that cannot run as recorded.
- **R5:** two recipes in the same wave leave hunks in the same file.
- **R6:** side quest per REC "Shared side-quest policy": data, release pin,
  workflow, Dockerfile, render/Vercel config, branch protection, dependency,
  unrelated reformat or file rename outside the exclusive list.
- **R7:** a browser, axe or network fact claimed without an observation, or a
  NOT PROVEN item promoted to a defect or a pass.
- **R8:** code change without an evidence anchor, checkpoint SHA or rollback
  metadata; or a change to product code during W0.
- **R9:** entry HEAD or branch does not match the wave plan, or the working tree
  contains unexplained product-code changes at entry.

## D. Per-wave audit checklist

I demand the following, in this order, before signing any wave. Missing item →
AMBER; a RED condition → STOP. The lead supplies all of it in the wave note and
the diff, not in chat prose.

1. **Entry git identity.** `git rev-parse HEAD`, `git branch --show-current`,
   `git status --short`, wave ID, recipe ID(s), implementation agent identity,
   and the expected identity from STRAT §4.
2. **Backup path + manifest verification output.** Absolute `ROOT`, exact backup
   commands, `git bundle verify` output, `tar -tzf` result, `sha256sum -c`
   output, and the vault commit that records them. Check R3 **before** anything
   else.
3. **Exact diff (file list).** `git diff --name-only`, `git diff --stat`,
   `git status --short`; map each path to the recipe's enumerated exclusive list
   from REC and to the corrected ownership register from §B. Note every
   out-of-list path as R1.
4. **Checkpoint SHAs.** `git log --oneline` for the wave, one logical change per
   commit, each message carrying recipe ID + evidence anchor + gate output +
   rollback SHA; confirm no `reset --hard`, force-push, tag move or history
   rewrite.
5. **Gate command + exit code + output excerpt.** For each applicable gate:
   working directory, exact command, exit code, and a verbatim excerpt. Use the
   corrected i18n command from S-07. Include `git diff --check` and the vault
   gates (STRAT §6:121-129).
6. **Vault note updated.** The wave section in
   [LINK-REPAIR-JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md), real
   `updated` date, `vault_sync.py --check`, `vault_lint.py`, doc-truth and
   `git diff --check` outputs; no hand-edited `_generated/*` file; relative
   Markdown links only.
7. **Browser evidence separated from code evidence.** Two titled subsections,
   with scope, raw capture path, observed result and NOT PROVEN limits. Browser
   output never substitutes for a code citation (MAINTENANCE-PROTOCOL §1).
8. **Recipe acceptance criteria, one by one.** A table: acceptance item →
   evidence pointer → PASS / AMBER / NOT PROVEN. NO-CHANGE decisions under
   STRAT §2.8 must cite the inspection that justified them (L-12 is the
   prescribed case).
9. **Rollback metadata.** Additive revert command order, bundle path, and the
   exact SHA to return to; confirm it matches item 4.
10. **Sign-off request.** The lead asks explicitly for a verdict and cites
    items 1–9. I reply using §F only.

## E. Agent-behaviour rubric

Score each dimension. A failure in **scope discipline**, **evidence discipline**
or **honesty about NOT PROVEN** is disqualifying → RED regardless of the other
scores; a failure elsewhere is at least AMBER.

| Dimension | Meets (expected) | Fails (disqualifying unless noted) |
|---|---|---|
| Scope discipline | Diff ⊆ enumerated exclusive list; only in-scope items from MASTER §3–§5 and STRAT §3; disputed files avoided per §B. | R1/R5/R6: out-of-list file, two-owner collision, data/release/workflow/deployment edit, opportunistic refactor. |
| Evidence discipline | Every claim carries `file:line` or a recorded command with exit code; code and browser evidence in separate sections; gate output excerpt present. | Assertion without citation; browser prose used as the sole basis for a defect; missing gate output (A3). |
| Honesty about NOT PROVEN | Unverifiable items marked NOT PROVEN with a named resolver; browser-unavailable items marked AMBER; false leads recorded and discarded, not claimed. | Promoting a NOT PROVEN item to PASS or BROKEN; hiding a failed or unrun check; claiming an axe/network fact not observed (R7). |
| Minimal diff | One logical change per checkpoint; no reformat, no renamed files, no new dependencies; NO-CHANGE recorded when already correct (STRAT §2.8). | Mixed concerns in one commit; unrelated churn; inventing a change where inspection showed none. |
| No side quests | Recipe steps followed in order; deviations recorded and escalated for supervisor approval (REC "Shared side-quest policy":439-445). | New recipe invented on the fly; backend, CI, pin, style-system or config work "while nearby". |
| Correct rollback metadata | Checkpoint SHA, message contents, additive revert order and verified bundle path all present and mutually consistent. | Missing/incorrect SHA, destructive rollback, or a bundle that was not verified first (R3/S-09). |

## F. Sign-off template

Copy this block into the wave section of the journey note and fill every field.
The authorisation sentence is exact; it appears **only** when verdict is GREEN
and every remediation is closed.

```text
WAVE SIGN-OFF
Wave ID:            W0 | W1 | W2 | W3 | W4 | W5 | W6 | W7
Recipes:            L-__, L-__ (agent(s): __________________)
Entry HEAD/branch:  __________________ / repair/links-______
Backup ROOT:        /tmp/opencode/backups/link-repair/______
Manifest evidence:  bundle verify __ | tar -tzf __ | sha256sum -c __ (vault commit ______)
Diff (name-only):   ________________________________________________
Checkpoint SHA(s):  ________________________________________________
Gates (cmd/exit):   ________________________________________________
Browser evidence:   ________________________________________________
Code evidence:      ________________________________________________
Acceptance items:   __/__ PASS · __/__ AMBER/NOT PROVEN
Verdict:            GREEN | AMBER (HOLD) | RED (STOP)

Citations (exact note/section or file:line for every judgement):
  - ________________________________________________________________
  - ________________________________________________________________

Required remediations (owner: lead; each must be closed before next verdict):
  - R__ / S-__ : __________________________________________ [open|closed]
  - R__ / S-__ : __________________________________________ [open|closed]

Authorisation (GREEN only — reproduce verbatim, filling the braces):
  "Integration authorised: wave {WAVE} is GREEN on the evidence cited above;
   the lead may merge {BRANCH} into repair/links-base with git merge --ff-only."
```

If the verdict is AMBER or RED, strike the authorisation line entirely and
write instead: "No integration authorised. HOLD pending {remediation}" or
"STOP: revert checkpoints {SHAs}; do not merge." Only the exact GREEN sentence
above authorises integration; its absence means no merge. Push, PR and deploy
remain owner gates (STRAT §9) and are never authorised by this block.

## G. Wave 0 preconditions

All of the following must be true before `L-00` runs. Citations are to the
strategy unless noted.

| # | Precondition | Citation |
|---|---|---|
| W0-P1 | Local branch is `main` at HEAD `88112168237e5c37841b785dccd2375f6cc40115` with a clean **product** tree; no wave branch exists yet. Re-verify at run time — do not rely on this note's authoring observation. | STRAT §4 W0 :74, §1 :28-29; REC L-00 :35-37 |
| W0-P2 | Working tree is enumerated by exact path, not by the count "11": 13 untracked vault notes plus a modified tracked `00-START/START-HERE.md` were observed at authoring, plus this supervision note. The disposition of the `START-HERE.md` modification is recorded before the baseline commit. | STRAT §1 :30; REC L-00 :35-38; S-08 |
| W0-P3 | This supervision protocol exists, is `active`/`canonical`, and is the governing authority for all wave verdicts — STRAT §4 assigns W0's supervisor cell "protocol authored" and §7:138-145 requires the supervisor to author it before the programme runs. | STRAT §4 :74, §7 :138-145 |
| W0-P4 | Backup at `/tmp/opencode/backups/link-repair/W0/` created per the §5 bundle/archive/manifest procedure with **expanded** paths; `git bundle verify`, `tar -tzf` and `sha256sum -c` all exit 0 and their output is committed in the journey note. "The manifest must verify before any wave starts." | STRAT §5 :88-109; REC L-00 :39-43; S-14 |
| W0-P5 | `repair/links-base` is created from HEAD and the baseline commit message is exactly `docs(vault): commit clickable investigation baseline (C-01..C-07)`; `main` is untouched. Rollback uses an additive revert, or `git branch -d` (only `-D` under the S-09 conditions). | REC L-00 :37-47; STRAT §2.3 :44-45 |
| W0-P6 | Scope gate holds: vault notes only in W0; no data, `data/latest-release.txt`, CI workflow, branch protection, dependency, merge or deployment change anywhere in the programme. | STRAT §2.1 :39-41, §3 :65-68, §9 :163-167; REC "Shared side-quest policy" :439-445 |
| W0-P7 | Vault gates runnable and their W0 output recorded: `vault_sync.py --check`, `vault_lint.py`, doc-truth gate, `git diff --check`; no `_generated/*` file hand-edited; frontmatter valid and links relative Markdown only. | STRAT §6 :125-129, §10 :169-175; AGENTS :22-26, :49-57 |
| W0-P8 | The four ownership contradictions S-01, S-02, S-05 and S-06 are logged as **blocking W1/W2/W3/W4/W5**, with a single corrected file-ownership register published before any code-editing wave starts. They do not block W0 itself, which edits vault notes only. | STRAT §2.2 :42-43, §4 :70-84; §B of this note |

## H. Corrections verification (2026-11-22)

Re-checked against the corrected [strategy](LINK-REPAIR-STRATEGY-2026-11-22.md),
[recipes](LINK-REPAIR-RECIPES-2026-11-22.md) and
[journey](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md). Read-only: no gate,
browser or network call was run by me. At authoring I re-verified `main`, HEAD
`88112168237e5c37841b785dccd2375f6cc40115`, 15 vault entries and no modified
product-code path (`git status --short`) — W0-P1 holds at this instant and must
still be re-verified at wave entry.

### H.1 Finding-by-finding

| ID | Status | Citation and basis |
|---|---|---|
| S-01 | **RESOLVED** | STRAT §4 W2 :76 and §4.1 :88-90; REC L-04 :178-180, L-05 :208-212. `LiveDashboard.tsx` has one owner/agent/checkpoint in W2. Caveat: N-1 below. |
| S-02 | **RESOLVED** | STRAT §4.1 :95-99 matches REC L-03 :148, L-07 :261-265, L-13 :388-391; non-owners disclaim i18n.ts at REC L-08 :294-295, L-09 :312-313, L-14 :412-413, L-15 :431-433; W1 :75 "no `i18n.ts`", W5 :79 read-only. **W1–W6 wave-table file lists agree exactly** with recipe exclusive lists at REC L-01 :76, L-02 :113, L-03 :148, L-04 :185, L-05 :217, L-06 :236, L-07 :261, L-08 :286, L-09 :307, L-10 :326, L-11 :346, L-12 :366, L-13 :388, L-14 :409-412, L-15 :424-430, L-16 :454. Caveat: N-2 below. |
| S-03 | **RESOLVED** | REC L-02 :135-138 "no delete-keys alternative"; L-15 :431-433, :442; STRAT §4.1 :101-102. |
| S-04 | **RESOLVED** | REC L-15 :431-433 replaces the permissive parenthetical with explicit read-only/no key removal. |
| S-05 | **RESOLVED** | STRAT W3 :77 lists `LiveDashboard.tsx` with "L-09 sole W3 owner"; §4.1 :90; REC L-09 :307. |
| S-06 | **RESOLVED** | STRAT W4 :78, W5 :79 enumerate full repo-relative paths; REC L-14 :409-412, L-15 :424-430. |
| S-07 | **RESOLVED** | REC global convention :29-35; i18n package-script checkpoints at L-03 :166, L-07 :276, L-08 :298, L-09 :316, L-13 :397, L-14 :416, L-15 :444 all use `npm run i18n:check` from the absolute frontend cwd. Caveat: N-3 below. |
| S-08 | **RESOLVED** | STRAT §1 :30; REC L-00 :43-50 enumerates exact paths at run time and decides `START-HERE.md` disposition. Caveat: N-4 below. |
| S-09 | **RESOLVED** | REC L-00 :63-65: `git branch -d` first, `-D` only after verified-bundle conditions. |
| S-12 | **RESOLVED** | STRAT §6 :149-155; REC global :29-35 require titled Code evidence / Browser evidence sections and AMBER/NOT PROVEN for unavailable browser checks. |
| S-13 | **RESOLVED** | REC L-16 :457-462 adds internal `href="/…"` anchors alongside `<NavLink>`/`<Link to>`/`navigate({to})`, with pre/post `nav_links` count and exit-code contract. |
| S-14 | **RESOLVED** | STRAT §5 :108-127 (`WAVE="<WAVE_ID>"`, expanded paths); REC L-00 :54-62, :61-62 fully expanded checkpoint and three verbatim outputs before first edit. |
| S-15 | **RESOLVED** | REC L-05 :211, :220: `wave?.start_date ?? clamped`. |

### H.2 New issues introduced by the corrections

| ID | Wave | Status | Citation and required remediation |
|---|---|---|---|
| N-1 | W2 | **OPEN** | STRAT §2.5 :48-49 "One logical change per commit" / "message states recipe ID" vs REC L-04 :178-180 "two logical changes in one commit" naming both IDs, and two separate checkpoint blocks at L-04 :201 and L-05 :225. Requirement: keep one agent but emit two atomic commits with one shared gate, or record an explicit waiver in §2.5. |
| N-2 | W4 | **OPEN** | STRAT §4 W4 :78 says "adds **both** W4 keys", but §4.1 :98, REC L-13 :389-391 and journey :52 specify **three** (`filter.minVotes`, `filter.minVotesPlaceholder`, `common.viewAll`). Requirement: change "both" to "all three" in the wave table. |
| N-3 | W1 | **OPEN** | REC global :29-31 requires npm commands from the absolute frontend cwd; L-01 checkpoint :99 still says `cd frontend && npm run lint && npm run build`, which cannot run from that cwd (no nested `frontend/`). Requirement: drop `cd frontend &&` or use the absolute path as at L-03 :166. The i18n package-script defect itself is fixed. |
| N-4 | W0 write-back | **OPEN** | Journey Phase S :26-27 still states "11 investigation vault notes uncommitted", contradicting STRAT §1 :30 and L-00 :43-50. Requirement: replace with the exact-path enumeration or label it historical per MAINTENANCE-PROTOCOL §1.3-1.4. |

L-16 :457 says "all three" but enumerates four patterns (NavLink added for
context); the required `href="/…"` pattern is present, so this wording is not
an OPEN item.

### H.3 Wave 0 readiness (W0-P1…P8)

| Precondition | Verdict | Basis |
|---|---|---|
| W0-P1 | READY (re-verify at entry) | Verified now: `main`, HEAD `8811216…`, clean product tree; STRAT §4 :74, §1 :28-29. |
| W0-P2 | READY | REC L-00 :43-50 exact paths incl. `START-HERE.md`, this note and the repair journey; STRAT §1 :30. N-4 is a stale journey sentence, not a precondition failure. |
| W0-P3 | READY | This note is active/canonical with §A/§H; STRAT §4 :74, §7 :160-167. |
| W0-P4 | READY (procedure only) | STRAT §5 :108-127; REC L-00 :54-62. Backup not yet executed; all three verifications must pass before the first edit. |
| W0-P5 | READY | REC L-00 :51-53 exact baseline message, :63-65 rollback. |
| W0-P6 | READY | STRAT §2.1 :39-41, §3 :65-68, §9 :183-189; REC shared policy :493-499. |
| W0-P7 | READY WITH CONDITION | STRAT §6 :143-146, §10 :191-197. Journey :39-41 gate output predates the corrections; L-00 :59-60 must re-run the four vault gates and record fresh output. Not re-run by me. |
| W0-P8 | READY | STRAT §4.1 :86-102 and journey :43-66 publish the corrected ownership register; N-1…N-4 are logged above with wave assignments. |

**W0 (vault-only) may start: YES.**

**First code-editing wave W1 is unblocked: NO** — N-3 (REC L-01 :99 versus the
global working-directory convention at REC :29-31) must be closed first; N-1
and N-2 are assigned to W2/W4 and N-4 to the W0 vault write-back.

**Final check (2026-11-22):** N-1…N-4 RESOLVED (REC L-04 :178-182/:203-233 vs STRAT §2.5 :48-49; STRAT §4 :78; REC L-01 :99; journey :26-28) — W0 MAY START: YES; W1 UNBLOCKED: YES (supersedes the NO above; residual "one checkpoint" wording at STRAT §4 :76 and §4.1 :88-90 to be aligned to two atomic commits before W2).

## See also

[LINK-REPAIR-STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) ·
[LINK-REPAIR-RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) ·
[LINK-REPAIR-JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) ·
[CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) ·
[CLICK-BROWSER-OBSERVATIONS](../60-EVIDENCE/CLICK-BROWSER-OBSERVATIONS-2026-11-22.md) ·
[MAINTENANCE-PROTOCOL](../00-START/MAINTENANCE-PROTOCOL.md)
