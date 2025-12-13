#!/bin/bash
# Pre-commit hook: Validate before commit

echo "[HOOK] Running pre-commit checks..."

# Check for debug statements
if git diff --cached --name-only | xargs grep -l "console\.log\|print(\|debugger\|pdb\." 2>/dev/null; then
    echo "[HOOK] WARNING: Debug statements found in staged files"
fi

# Check for TODO/FIXME
if git diff --cached --name-only | xargs grep -l "TODO\|FIXME\|XXX\|HACK" 2>/dev/null; then
    echo "[HOOK] WARNING: TODO/FIXME comments found in staged files"
fi

# Check for sensitive data patterns
SENSITIVE_PATTERNS="password\s*=\s*['\"]|api_key\s*=\s*['\"]|secret\s*=\s*['\"]"
if git diff --cached | grep -E "$SENSITIVE_PATTERNS" 2>/dev/null; then
    echo "[HOOK] ERROR: Potential sensitive data in staged changes"
    exit 1
fi

# Run tests for changed Python files
CHANGED_PY=$(git diff --cached --name-only --diff-filter=ACMR | grep "\.py$")
if [[ -n "$CHANGED_PY" ]]; then
    echo "[HOOK] Python files changed, running type check..."
    if command -v mypy &> /dev/null; then
        mypy $CHANGED_PY --ignore-missing-imports --no-error-summary 2>/dev/null || true
    fi
fi

echo "[HOOK] Pre-commit checks completed"
exit 0
