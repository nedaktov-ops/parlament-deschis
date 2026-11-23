---
id: LINK-FOLLOWUP-PARALLEL-RECIPES
type: runbook
title: "Parallel recipes for F1 and F2 — EmptyState CTA chain and AgeDistributionRadial arcs (2026-11-22)"
description: "Supervisor ruling and execution protocol for two disjoint, concurrently dispatched implementation recipes L-23 and L-24 in one wave W11, with a shared backup, lead-owned atomic commits, gates and per-recipe verdicts; a planning note, not an execution."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/frontend]
source_paths: [20-DIRECTION/LINK-FOLLOWUP-WAVE-PLAN-2026-11-22.md, 20-DIRECTION/LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md, 20-DIRECTION/LINK-REPAIR-SUPERVISION-2026-11-22.md, 40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md, frontend/src/components/ui/AsyncState.tsx, frontend/src/components/EmptyState.tsx, frontend/src/components/AgeDistributionRadial.tsx, frontend/src/components/ui/AgeDistributionSection.tsx]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Parallel recipes for F1 and F2 (wave W11)

**This is a planning note, not an execution.** It authorises the two deferred
code-touching follow-ups as recipes; it does not edit product code, run gates,
commit, merge, push, deploy or change any verdict. Governing references:
[WAVE-PLAN](LINK-FOLLOWUP-WAVE-PLAN-2026-11-22.md) §1 (ranking and deferral),
[CONSISTENCY-STEPS](LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md) §2/§3,
[SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §C/§D/§E/§J,
[C-05](../40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md) F2/F7, and W5 of
[JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md). An unrun check is
**NOT PROVEN**, never PASS.

## 1. Ruling

**F1 and F2 are now the top actionable recommendations** because every earlier
ranked item has been closed as far as this environment allows:

- W8 closed F4 with a dated probe corroborating the note claim; W9 attempted F3
  and recorded an honest NOT PROVEN with a named resolver; W10 recorded F6 as
  NOT PROVEN with the owner-PR resolver and attached F5's fresh captures
  ([JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) W8–W10).
- The [WAVE-PLAN](LINK-FOLLOWUP-WAVE-PLAN-2026-11-22.md) §1 deferred F1/F2 only
  because their code-change risk was highest and their closability depended on
  scoped recipes — both conditions are now met by the two recipes below. Their
  deferral states were explicitly **"NOT PROVEN — resolver: an approved scoped
  recipe"** (§1 rows 5 and 6); these recipes are that resolver.
- They remain the last two open items in [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md)
  §J follow-ups 1 and 2. W5 L-15 declined both because the files were outside
  its exclusive list ([JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md)
  W5 :910-915); that scope obstacle is removed by the new, exact lists below.
- Both are dead controls with no user-visible break
  ([investigation](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) §4.4), so
  each recipe must begin with an L-12-style decision
  ([RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) L-12) and must never invent a
  capability to justify an edit (§C R7; [CONSISTENCY-STEPS](LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md)
  §2 row 9).

**Why parallel in one wave W11.** The two exclusive-file lists are strictly
disjoint by construction:

| Recipe | Item | Exclusive files (full repo-relative paths) |
|---|---|---|
| L-23 | F1 | `frontend/src/components/ui/AsyncState.tsx`, `frontend/src/components/EmptyState.tsx` |
| L-24 | F2 | `frontend/src/components/ui/AgeDistributionSection.tsx`, `frontend/src/components/AgeDistributionRadial.tsx` |

No file appears in both lists, so §2.2 "one owner per file per wave"
([STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §2.2, §4.1; S-01/S-05) holds
even with two concurrent agents. `frontend/src/i18n.ts` is **read-only in W11**
for both recipes: neither adds, removes or changes a key, so there is no sole
i18n owner to assign and no key-registry conflict (S-02). One shared backup and
one shared gate replay avoid double work; the lead — not the agents — owns
staging, committing and gate execution.

**Known coupling to watch (not a conflict).** `AgeDistributionSection.tsx:5`
imports `./AsyncState`, so both recipes touch code in the same import graph.
The overlap is semantic, not textual: L-23 removes only the unused CTA props
(`emptyCtaLabel`/`onEmptyCta`), and `AgeDistributionSection.tsx:29-35` passes
`view`, `variant`, `onRetry`, `errorLabel` and `emptyTitle` — none of the CTA
props. Re-run the L-23 removal greps after both agents finish to prove no type
break. L-23 must **not** remove `onRetry`: the ErrorState retry is wired and
working (C-05 F3 :140, AgeDistributionSection.tsx:32 passes `shift.refetch`).

**Still owner-gated.** No merge to `main`, no PR merge, no push to `main`, no
deploy, no branch-protection change; after a GREEN verdict the lead may
integrate into `repair/links-base` with `git merge --ff-only` only
([STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §9;
[JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) W7 :1063-1069).
Creating a *new user capability* (actually wiring an EmptyState CTA or a cohort
click) is likewise not authorised by these recipes — it needs a new recipe and
supervisor approval under the shared side-quest policy.

## 2. Parallel execution protocol (wave W11, branch `repair/links-w11`)

1. **Entry identity and shared backup — before ANY edit.** From repo root,
   capture `git branch --show-current && git rev-parse HEAD && git rev-parse origin/main && git status --short`, record the entry HEAD SHA as `<W11-ENTRY-SHA>`,
   then create and verify **one** backup at
   `/tmp/opencode/backups/link-repair/W11` using the fully expanded-path
   procedure in [STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) §5 / S6 of
   [CONSISTENCY-STEPS](LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md):

   ```bash
   mkdir -p /tmp/opencode/backups/link-repair/W11
   git bundle create /tmp/opencode/backups/link-repair/W11/pre.bundle --all
   git rev-parse HEAD > /tmp/opencode/backups/link-repair/W11/pre.sha
   git status --porcelain > /tmp/opencode/backups/link-repair/W11/pre.status
   tar -czf /tmp/opencode/backups/link-repair/W11/worktree.tgz -C /home/nedaktov/parlament-deschis --exclude=.git --exclude=node_modules --exclude=.venv --exclude=.next --exclude=dist .
   (cd /tmp/opencode/backups/link-repair/W11 && sha256sum pre.bundle pre.sha pre.status worktree.tgz > SHA256SUMS)
   git bundle verify /tmp/opencode/backups/link-repair/W11/pre.bundle
   tar -tzf /tmp/opencode/backups/link-repair/W11/worktree.tgz >/dev/null
   (cd /tmp/opencode/backups/link-repair/W11 && sha256sum -c SHA256SUMS)
   ```

   All three verifications must exit 0 and their verbatim output must be
   committed in the vault wave note **before** either agent edits (G2/R3, S-14).
   `pre.sha` must equal `<W11-ENTRY-SHA>`. If any check fails → RED, no dispatch.

2. **Dispatch two agents concurrently.** Agent A executes L-23; Agent B
   executes L-24. Each agent receives only its own recipe and exclusive-file
   list. Hard constraints on both agents:
   - edit **only** the files in that list; no other file, no vault note,
     no `_generated/*`, no data, config, workflow or deployment file;
   - **do not run `git add`, do not commit, do not stage, do not push**;
   - **do not run any build, lint, i18n or browser gate** — the lead runs the
     shared gate once after both agents are finished, so no agent observes a
     half-applied sibling diff;
   - record decisions and evidence in the return report, not in a file.

   Wait for **both** agents to report before the next step.

3. **Diff partition check (the overlap stop condition).** From repo root run
   `cd /home/nedaktov/parlament-deschis && git status --short && git diff --name-only && git diff --stat`. The lead then verifies:

   ```bash
   git diff --name-only -- frontend/src/components/ui/AsyncState.tsx frontend/src/components/EmptyState.tsx
   git diff --name-only -- frontend/src/components/ui/AgeDistributionSection.tsx frontend/src/components/AgeDistributionRadial.tsx
   ```

   - `A` ⊆ L-23's two paths, `B` ⊆ L-24's two paths;
   - `A ∪ B` equals the full `git diff --name-only` (no unattributed path);
   - `A ∩ B` is **empty**.

   **STOP condition:** if `A ∩ B` is non-empty, if any path falls outside both
   lists, or if either agent staged/committed, issue **RED (STOP)** immediately:
   neither commit is emitted, both sets of edits are reverted additively
   (`git revert` only if any commit exists; otherwise restore from the verified
   bundle/worktree archive per STRAT §5), and the wave is never merged. A
   two-owner file is RED by §C R1/R5, even if the hunks are textually disjoint.

4. **Shared gate — once, on the combined tree, after both agents finish.**
   Run the gates in §5 and record working directory, exact command, exit code
   and output excerpt. A non-zero exit is RED; a not-run gate is NOT PROVEN
   (A1/R4). Do not let either agent run these.

5. **Two atomic commits, lead-owned, in recipe order.** Stage and commit each
   recipe's paths explicitly, with the usual four fields in the message
   (recipe ID, evidence anchor, gate output summary, rollback SHA
   `<W11-ENTRY-SHA>`):

   ```bash
   cd /home/nedaktov/parlament-deschis
   git add -- frontend/src/components/ui/AsyncState.tsx frontend/src/components/EmptyState.tsx
   git commit -m "refactor(empty): L-23 remove unreachable EmptyState CTA chain — evidence C-05 F2 / EmptyState.tsx:42-51; gates lint/build/i18n exit 0; rollback <W11-ENTRY-SHA>"
   git add -- frontend/src/components/ui/AgeDistributionSection.tsx frontend/src/components/AgeDistributionRadial.tsx
   git commit -m "refactor(radial): L-24 remove dead AgeDistributionRadial arc plumbing — evidence C-05 F7 / AgeDistributionRadial.tsx:73,98-108; gates lint/build/i18n exit 0; rollback <W11-ENTRY-SHA>"
   ```

   If a recipe ends in a documented NO-CHANGE, emit **no** commit for that
   recipe and say so in the wave note; the other recipe still gets its one
   commit. Never mix both recipes into one commit.

6. **Vault write-back and verdict.** Add the W11 section to
   [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md) with separate
   **Code evidence** and **Browser evidence** subsections, the diff partition
   output, both commit SHAs, the shared gate table and the additive rollback
   commands, then re-run the four vault gates. The supervisor issues **one
   verdict per recipe** against L-23/L-24 acceptance (§D items 8/10, §F) and
   **one wave sign-off**; GREEN integration is authorised only by the exact §F
   sentence, into `repair/links-base` by `--ff-only`.

## 3. Recipe L-23 — remove the unreachable EmptyState CTA chain (F1)

- **Objective.** Remove the dead CTA forwarding/props without changing any live
  state rendering. If inspection proves the CTA is actually reachable, record a
  cited NO-CHANGE instead of editing.
- **Evidence anchor.** [C-05](../40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md)
  F2 (C05-017 / C05-060): `EmptyState.tsx:5-6` (props), `:26-27` (destructure),
  `:42-51` (guarded button); `AsyncState.tsx:44-45` (StateViewProps),
  `:61-62` (destructure), `:89-90` (`ctaLabel={emptyCtaLabel}`,
  `onCta={onEmptyCta}`). Direct users pass only `title`: `Parties.tsx:91`,
  `Committees.tsx:397-402`. [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md)
  §J follow-up 1; [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md)
  W5 :910-915 (L-15 declined for scope).
- **Exclusive files.** `frontend/src/components/ui/AsyncState.tsx`,
  `frontend/src/components/EmptyState.tsx`. Everything else — including
  `frontend/src/i18n.ts`, `frontend/src/pages/Parties.tsx`,
  `frontend/src/pages/Committees.tsx`, tests and vault notes — is out of scope.
- **Steps.** From `/home/nedaktov/parlament-deschis`:
  1. Re-read and record verbatim:
     `grep -rn "onEmptyCta\|emptyCtaLabel" frontend/src` and
     `grep -rn "onCta\|ctaLabel" frontend/src` and
     `grep -rn "<EmptyState" frontend/src`.
  2. **L-12 decision FIRST.** If any supplier of `onEmptyCta`/`emptyCtaLabel`
     appears outside `AsyncState.tsx` (a dynamic prop spread, a test fixture or
     a call site), the CTA is reachable: write a **NO-CHANGE** block with those
     citations and make no edit. Do not invent a reason to change reachable
     code. Otherwise continue.
  3. **Remove the forwarding chain in `AsyncState.tsx` first:** delete
     `emptyCtaLabel?: string;` and `onEmptyCta?: () => void;` from
     `StateViewProps` (:44-45), their destructuring entries (:61-62) and the
     `ctaLabel={emptyCtaLabel}` / `onCta={onEmptyCta}` props on `<EmptyState>`
     (:89-90). Leave `onRetry` (:41, :58, :82) and every other prop untouched —
     ErrorState's retry is wired (C-05 F3 :140). Note that
     `AsyncStateProps extends Omit<StateViewProps, "view">` (:98), so removing
     the two fields from the interface automatically removes them from
     `AsyncState`'s accepted props.
  4. **Then remove the props in `EmptyState.tsx`:** delete `ctaLabel?: string;`
     and `onCta?: () => void;` from `EmptyStateProps` (:5-6), their
     destructuring (:26-27) and the guarded button branch (:42-51). Keep the
     container, icon, `title` and `description` rendering byte-identical.
  5. Record the final greps: `grep -rn "onEmptyCta\|emptyCtaLabel\|ctaLabel\|onCta" frontend/src` must return no match; `grep -rn "<EmptyState" frontend/src` must show the same direct users as step 1.
- **Checkpoint.** Shared gate from §5 exits 0; both final greps recorded; the
  diff is a non-empty subset of the two exclusive files (or empty with an
  accepted NO-CHANGE).
- **Rollback.** `git revert <L-23-commit-sha>` (additive). If both commits must
  be withdrawn, revert L-23 then L-24 in reverse commit order. Verified bundle:
  `/tmp/opencode/backups/link-repair/W11/pre.bundle`.
- **Acceptance.** (1) L-12 decision block cites the inspection; (2) removal
  order is forwarding-in-AsyncState first, then props-in-EmptyState; (3) no
  live state rendering or `onRetry` changed; (4) final greps clean and the
  import graph still builds; (5) a **local-dev click capture of a real
  EmptyState CTA is required only if a real CTA exists**. On the evidence at
  C-05 F2 no CTA supplier exists, so after removal there is nothing to click:
  mark this acceptance item **NOT PROVEN** with resolver "a future call site
  that supplies a real CTA, plus a local-dev click capture of that CTA" — never
  PASS, never a defect.
- **Side-quest policy.** No i18n key, page, test, data, config, workflow or
  deployment edit; no new CTA capability; no browser/network claim without a
  capture; no vault note edit by the agent.

## 4. Recipe L-24 — AgeDistributionRadial arc plumbing (F2)

- **Objective.** Decide from code whether the interactive arcs are a real
  capability or dead plumbing, then apply the honest choice with citations.
- **Evidence anchor.** [C-05](../40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md)
  F7 (C05-057): `AgeDistributionRadial.tsx:16` (prop), `:38` (destructure),
  `:73` (`const interactive = Boolean(onCohortClick)`), `:98-108` (the spread
  adding `role="button"`, `tabIndex=0`, `onClick`, `onKeyDown` with
  `activateOnKey`), `:83` (`role={interactive ? "group" : "img"}`), `:135-146`
  (cohort legend); sole caller `AgeDistributionSection.tsx:40` omits
  `onCohortClick`. [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md)
  §J follow-up 2; [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md)
  W5 :911-914.
- **Exclusive files.** `frontend/src/components/ui/AgeDistributionSection.tsx`,
  `frontend/src/components/AgeDistributionRadial.tsx`. Strictly disjoint from
  L-23. `frontend/src/i18n.ts` read-only; `frontend/src/utils/a11y.ts` read-only
  (do not change `activateOnKey`).
- **Steps.** From `/home/nedaktov/parlament-deschis`:
  1. Re-read and record verbatim:
     `grep -rn "onCohortClick" frontend/src` and
     `grep -rn "AgeDistributionRadial" frontend/src`, plus a code read of
     `AgeDistributionSection.tsx:1-44` and `AgeDistributionRadial.tsx:73-111`.
  2. **L-12 decision procedure FIRST — before any edit.** Decide:
     - **Wire?** Only if the caller already owns a real action for a cohort
       (e.g. an existing `useNavigate` or filter setter in
       `AgeDistributionSection.tsx`). At the evidence above it owns only
       `useQuery` (:10-13) and `useTranslation` (:9) and has no such action;
       wiring would **invent a new capability**, which is a new recipe after
       supervisor approval, not this one. If a real action does exist, stop and
       report it rather than guessing a destination.
     - **Remove (expected honest choice).** The legend at
       `AgeDistributionRadial.tsx:135-146` and the SVG `aria-label` at `:84`
       already expose each cohort's label and count, and the centre text at
       `:120-130` exposes the average; removing the unreachable interactive
       branch removes no user capability. Record this reasoning with the cited
       lines before editing.
     - A cited **NO-CHANGE** is also valid if inspection shows a real supplier
       of `onCohortClick` outside the sole caller.
  3. If removal is chosen: in `AgeDistributionRadial.tsx` delete the
     `onCohortClick?: (cohort: CohortData) => void` prop (:16), its
     destructure (:38), `const interactive = Boolean(onCohortClick)` (:73), the
     entire spread object (:98-108), and the now-unused `KeyboardEvent` type
     import (:2) and `activateOnKey` import (:3). Change
     `role={interactive ? "group" : "img"}` (:83) to the literal `role="img"`.
     Preserve `arcs`, `avgAge`, colours, `<title>` (:110) and the legend.
  4. In `AgeDistributionSection.tsx`, add a one-line code comment at the
     `<AgeDistributionRadial … />` call site (:40) recording that the chart is
     non-interactive and the legend is the cohort-information path. Do not add
     an `onCohortClick` prop unless a real action was proven in step 2 — and in
     that case stop and escalate instead.
  5. Record the final grep `grep -rn "onCohortClick" frontend/src` — expected:
     no match.
- **Checkpoint.** Shared gate from §5 exits 0; decision block cites the chosen
  branch; final grep clean; diff is a non-empty subset of the two exclusive
  files (or empty with a cited NO-CHANGE).
- **Rollback.** `git revert <L-24-commit-sha>` (additive); verified bundle as
  in L-23.
- **Acceptance.** (1) an L-12 decision block with `file:line` citations exists
  and cites the evidence for the chosen branch; (2) no new user capability was
  invented; (3) chart rendering, legend and `<title>` unchanged; (4) final grep
  clean and the import graph builds; (5) a keyboard probe of interactive arcs
  is **NOT PROVEN** after removal (no arcs are interactive by design) — resolver
  "a future recipe that deliberately wires a real cohort action", never PASS
  and never a defect.
- **Side-quest policy.** No i18n key, a11y utility, page, test, data, config,
  workflow or deployment edit; no invented navigation/filter; no keyboard or
  browser claim without a capture; no vault note edit by the agent.

## 5. Gates and verdict conditions

**Shared gates (run once by the lead on the combined tree, then again after the
vault write-back).** From `/home/nedaktov/parlament-deschis/frontend`:

```bash
cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build && npm run i18n:check
```

`lint` = type-check plus ESLint; `build` = TypeScript build plus Vite bundle;
`i18n:check` = the root i18n key-parity script (no keys change in W11, so it
must stay clean). From repo root, the four vault gates:

```bash
cd /home/nedaktov/parlament-deschis
python3 scripts/vault_lint.py
python3 scripts/vault_sync.py --check
bash scripts/check-doc-truth.sh
git diff --check
```

`_generated/*` is regenerated with `python3 scripts/vault_sync.py`, never
hand-edited; no banned literal string may appear in the vault (describe
categories only, per [MAINTENANCE-PROTOCOL](../00-START/MAINTENANCE-PROTOCOL.md)
§6).

**Verdict conditions.**

- **GREEN** requires: shared backup verified and its output committed before
  either edit; both agents' diffs strictly inside their own exclusive lists and
  mutually disjoint; exactly two atomic lead-owned commits (or one commit plus
  one cited NO-CHANGE) with all four message fields; every gate above actually
  run with working directory, command, exit code and excerpt; both L-12
  decisions cited; every browser item either captured or explicitly NOT PROVEN
  with a named resolver; separate **Code evidence** and **Browser evidence**
  subsections; vault write-back complete; and no owner-gate action taken.
- **AMBER / HOLD** when a browser item could not be observed — the two CTA/keyboard
  items are expected NOT PROVEN by construction — recorded item-scoped with a
  resolver under §C A2/A5 (the W3 precedent). A missing or uncited decision
  block is AMBER until supplied.
- **RED / STOP** if either agent's diff leaves its exclusive list, the two
  diffs overlap, an agent staged/committed/touched the vault, a required gate
  exits non-zero or is claimed green without being run (A1/R4), a NO-CHANGE is
  invented where inspection showed a real supplier (R7), a banned literal
  appears, or any push to `main`, PR merge or deploy occurs. REVERT the
  affected commit(s) additively and do not integrate.

The supervisor issues **one verdict per recipe** (L-23, L-24) with citations
plus **one wave sign-off** for W11. Integration into `repair/links-base` by
`git merge --ff-only` is permitted only on GREEN; `main`, PR and deploy stay
owner gates.

## See also

[WAVE-PLAN](LINK-FOLLOWUP-WAVE-PLAN-2026-11-22.md) ·
[CONSISTENCY-STEPS](LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md) ·
[SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) ·
[RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) ·
[C-05](../40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md) ·
[JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md)
