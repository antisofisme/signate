#!/bin/bash
# ============================================================================
# ARSAKA_PUGUH Phase A - Backend Verification Script
# ============================================================================
# Purpose: Verify backend is ready for Phase A deployment
# Usage: ./verify_phase_a.sh
# ============================================================================

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0

# Functions
log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASS++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAIL++))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_section() {
    echo ""
    echo "============================================================================"
    echo "$1"
    echo "============================================================================"
}

# ============================================================================
# VERIFICATION CHECKS
# ============================================================================

log_section "ARSAKA_PUGUH Phase A - Backend Verification"

# Check 1: Required files exist
log_section "1. Checking Required Files"

FILES=(
    ".env.example"
    "requirements-phase-a.txt"
    "Dockerfile"
    ".dockerignore"
    "README.md"
    "core/app.py"
    "core/api/__init__.py"
    "core/repositories/__init__.py"
    "core/use_cases/__init__.py"
    "migrations/001_initial_schema.sql"
    "migrations/002_immutability_triggers.sql"
    "migrations/003_rls_policies.sql"
    "migrations/seed_phase_a.sql"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        log_pass "File exists: $file"
    else
        log_fail "Missing file: $file"
    fi
done

# Check 2: Python dependencies
log_section "2. Checking Python Dependencies"

if [ -f "requirements-phase-a.txt" ]; then
    REQUIRED_PACKAGES=(
        "fastapi"
        "uvicorn"
        "sqlalchemy"
        "asyncpg"
        "pydantic"
        "python-jose"
        "passlib"
    )

    for package in "${REQUIRED_PACKAGES[@]}"; do
        if grep -q "$package" requirements-phase-a.txt; then
            log_pass "Dependency listed: $package"
        else
            log_fail "Missing dependency: $package"
        fi
    done

    # Check for DISABLED packages (should NOT be in Phase A)
    DISABLED_PACKAGES=(
        "redis"
        "slowapi"
        "prometheus"
        "opentelemetry"
    )

    for package in "${DISABLED_PACKAGES[@]}"; do
        if grep -q "$package" requirements-phase-a.txt; then
            log_fail "Phase A should NOT include: $package"
        else
            log_pass "Correctly excluded: $package"
        fi
    done
fi

# Check 3: .env.example configuration
log_section "3. Checking .env.example Configuration"

if [ -f ".env.example" ]; then
    REQUIRED_VARS=(
        "DATABASE_URL"
        "JWT_SECRET_KEY"
        "ALLOWED_TENANT_IDS"
        "REDIS_ENABLED=false"
        "RATE_LIMIT_ENABLED=false"
        "ENABLE_METRICS=false"
        "ENABLE_TRACING=false"
        "POOL_SIZE=2"
        "MAX_OVERFLOW=3"
    )

    for var in "${REQUIRED_VARS[@]}"; do
        VAR_NAME="${var%%=*}"
        if grep -q "$VAR_NAME" .env.example; then
            log_pass "Config variable present: $VAR_NAME"
        else
            log_fail "Missing config variable: $VAR_NAME"
        fi
    done
fi

# Check 4: Dockerfile optimization
log_section "4. Checking Dockerfile"

if [ -f "Dockerfile" ]; then
    if grep -q "multi-stage" Dockerfile || grep -q "AS builder" Dockerfile; then
        log_pass "Multi-stage build detected"
    else
        log_warn "No multi-stage build detected"
    fi

    if grep -q "PYTHONDONTWRITEBYTECODE" Dockerfile; then
        log_pass "PYTHONDONTWRITEBYTECODE flag set"
    else
        log_warn "PYTHONDONTWRITEBYTECODE not set"
    fi

    if grep -q "HEALTHCHECK" Dockerfile; then
        log_pass "Health check configured"
    else
        log_warn "No health check configured"
    fi

    if grep -q "USER" Dockerfile; then
        log_pass "Non-root user configured"
    else
        log_warn "Running as root (security risk)"
    fi
fi

# Check 5: Migrations
log_section "5. Checking Database Migrations"

MIGRATION_FILES=(
    "001_initial_schema.sql"
    "002_immutability_triggers.sql"
    "003_rls_policies.sql"
    "seed_phase_a.sql"
)

cd migrations 2>/dev/null || true

for migration in "${MIGRATION_FILES[@]}"; do
    if [ -f "$migration" ]; then
        # Check SQL syntax (basic)
        if grep -q "BEGIN;" "$migration" && grep -q "COMMIT;" "$migration"; then
            log_pass "Migration valid: $migration"
        else
            log_warn "Migration may be missing transaction: $migration"
        fi
    else
        log_fail "Missing migration: $migration"
    fi
done

cd .. 2>/dev/null || true

# Check 6: Core application structure
log_section "6. Checking Core Application Structure"

CORE_MODULES=(
    "core/app.py"
    "core/api/__init__.py"
    "core/api/routers.py"
    "core/api/schemas.py"
    "core/api/dependencies.py"
    "core/domain/__init__.py"
    "core/repositories/__init__.py"
    "core/use_cases/__init__.py"
)

for module in "${CORE_MODULES[@]}"; do
    if [ -f "$module" ]; then
        log_pass "Core module exists: $module"
    else
        log_warn "Optional module missing: $module"
    fi
done

# Check 7: Phase A configuration in app.py
log_section "7. Checking Phase A Configuration in app.py"

if [ -f "core/app.py" ]; then
    if grep -q "POOL_SIZE.*getenv" core/app.py; then
        log_pass "Pool size configurable via env"
    else
        log_fail "Pool size not configurable"
    fi

    if grep -q "REDIS_ENABLED.*false" core/app.py; then
        log_pass "Redis disabled by default"
    else
        log_warn "Redis enabled by default (should be false for Phase A)"
    fi

    if grep -q "PHASE_A_WARNING" core/app.py; then
        log_pass "Phase A warning configured"
    else
        log_warn "No Phase A warning"
    fi
fi

# Check 8: Seed data
log_section "8. Checking Seed Data"

if [ -f "migrations/seed_phase_a.sql" ]; then
    # Check tenant ID
    if grep -q "550e8400-e29b-41d4-a716-446655440000" migrations/seed_phase_a.sql; then
        log_pass "Hardcoded tenant ID present"
    else
        log_fail "Tenant ID not found in seed data"
    fi

    # Check rules
    if grep -q "INSERT INTO rules" migrations/seed_phase_a.sql; then
        RULE_COUNT=$(grep -c "INSERT INTO rules" migrations/seed_phase_a.sql)
        if [ "$RULE_COUNT" -ge 3 ]; then
            log_pass "Seed data includes $RULE_COUNT rules"
        else
            log_warn "Only $RULE_COUNT rules in seed data (expected 3+)"
        fi
    else
        log_fail "No rules in seed data"
    fi
fi

# Check 9: Docker build test (optional, requires Docker)
log_section "9. Docker Build Test (Optional)"

if command -v docker &> /dev/null; then
    log_info "Docker available, testing build..."

    # Try dry-run build (parse Dockerfile)
    if docker build --help | grep -q "dry-run"; then
        if docker build --dry-run -t arsaka-puguh-backend:test . &>/dev/null; then
            log_pass "Dockerfile syntax valid"
        else
            log_warn "Dockerfile may have syntax errors"
        fi
    else
        log_info "Skipping dry-run (Docker version doesn't support it)"
    fi
else
    log_info "Docker not available, skipping build test"
fi

# ============================================================================
# SUMMARY
# ============================================================================

log_section "Verification Summary"

echo ""
echo -e "${GREEN}Passed:${NC} $PASS"
echo -e "${RED}Failed:${NC} $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Backend is ready for Phase A deployment.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review .env.example and create .env with actual secrets"
    echo "  2. Build Docker image: docker build -t arsaka-puguh-backend:phase-a ."
    echo "  3. Test locally: docker run -p 8001:8001 --env-file .env arsaka-puguh-backend:phase-a"
    echo "  4. Upload to VPS: ../nomad/upload_to_vps.sh"
    echo ""
    exit 0
else
    echo -e "${RED}❌ $FAIL check(s) failed. Please fix issues before deployment.${NC}"
    echo ""
    exit 1
fi
