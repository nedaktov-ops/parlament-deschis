# Post-initial audit — exhaustive, contradiction-resolved report (2026-11-21)

**Scope.** All 61 first-party Markdown files in `/home/nedaktov/parlament-deschis`,
processed newest-first (2026-11-21 → 2026-11-12). Five fresh agents (no prior
context) audited disjoint date buckets and cross-corpus patterns; the master
agent independently adjudicated contradictions and corrected its own earlier
errors. Read-only throughout: no product code, data, workflow or GitHub state
was changed by the fleet.

**Companions.** `docs/GAP-ANALYSIS-2026-11-21.md` (vision vs. live state) and
`docs/AUDIT-RESOLUTIONS-2026-11-21.md` (R1–R11 master adjudications).

---

## 1. Resolution policy (applied in this order)

1. **Executable evidence > prose** — current source, DB queries, API responses,
   CI/CLI output and generated artifacts outrank any document claim.
2. **Scope before conflict** — if two numbers differ, check definitions and
   artifacts first; call a defect only when both describe the same thing.
3. **Newer wins on the same topic**, but an explicitly labelled historical
   snapshot is preserved as history, not used to override current state.
4. **Addendum > base body** within a single file (dated current-state banners).
5. **Generated artifacts derive from source** — never hand-edit `openapi.json`.
6. **No guessing** — report NOT PROVEN with a named resolver.

## 2. Master-adjudicated contradictions (R1–R11)

See `docs/AUDIT-RESOLUTIONS-2026-11-21.md` for full evidence. Summary:

| ID | Short resolution |
|---|---|
| R1 | 2,002 vs 1,217 switches = **definitional** (group+party vs group-only). Pinned release: 1,217 group + 785 party = 2,002. Labelling gap, not a data bug. |
| R2 | 7,358 vs 7,349 memberships = **raw release asset vs prepared runtime DB** (9 duplicate stints removed). Live truth 7,349. |
| R3 | WAL vs DELETE = **different lifecycle stages**; shipped asset is DELETE. |
| R4 | "No vote tables" vs local votes = **scope** (published corpus vs gitignored working DBs). |
| R5 | OpenAPI 40/41/48 = stale generated file vs current regenerated 48 paths. |
| R6 | "All 15 features complete" = **historical claim, withdrawn**; genealogy/real-time/blog gaps remain. |
| R7 | Error-tracking "PASS" = **withdrawn**; no hook file exists. |
| R8 | UI gate RED/18/24 = all true for their dates; current 24/24. |
| R9 | CI "green" in review vs RED on GitHub = fixes are local-only, unpushed. |
| R10 | Release pin at an earlier tag vs current = chronological. |
| R11 | Claim of a bare `push:` in `ci.yml` = **false**; it filters `branches: [main]`. Corrected in GAP-ANALYSIS. |

## 3. Findings by date bucket (newest first)

### 2026-11-21 — newest docs (Agent A)
- `GAP-ANALYSIS.md` called itself newer than `COMPREHENSIVE-REVIEW.md` while
  citing the older HEAD `3eb3c0a`; corrected to HEAD `221cf78`.
- `GAP-ANALYSIS.md` claimed no doc claim was contradicted and that `ci.yml`
  had no branch filter — both false; corrected (R11).
- `GAP-ANALYSIS.md` reported "no vote data" without saying local working DBs
  hold unreleased votes; scope note added (R4).
- `GAP-ANALYSIS.md` listed 2,002 vs 1,217 as an unresolved P0; adjudicated as
  definitional (R1) with pinned-release evidence.
- `COMPREHENSIVE-REVIEW.md` cited `data/parlament-real.db` as "the pinned release
  corpus" — it is a gitignored working DB; wording must identify the actual DB.
- `COMPREHENSIVE-REVIEW.md` said "19 tracked files changed" — `git show --stat
  3eb3c0a` shows 22 files; corrected.
- Untracked `taste-report.md` / `verification-matrix.md` disagree
  (CONDITIONAL-GO vs NO-GO) and are stale at HEAD `ff9d461`; both are untracked
  evidence, not gates.
- `qa-notes.md:41` says axe "not configured in this repo yet (TBD)" — so no axe
  baseline exists at any commit; the gap report overstated one.
- `stack-choices.md:19` locks "Lucide React" while status at :21 admits TBD and
  no Lucide dependency/import exists — de-facto icon family is inline SVG.
- `COMPLETION-CERTIFICATE.md` is gitignored and self-admits it is outside the
  truth gate; its "No further action required" is superseded.

### 2026-11-19 / 2026-11-18 — remediation and frontend strategies (Agent B)
- `EVIDENCE.md`'s 2026-11-21 withdrawal wins over its base body and over
  `WAVE-4-COMPLETION.md:39`, which still says the error-tracking hook is
  "available for integration" — no such file or symbol exists.
- `WAVE-4-COMPLETION.md` cites `dd463d1`/`23b5b81`/`1d72d06` as upgrade proof,
  but those commits changed only evidence files; the shipped React 19 / Vite 6
  bump is `fb95e56`, and `npm ls` reports React 19.3.1, not 19.0.0. Its
  "production-ready" claim is a dated snapshot (open residuals, no branch
  protection, live ideology 404).
- `WAVE-4-RECIPES.md` has a four-way Vite version conflict: R-D0.3 titled
  "Vite 8", procedure `^5.0.0`, STATE.md "Vite 6", shipped `^6.0.0`.
  `WAVE-4-STRATEGY.md` recommends Vite 8 with a rollback tag differing from its
  stated baseline.
- `WAVE-4-SUPERVISOR.md` ticks "STRATEGY.md approved" and "recipes for each
  task" while `STATE.md:52` says recipes are pending stakeholder review —
  approval NOT PROVEN.
- `STATE.md`'s per-part SHAs (`1fcd577`, `2aa5401`, integration `58ec23f`) are
  git objects but **not ancestors** of main or this branch; they describe
  abandoned worktrees. The on-branch fix is `b69c820`.
- `RECIPES.md` uses `python3 scripts/check-hook-order.mjs` (should be `node`)
  and requires `scripts/check-reflow.mjs`, which does not exist.
- `FRONTEND-UX-10X-STRATEGY.md`: H3-A/B/C and H5 dead-code removals are marked
  PENDING but were silently completed; H3-D (states applied) and H4-A (footer
  polish) genuinely remain open. It also says "10 pages" where its own table
  lists 16, mandates `<html data-type>` attributes absent from `index.html`,
  and still reports `pytest 259`.
- `DASHBOARD-STRATEGY.md:411-449` declares "IMPLEMENTATION COMPLETE – FINAL
  STATUS" while its Phase 6 `npm test` / `ui_validate` and verification boxes
  are unticked; `npm test` does not exist in `package.json`. It requires WCAG
  AAA (governing rule: AA) and offers a violet variant (forbidden by the newer
  design doc). Its emergency rollback uses `git reset --hard`, `--force` push
  and branch deletion — directly against the non-destructive policy.
- Fresh agent re-ran `ui_validate.py`: 24/24 PASS against the local backend;
  23/24 against the live proxy because `/api/analytics/ideology` 404s. Ruling:
  24/24 is proven for the repo; **production remains NOT PROVEN**, exactly as
  the `DASHBOARD-VERIFICATION.md` addendum warns for its own audit.

### 2026-11-17 / 2026-11-14 — strategy, ADRs, deployment (Agent C)
- `STRATEGY-TRANSPARENCY.md` promises "all 15 features completed" while its own
  banner admits contradictions; its tables actually contain **17 rows** (two
  duplicates) and recipes numbered 1-12, 12, 15. Presence audit: **11 PRESENT,
  6 PARTIAL, 0 wholly absent** — so "all 15 completed" is not supportable.
- Feature 12 ("toast") conflicts with the shipped inline `role="alert"` banner
  and with `REMEDIATION-STRATEGY.md:24`, which forbids toasts. Code wins.
- Feature 15 claims load-test proof and staging deploy; only `scripts/load_test.py`
  exists — staging NOT PROVEN.
- Loyalty formula in the doc differs from code (`api.py:1771-1786` computes a
  ×100 inverted volatility score); code + UI i18n agree.
- `REMEDIATION-STRATEGY.md:76` forbids a 60 s poll against immutable data, yet
  `LiveFeed.tsx:45-48` sets `refetchInterval: 60_000` while the poller is
  disabled in `render.yaml:28-29` — the rule is violated in production. Either
  relabel alerts "on release" or enable a writing poller.
- `REMEDIATION-STRATEGY.md:159-165` still lists two false source comments that
  are now corrected in code (`cli.py:611-614`, `api.py:430-437`) — per the
  document's own rule, both rows should be removed.
- `AGENTS.md:18-19` claims `overscroll-behavior: contain` and a `popover`
  attribute are used in the frontend; neither exists in `frontend/src`
  (`CitationPopover` uses React state). The polyfill rule is currently moot.
- `AGENTS.md:7-10` vs `:15` internally contradict: popover is called "Baseline
  widely available… safe without fallbacks" but also requires a polyfill.
- `AGENTS.md:20` requires `type="button"` on all buttons; one violation remains
  at `frontend/src/components/PartyComparisonMatrix.tsx:77-80` (code fix
  recommended, not applied in this read-only audit).
- `VERIFICATION.md:59-73` says `vote_evidence` 0 errors / 0 warnings; an audit
  on a DB copy produced 173 warnings over 177 votes (all other check counts
  reproduce exactly). Its reconciliation arithmetic (141+3+2 ≠ 143) also
  needs clarification, and it lacks a current-state banner.
- `SELF-SUSTAINABILITY-ARCHITECTURE.md` §6 says the marker push starts neither CI
  nor Render, while Phase 2 calls it "marker-triggered deployment"; `data.yml:142-152`
  explicitly POSTs Render, so §6 is right and Phase 2 wrong.
- `DEPLOYMENT.md` claims `vercel.json` sets `ignoreCommand: ""`; the current file
  has no such key (removed in `b44778e`) — stale claim in two places.
- `DEPLOYMENT.md:45` lists three CI jobs; there are four (`evidence-guards`), and
  ":keep main protected" is an unmet requirement, not a current fact.
- `AUDIT.md:103-127` marks five P0 findings "open" although all are fixed in
  code; `AUDIT.md:109`'s "every departure CHANGED_PARTY" is fixed in `ingest.py`
  but `events.py:460` still hardcodes that reason for derived party events.
- `ACTION_PLAN.md`: every ✅ DONE item is present in current code (no revert
  needed); its PENDING/IN-PROGRESS labels are stale but banner-covered.
- `ADR-0001` TTL 300 s is current (`backend/cache.py:28`); `SPEC.md`'s 1 h is
  historical. `ADR-0002`'s counts (7,358) are stale; its tag pointer is not.

### 2026-11-12 — oldest docs and cross-corpus patterns (Agent D)
- **0 broken internal Markdown links** (95 targets parsed, 34 local, all resolve).
- Stale "CLI not wired" claims: `coverage` (`ARCHITECTURE.md:270`,
  `METHODOLOGY.md:184-185`), `enrich` (`METHODOLOGY.md:244-245`), `serve`
  (`CONTRIBUTING.md:69-71`) — all present in `pipeline.cli --help`.
- Non-existent routes in docs: `SPEC.md:146` `/api/analytics/cohesion`,
  `SPEC.md:166` `/api/analytics/generations`, `METHODOLOGY.md:393`
  `/analytics/waves` (actual paths carry `/api` and different names).
- `DATA-MODEL.md` lists `switch_wave` both as persisted ORM table (:172) and as
  computed-on-demand (:356) — DB has 142 rows; ORM section is correct.
- `docs/API.md:338-357` omits the live `GET /api/metrics` endpoint.
- `docs/ARCHITECTURE.md:46` references a non-existent `pipeline/evidence.py`.
- Six high-signal unchecked `- [ ]` boxes beside "COMPLETED/DONE" prose
  (e.g. `DASHBOARD-STRATEGY.md:296-297`).
- Drift counts: 3 distinct release tags; 10 distinct pytest counts (86…384);
  7,349 ×29 vs 7,358 ×27 membership mentions; 26/23/9 committee counts (all
  defensible under distinct definitions); OpenAPI 40→48; React 18→19,
  Vite 5→6, Node 18→24.
- Date anomaly: `2025-11-12` stated in `RESEARCH.md`, `STRATEGY.md` and
  `DATA-ENRICHMENT-RESEARCH.md` while git first-add is `2026-11-12` (9 occurrences).
- `LICENSE-APPENDIX.md` says licence rows are mirrored in `source_license`;
  master check: pinned release has **no** `source_license` table, both working
  DBs have the table with **0 rows**, and `ensure_source_licenses()` is defined
  (`pipeline/licenses.py:215`) but not called from CLI or app startup.
  **Licence enforcement is latent — a real incomplete component.**
- 0 licence/attribution violations found; required attribution string present.
- `AUDIT-RESOLUTIONS.md` was untracked mid-audit; now to be committed.

## 4. Authoritative current state (after resolution)

- Production release: `data-20261117-T213500`; 3,388 persons, 7,349 prepared
  memberships (7,358 raw asset); 1,217 group switches (+785 party switches =
  2,002 events); 142 switch waves; 26 committee orgs, 23 with active
  memberships, 9 with active chairs.
- Published corpus has **no vote or CHES tables**; local working DBs do, but are
  gitignored and unreleased.
- Local HEAD `221cf78` (two commits above GitHub `main` `6b848f1`); all fixes in
  those commits are unpushed and therefore absent on Vercel/Render.
- CI is RED on main; branch protection absent; issue #14 open (cdep.ro timeouts).
- Gates green locally at HEAD: pytest 384, ruff clean, lint 0 errors, build 0,
  strict audit 275/0, doc-truth 0, UI 24/24 with zero JS/axe findings.

## 5. Open items / NOT PROVEN

- Live DB identity behind "published corpus" for local audit runs.
- Real date of the "2025-11-12" research (git says 2026-11-12).
- Whether `source_license` seeding ever runs in production.
- Exact Vercel build commit (strongly inferred `6b848f1`).
- Client-side rendering of SPA routes; runtime read-only enforcement.
- Deployment ordering; `2026-11-20` live robots/licence bytes (offline audit).

## 6. Recommended documentation repairs (in priority order)

1. Commit this report and its companions; re-run `check-doc-truth.sh` (green).
2. Fix stale CLI claims (`coverage`, `enrich`, `serve` wired) and invented routes
   (`SPEC.md:146,166`; `METHODOLOGY.md:393`). Add `/api/metrics` to `docs/API.md`.
3. Add explicit labels for the two switch definitions and the two membership
   counts in `docs/API.md` and `README.md`.
4. Re-license-align `MASTER-STRATEGY.md` and `DATA-ENRICHMENT-RESEARCH.md` with
   `LICENSE-APPENDIX.md` (vot-parlament cross-check-only; PopuList unverified;
   four Party Facts IDs).
5. Update `stack-choices.md` icon lock to the de-facto inline-SVG family, or add
   Lucide deliberately; correct `AGENTS.md` (no popover/overscroll usage, no
   polyfill need) and add the one missing `type="button"`.
6. Date-stamp all recon snapshots with their commit hashes; mark the untracked
   QA reports historical or delete them after migrating their evidence. Remove
   stale "false source comment" rows from `REMEDIATION-STRATEGY.md §9`.
7. Wire `ensure_source_licenses()` into an explicit, tested startup/CLI path.
8. Resolve the four-way Vite version conflict and mark Wave-4 approval ticks
   NOT PROVEN; cite `fb95e56` as the real dependency-bump commit.
9. Replace `DASHBOARD-STRATEGY.md`'s destructive rollback recipe with `git revert`
   / `git checkout <tag> -- <path>`, drop the non-existent `npm test` gate, and
   align WCAG AAA→AA and violet→approved palette.
10. Relabel the 15-feature "all complete" claim as 11 PRESENT / 6 PARTIAL, and
    either remove the 60 s poll against immutable data or relabel alerts "on release".
