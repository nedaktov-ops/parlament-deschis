---
id: CLICK-VALIDATION-FLEET
type: runbook
title: "Ten-agent clickable validation fleet plan (2026-11-23)"
description: "Plan for a ten-agent Playwright fleet that validates the functionality of all 258 inventoried clickables across 24 routes on the merged code; agent slices, exclusive files, test contract, two-batch concurrency, gates, verdicts and vault write-back."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/frontend]
source_paths: [40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md, 40-FRONTEND/CLICK-INV-C01-SHELL-2026-11-22.md, 40-FRONTEND/CLICK-INV-C02-OVERVIEW-2026-11-22.md, 40-FRONTEND/CLICK-INV-C03-ENTITIES-2026-11-22.md, 40-FRONTEND/CLICK-INV-C04-VOTES-2026-11-22.md, 40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md, 40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md, 40-FRONTEND/CLICK-INV-C07-HARNESS-2026-11-22.md, scripts/ui_validate.py]
source_commit: 863b200e1adc70aadb289fdd4df52a7e5be2c483
created: 2026-11-23
updated: 2026-11-23
---

# Ten-agent clickable validation fleet plan (2026-11-23)

## 1. Objective and scope

**Objective.** Validate the **functionality** of every clickable element
inventoried on 2026-11-22 — **258 elements** from
[C-01](../40-FRONTEND/CLICK-INV-C01-SHELL-2026-11-22.md) (61),
[C-02](../40-FRONTEND/CLICK-INV-C02-OVERVIEW-2026-11-22.md) (58),
[C-03](../40-FRONTEND/CLICK-INV-C03-ENTITIES-2026-11-22.md) (51),
[C-04](../40-FRONTEND/CLICK-INV-C04-VOTES-2026-11-22.md) (26) and
[C-05](../40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md) (62), per the
[master report](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) §2 — across
**all 24 routes** in `scripts/ui_validate.py:47-75`, plus the C-06 destination
index (100 route/API/URL targets) and the C-07 harness cross-check (6 checks).

**Code under test.** The merged, production-bound code at source commit
`863b200e1adc70aadb289fdd4df52a7e5be2c483` (owner rollout / PR merge recorded
in [OWNER-ROLLOUT](../60-EVIDENCE/OWNER-ROLLOUT-2026-11-23.md)), served by a
single read-only local dev server at `http://127.0.0.1:5188`. The local
integration branch may be ahead by vault-only commits; the lead must record the
exact served HEAD at fleet entry and re-run if it differs from the source
commit. This is **not** a production host: a local PASS is not a production
claim ([AGENTS](../00-START/AGENTS.md) NEVER). The fleet runs against post-repair
code, so some inventory verdicts are stale; that is expected.

**This is validation, not repair.** Every agent observes and records. A FAIL is
a **finding** with evidence — never an automatic fix, never a new recipe, never
a product-code edit. Fixing a finding requires a separate, approved recipe under
the [shared side-quest policy](LINK-REPAIR-RECIPES-2026-11-22.md) and the
[consistency methodology](LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md) §2/§3.
No agent changes product code, data, config, workflows, git state or vault
notes; only the lead writes the vault reports and commits them.

## 2. Ten specialised agents (V-01…V-10)

The element-ID partition below covers **each of the 258 IDs exactly once**.
Routes may overlap between agents (the shell and cross-cutting checks appear on
every route); **exclusive files may not**. Test-file and result-path prefixes
`vNN-` make file ownership disjoint by construction.

| ID | Speciality | Exact slice (components/routes; element IDs) | Exclusive test file | Exclusive result paths | "Functionality validated" means |
|---|---|---|---|---|---|
| **V-01** | Shell, navigation, footer, modals | `frontend/src/router.tsx`, `Footer.tsx`, `About.tsx`, `HeaderLogo.tsx`, `ui/ThemeToggle.tsx`, `ui/DashboardHeader.tsx`, `ErrorState.tsx`, `LoadingState.tsx`, `EmptyState.tsx`, `RetryButton.tsx`; all 24 routes | `tests/frontend_click/test_v01_shell.py` | `/tmp/opencode/click-validation/v01-results.json`, `v01-console.json`, `v01-shot-*.png` | **C01-001…061**: each nav/footer link lands on the expected route with scope preserved; language and theme toggles change `lang`/`data-theme`; dialogs open, trap focus, close on Escape/backdrop/close button; not-found and error recovery return to `/`. |
| **V-02** | Overview dashboard | `frontend/src/pages/LiveDashboard.tsx`, `DashboardCard.tsx`, `LegislatureSeatExplorer.tsx`, `ChamberView.tsx`, `LiveFeed.tsx`; route `/` | `tests/frontend_click/test_v02_overview.py` | `v02-results.json`, `v02-console.json`, `v02-shot-*.png` | **C02-001…020**: four stat cards navigate with scope; legislature slider, seat/member/party clicks, "View all", chair control and feed rows produce the expected URL/title or state change; retries fire a request. |
| **V-03** | Traseism and switch ledger | `frontend/src/pages/Traseism.tsx`, `SankeyFlow.tsx`, `SwitchTimeline.tsx`, `About.tsx` mount; route `/traseism` | `tests/frontend_click/test_v03_traseism.py` | `v03-results.json`, `v03-console.json`, `v03-shot-*.png` | **C02-021…039**: chamber/legislature scope stays on route; pagination and all sortable headers change rows/order; methodology link and About modal open; retry fires a request; wave rects and "View all" navigate with the wave date. |
| **V-04** | Party pages | `frontend/src/pages/Parties.tsx`, `PartyProfile.tsx`, `PartyTimeline.tsx`, `PartyComparison.tsx`, `Coalitions.tsx`, `ScopeControls.tsx`; routes `/parties`, `/party/PSD`, `/party-timeline`, `/compare`, `/coalitions` | `tests/frontend_click/test_v04_parties.py` | `v04-results.json`, `v04-console.json`, `v04-shot-*.png` | **C03-001…014, C03-038…040**: party row keyboard/mouse navigation, Wikidata anchor, movement row/drawer, timeline and comparison "view all", party selectors, and shared ScopeControls persist URL state. |
| **V-05** | MP, person and demographics pages | `frontend/src/pages/Mps.tsx`, `MpComparison.tsx`, `Demographics.tsx`, `PersonDeepDive.tsx`, `PersonDrawer.tsx`, `CitationPopover.tsx`, `ProvenanceStamp.tsx`; routes `/mps`, `/compare-mps`, `/person/$id`, `/demographics` | `tests/frontend_click/test_v05_mps_person.py` | `v05-results.json`, `v05-console.json`, `v05-shot-*.png` | **C03-022…037, C03-041…051**: search/sort/submit/pagination, compare slots, person links, citation toggle and provenance/source anchors produce the expected URL, drawer/popover state or request; disabled rows are genuinely disabled. |
| **V-06** | Committees, institutional, legislature, senate, coverage | `frontend/src/pages/Committees.tsx`, `InstitutionalView.tsx`, `LegislatureDetail.tsx`, `SenateHistory.tsx`, `CoverageView.tsx`, `TimelineChart.tsx`, `CommitteeControl.tsx`; routes `/committees`, `/institutional`, `/legislature/2024`, `/senate-history`, `/coverage` | `tests/frontend_click/test_v06_institutional.py` | `v06-results.json`, `v06-console.json`, `v06-shot-*.png` | **C03-015…021, C02-040…058**: committee expand/member links, native `<details>`, date/chamber/legislature inputs, movement-row navigation, all retries and coverage scope filters change state or fire a request. |
| **V-07** | Votes list and roll-call | `frontend/src/pages/Voturi.tsx`, `RollCallTable.tsx`; route `/Voturi` | `tests/frontend_click/test_v07_votes.py` | `v07-results.json`, `v07-console.json`, `v07-shot-*.png` | **C04-001…014**: scope probe, page-local title search, vote selection and back link, both paginations, source anchors, detail provenance and both retries produce the expected URL, visible text or request; truncation disclosure is observed, not assumed. |
| **V-08** | Vote analytics and report | `frontend/src/pages/Radar.tsx`, `Grafice.tsx`, `Topuri.tsx`, `Ideology.tsx`, `Report.tsx`, `VoteActivityChart.tsx`; routes `/radar`, `/grafice`, `/topuri`, `/ideology`, `/report` | `tests/frontend_click/test_v08_analytics.py` | `v08-results.json`, `v08-console.json`, `v08-shot-*.png` | **C04-015…026**: retries, min-votes filter, paginations, the ideology year selector (all-years must show all waves), print invocation and JSON download all produce the expected state/URL/request; no console error from chart chunks. |
| **V-09** | Charts and interactive primitives | `frontend/src/components/{Search,PersonDrawer,CitationPopover,ProvenanceStamp,RetryButton,DashboardCard,Hemicycle,SankeyFlow,SwitchTimeline,PartyNetwork,PartyListTable,CommitteeControl,LegislatureSeatExplorer,VoteActivityChart,TimelineChart,CrossChamberFlow,DataQualityGauge}.tsx`, `ui/AsyncState.tsx`, `ui/AgeDistributionSection.tsx`, `ui/ThemeToggle.tsx`; chart-bearing routes | `tests/frontend_click/test_v09_primitives.py` | `v09-results.json`, `v09-console.json`, `v09-shot-*.png` | **C05-001…016, 018, 020…021, 023…036, 040…042, 045…056, 058…059, 061…062** (52 IDs): each native or `role="button"` control is actually clicked/keypressed and the expected selection, navigation or refetch is observed; scroll regions and `<details>` behave as disclosures; SVG hovers/tooltips do not error. |
| **V-10** | Dead-control reconciliation, external URLs, API exports, keyboard/AT cross-check | `frontend/src/api/client.ts`, `config/links.ts`, all external-anchor hosts, `scripts/check_routes_nav.mjs`, `scripts/ui_state_probe.py`; all 24 routes | `tests/frontend_click/test_v10_crosscut.py` | `v10-results.json`, `v10-console.json`, `v10-shot-*.png` | **C05-017, 019, 022, 037…039, 043…044, 057, 060** (10 dead IDs) plus **C06 100 targets** and **C07 6 checks**: removed/dead controls are confirmed absent or documented with a resolver; every route/API/export target responds; every external anchor has a safe shape; keyboard traversal reaches every live interactive control. |

**Reconciliation:** 61+20+19+17+27+26+14+12+52+10 = **258** inventory IDs.
C-06's 100 targets and C-07's 6 checks are tracked in V-10's result JSON as a
separate `targets` and `checks` list, not added to the 258.

## 3. Test contract

Every agent writes **exactly one** Playwright pytest file at the exclusive path
above. The pattern follows `scripts/ui_validate.py:78-133,136-157`:

1. **Target** `BASE = "http://127.0.0.1:5188"` (no production URL, no guessed
   host). Resolve data-driven IDs from the live API as
   `ui_validate.py:30-45` does (`/api/mps?limit=1` → first person ID); never
   hard-code a UUID that changes with a data release.
2. **Browser lifecycle per file:** use `async_playwright()` →
   `pw.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])`
   in a fixture; `page = await browser.new_page()`; attach `console` (errors)
   and `pageerror` listeners exactly as at `ui_validate.py:82-90`; navigate with
   `wait_until="load"`, then `networkidle` (bounded) and a short settle
   (`ui_validate.py:94-103`); `await page.close()` and `await browser.close()` in
   a `finally` block so an assertion failure cannot leak a browser process.
   Install nothing: system `python3` with Playwright and the Chromium binary
   are the runtime (`ui_validate.py:13-14`); adding an npm dependency would
   change the lockfile and is forbidden.
3. **Per-element assertion.** For every assigned ID, perform the action and
   assert one observable outcome: URL/title change, expected visible text, a
   fired request (`expect_request`), a state transition (`data-state`, dialog,
   drawer, expanded row), or an explicitly disabled/designed no-op. A bare
   "element exists" assertion is **not** functionality validated; that is the
   C07-003 gap this fleet exists to close.
4. **Result row schema** — each row in `vNN-results.json` carries:
   `element_id`, `source_file_line`, `action`, `expected_outcome`,
   `observed_outcome`, `status` (`PASS`/`FAIL`/`SKIP`), `evidence_path`.
   `evidence_path` names a raw artifact under `/tmp/opencode/click-validation/vNN-*`
   (JSON capture or screenshot); prose alone is not evidence.
5. **SKIP discipline.** A SKIP requires a `resolver` field naming what must
   happen to close it (e.g. "data-dependent ID — rerun with a live payload" or
   "browser unavailable — rerun on local dev"). A SKIP is **never** converted
   to PASS; it is counted separately in the verdict and in the master report.
   Failures are findings only — no agent edits code in response to a FAIL.

## 4. Concurrency and safety rules

- **Two batches of five:** Batch A = V-01…V-05; Batch B = V-06…V-10. The lead
  starts a batch only after the previous batch's browsers have closed and its
  result JSON has been validated. No more than five Chromium instances at
  once; one browser per agent, sequential pages within an agent.
- **Disjoint exclusive files:** each agent owns one test file and the
  `vNN-*` result prefix only. No two agents may own the same file. **RED** if a
  path is shared, if an agent writes outside its two path sets, or if an agent
  touches product code, vault notes, data, config, workflows, git state,
  `_generated/*` or the lockfile.
- **No agent commits, stages or pushes.** The lead owns `git add`, commits,
  aggregation, gates and vault write-back. Agents return their JSON and a short
  report; they do not edit the journey or evidence notes.
- **Local dev server is read-only.** Agents only open pages and fire requests
  the UI already makes. No seeding, no data mutation, no API writes, no
  deployment and no production navigation.
- **Console errors are findings.** Any captured `console.error` or `pageerror`
  is recorded with the element ID and a raw capture; no agent suppresses or
  filters it away to obtain a PASS.
- **Known environmental risks** (record, do not paper over): five concurrent
  browsers plus a shared API can slow queries and cause false timeouts — use
  generous timeouts, bounded `networkidle` and a fixed settle as in
  `ui_validate.py:94-103`; `/tmp/axe.min.js` is external and untracked
  (`ui_validate.py:27`) — if absent, record AMBER/NOT PROVEN with a resolver;
  C-05 dead IDs removed by W11 must be reconciled as designed-absent, not
  counted as click failures.

## 5. Gates and verdict conditions

Run by the lead after each batch and once for the fleet:

```bash
cd /home/nedaktov/parlament-deschis
python3 -m pytest tests/frontend_click/ -q
python3 - <<'PY'
import json, pathlib
for p in sorted(pathlib.Path('/tmp/opencode/click-validation').glob('v*-results.json')):
    rows = json.loads(p.read_text(encoding='utf-8'))
    assert isinstance(rows, list) and all(
        {'element_id','source_file_line','action','expected_outcome',
         'observed_outcome','status','evidence_path'} <= set(r) for r in rows), p
    print(p.name, len(rows), 'rows')
PY
python3 scripts/vault_lint.py
python3 scripts/vault_sync.py --check
bash scripts/check-doc-truth.sh
git diff --check
```

Gate conditions:

- **pytest exit 0** for all ten files; a non-zero exit is a finding that must be
  triaged (FAIL vs harness error) before any verdict.
- **All ten result JSON files valid** and schema-conformant; each raw
  `evidence_path` exists.
- **Zero console errors** across all browser captures (`console.error` and
  `pageerror`), per `ui_validate.py:82-90,145-176`.
- **Element-count reconciliation:** every inventory ID from C-01…C-05 appears
  exactly once across the ten result files with a status of PASS, FAIL or SKIP;
  the master report prints 258 accounted IDs (plus 100 C-06 targets and 6 C-07
  checks in V-10). A missing or duplicated ID is RED, not a pass.
- **Four vault gates** exit 0; `_generated/*` regenerated, never hand-edited;
  no banned literal string in any vault note (describe categories only, per
  [MAINTENANCE-PROTOCOL](../00-START/MAINTENANCE-PROTOCOL.md) §6).

Verdicts, using [SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) §C/§D/§E:

- **GREEN** when all gates exit 0, the count reconciles to 258, zero console
  errors, every exclusive file respected, and every FAIL/SKIP has a cited
  finding/resolver (a FAIL does not by itself make the fleet RED — it is a
  validated finding, provided the validation itself was sound).
- **AMBER / HOLD** when a browser item could not be observed or a data-dependent
  ID could not be resolved: mark item-scoped SKIP/AMBER with a named resolver
  (§C A2/A5), never PASS.
- **RED / STOP** when two agents share a path, an out-of-list file changes, an
  agent commits or edits the vault, a required gate is unrun or exits non-zero
  (A1/R4), an element ID is dropped or duplicated, a console error is hidden,
  or any push/merge/deploy occurs.

The supervisor issues **one verdict per agent** (V-01…V-10) with citations plus
**one fleet verdict**. Integration is `--ff-only` into `repair/links-base` only
on GREEN; `main`, PR and deploy remain owner gates.

## 6. Vault write-back

- One master report: `60-EVIDENCE/CLICK-VALIDATION-FLEET-2026-11-23.md` — counts,
  per-agent verdicts, all FAIL/SKIP findings with resolvers, gate outputs and
  the 258-ID reconciliation table.
- Ten per-agent evidence notes: `60-EVIDENCE/CLICK-VALIDATION-V01-2026-11-23.md`
  … `60-EVIDENCE/CLICK-VALIDATION-V10-2026-11-23.md`, each citing its result
  JSON and raw artifacts, with separate **Code evidence** and **Browser
  evidence** subsections ([consistency methodology](LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md) §2 row 8).
- A **W13** section in [JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md)
  recording entry identity, backup, batch order, gate outputs, verdicts and the
  supervisor fleet sign-off (§F template). W13 does not merge to `main` or
  deploy.
- Every evidence note must be linked from the master report so none is an
  orphan; relative Markdown links only; bump `updated` on every changed note.

## See also

[CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) ·
[CONSISTENCY-STEPS](LINK-REPAIR-CONSISTENCY-STEPS-2026-11-22.md) ·
[SUPERVISION](LINK-REPAIR-SUPERVISION-2026-11-22.md) ·
[RECIPES](LINK-REPAIR-RECIPES-2026-11-22.md) ·
[JOURNEY](../50-RESEARCH/LINK-REPAIR-JOURNEY-2026-11-22.md)
