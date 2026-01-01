# Repository Governance & Multi-Repo Strategy

> **Date**: 2025-12-23
> **Status**: Draft
> **Purpose**: System architecture governance for multi-repository strategy
> **Audience**: Architects, Lead Developers, AI/LLM Coding Agents

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   MULTI-REPOSITORY ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  PRINCIPLE:                                                             │
│  1 Repository = 1 Business Capability (NOT 1 Folder or 1 Technology)   │
│                                                                         │
│  GOAL:                                                                  │
│  ✓ No single person/AI controls entire system                          │
│  ✓ Security through architecture, not trust                            │
│  ✓ Scalable team structure                                             │
│  ✓ Clear boundaries and responsibilities                               │
│                                                                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │   Repo A   │  │   Repo B   │  │   Repo C   │  │   Repo D   │       │
│  │ (Auth)     │  │ (PMS)      │  │ (POS)      │  │ (Frontend) │       │
│  │            │  │            │  │            │  │            │       │
│  │ ✓ Own DB   │  │ ✓ Own DB   │  │ ✓ Own DB   │  │ ✓ No DB    │       │
│  │ ✓ Own API  │  │ ✓ Own API  │  │ ✓ Own API  │  │ ✓ Own code │       │
│  │ ✓ Contract │  │ ✓ Contract │  │ ✓ Contract │  │ ✓ Contract │       │
│  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘  └──────┬─────┘       │
│         │               │               │               │              │
│         └───────────────┴───────────────┴───────────────┘              │
│                         │                                              │
│                    Communication Via:                                  │
│                  • Events (Event Bus)                                  │
│                  • API Calls (Read-only)                               │
│                  • NO Direct DB Access                                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Repository Boundaries

### 1.1 Core Principle

```
Repository = Business Capability Boundary
```

A repository should be defined by **what business problem it solves**, NOT by:
- ❌ Technical layers (controllers, models, services)
- ❌ Programming language
- ❌ Small features
- ❌ Number of developers
- ❌ Folder structure

### 1.2 Repository Classification Test

Use this 5-question test to determine if something should be a separate repository:

```
Question #1: Aturan Bisnis Sendiri?
└─ Apakah domain ini punya aturan bisnis yang unik dan tidak berlaku di domain lain?
   (e.g., PMS punya checkout flow, POS punya receipt generation)
   ✓ YES → Continue to Q2

Question #2: Data Berdiri Sendiri?
└─ Apakah domain ini punya data model yang dominan yang tidak bisa didekomposisi?
   (e.g., PMS needs Guest/Reservation, POS needs Order/Item)
   ✓ YES → Continue to Q3

Question #3: Skalabilitas Mandiri?
└─ Bisakah domain ini diskalakan independent dari domain lain?
   (e.g., PMS gets 1000 req/s, POS gets 10 req/s → skalakan terpisah)
   ✓ YES → Continue to Q4

Question #4: Mati Sendiri Tanpa Mematikan Lain?
└─ Jika domain ini down, apakah domain lain tetap bisa jalan?
   (e.g., POS down ≠ PMS down, tapi Auth down = semua down)
   ✓ YES → Continue to Q5

Question #5: Accessible via Event/API?
└─ Bisakah domain ini di-access oleh domain lain hanya via Event atau API?
   (NO direct database access)
   ✓ YES → LAYAK JADI REPOSITORY TERPISAH
```

**Scoring:**
- **≥ 4 YA** → **Definite**: Harus jadi repo terpisah
- **3 YA** → **Likely**: Pertimbangkan jadi repo terpisah
- **≤ 2 YA** → **No**: Tetap dalam repo yang sama

### 1.3 Example Repository Decisions

```
✅ SEPARATE REPO: Authentication (Core Auth)
├─ Q1: ✓ Unique auth rules (MFA, token management)
├─ Q2: ✓ Own data (users, sessions, tokens)
├─ Q3: ✓ Scalable independently
├─ Q4: ✗ Cannot die (critical) - BUT still separate for security
└─ Q5: ✓ Accessible via API/JWT

✅ SEPARATE REPO: Property Management System (PMS)
├─ Q1: ✓ Unique business logic (reservation, checkout)
├─ Q2: ✓ Own data (guests, rooms, reservations)
├─ Q3: ✓ Scalable independently
├─ Q4: ✓ Can die without affecting POS
└─ Q5: ✓ Events (guest_checked_in) + API

❌ SAME REPO: Booking & Confirmation
├─ Q1: ✗ Same booking logic
├─ Q2: ✗ Same data model
├─ Q3: ✗ Cannot scale independently
└─ Decision: Keep in same repo, not separate

❌ SAME REPO: Invoice & Invoice Item
├─ Q1: ✗ Item is part of Invoice logic
├─ Q2: ✗ Cannot exist without Invoice
├─ Q3: ✗ Not independent
└─ Decision: Keep in same repo as Accounting

✅ SEPARATE REPO: Accounting (Financial Spine)
├─ Q1: ✓ Unique accounting rules
├─ Q2: ✓ Critical data (GL, AP, AR)
├─ Q3: ✓ Must scale for financial integrity
├─ Q4: ✓ Can have fallback behavior
└─ Q5: ✓ Events only (no schema changes)
   NOTE: Accounting NEVER "receives" schema changes from other repos
```

### 1.4 Repository Types

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      REPOSITORY TYPES                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  TYPE 1: CORE SERVICES (Foundational)                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Examples: auth, tenant-management, audit, notification          │   │
│  │ Characteristics:                                                │   │
│  │ • Consumed by many repos                                        │   │
│  │ • Cannot be "down" without breaking system                      │   │
│  │ • Data is IMMUTABLE or APPEND-ONLY                             │   │
│  │ • Schema changes require consensus                              │   │
│  │ • Provides: API only (no events)                                │   │
│  │ Access: Read-only APIs, JWT tokens                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  TYPE 2: FEATURE MODULES (Business Domains)                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Examples: pms, pos, accounting, inventory, signage              │   │
│  │ Characteristics:                                                │   │
│  │ • Independent business capability                               │   │
│  │ • Own database tables                                           │   │
│  │ • Produces events (publish)                                     │   │
│  │ • Consumes events (subscribe)                                   │   │
│  │ • Can be down/degraded without blocking others                 │   │
│  │ Provides: API + Events                                          │   │
│  │ Access: Events + REST API (read-only)                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  TYPE 3: INFRASTRUCTURE / PLATFORM                                    │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Examples: deployment, monitoring, shared-libs                   │   │
│  │ Characteristics:                                                │   │
│  │ • Cross-cutting concerns                                        │   │
│  │ • No business logic                                             │   │
│  │ • Used by other repos                                           │   │
│  │ Provides: Libraries, configs, CI/CD                             │   │
│  │ Access: Via package manager, configs                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  TYPE 4: FRONTEND APPLICATIONS                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ Examples: web-app, mobile-app, admin-dashboard                  │   │
│  │ Characteristics:                                                │   │
│  │ • Consumes multiple repos' APIs                                 │   │
│  │ • No backend logic (presentation only)                          │   │
│  │ • Can be deployed independently                                 │   │
│  │ Provides: UI                                                    │   │
│  │ Access: Multiple APIs, no direct DB                             │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 2: Service Contracts

### 2.1 Why Service Contracts?

Service contracts are **guardrails for architecture**:
- Prevent AI from creating cross-repo dependencies
- Prevent developer from mixing business logic
- Make boundaries explicit and testable
- Enable safe refactoring within repo

### 2.2 Required Service Contract

Every repository **MUST** have:

```markdown
# SERVICE_CONTRACT.md (MANDATORY)

## Service Identity
- **Repository Name**: pms-service
- **Domain**: Property Management System
- **Owner Team**: PMS Team
- **Criticality**: High (guest operations)

## Responsibilities
This service owns:
- Guest management (profiles, documents)
- Reservations (booking, checking in/out)
- Room management (inventory, rates)
- Folio billing (charges, payments)

## What This Service Does NOT Own
- User authentication (auth-service owns this)
- Payment processing (payments-service owns this)
- Reporting (reporting-service owns this)

## Events Published
- `guest.created`
- `guest.updated`
- `reservation.created`
- `reservation.checked_in`
- `reservation.checked_out`
- `folio.created`
- `folio.charged`

## Events Consumed
- `user.created` (from auth-service) → Create guest profile
- `tenant.activated` (from tenant-service) → Setup tenant rates
- `payment.completed` (from payments-service) → Clear folio charges

## API Contract
```
GET /api/pms/guests/{id}
GET /api/pms/reservations?filters
POST /api/pms/reservations
PATCH /api/pms/reservations/{id}/check-in
```

## What's FORBIDDEN
❌ DO NOT query other services' databases directly
❌ DO NOT write business logic that spans 2+ repos
❌ DO NOT assume synchronous behavior from events
❌ DO NOT change database schema without notifying consumers
❌ DO NOT expose internal tables (only API endpoints)

## Data Ownership
| Entity | Owner | Read | Write |
|--------|-------|------|-------|
| Guest | pms | pms | pms only |
| Reservation | pms | pms | pms only |
| Room | pms | pms | pms only |

## Deployment
- CI/CD: GitHub Actions
- Deployment frequency: Multiple times per day
- Rollback procedure: Blue-green deployment

## Monitoring & SLA
- Availability target: 99.9%
- Response time: < 200ms (p95)
- Alert on: Errors > 1%, Latency > 500ms
```

### 2.3 Contract Enforcement

```python
# tests/test_service_contract.py
import pytest
from services.pms import models, api

def test_contract_no_direct_db_access():
    """Verify PMS doesn't query auth database directly"""
    import inspect
    source = inspect.getsource(models)

    # Should not contain direct DB imports from other services
    assert "from auth.models import" not in source
    assert "auth_db.query" not in source

def test_contract_no_unauthorized_tables():
    """Verify PMS only exposes authorized tables via API"""
    api_routes = [route.path for route in api.routes]

    # These internal tables should NOT have API endpoints
    assert "/api/pms/internal_" not in str(api_routes)
    assert "/api/pms/temp_" not in str(api_routes)

def test_events_published():
    """Verify PMS publishes expected events"""
    from services.pms.events import EVENT_REGISTRY

    required_events = [
        "guest.created",
        "reservation.created",
        "folio.charged"
    ]

    for event in required_events:
        assert event in EVENT_REGISTRY

def test_api_contract_schemas():
    """Verify API responses match contract"""
    client = TestClient(app)

    response = client.get("/api/pms/guests/1")
    assert response.status_code == 200

    # Should match contract schema
    guest = response.json()
    assert "id" in guest
    assert "name" in guest
    # Internal fields should NOT be exposed
    assert "internal_notes" not in guest
```

---

## Part 3: Inter-Repository Communication

### 3.1 Allowed Patterns

```
✅ PATTERN 1: Event-Driven (Async, Decoupled)
┌─────────────────┐        ┌──────────────────┐
│  PMS Service    │        │ Event Bus        │
│  (checkout)     │───────►│ (event_queue)    │
└─────────────────┘        └──────┬───────────┘
                                  │
                  ┌───────────────┼───────────────┐
                  ▼               ▼               ▼
            ┌──────────┐    ┌──────────┐   ┌──────────┐
            │ Accounting │  │ Reporting│   │ Inventory│
            │ (subscribe)│  │(subscribe)   │(subscribe)
            └──────────┘    └──────────┘   └──────────┘

Use: When PMS doesn't care about result
Pros: Decoupled, scalable, async
Cons: Eventual consistency


✅ PATTERN 2: API Read-Only (Sync, Coupled)
┌─────────────────┐
│  Reporting      │
│  Service        │
└────────┬────────┘
         │
         │ GET /api/pms/reservations?filter
         │ (read-only, no side effects)
         ▼
┌─────────────────┐
│  PMS Service    │
└─────────────────┘

Use: When need current state, no state change
Pros: Real-time data, simple
Cons: Synchronous coupling, must handle failures


✅ PATTERN 3: Saga Pattern (Distributed Transaction)
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Reservation  │────►│  Payment     │────►│  Accounting  │
│  (start)     │     │  (charge)    │     │  (record)    │
└──────────────┘     └──────────────┘     └──────────────┘
     │                    │                     │
     └────────────────────┴─────────────────────┘
           (Compensate on failure)

Use: Multi-step operations requiring consistency
Pros: ACID-like guarantee
Cons: Complex, need compensation logic


❌ PATTERN 4: Direct Database Access (FORBIDDEN)
┌─────────────────────┐
│ Reporting Service   │
└────────┬────────────┘
         │
         │ SELECT * FROM pms.reservations WHERE...
         │ (FORBIDDEN!)
         ▼
┌─────────────────┐
│  PMS Database   │
└─────────────────┘

Why forbidden:
• Breaks encapsulation
• Hides dependencies
• Makes refactoring impossible
• Couples to internal schema
• Cannot be audited


❌ PATTERN 5: Synchronous API Chain (RISKY)
Service A ──► Service B ──► Service C ──► Service D
(4-hop dependency chain)

Problems:
• If one service is slow, all slow
• If one service down, all fail
• Distributed tracing nightmare
• Hard to test

Use saga pattern instead.
```

### 3.2 Communication Guidelines

| Pattern | Use Case | Consistency | Coupling | Complexity |
|---------|----------|-------------|----------|------------|
| **Events** | State change notification | Eventual | Loose | Low |
| **API (read)** | Need current state | Strong | Moderate | Low |
| **Saga** | Multi-step transaction | Strong | Moderate | High |
| **DB Access** | ❌ FORBIDDEN | N/A | Tight | N/A |
| **Sync API** | Simple action | Strong | Tight | Low |

---

## Part 4: Governance & Access Control

### 4.1 Repository Access Matrix

```
┌────────────────┬──────────────────────────────────────────────────────┐
│ Role/Team      │ Permissions                                         │
├────────────────┼──────────────────────────────────────────────────────┤
│ PMS Team       │ ✓ Write to pms repo                                 │
│                │ ✓ Read from auth, tenant, infra                     │
│                │ ✗ Write to accounting, pos, inventory               │
│                │ ✗ Deploy to production (CI/CD only)                 │
├────────────────┼──────────────────────────────────────────────────────┤
│ Accounting Team│ ✓ Write to accounting repo                          │
│                │ ✓ Read from pms, pos (via API only)                │
│                │ ✗ Write to any other repo                           │
│                │ ✗ Change accounting schema without approval         │
├────────────────┼──────────────────────────────────────────────────────┤
│ AI Coding Agent│ ✓ Write to 1 assigned repo per task                │
│                │ ✓ Read shared docs, API contracts                   │
│                │ ✗ Write to multiple repos in 1 PR                   │
│                │ ✗ Create cross-repo dependencies                    │
│                │ ✗ Access production secrets                         │
├────────────────┼──────────────────────────────────────────────────────┤
│ DevOps/Infra   │ ✓ Write to infra repo                               │
│                │ ✓ Read all repos                                    │
│                │ ✓ Deploy (CI/CD pipeline)                           │
│                │ ✓ Manage secrets                                    │
│                │ ✗ Write business logic                              │
├────────────────┼──────────────────────────────────────────────────────┤
│ Security Team  │ ✓ Audit access                                      │
│                │ ✓ Review contracts & architecture                   │
│                │ ✓ Penetration testing                               │
│                │ ✗ Bypass controls                                   │
└────────────────┴──────────────────────────────────────────────────────┘
```

### 4.2 Secret Management (NO Secrets in Code)

```python
# ✅ CORRECT: Secrets from environment/vault
import os
from shared.config import get_secrets_manager

secrets = get_secrets_manager()  # Vault in prod, Bitwarden in dev
db_password = await secrets.get("database/password")
api_key = await secrets.get("payment_api/key")

# ❌ WRONG: Secrets in code
PASSWORD = "postgres123"  # NEVER!
API_KEY = "sk_live_abc123xyz"  # NEVER!
```

**Enforcement:**
```bash
# Pre-commit hook
if grep -r "password\s*=" . || grep -r "secret\s*=" .; then
    echo "ERROR: Found hardcoded secrets!"
    exit 1
fi

# Git secret scanner
git-secrets --scan
```

---

## Part 5: AI Development Rules

### 5.1 Global AI Rules Document

Every system **MUST** have:

```markdown
# AI_RULES.md (MANDATORY)

This document constrains AI/LLM agents to ensure architecture integrity.

## Rule 1: One Repository Per Task
- AI processes ONE repository per pull request
- AI cannot create PRs spanning multiple repos
- Exception: Shared library updates (infra repo)

## Rule 2: Obey Service Contracts
- AI MUST read SERVICE_CONTRACT.md before coding
- AI CANNOT:
  - Create new events without updating contract
  - Query other services' databases
  - Create cross-repo business logic
  - Call other services without documented API

## Rule 3: Architecture Boundaries
- AI CANNOT remove, extend, or bypass repository boundaries
- If business requirement spans repos, break into multiple PRs
- AI must propose changes to SERVICE_CONTRACT.md

## Rule 4: Testing Requirements
- Unit tests required for new business logic
- Integration tests for API contracts
- No merge without passing tests

## Rule 5: Documentation Requirements
- Update SERVICE_CONTRACT.md for API changes
- Document new events (publisher/subscriber)
- Document data model changes

## Rule 6: Security Rules
- No secrets in code (use environment variables)
- No hardcoded API keys, passwords, tokens
- Implement audit logging for sensitive data access
- All data access must be role-based

## Rule 7: Pull Request Template
Every PR must include:
```
- Repository: [pms-service]
- Changes Type: [feature/bugfix/refactor]
- Affected Contract Items: [list]
- Cross-Repo Dependencies: [none/list]
- Testing: [units/integration/e2e]
```

## Rule 8: Prohibited Patterns
❌ DO NOT:
- Direct database queries across repos
- Hardcoded configuration
- Unlogged data access
- Schema changes to other repos
- Circular dependencies
- Direct service imports (use API)

## Rule 9: Asking for Help
When in doubt:
1. Check SERVICE_CONTRACT.md of your repo
2. Check SERVICE_CONTRACT.md of other repos
3. Ask in architecture review channel
4. Don't guess or work around boundaries
```

### 5.2 AI Prompt Template

When prompting AI agents, include:

```
## Task: [Feature Name]

You are working on the **{repo_name}** repository.

### Context
[Describe what needs to be done]

### Constraints
1. Obey AI_RULES.md (read it first!)
2. Obey SERVICE_CONTRACT.md for this repo
3. Do NOT query other repos' databases
4. Do NOT create cross-repo business logic
5. Include unit tests for new logic
6. Update SERVICE_CONTRACT.md if API changes

### Example Allowed
- [Example of allowed work]

### Example NOT Allowed
- [Example of not allowed work]

---

**IMPORTANT**: Before coding, output:
- Which repo you're working on
- Which SERVICE_CONTRACT items apply
- Any cross-repo APIs you'll call
- Any new events you'll publish

Then proceed with implementation.
```

---

## Part 6: Deployment & Security

### 6.1 Deployment Pipeline

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│  Developer  │      │  Repository  │      │ Automated    │
│   Commits   │─────►│   CI/CD      │─────►│ Deployment   │
└─────────────┘      └──────────────┘      └──────────────┘
                            │                     │
                            ▼                     ▼
                     1. Run Tests         1. Deploy to Staging
                     2. Security Scan     2. Run Integration Tests
                     3. Build Image       3. Deploy to Production
                     4. Push Registry     4. Health Check

❌ FORBIDDEN:
- Direct SSH to production
- Manual database migrations
- Manual deployments
```

### 6.2 Security Through Architecture

**Single Point of Control = Security Risk**

```
❌ BAD: Monolithic Architecture
┌─────────────────────────────────────────────────────┐
│  MONOLITH (Single Repo)                             │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ One developer/AI has full system access     │   │
│  │ • Can read/write all databases              │   │
│  │ • Can call all internal functions           │   │
│  │ • Can deploy everything                     │   │
│  │ • If one part compromised → all compromised │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Breach = Total system compromise                  │
└─────────────────────────────────────────────────────┘

✅ GOOD: Multi-Repository Architecture
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Auth     │  │ PMS      │  │ Payments │
│ Repo     │  │ Repo     │  │ Repo     │
├──────────┤  ├──────────┤  ├──────────┤
│ Database │  │ Database │  │ Database │
│ API      │  │ API      │  │ API      │
└──────────┘  └──────────┘  └──────────┘

Dev A access: Auth repo only
Dev B access: PMS repo only
Dev C access: Payments repo only

Breach in PMS repo:
• Cannot access Auth database
• Cannot access Payments database
• System partially continues
```

**Principle:**
> Security is achieved through **architecture boundaries**, not through trust or access controls.

---

## Part 7: Repository Checklist

Use this when creating a new repository:

```markdown
# New Repository Checklist

## [ ] Architecture
- [ ] Passed 5-question test (≥ 3 YES)
- [ ] Clear business capability defined
- [ ] Does NOT duplicate existing repo responsibility
- [ ] Cannot be absorbed into existing repo

## [ ] Documentation
- [ ] SERVICE_CONTRACT.md created
- [ ] README.md with setup instructions
- [ ] Architecture decision recorded
- [ ] Ownership/team assigned

## [ ] Code Structure
- [ ] Follows clean architecture pattern
- [ ] Has package structure (entities/usecases/adapters)
- [ ] No imports from other service databases
- [ ] All external communication via API/events

## [ ] Data Management
- [ ] Database schema documented
- [ ] Tables clearly marked with repo ownership
- [ ] No joins to other repos' tables
- [ ] Event schema defined (if publishing)

## [ ] Testing
- [ ] Unit tests (>80% coverage)
- [ ] Integration tests for APIs
- [ ] Contract tests with consumers
- [ ] CI/CD pipeline configured

## [ ] API Contract
- [ ] API endpoints documented
- [ ] Request/response schemas defined
- [ ] Error codes documented
- [ ] Rate limiting defined

## [ ] Event Contract (if applicable)
- [ ] Events documented
- [ ] Event schema (JSON schema)
- [ ] Subscribers identified
- [ ] Retry/failure policy defined

## [ ] Security
- [ ] No hardcoded secrets
- [ ] Input validation on all APIs
- [ ] Authentication required
- [ ] Authorization checks in place
- [ ] Audit logging implemented

## [ ] Deployment
- [ ] Dockerfile created
- [ ] Deployment manifests (k8s/nomad)
- [ ] Health checks configured
- [ ] Monitoring/alerting setup

## [ ] Governance
- [ ] AI_RULES.md acknowledged
- [ ] Access matrix defined
- [ ] Code review process documented
- [ ] Escalation path for architecture questions
```

---

## Part 8: Decision Framework

### 8.1 Should This Be a New Repo?

```
Question: "Should we create a new repository?"

Ask:
1. Does it have its own business domain?
   → YES: Continue
   → NO: Add to existing repo, stop

2. Does it need independent scaling?
   → YES: Continue
   → NO: Add to existing repo, stop

3. Can it be maintained by one team?
   → YES: Continue
   → NO: Split further or use shared team, stop

4. Does separating it reduce system coupling?
   → YES: Create new repo ✅
   → NO: Keep in existing repo, stop
```

### 8.2 Repository Naming Convention

```
{type}-{domain}-{service}

Examples:
service-auth               → Core auth service
service-pms-property       → PMS property management
service-accounting-ledger  → Accounting general ledger
service-reporting-bi       → Reporting/BI service
app-web-admin              → Admin web application
app-mobile-guest           → Guest mobile application
lib-shared-utils           → Shared utilities library
infra-deployment           → Deployment infrastructure

Pattern: {type}-{domain}-{specific}
Types: service, app, lib, infra, tool
```

---

## Part 9: Anti-Patterns to Avoid

### 9.1 Common Mistakes

```
❌ MISTAKE 1: Repository Per Developer
Wrong: repo-john, repo-sarah, repo-team-a
Right: service-pms (team A owns it, John + Sarah work on it)

❌ MISTAKE 2: Repository Per Folder
Wrong: repo-controllers, repo-models, repo-services
Right: service-pms (contains all layers)

❌ MISTAKE 3: Repository Per Feature
Wrong: repo-login, repo-logout, repo-password-reset
Right: service-auth (contains all auth features)

❌ MISTAKE 4: Circular Dependencies
Wrong: Service A → Service B → Service A
Right: Service A publishes events → Service B subscribes

❌ MISTAKE 5: Long Dependency Chains
Wrong: A → B → C → D → E (5-hop chain)
Right: A publishes events, B/C/D/E subscribe independently

❌ MISTAKE 6: Sync All the Way Down
Wrong: API → API → API → Database (deep chain)
Right: Top-level API, events for async updates

❌ MISTAKE 7: Shared Database
Wrong: Multiple repos access same tables
Right: Each repo owns its database tables
```

---

## Summary

**Core Rules:**
1. **1 Repo = 1 Business Capability** (tested with 5 questions)
2. **Service Contracts are mandatory** (guardrails for architecture)
3. **No direct DB access** across repos (use Events/API)
4. **AI must obey boundaries** (AI_RULES.md enforced)
5. **Security through architecture** (distributed, no single control)
6. **CI/CD deployment only** (no manual production)
7. **Clear ownership** (one team per repo)

**Key Documents:**
- `SERVICE_CONTRACT.md` → In every repository
- `AI_RULES.md` → Global rules for all developers/AI
- Repository naming convention → Clear identity

**Communication Patterns:**
- **Events** → For state change notifications (decoupled)
- **API Read** → For querying current state (read-only)
- **Saga** → For distributed transactions (complex)
- **DB Access** → ❌ FORBIDDEN

---

**Related Documents:**
- ARCH-01: Platform Vision (system overview)
- ARCH-02: Module Architecture (within-repo organization)
- ARCH-03: Puzzle Architecture (module integration)
- GUIDE-01: Development Flow (day-to-day workflow)
