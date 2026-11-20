# Master Integration Blueprint — Parlament Deschis (supersedes `docs/MASTER-STRATEGY.md`)

**Document type:** Final integration and blueprint authoring (read-only session).  
**Date:** 2026-11-20.  
**Author:** @supervisor-architect (Master Supervisor).  
**Status:** Ready for parent agent to present/save. **No product file, DB, workflow, test or configuration was modified in this session.**  
**Authority order:** `/tmp/opencode/supervisor-input-2.md` (D2, six-worker consolidated reconnaissance, 2026-11-20) > this blueprint > `docs/MASTER-STRATEGY.md` (MS, 967 lines, earlier strategy) > `docs/DATA-ENRICHMENT-RESEARCH.md` (DR, evidence base). Where D2 contradicts MS or DR, **D2 wins** and the contradiction is recorded in §1.

**Citation key:** `D2:L21` = `/tmp/opencode/supervisor-input-2.md` line 21; `MS:513` = `/home/nedaktov/parlament-deschis/docs/MASTER-STRATEGY.md` line 513; `DR:294` = `/home/nedaktov/parlament-deschis/docs/DATA-ENRICHMENT-RESEARCH.md` line 294. Citations to source code are relative to `/home/nedaktov/parlament-deschis` unless marked `N4:` (NedCode4 repo).

---

## 1. Red-team verdict on prior assumptions (mandatory, first substantive section)

### 1.1 Overturned and corrected claims

Each row: **old claim → verified truth → evidence → consequence for plan.** Every item below is a mandatory correction to MS and/or the user brief as inherited from the earlier strategy.

| # | Old claim (source) | Verified truth (2026-11-20) | Evidence | Consequence for plan |
|---|---|---|---|---|
| RT-01 | "Target is 281.ro; we will add votes/UX to the 281.ro codebase" (user brief; MS:23 names only local repo but leaves ambiguity) | **No 281.ro codebase exists locally.** Filesystem search found no directory/repo/remote named 281; only 4 markdown files mention 281.ro, all our own research/strategy docs. `docs/remediation/STRATEGY.md:44` explicitly says the "469 current MPs from 281.ro API" claim is false and must be removed ("No code/data source exists; NOT PROVEN as a real integration"). | D2:L6-L9 | All implementation targets `parlament-deschis`. Any AP that writes to "281.ro" is **impossible in this workspace** and is deleted from the roadmap. 281.ro becomes an external CC-BY cross-check + UX inspiration only (Plan A, §6.1). |
| RT-02 | "281.ro is our product / we can ship there" | 281.ro is a **separate live product**: routes ACASĂ/DEPUTAȚI/SENATORI/PARTIDE/JUDEȚE/LEGI/TOPURI/RADAR/PENSII/COMPARĂ/QUIZ/ÎNTREABĂ/GHID/LEGISLATURI/GRAFICE/DESPRE + `/api`, `/press`, `/despre`, `/baza-legala`, `/roadmap`, `/errata`; counts 5,158 dosare, 10 legislaturi, 335/3,773 deputy mandates, 134/1,385 senate mandates; CC-BY 4.0; "semnal, nu verdict". Its public GitHub repo `zattarateo-cpu/281` is **404**. | D2:L6 | No repo handoff, no remote, no credentials. Plan A is explicitly **blocked** until a repo is supplied; design artefacts only (§6.1). |
| RT-03 | Old cdep vote URL `/pls/legis/legis_pck.htp_evot2015` (inherited from older research path) is the entry point | That URL is **404**. Working path is `https://www.cdep.ro/ords/pls/steno/evot2015.xml?par1=1&par2=YYYYMMDD` (HTTP 200, 5,394 B for `20261118`) and `.../evot2015.nominal?idv=VOTID&idl=1` (HTTP 200, 94,483 B for VOTID 37526). | D2:L21; DR:413-414 already carry the correct `/ords/pls/steno/` path | Fixture capture uses only `/ords/pls/steno/`. Any code/document containing `legis_pck.htp_evot2015` is a defect to fix in W1 documentation sweep. |
| RT-04 | "`par1` chamber meaning is UNVERIFIED — resolve by fixture before writing parser" (MS:204, MS:378, DR §7 not applicable) | **VERIFIED:** `par1=1&par2=YYYYMMDD` = day index; `par1=2&par2=VOTID` = nominal list (proven by the nominal page's own XML link). Other `par1` values UNVERIFIED (empty bodies). | D2:L23 | W1 P0 is **downgraded** from "discover semantics" to "capture fixtures to lock already-known semantics and detect drift". No parser is blocked on a discovery task; it is blocked on fixture capture only. |
| RT-05 | "`CAMERA` code values UNVERIFIED" (MS:204, MS:378) | **VERIFIED:** `CAMERA=2` = Camera Deputaților, `CAMERA=0` = Camere reunite (day XML for 20261110), `CAMERA=1` = Senat (observed in nominal rows / joint votes). **Day-level `CAMERA=1` remains UNVERIFIED** — resolver: capture a senate-only day fixture. | D2:L24 | Parser maps 2→`cdep`, 1→`senat`, 0→`joint`. Do **not** treat 0 as "deputies". Add one senate-day fixture or record `day_camera_1` as UNVERIFIED with named resolver in W1 CP. |
| RT-06 | "`idv == VOTID` UNVERIFIED" (MS:204, MS:378) | **VERIFIED three ways:** URL `idv=37526`; nominal XML `VOTID` element = 37526; tally DA=245, `-`=1 matches official totals (246 rows). | D2:L25 | `native_vote_id` is taken directly from `idv`/`VOTID`; no fuzzy vote key. A4 assertion enforces equality. |
| RT-07 | "21.01.1991 is a future-date birth-date anomaly to reject" (MS:274, MS:448, MS:R14, MS:CP-2.3) | **Misread column.** The 1990 `cam=2` birth table has an **extra column "Membru din"**; `21.01.1991` is a membership date, not a DOB. Real DOB example: Iorga Eugenia `1954-01-01`. 1990 `cam=1` has no such column. | D2:L38, D2:L43 | Replace "future-date rejection test" with **header-driven parsing** (parse by header text, never fixed index) plus a test asserting `Iorga Eugenia == 1954-01-01` and `!= 1991-01-21`. The old R14 mitigation is wrong and is stricken. |
| RT-08 | Naive `cam=1`=Deputies, `cam=2`=Senate | **Opposite is verified.** Page titles: `cam=1` = "Lista senatorilor nascuti..." (Senat), `cam=2` = "Lista deputatilor nascuti..." (Camera Deputaților). Votes `CAMERA` agrees (RT-05). | D2:L37 (DOB), D2:L24 (votes) | One canonical chamber map used by both DOB and vote parsers: `{1: 'senat', 2: 'cdep', 0: 'joint'}`. A mis-map here would silently corrupt 196 senate DOBs. |
| RT-09 | "`cmd_enrich` honours `--db`; CLI defaults to dry-run" (implied by MS:274, MS:446) | **`cmd_enrich` ignores `args.db`** (`cli.py:260-272`); `enrich.py:368-372` hardcodes DB via `get_session()`; **`cli.py:767` sets `dry_run=False`** while module default is `True` → CLI is **apply-by-default**. | D2:L39 | Fix `enrich.py:368-372` (add `db_path`/`cache_path`), `cli.py:260-272` (honour `args.db`), `cli.py:767` (align both to dry-run-by-default) **before any enrichment command runs** (W2 AP-2.01). Until then, every enrichment invocation is a corruption hazard. |
| RT-10 | "FSN→FDSN→PDSR→PSD should resolve to **one** Party Facts ID" (DR:332, MS:512/CP-3.2) | **Four distinct IDs:** FSN=**958**, FDSN=**276**, PDSR=**1034**, PSD=**120**. | D2:L48 | Delete MS:AP-3.2/CP-3.2 as written. Create `party_alias_map` with four rows + lineage links. Do not touch `organization.previous_party_id`/`successor_party_id`/`short_name`/`alt_labels`/dates; do not add a `partyfacts` scheme to `person_identifier` (party-level, not person-level). |
| RT-11 | "PopuList licence: open / COPY" (DR:207, DR:264, MS:511) | **UNVERIFIED:** OSF node_license `null`, no LICENSE file → **CONDITIONAL/XCHECK**. Also `dataset_key='pop'` = Poll of Polls (Politico), **not** PopuList; PopuList is `dataset_key='populist'` with 6 ROU rows, `year_last=2019`, AUR absent. | D2:L46-D2:L47 | PopuList values never copied into CC-BY release until licence resolved (resolver: written permission or explicit licence file). Join key is `(country='ROU', dataset_key, dataset_party_id)`; `'pop'` rows must be quarantined as wrong-source. |
| RT-12 | "robots policy is uniform; cdep/senat only" (MS:§3.4, DR §4) | **Per-host signals differ:** 281.ro robots (200, 466 B) has `User-agent: * Allow: /`, allows ClaudeBot/GPTBot/Google-Extended/PerplexityBot, **disallows CCBot**, plus Sitemap. vot-parlament.ro robots (200, 2,745 B, Cloudflare) carries `Content-Signal: search=yes,ai-train=no,use=reference` and disallows many training bots, with `User-agent: * Allow: /`. cdep robots 37 B `Disallow: /declaratii/` only; senat 404. | D2:L61 | Acquisition policy becomes host-specific. vot-parlament: research/reference retrieval permitted, **AI-training reuse prohibited** — no corpus training on its body; keep attribution. 281.ro: do not send CCBot-class clients. Never crawl `/declaratii/`; senat 404 is not permission to be impolite. |
| RT-13 | "NedCode4 `just`/skills apply to the whole programme" | NedCode4 commands apply **only** in `/home/nedaktov/Desktop/NedCode4`. There is no justfile in `parlament-deschis`. Product commands run only in `/home/nedaktov/parlament-deschis`. | D2:L11; MS:845-856 | Repo-scope banner pasted into every command block (§2.7, §4.0). Cross-repo command = checkpoint FAIL, not a warning. |
| RT-14 | "MCP tool delta 31 vs 33 is UNVERIFIED" (MS:873, MS:R28) | **Resolved:** 48 tools total — **33 chrome-devtools**, **8 opencode**, **7 shadcn**. opencode names fully known (worktree_create, session_move, models, list/read_mcp_resources, session_rename, worktree_list/remove). No subagent/task tool visible to workers (parent-only). | D2:L10 | Strike MS:R28 and the MS:§8.2 delta row. Tool schedule (§3) uses 33/8/7 counts; unknown tool names resolved by live `search()` discovery, never invented. |
| RT-15 | "NedCode4 has 20 skills" (N4 generated facts) vs "21 skills" (worker recce) | Both observed: D2 reports 21 skills; `N4:AGENTS.md` generated block counts 20 (git-tracked `.opencode/skills/*/SKILL.md`) and 17 agents. **Minor delta UNVERIFIED** — resolver: re-run `just docs` and count at execution time. | D2:L11; `N4:AGENTS.md` generated block | Do not state a skill count in any checkpoint without the count command output. Agents = 17 (both agree). |
| RT-16 | "Vote positions allow `person_id = NULL` for unknown MPs" (MS:390, MS:CP-1.5, MS:R12) | Model spec says **`VotePosition.person_id NOT NULL`**. Resolution order: `cdep_mandate {ch}:{leg}:{idm}` → `cdep_idm` **only if** person has matching chamber+legislature mandate → `cdep_person` with same check → **quarantine**. Measured on real DB: 246 links → 146 `cdep_mandate`, 245 `cdep_idm`, union 245, 1 unresolved (`deputies:2024:87` Csoma Botond), **5 disagreements** (cdep_idm points to stub without 2024 mandate). | D2:L29, D2:L31 | Unresolved positions are **not inserted** into `vote_position`; they are recorded in `VoteImportRun.report` quarantine JSON with `idm_raw/cam_raw/name_raw/raw_vote` + reason and an audit warning. Never name-match; never call `PersonResolver.resolve()` (`identity.py:110-130`), which creates persons. |
| RT-17 | "Capture fixtures to discover XML element form / VOT tokens" (MS:378, MS:204) | **VERIFIED:** day XML has exactly 9 text elements, no attributes, ISO-8859-2, 16 rows for 20261118; nominal XML exactly 6 elements, 246 rows for 37526, tokens `DA` and `-` observed. `NU`/`AB` are implied by totals but **UNVERIFIED as literal tokens**; test vote VOTID 37515 "Vot test 1" exists — exclusion policy **UNVERIFIED**. | D2:L22, D2:L25 | A2/A5 assert exact tag sets. Add `vote_tokens_nu_ab` and `test_vote_exclusion` as UNVERIFIED items with resolvers (capture a vote containing NU/AB; W5 sign-off on test-vote policy). |
| RT-18 | "vot-parlament API contract stable" | `/votes/export.csv` (200, 1,698,092 B, 22 exact columns) and `/votes/37526.json` (200, 126,323 B) work; **`/api/votes/37526` is 404**; stable API contract **UNVERIFIED**. | D2:L27 | Pin the 22-column header and JSON top-key set in a contract test (A7/A8). Treat any drift as `DATA_UNAVAILABLE`, never a strict-build failure. |
| RT-19 | "SenateHistory/PartyTimeline defect lines UNVERIFIED" (MS:696, MS:706, MS:740-741) | **Resolved:** `SenateHistory.tsx:67-69` label over `reduce` at `:68`, `senateStatCoverage` at `:82-85`; `PartyTimeline.tsx:123-125` label "Total switches" but value `datedJoins` at `:124`. | D2:L57 | Fix with exact lines; no `grep -n` resolver needed. Strike the `[UNVERIFIED]` markers from the 16-defect list. |
| RT-20 | "W7 counted 31 chrome-devtools, 7 shadcn, 8 opencode" (MS:873) | 33 / 7 / 8 (RT-14). | D2:L10 | See RT-14. |
| RT-21 | "Fixtures: 22 files" (D2:L14) vs "23 files ~1,033,300 B" (D2:L62) | Both appear in D2; **minor internal delta UNVERIFIED** — resolver: `find tests/fixtures -type f | wc -l` at execution; do not assume either number. | D2:L14, D2:L62 | State the count with command output in CP-2 baseline; never as a bare assertion. |
| RT-22 | "audit baseline error_findings 275 (223 mandate_coverage + 50 overlap + 2 index_reconciliation); 10 checks in CHECKS" | VERIFIED as stated; new checks must be registered in `audit.py:973-984` and baselined deliberately. `test_prepare_db.py:27-28`, `test_db_schema.py:360` assert shipped `journal_mode=delete`. | D2:L62-D2:L63 | Every new audit check lands in the same commit as its baseline delta; strict output must remain `275 known errors, 0 new errors` or an approved, reviewed delta. |

### 1.2 Claims that survive red-teaming (do not re-litigate)

- Fail-closed data pipeline, strict collect → strict audit → immutable `data-${run_id}-${attempt}` tag → 3-asset release → pinned `data/latest-release.txt` → explicit Render API deploy → poll served tag ≤30 min (MS:70-75; D2:L16).
- Evidence discipline: 0 `evidence` errors, 0 `switch_event` errors, 0 `interval_order`, 0 `missing_start` (MS:72).
- `PoliteClient` with identifying UA, robots honouring, 2.5 s pacing, conditional GET, backoff, 429 waiting, **hard stop on CAPTCHA** (DR:78; MS:73).
- Identity rules: exact ID → auto-link; name+DOB → propose; fuzzy name → review; conflicting IDs in one legislature → never merge; QID → strong signal (DR:384; MS:130-137). All resolution stays in `pipeline/identity.py`.
- Read-only production runtime, no background polling (MS:160-162); all enrichment pre-release on copies.
- Immutable releases; only `latest-release.txt` mutable (MS:164-166).
- **No attendance score / no presence ranking** (DR:304; MS:172-174; D2:L54 "semnal, nu verdict").
- Strict audit `275 known errors, 0 new errors` with natural-identity fingerprints (MS:168-170).

### 1.3 Items now VERIFIED and removed from "fixture-first discovery" gates

`par1` semantics (RT-04), `CAMERA` map (RT-05), `idv==VOTID` (RT-06), XML/nominal element form (RT-17), DOB `cam` map (RT-08), `"Membru din"` misread (RT-07), Party Facts four IDs (RT-10), PopuList licence status and `dataset_key` trap (RT-11), robots signals (RT-12), MCP counts (RT-14), SenateHistory/PartyTimeline lines (RT-19), vot-parlament CSV/JSON shapes (RT-18). **Fixtures are still mandatory** — but as regression locks and drift detectors, not as discovery tasks.

---

## 2. Workspace and tooling report (what the "immediate first step" actually found)

All figures below were observed read-only on 2026-11-20. No files modified.

### 2.1 Repo identity and counts

| Fact | Verified value | Evidence |
|---|---|---|
| Product repo | `/home/nedaktov/parlament-deschis`, origin `nedaktov-ops/parlament-deschis.git`, `main @ 2995bfd` | D2:L8 |
| Tracked files | 257 | D2:L8 |
| Frontend files | 78: 18 pages, 29 components + 6 `ui` | D2:L14 |
| Pipeline files | 36: 6 parsers, 4 source adapters | D2:L14 |
| Tests / fixtures | 36 `test_*.py` + `conftest.py` (88 lines); fixtures 22 (D2:L14) / 23 files ~1,033,300 B (D2:L62) — delta RT-21 | D2:L14, D2:L62 |
| Backend / workflows / data-reference / scripts | 11 / 5 / 4 / 13 | D2:L14 |
| Routes | 19 | D2:L8, D2:L18 |
| Missing DOB | 275 | D2:L8, D2:L36 |
| Wikidata QIDs | 0 | D2:L8 |
| Vote table | none | D2:L8, D2:L15 |

### 2.2 DB schema summary (18 tables; no vote table)

| Table | Verified structure | Evidence |
|---|---|---|
| `person` | `db.py:104-125` | D2:L15 |
| `person_identifier` | `db.py:127-140`; unique on (scheme, identifier, legislature); schemes `cdep_mandate` 3,381 / `cdep_person` 3,381 / `cdep_idm` 335 | D2:L15, D2:L8 |
| `organization` | `db.py:157-183` | D2:L15 |
| `mandate` | `db.py:196-226`; `constituency` 100% NULL (5,273/5,273) | D2:L15, MS:59 |
| `membership` | `db.py:229-270` | D2:L15 |
| `evidence` | `db.py:273-281`; **`membership_id NOT NULL`** — vote evidence cannot attach here | D2:L15, MS:128 |
| `fragment` | `db.py:296-307`; raw-source landing zone; `_ADDED_COLUMNS` at `db.py:463-481` | D2:L15, D2:L49 |
| `event` | `db.py:323-347`; `dedup_key UNIQUE` | D2:L15 |
| Enums | `EVIDENCE_TYPES` at `:72` contains `scrutin`; `EVENT_TYPES` at `:73-86` | D2:L15 |
| `create_all` | `db.py:456-458`; `SCHEMA_VERSION=1` — new tables created by `create_all`, no Alembic migration | D2:L29, MS:202 |
| Others | `SwitchWave` after `:350`, `MergeAudit` after `:414`, `SourceLicense` slot after `:423` before `:426` | D2:L17, D2:L49 |

Working DB `data/parlament-real.db` is WAL (`db.py:447`); shipped DB is DELETE (`prepare_db.py:9,12,160,170-177`), and both local DBs are physically WAL header 2,2 with `-wal` sidecars — raw `cp` is unsafe (D2:L64).

### 2.3 Daily pipeline and CLI map

- `data.yml`: cron 03:17 UTC (`:11-20`); cache key `cdep-pages-${run_id}` (`:47-54`); **collect strict** (`:56-68`); cache save (`:70-75`); **audit strict** (`:77-81`); `prepare_db` (`:83-84`); tag `data-${run_id}-${attempt}` (`:86-89`); release 3 assets (`:91-106`); pin `latest-release.txt` at `:121` + retry loop; Render API deploy (`:146-160`); verify served tag (`:162-193`). (D2:L16)
- CLI: 15 subcommands; `build-corpus` at `:526-712`; `cmd_enrich` at `:260-272` (ignores `args.db`); `enrich` subparser at `:763-772` (`dry_run=False` default); `cmd_stats` at `:489-502`. (D2:L16, D2:L39)
- `prepare_db.py:187` already does atomic `os.replace` — reuse, do not reimplement. (D2:L40)
- Known served state: `data/latest-release.txt = data-20261117-T213500`; tags `data-20261115-T203142`, `data-20261117-T060923`, `data-20261117-T213500`, `data-initial-2026-11-14`. (D2:L64)
- Rollback workflow inputs: `platform`, `target`, `dry_run` (default true), `confirm`; Vercel Hobby only previous deployment; **Render auto-deploy remains enabled**; `.bak` conventions in use. (D2:L64)

### 2.4 Frontend route inventory

19 routes in `router.tsx:310-458`, children `:460-480`, nav `:242-289`, title map `:186-208` (D2:L18). Reusable components already present (D2:L55): `PartyComparisonMatrix`, `SankeyFlow`, `TimelineChart`, `MembershipGantt`, `SwitchTimeline`, `DataViz`, `PartyNetwork`, `Hemicycle`, `AgeDistributionRadial`, `DashboardCard`, `InfoStat`, `GroupLegend`, `ui/{Drawer,Modal,Skeleton}`. `/api/analytics/party-cohesion` exists at `api.py:804-822` but the frontend never calls it and it returns **switch rate, not vote cohesion** (D2:L55) — do not present it as vote cohesion.

### 2.5 MCP catalog — 48 tools (33 + 8 + 7)

| Namespace | Count | Names verified in this session | Discovery rule for the rest |
|---|---:|---|---|
| `chrome-devtools` | 33 | `list_pages`, `select_page`, `close_page`, `type_text`, `screencast_start`, `screencast_stop` | Remaining 27 resolved by live `search({namespace:'chrome-devtools'})` at execution time; **never guess a tool name**. |
| `opencode` | 8 | `models`, `list_mcp_resources`, `read_mcp_resource`, `session_move`, `session_rename`, `worktree_create`, `worktree_list`, `worktree_remove` | Complete. |
| `shadcn` | 7 | `get_project_registries`, `get_add_command_for_items`, `get_item_examples_from_registries`, `view_items_in_registries`, `get_audit_checklist` | Remaining 2 by live `search({namespace:'shadcn'})`. |

No `subagent`/`task` tool is visible to workers; dispatch is parent-only (D2:L10). Tool names above are the catalog signatures; tool parameters are taken from the live schema, never from memory.

### 2.6 NedCode4 recipes, skills, agents

`just --list` real output captured: `doctor`, `verify`, `verify-project`, `docs`, `docs-check`, `secrets-scan`, `ship`, and others (D2:L11). Agents: 17 in `.opencode/agents` (D2:L11; N4 generated block). Skills: 21 reported by D2 vs 20 counted in `N4:AGENTS.md` — RT-15, resolver `just docs` + recount. `just docs-check` is stale today (exit 3) per MS:872; regenerate with `just docs`, never hand-edit GENERATED blocks, stage explicit paths (never `git add -A`).

### 2.7 Explicit repo-scope boundary

```
NedCode4 ONLY (/home/nedaktov/Desktop/NedCode4):
  just doctor | just verify | just verify-project | just docs | just docs-check
  lib/secret-scan.sh | just ship | worktree_create | session_move

Product ONLY (/home/nedaktov/parlament-deschis):
  uv sync --extra dev --locked | uv run ruff check ... | uv run pytest -q
  (cd frontend && npm ci && npm run build)
  uv run python -m pipeline.cli ... audit-corpus --strict ...
  gh workflow run deploy-verify.yml / platform-rollback.yml -R nedaktov-ops/parlament-deschis

NO 281.ro REPO EXISTS. Plan A is design-only (§6.1).
```

### 2.8 No-change statement

Every worker was read-only; the supervisor read three documents plus tool outputs only. No implementation code, DB row, schema, workflow, test, fixture, release or configuration was changed. This blueprint is the sole artefact.

---

## 3. Agent Operating Recipes

### 3.0 Fleet charter — clauses binding on every role

1. **Evidence over assertion.** Every PASS pastes raw output + command string + timestamp. A check that cannot run is `NOT PROVEN`, never PASS (D2:L66; MS:110-114).
2. **Max 3 attempts** per task, then escalate to @supervisor-architect with the failing CP and raw output.
3. **No attendance score / no presence ranking**, anywhere (MS:172-174).
4. **No ingest without licence class recorded** by @worker-covariates; NC/SA/UNVERIFIED values never enter the CC-BY release.
5. **Copy-only ingestion.** All writes to `data/parlament-real.db` are forbidden; use `sqlite3 backup()` into `/tmp/opencode/*.db` (D2:L40, D2:L64).
6. **Lookup-only identity.** No `PersonResolver.resolve()` in vote/bio paths; no name-only match; no person creation (D2:L31, D2:L39).
7. **Repo scope** per §2.7. Tool names per §2.5; unknown tools resolved by `search()`, never invented.
8. **Handoff** is a signed checkpoint with raw output, exact files/lines touched, and explicit UNVERIFIED list — never a chat assertion (MS:295-303).

---

### 3.1 @supervisor-architect (Master Supervisor)

| Field | Content |
|---|---|
| **Role / mission** | Own wave sequencing, quality gates, retry budget, context handoff, final production-readiness verdict. Never implement. Never waive a non-negotiable (§3.0). |
| **Exact inputs** | This blueprint; `D2` in full; `MS` in full; `DR` in full; each worker's signed CP artefacts; live `gh`/CI output at gates. |
| **Exact files/lines to read before opening any wave** | The D2 line ranges named in that wave (§4), the cited `file:line` ranges in the APs, and `MS:106-176` (safety contract). If a line moved, re-read surrounding code and record the new line in CP evidence before authorising work. |
| **Tool-usage protocol** | Planning: `opencode.worktree_list`/`worktree_create` for isolation; `session_move` if a worktree becomes primary. Evidence: `opencode.models` only if a model id is needed (never guess). Browser proof: `chrome-devtools.list_pages` → `select_page` → screenshot/screencast via discovered tool names. Knowledge: `knowledge-memory` skill at every gate. `subagent` dispatch is parent-only — the supervisor **is** the subagent here, so it requests parent action rather than spawning unlisted tools. |
| **Prohibited assumptions** | A doc statement is true; a worker summary is evidence; local test == deploy; branch protection list known (MS:246 UNVERIFIED — resolver `gh api .../branches/main/protection`); 281.ro writable; MCP names from memory. |
| **I/O contract** | In: signed worker CPs with raw output. Out: signed wave gate (PASS/HOLD/NEEDS WORK), retry log, updated risk register (§8.1), escalation memo. |
| **Verification checklist** | [ ] every AP has a CP; [ ] every CP has raw output + timestamp; [ ] every CP has rollback + irreversible note; [ ] all non-negotiables intact; [ ] UNVERIFIED items carry resolvers; [ ] no `git add -A`; [ ] no writes to shipped DB. |
| **Decision rights** | Advance/hold wave; open retry; escalate after 3 failures; veto any source ingest until licence recorded; halt promotion; cannot waive §3.0. |
| **Definition of done** | All APs in a wave PASS with evidence and named rollback; final integration verdict issued. |
| **Escalation triggers** | Same CP fails 3×; licence conflict; CAPTCHA; WAL/data-loss risk; production proof contradicts local; any UNVERIFIED resolver itself fails; 281.ro repo demanded. |
| **Copy-paste system prompt** | ```text\nYou are @supervisor-architect, Master Supervisor for parlament-deschis. Do NOT edit product files. Authority order: /tmp/opencode/supervisor-input-2.md > this blueprint > MASTER-STRATEGY.md > DATA-ENRICHMENT-RESEARCH.md. Before opening any wave, re-read the D2 line ranges for that wave and MS:106-176. Enforce: evidence over assertion; every AP has a CP; every CP has raw output, a rollback and an irreversible-items note; max 3 attempts then escalate; no attendance score; no NC/SA/UNVERIFIED values in the CC-BY release; copy-only DB writes; lookup-only identity; repo scope (NedCode4 just* only in /home/nedaktov/Desktop/NedCode4; product commands only in /home/nedaktov/parlament-deschis; no 281.ro repo). If a check cannot run, report NOT PROVEN, never PASS. Do not advance on a worker's assertion. Paste raw output + timestamp with every verdict.\n``` |

---

### 3.2 @worker-code-audit (structure, schema, insertion points)

| Field | Content |
|---|---|
| **Role / mission** | Own the ground truth of code structure, DB schema, daily pipeline, CLI map, route table and exact insertion points for every new model/parser/subcommand. Re-audit after each wave's merges. |
| **Exact inputs** | D2:L13-L18; `D2:L60-L66` for QA overlap; the wave's AP file list. |
| **Exact files/lines to read** | `pipeline/db.py:62-86,104-140,157-183,196-226,229-270,273-281,296-307,323-347,348-350,414,423-426,456-458,463-481,489-531`; `pipeline/fragments.py:25-33,46-80`; `pipeline/cli.py:260-272,489-502,526-712,763-772,826-831,861`; `pipeline/sources/cdep_committee.py:40-136` (adapter template); `frontend/src/router.tsx:242-289,310-458,460-480,186-208`; `.github/workflows/data.yml:11-20,47-54,56-68,70-75,77-81,83-89,91-106,121,146-193`. |
| **Tool-usage protocol** | Read-only source inspection via shell/read tools; use `opencode.models` only if asked for model ids; no browser tools needed except to confirm a route renders (then `chrome-devtools.list_pages` → `select_page`). No edits. |
| **Prohibited assumptions** | That line numbers in D2 are still current (re-verify each before an AP); that a cited table exists (confirm in `sqlite_master`); that `EVIDENCE_TYPES` being declared means it is used. |
| **I/O contract** | Out: a `file:line` map with current line numbers, a schema diff inventory, and a "no-guess" list of UNVERIFIED line drifts with resolver `grep -n <symbol> <file>`. |
| **Verification checklist** | [ ] counts match D2:L14; [ ] 18 tables confirmed; [ ] no vote table today; [ ] insertion points confirmed by reading surrounding lines; [ ] every claim has `path:line`. |
| **Decision rights** | Declare a cited line stale; cannot authorise code changes or wave advance. |
| **Definition of done** | Every AP in the active wave has a confirmed target file + current line range or an explicit UNVERIFIED resolver. |
| **Escalation triggers** | Line drift >10 lines; missing file/table; two workers cite different line numbers. |
| **Copy-paste system prompt** | ```text\nYou are @worker-code-audit. Read-only. Re-verify every file:line cited in /tmp/opencode/supervisor-input-2.md and this blueprint before it is used in an action point. Report current line numbers, the exact schema from sqlite_master, the 15 CLI subcommands and the 19 frontend routes. Never edit. Never assume a line number from memory. For every stale citation give the resolver command grep -n <symbol> <file>. Output raw command evidence and a path:line map only.\n``` |

---

### 3.3 @worker-votes-etl (vote ingestion, resolution, build isolation)

| Field | Content |
|---|---|
| **Role / mission** | Deliver the dry-run importer (W1) and the full backfill (W2): models, parsers, sources, deterministic keys, person resolution, isolation tests. |
| **Exact inputs** | D2:L20-L34; fixture manifest (§5.3); licence gate from @worker-covariates; chamber map `{1:senat,2:cdep,0:joint}`. |
| **Exact files/lines to read** | `db.py:62-86,72,73-86,275-281,348-350,456-458,463-481,489-531`; `fragments.py:46-80`; `events.py:109-134` and after `:134`; `identity.py:110-130` (resolve — forbidden), `ingest_corpus.py:192-209` (lookup pattern); `cli.py:526-712,489-502,826-831,861`; `pipeline/sources/cdep_committee.py:40-136`; `audit.py:973-984`; `ci.yml`, `data.yml`, `Dockerfile`, `backend/main` (isolation grep targets). |
| **Tool-usage protocol** | Fixture capture: `PoliteClient` only, via new dev-only `scripts/capture_vote_fixtures.py`; 2.5 s pacing, UA, conditional GET; **hard stop on CAPTCHA**; no `/declaratii/`; vot-parlament retrieval is research/reference only (RT-12). Parser work: `test-driven-development` skill (failing test first), `systematic-debugging` on mismatch. Browser proof of any vote UI belongs to @worker-frontend-stats, not here. |
| **Prohibited assumptions** | Old `/pls/legis/...` URL; `par1`/`CAMERA`/`idv` unknown (RT-04/05/06 — VERIFIED); that NU/AB literal tokens exist (UNVERIFIED); that test votes are excluded (UNVERIFIED); that `idv` is anything but `VOTID`; that `PersonResolver.resolve()` is allowed; that `person_id` may be NULL; that vot-parlament failure may fail strict build. |
| **I/O contract** | In: fixtures + manifest + licence class. Out: models `Vote`, `VotePosition`, `VoteImportRun`; files `pipeline/sources/votes_cdep.py`, `votes_thirdparty.py`, `pipeline/votes.py`, `scripts/capture_vote_fixtures.py`, `tests/fixtures/votes/*`, `tests/test_votes_cdep_parser.py`, `test_votes_thirdparty_contract.py`, `test_votes_dry_run.py`, `test_votes_build_isolation.py`; raw pytest output; UNVERIFIED list. |
| **Verification checklist** | A1–A16 all PASS (§5.4); person count 3,388 unchanged; `cdep_mandate` 146 / `cdep_idm` 245 / union 245 / 1 unresolved / 5 disagreements reproduced; no writes before gate; third-party failure → `DATA_UNAVAILABLE`. |
| **Decision rights** | Parser field mapping and confidence per source (`official_ledger` cdep / `community` third-party). Cannot change identity rules, cannot touch `data.yml`, cannot promote a release. |
| **Definition of done** | All 16 assertions green on the copy; idempotency proven; strict build stays green with third-party down; zero persons created. |
| **Escalation triggers** | Fixture disagrees with verified semantics; unresolved rate >1/246; any person created; cdep strict gate fails; NU/AB token not found; test-vote policy unresolved. |
| **Copy-paste system prompt** | ```text\nYou are @worker-votes-etl. Read D2:L20-L34 and the exact file:line list in section 3.3. VERIFIED facts: par1=1/par2=YYYYMMDD is day index, par1=2/par2=VOTID is nominal; CAMERA 2=cdep,1=senat,0=joint; idv==VOTID; day XML 9 text elements, no attributes, ISO-8859-2; nominal XML 6 elements. Use ONLY /ords/pls/steno/ URLs, never /pls/legis/. Create pipeline/sources/votes_cdep.py, votes_thirdparty.py, pipeline/votes.py, scripts/capture_vote_fixtures.py, tests/fixtures/votes/*, tests/test_votes_cdep_parser.py, test_votes_thirdparty_contract.py, test_votes_dry_run.py, test_votes_build_isolation.py. VotePosition.person_id is NOT NULL; unresolved positions go to VoteImportRun.report quarantine, never NULL person_id. Resolution order cdep_mandate -> cdep_idm (with chamber+legislature mandate check) -> cdep_person (same check) -> quarantine. NEVER call PersonResolver.resolve() (identity.py:110-130); NEVER name-match; NEVER write outside a sqlite backup() copy. Keys: vote=source:native_vote_id, position=(vote_key,person_id), run=sha256(fixtures||versions||dry_run). Third-party failure = DATA_UNAVAILABLE, never strict failure. Paste raw pytest output and the 16 assertion results.\n``` |

---

### 3.4 @worker-enrichment-ops (DOB backfill, CLI/DB safety, daily pipeline wiring)

| Field | Content |
|---|---|
| **Role / mission** | Fix the CLI/DB defects, backfill the 275 missing DOBs with header-driven exact-match ingestion, wire enrichment into `data.yml` safely, preserve identity/genealogy invariants. |
| **Exact inputs** | D2:L35-L44; 275/268/7 coverage map; 7 idm values `38,106,192,285,286,319,321`; chamber map RT-08. |
| **Exact files/lines to read** | `enrich.py:368-372`; `cli.py:260-272,763-772`; `db.py:after 104` (`person_attribute`), `275-281` (do not touch), `463-481`; `data.yml:81,83`; `prepare_db.py:9,12,160,170-177,187`; `identity.py`; `sources/client.py`; `test_prepare_db.py:27-28`, `test_db_schema.py:360`. |
| **Tool-usage protocol** | `PoliteClient` only; cdep birth tables `structura2015.de?leg=YYYY&par=V01..V12&cam=1|2`; 2.5 s pacing; no `/declaratii/`. `test-driven-development` for `test_enrich_birth_dates.py`; `systematic-debugging` on any count drift. Backup with `sqlite3 backup()` (never `cp`; WAL header 2,2). |
| **Prohibited assumptions** | `args.db` honoured (it is not, RT-09); CLI dry-run default (it is not); name matching sufficient (never); `21.01.1991` a DOB (it is "Membru din", RT-07); `cam=1` deputies (RT-08); fixed column indices (header-driven only); `mandate.constituency` joinable (100% NULL); Wikidata bulk `/sparql` allowed (disallowed — cached/dump flows). |
| **I/O contract** | Out: edits to `enrich.py:368-372`, `cli.py:260-272,767`; `person_attribute` model after `db.py:104`; new `pipeline/parse/…birth_dates.py`, source module, `tests/test_enrich_birth_dates.py`, `test_enrich_cli_db.py`, `test_wal_backup.py`, `test_cdep_birth_dates_source.py`, `test_db_schema.py` extension; `data.yml` step between `:81` and `:83`; raw pytest + pre/post SHA-256 proofs. |
| **Verification checklist** | [ ] 275 missing → 268 `cdep_mandate` (72 deputies + 196 senate, 1 in both) + 7 `cdep_idm` + 0 neither + 0 duplicates; [ ] Stoica idm 285 vs 286 kept distinct; [ ] `Iorga Eugenia == 1954-01-01`; [ ] person count 3,388 before/after; [ ] merge_audit unchanged; [ ] SHA-256 over sorted identifiers / existing birth dates / org genealogy+short_name / `evidence.membership_id` identical; [ ] cache key `cdep-birthdates-${run_id}` saved on failure. |
| **Decision rights** | Source order and confidence per source; cannot change `Evidence.membership_id NOT NULL`, cannot modify `organization.short_name`/genealogy, cannot create persons, cannot edit `data.yml` without W1+qasentinel sign-off. |
| **Definition of done** | Dry-run makes zero writes; apply-on-copy satisfies write conditions (exact idm, header-indexed DOB, `1900-01-01 <= dob <= min(today, legislature.start)`, `birth_date IS NULL`, one distinct DOB, person pre-exists); conflicts stored `status='conflict'`; workflow uses `s.backup(d)` and `prepare_db.py:187` atomic replacement. |
| **Escalation triggers** | Coverage below ~200 filled; `cam=2` only ≤72 reachable; 7 unmatched fallback fails; any name-only merge; any DOB outside bounds; WAL copy mismatch. |
| **Copy-paste system prompt** | ```text\nYou are @worker-enrichment-ops. Read D2:L35-L44. FIRST fix enrich.py:368-372 (add db_path/cache_path), cli.py:260-272 (honour args.db), cli.py:767 (make dry-run the default in both parser and module). VERIFIED: cam=1=Senat, cam=2=Camera Deputatilor; the 1990 cam=2 page has an extra "Membru din" column and 21.01.1991 is that column, NOT a DOB. Parse by HEADER, never fixed index. 275 missing DOB = 268 addressable via cdep_mandate (72 deputies, 196 senate, 1 in both) + 7 via cdep_idm (38,106,192,285,286,319,321), 0 neither, 0 duplicates; keep Stoica 285 and 286 distinct. person_attribute after db.py:104; DO NOT touch Evidence.membership_id NOT NULL. Back up with sqlite backup() (WAL), never cp. Write conditions: exact idm, header-indexed DOB, 1900-01-01 <= dob <= min(today,legislature.start), person.birth_date IS NULL, one distinct DOB, person pre-exists; conflicts -> status='conflict'. Wire into data.yml between :81 and :83 with cache key cdep-birthdates-${run_id}, dry-run then apply on copy, continue-on-error, prepare reads enriched copy. Prove no merges: person count 3388, merge_audit unchanged, SHA-256 over identifiers/birth dates/org genealogy/evidence.membership_id identical. Never create persons.\n``` |

---

### 3.5 @worker-covariates (licences, SourceLicense registry, external tables)

| Field | Content |
|---|---|
| **Role / mission** | Hold the licence veto; author the SourceLicense registry and quarantine design; deliver party alias map, speech/election/benchmark/context tables and the BenchmarkLabel contract. |
| **Exact inputs** | D2:L45-L52; DR §5 (247-274) and §3.6 (195-219); live licence quotes captured 2026-11-20. |
| **Exact files/lines to read** | `db.py:after 423 before 426` (SourceLicense), `463-481` (`_ADDED_COLUMNS`), `72,73-86`; `export.py:105,233-249,352`; `audit.py:973-984`; `cli.py` CLI patterns; `backend/routers/exports.py:190-203`; `export/report:139-159`; `organization` block `db.py:157-183` (read-only — do not modify). |
| **Tool-usage protocol** | Licence quotes captured via web fetch/read and stored with URL + verbatim string + `verified_on` (never paraphrased as a quote). Per-file verification for CHES/chesdata.eu (2024 wave UNVERIFIED). `test-driven-development` for `test_license_quarantine.py`. |
| **Prohibited assumptions** | A source's own footer governs facts (Law 8/1996 art. 9 prevails — DR:252); SA/NC may be copied into CC-BY; PopuList licence known (UNVERIFIED, RT-11); `dataset_key='pop'` is PopuList (it is Poll of Polls, RT-11); four-party lineage collapses to one ID (RT-10); `partyfacts` belongs in `person_identifier` (party-level, not person-level). |
| **I/O contract** | Out: `SourceLicense` model + seed rows; `party_alias_map`, `org_identifier`, `party_score`, `election_result`, `benchmark`, `context_year`, `speech` models; `export.py` guards; `audit.py` check; `test_license_quarantine.py`; `BenchmarkLabel.tsx` text contract; sign-off checklist (§7.6); exact attribution strings (§5.6). |
| **Verification checklist** | [ ] every external row has `source_name` FK + `license_flag` snapshot + `redistributable` + `source_url` + `dedup_key` + repeated CHECK; [ ] `redistributable=1` only for `CC0-1.0|CC-BY-4.0|OGL-ROU-1.0`; [ ] four Party Facts IDs 958/276/1034/120 in alias map; [ ] zero writes to `organization.*`; [ ] XCHECK rows absent from all exports. |
| **Decision rights** | **Veto** on any source ingest until licence class recorded. Cannot be overridden by supervisor or release owner. |
| **Definition of done** | Strict audit green with `check_license_quarantine` registered; zero NC/SA/unverified values in exportable tables; every benchmark/party_score row traceable to a Fragment + licence quote + date. |
| **Escalation triggers** | Any NC/SA/UNKNOWN licence; CAPTCHA; `/declaratii/`; personal data; unresolved party identity; PopuList permission sought; `partyfacts.github.io` 404 / site licence UNVERIFIED (resolver: Dataverse API metadata + written confirmation). |
| **Copy-paste system prompt** | ```text\nYou are @worker-covariates. Hold the licence veto. Read D2:L45-L52 and DR:247-274. VERIFIED licence quotes: 281.ro CC-BY-4.0 with EXACT attribution "281.ro · Registrul neoficial al Parlamentului României"; Party Facts Dataverse API CC0 1.0 doi:10.7910/DVN/TJINLQ (site licence UNVERIFIED, partyfacts.github.io 404); CHES EUI archive CC BY 4.0 hdl.handle.net/1814/69975 (chesdata.eu 2024 per-file UNVERIFIED); V-Dem CC BY-SA 4.0; IPU CC BY-NC-SA 4.0; OpenSanctions CC BY-NC 4.0; PopuList UNVERIFIED (OSF node_license null, no LICENSE) -> CONDITIONAL/XCHECK. Party Facts join key (country='ROU', dataset_key, dataset_party_id); dataset_key='populist' is PopuList (6 ROU rows, year_last=2019, AUR absent), 'pop' is Poll of Polls - quarantine it. FSN=958, FDSN=276, PDSR=1034, PSD=120 are FOUR IDs. Create SourceLicense after db.py:423 before :426 with CheckConstraint redistributable=0 OR license_id IN ('CC0-1.0','CC-BY-4.0','OGL-ROU-1.0'); add party_alias_map (not person_identifier). Do NOT modify organization.short_name/genealogy/alt_labels/dates. Add _assert_exportable at export.py:105 and export exclusions at :233-249; register check_license_quarantine in audit.py CHECKS :984. BenchmarkLabel text: "External benchmark · {source} · {license_id} · not part of this project's CC BY 4.0 dataset". Paste raw test output and the signed licence table.\n``` |

---

### 3.6 @worker-frontend-stats (two-frontends, UX, statistics contracts)

| Field | Content |
|---|---|
| **Role / mission** | Own Plan A (design-only for 281.ro) and Plan B (implementable local UI), the 16 defects, and the data contracts/filters/i18n/a11y of every new statistical view. |
| **Exact inputs** | D2:L53-L59; §6 of this blueprint; resolved defect lines (RT-19); statistics definitions from `DR:390-402` and `MS:770-790`. |
| **Exact files/lines to read** | `router.tsx:186-208,242-289,310-458,460-480`; `index.css:5-45,51-72,76-89,139-169,198-201,203-227`; `tailwind.config.js:8-28`; `api/client.ts`; `frontend/src/i18n/*`; `LiveDashboard.tsx:97-141,196`; `DashboardCard.tsx:76-95,97-108`; `InfoStat.tsx:48-82`; `CrossChamberFlow.tsx:24-27,55-80`; `DataQualityGauge.tsx:37-53,108,134`; `AgeDistributionRadial.tsx:113,125`; `InstitutionalView.tsx:71-74`; `Mps.tsx:82-106,395`; `Committees.tsx:239-243`; `Demographics.tsx:44-57`; `PartyComparison.tsx:46,51`; `CommitteeControl.tsx:122-125`; `SenateHistory.tsx:67-69,82-85`; `PartyTimeline.tsx:123-125`; `Traseism.tsx:134-164,845-866` (reference pattern). |
| **Tool-usage protocol** | **Run `modern-web-guidance` FIRST for any HTML/CSS/client-JS change** (mandatory). Then `design-taste-frontend`/`impeccable`; `break-ui` for worst-case data; `chrome-devtools.list_pages` → `select_page` → screenshot at target viewport for evidence; `shadcn.get_audit_checklist` after creating components. No `subagent` tool. |
| **Prohibited assumptions** | A number without denominator is self-explanatory; `div role=button` is a button; placeholders are data; a major-version framework upgrade is in scope (it is not — MS:757-759); 281.ro repo is available; `/api/analytics/party-cohesion` is vote cohesion (it is switch rate, D2:L55); attendance ranking is acceptable. |
| **I/O contract** | Out: quick-win PR + wave-coupled PRs; components per §6.2; ro/en keys for every string; `aria-sort`; SVG text alternatives; browser screenshots with URL + viewport; defect status table. |
| **Verification checklist** | [ ] all 16 defects closed with before/after proof; [ ] WCAG AA contrast; [ ] `type="button"`, no `onKeyPress`; [ ] no hardcoded `fill="white"` (CSS vars); [ ] every number shows scope + denominator + source; [ ] Plan A file list is design-only (no product edits). |
| **Decision rights** | Component composition and copy. Cannot invent statistics (definitions are governed by evidence), cannot change API semantics without the data workers, cannot bypass design/web gates. |
| **Definition of done** | Browser proof at target viewport; no unlabelled statistic; ro/en keys complete; build green; quick wins separated from wave-coupled work. |
| **Escalation triggers** | Required statistic has no endpoint; fix needs schema change; design-token ambiguity; a11y defect requires replacing a library component; 281.ro repo requested. |
| **Copy-paste system prompt** | ```text\nYou are @worker-frontend-stats. Run modern-web-guidance before any HTML/CSS/JS change. Read section 3.6 file:line list and D2:L53-L59. VERIFIED defect lines: SenateHistory.tsx:67-69 label over reduce at :68, senateStatCoverage at :82-85; PartyTimeline.tsx:123-125 label "Total switches" but value datedJoins at :124. Two plans: Plan A = 281.ro design ONLY (no local repo exists, do not write product files for it); Plan B = local parlament-deschis implementation. Reuse Traseism.tsx:134-164,845-866 for honest denominators. /api/analytics/party-cohesion (api.py:804-822) is switch rate, NOT vote cohesion - do not label it as such. Every displayed statistic states scope, denominator, sample size, missing count and source link; external benchmarks carry "external benchmark, not our data". Use type="button", no onKeyPress, WCAG AA contrast, CSS vars instead of fill="white", aria-sort on sortable tables, text alternatives for SVG, and ro+en keys for every new string. NO attendance score or ranking. Paste before/after screenshots with browser URL and viewport.\n``` |

---

### 3.7 @worker-qa-sentinel (tests, audit, rollback, proof)

| Field | Content |
|---|---|
| **Role / mission** | Own test inventory, strict-audit contract, baseline discipline, WAL-safe rollback proof, and the "NOT PROVEN" default. Independent of implementers. |
| **Exact inputs** | D2:L60-L67; MS:843-889 (deployment/checkpoint matrix); `ci.yml`; `DEPLOYMENT.md`; `VERIFICATION.md`. |
| **Exact files/lines to read** | `tests/conftest.py` (88 lines); `tests/test_prepare_db.py:27-28`; `tests/test_db_schema.py:360`; `pipeline/audit.py:973-984` (10 checks), `:375-407`, `:410-453`, `:812`; `data/reference/corpus-audit-baseline.json`; `.github/workflows/ci.yml`; `.github/workflows/platform-rollback.yml`; `vercel.json:6,14-15`; `backend/cache.py:28`; `db.py:447`; `prepare_db.py:9,12,160,170-177`; `scripts/verify-deploy.sh`; `scripts/check-deployment-status.sh`. |
| **Tool-usage protocol** | Strict audit command exactly as in MS:868; platform rollback dry-run before confirm (MS:871); browser proof via `chrome-devtools` when UI is in scope; `verification-before-completion` skill before any "done" claim; `knowledge-memory` to store results. |
| **Prohibited assumptions** | Tests were run in reconnaissance (they were **not**, D2:L66); strict output will be 275/0 without running it; branch protection known; `deploy-all.sh` safe (`git add -A` at `:21`); Render rollback disables auto-deploy (it does not); raw `cp` safe on WAL DBs. |
| **I/O contract** | Out: CP evidence table with raw output + timestamp; 13-checkpoint suite for W1 (CP-1.1..CP-1.13 per D2:L65); failure signatures; rollback ladder; irreversible-items list; `NOT PROVEN` register. |
| **Verification checklist** | [ ] 36 `test_*.py` + fixtures counted with command output (RT-21); [ ] no `test_votes.py` today; [ ] strict output `275 known errors, 0 new errors` = 223 + 50 + 2; [ ] new checks in `CHECKS` :973-984 and baselined; [ ] WAL checkpoints before copy; [ ] rollback dry-run printed before `confirm=ROLLBACK`. |
| **Decision rights** | Declare `NOT PROVEN`; block promotion on any FAIL; require raw evidence. Cannot approve product correctness alone. |
| **Definition of done** | Every CP has command + raw output + timestamp + PASS/FAIL/NOT PROVEN + rollback + irreversible note. |
| **Escalation triggers** | Test cannot run; audit output drifts; production proof contradicts local; Vercel Hobby only-one-previous limit; Render auto-deploy race (`platform-rollback.yml:145`); immutable bundle cache (`vercel.json:14-15`). |
| **Copy-paste system prompt** | ```text\nYou are @worker-qa-sentinel. Default to NOT PROVEN, never PASS without raw output + command + timestamp. Read D2:L60-L67 and MS:843-889. No tests were executed in reconnaissance; run them now. Strict audit command: uv run python -m pipeline.cli --db data/parlament-real.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json --json data/verification-report.json, expected "275 known errors, 0 new errors" (223 mandate_coverage + 50 overlap + 2 index_reconciliation). New checks must be in pipeline/audit.py CHECKS :973-984 and baselined in the same commit. Both local DBs are physically WAL header 2,2 -> use sqlite backup(), checkpoint WAL, NEVER raw cp. Rollback: gh workflow run platform-rollback.yml -R nedaktov-ops/parlament-deschis -f platform=vercel -f target=dpl_... -f dry_run=true, then confirm=ROLLBACK; Render auto-deploy stays enabled. Do not use scripts/deploy-all.sh (git add -A at :21). Paste raw output for every checkpoint and list irreversible items.\n``` |

### 3.8 Fleet interaction rules

1. No worker edits CI or `data.yml` without @worker-qa-sentinel + @supervisor-architect sign-off.
2. No ingest starts without @worker-covariates licence class in `SourceLicense`.
3. No statistic is exposed until its source table exists and @worker-votes-etl / @worker-enrichment-ops confirm provenance.
4. No UI displays a number until its denominator is defined and signed.
5. Supervisor advances waves only on signed CPs, never chat assertions.
6. Worker output always includes raw command output and exact files/lines touched.

---

## 4. Wave Execution Roadmap (exactly four waves)

### 4.0 Conventions, hierarchy and dependency graph

**Hierarchy:** Wave → Phases P0 (fixture/legal) → P1 (schema/parser) → P2 (ingest/dry-run) → P3 (API/UI) → P4 (audit/release) → Action Points (numbered, exact files/lines) → Verification Checkpoints (automated assertions with exact expected values/failure signatures) → Fail-Safe Rollbacks (exact commands) + Irreversible note. **Every AP has a CP; every CP has a rollback and an irreversible-items note. No TBD.**

```
W1 Foundation + governance + dry-run votes importer
   |  (dry-run vote schema/fixtures/licence registry established)
   v
W2 DOB backfill + daily pipeline + full votes backfill
   |  (identity/attribute tables + proven copies + served votes)
   v
W3 Covariates + committees + speeches + elections + benchmarks
   |  (all statistical source tables present and quarantined)
   v
W4 Frontend / API / export overhaul
      (views consume only tables whose CPs PASS)
```

Global rollback primitives (referenced by CP tables as `GIT`, `SQL`, `REL`, `PLAT`, `N4`):

- `GIT` = `git revert --no-edit <sha>` (explicit paths staged with `git add <path1> <path2>`; **never `git add -A`**).
- `SQL` = `python3 -c "import sqlite3; s=sqlite3.connect('data/parlament-real.db'); s.execute('PRAGMA wal_checkpoint(TRUNCATE)'); d=sqlite3.connect('/tmp/opencode/pre-cp.db'); s.backup(d); d.close(); s.close()"` then, on the **copy only**, `DROP TABLE <new_table>;`.
- `REL` = pin revert: `printf 'data-20261117-T213500\n' > data/latest-release.txt && git add data/latest-release.txt && git commit -m 'revert release pin to data-20261117-T213500'` (previous tags per D2:L64), then the existing explicit Render API trigger in `data.yml:146-160`.
- `PLAT` = `gh workflow run platform-rollback.yml -R nedaktov-ops/parlament-deschis -f platform=<vercel|render> -f target=<dpl_…> -f dry_run=true` then `-f dry_run=false -f confirm=ROLLBACK`.
- `N4` = in `/home/nedaktov/Desktop/NedCode4`: `just docs` (regenerate) + `git checkout -- <generated paths>`; never hand-edit GENERATED blocks.

---

### 4.1 W1 — Foundation, governance, dry-run votes importer

**Goal.** Tell the truth in docs/CI, stand up the licence registry, and land `Vote`/`VotePosition`/`VoteImportRun` with parser+fixtures+dry-run only — no production promotion.  
**Value / effort.** Highest value÷effort: ~3–5 days; near-zero data risk (all writes on copies).  
**Dependencies.** None (entry wave). Requires licence class from @worker-covariates before any ingest command.

| Phase | APs |
|---|---|
| P0 | AP-1.01 baseline counts · AP-1.02 git state · AP-1.03 licence classes · AP-1.04 capture 8 vote fixtures + manifest · AP-1.05 lock verified field facts |
| P1 | AP-1.06 models · AP-1.07 enum/index edits · AP-1.08 `votes_cdep.py` parser/source · AP-1.09 `votes_thirdparty.py` · AP-1.10 SourceLicense + quarantine DDL |
| P2 | AP-1.11 resolution order · AP-1.12 `VoteImportRun` + dry-run on copy · AP-1.13 16 assertions · AP-1.14 build isolation |
| P3 | AP-1.15 docs truth D1–D14 · AP-1.16 CI hardening · AP-1.17 definition collisions + quick-win UI |
| P4 | AP-1.18 audit checks · AP-1.19 full local gate · AP-1.20 deploy-verify (no votes in release yet) |

**P0 — Fixture / legal gate**

- **AP-1.01** Confirm baseline: `uv run python -c "import sqlite3; c=sqlite3.connect('data/parlament-real.db'); print({t:c.execute('select count(*) from '+t).fetchone()[0] for t in ['person','mandate','membership','event','organization']})"`. Expect `person 3388, mandate 5273, membership 7349, event 7429, organization 120` (D2:L8). → **CP-1.01**
- **AP-1.02** `git rev-parse --short HEAD` → `2995bfd`; `git status --porcelain` → clean (or only this blueprint). (D2:L8) → **CP-1.01**
- **AP-1.03** @worker-covariates records COPY/XCHECK/COND classes in `SourceLicense` seed (§5.6) before any ingest; cdep facts COPY, vot-parlament CC BY COPY (research/reference use only per RT-12), 281.ro attribution string registered. → **CP-1.03**
- **AP-1.04** Run `uv run python scripts/capture_vote_fixtures.py --out tests/fixtures/votes --manifest tests/fixtures/votes/manifest.json` (new dev-only script, D2:L28) with `PoliteClient`; capture the 8 files in §5.3; record sha256, byte_count, HTTP status, `verified_on`, source URL. → **CP-1.04**
- **AP-1.05** Write `tests/fixtures/votes/FIELD-MAP.md` locking VERIFIED semantics (RT-04/05/06/17) and listing two UNVERIFIED resolvers (`vote_tokens_nu_ab`, `test_vote_exclusion`). → **CP-1.05**

**P1 — Schema + parser**

- **AP-1.06** Insert `Vote`, `VotePosition`, `VoteImportRun` in `pipeline/db.py` after `:348` (after `Event`, before `SwitchWave :350`); exact fields §5.2; `SCHEMA_VERSION=1`; `create_all` at `:456-458` creates tables. (D2:L17, D2:L29) → **CP-1.06**
- **AP-1.07** `db.py:72` add `vote` to `EVIDENCE_TYPES`; `:73-86` add `vote` to `EVENT_TYPES`; `:62-71` add `VOTE` to `REASONS`; `:489-531` add partial unique `ux_vote_position_unresolved`; no `_ADDED_COLUMNS` change for votes. (D2:L15, MS:384) → **CP-1.06**
- **AP-1.08** Create `pipeline/sources/votes_cdep.py` + `pipeline/votes.py` against fixtures only; raw bytes via `record_fragment` (`fragments.py:46-80`); fragment model names `vote_day_xml / vote_nominal / vote_json / vote_csv`; chamber map RT-08; day/nominal tag sets A2/A5. (D2:L21-L26) → **CP-1.08**
- **AP-1.09** Create `pipeline/sources/votes_thirdparty.py` with non-fatal `DATA_UNAVAILABLE`; exact 22-column CSV header and JSON top-key set (A7/A8); `/api/votes/37526` 404 recorded. (D2:L27) → **CP-1.08**
- **AP-1.10** Add `SourceLicense` after `db.py:423` before `:426` with CheckConstraint (§7.1); fragment gains `license_flag`/`redistributable` via `_ADDED_COLUMNS db.py:463-481`. (D2:L49) → **CP-1.10**

**P2 — Ingest + dry-run**

- **AP-1.11** Implement resolution in `pipeline/votes.py`: `cdep_mandate {ch}:{leg}:{idm}` → `cdep_idm` only with matching chamber+legislature mandate → `cdep_person` with same check → quarantine; no name match, no `PersonResolver.resolve()` (`identity.py:110-130`); unresolved → `VoteImportRun.report`. (D2:L31) → **CP-1.11**
- **AP-1.12** Add `votes-import` subparser near `cli.py:861` with `--dry-run` default and `--skip-votes`; run on `/tmp/opencode/votes-dryrun.db` created by `backup()`. Keys per D2:L30. → **CP-1.12**
- **AP-1.13** Write and run `tests/test_votes_cdep_parser.py`, `test_votes_thirdparty_contract.py`, `test_votes_dry_run.py` asserting A1–A16. (D2:L33) → **CP-1.13**
- **AP-1.14** Write `tests/test_votes_build_isolation.py`: `grep -R` over `cmd_build_corpus` (`cli.py:526-712`), `prepare_db.py`, `backend.main`, `Dockerfile`, `ci.yml`, `data.yml` finds no `votes-import|vot-parlament|votes_cdep` token. (D2:L32) → **CP-1.14**

**P3 — API + UI (definition honesty only; no new vote endpoints yet)**

- **AP-1.15** Close D1–D14 in one documentation commit: `docs/RESEARCH.md` robots facts, `docs/DATA-COMPLETENESS-RECOVERY.md:3` 7,358→7,349, `db.py:505` count, `docs/METHODOLOGY.md:501`, `docs/AUDIT.md:121,134`, `audit.py:410-414,812`, `data/licenses/README.md:105-106`, `About.tsx:263-298`, `vercel.json:6`, commit `docs/DATA-ENRICHMENT-RESEARCH.md` explicitly. (MS:79-94, D2:L7) → **CP-1.15**
- **AP-1.16** Add `npm run lint` CI gate; remove dead 180 s Vercel tolerance in `scripts/verify-deploy.sh`; quarantine `scripts/deploy-all.sh:21` with dirty-tree guard; resolve branch protection via `gh api repos/nedaktov-ops/parlament-deschis/branches/main/protection` or record UNVERIFIED. (MS:334-336, D2:L64) → **CP-1.16**
- **AP-1.17** Fix definition collisions: `api.py:985-995` → `active_memberships_as_of`, `api.py:999-1005` → `switches_all_time` + `as_of`, align half-open `pipeline/queries.py:38-42`; fix quick-win UI defects #1–#13 and #16 (§6.3). → **CP-1.17**

**P4 — Audit + release (dry-run gate, no data promotion)**

- **AP-1.18** Register `check_vote_evidence` after `audit.py:375-407` in `CHECKS` `:973-984`; assert every vote has `source_url` + fragment checksum, positions resolve or are quarantined, no `attendance_score` column/endpoint. → **CP-1.18**
- **AP-1.19** Full local gate: `uv sync --extra dev --locked`; `uv run ruff check pipeline backend scripts tests`; `uv run pytest -q`; `(cd frontend && npm ci && npm run build)`; strict audit → `275 known errors, 0 new errors`. → **CP-1.19**
- **AP-1.20** `gh workflow run deploy-verify.yml -R nedaktov-ops/parlament-deschis --ref main`; assert SHA `2995bfd` (or new code SHA) and unchanged release tag `data-20261117-T213500` — **no votes in this release**. → **CP-1.20**

**Checkpoints — W1**

| CP | AP | Automated assertion + exact expected value / failure signature | Rollback | Irreversible |
|---|---|---|---|---|
| CP-1.01 | 1.01/1.02 | counts `3388/5273/7349/7429/120`; HEAD `2995bfd`. Fail: any diff → re-measure with `.venv/bin/python`, then escalate. | none (read-only) | none |
| CP-1.02 | 1.01 | `SELECT count(*) FROM sqlite_master WHERE name LIKE 'vote%'` = 0 today. Fail: existing vote table → stop, reconcile. | none | none |
| CP-1.03 | 1.03 | `SELECT source_name,license_id,redistributable FROM source_license` contains cdep facts + vot-parlament CC-BY + 281.ro attribution; zero NC/SA rows redistributable=1. | `GIT` governance commit | legal decision record persists; correction needs new commit |
| CP-1.04 | 1.04 | manifest has 8 entries; day XML 5,394 B; nominal HTML 94,483 B; CSV full 1,698,092 B; JSON 126,323 B; every sha256 recomputes equal. Fail: size/sha mismatch → refetch with PoliteClient. | delete untracked fixtures + manifest, refetch | fetched bytes exist in cache only |
| CP-1.05 | 1.05 | FIELD-MAP lists par1=1 day / par1=2 nominal, CAMERA 2/1/0, idv==VOTID, 9-element + 6-element tag sets; 2 UNVERIFIED resolvers named. Fail: any assumed item → block AP-1.08. | `git checkout -- tests/fixtures/votes/FIELD-MAP.md` | none |
| CP-1.06 | 1.06/1.07 | `sqlite_master` on copy lists `vote`, `vote_position`, `vote_import_run`, `ux_vote_position_unresolved`; `vote_position.person_id` NOT NULL (`PRAGMA table_info`). Fail: missing index/NULL allowed → fix before parser. | `SQL` on copy | none on copy |
| CP-1.08 | 1.08/1.09 | A2/A5/A7/A8 pass; parser reads fixtures with network monkeypatched to raise. Fail: tag-set or header drift → return to CP-1.04. | `GIT` parser files | none |
| CP-1.10 | 1.10 | `SELECT license_id FROM source_license WHERE redistributable=1` returns only CC0-1.0/CC-BY-4.0/OGL-ROU-1.0; CHECK rejects an injected `CC-BY-NC-4.0` row. Fail: CHECK absent → block. | `SQL` on copy + `GIT` | none on copy |
| CP-1.11 | 1.11 | 246 links → 146 / 245 / union 245 / 1 unresolved (`deputies:2024:87`) / 5 disagreements; `SELECT count(*) FROM person` = 3,388; zero name matches. Fail: person created → block. | restore copy via `SQL` | on shipped DB fabrication would be published — copy-only rule prevents |
| CP-1.12 | 1.12 | after `--dry-run`, `vote`/`vote_position` counts 0 on copy; `VoteImportRun.applied=0`; `dedup_key` non-null for every run. Fail: any write → block. | delete `/tmp/opencode/votes-dryrun.db` | none |
| CP-1.13 | 1.13 | A1–A16 all PASS with raw pytest output; failure signature any red → max 3 retries then escalate. | `GIT` test/parser commit | none |
| CP-1.14 | 1.14 | isolation grep returns zero hits in 6 targets; with third-party HTTP 500, `build-corpus --strict` exits 0 and logs `DATA_UNAVAILABLE`. Fail: any hit or strict fail → block. | `GIT` isolation-test commit | none |
| CP-1.15 | 1.15 | `grep -n "No roll-call" docs/METHODOLOGY.md` → no hit; `git ls-files docs/DATA-ENRICHMENT-RESEARCH.md` → tracked; all D1–D14 closed. | `GIT` doc commit | docs visible in SPA after deploy |
| CP-1.16 | 1.16 | CI shows lint job; `grep -n "180" scripts/verify-deploy.sh` → no dead tolerance; `grep -n "git add -A" scripts/deploy-all.sh` → gated only; protection fact captured or UNVERIFIED with resolver. | `GIT` workflow commit | CI run history |
| CP-1.17 | 1.17 | API returns `active_memberships_as_of=4461` (2026-11-20) and switches labelled all-time=2002; browser screenshot shows both labels; no unlabelled number. | `GIT` + `PLAT` | 300 s cache residue (`backend/cache.py:28`) |
| CP-1.18 | 1.18 | audit lists `check_vote_evidence` in `CHECKS`; strict `275 known errors, 0 new errors`; `grep -rn attendance_score` → 0 hits. | `GIT` audit commit | baseline file changes require review |
| CP-1.19 | 1.19 | ruff exit 0; pytest all green; npm build exit 0; strict audit exact output. | `GIT` + `PLAT` | published deploy history; immutable bundle cache (`vercel.json:14-15`) |
| CP-1.20 | 1.20 | `verify-deploy.sh` asserts SHA and **unchanged** tag `data-20261117-T213500`; no vote rows in served corpus. | `REL` → `PLAT` → `GIT` | release assets, browser bundles, third-party state |

---

### 4.2 W2 — DOB backfill + daily pipeline + full votes backfill

**Goal.** Fill the 275 DOBs with exact-match provenance, wire safe enrichment into the daily workflow, and ingest the full vote corpus on a copy then promote via immutable release.  
**Value / effort.** 1–2 weeks; high value, medium risk (CLI bugs + WAL).  
**Dependencies.** W1 schema, licence registry, dry-run importer, build-isolation proof.

| Phase | APs |
|---|---|
| P0 | AP-2.01 fix CLI/DB bugs · AP-2.02 DOB fixtures + FIELD-MAP · AP-2.03 legal gate (cdep/senat/GLD/SER-PROM/Wikidata) |
| P1 | AP-2.04 `person_attribute` + `org_identifier` · AP-2.05 header-driven DOB parser · AP-2.06 `cdep-birthdates` source/CLI |
| P2 | AP-2.07 dry-run DOB on copy + merge invariants · AP-2.08 `data.yml` wiring · AP-2.09 full votes backfill on copy |
| P3 | AP-2.10 `BioFacts`/`BioCoverageNote` + honest generational stats · AP-2.11 vote endpoints contract tests |
| P4 | AP-2.12 `check_biography_provenance` · AP-2.13 strict gate · AP-2.14 promotion + deploy proof |

- **AP-2.01** Edit `enrich.py:368-372` (add `db_path`/`cache_path`), `cli.py:260-272` (honour `args.db`), `cli.py:767` (dry-run default in parser and module). → **CP-2.01**
- **AP-2.02** Capture `structura2015.de?leg=1990&par=V01..V12&cam=2` (extra "Membru din"), `leg=1990&cam=1` (no such column), `leg=2024`; assert headers `Nume si prenume / Data nasterii / Circumscriptia electorala / Grupul parlamentar`; save Iorga Eugenia `1954-01-01` fixture. (D2:L38, D2:L43) → **CP-2.02**
- **AP-2.03** @worker-covariates records: cdep/senat facts COPY; GLD CC0 COPY; SER-PROM COND cross-check only; Wikidata CC0 but bulk `/sparql` disallowed → cached/dump flows. → **CP-2.03**
- **AP-2.04** Add `person_attribute` and `org_identifier` after `db.py:104`; leave `Evidence.membership_id NOT NULL` untouched. → **CP-2.04**
- **AP-2.05** Header-driven parser: DOB `D.MM.YYYY`, write conditions D2:L41; `Iorga Eugenia == 1954-01-01`, `!= 1991-01-21`; exact idm match only; conflicts `status='conflict'`. (D2:L38, D2:L41) → **CP-2.05**
- **AP-2.06** New `enrich-birth-dates` CLI + `pipeline/parse/…birth_dates.py` + `pipeline/sources/…`; cache key `cdep-birthdates-${run_id}`. → **CP-2.06**
- **AP-2.07** Dry-run on `/tmp/opencode/dob-dryrun.db`; prove 275 = 268 + 7 + 0 + 0, Stoica 285/286 distinct, person count 3,388, merge_audit unchanged, 4 SHA-256 invariants identical. → **CP-2.07**
- **AP-2.08** Insert enrichment step between `data.yml:81` and `:83`: `s.backup(d)`, dry-run → apply on copy `continue-on-error`, cache saved even on failure, prepare reads enriched copy and uses `prepare_db.py:187` atomic `os.replace`. → **CP-2.08**
- **AP-2.09** Full votes backfill on copy: apply `votes-import` for all captured days; idempotency by deterministic keys; cross-source equality cdep vs vot-parlament; unresolved positions quarantined in run report. → **CP-2.09**
- **AP-2.10** `BioFacts`/`BioCoverageNote` in `PersonDeepDive`/`Mps` with source + precision; `generational_shift` (A7) reports excluded count and true median. → **CP-2.10**
- **AP-2.11** Contract tests for `/analytics/vote-cohesion`, `/voting-record`, `/presence-at-vote`, `/person/{id}/votes`, `/votes` per MS:820-824; mandatory presence caveat string; min_votes 20; no ranking. → **CP-2.11**
- **AP-2.12** Register `check_biography_provenance` after `audit.py:410-453`; fix `:410-414` docstring/body mismatch. → **CP-2.12**
- **AP-2.13** Full local gate + strict audit. → **CP-2.13**
- **AP-2.14** Promote votes+DOB via new immutable tag, pin with retry, Render deploy, poll ≤30 min, deploy-verify; `/api/coverage/detailed` shows `votes: full` (or measured partial), biographies improved. → **CP-2.14**

**Checkpoints — W2**

| CP | AP | Assertion / expected value / failure signature | Rollback | Irreversible |
|---|---|---|---|---|
| CP-2.01 | 2.01 | dry-run makes zero row changes; `--db /tmp/opencode/x.db` writes only to x.db. Fail: shipped DB mtime/hash changes → block. | `GIT` | none |
| CP-2.02 | 2.02 | fixtures contain all 4 headers; 1990 cam=2 has "Membru din"; 1990 cam=1 does not; Iorga 1954-01-01 present. | delete untracked fixtures | none |
| CP-2.03 | 2.03 | SER-PROM `redistributable=0`; no bulk Wikidata SPARQL in code. | `GIT` licence commit | decision record |
| CP-2.04 | 2.04 | tables present on copy; `PRAGMA table_info(evidence)` shows `membership_id notnull=1`. | `SQL` on copy | none |
| CP-2.05 | 2.05 | zero name-only merges; Iorga assertion PASS; person count 3,388; conflicts stored `status='conflict'`. | restore copy | fabricated links on shipped DB (copy-only prevents) |
| CP-2.06 | 2.06 | cache key string `cdep-birthdates-${run_id}` present in workflow/CLI; no `/sparql` bulk call. | `GIT` | none |
| CP-2.07 | 2.07 | 268/7/0/0 exact; 4 SHA-256 invariants identical; merge_audit row count unchanged. | drop attributes on copy | none |
| CP-2.08 | 2.08 | injected GLD failure leaves official corpus unchanged; cache saved on failure; `journal_mode=delete` in shipped output. | `GIT` workflow | workflow run history; Render auto-deploy race (`platform-rollback.yml:145`) |
| CP-2.09 | 2.09 | full backfill counts equal sum of day fixtures; re-run produces identical counts and dedup keys; 1 unresolved / 5 disagreements preserved. | delete backfilled rows on copy | none |
| CP-2.10 | 2.10 | screenshots show source + precision; no fabricated day; A7 excluded count visible. | `GIT` + `PLAT` | bundle cache |
| CP-2.11 | 2.11 | all 5 endpoints return full envelope (MS:801-818); covenant caveat verbatim; `grep -rn attendance_score` 0. | `GIT` API commit | 300 s cache residue |
| CP-2.12 | 2.12 | check registered and green; strict `275 known errors, 0 new errors`. | `GIT` audit commit | baseline review record |
| CP-2.13 | 2.13 | ruff 0; pytest green; npm build 0; strict audit exact output. | `GIT` + `PLAT` | published deploy history |
| CP-2.14 | 2.14 | new tag served at `/api/health`; missing DOB reduced; `verify-deploy.sh` asserts SHA+tag. | `REL` → `PLAT` → `GIT` → physical DB restore (WAL checkpoint first) | published releases/assets, bundles, cache, third-party changes |

---

### 4.3 W3 — Covariates, committees, speeches, elections, benchmarks

**Goal.** Add all external statistical source tables with licence quarantine, party alias map (four IDs), committee role history, speech citations, election results and benchmarks — display-only where licence requires.  
**Value / effort.** 2–3 weeks; medium-high value, high licence risk.  
**Dependencies.** W2 identity/attribute tables and `SourceLicense` registry.

| Phase | APs |
|---|---|
| P0 | AP-3.01 per-file licence table · AP-3.02 four-ID alias map · AP-3.03 source fixtures (CHES/GLD/AEP/WB/Zenodo) |
| P1 | AP-3.04 external table models · AP-3.05 export guards + BenchmarkLabel · AP-3.06 committee/speech parsers |
| P2 | AP-3.07 dry-run + quarantine assertions · AP-3.08 genealogy immutability proof |
| P3 | AP-3.09 `/api/traseism/switchers-by-ideology` · AP-3.10 electoral-base `unavailable` path · AP-3.11 benchmark endpoints |
| P4 | AP-3.12 `check_benchmark_license` + `check_election_result` · AP-3.13 full gate · AP-3.14 promotion |

- **AP-3.01** Record per-file classes: CHES EUI archive CC BY 4.0 (`hdl.handle.net/1814/69975`; chesdata.eu 2024 per-file **UNVERIFIED** — resolver: download and read file headers), V-Dem CC BY-SA → `redistributable=0`, Party Facts Dataverse CC0 (site licence UNVERIFIED, partyfacts.github.io 404), IPU CC BY-NC-SA XCHECK, OpenSanctions CC BY-NC XCHECK, PopuList UNVERIFIED → CONDITIONAL/XCHECK, GLD CC0, AEP/data.gov.ro OGL/CC-BY. → **CP-3.01**
- **AP-3.02** Create `party_alias_map` with FSN=958, FDSN=276, PDSR=1034, PSD=120 and lineage edges; join key `(country='ROU', dataset_key, dataset_party_id)`; quarantine `dataset_key='pop'` rows. (D2:L47-L48) → **CP-3.02**
- **AP-3.03** Capture fixtures: `external-parties.csv` header row, 6 PopuList `populist` ROU rows, CHES EUI CSV, AEP/data.gov.ro CKAN `package_show` bodies, World Bank `SG.GEN.PARL.ZS` JSON (`lastupdated 2026-11-11`), Zenodo 3332908 `CDEPs2.csv` sample. → **CP-3.03**
- **AP-3.04** Add `party_score`, `org_identifier`, `election_result`, `benchmark`, `context_year`, `speech` after `db.py:423`; add `speech` to `EVIDENCE_TYPES :72` and `EVENT_TYPES :73-86`; committee history reuses `membership` (`db.py:229-270`) + committee join/leave events. (D2:L50) → **CP-3.04**
- **AP-3.05** `_assert_exportable(session)` at `export.py:105`; `meta.license_exclusions` at `:233-249`; `BenchmarkLabel.tsx` RO/EN string (D2:L49). → **CP-3.05**
- **AP-3.06** Parsers for committee roles (never overwrite stronger `official_ledger`), speeches (Zenodo speaker URLs, monitorul.ai 2-hop provenance), election results (seat sum 329 per `audit.py:812`, not docs' 330). → **CP-3.06**
- **AP-3.07** Dry-run on copy; XCHECK rows explicitly absent from all export formats; PopuList `'pop'` rows quarantined. → **CP-3.07**
- **AP-3.08** SHA-256 over `organization.short_name`, `alt_labels`, `previous_party_id`, `successor_party_id`, dates — identical before/after; zero writes to genealogy; no `partyfacts` in `person_identifier`. → **CP-3.08**
- **AP-3.09** `/api/traseism/switchers-by-ideology` with Welch CI, `partyfacts_id`, licence flag per source; SA sources `XCHECK` never exported. → **CP-3.09**
- **AP-3.10** `/analytics/electoral-base` returns `status: unavailable`, `missing_data_count: 5273`, reason "constituency not populated" while `mandate.constituency` is 100% NULL; never guess a constituency. → **CP-3.10**
- **AP-3.11** `/analytics/demographic-benchmarks` with `our_n`, `our_missing`, `benchmark_provenance`, `license_flag`; IPU rows `XCHECK` + `export_ok:false`; literal label "external benchmark, not our data". → **CP-3.11**
- **AP-3.12** Register `check_benchmark_license` before `audit.py:830` and `check_election_result` after benchmark in `CHECKS :973-984`; baseline deliberate. → **CP-3.12**
- **AP-3.13** Full local gate. → **CP-3.13**
- **AP-3.14** Promote via new tag; verify served benchmark labels and licence exclusions in public API. → **CP-3.14**

**Checkpoints — W3**

| CP | AP | Assertion / expected value / failure signature | Rollback | Irreversible |
|---|---|---|---|---|
| CP-3.01 | 3.01 | every planned source has a class row; PopuList `redistributable=0`; chesdata 2024 wave flagged UNVERIFIED with resolver. | `GIT` licence commit | decision record |
| CP-3.02 | 3.02 | alias map has rows 958/276/1034/120; zero `'pop'` rows mapped to PopuList; zero `organization.*` writes. | `GIT` alias commit | none |
| CP-3.03 | 3.03 | fixture sha256 + byte_count recorded; `external-parties.csv` header includes the 6 columns in D2:L47. | delete untracked fixtures | none |
| CP-3.04 | 3.04 | all 6 tables on copy; `speech` in both enums; committee rows use existing `membership` columns. | `SQL` on copy | none |
| CP-3.05 | 3.05 | injected NC row raises at `export.py:105`; BenchmarkLabel contains exact RO/EN text; `meta.license_exclusions` lists XCHECK sources. | `GIT` export commit | none |
| CP-3.06 | 3.06 | speech dedup idempotent; `interval_order` audit green; seat sum 329. | drop rows on copy | none |
| CP-3.07 | 3.07 | zero NC/SA/XCHECK rows in any export format; `'pop'` rows quarantined. | drop rows on copy | none |
| CP-3.08 | 3.08 | 5 SHA-256 invariants identical; zero genealogy writes. | `GIT` | none |
| CP-3.09 | 3.09 | endpoint envelope complete; Welch CI present; SA sources `XCHECK`. | `GIT` API commit | 300 s cache |
| CP-3.10 | 3.10 | `electoral-base` returns exact unavailable envelope with 5273. | `GIT` | none |
| CP-3.11 | 3.11 | `our_n`/`our_missing` present; IPU `export_ok:false`; label verbatim. | `GIT` + `PLAT` | bundle cache |
| CP-3.12 | 3.12 | both checks in `CHECKS`; strict `275 known errors, 0 new errors` (or approved reviewed delta). | `GIT` audit commit | baseline review record |
| CP-3.13 | 3.13 | ruff 0; pytest green; npm build 0; strict audit exact. | `GIT` + `PLAT` | deploy history |
| CP-3.14 | 3.14 | new tag served; licence exclusions enforced in public export; `verify-deploy.sh` green. | `REL` → `PLAT` → `GIT` | published assets/bundles/cache |

---

### 4.4 W4 — Frontend / API / export overhaul

**Goal.** Ship the new statistical views against proven endpoints, complete the 16 defects, and converge REST/GraphQL/export with full trust envelopes.  
**Value / effort.** 2–3 weeks; highest user-visible value; no new source risk.  
**Dependencies.** W1–W3 data tables and endpoint contracts PASS. No UI is designed against placeholders.

| Phase | APs |
|---|---|
| P0 | AP-4.01 design gate (Plan A design-only; Plan B build) · AP-4.02 freeze component/route/i18n inventory |
| P1 | AP-4.03 roll-call alignment matrix · AP-4.04 cohesion/defection timeline · AP-4.05 ideological spatial map · AP-4.06 MP behavioral scorecard · AP-4.07 Compară/Radar/Grafice upgrades |
| P2 | AP-4.08 wire endpoints + status envelopes · AP-4.09 REST/GraphQL convergence · AP-4.10 export convergence |
| P3 | AP-4.11 16 defects + a11y/i18n · AP-4.12 browser evidence at target viewport |
| P4 | AP-4.13 audit/no-attestation gate · AP-4.14 full gate · AP-4.15 promotion + proof |

- **AP-4.01** Run `modern-web-guidance` + `design-taste-frontend` gate; confirm Plan A produces **design artefacts only** (no local 281.ro repo — RT-01/02); Plan B targets `router.tsx:310-458`. → **CP-4.01**
- **AP-4.02** Freeze component names, data contracts, filters and ro/en key names per §6.2; inspect orphan components before writing new ones (MS:755). → **CP-4.02**
- **AP-4.03** `RollCallAlignmentMatrix` on new `/votes` route; filters chamber/legislature/from/to/min_votes; data from `/analytics/vote-cohesion`. → **CP-4.03**
- **AP-4.04** `PartyCohesionDefectionTimeline` on `/traseism` (reuse `Traseism.tsx:134-164,845-866`); data from vote cohesion + dated switch events. → **CP-4.04**
- **AP-4.05** `IdeologicalSpatialMap` on `/compare` and `/parties`; data from `party_score`; XCHECK sources display-only with `BenchmarkLabel`. → **CP-4.05**
- **AP-4.06** `MpBehaviorScorecard` in `PersonDeepDive`; **no attendance score, no ranking**; presence shown factually with caveat. → **CP-4.06**
- **AP-4.07** Upgrade Compară (`PartyComparison.tsx:46,51`), Radar and Grafice patterns for local repo per §6.2; explicit denominators. → **CP-4.07**
- **AP-4.08** Wire all endpoints with full envelope (MS:801-818): `status`, `scope`, `sample_size`, `denominator`, `missing_data_count`, `precision`, `source_link`, `benchmark_provenance`, `license_flag`, `computed_at` (aware UTC), `cache: no-store`. → **CP-4.08**
- **AP-4.09** Fix REST/GraphQL divergence: `party_cohesion` same `unavailable` envelope in both; `median_age` uses `statistics.median` in both; add `tests/test_graphql_convergence.py` byte comparison. → **CP-4.09**
- **AP-4.10** Export convergence: new branch at `pipeline/export.py:352` (not just `CSV_DATASETS` — MS:832); route beside `backend/routers/exports.py:190-203`; blocks in `/export/report:139-159`; XCHECK rows excluded. → **CP-4.10**
- **AP-4.11** Close 16 defects with before/after screenshots; fix `#14` SenateHistory `:67-69`/`:82-85` and `#15` PartyTimeline `:123-125` with resolved lines; theme toggle site-wide (`ui/DashboardHeader.tsx:15`); `aria-sort`; SVG text alternatives; ro/en keys. → **CP-4.11**
- **AP-4.12** Browser proof at target viewport for `/votes`, `/vote/$id`, `/parties`, `/compare`, `/traseism`, `/coverage`; `chrome-devtools` screenshots with URL + viewport. → **CP-4.12**
- **AP-4.13** Audit assertion: `grep -rn "attendance_score"` 0; presence caveat visible; BenchmarkLabel on every external series; no number without denominator. → **CP-4.13**
- **AP-4.14** Full local gate: ruff, pytest, npm build, strict audit. → **CP-4.14**
- **AP-4.15** Promote via new tag; deploy-verify asserts SHA + tag; `/api/coverage/detailed` honest for votes/biographies/committees. → **CP-4.15**

**Checkpoints — W4**

| CP | AP | Assertion / expected value / failure signature | Rollback | Irreversible |
|---|---|---|---|---|
| CP-4.01 | 4.01 | design-checker output green; zero product files referencing 281.ro repo paths. | none (design only) | none |
| CP-4.02 | 4.02 | component/route/i18n inventory signed; no placeholder endpoints. | `GIT` inventory doc | none |
| CP-4.03 | 4.03 | matrix renders with `aria-sort`, denominator + source; screenshot proof. | `GIT` + `PLAT` | bundle cache |
| CP-4.04 | 4.04 | timeline uses real vote cohesion (not `api.py:804-822` switch rate); dated events. | `GIT` + `PLAT` | bundle cache |
| CP-4.05 | 4.05 | ideological map labels licence + external benchmark; PopuList shown as XCHECK/conditional. | `GIT` + `PLAT` | bundle cache |
| CP-4.06 | 4.06 | no score/rank field; caveat verbatim; `grep -rn attendance_score` 0. | `GIT` + `PLAT` | bundle cache |
| CP-4.07 | 4.07 | Compară/Radar/Grafice numbers all scoped; no hardcoded 100% bars. | `GIT` + `PLAT` | bundle cache |
| CP-4.08 | 4.08 | all endpoints return every envelope field; `computed_at` UTC; `cache:no-store`. | `GIT` API commit | 300 s cache |
| CP-4.09 | 4.09 | REST/GraphQL byte-comparable after normalising transport; convergence test green. | `GIT` | none |
| CP-4.10 | 4.10 | export route emits new dataset with real columns; zero XCHECK rows in output. | `GIT` | published export artifacts |
| CP-4.11 | 4.11 | all 16 defects closed with before/after proof; `type="button"`; no `onKeyPress`; WCAG AA; ro/en keys complete. | `GIT` + `PLAT` | bundle cache |
| CP-4.12 | 4.12 | screenshots for 6 routes with URL + viewport; no console errors. | re-capture | none |
| CP-4.13 | 4.13 | zero attendance_score; caveat + BenchmarkLabel visible; every number scoped. | `GIT` + `PLAT` | bundle cache |
| CP-4.14 | 4.14 | ruff 0; pytest green; npm build 0; strict `275 known errors, 0 new errors`. | `GIT` + `PLAT` | deploy history |
| CP-4.15 | 4.15 | new tag served; deploy-verify asserts SHA+tag; coverage honest. | `REL` → `PLAT` → `GIT` | published assets/bundles/cache |

---

## 5. Wave 1 implementation-ready detail (ready to commit)

### 5.1 Exact file list to create / modify

**Create (new):**
`pipeline/sources/votes_cdep.py`, `pipeline/sources/votes_thirdparty.py`, `pipeline/votes.py`, `scripts/capture_vote_fixtures.py` (dev-only), `tests/fixtures/votes/manifest.json`, `tests/fixtures/votes/FIELD-MAP.md`, `tests/fixtures/votes/cdep_evot2015_day_20261118.xml`, `tests/fixtures/votes/cdep_evot2015_day_20261110.xml`, `tests/fixtures/votes/cdp_vote_nominal_37526.html`, `tests/fixtures/votes/cdp_vote_nominal_37526.xml`, `tests/fixtures/votes/cdp_vote_nominal_37492.html`, `tests/fixtures/votes/vot_parlament_votes_export_head.csv`, `tests/fixtures/votes/vot_parlament_vote_37526.json`, `tests/fixtures/votes/vot_parlament_api_votes_37526_404.txt`, `tests/test_votes_cdep_parser.py`, `tests/test_votes_thirdparty_contract.py`, `tests/test_votes_dry_run.py`, `tests/test_votes_build_isolation.py`, `tests/fixtures/votes/LICENSE-APPENDIX.md`.

**Modify (exact lines):** `pipeline/db.py` after `:348` (models), `:62-71`, `:72`, `:73-86`, `:423-426` (SourceLicense), `:456-458` (create_all — verify only), `:463-481` (fragment columns), `:489-531` (partial index); `pipeline/fragments.py:46-80` (use only); `pipeline/events.py:109-134` (reuse `_upsert_event` pattern); `pipeline/cli.py` near `:861` (subparser), `:489-502` (counts), `:526-712` (no vote wiring — isolation); `pipeline/audit.py:375-407` + `:973-984`; `docs/RESEARCH.md`, `docs/DATA-COMPLETENESS-RECOVERY.md:3`, `docs/METHODOLOGY.md:501`, `docs/AUDIT.md:121,134`, `data/licenses/README.md:105-106`, `.github/workflows/ci.yml`, `scripts/verify-deploy.sh`, `scripts/deploy-all.sh:21`; commit `docs/DATA-ENRICHMENT-RESEARCH.md` explicitly.

### 5.2 Exact model fields

```
Vote
  id                      Integer PK
  source                  String      # 'cdep' | 'vot_parlament'
  native_vote_id          String      # VOTID from day XML == idv (RT-06)
  platform_vote_id        String, nullable   # vot-parlament platform_vote_id
  chamber                 String      # 'senat'|'cdep'|'joint' (RT-05/08)
  legislature             String      # 'YYYY'
  vote_time               String/time # TIME_VOT
  title_raw               String      # DESCRIERE
  bill_code, bill_number, bill_year, bill_title, bill_url   # third-party bill fields
  present, not_voting, yes, no, abstain   # five counts (PREZENTI, NU_AU_VOTAT, DA, NU, AB)
  official_vote_url       String
  source_url              String NOT NULL
  snapshot_hash           String      # fragment checksum
  truth_contract_version  String
  positions_incomplete    Boolean default False
  dedup_key               String UNIQUE  # f"{source}:{native_vote_id}"
  Index('ix_vote_scope_date', chamber, legislature, vote_time)

VotePosition
  id                 Integer PK
  vote_id            Integer FK -> vote.id
  person_id          Integer NOT NULL FK -> person.id   # RT-16
  idm_raw, cam_raw, name_raw, group_raw   String
  raw_vote           String      # 'DA' | '-' | observed token
  choice             String      # normalised yes/no/abstain/not_voting
  resolution_scheme  String      # 'cdep_mandate'|'cdep_idm'|'cdep_person'
  dedup_key          String UNIQUE  # f"{vote_key}:{person_id}"
  Index('ix_vote_position_person_choice', person_id, choice)

VoteImportRun
  id                   Integer PK
  manifest_sha         String      # sha256(fixtures || versions || dry_run)
  parser_version       String
  resolver_version     String
  policy_version       String
  dry_run              Boolean
  applied              Boolean
  votes_seen, votes_written, positions_seen, positions_written   Integer
  unresolved_count     Integer     # 1 for 37526
  disagreement_count   Integer     # 5 for 37526
  report               JSON        # quarantine: idm_raw, cam_raw, name_raw, raw_vote, reason
  dedup_key            String UNIQUE
```
`SCHEMA_VERSION=1`; no Alembic; `create_all` at `db.py:456-458` creates the three tables. Partial unique `ux_vote_position_unresolved` at `db.py:489-531`. No timestamps/UUIDs in keys (D2:L30).

### 5.3 Exact fixture manifest

| File | Source URL | Size / content | Evidence |
|---|---|---|---|
| `cdep_evot2015_day_20261118.xml` | `/ords/pls/steno/evot2015.xml?par1=1&par2=20261118` | 5,394 B; 9 text elements, no attributes, ISO-8859-2; 16 records; includes VOTID 37515 "Vot test 1" | D2:L21-L22 |
| `cdep_evot2015_day_20261110.xml` | `...par2=20261110` | joint day, `CAMERA=0` | D2:L24 |
| `cdp_vote_nominal_37526.html` | `...evot2015.nominal?idv=37526&idl=1` | 94,483 B; 246 profile links | D2:L21, D2:L26 |
| `cdp_vote_nominal_37526.xml` | nominal page's own XML link; `par1=2&par2=37526` | 246 rows; DA=245, `-`=1; exact bytes recorded by capture script (size **UNVERIFIED** — resolver: capture script stdout) | D2:L23, D2:L25 |
| `cdp_vote_nominal_37492.html` | `...idv=37492&idl=1` | joint vote: 161 `cam=2` + 57 `cam=1` links | D2:L26 |
| `vot_parlament_votes_export_head.csv` | `vot-parlament.ro/votes/export.csv` | 22-column header + sample rows; full body 1,698,092 B | D2:L27 |
| `vot_parlament_vote_37526.json` | `vot-parlament.ro/votes/37526.json` | 126,323 B; 8 top keys; positions keys per D2:L27 | D2:L27 |
| `vot_parlament_api_votes_37526_404.txt` | `vot-parlament.ro/api/votes/37526` | 404 body | D2:L27 |

`manifest.json` per entry: `{path, sha256, byte_count, source_url, http_status, captured_at, captured_by:'scripts/capture_vote_fixtures.py', policy:'polite-v1'}`. Every shaded size above is a **measured expectation**, not a guess; the capture script writes the sha256 at capture time and A1 recomputes it.

### 5.4 Exact 16 QA assertions (A1–A16)

- **A1** For every manifest entry, `sha256(file) == manifest.sha256` and `byte_count == manifest.byte_count` (5,394 / 94,483 / 1,698,092 / 126,323 where known). Failure: any mismatch → abort before write.
- **A2** Day XML root has exactly the 9 text elements `{VOTID,TIME_VOT,DESCRIERE,CAMERA,PREZENTI,NU_AU_VOTAT,AU_VOTAT_DA,AU_VOTAT_NU,AU_VOTAT_AB}`, zero attributes, decodes as ISO-8859-2, 16 records for 20261118.
- **A3** Reconciliation: for VOTID 37526, nominal VOT tokens total **246** with `DA=245`, `-`=1, matching official totals and the day-record `PREZENTI`; parser records the exact addend identity used (computed from fixture, never assumed).
- **A4** `idv == VOTID`: nominate URL `idv=37526`, XML `VOTID=37526`, tally 245/1 — three-way equality.
- **A5** Nominal XML has exactly the 6 elements `{VOTID,NUME,PRENUME,GRUP,CAMERA,VOT}`, no attributes, 246 rows.
- **A6** Nominal HTML contains 246 `href` matching `/ords/pls/parlam/structura2015.mp?idm=N&cam=2&leg=2024`; joint 37492 has 161 `cam=2` + 57 `cam=1`.
- **A7** CSV header equals, in order, the exact 22 columns from D2:L27 (`platform_vote_id,…,truth_contract_version`).
- **A8** JSON top keys equal `{vote,bill,matter,group_breakdown,official_group_summary,party_breakdown,positions,cache}`; `positions[*]` includes the 8 keys from D2:L27; `/api/votes/37526` = 404.
- **A9** Cross-source equality: cdep day totals for 37526 equal vot-parlament `official_present/yes/no/official_not_voted` for `native_vote_id=37526`; any difference → quarantine, no merge.
- **A10** Zero persons created: `SELECT count(*) FROM person` before == after == **3,388**; `grep -rn "PersonResolver.resolve" pipeline/sources/votes_cdep.py pipeline/sources/votes_thirdparty.py pipeline/votes.py` → no hit.
- **A11** Resolution reproduced: 146 `cdep_mandate` / 245 `cdep_idm` / union 245 / 1 unresolved (`deputies:2024:87`) / 5 disagreements; zero name matches; unresolved only in `VoteImportRun.report`.
- **A12** `--dry-run` writes nothing: `vote` and `vote_position` counts remain 0 on the copy; `VoteImportRun.applied=False`.
- **A13** No network in unit tests: monkeypatched socket/fetch raises on any connection; all reads from fixtures.
- **A14** Idempotency in-memory: applying the same manifest twice yields identical counts and dedup keys (`source:native_vote_id`, `(vote_key,person_id)`, `sha256(fixtures||versions||dry_run)`); no duplicate-key errors.
- **A15** Corruption injection: flip one byte in a fixture → sha mismatch → import aborts with zero writes; restore → green.
- **A16** Build isolation: grep over `cmd_build_corpus` (`cli.py:526-712`), `prepare_db.py`, `backend.main`, `Dockerfile`, `ci.yml`, `data.yml` finds zero `votes-import|vot-parlament|votes_cdep` tokens; third-party HTTP 500 → `build-corpus --strict` exits 0 with `DATA_UNAVAILABLE`.

### 5.5 Exact 11-step governance recipe (verbatim structure from DR:372-382)

1. **Check the licence first** (DR:372). Use §7; if NC or SA, decide cross-check and stop — do not ingest values. *W1 target: `SourceLicense` row before any import.*
2. **Check robots.txt and pacing** (DR:373). Use `PoliteClient` only; never bypass CAPTCHA; never crawl `/declaratii/`; apply RT-12 per-host signals.
3. **Fetch raw pages into `fragment`** (DR:374). Set `source_name`, `source_id`, `source_url`, `checksum`, `snapshot_path`.
4. **Write a parser** in `pipeline/parse/<source>.py` (DR:375), follow `cdep_group.py`/`senat_grup.py`; save fixture under `tests/fixtures/` + unit test. *W1: `pipeline/sources/votes_cdep.py` + `tests/fixtures/votes/*`.*
5. **Write to target table with provenance** (DR:376): `source_url`, `confidence`, evidence row; never overwrite stronger `official_ledger` with weaker `community`.
6. **Use `dedup_key` for idempotency** (DR:377): re-running import must not duplicate rows.
7. **Add a CLI subcommand** in `pipeline/cli.py` (DR:378), follow `cmd_enrich`/`cmd_assets`; support `--dry-run` first.
8. **Update the audit** (DR:379): register in `pipeline/audit.py` `CHECKS` (`:973-984`) so missing/inconsistent data fails strict build.
9. **Only then** add a call to `.github/workflows/data.yml` (DR:380), with a separate cache key so a broken third-party source cannot block the official corpus. *W1: no data.yml wiring — see build-isolation A16.*
10. **Update `docs/DATA-MODEL.md`, `docs/RESEARCH.md`, `docs/VERIFICATION.md`** in the same commit (DR:381).
11. **Publish a new dataset release** (DR:382) and let existing release/Render verification prove it. *W1: dry-run only — publication deferred to W2.*

### 5.6 Exact licence appendix rows and attribution strings

| `source_name` | `license_id` | URL / quote (verbatim where marked) | `redistributable` | Attribution string |
|---|---|---|---|---|
| `cdep_facts` | `OGL-ROU-1.0` (facts; Law 8/1996 art. 9, DR:252) | cdep.ro MENȚIUNE JURIDICĂ applies to creative assets, not facts | 1 | project template: "Camera Deputaților — official parliamentary facts (names, dates, votes), source URL per row" |
| `senat_facts` | `OGL-ROU-1.0` | senat.ro facts; robots 404 | 1 | "Senatul României — official parliamentary facts, source URL per row" |
| `vot_parlament` | `CC-BY-4.0` | "CC BY 4.0" (DR:164); research/reference use only (RT-12) | 1 | "vot-parlament.ro · CC BY 4.0 · source URL per vote" |
| `ro_281` | `CC-BY-4.0` | verbatim on `/api`, `/despre`, `/metodologie`: "Toate datele sunt disponibile sub licență Creative Commons CC-BY 4.0" (D2:L46) | 1 | **exact mandatory**: "281.ro · Registrul neoficial al Parlamentului României" |
| `wikidata` | `CC0-1.0` | DR:200 | 1 | "Wikidata — CC0 1.0" |
| `gld` | `CC0-1.0` | `doi:10.7910/DVN/U1ZNVT` (DR:199) | 1 | "Global Legislators Database, doi:10.7910/DVN/U1ZNVT, CC0" |
| `partyfacts` | `CC0-1.0` | Dataverse API `doi:10.7910/DVN/TJINLQ`; site licence **UNVERIFIED**; `partyfacts.github.io` 404 (D2:L46) | 1 | "Party Facts, doi:10.7910/DVN/TJINLQ, CC0 1.0" |
| `ches_eui` | `CC-BY-4.0` | `hdl.handle.net/1814/69975` (D2:L46); chesdata.eu 2024 per-file UNVERIFIED | 1 | "CHES, EUI archive, hdl.handle.net/1814/69975, CC BY 4.0" |
| `data_gov_ro` | `OGL-ROU-1.0` / `CC-BY-4.0` (2020+) | DR:153 | 1 | "data.gov.ro / AEP — OGL-ROU-1.0 or CC BY 4.0, dataset ID per row" |
| `zenodo_3332908` | `CC-BY-4.0` | `doi.org/10.5281/zenodo.3332908` (DR:168) | 1 | "Zenodo 3332908, CC BY 4.0" |
| `v_dem` | `CC-BY-SA-4.0` | V-Dem FAQ (D2:L46) | 0 | "V-Dem, CC BY-SA 4.0 — external cross-check only" |
| `ipu` | `CC-BY-NC-SA-4.0` | D2:L46 | 0 | "IPU Parline, CC BY-NC-SA 4.0 — external cross-check only" |
| `open_sanctions` | `CC-BY-NC-4.0` | D2:L46 | 0 | "OpenSanctions, CC BY-NC 4.0 — external cross-check only" |
| `populist` | `UNVERIFIED` | OSF `node_license null`, no LICENSE (D2:L46) | 0 | "The PopuList — licence UNVERIFIED — conditional / external cross-check only" |
| `ser_prom` | `CC-BY-SA-4.0` (institutional) | DR:214 | 0 | "SER-PROM, CC BY-SA 4.0 — cross-check until CC-BY permission obtained" |

Rows with `redistributable=0` are display-only and excluded from every export (§7).

### 5.7 Exact command sequence — clean tree to green `pytest -q`, no writes outside a copy

```bash
# Scope: PRODUCT repo only
cd /home/nedaktov/parlament-deschis

# 1. clean-tree proof
git status --porcelain                       # expect empty (or only docs blueprint)
git rev-parse --short HEAD                   # expect 2995bfd

# 2. toolchain
uv sync --extra dev --locked
uv run ruff check pipeline backend scripts tests

# 3. WAL-safe copy — the ONLY writable DB for this sequence
python3 -c "import sqlite3; s=sqlite3.connect('data/parlament-real.db'); s.execute('PRAGMA wal_checkpoint(TRUNCATE)'); d=sqlite3.connect('/tmp/opencode/votes-dryrun.db'); s.backup(d); d.close(); s.close()"
python3 -c "import sqlite3; print({t:sqlite3.connect('/tmp/opencode/votes-dryrun.db').execute('select count(*) from '+t).fetchone()[0] for t in ['person','mandate','membership','event','organization']})"
# expect 3388 / 5273 / 7349 / 7429 / 120

# 4. capture fixtures (dev-only script created by AP-1.04; PoliteClient, no network in tests)
uv run python scripts/capture_vote_fixtures.py --out tests/fixtures/votes --manifest tests/fixtures/votes/manifest.json

# 5. create schema on the COPY only (create_all, SCHEMA_VERSION=1)
uv run python -m pipeline.cli --db /tmp/opencode/votes-dryrun.db create-all

# 6. dry-run ingest on the COPY (subparser created near cli.py:861)
uv run python -m pipeline.cli --db /tmp/opencode/votes-dryrun.db votes-import --fixtures tests/fixtures/votes --dry-run
uv run python -c "import sqlite3; c=sqlite3.connect('/tmp/opencode/votes-dryrun.db'); print(c.execute('select count(*) from vote').fetchone()[0], c.execute('select count(*) from vote_position').fetchone()[0])"
# expect 0 0  (A12)

# 7. focused + full tests (tests themselves point at fixtures/copy; A13 no network)
uv run pytest -q tests/test_votes_cdep_parser.py tests/test_votes_thirdparty_contract.py tests/test_votes_dry_run.py tests/test_votes_build_isolation.py
uv run pytest -q
# expect all green, exit 0

# 8. prove the shipped DB was untouched
python3 -c "import sqlite3; c=sqlite3.connect('file:data/parlament-real.db?mode=ro',uri=True); print({t:c.execute('select count(*) from '+t).fetchone()[0] for t in ['person','mandate','membership','event','organization']}); print(c.execute(\"select count(*) from sqlite_master where name like 'vote%'\").fetchone()[0])"
# expect 3388 / 5273 / 7349 / 7429 / 120  then  0
```

No `git add -A`; no command writes to `data/parlament-real.db`; no release or workflow is triggered in this sequence.

---

## 6. Frontend / statistical UX specification

### 6.1 Plan A — 281.ro (BLOCKED, design only until repo supplied)

**Status:** no local repo, public repo 404 (RT-01/02). **Deliverable:** design specification and component contracts only; **no product file is modified for Plan A.**

Reference design facts from the live site (D2:L54): Radar shows 78 signals with explicit denominators — e.g. "Din 423 voturi cu linie de partid clară, a votat ca majoritatea partidului în 53%" and "59% din cele 1295 voturi nominale"; deterministic thresholds (wealth jump ≥50% **and** ≥15,000 €; vote-line <70% over ≥80 votes; presence <80% over ≥50 votes); documented weights; right-to-reply at `legal@281.ro`. Grafice has stacked composition 2000–2028, per-party sparklines, `/grafice/harta/`, `/grafice/migratii/`, `/grafice/retea/`. Homepage has 8 investigation tiles including PREZENȚĂ LA VOT and LOIALITATE PARTID. `/api` serves static JSON + bulk CSV, CC BY 4.0.

Plan A components (design contract only): `RollCallAlignmentMatrix`, `PartyCohesionDefectionTimeline`, `IdeologicalSpatialMap`, `MpBehaviorScorecard`, plus upgrades to Compară/Radar/Grafice. Mandatory attribution on every view: "281.ro · Registrul neoficial al Parlamentului României"; echo the "semnal, nu verdict" stance; never present presence as an attendance score. **Unblock condition:** a real repo URL + write access is supplied and verified; then rerun §3.6 recipe against that codebase — not this one.

### 6.2 Plan B — local `parlament-deschis` (implementable, W4)

All components target `/home/nedaktov/parlament-deschis/frontend/src` and consume only endpoints whose CPs PASS. Baseline: 19 routes at `router.tsx:310-458`, nav `:242-289`, title map `:186-208`, tokens `index.css:5-45/51-72/76-89`, Tailwind bridge `tailwind.config.js:8-28` (v3 — **no Tailwind 4 migration**, MS:759). Reuse orphaned components before writing new ones (MS:755).

| Component | Host route(s) | Data contract | Filters | Accessibility | i18n keys |
|---|---|---|---|---|---|
| `RollCallAlignmentMatrix` | new `/votes` | `/analytics/vote-cohesion` envelope; `data.parties[] {party_id,votes,cohesion,ci,denominator}`; `min_votes=20` default | `chamber`, `legislature`, `from`, `to`, `min_votes` | `aria-sort` on all sortable columns; text alternative for cell heatmap | `votes.title`, `votes.denominator`, `votes.minVotes`, `votes.unavailable` + EN |
| `PartyCohesionDefectionTimeline` | `/traseism`, `/party/$shortName` | vote cohesion + dated `switch_group` events; reuse `Traseism.tsx:134-164,845-866` | `legislature`, `party`, `granularity` | SVG text alternative + tabular fallback; focus styles `index.css:198-201` | `timeline.cohesion`, `timeline.defection`, `timeline.gapNote` + EN |
| `IdeologicalSpatialMap` | `/compare`, `/parties` | `party_score` rows; `partyfacts_id` from alias map; XCHECK sources display-only with `BenchmarkLabel` | `year`, `ideology_variable` (`ches_left_right`,`vparty_populism`,`populist_dummy`) | text alternative listing coordinates + licence; no colour-only encoding | `ideology.map`, `ideology.external`, `ideology.licence` + EN |
| `MpBehaviorScorecard` | `/person/$id` | `/analytics/voting-record` + `/analytics/presence-at-vote` | `person_id` (lookup only), `legislature` | mandatory caveat string; **no score/rank field**; source links | `mp.votingRecord`, `mp.presenceCaveat`, `mp.noRanking` + EN |
| `ComparaUpgrade` | `/compare-mps`, `/compare` | existing compare data + voting record | existing filters + `voteCount` | scoped labels; `aria-sort` | `compare.scope`, `compare.denominator` + EN |
| `RadarUpgrade` | `/` (home investigation tile pattern) | 281.ro-style signals computed from **local** data with explicit denominators + thresholds | `chamber`, `legislature`, `minN` | each signal exposes numerator, denominator, threshold, method | `radar.signal`, `radar.denominator`, `radar.method` + EN |
| `GraficeUpgrade` | `/report`, `/coverage`, `/party/$shortName` | stacked composition, sparklines, map/migration/network patterns using local data | `legislature`, `chamber`, `party` | text alternatives + full legends (fix `AgeDistributionRadial.tsx:125` 4-row legend) | `grafice.composition`, `grafice.legend`, `grafice.network` + EN |
| `BenchmarkLabel` | every external series | props `{source,license_id}`; exact text below | — | `role="note"`; visible RO/EN | inline RO/EN literal per D2:L49 |

`BenchmarkLabel` exact visible text (D2:L49): **"External benchmark · {source} · {license_id} · not part of this project's CC BY 4.0 dataset"** with RO equivalent "Benchmark extern · {source} · {license_id} · nu face parte din setul de date CC BY 4.0 al acestui proiect".

New routes `/votes` and `/vote/$id` require top-nav entries (`router.tsx:242-289`) and title map entries (`:186-208`). `/compare-mps` currently has no top-nav link — only reachable from `Mps.tsx:395` (MS:684) — add one in W4.

**No attendance score**: presence is a fact with source and gaps; the caveat is verbatim: "Presence at a vote is a fact with known source gaps; this is not an attendance score and no ranking is computed." (MS:824).

### 6.3 The 16 verified defects — quick wins vs wave-coupled

| # | Defect | Exact location | Fix | Kind |
|---|---|---|---|---|
| 1 | Hero cards non-interactive, `onClick` undefined at 4 sites | `LiveDashboard.tsx:97-141` | wire navigation or remove affordance | Quick win |
| 2 | `div role=button`, deprecated `onKeyPress`, `window.location.href` loses `asOf`, nested link invalid | `DashboardCard.tsx:76-95` | `<button type="button">` / router link preserving `asOf` | Quick win |
| 3 | Numbers without denominator; definition collision | `DashboardCard.tsx:97-108`, `InfoStat.tsx:48-82`, `api.py:985-995`, `pipeline/queries.py:38-42` | label `active_memberships_as_of`, `switches all-time` | Quick win (W1) |
| 4 | `edges=[]` placeholder as data | `LiveDashboard.tsx:196` | remove / "not available" | Quick win |
| 5 | Both bars hardcoded 100% | `CrossChamberFlow.tsx:24-27,55-80` | compute or remove | Quick win |
| 6 | Fake coverage + hardcoded `fill="white"` | `DataQualityGauge.tsx:37-53,108,134` | real semantics; CSS var | Quick win |
| 7 | 4-row legend + hardcoded white | `AgeDistributionRadial.tsx:113,125` | full legend; CSS var | Quick win |
| 8 | Permanent "unavailable" state | `InstitutionalView.tsx:71-74` | real state | Quick win |
| 9 | Page size shown as total | `Mps.tsx:82-106` | real total from API | Quick win |
| 10 | Running tally labelled "total" | `Committees.tsx:239-243` | relabel running | Quick win |
| 11 | Unweighted mean-of-means | `Demographics.tsx:44-57` | weight by group size | Quick win (with W3) |
| 12 | Fake coverage | `CommitteeControl.tsx:122-125` | real coverage | Quick win |
| 13 | Unscoped aggregates | `PartyComparison.tsx:46,51` | add scope/denominator | Quick win |
| 14 | SenateHistory sums mislabelled | `SenateHistory.tsx:67-69` (label over `reduce` at `:68`; `senateStatCoverage` at `:82-85`) | correct sum labels | Quick win (line VERIFIED, RT-19) |
| 15 | PartyTimeline "Total switches" shows `datedJoins` | `PartyTimeline.tsx:123-125` (value at `:124`) | correct label | Quick win (line VERIFIED, RT-19) |
| 16 | Theme toggle only on `/` | `ui/DashboardHeader.tsx:15` | mount site-wide | Quick win |

**Wave-coupled:** vote routes/components (W1/W2), `BioFacts`/`BioCoverageNote` (W2), `IdeologyScatter`/`PartyScoreTable` (W3), speech citations (W3), electoral components (W3), `BenchmarkBand`/`BenchmarkSourceNote` (W3), final API/export overhaul (W4). **Quick wins:** #1–#13, #16 plus a11y/i18n fixes — shippable without new data. Supporting defects: SVG text alternatives, `ErrorState` role duplication, `EmptyState` nested `<svg>`, 57 i18n keys with literal English fallbacks, `nav.committees`/`nav.compare` only in `ro` (D2:L55, MS:744).

---

## 7. Licence / quarantine standard

### 7.1 `SourceLicense` registry — exact CheckConstraint

```sql
CREATE TABLE source_license (
    source_name      TEXT PRIMARY KEY,
    license_id       TEXT NOT NULL,
    license_url      TEXT NOT NULL,
    redistributable  BOOLEAN NOT NULL DEFAULT 0,
    share_alike      BOOLEAN NOT NULL DEFAULT 0,
    verification     TEXT NOT NULL,        -- VERIFIED | UNVERIFIED | CONDITIONAL
    evidence_url     TEXT,
    evidence_quote   TEXT,                 -- verbatim; never paraphrased as a quote
    verified_on      TEXT NOT NULL,        -- YYYY-MM-DD, 2026-11-20 for this baseline
    attribution      TEXT NOT NULL,
    CHECK (redistributable = 0 OR license_id IN ('CC0-1.0','CC-BY-4.0','OGL-ROU-1.0'))
);
```
Model placed after `db.py:423` before `:426` (D2:L49). Seed rows per §5.6. `fragment` gains `license_flag`/`redistributable` via `_ADDED_COLUMNS db.py:463-481`.

### 7.2 Row-level fields on every external-value table

`party_score`, `election_result`, `benchmark`, `context_year`, `speech`, `party_alias_map` (and any future external table) each carry:
`source_name TEXT NOT NULL REFERENCES source_license(source_name)`, `license_flag TEXT NOT NULL` (snapshot), `redistributable BOOLEAN NOT NULL`, `source_url TEXT NOT NULL`, `dedup_key TEXT NOT NULL UNIQUE`, and **repeat the CHECK**: `CHECK (redistributable = 0 OR license_id IN ('CC0-1.0','CC-BY-4.0','OGL-ROU-1.0'))` expressed on the row's `license_flag` equivalently: `CHECK (redistributable = 0 OR license_flag IN ('CC0-1.0','CC-BY-4.0','OGL-ROU-1.0'))`. No NC/SA/UNVERIFIED value may set `redistributable=1`. Provenance chain: row → `Fragment(source_name,source_id,source_url,checksum,snapshot_path)` → `SourceLicense` quote + `verified_on`.

### 7.3 Export guards

- `_assert_exportable(session)` at `pipeline/export.py:105` — raises if any candidate row has `redistributable=0` or `license_flag` outside the allowed set; every export format calls it before writing.
- `meta.license_exclusions` at `export.py:233-249` — enumerates `XCHECK` sources (`ipu`, `open_sanctions`, `v_dem`, `populist`, `ser_prom`) excluded from all outputs.
- New export branch at `export.py:352` (adding names to `CSV_DATASETS` alone derives empty columns from Popolo — do not do that, MS:832); route beside `backend/routers/exports.py:190-203`; blocks in `/export/report:139-159`.
- XCHECK rows may be **displayed only**, with `BenchmarkLabel`, never exported as our data.

### 7.4 Audit check

Register `check_license_quarantine` in `pipeline/audit.py:973-984` `CHECKS` (currently 10 checks). It asserts: every external row has a `source_license` row; `redistributable=1` implies allowed `license_id`; no NC/SA/UNVERIFIED value in an exportable table; every benchmark/speech row has a Fragment checksum. Baseline the expected findings in the same commit (strict must remain `275 known errors, 0 new errors` or an approved reviewed delta).

### 7.5 `BenchmarkLabel` text

Visible RO/EN: **"External benchmark · {source} · {license_id} · not part of this project's CC BY 4.0 dataset"** / "Benchmark extern · {source} · {license_id} · nu face parte din setul de date CC BY 4.0 al acestui proiect" (D2:L49). Rendered with `role="note"` on every external series, including `IdeologicalSpatialMap`, `BenchmarkBand`, `BenchmarkSourceNote`, `ElectoralBaseCard`.

### 7.6 Sign-off checklist (per @worker-covariates)

- [ ] Data minimisation: no home addresses, private emails, family financial details, `/declaratii/` content, photos/logos/audio/video.
- [ ] Exact licence quote + URL + `verified_on` recorded for each source; PopuList, chesdata 2024, Party Facts site licence marked UNVERIFIED with resolvers.
- [ ] `redistributable` defaults to **false**; only CC0/CC-BY/OGL rows may be true.
- [ ] 281.ro attribution string exact: "281.ro · Registrul neoficial al Parlamentului României".
- [ ] CC0 Dataverse copy for Party Facts (`doi:10.7910/DVN/TJINLQ`).
- [ ] EUI CC BY 4.0 archive for CHES (`hdl.handle.net/1814/69975`).
- [ ] PopuList conditional/XCHECK until licence resolved; `dataset_key='populist'` only.
- [ ] V-Party / IPU / OpenSanctions values `redistributable=0`, never exported (0 rows in exportable tables).
- [ ] Party Facts IDs 958 / 276 / 1034 / 120 in `party_alias_map` (four IDs).
- [ ] Provenance on every row (source_url + Fragment checksum + confidence + date precision + dedup_key).
- [ ] `check_license_quarantine` registered and green; `_assert_exportable` proven by injection test.
- [ ] `test_license_quarantine.py` green with raw output.
- [ ] `BenchmarkLabel` visible on every external series in browser proof.
- [ ] Docs updated in same commit (`DATA-MODEL.md`, `RESEARCH.md`, `VERIFICATION.md`, `LICENSE-APPENDIX.md`).

---

## 8. Risk register and day-1 checklist

### 8.1 Risk register (24 risks; L/M/H)

| # | Risk | L | I | Mitigation | Owner |
|---|---|---|---|---|---|
| R-01 | WAL copy corruption — working DB WAL (`db.py:447`), shipped DELETE (`prepare_db.py:170-177`); both physically WAL 2,2 with sidecars | M | H | `sqlite3 backup()` + `PRAGMA wal_checkpoint(TRUNCATE)`; never raw `cp`; verify counts post-copy | qa-sentinel |
| R-02 | 300 s cache serves stale numbers after pin (`backend/cache.py:28`) | H | M | new endpoints `cache:no-store`; cache-busting verify; document residue as irreversible | votes-etl / qa-sentinel |
| R-03 | Immutable release edited by mistake | L | H | only `latest-release.txt` mutable; tag `data-${run_id}-${attempt}`; release owner sole control | supervisor |
| R-04 | Third-party outage blocks official corpus | M | H | cdep strict; vot-parlament `DATA_UNAVAILABLE`; enrichment `continue-on-error` + own cache | votes-etl / enrichment-ops |
| R-05 | Licence contamination — NC/SA/unverified values in CC-BY export | M | H | covariates veto; SourceLicense CHECK + `_assert_exportable` + XCHECK display-only | covariates |
| R-06 | Stale docs contradict live data (D1–D14) | H | M | W1 AP-1.15; every wave updates docs in same commit | supervisor |
| R-07 | Untracked research doc lost | H | M | explicit `git add docs/DATA-ENRICHMENT-RESEARCH.md`; never `git add -A` | supervisor |
| R-08 | Vercel tolerance anomaly — 180 s grace but `vercel.json:6 ignoreCommand:""` | M | H | remove dead tolerance; assert deploy exists | qa-sentinel |
| R-09 | `npm run lint` not a CI gate | H | M | add lint job; gate on it | qa-sentinel |
| R-10 | `deploy-all.sh:21` footgun (hardcoded commit + `git add -A`) | M | H | quarantine + dirty-tree guard; never use for promotion | qa-sentinel |
| R-11 | Marker push blocked by branch protection (UNVERIFIED) | M | M | `gh api .../branches/main/protection`; fallback explicit Render trigger | qa-sentinel |
| R-12 | Person fabrication via `PersonResolver.resolve()` | M | H | lookup-only identity; person count 3,388 assertion; unknown → quarantine | votes-etl / enrichment-ops |
| R-13 | Field-semantics mis-parse — now VERIFIED but could drift | H | H | fixtures lock par1/CAMERA/idv/tag sets (A2/A4/A5); drift → fail CP | votes-etl |
| R-14 | `21.01.1991` misread again via fixed-index parser | M | M | header-driven parsing + Iorga 1954-01-01 test (RT-07) | enrichment-ops |
| R-15 | Identity mismatch in GLD/SER-PROM — name-only merge | M | H | exact ID rules; conflicts `status='conflict'`; idm 285/286 distinct | enrichment-ops |
| R-16 | REST/GraphQL divergence presented as convergence | H | M | fix cohesion envelope + median before claim; byte-comparison test | frontend-stats |
| R-17 | Attendance score introduced | M | H | audit `grep` 0 hits; mandatory caveat; no ranking | all |
| R-18 | Fake coverage / placeholder numbers read as data | H | M | 16 defects; coverage dimensions honest | frontend-stats |
| R-19 | Immutable browser bundle cache (1 year, `vercel.json:14-15`) serves old UI after rollback | H | M | treat irreversible; version asset paths; document in every rollback | frontend-stats |
| R-20 | Render auto-deploy race (`platform-rollback.yml:145`) redeploys over rollback | M | H | disable auto-deploy when freezing; re-enable after fix | qa-sentinel |
| R-21 | Vercel Hobby only previous deployment rollback | M | M | confirm target in dry-run; break-glass dashboard | qa-sentinel |
| R-22 | Read-only runtime prevents on-the-fly fixes | M | M | all enrichment pre-release on copies | enrichment-ops |
| R-23 | `EVIDENCE_TYPES` defined but unused → rows lack evidence | H | M | Fragment + source_url on every row; W5 registration | covariates |
| R-24 | `mandate.constituency` 100% NULL blocks electoral base | H | M | `/analytics/electoral-base` unavailable + 5273; never guess | frontend-stats |
| R-25 | Audit baseline drift from new findings | M | H | new checks baselined in same commit; 275/0 or reviewed delta | covariates |
| R-26 | Tooling scope error — `just` in product repo | M | L | repo-scope banner §2.7 in every command block | all |
| R-27 | NedCode4 docs stale (exit 3) / GENERATED block hand-edited | H | M | `just docs`; stage explicit paths; never hand-edit | supervisor |
| R-28 | Party Facts four IDs collapsed to one (old strategy error) | H | H | `party_alias_map` 958/276/1034/120; CP-3.02 | covariates |
| R-29 | PopuList wrong dataset (`'pop'` = Poll of Polls) | M | M | join on `'populist'`; quarantine `'pop'`; licence UNVERIFIED | covariates |
| R-30 | 281.ro treated as writable target | H | H | Plan A design-only; repo-scope rule; no product file for 281.ro | supervisor |

### 8.2 Day-1 checklist

- [ ] Read this blueprint, `D2`, `MS`, `DR`, `DEPLOYMENT.md`, `VERIFICATION.md` — no skipping.
- [ ] State repo-scope rule in the ticket: NedCode4 `just *` only in `/home/nedaktov/Desktop/NedCode4`; product commands only in `/home/nedaktov/parlament-deschis`; **no 281.ro repo**.
- [ ] Run AP-1.01 baseline counts; paste output: `3388 / 5273 / 7349 / 7429 / 120`.
- [ ] Run AP-1.02 git check: `2995bfd`; clean tree.
- [ ] Record MCP counts with live discovery: 33 / 8 / 7 = 48; do not state a skill count without recount (RT-15).
- [ ] @worker-covariates signs `SourceLicense` seed (incl. exact 281.ro attribution string and four Party Facts IDs).
- [ ] Commit `docs/DATA-ENRICHMENT-RESEARCH.md` explicitly; never `git add -A`.
- [ ] Close D1–D14 in one doc commit; verify `grep -n "No roll-call" docs/METHODOLOGY.md` → no hit.
- [ ] Capture the 8 vote fixtures + manifest; lock FIELD-MAP with VERIFIED semantics (RT-04/05/06/17) and 2 UNVERIFIED resolvers.
- [ ] Create models on the copy only; run §5.7 command sequence end-to-end to a green `uv run pytest -q` with shipped DB unchanged.
- [ ] Add `npm run lint` CI gate; remove dead 180 s Vercel tolerance; quarantine `deploy-all.sh`; resolve branch protection or record UNVERIFIED.
- [ ] Fix quick-win defects #1–#13, #16 with resolved lines for #14/#15 (RT-19); fix definition collisions (`active_memberships_as_of`, switches all-time).
- [ ] In NedCode4 repo only: `just doctor`, `just docs`, re-run `just docs-check`; stage explicit paths (never hand-edit GENERATED blocks).
- [ ] Record CP-1.01 … CP-1.20 with raw output + timestamp in `knowledge-memory`.
- [ ] Only after all W1 CPs PASS: open W2 P0 — fix CLI/DB bugs (`enrich.py:368-372`, `cli.py:260-272,767`) **before any enrichment command**.

### 8.3 Outstanding UNVERIFIED items and their resolvers

| Item | Resolver | Owner |
|---|---|---|
| Day-level `CAMERA=1` (senate-only day) | capture one senate-day `evot2015.xml` fixture | votes-etl |
| `NU`/`AB` literal VOT tokens | capture a vote whose official totals require them | votes-etl |
| Test-vote (VOTID 37515) exclusion policy | W5 written sign-off | covariates |
| vot-parlament stable API contract | contract test on 22-column header + 8 JSON top keys; drift → `DATA_UNAVAILABLE` | votes-etl |
| chesdata.eu 2024 per-file licence | download file + read headers, or use EUI CC BY archive | covariates |
| Party Facts site licence; `partyfacts.github.io` 404 | Dataverse API metadata + written confirmation | covariates |
| PopuList licence | OSF licence file or written permission; until then XCHECK | covariates |
| Branch-protection required checks | `gh api repos/nedaktov-ops/parlament-deschis/branches/main/protection` | qa-sentinel |
| Fixture count 22 vs 23 | `find tests/fixtures -type f | wc -l` at execution | qa-sentinel |
| NedCode4 skills 20 vs 21 | `just docs` + recount `.opencode/skills/*/SKILL.md` | supervisor |
| Production release asset state / deployed SHA+tag | credentials-gated `gh`/health check | qa-sentinel |
| Tests actually executed in recon | **NOT PROVEN** — run them in W1 §5.7 | qa-sentinel |

---

**Final supervisory statement.** This blueprint contains no placeholders: every UNVERIFIED item has a named resolver, every action point has a checkpoint, every checkpoint has raw-evidence expectations, an exact rollback and an irreversible-items note, and every external table is gated by a licence CHECK plus export guard. The earlier 967-line strategy was a sound architecture but carried verified-wrong operational facts (281.ro target, old vote URL, unknown field semantics, one-ID party lineage, PopuList licence, future-DOB anomaly, apply-by-default CLI). Those have been corrected against the six-worker digest. If shipping pressure ever conflicts with evidence, the answer is **NOT PROVEN**, not PASS. That discipline — source URL on every row, SHA-256 snapshots, conservative identity matching, strict audit before release, no attendance score, no incompatible licence — is what makes the 10× platform trustworthy rather than merely larger.

**Status:** integration complete; ready for parent agent to present/save. **No product file was modified.**

---

## Addendum A — Live MCP catalog volatility (recorded 2026-11-20)

During final validation the Code Mode tool catalog changed three times inside one session:

| Observation | chrome-devtools | opencode | shadcn | prompt-optimizer | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Supervisor integration time | 33 | 8 | 7 | 0 | **48** |
| First re-verification | 33 | 8 | 7 | 3 | **51** |
| Second re-verification | 33 | 8 | 7 | 0 | **48** |
| Third re-verification | 33 | 8 | 7 | 3 | **51** |

The `prompt-optimizer` namespace (tools `iterate-prompt`, `optimize-system-prompt`, `optimize-user-prompt`) toggled on and off between calls. Therefore **no checkpoint in this blueprint may assert a fixed tool count or assume a namespace is present.** §2.5 and RT-14 are corrected as follows:

- The **stable** namespaces in every observation are `chrome-devtools` (33), `opencode` (8) and `shadcn` (7).
- `prompt-optimizer` is **CONDITIONAL**. Its presence, and the exact parameter schema of any tool, must be resolved by a fresh `search(...)` inside `execute` immediately before use.
- Any agent that calls an unlisted tool name, or reports a tool count from memory, fails its checkpoint (`NOT PROVEN`).

This is the same evidence discipline applied elsewhere in the blueprint: the live tool catalog is a mutable external fact, not a stored assumption.

---

## Addendum B — Optimizer-assisted prompt pass (2026-11-20)

The user requested that the strategy request be sharpened with the `prompt-optimizer` MCP before execution. Result:

- Tool resolved by live discovery: `tools["prompt-optimizer"]["optimize-user-prompt"]` (template `user-prompt-planning`).
- Call result: **`[error.prompt.optimization] / [error.llm.api] Failed to send message: Request timed out.`**
- Per the governing instruction ("call once; never block; do not optimize recursively"), no retry was made and work continued with the original request.

Consequences for the fleet:

1. **No "optimized prompt" artifact exists.** Any checkpoint that claims the sharpened spec was applied is `NOT PROVEN`.
2. This is a second, independent confirmation of Addendum A: even when a tool is **visible** in the catalog, its backing service may be unavailable. Visibility ≠ availability.
3. Add to the @worker-qa-sentinel verification checklist: before any agent depends on an MCP service, resolve it with `search(...)` **and** make one bounded call; on timeout/error, record `NOT PROVEN` and proceed with the unassisted instruction. Never fabricate optimizer output or silently substitute a local rewrite.
4. The strategy itself is unaffected: its authority remains the six-worker evidence digest and the file:line citations, not any prompt-engineering transform.
