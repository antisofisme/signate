#!/bin/bash

# ============================================================================
# Automated Test Runner for Migration 007
# Content Table Rename: content → contents
# ============================================================================
# Purpose: Automate testing workflow with color-coded output and reporting
# Usage: ./run_migration_007_tests.sh [--pre|--post|--full|--rollback]
# ============================================================================

set -e  # Exit on error

# ============================================================================
# Configuration
# ============================================================================

DB_HOST="${DB_HOST:-192.168.5.12}"
DB_PORT="${DB_PORT:-5433}"
DB_USER="${DB_USER:-signage_user}"
DB_NAME="${DB_NAME:-signage_db}"
API_URL="${API_URL:-http://192.168.5.12:8001}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="${SCRIPT_DIR}/results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

PRE_TEST_FILE="${SCRIPT_DIR}/test_migration_007_pre.sql"
POST_TEST_FILE="${SCRIPT_DIR}/test_migration_007_post.sql"
MIGRATION_FILE="${SCRIPT_DIR}/../migrations/007_rename_content_to_contents.sql"
ROLLBACK_FILE="${SCRIPT_DIR}/../migrations/007_rollback_rename_contents_to_content.sql"

# ============================================================================
# Color Codes
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "${CYAN}"
    echo "============================================================================"
    echo "$1"
    echo "============================================================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_step() {
    echo -e "${MAGENTA}▶ $1${NC}"
}

# ============================================================================
# Database Connection Test
# ============================================================================

test_db_connection() {
    print_step "Testing database connection..."

    if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "SELECT 1;" > /dev/null 2>&1; then
        print_success "Database connection successful"
        return 0
    else
        print_error "Database connection failed"
        echo "Host: ${DB_HOST}:${DB_PORT}"
        echo "Database: ${DB_NAME}"
        echo "User: ${DB_USER}"
        return 1
    fi
}

# ============================================================================
# API Connection Test
# ============================================================================

test_api_connection() {
    print_step "Testing API connection..."

    if curl -s -f "${API_URL}/docs" > /dev/null 2>&1; then
        print_success "API connection successful (${API_URL})"
        return 0
    else
        print_warning "API connection failed (${API_URL})"
        echo "This may be expected if backend is stopped for migration"
        return 0  # Non-fatal
    fi
}

# ============================================================================
# Pre-Migration Tests
# ============================================================================

run_pre_migration_tests() {
    print_header "RUNNING PRE-MIGRATION TESTS"

    mkdir -p "${RESULTS_DIR}"
    local result_file="${RESULTS_DIR}/pre_migration_${TIMESTAMP}.txt"

    print_step "Executing pre-migration SQL tests..."

    if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -f "${PRE_TEST_FILE}" > "${result_file}" 2>&1; then
        print_success "Pre-migration tests completed"
    else
        print_error "Pre-migration tests failed"
        cat "${result_file}"
        return 1
    fi

    print_info "Results saved to: ${result_file}"
    echo ""

    # Extract and display key metrics
    print_step "Extracting baseline metrics..."

    local total_records=$(grep -oP 'total_records\s*\|\s*\K\d+' "${result_file}" | head -1)
    local fk_count=$(grep -oP 'fk_count\s*\|\s*\K\d+' "${result_file}" | head -1)
    local index_count=$(grep -oP 'index_count\s*\|\s*\K\d+' "${result_file}" | head -1)

    echo -e "${WHITE}Baseline Metrics:${NC}"
    echo "  Total Records: ${total_records}"
    echo "  Foreign Keys: ${fk_count}"
    echo "  Indexes: ${index_count}"
    echo ""

    # Save metrics for comparison
    cat > "${RESULTS_DIR}/baseline_metrics_${TIMESTAMP}.txt" <<EOF
TOTAL_RECORDS=${total_records}
FK_COUNT=${fk_count}
INDEX_COUNT=${index_count}
EOF

    print_success "Baseline metrics saved"
    return 0
}

# ============================================================================
# Post-Migration Tests
# ============================================================================

run_post_migration_tests() {
    print_header "RUNNING POST-MIGRATION TESTS"

    mkdir -p "${RESULTS_DIR}"
    local result_file="${RESULTS_DIR}/post_migration_${TIMESTAMP}.txt"

    print_step "Executing post-migration SQL tests..."

    if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -f "${POST_TEST_FILE}" > "${result_file}" 2>&1; then
        print_success "Post-migration tests completed"
    else
        print_error "Post-migration tests failed"
        cat "${result_file}"
        return 1
    fi

    print_info "Results saved to: ${result_file}"
    echo ""

    # Analyze results
    print_step "Analyzing test results..."

    local pass_count=$(grep -c "PASS" "${result_file}" || true)
    local fail_count=$(grep -c "FAIL" "${result_file}" || true)
    local warning_count=$(grep -c "WARNING" "${result_file}" || true)

    echo -e "${WHITE}Test Summary:${NC}"
    echo -e "  ${GREEN}PASS: ${pass_count}${NC}"
    echo -e "  ${RED}FAIL: ${fail_count}${NC}"
    echo -e "  ${YELLOW}WARNING: ${warning_count}${NC}"
    echo ""

    # Check for critical failures
    if [ "${fail_count}" -gt 0 ]; then
        print_error "Migration verification failed!"
        echo ""
        echo "Failed checks:"
        grep "FAIL" "${result_file}" | head -10
        echo ""
        print_warning "Consider rollback if data integrity is compromised"
        return 1
    else
        print_success "All critical tests passed!"
        return 0
    fi
}

# ============================================================================
# Compare Pre and Post Results
# ============================================================================

compare_results() {
    print_header "COMPARING PRE AND POST MIGRATION RESULTS"

    # Find most recent pre and post results
    local pre_result=$(ls -t "${RESULTS_DIR}"/pre_migration_*.txt 2>/dev/null | head -1)
    local post_result=$(ls -t "${RESULTS_DIR}"/post_migration_*.txt 2>/dev/null | head -1)

    if [ -z "${pre_result}" ] || [ -z "${post_result}" ]; then
        print_warning "Pre or post migration results not found"
        return 1
    fi

    print_step "Comparing record counts..."

    local pre_records=$(grep -oP 'total_records\s*\|\s*\K\d+' "${pre_result}" | head -1)
    local post_records=$(grep -oP 'total_contents\s*\|\s*\K\d+' "${post_result}" | head -1)

    echo "Pre-migration records: ${pre_records}"
    echo "Post-migration records: ${post_records}"

    if [ "${pre_records}" == "${post_records}" ]; then
        print_success "Record counts match!"
    else
        print_error "Record count mismatch! Data may be lost."
        return 1
    fi

    echo ""
    print_step "Comparing foreign keys..."

    local pre_fk=$(grep -oP 'fk_count\s*\|\s*\K\d+' "${pre_result}" | head -1)
    local post_fk=$(grep -c "PASS.*FK" "${post_result}" || echo "0")

    echo "Pre-migration FKs: ${pre_fk}"
    echo "Post-migration FKs: Expected 4"

    if grep -q "PASS (4/4)" "${post_result}"; then
        print_success "All foreign keys recreated correctly!"
    else
        print_error "Foreign key count mismatch!"
        return 1
    fi

    echo ""
    print_success "Migration data integrity verified!"
    return 0
}

# ============================================================================
# API Endpoint Tests
# ============================================================================

test_api_endpoints() {
    print_header "TESTING API ENDPOINTS"

    local test_results=()
    local failed_tests=0

    # Test 1: List content
    print_step "Testing GET /api/content..."
    if curl -s -f "${API_URL}/api/content" > /dev/null; then
        print_success "GET /api/content - OK"
    else
        print_error "GET /api/content - FAILED"
        ((failed_tests++))
    fi

    # Test 2: Get content details (if any exist)
    print_step "Testing GET /api/content/{id}..."
    local content_id=$(curl -s "${API_URL}/api/content" | jq -r '.[0].id' 2>/dev/null)
    if [ -n "${content_id}" ] && [ "${content_id}" != "null" ]; then
        if curl -s -f "${API_URL}/api/content/${content_id}" > /dev/null; then
            print_success "GET /api/content/{id} - OK"
        else
            print_error "GET /api/content/{id} - FAILED"
            ((failed_tests++))
        fi
    else
        print_warning "No content found to test GET /api/content/{id}"
    fi

    # Test 3: Playlists endpoint
    print_step "Testing GET /api/playlists..."
    if curl -s -f "${API_URL}/api/playlists" > /dev/null; then
        print_success "GET /api/playlists - OK"
    else
        print_error "GET /api/playlists - FAILED"
        ((failed_tests++))
    fi

    # Test 4: Settings endpoint
    print_step "Testing GET /api/settings/system/info..."
    if curl -s -f "${API_URL}/api/settings/system/info" > /dev/null; then
        print_success "GET /api/settings/system/info - OK"
    else
        print_error "GET /api/settings/system/info - FAILED"
        ((failed_tests++))
    fi

    echo ""
    if [ ${failed_tests} -eq 0 ]; then
        print_success "All API endpoint tests passed!"
        return 0
    else
        print_error "${failed_tests} API tests failed"
        return 1
    fi
}

# ============================================================================
# Create Backup
# ============================================================================

create_backup() {
    print_header "CREATING DATABASE BACKUP"

    local backup_dir="${SCRIPT_DIR}/../backups"
    mkdir -p "${backup_dir}"

    local backup_file="${backup_dir}/signage_db_pre_migration_007_${TIMESTAMP}.sql"

    print_step "Creating backup: ${backup_file}"

    if command -v docker &> /dev/null; then
        # If docker is available, use it
        if docker exec signage-postgres pg_dump -U "${DB_USER}" "${DB_NAME}" > "${backup_file}" 2>/dev/null; then
            print_success "Backup created successfully"
        else
            print_warning "Docker backup failed, trying direct pg_dump..."
            if PGPASSWORD="${DB_PASSWORD}" pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${DB_NAME}" > "${backup_file}"; then
                print_success "Backup created successfully"
            else
                print_error "Backup failed!"
                return 1
            fi
        fi
    else
        # Use direct pg_dump
        if PGPASSWORD="${DB_PASSWORD}" pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" "${DB_NAME}" > "${backup_file}"; then
            print_success "Backup created successfully"
        else
            print_error "Backup failed!"
            return 1
        fi
    fi

    local backup_size=$(du -h "${backup_file}" | cut -f1)
    print_info "Backup size: ${backup_size}"
    print_info "Backup location: ${backup_file}"

    return 0
}

# ============================================================================
# Execute Migration
# ============================================================================

execute_migration() {
    print_header "EXECUTING MIGRATION 007"

    if [ ! -f "${MIGRATION_FILE}" ]; then
        print_error "Migration file not found: ${MIGRATION_FILE}"
        return 1
    fi

    print_step "Running migration script..."

    local migration_output="${RESULTS_DIR}/migration_execution_${TIMESTAMP}.txt"

    if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -f "${MIGRATION_FILE}" > "${migration_output}" 2>&1; then
        print_success "Migration executed successfully"

        # Verify table exists
        if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
            -c "\\dt contents" | grep -q "contents"; then
            print_success "Table 'contents' verified"
        else
            print_error "Table 'contents' not found after migration!"
            return 1
        fi
    else
        print_error "Migration failed!"
        cat "${migration_output}"
        return 1
    fi

    print_info "Migration output saved to: ${migration_output}"
    return 0
}

# ============================================================================
# Execute Rollback
# ============================================================================

execute_rollback() {
    print_header "EXECUTING ROLLBACK"

    if [ ! -f "${ROLLBACK_FILE}" ]; then
        print_error "Rollback file not found: ${ROLLBACK_FILE}"
        return 1
    fi

    print_warning "This will revert the migration!"
    read -p "Are you sure you want to rollback? (yes/no): " confirm

    if [ "${confirm}" != "yes" ]; then
        print_info "Rollback cancelled"
        return 0
    fi

    print_step "Running rollback script..."

    local rollback_output="${RESULTS_DIR}/rollback_execution_${TIMESTAMP}.txt"

    if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        -f "${ROLLBACK_FILE}" > "${rollback_output}" 2>&1; then
        print_success "Rollback executed successfully"

        # Verify table exists
        if PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
            -c "\\dt content" | grep -q "content"; then
            print_success "Table 'content' verified"
        else
            print_error "Table 'content' not found after rollback!"
            return 1
        fi
    else
        print_error "Rollback failed!"
        cat "${rollback_output}"
        return 1
    fi

    print_info "Rollback output saved to: ${rollback_output}"
    return 0
}

# ============================================================================
# Full Test Suite
# ============================================================================

run_full_test_suite() {
    print_header "RUNNING FULL TEST SUITE FOR MIGRATION 007"

    local start_time=$(date +%s)
    local test_failed=0

    # Phase 1: Pre-checks
    print_info "Phase 1: Pre-checks"
    test_db_connection || exit 1
    test_api_connection
    echo ""

    # Phase 2: Pre-migration tests
    print_info "Phase 2: Pre-migration tests"
    if ! run_pre_migration_tests; then
        print_error "Pre-migration tests failed"
        exit 1
    fi
    echo ""

    # Phase 3: Backup
    print_info "Phase 3: Database backup"
    if ! create_backup; then
        print_error "Backup failed - aborting migration"
        exit 1
    fi
    echo ""

    # Phase 4: Execute migration
    print_info "Phase 4: Execute migration"
    print_warning "This will modify the database schema!"
    read -p "Proceed with migration? (yes/no): " proceed

    if [ "${proceed}" != "yes" ]; then
        print_info "Migration cancelled by user"
        exit 0
    fi

    if ! execute_migration; then
        print_error "Migration execution failed"
        exit 1
    fi
    echo ""

    # Phase 5: Post-migration tests
    print_info "Phase 5: Post-migration verification"
    if ! run_post_migration_tests; then
        print_error "Post-migration tests failed"
        test_failed=1
    fi
    echo ""

    # Phase 6: Compare results
    print_info "Phase 6: Data integrity comparison"
    if ! compare_results; then
        print_error "Data integrity check failed"
        test_failed=1
    fi
    echo ""

    # Phase 7: API tests
    print_info "Phase 7: API endpoint testing"
    if ! test_api_endpoints; then
        print_warning "Some API tests failed"
    fi
    echo ""

    # Final report
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    print_header "TEST SUITE COMPLETE"
    echo "Duration: ${duration} seconds"
    echo "Results directory: ${RESULTS_DIR}"
    echo ""

    if [ ${test_failed} -eq 0 ]; then
        print_success "Migration 007 completed successfully!"
        echo ""
        echo "Next steps:"
        echo "  1. Update backend code if not already done"
        echo "  2. Restart backend API: docker-compose restart backend-api"
        echo "  3. Test frontend functionality"
        echo "  4. Monitor production logs"
        return 0
    else
        print_error "Migration completed with errors!"
        echo ""
        echo "Recommended actions:"
        echo "  1. Review test results in ${RESULTS_DIR}"
        echo "  2. Check database state"
        echo "  3. Consider rollback if critical failures exist"
        echo "  4. Run: $0 --rollback"
        return 1
    fi
}

# ============================================================================
# Generate Test Report
# ============================================================================

generate_test_report() {
    print_header "GENERATING TEST REPORT"

    local report_file="${RESULTS_DIR}/migration_007_report_${TIMESTAMP}.md"

    cat > "${report_file}" <<EOF
# Migration 007 Test Report

**Date**: $(date)
**Migration**: Rename content table to contents
**Tested By**: $(whoami)
**Environment**: ${DB_HOST}:${DB_PORT}/${DB_NAME}

---

## Summary

Test execution completed at $(date +"%Y-%m-%d %H:%M:%S")

## Test Results

### Pre-Migration Tests
$([ -f "${RESULTS_DIR}"/pre_migration_*.txt ] && echo "✓ Completed" || echo "✗ Not run")

### Migration Execution
$([ -f "${RESULTS_DIR}"/migration_execution_*.txt ] && echo "✓ Completed" || echo "✗ Not run")

### Post-Migration Tests
$([ -f "${RESULTS_DIR}"/post_migration_*.txt ] && echo "✓ Completed" || echo "✗ Not run")

### API Endpoint Tests
Run manually or with --full option

---

## Files Generated

- Pre-migration results: ${RESULTS_DIR}/pre_migration_*.txt
- Post-migration results: ${RESULTS_DIR}/post_migration_*.txt
- Migration output: ${RESULTS_DIR}/migration_execution_*.txt

---

## Recommendations

Review all test outputs before deploying to production.

EOF

    print_success "Report generated: ${report_file}"
    return 0
}

# ============================================================================
# Main Script
# ============================================================================

show_usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Automated test runner for Migration 007 (content → contents)

OPTIONS:
    --pre           Run pre-migration tests only
    --post          Run post-migration tests only
    --compare       Compare pre and post migration results
    --api           Test API endpoints only
    --backup        Create database backup only
    --migrate       Execute migration only
    --rollback      Execute rollback migration
    --full          Run complete test suite (pre + migrate + post + api)
    --report        Generate test report
    --help          Show this help message

ENVIRONMENT VARIABLES:
    DB_HOST         Database host (default: 192.168.5.12)
    DB_PORT         Database port (default: 5433)
    DB_USER         Database user (default: signage_user)
    DB_NAME         Database name (default: signage_db)
    DB_PASSWORD     Database password (required)
    API_URL         API base URL (default: http://192.168.5.12:8001)

EXAMPLES:
    # Run pre-migration tests
    DB_PASSWORD=secret $0 --pre

    # Run full test suite
    DB_PASSWORD=secret $0 --full

    # Rollback migration
    DB_PASSWORD=secret $0 --rollback

EOF
}

# Main entry point
main() {
    if [ -z "${DB_PASSWORD}" ]; then
        print_error "DB_PASSWORD environment variable is required"
        echo "Example: DB_PASSWORD=secret $0 --pre"
        exit 1
    fi

    case "${1:-}" in
        --pre)
            test_db_connection && run_pre_migration_tests
            ;;
        --post)
            test_db_connection && run_post_migration_tests
            ;;
        --compare)
            compare_results
            ;;
        --api)
            test_api_connection && test_api_endpoints
            ;;
        --backup)
            create_backup
            ;;
        --migrate)
            test_db_connection && create_backup && execute_migration
            ;;
        --rollback)
            test_db_connection && execute_rollback
            ;;
        --full)
            run_full_test_suite
            ;;
        --report)
            generate_test_report
            ;;
        --help)
            show_usage
            ;;
        *)
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
