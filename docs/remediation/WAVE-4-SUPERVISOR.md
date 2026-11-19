# Wave 4 Supervisor Protocol

**Companion to:** `WAVE-4-STRATEGY.md`, `WAVE-4-RECIPES.md`

---

## Role: Wave 4 Supervisor

This is a **strategic supervisor** that validates modernization work follows the strategy without hallucinating side-quests.

---

## Pre-Work Checklist

Before any Wave 4 work begins:

1. ✅ `WAVE-4-STRATEGY.md` exists and is approved
2. ✅ `WAVE-4-RECIPES.md` has recipes for each numbered task
3. ✅ Each recipe follows the template format
4. ✅ Backup tag `eb069d2b` verified
5. ✅ Scope is limited to files in STRATEGY.md §Scope

---

## During-Work Validation

### File Ownership Check

Each sub-agent must only modify files explicitly listed in its recipe.

**ALLOWED** (per recipe):
- `frontend/package.json` (for dependency upgrades)
- `pipeline/schema.graphql` (generated)
- `docs/API.md` (documentation)
- `backend/routers/metrics.py` (new file)

**NOT ALLOWED**:
- Modifying business logic files
- Changing database schema
- Adding secret keys
- Removing tests

### Scope Police Commands

```bash
# Check recipe scope
grep -A10 "^## R-" WAVE-4-RECIPES.md | grep -A5 "Scope"

# Verify only owned files changed
git diff --name-only <commit>^..<commit>
```

### Data Loss Prevention

```bash
# Verify no data files deleted
git diff --name-only <commit>^..<commit> | grep -E "\.db$|\.sqlite$|data/" && exit 1

# Verify no secrets added
grep -r "secret\|token\|password" frontend/ backend/ --include="*.ts" --include="*.py" || echo "No secrets detected"
```

---

## Checkpoints Verification

### Build Gate
```bash
# Must pass before any integration
cd frontend && npm run build
# Expected: ✓ built in xx.xxs, BUILD_EXIT:0
```

### Test Gate
```bash
uv run pytest -q tests/
# Expected: N passed, 0 failed
```

### Lint Gate
```bash
npm run lint
# Expected: 0 errors (warnings OK)
uv run ruff check backend pipeline scripts tests
# Expected: All checks passed!
```

### Doc Truth Gate
```bash
bash scripts/check-doc-truth.sh
# Expected: false-claims: 0
```

### CSP Equality Gate (if frontend changed)
```bash
# Verify CSP hasn't drifted
python3 - << 'PY'
import json, re, pathlib
m = pathlib.Path('backend/main.py').read_text()
a = re.search(r'"Content-Security-Policy-Report-Only": \(\s*"([^"]+)"\s*\),', m, re.S).group(1)
v = json.loads(pathlib.Path('vercel.json').read_text())
b = [hh['value'] for h in v['headers'] for hh in h['headers'] if hh['key']=='Content-Security-Policy-Report-Only'][0]
assert a == b, "CSP MISMATCH"
print("CSP_EQUAL: True")
PY
```

### Axe Gate (if frontend changed)
```bash
npm run dev &
# Start local server on port 5173
# Run axe scan on all routes
python3 /tmp/opencode/wa-ui-validate-axe.py http://localhost:5173
# Expected: 0 violations
pkill -f "vite"
```

---

## Evidence Log Format

Every recipe must produce an evidence log like:

```
## Evidence log (CP-D1-1)

| Step | Evidence | Status |
|---|---|---|
| 1.1 | `cat frontend/package.json \| grep react` → `"react": "^18.3.1"` | PASS |
| 1.2 | `uv run pytest -q` → 286 passed, 0 failed | PASS |
| 1.3 | `npm run lint` → 0 errors | PASS |
| 1.4 | Doc truth → false-claims: 0 | PASS |
```

---

## Red Flags (REJECT Conditions)

Any of these = **REJECT**:
- ❌ Build fails after changes
- ❌ Tests decrease (pytest count goes down)
- ❌ New secrets in code
- ❌ Data file modified/deleted
- ❌ CSP drift detected
- ❌ Axe violations increase
- ❌ Scope exceeds recipe files

---

## Graduation Criteria

Wave 4 is **VERIFIED** when:
1. All recipe checkpoints pass
2. Integration test gate passes
3. All evidence logs show PASS
4. No out-of-scope files in any commit
5. Supervisor review approves

---

## Supervisor Override Commands

```bash
# Reject a commit
git revert --no-commit <sha>
git commit -m "REJECT: <reason>"

# Request revision
echo "NEEDS REVISION: <specific issue>" > /tmp/opencode/revise-<sha>.txt

# Approve after fix
git reset HEAD~1  # Then amend
```

---

*This supervisor is adversarial by default. It assumes REJECT until presented with raw evidence proving PASS.*