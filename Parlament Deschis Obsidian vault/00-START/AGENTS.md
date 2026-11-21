---
id: AGENTS
type: runbook
title: "Agent contract for the Obsidian vault"
description: "Machine-readable ALWAYS / ASK FIRST / NEVER rules and start/end checklists for agents using this vault."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/ops]
source_paths: [MAINTENANCE-PROTOCOL.md, START-HERE.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
---

# Agent contract — Parlament Deschis vault

Scope: this vault only. Governing rules: [MAINTENANCE-PROTOCOL](MAINTENANCE-PROTOCOL.md). State snapshot: [START-HERE](START-HERE.md).

## ALWAYS

- Read [START-HERE](START-HERE.md) first, before any other note.
- Use relative Markdown links only, e.g. `[CURRENT-STATE](../10-STATE/CURRENT-STATE.md)`.
- Keep YAML frontmatter valid and complete (all required fields; `tags` ≤ 3).
- Bump `updated` to the real date whenever a note's body changes.
- Mark unverified claims as NOT PROVEN and name the resolver; add `verified` only when actually checked.
- Regenerate derived content with `python3 scripts/vault_sync.py` after changes.

## ASK FIRST

- Changing any note's `status` to `done`.
- Deleting a note under `70-ARCHIVE/`.
- Changing a recorded resolution (an `R-N` entry) or superseding a decision.

## NEVER

- Edit `_generated/*` (or `openapi.json`) by hand — regenerate instead.
- Use double-bracket wiki-link syntax.
- Copy a `status` value into two notes — each note owns one status, in scope.
- Treat local green as production green; production is a separate scope.
- Put secrets (tokens, credentials, private URLs) in the vault.

## Read at start

1. [START-HERE](START-HERE.md)
2. [MAINTENANCE-PROTOCOL](MAINTENANCE-PROTOCOL.md)
3. [SOURCE-MAP](SOURCE-MAP.md) for the note you are about to touch
4. The note's authoritative source listed in [SOURCE-MAP](SOURCE-MAP.md)

## Write-back at end

- [ ] `updated` bumped with the real date on every changed note.
- [ ] Every claim points to a source in [SOURCE-MAP](SOURCE-MAP.md), or is marked NOT PROVEN.
- [ ] No banned literal strings from [MAINTENANCE-PROTOCOL](MAINTENANCE-PROTOCOL.md) §6.
- [ ] All links are relative Markdown; no wikilinks.
- [ ] `python3 scripts/vault_sync.py` run; `_generated` diff inspected.
- [ ] `--check` and `git diff --exit-code` pass with no residual drift.
- [ ] Code and vault changes committed together.
