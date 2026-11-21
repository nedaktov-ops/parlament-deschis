# Wave 4 Modernization Strategy — Post-Remediation Improvement Plan

**Version:** 1.0 · **Date:** 2026-11-19 · **Baseline:** `eb069d2b` (pre-remediation)
**Status:** ACTIVE — This is a strategic roadmap, not immediate remediation

> **Correction note — 2026-11-21 (evidence-backed).** The shipped tree declares
> `vite ^6.0.0` / `react ^19.0.0` in `frontend/package.json`; `npm ls vite react`
> resolves `vite@6.4.6` / `react@19.3.1` on Node `v24.22.3`. The commit that
> actually bumped the dependencies is **`fb95e56`**
> (`git log -S'"vite": "^6.0.0"' -- frontend/package.json` returns that commit
> alone; it is the only one touching `package.json` and `package-lock.json`).
> The commits `dd463d1`, `23b5b81` and `1d72d06` modified only `EVIDENCE.md`:
> they are **evidence-only**, not dependency bumps, notwithstanding their
> `upgrade(...)` messages. Sections 1.1 and 2.2 are corrected to match.
>
> **HISTORICAL / OBSOLETE (2026-11-21):** the "blocked by Node 18" reasoning in
> `docs/remediation/WAVE-4-COMPLETION.md:47,71` no longer holds — the runtime is
> Node v24.22.3 (`node --version`). Later-major evaluation is a separate gated
> programme (`docs/MASTER-STRATEGY.md:759`), not a current blocker.
>
> **NOT PROVEN (2026-11-21):** the approval tick at
> `docs/remediation/WAVE-4-SUPERVISOR.md:17` ("STRATEGY.md approved") and the
> "Error boundary hook: Available for integration" tick at
> `docs/remediation/WAVE-4-COMPLETION.md:39`. No dated approval record and no
> captured boundary-integration output were found; `STATE.md:52` says recipes
> are pending stakeholder review and `docs/POST-INITIAL-AUDIT-2026-11-21.md:83-85`
> records the approval as unproven. Resolver: the owner of those two files must
> attach dated evidence or relabel the ticks. Their history is preserved here;
> this note supersedes them without editing files outside this wave's ownership.

---

## Executive Summary

After completing Waves 1-3 remediation, this project has achieved:
- ✅ Wave 1: All P0 critical fixes integrated and verified
- ✅ Wave 2: All P1 correctness/security issues resolved
- ✅ Wave 3: All accessibility (axe) residuals fixed

The project is **functional and stable**. Wave 4 represents optimization and modernization opportunities that would enhance the codebase's maintainability, performance, and developer experience.

---

## Phase 1: Assessment & Gap Analysis

### 1.1 Current State Audit

| Component | Current Version | Recommended | Gap |
|---|---|---|---|
| **React** | ^19.0.0 (19.3.1 installed) | keep 19.x | Upgraded and shipped in `fb95e56` |
| **Vite** | ^6.0.0 (6.4.6 installed) | keep 6.x | Upgraded and shipped in `fb95e56` |
| **ECharts** | 5.5.1 | 6.x | New chart types, better performance |
| **Tailwind CSS** | 3.4.6 | 4.x | JIT engine, improved class handling |
| **i18next** | 23.12.0 | 27.x | Type improvements, better SSR |
| **Node.js** | v24.22.3 (verified 2026-11-21) | maintain 24.x | Earlier 18-based constraint is obsolete |
| **Python** | 3.12 | 3.13 | Latest stable |

### 1.2 Missing Infrastructure

| Feature | Status | Priority |
|---|---|---|
| **OpenAPI Schema Generation** | Not implemented | HIGH |
| **GraphQL Schema (`.graphql` file)** | Not committed | MEDIUM |
| **Generated TypeScript Client** | Not generated | HIGH |
| **API Metrics Endpoint (`/api/metrics`)** | Missing | HIGH |
| **Frontend Error Tracking** | Not implemented | MEDIUM |
| **Freshness Alert System** | Not implemented | MEDIUM |
| **Postgres Dual-Write Capability** | Not implemented | LOW (future scaling) |

---

## Phase 2: Modernization Action Plan

### Part D-1: Dependency Upgrades

#### 2.1 React 19 Upgrade Strategy

**Goal:** Upgrade from React 18.3.1 to React 19.x while maintaining compatibility.

**Action Plan:**
1. Audit current React usage patterns
2. Check for deprecated APIs
3. Update `frontend/package.json`
4. Run `npm install` and resolve peer dependency issues
5. Fix TypeScript errors from type definition changes
6. Update tests and verify no behavior changes

**Checkpoints:**
- CP-D1.1: `npm run build` → Exit 0
- CP-D1.2: `npm run lint` → 0 errors
- CP-D1.3: `uv run pytest -q` → 286+ passed
- CP-D1.4: axe scan → 0 violations

**Rollback:**
```bash
git checkout e9ef278 -- frontend/package.json
npm install
```

#### 2.2 Vite Upgrade Strategy (SHIPPED — Vite 6)

**Goal (2026-11-21):** keep the shipped `vite ^6.0.0` (resolved 6.4.6) build
green. The upgrade already landed in `fb95e56`; this is now a maintenance plan,
not a pending major-version migration.

**What shipped with the Vite 6 upgrade:**
- Build succeeds with Vite 6.4.6 and `@vitejs/plugin-react` 5.2.0
- Dev server starts on `http://localhost:5173` with working HMR
- All page routes render; G08 is the gate and production is NOT PROVEN

**Checkpoints:**
- CP-D1.5: `cd frontend && npm run build` → exit 0 with captured output
- CP-D1.6: `cd frontend && npm run dev` → server starts; HMR verified
- CP-D1.7: `python3 scripts/ui_validate.py <dev-server>` → 24/24, 0 axe violations

**Obsolete (2026-11-21):** earlier versions of this roadmap treated a further
major jump as blocked by Node 18. Node is now v24.22.3, so that constraint is
historical; any newer-major evaluation is a separate gated programme
(`docs/MASTER-STRATEGY.md:759`).

### Part D-2: Generated Contracts

#### 2.3 OpenAPI Schema Generation

**Goal:** Generate `openapi.json` from FastAPI schema and create generated TypeScript client.

**Action Plan:**
1. Configure FastAPI to expose OpenAPI schema at `/openapi.json`
2. Create script to extract and save schema
3. Generate TypeScript client via `openapi-typescript` or similar
4. Update `docs/API.md` with current endpoints
5. Add to CI to ensure diff-clean commits

**Checkpoints:**
- CP-D2.1: `curl http://localhost:8000/openapi.json | jq .info.title` → "Parlament Deschis"
- CP-D2.2: GitHub workflow generates schema on each push
- CP-D2.3: `scripts/generate-api-client.sh` → creates `frontend/src/api/client.ts`

#### 2.4 GraphQL Schema Export

**Goal:** Export GraphQL schema to `pipeline/schema.graphql`.

**Action Plan:**
1. Use Strawberry GraphQL's schema dump command
2. Add to CI/CD pipeline
3. Validate schema matches running API

**Checkpoints:**
- CP-D2.4: File `pipeline/schema.graphql` exists
- CP-D2.5: Schema introspection passes validation

### Part D-3: Observability

#### 2.5 API Metrics Endpoint

**Goal:** Create `/api/metrics` endpoint for monitoring.

**Action Plan:**
1. Create metrics module using `prometheus_client` or similar
2. Add endpoint to `backend/routers/`
3. Include Prometheus-formatted metrics:
   - Request counts by endpoint
   - Response times
   - Database query counts
   - Cache hit/miss ratios
4. Configure for Render/Vercel compatibility

**Checkpoints:**
- CP-D3.1: `GET /api/metrics` → HTTP 200
- CP-D3.2: Response includes Prometheus metrics format
- CP-D3.3: Metrics show non-zero values for active endpoints

#### 2.6 Frontend Error Tracking

**Goal:** Implement client-side error tracking.

**Action Plan:**
1. Add Sentry or LogRocket SDK
2. Configure environment-based initialization
3. Add error boundaries to catch React errors
4. Report uncaught exceptions

**Checkpoints:**
- CP-D3.4: Bundle includes error tracking SDK (check build size)
- CP-D3.5: `ErrorBoundary` component catches errors in dev

#### 2.7 Freshness Alert System

**Goal:** Implement data freshness monitoring.

**Action Plan:**
1. Create freshness check script
2. Add HTTP endpoint `/health/freshness`
3. Check last data ingestion timestamp
4. Return 200 if fresh, 503 if stale

**Checkpoints:**
- CP-D3.6: Endpoint returns proper freshness status
- CP-D3.7: CI includes freshness check in deployment gate

---

## Phase 3: Quality Assurance Framework

### 3.1 Integration Testing

**Goal:** Ensure all integrations work correctly after upgrades.

**Test Matrix:**
| Route | Expected | Verification |
|---|---|---|
| `/api/health` | 200, all headers | `curl -D -` |
| `/graphql` | Valid response | GraphQL query |
| `/api/export/report` | Fresh timestamp | Compare timestamps |
| `/api/timeline` | 200 or 422 (capped) | Request validation |

### 3.2 Performance Benchmarks

**Goal:** Establish baseline performance metrics.

**Metrics to Track:**
- Homepage load time (< 2s)
- GraphQL response time (< 1s)
- Database query count per request (< 10)
- CSS bundle size (< 100KB gzipped)

---

## Phase 4: Documentation & Knowledge Transfer

### 4.1 Upgrade Guides

Create upgrade guides for each major tool:
- `docs/UPGRADES.md` - Main upgrade documentation
- Per-tool guides with migration paths

### 4.2 Architecture Decision Records

Document architectural decisions for:
- Metrics endpoint design
- Error tracking strategy
- API contract generation

---

## Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Breaking API changes from React 19 | Medium | High | Staged rollout, thorough testing |
| Type errors from i18next 27 | Medium | Medium | Update types incrementally |
| Bundle size increase from Sentry | Low | Low | Use tree-shaking, measure sizes |
| Data consistency from dual-write | Low | High | Feature flag, rollback capability |

---

## Success Criteria

Wave 4 is considered complete when:
1. All dependency upgrades pass build/test/axe gates
2. OpenAPI schema and TypeScript client generated and committed
3. GraphQL schema exported to repository
4. `/api/metrics` endpoint functional with Prometheus metrics
5. Frontend error tracking implemented and verified
6. Freshness check system operational
7. All documentation updated
8. Zero regressions in existing functionality

---

## Next Steps

1. **Review this strategy** with project stakeholders
2. **Create individual sub-agent recipes** for each numbered task (D-1.1, D-1.2, D-2.1, etc.)
3. **Schedule upgrades** based on priority and risk assessment
4. **Begin with D-1.1 React 19 audit** as proof of concept

---

*This strategy document serves as the single source of truth for Wave 4 implementation. All sub-agent recipes must align with this plan.*