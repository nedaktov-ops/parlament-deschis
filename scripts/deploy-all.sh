#!/bin/bash
# Deploy all platforms

echo "=== DEPLOYMENT SCRIPT ==="
echo ""

# Run all verifications
echo "1. Running final verifications..."
npm run build --prefix frontend
if [ $? -ne 0 ]; then echo "BUILD FAILED"; exit 1; fi
uv run pytest -q tests/
if [ $? -ne 0 ]; then echo "TESTS FAILED"; exit 1; fi
bash scripts/check-doc-truth.sh
if [ $? -ne 0 ]; then echo "DOC TRUTH FAILED"; exit 1; fi

echo "2. All checks passed!"

# Git operations
echo "3. Staging changes..."
git add -A
git commit -m "Deploy: Wave 4 complete + W5 verification" || echo "No changes to commit"

# Push to trigger Vercel/Render
echo "4. Pushing to GitHub (triggers Vercel/Render deploy)..."
git push origin main

echo "5. Deployment triggered!"
echo "Monitor at:"
echo "  - Vercel: https://vercel.com/dashboard"
echo "  - Render: https://dashboard.render.com"
