# Hero brand mark — Concept A "Amfiteatrul deschis" (Open Hemicycle)

Date: 2026-11-22  
Scope: `frontend/src/components/HeroGraphic.tsx`, `variant === "overview"` SVG fragment only.  
Authoring method: authored from repo research only — no paid/outside design tool, no canvas/MCP that was not actually ingested. Geometry and token contract were derived from the existing component, `stack-choices.md`, `tokens.md`, and `asset-manifest.md` in this tree.

## Concept name and meaning
- **Concept A — "Amfiteatrul deschis"** (Romanian) = **"The open amphitheatre"** / **"Open Hemicycle"** in English.
- An abstracted parliamentary hemicycle: three concentric seating arcs over a broken floor. The 20-unit gap between the two floor segments is the **"open door"** negative space — a deliberate reference to transparent, open Parliament (Parlament Deschis).
- This is a **brand mark / hero identity**, not an illustration or an icon. Lucide React remains the single locked UI icon set.

## Geometry (viewBox `0 0 200 200`, visual centre ≈ (100, 150))
All paths are declarative; no `<text>` in the SVG, no literal hex, no gradients, no new CSS variables, no dependencies.

1. **Outer hemicycle arc:** `M36 150 A64 64 0 0 1 164 150`, `strokeWidth=3`, `opacity=0.5`.
   - Sweep flag `1` renders as an **upper** semicircle: with centre (100,150) the arc runs from 180° → 270° → 360°, passing through the apex at (100, 86). The positive-angle (sweep=1) direction is clockwise in SVG's y-down coordinate system; clockwise from the left endpoint goes up over the top to the right endpoint. The seat-dot coordinates below (all with y < 150) confirm the upper-hemicycle intent, so **no sweep-flag flip was needed**. This was verified by geometric reasoning against the arc spec, not in a browser.
2. **Middle seating arc (seat row):** `M50 150 A50 50 0 0 1 150 150`, `strokeWidth=2.5`, `opacity=0.35`.
3. **Inner presidium arc:** `M66 150 A34 34 0 0 1 134 150`, `strokeWidth=2`, `opacity=0.25`.
4. **Seven seat dots** on the middle r=50 arc, `r=4.5`, `fill=currentColor`, `opacity=0.55`; the apex dot is emphasised at `opacity=0.6` (normalised after QA to stay inside the existing 0.1–0.6 band):
   - (54,131), (65,115), (81,104), (100,100) ← apex / presidium, (119,104), (135,115), (146,131).
   - Each dot is ~50 units from the centre (100,150), i.e. they sit on the middle arc.
5. **Broken floor:** `M36 150 L90 150` and `M110 150 L164 150`, `strokeWidth=3`, `opacity=0.45`. The 20-unit gap (x 90→110) is the "open door" negative space.
6. **Two doorway posts:** `M90 144 L90 156` and `M110 144 L110 156`, `strokeWidth=2`, `opacity=0.4`, framing the gap.
7. Stroke caps: `strokeLinecap="round"` is used on all strokes (explicitly specified for the outer arc and applied consistently to the remaining strokes for a coherent mark). This changes no path coordinates.

## Token contract
- **Paint:** `currentColor` only, inherited from the SVG's `cfg.primary` Tailwind class (e.g. `text-sky-400`). This preserves light/dark theme rewriting — no literal hex, no gradients, no new CSS vars, no new Tailwind tokens.
- **Opacity ladder:** existing low-opacity aesthetic, values in the 0.25–0.55 band for arcs/dots/posts plus `0.6` for the single emphasised apex dot. All values now sit inside the documented 0.1–0.6 band; the initial 0.7 proposal was reduced after QA (2026-11-22).

## Placement update (2026-11-22)

A right-click comment in the VS Code preview requested: "Move the logo on the left side of the 'Parlament Deschis' text in the header". The SVG contents were therefore extracted into `frontend/src/components/BrandMark.tsx` (single source of truth) and rendered in `frontend/src/router.tsx` as a 36px decorative mark (`aria-hidden`) immediately left of the header title. The hero illustration still uses the same component; the header mark and hero mark are the same family, not two different logos.
- **Wrapper unchanged:** `width="200" height="200" viewBox="0 0 200 200" fill="none"`, `className`, `role="img"`, `aria-label={cfg.title}`; title/subtitle markup unchanged; all five non-`overview` variants unchanged.

## Documentation / licensing
- Recorded as a narrow brand-mark exception in `stack-choices.md` (Illustration family section).
- Recorded in `asset-manifest.md`: original in-repo authoring, license = repo LICENSE (AGPL-3.0-or-later), optimization to be confirmed with `npx svgo` after QA.

## Verification (read-only checks)
- `cd frontend && npm run lint`
- `cd frontend && npm run build`
- Result of these checks: see parent task report. **No browser verification was performed by this author.**

## Out of scope
- Other `HeroGraphic` variants, `VARIANT_CONFIG`, SVG wrapper attributes, buttons/interactivity, global tokens/CSS, and data/query logic.
