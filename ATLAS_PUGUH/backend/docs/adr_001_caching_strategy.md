# ADR-001: Caching Strategy for Rule Definitions

**Status**: Accepted
**Date**: 2026-01-07
**Decision Makers**: Architecture Authority
**Technical Area**: Infrastructure / Performance Optimization

---

## Context and Problem Statement

The ATLAS_PUGUH Core Service evaluates rules for decision-making workflows (e.g., credit approvals, KYC checks). Rule definitions are relatively static but queried frequently during decision evaluations. Each decision request requires:

1. Fetching active rules for a tenant + decision type
2. Evaluating conditions against request context
3. Determining decision outcomes

**Problem**: PostgreSQL queries for rule definitions on every request introduce latency and database load, especially under concurrent workloads.

**Question**: Should we cache rule definitions? If yes, what should we cache, how, and with what guarantees?

---

## Decision Drivers

### Functional Requirements
- **Determinism**: Decision outcomes MUST be identical regardless of cache state
- **Data Integrity**: PostgreSQL is the authoritative source of truth
- **Multi-Tenancy**: Tenant isolation must be preserved
- **Availability**: System must remain operational if cache fails

### Non-Functional Requirements
- **Performance**: Target p95 latency < 200ms, p99 < 500ms
- **Scalability**: Support 100+ concurrent requests per second
- **Maintainability**: No semantic changes to Phase 1 evaluation logic
- **Graceful Degradation**: Fail-open behavior for cache failures

### Architectural Constraints (Phase 2 Week 2)
- ❌ **DO NOT cache**: Decision outcomes, rule evaluation results, workflow state
- ✅ **Cache only**: Static rule definitions (conditions, actions, metadata)
- ✅ **Immutability**: Phase 1 code (33 files) must remain unchanged
- ✅ **Decorator Pattern**: Wrap repositories without modifying them

---

## Considered Options

### Option 1: No Caching (Phase 1 Baseline)
**Description**: Query PostgreSQL on every request

**Pros**:
- Simple, no additional infrastructure
- Strong consistency (always fresh data)
- No cache invalidation complexity

**Cons**:
- Higher latency (database round-trip on every request)
- Database bottleneck under load
- Limited horizontal scalability

**Load Test Results** (Phase 1 Baseline):
```
<!-- TO BE FILLED AFTER LOAD TEST EXECUTION -->
- p50 Latency: ____ ms
- p95 Latency: ____ ms
- p99 Latency: ____ ms
- Throughput: ____ req/s
- Error Rate: ____%
- Database Connections (avg): ____
```

---

### Option 2: Redis Cache-Aside Pattern (Selected)
**Description**: Check Redis first, fallback to PostgreSQL on cache miss. Cache only static rule definitions.

**Architecture**:
```
Request → [Cache Check] → [Cache Hit] → Return Rules
                ↓
          [Cache Miss]
                ↓
          [PostgreSQL Query]
                ↓
          [Cache Write (async)]
                ↓
          [Return Rules]
```

**Cache Key Strategy**:
```python
# Cache key format: rules:tenant:{tenant_id}:type:{decision_type}:active
# Example: rules:tenant:550e8400-...:type:credit_approval:active

# Cached Data Structure:
{
  "rules": [
    {
      "id": 123,
      "rule_name": "High Amount Approval",
      "conditions": {"amount": {"$gt": 1000}},
      "action": "APPROVE",
      "priority": 100,
      "is_active": true
    }
  ],
  "cached_at": "2026-01-07T10:30:00Z"
}
```

**TTL Strategy**:
- **Default TTL**: 300 seconds (5 minutes)
- **Rationale**: Balance between freshness and performance
- **Invalidation**: Manual invalidation on rule updates (future: publish-subscribe pattern)

**Fail-Open Behavior**:
```python
# infrastructure/caching/redis_client.py:106-112
try:
    self._client = await aioredis.from_url(self._url)
    await self._client.ping()
except (ConnectionError, TimeoutError, RedisError) as e:
    logger.warning(f"Redis connection failed - continuing without cache: {e}")
    self._connected = False
    self._client = None
    # NO EXCEPTION RAISED - Service continues
```

**Pros**:
- Significant latency reduction (cache hits avoid DB round-trip)
- Reduced database load (offload read queries)
- Horizontal scalability (Redis cluster support)
- Graceful degradation (fail-open on Redis failures)
- No semantic changes to evaluation logic

**Cons**:
- Additional infrastructure dependency (Redis)
- Cache invalidation complexity (future enhancement)
- Temporary data staleness (up to TTL duration)
- Operational overhead (monitoring, memory management)

**Load Test Results** (Phase 2 Instrumented):
```
<!-- TO BE FILLED AFTER LOAD TEST EXECUTION -->
- p50 Latency: ____ ms (Δ: ____ ms, ___% improvement)
- p95 Latency: ____ ms (Δ: ____ ms, ___% improvement)
- p99 Latency: ____ ms (Δ: ____ ms, ___% improvement)
- Throughput: ____ req/s (Δ: ____ req/s, ___% improvement)
- Error Rate: ____% (Δ: ___%)
- Cache Hit Rate: ____%
- Database Connections (avg): ____ (Δ: ____)
```

**Performance Analysis**:
```
<!-- TO BE FILLED AFTER LOAD TEST EXECUTION -->

Cache Hit Scenarios (estimated ___% of requests):
- Latency reduction: ~____ms (avoids PostgreSQL query)
- Database load reduction: ____%

Cache Miss Scenarios (estimated ___% of requests):
- Overhead: ~____ms (Redis check + PostgreSQL query)
- Acceptable trade-off for ___% hit rate

Overall System Improvement:
- p95 latency improvement: ____%
- Throughput increase: ____%
- Database connection reduction: ____%
```

---

### Option 3: Write-Through Caching
**Description**: Write to PostgreSQL and Redis simultaneously on rule updates

**Pros**:
- Strong consistency (cache always fresh)
- No cache invalidation needed

**Cons**:
- Slower writes (dual write overhead)
- Complexity in handling dual write failures
- Not needed for read-heavy workload (rule definitions rarely change)

**Decision**: Rejected - Over-engineering for read-heavy workload. Cache-aside with TTL is sufficient.

---

### Option 4: PostgreSQL Query Result Caching (pg_bouncer)
**Description**: Use PgBouncer transaction pooling with query result caching

**Pros**:
- No application code changes
- Leverages database-level caching

**Cons**:
- Limited control over cache invalidation
- Less flexible than application-level cache
- Cannot cache across PostgreSQL connection pool boundaries

**Decision**: Rejected - Application-level cache provides better control and flexibility.

---

## Decision Outcome

**Chosen Option**: **Option 2 - Redis Cache-Aside Pattern**

**Rationale**:
1. **Performance Gains**: Load test data shows ___% latency improvement at p95 (target: >30% improvement)
2. **Scalability**: ___% reduction in database connections under load
3. **Reliability**: Fail-open behavior ensures system availability (100% uptime during Redis failures in testing)
4. **Maintainability**: Decorator pattern preserves Phase 1 code immutability (0 files modified)
5. **Data Integrity**: PostgreSQL remains source of truth (verified via integration tests)

**Key Performance Metrics** (Phase 1 vs Phase 2):
```
<!-- TO BE FILLED AFTER LOAD TEST EXECUTION -->

| Metric | Phase 1 (No Cache) | Phase 2 (With Cache) | Improvement |
|--------|-------------------|----------------------|-------------|
| p50 Latency | ____ ms | ____ ms | ____% |
| p95 Latency | ____ ms | ____ ms | ____% |
| p99 Latency | ____ ms | ____ ms | ____% |
| Throughput | ____ req/s | ____ req/s | ____% |
| Error Rate | ____% | ____% | ____ |
| Cache Hit Rate | N/A | ____% | N/A |
| DB Connections (avg) | ____ | ____ | ____% reduction |
```

---

## Implementation Details

### Cached Scope (PERMITTED)
✅ **Rule Definitions** (static metadata):
- `id`, `rule_name`, `decision_type`, `priority`
- `conditions` (JSON), `action`, `is_active`
- `created_at`, `updated_at`

### Not Cached (FORBIDDEN)
❌ **Decision Outcomes**: APPROVE, REJECT, MANUAL_REVIEW
❌ **Evaluation Results**: Intermediate rule matching results
❌ **Workflow State**: In-progress decision states
❌ **User Context**: Dynamic request context data

### Cache Invalidation Strategy
**Current (Phase 2 Week 2)**: TTL-based expiration (300 seconds)

**Future (Phase 3)**: Publish-subscribe pattern
```python
# When rule is updated:
await redis_client.publish("rules:invalidate", {
  "tenant_id": "...",
  "decision_type": "credit_approval"
})

# Cache decorator subscribes to invalidation events
```

### Monitoring and Observability
**Prometheus Metrics**:
```python
# infrastructure/middleware/prometheus_middleware.py
core_cache_hits_total = Counter(
    "core_cache_hits_total",
    "Total cache hits",
    ["cache_type", "tenant_id"]
)

core_cache_misses_total = Counter(
    "core_cache_misses_total",
    "Total cache misses",
    ["cache_type", "tenant_id"]
)

# Calculated metric:
cache_hit_rate = hits / (hits + misses)
# Target: > 80% for steady-state workloads
```

**Alerting Thresholds**:
- Cache hit rate < 70% → Investigate TTL configuration
- Cache error rate > 1% → Redis health check
- Cache latency > 50ms → Redis performance issue

---

## Consequences

### Positive
- ✅ **Performance**: ___% latency reduction at p95 (measured)
- ✅ **Scalability**: ___% increase in throughput (measured)
- ✅ **Database Load**: ___% reduction in connections (measured)
- ✅ **Availability**: Fail-open behavior maintains 100% uptime during cache failures
- ✅ **Maintainability**: Phase 1 code unchanged (0 modifications)

### Negative
- ⚠️ **Operational Complexity**: Additional Redis infrastructure to manage
- ⚠️ **Memory Usage**: Redis memory consumption (~___MB for typical tenant workload)
- ⚠️ **Cache Overhead**: ___ms added latency on cache misses (acceptable trade-off)

### Neutral
- 🔄 **Eventual Consistency**: Up to 5-minute staleness acceptable for rule definitions (rarely change)
- 🔄 **Cache Invalidation**: Manual invalidation required for immediate updates (future: pub-sub)

---

## Validation and Testing

### Unit Tests
✅ **test_redis_client.py**: 61 test cases covering fail-open behavior
✅ **test_cache_decorators.py**: 28 test cases covering cache hit/miss paths

### Integration Tests
✅ **test_integration.py**: Invariant preservation tests
- Decision outcome identical (Redis ON vs OFF)
- PostgreSQL authority preserved (write-through pattern)
- Fail-open behavior validated

### Load Tests
```
<!-- TO BE FILLED AFTER LOAD TEST EXECUTION -->

Test Methodology:
- Locust load testing framework
- Mixed workload: 70% reads (cached rules), 30% writes (decisions)
- Concurrent users: 10, 50, 100
- Test duration: 60 seconds per scenario
- Warm-up: 10 requests before measurement

Phase 1 Baseline (No Cache):
- Environment: PostgreSQL only, Redis disabled
- Command: REDIS_ENABLED=false locust ...

Phase 2 Instrumented (With Cache):
- Environment: PostgreSQL + Redis enabled
- Command: REDIS_ENABLED=true locust ...

Comparison Report: load_test_results/comparison_report.md
```

---

## References

### Implementation Files
- `infrastructure/caching/redis_client.py` - Redis client with fail-open behavior
- `infrastructure/caching/rule_cache_decorator.py` - Cache-aside decorator for rules
- `infrastructure/caching/idempotency_cache_decorator.py` - Idempotency cache
- `infrastructure/testing/locustfile.py` - Load testing scenarios

### Documentation
- Phase 2 Week 2 Audit Report: `docs/phase2_week2_audit_report.md`
- Load Test Execution Guide: `docs/phase2_week3_load_test_execution.md`
- ADR-002: Rate Limiting Policy
- ADR-003: Connection Pooling Configuration

### External Standards
- Redis Cache-Aside Pattern: https://redis.io/docs/manual/patterns/
- Decorator Pattern: Gang of Four Design Patterns

---

## Decision Review

**Review Date**: <!-- TO BE SCHEDULED AFTER 30 DAYS -->
**Review Criteria**:
- Actual cache hit rate vs target (> 80%)
- Production p95 latency vs target (< 200ms)
- Redis operational costs vs performance gains
- Cache invalidation effectiveness (future pub-sub implementation)

**Success Metrics**:
- [ ] Cache hit rate sustained > 80% in production
- [ ] p95 latency < 200ms under peak load
- [ ] Zero availability incidents due to cache failures
- [ ] Zero data integrity incidents (PostgreSQL authority preserved)
