# Parlament Deschis

> **Unde stau aleșii tăi, în orice moment din 1990 până azi.**
> Open, source-cited tracker for the Romanian Parliament — Camera Deputaților and Senat.

[![Code license: AGPL-3.0-or-later](https://img.shields.io/badge/code-AGPL--3.0--or--later-blue.svg)](LICENSE)
[![Data license: CC-BY-4.0](https://img.shields.io/badge/data-CC--BY--4.0-lightgrey.svg)](data/licenses/README.md)

**Parlament Deschis** answers a simple civic question: on any given date, which party, parliamentary group, committee, bureau, delegation or friendship group did each elected member belong to — and when exactly did they move? Every fact is dated, carries a confidence level, links to the official publication, and points to an archived snapshot of the page it came from.

This is a transparency tool, not a news outlet or a voting record. It reports what the chambers themselves publish. Where the record is incomplete, it says so instead of guessing.

---

## Why this exists

Romanian parliamentary history is published, but it is scattered across changing chamber websites, per-legislature pages, and documents that express dates with different precision. Following a single member across terms, or measuring party switching over three decades, means manually reconciling pages that were never designed to be queried.

Parlament Deschis normalizes those publications into one temporal model. The goal is verifiability: any claim on the dashboard can be traced back to the exact official URL and a byte-for-byte archived copy of that page.

---

## Features

- **Time-slider dashboard (1990 → present)** — choose a date and see both chambers as they were composed that day.
- **Dual hemicycles** — Camera Deputaților and Senat side by side, colored by parliamentary group, with member lists and totals.
- **Group-size timeline** — how each group's seat count evolved across the selected interval (ECharts line chart).
- **Defection / party-switching sankey** — where members moved from and to (ECharts sankey).
- **Live feed with source health** — newly detected movements and the latest ingest status for `cdep.ro` and `senat.ro`.
- **Search** — find a member by name, then open a per-person drawer.
- **Per-person drawer** — membership Gantt, typed events, citation popovers (original source + archived snapshot), identifiers, and change history.
- **Bilingual RO/EN interface** — Romanian by default, English one click away.
- **About modal** — methodology, sources, coverage matrix, and licenses in the product.
- **Open data exports** — Popolo 1.0 JSON plus persons / organizations / posts / memberships / events CSV.
- **Honest coverage badges** — `full`, `partial`, or `none` per chamber and legislature; never a fabricated complete-looking history.

---

## Quickstart

### Prerequisites

- Python **3.12+**
- Node.js **18+** and npm (frontend only)

### Initialize and load development data

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'

.venv/bin/parlament init                     # create SQLite schema + seed legislature key events
.venv/bin/parlament ingest-fixtures          # load captured official HTML fixtures (development sample)
.venv/bin/parlament stats                    # person / organization / membership / event counts
```

`ingest-fixtures` is a **development sample**, not a full Parliament. It loads two captured Camera Deputaților group ledgers and two captured Senat profiles from `tests/fixtures/`.

### Run the backend

```bash
.venv/bin/parlament serve --host 127.0.0.1 --port 8000
```

- API root: <http://127.0.0.1:8000/api>
- Interactive docs: <http://127.0.0.1:8000/docs>
- OpenAPI schema: <http://127.0.0.1:8000/openapi.json>

If the `serve` subcommand is not yet wired in your checkout, the equivalent is:

```bash
.venv/bin/uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Vite serves <http://localhost:5173> and proxies `/api` and `/snapshots` to `http://127.0.0.1:8000`. Production build:

```bash
npm run build                      # tsc -b && vite build
npm run lint                       # tsc --noEmit (strict TypeScript)
```

---

## Pipeline commands

All commands accept `--db PATH` (default `data/parlament.db`).

> **Checkout note.** The table below is the **product command contract**. In the checkout used to write these docs, `parlament --help` lists only `init`, `ingest-fixtures`, `verify`, and `stats`; the `ingest` / `backfill` / `poll` / `export` / `enrich` / `coverage` / `serve` subcommands are not wired yet (`pipeline/cli.py` marks them as later phases). Run `parlament --help` in your checkout to confirm what is available. The underlying modules exist and are exercised by the test suite; the API equivalents for exports are live today (see [docs/API.md](docs/API.md)).

| Command | What it does |
| --- | --- |
| `parlament init` | Create the SQLite schema and seed legislature key events from `data/reference/legislatures.json`. |
| `parlament ingest-fixtures` | Load captured official HTML fixtures into the database (development data). |
| `parlament ingest --legislature 2024 --chamber both\|deputies\|senate --force --limit N` | **Contract only** — live, polite ingest from `cdep.ro` / `senat.ro`. Archives a snapshot per fetched page. `--force` re-processes unchanged pages; `--limit` caps profiles/pages for a cautious first run. |
| `parlament backfill --from 1990 --to 2024 --chamber deputies\|senate\|both --force` | **Contract only** — loop legislatures from the reference file and ingest each discoverable term. |
| `parlament poll --once` | **Contract only** — run one live diff/reconcile cycle (default). |
| `parlament poll --foreground --interval 30` | **Contract only** — run the poller continuously, one cycle every 30 minutes. `--legislature` selects the current term. |
| `parlament export --out data/exports --format json,csv --chamber ... --legislature ...` | **Contract only** — write Popolo 1.0 JSON and the five CSV datasets. |
| `parlament enrich --limit N --dry-run` | **Contract only** — Wikidata cross-check/enrichment for birth dates and QIDs. Conservative: it reports or fills only what Wikidata states; it never fabricates. |
| `parlament coverage` | **Contract only** — derive the coverage matrix from the rows actually present and refresh the `coverage` table. |
| `parlament verify` | Integrity checks: inverted intervals, orphan rows, duplicate open tenures, evidence presence. |
| `parlament stats` | Print row counts. |
| `parlament serve --host 127.0.0.1 --port 8000` | **Contract only** — run the FastAPI read API with uvicorn. |

### Backfill — honest limitation

`backfill` iterates the terms in `data/reference/legislatures.json` (1990, 1992, …, 2024). Camera Deputaților publishes per-legislature group ledgers that can be discovered and parsed. For the **Senate**, only the *current* sitemap is reliably discoverable; older profile URLs are not enumerated by the public site. Backfill therefore covers what is discoverable and marks the rest `partial` or `none` in the coverage matrix. It does not invent historical Senate rosters.

---

## Tests and lint

```bash
# Python
.venv/bin/pytest
.venv/bin/pytest --cov=pipeline --cov=backend
.venv/bin/ruff check .

# Frontend
cd frontend
npm run lint
npm run build
```

Tests never touch the live network. Parser tests read real captured HTML from `tests/fixtures/`; temporal, identity, reconcile, event, and export tests run against in-memory or temporary SQLite databases.

**Test suite: 86 tests passing** (as of this documentation).

---

## Repository layout

```text
pipeline/
  sources/        polite HTTP client + cdep.ro / senat.ro adapters
  parse/          cdep group ledger, Senat profile and group roster parsers
  approxdate.py   Romanian approximate-date parsing (YYYY / YYYY-MM / YYYY-MM-DD)
  normalize.py    diacritics, person-name and organization-label normalization
  fragments.py    SHA-256 snapshot archive + fragment records
  identity.py     person resolution, merge audit, reversible merges
  reconcile.py    authoritative and derived membership intervals
  events.py       join / leave / switch / founding / rename event derivation
  ingest.py       orchestration: parsed records → persons → tenures → evidence
  poller.py       diff/reconcile cycle + per-source health
  coverage.py     full / partial / none coverage matrix
  export.py       Popolo 1.0 JSON + CSV serialization
  queries.py      as-of temporal queries shared by API and tests
  db.py           SQLAlchemy models, enums, SQLite/WAL engine
  cli.py          `parlament` entry point
backend/
  main.py         FastAPI app factory, CORS, SPA/static serving, optional poller
  config.py       project-root paths and environment overrides
  deps.py         database session dependency
  queries.py      API serialization helpers
  routers/api.py  read routes + token-guarded admin poll
  routers/exports.py  Popolo JSON and CSV export routes
frontend/
  src/            React + Vite + TypeScript + Tailwind + ECharts dashboard
  src/components/ hemicycles, timeline, sankey, live feed, search, person drawer
data/
  reference/      committed legislatures.json and groups.json
  licenses/       CC-BY-4.0 text + licensing notes
  snapshots/      generated archived source pages (gitignored)
  exports/        generated Popolo/CSV exports (gitignored)
tests/
  fixtures/       real captured official HTML
  test_*.py       parser, temporal, identity, reconcile, export and integration tests
docs/             architecture, API, data model, methodology, contributing
```

---

## Data sources

| Source | Used for | Notes |
| --- | --- | --- |
| `cdep.ro` — Camera Deputaților, `structura2015.gp` | Group index and per-group dated ledgers (current + former members) | Authoritative group membership and join/leave dates; per-term `idm` identifiers. |
| `senat.ro` — Senat, `FisaSenator.aspx` and `ComponentaGrupuri.aspx` | Senator profiles, group/committee/bureau/delegation tenures, group rosters | Per-term GUID identifiers; discovered via `sitemap.xml`. |
| `data/reference/legislatures.json` | Term start/end dates and RO/EN labels | Committed reference data, not scraped at runtime. |
| `data/reference/groups.json` | Group/party display names and colors | Committed reference data. |
| Wikidata | Cross-check and enrichment of birth dates and QIDs | Enrichment only; never the primary source for a tenure. |

Official chamber publications are the **source of truth**. Wikidata may corroborate a fact; it does not override an official ledger, and it is never used to infer a membership date.

### Responsible scraping / compliance

The pipeline is deliberately slow and conservative:

- **robots.txt is honored** per host before fetching (`urllib.robotparser`). A disallowed URL raises and the run stops for that source.
- **At most one request per second per host** — the client defaults to a **2.5 s** pause between requests to the same host, well below the 1 req/s ceiling.
- **Identifying User-Agent** naming the project and its civic purpose; no browser impersonation.
- **Conditional GET** with `ETag` / `If-None-Match` and `Last-Modified` / `If-Modified-Since`; `304 Not Modified` is recorded as unchanged.
- **`429 Too Many Requests`** waits for `Retry-After` (capped at 120 s).
- **5xx / network errors** use exponential backoff, with a small retry limit.
- **CAPTCHA or challenge pages are a hard stop.** The client raises `CaptchaError`; it never attempts to solve, bypass, or evade a challenge. If a source starts challenging, ingestion for that source stops and the health indicator reports the failure.
- **No headless browser** is used to defeat anti-bot measures.

Snapshots are stored per content hash, so repeated runs do not re-download or duplicate unchanged content.

---

## Provenance and confidence

Every membership and event carries provenance fields:

| Field | Meaning |
| --- | --- |
| `source_url` | The exact official page the fact came from. |
| `confidence` | `official_ledger` → `official_profile` → `derived` → `community` (strongest first). |
| `start_precision`, `end_precision` | `YYYY-MM-DD`, `YYYY-MM`, or `YYYY` — the precision actually published. |
| `start_reason`, `end_reason` | Why a tenure began or ended (`GENERAL_ELECTION`, `CHANGED_PARTY`, `DIED`, …). |
| `evidence` rows | Typed links to the source URL and the archived snapshot checksum. |

The API exposes each citation at `/api/evidence/{id}`. The UI offers **“Vezi sursa originală”** and **“Vezi copia arhivată”**. If no archive exists, only the original link is shown — the application never fabricates an archive URL.

**No inferred day when only a month or year was published.** Dates are represented as an `[earliest, latest]` window plus a precision tag. See [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for the full fact rules.

---

## Coverage — what the badges mean

Coverage is computed per chamber and legislature from the distinct members actually present in the database, against modern constitutional chamber sizes (330 deputies, 136 senators):

| Badge | Rule | Meaning |
| --- | --- | --- |
| `full` | ≥ 90% of the modern seat count | The term is substantially complete. |
| `partial` | Some memberships, below the threshold | Real data, visibly incomplete. |
| `none` | Zero memberships | Nothing ingested; the UI says so instead of rendering an empty hemicycle as history. |

Legislatures before 2004 had different chamber sizes, so the modern threshold is a deliberately conservative bar: an old term will show `partial` rather than claim `full`. The API and the About modal report the same matrix. Coverage is never inferred from the existence of a legislature's dates alone.

---

## Exports and licensing

```bash
parlament export --out data/exports --format json,csv
```

> **Checkout note.** `parlament export` is part of the command contract but is not yet wired in this checkout. The same `pipeline/export.py` builders are served live at `GET /api/export/popolo` and `GET /api/export/{dataset}.csv`:

```bash
curl -s "http://127.0.0.1:8000/api/export/popolo?legislature=2024" -o popolo.json
curl -s "http://127.0.0.1:8000/api/export/memberships.csv?legislature=2024" \
  -o memberships.csv
```

An export contains:

- `popolo.json` — Popolo 1.0 subset: persons, organizations, posts, memberships, events, plus a `meta` block with generator, scope, counts and licenses.
- `persons.csv`, `organizations.csv`, `posts.csv`, `memberships.csv`, `events.csv` — UTF-8, Romanian diacritics preserved, list/dict fields serialized as JSON.

Scope filters (`--chamber`, `--legislature` on the CLI; `chamber`, `legislature` query parameters on the API) apply consistently to every section so foreign keys never dangle.

| Material | License |
| --- | --- |
| Source code | **AGPL-3.0-or-later** — see [LICENSE](LICENSE). |
| Generated data / exports | **CC-BY-4.0** — see [data/licenses/CC-BY-4.0.txt](data/licenses/CC-BY-4.0.txt). |
| Archived source pages | Copyright remains with the respective chamber; stored solely to substantiate cited facts. See [data/licenses/README.md](data/licenses/README.md). |

Attribution for data: **“Parlament Deschis”**, with a link to the project and the CC-BY-4.0 license. If you reuse a fact, keep its `source_url` and confidence so your readers can verify it too.

---

## Limitations

- **Historical Senate discovery is partial.** Only the current Senate sitemap is reliably enumerable; older profiles may be unreachable without a discoverable index. Those terms are marked `partial`/`none`.
- **The bundled fixture dataset is a sample.** It demonstrates the parsers and temporal model; it is not a complete term. Run live ingest/backfill for real coverage.
- **Not every committee, bureau, delegation, or friendship group is covered for every term.** Coverage badges describe member coverage; sub-body coverage can be thinner.
- **Official pages change.** When a page is restructured, its parser may need a new captured fixture. The archive lets you see exactly what the parser saw.
- **Wikidata enrichment is intentionally conservative.** A missing birth date or QID stays missing rather than being guessed from a namesake.
- **This is not an official record.** For legal or electoral purposes, consult the published decisions of the chambers and the Official Gazette.

---

## Status

The project is being finished in parallel with this documentation. This table records what is implemented in the product contract; in a given checkout, `parlament --help` and `/openapi.json` are the runtime source of truth.

| Area | Status | Notes |
| --- | --- | --- |
| SQLAlchemy schema + bitemporal queries | Implemented | SQLite/WAL, end-exclusive intervals. |
| Camera Deputaților + Senat parsers | Implemented | Real captured fixtures in `tests/fixtures/`. |
| Identity resolution + auditable merges | Implemented | Identifier-first, never guesses ambiguous names. |
| Reconciliation + event derivation | Implemented | Closed tenures immutable; idempotent dedup keys. |
| Polite live client + source adapters | Implemented | robots.txt, pacing, conditional GET, CAPTCHA stop. |
| Poller + source health | Implemented | Per-source failure isolation. |
| Backfill | Implemented | Senate historical discovery is the limiting factor. |
| Popolo / CSV export | Implemented via API | `GET /api/export/*`; CLI `export` subcommand not wired yet. |
| Wikidata enrichment | Implemented | Conservative; `--dry-run` supported. |
| Coverage + integrity checks | Implemented | `full` / `partial` / `none`, honest notes. |
| Read API | Implemented | As-of chamber, timeline, persons, history, movements, events, evidence, coverage, about, health. |
| Open-data endpoints | Implemented | Popolo JSON + five CSV datasets, scoped consistently. |
| Admin poll endpoint | Implemented | `POST /api/admin/poll`, `X-Admin-Token`, off by default. |
| CLI live ingest / poll / export | Not wired in checkout | Modules exist; `pipeline/cli.py` exposes `init`, `ingest-fixtures`, `verify`, `stats`. |
| Dashboard | Implemented | Slider, dual hemicycles, timeline, sankey, live feed, search, drawer, RO/EN. |
| Licenses | Implemented | AGPL-3.0 text + CC-BY-4.0 text + notes. |
| Complete pre-2024 Senate rosters | Planned / limited | Blocked on discoverable official indexes; badges stay honest. |
| Full sub-body coverage for every term | Planned / partial | Committees, bureaus, delegations, friendship groups. |

---

## Contributing

Contributions are welcome — especially **new captured fixtures** for pages the parsers do not yet handle, and corrections backed by an official URL.

- Read [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for setup, test-first expectations, fixture policy, style, and responsible-scraping rules.
- Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) before changing the pipeline.
- Read [docs/METHODOLOGY.md](docs/METHODOLOGY.md) before changing a fact rule, confidence level, or coverage threshold.
- Never add live network calls to tests. Never bypass a CAPTCHA. Never invent a date.

For a data correction, include the official page URL and, where possible, an archived snapshot. A correction that cannot be traced to a published source will not be merged.

---

## Documentation

| Document | Contents |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Pipeline stages, data flow, temporal semantics, identity, events, snapshots, coverage. |
| [docs/API.md](docs/API.md) | Every endpoint, parameters, response shapes, curl examples, export schema, errors. |
| [docs/DATA-MODEL.md](docs/DATA-MODEL.md) | Table-by-table schema reference and enumerations. |
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | Legal/civic basis, fact rules, confidence, coverage, corrections, licensing. |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Dev setup, tests, fixtures, style, scraping rules, PRs. |
| [data/licenses/README.md](data/licenses/README.md) | Code vs. data licensing, attribution, source terms, archive note. |

---

## License

Code: **GNU Affero General Public License v3.0 or later** ([LICENSE](LICENSE)).

Generated data: **Creative Commons Attribution 4.0 International** ([data/licenses/CC-BY-4.0.txt](data/licenses/CC-BY-4.0.txt)). Attribute as **“Parlament Deschis”** and retain source URLs.