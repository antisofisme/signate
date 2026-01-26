#!/bin/bash
#
# Run Load Tests - Phase 1 vs Phase 2 Comparison
#
# This script runs load tests against the Core Service API to compare:
# - Phase 1 Baseline: Without caching, rate limiting
# - Phase 2 Instrumented: With Redis caching, rate limiting, connection pooling
#
# Usage:
#   ./scripts/run_load_test.sh [scenario] [users] [duration]
#
# Examples:
#   ./scripts/run_load_test.sh mixed 10 60s
#   ./scripts/run_load_test.sh decisions 20 120s
#
# Source: Phase 2 Design & Execution Plan - Section 4.4

set -e

# Default configuration
SCENARIO="${1:-mixed}"
USERS="${2:-10}"
DURATION="${3:-60s}"
HOST="${LOAD_TEST_HOST:-http://localhost:8001}"
OUTPUT_DIR="${LOAD_TEST_OUTPUT_DIR:-./load_test_results}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CORE SERVICE LOAD TEST${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Scenario: ${GREEN}$SCENARIO${NC}"
echo -e "Users: ${GREEN}$USERS${NC}"
echo -e "Duration: ${GREEN}$DURATION${NC}"
echo -e "Host: ${GREEN}$HOST${NC}"
echo -e "Output: ${GREEN}$OUTPUT_DIR${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Determine test class based on scenario
case "$SCENARIO" in
  "decisions")
    TEST_CLASS="DecisionTestScenario"
    ;;
  "workflows")
    TEST_CLASS="WorkflowTestScenario"
    ;;
  "mixed")
    TEST_CLASS="MixedWorkloadScenario"
    ;;
  *)
    echo -e "${RED}Error: Unknown scenario '$SCENARIO'${NC}"
    echo "Valid scenarios: decisions, workflows, mixed"
    exit 1
    ;;
esac

# Function to run a single load test
run_test() {
  local phase=$1
  local redis_enabled=$2
  local rate_limit_enabled=$3
  local output_prefix=$4

  echo -e "\n${YELLOW}>>> Running $phase test...${NC}\n"

  # Set environment variables
  export LOAD_TEST_REDIS_ENABLED="$redis_enabled"
  export LOAD_TEST_RATE_LIMIT_ENABLED="$rate_limit_enabled"
  export LOAD_TEST_SCENARIO="$SCENARIO"

  # Run Locust in headless mode
  locust \
    -f infrastructure/testing/locustfile.py \
    "$TEST_CLASS" \
    --host "$HOST" \
    --users "$USERS" \
    --spawn-rate 1 \
    --run-time "$DURATION" \
    --headless \
    --html "$OUTPUT_DIR/${output_prefix}_report.html" \
    --csv "$OUTPUT_DIR/${output_prefix}" \
    --logfile "$OUTPUT_DIR/${output_prefix}.log" \
    --loglevel INFO

  echo -e "\n${GREEN}✓ $phase test completed${NC}"
  echo -e "  Report: $OUTPUT_DIR/${output_prefix}_report.html"
}

# Run Phase 1 baseline test
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}PHASE 1: BASELINE TEST${NC}"
echo -e "${BLUE}(No caching, no rate limiting)${NC}"
echo -e "${BLUE}========================================${NC}"
run_test "Phase 1 Baseline" "false" "false" "phase1_baseline"

# Wait between tests
echo -e "\n${YELLOW}Waiting 10 seconds before Phase 2 test...${NC}"
sleep 10

# Run Phase 2 instrumented test
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}PHASE 2: INSTRUMENTED TEST${NC}"
echo -e "${BLUE}(With caching, rate limiting)${NC}"
echo -e "${BLUE}========================================${NC}"
run_test "Phase 2 Instrumented" "true" "true" "phase2_instrumented"

# Generate comparison report
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}GENERATING COMPARISON REPORT${NC}"
echo -e "${BLUE}========================================${NC}"

python3 scripts/compare_load_test_results.py \
  "$OUTPUT_DIR/phase1_baseline_stats.csv" \
  "$OUTPUT_DIR/phase2_instrumented_stats.csv" \
  "$OUTPUT_DIR/comparison_report.md"

echo -e "\n${GREEN}✓ Comparison report generated${NC}"
echo -e "  Report: $OUTPUT_DIR/comparison_report.md"

# Print summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}LOAD TEST COMPLETED${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Results:"
echo -e "  Phase 1 Report: ${GREEN}$OUTPUT_DIR/phase1_baseline_report.html${NC}"
echo -e "  Phase 2 Report: ${GREEN}$OUTPUT_DIR/phase2_instrumented_report.html${NC}"
echo -e "  Comparison: ${GREEN}$OUTPUT_DIR/comparison_report.md${NC}"
echo -e "\nOpen reports in browser to view detailed metrics."
echo -e "${BLUE}========================================${NC}\n"
