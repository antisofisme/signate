# ADR-003: Database Connection Pooling Configuration

**Status**: Accepted
**Date**: 2026-01-07
**Decision Makers**: Architecture Authority
**Technical Area**: Infrastructure / Database / Performance

---

## Context and Problem Statement

The ARSAKA_PUGUH Core Service uses PostgreSQL as the authoritative data store. Each API request typically requires 1-3 database queries (authentication, rule fetching, decision logging). Without connection pooling:

1. **Connection Overhead**: Each request establishes a new TCP connection to PostgreSQL (~10-50ms overhead)
2. **Resource Exhaustion**: PostgreSQL has a finite connection limit (default: 100 connections)
3. **Performance Degradation**: Connection establishment becomes a bottleneck under high concurrency
4. **Cost**: Cloud PostgreSQL charges scale with connection count

**Problem**: How do we efficiently manage database connections to minimize latency, maximize throughput, and prevent resource exhaustion?

**Question**: Should we configure connection pooling? If yes, what pool size, timeout, and overflow strategy?

---

## Decision Drivers

### Functional Requirements
- **Connection Reuse**: Minimize connection establishment overhead
- **Concurrency Support**: Handle 100+ concurrent requests
- **Resource Limits**: Respect PostgreSQL max_connections (100)
- **Fault Tolerance**: Handle connection failures gracefully

### Non-Functional Requirements
- **Performance**: Target p95 latency < 200ms
- **Scalability**: Support horizontal scaling (multiple API instances)
- **Reliability**: No connection leaks or deadlocks
- **Maintainability**: Configuration should be tunable without code changes

### Architectural Constraints (Phase 2 Week 2)
- ❌ **No Semantic Changes**: Pool config MUST NOT change transaction boundaries, retry logic, or error handling
- ✅ **Configuration Only**: Pure infrastructure optimization
- ✅ **Phase 1 Immutability**: No changes to business logic (33 files)

---

## Considered Options

### Option 1: No Connection Pooling (Phase 1 Baseline)
**Description**: Create a new database connection for each request

**Architecture**:
```python
# Simple approach (not scalable)
async def get_db():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        await conn.close()
```

**Pros**:
- Simple implementation
- No connection pool management overhead
- Isolated connections (no cross-request contamination)

**Cons**:
- High latency (10-50ms per connection)
- Resource exhaustion under load (exceeds PostgreSQL max_connections)
- No connection reuse (wasteful)
- Limited scalability

**Load Test Results** (Phase 1 Baseline):
```
<!-- TO BE FILLED AFTER LOAD TEST EXECUTION -->
- Connection establishment time: ____ ms (avg)
- Active connections (peak): ____
- Connection errors: ____%
- p95 latency: ____ ms
- Throughput: ____ req/s
```

**Decision**: Rejected - Unacceptable for production workload.

---

### Option 2: Application-Level Connection Pool (Selected)
**Description**: SQLAlchemy AsyncEngine with connection pooling

**Architecture**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool

# Phase 2 Configuration
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,  # Connection pool
    pool_size=10,         # Base pool size
    max_overflow=10,      # Additional connections on demand
    pool_timeout=30,      # Wait for available connection
    pool_recycle=3600,    # Recycle connections after 1 hour
    pool_pre_ping=True,   # Validate connections before use
    echo=False            # Disable SQL logging (production)
)

async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
```

**Pool Behavior**:
```
┌─────────────────────────────────────────────────┐
│ Connection Pool (pool_size=10, max_overflow=10) │
├─────────────────────────────────────────────────┤
│                                                 │
│  [Core Pool: 10 connections]                   │
│  ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐    │
│  │ C1│ C2│ C3│ C4│ C5│ C6│ C7│ C8│ C9│C10│    │
│  └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘    │
│      ↑ Always maintained                       │
│                                                 │
│  [Overflow Pool: 10 additional on demand]      │
│  ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐    │
│  │C11│C12│C13│C14│C15│C16│C17│C18│C19│C20│    │
│  └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘    │
│      ↑ Created when core pool exhausted        │
│      ↓ Closed when idle (after timeout)        │
│                                                 │
│  Max Total: 20 connections per API instance    │
└─────────────────────────────────────────────────┘
```

**Request Flow**:
```
Request arrives
    ↓
[1] Acquire connection from pool
    ├─ Core pool available? → Use existing connection (fast)
    ├─ Overflow pool available? → Create new connection (slower)
    └─ Pool exhausted? → Wait up to pool_timeout (30s)
    ↓
[2] Execute database query
    ↓
[3] Return connection to pool
    ├─ Core pool? → Keep alive for reuse
    └─ Overflow? → Close after idle timeout
```

**Configuration Tuning**:
```python
# infrastructure/database/pool_config.py

class PoolConfig:
    """Database connection pool configuration"""

    # Core pool size (always maintained)
    POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))

    # Max overflow (additional on-demand)
    MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))

    # Wait timeout for available connection
    POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

    # Recycle connections after N seconds (prevent stale connections)
    POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

    # Validate connection health before use
    POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"

    @classmethod
    def calculate_optimal_pool_size(cls):
        """
        Calculate optimal pool size based on workload characteristics

        Formula: pool_size = (concurrent_requests * avg_db_time) / avg_request_time

        Example:
        - 100 concurrent requests
        - 50ms average DB time per request
        - 200ms average request time
        → pool_size = (100 * 0.05) / 0.2 = 25 connections
        """
        concurrent_requests = int(os.getenv("EXPECTED_CONCURRENT_REQUESTS", "100"))
        avg_db_time_ms = int(os.getenv("AVG_DB_TIME_MS", "50"))
        avg_request_time_ms = int(os.getenv("AVG_REQUEST_TIME_MS", "200"))

        optimal_pool_size = int(
            (concurrent_requests * avg_db_time_ms) / avg_request_time_ms
        )

        # Apply safety margin (20% buffer)
        return int(optimal_pool_size * 1.2)
```

**Pros**:
- ✅ Connection reuse (10-50ms latency reduction per request)
- ✅ Resource management (prevents exceeding PostgreSQL max_connections)
- ✅ Overflow handling (graceful scaling under load)
- ✅ Validation (pool_pre_ping prevents stale connection errors)
- ✅ Configuration flexibility (environment variables)

**Cons**:
- ⚠️ Complexity (requires tuning for workload)
- ⚠️ Memory overhead (idle connections consume PostgreSQL resources)
- ⚠️ Monitoring required (track pool exhaustion)

**Load Test Results** (Phase 2 Instrumented):
```
<!-- TO BE FILLED AFTER LOAD TEST EXECUTION -->
- Connection reuse rate: ____%
- Active connections (peak): ____ (vs ____ in Phase 1)
- Connection errors: ____%
- Pool exhaustion events: ____
- p95 latency: ____ ms (Δ: ____ ms, ___% improvement)
- Throughput: ____ req/s (Δ: ____ req/s, ___% improvement)

Connection Acquisition Times:
- p50: ____ ms (from core pool)
- p95: ____ ms (from overflow pool)
- p99: ____ ms (waiting for available connection)
```

---

### Option 3: External Connection Pooler (PgBouncer)
**Description**: Use PgBouncer as a proxy between application and PostgreSQL

**Architecture**:
```
API Instances (multiple)
    ↓
PgBouncer (connection pooler)
    ├─ Transaction pooling mode
    ├─ Pool size: 50 connections
    └─ Max client connections: 1000
    ↓
PostgreSQL (100 max_connections)
```

**Pros**:
- ✅ Centralized pool management (shared across API instances)
- ✅ Higher connection efficiency (transaction pooling)
- ✅ Reduced PostgreSQL load

**Cons**:
- ⚠️ Additional infrastructure component (operational overhead)
- ⚠️ Transaction pooling limitations (no prepared statements, no session-level SET)
- ⚠️ Single point of failure (requires HA setup)
- ⚠️ Complexity (another service to monitor and tune)

**Decision**: Deferred to Phase 3 - Application-level pooling sufficient for Phase 2.

---

### Option 4: No Pooling + PgBouncer (Hybrid)
**Description**: Disable application pool, rely entirely on PgBouncer

**Configuration**:
```python
engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Disable app-level pooling
)
```

**Pros**:
- Simplified application code
- Centralized management

**Cons**:
- Loses application-level metrics (pool utilization)
- Still requires PgBouncer setup
- Transaction pooling limitations

**Decision**: Rejected - Premature optimization, adds complexity without clear benefit.

---

## Decision Outcome

**Chosen Option**: **Option 2 - Application-Level Connection Pool (SQLAlchemy AsyncEngine)**

**Rationale**:
1. **Performance**: ___% latency reduction (measured in load tests)
2. **Simplicity**: No additional infrastructure required
3. **Flexibility**: Environment-driven configuration
4. **Proven**: Industry-standard solution (SQLAlchemy used by thousands of production apps)

**Configuration Selected**:
```python
# Production configuration (Phase 2 Week 2)
POOL_SIZE = 10          # Core pool (always maintained)
MAX_OVERFLOW = 10       # Overflow pool (on-demand)
POOL_TIMEOUT = 30       # Wait timeout (seconds)
POOL_RECYCLE = 3600     # Connection lifetime (1 hour)
POOL_PRE_PING = True    # Validate before use

# Total max connections: 20 per API instance
# For 3 API instances: 60 connections (well below PostgreSQL max_connections=100)
```

---

## Implementation Details

### No Semantic Changes Verification

**CRITICAL CONSTRAINT**: Pool configuration MUST NOT change:
1. Transaction boundaries (BEGIN/COMMIT/ROLLBACK)
2. Retry logic (application must handle all retries)
3. Error handling (pool failures must propagate to application)
4. Isolation levels (default READ COMMITTED)

**Verification**:
```python
# Phase 1 (No Pool) - Pseudo-code
async def save_decision(data):
    conn = await create_connection()
    try:
        result = await conn.execute("INSERT INTO decisions ...")
        await conn.commit()
        return result
    except Exception as e:
        await conn.rollback()
        raise  # Propagate error
    finally:
        await conn.close()

# Phase 2 (With Pool) - Exact same semantics
async def save_decision(data):
    async with async_session() as session:  # Acquire from pool
        try:
            result = await session.execute("INSERT INTO decisions ...")
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            raise  # Propagate error
        # Session automatically returned to pool
```

**Key Point**: Pool is transparent to business logic. Only difference is connection acquisition source (new vs pooled).

---

### Connection Lifecycle

**Initialization (Startup)**:
```python
# app/core/database.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""

    # Startup: Create connection pool
    logger.info("Creating database connection pool...")
    await init_database_pool()
    logger.info(f"Connection pool initialized: size={POOL_SIZE}, overflow={MAX_OVERFLOW}")

    yield  # Application runs

    # Shutdown: Close connection pool
    logger.info("Closing database connection pool...")
    await close_database_pool()
    logger.info("Connection pool closed")

app = FastAPI(lifespan=lifespan)
```

**Connection Acquisition (Per Request)**:
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for database sessions"""
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()  # Return to pool, not close TCP
```

**Health Check**:
```python
@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check with database connectivity test"""
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "pool_status": {
                "size": engine.pool.size(),
                "checked_in": engine.pool.checkedin(),
                "checked_out": engine.pool.checkedout(),
                "overflow": engine.pool.overflow()
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }
```

---

### Pool Sizing Guidelines

**Formula**:
```
pool_size = (concurrent_requests * avg_db_time_per_request) / avg_total_request_time

Example:
- 100 concurrent requests
- 50ms average DB time per request
- 200ms average total request time
→ pool_size = (100 * 0.05) / 0.2 = 25 connections

Apply 20% safety margin: 25 * 1.2 = 30 connections
→ Configure: pool_size=15, max_overflow=15
```

**Conservative Approach (Phase 2)**:
```python
# Start conservative, tune based on metrics
POOL_SIZE = 10          # Handles ~40 req/s (50ms DB time, 200ms total time)
MAX_OVERFLOW = 10       # Handles burst up to ~80 req/s
```

**Scaling Strategy**:
```
Load Test Results:
- If pool exhaustion > 1% → Increase pool_size
- If DB connections idle > 50% → Decrease pool_size
- If pool_timeout errors > 0.1% → Increase max_overflow
```

---

### Multi-Instance Deployment

**Scenario**: 3 API instances behind load balancer

**Configuration**:
```bash
# Each API instance
POOL_SIZE=10
MAX_OVERFLOW=10
# Total: 3 instances × 20 connections = 60 connections

# PostgreSQL must have:
# max_connections ≥ 60 (API) + 10 (admin) + 10 (buffer) = 80 connections
# Recommended: max_connections=100
```

**Connection Distribution**:
```
Load Balancer
    ├─ API Instance 1: 20 connections (max)
    ├─ API Instance 2: 20 connections (max)
    └─ API Instance 3: 20 connections (max)
    ↓
PostgreSQL: 60 connections (peak) / 100 max_connections (capacity)
```

---

## Monitoring and Observability

### Prometheus Metrics
```python
# infrastructure/middleware/prometheus_middleware.py

database_pool_size = Gauge(
    "database_pool_size",
    "Configured pool size"
)

database_pool_checked_in = Gauge(
    "database_pool_checked_in",
    "Connections checked in (idle)"
)

database_pool_checked_out = Gauge(
    "database_pool_checked_out",
    "Connections checked out (in use)"
)

database_pool_overflow = Gauge(
    "database_pool_overflow",
    "Overflow connections created"
)

database_pool_timeouts_total = Counter(
    "database_pool_timeouts_total",
    "Total pool timeout errors (pool exhausted)"
)

# Calculated metrics:
pool_utilization = checked_out / (size + overflow)  # Target: 50-80%
pool_exhaustion_rate = timeouts / requests          # Target: < 0.1%
```

### Grafana Dashboard
```json
{
  "dashboard": "Database Connection Pool",
  "panels": [
    {
      "title": "Pool Utilization",
      "query": "database_pool_checked_out / (database_pool_size + database_pool_overflow)",
      "target": "50-80% utilization"
    },
    {
      "title": "Pool Exhaustion Events",
      "query": "rate(database_pool_timeouts_total[5m])",
      "alert": "> 0.1% of requests"
    },
    {
      "title": "Connection Acquisition Time",
      "query": "histogram_quantile(0.95, rate(database_pool_acquire_duration_seconds[5m]))",
      "target": "< 10ms at p95"
    }
  ]
}
```

### Alerting Thresholds
```yaml
groups:
  - name: database_pool
    rules:
      - alert: HighPoolUtilization
        expr: |
          database_pool_checked_out /
          (database_pool_size + database_pool_overflow) > 0.9
        for: 5m
        annotations:
          summary: "Database pool utilization > 90%"
          description: "Consider increasing pool_size or max_overflow"

      - alert: PoolExhaustion
        expr: rate(database_pool_timeouts_total[5m]) > 0
        for: 2m
        annotations:
          summary: "Database pool exhausted (timeout errors)"
          description: "Requests waiting for available connections"

      - alert: HighPoolOverflow
        expr: database_pool_overflow > database_pool_size
        for: 10m
        annotations:
          summary: "High overflow usage (exceeds core pool)"
          description: "Consider increasing core pool_size"
```

---

## Consequences

### Positive
- ✅ **Latency Reduction**: ___% improvement at p95 (measured, target: >20%)
- ✅ **Throughput Increase**: ___% improvement (measured, target: >30%)
- ✅ **Resource Efficiency**: ___% reduction in active connections (measured)
- ✅ **Scalability**: Supports horizontal scaling (multiple API instances)
- ✅ **No Semantic Changes**: Phase 1 business logic unchanged (verified)

### Negative
- ⚠️ **Tuning Required**: Optimal pool size depends on workload (requires monitoring)
- ⚠️ **Memory Overhead**: Idle connections consume ~1-2MB each in PostgreSQL
- ⚠️ **Operational Complexity**: Connection pool monitoring and alerting required

### Neutral
- 🔄 **Configuration Management**: Pool size tunable via environment variables
- 🔄 **Horizontal Scaling**: Pool size must account for number of API instances

---

## Validation and Testing

### Unit Tests
✅ **No unit tests required** - Connection pooling is pure configuration, no business logic changes

### Integration Tests
✅ **test_integration.py**: Verified pool does not change:
- Transaction boundaries (COMMIT/ROLLBACK behavior identical)
- Error propagation (exceptions bubble up correctly)
- Isolation levels (READ COMMITTED preserved)

### Load Tests
```
<!-- TO BE FILLED AFTER LOAD TEST EXECUTION -->

Test Scenarios:
1. Phase 1 (No Pool):
   - Throughput: ____ req/s
   - p95 latency: ____ ms
   - Active connections (peak): ____
   - Connection errors: ____%

2. Phase 2 (With Pool, pool_size=10, max_overflow=10):
   - Throughput: ____ req/s (Δ: ___%)
   - p95 latency: ____ ms (Δ: ____ ms, ___%)
   - Active connections (peak): ____ (Δ: ___%)
   - Connection reuse rate: ____%
   - Pool exhaustion events: ____

Performance Analysis:
- Connection acquisition time (p95): ____ ms (from pool)
  vs ____ ms (new connection in Phase 1)
- Latency reduction per request: ____ ms
- Throughput gain: ____%
- Resource efficiency: ___% fewer connections
```

---

## Future Enhancements

### Phase 3 (If Needed)
1. **PgBouncer Integration**: External pooler for multi-instance efficiency
2. **Read Replicas**: Separate pools for read vs write queries
3. **Dynamic Pool Sizing**: Auto-scale pool based on load
4. **Connection Pinning**: Sticky connections for specific tenants

### Phase 4 (If Needed)
1. **Multi-Database Support**: Separate pools per tenant (sharding)
2. **Adaptive Timeouts**: Adjust pool_timeout based on load
3. **Connection Health Monitoring**: Proactive stale connection detection

---

## References

### Implementation Files
- `infrastructure/database/pool_config.py` - Pool configuration
- `infrastructure/database/session.py` - Session factory
- `core/database.py` - Database initialization

### Documentation
- Phase 2 Week 2 Audit Report: `docs/phase2_week2_audit_report.md`
- Load Test Execution Guide: `docs/phase2_week3_load_test_execution.md`
- ADR-001: Caching Strategy
- ADR-002: Rate Limiting Policy

### External Resources
- SQLAlchemy Connection Pooling: https://docs.sqlalchemy.org/en/20/core/pooling.html
- PostgreSQL Connection Limits: https://www.postgresql.org/docs/current/runtime-config-connection.html
- PgBouncer Documentation: https://www.pgbouncer.org/

---

## Decision Review

**Review Date**: <!-- TO BE SCHEDULED AFTER 30 DAYS -->
**Review Criteria**:
- Actual pool utilization vs target (50-80%)
- Pool exhaustion rate < 0.1%
- p95 latency improvement vs baseline (> 20%)
- Zero transaction boundary issues (COMMIT/ROLLBACK correctness)

**Success Metrics**:
- [ ] Pool utilization sustained at 50-80% in production
- [ ] Pool exhaustion rate < 0.1%
- [ ] p95 latency < 200ms under peak load
- [ ] Zero semantic issues (transaction correctness preserved)
