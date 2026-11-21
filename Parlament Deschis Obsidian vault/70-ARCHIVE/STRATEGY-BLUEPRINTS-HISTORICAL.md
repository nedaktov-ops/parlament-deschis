---
id: STRATEGY-BLUEPRINTS-HISTORICAL
type: archive
title: "Historical strategy and integration blueprints — supersession chain"
description: "Quarantined record of seven superseded strategy/blueprint documents, why each was replaced, the 2025-11-12 date anomaly, and pointers to current truth."
status: archived
authority: historical
tags: [type/archive, lifecycle/archived, domain/project]
source_paths: [STRATEGY.md, SPEC.md, ACTION_PLAN.md, docs/STRATEGY-TRANSPARENCY.md, docs/MASTER-STRATEGY.md, docs/MASTER-INTEGRATION-BLUEPRINT.md, docs/MASTER-INTEGRATION-BLUEPRINT-WAVE2.md]
created: 2026-11-21
updated: 2026-11-21
source_commit: 6fd6028
verified: 2026-11-21
---

# Historical strategy & integration blueprints

> **QUARANTINED ARCHIVE — NOT CURRENT TRUTH.** Every document below is
> superseded. Their dates, priorities, test counts, release pins and "COMPLETE"
> banners are preserved as evidence of what was believed *at the time*; none may
> be copied into a current-state claim. Current truth lives in
> [CURRENT-STATE](../10-STATE/CURRENT-STATE.md) and
> [CURRENT-STATE's companion gap ledger](../10-STATE/GAP-REGISTER.md). Adjudications are in
> [CONTRADICTIONS](../10-STATE/CONTRADICTIONS.md).

## Supersession chain

| # | Superseded document | Stated date | Why superseded | Pointer to current truth |
|---:|---|---|---|---|
| 1 | `STRATEGY.md` — red-team analysis & 10× improvement strategy | 2025-11-12 (stated; see anomaly) | Historical banner (2026-11-17): **proposed and never adopted as written**. Its "0/1,978 birth dates" and "0 Wikidata QIDs" figures are obsolete (shipped release: 3,113/3,388 with a birth date); ANAF items are explicitly excluded by later strategy; committee control is now 26 committees / 142 waves. | `SPEC.md` at the time; today [CURRENT-STATE](../10-STATE/CURRENT-STATE.md) |
| 2 | `SPEC.md` — 10× sprint specification & acceptance criteria | 2026-11-17 banner | Original sprint spec retained as history. Figures are as observed then (3,388 persons / 7,358 memberships, 3,113 birth dates, 26 committees, 142 waves). Its 86-test checkpoint, 1 h cache TTL and "CLI not wired" claims are stale (ADR-0001 sets TTL 300 s; the CLI commands are wired). Senate discovery is fixed; profile ingest deferred on identity risk, not source availability. | `ACTION_PLAN.md` at the time; today [API](../30-SYSTEM/API.md) + [DATA-MODEL](../30-SYSTEM/DATA-MODEL.md) |
| 3 | `ACTION_PLAN.md` — statistical UX/UI improvement plan | 2026-11-19 banner | Phase statuses, rollback points and test counts are as observed then. Every ✅ DONE item is still present in current code (no revert needed), but PENDING / IN-PROGRESS labels are stale — the banner says so. | `STRATEGY-TRANSPARENCY.md` at the time; today [TASK-REGISTER](../20-DIRECTION/TASK-REGISTER.md) + [GAP-REGISTER](../10-STATE/GAP-REGISTER.md) |
| 4 | `docs/STRATEGY-TRANSPARENCY.md` — 15-feature transparency strategy | 2026-11-17, banner 2026-11-19 | "All 15 features completed" is a **withdrawn historical claim**: the tables hold 17 rows (two duplicates) and the presence audit is **11 PRESENT / 6 PARTIAL / 0 wholly absent**. Feature 12 ("toast") conflicts with the shipped inline alert banner and a document that forbids toasts; feature 15's staging/load-test proof is not proven. Genealogy has 0 links. | [VISION](../20-DIRECTION/VISION.md) + [CONTRADICTIONS](../10-STATE/CONTRADICTIONS.md) (R6) + [CURRENT-STATE](../10-STATE/CURRENT-STATE.md) |
| 5 | `docs/MASTER-STRATEGY.md` — 10× parliamentary statistics platform | 2026-11-20 | Integration of seven read-only investigations; deliberately no implementation. Explicit evidence rule (VERIFIED / INFERRED / UNVERIFIED with named resolvers). Superseded by the later blueprint, whose fresh reconnaissance wins wherever it contradicts this document. Some figures (raw membership count, 1 h TTL) are stale. | `MASTER-INTEGRATION-BLUEPRINT.md` at the time; today [CURRENT-STATE](../10-STATE/CURRENT-STATE.md) |
| 6 | `docs/MASTER-INTEGRATION-BLUEPRINT.md` — final integration blueprint | 2026-11-20 | Declared authority order: fresh six-worker reconnaissance > this blueprint > MASTER-STRATEGY > research base. Its red-team table overturns prior assumptions (chamber mapping, vote semantics, party-lineage IDs, licence status, command scope, tool counts). Superseded by the Wave 2 blueprint; Wave 1 six NOT DONE items remain. | `MASTER-INTEGRATION-BLUEPRINT-WAVE2.md` at the time; today [GAP-REGISTER](../10-STATE/GAP-REGISTER.md) |
| 7 | `docs/MASTER-INTEGRATION-BLUEPRINT-WAVE2.md` — Wave 2 (frontend / vote API) | 2026-11-20, HEAD `752eff6` | "Wave 2 PRIMARY path complete and pushed; Waves 2-P5 / 3 / 4 planned" is a dated snapshot, not a current status. Its ground-truth table (vote tables 0 rows in production, SPA shell, 19 routes, no GraphQL client, group-scoped counts) has since been overtaken by the F1–F11 review. | [COMPREHENSIVE-REVIEW-2026-11-21](../60-EVIDENCE/COMPREHENSIVE-REVIEW-2026-11-21.md) → [CURRENT-STATE](../10-STATE/CURRENT-STATE.md) |

## Why the chain matters

- Each layer was written to fix the *previous* layer's evidence gap, not to add a new promise. Reading an earlier layer as current resurrects withdrawn claims (all-features-complete, error-tracking PASS, deployment readiness).
- **Newest state document in the chain** is `docs/COMPREHENSIVE-REVIEW-2026-11-21.md`, mirrored in [COMPREHENSIVE-REVIEW-2026-11-21](../60-EVIDENCE/COMPREHENSIVE-REVIEW-2026-11-21.md); the continuously maintained snapshot is [CURRENT-STATE](../10-STATE/CURRENT-STATE.md).
- Several "COMPLETE" banners in these files sit beside unticked checkboxes — a flagged pattern in the exhaustive audit. Never let a banner outrank an executable gate. See [AUDIT-2026-11-21](../60-EVIDENCE/AUDIT-2026-11-21.md).
- Licence alignment in the blueprints must be read with the audit's correction: external Romanian civic source (ro_281) is cross-check-only, PopuList licence is unverified, and four distinct Party Facts lineage IDs apply. Do not re-license from the archived text.

## Date anomaly — 2025-11-12 vs 2026-11-12

`RESEARCH.md`, `STRATEGY.md` and `DATA-ENRICHMENT-RESEARCH.md` state **2025-11-12**
in 9 places, but **git first-add is 2026-11-12**. The eight-to-nine-month offset
is unexplained and remains **NOT PROVEN**; the resolvers are a git-history check
on first-add dates and an author/owner confirmation of the intended research
date. Until resolved, use **2026-11-12** for vault chronology and quote
2025-11-12 only as "as stated in the archived document". Recorded in
[RESEARCH-LOG](../50-RESEARCH/RESEARCH-LOG.md).

## See also

[CURRENT-STATE](../10-STATE/CURRENT-STATE.md) · [CONTRADICTIONS](../10-STATE/CONTRADICTIONS.md) · [VISION](../20-DIRECTION/VISION.md) · [WAVE-STATUS](../20-DIRECTION/WAVE-STATUS.md) · [COMPLETION-CERTIFICATE](COMPLETION-CERTIFICATE.md) · [SOURCE-MAP](../00-START/SOURCE-MAP.md)
