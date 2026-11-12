# Arhitectură / Architecture

Parlament Deschis is a one-way data pipeline with a read-only query layer. Official
chamber pages are fetched politely, archived by content hash, parsed into typed records,
resolved to stable people, reconciled into bitemporal tenures, converted into events, and
served as an as-of API to a static React dashboard.

The system is intentionally boring at the edges: no headless browser, no CAPTCHA solving,
no live scraping from the UI, no writes from the read API except the token-protected
admin poll trigger.

```
                     scheduled poll / CLI
                              │
                    ┌─────────▼──────────┐
                    │  PoliteClient      │  robots.txt · pacing · ETag/304
                    │  (sources/client)  │  429 wait · CAPTCHA = stop
                    └─────────┬──────────┘
                              │ HTML
                    ┌─────────▼──────────┐
                    │ Source adapters    │  cdep.py · senat.py
                    │ discovery + fetch  │
                    └─────────┬──────────┘
                              │ content
                    ┌─────────▼──────────┐
                    │ Fragment store     │  SHA-256 → data/snapshots/<source>/<hash>.html
                    │ (fragments.py)     │  skip unchanged unless --force
                    └─────────┬──────────┘
                              │ HTML
                    ┌─────────▼──────────┐
                    │ Parsers            │  cdep_group.py · senat_profile.py
                    │ (parse/)           │  senat_grup.py
                    └─────────┬──────────┘
                              │ dataclasses (ApproxDate windows)
                    ┌─────────▼──────────┐
                    │ Identity           │  identifier → unique name → new person
                    │ (identity.py)      │  auditable, reversible merges
                    └─────────┬──────────┘
                              │ person ids
                    ┌─────────▼──────────┐
                    │ Reconciliation     │  authoritative intervals / observations
                    │ (reconcile.py)     │  closed tenures immutable
                    └─────────┬──────────┘
                              │ memberships
                    ┌─────────▼──────────┐
                    │ Evidence + events  │  evidence.py rows · events.py derivation
                    │                    │  dedup_key prevents duplicates
                    └─────────┬──────────┘
                              │ SQLite (WAL)
                    ┌─────────▼──────────┐
                    │ Read API           │  as-of queries · movements · exports
                    │ (backend/)         │  /api/* · /docs
                    └─────────┬──────────┘
                              │ JSON
                    ┌─────────▼──────────┐
                    │ Dashboard          │  React + Vite + TS + Tailwind + ECharts
                    │ (frontend/)        │  slider · hemicycles · timeline · drawer
                    └────────────────────┘
```

---

## 1. Design principles

1. **Official publications are the source of truth.** `cdep.ro` and `senat.ro` outrank
   any enrichment source. Wikidata may corroborate; it never creates a tenure.
2. **Facts are dated, not assumed.** A source that publishes only a month or year yields
   an `ApproxDate` window, not a fabricated day.
3. **Every fact is traceable.** A membership points to a source URL and to one or more
   `evidence` rows; an evidence row can point to an archived snapshot checksum.
4. **Closed tenures are immutable.** A member who returns gets a new membership row. The
   past is not silently rewritten.
5. **Uncertainty is visible.** Confidence, precision, and coverage are data, not
   footnotes. The UI renders them.
6. **Failure is isolated.** One chamber being down or challenging does not corrupt the
   other chamber's data or leave a half-written run.

---

## 2. Pipeline stages

### 2.1 Discovery and fetch

`pipeline/sources/client.py` provides `PoliteClient`:

- Reads and honors `robots.txt` per host before the first request.
- Paces requests per host. The default is **2.5 s** between requests, i.e. at most
  0.4 req/s — stricter than the documented 1 req/s ceiling.
- Sends an identifying `User-Agent`.
- Stores `ETag` and `Last-Modified` per URL and sends conditional headers on later runs.
  A `304 Not Modified` returns the cached body as `from_cache=True`.
- Waits on `429` using `Retry-After` (capped at 120 s).
- Retries network errors and `5xx` with exponential backoff.
- Detects CAPTCHA/challenge text and raises `CaptchaError`. There is no bypass path.

Chamber adapters:

| Adapter | Discovery | Pages |
| --- | --- | --- |
| `sources/cdep.py` | Group index page (`structura2015.gp?idl=1&cam=2&leg=…`) | Per-group ledger (`…&idg=…`) with current and former members, roles, party, join/leave dates. |
| `sources/senat.py` | `sitemap.xml` (`FisaSenator.aspx?ParlamentarID=…`, `ComponentaGrupuri.aspx?GrupID=…`) | Senator profile, committee/bureau/delegation/friendship history, group rosters. |

Both adapters write a `pipeline_run` row with status `SUCCESS` or `FAILURE`, timestamps,
row counts, and the error text. Per-source `try/except` blocks mean a Camera failure is
recorded without aborting a Senate run in the same cycle.

### 2.2 Fragments and snapshots

`pipeline/fragments.py` decouples raw fetched bytes from the normalized model:

- `checksum(content)` is **SHA-256** over the UTF-8 bytes.
- `archive_snapshot(source, content)` writes
  `data/snapshots/<source>/<sha256>.<ext>` and returns `(hash, path)`.
- `record_fragment(...)` first compares the new checksum with the latest fragment for the
  same `(source_name, group_key)`. If unchanged and `force=False`, it returns
  `(None, False)` and the caller skips re-parsing.
- A changed fragment is stored as a `fragment` row containing the model name, source,
  source id/URL, group key, checksum, parsed metadata (`data` JSON), and snapshot path.

Snapshots are content-addressed: identical pages across runs produce the same file and
are not duplicated. The directory is gitignored; the database is the index.

### 2.3 Parsing

Parsers are pure functions from HTML to dataclasses; they never touch the network or the
session:

- `parse/cdep_group.py` → `GroupLedger` with `GroupMeta` and `MemberRow` lists
  (`current`, `former`, `former_bureau`). Handles role cells, `idm` links, `Membru din`,
  `Membru până`, founding dates, and former names.
- `parse/senat_profile.py` → `SenatorProfile` with party/group header, constituency,
  election/validation dates, and `SenateMembership` rows classified as committee, joint
  committee, special committee, inquiry committee, bureau, friendship group, or
  delegation. History sections are distinguished from current sections by their `Istoric`
  headers.
- `parse/senat_grup.py` → `GroupRoster` (group name + member GUIDs), used for
  cross-checking group composition.

Dates flow through `pipeline/approxdate.py`, which recognizes Romanian full dates,
month-year expressions, and year-only expressions. The result is an `ApproxDate` with
`earliest`, `latest`, `precision`, and the original `source_string`. See
[docs/METHODOLOGY.md](METHODOLOGY.md) for the fact rules.

### 2.4 Identity resolution

`pipeline/identity.py` maps per-term source identifiers to a stable `person` row.

Official identifiers are scoped by scheme **and** legislature:

- Camera Deputaților: `scheme="cdep_idm"`, `identifier=<idm>`, `legislature="2024"`.
- Senat: `scheme="senat_guid"`, `identifier=<GUID>`, `legislature="2024"`.

Resolution order (`PersonResolver.resolve`):

1. **Exact official identifier** for `(scheme, identifier, legislature)`. If found, reuse
   that person.
2. **Unique name candidate** by normalized name or order-insensitive sort key, across
   canonical names and dated aliases. Candidates are filtered by:
   - birth date, when one is known (a candidate with a different known birth date is
     excluded; an unknown birth date remains a candidate);
   - conflicting official identifiers: a person already holding a *different* identifier
     of the same scheme in the same term is excluded. Two different `idm`/GUID values in
     one term are two different people, even with identical names.
3. If exactly **one** candidate remains, attach the new identifier.
4. Otherwise, **create a new person**. Ambiguity is never resolved by guessing; the
   person starts as `match_status="unmatched"`.

`score_match(a, b)` proposes merge confidence from name similarity plus birth-date
agreement, with a hard override for Wikidata QIDs: equal QIDs → 100, different QIDs → 0.
The module defines `AUTO_MERGE_THRESHOLD = 95` and `REVIEW_THRESHOLD = 80` for
review workflows.

### 2.5 Merges and reversal

`merge_persons(session, winner_id, loser_id)`:

- Repoints identifiers, names, memberships, and events from loser to winner.
- Converts the loser's canonical name into an alias on the winner (or appends it).
- Absorbs a missing birth date or Wikidata QID from the loser.
- Does **not** delete the loser row; it is kept for audit.
- Writes a `merge_audit` row whose `operations` JSON lists every `repoint`, `append`, and
  `replace`, making the merge reversible.
- Sets the winner's `match_status="merged"`.

`revert_merge(session, audit_id)` replays the recorded operations in reverse, moves rows
back to the loser, removes an appended alias, and marks the audit `reverted=True`.
Merges are therefore auditable and reversible rather than destructive.

`match_review` rows (`person_a`, `person_b`, score, reason, `pending` / `approved` /
`rejected`) hold proposed matches for human review.

### 2.6 Reconciliation

`pipeline/reconcile.py` turns observations into non-overlapping tenures. There are two
paths:

**Authoritative ledger** (`MembershipWriter.record_authoritative`) — used when the source
publishes explicit join/leave dates:

- If an identical closed tenure exists, the write is an idempotent no-op (only
  `last_seen_at` refreshes).
- An open tenure with the same start can be closed or enriched with a party, role, or end
  date.
- A returning member with a different interval gets a **new membership id**; the closed
  tenure is never reopened.
- Inverted intervals are clamped defensively so `end >= start` always holds.
- Confidence can improve (lower rank wins) but a strong row is not downgraded by a weak
  observation.

**Derived observation** (`record_observation`) — used for current-only rosters:

- Ensures an open membership for `(person, org)`.
- Closes any other open membership of the same organization class for that person on the
  observation date, with `end_reason="CHANGED_PARTY"` for groups.
- New rows carry `confidence="derived"`.
- `collapse_observations` is order-independent and idempotent: duplicate observations are
  dropped, runs are sorted, and a run closes the day before the next different-org
  observation.

### 2.7 Evidence

`ingest.py` attaches an `evidence` row to each written membership:

- `type` is `official_ledger`, `profile`, `jo`, `intervention`, `scrutin`, or `other`.
- `source_url` is the exact page.
- `snapshot_hash` is the fragment checksum when the page was archived through the live
  adapters; fixture ingests may have no hash.
- `note` records when a start date was inferred (for example, a founding member whose
  individual join date was not published).

The API's `/api/evidence/{id}` resolves the archive URL by looking up the fragment with
that checksum. If no fragment exists, `snapshot_url` is `null` and the UI shows only the
original source.

### 2.8 Event derivation

`pipeline/events.py` derives events from stored tenures; it never invents an event
without a corresponding interval.

For each person's group memberships sorted by start date:

- A `switch_group` event when the previous tenure's organization differs from the current
  one.
- A `join` event for the first tenure.
- A `leave` event when a tenure is closed and there is no later tenure in the same group.
- `group_founded` and `group_renamed` events from organization `founding_date` and
  `alt_labels`.

Every event gets a deterministic `dedup_key` such as
`switch:<person>:<from_org>:<to_org>:<date>`. Re-running derivation never duplicates an
event. Events carry `event_date`, `precision`, `reason`, `confidence`, the group acronym
at the time, and bilingual `summary_ro` / `summary_en`.

### 2.9 Coverage

`pipeline/coverage.py` derives the coverage matrix from rows actually present:

1. Read legislature key events per chamber from `key_event`.
2. Count **distinct** `person_id` values in `membership` for that chamber and legislature.
3. Compare with modern chamber sizes: **330 deputies**, **136 senators**.
4. `none` if count is 0; `full` if count ≥ 90% of the modern size; otherwise `partial`,
   with a note such as `"152 of ~330 seats ingested."`.

`refresh_coverage` upserts the result into the `coverage` table so the API and exports can
report it cheaply. The threshold is deliberately conservative because pre-2004 chambers
had different sizes; old terms should show `partial`, not a false `full`.

The API has a fallback: if the `coverage` table is empty, it derives `partial`/`none` from
key events and membership presence. The `pipeline.coverage` step persists the full
calculation, including `full`; its CLI subcommand is not wired in this checkout.

### 2.10 Exports

`pipeline/export.py` is the single serialization contract for both the CLI and the API:

- `build_popolo(...)` scopes memberships by chamber/legislature, collects referenced
  persons, organizations (plus parent organizations), posts, and events, and returns a
  Popolo 1.0-shaped document with a `meta` block (generator, project URL, Popolo version,
  code/data licenses, scope, counts).
- `csv_for(...)` emits one of five datasets: `persons`, `organizations`, `posts`,
  `memberships`, `events`.
- `write_export(...)` writes `popolo.json` plus the five CSV files with UTF-8 encoding and
  `ensure_ascii=False`, preserving Romanian diacritics.

Because the API and CLI share this module, there is exactly one field contract. See
[docs/API.md](API.md) for the field lists.

---

## 3. Temporal model

### 3.1 Valid time vs. transaction time

The model is bitemporal in the Popolo sense:

| Dimension | Fields | Meaning |
| --- | --- | --- |
| Valid time | `start_date`, `end_date` | When the membership was true in the real world. |
| Transaction/observation time | `first_seen_at`, `last_seen_at` | When the pipeline first/last observed the row. |
| Publication precision | `start_precision`, `end_precision` | How precisely the source stated the date. |

`event.detected_at` records when an event was derived. `evidence.observed_at` records when
the evidence was attached.

### 3.2 End-exclusive intervals

All as-of queries use **end-exclusive** semantics:

```sql
start_date <= :as_of
AND (end_date IS NULL OR end_date > :as_of)
```

Therefore:

- `end_date` is the **first day the tenure is no longer active**.
- A member who switches groups on 15 June 2026 may have a PSD row ending `2026-06-15` and
  a UPR row starting `2026-06-15`. On 15 June they are counted in UPR only; on 14 June
  they are counted in PSD.
- An open tenure has `end_date = NULL` and remains active.

This convention makes same-day transitions unambiguous and avoids double-counting a
member in both groups on the switch date.

### 3.3 Invariants

- `start_date <= end_date` when both exist; inverted input is clamped.
- Closed tenures are immutable. A new stint gets a new `membership.id`.
- Repeat stints coexist; the unique constraint is
  `(org_id, person_id, post_id, end_date)`, so an open row and a closed row for the same
  organization do not collide.
- `memberships_at` returns at most one group per person per chamber when the data is
  consistent; gaps are visible as absences rather than being filled.

---

## 4. Read API and UI

`backend/main.py` creates the FastAPI app:

- `backend/config.py` resolves `PROJECT_ROOT`, `DB_PATH` (`PARLAMENT_DB`),
  `SNAPSHOT_DIR` (`PARLAMENT_SNAPSHOT_DIR`), and `FRONTEND_DIST` relative to the
  repository root, so the process works from any working directory.
- CORS allows `http://localhost:5173` and `http://127.0.0.1:5173`.
- `data/snapshots` is mounted at `/snapshots` when the directory exists at startup.
- If `frontend/dist/index.html` exists, the built SPA is served at `/` with `/assets`
  mounted; unknown non-API paths fall back to `index.html`. `api`, `docs`,
  `openapi.json`, `redoc`, and `snapshots` are excluded from that fallback.
- Without a build, `/` returns a small identity document. Interactive docs are at
  `/docs`, OpenAPI at `/openapi.json`.
- A background poller starts only when `PARLAMENT_POLL_INTERVAL_MIN` is a positive
  integer; it is shut down with the app and a startup failure is logged rather than
  fatal.

`backend/routers/api.py` exposes the read surface under `/api`, plus the
token-guarded `POST /api/admin/poll`. `backend/routers/exports.py` exposes
`/api/export/popolo` and `/api/export/{dataset}.csv`. `backend/queries.py` serializes
memberships, events, organizations, evidence, coverage, history, about, and meta.
As-of composition is computed by `pipeline/queries.py`, the same code used by tests, so
the API and the temporal core cannot drift.

The frontend is a static Vite app:

- `TimeSlider` clamps to the available range and can play through dates; the visible
  timeline spans the full data range, not just the selected legislature.
- `ChamberView` + `Hemicycle` render group composition for a date.
- `TimelineChart` plots group sizes over time between the range bounds.
- `DefectionSankey` visualizes party-to-party movement flows.
- `LiveFeed` queries recent events and the source-health endpoint.
- `Search` queries `/api/persons`; `PersonDrawer` loads `/api/persons/{id}` and its
  `/history` timeline.
- `MembershipGantt` renders tenures with precision/confidence cues.
- `CitationPopover` links to the original source and, when available, the archived copy.
- `About` renders the `/api/about` payload: methodology, sources, licenses, coverage,
  and freshness.
- `i18n.ts` holds the RO/EN strings; RO is the default.

The dashboard never queries the chamber websites directly. It only reads the local API,
which reads SQLite.

---

## 5. Operational notes

- **SQLite in WAL mode** with `synchronous=NORMAL`, `foreign_keys=ON`, and a 5 s busy
  timeout. Writes are serialized by the pipeline; reads are concurrent.
- **One database file** (`data/parlament.db` by default, overridable with `--db` or
  `PARLAMENT_DB`).
- **Generated artifacts** — the database, snapshots, and exports — are gitignored.
  Reference JSON and license texts are committed.
- **Runs are observable** through `pipeline_run` and `/api/health`, which reports the
  latest status, timestamps, row count, and error per source.
- **Admin poll** is the only write endpoint on the API surface; it is token-protected via
  `PARLAMENT_ADMIN_TOKEN` and disabled with a `503` when no token is configured.

---

## 6. Where to change what

| Change | Files |
| --- | --- |
| Add or fix a chamber parser | `pipeline/parse/`, a real fixture in `tests/fixtures/`, parser tests. |
| Add a source | `pipeline/sources/`, a `PipelineRun` source name, discovery + adapter, tests. |
| Change temporal semantics | `pipeline/queries.py`, `pipeline/reconcile.py`, tests in `tests/test_reconcile.py` and `tests/test_ingest_integration.py`. |
| Change identity rules | `pipeline/identity.py`, `tests/test_identity.py`. |
| Change event types or summaries | `pipeline/events.py`, `pipeline/db.py` enums, export field lists. |
| Change coverage thresholds | `pipeline/coverage.py`, this document, `docs/METHODOLOGY.md`. |
| Add an API field or endpoint | `backend/queries.py`, `backend/routers/api.py`, `frontend/src/api/client.ts`, `docs/API.md`. |
| Change export shape or add a dataset | `pipeline/export.py`, `backend/routers/exports.py`, `docs/API.md`, `tests/test_export.py`. |
| Change the schema | `pipeline/db.py`, `docs/DATA-MODEL.md`, a migration note. |
