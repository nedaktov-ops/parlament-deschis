#!/bin/bash
# Dashboard Deployment Script
# Run by the owner with admin privileges.
#
# This script does NOT create tags, does NOT push anything, and does NOT call
# any deploy API. Deployment happens through Vercel Git integration and Render
# `checksPass`. It only verifies the build locally and prints MEASURED artifact
# sizes — no bundle size, build time or pass status is hardcoded.
set -e

echo "=================================================="
echo "   DASHBOARD DEPLOYMENT SCRIPT"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/home/nedaktov/parlament-deschis"

cd "$PROJECT_DIR/frontend"

echo "Step 1: Verifying implementation..."
echo -n "  TypeScript: "
if npx tsc --noEmit 2>/dev/null; then
	echo -e "${GREEN}✓ Pass${NC}"
else
	echo -e "${RED}✗ Failed${NC}"
	exit 1
fi

echo -n "  Build: "
if npm run build 2>/dev/null; then
	echo -e "${GREEN}✓ Pass${NC}"
else
	echo -e "${RED}✗ Failed${NC}"
	exit 1
fi

cd "$PROJECT_DIR"

echo ""
echo "Step 2: Deployment is external to this script."
echo "--------------------------------------------------------"
echo "No tag is created and nothing is pushed by this script."
echo "Vercel Git integration + Render checksPass are the only deploy paths."
echo "Independent proof: bash scripts/verify-deploy.sh (after deploy)."

echo ""
echo "Step 3: Measured build artifacts"
echo "--------------------------------------------------------"
if [ -f "$PROJECT_DIR/frontend/dist/index.html" ]; then
	total_kb=$(du -sk "$PROJECT_DIR/frontend/dist" | cut -f1)
	echo "frontend/dist total: ${total_kb}KB"
	assets_seen=0
	for f in "$PROJECT_DIR"/frontend/dist/assets/*.js; do
		if [ -f "$f" ]; then
			assets_seen=$((assets_seen + 1))
			printf '  %s : %sKB\n' "$(basename "$f")" "$(du -k "$f" | cut -f1)"
		fi
	done
	echo "Measured JS asset count: ${assets_seen}"
else
	echo "No build artifacts found at frontend/dist (nothing to measure)."
fi

echo ""
echo "--------------------------------------------------------"
echo "LOCAL VERIFICATION COMPLETE. No push, no tag, no deploy was performed."
echo "Open the PR/merge in the SCM UI; the platform builds and deploys from Git."
echo -e "${GREEN}DEPLOYMENT PACKAGE READY 🚀${NC}"
