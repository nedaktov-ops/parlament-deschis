---
id: STACK-AND-TOKENS
type: reference
title: "Locked frontend stack and design tokens"
description: "Mirror of the repo's locked stack choices and token sources, with verified drift flags: icon-lock contradiction, undocumented light theme, AGENTS.md inaccuracies and one missing button type."
status: active
authority: mirror
tags: [type/reference, lifecycle/active, domain/frontend]
source_paths: [frontend/docs/design/stack-choices.md, frontend/docs/design/tokens.md, frontend/package.json, frontend/tailwind.config.js, frontend/src/index.css, frontend/src/components/PartyComparisonMatrix.tsx]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Stack and tokens

Scope: the design/implementation choices locked in
`frontend/docs/design/stack-choices.md`, cross-checked against the tree at
`6fd6028`. Brand intent lives in [DESIGN-CONTRACT](DESIGN-CONTRACT.md); observed
test results live in [QA-AND-AXE](QA-AND-AXE.md).

## Locked stack

| Concern | Locked choice | Evidence |
|---|---|---|
| Framework | **React 19** | `react`, `react-dom` ^19; `npm ls react` reports **19.3.1** |
| Language | **TypeScript**, strict options | `tsconfig.json` |
| Build/dev | **Vite 6** + `@vitejs/plugin-react` | `vite.config.ts`; installed Vite 6.4.6 |
| Styling | **Tailwind CSS v3** | `tailwindcss` ^3.4 (installed 3.4.19), PostCSS, autoprefixer |
| Routing / data | **@tanstack/react-router** + **@tanstack/react-query** | `package.json`; design should not fight these patterns |
| Icons | de-facto **inline SVG** (see contradiction below) | no icon package in dependencies; inline `<svg>` in `src/` |
| Lint gate | `npm run lint` = `tsc --noEmit && eslint src --ext .ts,.tsx` | `package.json` |

- **No shadcn/ui.** Not installed and not approved by default; adoption needs a
  PR that updates `stack-choices.md` and documents bundle/theming tradeoffs.
- **No additional UI kit.** Prefer Tailwind utilities and small in-repo
  primitives over a second styling system.
- **No default illustration family.** Use existing charts/data visuals
  (ECharts, d3-scale/d3-sankey are present) and simple UI affordances. If
  illustrations are added later, pick one licensed family and record it in the
  asset manifest. That manifest is currently empty — see
  [QA-AND-AXE](QA-AND-AXE.md).
- **System fonts**, locked: `ui-sans-serif, system-ui, -apple-system,
  "Segoe UI", Roboto, sans-serif`. No web font is approved; self-hosting and
  licence notes would be required to change this.
- **Runtime:** Node **v24** is now available on this machine (`v24.22.3`); older
  docs that cite Node 18 are historical.

## Token sources — and a documentation mismatch

Two files are the documented sources of truth:

1. `frontend/tailwind.config.js` — `content` is
   `["./index.html", "./src/**/*.{ts,tsx}"]`; `theme.extend.colors` defines
   `ink` and `panel` plus a generated `slate` scale. The **code** builds these
   with `rgb(var(--<name>) / <alpha-value>)`, so opacity modifiers such as
   `bg-slate-800/30` keep working.
2. `frontend/src/index.css` — `:root` declares the actual values as space
   separated RGB triplets (`--slate-50` … `--slate-950`, `--ink: 15 23 42`,
   `--panel: 30 41 59`) and semantic CSS variables: `--color-muted`,
   `--color-accent`, `--color-accent-hover`, `--color-success`,
   `--color-warning`, `--color-danger`, `--color-info`, `--bg-hero`,
   `--bg-surface`. Base typography, `h1`–`h6`, `.card`, `.wrap`, focus-visible,
   reduced-motion, scrollbar and print rules also live here.

> **Drift to flag:** `stack-choices.md:34` and `tokens.md:27` still print the
> pre-variable literals `ink: "#0f172a"` and `panel: "#1e293b"`. Those are the
> *dark-theme values*, not the current token implementation. Read
> `index.css` for authoritative values; do not hardcode hex in new components.
> There is no formal exported token table (name → value → usage) yet.

`index.html` sets `<html lang="ro">` and the document title; it is not a visual
token file.

## Light theme exists but is undocumented

`:root` sets `color-scheme: dark`, but `index.css` also contains a complete
`html[data-theme="light"]` block: the slate scale is reversed (e.g.
`--slate-50: 2 6 23`, `--slate-900: 241 245 249`), `--ink` and `--panel` become
light surfaces, semantic accents are darkened for contrast, and focus outlines
are re-tuned. The design docs describe only the dark default and even say
"`color-scheme: dark` is set globally" — they never mention the light theme.
No runtime `data-theme` setter was found in `src/`, so treat the light theme as
present in CSS but **undocumented and not surfaced by an in-app toggle**.

## Icon lock contradiction

- `stack-choices.md:19` says the locked icon set is **Lucide React**.
- `stack-choices.md:21` itself admits the repo status is **TBD** ("if icons are
  already imported from another library, treat that as the de facto current
  choice").
- There is **no Lucide dependency and no Lucide import** in `frontend/src`.
  Inline `<svg>` markup is the de-facto family.

Resolution rule already written into the source doc: update the lock to inline
SVG (or deliberately add Lucide) in the same PR that standardises icons. Until
that PR lands, the lock is contradictory — do not treat Lucide as installed.

## AGENTS.md inaccuracies to flag

The repo-root `AGENTS.md` (browser-support policy) makes claims that do not hold
against `6fd6028`:

- **No `overscroll-behavior: contain` usage.** `:18-19` claims it is used on
  modal overlays (`About.tsx`, `PersonDrawer.tsx`); no such declaration exists
  in `frontend/src`.
- **No `popover` attribute usage.** `:19` claims `CitationPopover` uses it;
  that component uses React state. Consequently the polyfill paragraph at
  `:15` is **moot** — no code path needs `@oddbird/popover-polyfill` today.
- **Internal contradiction.** `:7-9` calls `popover` "Baseline widely
  available… safe without fallbacks" while `:15` requires a polyfill for older
  browsers. Both cannot be the governing rule.
- **`type="button"` rule has one violation.** `:20` requires the attribute on
  all buttons. `frontend/src/components/PartyComparisonMatrix.tsx:77-80`
  renders `<button onClick={…} className="text-sky-400 hover:underline
  text-xs">View all transitions →</button>` with no `type`. **Recommended fix
  (not applied in this read-only mirror): add `type="button"`.** No other button
  in that file lacks it.

## Change protocol

Edit `tailwind.config.js` for theme-level colours and `src/index.css` for
runtime CSS variables; then grep `src/` for affected class names, document the
change in both design docs, and verify with `npm run lint` and `npm run build`.
Never edit generated files or introduce a parallel theme system.
