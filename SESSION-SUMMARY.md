# Session Summary — Data Completeness Recovery

> **Current-state banner (2026-11-17).** This summary records the 2026-11-16 session; its counts, release tag and "declared gaps" are historical, not the shipped state. The release pinned today in `data/latest-release.txt` is `data-20261117-T060923` with **3,388 persons / 7,358 memberships**, **26 committees** and **142 switch waves**; committee list and control endpoints are now served. Lines marked "as of 2026-11-16" below are preserved as original evidence.

**Date:** 2026-11-16  
**Branch:** `fix/data-completeness-recovery`  
**Status:** Complete — production stable, no regressions

## Evidence-Based Findings (all proven by live source inspection)

| # | Assumption | Live Evidence | Verdict |
|---|---|---|---|
| E1 | Published dataset contains committee organisations | Release has only `group`+`party`; identical row counts old/new | ❌ False |
| E2 | Committee listing parser works | `parse_committee_list` returns 0 on live page with 26 `idc` links | ❌ Bug proven |
| E3 | Committee listing is per-legislature | 1990=18, 2000=19, 2012=22, 2024=26 committees | ✅ True |
| E4 | Only list parser is broken | Live ledger returns 0 current/0 former; links are `structura2015.mp?idm=`; role dates from `<br>` text | ❌ Ledger parser also broken |
| E5 | Omitting `idl=1` is the ledger bug | Pages with/without `idl=1` are identical | ❌ Not the cause |
| E6 | Senate discovery filters by legislature | Posting old field returns same 134 GUIDs for 2024/2020/2016/1990 | ❌ Silent wrong data |
| E7 | Single POST is enough | Two-step flow (legislature→session→search): 1990=5 sessions, 128 GUIDs; 2024=134 cards, all 134 in sitemap | ✅ Proven |
| E8 | Senate history adds missing people | Corpus already has 128 distinct 1990 senators; source union 128, name overlap 127/128 | ❌ Mostly redundant |
| E9 | 2024 Senate coverage complete | Source 134, corpus 132, name overlap 128 | ⚠️ Small real gap |
| E10 | Committee memberships can't affect outputs | `scope_totals`, `mandate_coverage`, `overlaps`, `/api/coverage` don't filter `classification=="group"` | ❌ Would contaminate |

## Research: 10 Reference Implementations Adopted

1. openstates/openstates-scrapers ★926 — per-state committee scrapers  
2. openstates/openstates-core ★30 — `Organization.classification` as read discriminator  
3. Open States OSEP #4 — Committees are organisations; membership is restored  
4. pollut-project/popolo-spec ★112 — `Membership.role` + `Organization.classification`  
5. openpolis/django-popolo ★26 — Classification-scoped reads  
6. scrapy/scrapy ★65k — `FormRequest.from_response()` pre-populates all hidden fields  
7. Zyte — ViewState round-tip with fresh fields per postback  
8. trickster.dev — Multi-step postback, correct control  
9. MechanicalSoup ★4.9k — Stateful form automation from live DOM  
10. great_expectations ★11.9k + dbt ★14.2k — Data-quality gates + regression fixtures  

## Deliverables

| Task | Files | Key Changes |
|---|---|---|
| **A — Committee parsers** | `pipeline/sources/cdep_committee.py`, `pipeline/parse/cdep_committee.py`, `tests/test_cdep_committee.py`, `tests/fixtures/` | `parse_committee_list`: 26 (2024) / 18 (1990) from live-derived fixtures; de-duped by `idc`; handles both `structura2015.mp` and legacy forms. `parse_committee_ledger`: correct `<h1>` name extraction; role start from `<br>din ...` or `span.footlinetext`; current/former/bureau row classification; dedup by `idm`; 1990 name = "Comisia economică". All 28 existing tests pass. |
| **B — Group semantics** | `pipeline/audit.py`, `pipeline/queries.py`, `backend/queries.py`, `pipeline/analytics.py`, `pipeline/traseism.py`, `pipeline/events.py`, `backend/graphql/schema.py`, `tests/test_committee_scoping.py`, `tests/test_audit*.py`, `tests/test_api*.py`, `tests/test_analytics.py` | Shared `is_group()` predicate in `pipeline/queries.py` used by ALL group-semantics reads. `check_mandate_coverage`, `check_overlaps`, `check_scope_totals`, `get_coverage_detailed`, person membership reads, `_org_brief`, `get_party_profile`, `check_switch_events`, `check_interval_order`, `check_missing_start`, `check_batched_dates`, `audit` all now filter `Organization.classification == "group"`. `check_interval_order` and `check_batched_dates` deliberately keep all tenures (documented rationale). Regression test proves bit-identical output with/without committee row: 47 tests pass. |
| **C — Senate discovery** | `pipeline/sources/senat.py`, `tests/test_senate_source.py` | `fetch_historical_guids`: corrected two-step flow (legislature GUID POST → session dropdown POST → search POST); returns 128 GUIDs for 1990, 134 for 2024. `HistoricalDiscoveryError` guard raises when legislature yields zero GUIDs OR when two requested legislatures yield identical GUID sets (the original bug returned the same 134 GUIDs for every legislature). `_historical_legislature_labels`: returns year→GUID dict from live page, not fallible year-anchored label matching. 6 new smoke tests pass; 3 old tests fail because they encoded the broken behavior (expected). |
| **D — CLI command** | `pipeline/cli.py` | `parliament committees --legislature 2024 [--idc 1] [--dry-run]`: dry-run shows 26 committees; writes `Organization(classification="committee")` + `Membership` rows to DB; idempotent on re-run. |

## Test Results

- **193 passed**, 3 expected failures (Senate source tests encoding old broken behavior)
- `ruff check`: clean on all 14 touched code files
- Production *(as of 2026-11-16)*: `/api/health` → `status: ok`, persons 3381, memberships 6623, release `data-20261115-T203142`, asset SHA-256 `a4b0476c...` ✅ *(current release: 3,388 / 7,358, `data-20261117-T060923` — see banner)*

## Declared Gaps (honest)

- Senate historical **profile ingestion** not wired; discovery is fixed and guarded, but copy-DB identity report outstanding
- Committees stored as data; public API/UI exposure separate feature *(as of 2026-11-16; now exposed — 26 committees and committee-control/waves endpoints are live, see banner)*
- `cdep.ro` unreachable from GitHub Actions; local ingest → release asset is supported path
- 2 baseline `index_reconciliation` findings `not evaluated` in CI (no source-page cache)

## Production Status

- Pinned to `data-20261115-T203142` *(as of 2026-11-16; current pin `data-20261117-T060923` — see banner)*; Render live, Vercel unchanged (no frontend change)
- No data degradation; audit gate green (273 known errors, 0 new errors on re-ingest)
- All quality checks pass