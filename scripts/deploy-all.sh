#!/bin/bash
# Deploy all platforms
#
# NOTE: This script runs verifications only. Deployment is triggered by CI
# on push to main (Vercel Git integration, .github/workflows/ci.yml:125) and
# Render auto-deploy gated by checksPass (.github/workflows/ci.yml:126-127).
# Do NOT use git add -A here — it stages untracked/unrelated changes and can
# commit secrets or half-finished work. See risk R-10.

set -euo pipefail

echo "=== DEPLOYMENT SCRIPT ==="
echo ""

# --- Dirty-tree guard: refuse to run if the working tree has changes -------
if ! git diff --quiet || ! git diff --cached --quiet; then
	echo "ERROR: working tree is dirty. Commit or stash changes before running."
	git status --porcelain
	exit 1
fi

# Run all verifications
echo "1. Running final verifications..."
npm run build --prefix frontend
if [ $? -ne 0 ]; then
	echo "BUILD FAILED"
	exit 1
fi
uv run pytest -q tests/
if [ $? -ne 0 ]; then
	echo "TESTS FAILED"
	exit 1
fi
bash scripts/check-doc-truth.sh
if [ $? -ne 0 ]; then
	echo "DOC TRUTH FAILED"
	exit 1
fi

echo "2. All checks passed!"
echo ""
echo "3. Deployment is triggered automatically by CI on push to main:"
echo "   - Vercel: Git integration on push to main"
echo "   - Render: auto-deploy gated by CI checksPass"
echo "   Do not run git add -A / commit / push from this script."
