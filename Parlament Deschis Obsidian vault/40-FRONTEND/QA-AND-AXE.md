---
id: QA-AND-AXE
type: state
title: "UI validation and accessibility state"
description: "Observed QA state at 6fd6028: 24-route ui_validate gate, local pass versus live failure, absent axe baseline, warning debt and empty design assets."
status: active
authority: mirror
tags: [type/state, lifecycle/active, domain/frontend]
source_paths: [frontend/docs/design/qa-notes.md, scripts/ui_validate.py, docs/DASHBOARD-VERIFICATION.md, docs/POST-INITIAL-AUDIT-2026-11-21.md, docs/COMPREHENSIVE-REVIEW-2026-11-21.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# QA and axe — observed state

Scope: the frontend QA gate as it stands at `6fd6028`. Design intent is in
[DESIGN-CONTRACT](DESIGN-CONTRACT.md); stack/token facts are in
[STACK-AND-TOKENS](STACK-AND-TOKENS.md). Evidence snapshots live in
[AUDIT-2026-11-21](../60-EVIDENCE/AUDIT-2026-11-21.md) and
[DASHBOARD-VERIFICATION-2026-11-19](../60-EVIDENCE/DASHBOARD-VERIFICATION-2026-11-19.md).

> **Scope rule:** local green is not production green. The local backend and
> the live proxy are separate scopes with different results.

## The gate: `scripts/ui_validate.py`

`ui_validate.py` is a pre-merge Playwright gate. For each of its **24 routes**
it requires: the page loads with real body text (no error boundary), zero
JavaScript errors (`console.error` and uncaught `pageerror` are both captured),
and an axe-core scan with zero violations. It prints a per-route table and
exits non-zero on any finding. The route list is the original 18 plus six added
later: `/parties`, `/Voturi`, `/radar`, `/grafice`, `/topuri`, `/ideology`.

| Target | Result | Detail |
|---|---|---|
| Local backend / integrated tree | **24/24 PASS** | zero JavaScript errors, zero axe findings |
| Live Vercel proxy | **23/24 FAIL** | the canonical `/ideology` route 404s on the live proxy; the other 23 routes pass |

The local result is proven for the repository. The live result reflects a
deployment lag: the fixes that added the canonical routes are in unpushed local
commits (`6fd6028` unpushed; `origin/main` is `6b848f1`), and the live bundle
hash differs from the local build. Production therefore remains **NOT PROVEN**
as a green scope — the same caution the dated dashboard-verification addendum
raises for its own audit.

## No axe baseline exists

- `frontend/docs/design/qa-notes.md:41` states plainly that **Playwright +
  axe (axe-core) integration is "not configured in this repo yet (TBD)"**.
  There is no committed config, route list with thresholds, or stored baseline
  in the design docs.
- `ui_validate.py` does invoke axe at runtime by injecting
  `/tmp/axe.min.js` (axe-core 4.10.2) into each page — an external, untracked
  file — so the *check* can run locally, but there is still **no axe baseline
  artifact** to compare against and no CI-configured accessibility gate.
- Manual Tier A checks (keyboard order, visible `:focus-visible`, contrast on
  `ink`/`panel`, 200% reflow) remain the documented interim method. Earlier
  live observations of a few moderate findings are historical, not a baseline.

## Other QA observations

- **Lint:** `npm run lint` reports **0 errors, 7 pre-existing
  `react-hooks/exhaustive-deps` warnings** (in `AgeDistributionRadial.tsx`,
  `TimelineChart.tsx`, `CoverageView.tsx`, `MpComparison.tsx`,
  `PartyTimeline.tsx`). `npm run build` succeeds.
- **No unit-test runner:** there is no `vitest` dependency and **no `npm test`
  script** in `frontend/package.json`. Any doc that names `npm test` as a gate
  is wrong. Python-side checks (`pytest`, `ruff`) are a separate scope.
- **Wireframes:** `frontend/docs/design/wireframes/` contains **only four text
  notes** — `README.md` plus three 2026-11-20 low-fidelity notes (`mps`,
  `livedashboard_section1`, `report_header_hero`). There are **no image
  exports**.
- **Asset manifest:** `frontend/docs/design/asset-manifest.md` has only a
  template table and a "details TBD" note about `public/favicon.svg`. It is
  effectively **empty**; no licensed asset inventory exists yet.

## Consequence for design work

Presentation-only changes can still be checked with `npm run lint`,
`npm run build` and the local `ui_validate.py` run. Claims about accessibility
"passing" must name the scope (local vs live) and the fact that no axe baseline
or committed a11y config exists. See
[QA evidence notes](../60-EVIDENCE/DASHBOARD-VERIFICATION-2026-11-19.md) for the
dated, scope-limited verification record.
