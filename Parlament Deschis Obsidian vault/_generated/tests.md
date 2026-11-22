---
id: GEN-TESTS
type: reference
title: "Generated test inventory"
description: "Tracked test files and their test-function counts at the source commit."
status: active
authority: mirror
tags: [type/reference, lifecycle/active, domain/ops]
source_paths: [scripts/vault_sync.py, tests/]
created: 2026-11-22T21:28:07+02:00
updated: 2026-11-22T21:28:07+02:00
source_commit: 943f4bf00fe191a1d60542676d9f5029bc00a672
generated: true
generator: scripts/vault_sync.py
---

> DO NOT EDIT — regenerated. Edits are overwritten.

# Generated test inventory

Counts come from the source-commit versions of tracked files under `tests/`.

- Python test files: 52; `def test_` definitions: 392.
- Bats test files: 0; `@test` cases: 0.

| File | Pattern | Count |
|---|---|---:|
| `tests/__init__.py` | `def test_` | 0 |
| `tests/conftest.py` | `def test_` | 0 |
| `tests/test_admin_lockout.py` | `def test_` | 4 |
| `tests/test_analytics.py` | `def test_` | 5 |
| `tests/test_analytics_transparency.py` | `def test_` | 3 |
| `tests/test_api.py` | `def test_` | 49 |
| `tests/test_api_exports.py` | `def test_` | 6 |
| `tests/test_approxdate.py` | `def test_` | 10 |
| `tests/test_audit.py` | `def test_` | 18 |
| `tests/test_audit_overlap.py` | `def test_` | 2 |
| `tests/test_cache.py` | `def test_` | 3 |
| `tests/test_cdep_committee.py` | `def test_` | 18 |
| `tests/test_cdep_group.py` | `def test_` | 12 |
| `tests/test_cdep_profile.py` | `def test_` | 3 |
| `tests/test_cdep_roster.py` | `def test_` | 2 |
| `tests/test_ches_parser.py` | `def test_` | 6 |
| `tests/test_cli.py` | `def test_` | 14 |
| `tests/test_cli_coverage_dimensions.py` | `def test_` | 4 |
| `tests/test_collect_cache.py` | `def test_` | 10 |
| `tests/test_committee_scoping.py` | `def test_` | 2 |
| `tests/test_count_definitions.py` | `def test_` | 7 |
| `tests/test_crosscheck.py` | `def test_` | 1 |
| `tests/test_dataset_download.py` | `def test_` | 7 |
| `tests/test_db_schema.py` | `def test_` | 8 |
| `tests/test_events.py` | `def test_` | 8 |
| `tests/test_export.py` | `def test_` | 5 |
| `tests/test_export_report.py` | `def test_` | 5 |
| `tests/test_graphql_convergence.py` | `def test_` | 7 |
| `tests/test_group_discovery.py` | `def test_` | 2 |
| `tests/test_identity.py` | `def test_` | 11 |
| `tests/test_ingest_dedup_scope.py` | `def test_` | 1 |
| `tests/test_ingest_integration.py` | `def test_` | 10 |
| `tests/test_logo_store.py` | `def test_` | 3 |
| `tests/test_normalize_groups.py` | `def test_` | 3 |
| `tests/test_party_facts_parser.py` | `def test_` | 7 |
| `tests/test_polite_client_content.py` | `def test_` | 3 |
| `tests/test_prepare_db.py` | `def test_` | 6 |
| `tests/test_r08_feature_honesty.py` | `def test_` | 12 |
| `tests/test_reconcile.py` | `def test_` | 14 |
| `tests/test_scope_backend.py` | `def test_` | 4 |
| `tests/test_security_hardening.py` | `def test_` | 6 |
| `tests/test_senat_profile.py` | `def test_` | 9 |
| `tests/test_senat_source.py` | `def test_` | 6 |
| `tests/test_senate_source.py` | `def test_` | 6 |
| `tests/test_source_licenses.py` | `def test_` | 13 |
| `tests/test_traseism.py` | `def test_` | 4 |
| `tests/test_vote_hash_backfill.py` | `def test_` | 3 |
| `tests/test_vote_ideology_convergence.py` | `def test_` | 14 |
| `tests/test_votes_build_isolation.py` | `def test_` | 3 |
| `tests/test_votes_cdep_parser.py` | `def test_` | 17 |
| `tests/test_votes_dry_run.py` | `def test_` | 9 |
| `tests/test_votes_thirdparty_contract.py` | `def test_` | 7 |

Regenerate with `scripts/vault_sync.py`.
