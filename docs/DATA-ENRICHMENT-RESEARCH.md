# Data Enrichment Research — External Sources and a Practical Roadmap

> **Execution plan:** this document is the evidence base. The waves, phases,
> action points, checkpoints and fail-safe rollbacks built from it are in
> [`docs/MASTER-STRATEGY.md`](MASTER-STRATEGY.md).

**Date:** 2026-11-20
**Status:** research + recommendation only. **No code, database, schema, pipeline or CI file was changed by this research.**
**Audience:** maintainers of Parlament Deschis, including non-programmers. Every technical term is explained the first time it is used.

**Purpose.** Answer two questions:

1. What public data exists about the Romanian Parliament (Camera Deputaților and Senat) from 1990 to today, including European and international sources?
2. Given the code and database we actually have, what is the *most recommendable* way to ingest and enrich it so this becomes a 10× better statistical platform — without breaking the project's evidence and verification rules?

This document supersedes the stale parts of `docs/RESEARCH.md` (dated 2025-11-12). Read the two together: that file documents the original design; this one records what is actually true today and what to do next.

---

## 0. Executive summary (read this first)

**The good news:** the core of the project is stronger than its own docs admit. The shipped database (`data/parlament-real.db`) already contains **both chambers, all 10 legislatures**, with 3,388 people, 5,273 mandates, 7,349 memberships and 7,429 events. Every membership has a source URL and an archived-page hash. That is a solid backbone.

**The real gaps are not "which MPs existed" but "what else can we say about their activity":**

| Gap | What it costs us today | Best free source to fix it |
| --- | --- | --- |
| No votes in the database | Cannot measure how an MP *actually voted*, only group changes | cdep.ro per-day XML (official, machine-readable) + `vot-parlament.ro` for both chambers |
| 275 people have no birth date | The age/generational statistics lose ~8% of people | cdep.ro birth-month tables (official, 3,165 rows) |
| 0 Wikidata IDs in the shipped database | No stable cross-reference to the wider world | Existing `pipeline/enrich.py` exists but is **not run** by the daily workflow |
| No education / profession / birthplace | Cannot compare MPs by background | Global Legislators Database (CC0), SER-PROM XLSX, cdep profiles, Politoscop |
| No party ideology / populism context | Cannot explain *why* switching clusters happen | CHES, V-Party, PopuList, ParlGov, PPEG via Party Facts IDs |
| No election results / constituency denominator | Cannot relate an MP to their electoral base | AEP datasets on data.gov.ro (CSV/XLSX, CC-BY/OGL) |
| No statistical benchmarks | Cannot tell if a number is unusual | IPU, World Bank `SG.GEN.PARL.ZS`, INS TEMPO, Eurostat, EC 1990–2024 table |

**The single highest-value upgrade:** add **roll-call votes** as first-class dated events. That turns a "party-switch tracker" into a "parliamentary behaviour statistics platform" and makes existing features (party cohesion, switch waves, committee control) far more meaningful.

**The single easiest upgrade:** wire the already-written Wikidata enrichment into the daily data workflow and fill birth dates from cdep's own birth-month tables.

**A critical warning:** several excellent sources are **non-commercial only** (IPU, OpenSanctions) or **ShareAlike** (V-Dem, some academic sets). They are fine for *checking* our numbers, but their rows must not be copied into our CC-BY dataset. Section 5 gives the exact rules.

---

## 1. What the project actually contains today (verified, not assumed)

Measured directly from `data/parlament-real.db` on 2026-11-20:

| Table | Rows | Note |
| --- | ---: | --- |
| `person` | 3,388 | — |
| `mandate` | 5,273 | Both chambers, all legislatures |
| `membership` | 7,349 | Every row has source URL + SHA-256 evidence |
| `event` | 7,429 | join 5,282 · switch_group 1,217 · leave 924 · group_founded 6 |
| `organization` | 120 | chambers, groups, parties, committees, bureaus |
| `person` with no `birth_date` | **275** | ~8% of people |
| `person` with `wikidata_qid` | **0** | See finding F3 below |
| `person_identifier` schemes | `cdep_mandate` 3,381 · `cdep_person` 3,381 · `cdep_idm` 335 | No Wikidata, Senate-GUID or external IDs |

Mandates by chamber and legislature (proof that both chambers are really present — this contradicts the older docs):

| Legislature | Deputies | Senate | Legislature | Deputies | Senate |
| --- | ---: | ---: | --- | ---: | ---: |
| 1990 | 447 | 126 | 2012 | 416 | 179 |
| 1992 | 381 | 160 | 2016 | 361 | 136 |
| 1996 | 367 | 154 | 2020 | 354 | 151 |
| 2000 | 393 | 163 | 2024 | 336 | 132 |
| 2004 | 378 | 163 | | | |
| 2008 | 339 | 137 | | | |

### Architecture facts that matter for enrichment

- `pipeline/db.py` uses SQLAlchemy with a **Popolo-style model**: `Person`, `Organization`, `Post`, `Mandate`, `Membership`, `Event`, `Evidence`, `Fragment`, `Coverage`, `PipelineRun`, plus a `match_review` queue.
- `person_identifier` already has a `scheme` field; its own code comment lists `cdep_idm / senat_guid / ep_uuid / wikidata`. **The hooks for external IDs already exist.**
- `organization` already has `classification` (`chamber`, `group`, `party`, `committee`, `bureau`, `delegation`, `friendship`, `other`), `alt_labels`, `previous_party_id` and `successor_party_id` for party genealogy.
- `event` has a unique `dedup_key` — ideal for idempotent ingestion of votes, speeches or election results from a second source.
- `fragment` stores raw source data with `source_name`, `source_id`, `source_url`, `checksum`, `snapshot_path` — **this is the natural landing zone for every new source**, so original evidence is never lost.
- `evidence` has types `official_ledger`, `profile`, `jo`, `intervention`, `scrutin`, `other`. New types (e.g. `vote`, `speech`, `benchmark`) can be added as strings.
- `pipeline/sources/client.py` provides `PoliteClient`: identifying User-Agent, robots.txt honoured, per-host pacing, conditional GET (ETag/Last-Modified), exponential backoff, 429 waiting, and a **hard stop on CAPTCHA** (never bypassed). Every new source must use this client.
- `pipeline/cli.py` builds the corpus with `build-corpus --chamber both --strict`, then ingests, cross-checks and audits. The daily `.github/workflows/data.yml` runs this, publishes an immutable dataset release, pins `data/latest-release.txt`, triggers Render explicitly, and verifies the deployed release tag.
- `backend/routers/api.py` exposes REST endpoints; `backend/graphql/schema.py` exposes GraphQL; analytics endpoints already exist for switch waves, party cohesion, cross-chamber careers, committee control and generational shift. `frontend/src/api/client.ts` calls them.

### Findings from this code analysis

- **F1 — The Senate "gap" in the docs is stale.** Both chambers, all legislatures, are in the shipped database. Do not re-ingest the Senate from scratch. What is missing is *detail* (votes, speeches, committee histories with dates, biographies).
- **F2 — `coverage` says `full` for all 20 scopes.** Good, but it only describes mandates/memberships. It should be extended or complemented to describe new dimensions (votes, biographies, committee history) so the `/api/coverage` endpoints tell the truth about what is and is not in the release.
- **F3 — `enrich.py` writes QIDs and birth dates with `--apply`, but `build-corpus` and `data.yml` never call it.** That explains 0 QIDs. The code is not broken; it is simply not scheduled.
- **F4 — There is no `vote`, `vote_position`, `speech`, `election_result`, `party_score`, `benchmark` or `context_year` table.** These are the concrete additions that would produce the "10×" statistical upgrade.
- **F5 — `docs/RESEARCH.md` has incorrect robots.txt facts** (see §4). It also says senat.ro has no historical discovery path; live checks disagree. Treat that file as historical context only.

---

## 2. Red-team results: what earlier research got wrong

Eight research agents were explicitly instructed to *disprove* the earlier findings. Verdicts:

| Earlier assumption | Verdict | Corrected understanding |
| --- | --- | --- |
| "No single source covers both chambers + 1990–today + votes + committees + events + citations" | **Holds as written**, but a narrower version is broken | `vot-parlament.ro` covers both chambers + votes + official source links from **2006**, but no committees and no 1990s. |
| "1990–1996 is a data dead zone" | **Broken** | SER-PROM XLSX datasets with DOIs (1990→2012), archived official cdep rosters from 1990, Romanian Wikipedia lists with 99–100% Wikidata IDs and >92% birth dates, 281.ro JSON for 1990/1992, Zenodo speech corpus from 1996. Only **1990s votes** remain genuinely thin. |
| "Senate is systematically underserved / `scrape_senat.py` is a stub" | **Partly broken** | Structured Senate data exists (281.ro JSON 1990–2024, Senate votes 2006–2026, 545 Senate sessions in the ParlaMint pipeline, Senate speeches from 2001). The literal file name could not be found in any public Romanian project — that claim was unsourced. |
| "281.ro has no verifiable license" | **Broken as phrased** | The GitHub repo is genuinely 404 (the user has 0 public repos), but CC-BY 4.0 is declared verbatim on `/despre`, `/api`, `/metodologie` and the footer, with a required attribution string. Correct phrase: *self-declared CC-BY 4.0, unbacked by a published repository*. |
| "No dataset contains Romanian MP-level data" | **Broken** | Global Legislators Database (CC0, Harvard Dataverse) contains **329 named Romanian deputies from 2016**, verified by downloading the actual data file. |
| "Comparative Legislators Database excludes Romania" | **Survives** | Verified against CLD's 16-country list, `legislatoR` docs and CRAN vignette. |
| "cdep robots.txt disallows `/ords/`, Crawl-delay 5" | **Wrong** | Live file is exactly 37 bytes: `User-agent: *` / `Disallow: /declaratii/`. No `/ords/` rule, no crawl-delay. |
| "senat robots.txt has Crawl-delay 10" | **Wrong** | `https://www.senat.ro/robots.txt` returns **404** today. |
| IPU API filter syntax | **Both earlier agents were right** | `filter[]=field:op:value` works; `filter[field]=...` is silently ignored (returns all 2,981 records). |
| "gov2.ro is an official government project" | **Wrong** | The site itself says *"Acesta NU ESTE un proiect oficial al Guvernului României"*. |
| "`cdep.ro/api/v1/deputati` is an official API" | **Wrong** | 404. The "API Deschis" is a third-party GitHub-Pages proof of concept. |

---

## 3. Full source inventory

Legend: **Official** = primary publisher · **Derived** = someone else's consolidation of official data · **Academic** = research dataset · **Aggregate** = statistics, not named people.
License shorthand: **CC-BY** = free reuse with credit · **CC0** = public domain dedication · **OGL** = Open Government Licence · **NC** = non-commercial only · **SA** = ShareAlike · **NC-SA** = both.

### 3.1 Official — Camera Deputaților (`www.cdep.ro`, both chambers via `cam=1`/`cam=2`)

The chamber's own site is our primary source. Most endpoints are legacy HTML with Romanian diacritics; the one real machine-readable feed is the vote XML.

| Source | Exact URL pattern | What it gives us | Years | Format | License / caution |
| --- | --- | --- | --- | --- | --- |
| MP directory, profiles, cross-legislature matrix | `structura2015.home?leg=YYYY`; `structura2015.mp?idm=N&cam=2&leg=YYYY`; `structura2015.de?leg=YYYY&par=X` | Name, birth date, constituency, party/group, bureau and committee roles, activity counts, all past mandates. `idm` is per-mandate, so identity must be resolved via the mandate graph, never by name | **1990–today** (1990–92 body = "Adunarea Deputaților") | HTML, ISO-8859-2 on some legacy paths | Site notice: non-commercial, with attribution — see §5 |
| **Electronic votes** | `evot2015.xml?par1=1&par2=YYYYMMDD`; `evot2015.nominal?idv=VOTID&idl=1`; `evot2015.zile_vot?lu=MM&an=YYYY` | Per-day vote list with counts (present, yes/no/abstain/did-not-vote) and per-MP choice with party group at vote time | **~2006–today** | **XML** (ISO-8859-2) + HTML | The only genuinely machine-readable official feed. Highest priority |
| Legislative initiatives | `upl_pck2015.home`; `upl_pck2015.proiect?idp=NNNNN` | Bill initiators by party/chamber, dated procedure timeline, final vote results | 1996–today | HTML + PDF | Site says this database is "nu are caracter oficial" — evidence, not legal truth |
| Stenograms / agendas | `steno2015.home`, `steno2015.calendar?cam=2&an=YYYY`, `steno2015.data?...`, `steno2015.cautare?leg=YYYY` | Session agenda with outcomes, link to Official Gazette transcript, video | **Feb 1996–today** (no 1990–96) | HTML + PDF + video | Citations and speech events |
| Questions / interpellations | `interpelari2015.home` | MP questions and interpellations by year, addressee, keyword | 1997–today | HTML | Freshness label on old page is contradictory |
| Motions, committees, agendas, sanctions | `motiuni2015.home`, `sedinte2015.comisii`, `upl_com2015.home`, `ecaseta2015.OrdineZi`, `sanctiuni_parlam.lista_sanctionati` | Motions, committee sittings and documents, order of the day, sanctions | Mostly 2001–today | HTML + PDF | — |
| Asset / interest declarations | `declaratii2015.home`; PDFs at `/declaratii/deputati/{leg}/{avere\|interese}/nnn.pdf` | Wealth and interests, multiple filings per MP | Only **2020–today** on this portal | HTML + PDF | ⚠️ `robots.txt` **disallows `/declaratii/`** — do not bulk crawl |
| Birth-month tables | `structura2015.de?leg=YYYY&par=V01` … `par=V12` | "Data nasterii" for every deputy, by legislature | **1990–today** | HTML | Official and complete; best source for the 275 missing birth dates |
| Sitemap / open data | `sitemap.xml` → 404 | — | — | — | **No open-data portal, no JSON/CSV/RDF API, no bulk export** except the vote XML |
| Electronic services portal | `servicii-electronice.cdep.ro` | Petitions | — | Web portal | Down for maintenance on 2026-11-20 |
| Wayback legacy site | e.g. `web.archive.org/web/20060207121411/http://www.cdep.ro/pls/parlam/structura.de?leg=1990&cam=2&par=A` | Full 1990–92 rosters with party, county and mandate-end dates (387 deputies, 106 senators) | 1990s | Archived HTML | Live URLs now 404; archive is the only route |

### 3.2 Official — Senatul României (`www.senat.ro`)

| Source | Exact URL pattern | What it gives us | Years | Format | License / caution |
| --- | --- | --- | --- | --- | --- |
| Senator directory | `FisaSenatori.aspx` | Searchable cards with GUID links; filters by legislature/session/chamber | 1990–today | ASP.NET HTML (POST filters) | No reuse licence stated |
| **Senator profile** | `FisaSenator.aspx?ParlamentarID=<GUID>` | Exact mandate dates, party group + role, dated committee/bureau history, activity counters, declarations | 1990–today (early records patchy) | HTML | GUID is stable; duplicate-name profiles exist — disambiguate carefully |
| Parliamentary groups | `EnumGrupuri.aspx`; `ComponentaGrupuri.aspx?GrupID=<GUID>` | Dated rosters with "including those who left" — the best official signal for party switches | 1990 (FSN) → today | HTML | Historical GUID enumeration is brittle |
| Committees | `EnumComisii.aspx?Permanenta=1`; `Comisie_new.aspx?ComisieID=<GUID>&Zi=` | Committee lists, membership, agendas, documents | 1990–today | HTML | — |
| Nominal votes | `VoturiPlen.aspx`; `VoturiPlenDetaliu.aspx?AppID=<GUID>` | Per-senator votes with group at vote time | Verified 2025–26; earlier unverified | HTML | — |
| Bills | `legis/lista.aspx`; `legis/PDF/YYYY/YYLnnnXX.PDF` | Dated procedure timeline + PDF document trail | 1990–today | HTML + PDF | Excellent citation chain |
| Questions, declarations, stenograms, video | `VizualizareIntrebariInterpelari.aspx`, `DeclaratiiAvere.aspx`, `StenoPag2.aspx`, `live.aspx` | Events, PDFs, transcripts, video | Mostly recent | HTML + PDF | Declarations kept online ≥3 years only |
| Sitemap, legislative bulletin | `sitemap.xml`; `UploadFisiere/<GUID>/Buletin legislativ ...pdf` | GUID discovery; per-session PDF snapshot of all bills | Current | XML + PDF | `robots.txt` is 404 |
| Senat Online | `online.senat.ro/portal` | FOIA requests and **requests for archived documents** ("retrodigitalizare") | — | Portal, login required | Fallback channel, not a dataset |

### 3.3 Romanian national public-sector sources

| Source | Exact URL / API | What it gives us | Format | License | Caution |
| --- | --- | --- | --- | --- | --- |
| **data.gov.ro (CKAN API)** | `https://data.gov.ro/api/3/action/package_search?q=...`; `organization_show?id=autoritatea-electorala-permanenta&include_datasets=true`; `package_show?id=<slug>` | Election results and mandate allocation by constituency for 2012, 2016, 2020; 2024 candidates/mandates from ANES; 2009 referenda on unicameralism and a 300-MP cap | CSV, XLS, XLSX | OGL-ROU-1.0 (older), **CC-BY 4.0** (2020+) | No dataset of named MPs, switches or committees. Some resources flagged broken |
| AEP election databases | `roaep.ro/prezentare/baze-de-date-alegeri-electorale/`; 1990 archive `roaep.ro/alegeri_1990/index.html`; 2024 protocols | 1990/1992/2012/2016/2020/2024 election files | CSV, XLS, PDF | Not stated on AEP site | ⚠️ Whole site behind reCAPTCHA — prefer data.gov.ro mirrors |
| Monitorul Oficial | `monitoruloficial.ro`; free e-monitor from 2000 | Primary legal record: appointment acts, election protocols, transcripts in Part II | PDF | **No reuse licence**, paid archive pre-2000 | Cite as evidence; do not redistribute |
| INS statistics | TEMPO Online `http://statistici.insse.ro:8077/tempo-ins/matrix/TSS1661` (parliament by sex, Total/Senat/Camera, 2008+); `POP105A` population by age/sex/region | Statistical denominators and an official gender series | JSON API (POST required), CSV/XLS | Attribution only, not an open licence | Exact POST body not fully verified |
| ANI declarations | `declaratii.integritate.eu`; archive `old-declaratii.integritate.eu` | Asset/interests to ~2022 | HTML, CSV, PDF | Personal-data constraints | Public publication stopped after a 2025 Constitutional Court decision |
| Political financing | `finantarepartide.ro` | Party subsidies and fiscal register | PDF | Not stated | reCAPTCHA; party-level, not MP-level |

### 3.4 Civic tech and independent aggregators (the closest analogues to our project)

| Source | URL / API | What it gives us | Years | Format | License | Relevance |
| --- | --- | --- | --- | --- | --- | --- |
| **vot-parlament.ro** ⭐ | `/votes`, `/bills`, `/politicians`, `/groups`, `/ce-urmeza`, `/metodologie`, `/data`; `/votes/export.csv?chamber=senat&...`; `/votes/{id}.json` | **36,103 votes, 6,893,607 nominal positions, 17,401 bills**, both chambers + joint sittings, each vote linked to the official cdep/senat page; documented gaps | **6 Feb 2006 – 18 Nov 2026** | HTML + filtered CSV + per-vote JSON | **CC BY 4.0** | Best vote source. No full bulk dump yet. Separates "current group / party / ballot label" — copy that methodology |
| **281.ro** ⭐ | `/api/index.json`, `/api/bulk/mps.csv`, `/api/bulk/bills.csv`, `/api/senators/{leg}.json`, `/api/deputies/{leg}.json`, `/errata/` | 3,546 MP×legislature rows, both chambers; JSON endpoints reach 1990; bills, wealth, interests, some reconstructed votes | Site claims 1990–2028; bulk CSV 2000–2024 | Static JSON + CSV + RSS | **Self-declared CC BY 4.0**; GitHub repo is 404 | Excellent cross-check. Pre-2000 records shallow (`party` empty for 1990–96 senators). Read `/errata/` before trusting any field |
| **lab.gov2.ro/cdep** (`Endimion2k/cdep-api-poc`, `gov2-ro/cdep-stats`) | `lab.gov2.ro/cdep/llms.txt`, `/cdep/data/v1/*.json`, GitHub repos | Static JSON: deputies, nominal votes, 9,758 interpellations, 162 motions (1992–2024), ~85,895 committee docs | 2016/2020/2024 mainly | JSON, Atom/JSON Feed | OGL v3.0 | **Not an official government project** despite the domain. Chamber only. README warns data is not 100% verified |
| **monitorul.ai** (`ciocan/monitorul-ii`) | `monitorul.ai`, `/politicieni`, `/statistici`, `/mcp`; GitHub `ciocan/monitorul-ii` | 535,688 speeches, 55,313 votes (counts only), 14,325 committee sittings, 13,479 persons, verbatim Gazette text with stable permalinks | **2000–today** | HTML permalinks, MCP server; bulk by request | Code AGPL-3.0; public text is official; derived dumps CC BY 4.0 | Best source for events and citations. No public bulk dump; vote `nominal_breakdown` is hard-coded empty |
| Zenodo 3332908 | `doi.org/10.5281/zenodo.3332908` | ~1 GB of speeches, **both chambers** (Senate from Jan 2001), speaker-profile URLs | **1996–2019** | CSV (`CDEPs2.csv` 506 MB, `validated-1.csv` 498 MB), plain text | **CC BY 4.0** | Fixes both the 1990s and Senate speech gaps |
| ELRC corpora | data.europa.eu `ELRC_2545`, `ELRC_1245` | Processed transcripts from cdep.ro, 500k+ sentences | 1996–2018 | ZIP text | Public catalogue record | Near-duplicate of Zenodo 3332908 |
| `dmdafsm/parlament` | GitHub repo; `parlament.romdata.ro` (down 530) | Both chambers' members and initiatives, CSV/JSON API, RSS | From Oct 2026 | Python/Postgres, CSV, JSON | MIT | Emerging, unstable; Senate nominal votes explicitly unavailable |
| Code for Romania | `rezultatevot.ro`, `istoric.rezultatevot.ro`, `romanian-elections-data` | Election results 1990–2025 and a backup of the fragile official live-results site | 1990–2025 | HTML, CSV, JSON | MPL-2.0 | Useful fallback for election data |
| Politoscop | `politoscop.ro` + PDF studies | Individual profiles from official parliamentary CVs: age at entry, education, doctorates, profession | 2016–2024 | HTML + PDF | Site terms | Rich for the recent legislatures; not machine-readable |
| Expert Forum | `expertforum.ro/migratie-candidati-parlamentare-2024` + PDF | Transition matrices for candidate migration/traseism 2016–2024 | 2016–2024 | PDF tables | Site terms | Best qualitative traseism cross-check; not a dataset |
| România Curată / IPP / TI Romania | `romaniacurata.ro/lista-parlamentari-mandat-2024-2028`, `ipp.ro/parlament/`, `transparency.org.ro` | 2024 elected-member lists, monitoring reports, integrity context | Mostly 2024 | HTML, PDF | Standard copyright | Cross-check and citations only |
| Party sites | `usr.ro/organizatie/parlamentari` etc. | Current party rosters | Current | HTML | — | Cross-check only |

**Dead / unverified domains — do not build on them:** `senatori.ro`, `alegeri.ro`, `politici.ro`, `alesiivoteaza.ro` (403), `date.gov.ro` (503), `opendata.gov.ro` (dead), `parlament.romdata.ro` (530), `prezenta.roaep.ro` (unreliable/bot-checked), EveryPolitician Romania (empty, archived), Kaggle/Figshare/Hugging Face (no Romanian parliament dataset).

### 3.5 European resources with Romanian Parliament links

| Source | Exact URL / endpoint | What it gives us | Years | Format | License | Relevance |
| --- | --- | --- | --- | --- | --- | --- |
| **European Parliament Open Data API v2** ⭐ | `https://data.europarl.europa.eu/api/v2/`; `/meps?country-of-representation=RO&format=application/ld+json&limit=1000`; `/meps/show-current?...`; `/meps/{id}`; `/corporate-bodies/{id}` | **146 Romanian MEP records** (33 current), `bday`, gender, birthplace, exact membership start/end dates, national-party links (`org/4135` = PSD, `org/6709` = PNL), committee/delegation roles | Terms 6–10 (**2004–today**); terms 1–5 return 204 (Romania not yet in EU) | JSON-LD / RDF / TTL | **CC BY 4.0**, 500 req / 5 min | Best free source for a stable MEP ↔ national party crosswalk |
| EP bulk files | `https://data.europarl.europa.eu/distribution/meps_{term}_{version}_{lang}.csv`; `meps_10_22.ttl` (16.6 MB), `.rdf` (18.3 MB) | Full MEP lists per term | 2004–today | CSV, TTL, RDF | CC BY 4.0 | ⚠️ CSV has **no national-party column** — use API/RDF for that |
| **data.europa.eu API hub** | `https://data.europa.eu/api/hub/search/`; `/datasets/{id}`; `/ckan/package_search` | Searchable EU catalogue. `ELRC_2545` transcripts 1996–2018; harvested AEP election data; Eurostat `sdg_05_50`; 2009 unicameral and 300-MP referenda | 1996–2025 | JSON, CSV, SDMX | Per dataset | `https://data.europa.eu/api/3/action/package_search` is a **404** — use the hub API |
| EP election results datasheets | `https://results.elections.europa.eu/data-sheets/json/2024-2029/election-results/ro.json` (also 2019, 2014, 2009; `2004-2009/outgoing-parliament/ro.json`); CSV equivalents; `.sig` signatures | Romanian parties, votes %, seats, party→group→MEP breakdown | 2009–2024 (+ 2007 outgoing) | JSON, XML, CSV | Official | No 2007 election file (Romania joined 1 Jan 2007) |
| **Council of Europe / PACE** ⭐ | `https://pace.coe.int/en/aplist/countries/34/romania`; member pages e.g. `/en/members/6463/stroe` | **10 representatives + 10 substitutes**, with national party and **chamber secretariat** (Camera Deputaților / Senatul României), dated mandates and committee roles | Current + historical | HTML | Official | Excellent independent cross-check of chamber, party and career dates |
| Venice Commission | `venice.coe.int/webforms/documents/?country=25&year=all`; `CDL-PI(2025)001` on the 2024 election cancellation | Opinions on Romanian election law, thresholds, ordinances | 2004–2025 | PDF | Official | Context and citation events |
| GRECO | `coe.int/en/web/greco/evaluations/romania`; `GrecoRC5(2025)11` | Fourth Round explicitly covers **members of parliament**; 26 recommendations in 2025 report | 2018–2025 | PDF | Official | Integrity context |
| EPRS | `europarl.europa.eu/thinktank/...`; briefing PE 630.313 (Romanian Presidency, describes bicameral system), PE 760.348 (women in politics), IPOL STU(2017)583126 (RO1 and RO2 opinions) | Institutional context, chamber comparison, historical MEP composition | 2017–2025 | PDF, HTML | Official | Useful for documentation and benchmark context |
| Eurostat API | `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{code}?format=JSON&geo=RO&lang=en` | `sdg_05_50` women in parliaments 2003–2025; `demo_pjan`, `demo_r_d2jan`, `demo_r_pjanaggr3`, `edat_lfse_03`, `tps00001` | 1960–2025 | JSON-stat, SDMX, CSV | **CC BY 4.0** | Population/age/education denominators by region |
| ESS / EVS | `europeansocialsurvey.org/about/country-information/romania`, `romanianvalues.ro/databases` | Mass-public surveys, Romania waves 1993–2019 | 1993–2019 | SPSS/Stata | Academic | **No MP/political-elite module found** — do not expect MP data |
| EUR-Lex / OEIL | `eur-lex.europa.eu/collection/n-law/mne.html`, `oeil.europarl.europa.eu` | National transposition notices; EP resolutions mentioning both Romanian chambers (e.g. P8_TA(2018)0213) | 1990s–today | HTML, PDF | Official | No bulk per-chamber position dataset. TFEU Protocol 1 confirms each chamber of a bicameral parliament has one vote — useful for modelling RO1/RO2 separately |

### 3.6 International and academic datasets

| Source | URL / DOI | What it gives us | Granularity | Format | License | Relevance |
| --- | --- | --- | --- | --- | --- | --- |
| **Global Legislators Database (GLD)** ⭐ | `doi:10.7910/DVN/U1ZNVT` (replication `DVN/KGYJFJ`), BJPS 2025 | **329 named Romanian deputies from the 2016 election**, verified directly in `global_legislator_database.tab`: `dob`, `gender`, `party`, `education`, `last_occupation`, `isco08`, source fields | **Individual MP**, single snapshot | TAB, codebook | **CC0** | Highest-value ready-made biographical dataset |
| Wikidata SPARQL | `https://query.wikidata.org/sparql`; items `Q17556530` (deputy), `Q19938957` (senator); IDs `P9523` (Senate), `P9524` (Chamber) | 3,600 persons with either position; **3,492 DOB (97%)**, 1,238 education (34%), 2,101 birthplace (58%), 293 in both chambers | Individual, crosswalk | SPARQL JSON/CSV | **CC0** | Best identity crosswalk. `robots.txt` disallows bulk `/sparql` harvesting — use cached/dump flows |
| DBpedia | `https://dbpedia.org/sparql` | 722 Romanian MPs in two categories; 442 birth dates (61%) | Individual | RDF/SPARQL | CC BY-SA 3.0 | Supplementary only |
| OpenSanctions | `opensanctions.org/datasets/ro_cdep_deputies/`, `/ro_senate`; bulk `data.opensanctions.org/datasets/latest/.../index.json` | 1,470 deputies (1,446 with DOB) + 231 senators (230 with DOB), monthly, Wikidata-linked | Individual, recent terms | FTM JSON, CSV, API | **CC BY-NC 4.0** | **Cross-check only.** "Since 1990" claim is not supported by the data (occupancies 2020–2026) |
| ParlGov / PPEG | `parlgov.org/data-info`; `ppeg.wzb.eu`; `doi:10.7910/DVN/5OAH7P` | Romanian parties/elections 1990–2024; PPEG 43 parties, 10 elections, 127 observations | Party/election | CSV, SQLite, XLSX | CC0 (ParlGov) | Party identity and ideology normalization |
| CHES (Chapel Hill Expert Survey) | `chesdata.eu/ches-europe`; 2024 CSV on GitHub releases | 7 Romanian parties in 2024; left-right, EU position, populism, democracy items | Party (expert-level too) | CSV, Stata | EUI archive CC BY 4.0 | Party covariates for switching analysis |
| V-Party v2 | `v-dem.net/data/v-party-dataset/country-party-date-v2/`; `doi:10.23696/vpartydsv2` | Populism, anti-pluralism, party organization indices for Romanian parties | Party-date | CSV, Stata, R | CC BY-SA 4.0 | Join by Party Facts ID |
| POPPA | `poppa-data.eu/data/`; `doi:10.7910/DVN/RMQREQ` | 0–10 populism score and components | Party | Stata, CSV | Academic, free | Party covariates |
| The PopuList | `popu-list.org`, OSF `2ewkq` | Populist / far-left / far-right / eurosceptic dummies for AUR, PSD, PMP, PRM, PUNR, PP-DD… | Party-year | Excel, CSV | Open | Simple, robust controls |
| Party Facts | `partyfacts.herokuapp.com`; `doi:10.7910/DVN/TJINLQ`; GitHub `h-digital/partyfactsdata` | Crosswalk IDs linking CHES, ParlGov, Manifesto, V-Party, POPPA and PopuList | Party | CSV | Free | **Use as the join key** to avoid party-name mismatches (FSN→FDSN→PDSR→PSD lineage) |
| V-Dem v13 | `v-dem.net/data/dataset-archive/`; `doi:10.23696/vdemds23` | Country-year democracy indices, party gender quotas | Country-year | CSV, Stata, R | CC BY-SA 4.0 | Contextual controls, not MP rows |
| CPDS / DPI / Polity 5 | `cpds-data.org/data`; `data.iadb.org` DPI 2023 (`doi:10.60966/8tx1xs4i`); `systemicpeace.org/inscrdata.html` | Effective number of parties, government changes, seats, checks, polarization, gender quotas, regime scores | Country-year | Stata, XLSX, CSV | DPI CC BY 4.0 | Contextual controls |
| IPU Parline | `data.ipu.org/parliament/RO/RO-LC01/`, `/RO-UC01/`; API `api.data.ipu.org/v1/documentation/json`; women 1945–2018 XLSX; age 2008–2026 XLSX | Chamber composition, 23 Romanian elections, age brackets by sex, % women, next election 30 Nov 2028 | Aggregate only | JSON:API, CSV, XLSX | **CC BY-NC-SA 4.0** | **Cross-check only.** No individual DOBs |
| World Bank WDI | `https://api.worldbank.org/v2/country/ROU/indicator/SG.GEN.PARL.ZS?format=json&date=1997:2025` | % women in parliament, 1997–2025, last updated 2026-11-11 | Country-year | JSON API | **CC BY 4.0** | Clean, licence-safe benchmark (lower house only) |
| European Commission paper | Băluță & Tufiș, `commission.europa.eu/document/download/e7d42e20-...pdf` | **The only single table with % women for both chambers and total for every legislature 1990–2024** | Legislature × chamber | PDF | EU document | Best like-for-like benchmark for a 1990+ project |
| SER-PROM (Tufiș / RQSA) ⭐ | `sites.google.com/site/rqsaro/projects/romanian-mps`; DOIs e.g. `10.13140/RG.2.1.3848.9762` (1990), `10.13140/RG.2.1.2115.8569` (1992); files on Google Drive still live | Six XLSX datasets + Romanian codebooks for 1990–92 … 2008–12 | Individual MP, per legislature | XLSX | Institutional page states **CC BY-SA 4.0** | Best hope for 1990–2012 biographies and short-tenure substitutes. Check licence compatibility before merging |
| Chiru & Popescu | OSU paper `kb.osu.edu/.../eb4c50ec-...` | "Romanian Parliamentary Candidates Study 1990–2012", machine-readable file mentioned | Candidate-level | Unknown | Academic | Access not verified — contact authors |
| WARP / age representation | `doi:10.1111/ssqu.13221` | Party-level youth representation, includes Romania | Party | Article | CC BY 3.0 | Benchmark method |
| INSTAPARTY | `instapartyproject.com`; Ibenskas et al., LSQ 2025 | Party-group instability events, Romania 1996–2020 — exactly "traseism" | Event-level | On request | Unknown | Topic-perfect but not openly downloadable |
| EurElite | Semenova/Edinger/Best (Routledge 2013), ch. 9 "Romanian parliament after 1989" | Occupational backgrounds, recruitment and career variables | Individual (book tables) | PDF | Academic | No bulk download |
| Free datasets that **exclude** Romania | Comparative Legislators Database, ParlSpeech V2 (`doi:10.7910/DVN/L4OAKN`), Committee Membership Dataset (`doi:10.7802/2940`), Parliaments Day-by-Day | — | — | — | — | Verified exclusions — do not spend time on them |

---

## 4. Request etiquette and the stale robots.txt facts

**Exact live bytes, verified 2026-11-20:**

```
https://www.cdep.ro/robots.txt   (HTTP 200, 37 bytes)
User-agent: *
Disallow: /declaratii/
```

No `/ords/` rule. No crawl-delay. The `/declaratii/` path (wealth and interest declarations) is off-limits to crawlers; the group ledgers and profiles under `/ords/pls/parlam/` are **not** disallowed.

```
https://www.senat.ro/robots.txt  → HTTP 404
```

No robots file exists. That is not permission to be impolite: keep the existing 2.5 s pacing, identifying User-Agent, conditional GET, backoff and CAPTCHA hard-stop in `PoliteClient`.

`docs/RESEARCH.md` quotes older robots files with `/ords/` disallowed and `Crawl-delay: 5` / `10`. Those snapshots are from 2025-11-12 and are **no longer accurate**. Keep the file for history, but do not use it to decide what to crawl.

**IPU API correction:** use `filter[]=field:op:value` (or `filter=field:op:value`). The documented `filter[field]=value` form is silently ignored by the backend.

---

## 5. Licensing: what we may put in our CC-BY dataset

Our code is AGPL-3.0-or-later; our generated data is published as **CC-BY-4.0** ("Parlament Deschis"). The legal position, based on Romanian law read on 2026-11-20:

- **Constitution art. 31(1):** "Dreptul persoanei de a avea acces la orice informație de interes public nu poate fi îngrădit."
- **Law 8/1996 (copyright), art. 9:** explicit exclusion from copyright protection for *"textele oficiale de natură politică, legislativă, administrativă"* (lit. b), *"știrile și informațiile de presă"* (lit. e) and *"simplele fapte și date"* (lit. f). Names, dates, party affiliations and committee memberships are **facts**, not protected expression. A site footer cannot create copyright where the statute denies it. **Confidence: HIGH.**
- **Law 179/2022 art. 11:** reuse conditions must be objective, proportionate and non-discriminatory; art. 11(4) and the data.gov.ro licence page **recommend CC BY 4.0** for this category. A blanket non-commercial bar on official parliamentary facts is hard to defend as proportionate. **Confidence: MEDIUM-HIGH.**
- cdep.ro's "MENȚIUNE JURIDICĂ" claims exclusive ownership of text and multimedia elements (logos, images, audio, video, photographs) and allows reproduction "only for non-commercial purposes, with attribution". That notice attaches to its **creative assets**, not to unprotected facts. **Confidence: MEDIUM-HIGH** that the facts prevail in a dispute; no Romanian case law was found.

**Practical rules for this project:**

| Source category | Verdict | Rule |
| --- | --- | --- |
| cdep.ro / senat.ro facts (names, dates, party, committees, votes) | **SAFE** | Attribute the source; keep our own derived structure. Do not copy their layout/database arrangement |
| AEP / data.gov.ro election results | **SAFE** | Explicit CC BY 4.0 / OGL with attribution and personal-data care |
| Wikidata structured data | **SAFE** | CC0; record the QID anyway |
| 281.ro published data | **SAFE** | Self-declared CC BY 4.0; cite 281.ro and its errata page |
| GLD, ParlGov, World Bank, Eurostat, EP Open Data | **SAFE** | CC0 / CC BY 4.0 |
| Zenodo 3332908, ELRC, monitorul.ai public-document text | **SAFE** | CC BY 4.0 / public official documents |
| SER-PROM institutional licence | **CHECK FIRST** | Stated CC BY-SA 4.0 — ShareAlike may be incompatible with our CC-BY output if we copy values. Safest: use it as a cross-check, or seek permission for CC-BY release |
| IPU Parline | **CROSS-CHECK ONLY** | CC BY-NC-SA 4.0 — NC + SA incompatible with CC-BY |
| OpenSanctions | **CROSS-CHECK ONLY** | CC BY-NC 4.0 |
| V-Dem, V-Party, CHES (some files) | **CROSS-CHECK / CHECK PER FILE** | CC BY-SA 4.0 or EUI CC BY 4.0 archive — prefer the CC BY archive copies |
| parlament.openpolitics.ro | **CROSS-CHECK ONLY** | Site unreachable on 2026-11-20; licence unverifiable |
| Monitorul Oficial, ANI declarations, AEP site | **CITATION ONLY** | No open licence, PDF-only, personal-data constraints |

**Always keep out of the CC-BY output:** home addresses, private emails, family financial details, `/declaratii/` content, photos/logos/audio/video, and any field where the source licence is unverified.

---

## 6. Recommended enrichment roadmap (ordered by value ÷ effort)

Each phase states what to add, where it fits in the existing code, and how a non-programmer can sanity-check it.

### Phase 0 — Fix the truth layer first (½ day, almost zero risk)

1. Add a short note at the top of `docs/RESEARCH.md` pointing to this file and marking its robots facts as historical.
2. Extend `Coverage` (or add a simple `coverage_dimension` table) so `/api/coverage/detailed` distinguishes **mandates: full** from **votes: none**, **biographies: partial**, **committee history: partial**. Right now "full for all 20 scopes" could be read as "everything is complete", which is not true.
3. Add the identifier schemes we will use to `person_identifier`: `wikidata`, `senat_guid`, `gld`, `ep`, `partyfacts`. The column already exists — no schema migration needed, just new values.

**Sanity check:** `/api/coverage/detailed` should visibly show votes as not yet ingested.

### Phase 1 — Vote events (the 10× move) (2–4 weeks)

**Why:** votes turn "who changed group" into "how did Parliament actually behave". It powers party cohesion based on real divisions, attendance-at-vote context, an MP-level voting record, and event citations back to the official page.

**Sources, in order:**
1. `cdep.ro` per-day XML — official, machine-readable, ~2006–today. One file per sitting day; fields `VOTID, TIME_VOT, DESCRIERE, CAMERA, PREZENTI, NU_AU_VOTAT, AU_VOTAT_DA, AU_VOTAT_NU, AU_VOTAT_AB`. Nominal choice comes from `evot2015.nominal?idv=...`.
2. `vot-parlament.ro` — both chambers + joint sittings, already normalized, CC BY 4.0, per-vote JSON with official source URLs. Use it to get Senate votes and to cross-check cdep totals.
3. senat.ro `VoturiPlenDetaliu.aspx` — authoritative fallback for individual Senate votes.

**Where it fits:**
- New tables: `vote` (id, chamber, legislature, event_date, subject, bill_ref, totals, source_url, dedup_key) and `vote_position` (vote_id, person_id, choice, group_at_vote, party_at_vote).
- Reuse `event.dedup_key` pattern for idempotency; store raw XML/JSON in `fragment` with a checksum.
- Link each vote to `event` so the existing timeline shows it; add evidence type `vote`.
- New API endpoints: `/analytics/vote-cohesion`, `/person/{id}/votes`, `/votes` with filters. New frontend pages: a vote explorer and a per-person voting record.

**Ethical caution:** `vot-parlament.ro` deliberately refuses to publish an "attendance" metric. Report **presence at a vote** factually, with its source and the known gaps; do not invent an "attendance score" or rank MPs by it.

**Sanity check:** the dashboard should show a vote count for 2024 that matches the official cdep XML totals; a known switch (e.g. a 2017 PSD→independent move) should show the MP's group label at the vote date.

### Phase 2 — Biographical completion (1–2 weeks, high value, low risk)

**Why:** 275 people have no birth date, and we store no education, profession or birthplace. These are the inputs of the existing `generational_shift` endpoint and every "type of MP" statistic.

**Sources in priority order:**
1. **cdep birth-month tables** (`structura2015.de?leg=YYYY&par=V01…V12`) — official, ~3,165 rows with DOB across all 10 legislatures. Best for deputies.
2. **senat.ro `FisaSenator`** — best for senators; OpenSanctions got a DOB for 230/231 from it.
3. **GLD** (CC0) — 329 named 2016 deputies with DOB, education, occupation; import as *additional* attributes with `source_url`, never as authority for tenures.
4. **SER-PROM XLSX** — 1990–2012, best for short-tenure substitutes; check the CC BY-SA compatibility before merging values into a CC-BY release.
5. **Existing `pipeline/enrich.py`** — wire `enrich --apply` into `.github/workflows/data.yml` **after** `build-corpus`, with conservative thresholds. It currently never runs, hence 0 QIDs.
6. **Politoscop PDFs** — manual,recent legislatures only, for education and profession.

**Where it fits:** add nullable columns to `Person` (`education`, `occupation`, `birthplace`, `gender`, `birth_date_precision`), or better, a `person_attribute` table with `(person_id, key, value, source_url, confidence, observed_at)` so every value carries provenance. Record QIDs in both `person.wikidata_qid` and `person_identifier(scheme='wikidata')`.

**Sanity check:** the 275 missing birth dates should drop substantially; every filled date should have a `source_url` and an `evidence` row; no name-only merge should occur (use the project's existing identity rules).

### Phase 3 — Party context and statistical covariates (1 week, high analytical payoff)

**Why:** switch waves are more interesting when we can say what kind of parties people moved between.

**Sources:** Party Facts IDs as the crosswalk; CHES 2019/2024 (left-right, EU position, populism, democracy items), V-Party v2, POPPA, The PopuList, ParlGov/PPEG (Romania 1990–2024, 43 parties). Prefer the **CC BY** EUI archive copies where a source is otherwise ShareAlike.

**Where it fits:** new table `party_score(party_org_id, year, source, variable, value, source_url)`; join by `Organization.wikidata_qid` / Party Facts ID stored in `organization` or a new `org_identifier` row. Do **not** write third-party values into `organization.short_name` or overwrite genealogy.

**Sanity check:** switching rate by party ideology quartile should be computable; PSD's FSN→FDSN→PDSR→PSD lineage should resolve to one Party Facts ID.

### Phase 4 — Committee histories and speeches (2 weeks)

**Why:** we have committee memberships but not the dated detail or what was said.

**Sources:** senat.ro committee pages (dated membership and roles), cdep committee sittings, Zenodo 3332908 (both chambers, 1996–2019, CC BY 4.0, speaker URLs), monitorul.ai (cited verbatim Gazette text, 2000+).

**Where it fits:** extend `Membership` with committee role dates (already possible via `role`, `start_date`, `end_date`, `confidence`, `source_url`); add a `speech` table with person_id, date, chamber, text_url, source, dedup_key. Use `EVIDENCE_TYPES` additions `speech` / `intervention`.

### Phase 5 — Election results and electoral base (1 week)

**Why:** an MP without a constituency denominator is only half a statistic.

**Sources:** AEP datasets on data.gov.ro (2012, 2016, 2020 CSV/XLSX with `mandate-repartizate-*.csv`), ANES 2024 candidates/mandates XLSX (CC BY 4.0), Code for Romania's `romanian-elections-data` backup as a fallback.

**Where it fits:** `election_result(chamber, legislature, constituency, party_org_id, votes, seats, source_url)`; link to `Mandate.constituency` (already exists). New endpoint `/analytics/electoral-base`.

### Phase 6 — Benchmarks and country-year context (1 week)

**Why:** "22% women" is only meaningful with a comparison.

**Sources:** IPU women 1945–2018 XLSX and age 2008–2026 XLSX (**cross-check only** — never copy IPU fields into the CC-BY release), World Bank `SG.GEN.PARL.ZS` (CC BY 4.0, safe), European Commission 1990–2024 both-chamber table, INS TEMPO `TSS1661`, Eurostat `sdg_05_50`, International IDEA gender quotas.

**Where it fits:** `benchmark(source, chamber, legislature_or_year, metric, value, license_flag, source_url)` and `context_year(year, source, variable, value)`. Render comparison lines on existing charts, clearly marked "external benchmark, not our data".

### Phase 7 — Future-facing data (ongoing)

- `vot-parlament.ro/ce-urmeaza` — bills in committee / with report / on the agenda (1,515 items on 19 Nov 2026), CC BY 4.0.
- senat.ro weekly/daily programmes and cdep calendars — authoritative future agendas.
- First verified future election date: **30 Nov 2028** (IPU Parline).
- Watch the 2026 draft law `26L629FG` / `26b533FG`, which would create a High-Value Dataset Register on data.gov.ro with mandatory APIs and bulk downloads. If it passes, official open data could replace several scrapers.
- Watch `vot-parlament.ro/data` — the promised SHA-256/row-count atomic bulk dumps are not published yet; when they are, Phase 1 becomes simpler.

---

## 7. How to add a new source without breaking the project (recipe for a newbie)

The project has a strong "evidence first" culture. Keep it. For every new source:

1. **Check the licence first.** Use §5. If it is NC or SA, decide it is a *cross-check* and stop — do not ingest values.
2. **Check robots.txt and pacing.** Use the existing `PoliteClient`; never bypass CAPTCHA; never crawl `/declaratii/`.
3. **Fetch raw pages into `fragment`.** Set `source_name`, `source_id`, `source_url`, `checksum`, `snapshot_path`. This keeps the original evidence even if the parser later changes.
4. **Write a parser** in `pipeline/parse/<source>.py` (follow `cdep_group.py` / `senat_grup.py`). Add a saved HTML/CSV fixture under `tests/fixtures/` and a unit test.
5. **Write to the target table with provenance.** Every row gets `source_url`, `confidence`, and an `evidence` row. Never overwrite a stronger `official_ledger` value with a weaker `community` value.
6. **Use `dedup_key` for idempotency.** Re-running the same import must not duplicate rows.
7. **Add a CLI subcommand** in `pipeline/cli.py` (follow `cmd_enrich` / `cmd_assets`). Support `--dry-run` first.
8. **Update the audit** (`pipeline/audit.py`, `audit-corpus --strict`) so a missing or inconsistent new dataset fails the build, exactly like a missing mandate today.
9. **Only then** add a call to `.github/workflows/data.yml`, with a separate cache key so a broken third-party source cannot block the official corpus.
10. **Update `docs/DATA-MODEL.md`, `docs/RESEARCH.md` (this file's pointers) and `docs/VERIFICATION.md`** in the same commit.
11. **Publish a new dataset release** and let the existing release/Render verification prove it.

**Merge discipline (never change):** exact official ID match → auto-link; name + birth date → propose merge; fuzzy name without a date → review queue only; conflicting official IDs in the same legislature → never merge; QID → strong signal but still check. Identity resolution stays in `pipeline/identity.py`.

**Do not:** copy cdep's field arrangement or multimedia; bulk-scrape `/declaratii/`; treat IPU or OpenSanctions rows as source data for the CC-BY release; merge people by name alone; publish an "attendance score" without caveats; let a third-party outage break the daily official corpus.

---

## 8. What a "10× statistical platform" would let users ask

After Phases 1–6, the site could answer questions it cannot answer today:

- How did a specific MP vote on a given bill, and what group label did they have that day?
- Which parties' MPs switched the most, controlling for party ideology (CHES) and populism (PopuList)?
- Are switchers younger / less educated / more often newly elected than non-switchers (GLD + birth tables)?
- How does Romania's gender balance by chamber compare, legislature by legislature, to the EU (Eurostat) and to IPU aggregates?
- How many MPs came from a constituency that their party later lost (AEP results + mandates)?
- What bills are in the pipeline right now, and which committee handles them (`ce-urmeaza`)?
- Which committee seats were held by MPs who later switched groups (committee date history + events)?

Every answer would carry a source URL, a confidence level and an explicit gap note — the property that already makes the current project trustworthy.

---

## 9. Appendix: exact URLs and queries worth keeping

**Official cdep (both chambers via `cam=1` / `cam=2`)**
```
https://www.cdep.ro/ords/pls/parlam/structura2015.gp?cam=2&leg={LEG}&idg={IDG}
https://www.cdep.ro/ords/pls/parlam/structura2015.mp?idm={IDM}&cam=2&leg={LEG}
https://www.cdep.ro/ords/pls/parlam/structura2015.de?leg={LEG}&par=V{01..12}
https://www.cdep.ro/ords/pls/steno/evot2015.xml?par1=1&par2={YYYYMMDD}
https://www.cdep.ro/ords/pls/steno/evot2015.nominal?idv={VOTID}&idl=1
https://www.cdep.ro/ords/pls/proiecte/upl_pck2015.proiect?idp={IDP}
https://www.cdep.ro/ords/pls/steno/steno2015.home?idl=1
```

**Official senat**
```
https://www.senat.ro/FisaSenator.aspx?ParlamentarID={GUID}
https://www.senat.ro/ComponentaGrupuri.aspx?GrupID={GUID}
https://www.senat.ro/VoturiPlen.aspx
https://www.senat.ro/VoturiPlenDetaliu.aspx?AppID={GUID}
https://www.senat.ro/legis/lista.aspx
https://www.senat.ro/StenoPag2.aspx
https://www.senat.ro/sitemap.xml
```

**Machine-readable hubs**
```
https://data.gov.ro/api/3/action/package_search?q={QUERY}&rows=20
https://data.europa.eu/api/hub/search/?q={QUERY}&filters=dataset
https://api.data.ipu.org/v1/documentation/json
https://data.europarl.europa.eu/api/v2/meps?country-of-representation=RO&format=application/ld+json
https://api.opensanctions.org/
https://query.wikidata.org/sparql
https://api.worldbank.org/v2/country/ROU/indicator/SG.GEN.PARL.ZS?format=json&date=1997:2025
https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/sdg_05_50?format=JSON&geo=RO&lang=en
```

**Verified Wikidata query (counts in §3.6)**
```sparql
SELECT (COUNT(DISTINCT ?p) AS ?n) WHERE {
  { ?p wdt:P39 wd:Q17556530 } UNION { ?p wdt:P39 wd:Q19938957 }
  ?p wdt:P569 ?v .          # swap for P69 (education), P106 (occupation), P19 (birthplace)
}
```

**IPU filter that actually works**
```
https://api.data.ipu.org/v1/elections?filter[]=election_code:eq:RO-LC01-E20201206
```

**1990s sources that break the "dead zone" claim**
```
https://sites.google.com/site/rqsaro/projects/romanian-mps
https://web.archive.org/web/20060207121411/http://www.cdep.ro/pls/parlam/structura.de?leg=1990&cam=2&par=A
https://ro.wikipedia.org/wiki/Legislatura_1990-1992_(Camera_Deputa%C8%9Bilor)
https://doi.org/10.5281/zenodo.3332908
https://281.ro/api/senators/1990.json
```

---

## 10. Final note

Everything in this document comes from live checks on 2026-11-20 or from reading this repository. Where a claim could not be verified, it says so explicitly. The project's existing habits — source URL on every row, SHA-256 snapshots, conservative identity matching, strict audit before release — are exactly what make the additions above safe. Add new sources in that same shape and the project keeps getting more useful without becoming less trustworthy.
