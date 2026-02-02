# Phase 2 Week 3 - Load Test Execution Guide

**Date**: 2026-01-07
**Purpose**: Execute Phase 1 baseline vs Phase 2 instrumented load tests
**Status**: Ready for Execution

---

## Prerequisites

### 1. Services Running

**Required Services**:
- PostgreSQL (port 5432)
- Redis (port 6379) - for Phase 2 only
- Backend API (port 8001)

**Start Services**:
```bash
# Start all services
cd /mnt/f/WINDSURF/neliti_code/signate/ARSAKA_PUGUH/backend
docker-compose -f ../docker/docker-compose.yml up -d

# Verify services
docker ps
curl http://localhost:8001/health
```

### 2. Test Data Preparation

**Seed Test Data**:
```bash
# Create test tenant
psql -U signage_user -d signage_db -c "
INSERT INTO organizations (id, name) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'Load Test Org')
ON CONFLICT (id) DO NOTHING;
"

# Create test rules
psql -U signage_user -d signage_db -c "
INSERT INTO rules (tenant_id, rule_name, decision_type, conditions, action, is_active)
VALUES
('550e8400-e29b-41d4-a716-446655440000', 'Test Rule 1', 'credit_approval',
 '{\"amount\": {\"\$gt\": 1000}}', 'APPROVE', true),
('550e8400-e29b-41d4-a716-446655440000', 'Test Rule 2', 'credit_approval',
 '{\"amount\": {\"\$lt\": 500}}', 'REJECT', true)
ON CONFLICT DO NOTHING;
"
```

### 3. Install Load Test Dependencies

```bash
pip install -r requirements-phase2-week2.txt
# Installs: redis[hiredis]==5.0.1, locust==2.20.0
```

---

## Phase 1 Baseline Test

**Configuration**: No Redis, no rate limiting, default connection pool

### Step 1: Configure for Phase 1

```bash
# Disable Phase 2 features
export REDIS_ENABLED=false
export RATE_LIMIT_ENABLED=false

# Use Phase 1 app (core/app.py, not core/app_v2.py)
# Or configure app_v2.py to skip middleware
```

### Step 2: Warm Up Backend

```bash
# Send warm-up requests
for i in {1..10}; do
  curl -X POST http://localhost:8001/api/v1/decisions \
    -H "Content-Type: application/json" \
    -d '{
      "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
      "decision_id": "'$(uuidgen)'",
      "decision_type": "credit_approval",
      "context": {"amount": 5000},
      "idempotency_key": "warmup_'$i'"
    }'
done
```

### Step 3: Execute Phase 1 Load Test

```bash
# Run baseline test
./scripts/run_load_test.sh mixed 10 60s

# Or manual execution:
LOAD_TEST_REDIS_ENABLED=false \
LOAD_TEST_RATE_LIMIT_ENABLED=false \
locust -f infrastructure/testing/locustfile.py \
  MixedWorkloadScenario \
  --host http://localhost:8001 \
  --users 10 \
  --spawn-rate 1 \
  --run-time 60s \
  --headless \
  --html load_test_results/phase1_baseline_report.html \
  --csv load_test_results/phase1_baseline \
  --logfile load_test_results/phase1_baseline.log
```

### Step 4: Collect Phase 1 Metrics

```bash
# Prometheus metrics (if enabled)
curl http://localhost:8001/metrics > load_test_results/phase1_metrics.txt

# Database connection stats
psql -U signage_user -d signage_db -c "
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE datname = 'signage_db';
"
```

---

## Phase 2 Instrumented Test

**Configuration**: Redis enabled, rate limiting enabled, optimized connection pool

### Step 1: Configure for Phase 2

```bash
# Enable Phase 2 features
export REDIS_ENABLED=true
export REDIS_URL=redis://localhost:6379
export RATE_LIMIT_ENABLED=true

# Use Phase 2 app (core/app_v2.py with all middleware)
```

### Step 2: Clear Redis Cache

```bash
# Flush Redis to start fresh
redis-cli FLUSHALL

# Verify empty
redis-cli DBSIZE
# Should return: (integer) 0
```

### Step 3: Warm Up Backend

```bash
# Send warm-up requests (cache population)
for i in {1..10}; do
  curl -X POST http://localhost:8001/api/v1/decisions \
    -H "Content-Type: application/json" \
    -d '{
      "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
      "decision_id": "'$(uuidgen)'",
      "decision_type": "credit_approval",
      "context": {"amount": 5000},
      "idempotency_key": "warmup_phase2_'$i'"
    }'
done
```

### Step 4: Execute Phase 2 Load Test

```bash
# Run instrumented test
LOAD_TEST_REDIS_ENABLED=true \
LOAD_TEST_RATE_LIMIT_ENABLED=true \
locust -f infrastructure/testing/locustfile.py \
  MixedWorkloadScenario \
  --host http://localhost:8001 \
  --users 10 \
  --spawn-rate 1 \
  --run-time 60s \
  --headless \
  --html load_test_results/phase2_instrumented_report.html \
  --csv load_test_results/phase2_instrumented \
  --logfile load_test_results/phase2_instrumented.log
```

### Step 5: Collect Phase 2 Metrics

```bash
# Prometheus metrics
curl http://localhost:8001/metrics > load_test_results/phase2_metrics.txt

# Redis cache stats
redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses"

# Cache hit rate
redis-cli INFO stats | grep -A 10 "Keyspace"

# Database connection stats
psql -U signage_user -d signage_db -c "
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE datname = 'signage_db';
"
```

---

## Generate Comparison Report

```bash
# Generate comparison report
python scripts/compare_load_test_results.py \
  load_test_results/phase1_baseline_stats.csv \
  load_test_results/phase2_instrumented_stats.csv \
  load_test_results/comparison_report.md

# View report
cat load_test_results/comparison_report.md
```

---

## Expected Metrics to Collect

### Performance Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| **p50 Latency** | Median response time | Locust stats CSV |
| **p95 Latency** | 95th percentile | Locust stats CSV |
| **p99 Latency** | 99th percentile | Locust stats CSV |
| **Throughput** | Requests/second | Locust stats CSV |
| **Error Rate** | Failed requests % | Locust stats CSV |

### Phase 2 Specific Metrics

| Metric | Description | Source |
|--------|-------------|--------|
| **Cache Hit Rate** | Rule cache hits % | Prometheus /metrics |
| **Idempotency Cache Hits** | Idempotency cache hits | Prometheus /metrics |
| **Rate Limit Hits** | Requests rate limited | Prometheus /metrics |
| **DB Pool Utilization** | Active connections | Prometheus /metrics |

### Prometheus Metric Queries

```bash
# Cache hit rate
curl -s http://localhost:8001/metrics | grep "core_cache_hits_total"
curl -s http://localhost:8001/metrics | grep "core_cache_misses_total"

# Calculate hit rate:
# hit_rate = hits / (hits + misses)

# Idempotency cache hits
curl -s http://localhost:8001/metrics | grep "core_idempotency_cache_hits_total"

# Rate limiting
curl -s http://localhost:8001/metrics | grep "core_rate_limit_exceeded_total"

# Database pool
curl -s http://localhost:8001/metrics | grep "database_pool_active_connections"
```

---

## Validation Checklist

### Pre-Test Validation

- [ ] All services running (PostgreSQL, Redis, Backend)
- [ ] Test data seeded
- [ ] Warm-up requests completed
- [ ] Baseline metrics recorded

### Post-Test Validation

- [ ] Phase 1 report generated
- [ ] Phase 2 report generated
- [ ] Comparison report generated
- [ ] Prometheus metrics collected
- [ ] No errors in backend logs
- [ ] Redis cache hit rate > 70% (Phase 2)

---

## Troubleshooting

### Issue: High Error Rate

**Symptoms**: Error rate > 1%

**Diagnosis**:
```bash
# Check backend logs
docker logs backend-api --tail 100

# Check database connections
psql -U signage_user -d signage_db -c "
SELECT count(*), state
FROM pg_stat_activity
WHERE datname = 'signage_db'
GROUP BY state;
"
```

**Solutions**:
- Increase connection pool size
- Check for database deadlocks
- Verify test data exists

### Issue: Low Cache Hit Rate

**Symptoms**: Cache hit rate < 50% (Phase 2)

**Diagnosis**:
```bash
# Check Redis keys
redis-cli KEYS "rules:*"
redis-cli KEYS "idempotency:*"

# Check TTLs
redis-cli TTL "rules:tenant:550e8400-e29b-41d4-a716-446655440000:type:credit_approval:active"
```

**Solutions**:
- Increase cache TTL
- Verify cache warming
- Check for cache invalidation

### Issue: Rate Limiting Affecting Results

**Symptoms**: Many 429 responses

**Diagnosis**:
```bash
# Check rate limit counts
curl -s http://localhost:8001/metrics | grep rate_limit

# Check Redis rate limit keys
redis-cli KEYS "rate_limit:*"
```

**Solutions**:
- Increase rate limits for load test
- Use separate tenant for load test
- Disable rate limiting for baseline

---

## Cleanup

```bash
# Stop services
docker-compose -f ../docker/docker-compose.yml down

# Clear test data
psql -U signage_user -d signage_db -c "
DELETE FROM decisions WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000';
DELETE FROM rules WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000';
"

# Clear Redis
redis-cli FLUSHALL

# Archive results
tar -czf load_test_results_$(date +%Y%m%d_%H%M%S).tar.gz load_test_results/
```

---

## Next Steps

1. **Analyze Results**: Review comparison report for improvements
2. **Document Findings**: Update ADRs with performance data
3. **Tune Configuration**: Adjust pool size, cache TTLs based on results
4. **Repeat Testing**: Run with different user counts (10, 50, 100)
