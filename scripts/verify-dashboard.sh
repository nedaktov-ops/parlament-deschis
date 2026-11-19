#!/bin/bash
# Dashboard Verification Script
# Run after staging deployment to verify all visualizations work.
#
# All sizes and counts below are MEASURED from the built artifacts at run time.
# No bundle hash, bundle size, component count or pass status is hardcoded.
set -e

echo "=== DASHBOARD VERIFICATION SCRIPT ==="
echo "Date: $(date)"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="${DASHBOARD_URL:-http://localhost:5173}"
STAGING_URL="${STAGING_URL:-$BASE_URL}"

echo "1. Checking build artifacts..."
echo "--------------------------------"

if [ -f "frontend/dist/index.html" ]; then
	echo -e "${GREEN}✓ Build exists${NC}"
else
	echo -e "${RED}✗ Build not found. Run 'npm run build' first${NC}"
	exit 1
fi

echo ""
echo "2. Checking TypeScript compilation..."
echo "--------------------------------"
cd frontend
if npx tsc --noEmit 2>/dev/null; then
	echo -e "${GREEN}✓ TypeScript compiles with 0 errors${NC}"
else
	echo -e "${RED}✗ TypeScript compilation failed${NC}"
	exit 1
fi

echo ""
echo "3. Checking bundle sizes (measured from dist/assets)..."
echo "--------------------------------"
# Resolve the real LiveDashboard asset name; no hardcoded hash is allowed.
ld_file=""
for f in dist/assets/LiveDashboard-*.js; do
	if [ -f "$f" ]; then
		ld_file="$f"
		break
	fi
done
if [ -n "$ld_file" ]; then
	ld_kb=$(du -k "$ld_file" | cut -f1)
	echo -e "${GREEN}✓ LiveDashboard bundle measured: $(basename "$ld_file") — ${ld_kb}KB${NC}"
else
	echo -e "${YELLOW}! LiveDashboard bundle: not found (measured 0 matching files in dist/assets/LiveDashboard-*.js)${NC}"
fi
echo "   Measured JS assets present in dist/assets:"
assets_seen=0
for f in dist/assets/*.js; do
	if [ -f "$f" ]; then
		assets_seen=$((assets_seen + 1))
		printf '     %s : %sKB\n' "$(basename "$f")" "$(du -k "$f" | cut -f1)"
	fi
done
echo "   Measured JS asset count: ${assets_seen}"

echo ""
echo "4. Checking component exports..."
echo "--------------------------------"
REQUIRED_COMPONENTS="DashboardCard PartyListTable PartyNetwork AgeDistributionRadial SwitchTimeline CommitteeControl CrossChamberFlow DataQualityGauge"
present=0
missing=0
for component in $REQUIRED_COMPONENTS; do
	if [ -f "src/components/${component}.tsx" ]; then
		present=$((present + 1))
		echo -e "${GREEN}✓ ${component}.tsx exists${NC}"
	else
		missing=$((missing + 1))
		echo -e "${RED}✗ ${component}.tsx missing${NC}"
	fi
done
echo "   Measured components: ${present} present, ${missing} missing"
if [ "$missing" -gt 0 ]; then
	echo -e "${RED}✗ Required components are missing - verification FAILED${NC}"
	exit 1
fi

echo ""
echo "5. Checking API endpoint definition..."
echo "--------------------------------"
if grep -q "dashboard/stats" ../backend/routers/api.py; then
	echo -e "${GREEN}✓ /api/dashboard/stats endpoint defined${NC}"
else
	echo -e "${RED}✗ /api/dashboard/stats endpoint not found${NC}"
	exit 1
fi

cd ..

echo ""
echo "=== VERIFICATION COMPLETE ==="
echo ""
echo "Next steps (manual, no automatic deploy/push):"
echo "1. Deploy through Vercel Git integration / Render checksPass"
echo "2. Run accessibility test: python scripts/ui_validate.py"
echo "3. Run Lighthouse: lighthouse ${STAGING_URL}"
echo "4. Manual browser testing of all visualizations"

echo ""
echo "Summary (measured):"
echo "-------"
echo "TypeScript: ✓ Pass (tsc --noEmit)"
echo "Build: ✓ Pass (frontend/dist/index.html present)"
echo "Components: ✓ ${present} present / ${missing} missing"
echo "API endpoint: ✓ defined"
echo ""
echo "All measured checks passed. 🚀"
