#!/usr/bin/env bash
# End-to-end verification of a Parlament Deschis production deployment.
#
# The script waits for the Render deploy that matches TARGET_SHA to become
# live, tolerates a Vercel build that was intentionally skipped by
# vercel.json's ignoreCommand, then checks the public contract: the SPA, the
# /api rewrite, health, the pinned dataset release, and two read-only API
# routes.
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
#   VERCEL_SKIP_GRACE_SECONDS (180)
#
# Requires curl and jq. Never prints tokens.
set -euo pipefail

: "${TARGET_SHA:?TARGET_SHA is required}"
: "${EXPECTED_RELEASE:?EXPECTED_RELEASE is required}"
: "${VERCEL_PROJECT_ID:?VERCEL_PROJECT_ID is required}"
: "${VERCEL_TOKEN:?VERCEL_TOKEN is required}"
: "${RENDER_SERVICE_ID:?RENDER_SERVICE_ID is required}"
: "${RENDER_API_KEY:?RENDER_API_KEY is required}"

VERCEL_ORIGIN="${VERCEL_ORIGIN:-https://parlament-deschis.vercel.app}"
RENDER_ORIGIN="${RENDER_ORIGIN:-https://parlament-deschis.onrender.com}"
VERIFY_TIMEOUT_SECONDS="${VERIFY_TIMEOUT_SECONDS:-1800}"
VERIFY_POLL_SECONDS="${VERIFY_POLL_SECONDS:-20}"
VERCEL_SKIP_GRACE_SECONDS="${VERCEL_SKIP_GRACE_SECONDS:-180}"

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

say() { printf '%s\n' "$*"; }
die() {
	printf 'ERROR: %s\n' "$*" >&2
	exit 1
}

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
vercel_skipped=0
vercel_absent_since=""
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
		vercel_skipped=0
		;;
	ERROR | BLOCKED)
		die "Vercel deployment for ${TARGET_SHA} is ${vercel_state}"
		;;
	CANCELED | absent)
		if [ -z "$vercel_absent_since" ]; then
			vercel_absent_since=$SECONDS
		fi
		if ((SECONDS - vercel_absent_since >= VERCEL_SKIP_GRACE_SECONDS)); then
			vercel_ok=1
			vercel_skipped=1
		fi
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

if ((vercel_skipped == 1)); then
	say "Vercel: no deployment for ${TARGET_SHA} (build skipped by ignoreCommand); checking the stable origin."
else
	say "Vercel: deployment for ${TARGET_SHA} is READY."
fi
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
if ((vercel_skipped == 1)); then
	vercel_label="skipped (no frontend change)"
fi

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
