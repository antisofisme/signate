# PUGUH-MANTRA Integration Analysis

## Strategic Vision

> **Konsep Utama**: PUGUH sebagai Infrastructure Platform yang menyediakan core services (Auth, Multi-tenancy, Billing, Audit) untuk dikonsumsi oleh MANTRA. Keduanya bisa di-subscribe secara independen, namun MANTRA mendapat nilai tambah dengan menggunakan infrastruktur PUGUH.

---

## 1. Pemahaman Konsep

### 1.1 Apa yang User Inginkan

```
┌─────────────────────────────────────────────────────────────────┐
│                        SUBSCRIBER A                              │
│                    (Hanya pakai PUGUH)                          │
│         ┌───────────────────────────────────┐                   │
│         │           ARSAKA_PUGUH             │                   │
│         │   - Decision Engine Standalone    │                   │
│         │   - Workflow Approval             │                   │
│         │   - Rule Management               │                   │
│         └───────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        SUBSCRIBER B                              │
│                 (Pakai MANTRA + PUGUH)                          │
│                                                                  │
│         ┌───────────────────────────────────┐                   │
│         │          ARSAKA_MANTRA             │                   │
│         │   - Constitutional Law System     │                   │
│         │   - Decision Recording            │                   │
│         │   - Application Documentation     │                   │
│         └───────────────┬───────────────────┘                   │
│                         │ uses                                   │
│                         ▼                                        │
│         ┌───────────────────────────────────┐                   │
│         │     ARSAKA_PUGUH (Infrastructure)  │                   │
│         │   - Authentication                │                   │
│         │   - Multi-tenancy                 │                   │
│         │   - Billing & Subscription        │                   │
│         │   - Audit Trail                   │                   │
│         └───────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Manfaat Strategi Ini

| Aspek | Manfaat |
|-------|---------|
| **Untuk PUGUH** | MANTRA menjadi "dogfooding" - use case nyata yang memaksa PUGUH mature |
| **Untuk MANTRA** | Tidak perlu bangun auth/tenant/billing dari nol - fokus ke core value |
| **Untuk Developer** | Develop 2 produk sekaligus, saling memperkuat |
| **Untuk Business** | 2 revenue stream: PUGUH standalone + MANTRA bundle |

---

## 2. Current State Analysis

### 2.1 ARSAKA_PUGUH - Infrastructure Platform

**Status: ~35% Production Ready** (per Jan 2026 review)

#### Apa yang Sudah Ada:

| Service | Completeness | Notes |
|---------|--------------|-------|
| Auth Module | 70% | JWT, email/password, OAuth scaffold |
| Tenant Module | 80% | Organization, membership, invitations |
| Billing Module | 60% | Midtrans integration, plans defined |
| Decision Engine | 75% | Rule evaluation, workflow, caching |
| Audit Module | 50% | Event sourcing, append-only log |

#### Critical Gaps (Blocking Production):

```
❌ SECURITY VULNERABILITIES
   - No API authentication middleware (all endpoints public!)
   - Hardcoded database password in source code
   - No RBAC enforcement on endpoints
   - Stack traces exposed in errors

❌ DEPLOYMENT
   - No Docker configuration
   - No CI/CD pipeline
   - No health check endpoints
   - Dual app files (app.py vs app_v2.py)

❌ TESTING
   - Repository layer: 0% tested
   - Domain layer: 80% tested
   - Integration tests: missing
```

#### Database Schema (Well-Designed):

```sql
-- Core tenant model
tenants (
    tenant_id UUID PRIMARY KEY,
    name, slug,
    owner_user_id UUID,
    plan ENUM(FREE, STARTER, PRO, ENTERPRISE),
    status ENUM(ACTIVE, SUSPENDED, TRIAL),
    settings JSONB
)

-- User identity
users (
    user_id UUID PRIMARY KEY,
    email VARCHAR UNIQUE,
    password_hash VARCHAR,
    email_verified BOOLEAN,
    oauth_provider, oauth_id
)

-- Membership with roles
memberships (
    membership_id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants,
    user_id UUID REFERENCES users,
    role ENUM(OWNER, ADMIN, MEMBER, VIEWER)
)
```

### 2.2 ARSAKA_MANTRA - Constitutional Law System

**Status: Functional but Single-Tenant**

#### Apa yang Sudah Ada:

| Feature | Status | Notes |
|---------|--------|-------|
| Decision CRUD | ✅ Complete | Full lifecycle management |
| Validation (47 rules) | ✅ Complete | 3-level validation |
| Semantic Search | ✅ Complete | Qdrant + embeddings |
| AI Assistant | ✅ Complete | Chat, hints, arbitration |
| MCP Integration | ✅ Complete | Both Python & TypeScript |
| Caching | ✅ Complete | Redis integration |
| Message Queue | ✅ Complete | RabbitMQ + workers |

#### Critical Gaps (For SaaS):

```
❌ NO MULTI-TENANCY
   - Zero tenant_id in any table
   - All data visible to all requests
   - No organization isolation

❌ NO USER MANAGEMENT
   - No users table
   - No authentication flow
   - created_by is just VARCHAR string

❌ NO BILLING
   - No subscription model
   - No usage metering
   - No plan limits

❌ IDENTITY MODEL IS STRING-BASED
   - created_by VARCHAR(200) -- "john" or any string
   - approved_by VARCHAR(200)
   - actor VARCHAR(200)
   - Cannot audit real users
```

#### Current Schema (Missing Tenant/User):

```sql
-- Current MANTRA schema
decisions (
    decision_id UUID PRIMARY KEY,
    decision_code VARCHAR,
    domain_id VARCHAR,
    aspect_id VARCHAR,
    statement TEXT,
    rationale TEXT,
    -- ❌ NO tenant_id
    -- ❌ NO user_id
    created_by VARCHAR(200),  -- String, not UUID
    stored_by VARCHAR(200)
)
```

---

## 3. Gap Analysis: What's Missing

### 3.1 MANTRA Needs from PUGUH

| Need | PUGUH Has? | Integration Effort |
|------|------------|-------------------|
| User Authentication | ✅ Yes (JWT) | Add middleware |
| Multi-Tenancy | ✅ Yes (tenant model) | Add FK + scope queries |
| RBAC | ⚠️ Partial (roles exist) | Complete middleware |
| Billing/Subscription | ✅ Yes (Midtrans) | Connect subscription checks |
| Audit with User Identity | ✅ Yes (event log) | Replace string actor |
| Invitation System | ✅ Yes | Expose API |

### 3.2 PUGUH Needs Before Integration

| Gap | Priority | Effort |
|-----|----------|--------|
| Add auth middleware to all endpoints | 🔴 Critical | 1-2 days |
| Remove hardcoded credentials | 🔴 Critical | 1 hour |
| Add health check endpoints | 🔴 Critical | 2 hours |
| Create Docker configuration | 🔴 Critical | 1 day |
| Fix dual app.py issue | 🟡 High | 2 hours |
| Add repository tests | 🟡 High | 3-5 days |
| Complete RBAC middleware | 🟡 High | 2-3 days |

### 3.3 Integration Points Needed

```
┌──────────────────────────────────────────────────────────────┐
│                    SHARED DATABASE                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    Core Tables                           │ │
│  │  users, tenants, memberships, subscriptions, invoices   │ │
│  │  (Owned by PUGUH, consumed by MANTRA)                   │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   MANTRA Tables                          │ │
│  │  decisions, api_keys, decision_events, embeddings       │ │
│  │  (Add tenant_id FK, user_id FK)                         │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                   PUGUH Tables                           │ │
│  │  rules, workflows, decision_log (PUGUH's decisions)     │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Proposed Architecture

### 4.1 Service Topology

```
                         ┌─────────────────────┐
                         │   Load Balancer     │
                         │   (Traefik/Nginx)   │
                         └──────────┬──────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────────┐       ┌─────────────────┐
│ PUGUH Frontend│         │  MANTRA Frontend  │       │   PUGUH API     │
│  (Optional)   │         │    (React/Vite)   │       │ (Auth Endpoints)│
│  Port: 3000   │         │    Port: 3001     │       │   Port: 8000    │
└───────────────┘         └────────┬──────────┘       └────────┬────────┘
                                   │                           │
                                   │ API calls                 │ Auth validation
                                   ▼                           │
                          ┌────────────────────┐               │
                          │   MANTRA Backend   │◄──────────────┘
                          │    (FastAPI)       │
                          │    Port: 8002      │
                          │                    │
                          │ - JWT validation   │
                          │ - Tenant scoping   │
                          │ - Decision CRUD    │
                          └─────────┬──────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────────┐       ┌─────────────────┐
│  PostgreSQL   │         │      Redis        │       │     Qdrant      │
│ (Shared DB)   │         │   (Caching)       │       │  (Embeddings)   │
│  Port: 5434   │         │   Port: 6380      │       │   Port: 6335    │
└───────────────┘         └───────────────────┘       └─────────────────┘
```

### 4.2 Authentication Flow

```
┌─────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User   │     │   MANTRA     │     │    PUGUH     │     │  Shared DB   │
│ Browser │     │   Frontend   │     │   Auth API   │     │ (users table)│
└────┬────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
     │                 │                    │                    │
     │ 1. Login        │                    │                    │
     │─────────────────>                    │                    │
     │                 │                    │                    │
     │                 │ 2. POST /auth/login│                    │
     │                 │───────────────────>│                    │
     │                 │                    │                    │
     │                 │                    │ 3. Verify user     │
     │                 │                    │───────────────────>│
     │                 │                    │                    │
     │                 │                    │<───────────────────│
     │                 │                    │    User + Memberships
     │                 │                    │                    │
     │                 │ 4. JWT Token       │                    │
     │                 │   (contains:       │                    │
     │                 │    user_id,        │                    │
     │                 │    tenant_id,      │                    │
     │                 │    role)           │                    │
     │                 │<───────────────────│                    │
     │                 │                    │                    │
     │ 5. Store token  │                    │                    │
     │<─────────────────                    │                    │
     │                 │                    │                    │
     │ 6. API Request  │                    │                    │
     │   (with JWT)    │                    │                    │
     │─────────────────>                    │                    │
     │                 │                    │                    │
     │                 │ 7. Call MANTRA API │                    │
     │                 │   (JWT in header)  │                    │
     │                 │────────────────────────────────────────>│
     │                 │                    │                    │
```

### 4.3 Multi-Tenancy Enforcement

```python
# MANTRA Backend - Middleware Pattern

from fastapi import Depends, HTTPException
from jose import jwt

async def get_current_tenant(token: str = Depends(oauth2_scheme)):
    """
    Extract and validate tenant context from JWT.
    All MANTRA endpoints will use this dependency.
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    tenant_id = payload.get("tenant_id")
    user_id = payload.get("user_id")
    role = payload.get("role")

    if not tenant_id:
        raise HTTPException(401, "Tenant context required")

    return TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        role=role
    )

# Repository scoping
class PostgresDecisionRepository:
    async def find_all_async(
        self,
        tenant_id: UUID,  # ← Required parameter
        limit: int = 100
    ) -> List[StoredDecision]:
        query = """
            SELECT * FROM decisions
            WHERE tenant_id = $1  -- ← Tenant isolation
            AND is_deleted = FALSE
            ORDER BY created_at DESC
            LIMIT $2
        """
        return await self.pool.fetch(query, tenant_id, limit)
```

---

## 5. Database Migration Strategy

### 5.1 MANTRA Schema Changes

```sql
-- Migration: Add multi-tenancy support

-- Step 1: Add tenant_id and user_id columns
ALTER TABLE decisions
    ADD COLUMN tenant_id UUID,
    ADD COLUMN created_by_user_id UUID,
    ADD COLUMN approved_by_user_id UUID;

ALTER TABLE api_keys
    ADD COLUMN tenant_id UUID,
    ADD COLUMN created_by_user_id UUID;

ALTER TABLE decision_events
    ADD COLUMN tenant_id UUID,
    ADD COLUMN actor_user_id UUID;

-- Step 2: Create shared tables (or reference PUGUH's)
-- Option A: Shared database
-- PUGUH owns users, tenants, memberships tables
-- MANTRA adds FKs to those tables

-- Option B: Separate databases with cross-reference
-- MANTRA stores user_id/tenant_id but doesn't FK
-- Validates via API call to PUGUH

-- Step 3: Add foreign keys (Option A)
ALTER TABLE decisions
    ADD CONSTRAINT fk_decisions_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id);

ALTER TABLE decisions
    ADD CONSTRAINT fk_decisions_created_by
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id);

-- Step 4: Add indexes for tenant queries
CREATE INDEX idx_decisions_tenant ON decisions(tenant_id);
CREATE INDEX idx_decisions_tenant_created ON decisions(tenant_id, created_at DESC);

-- Step 5: Migrate existing data
-- Assign all existing decisions to a "default" tenant
UPDATE decisions SET tenant_id = 'default-tenant-uuid-here';
UPDATE decisions SET created_by_user_id = 'default-user-uuid-here';

-- Step 6: Make tenant_id NOT NULL
ALTER TABLE decisions ALTER COLUMN tenant_id SET NOT NULL;
```

### 5.2 API Key Migration

```sql
-- Current: created_by is string
-- Target: created_by_user_id is UUID FK

-- Migration steps:
-- 1. Add new column
ALTER TABLE api_keys ADD COLUMN created_by_user_id UUID;

-- 2. Map existing strings to users (manual or script)
-- UPDATE api_keys SET created_by_user_id = (
--     SELECT user_id FROM users WHERE email = api_keys.created_by
-- );

-- 3. Add tenant_id
ALTER TABLE api_keys ADD COLUMN tenant_id UUID;

-- 4. Add constraints
ALTER TABLE api_keys
    ADD CONSTRAINT fk_api_keys_tenant
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id);
```

---

## 6. Implementation Roadmap

### Phase 0: PUGUH Production-Ready (2 weeks)

**Goal**: Fix critical security and deployment gaps in PUGUH

```
Week 1:
├── Day 1-2: Add auth middleware to all API endpoints
├── Day 3: Remove hardcoded credentials, use env vars
├── Day 4: Add health check endpoints
└── Day 5: Create Docker configuration

Week 2:
├── Day 1-2: Fix dual app.py, consolidate entry point
├── Day 3-4: Add repository tests (critical paths)
└── Day 5: Complete RBAC middleware
```

**Deliverables**:
- [ ] All endpoints require JWT authentication
- [ ] Dockerfile + docker-compose.yml
- [ ] Health check endpoint `/health`
- [ ] Environment-based configuration
- [ ] 50%+ test coverage on repositories

### Phase 1: Shared Database Setup (1 week)

**Goal**: Establish shared database schema between PUGUH and MANTRA

```
├── Day 1: Create unified database schema
│   └── Core tables: users, tenants, memberships, subscriptions
├── Day 2: Migrate PUGUH to shared schema
├── Day 3: Add tenant_id/user_id columns to MANTRA tables
├── Day 4: Create migration scripts
└── Day 5: Test data isolation
```

**Deliverables**:
- [ ] Shared database with proper schemas
- [ ] MANTRA tables have tenant_id, user_id columns
- [ ] Migration scripts for existing data
- [ ] Row-level isolation verified

### Phase 2: MANTRA Auth Integration (1 week)

**Goal**: MANTRA validates auth via PUGUH

```
├── Day 1-2: Add JWT validation middleware to MANTRA
├── Day 3: Update all repositories with tenant scoping
├── Day 4: Update API endpoints to use TenantContext
└── Day 5: Test end-to-end auth flow
```

**Deliverables**:
- [ ] MANTRA validates JWT from PUGUH
- [ ] All queries scoped by tenant_id
- [ ] User identity tracked (not strings)
- [ ] RBAC enforced on write operations

### Phase 3: Frontend Integration (1 week)

**Goal**: Unified login experience

```
├── Day 1-2: Add login page to MANTRA frontend
│   └── Calls PUGUH auth API
├── Day 3: Add workspace/tenant switcher
├── Day 4: Store JWT in localStorage/cookie
└── Day 5: Handle token refresh
```

**Deliverables**:
- [ ] Login/logout flow working
- [ ] Tenant context in UI
- [ ] Protected routes

### Phase 4: Billing Integration (1 week)

**Goal**: MANTRA respects subscription limits

```
├── Day 1-2: Query subscription status from PUGUH
├── Day 3: Enforce decision limits per plan
├── Day 4: Add upgrade prompts in UI
└── Day 5: Test billing flows
```

**Deliverables**:
- [ ] MANTRA checks subscription status
- [ ] Usage limits enforced
- [ ] Upgrade path available

---

## 7. Subscription Model Proposal

### 7.1 PUGUH Standalone Plans

| Plan | Price (IDR) | Features |
|------|-------------|----------|
| Free | 0 | 1,000 decisions/month, 3 members |
| Starter | 290,000 | 10,000 decisions/month, 10 members |
| Pro | 990,000 | 100,000 decisions/month, 50 members |
| Enterprise | Custom | Unlimited, SLA, support |

### 7.2 MANTRA Plans (Requires PUGUH Base)

| Plan | Price (IDR) | Features |
|------|-------------|----------|
| MANTRA Free | 0 | 100 constitutional decisions, basic validation |
| MANTRA Pro | 490,000 | Unlimited decisions, AI assistant, semantic search |
| MANTRA Enterprise | Custom | Custom domains, SLA, dedicated support |

### 7.3 Bundle Pricing

| Bundle | Components | Price (IDR) |
|--------|------------|-------------|
| Governance Starter | PUGUH Starter + MANTRA Free | 290,000 |
| Governance Pro | PUGUH Pro + MANTRA Pro | 1,290,000 |
| Enterprise | Everything | Custom |

---

## 8. Risk Analysis

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Shared DB coupling | Medium | High | Clear schema ownership, versioned migrations |
| Auth service downtime | Low | Critical | Circuit breaker, token caching |
| Data leak between tenants | Low | Critical | RLS + query scoping + integration tests |
| Performance degradation | Medium | Medium | Separate connection pools, caching |

### 8.2 Business Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Complexity slows development | Medium | Medium | Clear phase boundaries, MVP first |
| PUGUH not mature enough | High | High | Fix critical gaps before integration |
| User confusion (2 products) | Medium | Low | Clear documentation, unified UX |

---

## 9. Success Criteria

### Technical Metrics

- [ ] All MANTRA endpoints require valid JWT
- [ ] 100% tenant isolation (no cross-tenant data access)
- [ ] Auth latency < 50ms (with caching)
- [ ] Zero hardcoded credentials
- [ ] 80%+ test coverage on auth/tenant code

### Business Metrics

- [ ] Can onboard new tenant in < 5 minutes
- [ ] Can add team member in < 1 minute
- [ ] Subscription upgrade works end-to-end
- [ ] Audit log shows real user identity

---

## 10. Immediate Next Steps

### For PUGUH (Owner: TBD)

1. **URGENT**: Add authentication middleware to all endpoints
2. **URGENT**: Move credentials to environment variables
3. Create Dockerfile and docker-compose.yml
4. Add `/health` endpoint
5. Consolidate app.py and app_v2.py

### For MANTRA (Owner: TBD)

1. Design tenant_id column addition (non-breaking)
2. Create TenantContext middleware (prepare, don't deploy)
3. Audit all repositories for tenant scoping needs
4. Document API changes needed

### For Integration (Owner: TBD)

1. Design shared database schema
2. Create migration plan for existing MANTRA data
3. Define JWT token structure
4. Plan rollout strategy (feature flags)

---

## 11. Conclusion

### Apakah Konsep Ini Viable?

**YA**, dengan catatan:

1. **PUGUH harus production-ready dulu** - Saat ini ada security vulnerabilities yang blocking
2. **Integration straightforward** - Hanya perlu add columns dan middleware
3. **Effort reasonable** - ~6 weeks total untuk full integration
4. **Mutual benefit jelas** - MANTRA dapat infra, PUGUH dapat real use case

### Recommended Approach

```
┌─────────────────────────────────────────────────────────────┐
│                     RECOMMENDED SEQUENCE                     │
├─────────────────────────────────────────────────────────────┤
│  1. Fix PUGUH critical gaps (2 weeks)                       │
│     └── Auth middleware, Docker, credentials                │
│                                                              │
│  2. Add tenant columns to MANTRA (non-breaking) (3 days)    │
│     └── tenant_id, user_id - nullable first                 │
│                                                              │
│  3. Shared database setup (1 week)                          │
│     └── PUGUH owns core tables                              │
│                                                              │
│  4. MANTRA auth integration (1 week)                        │
│     └── JWT validation, tenant scoping                      │
│                                                              │
│  5. Frontend integration (1 week)                           │
│     └── Login flow, tenant switcher                         │
│                                                              │
│  6. Billing integration (1 week)                            │
│     └── Subscription checks, limits                         │
└─────────────────────────────────────────────────────────────┘

Total: ~6 weeks from start to SaaS-ready
```

---

*Document created: 2026-01-28*
*Author: Claude (Analysis based on codebase exploration)*
*Status: DRAFT - Pending Review*
