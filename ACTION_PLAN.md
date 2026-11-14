# Action Plan — Parlament Deschis Statistical UX/UI Improvement

**Strategy (approved):** Fix data contract → add d3-sankey flow → coverage page → comparison/denominator.
**No new pages.** Each existing page keeps one coherent job.
**No guesswork.** Every change tested against live API.
**Rollback:** git tag `pre-github-20261113-115113` + tarball backup exist; new tag per phase.

---

## Phase 1 — Fix data contract (backend) — COMPLETE

| Step | Action | Evidence source | Status |
|------|--------|-----------------|--------|
| 1.1 | Fix `/api/chamber` cumulative-total → current members at date (legislature-bounded) | Verified: `total=319 legislature=2024 PSD=85` | ✅ DONE |
| 1.2 | Fix `/api/traseism/overview` to return full `TraseismScope` shape (`party`, `by_party`, `matrix`, `timing`; remove `party_switches*`) | `pipeline/traseism.py:traseism_overview` vs frontend `TraseismScope` type | ✅ DONE |
| 1.3 | Dedup `by_party` duplicates in `/api/traseism/summary` (AUR×3, NEAFILIATI×3, PNȚCD×3, UNR×2) | Verified: by_party has duplicates | ✅ DONE |
| 1.4 | Implement `/api/export/*` routes or remove `exportPopoloUrl`/`exportCsvUrl` helpers (404 risk) | `frontend/src/api/client.ts:244-256`; backend has no export routes | ✅ DONE |
| 1.5 | Wire up dead `traseism*` client functions (currently unused) | Verified: defined but never called | ⏳ PENDING (defer to Phase 4) |

---

## Phase 2 — Flow visualization (frontend) — COMPLETE

| Step | Action | Evidence source | Status |
|------|--------|-----------------|--------|
| 2.1 | Research d3-sankey integration pattern (verified repo: d3/d3-sankey, 947⭐) | `/tmp/opencode/research-10-statistical.md` | ✅ DONE |
| 2.2 | Add legislature→legislature flow diagram on `/traseism` (link width = switchers, hover = count/date/source) | Verified: `/api/traseism/summary` returns `matrix` with from→to counts | ✅ DONE |
| 2.3 | Test sankey renders without crashes on cyclic flows | Cycle-breaking removes smallest link in mutual pairs | ✅ DONE |

---

## Phase 3 — Coverage & provenance

| Step | Action | Evidence source | Status |
|------|--------|-----------------|--------|
| 3.1 | Add coverage/quality page (frictionlessdata pattern: % memberships dated, % switches sourced, gaps, last refreshed) | Verified: `/api/coverage` returns completeness per scope | IN PROGRESS |
| 3.2 | Add provenance chips on switch events (source URL + retrieval date) | Verified: every `EventItem.source_url` populated; `Evidence.snapshot_hash` exists | PENDING |

---

## Phase 4 — Comparison & denominator

| Step | Action | Evidence source | Status |
|------|--------|-----------------|--------|
| 4.1 | Legislature comparison table (legislatoR pattern: Legislature \| Chamber \| MPs \| Switches \| Rate per 100 MPs) | Verified: `/api/traseism/overview` returns all 20 scopes | PENDING |
| 4.2 | Switches per 100 MPs shown explicitly alongside raw counts (abjur pattern) | Verified: `switches_per_100_members` field exists | PENDING |

---

## Rollback points

| Point | What | How to rollback |
|-------|------|-----------------|
| R0 | Baseline before Phase 1 | `git tag pre-github-20261113-115113`; tarball at `/home/nedaktov/backups/parlament-deschis/` |
| R1 | After Phase 1 | New git tag `phase1-data-contract-20261114` |
| R2 | After Phase 2 | New git tag `phase2-sankey-20261114` |
| R3 | After Phase 3 | New git tag `phase3-coverage-20261114` |
| R4 | After Phase 4 | New git tag `phase4-comparison-20261114` |

---

## Test requirements (gate before any change lands)

- `cd /home/nedaktov/parlament-deschis && .venv/bin/python -m pytest tests/ -q` → 125 passed (baseline)
- `cd /home/nedaktov/parlament-deschis && .venv/bin/python -m pipeline.cli --db data/parlament-real.db audit-corpus` → 0 errors
- Live API curl on each changed endpoint returns real, non-empty data

---

## Research evidence (verified, NOT guessed)

- d3/d3-sankey (947⭐): directed flow between nodes, link width = flow quantity — ideal for legislature→legislature switch flows
- paride92/italyParlR (10⭐): two-chamber legislature-bounded data model — directly analogous to Camera+Senat
- frictionlessdata/data-quality-dashboard (32⭐): per-source quality statistics with gaps
- SidneyBissoli/ibge-br-mcp (14⭐): provenance block with source_url + data_vintage per response
- saschagobel/legislatoR (97⭐): legislature-vs-legislature comparative tables via stable person IDs
- abjur/brcities (12⭐): denominator-aware per-capita indicators
- tradingview/lightweight-charts (17,851⭐): lightweight canvas charts for constrained hosting
- devotees/biograph (25⭐): per-person dated timeline

Full report: `/tmp/opencode/research-10-statistical.md`

---

**Note on agents:** All launched subagents fail with HTTP 429 / "content safety screening unavailable." I am executing directly. If agents become available, I will delegate Phase 3+ frontend work.
