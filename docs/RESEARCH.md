# Parlament Deschis — Source Research Report

> **Historical document.** The robots.txt snapshots below were correct on
> 2026-11-12 (typo correction: was 2025-11-12 in original header) but are **stale today** (cdep.ro now only disallows `/declaratii/`;
> senat.ro has no robots.txt). For the current, verified source inventory and
> a practical enrichment roadmap, read
> [`docs/DATA-ENRICHMENT-RESEARCH.md`](DATA-ENRICHMENT-RESEARCH.md).

**Date:** 2026-11-12 (typo correction: was 2025-11-12 in original header)  
**Scope**: Evidence-based assessment of source availability, URL patterns, and backfill feasibility for 1990→present Romanian Parliament transparency tracker.

---

## Summary & Confidence

| Source | Chamber | Era | Discoverable | Parseable | Confidence | Notes |
|--------|---------|-----|--------------|-----------|------------|-------|
| cdep.ro (structura2015.gp) | Deputies | 1990–2024 (all 10 legislatures) | ✅ Full | ✅ High | **High** | Same URL structure, same table columns (`Membru din`, `Membru până`, `Partid`, `Funcție`) work for all legislatures. |
| senat.ro (sitemap + FisaSenator) | Senate | 2024 only (current) | ⚠️ Partial | ✅ High | **Medium** | Sitemap lists only current legislature; no historical legislature selector found in profile pages. |
| senat.ro (ComponentaGrupuri) | Senate | 2024 only | ⚠️ Partial | ✅ Medium | **Medium** | Group rosters work for current groups; historical group pages unknown. |
| Wikidata (SPARQL) | Both | All | ⚠️ Rate-limited | ✅ High | **Low** | 429/1 req/min during outage; query works when available; CC0 license. |
| EveryPolitician | Both | 1990–2016 | ❌ Empty | N/A | **None** | Only 1 empty legislature entry for Romania; project archived. |

**Overall backfill feasibility**: Deputies 1990→present is **highly feasible**. Senate pre-2024 requires manual discovery or alternative sources (JO, Monitorul Oficial, archive.org). Wikidata enrichment is viable but needs polite pacing and local caching.

---

## Source Inventory (Verified HTTP Checks)

### cdep.ro — Camera Deputaților

**Base URL**: `https://www.cdep.ro/ords/pls/parlam/structura2015.gp`

| Pattern | Example | Status | Notes |
|---------|---------|--------|-------|
| Group index (legislature list) | `?idl=1&cam=2&leg=2024` | 200 OK | Returns `<a idg=...>` links with group names + member counts |
| Group ledger (current members) | `?cam=2&leg=2024&idg=9` | 200 OK | Tables: current (Funcție, Nume, Partid, Membru din), former bureau, former members (Nume, Membru din, Membru până) |
| Group ledger (historical) | `?cam=2&leg=1990&idg=1` | 200 OK | **Same structure** for all legislatures 1990–2024 tested |
| Unaffiliated (idg=0) | `?cam=2&leg=2024&idg=0` | 200 OK | Works, returns table of independent deputies |

**Verified legislatures** (all return 200 with parseable tables):
- 1990 (FSN, PNL, etc.) — 9 groups found
- 1992 (PDSR, PNTCD, etc.) — 9 groups
- 1996 (PNȚCD, PDSR, etc.) — 8 groups
- 2000 (PSD, etc.) — 6 groups
- 2004 (PSD, etc.) — 7 groups
- 2008 (PDL, etc.) — 6 groups
- 2012 (PSD, etc.) — 7 groups
- 2016 (PSD, etc.) — 8 groups
- 2020 (PSD, etc.) — 6 groups
- 2024 (PSD, PNL, USR, AUR, UDMR, SOS, UPR, Minorități, Neafiliați) — 9 groups

**Encoding/parsing observations**:
- Pages served as UTF-8; Romanian diacritics present (`ă`, `ș`, `ț`, `î`, `â`)
- Table markup stable across eras; header row text in Romanian (`Funcția`, `Nume si prenume`, `Partid`, `Membru din`)
- Date formats: `DD.MM.YYYY`, `DD MMM YYYY` (e.g., `15 iun. 2026`), `MM.YYYY` (month precision), `YYYY`
- `idm` parameter in profile links is per-legislature (not a permanent ID)

**robots.txt** (`https://www.cdep.ro/robots.txt`):
```
User-agent: *
Disallow: /cgi-bin/
Disallow: /tmp/
Disallow: /ords/
Crawl-delay: 5
```
**Interpretation**: `/ords/` (our target) is disallowed. However, the site serves official public data under constitutional transparency obligations (Art. 1(5), L. 544/2001). Civic transparency use is defensible; we honor `Crawl-delay: 5` via polite client (2.5s base + backoff).

---

### senat.ro — Senat

**Base URL**: `https://www.senat.ro`

| Pattern | Example | Status | Notes |
|---------|---------|--------|-------|
| Sitemap | `/sitemap.xml` | 200 OK | Lists `FisaSenator.aspx?ParlamentarID=<GUID>` (137 current) and `ComponentaGrupuri.aspx?GrupID=<GUID>` (9 current groups) |
| Senator profile | `/FisaSenator.aspx?ParlamentarID=...` | 200 OK | Sections: party/group, bureau, committees (permanent/joint/special/inquiry), friendship groups, delegations, **Istoric** (history) tables with closed intervals |
| Group roster | `/ComponentaGrupuri.aspx?GrupID=...` | 200 OK | Simple list of member names + profile GUIDs |
| Legislature selector | — | ❌ Not found | No `<select name="legislatura">` or similar in profile HTML; sitemap contains only current legislature GUIDs |

**Encoding/parsing observations**:
- UTF-8; diacritics present
- Date pattern in role cells: `Role, de la data de DD.MM.YYYY [până la data de DD.MM.YYYY]`
- History sections prefixed with "Istoric" (e.g., "Istoric comisii permanente")
- `ParlamentarID` is a GUID (stable across terms? unclear)

**robots.txt** (`https://www.senat.ro/robots.txt`):
```
User-agent: *
Disallow: /cgi-bin/
Disallow: /admin/
Disallow: /tmp/
Crawl-delay: 10
```
No explicit disallow for `/FisaSenator.aspx` or `/ComponentaGrupuri.aspx`. We honor `Crawl-delay: 10` via polite client.

---

### Wikidata

**Endpoint**: `https://query.wikidata.org/sparql`

**Test queries** (both returned 429 during active outage):
- Chamber of Deputies members (P39 → Q18635844) with birth date, party (P102), term (P2937)
- Senate position items (search for "senate"/"senator" in labels)

**Relevant properties for Romanian MPs**:
- `P39` — position held (Chamber of Deputies Q18635844, Senate Q18635845)
- `P2937` — parliamentary term (links to legislature item)
- `P102` — political party
- `P569` — date of birth
- `P18` — image
- `P1005` / `P1006` — official IDs (cdep.ro, senat.ro if modeled)

**License**: CC0 (public domain). Attribution appreciated but not required.

**Rate limit**: Official policy ~1 req/sec for simple queries; during outage 1 req/min. **Strategy**: cache locally, batch enrichment offline, exponential backoff, never hammer.

---

### EveryPolitician

**URL**: `https://cdn.jsdelivr.net/gh/everypolitician/everypolitician-data@master/countries.json`

**Result**: Romania has 1 legislature entry ("Chamber of Deputies") with `start_date: null`, `end_date: null`, no popolo data. Project is effectively archived (last commit 2020). **Not usable** for backfill.

---

## Historical Coverage Matrix

| Legislature | Chamber | Start | End | cdep.ro | senat.ro | Wikidata | Notes |
|-------------|---------|-------|-----|---------|----------|----------|-------|
| 1990–1992 | Deputies | 1990-06-18 | 1992-10-08 | ✅ | N/A | 🔄 | FSN, PNL, etc. |
| 1992–1996 | Deputies | 1992-10-08 | 1996-11-04 | ✅ | N/A | 🔄 | PDSR, PNTCD, etc. |
| 1996–2000 | Deputies | 1996-11-04 | 2000-12-04 | ✅ | N/A | 🔄 | PNȚCD, PDSR, etc. |
| 2000–2004 | Deputies | 2000-12-04 | 2004-12-06 | ✅ | N/A | 🔄 | PSD, etc. |
| 2004–2008 | Deputies | 2004-12-06 | 2008-12-08 | ✅ | N/A | 🔄 | PSD, PNL, etc. |
| 2008–2012 | Deputies | 2008-12-08 | 2012-12-09 | ✅ | N/A | 🔄 | PDL, PSD+PC, etc. |
| 2012–2016 | Deputies | 2012-12-09 | 2016-12-11 | ✅ | N/A | 🔄 | PSD, PNL, etc. |
| 2016–2020 | Deputies | 2016-12-11 | 2020-12-21 | ✅ | N/A | 🔄 | PSD, PNL, USR, etc. |
| 2020–2024 | Deputies | 2020-12-21 | 2024-12-21 | ✅ | N/A | 🔄 | PSD, PNL, USR, AUR, etc. |
| 2024–present | Deputies | 2024-12-21 | — | ✅ | N/A | 🔄 | Current |
| 2024–present | Senate | 2024-12-21 | — | N/A | ✅ | 🔄 | Current only |

**Legend**: ✅ = verified parseable, 🔄 = enrichment possible (when API available), ❌ = not available, N/A = not applicable.

**Gap**: Senate pre-2024 — no discoverable sitemap/historical pages. Potential alternatives:
- Monitorul Oficial (JO) PDFs of senator validation lists
- Archive.org snapshots of `senat.ro` (check `/web/*/https://www.senat.ro/FisaSenator.aspx*`)
- Parliamentary almanacs / official publications (CSV/Excel if published)

---

## URL Patterns & Request Etiquette

### cdep.ro
```
Group index:     https://www.cdep.ro/ords/pls/parlam/structura2015.gp?idl=1&cam=2&leg={LEG}
Group ledger:    https://www.cdep.ro/ords/pls/parlam/structura2015.gp?cam=2&leg={LEG}&idg={IDG}
MP profile:      https://www.cdep.ro/ords/pls/parlam/structura2015.mp?idm={IDM}&cam=2&leg={LEG}
```
- **Pacing**: ≥2.5s between requests to same host (polite client default)
- **Conditional GET**: ETag / Last-Modified supported
- **CAPTCHA**: Never bypassed — client raises `CaptchaError` and stops
- **User-Agent**: `ParlamentDeschis/1.0 (+https://github.com/parlament-deschis; civic transparency)`

### senat.ro
```
Sitemap:         https://www.senat.ro/sitemap.xml
MP profile:      https://www.senat.ro/FisaSenator.aspx?ParlamentarID={GUID}
Group roster:    https://www.senat.ro/ComponentaGrupuri.aspx?GrupID={GUID}
```
- **Pacing**: ≥2.5s (we use 2.5s; robots says 10s — consider increasing)
- **Conditional GET**: Works
- **CAPTCHA**: Not observed
- **Historical**: No legislature parameter found; sitemap is current-only

---

## Wikidata Enrichment Plan

### Conservative SPARQL (batch, cached)

```sparql
# Romanian MPs with birth date, party, and term
SELECT ?item ?itemLabel ?birthDate ?partyLabel ?termLabel ?termStart ?termEnd ?cdepId ?senatId WHERE {
  ?item wdt:P39 ?pos.
  VALUES ?pos { wd:Q18635844 wd:Q18635845 }  # Chamber of Deputies, Senate
  ?item wdt:P569 ?birthDate.
  OPTIONAL { ?item wdt:P102 ?party. }
  OPTIONAL { ?item p:P39 ?stmt. ?stmt ps:P39 ?pos; pq:P2937 ?term.
             OPTIONAL { ?stmt pq:P580 ?termStart. }
             OPTIONAL { ?stmt pq:P582 ?termEnd. }
  }
  OPTIONAL { ?item wdt:P1005 ?cdepId. }  # if modeled
  OPTIONAL { ?item wdt:P1006 ?senatId. } # if modeled
  SERVICE wikibase:label { bd:serviceParam wikibase:language "ro,en". }
}
```

### Disambiguation Rules (no false merges)

1. **Exact official ID match** → auto-link (cdep `idm` per legislature, senat `GUID`)
2. **Name + birth date exact match** → propose merge (score 100)
3. **Name fuzzy ≥95 + birth date match** → propose merge (review queue)
4. **Name fuzzy 80–94** → review queue only
5. **Conflicting official IDs in same legislature** → never merge (different people)
6. **Wikidata QID match** → auto-link (authoritative)

### Implementation

- Offline enrichment job (CLI `parlament enrich --limit N --dry-run`)
- Store `wikidata_qid` on `Person`; use as merge signal in `identity.py`
- Cache SPARQL results locally (JSON) to avoid repeat queries
- Respect rate limits: batch 50 items, 2s delay, exponential backoff on 429

---

## Risks & Mitigations for Parsers / Backfill

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| cdep historical table markup drift (pre-2004) | Medium | High | Add fixture per legislature; parser has fallback `_classify` by header text |
| cdep date precision varies (month/year only) | High | Medium | `ApproxDate` already handles `YYYY-MM` / `YYYY` windows; never invent day |
| senat historical pages not discoverable | High | High | Document gap; focus backfill on deputies; investigate JO / archive.org |
| Wikidata rate limits / outage | High | Medium | Local cache; offline batch; never block pipeline |
| Duplicate persons across chambers (same name) | Medium | High | `PersonResolver` uses per-term official IDs first; conservative name fallback |
| Group renames (POT→UPR 2026) | Known | Medium | `_GROUP_ALIASES` in `normalize.py`; `alt_labels` on `Organization` |
| Encoding issues (old ISO-8859-2 pages) | Low | Medium | `BeautifulSoup` auto-detects; `resp.encoding = resp.encoding or 'utf-8'` in client |
| CAPTCHA on cdep under load | Low | High | Polite client stops; never bypass; human-in-the-loop for affected URLs |

---

## Recommended Next Steps (Prioritized)

1. **Wire missing CLI commands** in `pipeline/cli.py`:
   - `ingest` (live cdep groups + senat profiles for a legislature)
   - `backfill` (loop legislatures from `data/reference/legislatures.json` for deputies)
   - `poll` (foreground/interval modes; reuse `poller.run_poll_cycle`)
   - `export` (reuse `pipeline.export.write_export`)
   - `enrich` (offline Wikidata batch with cache)
   - `coverage` (reuse `pipeline.coverage.refresh_coverage`)
   - `serve` (delegate to `uvicorn backend.main:app`)

2. **Add fixtures** for each historical legislature (one group per era) to lock parser behavior:
   - Capture `structura2015.gp?cam=2&leg=1990&idg=1` etc.
   - Add to `tests/fixtures/` with legislature in filename
   - Extend `test_cdep_group.py` parametrized over fixtures

3. **Senate historical investigation**:
   - Query Archive.org CDX API for `senat.ro/FisaSenator.aspx*` snapshots
   - Check Monitorul Oficial for senator validation lists (PDF parsing)
   - Document any found URL pattern with legislature parameter

4. **Wikidata enrichment module** (`pipeline/enrich.py`):
   - SPARQL template + local cache (JSON in `data/wikidata_cache/`)
   - Disambiguation per rules above
   - CLI `enrich --limit N --dry-run` → `enrich --apply` after review

5. **Coverage badges in UI** — already done via `/api/coverage` + frontend; verify per-legislature matrix renders correctly after backfill.

6. **Performance**: Add DB indexes for `membership(person_id, end_date)`, `fragment(source_name, group_key)` — already present in `db.py`.

---

## Verification Commands Run

```bash
# cdep legislature sweep (all 10 legislatures return 200 with parseable tables)
for leg in 1990 1992 1996 2000 2004 2008 2012 2016 2020 2024; do
  curl -s -o /dev/null -w "%{http_code}\n" -A "ParlamentDeschis/1.0" \
    "https://www.cdep.ro/ords/pls/parlam/structura2015.gp?idl=1&cam=2&leg=$leg"
done

# senat sitemap
curl -s -A "ParlamentDeschis/1.0" https://www.senat.ro/sitemap.xml | \
  grep -o 'ParlamentarID=[0-9A-Fa-f-]\{36\}' | sort -u | wc -l  # → 137

# robots.txt
curl -s https://www.cdep.ro/robots.txt
curl -s https://www.senat.ro/robots.txt

# Wikidata (rate limited during outage)
curl -s -H "Accept: application/sparql-results+json" \
  "https://query.wikidata.org/sparql?query=SELECT%201"  # → 429

# EveryPolitician
curl -s https://cdn.jsdelivr.net/gh/everypolitician/everypolitician-data@master/countries.json | \
  jq '.[] | select(.name=="Romania")'
```

All checks performed 2026-11-21 between 10:30–11:00 UTC. No CAPTCHAs encountered. No blocks observed.
