---
id: CONTINUATION-STRATEGY
type: runbook
title: "Continuation Strategy — Parlament Deschis (2026-11-21)"
description: "Navigable mirror of docs/CONTINUATION-STRATEGY-2026-11-21.md: five-agent method, verified baseline, governing rules, master gates, Wave 0-4, session boundary and agent recipe."
status: active
authority: canonical
tags: [type/runbook, lifecycle/active, domain/project]
source_paths: [docs/CONTINUATION-STRATEGY-2026-11-21.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 96e6fdd
---

# Continuation Strategy — Parlament Deschis (2026-11-21)

> **Addendum (2026-11-21):** Re-anchored 2026-11-21 from `docs/CONTINUATION-STRATEGY-2026-11-21.md` §0.

This is a canonical, navigable mirror of `docs/CONTINUATION-STRATEGY-2026-11-21.md`. Start at [START-HERE](../00-START/START-HERE.md) for the current snapshot, use [TASK-REGISTER](TASK-REGISTER.md) for ordered next work, and read [ACTION-LOG](../10-STATE/ACTION-LOG.md) for the completed/remaining record and ranked next steps. The six authority rules in [MAINTENANCE-PROTOCOL](../00-START/MAINTENANCE-PROTOCOL.md) apply here too.

**Mandate.** No guessing, no assumptions, no presumptions. Every claim is backed by code, a command with printed output, a git fact, a live probe, or a cited source. If evidence is absent, record `NOT PROVEN` with a named resolver. Work is real, non-destructive, versioned on GitHub, and gated by evidence.

## 1. Method — five read-only strategy agents

Five parallel agents worked read-only: **S1** evidence inventory, **S2** GitHub best practice, **S3** missing-data acquisition, **S4** wave/rollback design, **S5** QA/security gates. Their reports are distilled in the source document; every step below inherits their evidence.

## 2. Verified baseline (do not assume older numbers)

| Fact | Verified value | Source |
| --- | --- | --- |
| Local HEAD | `96e6fdd`, branch `review/completion-20261121` | `git rev-parse HEAD` |
| Divergence | **8 ahead / 0 behind** `origin/main` (`6b848f1`) | `git rev-list --left-right --count origin/main...HEAD` |
| Unpushed commits | `3eb3c0a, 221cf78, 6fd6028, a311382, 537cef7, bf75556, bc4bee2, 96e6fdd` | `git log origin/main..HEAD` |
| Release pin | `data-20261117-T213500` | `data/latest-release.txt`, live `/api/health` |
| CI on main | `test` failure ×6 recent runs; `audit`/`evidence-guards` success; `docker` skipped | `gh api .../check-runs`, `gh run list` |
| Branch protection | **absent** (HTTP 404) | `gh api .../branches/main/protection` |
| Issue #14 | OPEN, 11 failed data runs, `ConnectTimeout` to `www.cdep.ro` | `gh issue view 14`, run `44729831051` log |
| Local gates | pytest 384, ruff clean, lint 0 errors, build 0, audit 275/0, doc-truth 0, UI 24/24 local / 23/24 live, vault lint + sync clean | `scripts/` gates, 2026-11-21 |
| Production | no vote data (`/api/votes total=0`), canonical ideology 404, live bundle `index-D61EXxHz.js` | live curl probes |

Detail: [GIT-POSITION](../10-STATE/GIT-POSITION.md), [CURRENT-STATE](../10-STATE/CURRENT-STATE.md), [RELEASE-AND-VERIFICATION](../10-STATE/RELEASE-AND-VERIFICATION.md).

## 3. Governing rules and authority

1. Evidence over assertion; `NOT PROVEN` beats a guessed PASS.
2. One fact, one home; hubs link, never duplicate status.
3. Never `git push --force`, `git reset --hard`, branch deletion, or tag moves. Rollback = `git revert <sha>` or a new pin commit; backups are additive tags.
4. Owner-only actions are marked 🔒: merge to main, branch protection, secret settings, releases, `workflow_dispatch`, deploys, product-policy decisions. Agents STOP and ask rather than presume authority.
5. An unavailable check reports `NOT PROVEN` and fails a required gate; no `|| true`, `continue-on-error`, silent skips, or auto-accepted baselines.
6. Licence/quarantine first: NC/SA/UNVERIFIED sources are display-only; every imported row carries `source_url` + SHA-256 + `dedup_key`; identity by exact ID → auto, name+DOB → propose, name alone → review; never name-only merges.
7. No attendance score; group-semantics reads always filter `Organization.classification == 'group'`.

## 4. Master gate table

| ID | Command | Expected | Waves | Waiver |
| --- | --- | --- | --- | --- |
| G01 | `.venv/bin/python -m pytest -q` | 384 passed, 0 failed | all | owner, dated |
| G02 | `.venv/bin/ruff check backend pipeline scripts tests` | All checks passed | all | owner |
| G03 | `cd frontend && npm run lint` | 0 errors | 1+ | owner |
| G04 | `cd frontend && npm run build` | exit 0 | 1+ | owner |
| G05 | `bash scripts/check-doc-truth.sh` | false-claims: 0 | all | none |
| G06 | strict audit `--baseline data/reference/corpus-audit-baseline.json` | 275 known / 0 new | 2+ | none (reviewed change only) |
| G07 | `node scripts/check_livefeed_props.mjs` | exit 0 | all | owner |
| G08 | `python3 scripts/ui_validate.py <dev-server>` | 24/24, zero JavaScript errors, zero axe | 1+ | owner (never waive a deliverable route) |
| G09 | `python3 scripts/vault_sync.py --check && python3 scripts/vault_lint.py` | clean | all | owner |
| G10 | `git diff --check` | empty | all | none |
| G11 | `sha256sum -c <backup manifest>` | all OK | all | none |
| G12 | live `gh pr checks <n>` | 4/4 SUCCESS | 1+ | owner |

No wave starts until the previous wave's gate is GREEN and its output is printed. AMBER = blocked on an owner decision; RED = stop and revert.

## 5. Wave 0–4 summary

### Wave 0 — Safety, versioning, backups (must be GREEN first)

W0.1 freeze baseline; W0.2 full backup bundle + DB copies + vault copy + manifest; W0.3 restore drill (restored HEAD = `96e6fdd`); W0.4 replace the destructive rollback recipe in `docs/DASHBOARD-STRATEGY.md` with `git revert` / `git checkout <tag> -- <path>`, drop the nonexistent `npm test` gate, align WCAG AA and the approved palette; W0.5 resolve the four-way Vite version conflict against shipped `^6.0.0` (cite `fb95e56`); **W0.6 re-anchor vault notes to real HEAD / 8 ahead and add this note**. GREEN = backup + restore drill + G05/G09/G11. See [GIT-POSITION](../10-STATE/GIT-POSITION.md) and [MAINTENANCE-PROTOCOL](../00-START/MAINTENANCE-PROTOCOL.md).

### Wave 1 — Land the already-made local fixes

W1.1 full local gate sweep; W1.2 push branch / open PR (authorized this session); W1.3 fix RED with normal commits only; W1.4 merge to main 🔒 (owner, not in this session); W1.5 branch protection 🔒; W1.6 Render backend verify 🔒; W1.7 Vercel frontend verify 🔒; W1.8 record evidence. See [CURRENT-STATE](../10-STATE/CURRENT-STATE.md), [GAP-REGISTER](../10-STATE/GAP-REGISTER.md), [TASK-REGISTER](TASK-REGISTER.md) and [DEPLOYMENT](../30-SYSTEM/DEPLOYMENT.md).

### Wave 2 — Data completeness and release (recipe specs; next session)

Ordered by dependency: W2.1 licence register; W2.2 honest coverage dimensions; W2.3 `cdep.ro` acquisition reliability; W2.4 vote release; W2.5 label the switch and membership discrepancies; W2.6 CHES / Party Facts; W2.7 Senate profiles / genealogy 🔒. Each step gets a standalone recipe with exclusive files, precondition, exact commands, printed checkpoint, `git revert` rollback, backup path and a `NOT PROVEN` clause. See [RESEARCH-LOG](../50-RESEARCH/RESEARCH-LOG.md), [DATA-RELEASE-PROCEDURE](../30-SYSTEM/DATA-RELEASE-PROCEDURE.md), [DATA-ENRICHMENT](../50-RESEARCH/DATA-ENRICHMENT.md) and [GAP-REGISTER](../10-STATE/GAP-REGISTER.md).

### Wave 3 — Vision gaps (recipe specs; later)

W3.1 genealogy (source decision first); W3.2 Senate profiles (copy-DB bit-identity gate); W3.3 multi-dimensional coverage; W3.4 frontend H3-D/H4-A + dead code + 7 lint warnings + one missing `type="button"`; W3.5 docs/vault truth pass; W3.6 decide 60 s poll vs "on release" alert semantics 🔒; W3.7 resolve GraphQL 404. See [VISION](VISION.md), [DECISIONS](DECISIONS.md) and [QA-AND-AXE](../40-FRONTEND/QA-AND-AXE.md).

### Wave 4 — Hardening (recipe specs; later)

W4.1 staging load-test evidence; W4.2 CSP enforcement decision (report-only is not protection); W4.3 blog/donations drop-or-scope decision 🔒; W4.4 Vercel Cron watchdog; W4.5 end-to-end `verify-deploy.sh` + freshness gate. See [ARCHITECTURE](../30-SYSTEM/ARCHITECTURE.md), [DEPLOYMENT](../30-SYSTEM/DEPLOYMENT.md) and [STRATEGY-BLUEPRINTS-HISTORICAL](../70-ARCHIVE/STRATEGY-BLUEPRINTS-HISTORICAL.md).

## 6. Cross-cutting sequences

- **GitHub hardening (owner-only where marked):** safe order is (1) backup refs; (2) push branch/PR [done this session]; (3) get CI green; (4) triage 9 PRs without bulk-close; (5) 🔒 block force-push and deletion, no required checks yet; (6) 🔒 require PR + 1 approval; (7) 🔒 add required checks "loose" after 7 green days; (8) 🔒 strict + include admins; (9) 🔒 secret scanning/push protection/Dependabot alerts; (10) 🔒 release immutability. Keep SHA-pinned actions, `permissions: {}` by default, and never require `data.yml` checks on PRs.
- **Missing-data acquisition:** official cdep facts only (`OGL-ROU-1.0`), hash raw bytes, quarantine unresolved vote positions; the external Romanian civic source (ro_281), Party Facts, CHES and Wikidata are licensed cross-checks or CC0/CC-BY; NC/SA sources are display-only; PolPaL licence NOT PROVEN — do not ingest. Dry-run on copies, keep `--strict`; if no licence-complete genealogy source exists, DROP the feature. See [SOURCE-RESEARCH](../50-RESEARCH/SOURCE-RESEARCH.md).

## 7. Session boundary (2026-11-21)

**Executed now:** W0.1–W0.6, W1.1–W1.3 and W1.8.

**Prepared but deliberately NOT performed:** W1.4–W1.7 are 🔒 owner / deploy runbooks — merge to main, branch protection, Render backend verification and Vercel frontend verification. Git observed at this re-anchor: `git rev-list --left-right --count origin/main...HEAD` → `0  8`, with no remote branch containing HEAD.

## 8. Agent recipe template (every step of every wave)

```
ID / ROLE         stable step id + specialist agent type
INPUTS            project root, vault path, baseline SHA, backup path
PRECONDITION      previous wave/step gate GREEN (print evidence)
EXCLUSIVE FILES   exact list; everything else is a side-quest -> REJECT
STEPS             numbered, each with exact command
CHECKPOINT        raw output + exit code; NOT PROVEN if unavailable
ROLLBACK          git revert <sha> / pin revert; never reset or force-push
BACKUP            BK path + sha256 manifest, verified before first edit
NO-FALSE-GREEN    no || true, no skip; missing tool = NOT PROVEN
SIDE-QUESTS       none; report any anomaly instead
REPORT            command output, changed files, residual, next owner action
```

## 9. Canonical source

The authority is the repository document `docs/CONTINUATION-STRATEGY-2026-11-21.md` (sections 0–12). This note is its vault mirror; if they diverge, re-verify with read-only commands and update both with a dated addendum. Engineered facts and unresolved claims are tracked in [RESEARCH-LOG](../50-RESEARCH/RESEARCH-LOG.md).
