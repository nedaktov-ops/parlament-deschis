# Project Improvement Architecture Plan

This plan turns the project review into an incremental engineering program. It
preserves the intended architecture: official sources remain authoritative,
the pipeline owns data derivation, and runtime reads should be read-only. It
also calls out and schedules fixes for places where current behavior diverges
from that intent.

## Outcomes

1. Make analytics correct, reproducible, and independently testable.
2. Give the dashboard one stable, observable API contract.
3. Make local setup and CI use the same locked dependency definition.
4. Make deployed data availability and freshness visible to operators.

## Stages

### Stage 1 — Analytics correctness and reproducibility

**Goal:** Analytics must produce deterministic, scope-correct results and must
not silently omit incomplete/current scopes.

**Architecture:** Keep derivations in `pipeline/analytics.py`; keep API
serialization in the backend. Derived outputs should become pure or
idempotent operations, with persistence explicit rather than hidden in reads.

**Actions**

- [x] Include open-ended legislature periods when deriving switch waves.
- [x] Add a regression test covering an open legislature and repeated derivation.
- [ ] Resolve legislature boundaries by chamber and define behavior for missing
  start dates.
- [ ] Replace print-based analytics and placeholder return values with
  structured, testable results.
- [ ] Separate read-only analytics queries from any command that persists
  derived records; use explicit mutation semantics for persisted results.
- [ ] Add focused correctness and performance tests for high-volume event
  scopes.

**Acceptance:** Re-running a derivation on the same facts is stable; current
open scopes are covered; public read endpoints do not create or rewrite data.

### Stage 2 — API contract and frontend boundary

**Goal:** Prevent REST, GraphQL, documentation, and frontend types from
drifting apart.

**Architecture decision:** Treat REST as the canonical dashboard API.
Keep GraphQL exploratory and ensure its resolvers remain read-only until there
is a concrete consumer and a shared schema-generation strategy.

**Actions**

- [x] Preserve useful server error details in frontend API failures.
- [x] Include database row counts in health responses and the frontend health
  type.
- [ ] Generate frontend types from FastAPI's OpenAPI schema and remove
  hand-maintained duplicates incrementally.
- [ ] Add contract checks for documented endpoints, status codes, and response
  shapes.
- [ ] Audit GraphQL resolvers and make the read-only boundary explicit.
- [ ] Define pagination, filtering, and compatibility rules for collection
  endpoints.

**Acceptance:** API behavior is discoverable from OpenAPI; generated types
build in CI; documented response shapes match tested responses.

### Stage 3 — Reproducible development and CI

**Goal:** A clean checkout can install exactly the dependencies required by
its selected task, and CI validates the same setup.

**Actions**

- [x] Use the `dev` optional extra explicitly for test/lint CI, locked to
  `uv.lock`.
- [x] Use locked runtime-only installs in data-build workflows.
- [x] Align contributor setup instructions with the CI commands.
- [ ] Add a clean-environment install smoke test and verify it runs tests,
  lint, and the frontend build.
- [ ] Document supported Python/Node versions and a single canonical command
  sequence for local development.

**Acceptance:** CI installs with `--locked`; a fresh environment has pytest and
ruff in the test job, while data-only jobs install no development extras.

### Stage 4 — Operations, data health, and schema evolution

**Goal:** Operators can distinguish a running API from a usable, current
dataset, and can evolve the database without relying on undocumented rebuilds.

**Actions**

- [x] Report database availability counts alongside source freshness in
  `/api/health`.
- [ ] Define separate liveness and readiness checks and configure deployment
  health checks to use the appropriate one.
- [ ] Add a database schema version and a documented migration/rebuild policy.
- [ ] Publish structured pipeline counters for fetches, retries, parse
  failures, audit outcomes, and source freshness.
- [ ] Define alert thresholds for failed audits and stale source data.

**Acceptance:** Deployment checks fail when required runtime data is missing;
health output distinguishes service availability, dataset presence, and source
freshness; schema changes have a reproducible upgrade path.

### Stage 5 — Frontend scope, performance, and accessibility

**Goal:** Users can tell which data they are viewing, how complete it is, and
how to explore it without relying on color, mouse interaction, or an
unqualified "live" claim.

**Actions**

- [x] Mount one routed application shell and remove the duplicate legacy app.
- [x] Keep date context in route search parameters; use chamber and legislature
  selectors for the switching analysis.
- [x] Fix open-ended current-term comparisons and scope timeline data to the
  selected date.
- [x] Avoid repeated per-date database queries for timeline composition and
  adapt chart sampling to the selected date range.
- [x] Add explicit chart/search/data-load failures and retry actions.
- [x] Replace the "live" badge with source-refresh status and the latest
  successful refresh time.
- [x] Add accessible navigation, search keyboard controls, date labels,
  dialog focus handling, and text alternatives for composition/timeline data.
- [x] Raise muted text contrast and minimum small-label sizing; add reduced
  motion support.
- [x] Derive detailed coverage metrics when persisted coverage rows are absent
  and show unavailable values rather than `NaN` or zero-denominator percentages.
- [ ] Finish replacing remaining institutional placeholders with verified
  underlying data, and split the ECharts bundle if its load cost remains
  measurable after deployment.

**Acceptance:** Every count is tied to an explicit scope and coverage status;
date-dependent views retain their date in the URL; long-range charts load
progressively and expose a text alternative; keyboard and screen-reader users
can reach the primary exploration flows.

## Delivery order

Stages are ordered by dependency: reliable analytics provide a trustworthy
contract; the contract provides a basis for generated client types; reproducible
CI validates both; operational checks then validate the deployed artifact.
Each action should remain a focused change with a regression test where
behavior changes. Data-methodology changes must also update
[`METHODOLOGY.md`](METHODOLOGY.md), and schema/API changes must update
[`DATA-MODEL.md`](DATA-MODEL.md) or [`API.md`](API.md), respectively.
For the detailed free-tier data refresh, release, deployment, and recovery
architecture, see
[`SELF-SUSTAINABILITY-ARCHITECTURE.md`](SELF-SUSTAINABILITY-ARCHITECTURE.md).

## Current implementation checkpoint

The first implementation pass addresses one issue in each stage: open
legislature analytics, frontend API error detail, locked dependency commands,
and database counts in health output. The remaining items are intentionally
listed as follow-up actions rather than being implied complete.

The frontend pass now mounts the routed shell, preserves date context in the
URL, fixes the open-ended legislature boundary, optimizes timeline sampling,
and shows data freshness rather than an availability-based "live" status.
Navigation, search, date controls, dialogs, and chart alternatives have
keyboard/screen-reader support. The institutional committee/bureau datasets
remain incomplete and are labeled as such; they are not represented with
unrelated charts or fabricated figures.
