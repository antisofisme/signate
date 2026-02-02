#!/bin/bash
# ============================================================================
# ARSAKA_MANTRA: DB Conformance Re-Audit Runner
# ============================================================================
# Authority: Implementation Conformance Audit
# Date: 2025-01-24
#
# Usage:
#   ./run_conformance_audit.sh
#
# Requirements:
#   - Docker running with mantra-postgres container
#   - OR psql available with access to arsaka_mantra database
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_CONTAINER="mantra-postgres"
DB_NAME="arsaka_mantra"
OWNER_USER="mantra_owner"
APP_USER="mantra_app"

echo "=============================================="
echo "ARSAKA_MANTRA DB CONFORMANCE RE-AUDIT"
echo "=============================================="
echo ""

# Check if Docker container is running
if docker ps | grep -q "$DOCKER_CONTAINER"; then
    echo "[INFO] Using Docker container: $DOCKER_CONTAINER"
    PSQL_OWNER="docker exec -i $DOCKER_CONTAINER psql -U $OWNER_USER -d $DB_NAME"
    PSQL_APP="docker exec -i $DOCKER_CONTAINER psql -U $APP_USER -d $DB_NAME"
else
    echo "[INFO] Docker container not found. Using local psql."
    PSQL_OWNER="psql -U $OWNER_USER -d $DB_NAME"
    PSQL_APP="psql -U $APP_USER -d $DB_NAME"
fi

echo ""
echo "=============================================="
echo "PART 1: ROLE MATRIX VERIFICATION"
echo "=============================================="
echo ""

echo "[TEST 1.1] mantra_app privileges on tables:"
echo "--------------------------------------------"
$PSQL_OWNER <<'EOF'
SELECT
    grantee,
    table_name,
    privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'mantra_app'
  AND table_schema = 'public'
ORDER BY table_name, privilege_type;
EOF

echo ""
echo "[TEST 1.2] mantra_app role attributes:"
echo "---------------------------------------"
$PSQL_OWNER <<'EOF'
SELECT
    rolname,
    rolsuper AS is_superuser,
    rolcreatedb AS can_createdb,
    rolcreaterole AS can_createrole,
    rolreplication AS can_replicate
FROM pg_roles
WHERE rolname = 'mantra_app';
EOF

echo ""
echo "=============================================="
echo "PART 2: TRIGGER VERIFICATION"
echo "=============================================="
echo ""

echo "[TEST 2.1] Triggers on decisions table:"
echo "----------------------------------------"
$PSQL_OWNER <<'EOF'
SELECT
    trigger_name,
    event_manipulation,
    action_timing
FROM information_schema.triggers
WHERE event_object_table = 'decisions'
ORDER BY trigger_name;
EOF

echo ""
echo "[TEST 2.2] Trigger function bodies (no IF conditions):"
echo "-------------------------------------------------------"
$PSQL_OWNER <<'EOF'
SELECT proname, prosrc
FROM pg_proc
WHERE proname IN ('reject_all_updates', 'reject_all_deletes');
EOF

echo ""
echo "=============================================="
echo "PART 3: SCHEMA VERIFICATION"
echo "=============================================="
echo ""

echo "[TEST 3.1] Status column must NOT exist:"
echo "-----------------------------------------"
$PSQL_OWNER <<'EOF'
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'decisions'
  AND column_name IN ('status', 'is_immutable');
EOF
echo "(Expected: 0 rows)"

echo ""
echo "[TEST 3.2] decision_status enum must NOT exist:"
echo "------------------------------------------------"
$PSQL_OWNER <<'EOF'
SELECT typname FROM pg_type WHERE typname = 'decision_status';
EOF
echo "(Expected: 0 rows)"

echo ""
echo "=============================================="
echo "PART 4: BEHAVIORAL TESTS (as mantra_app)"
echo "=============================================="
echo ""

echo "[TEST 4.1] INSERT should SUCCEED:"
echo "----------------------------------"
$PSQL_APP <<'EOF' 2>&1 || true
INSERT INTO decisions (title, description, category, created_by)
VALUES ('Audit Test Decision', 'Testing constitutional enforcement', 'AUDIT', 'auditor')
RETURNING decision_id, title;
EOF

echo ""
echo "[TEST 4.2] UPDATE should FAIL with CONSTITUTIONAL VIOLATION:"
echo "-------------------------------------------------------------"
$PSQL_APP <<'EOF' 2>&1 || true
UPDATE decisions SET title = 'Modified' WHERE category = 'AUDIT';
EOF
echo "(Expected: ERROR - CONSTITUTIONAL VIOLATION)"

echo ""
echo "[TEST 4.3] DELETE should FAIL with CONSTITUTIONAL VIOLATION:"
echo "-------------------------------------------------------------"
$PSQL_APP <<'EOF' 2>&1 || true
DELETE FROM decisions WHERE category = 'AUDIT';
EOF
echo "(Expected: ERROR - CONSTITUTIONAL VIOLATION)"

echo ""
echo "[TEST 4.4] DISABLE TRIGGER should FAIL (permission denied):"
echo "------------------------------------------------------------"
$PSQL_APP <<'EOF' 2>&1 || true
ALTER TABLE decisions DISABLE TRIGGER trigger_reject_all_updates;
EOF
echo "(Expected: ERROR - permission denied or must be owner)"

echo ""
echo "[TEST 4.5] TRUNCATE should FAIL (permission denied):"
echo "-----------------------------------------------------"
$PSQL_APP <<'EOF' 2>&1 || true
TRUNCATE decisions;
EOF
echo "(Expected: ERROR - permission denied)"

echo ""
echo "=============================================="
echo "CONFORMANCE AUDIT COMPLETE"
echo "=============================================="
echo ""
echo "PASS CRITERIA:"
echo "  1. Role Matrix: Only SELECT + INSERT for mantra_app"
echo "  2. Role Attributes: All admin privileges FALSE"
echo "  3. Triggers: reject_all_updates and reject_all_deletes exist"
echo "  4. Trigger Bodies: NO IF conditions (unconditional rejection)"
echo "  5. Schema: No 'status' or 'is_immutable' columns"
echo "  6. Behavioral: UPDATE, DELETE, DISABLE TRIGGER all FAIL"
echo ""
echo "If all criteria met: PHASE 1 PASS"
echo "If any criteria fails: PHASE 1 FAIL - DO NOT proceed to Phase 2"
