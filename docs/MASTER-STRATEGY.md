# Parlament Deschis — Master Strategy: From Party-Switch Tracker to a 10× Parliamentary Statistics Platform

**Document type:** Integration and strategy synthesis (read-only).  
**Date:** 2026-11-20.  
**Prepared by:** Master Supervisor (integration of seven read-only specialist investigations).  
**Audience:** Senior engineers, release engineers, governance/audit owner, frontend team, and the NedCode4 tooling operator who will execute the waves.  
**Companion documents:** `docs/DATA-ENRICHMENT-RESEARCH.md` (sources, licences, roadmap), `docs/VERIFICATION.md` (audit semantics and real-corpus results), `docs/DEPLOYMENT.md` (gates, verification, rollback), `/tmp/opencode/supervisor-input.md` (consolidated seven-worker digest with file:line citations).

---

## 1. Purpose, scope, evidence rule, and change statement

### 1.1 Purpose

This document converts seven independent, read-only investigations into one executable strategy. It does not add new research and it does not implement anything. Its job is to fix the order of work, the evidence standard, the ownership, the checkpoints, and the rollback path before any engineer touches the product repository.

The user's instruction is binding and is reproduced here as the control clause:

> No guesswork, no assumptions, no presumptions. If anything changes, agents must first investigate the exact lines of code affected plus research, deployment and testing. The project must become a trustworthy statistical source, future-proof, with no old technology. Use NedCode4 abilities, skills and MCPs. Deliver a MASTER STRATEGY with WAVES → PHASES → ACTION POINTS → CHECKPOINTS → FAIL-SAFE ROLLBACKS, plus highly customised RECIPES for the Supervisor and each Worker. Professional standard of a large team of senior specialists.

### 1.2 Scope

**In scope:** the repository at `/home/nedaktov/parlament-deschis` (product) and the tooling repository at `/home/nedaktov/Desktop/NedCode4` (tooling only). All seven enrichment domains researched by the workers: votes, biographies, party covariates, committee histories/speeches, elections, benchmarks, and the tooling/verification layer that governs them all.

**Out of scope:** changing any product file in this session; publishing releases; contacting any third-party source; merging any data into the shipped corpus; bypassing a CAPTCHA; adding a licence-incompatible dataset; inventing a tool, token, or secret.

### 1.3 Evidence rule (applies to every sentence below)

| Grade | Definition | How it is marked here |
|---|---|---|
| **VERIFIED** | Directly observed in a file at a cited `path:line`, measured from `data/parlament-real.db`, taken from a live HTTP response on 2026-11-20, or quoted from `DEPLOYMENT.md` / `VERIFICATION.md` / `DATA-ENRICHMENT-RESEARCH.md`. | Stated plainly with the citation. |
| **INFERRED** | A logical deduction from two or more VERIFIED facts. No new fact is introduced. | Tagged `[INFERRED]`. |
| **UNVERIFIED** | Could not be confirmed by the seven workers from the evidence available. It is never treated as true. It is resolved by a named fixture, command, or check defined in the wave that needs it. | Tagged `[UNVERIFIED]` **and** paired with a resolver. |

Rule of precedence: **evidence over assertion**. A check that cannot run is reported as *not proven*, never as a pass (W7, digest line 78). No worker may convert an UNVERIFIED item into a plan assumption; they must run its resolver first.

### 1.4 Explicit no-change statement

**No implementation code, database, schema, pipeline, test, CI workflow, or deployment configuration was changed by this strategy work.** All seven workers were read-only; the Master Supervisor likewise only read files. `docs/DATA-ENRICHMENT-RESEARCH.md` itself declares the same at its line 4. The only artefact produced here is this strategy text, to be saved by the parent agent under `docs/`. The research document `docs/DATA-ENRICHMENT-RESEARCH.md` is currently **untracked** (W5, digest line 57) and must be committed as the first action of Wave 0 — that is a documentation commit, not an implementation change.

---

## 2. Executive summary

### 2.1 The current truth of the project (VERIFIED, measured 2026-11-20)

Measured directly from `data/parlament-real.db` (digest line 3; research §1, lines 42–53):

| Object | Count | Note |
|---|---:|---|
| `person` | 3,388 | — |
| `mandate` | 5,273 | Both chambers, all 10 legislatures |
| `membership` | 7,349 | Every row has `source_url` + SHA-256 evidence |
| `event` | 7,429 | join 5,282 · switch_group 1,217 · leave 924 · group_founded 6 |
| `organization` | 120 | chambers, groups, parties, committees, bureaus |
| `person` with no `birth_date` | 275 | ~8% of people |
| `person` with `wikidata_qid` | 0 | `enrich.py` exists but is never scheduled (research F3, line 82) |
| `person_identifier` schemes | `cdep_mandate` 3,381 · `cdep_person` 3,381 · `cdep_idm` 335 | No Wikidata, Senate-GUID, GLD, EP or Party Facts IDs |
| `mandate.constituency` NULL | 5,273 of 5,273 | 100% NULL — election-base modelling cannot join today |
| `vote` / `vote_position` / `election_result` / `benchmark` / `person_attribute` / `party_score` / `speech` tables | **0** | None exist (research F4, line 83) |
| `event.snapshot_hash` NULL | 7,429 of 7,429 | No archived raw snapshot on events (W5 gap) |
| `group_founded` events with no `source_url` | 6 | Governance gap (W5) |

Git state: `main @ 2995bfd`, `origin/main` matches (digest line 3). Working DB `data/parlament-real.db` is **not git-tracked**; shipped DB must be `journal_mode=DELETE` (prepare_db.py:170-177) while the working DB is WAL (db.py:447) — this is a real backup hazard, not a theoretical one (W4, digest line 48).

Mandates by chamber and legislature are fully populated (research lines 57–64): 1990 447/126, 1992 381/160, 1996 367/154, 2000 393/163, 2004 378/163, 2008 339/137, 2012 416/179, 2016 361/136, 2020 354/151, 2024 336/132. **The Senate "gap" in older docs is stale** — do not re-ingest either chamber from scratch (research F1, line 80).

### 2.2 What already works (and must be preserved)

- Fail-closed data pipeline: strict collection → strict audit → immutable tag `data-${run_id}-${attempt}` → GitHub release with 3 assets → pin `data/latest-release.txt` → explicit Render API deploy → poll served `release_tag` up to 30 min (W4, digest line 44; DEPLOYMENT.md:77-81).
- Strict audit with reviewed baseline: **275 known errors, 0 new errors** (W4, digest line 50); the 275 = 223 `mandate_coverage` + 50 `overlap` + 2 `index_reconciliation` (VERIFICATION.md:60-71). New or changed errors fail the gate; resolved findings are reported so the allowlist can shrink (VERIFICATION.md:21-28).
- Evidence discipline on memberships: 0 `evidence` errors, 0 `switch_event` errors, 0 `interval_order`, 0 `missing_start` (VERIFICATION.md:64-70).
- Polite acquisition: `PoliteClient` with identifying User-Agent, robots.txt honouring, per-host pacing (2.5 s), conditional GET, exponential backoff, 429 waiting, and **hard stop on CAPTCHA** (research line 74; §4, lines 221-237).
- Deployment verification: `Deploy verify` asserts SPA shell, `/api/health` through Vercel rewrite, Render health endpoints, non-zero persons/memberships, `dataset.release_tag` equal to `data/latest-release.txt`, valid `/api/coverage` and `/api/traseism/overview` (DEPLOYMENT.md:96-114).
- Rollback tooling exists: `platform-rollback.yml` dry-run-first for Vercel and Render (DEPLOYMENT.md:141-170).

### 2.3 What is stale or wrong in the docs (VERIFIED contradictions — fix in Wave 0)

| # | Stale claim | Correct truth | Citation |
|---|---|---|---|
| D1 | `METHODOLOGY.md:501` says "No roll-call or vote publications found" | False: cdep XML, vot-parlament.ro (36,103 votes / 6,893,607 positions), senat.ro nominal votes all exist | W5 digest line 53; research lines 120, 160 |
| D2 | `docs/RESEARCH.md` robots facts: cdep disallows `/ords/`, `Crawl-delay: 5`; senat `Crawl-delay: 10` | cdep robots is 37 bytes: `User-agent: *` / `Disallow: /declaratii/`; senat robots is 404 | research lines 100-102, 221-237 |
| D3 | `DATA-COMPLETENESS-RECOVERY.md:3` says 7,358 memberships | 7,349 (`db.py:505` and measured DB) | W5 digest line 56 |
| D4 | Docs say coverage/enrich CLI not wired | Both are wired (`cli.py:282`, `cli.py:260`) — but `enrich --apply` is simply never called by `data.yml` | W5 digest line 56; research F3 |
| D5 | Coverage seat count 330 | 329 (`audit.py:812`) | W5 digest line 56 |
| D6 | `AUDIT.md:134` wrong line pointer; `AUDIT.md:121` historical event fields; `audit.py:410-414` docstring vs body | Need in-place correction | W5 digest line 56 |
| D7 | `REASONS` enum vs actual DB values mismatch | Needs reconciliation, not assumption | W5 digest line 56 |
| D8 | `data/licenses/README.md:105-106` omits `/declaratii/` prohibition | Add the prohibition verbatim | W5 digest line 56 |
| D9 | `About.tsx:263-298` hides `coverage` row `note` | Genuine gap disclosure is suppressed in UI | W5 digest line 53 |
| D10 | Dashboard shows "Memberships 4,461", "Switches 2,002" | 4,461 = *active* memberships on 2026-11-20 under `end_date >= ref`; 2,002 = *all-time* switches with no `as_of`. Same field names, two meanings | W2 digest lines 19-20; `api.py:985-995`, `:999-1005`, `pipeline/queries.py:38-42` |
| D11 | "Legislatures 20" | 20 `KeyEvent` rows vs 10 unique labels | W2 digest line 20 |
| D12 | `vercel.json` documented `ignoreCommand` git-diff skip | Actually `ignoreCommand: ""` — no build is skipped; the old tolerance in `verify-deploy.sh` for an absent Vercel deploy after 180 s is dead code and weak proof | W4 digest line 46; DEPLOYMENT.md:185-192 |
| D13 | `docs/DATA-ENRICHMENT-RESEARCH.md` untracked | Must be committed | W5 digest line 57 |
| D14 | "all 20 scopes full" coverage | True only for mandates/memberships; votes/biographies/committee history are not full | research F2, line 81 |

### 2.4 The 10× thesis

The project today answers *"who changed parliamentary group, and when?"* It cannot answer *"how did that MP actually vote, what did their party believe, what was their constituency's electoral base, and is this number unusual by international standards?"*

The single highest-value move is **roll-call votes as first-class, dated, provable events** (research line 32). That one addition activates party cohesion on real divisions, an MP-level voting record, presence-at-vote context, dated event citations, and a much sharper traseism story. Around it, four supporting axes compound the value: biographies (275 missing DOBs, zero education/occupation/birthplace), party covariates (CHES/V-Party/PopuList via Party Facts IDs), committee histories and speeches (dated committee roles, Zenodo 3332908, monitorul.ai citations), and elections + benchmarks (AEP denominators, World Bank/EC/Eurostat comparison lines).

The multiplier is only real if the trust properties survive the growth: **every row carries source URL + confidence + date precision + dedup_key; every new source passes a legal gate; every release passes strict audit; no attendance score.** If any of those break, the platform gets bigger but less trustworthy — which is the opposite of the brief.

---

## 3. Safety contract and non-negotiables

These are hard constraints. No wave, action point, or agent may override them. A conflict between a checkpoint and a non-negotiable is resolved in favour of the non-negotiable.

### 3.1 Evidence over assertion

- An UNVERIFIED item cannot be implemented. It must first be resolved by the fixture/command named in this document.
- Every PASS requires pasted raw output (counts, exit code, command string) and a timestamp. A screenshot for UI work is mandatory; for non-UI work the raw terminal output is the screenshot.
- Checks that cannot run are recorded as `NOT PROVEN`, never as PASS.

### 3.2 Provenance on every row

Every new row in `vote`, `vote_position`, `person_attribute`, `party_score`, `election_result`, `benchmark`, `speech`, `context_year`, and any new event must carry:

| Field | Rule |
|---|---|
| `source_url` | Non-null, exact page/endpoint, archived via `record_fragment` (`pipeline/fragments.py:46-80`) with checksum. |
| `confidence` | From the declared enum. Never overwrite a stronger `official_ledger` value with a weaker `community` value (research §7 step 5, line 372). |
| **date precision** | Store `birth_date_precision` / date precision explicitly (day/month/year). Where only a month is known (cdep `par=V01..V12` tables), do not fabricate a day. |
| `dedup_key` | Unique; re-running an import must not duplicate rows (research §7 step 6, line 373). |
| `detected_at` / `computed_at` | Export as aware UTC where present (W3, digest line 35). |

Note the specific exception: `Evidence.membership_id` is **NOT NULL** (`db.py:275-281`), so vote evidence cannot be attached through `Evidence`. Use `Vote.event_id → Event` plus `Fragment` (W1, digest line 6). For biographies, `person_attribute` **is** the evidence carrier — do not relax the `Evidence` constraint (W6, digest line 61).

### 3.3 Identity rules (never change — research line 380)

1. Exact official ID match → auto-link.
2. Name + birth date → propose merge.
3. Fuzzy name without a date → review queue only.
4. Conflicting official IDs in the same legislature → **never merge**.
5. QID → strong signal, still check.
6. All resolution stays in `pipeline/identity.py` (`PersonResolver.resolve()`, digest line 11 at `identity.py:118-148`). **Vote and biography ingestion must use lookup-only** `PersonIdentifier(scheme='cdep_mandate', identifier=f'deputies:{leg}:{idm}')` (`ingest_corpus.py:192-209`), fallback `cdep_idm`. Unknown person → `person_id = NULL` + verbatim `member_name` + audit warning. W1 and W6 are forbidden from calling `PersonResolver.resolve()` because it creates persons.

### 3.4 Polite acquisition

- All sources use `PoliteClient` only. No new HTTP client, no `requests` in a parser.
- 2.5 s per-host pacing, identifying User-Agent, conditional GET, backoff, 429 waiting.
- **Hard stop on CAPTCHA — never bypassed** (research line 74). AEP whole site is behind reCAPTCHA: prefer data.gov.ro mirrors (research line 150).
- **Never crawl `/declaratii/`** — cdep robots disallows it (research line 125, 229). No asset/interests bulk ingestion in any wave.
- senat robots is 404 (research line 232): absence of a robots file is not permission to be impolite.
- Third-party failure is non-fatal to the official corpus: cdep primary is strict-gated; vot-parlament is non-fatal `DATA_UNAVAILABLE` (W1, digest line 9); all enrichment is `continue-on-error` with its own cache (W6, digest line 67).

### 3.5 Licence flags

Three classes only (W5, digest line 54; research §5 lines 252-269):

- **COPY** (safe into our CC-BY-4.0 output): cdep/senat facts, 281.ro (self-declared CC BY 4.0, repo 404), vot-parlament.ro CC BY, Wikidata CC0, GLD CC0, data.gov.ro/AEP OGL/CC BY, Zenodo 3332908 CC BY, World Bank/Eurostat CC BY, monitorul.ai public text/CC BY dumps, EP Open Data CC BY, ParlGov CC0, PopuList open, Party Facts free.
- **XCHECK ONLY** (never copy values into our release): OpenSanctions CC BY-NC, IPU CC BY-NC-SA, V-Dem/V-Party CC BY-SA (prefer EUI CC BY archive copies), parlament.openpolitics.ro (unreachable — licence unverifiable), CHES per-file (use the EUI CC BY 4.0 archive).
- **CONDITIONAL**: SER-PROM institutional CC BY-SA — cross-check unless permission for CC-BY release is obtained; CHES per-file.

Every benchmark/party_score/election_result row carries `license_flag` and `redistributable` boolean; `license_flag` gates export (`export_ok`). XCHECK rows may be displayed *only* as clearly labelled external comparison lines, never as our data (research line 36; W3 digest line 36).

Legal basis for treating official parliamentary facts as copyable: Romanian Law 8/1996 art. 9 excludes "simple fapte și date" and official political/legislative/administrative texts from copyright (research line 248, confidence HIGH); Law 179/2022 art. 11 recommends CC BY 4.0 (confidence MEDIUM-HIGH); cdep's non-commercial notice attaches to creative assets, not facts (confidence MEDIUM-HIGH, no Romanian case law found). **Never copy cdep's layout/database arrangement, multimedia, `/declaratii/` content, home addresses, private emails, or family financial details** (research line 269).

### 3.6 Read-only runtime

Production API is read-only: `PARLAMENT_POLL_INTERVAL_MIN` empty, no background polling (DEPLOYMENT.md:15-19). The runtime filesystem is read-only (W4, digest line 49). Therefore every enrichment runs in the **data workflow before release**, on a copy, with atomic promotion — never at request time. Any proposal to compute/store new data in the running API is rejected by this contract.

### 3.7 Immutable releases

Release tags `data-${run_id}-${attempt}` are immutable. `data/latest-release.txt` is the only mutable pointer and is pinned with retry (W4, digest line 44). Never edit a published release or its 3 assets. Never re-point a release to different bytes; publish a new tag instead.

### 3.8 Strict audit

`audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json` must report **275 known errors, 0 new errors**. Baseline fingerprints use natural identity (check, severity, chamber, legislature, normalized person name, detail, context), not UUIDs (VERIFICATION.md:82-91). New checks from W5 must be registered in `CHECKS` (`pipeline/audit.py:973-984`) and their expected findings baselined in the same commit that introduces them. No "warnings hidden to get green" — warnings remain visible (VERIFICATION.md:45).

### 3.9 No attendance score

Report **presence at a vote** factually, with source and known gaps. Never invent an "attendance score", never rank MPs by presence, never publish a loyalty/attendance leaderboard number derived from vote presence (research line 300; W3 digest line 36). The existing leaderboard loyalty caveat must remain visible (`SwitchLeaderboard.tsx`) and must not be extended into a vote-based ranking.

---

## 4. Organisation of the work — FLEET CHARTER

Eight roles: one Master Supervisor and seven Workers (W1–W7). Every recipe below is reusable verbatim for the implementation waves. Each recipe contains: mission, exact inputs, exact files to read, prohibited assumptions, exact deliverables, decision rights, definition of done, escalation triggers, and the exact prompt/behaviour to use.

### 4.0 Master Supervisor (MS)

| Field | Content |
|---|---|
| **Mission** | Own wave sequencing, quality gates, retry budget (max 3 attempts per task then escalate), context handoff between workers, and the final production-readiness verdict. Never implement. |
| **Exact inputs** | This document; `/tmp/opencode/supervisor-input.md`; `docs/DATA-ENRICHMENT-RESEARCH.md`; `docs/DEPLOYMENT.md`; `docs/VERIFICATION.md`; each worker's deliverables at wave checkpoints. |
| **Files MS must read before any wave advance** | The four documents above, plus the specific `file:line` ranges cited in the wave being opened. If a cited line has moved, MS re-reads the surrounding code and records the new line in the checkpoint evidence before authorising work. |
| **Prohibited assumptions** | That a doc statement is true; that a worker's summary is evidence; that a passing local test equals a passing deploy; that branch protection required-check list is known (W4: UNVERIFIED). |
| **Deliverables** | Signed wave checkpoints (CP-Wx.y) with raw output; retry log; final integration verdict; maintained risk register (§9). |
| **Decision rights** | Advance/hold a wave; open a retry; escalate after 3 failures; veto any change violating §3; require W5 legal sign-off before ingest; require W4 release sign-off before promotion. MS cannot waive a non-negotiable. |
| **Definition of done** | Every AP in a wave has a PASS checkpoint with pasted evidence and a named rollback; all non-negotiables verifiably intact. |
| **Escalation triggers** | Same checkpoint FAILs 3×; legal licence conflict; CAPTCHA encountered; data loss risk (WAL); production proof contradicts local proof; any UNVERIFIED resolver itself fails. |
| **Exact prompt/behaviour** | ```text\nYou are the Master Supervisor. Do not edit product files. Before opening any wave, re-read the cited file:line ranges and the four control documents. Enforce: evidence over assertion; every action point has a checkpoint; every checkpoint has a rollback; max 3 attempts per task then escalate; no attendance score; no NC/SA values in the CC-BY release. At each gate paste raw command output + timestamp and state PASS/FAIL/NOT PROVEN. If a check cannot run, report NOT PROVEN. Do not advance on a worker's assertion.\n``` |

### 4.1 W1 — Backend / vote ingestion

| Field | Content |
|---|---|
| **Mission** | Add `vote` and `vote_position` as first-class, idempotent, provenance-carrying entities; wire cdep XML as strict primary and vot-parlament.ro as non-fatal secondary. |
| **Exact inputs** | Live cdep vote XML + nominal pages, vot-parlament per-vote JSON, fixtures, digest W1 (lines 5-16). |
| **Files to read (exact)** | `pipeline/db.py:62-86` (REASONS/EVIDENCE_TYPES/EVENT_TYPES), `:275-281` (Evidence NOT NULL), `:348-350` (insertion point after `Event`, before `SwitchWave` at :350), `:456-458` (`create_all`), `:489-531` (partial unique index pattern); `pipeline/fragments.py:46-80`; `pipeline/events.py:109-134, after :134`; `pipeline/identity.py:118-148`; `pipeline/ingest_corpus.py:192-209`; `pipeline/cli.py:after :697, :489-502, :826-831`. |
| **New files** | `pipeline/parse/cdep_votes.py`, `pipeline/ingest_votes.py`, `pipeline/sources/cdep_votes.py`, `pipeline/sources/vot_parlament.py`, `tests/test_votes.py`, fixtures `tests/fixtures/cdep_votes_YYYYMMDD.xml`, `cdp_vote_nominal_IDV.html`, `vot_parlament_vote_ID.json`. |
| **Prohibited assumptions** | That `par1` means a given chamber, that `CAMERA` code values are known, that `idv == VOTID`, that exact XML element/attribute form is known — all four are `[UNVERIFIED]` and resolved by capturing fixtures FIRST (digest line 13). Never call `PersonResolver.resolve()`; never attach vote evidence via `Evidence`; never fabricate an unknown person. |
| **Deliverables** | Models `Vote`, `VotePosition` per digest line 7; edits at db.py:72, :73-86, :62-71, :489-531; `derive_vote_events()` dedup `vote:{source}:{external_id...}` with `person_id NULL`, confidence `official_ledger` (cdep) / `community` (third-party); `--skip-votes`; counts in `cmd_stats`; 11 named tests in `tests/test_votes.py` (digest line 14). |
| **Decision rights** | Choose parser field mapping **only after** fixture capture; choose `confidence` value per source class. Cannot change identity rules, cannot touch `data.yml`, cannot promote a release. |
| **Definition of done** | All 11 tests pass; strict gate fails if cdep votes empty; vot-parlament unreachable keeps strict green; audit flags vote without source; idempotency proven by duplicate ingest. |
| **Escalation triggers** | Fixture disagrees with assumed field meaning; unknown-MP rate > agreed threshold; cdep strict gate fails; any person created by resolution path. |
| **Exact prompt** | ```text\nYou are W1 (vote ingestion). Read pipeline/db.py:62-86,275-281,348-350,456-458,489-531; fragments.py:46-80; events.py:109-134; identity.py:118-148; ingest_corpus.py:192-209; cli.py:697,489-502,826-831. FIRST capture fixtures for cdep XML, nominal HTML and vot-parlament JSON; do not assume par1/CAMERA/idv semantics. Insert Vote and VotePosition after db.py:348. Use lookup-only PersonIdentifier; never call PersonResolver.resolve(); never use Evidence for votes (membership_id NOT NULL). Write 11 TDD tests, including unknown MP not fabricated and strict-fails-on-empty-cdep. Report raw pytest/ruff output; do not touch data.yml or releases.\n``` |

### 4.2 W2 — Frontend / UX

| Field | Content |
|---|---|
| **Mission** | Fix the 16 verified UI defects, then add vote/bio/ideology/election/benchmark surfaces with honest denominators and full accessibility. |
| **Exact inputs** | Digest W2 (lines 17-31); live browser snapshot (16 nav links, home sections); design tokens and i18n dictionaries. |
| **Files to read (exact)** | `frontend/src/router.tsx:303-480`; `LiveDashboard.tsx:97-141,196`; `DashboardCard.tsx:76-95,97-108`; `InfoStat.tsx:48-82`; `CommitteeControl.tsx:122-125`; `DataQualityGauge.tsx:37-53,108,134`; `Mps.tsx:82-106,395`; `Committees.tsx:239-243`; `Demographics.tsx:44-57`; `PartyComparison.tsx:46,51`; `CrossChamberFlow.tsx:24-27,55-80`; `AgeDistributionRadial.tsx:113,125`; `InstitutionalView.tsx:71-74`; `Traseism.tsx:134-164,845-866` (reference pattern); `ui/DashboardHeader.tsx:15`; `index.css:5-45,51-72,76-89,139-169,198-201,203-227`; `tailwind.config.js:8-28`; `api/client.ts`; `frontend/src/i18n/*`. |
| **Prohibited assumptions** | That a number without a denominator is self-explanatory; that a div with `role=button` is a button; that placeholders are data; that a major-version framework upgrade is in scope (it is not — see §6.5); that site-wide design changes are free. |
| **Deliverables** | 16 defect fixes; new components and routes per §6; ro/en i18n keys for every added string; `aria-sort` on tables; text alternatives for SVG charts; theme toggle mounted site-wide; quick-win PR split from wave-coupled PRs. |
| **Decision rights** | Choose component composition and copy. Cannot invent statistics (W3 owns definitions), cannot change API semantics without W3, cannot bypass `modern-web-guidance`/`impeccable` gates. |
| **Definition of done** | Browser proof with screenshots at target viewport; WCAG AA contrast; `type="button"`; no deprecated `onKeyPress`; no `window.location.href` that drops `asOf`; build green; every number shows scope/denominator. |
| **Escalation triggers** | A required statistic has no endpoint yet; a fix requires a schema change; design-system token ambiguity; a11y defect that cannot be fixed without replacing a library component. |
| **Exact prompt** | ```text\nYou are W2 (frontend/UX). First run modern-web-guidance guidance for any HTML/CSS/JS change. Read the exact file:line list in the Fleet Charter and the 16 defects in §6.3. Fix defects with evidence: paste before/after screenshots and the browser URL. Every displayed statistic must state scope and denominator; reuse Traseism.tsx:134-164,845-866 as the reference pattern. Use type="button", WCAG AA contrast, text alternatives for SVG, aria-sort on sortable tables, and ro/en keys for every new string. Do not invent statistics and do not upgrade framework majors.\n``` |

### 4.3 W3 — Statistics / API

| Field | Content |
|---|---|
| **Mission** | Define and expose trustworthy statistics with explicit denominators, uncertainty, missing-data disclosure, and REST/GraphQL convergence. |
| **Exact inputs** | Digest W3 (lines 32-41); existing formulas A3/A6/A7/A9/A10/T2/T8 and leaderboard loyalty; full W3 output at `/home/nedaktov/.local/share/opencode/tool-output/tool_1f82ef456001LYaPL5Eu9d0R6Y`. |
| **Files to read (exact)** | `pipeline/queries.py:1-5,38-42` (half-open time semantics); `backend/routers/api.py:772-773` (scope regexes), `:985-995` (dashboard stats), `:990` (inclusive `>=`), `:999-1005` (switches all-time); `backend/graphql/schema.py`; `pipeline/export.py:352`; `backend/routers/exports.py:190-203`; `/export/report:139-159`; `tests/test_analytics.py`, `tests/test_api.py`, `tests/test_graphql_convergence.py`. |
| **Prohibited assumptions** | That REST and GraphQL already agree (they do not — digest line 34); that `date.today()` is UTC (it is server-local; only `computed_at`/`generated_at` are aware UTC); that "unavailable" and `[]` are equivalent (they are not); that a mean-of-means is a weighted mean. |
| **Deliverables** | Six endpoint contracts per §7.4; convergence fixes (party_cohesion status envelope, median algorithm); truthful `status/scope/data` payload with all trust fields; 4 behaviour-documenting tests + 22 new tests in `tests/test_new_statistics.py` and `tests/test_statistics_contract.py`; export branch in `pipeline/export.py:352` (adding names to `CSV_DATASETS` alone derives empty columns from Popolo), route beside `backend/routers/exports.py:190-203`, blocks in `/export/report:139-159`. |
| **Decision rights** | Own statistical definitions, denominators, CI method, minimum-sample thresholds. Cannot change source data or UI presentation without coordinating with W1/W2/W6. |
| **Definition of done** | Every endpoint returns `status`, `scope`, `sample_size + unit`, `denominator`, `missing_data_count`, `precision/CI`, `source_link`, `benchmark_provenance`, `license_flag`, `as_of`/`computed_at`, `no-store`; REST and GraphQL outputs byte-comparable for the same query; no attendance score anywhere. |
| **Escalation triggers** | Denominator cannot be defined from available columns (e.g. `mandate.constituency` 100% NULL → electoral-base endpoint must return `status: unavailable` with reason until Wave 5); sample below `min_votes` default 20; licence flag unresolved. |
| **Exact prompt** | ```text\nYou are W3 (statistics/API). Read pipeline/queries.py:1-5,38-42; api.py:772-773,985-995,990,999-1005; graphql/schema.py; export.py:352; exports.py:190-203; export/report:139-159. Fix REST/GraphQL divergence first: party_cohesion must return the same unavailable status envelope, and median_age must use statistics.median in both. Define every new statistic with denominator, unit, missing count, Wilson/Welch CI where applicable, min_votes=20 default, and no-store caching. No attendance score or ranking. Add 22 contract tests plus the 4 behaviour tests. Paste raw test output.\n``` |

### 4.4 W4 — Release / rollback

| Field | Content |
|---|---|
| **Mission** | Own every promotion to `main`, every release tag, every deploy verification, and every rollback. |
| **Exact inputs** | Digest W4 (lines 42-51); `docs/DEPLOYMENT.md` in full; CI/data workflow definitions. |
| **Files to read (exact)** | `.github/workflows/ci.yml:17,42,63,89`; data workflow (cron 03:17 UTC, strict collect, audit, prepare, tag, release, pin, Render trigger, poll); `.github/workflows/deploy-verify.yml`; `.github/workflows/platform-rollback.yml:145`; `vercel.json:6,14-15`; `backend/cache.py:28`; `db.py:447`; `prepare_db.py:170-177`; `scripts/deploy-all.sh:21`; `scripts/verify-deploy.sh`; `scripts/check-deployment-status.sh`. |
| **Prohibited assumptions** | That branch protection required-check list is known (UNVERIFIED — resolve with `gh api repos/nedaktov-ops/parlament-deschis/branches/main/protection` or by reading the dashboard; until then, do not claim it); that a marker push with `GITHUB_TOKEN` triggers CI (it does not — DEPLOYMENT.md:56-58); that Render rollback disables auto-deploy (it does not — DEPLOYMENT.md:164-167); that `deploy-all.sh` is safe (hardcoded wave commit message + `git add -A` at line 21 — do not use for promotion). |
| **Deliverables** | Wave gate ladder (source/legal → parser+fixture+unit → staging copy dry-run/apply/idempotency → audit error check → promotion to data.yml + release + deploy verify); fixed known gaps A-1 (dead Vercel tolerance), A-2 (`npm run lint` not a CI gate), A-3 (footgun script), A-5 (marker push [UNVERIFIED]); rollback ladder with explicit irreversible list. |
| **Decision rights** | Sole owner of `data/latest-release.txt`, release tags, workflow edits, and platform rollbacks. Can halt any promotion. |
| **Definition of done** | `verify-deploy.sh` passes with asserted SHA and release tag; rollback dry-run printed before any confirm; no `git add -A` on a dirty tree; WAL checkpoint performed before any DB copy. |
| **Escalation triggers** | Render deploy missing for commit; release marker push blocked; Vercel deploy absent (dead tolerance must not paper over it); third-party outage during data workflow; licence-contaminated data in staging. |
| **Exact prompt** | ```text\nYou are W4 (release/rollback). Do not use scripts/deploy-all.sh for promotion. Never git add -A on a dirty tree. Before any DB backup, checkpoint WAL (working DB journal_mode=WAL at db.py:447; shipped DB DELETE at prepare_db.py:170-177). Prove rollback target with platform-rollback.yml dry_run=true before confirm=ROLLBACK. Add npm run lint as a CI gate and remove the dead 180s Vercel tolerance; do not claim branch protection required checks without reading them. Paste raw verify-deploy output and the asserted SHA/tag.\n``` |

### 4.5 W5 — Governance / audit

| Field | Content |
|---|---|
| **Mission** | Guard R1–R12, legal gates, licence flags, audit registration, and documentation truth. Holder of the legal veto. |
| **Exact inputs** | Digest W5 (lines 52-58); `DATA-ENRICHMENT-RESEARCH.md` §4-§5; acceptance standard R1–R12. |
| **Files to read (exact)** | `pipeline/audit.py:973-984` (`CHECKS`), `:375-407` (insert check_vote_evidence after), `:410-453` (check_biography_provenance after; `:410-414` docstring/body mismatch), `before :830` (check_benchmark_license), after benchmark (check_election_result), `:812` (329 seats); `data/licenses/README.md:105-106`; `docs/RESEARCH.md`; `docs/METHODOLOGY.md:501`; `docs/AUDIT.md:121,134`; `docs/DATA-COMPLETENESS-RECOVERY.md:3`; `db.py:505`; `frontend/src/.../About.tsx:263-298`. |
| **Prohibited assumptions** | That a source's own licence footer governs facts (Law 8/1996 art. 9 prevails for facts — research line 248); that a ShareAlike value can be copied into CC-BY; that warnings may be hidden; that `EVIDENCE_TYPES` being defined means it is used (it is not). |
| **Deliverables** | Four new audit checks registered in `CHECKS`; "no `attendance_score` column/endpoint" assertion; `license_flag` export_ok gate; seat sums vs mandates; 2-hop provenance for vot-parlament; sign-off per §4.5; 11 doc contradictions A–K resolved; `docs/DATA-ENRICHMENT-RESEARCH.md` committed; `About.tsx` note exposed. |
| **Decision rights** | **Veto** on any source ingest until licence class is recorded. Cannot be overridden by MS or W4. |
| **Definition of done** | Strict audit green with new checks baselined; zero NC/SA values in exportable tables; every new row's provenance traceable to a `Fragment`; docs contradictions closed. |
| **Escalation triggers** | Any NC/SA/UNKNOWN licence; CAPTCHA encountered; `/declaratii/` requested; personal data in scope; unresolved identity conflict. |
| **Exact prompt** | ```text\nYou are W5 (governance/audit). Hold the licence veto: COPY vs XCHECK vs COND must be decided before any ingest. Register new checks in pipeline/audit.py CHECKS at :973-984: check_vote_evidence after :375-407, check_biography_provenance after :410-453, check_benchmark_license before :830, check_election_result after benchmark. Assert no attendance_score column/endpoint and license_flag export_ok gating. Fix the 11 documentation contradictions, expose About.tsx:263-298 coverage notes, and commit docs/DATA-ENRICHMENT-RESEARCH.md. Never hide warnings.\n``` |

### 4.6 W6 — Enrichment ingestion

| Field | Content |
|---|---|
| **Mission** | Ingest biographies, identifiers and external covariates with provenance, on a copied DB, dry-run first, non-fatally. |
| **Exact inputs** | Digest W6 (lines 59-69); research §3.1, §3.6, §6 Phases 2-3, §7. |
| **Files to read (exact)** | `pipeline/enrich.py:368-372` (hardcoded default DB via `get_session()`); `pipeline/cli.py:260-272` (`cmd_enrich` ignores `args.db`), `:763-772` (parser defaults `dry_run=False`); `pipeline/db.py:after Person(:104)`; `.github/workflows/data.yml:81,83` (between audit and prepare); `pipeline/identity.py`; `pipeline/sources/client.py`. |
| **Prohibited assumptions** | That `--apply` is the parser default (module default is dry-run; CLI parser is apply-by-default — fix both); that `args.db` is honoured (it is not); that a name match is enough; that DOB `21.01.1991` on the 1990 page is valid (it is a future-date anomaly — reject); that `mandate.constituency` can be joined (100% NULL); that IPU XLSX columns are known ([UNVERIFIED]); that AEP internal columns are known ([UNVERIFIED]); that Wikidata bulk `/sparql` is allowed (robots disallows it — use cached/dump flows). |
| **Deliverables** | New models `PersonAttribute`, `OrgIdentifier`, `PartyScore`, `ElectionResult`, `Benchmark` after `db.py:104`; new parse/sources modules and `enrich-birth-dates` CLI; `structura2015.de?leg=YYYY&par=V01..12&cam=1|2` ingest; GLD via Dataverse persistentId `doi:10.7910/DVN/U1ZNVT`, dataFile `10595375` (8,991,183 bytes, 30 vars), codebook `10595363`, CC0, 329 RO 2016 rows; Party Facts alias map; data.yml wiring at :81–:83; TDD per source; no `test_enrich*.py` exists today — create it. |
| **Decision rights** | Choose source order and confidence per source. Cannot change `Evidence.membership_id` NOT NULL, cannot modify `organization.short_name`/genealogy, cannot create persons. |
| **Definition of done** | 275/275 addressable keys checked (268 `cdep_mandate`, 7 `cdep_idm`; 196 senate-only, 72 deputies); expected filled 200–268 (central ~240) with MEDIUM confidence, [INFERRED] from coverage analysis — reported as estimate, not claim; conflicts stored `status='conflict'`; existing `birth_date` wins; dry-run then apply on copy; cache saved even on failure. |
| **Escalation triggers** | Coverage below ~200 filled; `cam=2` only ≤72 reachable; GLD ≤2 of 275; Wikidata 50–150 LOW confidence; residual ~7–35; any name-only merge; licence COND without permission. |
| **Exact prompt** | ```text\nYou are W6 (enrichment ingestion). Fix enrich.py:368-372 and cli.py:260-272,763-772 first: honour args.db and make dry-run the CLI default. Never alter Evidence.membership_id NOT NULL; person_attribute is the evidence carrier. Use exact identifier match only (cdep_mandate deputies:{leg}:{idm} / senate:{leg}:{idm}, fallback cdp_idm+leg). Existing birth_date wins; reject the 21.01.1991 future-date anomaly; store conflicts as status='conflict'. Use sqlite backup API not raw cp (WAL). Wire into data.yml between audit(:81) and prepare(:83) with separate cache and continue-on-error. Never create persons, never touch organization.short_name/genealogy.\n``` |

### 4.7 W7 — NedCode4 tooling / verification operator

| Field | Content |
|---|---|
| **Mission** | Schedule the correct NedCode4 skills/MCPs at each checkpoint and enforce the repo-scope boundary. |
| **Exact inputs** | Digest W7 (lines 71-78); live MCP catalog; NedCode4 skill inventory. |
| **Files to read (exact)** | `/home/nedaktov/Desktop/NedCode4/AGENTS.md` (generated block, `just docs`, `just verify`), `justfile`, `scripts/docs/facts.py`, product `AGENTS.md`. |
| **Prohibited assumptions** | That NedCode4 commands work in the product repo (they do not — no justfile there); that MCP tools are available to workers (the visible catalog has chrome-devtools, shadcn, opencode only; subagent/task is parent-only); that a stale docs-check is harmless (exit 3 today). |
| **Deliverables** | Skill/MCP schedule per §8; `just docs` regeneration discipline (never hand-edit GENERATED blocks; stage explicit paths, never `git add -A`); C0–C9 checkpoint evidence; reconciliation of tool counts. |
| **Decision rights** | Own tooling scheduling and proof artifacts. Cannot approve product correctness (that is W1–W6 + MS). |
| **Definition of done** | Each checkpoint has the named skill/MCP invoked with pasted output; repo scope stated in every command block. |
| **Escalation triggers** | `just docs-check` still stale; MCP unavailable at checkpoint; gap between W7's counted 31 chrome-devtools tools and the master session's visible catalog of 33 — [UNVERIFIED] reconciliation, resolve by re-running tool discovery at execution time, not by assuming either number. |
| **Exact prompt** | ```text\nYou are W7 (NedCode4 tooling). Repo scope first: just doctor/verify/docs/secrets-scan/verify-project/ship run ONLY in /home/nedaktov/Desktop/NedCode4; product commands (uv run pytest, ruff, npm build, project workflows) run ONLY in /home/nedaktov/parlament-deschis. Never hand-edit GENERATED blocks; regenerate with just docs and stage explicit paths. At each checkpoint invoke the scheduled skill/MCP and paste raw output. A check that cannot run is NOT PROVEN.\n``` |

### 4.8 Fleet interaction rules

1. **No worker edits CI or `data.yml` without W4 + MS sign-off.**
2. **No ingest starts without W5 licence class recorded.**
3. **No statistic is exposed by W3 until its source table exists and W1/W6 confirm provenance.**
4. **No UI displays a number until W3 defines its denominator.**
5. **MS advances waves only on signed checkpoints, never on chat assertions.**
6. Worker output must always include raw command output and the exact files/lines touched.

---

## 5. WAVES

Conventions used throughout: **AP** = action point (2–5 minutes of code work where code is involved), each annotated with its checkpoint; **CP** = checkpoint with explicit pass/fail evidence and rollback; **P0–P4** = phase ladder (P0 fixture/legal gate, P1 schema+parser, P2 ingest+dry-run, P3 API+UI, P4 audit+release). Every CP lists **Irreversible** items — things the rollback cannot undo.

---

### WAVE 0 — Truth, documentation and CI hardening

**Goal.** Make the repository tell the truth about itself and make the gates trustworthy before any new data is added.  
**Value/effort.** Highest value ÷ effort in the whole plan: half a day, almost zero data risk (research Phase 0, lines 277-283). Without it, every later wave is judged against stale claims.

**Affected files with exact ranges (from digest):** `docs/RESEARCH.md` (robots facts, research lines 100-102, 237); `docs/DATA-COMPLETENESS-RECOVERY.md:3`; `db.py:505`; `docs/METHODOLOGY.md:501`; `docs/AUDIT.md:121,134`; `pipeline/audit.py:410-414,812,973-984`; `data/licenses/README.md:105-106`; `About.tsx:263-298`; `frontend/src/router.tsx:303-480`; `vercel.json:6`; `scripts/deploy-all.sh:21`; `.github/workflows/ci.yml:17,42,63,89`; `docs/DATA-ENRICHMENT-RESEARCH.md` (untracked); `pipeline/db.py:72` (identifier scheme values only — no schema migration).

#### Phase P0 — Fixture / legal gate

- **AP-0.1** Confirm baseline: `uv run python -c "import sqlite3; c=sqlite3.connect('data/parlament-real.db'); print({t:c.execute('select count(*) from '+t).fetchone()[0] for t in ['person','mandate','membership','event','organization']})"`. Expect `person 3388, mandate 5273, membership 7349, event 7429, organization 120`. → **CP-0.1**
- **AP-0.2** Confirm git state: `git rev-parse --short HEAD` → `2995bfd`; `git status --porcelain` → expect `?? docs/DATA-ENRICHMENT-RESEARCH.md`. → **CP-0.1**
- **AP-0.3** W5 legal gate: record licence classes from research §5 for all planned sources (COPY / XCHECK / COND) in a tracked governance note; no ingest authority granted yet. → **CP-0.2**

#### Phase P1 — Schema + parser (documentation schema only)

- **AP-0.4** Add pointer note at top of `docs/RESEARCH.md`: superseded parts marked historical, pointing to `DATA-ENRICHMENT-RESEARCH.md` (research line 279). → **CP-0.3**
- **AP-0.5** Fix D1–D8, D13, D14 from §2.3 in one documentation commit; include `git add docs/DATA-ENRICHMENT-RESEARCH.md` explicitly (never `git add -A`). → **CP-0.3**
- **AP-0.6** Extend coverage semantics: `/api/coverage/detailed` must distinguish `mandates: full`, `votes: none`, `biographies: partial`, `committee history: partial` (research line 280); add identifier scheme values `wikidata, senat_guid, gld, ep, partyfacts` as data values only (research line 281 — no migration). → **CP-0.4**
- **AP-0.7** Expose `About.tsx:263-298` coverage `row.note` instead of hiding it (W5). → **CP-0.4**

#### Phase P2 — Ingest + dry-run (CI hardening, no new data)

- **AP-0.8** Add `npm run lint` as a CI gate (W4 anomaly A-2); remove dead 180 s Vercel tolerance in `verify-deploy.sh` and assert the deploy exists instead (A-1, `vercel.json:6` `ignoreCommand:""`). → **CP-0.5**
- **AP-0.9** Quarantine `scripts/deploy-all.sh:21` (footgun: hardcoded wave commit + `git add -A`); add a header comment forbidding promotion use and a guard that refuses a dirty tree. → **CP-0.5**
- **AP-0.10** Resolve branch-protection required-check list: `gh api repos/nedaktov-ops/parlament-deschis/branches/main/protection` or dashboard read; record as VERIFIED or stay UNVERIFIED with named resolver. → **CP-0.6**

#### Phase P3 — API + UI (quick-win fixes only)

- **AP-0.11** Fix dashboard definition collision: `api.py:985-995` active-membership count must be labelled `active_memberships_as_of`, `api.py:999-1005` switches must carry `as_of`/`all_time` in the field name; align with half-open `pipeline/queries.py:38-42`. → **CP-0.7**
- **AP-0.12** Fix UI quick wins 1–13 from §6.3 that do not need new endpoints (hero cards, edges, CrossChamberFlow, DataQualityGauge, AgeDistributionRadial, InstitutionalView, Mps total, Committees label, Demographics weighting, CommitteeControl, PartyComparison, SenateHistory, PartyTimeline). → **CP-0.7**

#### Phase P4 — Audit + release

- **AP-0.13** Run strict audit: `uv run python -m pipeline.cli --db data/parlament-real.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json --json data/verification-report.json` → expect `275 known errors, 0 new errors`, exit 0. → **CP-0.8**
- **AP-0.14** Run full local gate (DEPLOYMENT.md:130-139): `uv sync --extra dev --locked`; `uv run ruff check pipeline backend scripts tests`; `uv run pytest -q`; `(cd frontend && npm ci && npm run build)`; then `gh workflow run deploy-verify.yml -R nedaktov-ops/parlament-deschis --ref main`. → **CP-0.8**

##### Checkpoints — Wave 0

**CP-0.1 Baseline truth.** Pass: all five counts match digest line 3 exactly; HEAD `2995bfd`; research doc untracked. Fail: any count differs → stop, re-measure with `.venv/bin/python` variant, escalate to MS. **Rollback:** none needed (read-only commands). **Irreversible:** nothing.

**CP-0.2 Legal gate recorded.** Pass: written COPY/XCHECK/COND table exists in a tracked file; W5 signature. Fail: any source unclassified → that source stays out of scope. **Rollback:** revert the governance note commit (`git revert <sha>`). **Irreversible:** the fact that a licence decision was once recorded — correction requires a new commit, never an edit of the record.

**CP-0.3 Docs truth.** Pass: all D-items 1–8, 13, 14 closed; `grep -n "No roll-call" docs/METHODOLOGY.md` → no hit; `git status --porcelain` shows research doc tracked. Fail: stale string remains → fix before continuing. **Rollback:** `git revert <doc-commit>`. **Irreversible:** published docs on the live site until next deploy — but docs are in the SPA bundle, so a bad doc commit is visible after Vercel deploy.

**CP-0.4 Coverage honesty.** Pass: `/api/coverage/detailed` output shows `votes: none`, `biographies: partial`; About note visible in browser screenshot. Fail: "full for all 20 scopes" still implied → block. **Rollback:** `git revert <sha>` + platform rollback of the Vercel deploy. **Irreversible:** users may have read the misleading coverage page during the exposure window.

**CP-0.5 CI hardening.** Pass: CI run shows lint job green and no 180 s Vercel tolerance string in `verify-deploy.sh`; `grep -n "git add -A" scripts/deploy-all.sh` returns no ungated occurrence. Fail: gate absent. **Rollback:** revert workflow commit; re-run CI. **Irreversible:** CI runs already recorded in GitHub history.

**CP-0.6 Branch protection fact.** Pass: required-check list captured with command output, or explicitly recorded as UNVERIFIED with resolver command. Fail: unverifiable and claimed → strike the claim. **Rollback:** documentation revert. **Irreversible:** none.

**CP-0.7 Definition collision fixed.** Pass: API response shows `active_memberships_as_of` = 4,461 for 2026-11-20 and switches labelled all-time = 2,002; browser screenshot shows labels; no unlabelled number. Fail: any old field name remains in client. **Rollback:** revert UI/API commit + redeploy; data unchanged. **Irreversible:** cached API responses for up to 300 s (`backend/cache.py:28`).

**CP-0.8 Full gate.** Pass: ruff exit 0; pytest all green; npm build exit 0; audit `275 known errors, 0 new errors`; deploy-verify asserts SHA/tag. Fail: any non-zero → no promotion. **Rollback:** revert commit; if deployed, `platform-rollback.yml` dry-run then `confirm=ROLLBACK`. **Irreversible:** published Vercel/Render deployment history; immutable browser bundle cache (`vercel.json:14-15`, 1 year).

---

### WAVE 1 — Votes (the 10× move)

**Goal.** Roll-call votes become first-class dated events with per-MP positions, official provenance and idempotent ingest.  
**Value/effort.** 2–4 weeks (research Phase 1, lines 285-302), highest analytical value. Powers cohesion, voting record, presence-at-vote context, event citations.

**Affected files with exact ranges (digest W1):** `pipeline/db.py:62-71, after 348, 350, 456-458, 489-531`; `pipeline/fragments.py:46-80`; `pipeline/events.py:109-134, after 134`; `pipeline/identity.py:118-148`; `pipeline/ingest_corpus.py:192-209`; `pipeline/cli.py:after 697, 489-502, 826-831`; new files as listed in §4.1.

#### Phase P0 — Fixture / legal gate

- **AP-1.1** Capture raw cdep day XML (`evot2015.xml?par1=1&par2=YYYYMMDD`), one nominal HTML (`evot2015.nominal?idv=VOTID&idl=1`) and one vot-parlament JSON (`/votes/{id}.json`) into `tests/fixtures/` via `PoliteClient` only; record the exact response bytes and HTTP headers. → **CP-1.1**
- **AP-1.2** Resolve the four `[UNVERIFIED]` field facts from digest line 13: meaning of `par1`, `CAMERA` code values, exact element/attribute form, whether `idv == VOTID`. Evidence = the captured fixture plus a one-page note mapping each field. → **CP-1.1**
- **AP-1.3** W5 confirms cdep facts COPY and vot-parlament CC BY COPY; vot-parlament 2-hop provenance rule registered. → **CP-1.2**

#### Phase P1 — Schema + parser

- **AP-1.4** Insert `Vote` and `VotePosition` models in `pipeline/db.py` after line 348 (after `Event`, before `SwitchWave` at :350); exact columns per digest line 7, including `dedup_key UNIQUE`, `Index(ix_vote_scope_date)`, `Index(ix_vote_position_person_choice)`. No new imports. → **CP-1.3**
- **AP-1.5** Supporting enum/index edits: `db.py:72` add `vote` to `EVIDENCE_TYPES`; `:73-86` add `vote` to `EVENT_TYPES`; `:62-71` add `VOTE` to `REASONS`; `:489-531` add partial unique `ux_vote_position_unresolved`; no `_ADDED_COLUMNS` change; `create_all` at `:456-458` creates tables. → **CP-1.3**
- **AP-1.6** Write `pipeline/parse/cdep_votes.py` and `pipeline/sources/cdep_votes.py` against the captured fixture only; raw content via `record_fragment` (`fragments.py:46-80`), checksum into `snapshot_hash`, model names `vote_day_xml / vote_nominal / vote_json / vote_csv`. → **CP-1.4**
- **AP-1.7** Write `pipeline/sources/vot_parlament.py` with non-fatal `DATA_UNAVAILABLE` behaviour. → **CP-1.4**

#### Phase P2 — Ingest + dry-run

- **AP-1.8** Person resolution: lookup-only via `PersonIdentifier(scheme='cdep_mandate', identifier=f'deputies:{leg}:{idm}')` (`ingest_corpus.py:192-209`), fallback `cdep_idm`; never `PersonResolver.resolve()`; unknown → `person_id NULL` + verbatim `member_name` + audit warning. → **CP-1.5**
- **AP-1.9** Add `derive_vote_events(session)` in `pipeline/events.py` after :134 reusing `_upsert_event` (:109-134); dedup `vote:{source}:{external_id...}`, `person_id NULL`, confidence `official_ledger` (cdep) / `community` (third-party). → **CP-1.5**
- **AP-1.10** Wire ingestion in `cli.py` after :697 inside `cmd_build_corpus`; cdep strict-gated, vot-parlament non-fatal; add `--skip-votes` near :826-831; add counts to `cmd_stats` :489-502. → **CP-1.6**
- **AP-1.11** Write 11 named tests in `tests/test_votes.py` per digest line 14; run `uv run pytest -q tests/test_votes.py`. → **CP-1.7**
- **AP-1.12** Dry-run on a **copy**: `uv run python -c "import sqlite3; s=sqlite3.connect('data/parlament-real.db'); d=sqlite3.connect('data/votes-dryrun.db'); s.backup(d); d.close(); s.close()"` (WAL-safe backup, not `cp`), then run vote ingest `--dry-run`. → **CP-1.8**

#### Phase P3 — API + UI

- **AP-1.13** W3 exposes `/analytics/vote-cohesion`, `/analytics/voting-record`, `/analytics/presence-at-vote`, `/person/{id}/votes`, `/votes` with filters, using §7.4 envelope. → **CP-1.9**
- **AP-1.14** W2 adds `/votes`, `/vote/$id` routes and `VoteExplorer / VoteTable / VoteDetail / VotePositionStrip / PartyCohesionChart / VoteCoverageBanner` per §6.2, with "presence at a vote" wording only — no attendance score. → **CP-1.10**

#### Phase P4 — Audit + release

- **AP-1.15** W5 registers `check_vote_evidence` in `CHECKS` (`audit.py:973-984`, insert after :375-407): every vote has `source_url` + fragment checksum; every position resolves or is explicitly unresolved; no `attendance_score` column/endpoint. → **CP-1.11**
- **AP-1.16** Strict audit + full local gate; verify strict still `275 known errors, 0 new errors` (new findings baselined only if approved). → **CP-1.12**
- **AP-1.17** W4 promotion: data.yml call, immutable tag, release, pin with retry, explicit Render deploy, poll served tag ≤30 min, deploy-verify. → **CP-1.13**

##### Checkpoints — Wave 1

**CP-1.1 Fixture/field facts.** Pass: three fixtures saved with checksums; all four field facts evidenced in writing. Fail: fact still assumed → do not write parser. **Rollback:** delete fixture files (untracked) and re-fetch. **Irreversible:** the fetched pages exist in cache; no external state changed.

**CP-1.2 Legal gate.** Pass: W5 signature on cdep/vot-parlament classes; XCHECK not ingested. Fail: block ingest. **Rollback:** revert governance commit. **Irreversible:** legal decision record persists.

**CP-1.3 Schema.** Pass: `create_all` produces both tables and all indexes; `sqlite_master` query lists `ux_vote_position_unresolved`, `ix_vote_scope_date`, `ix_vote_position_person_choice`. Fail: missing index → fix before ingest. **Rollback:** drop the two new tables on the **copy** (`DROP TABLE vote_position; DROP TABLE vote;`) — never on shipped DB; on shipped DB revert code and restore prior DB snapshot. **Irreversible:** none if done on copy.

**CP-1.4 Parser.** Pass: 11/11 fixture-based parse assertions; field mapping note matches fixture. Fail: mismatch → return to CP-1.1. **Rollback:** revert parser files. **Irreversible:** none.

**CP-1.5 Resolution/events.** Pass: known MP resolves to existing `person_id`; unknown MP produces NULL + `member_name` + warning; zero new persons created (compare person count before/after = 3,388). Fail: any person created → block. **Rollback:** restore DB copy from pre-ingest backup. **Irreversible:** if run on shipped DB, fabricated persons would already be published — hence copy-only rule.

**CP-1.6 Wiring.** Pass: `build-corpus --strict` with cdep votes succeeds; with cdep votes empty it **fails**; vot-parlament unreachable logs `DATA_UNAVAILABLE` and strict stays green; `--skip-votes` bypasses. Fail: any inversion → block. **Rollback:** revert cli.py changes. **Irreversible:** none.

**CP-1.7 Tests.** Pass: 11 named tests green with raw pytest output. Fail: any red → max 3 retries then escalate. **Rollback:** revert test/parser commit. **Irreversible:** none.

**CP-1.8 Dry-run idempotency.** Pass: run twice on `data/votes-dryrun.db`, row counts identical; `SELECT count(*) FROM vote WHERE dedup_key IS NULL` = 0. Fail: duplicates → fix dedup. **Rollback:** delete `data/votes-dryrun.db` (not tracked). **Irreversible:** none.

**CP-1.9 API contract.** Pass: all five endpoints return full §7.4 envelope; cohesion uses votes-cast denominator with Wilson CI; min_votes 20; presence has mandatory caveat text; 0 occurrences of `attendance_score`. Fail: missing field → block. **Rollback:** revert API commit. **Irreversible:** 300 s cache residue (`backend/cache.py:28`).

**CP-1.10 UI.** Pass: browser screenshots of `/votes` and `/vote/$id`; vote table has `aria-sort`; no "attendance" ranking; i18n ro/en keys present. Fail: fix before merge. **Rollback:** revert UI commit + Vercel rollback. **Irreversible:** immutable bundle cache for 1 year (`vercel.json:14-15`).

**CP-1.11 Audit.** Pass: `check_vote_evidence` registered and green; strict output `275 known errors, 0 new errors`; no new error findings. Fail: block release. **Rollback:** revert audit commit. **Irreversible:** baseline file changes require review.

**CP-1.12 Full gate.** Pass: same as CP-0.8 plus vote counts in `cmd_stats`. Fail: any non-zero. **Rollback:** as CP-0.8. **Irreversible:** as CP-0.8.

**CP-1.13 Production proof.** Pass: `verify-deploy.sh` asserts HEAD SHA and new release tag; `/api/health` shows new vote counts; `Deploy verify` green. Fail: rollback. **Rollback ladder:** (1) pin revert `data/latest-release.txt` + explicit Render API trigger (fastest, data-only); (2) `platform-rollback.yml` dry-run then `confirm=ROLLBACK` for Render and Vercel; (3) git revert of code; (4) full physical DB restore from pre-upload snapshot (WAL checkpoint first). **Cannot roll back:** published GH releases/assets, immutable browser bundles, Render auto-deploy race (`platform-rollback.yml:145`), Vercel Hobby previous-deployment-only, 300 s in-process cache, read-only runtime FS, third-party outages.

---

### WAVE 2 — Biographies

**Goal.** Fill the 275 missing birth dates with exact-match official sources, add education/occupation/birthplace as attributed attributes, wire Wikidata enrichment into the daily workflow.  
**Value/effort.** 1–2 weeks, high value, low risk (research Phase 2, lines 304-318).

**Affected files (digest W6):** `pipeline/enrich.py:368-372`; `cli.py:260-272,763-772`; `db.py:after Person(:104)`; `data.yml:81,83`; `pipeline/identity.py`; new `pipeline/parse/enrich_birth_dates.py`, `pipeline/sources/*`, `tests/test_enrich*.py`.

#### P0

- **AP-2.1** Fix the three known CLI/DB bugs first: `enrich.py:368-372` hardcoded DB, `cli.py:260-272` ignores `args.db`, `cli.py:763-772` apply-by-default. Make dry-run the CLI default and honour `args.db`. → **CP-2.1**
- **AP-2.2** W5 confirms cdep birth tables COPY, senat facts COPY, GLD CC0 COPY, SER-PROM COND (cross-check only until permission), Wikidata CC0 but bulk `/sparql` disallowed → cached/dump flows. → **CP-2.2**
- **AP-2.3** Capture fixtures for `structura2015.de?leg=1990&par=V01..V12` and `leg=2024`, plus the `21.01.1991` anomaly row; verify headers `Nume si prenume / Data nasterii / Circumscriptia electorala / Grupul parlamentar` and `idm` in link. → **CP-2.3**

#### P1

- **AP-2.4** Add models after `db.py:104`: `PersonAttribute` (with `status active/conflict/superseded`, `soft-delete`, `Index(person_id,key)`), `OrgIdentifier`; leave `Evidence.membership_id` untouched. → **CP-2.4**
- **AP-2.5** Write birth-month parser with DOB `D.MM.YYYY`, future-date rejection, and exact identifier match `deputies:{leg}:{idm}` / `senate:{leg}:{idm}`, fallback `cdp_idm+leg`; existing `birth_date` wins; conflicts stored `status='conflict'`. → **CP-2.5**
- **AP-2.6** Write GLD source using Dataverse persistentId `doi:10.7910/DVN/U1ZNVT`, dataFile `10595375` (8,991,183 bytes, 30 vars), codebook `10595363`; match only among 2016 deputies, exactly one name candidate, DOB decisive; never create persons. GLD is for education/occupation, **not** mass DOB repair. → **CP-2.6**
- **AP-2.7** Write Party Facts alias map layer (party covariates land in Wave 3, but the crosswalk schema is created here). → **CP-2.4**

#### P2

- **AP-2.8** Add CLI `enrich-birth-dates`; run dry-run on DB copy; verify coverage 275/275 addressable (268 cdep_mandate, 7 cdep_idm; 196 senate-only, 72 deputies). → **CP-2.7**
- **AP-2.9** Wire `enrich --apply` into `data.yml` between audit (:81) and prepare (:83): restore wikidata-cache separately, copy DB via sqlite backup (not raw `cp`, WAL), dry-run then apply on copy, atomic `mv`, upload reports, save cache even on failure, `continue-on-error` throughout. → **CP-2.8**
- **AP-2.10** Write `tests/test_enrich*.py` (none exist today) with per-source fixtures and exact test names; run `uv run pytest -q tests/test_enrich*`. → **CP-2.9**

#### P3

- **AP-2.11** W2 adds `BioFacts` and `BioCoverageNote` into `PersonDeepDive` and `Mps`, showing source URL and precision (month-only DOB must not display a fabricated day). → **CP-2.10**
- **AP-2.12** W3 updates `generational_shift` (A7) to report excluded no-birth-date count explicitly instead of silently excluding 275; use true median. → **CP-2.10**

#### P4

- **AP-2.13** W5 registers `check_biography_provenance` after `audit.py:410-453` (and fixes the `:410-414` docstring/body mismatch). → **CP-2.11**
- **AP-2.14** Strict audit, full gate, promotion per Wave 1 P4. → **CP-2.12, CP-2.13**

##### Checkpoints — Wave 2

**CP-2.1 CLI bugs fixed.** Pass: `args.db` honoured, CLI default dry-run, module default dry-run; a dry-run makes zero row changes. Fail: revert. **Rollback:** revert commit. **Irreversible:** none.

**CP-2.2 Legal gate.** Pass: SER-PROM marked COND/cross-check; no bulk Wikidata SPARQL. Fail: block those sources. **Rollback:** revert note. **Irreversible:** decision record.

**CP-2.3 Birth fixtures.** Pass: fixtures saved; anomaly row identified and rejected in parser test. Fail: no parser. **Rollback:** delete untracked fixtures. **Irreversible:** none.

**CP-2.4 Schema.** Pass: `person_attribute` and `org_identifier` present; `Evidence.membership_id` still NOT NULL. Fail: block. **Rollback:** drop tables on copy / restore snapshot. **Irreversible:** none on copy.

**CP-2.5 Exact-match parse.** Pass: zero name-only merges; unknown → conflict/NULL + warning; person count unchanged at 3,388 before enrichment. Fail: block. **Rollback:** restore DB copy. **Irreversible:** fabricated links on shipped DB (copy-only rule prevents).

**CP-2.6 GLD.** Pass: ≤329 candidate rows, match only 2016 deputies, education/occupation stored with `source_url`, `license_flag='CC0'`; GLD DOB used only as secondary evidence. Fail: block. **Rollback:** delete GLD-attributed attributes on copy. **Irreversible:** none.

**CP-2.7 Coverage estimate.** Pass: measured filled count within 200–268 central ~240 [INFERRED, MEDIUM confidence] or explicitly reported outside with reason; `cam=2` ≤72 case handled; GLD ≤2; Wikidata 50–150 LOW; residual ~7–35 disclosed. Fail: investigate before promotion. **Rollback:** drop attributes. **Irreversible:** none.

**CP-2.8 Workflow wiring.** Pass: data.yml dry-run→apply-on-copy→atomic mv sequence proven in a workflow run; cache saved on injected failure; official corpus unaffected by injected GLD failure. Fail: block. **Rollback:** revert workflow commit. **Irreversible:** workflow run history; possible Render auto-deploy (disable first if freezing — DEPLOYMENT.md:164-167).

**CP-2.9 Enrichment tests.** Pass: all `test_enrich*` green with raw output. Fail: 3-retry then escalate. **Rollback:** revert. **Irreversible:** none.

**CP-2.10 UI/statistics.** Pass: screenshots show source + precision; A7 exposes excluded count; no fabricated day. Fail: block. **Rollback:** revert + Vercel rollback. **Irreversible:** bundle cache.

**CP-2.11 Audit.** Pass: biography provenance check registered and green. **Rollback:** revert. **Irreversible:** baseline review record.

**CP-2.12 Full gate.** Pass: CP-0.8 criteria. **Rollback:** as CP-0.8. **Irreversible:** as CP-0.8.

**CP-2.13 Production proof.** Pass: release tag served, `wikidata_qid` > 0, missing birth dates reduced, `/api/coverage/detailed` updated. **Rollback:** release-pin revert → platform rollback → git revert → physical restore. **Irreversible:** published release assets, bundles, cache, third-party changes.

---

### WAVE 3 — Party covariates

**Goal.** Add party ideology/populism context via Party Facts IDs, without touching party genealogy or `organization.short_name`.  
**Value/effort.** 1 week, high analytical payoff (research Phase 3, lines 320-328).

**Affected files:** `db.py` (after `Person(:104)` area for `PartyScore`, `OrgIdentifier` from Wave 2); `pipeline/parse/party_score.py`, `pipeline/sources/partyfacts.py`; `backend/routers/api.py` (new `/api/traseism/switchers-by-ideology`); `pipeline/audit.py` (benchmark/licence checks); `frontend` `PartyComparison.tsx:46,51`, `Traseism.tsx` new tab, `IdeologyScatter / PartyScoreTable`.

#### P0
- **AP-3.1** W5 class per file: CHES prefer EUI CC BY 4.0 archive; V-Party CC BY-SA → `redistributable=False`; POPPA academic free; PopuList open; Party Facts free; ParlGov CC0. → **CP-3.1**
- **AP-3.2** Verify Party Facts crosswalk resolves FSN→FDSN→PDSR→PSD to one ID using the reviewed alias map; capture evidence. → **CP-3.2**

#### P1
- **AP-3.3** Add `party_score(party_org_id, year, source, variable, value, value_text, license_flag, source_url, dedup_key UNIQUE)`; join by Party Facts ID / `Organization.wikidata_qid` stored in `org_identifier`. → **CP-3.3**
- **AP-3.4** Parser per source with `source_url`, `confidence`, `license_flag`, `dedup_key`; XCHECK sources produce display-only rows with `redistributable=False` and `export_ok=False`. → **CP-3.4**

#### P2
- **AP-3.5** Dry-run on copy; verify switching rate by ideology quartile is computable; lineage resolves to one Party Facts ID. → **CP-3.5**
- **AP-3.6** Tests: no write to `organization.short_name`, `previous_party_id`, `successor_party_id`; no CC-BY export of SA rows. → **CP-3.4**

#### P3
- **AP-3.7** W3 exposes `/api/traseism/switchers-by-ideology` with Welch CI and Party Facts join; switchers-vs-nonswitchers by party-year. → **CP-3.6**
- **AP-3.8** W2 adds `IdeologyScatter / PartyScoreTable` in `PartyComparison` and a Traseism tab, labelled external covariates. → **CP-3.6**

#### P4
- **AP-3.9** W5 registers `check_benchmark_license` before `audit.py:830` and `check_election_result` after benchmark; `license_flag` export gate asserted. → **CP-3.7**
- **AP-3.10** Full gate + promotion. → **CP-3.8, CP-3.9**

##### Checkpoints — Wave 3

**CP-3.1 Licence per file.** Pass: each dataset has a recorded class; SA files flagged non-redistributable. Fail: exclude. **Rollback:** revert note. **Irreversible:** decision record.

**CP-3.2 Lineage.** Pass: alias map resolves lineage with evidence; no `organization` row changed. Fail: keep lineage unresolved and report. **Rollback:** revert alias map. **Irreversible:** none.

**CP-3.3 Schema.** Pass: `party_score` present with unique dedup; `org_identifier` present. **Rollback:** drop on copy. **Irreversible:** none.

**CP-3.4 Parser/export gate.** Pass: tests prove SA rows `export_ok=False`; no genealogy writes. **Rollback:** revert parser. **Irreversible:** none.

**CP-3.5 Dry-run.** Pass: quartile computation returns values; zero changes to `organization`. **Rollback:** drop `party_score` rows on copy. **Irreversible:** none.

**CP-3.6 API/UI.** Pass: endpoint envelope complete, CI present, UI label "external covariate, not our event data". **Rollback:** revert + Vercel rollback. **Irreversible:** bundle cache.

**CP-3.7 Audit.** Pass: licence checks green; no SA value exportable. **Rollback:** revert audit. **Irreversible:** baseline record.

**CP-3.8 Full gate / CP-3.9 Production.** Same mechanics as CP-1.12/CP-1.13. **Rollback ladder:** identical. **Irreversible:** identical.

---

### WAVE 4 — Committee histories and speeches

**Goal.** Add dated committee roles and citable speech events.  
**Value/effort.** 2 weeks (research Phase 4, lines 330-337).

**Affected files:** `Membership` already supports `role`, `start_date`, `end_date`, `confidence`, `source_url` (research line 336 — no schema change needed for roles); new `speech` table in `db.py`; `EVIDENCE_TYPES` additions `speech`/`intervention` at `db.py:72`; new `pipeline/parse/*`, `pipeline/sources/*`; `pipeline/audit.py` evidence checks; frontend timeline components.

#### P0
- **AP-4.1** W5 confirms Zenodo 3332908 CC BY (safe), monitorul.ai public text CC BY dumps (safe), senat committee facts COPY, cdep committee sittings facts COPY. → **CP-4.1**
- **AP-4.2** Capture fixtures: senat `Comisie_new.aspx?ComisieID=<GUID>&Zi=`, cdep `sedinte2015.comisii`, one Zenodo `CDEPs2.csv` sample row, one monitorul.ai permalink. → **CP-4.2**

#### P1
- **AP-4.3** Add `speech` table (person_id, date, chamber, text_url, source, `dedup_key`, `source_url`, `confidence`, `snapshot_hash`); extend `EVIDENCE_TYPES` with `speech`/`intervention` at `db.py:72`. → **CP-4.3**
- **AP-4.4** Parsers for dated committee roles writing into `Membership` via existing columns, never overwriting a stronger `official_ledger` value. → **CP-4.4**

#### P2
- **AP-4.5** Dry-run on copy; verify 2-hop provenance for monitorul.ai citations and Zenodo speaker URLs. → **CP-4.5**
- **AP-4.6** Tests: speech dedup idempotency; committee date ordering (`interval_order` check remains green). → **CP-4.4**

#### P3
- **AP-4.7** Timeline integration: link speeches to the existing chronology; W2 adds speech citation affordance in `PersonDeepDive`. → **CP-4.6**

#### P4
- **AP-4.8** Audit registration; full gate; promotion. → **CP-4.7, CP-4.8, CP-4.9**

##### Checkpoints — Wave 4

**CP-4.1 Legal gate.** Pass: classes recorded; no full-text redistribution without CC BY basis. **Rollback:** revert note. **Irreversible:** decision record.

**CP-4.2 Fixtures.** Pass: four fixtures with checksums. **Rollback:** delete untracked. **Irreversible:** none.

**CP-4.3 Schema.** Pass: `speech` table + enums. **Rollback:** drop on copy. **Irreversible:** none.

**CP-4.4 Parser.** Pass: idempotent, no overwrite of stronger values, dates ordered. **Rollback:** revert. **Irreversible:** none.

**CP-4.5 Provenance.** Pass: every speech has `text_url` + fragment checksum. **Rollback:** drop rows on copy. **Irreversible:** none.

**CP-4.6 UI.** Pass: browser screenshot shows citation link. **Rollback:** revert + Vercel rollback. **Irreversible:** bundle cache.

**CP-4.7 Audit / CP-4.8 Full gate / CP-4.9 Production.** As Wave 1 equivalents. **Rollback ladder:** identical. **Irreversible:** identical.

---

### WAVE 5 — Elections

**Goal.** Give MPs an electoral-base denominator from AEP/data.gov.ro results.  
**Value/effort.** 1 week (research Phase 5, lines 338-344). **Critical caveat:** `mandate.constituency` is 100% NULL today (5,273/5,273), so the join cannot work until this wave actually populates constituency data.

**Affected files:** `db.py` (`ElectionResult` from W6 model set); `pipeline/sources/aep.py`, `pipeline/parse/election_result.py`; `backend/routers/api.py` (`/analytics/electoral-base`); `frontend` `PartyProfile`, `LegislatureDetail` with `ElectoralBaseCard / ConstituencyTable / SeatVoteComparison`; `pipeline/audit.py` `check_election_result` (registered in Wave 3).

#### P0
- **AP-5.1** W5 confirms data.gov.ro OGL/CC BY classes; AEP site reCAPTCHA → use CKAN mirrors only; Code for Romania MPL-2.0 fallback; internal AEP columns `[UNVERIFIED]` → resolve by downloading the actual CSV/XLSX and recording headers before parsing. → **CP-5.1**
- **AP-5.2** Verify the 2012/2016 slugs via `package_search`/`package_show` and capture response bodies. → **CP-5.2**

#### P1
- **AP-5.3** `ElectionResult(chamber, legislature, constituency, party_org_id, votes, seats, source_url, license_flag, dedup_key UNIQUE)`; derive `valid_votes` denominator. → **CP-5.3**
- **AP-5.4** Parser must not join `mandate.constituency` until that column is populated; if still 100% NULL, endpoint returns `status: unavailable` with reason. → **CP-5.4**

#### P2
- **AP-5.5** Dry-run; assert seat sums vs mandates (`check_election_result`, W5) — docs say 330, audit.py:812 says 329; use 329 unless a new source proves otherwise. → **CP-5.5**
- **AP-5.6** Tests for denominator correctness and for `unavailable` behaviour. → **CP-5.4**

#### P3
- **AP-5.7** W3 exposes `/analytics/electoral-base` with valid-votes denominator and `missing_data_count`. → **CP-5.6**
- **AP-5.8** W2 adds electoral UI with "external benchmark, not our data" labelling where benchmarks appear. → **CP-5.6**

#### P4
- **AP-5.9** Audit, full gate, promotion. → **CP-5.7, CP-5.8, CP-5.9**

##### Checkpoints — Wave 5

**CP-5.1 Legal/acquisition gate.** Pass: CKAN-only acquisition; no reCAPTCHA bypass. **Rollback:** revert note. **Irreversible:** decision record.

**CP-5.2 Slug verification.** Pass: response bodies saved, headers recorded; internal-column `[UNVERIFIED]` resolved. **Rollback:** delete fixtures. **Irreversible:** none.

**CP-5.3 Schema.** Pass: table with unique dedup and licence flag. **Rollback:** drop on copy. **Irreversible:** none.

**CP-5.4 Denominator/disabled path.** Pass: no join to NULL constituency; `unavailable` envelope returned when needed. **Rollback:** revert. **Irreversible:** none.

**CP-5.5 Seat reconciliation.** Pass: seat sums equal 329 or documented discrepancy; zero new audit errors. **Rollback:** drop election rows on copy. **Irreversible:** none.

**CP-5.6 API/UI.** Pass: envelope complete; benchmark labels present. **Rollback:** revert + Vercel rollback. **Irreversible:** bundle cache.

**CP-5.7 Audit / CP-5.8 Full gate / CP-5.9 Production.** As Wave 1 equivalents. **Rollback ladder:** identical. **Irreversible:** identical.

---

### WAVE 6 — Benchmarks

**Goal.** Make every headline number comparable to an external, clearly-labelled series.  
**Value/effort.** 1 week (research Phase 6, lines 346-352).

**Affected files:** `db.py` (`Benchmark`, `context_year`); `pipeline/sources/worldbank.py`, `pipeline/sources/eurostat.py`, `pipeline/sources/ec_table.py`; `backend/routers/api.py` (`/analytics/demographic-benchmarks`); `frontend` `CoverageView`, `Demographics`, `Report`, `BenchmarkBand / BenchmarkSourceNote`.

#### P0
- **AP-6.1** W5 class: World Bank `SG.GEN.PARL.ZS` CC BY safe; Eurostat `sdg_05_50` CC BY safe; EC 1990–2024 both-chamber table EU document safe as citation; IPU CC BY-NC-SA **XCHECK ONLY** — never copy fields; INS TEMPO attribution only, POST body `[UNVERIFIED]` → resolve by capturing the POST response before use. → **CP-6.1**
- **AP-6.2** Verify live World Bank shape (`lastupdated 2026-11-11`, null values skipped) and Eurostat JSON-stat shape. → **CP-6.2**

#### P1
- **AP-6.3** `benchmark(source, chamber, legislature_or_year, metric, value, license_flag, redistributable, source_url, dedup_key UNIQUE)` and `context_year(year, source, variable, value, ...)`; IPU rows stored as XCHECK with `export_ok=False` or kept out of DB and used only in the audit comparison. → **CP-6.3**
- **AP-6.4** Parsers with `min_votes`-style minimums not applicable; require `source_link` and `benchmark_provenance` fields. → **CP-6.4**

#### P2
- **AP-6.5** Dry-run; verify EC both-chamber series aligns to the 10 legislatures; nulls skipped explicitly. → **CP-6.5**

#### P3
- **AP-6.6** W3 exposes `/analytics/demographic-benchmarks` with `our_n`, `our_missing`, `license_flag`, `benchmark_provenance`. → **CP-6.6**
- **AP-6.7** W2 adds `BenchmarkBand / BenchmarkSourceNote` with the literal label "external benchmark, not our data". → **CP-6.6**

#### P4
- **AP-6.8** `check_benchmark_license` (already registered in Wave 3) proven green; full gate; promotion. → **CP-6.7, CP-6.8, CP-6.9**

##### Checkpoints — Wave 6

**CP-6.1 Legal gate.** Pass: IPU marked XCHECK; no IPU value in exportable tables. **Rollback:** revert note. **Irreversible:** decision record.

**CP-6.2 Live shapes.** Pass: response bodies saved with `lastupdated` and null handling documented. **Rollback:** delete fixtures. **Irreversible:** none.

**CP-6.3 Schema.** Pass: licence fields and unique dedup. **Rollback:** drop on copy. **Irreversible:** none.

**CP-6.4 Parser.** Pass: provenance fields non-null. **Rollback:** revert. **Irreversible:** none.

**CP-6.5 Dry-run.** Pass: 10-legislature alignment; nulls disclosed. **Rollback:** drop rows on copy. **Irreversible:** none.

**CP-6.6 API/UI.** Pass: envelope includes `our_n`, `our_missing`, provenance, label text; screenshot proof. **Rollback:** revert + Vercel rollback. **Irreversible:** bundle cache.

**CP-6.7 Audit / CP-6.8 Full gate / CP-6.9 Production.** As Wave 1 equivalents. **Rollback ladder:** identical. **Irreversible:** identical.

---

## 6. Cross-wave FRONTEND/UX MASTER PLAN

### 6.1 Route-by-route impact

19 routes are defined at `frontend/src/router.tsx:303-480` (W2, digest line 18). `/compare-mps` has no top-nav link — only reachable from `Mps.tsx:395`.

| Route | Wave impact | Change |
|---|---|---|
| `/` LiveDashboard | W0, W1, W6 | Definition labels (AP-0.11), hero card clicks (AP-0.12), edges (AP-0.12), new vote-count card, benchmark band on gender card |
| `/electoral` | W5 | Redirect target gains electoral-base card |
| `/institutional` | W6 | BenchmarkSourceNote; AP-0.12 InstitutionalView:71-74 placeholder removal |
| `/party/$shortName` PartyProfile | W3, W5 | Ideology row, ElectoralBaseCard, ConstituencyTable, SeatVoteComparison |
| `/person/$id` PersonDeepDive | W1, W2, W4 | Voting record, BioFacts, speech citations, presence-at-vote note |
| `/legislature/$year` LegislatureDetail | W5, W6 | Electoral base, benchmark band |
| `/traseism` Traseism | W3 | Ideology-tab; reuse `Traseism.tsx:134-164,845-866` pattern |
| `/coverage` CoverageView | W0, W1, W2, W6 | Honest per-dimension coverage, BenchmarkBand |
| `/senate-history` | W0 | Fix sum labels (line [UNVERIFIED] in digest — resolve with `grep -n "sum\|total" src/pages/SenateHistory.tsx` before edit) |
| `/leaderboard` | W1 | Presence must NOT become a ranking; loyalty caveats remain |
| `/demographics` | W0, W2, W6 | Fix unweighted mean-of-means `Demographics.tsx:44-57`; benchmark band |
| `/committees` | W0, W4 | Fix tally label `Committees.tsx:239-243`; dated committee history |
| `/compare` | W3 | Ideology scatter |
| `/coalitions` | W3 | Party-context reference |
| `/mps` Mps | W0, W2 | Fix page-size-as-total `Mps.tsx:82-106`; BioFacts |
| `/compare-mps` | W0, W1 | Add top-nav link; voting-record comparison |
| `/report` Report | W6 | BenchmarkSourceNote |
| `/parties` | W3 | PartyScoreTable |
| `/party-timeline` | W0, W3 | Fix label (line [UNVERIFIED] in digest — resolve with `grep -n "label" src/pages/PartyTimeline.tsx`); ideology rows |

**New routes:** `/votes` (vote explorer), `/vote/$id` (vote detail) — Wave 1. Both need top-nav entries and ro/en keys.

### 6.2 New pages, sections, components

| Domain | Components | Host pages | Wave |
|---|---|---|---|
| Votes | `VoteExplorer`, `VoteTable`, `VoteDetail`, `VotePositionStrip`, `PartyCohesionChart`, `VoteCoverageBanner` | new `/votes`, `/vote/$id`, `PersonDeepDive`, `Mps` | W1 |
| Biographies | `BioFacts`, `BioCoverageNote` | `PersonDeepDive`, `Mps` | W2 |
| Ideology | `IdeologyScatter`, `PartyScoreTable` | `PartyComparison`, `Traseism` tabs, `/parties` | W3 |
| Elections | `ElectoralBaseCard`, `ConstituencyTable`, `SeatVoteComparison` | `PartyProfile`, `LegislatureDetail` | W5 |
| Benchmarks | `BenchmarkBand`, `BenchmarkSourceNote` | `CoverageView`, `Demographics`, `Report`, `InstitutionalView` | W6 |
| Speeches | citation affordance in timeline | `PersonDeepDive` | W4 |

Each new component ships with: ro + en i18n keys (no English literal fallback — W2 found 57 such keys already, digest line 27), `aria-sort` on sortable tables, a text alternative for every SVG chart, and an explicit denominator/source label.

### 6.3 The 16 verified UI defects to fix first (exact file:line)

| # | Defect | Exact location | Fix | Kind |
|---|---|---|---|---|
| 1 | Hero cards look interactive but `onClick` undefined at all four call sites | `LiveDashboard.tsx:97-141` | Wire navigation or remove affordance | Quick win |
| 2 | `div role=button` + deprecated `onKeyPress` + `window.location.href` that loses `asOf`; nested link invalid | `DashboardCard.tsx:76-95` | Use `<button type="button">` / router link preserving `asOf` | Quick win |
| 3 | Dashboard numbers with no denominator/scope labels; definition collision | `DashboardCard.tsx:97-108`, `InfoStat.tsx:48-82`, `api.py:985-995`, `pipeline/queries.py:38-42` | Label `active_memberships_as_of`, `switches all-time` | Quick win (W0) |
| 4 | `edges=[]` placeholder presented as data | `LiveDashboard.tsx:196` | Remove or mark "not available" | Quick win |
| 5 | Both bars hard-coded 100% | `CrossChamberFlow.tsx:24-27,55-80` | Compute or remove | Quick win |
| 6 | Fake coverage + hardcoded `fill="white"` | `DataQualityGauge.tsx:37-53,134` and `:108` | Real coverage semantics; CSS var | Quick win |
| 7 | Only 4 legend rows (`AgeDistributionRadial.tsx:125`) + hardcoded white (`:113`) | `AgeDistributionRadial.tsx:113,125` | Full legend; CSS var | Quick win |
| 8 | Permanent "unavailable" state | `InstitutionalView.tsx:71-74` | Real state | Quick win |
| 9 | Page size shown as total | `Mps.tsx:82-106` | Use real total from API | Quick win |
| 10 | Running tally labelled "total" | `Committees.tsx:239-243` | Relabel running | Quick win |
| 11 | Unweighted mean-of-means | `Demographics.tsx:44-57` | Weight by group size | Quick win (with W3) |
| 12 | Fake coverage | `CommitteeControl.tsx:122-125` | Real coverage | Quick win |
| 13 | Unscoped aggregates | `PartyComparison.tsx:46,51` | Add scope/denominator | Quick win |
| 14 | SenateHistory sums mislabelled — defect VERIFIED, exact line `[UNVERIFIED]` in digest | resolve with `grep -n` in `SenateHistory.tsx` before edit | Correct sum labels | Quick win |
| 15 | PartyTimeline label — defect VERIFIED, exact line `[UNVERIFIED]` in digest | resolve with `grep -n` in `PartyTimeline.tsx` before edit | Correct label | Quick win |
| 16 | Theme toggle mounted only on `/` | `ui/DashboardHeader.tsx:15` | Mount site-wide | Quick win |

**Supporting a11y/i18n defects (fix with #1–#16):** SVG charts without text alternatives; `ErrorState` role duplication; `EmptyState` nested `<svg>`; 57 i18n keys with literal English fallbacks absent from both dictionaries; `nav.committees` / `nav.compare` only in `ro` (digest line 27).

### 6.4 Accessibility, i18n and design-system rules

- **Baseline widely-available features only** (product `AGENTS.md`, W7 line 76).
- `type="button"` on every button; no `onKeyPress`.
- WCAG AA contrast; **no hardcoded `fill="white"`** — use tokens (`index.css:5-45` dark, `:51-72` light, `:76-89` accent overrides).
- Tailwind bridge at `tailwind.config.js:8-28` is v3-specific — do not migrate to Tailwind 4 in these waves.
- Focus styles at `index.css:198-201`; motion at `:139-169,203-227` with reduced-motion rest state.
- Every new string gets ro + en keys; no literal fallback.
- Reuse existing good patterns: `Traseism.tsx:134-164,845-866` for honest denominators/gap notes; `DashboardCard` after fix for card composition; the existing `ui/*` primitives — but check the orphan list first.
- **Orphaned components available for reuse** (digest line 27): `LiveFeed`, `TimeSlider`, `ChamberView`, `TimelineStrip`, `PartyComparisonMatrix`, `EmptyState`, `LoadingState`, `ui/Modal`, `ui/Drawer`, `ErrorState` — inspect before writing new ones.

### 6.5 Stack version stance (do not upgrade in these waves)

Pinned: react 19.3.1, vite 6.4.6, tailwind 3.4.19, TS 5.9.3, @tanstack/react-router 1.161.3, react-query 5.107.1 (digest line 28). W2 checked the registry: vite 8.3.8 (two majors ahead), tailwind 4.3.5 (one major), TS 7.0.2 (two majors), echarts one major, router 9 minors behind. **Tailwind 4 migration is non-trivial because the CSS-var architecture is v3-specific.** Version upgrades are a separate, later programme with its own wave and gates; bundling them into the data-enrichment waves would make every checkpoint ambiguous. "No old technology" is satisfied by using current, widely-available APIs within the pinned majors and by scheduling the major-version review as a tracked follow-on — not by silently mixing upgrades into Wave 1.

### 6.6 Quick wins vs wave-coupled

- **Quick wins (Wave 0, no new data required):** #1–#13, #16, a11y/i18n fixes. These are independently shippable and reduce the noise in later screenshots.
- **Wave-coupled:** vote routes/components (W1), BioFacts (W2), ideology components (W3), speech citations (W4), electoral components (W5), benchmark bands (W6). Work on these must wait for their endpoint contract to PASS, otherwise W2 would be designing against placeholders — exactly the defect class already found.

---

## 7. STATISTICAL TRUST framework

### 7.1 Definitions (owned by W3, no exceptions in UI copy)

| Statistic | Definition | Denominator | Source |
|---|---|---|---|
| Party cohesion (vote-based) | `Σmax_vp / Σcast_vp` with Wilson CI | **votes cast**, not all members; `min_votes` default 20 | new `vote_position` table |
| Agreement with party | share of an MP's votes matching majority of their group at vote date | votes cast by that MP | `vote_position` |
| Voting record | per-MP list of votes with choice + group at vote | — | `vote_position`, `PersonIdentifier` |
| Presence at vote | factual count with source + known gaps | eligible records at that vote | `vote.present`, `vote.not_voting` |
| Switch rate (T2) | switchers / distinct members | distinct members | existing |
| Loyalty (leaderboard) | `(switch_count/total_events)*min(1, tenure_years/4)` | total events | existing — caveats must stay visible |
| Generational shift (A7) | true `statistics.median`, excluding count disclosed | persons with birth date | `person.birth_date`, `person_attribute` |
| Committee control (A9) | chairs / **active chairs** (not committees) | active chairs | existing — relabel |
| Electoral base | votes by valid votes denominator | `valid_votes` | `election_result` |
| Demographic benchmark | our value vs external series with `our_n`, `our_missing` | our N | `benchmark`, `party_score` |

**Never:** attendance score, presence ranking, unweighted mean-of-means, all-time number without `as_of`, KeyEvent-row "legislature count" presented as 10 unique legislatures.

### 7.2 Time semantics

- Core is **half-open**: `pipeline/queries.py:1-5,38-42` (`end_date > D`).
- `/api/dashboard/stats:990` uses inclusive `>=` — this is the source of the 4,461 vs 7,349 confusion (W2 G1). Fix by explicit field names, not by silently changing semantics.
- `date.today()` is server-local; only `computed_at`/`generated_at` are aware UTC (W3, digest line 35). New endpoints must export aware UTC and state `as_of` explicitly.

### 7.3 REST/GraphQL convergence fixes (must land before any "convergence" claim)

1. `party_cohesion`: GraphQL currently uses `to_org_id` only and returns `[]`; REST returns `unavailable` because A6 uses `switch_party` events only and the corpus has 0 such events (`api.py:999-1005` context). Fix: both return the same `status: unavailable` envelope with reason until vote-based cohesion exists; afterwards both use the vote formula.
2. `median_age`: GraphQL uses upper median, REST uses true `statistics.median`. Fix: identical algorithm in both.
3. Add `tests/test_graphql_convergence.py` assertions comparing REST and GraphQL payloads for the same query; byte-comparable after normalising transport fields.

### 7.4 Exact new endpoint contracts

All endpoints share this envelope:

```json
{
  "status": "ok | unavailable | partial",
  "scope": { "chamber": "cdep|senat|both", "legislature": "YYYY", "as_of": "YYYY-MM-DD" },
  "data": { },
  "sample_size": { "value": 0, "unit": "votes|persons|memberships|election_results" },
  "denominator": "human-readable string, e.g. 'votes cast in scope, present and voting'",
  "missing_data_count": 0,
  "precision": { "ci": [0.0, 0.0], "method": "wilson|welch|none", "min_votes": 20 },
  "source_link": "https://…",
  "benchmark_provenance": "external:WorldBank:CC-BY|null",
  "license_flag": "CC-BY|CC0|XCHECK|null",
  "computed_at": "UTC ISO-8601",
  "cache": "no-store"
}
```

**GET `/analytics/vote-cohesion`** — params `chamber`, `legislature`, `from`, `to`, `min_votes` (default 20). `data.parties[]` with `party_id`, `votes`, `cohesion`, `ci`, `denominator`. Scope regexes from `api.py:772-773`. `status: unavailable` when votes in scope < `min_votes`.

**GET `/analytics/voting-record`** — params `person_id` (must resolve via `PersonIdentifier`, never create). `data.votes[]` with `vote_id`, `date`, `choice`, `group_at_vote`, `party_at_vote`, `source_url`. `sample_size.unit = votes`.

**GET `/analytics/presence-at-vote`** — params `person_id` or `party_id`, `legislature`. `data.present`, `data.not_voting`, `data.eligible_records`, mandatory `caveat` string: "Presence at a vote is a fact with known source gaps; this is not an attendance score and no ranking is computed." No score field, no rank field.

**GET `/api/traseism/switchers-by-ideology`** — params `year`, `ideology_variable` (`ches_left_right`, `vparty_populism`, `populist_dummy`). `data.switchers` / `data.nonswitchers` with `n`, `mean`, `ci`, `method: welch`, `partyfacts_id`. `license_flag` per source; SA sources `XCHECK`, never in export.

**GET `/analytics/demographic-benchmarks`** — params `metric`, `legislature`. `data.our_value`, `data.our_n`, `data.our_missing`, `data.benchmark_value`, `data.benchmark_source`, `benchmark_provenance` = `"external:<source>:<licence>"`, `license_flag`. IPU rows return `license_flag: "XCHECK"` and `export_ok: false`.

**GET `/analytics/electoral-base`** — params `chamber`, `legislature`, `constituency`. `data.valid_votes`, `data.votes_by_party`, `data.seats`, `data.mandates_linked`. When `mandate.constituency` is 100% NULL (today), return `status: unavailable`, `missing_data_count: 5273`, reason "constituency not populated", cache `no-store`.

**Export convergence:** add a new branch in `pipeline/export.py:352` (adding names to `CSV_DATASETS` alone derives empty columns from Popolo — do not do that); add route beside `backend/routers/exports.py:190-203`; add blocks to `/export/report:139-159`. `license_flag = XCHECK` or `redistributable = false` rows are excluded from all export formats.

### 7.5 Disclosure rules

- Every number displayed in UI carries: scope, denominator, sample size, missing count, source link.
- External benchmark series carry the literal label **"external benchmark, not our data"**.
- Gap disclosure wins over aesthetics: `About.tsx:263-298` note must be visible; `coverage` must say `votes: none` until Wave 1 lands.
- Corrections/errata: append, never silently rewrite; the baseline fingerprint discipline (VERIFICATION.md:82-91) is the model.

---

## 8. DEPLOYMENT / CHECKPOINT MATRIX

### 8.1 Repo-scope warning (display before every command block)

```
NedCode4 commands (just doctor | just verify | just docs | just docs-check |
lib/secret-scan.sh | just verify-project | just ship) run ONLY in
/home/nedaktov/Desktop/NedCode4. There is no justfile in parlament-deschis.

Product commands (uv sync --extra dev --locked | uv run ruff check ... |
uv run pytest -q | cd frontend && npm ci && npm run build |
uv run python -m pipeline.cli ... audit-corpus | gh workflow run ...)
run ONLY in /home/nedaktov/parlament-deschis.
```

### 8.2 Commands and expected outputs

| Checkpoint | Command (product repo unless marked N4) | Expected output |
|---|---|---|
| CP-0.1 | `uv run python -c "...sqlite3 counts..."`; `git rev-parse --short HEAD` | counts 3388/5273/7349/7429/120; `2995bfd` |
| CP-0.3 | `grep -n "No roll-call" docs/METHODOLOGY.md` | no hit |
| CP-0.5 | `grep -n "ignoreCommand" vercel.json` | `""` only (no dead tolerance in verify-deploy) |
| CP-0.8 / all full gates | `uv run ruff check pipeline backend scripts tests` | exit 0 |
| CP-0.8 / all full gates | `uv run pytest -q` | all green, exit 0 |
| CP-0.8 / all full gates | `(cd frontend && npm ci && npm run build)` | build exit 0 |
| CP-0.8 / all full gates | `uv run python -m pipeline.cli --db data/parlament-real.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json --json data/verification-report.json` | `275 known errors, 0 new errors`, exit 0 |
| CP-0.8 production | `gh workflow run deploy-verify.yml -R nedaktov-ops/parlament-deschis --ref main` | SHA + release tag asserted, all checks green |
| CP-0.6 | `gh api repos/nedaktov-ops/parlament-deschis/branches/main/protection` | required-check list or explicit UNVERIFIED note |
| Any rollback | `gh workflow run platform-rollback.yml -R ... -f platform=vercel -f target=dpl_… -f dry_run=true` then `dry_run=false -f confirm=ROLLBACK` | dry-run prints target first |
| All N4 gates | `just doctor`, `just verify`, `just docs-check` | exit 0; `just docs-check` **currently stale, exit 3** (AGENTS.md, llms.txt) — resolve with `just docs` and stage explicit paths, never hand-edit GENERATED blocks |
| N4 proof | `chrome-devtools` tools, `shadcn` tools, `opencode` tools | W7 counted 31 / 7 / 8; master session catalog shows 33 chrome-devtools — `[UNVERIFIED]` delta, resolve by live tool discovery |

### 8.3 Skill/MCP schedule by checkpoint

| Checkpoint class | NedCode4 skill / MCP | Behaviour |
|---|---|---|
| Wave opening / planning | `brainstorming`, `writing-plans`, `executing-plans`, `using-git-worktrees` | Plan gate before any code; isolate work in a worktree if parallel |
| P0 fixture/legal | `mcp-tool-resolution`, `modern-web-guidance` (if UI) | Resolve which MCP fetches the fixture; web guidance first for any UI |
| P1 schema/parser | `test-driven-development`, `systematic-debugging` | Failing test first; root cause before fix |
| P2 ingest/dry-run | `executing-plans`, `systematic-debugging` | Verify each step's output; stop when blocked |
| P3 API/UI | `design-taste-frontend`, `impeccable`, `modern-web-guidance`, `break-ui` | Design + checker gate; feed worst-case data; chrome-devtools screenshots |
| P4 audit/release | `requesting-code-review`, `receiving-code-review`, `verification-before-completion` | Second pair of eyes; run and read full verification output before any "done" claim |
| Every checkpoint | `knowledge-memory` | Store decisions, bug fixes, architecture choices for future sessions |
| Ship/proof (N4 only) | `just verify-project`, `just ship` | Product ship happens via product workflows, not N4 `just ship` |

MCP availability: visible catalog is chrome-devtools, shadcn, opencode; no subagent/task tool is visible to workers — treat subagent dispatch as parent-only (W7, digest line 74).

---

## 9. RISK REGISTER

Likelihood / Impact: H/M/L. Owner role from §4.

| # | Risk | L | I | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | WAL copy corruption — working DB `journal_mode=WAL` (db.py:447), shipped DB DELETE (prepare_db.py:170-177); raw `cp` yields inconsistent backup | M | H | Use sqlite `backup()` API; checkpoint WAL before any copy; verify backup counts | W4 |
| R2 | Cache invalidation — 300 s in-process result cache (`backend/cache.py:28`) serves stale numbers after a release pin | H | M | New endpoints `cache: no-store`; after promotion, verify with cache-busting query; document the 300 s residue as irreversible | W3/W4 |
| R3 | Immutable release edited by mistake | L | H | Only `latest-release.txt` is mutable; release tag `data-${run_id}-${attempt}`; W4 sole owner | W4 |
| R4 | Third-party outage blocks official corpus | M | H | cdep strict / vot-parlament non-fatal `DATA_UNAVAILABLE`; enrichment `continue-on-error` with own cache | W1/W6/W4 |
| R5 | Licence contamination — NC/SA values copied into CC-BY release | M | H | W5 veto; `license_flag` + `redistributable` + `export_ok` gate; XCHECK display-only | W5 |
| R6 | Stale docs contradict live data (D1–D14) | H | M | Wave 0 doc fixes; every wave updates DATA-MODEL/RESEARCH/VERIFICATION in same commit (research line 377) | W5 |
| R7 | Untracked research doc lost (`docs/DATA-ENRICHMENT-RESEARCH.md`) | H | M | Commit explicitly in AP-0.5; never `git add -A` on dirty tree | W5/W4 |
| R8 | Vercel skip-grace anomaly — `verify-deploy.sh` tolerates absent deploy after 180 s but `vercel.json:6` `ignoreCommand:""` | M | H | Remove dead tolerance; assert deploy exists (A-1) | W4 |
| R9 | `npm run lint` not a CI gate (A-2) | H | M | Add lint job; gate on it | W4 |
| R10 | `deploy-all.sh:21` footgun — hardcoded wave commit + `git add -A` (A-3) | M | H | Quarantine + dirty-tree guard; never use for promotion | W4 |
| R11 | Marker push via default token blocked by branch protection (A-5) `[UNVERIFIED]` | M | M | Resolve with `gh api .../branches/main/protection`; if blocked, use explicit Render API trigger (already in workflow) | W4 |
| R12 | Person fabrication via `PersonResolver.resolve()` in vote/bio ingest | M | H | Lookup-only `PersonIdentifier`; audit asserts person count unchanged; unknown → NULL + name + warning | W1/W6 |
| R13 | Missing field semantics (`par1`, `CAMERA`, `idv`) mis-parsed | H | H | Fixtures FIRST; four facts resolved in CP-1.1 before parser code | W1 |
| R14 | Birth-date anomaly `21.01.1991` on 1990 page accepted | M | M | Explicit future-date rejection test; `birth_date_precision` stored | W6 |
| R15 | Identity mismatch in GLD/SER-PROM — name-only merge | M | H | Exact official ID / name+DOB rules; conflicts `status='conflict'`; GLD only among 2016 deputies with one candidate | W6 |
| R16 | REST/GraphQL divergence presented as convergence | H | M | Fix party_cohesion envelope and median before any convergence claim; byte-comparison test | W3 |
| R17 | Attendance score introduced by UI or API | M | H | Non-negotiable §3.9; audit assertion "no attendance_score column/endpoint"; presence caveat text | W2/W3/W5 |
| R18 | Fake coverage / placeholder numbers misread as data | H | M | Fix 16 UI defects; CoverageView dimensions; `/api/coverage/detailed` honesty | W2 |
| R19 | Immutable browser bundle cache (`vercel.json:14-15`, 1 year) serves old UI after rollback | H | M | Treat as irreversible; version new asset paths; document in every rollback | W4/W2 |
| R20 | Render auto-deploy race (`platform-rollback.yml:145`) redeploys over a rollback | M | H | Disable auto-deploy in dashboard when freezing; re-enable after fix (DEPLOYMENT.md:164-167) | W4 |
| R21 | Vercel Hobby only previous deployment rollback | M | M | Confirm available target in dry-run; break-glass dashboard if needed | W4 |
| R22 | Read-only runtime prevents on-the-fly fixes | M | M | All enrichment pre-release on copies; no runtime writes | W6/W4 |
| R23 | `EVIDENCE_TYPES` defined but unused → new rows lack evidence | H | M | New audit checks use Fragment + source_url; W5 registration in `CHECKS` | W5 |
| R24 | `mandate.constituency` 100% NULL blocks electoral base | H | M | `/analytics/electoral-base` returns `status: unavailable` with `missing_data_count: 5273` until populated; never guess a constituency | W3/W5 |
| R25 | Audit baseline drift — natural-identity fingerprints broken by new findings | M | H | New checks baselined in same commit; strict must remain 275 known / 0 new or approved delta | W5 |
| R26 | Tooling scope error — `just` commands run in product repo (no justfile) | M | L | Repo-scope warning in §8.1 pasted into every command block | W7 |
| R27 | NedCode4 docs stale (`just docs-check` exit 3) and GENERATED block hand-edited | H | M | Regenerate with `just docs`, stage explicit paths; never hand-edit between markers | W7 |
| R28 | MCP count discrepancy (31 vs 33 chrome-devtools) treated as fact | L | L | `[UNVERIFIED]`; resolve with live tool discovery, no assumption | W7 |
| R29 | 275 missing birth dates not actually addressable (coverage estimate wrong) | M | M | CP-2.7 measures 268 cdep_mandate + 7 cdep_idm; report actual vs 200–268 estimate; no claim if below | W6 |
| R30 | Modules `enrich.py` / `cli.py` apply-by-default corrupts working DB | M | H | Fix `enrich.py:368-372`, `cli.py:260-272,763-772` in AP-2.1 before any enrichment | W6 |

---

## 10. PRIORITISED START ORDER and day-1 checklist

### 10.1 Start order

1. **Wave 0** — truth/docs and CI hardening. Nothing else starts until D1–D14 are closed and gates are honest. (½ day)
2. **Wave 1** — votes. The 10× move; fixtures first, four field facts resolved before parser. (2–4 weeks)
3. **Wave 2** — biographies and identifier wiring (fix CLI DB bugs first). (1–2 weeks)
4. **Wave 3** — party covariates (Party Facts crosswalk). (1 week)
5. **Wave 4** — committee histories and speeches. (2 weeks)
6. **Wave 5** — elections (constituency gap disclosed). (1 week)
7. **Wave 6** — benchmarks (IPU cross-check only). (1 week)

Parallelisable within a wave: W2 UI quick wins while W1 works on fixtures; W6 schema design while W1 finishes P4 — but no shared CI/data.yml edits, and every merge still passes the full gate.

### 10.2 What to do on day 1 (one-page checklist)

- [ ] Read this document, `DATA-ENRICHMENT-RESEARCH.md`, `DEPLOYMENT.md`, `VERIFICATION.md`, and `/tmp/opencode/supervisor-input.md` — no skipping.
- [ ] State the repo-scope rule aloud/in the ticket: NedCode4 `just *` only in `/home/nedaktov/Desktop/NedCode4`; product commands only in `/home/nedaktov/parlament-deschis`.
- [ ] Run AP-0.1 baseline counts; paste output. Expect 3388 / 5273 / 7349 / 7429 / 120.
- [ ] Run AP-0.2 git check; expect `2995bfd`, research doc untracked.
- [ ] W5 records licence classes (COPY / XCHECK / COND) for all planned sources and signs the legal gate.
- [ ] Commit `docs/DATA-ENRICHMENT-RESEARCH.md` explicitly (`git add docs/DATA-ENRICHMENT-RESEARCH.md`), never `git add -A`.
- [ ] Close D1–D14 in one documentation commit; verify `grep -n "No roll-call" docs/METHODOLOGY.md` returns nothing.
- [ ] Fix CLI truth defects AP-0.11 (dashboard definition collision) and the 16 UI defects that need no new endpoint.
- [ ] Add `npm run lint` CI gate and remove the dead 180 s Vercel tolerance.
- [ ] Quarantine `scripts/deploy-all.sh` with a dirty-tree guard.
- [ ] Resolve branch-protection required checks with `gh api ...` or record as UNVERIFIED with resolver.
- [ ] Run the full local gate: `uv sync --extra dev --locked`; `uv run ruff check pipeline backend scripts tests`; `uv run pytest -q`; `(cd frontend && npm ci && npm run build)`; strict audit → `275 known errors, 0 new errors`.
- [ ] In NedCode4 repo only: `just doctor`, then `just docs` (regenerate, stage explicit paths), then re-run `just docs-check` — it is stale today (exit 3).
- [ ] Record CP-0.1 … CP-0.8 results with raw output and timestamp in `knowledge-memory`.
- [ ] Only after all Wave 0 checkpoints PASS: open Wave 1 P0 — capture the three vote fixtures and resolve `par1`, `CAMERA`, `idv`, and element form. **No parser code before CP-1.1 PASSes.**

### 10.3 Final supervisory statement

This strategy contains no placeholders: every UNVERIFIED item has a named resolver, every action point has a checkpoint, every checkpoint has a rollback and an irreversible-items list, and every new statistic has a defined denominator. The safety contract in §3 is not advisory. If at any point the pressure to ship conflicts with evidence, the answer is **NOT PROVEN**, not PASS. That discipline — source URL on every row, SHA-256 snapshots, conservative identity matching, strict audit before release, no attendance score, no incompatible licence — is exactly what turns the current party-switch tracker into a trustworthy 10× parliamentary statistics platform rather than a bigger, less reliable one.

**Status of this document:** integration complete; ready for the parent agent to save under `docs/`. No product file was modified.
