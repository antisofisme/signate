#!/bin/bash
# ============================================================================
# ARSAKA_PUGUH Phase A - Run Database Migrations
# ============================================================================
# Purpose: Execute all migrations in sequence
# Usage: ./run_migrations.sh [postgres-host] [postgres-port] [database-name]
# ============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
POSTGRES_HOST="${1:-localhost}"
POSTGRES_PORT="${2:-5433}"
POSTGRES_DB="${3:-arsaka_puguh}"
POSTGRES_USER="${POSTGRES_USER:-atlas_user}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# ============================================================================
# MAIN
# ============================================================================

echo ""
echo "============================================================================"
echo "  ARSAKA_PUGUH Phase A - Database Migration"
echo "============================================================================"
echo ""
echo "Target Database:"
echo "  Host: $POSTGRES_HOST"
echo "  Port: $POSTGRES_PORT"
echo "  Database: $POSTGRES_DB"
echo "  User: $POSTGRES_USER"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    log_error "psql not found. Please install PostgreSQL client."
    exit 1
fi

# Check if password is set
if [ -z "$POSTGRES_PASSWORD" ]; then
    log_warn "POSTGRES_PASSWORD not set. Will prompt for password."
fi

# Test connection
log_step "Testing database connection..."

if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT 1" &>/dev/null; then
    log_info "✅ Connection successful"
else
    log_error "❌ Connection failed"
    log_error "Please verify:"
    log_error "  - PostgreSQL is running"
    log_error "  - Host, port, database name are correct"
    log_error "  - User credentials are valid"
    exit 1
fi

echo ""

# Run migrations
MIGRATIONS=(
    "001_initial_schema.sql"
    "002_immutability_triggers.sql"
    "003_rls_policies.sql"
    "seed_phase_a.sql"
)

for migration in "${MIGRATIONS[@]}"; do
    log_step "Running migration: $migration"

    if [ ! -f "$migration" ]; then
        log_error "Migration file not found: $migration"
        exit 1
    fi

    if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f "$migration"; then
        log_info "✅ Migration succeeded: $migration"
    else
        log_error "❌ Migration failed: $migration"
        exit 1
    fi

    echo ""
done

# Verify migrations
log_step "Verifying migrations..."

EXPECTED_TABLES=(
    "decisions"
    "workflows"
    "workflow_transitions"
    "rules"
    "event_log"
    "operations_audit"
    "idempotency_cache"
    "schema_migrations"
)

for table in "${EXPECTED_TABLES[@]}"; do
    if PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\\dt $table" | grep -q "$table"; then
        log_info "✅ Table exists: $table"
    else
        log_warn "⚠️  Table not found: $table"
    fi
done

echo ""

# Check seed data
log_step "Verifying seed data..."

RULE_COUNT=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM rules WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000';" | xargs)
DECISION_COUNT=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM decisions WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000';" | xargs)
WORKFLOW_COUNT=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM workflows WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000';" | xargs)

log_info "Seed data summary:"
log_info "  - Rules: $RULE_COUNT (expected: 4)"
log_info "  - Decisions: $DECISION_COUNT (expected: 2)"
log_info "  - Workflows: $WORKFLOW_COUNT (expected: 1)"

echo ""

# Success
echo "============================================================================"
log_info "✅ All migrations completed successfully!"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "  1. Start backend API: uvicorn core.app:app --host 0.0.0.0 --port 8001"
echo "  2. Test health endpoint: curl http://localhost:8001/health"
echo "  3. View API docs: http://localhost:8001/api/docs"
echo ""

# ============================================================================
# USAGE EXAMPLES
# ============================================================================
#
# Local PostgreSQL:
#   POSTGRES_PASSWORD=your_password ./run_migrations.sh
#
# Custom host/port:
#   POSTGRES_PASSWORD=your_password ./run_migrations.sh 192.168.1.100 5432 arsaka_puguh
#
# Via Docker container:
#   docker exec -i <container-id> psql -U atlas_user -d arsaka_puguh < 001_initial_schema.sql
#
# ============================================================================
