# Parlament Deschis — frontend/API slice verification matrix
Repo: /home/nedaktov/parlament-deschis (HEAD ff9d461). CI = .github/workflows/ci.yml: test:17-41, audit:42-61, docker:63-87, evidence-guards:89-117.
Baseline (read, not assumed): `uv run pytest -q` 342 passed; `uv run ruff` clean; `cd frontend && npm ci && npm run build` exit 0 (frontend/package.json:8 `tsc -b && vite build`); audit strict 275 known errors / 0 new (ci.yml:59-61; tests/test_audit.py:160 vote_evidence registered). deploy-all.sh:20 `git add -A` footgun + :21 hardcoded commit message. verify-deploy.sh:1-255 prod contract. i18n ro+en in frontend/src/i18n.ts.
Frontend has NO vote feature (grep vote in frontend/src = 0 hits); vote tables empty in production → empty-state tests mandatory, no pretend data.

GATE: NO-GO until: (1) `cd frontend && npm ci && npm run build` exit 0; (2) `uv run pytest -q` all pass incl. new vote empty-state + REST/GraphQL convergence; (3) `uv run ruff check pipeline backend scripts tests` clean; (4) `uv run python -m pipeline.cli --db data/parlament.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json` → 275/0; (5) `bash scripts/check-doc-truth.sh` → false-claims: 0; (6) `python3 scripts/ui_validate.py` on new vote routes → 0 JS errors, 0 axe violations (NOT PROVEN locally: no playwright/chromium, ci.yml:104-117). Any FAIL = NO-GO, revert per §5.

1. TEST MATRIX (file → asserts → expected → rollback)
tests/test_api.py::test_committees_endpoint_returns_empty_list:649 | GET /api/committees?as_of= → 200 + [] | 200, body == [] | `git revert <sha> --no-edit -- backend/routers/api.py`
tests/test_graphql_convergence.py::test_empty_overridden_db_yields_empty_rest_and_graphql:221 | empty DB → REST [] and GraphQL [] | rest == [], gql.data.persons == [] | revert resolver commit; `git checkout <tag> -- backend/`
tests/test_votes_cdep_parser.py, test_votes_thirdparty_contract.py, test_votes_dry_run.py | vote fixtures parse; export↔JSON counts equal; dry-run never creates person, quarantines unresolved | parser/dry-run asserts pass | revert vote-importer commits; test_votes_build_isolation.py:48-55 stays green
frontend (NEW; 0 *.test.*, no vitest) | each new vote view renders empty table + ro/en "no votes"/"nu există voturi"; /api votes endpoints 200 + [] never 500 | renders empty, 200+[] | revert frontend view commit; feature-flag off if flagged (no flag yet — add before merge)
frontend build | `cd frontend && npm ci && npm run build` | exit 0 | revert build-breaking commit
audit strict | `--strict --baseline ...` | 275 errors / 0 new | revert audit-breaking change

2. ACCESSIBILITY (modern-web-guidance: accessibility/responsive-table/html)
- semantic table headers: <thead><th scope="col"> + sr-only <caption> per frontend/src/components/TimelineChart.tsx:251-257; new vote tables must match.
- focus order: no positive tabindex traps; scroll container tabIndex={0} role="region" (TimelineChart:249); keyboard-activatable chart controls.
- ARIA labels on charts: role="img" aria-labelledby/aria-describedby + sr-only description (TimelineChart:206-224).
- reduced-motion: respect prefers-reduced-motion; ECharts smooth:false, no scroll-linked motion (TimelineChart:113,127).
- colour-not-only-meaning: vote choice/party never encoded by colour alone; add text label or pattern.
- ui_validate.py:1-147: axe-core 4.10.2 scan target 0 violations, 0 console.error/pageerror, per-route table (routes:28-47); add new vote views to ROUTES.

3. PERFORMANCE BUDGET
- new view LCP ≤ 2.5s, CLS ≤ 0.1; empty table must not shift on data arrival (reserve skeleton/fixed height).
- ECharts bundle guard: modular imports only (TimelineChart:4-5, 487 KB min / 164 KB gzip vs monolith 1,040 KB / 345 KB); fail build if chunk grows >10%; no `import * as echarts from "echarts"` monolith.
- no client-side GraphQL library unless justified: frontend/package.json:12-24 has none; adding one requires bundle audit + owner sign-off.

4. REGRESSION RISK REGISTER (L/I/mitigation/owner)
1. Empty table mistaken for "no data" vs API error | M/H | client.ts:268-287 throws on non-ok; views must show error banner + retry distinct from empty state (TimelineChart:230-242) | page-builder
2. Party-cohesion REST vs GraphQL divergence | M/H | add convergence test like test_graphql_convergence.py:171-175 crossChamber matches REST for party-cohesion | backend
3. Vote importer leaks into corpus build (outage stops release) | L/H | test_votes_build_isolation.py:48-55 FORBIDDEN_TOKENS stays green | backend
4. deploy-all.sh `git add -A` (20) + hardcoded message (21) commits unintended files | M/M | run from clean tree; review `git status --short` before commit; prefer verify-deploy.sh | release
5. Stale dataset / release tag mismatch | L/M | verify-deploy.sh:209-212; check-doc-truth.sh:19 pins counts/tags | data

5. ROLLBACK PER STEP
- API route/shape change: `git revert <sha> --no-edit -- backend/routers/api.py`; public API shape changes are IRREVERSIBLE — use /api/v2 or a deprecation window, never silent removal.
- Frontend vote view: `git revert <sha> --no-edit -- frontend/src`; feature-flag off (no flag yet — add flag before merge).
- Build/config: revert package.json/tsconfig.json/vite.config.ts commit; `cd frontend && npm ci && npm run build` must return exit 0.
- Audit/count change: revert the change; re-run audit → 275/0.
- Tag restore: `git checkout <tag> -- <path>`; `git tag -d <badtag>` only if not pushed.

6. GO/NO-GO GATE — run in order, stop on first FAIL:
1 `cd frontend && npm ci && npm run build` → exit 0
2 `uv run pytest -q` → 342+ passed, 0 failed
3 `uv run ruff check pipeline backend scripts tests` → clean
4 `uv run python -m pipeline.cli --db data/parlament.db audit-corpus --strict --baseline data/reference/corpus-audit-baseline.json` → 275 errors, 0 new
5 `bash scripts/check-doc-truth.sh` → false-claims: 0
6 `python3 scripts/ui_validate.py <vote-url>` → 0 JS errors, 0 axe violations (NOT PROVEN without playwright/chromium)
ALL GREEN = GO. Any FAIL = NO-GO, revert §5, re-run gate. Assumed: no production vote data exists; every endpoint/contract tested against empty DB. Could not check: live axe/JS-error scan (runner lacks playwright/chromium), ECharts chunk-size CI guard (not wired yet), GraphQL-library absence is by package.json inspection only.