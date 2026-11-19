# Data Completeness Recovery — Action Plan

> **Current-state banner (2026-11-17).** This is the historical recovery plan, captured 2026-11-15/16. Its release tag, counts, "in progress" status and evidence rows are as-of-that-date records, not the shipped state. The release pinned today in `data/latest-release.txt` (read that file for the exact tag) has 3,388 persons / 7,358 memberships, 26 committee organisations and 142 switch waves. The E1 baseline counts below are explicitly historical evidence. Do not read this plan as current status.

Status (as of 2026-11-15/16): **in progress**. Production was pinned to `data-20261115-T203142`.
No data release was to be published by this plan until every gate below was green and the
impact report on a copy database showed no regression.

## 1. Why this plan exists

The previous release shipped schema, marker, authentication and audit-gate fixes,
but the "data completeness" features merged in code did **not** ship data. This
plan is based on live-source evidence, not assumptions.

### Evidence (captured 2026-11-15/16)

| # | Assumption | Live evidence | Verdict |
| --- | --- | --- | --- |
| E1 | The published dataset contains committee organisations/memberships | *(historical evidence, 2026-11-15/16)* Release `data-20261115-T203142` had only `group` and `party` organisations; old and new releases had identical row counts (3381 persons, 86 orgs, 6623 memberships, 5273 mandates, 7429 events) | **False** |
| E2 | Committee listing parsing works | `parse_committee_list` returns 0 on a live page with 26 `idc` links; the parser searches for `</a>` inside the opening tag | **Bug proven** |
| E3 | The committee listing is per-legislature | Live counts: 1990 = 18, 2000 = 19, 2012 = 22, 2024 = 26 committees; 1990 uses different `idc` values (51, 52) | **True** |
| E4 | Only the list parser is broken | `parse_committee_ledger` returns 0 current / 0 former on live pages; live links are `structura2015.mp?idm=`, role dates are plain text after `<br>`, committee name is the third `<h1>` | **False — ledger parser is broken too** |
| E5 | Omitting `idl=1` from the ledger URL is the bug | Pages with and without `idl=1` are identical (49 KB, 27 `idm` occurrences) | **False** |
| E6 | Historical Senate discovery filters by legislature | Posting `ddlLegislatura=2016` returned the same 134 GUIDs as 2024/2020/1990; the live field is `ctl00$B_Center$ddLegislatura` with GUID values | **Bug proven** |
| E7 | A single POST is enough | Correct two-step flow (legislature → session → search): 1990 = 5 sessions, union **128**; 2024 = 134 cards, all 134 in the 137-entry sitemap after lowercasing | **True** |
| E8 | Senate history adds missing people | Corpus already has 128 distinct 1990 senators and 126 mandates; source union is 128, order-insensitive name overlap 127/128 | **Mostly false** |
| E9 | 2024 Senate coverage is complete | Source 134, corpus 132, name overlap 128; a small real gap remains | **Partially false** |
| E10 | Committee memberships cannot affect existing outputs | `scope_totals`, `check_mandate_coverage`, `check_overlaps` and `/api/coverage` do not filter `Organization.classification == "group"` | **False — they would be contaminated** |

## 2. Reference implementations (researched, not invented)

| # | Project | Verified signal | Pattern adopted here |
| --- | --- | --- | --- |
| 1 | [openstates/openstates-scrapers](https://github.com/openstates/openstates-scrapers) ★926 | Per-state `committees.py` scrapers | Parse list + ledger with BeautifulSoup; commit live-derived fixtures |
| 2 | [openstates/openstates-core](https://github.com/openstates/openstates-core) ★30 | Data model + migration discipline | `Organization.classification` is the discriminator for reads |
| 3 | [Open States OSEP #4 — Committee Data](https://docs.openstates.org/enhancement-proposals/004-committee-data) | Committees are organisations; committee membership is restored via organisation membership | Store committees as `organization.classification="committee"` |
| 4 | [popolo-project/popolo-spec](https://github.com/popolo-project/popolo-spec) ★112 | `Membership.role` + `Organization.classification` | Committee membership is a `Membership` to a committee org, not a party |
| 5 | [openpolis/django-popolo](https://github.com/openpolis/django-popolo) ★26 | Real Popolo implementation | Same model; classification-scoped reads |
| 6 | [scrapy/scrapy](https://github.com/scrapy/scrapy) ★65k | `FormRequest.from_response()` pre-populates **all** hidden fields | Generic form-state extraction, never hardcode a subset |
| 7 | [Zyte — Scraping ViewState with Scrapy](https://www.zyte.com/blog/scrapy-tips-from-the-pros-april-2016-edition) | `__VIEWSTATE` round-trip | Carry fresh hidden fields across sequential postbacks |
| 8 | [trickster.dev — legacy ASP.NET with Scrapy](https://www.trickster.dev/post/scraping-legacy-asp-net-site-with-scrapy-a-real-example) | Real WebForms flow | Multi-step postback; target the correct control |
| 9 | [MechanicalSoup/MechanicalSoup](https://github.com/MechanicalSoup/MechanicalSoup) ★4.9k | Stateful form automation | Session state; parse forms from the live DOM |
| 10 | [fivetran/great_expectations](https://github.com/fivetran/great_expectations) ★11.9k + [dbt-labs/dbt](https://github.com/dbt-labs/dbt) ★14.2k | Data quality gates | Regression fixtures + expectations before publish |
| 11 | [simonw/sqlite-utils](https://github.com/simonw/sqlite-utils) ★2.2k | SQLite integrity tooling | `PRAGMA integrity_check`, row counts, checksums before release |

## 3. Decisions

- **D1 — Committee model.** Committees are `Organization` rows with
  `classification="committee"`; memberships are `Membership` rows to those
  organisations. This matches OpenStates OSEP #4 and Popolo.
- **D2 — Group semantics are explicit.** Every query that means "party/group
  membership" must filter `Organization.classification == "group"`. A single
  helper is used so the filter cannot drift.
- **D3 — Senate historical ingest is deferred.** Discovery is fixed and guarded,
  but not wired into `build-corpus`/`ingest_profiles`. The corpus already has
  1990: 128/128 and 2024: 132/134. The remaining gap is small and the identity
  risk (name order, homonyms, 0 existing `senat_guid` identifiers) is not yet
  proven safe. A copy-DB impact report is required first.
- **D4 — No publish until parity.** The release is only published after parser
  tests, the audit gate, an API parity report on a copy DB, and checksum
  verification. Production stayed on `data-20261115-T203142` until then *(historical; the current pin is in `data/latest-release.txt`)*.

## 4. Work breakdown (subagent recipes)

Each task has a file boundary, acceptance criteria and a rollback. Agents must
not commit, push, or touch untracked user files (`.playwright-mcp/`,
`TRACEISM_REVIEW.md`, `docs/BLOG-SEO-AND-HOSTING-STRATEGY.md`,
`traseism-before.png`).

### Task A — Committee discovery + ledger parsers

Owner: `data-engineer`.
Files: `pipeline/sources/cdep_committee.py`, `pipeline/parse/cdep_committee.py`,
`tests/test_cdep_committee.py`, `tests/fixtures/cdep_committee_*`.

Acceptance:
1. `parse_committee_list` returns **26** items for live 2024 and **18** for 1990,
   with correct names and de-duplicated `idc` values.
2. `parse_committee_ledger` on live 2024 `idc=1` returns
   name `Comisia pentru politică economică, reformă şi privatizare`,
   `len(current) >= 20`, `len(former) >= 2`, and role start
   `2025-03-19` for `Dunava Costel Neculai`.
3. 1990 `idc=51` returns name `Comisia economică` and `len(current) > 0`.
4. Tests run offline against trimmed live-derived fixtures; no network.
5. `uv run pytest tests/test_cdep_committee.py tests/test_ingest_integration.py -q`
   passes; `uv run ruff check` clean on touched files.

Rollback: revert the task commit; no data is written.

### Task B — Group-scoped audit and API reads

Owner: `backend-architect`.
Files: `pipeline/audit.py`, `pipeline/queries.py`, `backend/queries.py`,
`pipeline/analytics.py`, `pipeline/traseism.py`, `pipeline/events.py`,
`backend/graphql/schema.py`, `tests/test_audit*.py`, `tests/test_api*.py`.

Acceptance:
1. A shared group predicate/helper exists and is used by
   `scope_totals`, `check_mandate_coverage`, `check_overlaps`,
   `get_coverage_detailed` membership stats, and person membership reads.
2. A regression test inserts a committee organisation + membership and proves
   every group output is **bit-identical** to the same DB without that row.
3. Existing tests pass: `uv run pytest tests/test_audit.py tests/test_audit_overlap.py
   tests/test_api.py tests/test_analytics.py -q`.

Rollback: revert the task commit; no data is written.

### Task C — Senate historical discovery + fail-closed guard

Owner: `senior-developer`.
Files: `pipeline/sources/senat.py`, `tests/test_senat_source.py`,
`tests/fixtures/senat_*`.

Acceptance:
1. `fetch_historical_guids(["1990"])` follows the two-step flow and returns
   **128** unique GUIDs; `["2024"]` returns **134**; the sets differ.
2. A `HistoricalDiscoveryError` is raised if two requested legislatures yield
   identical GUID sets, or if a legislature yields zero.
3. `_historical_legislature_labels()` returns 10 labels (`1990` … `2024`) from
   the live select, or is removed in favour of the explicit map.
4. Tests use a fake client; no network; `uv run pytest tests/test_senat_source.py -q`
   passes.

Rollback: revert the task commit; discovery is not wired into ingest.

### Task D — Reproducible ingest command (after A–C)

Owner: `senior-developer`.
Files: `pipeline/cli.py`, `tests/test_cli.py` (or a new test file).

Acceptance:
1. `ingest-committees --db <copy> --legislature 2024 [--idc 1] [--dry-run]`
   reports committees/current/former/persons and writes only when not dry-run.
2. Re-running is idempotent (content fragments unchanged → `unchanged` count;
   no duplicate organisations/memberships).
3. No change to `build-corpus` default behaviour.

Rollback: revert the task commit; the command is additive.

### Task E — Redteam verification (after A–D)

Owner: `code-reviewer` + `reality-checker`.
Acceptance:
1. Every claim in this plan is checked against code/output; no claim accepted
   without a command and captured output.
2. The diff is reviewed for silent behaviour changes, especially group filters.
3. A copy-DB impact report compares `/api/coverage`, `/api/traseism/overview`,
   person profiles and the audit baseline before/after a committee ingest.

## 5. Rollback playbook

- **Code:** every task lands as its own commit on `fix/data-completeness-recovery`.
  Rollback is `git revert <sha>`. Nothing reaches production until the PR is
  merged and CI is green.
- **Dataset:** production is pinned by `data/latest-release.txt` and the release
  asset digest. A bad release is rolled back by restoring the previous tag in
  the marker (PR) and re-running deploy verification; the old asset remains
  immutable on GitHub.
- **Database copy:** never overwrite the release asset; always build on a copy
  and verify `sha256sum` + `PRAGMA integrity_check` before upload.
- **Render:** `autoDeployTrigger: checksPass` means a red CI blocks deploy; a
  bad deploy is reverted by re-pinning the previous release and redeploying.

## 6. Declared gaps (honest)

- Senate historical **profile ingestion** is not wired; discovery is fixed and
  guarded, but the copy-DB identity/impact report is outstanding.
- Committees are stored as data; public API/UI exposure is a separate feature.
- `cdep.ro` is unreachable from GitHub Actions; local ingest → release asset
  remains the supported path.
- The 2 `index_reconciliation` baseline findings cannot be evaluated in CI
  without the source-page cache; they are reported as `not evaluated`.
