---
id: RESEARCH-FLEET
type: research
title: "Research fleet findings — missing components (2026-11-21)"
description: "Six tailored agents investigated the workflow pin, vote-aware refresh, genealogy, Senate identity, platform gaps and frontend polish. Evidence and recommendations only."
status: active
authority: canonical
tags: [type/research, lifecycle/active, domain/project]
source_paths:
  - docs/DECISION-DATA-REFRESH-2026-11-21.md
  - docs/DECISION-PARTY-GENEALOGY.md
  - docs/SENATE-PROFILE-IMPACT.md
  - docs/LOAD-TEST-EVIDENCE.md
created: 2026-11-21
updated: 2026-11-21
source_commit: e4c3107
---

# Research fleet — missing components

Six read-only agents, each with a tailored brief, investigated the outstanding
gaps in [ACTION-PLAN](../20-DIRECTION/ACTION-PLAN.md). No code, data or settings
were changed by the research. Every claim below carries source evidence;
unverifiable items stay `NOT PROVEN`.

## 1. Workflow pin (A-01/A-02) — recommend option A + vote guard

Verified live protection: classic branch protection, checks `test/audit/docker/evidence-guards`,
1 approval, `enforce_admins: true`, no bypass allowances, zero rulesets; owner is a
**User** account, so actor bypass lists are unavailable (GitHub docs: bypass
actors require an organization). Bot PRs start `pull_request` checks in
approval-required state.

- **Option A (PR pin)** is the only route that keeps every check, review and
  admin rule intact. Rollback is `git revert`; no settings reversal.
- **Option B (ruleset bypass)** works but necessarily removes PR + all four
  checks for one actor and requires deleting classic protection — rejected.
- **Option C (vote-aware)** is a prerequisite for unattended pinning but is
  larger and needs its own source decision.
- **Option D (manual)** is today's state.

Decisive safety property for **any** option: before publishing/pinning, assert
the candidate corpus has at least as many votes as live (189). Without that
guard even a correctly merged PR pins a vote-less corpus — a silent regression.

## 2. Vote-aware workflow (A-03) — release-asset merge is feasible

- Locked fixtures yield **1 vote / 244 positions**, not 189 — a 99.5 % regression
  (`votes-import --json` raw output; only one nominal XML pair exists).
- Live vote XML is reachable from this host (HTTP 200) but runner reachability is
  **NOT PROVEN**; `ingest-votes` has no offline mode, ignores `--limit-days`, and
  is not drop-in safe.
- A deterministic merge from the pinned release asset works: all **24,682**
  positions remap by `cdep_mandate` with 0 misses and 0 ambiguities against a
  fresh corpus (release identifier keys 6762 ⊂ fresh 7097). Verified SHA
  `eabdb857…` and strict audit `275 known / 0 new`.
- Minimal design: download pinned `parlament.db`, add a `votes-merge --source-db
  … --apply` CLI command with identifier-only remap and fail-closed unresolved
  positions, add an `assert-votes --min-votes 189 --min-positions 24682` gate,
  update `tests/test_votes_build_isolation.py` explicitly (its rationale is
  third-party outages, not GitHub release assets), and assert live
  `/api/votes total >= 189` after deploy.

## 3. Party genealogy (A-06/A-07) — DROP confirmed, with corrected reasoning

The prior decision was incomplete, not wrong. New evidence:
- **ParlGov** (CC0 confirmed) *does* declare 22 Romanian party-change rows with
  stable IDs — but PSD has two predecessors, PNL six+, and 18/22 rows have no
  source (the rest are bare agency codes). A one-valued FK cannot be filled
  without choosing one — inference, which is forbidden.
- **Manifesto Project** declares RO PSD-PUR ← FDSN but its terms forbid
  redistribution; excluded.
- **PolPaL** is live since 2026 (the "under construction" premise is stale);
  software AGPL-3.0, **data licence NOT PROVEN** — excluded.
- Wikidata: **zero referenced predecessor/successor statements for RO political
  parties**; the referenced Romanian `replaces` hits are cabinets, not parties.
  Q752435 has four unlinked predecessors.
- Party Facts archive has no relations file and self-declares incomplete coding.

Verdict: keep both FK columns NULL; relabel docs with the corrected reasoning.
NOT PROVEN: PolPaL data licence, ParlGov `party_id` → our `organization.id`
mapping, any official register with a declared single-valued relation.

## 4. Senate identity (A-07) — HOLD confirmed, reason upgraded

- senat.ro profiles expose only the GUID; no DOB, CNP or cdep `idm` (live GET and
  Biografie postback, 2.5 s pacing).
- Wikidata **P9523** maps 813 distinct Senate GUIDs / 705 items (93 % of the
  128 GUIDs for 1990), but **0** `senat_guid` and **0** `wikidata_qid` exist in
  our corpus, and the sole P9523↔P9524 item (Q731851) has two conflicting GUIDs.
  The final GUID→person join is missing.
- Name+DOB bridge gives 87/128 unique for 1990, but `PersonResolver.resolve`
  auto-links the unique case — still name-based, therefore prohibited.
- Lift conditions: (a) an authoritative, licence-compatible `senat_guid →
  cdep_mandate` table with ≥~90 % coverage and 0 conflicts; or (b) reviewed
  Wikidata-QID enrichment plus P9523→QID→person join with name-only paths forced
  to review. Gate on any staged ingest: 0 name-only auto-links, strict audit
  275/0, coverage 20 scopes / 5282 persons, `/api/traseism/overview` SHA
  `7b535864…57845857` unchanged.

## 5. Platform gaps (A-15–A-20)

- **A-20 RESOLVED**: `POST /graphql {"query":"{__typename}"}` → 200 on both hosts;
  earlier 404 was a GET-only probe artifact. GraphiQL disabled in production.
- **A-16 PARTIAL**: GitHub status ties deploy IDs to SHAs (`afd1944` →
  `DMWBXLWkHjm65NiMzFHraiXJg1zd`, `e4c3107` → `AactV98rQaCR23spBQXM9kskCEys`);
  which SHA the live alias serves remains NOT PROVEN without a Vercel token.
- **A-15**: tokenless POSTs to all three write endpoints return 503 before any
  write; OS-level FS proof impossible on Render Free (no shell) — use a
  disposable instance for the DB-level probe.
- **A-17**: `vercel.json` rewrites even previews to production Render; staging
  requires a second backend (Free Render service) and a rewrite override.
- **A-18**: keep DEFER — no Vercel Function exists; a cron would 404. Prefer a
  read-only scheduled GitHub Actions health check if a daily signal is wanted.
- **A-19**: CSP now enforces; `index.html` has a 419-byte inline theme script
  (`sha256-CHoUVBvg4ZNU5xFdBlBHnEMCd4zOjWZJeeXR697M7aA=`), 35 inline `style=`
  uses, 0 `eval(`. Stage: drop `'unsafe-eval'` → add hash/drop script-inline →
  `style-src-attr`/refactor. One revert per stage.

## 6. Frontend polish (A-11–A-13)

- **A-11 DO**: Voturi's loading/empty branches map 1:1 to `LoadingState`/
  `EmptyState`; all three i18n keys exist in both locales; markup-only change.
- **A-12 DROP**: no newsletter endpoint, subscriber store or endorsement data
  in repo or API; About's "featured testimonial" is self-attributed copy.
  Reopen only with a real source; invent no links/logos/quotes.
- **A-13 KEY MISSING but gate unachievable as stated**: `footer.datasetRelease`
  is absent in ro/en (flat `datasetRelease` exists); add the namespaced key in
  both locales and fix the stale footer comment. NOTE: the broader key-diff gate
  is RED with **64 missing keys** — adding one key cannot green it; record
  that honestly rather than lowering the gate.

## Consolidated next decisions

1. Owner chooses workflow-pin option A with the ≥189-vote guard (A-01).
2. Then implement release-asset vote merge + `assert-votes` gate (A-03).
3. Apply the documented relabellings for genealogy DROP and Senate HOLD (A-06).
4. Do the safe frontend wins (A-11, A-13) and record A-12 DROP.
5. Close A-20 in the vault; keep A-18 DEFER; stage A-19 only with browser proof.

## See also

[ACTION-PLAN](../20-DIRECTION/ACTION-PLAN.md) · [NEXT-ACTIONS](../10-STATE/NEXT-ACTIONS.md) · [DECISIONS](../20-DIRECTION/DECISIONS.md) · [RESEARCH-LOG](RESEARCH-LOG.md)
