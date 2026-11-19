# Wireframes (design exports)

## Purpose
This folder holds **exported wireframes and low-fidelity layout references** for the Parlament Deschis frontend. Wireframes are **planning artifacts** (not source code): they help align structure, hierarchy, and key flows before or alongside implementation.

They live in-repo so reviewers and contributors can find them next to other design contract docs (`../brief.md`, `../stack-choices.md`, `../tokens.md`).

## What to store here
- Exported images (e.g. `.png`, `.jpg`, `.webp`) or PDFs of wireframes.
- Optional: short notes per file in a sibling Markdown file if context is not obvious from the filename.
- **Do not** commit editable source-of-truth files from external tools here unless the team explicitly decides to (prefer linking or storing exports). Keep large binaries reasonable; optimize images when practical.

## Recommended naming
Use a clear pattern, for example:
- `YYYY-MM-DD_<route-or-screen>_wireframe_v01.png`
- `home_lofi_v01.png`, `mp-detail_lofi_v01.png`

## How to add exports from Excalidraw / Penpot (outside tools)
1. **Create or edit** the wireframe in **Excalidraw** or **Penpot** (outside this repo).
2. **Export** a shareable artifact:
   - **Excalidraw:** export to PNG/SVG as appropriate (PNG is usually easiest for quick review in PRs).
   - **Penpot:** export the frame/page to PNG/PDF/SVG per project need.
3. **Optimize** the export if large (reasonable dimensions; compress PNG/JPG when helpful).
4. **Add the file** to this directory (`docs/design/wireframes/`).
5. **Update references** if needed (e.g. link from a PR description or from `../qa-notes.md` / issue notes). If a screen set is important, add a short `README` note in the same folder describing the set.
6. **Commit** with a message that mentions the screen(s) and version (e.g. `docs(design): add home wireframe v01`).

## Relationship to implementation
- Wireframes are **guidance**, not pixel-perfect specs unless stated otherwise.
- Final visuals must respect `docs/design/stack-choices.md` and `docs/design/tokens.md` and the current codebase constraints (Tailwind v3, React 19, TypeScript).
- If wireframes and implementation diverge, record the decision (PR note or follow-up doc update) so the contract stays truthful.