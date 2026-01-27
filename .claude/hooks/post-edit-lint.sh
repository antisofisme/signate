#!/bin/bash
# Post-edit hook: Lint after file modification

FILE_PATH="$1"

# Python files
if [[ "$FILE_PATH" =~ \.py$ ]]; then
    if command -v ruff &> /dev/null; then
        echo "[HOOK] Running ruff on $FILE_PATH"
        ruff check "$FILE_PATH" --fix --quiet 2>/dev/null || true
    fi
fi

# TypeScript/JavaScript files
if [[ "$FILE_PATH" =~ \.(ts|tsx|js|jsx)$ ]]; then
    # Find project root with package.json
    DIR=$(dirname "$FILE_PATH")
    while [[ "$DIR" != "/" ]]; do
        if [[ -f "$DIR/package.json" ]]; then
            if [[ -f "$DIR/node_modules/.bin/eslint" ]]; then
                echo "[HOOK] Running ESLint on $FILE_PATH"
                "$DIR/node_modules/.bin/eslint" "$FILE_PATH" --fix --quiet 2>/dev/null || true
            fi
            break
        fi
        DIR=$(dirname "$DIR")
    done
fi

exit 0
