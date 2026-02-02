#!/bin/bash

# =============================================================================
# ARSAKA_PUGUH Database Initialization Script
# =============================================================================
# Purpose: Run all migrations in sequential order to initialize database
# Usage: ./init_database.sh
# Prerequisites: PostgreSQL 13+, database created, connection configured
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# =============================================================================
# Configuration
# =============================================================================

# Database connection (override with environment variables)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-infra_puguh}"
DB_USER="${DB_USER:-postgres}"

# Migration directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# =============================================================================
# Functions
# =============================================================================

log_info() {
  echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
  echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
  log_info "Checking prerequisites..."

  # Check if psql is installed
  if ! command -v psql &> /dev/null; then
    log_error "psql not found. Please install PostgreSQL client."
    exit 1
  fi

  # Check if database is accessible
  if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT 1" &> /dev/null; then
    log_error "Cannot connect to database: $DB_NAME@$DB_HOST:$DB_PORT"
    log_error "Please check connection settings and ensure database is running."
    exit 1
  fi

  log_info "Prerequisites check passed ✓"
}

run_migration() {
  local migration_file=$1
  local migration_name=$(basename $migration_file)

  log_info "Running migration: $migration_name"

  if PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$migration_file" > /dev/null 2>&1; then
    log_info "✓ $migration_name completed successfully"
    return 0
  else
    log_error "✗ $migration_name failed"
    log_error "Check database logs for details"
    return 1
  fi
}

verify_migrations() {
  log_info "Verifying migrations..."

  local count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM schema_migrations")

  if [ "$count" -eq 3 ]; then
    log_info "✓ All 3 migrations verified in schema_migrations table"
  else
    log_warn "Expected 3 migrations, found $count"
  fi
}

verify_tables() {
  log_info "Verifying tables..."

  local expected_tables=(
    "decisions"
    "workflows"
    "workflow_transitions"
    "rules"
    "event_log"
    "operations_audit"
    "idempotency_cache"
    "schema_migrations"
  )

  local missing_tables=()

  for table in "${expected_tables[@]}"; do
    if ! PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "\dt $table" | grep -q "$table"; then
      missing_tables+=("$table")
    fi
  done

  if [ ${#missing_tables[@]} -eq 0 ]; then
    log_info "✓ All 8 tables created successfully"
  else
    log_error "Missing tables: ${missing_tables[*]}"
    exit 1
  fi
}

verify_triggers() {
  log_info "Verifying triggers..."

  local trigger_count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE '%immutable%'")

  if [ "$trigger_count" -ge 6 ]; then
    log_info "✓ All immutability triggers created ($trigger_count triggers)"
  else
    log_warn "Expected at least 6 triggers, found $trigger_count"
  fi
}

verify_rls() {
  log_info "Verifying RLS policies..."

  local policy_count=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM pg_policies WHERE tablename IN ('decisions', 'workflows', 'workflow_transitions', 'rules', 'event_log', 'operations_audit', 'idempotency_cache')")

  if [ "$policy_count" -eq 7 ]; then
    log_info "✓ All 7 RLS policies created successfully"
  else
    log_warn "Expected 7 RLS policies, found $policy_count"
  fi
}

print_summary() {
  echo ""
  echo "============================================"
  echo "ARSAKA_PUGUH Database Initialization"
  echo "============================================"
  echo "Database: $DB_NAME@$DB_HOST:$DB_PORT"
  echo ""
  echo "Migrations Applied:"
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT migration_id, migration_name, applied_at FROM schema_migrations ORDER BY migration_id"
  echo ""
  echo "Tables Created:"
  PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\dt"
  echo ""
  echo "============================================"
  echo -e "${GREEN}✓ Database initialization completed${NC}"
  echo "============================================"
  echo ""
  echo "Next Steps:"
  echo "  1. Verify schema: psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME"
  echo "  2. Run tests: See migrations/README.md"
  echo "  3. Proceed to Week 2-3: Core Service Implementation"
  echo ""
}

# =============================================================================
# Main
# =============================================================================

main() {
  echo ""
  echo "============================================"
  echo "ARSAKA_PUGUH Database Initialization"
  echo "============================================"
  echo "Host: $DB_HOST:$DB_PORT"
  echo "Database: $DB_NAME"
  echo "User: $DB_USER"
  echo "============================================"
  echo ""

  # Check prerequisites
  check_prerequisites

  # Run migrations in order
  log_info "Starting migrations..."
  echo ""

  run_migration "$SCRIPT_DIR/001_initial_schema.sql" || exit 1
  run_migration "$SCRIPT_DIR/002_immutability_triggers.sql" || exit 1
  run_migration "$SCRIPT_DIR/003_rls_policies.sql" || exit 1

  echo ""

  # Verify all migrations
  verify_migrations
  verify_tables
  verify_triggers
  verify_rls

  # Print summary
  print_summary
}

# Run main
main
