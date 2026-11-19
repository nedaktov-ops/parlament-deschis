#!/usr/bin/env bash
# Deployment Status Checker
# For the owner to run to check whether the dashboard is actually deployed.
#
# Truth-telling contract:
#   * Every check is a real assertion. Absence of the thing being checked is a
#     FAILURE (non-zero exit), never a green "✅". The old pattern that piped
#     grep output through a first-line truncator and then echoed ✅ is gone:
#     that truncator exits 0 on empty input, so it always printed ✅. Here a
#     value is first extracted, then explicitly tested with test -n / grep -q
#     before any ✅ is emitted.
#   * The JS bundle is resolved from the *served* index.html instead of the
#     literal, never-matching URL `assets/index-*.js` (curl does not glob).
#   * Target is overridable so the same script can be pointed at a local
#     fixture server: DEPLOYMENT_URL=http://127.0.0.1:PORT bash $0
set -uo pipefail

BASE_URL="${DEPLOYMENT_URL:-${BASE_URL:-https://parlament-deschis.vercel.app}}"
BASE_URL="${BASE_URL%/}"

fail=0
pass() { printf '   ✅ %s\n' "$*"; }
warn() {
	printf '   ⚠️  %s\n' "$*"
	fail=$((fail + 1))
}
die() {
	printf 'ERROR: %s\n' "$*" >&2
	exit 2
}

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

fetch() { # url outfile -> prints http code only
	local code
	code=$(curl -sS -o "$2" -w '%{http_code}' --max-time 10 "$1" 2>/dev/null) || code="000"
	printf '%s' "$code"
}

echo "🔍 CHECKING DASHBOARD DEPLOYMENT STATUS"
echo "========================================"
echo "Target: ${BASE_URL}"

echo ""
echo "1. Checking main frontend..."
code=$(fetch "$BASE_URL/" "$tmpdir/index.html")
if [ "$code" = "200" ]; then
	pass "Main page: LIVE (HTTP 200)"
else
	warn "Main page: HTTP ${code} (expected 200)"
fi

echo ""
echo "2. Checking dashboard stats API..."
code=$(fetch "$BASE_URL/api/dashboard/stats" "$tmpdir/stats.json")
if [ "$code" = "200" ] && jq -e . "$tmpdir/stats.json" >/dev/null 2>&1; then
	pass "Dashboard Stats API: LIVE (HTTP 200, valid JSON)"
else
	warn "Dashboard Stats API: HTTP ${code} or invalid JSON"
fi

echo ""
echo "3. Checking health endpoint..."
code=$(fetch "$BASE_URL/api/health" "$tmpdir/health.json")
if [ "$code" = "200" ] && jq -e '.status == "ok"' "$tmpdir/health.json" >/dev/null 2>&1; then
	pass "Health endpoint: LIVE (status ok)"
else
	warn "Health endpoint: HTTP ${code} or status != ok"
fi

echo ""
echo "4. Resolving the real JS bundle from the served index.html..."
asset_path=""
if [ -s "$tmpdir/index.html" ]; then
	# Extract the FIRST script src ending in .js; extraction is not the check.
	while IFS= read -r hit; do
		asset_path="$hit"
		break
	done < <(grep -oE 'src="[^"]+\.js"' "$tmpdir/index.html")
	asset_path="${asset_path#src=\"}"
	asset_path="${asset_path%\"}"
fi
if [ -z "$asset_path" ]; then
	warn "No .js bundle referenced in served index.html - dashboard cannot be verified"
else
	pass "Resolved asset from index.html: ${asset_path}"
fi

echo ""
echo "5. Verifying the resolved dashboard bundle..."
if [ -z "$asset_path" ]; then
	warn "SKIPPED: no asset was resolved; component checks cannot pass"
else
	case "$asset_path" in
	http://* | https://*) asset_url="$asset_path" ;;
	/*) asset_url="${BASE_URL}${asset_path}" ;;
	*) asset_url="${BASE_URL}/${asset_path}" ;;
	esac
	code=$(fetch "$asset_url" "$tmpdir/asset.js")
	size=$(wc -c <"$tmpdir/asset.js" 2>/dev/null | tr -d ' ')
	size=${size:-0}
	if [ "$code" != "200" ]; then
		warn "Resolved asset returned HTTP ${code}: ${asset_url}"
	elif [ "$size" -lt 1000 ]; then
		warn "Resolved asset is empty/too small (${size} bytes): ${asset_path}"
	elif ! grep -q 'LiveDashboard' "$tmpdir/asset.js"; then
		warn "Dashboard marker 'LiveDashboard' absent from ${asset_path} (${size} bytes)"
	else
		pass "Dashboard bundle detected: ${asset_path} (HTTP 200, ${size} bytes, LiveDashboard marker present)"
	fi
fi

echo ""
echo "========================================"
if [ "$fail" -eq 0 ]; then
	echo "RESULT: PASS - every check found the thing it checks for."
	exit 0
fi
echo "RESULT: FAIL - ${fail} check(s) did not find the thing they check for."
echo "A ✅ is emitted only for checks that actually passed. Re-run after deploy:"
echo "  DEPLOYMENT_URL=<url> $0"
exit 1
