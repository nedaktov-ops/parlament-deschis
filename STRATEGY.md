# Parlament Deschis — Red Team Analysis & 10x Improvement Strategy

**Date:** 2025-11-12  
**Status:** For approval before implementation

---

## Executive Summary

The project has **solid infrastructure** (pipeline, DB, API, frontend) but **fails its core mission**: enabling users to draw useful conclusions about Romanian parliamentary politics. The data exists but is poorly surfaced; the UI confuses rather than clarifies; critical enrichment (Wikidata, birth dates, photos, asset declarations, voting records) is missing.

**Verdict:** The project is at ~30% of its potential. A focused 4-week sprint can bring it to 80%+.

---

## Red Team Findings — Critical Failures

### 1. Data Quality: "Garbage In, Pretty Out"

| Metric | Current | Required for Insight |
|--------|---------|---------------------|
| Persons with birth_date | **0 / 1,978** | 100% (age analysis, generational shifts) |
| Persons with Wikidata QID | **0 / 1,978** | 100% (cross-ref, photos, bios) |
| Orgs with Wikidata QID | **0 / 231** | 100% (party history, mergers) |
| Party memberships surfaced | Partial (via `on_behalf_of`) | First-class citizen in UI |
| Senate historical coverage | 1–76 persons/leg | Full (needs JO/Monitorul Oficial) |

**Impact:** Cannot answer "What's the average age of PSD deputies?" or "Show me all MPs who served in both chambers" or "Which party has the youngest caucus?"

### 2. Frontend: Tab Sprawl Without Purpose

| Tab | Problem |
|-----|---------|
| **Prezentare generală** | Shows everything → user sees nothing |
| **Legislatura curentă** | Group diff only; no party diff; no committee/bureau view |
| **Traseism politic** | Lists switchers but no *pattern* detection (electoral cycles, post-election purges) |
| **Party Flow Detail** | Shows in/out but no *net trajectory*, no committee correlates |

**Root cause:** Tabs organized by *data structure* not *user questions*.

### 3. Missing "Useful Conclusions" Features

| Question a journalist/citizen asks | Can the tool answer? |
|------------------------------------|---------------------|
| "Who switched from PSD to AUR after 2020?" | ❌ (no party switch tracking in UI) |
| "What's the gender/age balance per party?" | ❌ (no birth dates, no gender) |
| "Which committees does a switcher join/leave?" | ❌ (committee data exists, not visualized) |
| "Show me all MPs with asset declaration anomalies" | ❌ (no asset data) |
| "Who voted against party line on key laws?" | ❌ (no voting data) |
| "Which MPs have EU Parliament experience?" | ❌ (no cross-ref) |
| "Track a person's full career: local → national → EU" | ❌ (no career timeline) |

### 4. Pipeline Gaps

- **Wikidata enrichment:** Placeholder only (`pipeline/enrich.py` missing)
- **Senate historical:** Only 2024 via sitemap; pre-2024 needs JO/Monitorul Oficial PDF parsing
- **Asset declarations:** ANAF/Integrity Agency data not ingested
- **Voting records:** Camera Deputaților stenograme not parsed
- **Media monitoring:** No GDELT/NewsAPI integration

---

## 10x Strategy — Four Pillars

### Pillar 1: Data Completeness (Week 1-2)
**Goal:** Every person has birth_date, gender, photo, Wikidata QID; every party has QID; Senate pre-2024 covered.

| Task | Owner | Effort | Validation |
|------|-------|--------|------------|
| Implement `pipeline/enrich.py` — Wikidata SPARQL batch with local cache, disambiguation rules | Backend | 3 days | >90% persons matched |
| Parse Monitorul Oficial / JO PDFs for Senate 1990-2020 validation lists | Pipeline | 5 days | Senate coverage >80% all legs |
| Integrate ANAF asset declarations (public CSV/API) | Pipeline | 3 days | Asset data for 2020, 2024 legs |
| Add gender inference (first name + Wikidata) | Pipeline | 1 day | Gender for >95% |
| Download person photos from Wikidata/Parliament CDN | Pipeline | 1 day | Photos for >80% current MPs |

### Pillar 2: Question-Driven UI Redesign (Week 2-3)
**Goal:** Replace tab sprawl with **perspectives** that answer specific questions.

#### New IA (Information Architecture)

```
┌─ HOME / DASHBOARD ────────────────────────────────────────┐
│  "What's happening NOW?" — Live feed + today's switches   │
├─ PARTY ANALYSIS ──────────────────────────────────────────┤
│  ├── Party Profile (size, age, gender, switch rate,      │
│  │   committee control, loyalty score, asset stats)       │
│  ├── Party Comparison (side-by-side any 2-3 parties)      │
│  └── Party Genealogy (mergers, splits, renames over time) │
├─ PERSON DEEP-DIVE ────────────────────────────────────────┤
│  ├── Career Timeline (local → national → EU, all roles)   │
│  ├── Loyalty Score (votes w/ party, switches, tenure)     │
│  ├── Network (co-sponsorship, committee overlap, same     │
│  │   party switches)                                      │
│  └── Assets & Interests (declarations, conflicts)         │
├─ INSTITUTIONAL VIEW ──────────────────────────────────────┤
│  ├── Chamber Composition (by party, not just group)       │
│  ├── Committee Control (which party chairs what)          │
│  ├── Bureau & Leadership (party representation)           │
│  └── Cross-Chamber MPs (served in both)                   │
├─ ELECTORAL DYNAMICS ──────────────────────────────────────┤
│  ├── Switch Waves (post-election, post-govt formation)    │
│  ├── Defection Patterns (source→dest party matrix)        │
│  └── Loyalty by Legislature (cohort analysis)             │
└─ EXPORT / API ────────────────────────────────────────────┤
   ├── Popolo + CSV (current)                                │
   └── GraphQL endpoint for custom queries                   │
```

#### Component Audit — Keep / Refactor / Delete

| Component | Verdict | Action |
|-----------|---------|--------|
| `ChamberView` + `Hemicycle` | **Keep** | Enhance: show party dots inside group arcs |
| `TimelineChart` | **Refactor** | Dual-axis: groups + parties; add election markers |
| `DefectionSankey` | **Refactor** | Add party-level sankey; filter by legislature |
| `DefectionsList` | **Refactor** | Group by "wave" (election cycle), show net party flow |
| `PartyFlowDetail` | **Merge** | → Party Profile page |
| `CurrentLegislatureView` | **Refactor** | → Party Analysis > Current Legislature |
| `PersonDrawer` | **Refactor** | → Person Deep-Dive modal with tabs |
| `About` | **Keep** | Move to footer link |

### Pillar 3: Analytical Layer — "Conclusions Engine" (Week 3-4)
**Goal:** Pre-compute insights so UI shows *answers*, not just raw data.

| Insight | Computation | UI Surface |
|---------|-------------|------------|
| **Loyalty Score** per MP | `(votes_with_party / total_votes) * tenure_weight` | Person badge, Party ranking |
| **Switch Wave Detection** | Cluster switches by 30-day windows post-election/govt | "Wave 3: Post-2020 election (47 switches)" |
| **Committee Control Index** | `party_chairs / total_committees` per legislature | Party Profile > Institutional Power |
| **Cross-Chamber Career** | Identify MPs in both chambers; map trajectory | Person Deep-Dive > Career |
| **Asset Anomaly Flags** | ML: declare vs peers, sudden changes | Person > Assets tab (red flags) |
| **Party Cohesion** | Std dev of loyalty scores within party | Party Comparison |
| **Generational Shift** | Avg age per party per legislature | Party Profile > Demographics |

### Pillar 4: External Integrations (Ongoing)
| Source | Value | Priority |
|--------|-------|----------|
| **Chamber stenograme (voting)** | Loyalty scores, rebellion tracking | P0 |
| **ANAF asset declarations** | Wealth tracking, conflict detection | P0 |
| **Monitorul Oficial (Senate history)** | Complete Senate 1990-2020 | P1 |
| **Wikidata** | Bios, photos, party history, EU refs | P0 |
| **GDELT / NewsAPI** | Media mentions, scandal tracking | P2 |
| **EU Parliament MEPs API** | Cross-mandate tracking | P2 |
| **Local election data (BEC)** | Mayoral → MP pipeline | P3 |

---

## Research: 3 Successful Implementations per Problem

### Problem 1: Parliamentary Tracking with Enrichment

| Project | Key Technique | Adoptable |
|---------|---------------|-----------|
| **EveryPolitician / Popolo** (archive) | Standardized Popolo schema; CSV/JSON releases; scraper per country | Schema ✅ (we use Popolo); Scraper pattern ✅ |
| **ParlTrack (EU)** | Real-time EP monitoring; dossier tracking; MEP profiles with votes | Dossier tracking → legislative initiatives; Vote API → loyalty |
| **TheyWorkForYou (UK)** | Hansard parsing; MP attendance; voting record; email alerts | Hansard → stenograme parsing; Attendance API |
| **OpenStates (US)** | Bill tracking; legislator profiles; vote comparison; district mapping | Bill tracking → legislative initiatives; District → constituency |

### Problem 2: Party Switching / Defection Analysis

| Project | Key Technique | Adoptable |
|---------|---------------|-----------|
| **ParlGov** (party systems) | Party genealogy (merge/split/rename); cabinet participation; election results | Party genealogy ✅ (we have `alt_labels`); Election results → seat share |
| **Manifesto Project** | Party positions over time (CMP coding) | Not directly; but party ideology tags useful |
| **V-Party-Dem (V-Dem)** | Party institutionalization, personalism, cohesion indices | Cohesion index → our Loyalty Score |

### Problem 3: Wikidata Enrichment at Scale

| Project | Key Technique | Adoptable |
|---------|---------------|-----------|
| **Wikidata Integrator (Python)** | Batch SPARQL; local cache; rate limiting; retry logic | Direct library use |
| **WikiProject Parliaments** | Standardized properties (P39, P2937, P4100, P102, P569) | Property map ✅ |
| **OpenRefine + Wikidata reconciliation** | Fuzzy match → review UI → batch upload | Reconciliation UI pattern for our `MatchReview` table |

### Problem 4: Senate Historical Reconstruction

| Project | Key Technique | Adoptable |
|---------|---------------|-----------|
| **Polish Sejm Historical** | PDF parsing of JO/Monitorul Oficial; OCR + template extraction | Same source (Monitorul Oficial) |
| **French Assemblée Historique** | XML/TEI encoding of historical sessions; prosopography | TEI export for our data |
| **Italian Camera Storica** | Linked open data for historical MPs; SPARQL endpoint | LOD publishing for our exports |

---

## Proposed 4-Week Sprint Plan

### Week 1: Data Completeness
- [ ] `pipeline/enrich.py` — Wikidata batch (birth_date, gender, photo, QID, party history)
- [ ] `pipeline/senat_historical.py` — Monitorul Oficial PDF parsing for Senate 1990-2020
- [ ] `pipeline/assets.py` — ANAF asset declarations ingestion
- [ ] DB migration: add `gender`, `photo_url`, `asset_declarations` table
- [ ] Validation: >90% persons enriched; Senate >80% all legislatures

### Week 2: Question-Driven UI
- [ ] Redesign routing: `/party/:short`, `/person/:id`, `/legislature/:year`, `/compare`
- [ ] Party Profile page (demographics, loyalty, committees, switches, assets)
- [ ] Person Deep-Dive (career timeline, loyalty, network, assets)
- [ ] Electoral Dynamics page (switch waves, defection matrix, cohort loyalty)
- [ ] Refactor TimelineChart (dual axis: groups + parties)
- [ ] Refactor DefectionSankey (party-level, legislature filter)

### Week 3: Analytical Layer
- [ ] Loyalty Score computation (requires voting data — start with switch-based proxy)
- [ ] Switch Wave detection (cluster by 30-day windows post-election)
- [ ] Committee Control Index per party/legislature
- [ ] Cross-Chamber Career mapping
- [ ] Party Cohesion & Generational Shift metrics
- [ ] API endpoints: `/api/analytics/*`

### Week 4: Polish & External Prep
- [ ] GraphQL endpoint for custom queries
- [ ] Wikidata reconciliation UI (for `match_review` table)
- [ ] Export: add analytics to Popolo/CSV
- [ ] Documentation: API.md, Data Model, Methodology updates
- [ ] Load test: 100 concurrent users on dashboard
- [ ] Staging deploy + stakeholder demo

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Wikidata rate limits / outage | High | Medium | Local cache (SQLite); exponential backoff; offline batch mode |
| Monitorul Oficial PDF parsing failures | Medium | High | Manual fallback for key legislatures; OCR + template matching |
| Voting data not available in machine-readable form | High | High | Start with switch-based loyalty proxy; push for open data |
| Scope creep | High | Medium | Strict 4-week timebox; "not in sprint" column on board |
| Frontend bundle size | Medium | Low | Code-split by route; lazy-load ECharts |

---

## Decision Required

**Approve this strategy?** If yes, I'll:

1. **Create detailed specs** for each sprint task (acceptance criteria, test cases)
2. **Spin up parallel agents** for: Wikidata enrichment, Senate historical, Asset ingestion, UI redesign, Analytics engine
3. **Set up weekly checkpoints** with working demos
4. **Deliver production-ready** Parlament Deschis v1.0 at end of Week 4

**Or:** Tell me which pillar to prioritize / deprioritize / change.

---

## Appendix: Current Codebase Health

| Area | Score | Notes |
|------|-------|-------|
| Pipeline architecture | 8/10 | Clean separation; fragment store; idempotent reconciliation |
| Data model | 7/10 | Bitemporal memberships; evidence; merge audit — missing: voting, assets, gender |
| API design | 7/10 | RESTful; temporal queries; exports — missing: GraphQL, analytics endpoints |
| Frontend architecture | 6/10 | React + TS + TanStack Query + ECharts — tab sprawl; no route-based code splitting |
| Test coverage | 8/10 | 86 tests; parser fixtures; temporal logic — missing: API integration, UI component tests |
| Documentation | 9/10 | Comprehensive: ARCHITECTURE, API, DATA-MODEL, METHODOLOGY, RESEARCH, CONTRIBUTING |
| DevOps | 5/10 | No CI/CD; no staging; manual deploy; no monitoring |

**Overall: 7.1/10** — Strong foundation, weak product-market fit.