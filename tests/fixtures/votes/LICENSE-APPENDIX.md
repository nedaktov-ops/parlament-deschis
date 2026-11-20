# LICENCE APPENDIX — source register for Parlament Deschis

This is the **single authority** for which sources may be copied into the
CC BY 4.0 dataset and which are display-only cross-checks. It is mirrored as
rows in the `source_license` table (`pipeline/licenses.py`), enforced by a
database `CHECK` constraint, and re-checked by the audit.

Rules that never bend:

* `redistributable = 1` is allowed **only** for `CC0-1.0`, `CC-BY-4.0` and
  `OGL-ROU-1.0`. Anything else (NC, SA, unverified) is `redistributable = 0`
  and can never enter an export, a CSV or the API.
* Every source carries its licence URL, the verbatim licence quote, the date
  it was checked and the exact attribution string.
* A source whose licence cannot be verified is treated as **not
  redistributable** until written permission is obtained.

---

## 1. Sources that may be copied into the dataset

| `source_name` | `license_id` | Licence evidence (verified 2026-11-20) | Attribution string (use verbatim) |
|---|---|---|---|
| `cdep_facts` | `OGL-ROU-1.0` | Romanian official facts; Law 8/1996 art. 9. cdep.ro's legal notice covers creative assets, **not** facts | `Camera Deputaților — official parliamentary facts (names, dates, votes), source URL per row` |
| `senat_facts` | `OGL-ROU-1.0` | senat.ro publishes the parliamentary facts; no `robots.txt` is served (HTTP 404) | `Senatul României — official parliamentary facts, source URL per row` |
| `ro_281` | `CC-BY-4.0` | `/api`, `/despre` and `/metodologie`: *"Toate datele sunt disponibile sub licență Creative Commons CC-BY 4.0"* | `281.ro · Registrul neoficial al Parlamentului României` |
| `wikidata` | `CC0-1.0` | Wikidata's licence statement: CC0 1.0 Universal | `Wikidata — CC0 1.0` |
| `gld` | `CC0-1.0` | `doi:10.7910/DVN/U1ZNVT` — Global Legislators Database, CC0 | `Global Legislators Database, doi:10.7910/DVN/U1ZNVT, CC0` |
| `partyfacts` | `CC0-1.0` | Dataverse API metadata for `doi:10.7910/DVN/TJINLQ`: CC0 1.0 | `Party Facts, doi:10.7910/DVN/TJINLQ, CC0 1.0` |
| `ches_eui` | `CC-BY-4.0` | EUI archive `hdl.handle.net/1814/69975`: CC BY 4.0 | `CHES, EUI archive, hdl.handle.net/1814/69975, CC BY 4.0` |
| `data_gov_ro` | `OGL-ROU-1.0` | data.gov.ro / AEP open-data terms | `data.gov.ro / AEP — OGL-ROU-1.0, dataset ID per row` |
| `zenodo_3332908` | `CC-BY-4.0` | `doi.org/10.5281/zenodo.3332908`: CC BY 4.0 | `Zenodo 3332908, CC BY 4.0` |

## 2. Cross-check only — never copied into the dataset

| `source_name` | `license_id` | Why it is display-only |
|---|---|---|
| `vot_parlament` | `CC-BY-4.0` | The licence permits reuse, but vot-parlament.ro serves `Content-Signal: ai-train=no, use=reference` and its `robots.txt` disallows the training bots. **Decision: cross-check only.** Every published row comes from cdep.ro; vot-parlament is used to *verify* the official numbers, never as the origin of a row. Attribution if displayed: `vot-parlament.ro · CC BY 4.0 · source URL per vote` |
| `v_dem` | `CC-BY-SA-4.0` | ShareAlike — the derivative would have to be SA, which this dataset is not |
| `ipu` | `CC-BY-NC-SA-4.0` | Non-commercial + ShareAlike |
| `open_sanctions` | `CC-BY-NC-4.0` | Non-commercial |
| `populist` | `UNVERIFIED` | OSF node licence is `null` and the project has no LICENSE file |
| `ser_prom` | `CC-BY-SA-4.0` | ShareAlike; institutional permission not obtained |

## 3. Vote fixtures (this directory)

| Fixture | Licence | Use |
|---|---|---|
| `cdep_evot2015_*.xml`, `cdep_evot2015_*.html` | `OGL-ROU-1.0` (official facts) | Test fixtures for the vote importer; every row keeps its source URL |
| `vot_parlament_vote_37526.json`, `vot_parlament_votes_export_head.csv` | `CC-BY-4.0` | Contract test only (cross-check). The 404 body is stored to prove the route does not exist |

The source URLs are stored in `manifest.json` next to the SHA-256 of every
file, so any reviewer can re-fetch and compare bytes.

## 4. robots.txt summary (verified 2026-11-20)

| Host | Status | Relevant rule | Our behaviour |
|---|---|---|---|
| `www.cdep.ro` | 200, 37 bytes | `User-agent: *` / `Disallow: /declaratii/` | We never request `/declaratii/`; vote endpoints are allowed |
| `www.senat.ro` | 404 | no robots.txt served | treated as "no restrictions" |
| `281.ro` | 200, 466 bytes | `User-agent: * Allow: /`; several AI crawlers disallowed; `CCBot` disallowed | we are a documented research crawler, not a training crawler |
| `vot-parlament.ro` | 200, 2 745 bytes | `User-agent: * Allow: /`; many training bots disallowed; `Content-Signal: ai-train=no, use=reference` | cross-check only, paced, attributed |

## 5. Change protocol

To add or change a licence class, edit this file **and** `pipeline/licenses.py`
in the same commit, then run:

```bash
uv run pytest -q tests/test_source_licenses.py
uv run python -m pipeline.cli audit-corpus --strict
```

A source that is not in the register is not a source. The audit fails when a
row points at a licence that is missing or not redistributable.
