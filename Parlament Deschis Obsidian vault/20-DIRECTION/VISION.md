---
id: VISION
type: reference
title: "Parlament Deschis — corrected vision (2026-11-21)"
description: "The 10x thesis, trust invariants, corrected 15-feature tally, F-to-G-to-H frontend path, bounded self-sustainability promise, and the explicit document supersession chain."
status: active
authority: canonical
tags:
  - type/reference
  - lifecycle/active
  - domain/project
source_paths:
  - docs/GAP-ANALYSIS-2026-11-21.md
  - docs/POST-INITIAL-AUDIT-2026-11-21.md
  - docs/COMPREHENSIVE-REVIEW-2026-11-21.md
  - docs/AUDIT-RESOLUTIONS-2026-11-21.md
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
---

# Vision (corrected, 2026-11-21)

This is the current statement of intent for Parlament Deschis. It is written
after the 2026-11-21 review wave, which withdrew earlier "all complete"
claims. It describes the destination, not the shipped state. Live state is
tracked in [GAP-REGISTER](../10-STATE/GAP-REGISTER.md) and [CURRENT-STATE](../10-STATE/CURRENT-STATE.md).

Facts used here are pinned to HEAD `6fd6028`, three commits ahead of
`origin/main` `6b848f1` and unpushed. The production dataset release is
`data-20261117-T213500`: 3,388 persons, 7,349 prepared memberships,
1,217 group switches plus 785 party switches (2,002 events), 142 switch waves.
Production has no vote data. Local gates are green; CI is RED on main; `main`
has no branch protection; issue #14 is open.

## 1. The 10x thesis

Move the platform from "who changed parliamentary group, and when?" to a
trustworthy statistics layer answering how MPs actually voted, what parties
believe, where their electoral base is, and how Romania compares
internationally.

- **Single highest-value move:** roll-call votes as *first-class, dated
  events* — queryable by date, legislature, chamber and party, not a side
  table. This centrepiece is specified and locally tested but **not visible
  in production**, where the published corpus has no vote tables.
- **Supporting axes, in dependency order:** (a) biographies and profile
  completeness; (b) party covariates, ideology and loyalty; (c) committee
  and speech history; (d) elections, constituency base and cross-country
  benchmarks.
- The thesis is a *releases-and-provenance* programme, not a dashboard
  redesign: a new axis is only real once it is in a published, audited
  release.

## 2. Trust invariants (non-negotiable)

1. **Provenance on every row** — source URL, confidence, date precision and
   `dedup_key` accompany each ingested fact; an unprovenanced row is a
   defect, not an approximation.
2. **Strict audit gate** — `audit-corpus --strict` must pass with no new
   findings; 275 known / 0 new is the current local baseline. Gate weakening
   is not an acceptable repair.
3. **No attendance score** — presence is not a proxy for usefulness or
   integrity; the project explicitly refuses to manufacture one.
4. **Immutable, pinned releases** — the runtime is read-only; data changes
   only via a pinned, checksum-verified release, never an in-place rewrite.
5. **Fail-closed freshness** — if collection or audit fails, users keep the
   previous correct release; no partial data is published.
6. **Labelled definitions** — where two correct counts coexist (group-only
   versus group-plus-party switches; raw asset versus prepared memberships),
   both are published with their definition rather than silently choosing
   one.

## 3. The 15-feature transparency list — corrected tally

The original programme named fifteen capabilities: leaderboard, commitment
tracker, Senate gap page, demographics, committee control, party comparison,
PDF export, biography cards, person deep-dive, loyalty score, wave detection,
merger/split timeline, real-time alerts, coalition stability, MP comparison,
and load test. `STRATEGY-TRANSPARENCY.md` tabulated 17 rows (two duplicates),
which is why "15" and "17" both appear in older documents.

The withdrawn claim "all 15 features completed" is replaced by the audited
tally:

| Verdict | Count |
| --- | ---: |
| PRESENT | 11 |
| PARTIAL | 6 |
| wholly ABSENT | 0 |

Named residuals behind the six PARTIAL verdicts include party genealogy
(zero non-null predecessor/successor links), Senate historical profile ingest
(deferred on identity risk), real-time switch alerts (poller disabled in the
deployment configuration), one-dimensional coverage (mandates only; votes
and biographies missing as dimensions), H3–H5 frontend states, and
staging/load-test evidence (script exists, staged run not proven). Blog,
SEO and donations are **strategy-only**, not implemented, so they are not
counted as shipped features. Per-row evidence is in
[GAP-REGISTER](../10-STATE/GAP-REGISTER.md); the adjudication of the claim is
in [DECISIONS](DECISIONS.md).

## 4. Frontend F → G → H

- **Phase F — deep audit before repair.** Establish the real baseline with
  the modern-web-guidance pass: current framework versions, route inventory,
  accessibility and reflow probes, and a written design contract. No new
  pages in F; fix the broken rather than add the new. F work already landed
  locally includes the hooks-after-return CI fix, canonical API routes, vote
  date filters and provenance backfill — all unpushed, so not live.
- **Phase G — one system, calm civic design.** Dark, calm, civic visual
  language with one coherent token system, equal edges and one effect plus
  one or two dealt moments per page. De-facto icon family is inline SVG;
  a Lucide lock exists in an older design document but has no dependency
  or import. Remove dead code and finish the interactive states (H3-D and
  H4-A remain open). Governing accessibility level is WCAG AA, not AAA.
- **Phase H — proof and hardening.** Re-run UI validation across the full
  24-route set, require zero JavaScript errors and zero axe violations,
  verify reflow at 320 px, and prove production parity — locally green is
  not the same as live green. H's contract is evidence, not extra scope.

## 5. Self-sustainability — bounded promise

The promise is deliberately limited: hands-off, observable and recoverable
operation on free-tier infrastructure, with an explicit, tested manual
recovery path. It is **not** a 100% uptime promise and **not** fully
unattended publishing. A pinned release restarts the process, which resets
the in-process cache; the scheduler is best-effort because the upstream
external Romanian civic source (ro_281) may be unreachable from CI. The Vite
watchdog / Phase 4 work is still pending, so present operation depends on
manual local ingest when the source is down.

## 6. Blog, SEO and donations — strategy only

A 30-article bilingual, evidence-led content plan, canonical Vercel hosting
and a verified donation path are documented as strategy. Implementation has
not started: no blog directory, no article routes and no donation UI exist.
No delivery date is promised here; an owner decision to drop or to scope
this work is required before it enters [TASK-REGISTER](TASK-REGISTER.md)
as committed work.

## 7. Supersession chain (explicit)

Newer evidence wins on the same topic; a historical snapshot is preserved as
history and never used to override current state.

1. `STRATEGY.md`, `SPEC.md`, `ACTION_PLAN.md` and
   `STRATEGY-TRANSPARENCY.md` — **historical**, carry status-labels banners.
   Their TTL, feature-completion and route claims are superseded.
2. `MASTER-STRATEGY.md` — the consolidated 10x strategy; superseded on
   integration detail.
3. `MASTER-INTEGRATION-BLUEPRINT.md` — supersedes `MASTER-STRATEGY.md`.
4. `MASTER-INTEGRATION-BLUEPRINT-WAVE2.md` — supersedes the prior blueprint
   again for Wave 2 sequencing.
5. **2026-11-21 reviews** — `COMPREHENSIVE-REVIEW-2026-11-21.md`,
   `GAP-ANALYSIS-2026-11-21.md`, `POST-INITIAL-AUDIT-2026-11-21.md` and
   `AUDIT-RESOLUTIONS-2026-11-21.md` — current authority for state and for
   the withdrawal of stale claims.

Where a decision is reversed, a new decision entry is recorded rather than
editing the old one; see [DECISIONS](DECISIONS.md).
