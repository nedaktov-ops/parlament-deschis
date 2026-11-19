# Project Design Contract — Tokens

## Where design tokens live (current)
1. **Tailwind theme (extend):** `tailwind.config.js`
   - `content`: `["./index.html", "./src/**/*.{ts,tsx}"]`
   - `theme.extend.colors`:
     - `ink`: `#0f172a`
     - `panel`: `#1e293b`
   - `plugins`: `[]`
2. **Global CSS tokens and component utilities:** `src/index.css`
   - `:root` (dark scheme) sets CSS custom properties, including (observed):
     - `--color-muted`
     - `--color-accent`
     - `--color-accent-hover`
     - `--color-success`
     - `--color-warning`
     - `--color-danger`
     - `--color-info`
     - `--bg-hero`
     - `--bg-surface`
   - Base element styles: `body`, headings `h1`–`h6`, `.card`, `.wrap`, focus-visible rules, reduced-motion media query, scrollbar styling, and print rules are defined here (see file for full context).
3. **HTML root:** `index.html` sets `<html lang="ro">` and document title (useful for consistent language/metadata expectations; not a visual token file).

> Note: This project uses **Tailwind v3** utility classes widely; many colors come from Tailwind’s default palette (e.g. `slate-*`, `sky-*`) in components/styles unless mapped into theme/tokens. Treat `tailwind.config.js` + `src/index.css` as the **documented token sources** to extend carefully.

## Key tokens observed (do not guess beyond what is visible)
- **Brand/base colors (Tailwind extend):** `ink` (`#0f172a`), `panel` (`#1e293b`).
- **CSS variables (from `src/index.css :root`):** `--color-muted`, `--color-accent`, `--color-accent-hover`, `--color-success`, `--color-warning`, `--color-danger`, `--color-info`, `--bg-hero`, `--bg-surface`.  
  - Exact hex/rgba values for these variables: **TBD in this document** if not reprinted here; read `src/index.css` for the current authoritative values.
- **Typography (observed):** body uses system stack `ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;` with `line-height: 1.6` and antialiasing (see `src/index.css`). Heading scale is defined in CSS (`h1`–`h6` rules present).
- **Shape/spacing patterns:** common utilities in use (e.g. rounded cards via `.card`, layout wrapper `.wrap`) — refer to components in `src/` for patterns; no separate design-token JSON file is present in the repo today.

## How to change tokens
1. **Prefer minimal, purposeful changes.** Avoid introducing a parallel theme system.
2. For **Tailwind color/extend changes:** edit `tailwind.config.js`, then search for affected class names in `src/` to confirm impact.
3. For **runtime CSS variables / global semantics** (accent, status colors, surfaces): edit `:root` and related rules in `src/index.css`. Keep dark-mode behavior consistent (`color-scheme: dark` is set globally today).
4. **Document the change** in this file (and in `stack-choices.md` if the change affects locked choices such as font family or icon policy).
5. **Verify:** run `npm run lint` and `npm run build` (see `package.json`). For visual changes, do a quick manual pass on key routes and record notes in `docs/design/qa-notes.md`.

## Open items / TBD
- A formal exported token table (name → value → usage) is **not yet maintained** here beyond the lists above. **TBD:** expand this file when tokens are formalized.
- Whether to mirror CSS vars into Tailwind theme for consistency is **TBD** (decision needed before large-scale refactors).