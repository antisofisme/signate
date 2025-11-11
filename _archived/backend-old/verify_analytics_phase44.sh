#!/bin/bash
# Verification Script for Phase 4.4: Analytics System
# Run this script to verify all components are correctly deployed

set -e

echo "============================================"
echo "Phase 4.4 Analytics System Verification"
echo "============================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ PASSED${NC}: $1"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}: $1"
        ((FAILED++))
    fi
}

# 1. Check files exist
echo "1. Checking file existence..."
test -f "app/services/analytics_service.py"
check "analytics_service.py exists"

test -f "app/api/analytics.py"
check "analytics.py exists"

test -f "migrations/013_add_analytics_system.sql"
check "013_add_analytics_system.sql exists"

test -f "../viewer/js/shared/analytics-tracker.js"
check "analytics-tracker.js exists"

# 2. Check line counts
echo ""
echo "2. Checking code metrics..."
ANALYTICS_SERVICE_LINES=$(wc -l < app/services/analytics_service.py)
test $ANALYTICS_SERVICE_LINES -gt 700
check "analytics_service.py has $ANALYTICS_SERVICE_LINES lines (expected: 700+)"

MIGRATION_LINES=$(wc -l < migrations/013_add_analytics_system.sql)
test $MIGRATION_LINES -gt 400
check "Migration has $MIGRATION_LINES lines (expected: 400+)"

API_LINES=$(wc -l < app/api/analytics.py)
test $API_LINES -gt 500
check "API has $API_LINES lines (expected: 500+)"

TRACKER_LINES=$(wc -l < ../viewer/js/shared/analytics-tracker.js)
test $TRACKER_LINES -gt 300
check "Tracker has $TRACKER_LINES lines (expected: 300+)"

# 3. Check database connection
echo ""
echo "3. Checking database connection..."
if command -v psql &> /dev/null; then
    PGPASSWORD="signage" psql -h 192.168.5.12 -p 5433 -U signage -d signage -c "SELECT 1" > /dev/null 2>&1
    check "Database connection successful"
else
    echo -e "${YELLOW}⚠ SKIPPED${NC}: psql not installed"
fi

# 4. Check Python imports
echo ""
echo "4. Checking Python imports..."
python3 -c "
import sys
sys.path.insert(0, 'app')
from services.analytics_service import AnalyticsService
print('AnalyticsService imported successfully')
" > /dev/null 2>&1
check "AnalyticsService imports correctly"

python3 -c "
import sys
sys.path.insert(0, 'app')
from api.analytics import router
print('Analytics router imported successfully')
" > /dev/null 2>&1
check "Analytics API imports correctly"

# 5. Check documentation
echo ""
echo "5. Checking documentation..."
test -f "PHASE4_4_ANALYTICS_COMPLETE.md"
check "Complete documentation exists"

test -f "PHASE4_4_QUICK_REFERENCE.md"
check "Quick reference exists"

test -f "ANALYTICS_PERFORMANCE_BENCHMARK.md"
check "Performance benchmarks exist"

# 6. Check key features in code
echo ""
echo "6. Checking implementation features..."

grep -q "class AnalyticsService" app/services/analytics_service.py
check "AnalyticsService class defined"

grep -q "async def track_event" app/services/analytics_service.py
check "track_event method implemented"

grep -q "async def flush_buffer" app/services/analytics_service.py
check "flush_buffer method implemented"

grep -q "async def get_dashboard_data" app/services/analytics_service.py
check "get_dashboard_data method implemented"

grep -q "CREATE TABLE.*analytics_events" migrations/013_add_analytics_system.sql
check "analytics_events table defined"

grep -q "PARTITION BY RANGE" migrations/013_add_analytics_system.sql
check "Partitioning strategy defined"

grep -q "CREATE MATERIALIZED VIEW.*dashboard_stats" migrations/013_add_analytics_system.sql
check "Materialized view defined"

grep -q "class AnalyticsTracker" ../viewer/js/shared/analytics-tracker.js
check "AnalyticsTracker class defined"

grep -q "trackContentPlay" ../viewer/js/shared/analytics-tracker.js
check "Content tracking implemented"

grep -q "trackHeartbeat" ../viewer/js/shared/analytics-tracker.js
check "Heartbeat tracking implemented"

# Summary
echo ""
echo "============================================"
echo "Verification Summary"
echo "============================================"
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Analytics system is ready for deployment.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review the output above.${NC}"
    exit 1
fi
