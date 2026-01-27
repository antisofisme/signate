#!/bin/bash
# Pre-edit hook: Check before file modification

FILE_PATH="$1"

# Skip non-code files
if [[ ! "$FILE_PATH" =~ \.(py|ts|tsx|js|jsx)$ ]]; then
    exit 0
fi

# Check if file exists and is tracked by git
if [[ -f "$FILE_PATH" ]]; then
    # Backup check - ensure we can recover
    if command -v git &> /dev/null; then
        if git ls-files --error-unmatch "$FILE_PATH" &> /dev/null; then
            echo "[HOOK] File tracked by git: $FILE_PATH"
        else
            echo "[HOOK] WARNING: File not tracked by git: $FILE_PATH"
        fi
    fi
fi

# Check for potential sensitive files
if [[ "$FILE_PATH" =~ (\.env|secret|credential|password|key) ]]; then
    echo "[HOOK] WARNING: Modifying sensitive file: $FILE_PATH"
fi

exit 0
