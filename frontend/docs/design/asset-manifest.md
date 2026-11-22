# Project Design Contract — Asset manifest

Use this file to track non-code design assets (images, icons sources, illustrations, fonts files if self-hosted) so licensing and optimization are explicit.

## Rules (align with `stack-choices.md`)
- **Icons:** follow the locked icon set in `docs/design/stack-choices.md` (one family). Do not add ad-hoc SVG icon packs without updating that doc.
- **Illustrations:** avoid adding illustrations by default; if added, use **one** minimal family, document license here, and update `stack-choices.md`.
- **Fonts:** prefer system stack currently in use. If a web font is introduced, record source, license, self-hosting path, and fallback stack here.
- **Optimization:** mark whether assets are optimized (compressed, correctly sized, modern formats where appropriate). Prefer SVG for simple icons/marks when hand-authored; avoid unoptimized large PNG/JPG exports in `public/` or `src/` without review.

## Asset table (template)
Fill rows as assets are added. Use relative paths from the repo root (e.g. `frontend/public/...` or `frontend/src/assets/...`) or clearly state external/CDN sources.

| Path / location | Description | Source (author/vendor/link) | License | Optimized? (yes/no + notes) | Notes |
|---|---|---|---|---|---|
| _Example: `public/favicon.svg`_ | _Favicon_ | _Existing repo asset_ | _TBD / see repo_ | _TBD_ | _Verify current state_ |
| `frontend/src/components/BrandMark.tsx` + `frontend/src/components/HeroGraphic.tsx` | Concept A "Amfiteatrul deschis" (Open Hemicycle) — original hand-authored SVG brand mark; shared component used in the site header (left of the title) and the hero | Original in-repo authoring | Repo LICENSE (AGPL-3.0-or-later, free/open source) | Inline JSX SVG, minified by the Vite production build; no separate `.svg` asset for SVGO. Free SVGO 4.1.0 confirmed available (`npx svgo --version`) if a standalone asset is exported later. No raster exports. | Single permitted custom brand-mark family; theme via `currentColor`; no new hex tokens |
| | | | | | |

## How to update this manifest
1. Add or change an asset in the repo (or approve an external dependency).
2. Add/update a row in the table with license and optimization status.
3. If the change affects locked stack choices, update `docs/design/stack-choices.md` in the same PR.

## Current repo assets (known)
- `public/favicon.svg` exists in the frontend tree (**details TBD** — confirm license/optimization and add a row when auditing assets).