---
id: CLICK-INVESTIGATION-JOURNEY
type: research
title: "Clickable-element investigation — journey log (2026-11-22)"
description: "Wave-by-wave log of the seven-recipe fleet investigation into every front-end button, link and click handler, including recipe contracts, verification passes, browser observations and vault write-backs."
status: active
authority: canonical
tags: [type/research, lifecycle/active, domain/frontend]
source_paths: [frontend/src, backend/routers, scripts/ui_validate.py]
created: 2026-11-22
updated: 2026-11-22
source_commit: 8811216
---

# Clickable-element investigation — journey log

**Purpose.** Produce an evidence-only inventory of every clickable element in
the Parlament Deschis front end, for a later repair phase. No claim is admitted
without a code citation. No assumptions, guesswork or presumptions are allowed.
Journey is recorded at each phase, in this vault.

**Governing rules.** [AGENTS](../00-START/AGENTS.md) ·
[MAINTENANCE-PROTOCOL](../00-START/MAINTENANCE-PROTOCOL.md) ·
[SOURCE-MAP](../00-START/SOURCE-MAP.md). Final report:
[CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md).

## Phase 0 — grounding

Recorded before any agent was dispatched, at local HEAD `8811216` (clean
working tree, branch `main`). Observable facts, each with a code source:

| Grounding fact | Code evidence |
|---|---|
| Front end is a TanStack Router SPA with 24 registered routes | `frontend/src/router.tsx` lines 519–544 (`routeTree.addChildren([...])`); `createRouter` at line 570 |
| Shared chrome holds 2 nav bars, footer, About modal, language toggle, search | `frontend/src/router.tsx` lines 229–332 (`RootLayout`) |
| Route set includes one uppercase path `/Voturi` and a redirect `/electoral` → `/traseism` | `frontend/src/router.tsx` lines 484–489 and 348–362 |
| Existing 23-page audit flags dead/orphan UI but does not inventory clickables | vault [FRONTEND-AUDIT](../40-FRONTEND/FRONTEND-AUDIT-2026-11-21.md) §2 X5, §3 |
| Automated clickable-related checks exist (`check_routes_nav.mjs`, `ui_validate.py`) | `scripts/check_routes_nav.mjs`; `scripts/ui_validate.py` |
| Browser has a local dev page (`http://127.0.0.1:5188`) and the Vercel page open | chrome-devtools `list_pages` observed this session; supplementary only |
| Backend has a dedicated export router (`/api/export`) | `backend/routers/exports.py` line 25 (`APIRouter(prefix="/api/export")`) |

## Phase 1 — fleet dispatch and return

Seven bespoke "recipe" agents were dispatched in parallel, each with one slice
of the tree, one output note and the same evidence contract: exact `file:line`,
verbatim label/i18n definition, traced destination or handler chain,
classification, a short code quote, a verdict of `WORKING-AS-CODED` /
`BROKEN` / `SUSPECT` / `NOT PROVEN` with a code-grounded reason, a named
resolver for anything unverifiable, and a concrete improvement anchored at
`file:line`. They were read-only: no code, data, config or git state changed.

| Recipe | Agent speciality | Slice | Output note | Returned |
|---|---|---|---|---|
| C-01 | code review | shell, router, nav, footer, modals | [C01 SHELL](../40-FRONTEND/CLICK-INV-C01-SHELL-2026-11-22.md) | 61 elements, 0 broken, 5 suspect, 6 not proven |
| C-02 | front end | overview, traseism, scope pages | [C02 OVERVIEW](../40-FRONTEND/CLICK-INV-C02-OVERVIEW-2026-11-22.md) | 58 elements, 0 broken, 7 suspect, 1 not proven |
| C-03 | front end | party / MP / committee / person pages | [C03 ENTITIES](../40-FRONTEND/CLICK-INV-C03-ENTITIES-2026-11-22.md) | 51 elements, 1 broken, 5 suspect, 4 not proven |
| C-04 | front end | vote-analytics pages | [C04 VOTES](../40-FRONTEND/CLICK-INV-C04-VOTES-2026-11-22.md) | 26 elements, 1 broken, 3 suspect |
| C-05 | accessibility | shared interactive components | [C05 COMPONENTS](../40-FRONTEND/CLICK-INV-C05-COMPONENTS-2026-11-22.md) | 62 elements, 1 suspect, 1 not proven, 6 dead controls |
| C-06 | API testing | routes, endpoints, external URLs | [C06 DESTINATIONS](../40-FRONTEND/CLICK-INV-C06-DESTINATIONS-2026-11-22.md) | 100 targets, 0 unmatched, 4 suspect, 7 not proven |
| C-07 | QA review | existing checks and known defects | [C07 HARNESS](../40-FRONTEND/CLICK-INV-C07-HARNESS-2026-11-22.md) | 6 checks, 2 clickable-related, 6 gaps |

**Wave gate 1:** all seven notes written, all frontmatter valid,
`python3 scripts/vault_lint.py` green. The recipe contracts were honoured — no
agent edited generated files, code or config.

## Phase 2 — verification and browser pass

Independent re-read of the highest-severity claims before any was promoted:

- Ideology `""` → `undefined` → `years[0]` → single-year filter confirmed at
  `Ideology.tsx:250,80,84` and `router.tsx:553`.
- `mps.compareLink` confirmed to have only two i18n definitions and zero render
  sites by direct grep (`i18n.ts:520,1266`).
- Footer native anchors confirmed at `Footer.tsx:65,73,81,123`; browser marker
  test showed context destruction and marker loss on click.
- `Hemicycle.tsx:107-120` seat circle confirmed to have `onClick` but no
  keyboard semantics; the keyboard path is the separate member list at `:142`.
- `PartyProfile.tsx:177-202` button wrapping `ProvenanceStamp`'s `<a>`
  (`ProvenanceStamp.tsx:46`) confirmed as nested interactive markup.
- `LiveDashboard.tsx:140,151,162,174` confirmed to omit `searchParams`;
  `DashboardCard.tsx:81` confirms the `search` prop is simply forwarded.
- `Mps.tsx:47` `rows.length` bound and `Voturi.tsx:51,74-80` local filter
  confirmed.

Browser results were written to
[CLICK-BROWSER-OBSERVATIONS](../60-EVIDENCE/CLICK-BROWSER-OBSERVATIONS-2026-11-22.md)
with scope, raw capture paths and limits. One false lead (an anomalous nav
click during viewport emulation) was reproduced cleanly and **discarded** — it
is recorded, not claimed as a defect. Production `/ideology` never finished
loading (zero selects), so that control's production behaviour stays NOT PROVEN.

**Wave gate 2:** every BROKEN verdict has both a code chain and, where the
environment allowed it, a browser corroboration; no NOT PROVEN item was
promoted.

## Phase 3 — synthesis and hand-off

[CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) now
contains the consolidated inventory (258 elements), the two BROKEN items, the
deduplicated SUSPECT list grouped by repair theme, the dead-control list, the
verified-correct list, the NOT PROVEN register and an ordered repair hand-off.
This investigation made **no repairs**; the report is the input to that phase.

**Wave gate 3:** `python3 scripts/vault_sync.py --check`,
`python3 scripts/vault_lint.py`, the project doc-truth gate and
`git diff --check` were run after the write-back (see the final session report
for their output). No code was changed, only vault notes.

## See also

[CLICK-INVESTIGATION](../40-FRONTEND/CLICK-INVESTIGATION-2026-11-22.md) ·
[FRONTEND-AUDIT](../40-FRONTEND/FRONTEND-AUDIT-2026-11-21.md) ·
[RESEARCH-FLEET](RESEARCH-FLEET-2026-11-21.md)
