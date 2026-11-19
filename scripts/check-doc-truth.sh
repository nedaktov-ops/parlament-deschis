#!/usr/bin/env bash
# Documentation truth gate (remediation P0-6).
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

# Stale release tags, wrong test/audit counts, fabricated sources, false UI and
# readiness claims, non-existent commands/fields, and wrong dashboard numbers.
pattern='data-20261117-T060923|193 passed|199 pytest|281\.ro|0 JS errors|Ready for Deployment|3 expected failures|125 passed|273 known errors|"ignoreCommand": "git|previous \{ shortName|successor \{ shortName|"memberships": 12445|"switches": 7429|"legislatures": 10|"parties": 62|"cross_chamber": 461|"coverage_score": 85'

hits="$(git grep -nE "$pattern" -- '*.md' ':(exclude)docs/remediation/*' || true)"

if [[ -n "$hits" ]]; then
	printf '%s\n' "$hits" >&2
	count="$(printf '%s\n' "$hits" | wc -l | tr -d ' ')"
	echo "false-claims: $count" >&2
	exit 1
fi

echo "false-claims: 0"
exit 0
