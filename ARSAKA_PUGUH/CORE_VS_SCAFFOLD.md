# CORE vs SCAFFOLD — ARSAKA_PUGUH Architecture

**Purpose**: Define what's permanent (CORE) vs temporary (SCAFFOLD) to enable safe refactoring without trauma.

**Philosophy**: Phase A exists to SEE the system, not to TRUST the system.

---

## 🟢 CORE (PERMANENT — DO NOT TOUCH)

These components represent the fundamental business logic and must remain immutable across all phases.

### 1. Domain Model (`core/domain/`)

**Files**:
- `aggregates.py` - Decision aggregate, Workflow state machine
- `events.py` - Domain events (DecisionCreated, WorkflowApproved, etc.)
- `value_objects.py` - Immutable value objects (Decision context, Outcome)

**Why CORE**:
- Represents business invariants
- Workflow state machine is the heart of the system
- Decision immutability is architectural constraint
- Event semantics drive audit trail

**Immutability Rules**:
- ✅ Decision data is immutable after creation
- ✅ Workflow state transitions are explicit (PENDING → APPROVED/REJECTED)
- ✅ Events are append-only (never modified or deleted)
- ✅ Outcome derivation is deterministic (same input = same output)

**Test Coverage**: `core/tests/test_domain.py` verifies these invariants MUST NOT break.

---

### 2. Use Cases (`core/use_cases/`)

**Files**:
- `create_decision.py` - Create decision with idempotency
- `approve_workflow.py` - Approve decision workflow
- `reject_workflow.py` - Reject decision workflow
- `delegate_workflow.py` - Delegate to another user
- `escalate_workflow.py` - Escalate to higher authority
- `dtos.py` - Data Transfer Objects
- `exceptions.py` - Business exceptions
- `interfaces.py` - Repository interfaces

**Why CORE**:
- Encapsulates business logic (decision creation, approval, rejection)
- Enforces workflow state transitions
- Handles idempotency (critical for reliability)
- Defines clear boundaries (ports in hexagonal architecture)

**Immutability Rules**:
- ✅ Use case outcomes are deterministic
- ✅ Idempotency keys prevent duplicate decisions
- ✅ Workflow state changes are atomic (no partial updates)
- ✅ Business exceptions bubble up (no swallowing errors)

**Test Coverage**: `core/tests/test_use_cases.py` verifies business logic correctness.

---

### 3. Repository Interfaces (`core/use_cases/interfaces.py`)

**Interfaces**:
```python
class IDecisionRepository(Protocol):
    async def save(self, decision: Decision) -> None
    async def find_by_id(self, decision_id: str) -> Optional[Decision]

class IRuleRepository(Protocol):
    async def find_active_rules(self, tenant_id: str, decision_type: str) -> list[Rule]

class IWorkflowRepository(Protocol):
    async def save(self, workflow: Workflow) -> None
    async def find_by_decision_id(self, decision_id: str) -> Optional[Workflow]

class IIdempotencyRepository(Protocol):
    async def check_and_reserve(self, key: str) -> bool
```

**Why CORE**:
- Defines contracts between use cases and infrastructure
- Enables testability (mock implementations)
- Allows infrastructure to evolve independently
- Hexagonal architecture boundary

**Immutability Rules**:
- ✅ Interface methods MUST NOT change signatures
- ✅ Repositories MUST return domain objects (not database models)
- ✅ Repositories MUST handle transaction boundaries
- ✅ Repositories MUST NOT leak infrastructure details

---

### 4. Event Semantics

**Event Types**:
- `DecisionCreated` - New decision created
- `WorkflowApproved` - Decision approved
- `WorkflowRejected` - Decision rejected
- `WorkflowDelegated` - Decision delegated to another user
- `WorkflowEscalated` - Decision escalated to higher authority

**Why CORE**:
- Events are the source of truth for audit trail
- Event structure defines what happened, when, and why
- Cannot be changed without breaking audit integrity

**Immutability Rules**:
- ✅ Events are append-only (never updated or deleted)
- ✅ Event schema is versioned (backward compatible changes only)
- ✅ Event metadata includes: timestamp, actor, reason
- ✅ Events drive projections (decision list, audit log)

---

## 🔵 SCAFFOLD (PHASE A ONLY — TEMPORARY, CAN BE REPLACED)

These components are minimal implementations to make Phase A visible and debuggable. They will be replaced or significantly refactored in later phases.

### 1. Authentication (`shared/auth.py` - if exists)

**Current Implementation** (Phase A):
- Basic JWT generation and validation
- Hardcoded 2 users: `admin` (password: `admin123`), `approver` (password: `approver123`)
- Hardcoded 1 tenant: `550e8400-e29b-41d4-a716-446655440000`
- No token refresh, no password reset, no user registration

**Why SCAFFOLD**:
- Phase A needs login to test the flow, not secure authentication
- Production will require: OAuth2, SAML, MFA, password policies
- User management will be dynamic (database-driven)

**Safe to Change**:
- ❌ JWT algorithm (HS256 is fine for Phase A)
- ❌ User model structure (will change when RBAC is implemented)
- ❌ Password hashing (bcrypt placeholder)
- ❌ Session management (stateless JWT for now)

**What to Keep**:
- ✅ JWT token format (for frontend compatibility during Phase A)
- ✅ Bearer token authentication (industry standard)

**Replacement Timeline**: Phase B-C (authentication hardening)

---

### 2. Authorization (Hardcoded RBAC)

**Current Implementation** (Phase A):
- Hardcoded roles: `admin` (can create decisions), `approver` (can approve)
- No role matrix, no permission checks beyond user role
- Tenant isolation is hardcoded (single tenant only)

**Why SCAFFOLD**:
- Phase A needs to show approval flow, not enforce complex RBAC
- Production will require: dynamic roles, permission matrix, tenant isolation
- Role assignment will be configurable (not hardcoded)

**Safe to Change**:
- ❌ Role definitions (will become database-driven)
- ❌ Permission checks (will use permission matrix)
- ❌ Tenant isolation (will use Row-Level Security + application checks)

**What to Keep**:
- ✅ Concept of "creator" and "approver" (workflow semantics)
- ✅ Tenant ID in requests (for future multi-tenancy)

**Replacement Timeline**: Phase C (multi-tenant RBAC)

---

### 3. Infrastructure - Caching (`infrastructure/caching/`)

**Current Implementation** (Phase 2):
- Redis client with fail-open behavior
- Cache decorators for rules, idempotency
- Write-through pattern (PostgreSQL first, Redis second)
- TTL: 10 minutes for rules, 1 hour for static data

**Why SCAFFOLD FOR PHASE A**:
- Phase A has 1 tenant, 2 users → caching provides ZERO value
- Redis adds operational complexity (deploy, monitor, troubleshoot)
- PostgreSQL is fast enough for Phase A load (< 10 requests/second)

**DISABLE FOR PHASE A**:
```bash
# Phase A configuration
REDIS_ENABLED=false  # ← CRITICAL: Disable Redis entirely
```

**Effect**:
- All cache decorators fall back to PostgreSQL only
- No Redis connection attempts
- Fail-open behavior ensures system works without Redis
- Reduces moving parts (easier to debug)

**When to Re-Enable**: Phase C (after multi-tenant deployment with > 100 tenants)

**Rationale**:
> "Premature optimization is the root of all evil" — Donald Knuth
>
> Phase A goal: SEE the flow work. Caching optimization can wait until we have real load.

---

### 4. Infrastructure - Rate Limiting (`infrastructure/security/rate_limiter.py`)

**Current Implementation** (Phase 2):
- Token bucket algorithm (100 requests/minute per tenant)
- Backend rate limiting with Redis
- Fail-open when Redis unavailable

**Why SCAFFOLD FOR PHASE A**:
- Phase A has 1 tenant, 2 users → rate limiting is overkill
- Cloudflare already provides rate limiting (30 requests/minute per IP)
- Backend rate limiting adds complexity without value

**DISABLE FOR PHASE A**:
```bash
# Phase A configuration
RATE_LIMIT_ENABLED=false  # ← CRITICAL: Disable backend rate limiting
```

**Alternative Protection**:
- Cloudflare firewall rules: 30 requests/minute per IP
- Nginx rate limiting: 10 requests/second per IP (if needed)
- No backend rate limiting needed for Phase A

**When to Re-Enable**: Phase C (multi-tenant production with public access)

**Rationale**:
> Phase A is IP-whitelisted (only office IPs). No risk of abuse.
> Cloudflare + Nginx provide sufficient protection for Phase A.

---

### 5. Infrastructure - Connection Pooling (`infrastructure/database/pool_config.py`)

**Current Implementation** (Phase 2):
- SQLAlchemy AsyncEngine with QueuePool
- Pool size: 10 (core) + 10 (overflow) = 20 max connections
- Connection reuse, pre-ping validation

**Why SIMPLIFIED FOR PHASE A**:
- Phase A has 1 tenant, 2 users → peak load is ~2-5 concurrent requests
- Pool size of 20 is overkill (wastes PostgreSQL resources)
- Simpler configuration reduces troubleshooting surface

**SIMPLIFY FOR PHASE A**:
```python
# Phase A configuration
POOL_SIZE=2          # 2 connections (1 admin + 1 approver)
MAX_OVERFLOW=3       # Burst capacity up to 5 connections
POOL_TIMEOUT=10      # Fast failure (don't wait 30 seconds)
```

**Why Keep Connection Pooling**:
- Eliminates 10-50ms connection establishment overhead
- Minimal complexity (SQLAlchemy built-in)
- Production-ready (scales when Phase B/C add more users)

**What to Skip**:
- ❌ PgBouncer (external connection pooler - not needed for Phase A)
- ❌ Advanced tuning (pool recycle, overflow tracking)
- ❌ Load testing (defer to production validation)

**Rationale**:
> Connection pooling with MINIMAL pool size (2-5) is the sweet spot for Phase A.
> Removes overhead without adding complexity.

---

### 6. Infrastructure - Observability

**Current Implementation** (Phase 2):
- Structured logging (JSON format)
- Prometheus metrics (latency, throughput, error rate)
- OpenTelemetry tracing (Jaeger integration)

**Why SIMPLIFIED FOR PHASE A**:
- Phase A is for debugging, not production monitoring
- Structured logging is useful (keep JSON format for easy grep)
- Prometheus + Jaeger are overkill (no distributed tracing needed)

**SIMPLIFY FOR PHASE A**:
```bash
# Phase A configuration
LOG_LEVEL=DEBUG              # Verbose logging for debugging
ENABLE_METRICS=false         # Disable Prometheus (not needed)
ENABLE_TRACING=false         # Disable Jaeger (not needed)
```

**What to Keep**:
- ✅ Structured logging (JSON format with request context)
- ✅ Log levels (DEBUG for development, INFO for staging)
- ✅ Exception logging (with stack traces)

**What to Disable**:
- ❌ Prometheus metrics (no monitoring dashboard needed)
- ❌ Jaeger tracing (no distributed tracing needed)
- ❌ Custom metrics (latency histograms, counters)

**Rationale**:
> Phase A debugging: grep logs, read stack traces.
> Prometheus/Jaeger are for production scale, not Phase A debugging.

---

### 7. Frontend (`frontend/` - if exists)

**Current Implementation** (Phase A):
- React + TypeScript + Vite
- Minimal UI: Login, Create Decision, Approve Workflow, Decision List
- Hardcoded API base URL (http://localhost:8001 or VPS IP)

**Why SCAFFOLD**:
- Phase A UI is for manual testing, not end users
- Production UI will have: proper design system, validation, error handling
- API contracts are unstable (response shapes may change)

**Mark as UNSTABLE**:
```typescript
// ⚠️ WARNING: API response shape is UNSTABLE (Phase A)
// This WILL change in Phase B/C. Do NOT rely on this structure.

interface DecisionResponse {
  decision_id: string;
  outcome: string;  // ← May change to enum or nested object
  created_at: string;  // ← May change to ISO 8601 format
  // Pagination? Filtering? Sorting? → Not implemented in Phase A
}
```

**What to Keep Simple**:
- ❌ Form validation (basic only, defer complex rules)
- ❌ Error handling (show error message, no retry logic)
- ❌ Loading states (simple spinner, no skeleton screens)
- ❌ Pagination (fetch all, no infinite scroll)
- ❌ Design system (plain Tailwind, no custom components)

**Rationale**:
> Phase A frontend: display data, trigger actions, show results.
> Polished UI can wait until API contracts stabilize.

---

### 8. Database Schema

**Current Implementation**:
- PostgreSQL with 29 tables (signage project schema)
- Used tables for Phase A:
  - `users` - 2 hardcoded users (admin, approver)
  - `organizations` - 1 hardcoded tenant
  - `decisions` - Decision records
  - `workflows` - Workflow state
  - `events` - Audit trail
  - `rules` - Decision rules (2-3 test rules)
  - `idempotency_keys` - Duplicate prevention

**Why SIMPLIFIED FOR PHASE A**:
- Only 7 tables actively used (other 22 tables are from signage project)
- Phase A doesn't need: devices, playlists, content management

**What to Keep**:
- ✅ Core tables: decisions, workflows, events, rules
- ✅ Idempotency table (prevents duplicate decisions)
- ✅ Users + organizations (minimal auth/tenant)

**What to Ignore**:
- ❌ Signage-specific tables (devices, playlists, content, schedules)
- ❌ Advanced features (notifications, analytics, webhooks)

**Seed Data** (Phase A):
```sql
-- 1 tenant
INSERT INTO organizations (id, name) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'Demo Tenant Phase A');

-- 2 users
INSERT INTO users (id, username, password_hash, organization_id, role) VALUES
('user-admin-001', 'admin', '<bcrypt_hash>', '550e8400-...', 'admin'),
('user-approver-001', 'approver', '<bcrypt_hash>', '550e8400-...', 'approver');

-- 2 test rules
INSERT INTO rules (tenant_id, rule_name, decision_type, conditions, action) VALUES
('550e8400-...', 'Auto Approve Small', 'purchase_approval', '{"amount": {"$lt": 1000}}', 'APPROVE'),
('550e8400-...', 'Auto Reject Large', 'purchase_approval', '{"amount": {"$gt": 10000}}', 'REJECT');
```

**Rationale**:
> Phase A uses minimal schema subset. Other tables exist but are ignored (no harm, no foul).

---

## 🔴 EXPLICITLY DISABLED FOR PHASE A

These features are implemented in Phase 2 but MUST be disabled for Phase A to keep the system simple and debuggable.

### Disabled Features Checklist

```bash
# Phase A .env configuration

# ❌ DISABLED: Redis caching
REDIS_ENABLED=false

# ❌ DISABLED: Backend rate limiting
RATE_LIMIT_ENABLED=false

# ❌ DISABLED: Prometheus metrics
ENABLE_METRICS=false

# ❌ DISABLED: Jaeger tracing
ENABLE_TRACING=false

# ✅ ENABLED: Minimal connection pooling
POOL_SIZE=2
MAX_OVERFLOW=3

# ✅ ENABLED: Debug logging
LOG_LEVEL=DEBUG

# ✅ ENABLED: Single tenant
ALLOWED_TENANT_IDS=550e8400-e29b-41d4-a716-446655440000
```

---

## 🧪 TESTING STRATEGY

### CORE Tests (MUST PASS ALWAYS)

**Domain Tests** (`core/tests/test_domain.py`):
- Decision immutability
- Workflow state transitions
- Event append-only
- Value object validation

**Use Case Tests** (`core/tests/test_use_cases.py`):
- Create decision with idempotency
- Approve workflow (state change verification)
- Reject workflow (state change verification)
- Business exception handling

**Integration Tests** (`core/tests/test_integration.py`):
- End-to-end flow: Create → Approve → Audit
- Determinism: Same input → Same output
- Transaction boundaries: COMMIT/ROLLBACK correctness

**Test Coverage Target**: 100% for CORE (domain + use cases)

---

### SCAFFOLD Tests (PHASE A ONLY)

**Infrastructure Tests** (`infrastructure/tests/`):
- Redis fail-open behavior (verifies graceful degradation)
- Rate limiter fail-open (verifies availability during failures)
- Connection pool health checks

**Purpose**: Verify Phase 2 infrastructure works when enabled, but NOT required for Phase A.

**Test Execution for Phase A**:
```bash
# Only run CORE tests for Phase A
pytest core/tests/ -v

# Skip infrastructure tests (not enabled in Phase A)
# pytest infrastructure/tests/  ← Skip this
```

**Rationale**:
> Phase A: Test business logic (CORE) only.
> Infrastructure tests are for Phase 2 validation, not Phase A deployment.

---

## 📋 PHASE A CHECKLIST

Before deploying Phase A, verify:

### CORE (Must Work)
- [ ] Login with hardcoded users (admin / approver)
- [ ] Create decision API works
- [ ] Approve workflow API works
- [ ] Reject workflow API works
- [ ] Decision list API returns results
- [ ] Events are logged in `events` table
- [ ] Idempotency prevents duplicate decisions

### SCAFFOLD (Disabled or Minimal)
- [ ] Redis caching DISABLED (`REDIS_ENABLED=false`)
- [ ] Backend rate limiting DISABLED (`RATE_LIMIT_ENABLED=false`)
- [ ] Prometheus metrics DISABLED (`ENABLE_METRICS=false`)
- [ ] Jaeger tracing DISABLED (`ENABLE_TRACING=false`)
- [ ] Connection pool MINIMAL (`POOL_SIZE=2, MAX_OVERFLOW=3`)
- [ ] Structured logging ENABLED (`LOG_LEVEL=DEBUG`)

### Deployment
- [ ] Docker container builds successfully
- [ ] PostgreSQL migrations applied
- [ ] Seed data loaded (1 tenant, 2 users, 2 rules)
- [ ] `/health` endpoint returns 200 OK
- [ ] Cloudflare IP whitelisting configured
- [ ] VPS accessible via HTTPS (admin.zhmhotels.online)

---

## 🔄 TRANSITION PLAN (SCAFFOLD → PERMANENT)

### Phase B (Deployed But Not Trusted)
- Enable Prometheus metrics for basic observability
- Keep Redis and rate limiting disabled (Cloudflare sufficient)
- Add basic monitoring (uptime, error rate)

### Phase C (Controlled Multi-Tenant)
- Enable Redis caching (when > 10 tenants)
- Enable backend rate limiting (when public access required)
- Implement dynamic user management (replace hardcoded users)
- Implement RBAC (replace hardcoded roles)

### Phase D (Hardening)
- Enable Jaeger tracing (distributed system debugging)
- Increase connection pool size (based on load testing)
- Add advanced features (password reset, MFA, audit export)

---

## 🚨 WARNING SIGNS (PHASE A DRIFT)

If you see these, you're over-engineering Phase A:

❌ "Let's add user registration for Phase A" → NO. Hardcoded users are fine.
❌ "Let's add pagination for Phase A" → NO. Fetch all decisions (< 100 for Phase A).
❌ "Let's add filtering/sorting for Phase A" → NO. Simple list is fine.
❌ "Let's add email notifications for Phase A" → NO. Manual testing doesn't need email.
❌ "Let's add API versioning for Phase A" → NO. API is unstable, versioning premature.
❌ "Let's add rate limiting for Phase A" → NO. Cloudflare already provides this.
❌ "Let's add caching for Phase A" → NO. PostgreSQL is fast enough (< 10 req/s load).

**Remember**: Phase A exists to SEE the system, not to TRUST the system.

**Guiding Principle**:
> If it doesn't help you DEBUG the core flow (Login → Create → Approve → Audit), it's not needed for Phase A.

---

## 📖 SUMMARY

| Component | Type | Phase A Status | Rationale |
|-----------|------|----------------|-----------|
| **Decision Model** | CORE | ✅ Active | Business logic (immutable) |
| **Workflow State Machine** | CORE | ✅ Active | Business logic (immutable) |
| **Use Cases** | CORE | ✅ Active | Business logic (immutable) |
| **Events** | CORE | ✅ Active | Audit trail (immutable) |
| **Repository Interfaces** | CORE | ✅ Active | Hexagonal boundary |
| **JWT Auth** | SCAFFOLD | ✅ Minimal | Hardcoded users |
| **RBAC** | SCAFFOLD | ✅ Minimal | Hardcoded roles |
| **Redis Caching** | SCAFFOLD | ❌ Disabled | No value for 1 tenant |
| **Rate Limiting** | SCAFFOLD | ❌ Disabled | Cloudflare sufficient |
| **Prometheus** | SCAFFOLD | ❌ Disabled | No monitoring needed |
| **Jaeger** | SCAFFOLD | ❌ Disabled | No tracing needed |
| **Connection Pool** | SCAFFOLD | ✅ Minimal | Pool size = 2 |
| **Frontend** | SCAFFOLD | ✅ Minimal | Unstable API contracts |

**Phase A Philosophy**:
- CORE = Permanent, immutable, well-tested
- SCAFFOLD = Temporary, replaceable, intentionally simple

**Next Steps**:
1. Review this document with team
2. Create Phase A `.env` configuration (disable SCAFFOLD features)
3. Deploy Phase A to staging
4. Manual testing: Login → Create → Approve → Audit
5. Verify flow works end-to-end
6. Proceed to Phase B (deployment with monitoring)

---

**Document Version**: 1.0
**Last Updated**: 2026-01-08
**Status**: Active (Phase A Reference)
