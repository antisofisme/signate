#!/bin/bash
# Tenant isolation check: Verify tenant_id in queries

FILE_PATH="$1"

# Only check Python files
if [[ ! "$FILE_PATH" =~ \.py$ ]]; then
    exit 0
fi

# Skip test files and migrations
if [[ "$FILE_PATH" =~ (test_|_test\.py|migrations/) ]]; then
    exit 0
fi

# Check for select/update/delete without tenant_id
if grep -E "(select|update|delete).*where" "$FILE_PATH" 2>/dev/null | grep -v "tenant_id" | grep -v "#.*noqa" &>/dev/null; then
    echo "[HOOK] WARNING: Query without tenant_id filter in $FILE_PATH"
    echo "        Ensure multi-tenancy isolation is maintained"
fi

# Check for raw SQL without tenant_id
if grep -E "text\(|execute\(" "$FILE_PATH" 2>/dev/null | grep -v "tenant_id" &>/dev/null; then
    echo "[HOOK] WARNING: Raw SQL without tenant_id in $FILE_PATH"
fi

exit 0
