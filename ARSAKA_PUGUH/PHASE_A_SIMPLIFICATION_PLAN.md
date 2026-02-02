# Phase A Simplification Plan — Course Correction

**Date**: 2026-01-08
**Status**: Active
**Purpose**: Refocus implementation from "comprehensive" to "minimal viable visible system"

---

## 🎯 Problem Statement

Current implementation is **TOO FAT** for Phase A goals:

❌ **Current State**:
- 119 unit tests + 6 integration test classes (Phase 2 quality assurance)
- Redis caching with 5 decorator files (premature optimization)
- Token bucket rate limiting (over-engineering for 2 users)
- Prometheus metrics + Jaeger tracing (production monitoring, not debugging)
- Connection pool size 20 (overkill for 2 concurrent users)
- 3 comprehensive ADRs (2,220 lines of architectural documentation)

✅ **Desired State (Phase A)**:
- One clean flow: Login → Create Decision → Approve → View Audit
- Minimal infrastructure (PostgreSQL + JWT only)
- Easy to debug (structured logs, simple stack traces)
- Deployable (Docker + Cloudflare)
- **NOT production-ready, NOT scalable, NOT optimized**

**Guiding Principle**:
> Phase A exists to SEE the system, not to TRUST the system.
>
> If in doubt → remove/disable, don't add.

---

## 📊 What We Built (Phase 2) vs What We Need (Phase A)

| Feature | Phase 2 Status | Phase A Need | Decision |
|---------|---------------|--------------|----------|
| **Redis Caching** | ✅ Implemented (5 files, fail-open) | ❌ Not needed (1 tenant, 2 users) | **DISABLE** |
| **Rate Limiting** | ✅ Implemented (token bucket) | ❌ Not needed (Cloudflare sufficient) | **DISABLE** |
| **Connection Pool** | ✅ Implemented (size 20) | ⚠️ Needed but oversized | **REDUCE** (size 2) |
| **Prometheus Metrics** | ✅ Implemented | ❌ Not needed (no monitoring dashboard) | **DISABLE** |
| **Jaeger Tracing** | ✅ Implemented | ❌ Not needed (no distributed system) | **DISABLE** |
| **Structured Logging** | ✅ Implemented | ✅ Needed (debugging) | **KEEP** (JSON logs) |
| **119 Unit Tests** | ✅ Implemented | ⚠️ Overkill for Phase A | **DEFER** (run in CI only) |
| **3 ADRs** | ✅ Implemented | ⚠️ Premature for Phase A | **ARCHIVE** (reference only) |

**Summary**:
- **DISABLE**: 4 features (Redis, rate limiting, metrics, tracing)
- **REDUCE**: 1 feature (connection pool: 20 → 2)
- **KEEP**: 1 feature (structured logging)
- **DEFER**: Testing + documentation (valuable for Phase 2, not Phase A deployment)

---

## 🔴 TASK 1: Disable Over-Engineered Infrastructure

### 1.1 Disable Redis Caching

**Current Implementation**:
- `infrastructure/caching/redis_client.py` (9,541 bytes)
- `infrastructure/caching/cache_decorator.py` (4,115 bytes)
- `infrastructure/caching/rule_cache_decorator.py` (10,227 bytes)
- `infrastructure/caching/idempotency_cache_decorator.py` (9,893 bytes)
- Total: ~34KB of caching code

**Why Disable**:
- Phase A load: 1 tenant, 2 users → ~2-10 requests/hour (manual testing)
- PostgreSQL query time: ~5-20ms (fast enough for manual testing)
- Redis adds: deployment complexity, monitoring overhead, debugging surface
- Fail-open behavior tested, but not needed if Redis not deployed

**How to Disable**:
```bash
# .env configuration
REDIS_ENABLED=false
REDIS_URL=  # Leave empty (fail-open will handle this)
```

**Code Changes**: NONE required (fail-open behavior already implemented)

**Effect**:
- All cache decorators fall back to PostgreSQL only
- No Redis connection attempts
- System works exactly the same (PostgreSQL is authoritative)
- Reduces moving parts (easier debugging)

**Safe Because**:
✅ Fail-open behavior tested (61 unit tests verify graceful degradation)
✅ Write-through pattern ensures PostgreSQL is authoritative
✅ Integration tests verify determinism (Redis ON = Redis OFF outcomes)
✅ No semantic changes to business logic

**When to Re-Enable**: Phase C (after > 10 tenants deployed)

---

### 1.2 Disable Backend Rate Limiting

**Current Implementation**:
- `infrastructure/security/rate_limiter.py` (11,948 bytes)
- Token bucket algorithm (100 requests/minute per tenant)
- Backend rate limiting with Redis
- Fail-open when Redis unavailable

**Why Disable**:
- Phase A load: 1 tenant, 2 users → ~2-10 requests/hour (no abuse risk)
- Cloudflare rate limiting: 30 requests/minute per IP (sufficient)
- Backend rate limiting requires Redis (which we're disabling)

**How to Disable**:
```bash
# .env configuration
RATE_LIMIT_ENABLED=false
```

**Code Changes**: NONE required (fail-open behavior already implemented)

**Effect**:
- No backend rate limiting checks
- Cloudflare + Nginx still provide protection
- Reduces latency overhead (~2-5ms per request)

**Safe Because**:
✅ Fail-open behavior tested (30+ unit tests verify graceful degradation)
✅ Cloudflare firewall rules block non-whitelisted IPs
✅ Phase A is internal-only (office IPs whitelisted)
✅ No public access (no abuse risk)

**Alternative Protection**:
- Cloudflare: 30 requests/minute per IP (already configured)
- Nginx: 10 requests/second per IP (if needed, optional)

**When to Re-Enable**: Phase C (when opening to public access)

---

### 1.3 Disable Prometheus Metrics

**Current Implementation**:
- `infrastructure/metrics/` (Prometheus client)
- Custom metrics: latency histograms, request counters, error rates
- `/metrics` endpoint for Prometheus scraping

**Why Disable**:
- Phase A has no monitoring dashboard (no Grafana/Prometheus deployment)
- Metrics collection adds overhead (~1-2ms per request)
- Phase A debugging: read logs, not monitor dashboards

**How to Disable**:
```bash
# .env configuration
ENABLE_METRICS=false
```

**Code Changes**: NONE required (conditional middleware registration)

**Effect**:
- No Prometheus metrics collected
- `/metrics` endpoint returns 404 (or disabled message)
- Reduces per-request overhead

**Safe Because**:
✅ Metrics are observability, not functionality
✅ Phase A debugging relies on logs (JSON structured logging)
✅ No monitoring dashboard deployed in Phase A

**Alternative Debugging**:
- Structured logs (JSON format) → grep/jq for analysis
- Health check endpoint (`/health`) → uptime verification
- Error logs (with stack traces) → debugging failures

**When to Re-Enable**: Phase B (when deploying Prometheus/Grafana)

---

### 1.4 Disable Jaeger Tracing

**Current Implementation**:
- `infrastructure/tracing/` (OpenTelemetry + Jaeger)
- Distributed tracing spans
- Jaeger agent integration

**Why Disable**:
- Phase A is monolithic (no distributed tracing needed)
- Jaeger not deployed (no tracing UI)
- Tracing overhead: ~5-10ms per request

**How to Disable**:
```bash
# .env configuration
ENABLE_TRACING=false
JAEGER_ENDPOINT=  # Leave empty
```

**Code Changes**: NONE required (conditional initialization)

**Effect**:
- No tracing spans created
- No Jaeger agent connection attempts
- Reduces per-request overhead

**Safe Because**:
✅ Tracing is observability, not functionality
✅ Phase A debugging relies on logs (with request context)
✅ No Jaeger deployment in Phase A

**When to Re-Enable**: Phase D (distributed system with microservices)

---

### 1.5 Reduce Connection Pool Size

**Current Implementation**:
```python
# Phase 2 configuration
POOL_SIZE=10          # Core pool
MAX_OVERFLOW=10       # Overflow pool
# Total: 20 connections per API instance
```

**Why Reduce**:
- Phase A load: 1 tenant, 2 users → peak 2-5 concurrent requests
- Pool size 20 wastes PostgreSQL resources (idle connections)
- Simpler to debug with fewer connections

**How to Reduce**:
```bash
# .env configuration
POOL_SIZE=2           # 2 core connections (admin + approver)
MAX_OVERFLOW=3        # Burst capacity up to 5 connections
POOL_TIMEOUT=10       # Fast failure (don't wait 30 seconds)
```

**Why Keep Connection Pooling**:
✅ Eliminates 10-50ms connection establishment overhead
✅ Minimal complexity (SQLAlchemy built-in)
✅ Production-ready (scales when Phase B/C add more users)

**Safe Because**:
✅ Pool size calculation: (concurrent_requests * db_time) / total_time
   - Phase A: (5 concurrent * 0.05s db) / 0.2s total = 1.25 → use 2
✅ Overflow handles burst (up to 5 connections total)
✅ Connection pooling has no semantic changes (verified in integration tests)

**When to Increase**: Phase B (based on actual concurrent user count)

---

## 🟢 TASK 2: Simplify Auth & Tenant Handling

### 2.1 Authentication: Keep JWT, Remove Complexity

**What to Keep**:
- ✅ JWT generation (HS256 algorithm)
- ✅ JWT validation (Bearer token)
- ✅ Password hashing (bcrypt)
- ✅ Login endpoint (`POST /api/v1/auth/login`)

**What to Remove/Not Implement**:
- ❌ Token refresh (no `/refresh` endpoint)
- ❌ Password reset (no "forgot password" flow)
- ❌ User registration (no `POST /users` endpoint)
- ❌ Email verification (not needed for internal demo)
- ❌ MFA (not needed for Phase A)

**Hardcoded Users** (seed data):
```sql
-- Phase A: 2 users only
INSERT INTO users (id, username, password_hash, organization_id, role) VALUES
('user-admin-001', 'admin', '$2b$12$KK.KGcUEcVCSYotdWlLOP...', '550e8400-...', 'admin'),
('user-approver-001', 'approver', '$2b$12$KK.KGcUEcVCSYotdWlLOP...', '550e8400-...', 'approver');

-- Credentials:
-- admin / admin123
-- approver / approver123
```

**Why This Is Enough**:
- Phase A is for manual testing (not end users)
- 2 users cover the flow: admin creates, approver approves
- No need for dynamic user management yet

**Safe Because**:
✅ JWT is industry standard (portable to Phase B/C)
✅ bcrypt password hashing is secure (ready for production)
✅ Hardcoded users can be replaced with database-driven users later

---

### 2.2 Authorization: Hardcode Roles, Skip RBAC

**What to Keep**:
- ✅ User role field (`admin`, `approver`)
- ✅ Basic permission check: "admin can create, approver can approve"
- ✅ Tenant ID in JWT (for future multi-tenancy)

**What to Remove/Not Implement**:
- ❌ Role matrix (no `permissions` table)
- ❌ Dynamic permission assignment (no `user_roles` table)
- ❌ Permission checks beyond user role (no `can_edit`, `can_delete`)
- ❌ Tenant switching (only 1 tenant in Phase A)

**Simplified Permission Logic**:
```python
# Phase A permission checks (simple)
def can_create_decision(user: User) -> bool:
    return user.role == "admin"

def can_approve_decision(user: User) -> bool:
    return user.role == "approver"

# No complex permission matrix needed
```

**Why This Is Enough**:
- Phase A flow: admin creates, approver approves (2 roles only)
- No need for fine-grained permissions (view, edit, delete, export)
- Production RBAC can be added later without changing core logic

**Safe Because**:
✅ Role concept is permanent (workflow semantics)
✅ Simple permission checks don't lock architecture
✅ Can add permission matrix in Phase C without breaking flow

---

### 2.3 Tenant Handling: Single Tenant, No Switching

**What to Keep**:
- ✅ Tenant ID in database models (`tenant_id` column)
- ✅ Tenant ID in JWT claims (`tenant_id` field)
- ✅ Tenant ID in API requests (for future multi-tenancy)

**What to Remove/Not Implement**:
- ❌ Tenant selection UI (no dropdown)
- ❌ Tenant switching (no `POST /switch-tenant`)
- ❌ Cross-tenant access checks (only 1 tenant exists)
- ❌ Tenant isolation verification (not needed for 1 tenant)

**Hardcoded Tenant** (seed data):
```sql
-- Phase A: 1 tenant only
INSERT INTO organizations (id, name) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'Demo Tenant Phase A');
```

**Simplified Tenant Logic**:
```python
# Phase A tenant validation (simple)
ALLOWED_TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"

def validate_tenant(tenant_id: str) -> bool:
    return tenant_id == ALLOWED_TENANT_ID

# No multi-tenant isolation logic needed
```

**Why This Is Enough**:
- Phase A is for demonstrating the flow (not multi-tenancy)
- 1 tenant simplifies testing (no tenant leak concerns)
- Multi-tenancy can be added in Phase C without changing schema

**Safe Because**:
✅ Tenant ID is already in schema (future-proof)
✅ Hardcoded validation can be replaced with database lookup later
✅ No semantic changes to decision/workflow logic

**Warning: Don't Fake Multi-Tenancy**:
❌ DON'T add tenant selection UI (not used)
❌ DON'T add tenant isolation checks (only 1 tenant)
❌ DON'T add cross-tenant access prevention (no risk with 1 tenant)

> If you only have 1 tenant, don't pretend you have multi-tenancy.
> It's better to be honestly simple than fake complex.

---

## 🟡 TASK 3: Frontend Decoupling

### 3.1 Mark API Contracts as UNSTABLE

**Problem**: Frontend is locking API response shapes too early

**Solution**: Add explicit warnings in API responses (Phase A only)

```json
{
  "_meta": {
    "api_version": "phase-a-unstable",
    "warning": "⚠️ API response shape is UNSTABLE. Do NOT rely on this structure in production code."
  },
  "data": {
    "decision_id": "dec-001",
    "outcome": "APPROVED"
  }
}
```

**Frontend Code Warning**:
```typescript
// ⚠️ WARNING: Phase A API contracts are UNSTABLE
// This response shape WILL change in Phase B/C
// Do NOT build production features on this structure

interface DecisionResponse {
  decision_id: string;    // May become UUID type
  outcome: string;        // May become enum or nested object
  created_at: string;     // May change to ISO 8601 timestamp
  // Pagination? Filtering? → Not implemented in Phase A
}
```

**Why This Matters**:
- Prevents frontend from over-engineering based on unstable API
- Makes it clear that API will evolve (not locked in stone)
- Encourages simple frontend implementation (display data, trigger actions)

---

### 3.2 Reduce Frontend Assumptions

**What Frontend Should NOT Assume**:
- ❌ Pagination (not implemented in Phase A)
- ❌ Filtering (not implemented in Phase A)
- ❌ Sorting (not implemented in Phase A)
- ❌ Enum values (outcome may change: APPROVED/REJECTED/PENDING vs APPROVE/REJECT/REVIEW)
- ❌ Field names (decision_id vs decisionId vs id)

**What Frontend SHOULD Do**:
- ✅ Display data as-is (no transformation)
- ✅ Trigger actions (create decision, approve, reject)
- ✅ Show visual feedback (success message, error message)
- ✅ Handle errors gracefully (show error, no retry logic yet)

**Simplified Frontend Components**:
```typescript
// Phase A: Simple components, no over-engineering

// ✅ GOOD: Simple list (no pagination)
function DecisionList() {
  const { data } = useQuery('/decisions');  // Fetch all
  return <ul>{data.map(d => <li>{d.decision_id}</li>)}</ul>;
}

// ❌ BAD: Over-engineered with pagination (not implemented in backend)
function DecisionListWithPagination() {
  const [page, setPage] = useState(1);
  const { data } = useQuery(`/decisions?page=${page}&limit=10`);  // Backend doesn't support this
  return <PaginatedList data={data} onPageChange={setPage} />;  // Wasted effort
}
```

**Why This Matters**:
- Frontend shouldn't design the API (backend should)
- Phase A API is unstable (will change based on usage patterns)
- Simple frontend = easier to refactor when API stabilizes

---

### 3.3 Focus Frontend on Essentials

**Phase A Frontend: Only These Screens**

1. **Login Page** (`/login`):
   - Username + password fields
   - Login button
   - Error message display
   - Redirect to dashboard on success

2. **Dashboard** (`/`):
   - User info (username, role)
   - System status (API health)
   - Navigation: Create Decision, View Decisions

3. **Create Decision** (`/decisions/create`):
   - Form: decision_type, context (JSON input)
   - Submit button
   - Success message → redirect to decision list
   - Error message display

4. **Decision List** (`/decisions`):
   - Table: decision_id, outcome, created_at
   - Actions: View, Approve (if approver)

5. **Approve Workflow** (`/decisions/:id/approve`):
   - Decision details (read-only)
   - Approve button
   - Reject button
   - Comment field (optional)
   - Success message → redirect to decision list

**What NOT to Build in Phase A**:
- ❌ Settings page (no user settings yet)
- ❌ Profile page (no profile editing)
- ❌ Admin panel (no user management)
- ❌ Analytics dashboard (no metrics)
- ❌ Audit log viewer (simple decision list is enough)
- ❌ Rule editor (rules are hardcoded in seed data)

**Why This Is Enough**:
- These 5 screens cover the entire flow: Login → Create → Approve → Audit
- No need for polished UI (Tailwind defaults are fine)
- No need for advanced features (pagination, filtering, export)

**Safe Because**:
✅ Flow is complete (can test end-to-end)
✅ Simple UI is easier to debug (fewer moving parts)
✅ Can add features in Phase B/C without breaking flow

---

## 🔵 TASK 4: CORE vs SCAFFOLD Documentation

**Created**: `CORE_VS_SCAFFOLD.md` ✅

**Purpose**: Define what's permanent (CORE) vs temporary (SCAFFOLD)

**Key Sections**:
- **CORE**: Decision model, workflow, use cases, events (NEVER change)
- **SCAFFOLD**: Auth, tenant handling, infrastructure (WILL change)
- **Testing Strategy**: CORE tests must pass (100%), SCAFFOLD tests optional
- **Phase A Checklist**: Verify login → create → approve → audit works

---

## 🟢 TASK 5: Expected Output After Simplification

### What Changes

**Files Disabled** (via configuration, not deletion):
- `infrastructure/caching/` (5 files) → Disabled via `REDIS_ENABLED=false`
- `infrastructure/security/rate_limiter.py` → Disabled via `RATE_LIMIT_ENABLED=false`
- `infrastructure/metrics/` → Disabled via `ENABLE_METRICS=false`
- `infrastructure/tracing/` → Disabled via `ENABLE_TRACING=false`

**Configuration Changes**:
```bash
# .env for Phase A (simplified)
# ========================

# Database (REQUIRED)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5433/arsaka_puguh

# Auth (MINIMAL)
JWT_SECRET_KEY=your-secret-key-here-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Tenant (HARDCODED)
ALLOWED_TENANT_IDS=550e8400-e29b-41d4-a716-446655440000

# Infrastructure (DISABLED FOR PHASE A)
REDIS_ENABLED=false
REDIS_URL=
RATE_LIMIT_ENABLED=false
ENABLE_METRICS=false
ENABLE_TRACING=false
JAEGER_ENDPOINT=

# Connection Pool (MINIMAL)
POOL_SIZE=2
MAX_OVERFLOW=3
POOL_TIMEOUT=10

# Logging (DEBUG MODE)
LOG_LEVEL=DEBUG
LOG_FORMAT=json
```

**What Stays the Same**:
- ✅ Core domain logic (33 files unchanged)
- ✅ Use cases (create decision, approve, reject)
- ✅ Database schema (all tables exist, some unused)
- ✅ API endpoints (same URLs, same request/response shapes)

**What Gets Simpler**:
- ✅ Deployment (no Redis, no Prometheus, no Jaeger)
- ✅ Debugging (structured logs only, no distributed tracing)
- ✅ Testing (run CORE tests only, skip infrastructure tests)
- ✅ Configuration (fewer environment variables)

---

### How to Verify Simplification Worked

**Test Flow** (manual):
1. **Login**: `POST /api/v1/auth/login` with `admin / admin123`
   - Expect: JWT token returned
2. **Create Decision**: `POST /api/v1/decisions` with decision data
   - Expect: Decision created, outcome returned
3. **View Decision**: `GET /api/v1/decisions/:id`
   - Expect: Decision details displayed
4. **Approve Workflow**: `POST /api/v1/workflows/:id/approve`
   - Expect: Workflow state changed to APPROVED
5. **View Audit**: `GET /api/v1/decisions`
   - Expect: Decision list with approved decision

**Expected Behavior**:
- ✅ Flow completes without errors
- ✅ No Redis connection attempts (logs show "Redis disabled")
- ✅ No rate limiting overhead (logs show "Rate limiting disabled")
- ✅ Structured logs show request flow (JSON format)
- ✅ PostgreSQL queries logged (can verify decision creation)

**Performance Expectations** (Phase A):
- Latency: 20-100ms per request (PostgreSQL only, no caching)
- Throughput: 10-50 requests/second (limited by manual testing speed)
- Database connections: 2-5 active (minimal pool size)
- Memory usage: ~50-100MB (no Redis, no metrics, no tracing)

**What NOT to Expect** (intentionally missing):
- ❌ Fast response times (no caching, acceptable for manual testing)
- ❌ Rate limiting protection (Cloudflare handles this)
- ❌ Metrics dashboard (no Prometheus/Grafana)
- ❌ Distributed tracing (no Jaeger)

---

## 📋 Checklist: Before Deploying Phase A

### Infrastructure Disabled
- [ ] `REDIS_ENABLED=false` (no Redis connection attempts)
- [ ] `RATE_LIMIT_ENABLED=false` (no backend rate limiting)
- [ ] `ENABLE_METRICS=false` (no Prometheus metrics)
- [ ] `ENABLE_TRACING=false` (no Jaeger tracing)

### Infrastructure Minimized
- [ ] `POOL_SIZE=2` (minimal connection pooling)
- [ ] `MAX_OVERFLOW=3` (burst capacity only)
- [ ] `LOG_LEVEL=DEBUG` (verbose logging for debugging)

### Core Flow Works
- [ ] Login with `admin / admin123` returns JWT
- [ ] Create decision API creates decision in database
- [ ] Approve workflow API changes workflow state
- [ ] Decision list API returns decisions
- [ ] Events table logs all actions

### Deployment Ready
- [ ] Docker container builds successfully
- [ ] PostgreSQL migrations applied
- [ ] Seed data loaded (1 tenant, 2 users, 2 rules)
- [ ] `/health` endpoint returns 200 OK
- [ ] Structured logs visible (`docker logs backend`)

---

## 🧠 Decision Rationale Summary

### What We Cut (and Why It's Safe)

| Feature | Why We Cut | Why It's Safe |
|---------|-----------|---------------|
| **Redis Caching** | 1 tenant, 2 users → no load | Fail-open tested, PostgreSQL authoritative |
| **Rate Limiting** | Cloudflare sufficient | Fail-open tested, IP whitelisted |
| **Prometheus** | No monitoring dashboard | Structured logs for debugging |
| **Jaeger** | Monolithic system | Logs with request context |
| **Pool Size 20** | Only 2-5 concurrent requests | Reduced to 2, scales later |
| **119 Tests** | Phase 2 QA, not Phase A deployment | Run in CI, not deployment blocker |
| **3 ADRs** | Premature for Phase A | Archived for Phase 2 reference |

### What We Kept (and Why)

| Feature | Why We Kept |
|---------|-------------|
| **Core Domain Logic** | Business logic is permanent (CORE) |
| **Structured Logging** | Essential for debugging (JSON format) |
| **JWT Auth** | Industry standard (portable to Phase B/C) |
| **Connection Pooling** | Eliminates latency overhead (minimal size) |
| **Tenant ID in Schema** | Future-proofs multi-tenancy (Phase C) |

---

## 🚨 What We're Intentionally Leaving "Ugly"

### 1. Hardcoded Users
**Ugly**: Users hardcoded in seed data (not database-driven)
**Why**: Phase A is for manual testing (not end users)
**When to Fix**: Phase C (when adding user management)

### 2. Hardcoded Tenant
**Ugly**: Single tenant hardcoded (no multi-tenancy)
**Why**: Phase A is for demonstrating flow (not multi-tenant)
**When to Fix**: Phase C (when deploying multiple tenants)

### 3. No Pagination
**Ugly**: Decision list fetches all records (no pagination)
**Why**: Phase A will have < 100 decisions (manual testing)
**When to Fix**: Phase B (when list grows > 100 records)

### 4. No Error Retry Logic
**Ugly**: Frontend shows error, no automatic retry
**Why**: Phase A debugging needs to see errors (not hide them)
**When to Fix**: Phase B (when adding production error handling)

### 5. No Metrics Dashboard
**Ugly**: No monitoring, rely on logs only
**Why**: Phase A is for debugging (not production monitoring)
**When to Fix**: Phase B (when deploying Prometheus/Grafana)

**Why This Is Okay**:
> "Perfect is the enemy of good" — Voltaire
>
> Phase A goal: SEE the flow work. Polish can wait until flow is validated.

---

## 📖 Final Checklist

Before submitting Phase A for deployment:

### Documentation
- [ ] `CORE_VS_SCAFFOLD.md` created (defines permanent vs temporary)
- [ ] `PHASE_A_SIMPLIFICATION_PLAN.md` created (this document)
- [ ] `PHASE_A_CONFIGURATION.md` created (next document - .env guide)

### Configuration
- [ ] `.env.phase-a` file created with minimal configuration
- [ ] All infrastructure features disabled (Redis, rate limiting, metrics, tracing)
- [ ] Connection pool size reduced (2 core, 3 overflow)
- [ ] Structured logging enabled (DEBUG level)

### Testing
- [ ] CORE tests pass (`pytest core/tests/ -v`)
- [ ] Manual flow tested (login → create → approve → audit)
- [ ] No Redis connection errors in logs
- [ ] No rate limiting errors in logs

### Deployment
- [ ] Docker container builds
- [ ] PostgreSQL migrations applied
- [ ] Seed data loaded
- [ ] Health check passes

---

## 🎯 Success Criteria (Phase A)

**Phase A is successful if**:
1. ✅ Login works (admin + approver)
2. ✅ Create decision works (admin creates decision)
3. ✅ Approve workflow works (approver approves decision)
4. ✅ Decision list works (shows created + approved decisions)
5. ✅ Audit trail works (events table logs all actions)
6. ✅ System is debuggable (structured logs show flow)
7. ✅ Deployment is simple (Docker + PostgreSQL only)

**Phase A is NOT successful if**:
- ❌ Redis is required (should be disabled)
- ❌ Metrics dashboard is required (should be disabled)
- ❌ Advanced features are needed (pagination, filtering, etc.)
- ❌ System is production-ready (it's not supposed to be)

**Remember**: Phase A exists to SEE the system, not to TRUST the system.

---

**Document Version**: 1.0
**Last Updated**: 2026-01-08
**Status**: Active (Phase A Refocus)
**Next**: Create `PHASE_A_CONFIGURATION.md` (environment variable guide)
