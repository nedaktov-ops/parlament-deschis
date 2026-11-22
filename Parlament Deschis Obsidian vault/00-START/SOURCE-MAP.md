---
id: SOURCE-MAP
type: source-map
title: "Vault note → authoritative source map"
description: "Maps every planned vault note to the repo path(s) that are authoritative for its content."
status: active
authority: derived
tags: [type/source-map, lifecycle/active, domain/project]
source_paths: [docs/POST-INITIAL-AUDIT-2026-11-21.md, docs/GAP-ANALYSIS-2026-11-21.md, docs/AUDIT-RESOLUTIONS-2026-11-21.md, docs/COMPREHENSIVE-REVIEW-2026-11-21.md]
created: 2026-11-21
updated: 2026-11-22
source_commit: 6fd6028
verified: 2026-11-21
---

# Source map

All paths are **repo-relative** to `/home/nedaktov/parlament-deschis`. Per the [resolution policy](MAINTENANCE-PROTOCOL.md), executable sources (code, DB, API, CI output, generated artifacts) outrank prose; a doc is authoritative only when no executable source covers the claim. Rebuild derived notes with `python3 scripts/vault_sync.py`.

Status vocabulary in the table: `active` (current truth), `stale` (newer source exists), `archived` (history only), `mirror` (copy of a source, never hand-edit content), `derived` (generated from sources).

| # | Vault note | Folder | Authoritative source path(s) | Status |
|---:|---|---|---|---|
| 1 | [START-HERE](START-HERE.md) | 00-START | `docs/POST-INITIAL-AUDIT-2026-11-21.md`; `docs/GAP-ANALYSIS-2026-11-21.md`; `docs/AUDIT-RESOLUTIONS-2026-11-21.md` | active |
| 2 | [SOURCE-MAP](SOURCE-MAP.md) | 00-START | build brief + `git ls-files` repo tree; `scripts/vault_sync.py` | active / derived |
| 3 | [MAINTENANCE-PROTOCOL](MAINTENANCE-PROTOCOL.md) | 00-START | `docs/AUDIT-RESOLUTIONS-2026-11-21.md` §resolution policy; LLM update ritual from research | active |
| 4 | [CURRENT-STATE](../10-STATE/CURRENT-STATE.md) | 10-STATE | `docs/COMPREHENSIVE-REVIEW-2026-11-21.md`; `docs/POST-INITIAL-AUDIT-2026-11-21.md` §4 | active |
| 5 | [CONTRADICTIONS](../10-STATE/CONTRADICTIONS.md) | 10-STATE | `docs/AUDIT-RESOLUTIONS-2026-11-21.md`; `docs/POST-INITIAL-AUDIT-2026-11-21.md` §2 | active |
| 6 | [RELEASE-AND-VERIFICATION](../10-STATE/RELEASE-AND-VERIFICATION.md) | 10-STATE | `docs/COMPREHENSIVE-REVIEW-2026-11-21.md`; `docs/VERIFICATION.md`; `data/latest-release.txt`; CI/CLI output | active |
| 7 | [GIT-POSITION](../10-STATE/GIT-POSITION.md) | 10-STATE | `git` refs/HEAD/rev-list; `.github/workflows/ci.yml`; `docs/GAP-ANALYSIS-2026-11-21.md` §3 | active / derived |
| 8 | [GAP-REGISTER](../10-STATE/GAP-REGISTER.md) | 10-STATE | `docs/GAP-ANALYSIS-2026-11-21.md` §4; `docs/POST-INITIAL-AUDIT-2026-11-21.md` §5 | active |
| 9 | [VISION](../20-DIRECTION/VISION.md) | 20-DIRECTION | `docs/MASTER-STRATEGY.md`; `docs/STRATEGY-TRANSPARENCY.md`; `docs/GAP-ANALYSIS-2026-11-21.md` §1 | active (historical labels) |
| 10 | [TASK-REGISTER](../20-DIRECTION/TASK-REGISTER.md) | 20-DIRECTION | `docs/ACTION_PLAN.md`; `docs/GAP-ANALYSIS-2026-11-21.md` §6 | active / derived |
| 11 | [DECISIONS](../20-DIRECTION/DECISIONS.md) | 20-DIRECTION | `docs/adr/*.md`; `docs/AUDIT-RESOLUTIONS-2026-11-21.md` | active |
| 12 | [WAVE-STATUS](../20-DIRECTION/WAVE-STATUS.md) | 20-DIRECTION | `docs/MASTER-INTEGRATION-BLUEPRINT.md`; `docs/MASTER-INTEGRATION-BLUEPRINT-WAVE2.md` | stale |
| 13 | [ARCHITECTURE](../30-SYSTEM/ARCHITECTURE.md) | 30-SYSTEM | `docs/ARCHITECTURE.md`; `backend/main.py` | active |
| 14 | [API](../30-SYSTEM/API.md) | 30-SYSTEM | `docs/API.md`; `backend/routers/api.py`; `pipeline/openapi.json` (regenerate, never edit) | active |
| 15 | [DATA-MODEL](../30-SYSTEM/DATA-MODEL.md) | 30-SYSTEM | `docs/DATA-MODEL.md`; `data/parlament.db` | active |
| 16 | [METHODOLOGY](../30-SYSTEM/METHODOLOGY.md) | 30-SYSTEM | `docs/METHODOLOGY.md`; `docs/SOURCE-ONBOARDING-RECIPE.md` | active |
| 17 | [DEPLOYMENT](../30-SYSTEM/DEPLOYMENT.md) | 30-SYSTEM | `docs/DEPLOYMENT.md`; `render.yaml`; `vercel.json`; `.github/workflows/ci.yml` | active |
| 18 | [DATA-RELEASE-PROCEDURE](../30-SYSTEM/DATA-RELEASE-PROCEDURE.md) | 30-SYSTEM | `docs/SOURCE-ONBOARDING-RECIPE.md`; `scripts/prepare_db.py`; `scripts/download_dataset.py`; `data/latest-release.txt` | active |
| 19 | [DESIGN-CONTRACT](../40-FRONTEND/DESIGN-CONTRACT.md) | 40-FRONTEND | `frontend/docs/design/brief.md`; `docs/DASHBOARD-STRATEGY.md` | stale (open TBDs) |
| 20 | [STACK-AND-TOKENS](../40-FRONTEND/STACK-AND-TOKENS.md) | 40-FRONTEND | `frontend/docs/design/stack-choices.md`; `frontend/docs/design/tokens.md`; `frontend/package.json` | mirror |
| 21 | [QA-AND-AXE](../40-FRONTEND/QA-AND-AXE.md) | 40-FRONTEND | `frontend/docs/design/qa-notes.md`; `scripts/ui_validate.py`; `docs/DASHBOARD-VERIFICATION.md` | derived |
| 22 | [SOURCE-RESEARCH](../50-RESEARCH/SOURCE-RESEARCH.md) | 50-RESEARCH | `docs/RESEARCH.md`; `docs/DATA-ENRICHMENT-RESEARCH.md` | active |
| 23 | [DATA-ENRICHMENT](../50-RESEARCH/DATA-ENRICHMENT.md) | 50-RESEARCH | `docs/DATA-ENRICHMENT-RESEARCH.md`; `docs/DATA-COMPLETENESS-RECOVERY.md` | active |
| 24 | [RESEARCH-LOG](../50-RESEARCH/RESEARCH-LOG.md) | 50-RESEARCH | `docs/RESEARCH.md`; `docs/POST-INITIAL-AUDIT-2026-11-21.md` §5 | active / derived |
| 25 | [AUDIT-2026-11-21](../60-EVIDENCE/AUDIT-2026-11-21.md) | 60-EVIDENCE | `docs/POST-INITIAL-AUDIT-2026-11-21.md` | mirror |
| 26 | [GAP-ANALYSIS-2026-11-21](../60-EVIDENCE/GAP-ANALYSIS-2026-11-21.md) | 60-EVIDENCE | `docs/GAP-ANALYSIS-2026-11-21.md` | mirror |
| 27 | [COMPREHENSIVE-REVIEW-2026-11-21](../60-EVIDENCE/COMPREHENSIVE-REVIEW-2026-11-21.md) | 60-EVIDENCE | `docs/COMPREHENSIVE-REVIEW-2026-11-21.md` | mirror |
| 28 | [DASHBOARD-VERIFICATION-2026-11-19](../60-EVIDENCE/DASHBOARD-VERIFICATION-2026-11-19.md) | 60-EVIDENCE | `docs/DASHBOARD-VERIFICATION.md` (dated addendum — scope-limited) | stale |
| 29 | [STRATEGY-BLUEPRINTS-HISTORICAL](../70-ARCHIVE/STRATEGY-BLUEPRINTS-HISTORICAL.md) | 70-ARCHIVE | `docs/MASTER-STRATEGY.md`; `docs/MASTER-INTEGRATION-BLUEPRINT.md`; `docs/MASTER-INTEGRATION-BLUEPRINT-WAVE2.md`; `docs/STRATEGY-TRANSPARENCY.md` | archived / historical |
| 30 | [COMPLETION-CERTIFICATE](../70-ARCHIVE/COMPLETION-CERTIFICATE.md) | 70-ARCHIVE | `COMPLETION-CERTIFICATE.md` (gitignored, outside the truth gate; self-withdrawn) | archived / superseded |
| 31 | [GITHUB-TOOLING-INVENTORY-2026-11-22](../50-RESEARCH/GITHUB-TOOLING-INVENTORY-2026-11-22.md) | 50-RESEARCH | external: GitHub REST API and live repository pages, read 2026-11-22 (no repo path authoritative; curation claims marked NOT PROVEN in the note) | unverified |
| 32 | [DEEP-DIVE-REDESIGN-2026-11-22](../50-RESEARCH/DEEP-DIVE-REDESIGN-2026-11-22.md) | 50-RESEARCH | `frontend/src/pages/LiveDashboard.tsx`; `frontend/src/components/{PartyNetwork,SwitchTimeline,CrossChamberFlow,LiveFeed}.tsx`; `frontend/src/i18n.ts` | derived |

`AGENTS.md` in this folder is the machine-readable operating contract, not a content note; it is self-authoring and is not counted in the 32 notes above.

## Conventions

- A `mirror` note is a verbatim projection — never hand-edit its body; regenerate it.
- A `derived` note may carry hand-written analysis, but every fact must point back to a listed source.
- If a source path does not resolve, mark the note `stale` and record the resolver rather than guessing.
