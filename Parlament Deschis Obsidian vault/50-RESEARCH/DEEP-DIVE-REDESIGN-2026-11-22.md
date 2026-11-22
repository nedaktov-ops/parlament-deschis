---
id: DEEP-DIVE-REDESIGN-2026-11-22
type: research
title: "Deep Dive Views redesign — progress and next steps"
description: "Supervised fleet redesign of the overview 'Vederi detaliate' section: research, implementation, QA fixes, verification evidence, and upcoming work."
status: active
authority: derived
tags: [type/research, lifecycle/active, domain/frontend]
source_paths: [frontend/src/pages/LiveDashboard.tsx, frontend/src/components/PartyNetwork.tsx, frontend/src/components/SwitchTimeline.tsx, frontend/src/components/CrossChamberFlow.tsx, frontend/src/components/LiveFeed.tsx, frontend/src/i18n.ts]
created: 2026-11-22
updated: 2026-11-22
source_commit: 618849a
---

# Deep Dive Views redesign — 2026-11-22

Companion research: [GITHUB-TOOLING-INVENTORY-2026-11-22](GITHUB-TOOLING-INVENTORY-2026-11-22.md),
[RESEARCH-LOG](RESEARCH-LOG.md), and the frontend audits in
[TRIAD-AUDIT-2026-11-21](../40-FRONTEND/TRIAD-AUDIT-2026-11-21.md) and
[FRONTEND-AUDIT-2026-11-21](../40-FRONTEND/FRONTEND-AUDIT-2026-11-21.md).

## Problem and evidence

The overview page section `deepDiveViews` ("Vederi detaliate") rendered four
widgets in `lg:grid-cols-4` at roughly 240px per card. Preview screenshots
showed 3–4px effective SVG labels and no explanation of what each chart asked.
Git history (`731a3c0`, `92e941b`, `2ebb24a`, `479f551`) shows the section was
born in the "zero wasted vertical space" redesign; `AgeDistributionRadial` was
removed as misleading, and `LiveFeed` was added later without a label.

## Supervised fleet (this session)

| Role | Purpose | Outcome |
|---|---|---|
| Supervisor (agents-orchestrator) | Scope, exclusive file ownership, gates, stop conditions | Plan accepted; no edits |
| Historian (explore) | Trace all git versions of the section | Reported introduction, every modification, and removed visuals |
| Vault researcher (general) | Mine 50-RESEARCH and 40-FRONTEND notes | No charting library in the saved inventory; design-contract and audit constraints extracted |
| UX architect | Build-ready layout and copy proposal | 12-column responsive grid, per-widget purpose statements |
| Widget agent A (frontend-developer) | `PartyNetwork.tsx`, `SwitchTimeline.tsx` | Larger labels, native buttons, honest empty state |
| Widget agent B (frontend-developer) | `CrossChamberFlow.tsx`, `LiveFeed.tsx` | Removed misleading bars, per-person buttons, scope-aware feed |
| QA reviewer | Read-only adversarial browser audit | Six findings; all addressed before sign-off (see below) |

The main agent owned `LiveDashboard.tsx` and `i18n.ts`; ownership was exclusive
so no two agents wrote the same file. No git state was changed and no commit was
made — the working tree already contained extensive staged user work.

## Progress made — VERIFIED

- Section 4 is now a labelled 12-column responsive grid: H2 "Vederi detaliate"
  plus a purpose subtitle, four per-widget explanations, and two rows
  (7/5, 5/7 column spans).
- Widget cards are capped at 440px so internal scroll regions work; the
  previous 2018px/2560px runaway cards are gone.
- `SwitchTimeline` uses a 480-unit canvas, 14px labels, and every other
  legislature tick — measured ≥22px spacing, no overlap.
- `PartyNetwork` renders 12px HTML labels and real `type="button"` nodes;
  the misleading "Edges: 0" footer was removed.
- `CrossChamberFlow` no longer sends every click to `data[0]`; each MP has its
  own button, and its own honest empty state is now visible.
- `LiveFeed` uses real route scope instead of hardcoded `2024`/`senate`,
  scrolls inside its card, and wraps its mobile header cleanly.
- Copy no longer claims date scoping for the two widgets that use the whole
  corpus (`/parties`, `switchWaves`); it says so explicitly.
- QA's six findings (axis overlap, runaway heights, false scope copy, wrong
  empty state, mobile header overflow, broken heading hierarchy) were fixed
  and re-checked in the browser.
- Gates: `npm run lint` 0, `npm run i18n:check` 724/724 clean,
  `npm run build` exit 0, `pytest -q` 431 passed (before the final copy edits),
  browser console clean, VS Code preview screenshots at
  `/tmp/opencode/vederi-before-2.png` and `/tmp/opencode/vederi-final-4.png`.
- Section 2 (legislature slider + two hemicycles) was re-checked: heading,
  slider `min=0 max=9`, and both chamber charts still render and update scope.

## Commit and deployment verification — 2026-11-22

- Main commit: `efdbba71705d154767754766b4d4e8b6fe0603a6` on
  `w5-deployment-squash`. Before it, local HEAD equalled `origin/main`
  (`618849af13d65db89c4ce585954cdd0edc79a7a8`).
- **GitHub:** `origin/main` is still `618849a…`; the new commit is **not** on
  GitHub. No push or PR was made in this session.
- **Vercel:** production alias `parlament-deschis.vercel.app` serves deployment
  `dpl_53HDzW8FT4PaiA3GkSW3xV6su4pp` (READY), whose
  `meta.githubCommitSha = 618849a…` on branch `main`. Its served bundle
  `/assets/index-DjwGQole.js` lacks the new markers (`Compoziția camerelor pe
  legislaturi`, `Harta partidelor`); the local `frontend/dist` bundle has them.
- **Render:** `https://parlament-deschis.onrender.com/api/health` is HTTP 200 /
  `status ok`, but its data differs from local: Render `persons=3381`,
  `memberships=6614`, release `data-20261121-votes-001`; local API
  `persons=3388`, `memberships=7349`, release `null`. The deployed Render
  commit SHA is **NOT PROVEN** — no Render API key is available here. Resolver:
  `RENDER_API_KEY` + `scripts/verify-deploy.sh` with `TARGET_SHA`.
- **Verdict:** the preview pane at `http://127.0.0.1:5188/` shows the local
  committed tree, which is **not identical** to GitHub, Vercel, or Render.
  Local green is not production green.

## Upcoming progress — NOT DONE

1. Push the branch and open a PR to `main` (all CI gates are green locally);
   after merge, re-run `scripts/verify-deploy.sh` with `TARGET_SHA` equal to the
   merge commit and re-check the served bundle markers on Vercel.
2. Confirm the exact Render commit SHA and dataset release with a Render API
   token, then reconcile the `3381/6614` vs `3388/7349` count difference.
3. Make `Parties` and `switchWaves` honour date/legislature scope so the copy
   can be upgraded from "whole corpus" to "selected legislature". Resolver:
   API query support in `backend/routers/api.py` + `frontend/src/api/client.ts`.
4. Run `scripts/ui_validate.py` across all routes at 1280/768/390px and a real
   axe/Lighthouse pass; neither was run in this session. Resolver: QA owner.
5. Add a visual-regression baseline for Section 4 using a tool from the saved
   inventory (e.g. `garris/BackstopJS` or `argos-ci/argos`). Resolver: owner.
6. This note is indexed in [START-HERE](../00-START/START-HERE.md) and
   [SOURCE-MAP](../00-START/SOURCE-MAP.md) row 32; generated vault notes were
   resynced against `efdbba7` by `scripts/vault_sync.py`.

## NOT PROVEN

- WCAG AA contrast, screen-reader tab order, and production rendering were not
  measured; the QA agent observed rendered DOM at 1905px/1440px/390px only.
- Maintenance/licence claims in the GitHub tooling inventory remain marked
  NOT PROVEN in that note; no repository data was re-fetched in this session.
- The `pytest` run predates the final copy and tick-thinning edits; those were
  frontend-only and followed by clean lint/i18n/build, but the full test gate
  was not repeated afterwards.
