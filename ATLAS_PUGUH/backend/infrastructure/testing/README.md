# Load Testing Framework

Load testing infrastructure for Core Service API using Locust.

**Source**: Phase 2 Design & Execution Plan - Section 4.4

## Overview

This framework provides load testing to compare:
- **Phase 1 Baseline**: Performance without caching, rate limiting
- **Phase 2 Instrumented**: Performance with Redis caching, rate limiting, connection pooling

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-phase2-week2.txt
```

### 2. Run Load Test

```bash
# Automated comparison (Phase 1 vs Phase 2)
./scripts/run_load_test.sh mixed 10 60s

# Phase 1 baseline only
LOAD_TEST_REDIS_ENABLED=false \
LOAD_TEST_RATE_LIMIT_ENABLED=false \
locust -f infrastructure/testing/locustfile.py \
  MixedWorkloadScenario \
  --host http://localhost:8001 \
  --users 10 --spawn-rate 1 --run-time 60s --headless

# Phase 2 instrumented only
LOAD_TEST_REDIS_ENABLED=true \
LOAD_TEST_RATE_LIMIT_ENABLED=true \
locust -f infrastructure/testing/locustfile.py \
  MixedWorkloadScenario \
  --host http://localhost:8001 \
  --users 10 --spawn-rate 1 --run-time 60s --headless
```

### 3. View Results

```bash
# HTML reports
open load_test_results/phase1_baseline_report.html
open load_test_results/phase2_instrumented_report.html

# Comparison report
cat load_test_results/comparison_report.md
```

## Test Scenarios

### 1. Decision Test Scenario

Tests decision creation and retrieval endpoints.

**Endpoints**:
- `POST /api/v1/decisions` (70% of requests)
- `GET /api/v1/decisions/{id}` (20% of requests)
- `GET /api/v1/decisions` (10% of requests)

**Measures**:
- Rule cache hit rates
- Idempotency cache hit rates
- Decision creation throughput
- Latency (p50, p95, p99)

**Usage**:
```bash
locust -f infrastructure/testing/locustfile.py \
  DecisionTestScenario \
  --host http://localhost:8001 \
  --users 10 --spawn-rate 1 --run-time 60s
```

### 2. Workflow Test Scenario

Tests workflow creation and approval endpoints.

**Endpoints**:
- `POST /api/v1/workflows` (60% of requests)
- `POST /api/v1/workflows/{id}/approve` (40% of requests)

**Measures**:
- Workflow creation throughput
- Approval processing latency
- Error rates

**Usage**:
```bash
locust -f infrastructure/testing/locustfile.py \
  WorkflowTestScenario \
  --host http://localhost:8001 \
  --users 10 --spawn-rate 1 --run-time 60s
```

### 3. Mixed Workload Scenario

Simulates realistic production workload (70% decisions, 30% workflows).

**Endpoints**:
- `POST /api/v1/decisions` (50% weight)
- `GET /api/v1/decisions/{id}` (20% weight)
- `POST /api/v1/workflows` (20% weight)
- `POST /api/v1/workflows/{id}/approve` (10% weight)

**Measures**:
- Combined throughput
- Resource contention
- Connection pool efficiency

**Usage**:
```bash
locust -f infrastructure/testing/locustfile.py \
  MixedWorkloadScenario \
  --host http://localhost:8001 \
  --users 10 --spawn-rate 1 --run-time 60s
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOAD_TEST_HOST` | `http://localhost:8001` | Target API host |
| `LOAD_TEST_REDIS_ENABLED` | `true` | Enable Redis caching |
| `LOAD_TEST_RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `LOAD_TEST_USERS` | `10` | Number of concurrent users |
| `LOAD_TEST_SPAWN_RATE` | `1` | Users spawned per second |
| `LOAD_TEST_RUN_TIME` | `60s` | Test duration |
| `LOAD_TEST_TENANT_ID` | `550e8400-...` | Test tenant UUID |
| `LOAD_TEST_DECISION_TYPE` | `credit_approval` | Decision type |
| `LOAD_TEST_SCENARIO` | `mixed` | Scenario (decisions, workflows, mixed) |
| `LOAD_TEST_OUTPUT_DIR` | `./load_test_results` | Output directory |

### Load Test Parameters

```bash
# Light load (10 users, 1 min)
./scripts/run_load_test.sh mixed 10 60s

# Medium load (50 users, 5 min)
./scripts/run_load_test.sh mixed 50 300s

# Heavy load (100 users, 10 min)
./scripts/run_load_test.sh mixed 100 600s
```

## Performance Targets

Phase 2 performance goals:

| Metric | Target | Description |
|--------|--------|-------------|
| **p95 Latency** | < 200ms | 95th percentile response time |
| **p99 Latency** | < 500ms | 99th percentile response time |
| **Error Rate** | < 0.1% | Failed requests |
| **Throughput** | > 100 req/s | Requests per second |
| **Cache Hit Rate** | > 80% | Rule cache hits (Phase 2) |

## Web UI Mode

For interactive testing with real-time graphs:

```bash
# Start Locust web UI
locust -f infrastructure/testing/locustfile.py \
  --host http://localhost:8001

# Open browser
open http://localhost:8089
```

## Output Files

After running `./scripts/run_load_test.sh`:

```
load_test_results/
├── phase1_baseline_report.html      # Phase 1 HTML report
├── phase1_baseline_stats.csv        # Phase 1 CSV stats
├── phase1_baseline.log              # Phase 1 logs
├── phase2_instrumented_report.html  # Phase 2 HTML report
├── phase2_instrumented_stats.csv    # Phase 2 CSV stats
├── phase2_instrumented.log          # Phase 2 logs
└── comparison_report.md             # Comparison report
```

## Comparison Report

The comparison report includes:

1. **Summary Table**: Side-by-side comparison of key metrics
2. **Detailed Statistics**: Full stats for both phases
3. **Performance Targets**: Phase 2 target compliance
4. **Endpoint Breakdown**: Per-endpoint performance
5. **Key Findings**: Improvement highlights
6. **Recommendations**: Optimization suggestions

Example output:

```markdown
## Summary

| Metric | Phase 1 Baseline | Phase 2 Instrumented | Improvement | Status |
|--------|-----------------|---------------------|-------------|--------|
| Throughput (req/s) | 85.23 | 142.67 | 67.4% | ✓ Better |
| Avg Latency (ms) | 117 | 70 | 40.2% | ✓ Better |
| p95 Latency (ms) | 245 | 158 | 35.5% | ✓ Better |
| p99 Latency (ms) | 512 | 287 | 43.9% | ✓ Better |
| Error Rate (%) | 0.12 | 0.03 | 75.0% | ✓ Better |
```

## Troubleshooting

### High Error Rates

If error rate > 1%:
1. Check application logs: `docker logs signage-backend`
2. Verify database connections: Check pool stats
3. Check rate limiting: Increase limits if hit

### Low Throughput

If throughput < 50 req/s:
1. Check CPU/memory usage
2. Increase worker processes
3. Optimize slow queries
4. Scale horizontally (more instances)

### Cache Misses

If cache hit rate < 50% (Phase 2):
1. Verify Redis is running
2. Check cache TTLs (may be too short)
3. Verify cache keys are correct

## Best Practices

1. **Run baseline first**: Always test Phase 1 before Phase 2
2. **Consistent environment**: Same hardware, same data
3. **Warm-up period**: Let system stabilize before measuring
4. **Multiple runs**: Average results across 3+ runs
5. **Monitor resources**: Watch CPU, memory, disk during tests
6. **Clean data**: Reset database between runs for consistency

## Integration with CI/CD

Example GitHub Actions workflow:

```yaml
name: Load Test

on:
  push:
    branches: [main]

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Start services
        run: docker-compose up -d

      - name: Run load test
        run: ./scripts/run_load_test.sh mixed 10 60s

      - name: Upload reports
        uses: actions/upload-artifact@v2
        with:
          name: load-test-reports
          path: load_test_results/
```

## Architecture Notes

### Phase 1 Baseline

- No Redis caching
- No rate limiting
- Default connection pooling
- Measures raw performance

### Phase 2 Instrumented

- Redis caching enabled (rules, idempotency)
- Rate limiting enabled (per-tenant + global)
- Optimized connection pooling
- Measures optimized performance

### Graceful Degradation

Phase 2 gracefully degrades to Phase 1 behavior if:
- Redis is unavailable (cache misses)
- Rate limiting fails (fail-open policy)
- Connection pool exhausted (waits for connection)

## Related Documentation

- Phase 2 Design: `docs/phase2_design_execution_plan.md`
- Redis Caching: `infrastructure/caching/README.md`
- Rate Limiting: `infrastructure/security/README.md`
- Connection Pooling: `infrastructure/database/README.md`
