# Project Design Contract — Stack choices (locked)

This document locks **design/implementation stack choices** for the frontend so UI work stays consistent and minimal. Update only via PR with rationale.

## Repo facts (source of truth in tree)
- **Framework:** React 19 (`react`, `react-dom` ^19 in `package.json`).
- **Language:** TypeScript (strict options in `tsconfig.json`).
- **Build/dev:** Vite 6 + `@vitejs/plugin-react` (`vite.config.ts`).
- **Styling:** Tailwind CSS v3 (`tailwindcss` ^3.4, `postcss`, `autoprefixer`), configured in `tailwind.config.js`, directives in `src/index.css`.
- **Routing/data (present):** `@tanstack/react-router`, `@tanstack/react-query` (design should not fight these patterns).
- **Lint/type gate:** `npm run lint` runs `tsc --noEmit && eslint src --ext .ts,.tsx` (see `package.json`).

## Locked UI approach (default)
- **UI approach:** **Tailwind CSS v3 + custom React components** (no additional component/UI kit added now).
- **shadcn/ui:** **Not installed** in this repo today. It may be evaluated later, but **is not approved by default**. Any adoption requires a PR that updates this file and documents tradeoffs (bundle, theming alignment with existing tokens).
- **Component styling rule:** Prefer composition with Tailwind utilities and small shared primitives in-repo over introducing a second styling system.

## Icon set (locked)
- **Locked icon set:** **Lucide React** (recommended default for React + Tailwind projects unless product requires otherwise).
- **Rule:** Use **one** icon family across the app. Do **not** mix multiple icon libraries without updating this document.
- **Status in repo:** **TBD** (verify current usage in `src/`); if icons are already imported from another library, treat that as the de facto current choice and update this file in the same PR that standardizes going forward.

## Illustration family (locked)
- **Locked default:** **No custom illustration family by default.** Prefer charts/data visuals already in use (e.g. ECharts/D3-related deps present) and simple UI affordances.
- **If illustrations are added later:** pick **one** minimal, consistent family (style + license documented in `docs/design/asset-manifest.md`) and update this file. Avoid mixing styles.
- One custom **brand-mark family** is permitted as a narrow exception to the "No custom illustration family by default" rule: a single original, hand-authored SVG mark used only for the product's brand/hero identity (e.g. `HeroGraphic.tsx`), painted exclusively with `currentColor` and existing CSS-variable tokens so it follows both themes. This is a brand mark, **not** an illustration or icon pack: Lucide React remains the single locked icon set for all UI icons, and no second icon library, illustration style, or additional custom mark may be introduced without a further PR updating this file and `docs/design/asset-manifest.md`. The mark's source, license, and optimisation status must be recorded in the asset manifest before merge.

## Fonts
- **Current (observed):** System UI stack in `src/index.css`:
  - `font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;`
- **Locked unless changed by PR:** Keep the existing system stack for performance and simplicity unless a branding decision approves a web font (self-hosted preferred; document loading + license in `asset-manifest.md`).

## Colors and design tokens (where they live)
- **Tailwind theme extension:** `tailwind.config.js`
  - `theme.extend.colors`: `ink: "#0f172a"`, `panel: "#1e293b"`.
- **Global CSS variables and base styles:** `src/index.css`
  - `:root` defines dark color scheme and CSS custom properties (examples observed): `--color-muted`, `--color-accent`, `--color-accent-hover`, `--color-success`, `--color-warning`, `--color-danger`, `--color-info`, plus background helpers like `--bg-hero`, `--bg-surface`.
  - Base typography, heading scale, `.card`, `.wrap`, focus styles, reduced-motion rules, scrollbars, and print-related rules are also defined here.
- **Practical rule:** Prefer **existing tokens** (`ink`, `panel`, CSS vars) for new UI. If new tokens are needed, add them in `tailwind.config.js` and/or `src/index.css` in the same change and record them in `docs/design/tokens.md`.

## Notes: what must NOT look like (3 bullets)
- A generic SaaS marketing template with interchangeable hero sections and no connection to Romanian parliamentary transparency.
- A partisan or campaign-style visual identity (no party-color-driven branding; avoid emotive propaganda aesthetics).
- A cluttered, unexplained data dashboard (no chart without context: labels, scope, dates, or definitions where users need them).