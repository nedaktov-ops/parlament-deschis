---
id: RESEARCH-LOG
type: state
title: "Research log and NOT PROVEN register"
description: "Canonical dated investigation log with commit anchors, five-agent audit provenance, and the register of claims that remain unproven with named resolvers."
status: active
authority: canonical
tags: [type/state, lifecycle/active, domain/research]
source_paths: [docs/CONTINUATION-STRATEGY-2026-11-21.md, docs/RESEARCH.md, docs/POST-INITIAL-AUDIT-2026-11-21.md, docs/GAP-ANALYSIS-2026-11-21.md, docs/COMPREHENSIVE-REVIEW-2026-11-21.md]
created: 2026-11-21
updated: 2026-11-22
source_commit: 96e6fdd
---

# Research log

> **Addendum (2026-11-21):** Re-anchored 2026-11-21 from `docs/CONTINUATION-STRATEGY-2026-11-21.md` §0. Vault mirror: [CONTINUATION-STRATEGY](../20-DIRECTION/CONTINUATION-STRATEGY.md).

This is the canonical **chronology and uncertainty register** for the vault.
Source dispositions are in [SOURCE-RESEARCH](SOURCE-RESEARCH.md) and
[DATA-ENRICHMENT](DATA-ENRICHMENT.md); frozen report snapshots are in
[AUDIT-2026-11-21](../60-EVIDENCE/AUDIT-2026-11-21.md),
[GAP-ANALYSIS-2026-11-21](../60-EVIDENCE/GAP-ANALYSIS-2026-11-21.md) and
[COMPREHENSIVE-REVIEW-2026-11-21](../60-EVIDENCE/COMPREHENSIVE-REVIEW-2026-11-21.md).

Every claim here follows the [resolution policy](../00-START/MAINTENANCE-PROTOCOL.md#1-resolution-policy):
executable evidence outranks prose; scope is checked before conflict; newer
wins unless explicitly historical; addendum beats base body; generated files
derive from source; anything unproven is reported with a named resolver.

## Commit anchors

| Anchor | Meaning |
|---|---|
| `96e6fdd` | **current HEAD — unpushed**; 8 commits ahead / 0 behind `origin/main`, branch `review/completion-20261121` |
| `6b848f1` | `origin/main` and GitHub default branch; the state the live services were probed against |
| `3eb3c0a` | local review commit: CI hook-order fix, canonical vote/ideology routes, accessibility repairs |
| `221cf78` | local commit adding the six-agent gap analysis |
| `6fd6028` | historical audit commit — recorded HEAD at the 2026-11-21 post-initial audit, superseded by this re-anchor |
| `data-20261117-T213500` | published dataset pin (3,388 persons, 7,349 prepared memberships, 26 committee orgs) — unchanged by the vault commits |

Unpushed series, oldest first (8): `3eb3c0a`, `221cf78`, `6fd6028`, `a311382`,
`537cef7`, `bf75556`, `bc4bee2`, `96e6fdd`. The five newest are vault mirror
commits; the three oldest are the review/audit commits described above.

## Dated investigation log

- **2025-11-12 (as *stated* in documents) / 2026-11-12 (git first-add).**
  `docs/RESEARCH.md`, `docs/STRATEGY.md` and
  `docs/DATA-ENRICHMENT-RESEARCH.md` date the first source survey to
  2025-11-12 in 9 places, while git records 2026-11-12. Their robots.txt
  snapshots are explicitly historical; see the anomaly entry below.
- **2026-11-17.** Release `data-20261117-T213500` published. The current
  release pin still points here; the pinned asset contains 18 tables and **no
  vote or CHES tables**, which is why production has no vote data.
- **2026-11-19 / 2026-11-20.** Frontend design contract drafted
  (`frontend/docs/design/*`); QA baseline recorded at commit `a655f98` with
  `npm run lint` (0 errors, 7 warnings) and `npm run build` passing; four
  low-fidelity wireframe notes written (no image exports). On 2026-11-20 the
  vote fixtures were captured byte-exact with a SHA-256 manifest, and the
  licence appendix recorded current robots facts.
- **2026-11-21 — comprehensive review.** One supervising master agent plus
  four parallel specialists with exclusive file ownership, then independent
  master verification of every claim. Found and fixed F1–F11 (CI hooks,
  canonical routes, date filters, `meta`, vote frontend, provenance backfill,
  doc-truth, widened 24-route UI gate and accessibility regressions). Verified
  locally: pytest 384 passed, ruff clean, lint 0 errors / 7 warnings, build 0,
  strict audit 275 known / 0 new, doc-truth 0, **24/24 UI routes with zero
  JavaScript errors and zero axe findings**. The fixes were never pushed.
- **2026-11-21 — gap analysis (six agents).** Four agents partitioned the 60
  project Markdown files by theme (vision, data/verification, operations,
  frontend design), one read GitHub state read-only, one probed Vercel +
  Render read-only. Result: 24/24 local UI validation but **23/24 against the
  live proxy**, because the canonical `/ideology` route 404s; live OpenAPI
  still 48 pre-fix paths; CI RED on main with no branch protection; issue #14
  open with 11 `cdep.ro` ConnectTimeout data-run failures.
- **2026-11-21 — post-initial audit (five agents).** See provenance below.
  Adjudicated R1–R11 and produced the authoritative current-state summary.
- **2026-11-21 — this re-anchor.** Local HEAD `96e6fdd`, eight commits above
  `origin/main` `6b848f1` (0 behind); all 2026-11-21 fixes remain unpushed and
  therefore absent from Vercel/Render.
- **2026-11-22 — external tooling inventory.** Three research rounds on
  website visual inspection, content/design and semantic understanding were
  consolidated into [GITHUB-TOOLING-INVENTORY-2026-11-22](GITHUB-TOOLING-INVENTORY-2026-11-22.md).
  Star counts were read from GitHub on 2026-11-22; curation and maintenance
  claims are marked NOT PROVEN in that note. No product or vault-generated
  file was changed by this research.
- **2026-11-22 — Deep Dive Views redesign.** A supervised agent fleet researched
  the section's history and the vault notes, then redesigned and QA-audited the
  "Vederi detaliate" section. Progress, verified fixes, upcoming work and NOT
  PROVEN items are recorded in
  [DEEP-DIVE-REDESIGN-2026-11-22](DEEP-DIVE-REDESIGN-2026-11-22.md).

## Five-agent post-initial audit — provenance

- **Corpus:** all **61 first-party Markdown files** in
  `/home/nedaktov/parlament-deschis`, processed **newest-first**
  (2026-11-21 → 2026-11-12).
- **Fleet:** **five fresh agents with no prior context**. They audited disjoint
  date buckets (2026-11-21; 2026-11-19/18; 2026-11-17/14; 2026-11-12) plus
  cross-corpus patterns; the master agent independently adjudicated every
  contradiction and corrected its own earlier errors.
- **Posture:** read-only throughout — no product code, data, workflow or
  GitHub state was changed by the fleet.
- **Companions:** the six-agent gap analysis above and
  `docs/AUDIT-RESOLUTIONS-2026-11-21.md` (R1–R11 adjudications with full
  evidence).
- **Highest-value corrections:** the 2,002 vs 1,217 switch totals are
  definitional (group+party vs group-only); 7,358 vs 7,349 memberships is raw
  asset vs prepared runtime DB; licence enforcement is latent; the Lucide icon
  lock is contradicted by inline-SVG code; `AGENTS.md` claims popover and
  overscroll usage that does not exist; one button lacks `type="button"`.
- Do not confuse this with the **six-agent** gap analysis or the **five-agent
  comprehensive review** — different fleets, different scopes, same date.

## NOT PROVEN register

Each item is a claim that must not be asserted as fact until its resolver is
executed. This register is authoritative for the vault.

| # | Claim / gap | Why unproven | Named resolver |
|---|---|---|---|
| N1 | Exact Vercel build commit | Probe showed a bundle hash different from the local build; strong inference is `6b848f1`, not direct proof | Read Vercel deployment metadata/build logs for the live deployment |
| N2 | Runtime read-only enforcement | Architecture says the DB is baked into a read-only image and the app is read-only; not observed at runtime | Inspect the running container filesystem and attempt a write-path probe on Render |
| N3 | Client-side rendering of SPA routes | SPA fallback is proven (several paths, including a nonsense path, return the same shell); that is not proof any route renders | Real-browser DOM/screenshot assertion against the live host for each route |
| N4 | Licence seeding in production | `ensure_source_licenses()` is defined but uncalled; pinned release has no `source_license` table, working DBs have it with 0 rows | Wire it into an explicit tested startup/CLI path, then query the deployed DB |
| N5 | Real date of the first source research | Documents say 2025-11-12; git first-add is 2026-11-12 (9 occurrences) | Original file metadata or interview with the author |
| N6 | Live robots bytes for 2026-11-21 | The fleet was offline during that probe; only the 2026-11-20 appendix bytes are verified | Re-fetch `robots.txt` from each host and compare byte counts |
| N7 | Production as a green QA scope | 24/24 is local only; live is 23/24 and the audit could not re-run the UI gate in its own environment | Re-run `scripts/ui_validate.py` against a deployed backend after pushing fixes |

## Resolution and write-back

When a resolver settles an item, update this register with the evidence and a
date, then mark the affected note's `verified` field and bump `updated`. Never
silently rewrite a dated entry; add an addendum. Governance is defined in
[MAINTENANCE-PROTOCOL](../00-START/MAINTENANCE-PROTOCOL.md) and note ownership
in [SOURCE-MAP](../00-START/SOURCE-MAP.md).

## Continuation strategy

The five-agent continuation strategy is mirrored in
[CONTINUATION-STRATEGY](../20-DIRECTION/CONTINUATION-STRATEGY.md), anchored on
`docs/CONTINUATION-STRATEGY-2026-11-21.md` §0. It supersedes the older
ahead/behind framing in this log; the superseded values survive only as dated
historical context above.
