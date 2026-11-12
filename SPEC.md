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

### Task 1.1: Wikidata Enrichment Pipeline (`pipeline/enrich.py`)
**Acceptance Criteria:**
- [ ] Batch SPARQL query for Romanian MPs: name + birth year + legislature + chamber
- [ ] Local SQLite cache (`data/wikidata_cache.db`) with TTL 30 days
- [ ] Rate limiting: 1 req/sec, exponential backoff on 429
- [ ] Multi-column scoring: name (fuzzy) + birth_year (exact) + legislature (exact) + chamber (exact)
- [ ] Auto-accept threshold ≥95, review queue 80-95, reject <80
- [ ] Output: `Person.wikidata_qid`, `Person.birth_date`, `Person.gender`, `Person.photo_url`
- [ ] CLI: `parlament enrich --limit N --dry-run` → `parlament enrich --apply`
- [ ] Tests: mock SPARQL response, verify cache hit/miss, verify scoring logic

### Task 1.2: Explicit Party Memberships Backfill
**Acceptance Criteria:**
- [ ] For every group membership with `on_behalf_of_id` → create matching party membership
- [ ] Party membership: `classification="party"`, same dates, same person, linked via `on_behalf_of_id` to group
- [ ] Senate: derive party from profile `party` field → create party org + membership
- [ ] Verify: `SELECT COUNT(*) FROM membership WHERE classification='party'` ≈ group memberships count
- [ ] Tests: fixture with known group+party → verify party membership created

### Task 1.3: Derive Party Switch Events
**Acceptance Criteria:**
- [ ] In `pipeline/events.py`: derive `switch_party` from party membership changes (like `switch_group`)
- [ ] Dedup key: `switch_party:{person}:{from_party}:{to_party}:{date}`
- [ ] Only emit if `from_party != to_party` and both non-null
- [ ] Tests: person with 2 party memberships → 1 switch_party event

### Task 1.4: Asset Declaration Extraction (2020, 2024)
**Acceptance Criteria:**
- [ ] `tabula-py` extracts tables from `data/assets/*.pdf` (Chamber/Senate declarations)
- [ ] Schema: `person_id`, `year`, `asset_type`, `value_ron`, `description`, `source_url`
- [ ] New table: `asset_declaration`
- [ ] Manual entry UI in admin for current legislature
- [ ] Tests: sample PDF → extracted rows match expected schema

### Task 1.5: Web-Based Reconciliation UI (Admin)
**Acceptance Criteria:**
- [ ] Route: `/admin/reconcile` — shows review queue from `match_review` table
- [ ] Columns: local name, birth year, legislature, chamber, Wikidata candidates (name, QID, birth date, party, score)
- [ ] Actions: Accept (write QID), Reject (mark reviewed), Skip
- [ ] Batch accept for score ≥95
- [ ] Tests: seed match_review → UI loads → accept → QID persisted

### Task 1.6: Senate Historical Gap Documentation
**Acceptance Criteria:**
- [ ] Update `docs/METHODOLOGY.md` with explicit gap statement
- [ ] Coverage badge in UI: "Senate 1990-2020: data incomplete"
- [ ] No fake data inserted

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
- [ ] Switch Waves: timeline with clusters (30-day windows post-election/govt)
- [ ] Defection Matrix: from_party → to_party heatmap per legislature
- [ ] Cohort Loyalty: switch rate by entry legislature
- [ ] Net Flow: party A → party B → party C chains
- [ ] Export: wave CSV, matrix CSV

### Task 2.5: Institutional View (`/institutional`)
**Acceptance Criteria:**
- [ ] Committee Control: party chairs / total per legislature
- [ ] Bureau Composition: party representation in leadership
- [ ] Cross-Chamber MPs: list with career trajectory
- [ ] Vacancy Tracker: unfilled seats per chamber/legislature

### Task 2.4: Live Dashboard (`/`)
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