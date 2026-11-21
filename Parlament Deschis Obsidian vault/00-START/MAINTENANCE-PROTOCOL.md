---
id: MAINTENANCE-PROTOCOL
type: runbook
title: "Vault maintenance protocol"
description: "The operating contract: resolution policy, status meanings, link conventions, ID scheme, banned strings, and the LLM update ritual."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/ops]
source_paths: [docs/AUDIT-RESOLUTIONS-2026-11-21.md, docs/POST-INITIAL-AUDIT-2026-11-21.md, docs/GAP-ANALYSIS-2026-11-21.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Maintenance protocol

This is the operating contract for the vault. See [START-HERE](START-HERE.md) for state and [SOURCE-MAP](SOURCE-MAP.md) for which repo path is authoritative for each note.

## 1. Resolution policy (applied in this order)

1. **Executable evidence > prose** — current source, DB queries, API responses, CI/CLI output and generated artifacts outrank any document claim.
2. **Scope before conflict** — if two numbers differ, check definitions and artifacts first; call a defect only when both describe the same thing.
3. **Newer wins unless labelled historical** — an explicitly labelled historical snapshot is preserved as history, not used to override current state.
4. **Addendum > base body** — within one file, a dated current-state banner or addendum beats the body.
5. **Generated artifacts derive from source** — never hand-edit generated files such as `openapi.json` or anything under `_generated/`; regenerate them.
6. **No guessing → NOT PROVEN** — if evidence is unavailable, report NOT PROVEN and name the resolver that could settle it.

## 2. Status field meanings

| Status | Meaning |
|---|---|
| `active` | Current, authoritative for its scope; safe to rely on. |
| `stale` | A newer source exists; still readable, but do not treat as current. |
| `archived` | Kept for history only; never used to override an active note. |
| `superseded` | Replaced by a named newer note; point readers to the replacement. |
| `open` | A gap or question with no resolution yet; needs an owner. |
| `in-progress` | Work is underway locally and has not shipped. |
| `done` | Fully resolved *and* shipped/verified in the stated scope. |

Scope is mandatory: a status like `done` means "done locally" only if the note says so; local green is never production green.

## 3. Authority field meanings

`canonical` (source of truth for its topic) · `mirror` (verbatim projection, regenerate) · `derived` (computed from sources) · `historical` (preserved snapshot) · `unverified` (claim not yet checked; must name a resolver).

## 4. Link and naming conventions

- Use **relative Markdown links only**: `[CURRENT-STATE](../10-STATE/CURRENT-STATE.md)`. Wikilinks are banned.
- Note files are `SCREAMING_SNAKE_CASE.md`; folder names are `NN-NAME` (e.g. `10-STATE`).
- Frontmatter is the first thing in every note, with exactly: `id`, `type`, `title`, `description`, `status`, `authority`, `tags`, `source_paths`, `created`, `updated`, `source_commit`, and `verified` only when a claim was actually checked.
- `tags` has at most 3 values: `type/<type>`, one `lifecycle/<active|stale|archived>`, one `domain/<project|frontend|data|ops|research>`.
- `source_commit` is the repo commit the note was synced against; `source_commit: 6fd6028` for this snapshot.
- Bump `updated` to the real date whenever a note's body changes.

## 5. ID scheme

- **Tasks:** `T-2026-NNN` (e.g. `T-2026-001`).
- **Decisions:** `D-NNNN` (e.g. `D-0001`), backed by an ADR in `docs/adr/`.
- **Resolutions:** `R-N` (e.g. `R1` … `R11`), matching `docs/AUDIT-RESOLUTIONS-2026-11-21.md`.
- **Gaps:** `G-P0-NN`, `G-P1-NN`, `G-P2-NN` by priority (e.g. `G-P0-01`).
- **Evidence:** `E-YYYYMMDD-slug` (e.g. `E-20261121-audit`).

Do not reuse an ID; supersede the old note and link to the replacement.

## 6. Banned literal strings (project doc-truth gate)

The exact banned literals are defined by `scripts/check-doc-truth.sh` in the repo. **Do not copy them into the vault** — describing them here must not reproduce them. The categories and their safe replacements are:

- A legacy "JS errors" badge phrased with the abbreviation → say "zero JavaScript errors".
- The old civic-source domain string → say "the external Romanian civic source (ro_281)".
- The superseded data-release tag ending in `T060923` → use `data-20261117-T213500`.
- Stale pytest-count phrasings (the historical 193/125/199-style numbers) → use "pytest 384 passed" or state the dated scope explicitly.
- A "Ready … Deployment" readiness badge → describe the actually verified scope instead.
- The legacy "three expected failures" phrasing → name the failures and their real status.
- The old strict-audit error count badge → say "strict audit 275 known / 0 new".
- Stale JSON metric literals for `memberships`, `switches`, `legislatures`, `parties`, `cross_chamber`, `coverage_score` → use the current values with their endpoint and date: "7,349 prepared memberships (7,358 raw asset)", "2,002 total switch events"; for the others, query and state the live value rather than copying a number.

If you need the precise strings to test the gate, read the gate script itself; never paste them into a note.

## 7. LLM update ritual (7 steps, in order)

1. `git status` — capture the working-tree state before touching anything.
2. Make the changes (hand-written notes only; never edit generated files).
3. Run `python3 scripts/vault_sync.py` to regenerate derived/`_generated` content.
4. Inspect `git diff -- "Parlament Deschis Obsidian vault/_generated"`.
5. Update the hand-written notes to match, recording the reason for each change.
6. Run the check (`scripts/vault_sync.py --check`) plus `git diff --exit-code` to prove there is no residual drift.
7. Commit code and vault changes together.

If step 6 fails, stop — do not claim the vault is current.
