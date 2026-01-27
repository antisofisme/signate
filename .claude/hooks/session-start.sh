#!/bin/bash
# Session start hook: Initialize development environment

echo "============================================"
echo "PROJECT_BESAR Development Session"
echo "============================================"

# Check Docker
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        echo "[OK] Docker: Running"
    else
        echo "[WARN] Docker: Not running"
    fi
else
    echo "[INFO] Docker: Not installed"
fi

# Check Python environment
if [[ -d "PROJECT_BESAR/backend/venv" ]]; then
    echo "[OK] Python venv: Found"
else
    echo "[INFO] Python venv: Not found"
fi

# Check Node/Bun
if command -v bun &> /dev/null; then
    echo "[OK] Bun: $(bun --version)"
elif command -v node &> /dev/null; then
    echo "[OK] Node: $(node --version)"
else
    echo "[WARN] Node/Bun: Not found"
fi

# Git status
if command -v git &> /dev/null; then
    if git rev-parse --git-dir &> /dev/null; then
        BRANCH=$(git branch --show-current 2>/dev/null)
        CHANGES=$(git status --porcelain 2>/dev/null | wc -l)
        echo "[GIT] Branch: $BRANCH | Changes: $CHANGES"
    fi
fi

echo "============================================"
echo "Use /dev to start development servers"
echo "Use /review before committing"
echo "============================================"
