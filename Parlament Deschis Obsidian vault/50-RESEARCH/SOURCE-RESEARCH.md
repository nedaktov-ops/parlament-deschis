---
id: SOURCE-RESEARCH
type: research
title: "Source research — official chambers, licences and robots facts"
description: "Mirror of source discovery: cdep group/roster/profile views, hidden groups, senate GUID discovery, licence classes and current-versus-historical robots facts."
status: active
authority: mirror
tags: [type/research, lifecycle/active, domain/research]
source_paths: [docs/RESEARCH.md, docs/DATA-ENRICHMENT-RESEARCH.md, tests/fixtures/votes/LICENSE-APPENDIX.md, README.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Source research

Companions: [DATA-ENRICHMENT](DATA-ENRICHMENT.md) for external datasets and
[RESEARCH-LOG](RESEARCH-LOG.md) for dated provenance and NOT PROVEN items. The
licence register mirrored here is `tests/fixtures/votes/LICENSE-APPENDIX.md`.

## cdep.ro — three cross-checked views

The deputies' chamber is the only **row source** for published data. Official
facts (names, dates, votes) are covered by Romanian law, not by the site's
creative-asset legal notice.

| View | URL pattern | What it gives us |
|---|---|---|
| Group index | `structura2015.gp?idl=1&cam=2&leg=<leg>` | group links (`idg`) with published member counts, per legislature |
| Group ledger | `structura2015.gp?cam=2&leg=<leg>&idg=<id>` | dated intervals (`Membru din` / `până în`), party, function, current and former members; `idg=0` is unaffiliated |
| Alphabetical roster | `structura2015.de?par=A` | second view of the same population; used for reconciliation, not as a separate row source |
| MP profile | `structura2015.mp?idm=<id>&cam=<c>&leg=<leg>` | mandates a person ever held; `idm` is **per mandate**, so identity is resolved through the mandate graph, never by name |

- The group index **omits groups that no longer exist** (for example the
  2016–2020 Deputies ALDE group). The collector probes the id space and finds
  **15 hidden groups across 10 scopes**.
- The three views (group page, index count, roster) are reconciled against each
  other: **141 of 143 groups reconcile exactly**. The two exceptions are
  documented source inconsistencies, reported rather than smoothed over.
- All 10 legislatures (1990–2024) return the same parseable table structure.
  Date formats vary (`DD.MM.YYYY`, `DD MMM YYYY`, month precision, year only)
  and are preserved at their stated precision.

## senat.ro — discovery, not profile ingest

- The sitemap exposes `FisaSenator.aspx?ParlamentarID=<GUID>` (137 current) and
  `ComponentaGrupuri.aspx?GrupID=<GUID>` (9 current groups). No historical
  legislature selector exists in profile HTML.
- The historical discovery flow is fixed and guarded: a two-step
  legislature → session → search POST yields **128 unique GUIDs for 1990** and
  **134 for 2024**; posting a legislature parameter into the wrong field used
  to return the same 134 GUIDs for every year (bug E6, now understood).
- Against those source sets the corpus has 1990: **128/128** and 2024:
  **132/134**; name overlap is 127/128 and 128/134 respectively. The residual
  gap is small, but **profile ingestion is deferred** on identity risk (name
  order, homonyms, 0 existing `senat_guid` identifiers) — see
  [DATA-ENRICHMENT](DATA-ENRICHMENT.md) and decision D3 in the source repo.

## Licence classes

| Class | Sources | Disposition |
|---|---|---|
| Code | repository `LICENSE` is **GNU AGPL v3** | governs code, not facts |
| Data — copyable | `OGL-ROU-1.0` official facts (cdep, senat, data.gov.ro); `CC-BY-4.0` (external Romanian civic source (`ro_281`), CHES, Zenodo 3332908); `CC0-1.0` (Wikidata, GLD, Party Facts) | may enter the CC BY dataset **with the verbatim attribution string and row-level source URL** |
| Cross-check only | `vot_parlament`, `v_dem` (ShareAlike), `ipu` (NC-SA), `open_sanctions` (NC), `ser_prom` (SA), `populist` (unverified) | display-only; never the origin of a published row |

- **External Romanian civic source (`ro_281`):** self-declared **CC BY 4.0** on
  its `/api`, `/despre` and `/metodologie` pages, with a required attribution
  string; its public code repository is a 404, so the licence is
  self-declared rather than repository-backed. The register lists it as
  copyable-with-attribution, **but the data policy keeps it cross-check-only,
  never a row source**: every published row comes from cdep.ro and the civic
  source is used to verify numbers. Read its `/errata/` before trusting any
  field.
- **Licence enforcement is latent, not operating.** The pinned release has no
  `source_license` table; both working DBs have the table with **0 rows**;
  `ensure_source_licenses()` is defined (`pipeline/licenses.py`) but is not
  called from the CLI or app startup. Separately, 0 licence/attribution
  violations were found and the required attribution string is present.
  Resolver: wire the function into an explicit, tested startup/CLI path.
- IPU, V-Dem and SER-PROM are **cross-check only**: ShareAlike and
  Non-Commercial terms make them unsuitable for this CC BY dataset. IPU and EC
  figures may be consulted and cited, never copied into release fields.

## robots.txt — historical snapshot versus current facts

The original research document is explicitly labelled **historical**; its
stated date is **2025-11-12**, while git first-adds the file on **2026-11-12**
(the date anomaly is registered in [RESEARCH-LOG](RESEARCH-LOG.md)). Its
robots snapshots are stale. Current facts were verified **2026-11-20** in the
licence appendix.

| Host | Historical snapshot (as printed in the old report) | Current verified fact (2026-11-20) |
|---|---|---|
| `www.cdep.ro` | 200; disallowed `/cgi-bin/`, `/tmp/`, `/ords/`; `Crawl-delay: 5`. The old report argued civic transparency use of `/ords/` was defensible. | **200, 37 bytes**; only `Disallow: /declaratii/`. Vote endpoints are allowed; we never request `/declaratii/`. |
| `www.senat.ro` | 200; disallowed `/cgi-bin/`, `/admin/`, `/tmp/`; `Crawl-delay: 10`. | **404 — no robots.txt served**; treated as "no restrictions" but still paced politely. |
| external Romanian civic source (`ro_281`) | not covered by the historical snapshot | **200, 466 bytes**; `User-agent: * Allow: /`, several AI crawlers and `CCBot` disallowed. We act as a documented research crawler, not a training crawler. |
| `vot-parlament.ro` | not covered by the historical snapshot | **200, 2745 bytes**; `Allow: /`, many training bots disallowed, `Content-Signal: ai-train=no, use=reference`. Cross-check only, paced and attributed. |

The live bytes for the 2026-11-21 probe were recorded **offline**; re-reading
them from the network remains a named resolver in the NOT PROVEN register.
