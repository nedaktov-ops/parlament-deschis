#!/usr/bin/env bash
# End-to-end verification of a Parlament Deschis production deployment.
#
# The script waits for the Render deploy that matches TARGET_SHA to become
# live, then checks the public contract: the SPA, the /api rewrite, health,
# the pinned dataset release, and two read-only API routes.
#
# Required environment:
#   TARGET_SHA           commit that must be live on Render
#   EXPECTED_RELEASE     dataset release tag from data/latest-release.txt
#   VERCEL_PROJECT_ID    prj_...
#   VERCEL_TOKEN         Vercel API token
#   RENDER_SERVICE_ID    srv-...
#   RENDER_API_KEY       Render API key
#
# Optional environment:
#   VERCEL_TEAM_ID, VERCEL_ORIGIN, RENDER_ORIGIN,
#   VERIFY_TIMEOUT_SECONDS (1800), VERIFY_POLL_SECONDS (20),
#   DATASET_MAX_AGE_DAYS (7)   max permitted age of dataset.published_at
#   FRESHNESS_NOW (RFC3339)    override "now" for deterministic freshness checks
#   HEALTH_JSON_FILE (path)    OFFLINE fixture mode: make NO network/API calls,
#                              skip token requirements, and check freshness of
#                              dataset.published_at in this local JSON file only.
#
# Requires curl and jq. Never prints tokens.
set -euo pipefail

VERCEL_ORIGIN="${VERCEL_ORIGIN:-https://parlament-deschis.vercel.app}"
RENDER_ORIGIN="${RENDER_ORIGIN:-https://parlament-deschis.onrender.com}"
VERIFY_TIMEOUT_SECONDS="${VERIFY_TIMEOUT_SECONDS:-1800}"
VERIFY_POLL_SECONDS="${VERIFY_POLL_SECONDS:-20}"
DATASET_MAX_AGE_DAYS="${DATASET_MAX_AGE_DAYS:-7}"

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

say() { printf '%s\n' "$*"; }
die() {
	printf 'ERROR: %s\n' "$*" >&2
	exit 1
}

# Fail loudly when dataset.published_at is older than DATASET_MAX_AGE_DAYS.
# Used by the full deploy verification and by offline fixture mode.
check_dataset_freshness() { # health_json_file
	local file="$1" published pub_s now_s age_s max_s age_days
	case "$DATASET_MAX_AGE_DAYS" in
	'' | *[!0-9]*) die "DATASET_MAX_AGE_DAYS must be a non-negative integer (got '${DATASET_MAX_AGE_DAYS}')" ;;
	esac
	published=$(jq -r '.dataset.published_at // empty' "$file" 2>/dev/null)
	if [ -z "$published" ]; then
		die "DATASET FRESHNESS FAIL: .dataset.published_at is missing in ${file}"
	fi
	pub_s=$(date -u -d "$published" +%s 2>/dev/null) ||
		die "DATASET FRESHNESS FAIL: cannot parse published_at '${published}'"
	if [ -n "${FRESHNESS_NOW:-}" ]; then
		now_s=$(date -u -d "$FRESHNESS_NOW" +%s 2>/dev/null) ||
			die "DATASET FRESHNESS FAIL: cannot parse FRESHNESS_NOW '${FRESHNESS_NOW}'"
	else
		now_s=$(date -u +%s)
	fi
	age_s=$((now_s - pub_s))
	if [ "$age_s" -lt 0 ]; then
		die "DATASET FRESHNESS FAIL: published_at '${published}' is in the future"
	fi
	max_s=$((DATASET_MAX_AGE_DAYS * 86400))
	age_days=$((age_s / 86400))
	if [ "$age_s" -gt "$max_s" ]; then
		die "DATASET STALE: published_at=${published} age=${age_days}d exceeds maximum of ${DATASET_MAX_AGE_DAYS}d"
	fi
	say "Dataset freshness OK: published_at=${published} age=${age_days}d (max ${DATASET_MAX_AGE_DAYS}d)"
}

# Offline fixture mode: check freshness only, make NO network/API calls and
# require NO tokens. This is how the freshness gate is tested deterministically.
if [ -n "${HEALTH_JSON_FILE:-}" ]; then
	[ -f "$HEALTH_JSON_FILE" ] || die "HEALTH_JSON_FILE not found: ${HEALTH_JSON_FILE}"
	jq -e . "$HEALTH_JSON_FILE" >/dev/null 2>&1 || die "HEALTH_JSON_FILE is not valid JSON: ${HEALTH_JSON_FILE}"
	say "Offline fixture mode: freshness check against ${HEALTH_JSON_FILE}"
	check_dataset_freshness "$HEALTH_JSON_FILE"
	exit 0
fi

# Full verification requires these; offline fixture mode exits above, so it
# never needs credentials or calls any deploy API.
: "${TARGET_SHA:?TARGET_SHA is required}"
: "${EXPECTED_RELEASE:?EXPECTED_RELEASE is required}"
: "${VERCEL_PROJECT_ID:?VERCEL_PROJECT_ID is required}"
: "${VERCEL_TOKEN:?VERCEL_TOKEN is required}"
: "${RENDER_SERVICE_ID:?RENDER_SERVICE_ID is required}"
: "${RENDER_API_KEY:?RENDER_API_KEY is required}"

team_query=""
if [ -n "${VERCEL_TEAM_ID:-}" ]; then
	team_query="&teamId=${VERCEL_TEAM_ID}"
fi

api_get() { # url outfile token
	curl -sS -o "$2" -w '%{http_code}' -H "Authorization: Bearer $3" "$1"
}

public_get() { # url outfile
	curl -sS -o "$2" -w '%{http_code}' --max-time 90 "$1"
}

say "Verifying commit ${TARGET_SHA} against dataset ${EXPECTED_RELEASE}"

deadline=$((SECONDS + VERIFY_TIMEOUT_SECONDS))
vercel_state="absent"
vercel_ok=0
render_state="absent"
render_ok=0

while ((SECONDS < deadline)); do
	vcode=$(api_get \
		"https://api.vercel.com/v7/deployments?projectId=${VERCEL_PROJECT_ID}&target=production&limit=20${team_query}" \
		"$workdir/vercel.json" "$VERCEL_TOKEN")
	if [ "$vcode" != "200" ]; then
		die "Vercel API returned HTTP ${vcode}: $(jq -r '.error.message // empty' "$workdir/vercel.json" 2>/dev/null || true)"
	fi
	vercel_state=$(jq -r --arg sha "$TARGET_SHA" \
		'[.deployments[] | select((.meta.githubCommitSha // "") | startswith($sha))] | .[0].state // "absent"' \
		"$workdir/vercel.json")
	case "$vercel_state" in
	READY)
		vercel_ok=1
		;;
	ERROR | BLOCKED | CANCELED)
		die "Vercel deployment for ${TARGET_SHA} is ${vercel_state}"
		;;
	absent)
		die "Vercel deployment for ${TARGET_SHA} not found (no build started)"
		;;
	esac

	rcode=$(api_get \
		"https://api.render.com/v1/services/${RENDER_SERVICE_ID}/deploys?limit=20" \
		"$workdir/render.json" "$RENDER_API_KEY")
	if [ "$rcode" != "200" ]; then
		die "Render API returned HTTP ${rcode}: $(jq -r '.message // empty' "$workdir/render.json" 2>/dev/null || true)"
	fi
	render_state=$(jq -r --arg sha "$TARGET_SHA" \
		'[.[] | .deploy | select((.commit.id // "") | startswith($sha))] | .[0].status // "absent"' \
		"$workdir/render.json")
	case "$render_state" in
	live)
		render_ok=1
		;;
	build_failed | update_failed | canceled | pre_deploy_failed)
		die "Render deploy for ${TARGET_SHA} is ${render_state}"
		;;
	esac

	if ((vercel_ok == 1 && render_ok == 1)); then
		break
	fi

	say "waiting: vercel=${vercel_state} render=${render_state}"
	sleep "$VERIFY_POLL_SECONDS"
done

if ((render_ok != 1)); then
	die "Render deploy for ${TARGET_SHA} did not become live within ${VERIFY_TIMEOUT_SECONDS}s (last state: ${render_state})"
fi
if ((vercel_ok != 1)); then
	die "Vercel did not resolve within ${VERIFY_TIMEOUT_SECONDS}s (last state: ${vercel_state})"
fi
say "Vercel: deployment for ${TARGET_SHA} is READY."
say "Render: deploy for ${TARGET_SHA} is live."

health_ok=0
for _ in $(seq 1 15); do
	hcode=$(public_get "${RENDER_ORIGIN}/api/health" "$workdir/health.json" || true)
	if [ "$hcode" = "200" ] && jq -e '.status == "ok"' "$workdir/health.json" >/dev/null 2>&1; then
		health_ok=1
		break
	fi
	say "health not ready yet (HTTP ${hcode:-000}); retrying..."
	sleep 10
done
((health_ok == 1)) || die "Render /api/health did not become healthy"

jq -e '.database.status == "ok"' "$workdir/health.json" >/dev/null ||
	die "Render database is not healthy"
persons=$(jq -r '.database.persons // 0' "$workdir/health.json")
memberships=$(jq -r '.database.memberships // 0' "$workdir/health.json")
if ((persons <= 0 || memberships <= 0)); then
	die "Render health returned empty counts (persons=${persons}, memberships=${memberships})"
fi

actual_release=$(jq -r '.dataset.release_tag // "missing"' "$workdir/health.json")
if [ "$actual_release" != "$EXPECTED_RELEASE" ]; then
	die "dataset release mismatch: expected ${EXPECTED_RELEASE}, got ${actual_release}"
fi

# Dataset freshness gate: a stale dataset must fail the whole deployment check.
check_dataset_freshness "$workdir/health.json"

check_public() { # url outfile label
	local code
	code=$(public_get "$1" "$2" || true)
	if [ "$code" != "200" ]; then
		die "$3 returned HTTP ${code:-000} (${1})"
	fi
}

check_public "${VERCEL_ORIGIN}/" "$workdir/index.html" "Vercel frontend"
grep -q '<div id="root">' "$workdir/index.html" ||
	die "Vercel frontend did not return the SPA shell"

check_public "${VERCEL_ORIGIN}/api/health" "$workdir/vercel-health.json" "Vercel /api/health rewrite"
jq -e --arg tag "$EXPECTED_RELEASE" '.dataset.release_tag == $tag' "$workdir/vercel-health.json" >/dev/null ||
	die "Vercel /api/health does not expose dataset ${EXPECTED_RELEASE}"

check_public "${RENDER_ORIGIN}/api/health/live" "$workdir/live.json" "Render /api/health/live"
check_public "${RENDER_ORIGIN}/api/health/ready" "$workdir/ready.json" "Render /api/health/ready"
check_public "${RENDER_ORIGIN}/api/coverage" "$workdir/coverage.json" "Render /api/coverage"
jq -e . "$workdir/coverage.json" >/dev/null || die "Render /api/coverage did not return JSON"
check_public "${RENDER_ORIGIN}/api/traseism/overview" "$workdir/traseism.json" "Render /api/traseism/overview"
jq -e . "$workdir/traseism.json" >/dev/null || die "Render /api/traseism/overview did not return JSON"

vercel_label="READY"

say ""
say "### Deployment verified"
say ""
say "| Check | Result |"
say "|---|---|"
say "| Commit | \`${TARGET_SHA}\` |"
say "| Render deploy | live |"
say "| Vercel deploy | ${vercel_label} |"
say "| Dataset release | \`${actual_release}\` |"
say "| Persons / memberships | ${persons} / ${memberships} |"
say "| SPA, /api rewrite, health, coverage, traseism | 200 |"
