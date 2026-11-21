# Wave 4 Modernization Recipes — Action Plans for Improvement

**Companion to:** `WAVE-4-STRATEGY.md` · `SUPERVISOR-RECIPE.md` · `STATE.md`

---

## Universal Recipe Template

```markdown
## R-<ID> — <Task Name>

**Role:** <Specialist role>
**Worktree:** `/tmp/opencode/wt-<ID>`, branch `remediation/<ID>`
**Scope:** <exact files to modify>
**Backup:** Tag `eb069d2b` verified
**Rules:** Evidence-only; red→green; atomic commit; no push/deploy/secrets

### Procedure
1. <step>
2. <step>

### Checkpoints
| CP | Command | Expected |
|---|---|---|

### Rollback
```bash
git checkout <commit> -- <files>
```

### Verdict
```

---

## Phase 1: Dependency Upgrades (D-1.x)

### R-D0.1 — React 19 Compatibility Audit

**Role:** Senior React Engineer
**Worktree:** `/tmp/opencode/wt-D0.1`, branch `remediation/D0.1`
**Scope:** `frontend/package.json`, no runtime files
**Backup:** Tag `eb069d2b` verified
**Rules:** Only modify package.json, no breaking changes

### Procedure
1. Run `npm ls react` to identify current version
2. Check for deprecated APIs via `eslint-plugin-react`
3. Review React 19 release notes for breaking changes
4. Create compatibility matrix

### Checkpoints
| CP | Command | Expected |
|---|---|---|
| CP-D0.1.1 | `npm ls react` | Shows 18.3.1 |
| CP-D0.1.2 | `npx react-docgen-typescript` | No deprecated patterns |

### Rollback
```bash
git checkout eb069d2b -- frontend/package.json
```

### Verdict
```

---

### R-D0.2 — React 19 Upgrade Implementation

**Role:** Senior React Engineer
**Worktree:** `/tmp/opencode/wt-D0.2`, branch `remediation/D0.2`
**Scope:** `frontend/package.json`
**Backup:** Tag `eb069d2b` verified
**Dependency:** Must complete R-D0.1 first

### Procedure
1. Update React version in package.json to ^19.x
2. Update React DOM to ^19.x
3. Update react-dom package
4. Run `npm install` and resolve peer dependencies
5. Fix TypeScript errors from type definition changes
6. Update tests and verify no behavior changes

### Checkpoints
| CP | Command | Expected |
|---|---|---|
| CP-D0.2.1 | `npm install` | No peer dependency errors |
| CP-D0.2.2 | `npm run build` | EXIT:0 |
| CP-D0.2.3 | `npm run lint` | 0 errors |
| CP-D0.2.4 | `uv run pytest -q` | 286+ passed |
| CP-D0.2.5 | axe scan | 0 violations |

### Rollback
```bash
git checkout eb069d2b -- frontend/package.json
git checkout eb069d2b -- frontend/package-lock.json
npm install
```

### Verdict
```

---

### R-D0.3 — Vite 6 Upgrade Implementation

**Role:** Build Engineer
**Worktree:** `/tmp/opencode/wt-D0.3`, branch `remediation/D0.3`
**Scope:** `frontend/package.json`
**Dependency:** Must complete R-D0.2 first

**Shipped state (verified 2026-11-21):** `frontend/package.json` declares
`"vite": "^6.0.0"` and `"react": "^19.0.0"`. `npm ls vite react` resolves
`vite@6.4.6` / `react@19.3.1` under Node `v24.22.3`. The real dependency bump
is `fb95e56` — `git log -S'"vite": "^6.0.0"' -- frontend/package.json` returns
that commit alone, and it is the only one touching `package.json` and
`package-lock.json`. The commits `dd463d1`, `23b5b81` and `1d72d06` modify only
`EVIDENCE.md`; they are **evidence-only** records, not dependency bumps,
notwithstanding their `upgrade(...)` commit messages.

**HISTORICAL — superseded 2026-11-21:** this recipe previously carried a
title naming a later Vite major and a procedure step quoting the pre-upgrade
version string. Both were inconsistent with the shipped tree; the conflict is
recorded at `docs/POST-INITIAL-AUDIT-2026-11-21.md:80` and
`docs/GAP-ANALYSIS-2026-11-21.md:110`. Do not reintroduce those values.

### Procedure
1. Confirm `frontend/package.json` still declares `^6.0.0`; the upgrade already
   shipped in `fb95e56`. Do not reintroduce the superseded pre-upgrade value.
2. Run `npm install`
3. Run `npm run build` and fix any configuration issues
4. Verify HMR works in dev mode

### Checkpoints
| CP | Command | Expected |
|---|---|---|
| CP-D0.3.1 | `npm run build` | EXIT:0 |
| CP-D0.3.2 | `npm run dev` | Server starts on http://localhost:5173 |

### Rollback
```bash
git checkout eb069d2b -- frontend/package.json
```

### Verdict
```

---

## Phase 2: Generated Contracts (D-2.x)

### R-D2.1 — OpenAI Schema Generation Setup

**Role:** Backend API Engineer
**Worktree:** `/tmp/opencode/wt-D2.1`, branch `remediation/D2.1`
**Scope:** `backend/routers/`, `scripts/`, `docs/API.md`
**Dependency:** None

### Procedure
1. Verify FastAPI OpenAPI schema is accessible
2. Create script to extract and save to repo
3. Add CI workflow to update on push
4. Update docs/API.md

### Checkpoints
| CP | Command | Expected |
|---|---|---|
| CP-D2.1.1 | `curl localhost:8000/openapi.json | jq .info.title` | "Parlament Deschis" |
| CP-D2.1.2 | `npm run build` | EXIT:0 |

### Rollback
```bash
git checkout eb069d2b -- scripts/generate-openapi.sh docs/API.md
```

### Verdict
```

---

## Phase 3: Observability (D-4.x)

### R-D4.1 — API Metrics Endpoint Implementation

**Role:** Backend Observability Engineer
**Worktree:** `/tmp/opencode/wt-D4.1`, branch `remediation/D4.1`
**Scope:** `backend/routers/metrics.py`, `backend/main.py`
**Dependency:** None

### Procedure
1. Create metrics module with Prometheus format
2. Add middleware to track request metrics
3. Create `/api/metrics` endpoint
4. Test endpoint returns proper metrics

### Checkpoints
| CP | Command | Expected |
|---|---|---|
| CP-D4.1.1 | `GET /api/metrics` | HTTP 200, Prometheus format |
| CP-D4.1.2 | `uv run pytest -q` | 286+ passed |

### Rollback
```bash
git checkout eb069d2b -- backend/routers/metrics.py backend/main.py
```

### Verdict
```