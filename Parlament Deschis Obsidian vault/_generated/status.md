---
id: GEN-STATUS
type: state
title: "Generated git status snapshot"
description: "Merge-stable source commit and date; live git state is authoritative for branch/divergence."
status: active
authority: mirror
tags: [type/state, lifecycle/active, domain/ops]
source_paths: [scripts/vault_sync.py]
created: 2026-11-23T15:11:40+02:00
updated: 2026-11-23T15:11:40+02:00
source_commit: f17c5376c6977a6a2ef859234c4aebbe0ea6f1c5
generated: true
generator: scripts/vault_sync.py
---

> DO NOT EDIT — regenerated. Edits are overwritten.

# Generated git status snapshot

| Fact | Value |
|---|---|
| Source commit (last non-vault change) | `f17c5376c6977a6a2ef859234c4aebbe0ea6f1c5` |
| Source commit date | `2026-11-23T15:11:40+02:00` |
| Default branch | `main` |

Branch name, ahead/behind and dirty state are deliberately omitted: they
change on merge and would make `--check` drift after every PR. Check the
live repository with `git status` / `gh pr list` for those facts.
Regenerate with `scripts/vault_sync.py`.
