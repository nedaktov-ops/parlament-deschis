---
id: DAILY-YYYY-MM-DD
type: daily
title: "Daily — YYYY-MM-DD"
description: "What was checked, changed, and left open on this date."
status: active
authority: mirror
tags: [type/daily, lifecycle/active, domain/ops]
source_paths: [docs/REPLACE-WITH-SOURCE.md]
created: YYYY-MM-DD
updated: YYYY-MM-DD
source_commit: 6fd6028
---

# Daily — YYYY-MM-DD

This is the template for notes in `Daily Notes/` (format `YYYY-MM-DD`, automatic creation off). Copy it manually when needed.

## Start

- `git status` captured before any edit.
- HEAD SHA and release pin recorded.

## Work log

- Change — reason — verification command and result.

## Generated artifacts

- Run `python3 scripts/vault_sync.py`, then review `git diff -- "Parlament Deschis Obsidian vault/_generated"`. Never hand-edit generated notes.

## End

- Run `python3 scripts/vault_sync.py --check`; if it reports drift, stop and fix before claiming the vault is current.
- Link follow-ups to [TASK-REGISTER](../20-DIRECTION/TASK-REGISTER.md).
