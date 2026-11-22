#!/usr/bin/env bash
# Documentation truth gate (remediation P0-6; 2026-11-21 precise-claim repair).
#
# Fails when a known-false claim survives in a tracked Markdown file. Uses
# `git grep`, so gitignored build output (node_modules/, .venv/, dist/) is never
# scanned. `docs/remediation/*` is excluded because those strategy artifacts are
# the source of truth and legitimately quote the false strings as instructions
# to remove them; they are not project documentation.
set -uo pipefail

root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
	echo "error: not inside a git worktree" >&2
	exit 2
}
cd "$root" || exit 2

# Wrong test/audit counts, false UI and readiness claims, non-existent
# commands/fields, and wrong dashboard numbers. These 14 strings are unchanged
# from P0-6. Two overbroad bare tokens (`data-20261117-T060923` and `281\.ro`)
# were replaced by the precise false-assertion checks below: both now appear
# legitimately in research/strategy docs as historical tags / an external CC-BY
# source, so a bare-token match no longer means a false claim.
pattern='193 passed|199 pytest|0 JS errors|Ready for Deployment|3 expected failures|125 passed|273 known errors|"ignoreCommand": "git|previous \{ shortName|successor \{ shortName|"memberships": 12445|"switches": 7429|"legislatures": 10|"parties": 62|"cross_chamber": 461|"coverage_score": 85'

hits="$(git grep -nE "$pattern" -- '*.md' ':(exclude)docs/remediation/*' ':(exclude).nedcode/qa/*' || true)"

# The genuine stale-tag false claim asserts that the OLD tag is the CURRENT pin.
# A list of historical tags (as in MASTER-INTEGRATION-BLUEPRINT.md:103) is not
# that claim. Match the assertion, not mere mention, over every tracked .md.
stale_tag='(pinned|pin|current|today|serving|served|latest).{0,60}data-20261117-T060923|data-20261117-T060923.{0,60}(pinned|current|serving|served|is the latest)'
hits_tag="$(git grep -niE "$stale_tag" -- '*.md' ':(exclude)docs/remediation/*' ':(exclude).nedcode/qa/*' || true)"
if [[ -n "$hits_tag" ]]; then
	if [[ -n "$hits" ]]; then
		hits="$(printf '%s\n%s\n' "$hits" "$hits_tag")"
	else
		hits="$hits_tag"
	fi
fi

# The original 281.ro claim was never "281.ro is mentioned". It was the specific
# assertion that 281.ro is OUR product/codebase/target/repo or a real integrated
# data source ("281.ro is our product", "Target is 281.ro", "469 current MPs from
# 281.ro API"). Later evidence established 281.ro as an external CC-BY cross-check
# whose public repo is 404, so a bare-token check now flags 37 TRUE statements.
# Match only the false assertion. The research/strategy/licence-fixture artifacts
# below legitimately QUOTE or NEGATE those exact phrases (the same role
# docs/remediation/* plays), so they are excluded from this one check. Every
# other pattern above still applies to every tracked .md file, including them.
false_281='281\.ro is (our|the) (product|codebase|target|repo)|target is 281\.ro|we (ship to|add votes/UX to|write to) 281\.ro|469 current MPs from 281\.ro'
hits_281="$(git grep -niE "$false_281" -- '*.md' \
	':(exclude)docs/remediation/*' \
	':(exclude)docs/MASTER-INTEGRATION-BLUEPRINT.md' \
	':(exclude)docs/MASTER-INTEGRATION-BLUEPRINT-WAVE2.md' \
	':(exclude)docs/DATA-ENRICHMENT-RESEARCH.md' \
	':(exclude)docs/MASTER-STRATEGY.md' \
	':(exclude)tests/fixtures/votes/LICENSE-APPENDIX.md' \
	':(exclude).nedcode/qa/*' || true)"

if [[ -n "$hits_281" ]]; then
	if [[ -n "$hits" ]]; then
		hits="$(printf '%s\n%s\n' "$hits" "$hits_281")"
	else
		hits="$hits_281"
	fi
fi

if [[ -n "$hits" ]]; then
	printf '%s\n' "$hits" >&2
	count="$(printf '%s\n' "$hits" | wc -l | tr -d ' ')"
	echo "false-claims: $count" >&2
	exit 1
fi

echo "false-claims: 0"
exit 0
