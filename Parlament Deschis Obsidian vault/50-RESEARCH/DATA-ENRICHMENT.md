---
id: DATA-ENRICHMENT
type: research
title: "Data enrichment — proposed sources, gaps and vote fixtures"
description: "Mirror of enrichment research: EP/PACE/benchmark proposals not ingested, zero genealogy links, mandate-only coverage, byte-exact vote fixtures and identifier-only resolution."
status: active
authority: mirror
tags: [type/research, lifecycle/active, domain/data]
source_paths: [docs/DATA-ENRICHMENT-RESEARCH.md, docs/DATA-COMPLETENESS-RECOVERY.md, tests/fixtures/votes/FIELD-MAP.md, tests/fixtures/votes/manifest.json]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Data enrichment

Source discovery and licence disposition are in [SOURCE-RESEARCH](SOURCE-RESEARCH.md);
dated provenance is in [RESEARCH-LOG](RESEARCH-LOG.md). Nothing in this note is
an ingestion claim: "proposed" means documented and evaluated, not loaded into
the released corpus.

## External datasets — proposed, not ingested

| Source | What it offers | Status |
|---|---|---|
| **European Parliament Open Data API v2** | **146 Romanian MEP records** (33 current), exact membership dates, birth data, national-party crosswalk (`org/4135` PSD, `org/6709` PNL); terms 6–10 (2004→today), terms 1–5 return 204. CC BY 4.0. Bulk CSV lacks a national-party column — use API/RDF. | Best free MEP ↔ national-party crosswalk; **not ingested** |
| **Council of Europe / PACE** | 10 representatives + 10 substitutes with national party, chamber secretariat, dated mandates and committee roles | Strong independent chamber/party cross-check; **not ingested** |
| **Eurostat** | `sdg_05_50` women in parliaments 2003–2025, population/age/education denominators; CC BY 4.0 | Benchmark denominator; **not ingested** |
| **European Commission** | 1990–2024 both-chamber comparison table | Benchmark; **not ingested** |
| IPU / V-Dem / SER-PROM / World Bank | Gender and party covariates, historical series | **Cross-check only** by licence (ShareAlike / Non-Commercial); never copied into the CC BY release |

`PACE`, `Eurostat` and `EC` figures are proposed as benchmark columns in a
future `party_score`-style table joined through stored identifiers. They must
not be written into `organization.short_name` or overwrite genealogy.

## Known gaps in the released corpus

- **Party genealogy: 0 links (DROP confirmed 2026-11-21).** `previous_party_id` / `successor_party_id` exist
  in the `organization` model and in the migration, but every value is NULL in
  the corpus and GraphQL exposes no such fields. **No licence-complete source
  declares an ID-addressable predecessor/successor relation for Romanian parties**
  (Wikidata zero references, Party Facts incomplete, PolPaL NOT PROVEN, SER-PROM
  ShareAlike). The feature is formally dropped; the columns remain for
  forward-compatibility but are documented as unused. See `docs/METHODOLOGY.md`
  §9.5 and `docs/DECISION-PARTY-GENEALOGY.md`.
- **Senate historical profile ingest deferred.** Discovery is fixed and guarded
  (128/134 GUIDs — see [SOURCE-RESEARCH](SOURCE-RESEARCH.md)) but is **not**
  wired into `build-corpus` / `ingest_profiles`. Identity risk (name order,
  homonyms, 0 existing `senat_guid` identifiers) must be cleared with a
  copy-DB impact report first (decision D3).
- **Coverage is one-dimensional.** "Full for all 20 scopes" describes the
  **mandate** dimension only. The `votes` dimension is **none** in the
  published corpus and `biographies` is **partial**. Production `/api/votes`
  reports `data_exists: false, total: 0`; the vote tables exist only in local,
  gitignored working DBs and have never been released. The release pin is
  `data-20261117-T213500`.
- **Licence register is latent** — see [SOURCE-RESEARCH](SOURCE-RESEARCH.md).

## Vote fixtures — byte-exact and hashed

`tests/fixtures/votes/` holds captured cdep.ro and external civic-source
snapshots used by the importer's contract tests:

- `scripts/capture_vote_fixtures.py` captured them **byte-exact** on
  **2026-11-20** with a polite client, robots honoured and no CAPTCHA bypass.
- `manifest.json` stores source URL, byte count, HTTP status and **SHA-256**
  for every file; the importer aborts if a file and its manifest entry
  disagree. The 404 body for `/api/votes/37526` is stored deliberately to
  prove that route does not exist.
- The anchor vote `37526` reconciles across three views: day index
  (`PREZENTI` 246, 1 not voting, 245 yes), nominal XML (246 rows) and the
  external cross-check CSV — with the raw token `-` meaning **present but did
  not vote**, not abstain. Literal `NU` and `AB` tokens and day-level
  `CAMERA=1` remain UNVERIFIED with named capture resolvers.

## Identifier-only identity resolution

No name matching, no fabrication. Order: `cdep_mandate`
(`<chamber>:<leg>:<idm>`), then `cdep_idm` (`<idm>` + legislature) **only** if a
mandate exists in that chamber/legislature, then `cdep_person` (same mandate
check), otherwise quarantine. Against the shipped corpus on vote 37526
(246 positions):

| Outcome | Count |
|---|---:|
| resolved via `cdep_mandate` | **146** |
| resolved via `cdep_idm` (mandate check passed) | **98** |
| resolved via `cdep_person` | 0 |
| unresolved / quarantined | **2** |

`idm=87` is absent from the person table; `idm=106` is rejected by the mandate
check. Both are recorded in the import report and never become new `person`
rows. A name matching more than one HTML row is ambiguous → quarantined. The
HTML page prints surnames first, the XML given names first; the join uses
normalized `NUME + " " + PRENUME`, yielding 246/246 for the anchor vote. The
group label differs for 20 of 246 rows, so group is **not** part of the join
key and both raw values are retained.

## Encoding trap

The XML prolog declares `encoding="ISO-8859-2"`, but the server sends
`Content-Type: text/xml; charset=UTF-8` and the **bytes are UTF-8**: the UTF-8
sequence `c4 83` ("ă") is present while the latin-2 byte `e3` is absent.
Trusting the prolog produces mojibake. **Rule:** decode UTF-8 first, fall back
to ISO-8859-2, never trust the prolog. The CSV export similarly begins with a
UTF-8 BOM and must be read as `utf-8-sig`.

## Open items and resolvers

- Senate-only sitting `CAMERA=1`, nominal tokens `NU`/`AB`, and other `par1`
  values: capture a matching source page.
- Test vote `37515` ("Vot test 1"): written sign-off before any production
  backfill.
- `vot-parlament` "stable API": there is none (HTTP 404); assert the CSV header
  plus JSON key shape and return `DATA_UNAVAILABLE` on drift.
- EP/PACE/Eurostat/EC ingestion requires an explicit data-release decision, not
  just code.
