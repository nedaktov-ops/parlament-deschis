# 10x Sprint Specification — Detailed Acceptance Criteria

**Branch Strategy:**
- `main` — production-ready
- `wip/week-1-data` — Week 1 data completeness
- `wip/week-2-ui` — Week 2 question-driven UI
- `wip/week-3-analytics` — Week 3 analytical layer
- `wip/week-4-polish` — Week 4 polish & deploy

**Checkpoint Protocol:**
- After each task: run full test suite (86 tests must pass)
- After each day: commit with descriptive message, tag checkpoint
- If tests fail: revert to last passing checkpoint, debug, re-apply

---

## WEEK 1: DATA COMPLETENESS

### Task 1.1: Wikidata Enrichment Pipeline (`pipeline/enrich.py`) ✅ DONE
**Acceptance Criteria:**
- [x] Batch reconciliation via Wikidata Reconciliation API (not SPARQL) for Romanian MPs
- [x] Local SQLite cache (`data/wikidata_cache.db`) with TTL 30 days
- [x] Rate limiting: 0.5 req/sec (2 req/sec), exponential backoff on 429/timeout
- [x] Multi-column scoring: name (fuzzy) + birth_year (exact) + chamber (exact)
- [x] Auto-accept threshold ≥95, review queue 80-95 (stored in `wikidata_review` table), reject <80
- [x] Output: `Person.wikidata_qid`, `Person.birth_date` (gender, photo_url pending DB migration)
- [x] CLI: `parlament enrich --limit N --dry-run --legislature YYYY` → `--apply`
- [x] Results: 97 persons enriched (4.9% of 1,978), 79 with birth dates
- [ ] Tests: mock API response, verify cache hit/miss, verify scoring logic

### Task 1.2: Explicit Party Memberships Backfill ✅ DONE
**Acceptance Criteria:**
- [x] For every group membership with `on_behalf_of_id` → create matching party membership
- [x] Party membership: `classification="party"`, same dates, same person, linked via `on_behalf_of_id` to group
- [x] Senate: derive party from profile `party` field → create party org + membership
- [x] Verify: 1,675 party memberships created from 2,004 group memberships with party affiliation
- [ ] Tests: fixture with known group+party → verify party membership created

### Task 1.3: Derive Party Switch Events ✅ DONE
**Acceptance Criteria:**
- [x] In `pipeline/events.py`: derive `switch_party` from party membership changes (like `switch_group`)
- [x] Dedup key: `switch_party:{person}:{from_party}:{to_party}:{date}`
- [x] Only emit if `from_party != to_party` and both non-null
- [x] Results: 132 switch_party events derived from 122 persons with multi-party histories across legislatures
- [x] Poller updated to call `derive_party_events` on each cycle
- [ ] Tests: person with 2 party memberships → 1 switch_party event

### Task 1.4: Asset Declaration Extraction (2020, 2024) ⚠️ INFRASTRUCTURE READY
**Acceptance Criteria:**
- [x] `tabula-py` extracts tables from `data/assets/*.pdf` (Chamber/Senate declarations)
- [x] Schema: `person_id`, `year`, `asset_type`, `value_ron`, `description`, `source_url`
- [x] New table: `asset_declaration` (created in pipeline/db.py)
- [x] CLI command: `parlament assets --year YYYY --apply`
- [x] Heuristic table detection for asset tables (valoare, suma, ron columns)
- [ ] Manual entry UI in admin for current legislature
- [ ] Tests: sample PDF → extracted rows match expected schema
- [ ] No PDFs available yet in data/assets/

### Task 1.5: Web-Based Reconciliation UI (Admin) ⚠️ PENDING
**Acceptance Criteria:**
- [ ] Route: `/admin/reconcile` — shows review queue from `wikidata_review` table (created in cache DB)
- [ ] Columns: local name, birth year, legislature, chamber, Wikidata candidates (name, QID, birth date, party, score)
- [ ] Actions: Accept (write QID), Reject (mark reviewed), Skip
- [ ] Batch accept for score ≥95
- [ ] Tests: seed wikidata_review → UI loads → accept → QID persisted
- [ ] Note: Review queue now stored in `wikidata_review` table in cache DB, not `match_review`

### Task 1.6: Senate Historical Gap Documentation ⚠️ DOCUMENTED
**Acceptance Criteria:**
- [x] Update `docs/METHODOLOGY.md` with explicit gap statement (see docs/RESEARCH.md)
- [ ] Coverage badge in UI: "Senate 1990-2020: data incomplete" (UI not updated yet)
- [x] No fake data inserted
- [x] Documented in docs/RESEARCH.md: Senate historical data not discoverable via sitemap; only 2024 legislature available

---

## WEEK 2: QUESTION-DRIVEN UI (ROUTE-BASED)

### Task 2.1: Migrate to TanStack Router
**Acceptance Criteria:**
- [ ] `npm i @tanstack/react-router` + `@tanstack/router-devtools`
- [ ] Routes: `/` (Live), `/party/:short` (PartyProfile), `/person/:id` (PersonDeepDive), `/electoral` (ElectoralDynamics), `/institutional` (InstitutionalView), `/legislature/:year` (LegislatureDetail)
- [ ] Search params for filters: `?date=...&chamber=...`
- [ ] Code splitting per route (lazy load)
- [ ] Preserve TanStack Query keys (same queryKey structure)
- [ ] Tests: navigate between routes → no full reload, cache preserved

### Task 2.2: Party Profile Page (`/party/:short`)
**Acceptance Criteria:**
- [ ] Header: party name, color, short_name, QID link, genealogy timeline
- [ ] Demographics: avg age, gender split, total MPs (current + historical)
- [ ] Switch Analysis: in/out flows, net change per legislature, wave detection
- [ ] Committee Control: chairs/members per legislature
- [ ] Asset Summary: total declared, avg, anomalies (if data exists)
- [ ] Loyalty Proxy: switch rate, tenure distribution
- [ ] Export button: CSV for party data

### Task 2.3: Person Deep-Dive (`/person/:id`)
**Acceptance Criteria:**
- [ ] Career Timeline: all memberships (group, party, committee, bureau, delegation) with dates
- [ ] Party Loyalty Proxy: switches, tenure per party, net trajectory
- [ ] Network: co-committee, co-party, co-switchers (top 10)
- [ ] Assets: declarations by year (if data exists)
- [ ] Sources: every fact linked to evidence + snapshot
- [ ] Export: Popolo person JSON

### Task 2.4: Electoral Dynamics (`/electoral`)
**Acceptance Criteria:**
- [ ] Switch Waves: timeline with clusters (30-day windows post-election/govt formation)
- [ ] Defection Matrix: from_party → to_party heatmap per legislature
- [ ] Cohort Loyalty: switch rate by entry legislature
- [ ] Net Flow: party A → party B → party C chains
- [ ] Export: wave CSV, matrix CSV

### Task 2.5: Institutional View (`/institutional`)
**Acceptance Criteria:**
- [ ] Committee Control: party chairs / total committees per legislature
- [ ] Bureau Composition: party representation in leadership
- [ ] Cross-Chamber MPs: list with career trajectory
- [ ] Vacancy Tracker: unfilled seats per chamber/legislature

### Task 2.6: Live Dashboard (`/`)
**Acceptance Criteria:**
- [ ] Today's switches (live feed from poller)
- [ ] Upcoming events (committee meetings, plenaries - if data exists)
- [ ] Alerts: new switches in last 24h
- [ ] Quick links to affected party/person pages

---

## WEEK 3: ANALYTICAL LAYER

### Task 3.1: Switch Wave Detection
**Acceptance Criteria:**
- [ ] Algorithm: cluster switches by 30-day sliding window; label clusters near election/govt formation dates
- [ ] Output: `switch_wave` table (wave_id, label, start_date, end_date, switch_count, trigger_event)
- [ ] API: `/api/analytics/waves?legislature=...`
- [ ] Tests: known post-2020 wave detected

### Task 3.2: Party Cohesion Index
**Acceptance Criteria:**
- [ ] Formula: `1 - (std_dev(switch_rate_per_mp) / mean(switch_rate_per_mp))` per party per legislature
- [ ] Output: `party_cohesion` table
- [ ] API: `/api/analytics/cohesion?party=...&legislature=...`
- [ ] Tests: synthetic data with known variance → correct index

### Task 3.3: Committee Control Index
**Acceptance Criteria:**
- [ ] `party_chairs / total_committees` per legislature per party
- [ ] Output: `committee_control` table
- [ ] API: `/api/analytics/committee-control?legislature=...`

### Task 3.4: Cross-Chamber Career Map
**Acceptance Criteria:**
- [ ] Identify persons with memberships in both chambers
- [ ] Career trajectory: deputy → senator (or reverse) with dates
- [ ] Output: `cross_chamber_career` table
- [ ] API: `/api/analytics/cross-chamber`

### Task 3.5: Generational Shift
**Acceptance Criteria:**
- [ ] Avg/median age per party per legislature (from Wikidata birth dates)
- [ ] Output: `generational_shift` table
- [ ] API: `/api/analytics/generations?party=...`

### Task 3.6: Analytics API Endpoints
**Acceptance Criteria:**
- [ ] Router: `/api/analytics/*`
- [ ] All endpoints return JSON with `meta.generated_at`, `meta.count`
- [ ] Caching: 1 hour TTL
- [ ] Tests: each endpoint returns 200 + valid schema

---

## WEEK 4: POLISH & DEPLOY

### Task 4.1: GraphQL Endpoint
**Acceptance Criteria:**
- [ ] `pip install strawberry-graphql`
- [ ] Schema: Person, Party, Membership, Event, Analytics types
- [ ] Query: `person(id)`, `party(shortName)`, `analytics { waves, cohesion, committeeControl }`
- [ ] Playground at `/graphql`

### Task 4.2: Party Genealogy Manual Population
**Acceptance Criteria:**
- [ ] `Organization.previous_party_id`, `successor_party_id` columns added
- [ ] Populated: PSD←FDSN←FSN, PNL splits (PNTCD, PNL-CD, etc.), POT→UPR, USR new, AUR new, UDMR continuous
- [ ] Party Profile shows genealogy timeline

### Task 4.3: Documentation Updates
**Acceptance Criteria:**
- [ ] `METHODOLOGY.md`: honest gaps (Senate historical, voting records, assets pre-2020)
- [ ] `API.md`: all new endpoints documented
- [ ] `DATA-MODEL.md`: new tables (asset_declaration, switch_wave, party_cohesion, etc.)

### Task 4.4: Load Test
**Acceptance Criteria:**
- [ ] `locust` or `hey` — 100 concurrent users, 5 min
- [ ] p95 < 500ms for all endpoints
- [ ] Zero 5xx errors

### Task 4.5: Staging Deploy + Demo
**Acceptance Criteria:**
- [ ] Deploy to staging (Docker compose or systemd)
- [ ] Demo script: journalist workflow (party profile → person deep-dive → electoral dynamics)
- [ ] Feedback captured

---

## TESTING REQUIREMENTS (All Tasks)

| Layer | Tool | Coverage Target |
|-------|------|-----------------|
| Python unit | pytest | 100% new code |
| Python integration | pytest + temp DB | All CLI commands |
| Frontend unit | vitest | New components |
| Frontend integration | Playwright | Critical user flows |
| E2E | Playwright | 5 core journeys |

**CI Gate:** All tests must pass before merge to `main`.