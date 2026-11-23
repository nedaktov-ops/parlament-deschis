---
id: LINK-REPAIR-RECIPES
type: runbook
title: "Link repair recipes L-00 to L-17 — implementable specifications (2026-11-22)"
description: "Bespoke, file-exclusive repair recipes with exact evidence anchors, implementation steps, checkpoints, rollbacks, acceptance criteria and side-quest policy for the 2026-11-22 clickable repair programme."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/frontend]
source_paths: [frontend/src, frontend/package.json, scripts, .github/workflows/ci.yml]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Link repair recipes L-00 … L-17

Each recipe is a durable prompt for one bespoke agent. Every recipe is
read-only until its wave's backup manifest verifies; then its agent may edit
**only** the listed files. Each recipe ends with a checkpoint command, a
rollback and an acceptance list. Evidence anchors come from
[CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) and the
[C-01…C-07 notes](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md).

Shared preconditions for all recipes: HEAD identity re-verified; wave backup
verified (strategy §5); `git diff --check` clean at wave start; no edits to data,
release pin, workflows, branch protection or `_generated/*`. If a precondition
fails, stop and report RED without editing.

Two global conventions (supervisor S-07, S-12): every `npm run …` command in a
checkpoint is executed from `/home/nedaktov/parlament-deschis/frontend` (the i18n
checkpoint uses the package script `i18n:check`, which resolves to
`../scripts/check_i18n_keys.mjs`); every wave note records **Code evidence** and
**Browser evidence** in separate titled subsections, each with scope, raw capture
path where relevant, result and limits. An unrun or unavailable browser check is
AMBER/NOT PROVEN for that item with a named resolver, never PASS.

---

## L-00 — Wave 0 safety baseline · agent: `git-master`

**Objective.** Establish a clean, additive baseline for the whole programme.
**Files:** vault notes only. **Steps:**
1. Verify `git branch --show-current` = `main`, `git rev-parse HEAD` =
   `88112168237e5c37841b785dccd2375f6cc40115`, and that no product-code path is
   modified. Enumerate the working tree **by exact path** (`git status --short`);
   do not test a count. The expected set includes the investigation C-01…C-07
   notes, the master report, the investigation journey, the browser evidence
   note, the strategy, recipes, supervision protocol and repair journey notes,
   plus the modified tracked file `00-START/START-HERE.md`. Record each path and
   decide explicitly to commit `START-HERE.md` with the baseline (supervisor S-08).
2. Create `repair/links-base` from HEAD; commit the enumerated vault notes there
   with the exact message
   `docs(vault): commit clickable investigation baseline (C-01..C-07)`.
3. Create `/tmp/opencode/backups/link-repair/W0/` with bundle, `pre.sha`,
   `pre.status`, worktree archive and `SHA256SUMS` per strategy §5, using the
   fully expanded absolute path in every recorded command. Run `git bundle
   verify`, `tar -tzf` and `sha256sum -c`; record all three outputs verbatim in
   the W0 journey section **before** the first edit (supervisor S-14).
4. Record the W0 section in the journey note with the exact outputs and run the
   four vault gates.
**Checkpoint:**
`git bundle verify /tmp/opencode/backups/link-repair/W0/pre.bundle && tar -tzf /tmp/opencode/backups/link-repair/W0/worktree.tgz >/dev/null && (cd /tmp/opencode/backups/link-repair/W0 && sha256sum -c SHA256SUMS)` → exit 0.
**Rollback:** `git branch -d repair/links-base` first; use `-D` only on this
just-created, never-merged branch and only after `git bundle verify` and
`sha256sum -c` both exited 0 with their outputs recorded (supervisor S-09).
**Acceptance:** branch exists, baseline commit exists, manifest verifies,
`main` untouched, no product code changed in W0.

---

## L-01 — Ideology "All years" · agent: `minimal-change-engineer` · wave W1

**Evidence:** master report B1; `Ideology.tsx:250,55-60,79-87,248-261`;
`router.tsx:553` drops undefined search keys; `api.py:1747` declares
`year: str | None = Query(None, pattern=r"^\d{4}$")`.
**Exclusive file:** `frontend/src/pages/Ideology.tsx`.

**Steps:**
1. Declare `const ALL_YEARS = "all";` near the top of the component.
2. Replace the `selectedYear` derivation at `:80` with:
   ```ts
   const selectedYear =
     chesYear === ALL_YEARS
       ? undefined
       : chesYear ?? (years.length > 0 ? String(years[0]) : undefined);
   ```
   This keeps "latest wave by default" when there is no `chesYear`, makes
   `all` mean no client filter, and keeps a real year meaning that year only.
3. Change the query function at `:64` from `ideology(chesYear)` to
   `ideology(chesYear === ALL_YEARS ? undefined : chesYear)` — **mandatory**,
   otherwise `year=all` would be sent and rejected by the backend's `^\d{4}$`
   pattern. Do not change the query key (`:63`); `all` remains a distinct cache entry.
4. Change the `<select>` at `:249` to `value={selectedYear ?? ALL_YEARS}` and
   keep `onChange={(e) => setYear(e.target.value)}` (remove the `|| undefined`
   at `:250`). Change the option at `:253` to `value={ALL_YEARS}`.
5. Verify the counter at `:264` still reads `filteredData.length` so the number
   shown matches the rows displayed.

**Checkpoint:** `cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build`; then browser:
load `/ideology?date=2026-11-22`, select "Toți anii", assert URL contains
`chesYear=all`, select value stays `all`, and the table shows more than one
distinct YEAR. **Rollback:** `git revert <checkpoint>`.
**Acceptance:** option persists, URL carries sentinel, API receives no `year`
parameter for `all`, no new console errors, i18n keys unchanged.
**Side-quest policy:** do not touch the ideology copy, PopuList note or chart colours.

---

## L-02 — Restore the dead "Compare MPs" affordance · agent: `minimal-change-engineer` · wave W1

**Evidence:** master report B2; `i18n.ts:520` (ro) / `:1266` (en) define
`mps.compareLink`; `router.tsx:458` registers `/compare-mps`; no render site exists.
**Exclusive files:** `frontend/src/pages/Mps.tsx` (i18n file is read-only here — keys already exist).

**Steps:**
1. Import `Link` is already present at `Mps.tsx:4`; no new import needed.
2. Insert a link immediately after the `<form>` at `:142` and before `<AsyncState>`:
   ```tsx
   <div className="mb-4 flex justify-end">
     <Link
       to="/compare-mps"
       search={scope.searchFor()}
       className="text-sky-400 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-sky-400 rounded"
     >
       {t("mps.compareLink", "Compare MPs →")}
     </Link>
   </div>
   ```
3. Preserve the submitted `q`/`sort`/`offset` only if they are valid on the
   target page; default behaviour (`scope.searchFor()`) is sufficient — do not
   forward page-local params that the target does not declare.

**Checkpoint:** `npm run lint && npm run build`; browser click the new link on
`/mps`, assert URL `/compare-mps?date=…` and title changes.
**Rollback:** `git revert <checkpoint>`. **Acceptance:** link visible in ro and en,
target route renders, no i18n key added or removed, `grep compareLink` finds the
render call plus the two original definitions. There is **no delete-keys
alternative**: the link is always rendered, so L-15 keeps the keys (supervisor S-03).

---

## L-03 — Footer navigation, label and broken project URL · agent: `frontend-developer` · wave W2

**Evidence:** master report §4.1 C01 F1/C06-008; `Footer.tsx:65,73,81,123`
native anchors; `Footer.tsx:96-104` `t("about")` → GitHub; `About.tsx:6`
`https://github.com/parlament-deschis` → measured HTTP 404; `router.tsx:178`
and `Footer.tsx:97,107` use the HTTP 200 URL; `router.tsx:110-118` NavLink helper.
**Exclusive files:** `frontend/src/components/Footer.tsx`, `frontend/src/components/About.tsx`, `frontend/src/router.tsx`, new `frontend/src/config/links.ts`, `frontend/src/i18n.ts` (**sole W2 i18n owner**, adds `footer.sourceCode` only — strategy §4.1).

**Steps:**
1. Create `frontend/src/config/links.ts` exporting
   `export const PROJECT_URL = "https://github.com/nedaktov-ops/parlament-deschis";`
   with a short comment citing the measured 404/200 probe.
2. Import `Link` from `@tanstack/react-router` and `useScope` in `Footer.tsx`;
   call `const scope = useScope();` inside `Footer`.
3. Replace the four native in-app anchors at `:65/:73/:81/:123` with
   `<Link to="/…" search={scope.searchFor()}>`, keeping existing classes and
   the exact label keys. Keep `target="_blank"` only on external anchors.
4. Replace the `t("about")` label on the GitHub anchor at `:102` with a new
   key `footer.sourceCode` (add to both `i18n.ts` locales — this recipe owns
   that key) or an existing equivalent; do not change the destination.
5. Replace the GitHub literal at `Footer.tsx:97,107`, `router.tsx:178` and
   `About.tsx:6` / its `PROJECT_URL` constant with an import of the shared
   constant from `config/links.ts`. Keep `About.tsx` exporting nothing new.

**Checkpoint:** `cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build && npm run i18n:check`;
browser: set `window.__m`, click footer `/` link, assert marker survives (SPA)
and `date`/scope survives in URL; assert no `github.com/parlament-deschis`
literal remains (`grep -R`).
**Rollback:** `git revert <checkpoint>` (revert deletes the new file too).
**Acceptance:** four footer links are router links, label distinct from About,
one project URL constant, no raw 404 URL in source, keys parity clean.

---

## L-04 — Preserve scope on four dashboard stat cards · agent: `frontend-developer` · wave W2

**Ownership note (supervisor S-01/N-1):** L-04 and L-05 are executed by **one
agent, in two atomic commits** (one per recipe) sharing the same gate, because
both own `LiveDashboard.tsx`. Each commit message names its own recipe ID, its
evidence anchor, the gate output and the rollback SHA. No other agent touches
this file in W2.

**Evidence:** master report §4.1 C02 F1; `LiveDashboard.tsx:140,151,162,174`;
`DashboardCard.tsx:9,81` (`searchParams?: Record<string, string>` forwarded to `<Link search>`);
`useScope.ts:69-72` returns `ScopeSearch` with possibly-undefined values.
**Exclusive file:** `frontend/src/pages/LiveDashboard.tsx`.

**Steps:**
1. After `scope` is available in the component, define a plain string map:
   ```ts
   const cardSearch: Record<string, string> = {
     date: scope.date,
     ...(scope.chamber ? { chamber: scope.chamber } : {}),
     ...(scope.legislature ? { legislature: scope.legislature } : {}),
   };
   ```
   Do **not** change `DashboardCardProps` — passing `scope.searchFor()` directly
   would introduce undefined values into a `Record<string, string>`.
2. Add `searchParams={cardSearch}` to each of the four `<DashboardCard>` usages
   at `:132`, `:143`, `:154`, `:165`.

**Checkpoint (commit 1 of 2):** after only the L-04 edit, run
`cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build`,
then commit. Browser: from `/?date=2024-06-01`, click the "Members of Parliament"
card and assert the destination URL retains `date=2024-06-01`.
**Rollback:** `git revert <L-04-checkpoint-SHA>`.
**Acceptance:** four call sites carry scope; no type errors; no prop-type change.

---

## L-05 — Wave click carries the selected wave · executed by the L-04 agent as W2 commit 2 of 2 · wave W2

**Ownership note:** this is not a separate dispatch. `LiveDashboard.tsx` has one
owner in W2 (supervisor S-01). Use `wave?.start_date` so a no-argument or
synthetic callback cannot throw (S-15).

**Evidence:** master report §4.1 C02 F2; `LiveDashboard.tsx:277` ignores its
`wave` argument; `SwitchTimeline.tsx:179-187` passes a `SwitchWaveData` with
`start_date`; copy at `i18n.ts` `deepDiveSwitchTimelineDesc` promises "select one for details".
**Exclusive file:** `frontend/src/pages/LiveDashboard.tsx`.

**Steps:**
1. Change the handler signature to `(wave) => navigate({ to: "/traseism", search: scope.searchFor({ date: wave?.start_date ?? clamped, chamber: "deputies", legislature: undefined }) })`. The optional chain covers the synthetic `{id:"all"}` wave from `SwitchTimeline.tsx:218-227` and any no-argument call.
2. Do not add new scope keys; `date` already exists in `validateScopeSearch`.
3. Keep the "View all" synthetic wave path working: its `start_date` is `null`
   (`SwitchTimeline.tsx:221`), so the `?? clamped` fallback preserves today's behaviour.

**Checkpoint (commit 2 of 2):** after the L-05 edit, re-run the same gate, then
commit. Browser: click a wave bar on the local overview and assert the URL's
`date` equals that wave's start date; click "View all" and assert the fallback
date. **Rollback:** `git revert <L-05-checkpoint-SHA>` (and, if needed, the L-04
SHA first, in reverse order).
**Acceptance:** distinct waves produce distinct dates; no hardcoded scope regression.

---

## L-06 — Pagination bounds · agent: `frontend-developer` · wave W2

**Evidence:** master report §4.1 C03 F2 / C02 F3; `Mps.tsx:12,47,204`;
`Traseism.tsx:292-313,414-426`.
**Exclusive files:** `frontend/src/pages/Mps.tsx`, `frontend/src/pages/Traseism.tsx`.

**Steps:**
1. In `Mps.tsx:47` replace `rows.length` with `PAGE_SIZE`:
   `const canNext = total !== null ? offset + PAGE_SIZE < total : false;`
2. In `Traseism.tsx`, after `totalPages` is computed at `:311`, add an effect:
   ```ts
   useEffect(() => {
     setPage((p) => Math.min(p, totalPages - 1));
   }, [totalPages]);
   ```
   Keep the existing effect at `:294-296` that resets on scope change.
3. Do not change button labels, disabled styling or API limits.

**Checkpoint:** `npm run lint && npm run build`; browser: on `/mps` with a short
last page, assert Next enables/disables at the corpus boundary; on `/traseism`
with a narrow scope, assert no empty page beyond `totalPages`.
**Rollback:** `git revert <checkpoint>`. **Acceptance:** no out-of-range page, no new query loops.

---

## L-07 — Vote title search honesty · agent: `frontend-developer` · wave W3

**Evidence:** master report §4.2 C04 F4; `Voturi.tsx:47-49,51,53,74-80,162-168,171`;
`api.py:1261-1269` has no title filter; `client.ts:560-571` has no title param.
**Exclusive files:** `frontend/src/pages/Voturi.tsx`, `frontend/src/i18n.ts`.
**i18n ownership (supervisor S-02):** L-07 is the **sole W3 i18n owner** and
adds all three W3 keys in one edit: `view.voturi.searchHint`,
`vote.positionsTruncated` (needed by L-08) and `committee.noChair` (needed by
L-09). No other W3 recipe may edit `i18n.ts`.

**Steps:**
1. Add `useEffect(() => setOffset(0), [query]);` next to the existing
   `activeKey` reset at `:47-49`. Do NOT add `query` to `queryKey` or the API call:
   the backend has no title parameter and adding one would be a backend change.
2. Keep the counter text at `:171` which already says "on this page", and add a
   short visible hint under the input using `t("view.voturi.searchHint", …)`
   stating the search filters the current page only. The key is added by the
   L-07-owned i18n edit described above.

**Checkpoint:** `cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build && npm run i18n:check`.
**Rollback:** `git revert <checkpoint>`. **Acceptance:** offset resets on typing;
label explicitly page-local; no backend change.

---

## L-08 — Vote position source links truncation · agent: `frontend-developer` · wave W3

**Evidence:** master report §4.2 C04 F3; `RollCallTable.tsx:21-27,126-130`;
`client.ts:574-582` supports `limit`/`offset`; `api.py:1387` defaults 100, max 500.
**Exclusive file:** `frontend/src/components/RollCallTable.tsx`.

**Steps:**
1. Define `const POSITION_LIMIT = 500;` with a comment citing `api.py:1387`.
2. Change `queryFn` to `api.votePositions(voteId, { limit: POSITION_LIMIT })`
   and the query key to `["votePositions", voteId, POSITION_LIMIT]`.
3. Read `const total = query.data?.total ?? 0;` and render a small visible note
   when `total > data.length` using `t("vote.positionsTruncated", …)` so the table
   never silently claims completeness. The key is added by L-07's single W3 i18n
   edit; do not edit `i18n.ts` here.
4. Do not implement full pagination in this wave — that is a separate, larger change.

**Checkpoint:** `cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build && npm run i18n:check`;
browser: open a vote with >100 positions and check more source anchors render.
**Rollback:** `git revert <checkpoint>`. **Acceptance:** bounded request, honest note, no 422.

---

## L-09 — Chair button silent no-op · agent: `minimal-change-engineer` · wave W3

**Evidence:** master report §4.2 C02 F4; `CommitteeControl.tsx:97-116`; `LiveDashboard.tsx:227`.
**Exclusive files:** `frontend/src/components/CommitteeControl.tsx`, `frontend/src/pages/LiveDashboard.tsx`.

**Steps:**
1. In `CommitteeControl`, compute `const canOpenChair = Boolean(chairForParty?.chair_person_id);`
   and set `disabled={!canOpenChair}` on the button at `:97`, with an
   `aria-label` using `t("committee.noChair", …)` when disabled. The key is added
   by L-07's single W3 i18n edit; do not edit `i18n.ts` here.
2. Keep the existing callback guard as defence in depth.

**Checkpoint:** `cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build && npm run i18n:check`.
**Rollback:** `git revert <checkpoint>`. **Acceptance:** no clickable-looking button with no action.

---

## L-10 — PartyProfile nested interactive markup · agent: `accessibility-auditor` · wave W3

**Evidence:** master report §4.2 C03 F1; `PartyProfile.tsx:176-202` button wraps
`ProvenanceStamp` → `ProvenanceStamp.tsx:46` `<a>`; `onClick` at `:178` is a
silent no-op when `m.person` is null.
**Exclusive file:** `frontend/src/pages/PartyProfile.tsx`.

**Steps:**
1. Change the outer `<button>` to a `<div>` with the same layout classes.
2. Add an inner `<button type="button" disabled={!m.person} onClick={...}>`
   wrapping only the movement text (`:181-195`).
3. Render `<ProvenanceStamp … />` as a **sibling** of that button, inside the
   div, preserving `:196-201` props.
4. Keep the `role="region"` scroll container at `:175` unchanged.

**Checkpoint:** `npm run lint && npm run build`; browser: Tab to the movement
button and the source link as separate stops; assert disabled rows are not focusable.
**Rollback:** `git revert <checkpoint>`. **Acceptance:** no nested interactive
elements, disabled state explicit, provenance link still clickable.

---

## L-11 — PartyComparison default selections · agent: `frontend-developer` · wave W3

**Evidence:** master report §4.2 C03 F5; `PartyComparison.tsx:44-47,178-202`.
**Exclusive file:** `frontend/src/pages/PartyComparison.tsx`.

**Steps:**
1. After the party list resolves, validate `partyA`/`partyB` against the
   available `short_name` values; if a default is absent, navigate once with a
   corrected value using the existing setters (`:46-47`) rather than rendering
   an empty select.
2. Guard against an infinite loop: only correct when the current value is not
   in the list and a valid candidate exists.

**Checkpoint:** `npm run lint && npm run build`.
**Rollback:** `git revert <checkpoint>`. **Acceptance:** selects always show a real party; no redirect loop.

---

## L-12 — Hemicycle seat click semantics · agent: `accessibility-auditor` · wave W4

**Evidence:** master report §4.3 C05 F1; `Hemicycle.tsx:107-120` seat `<circle>`
has `onClick`, no `role`/`tabIndex`/`onKeyDown`, inside `aria-hidden="true"`
svg; an equivalent accessible member list exists at `:129-149` with real buttons.
**Exclusive file:** `frontend/src/components/Hemicycle.tsx`.

**Decision procedure (no guesswork):**
1. Confirm by code read that every seat with a member also appears as a
   `<button>` in the member list (`:140-147`). If true, record a **NO-CHANGE**
   decision: the chart is decorative, the list is the keyboard/mouse equivalent,
   and adding hundreds of tab stops would trade one accessibility problem for a
   worse one. Add a one-line code comment pointing to the list as the accessible path.
2. If confirmation fails, make the svg non-hidden (`role="group"`, `aria-label`)
   and add `role="button" tabIndex={0} onKeyDown={activateOnKey}` using
   `utils/a11y.ts:5-12` to the seats. Do not do both.

**Checkpoint:** `npm run lint && npm run build`; keyboard probe: Tab reaches the
member list buttons. **Rollback:** `git revert <checkpoint>` if any change was made.
**Acceptance:** a documented decision with code citations; no keyboard trap.

---

## L-13 — Topuri untranslated label · agent: `minimal-change-engineer` · wave W4

**Evidence:** master report §4.3 C04 F2; `Topuri.tsx:120` literal "Minimum votes",
placeholder `"1"` at `:126`, no key in either i18n locale.
**Exclusive files:** `frontend/src/pages/Topuri.tsx`, `frontend/src/i18n.ts`.
**i18n ownership (supervisor S-02):** L-13 is the **sole W4 i18n owner** and
adds `filter.minVotes`, `filter.minVotesPlaceholder` and `common.viewAll` in one
edit. L-14 only edits component files.

**Steps:** add `filter.minVotes` to ro and en blocks near `filter.year`
(`i18n.ts:611`), replace `:120` with `t("filter.minVotes", "Minimum votes")`
and `:126` with `placeholder={t("filter.minVotesPlaceholder", "1")}` (also both locales).

**Checkpoint:** `cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run i18n:check`.
**Rollback:** `git revert <checkpoint>`. **Acceptance:** zero hardcoded English labels in this control.

---

## L-14 — "View all" literals · agent: `minimal-change-engineer` · wave W4

**Evidence:** master report §4.3 C05 F8; C-05 F8 :180 lists five occurrences, of
which three are live controls ("View all →" at `SwitchTimeline.tsx:230`,
`PartyNetwork.tsx:151`, `PartyListTable.tsx:112`); the other two are a dead
component (`PartyComparisonMatrix.tsx:86`) and a different label
(`CommitteeControl.tsx:157` "View all chairs"), both out of scope here.
**Exclusive files (supervisor S-06 — exact, no placeholders):**
`frontend/src/components/SwitchTimeline.tsx`,
`frontend/src/components/PartyNetwork.tsx`,
`frontend/src/components/PartyListTable.tsx`. `i18n.ts` is **not** in this list;
L-13 adds `common.viewAll` in W4.
**Steps:** replace each of the three literals with `t("common.viewAll", "View all →")`,
preserving classes and handlers.
**Checkpoint:** `cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build && npm run i18n:check`.
**Rollback:** `git revert <checkpoint>`. **Acceptance:** grep finds no remaining literal in the three files.

---

## L-15 — Dead controls cleanup · agent: `minimal-change-engineer` · wave W5

**Evidence:** master report §4.4; C-05 F2–F7 and C-03 F4.
**Exclusive files (supervisor S-06 — exact, no placeholders):**
`frontend/src/components/EmptyState.tsx`,
`frontend/src/components/LoadingState.tsx`,
`frontend/src/components/DashboardCard.tsx`,
`frontend/src/components/PartyComparisonMatrix.tsx`,
`frontend/src/components/TimeSlider.tsx`,
`frontend/src/components/ui/AgeDistributionSection.tsx`.
`frontend/src/i18n.ts` is **read-only in W5**: no key may be removed. L-02's
delete-keys branch was removed from the programme, so `mps.compareLink` is now
rendered and must stay (supervisor S-03/S-04).

**Steps:**
1. Re-run importer greps for each component; record the result in the wave note.
2. For components with zero importers (`PartyComparisonMatrix`, `TimeSlider`),
   delete the file **only** if the grep is still empty.
3. For unused props/branches in live components, remove the dead branch only
   after confirming every call site (e.g. all four `DashboardCard` callers pass
   `linkTo`; all `EmptyState` callers omit `onCta`).
4. Do not remove `mps.compareLink` keys — L-02 now uses them.

**Checkpoint:** `cd /home/nedaktov/parlament-deschis/frontend && npm run lint && npm run build && npm run i18n:check`;
`grep -R` for each deleted symbol returns no source match.
**Rollback:** `git revert <checkpoint>`. **Acceptance:** no importer broken, no live control removed.

---

## L-16 — Regression guards · agent: `qa-reviewer` · wave W6

**Evidence:** master report §4.5; C-07 G1–G6; `check_routes_nav.mjs:10`;
`ui_state_probe.py:84,95`; `ci.yml:130,136,138`.
**Exclusive files:** `scripts/check_routes_nav.mjs`, `scripts/ui_state_probe.py`.

**Steps:**
1. Extend `check_routes_nav.mjs` with **all three** source patterns required by
   C-07 G1 (supervisor S-13): `<NavLink to="…">` (existing at `:10`), literal
   `to="…"` / `<Link to="…">`, `navigate({ to: "…" })`, and internal native
   anchors `href="/…"` so a future footer regression is caught. Use the same
   route-normalisation and whitelist, keep the exit-code contract (0 = every
   route reachable, 1 = unlinked), and record the pre/post `nav_links` count.
2. Add a click assertion to `ui_state_probe.py` for the retry button using the
   existing selector at `:84,95` (click, then assert a network request or state
   change) so "presence only" is no longer the whole check.
3. Do not edit CI workflows; document that `ui_validate.py` remains skipped there.

**Checkpoint:** `node scripts/check_routes_nav.mjs` exit 0 with a higher
`nav_links` count; `python3 scripts/ui_state_probe.py` exit 0 if runnable,
otherwise record AMBER/NOT PROVEN with the resolver.
**Rollback:** `git revert <checkpoint>`. **Acceptance:** guards still green, no false positives.

---

## L-17 — Integration and hand-off · agent: `git-master` · wave W7

**Objective.** Replay all gates, integrate Green waves into `repair/links-base`,
push only repair branches, and prepare an owner decision note. **Files:** none.
**Steps:**
1. Re-run every wave gate command on the integrated branch.
2. `git checkout repair/links-base && git merge --ff-only repair/links-wN` for
   each GREEN wave in order; never merge a RED or unsupervized wave.
3. Push `repair/links-base` and each GREEN wave branch to origin. Do not push to
   `main`, open a merge PR, deploy, or change branch protection.
4. Record the final verification table and the owner-only next step in the vault.

**Checkpoint:** all gate outputs recorded; `git log --oneline` shows only additive commits.
**Rollback:** `git revert <merge-or-checkpoint-sha>`; bundles remain in `/tmp/opencode/backups/link-repair/`.
**Acceptance:** owner decision note exists; main and production untouched by this programme.

---

## Shared side-quest policy

No recipe may: change data or release pins; edit workflows, Dockerfiles, render
or Vercel config; change branch protection; add dependencies; reformat unrelated
code; rename files beyond its exclusive list; or claim browser/axe/network
facts it did not actually observe. Any such need becomes a new recipe after
supervisor approval.

## See also

[LINK-REPAIR-STRATEGY](LINK-REPAIR-STRATEGY-2026-11-22.md) ·
[LINK-REPAIR-SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) ·
[CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md)
