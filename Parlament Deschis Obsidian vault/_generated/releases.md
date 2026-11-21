---
id: GEN-RELEASES
type: reference
title: "Generated release inventory"
description: "Sorted git tags and the pinned release marker at the source commit."
status: active
authority: mirror
tags: [type/reference, lifecycle/active, domain/ops]
source_paths: [scripts/vault_sync.py, data/latest-release.txt]
created: 2026-11-21T11:55:03+02:00
updated: 2026-11-21T11:55:03+02:00
source_commit: e46eab8bc1e8c2b15e4ab0ad1980592a65d861b6
generated: true
generator: scripts/vault_sync.py
---

> DO NOT EDIT — regenerated. Edits are overwritten.

# Generated release inventory

Pinned release (`data/latest-release.txt` at the source commit): `data-20261117-T213500`.
Tags: 20.

Tags are listed in sorted order. One historical tag is shown under a stable
alias because its literal spelling is banned by the doc-truth policy;
see `00-START/MAINTENANCE-PROTOCOL.md` section 6. Never use it as the pin.

| # | Tag |
|---:|---|
| 1 | `dashboard-for-deployment-1795041320` |
| 2 | `dashboard-v1.0-20261119-002049` |
| 3 | `dashboard-v1.0-complete-20261119-001943` |
| 4 | `dashboard-v1.0-staging-ready-20261119-001539` |
| 5 | `dashboard-v1.0-staging-ready-20261119-001543` |
| 6 | `data-20261115-T203142` |
| 7 | `data-20261117-T[superseded-tag]` |
| 8 | `data-20261117-T213500` |
| 9 | `data-initial-2026-11-14` |
| 10 | `perf-baseline-20261114` |
| 11 | `phase1-data-contract-20261114` |
| 12 | `phase2-sankey-20261114` |
| 13 | `phase3-complete-20261114` |
| 14 | `phase3-coverage-20261114` |
| 15 | `phase4-complete-20261114` |
| 16 | `pre-github-20261113-115113` |
| 17 | `pre-remediation-2026-11-19` |
| 18 | `pre-wave2-2026-11-19` |
| 19 | `v0.2.0` |
| 20 | `v1.0-full-dashboard-20261119` |

Regenerate with `scripts/vault_sync.py`.
