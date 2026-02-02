# ARSAKA_PUGUH Backend - Phase A

**Decision Engine & Workflow Orchestration Service**

---

## 📋 Overview

ARSAKA_PUGUH Core Service provides:
- **Decision Engine**: Evaluates governance rules and returns decisions (ALLOWED, DENIED, REQUIRE_APPROVAL)
- **Workflow Orchestration**: Manages approval workflows with state transitions
- **Event Sourcing**: Immutable audit trail of all decisions and state changes

**Phase A Goal**: Visible, debuggable, end-to-end system (NOT production-ready)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker (optional, for containerized deployment)

### Local Development

```bash
# 1. Install dependencies
pip install -r requirements-phase-a.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials and JWT secret

# 3. Run migrations
psql -h localhost -p 5433 -U atlas_user -d arsaka_puguh < migrations/001_initial_schema.sql
psql -h localhost -p 5433 -U atlas_user -d arsaka_puguh < migrations/002_immutability_triggers.sql
psql -h localhost -p 5433 -U atlas_user -d arsaka_puguh < migrations/003_rls_policies.sql
psql -h localhost -p 5433 -U atlas_user -d arsaka_puguh < migrations/seed_phase_a.sql

# 4. Run application
uvicorn core.app:app --host 0.0.0.0 --port 8001 --reload

# 5. Test API
curl http://localhost:8001/health
curl http://localhost:8001/api/docs  # Swagger UI
```

---

## 🐳 Docker Deployment

### Build Image

```bash
# Build
docker build -t arsaka-puguh-backend:phase-a .

# Run locally
docker run -p 8001:8001 --env-file .env arsaka-puguh-backend:phase-a

# Push to registry (for Nomad)
docker tag arsaka-puguh-backend:phase-a your-registry/arsaka-puguh-backend:phase-a
docker push your-registry/arsaka-puguh-backend:phase-a
```

---

## 🎯 Phase A Configuration

### What's Enabled (CORE)

✅ **Core Domain Logic**:
- Decision engine with rule evaluation
- Workflow state machine (PENDING → APPROVED/REJECTED)
- Immutability guarantees (decisions never mutate)
- Event sourcing (all state changes logged)

✅ **Minimal Infrastructure**:
- PostgreSQL connection pooling (pool_size=2)
- Structured logging (JSON format)
- JWT authentication (hardcoded users)
- Basic CORS configuration

### What's Disabled (SCAFFOLD)

❌ **Caching**: No Redis (set `REDIS_ENABLED=false`)
❌ **Rate Limiting**: No backend rate limiter (set `RATE_LIMIT_ENABLED=false`)
❌ **Metrics**: No Prometheus (set `ENABLE_METRICS=false`)
❌ **Tracing**: No Jaeger (set `ENABLE_TRACING=false`)

**Why Disabled?** Phase A focuses on visibility and debugging, not production scale. All disabled features are tested (119 unit tests) and have fail-open behavior.

---

## 📦 Directory Structure

```
backend/
├── core/                       # Core domain logic (PERMANENT)
│   ├── app.py                 # FastAPI application entry point
│   ├── api/                   # HTTP API routes
│   ├── domain/                # Domain models & aggregates
│   ├── use_cases/             # Business logic use cases
│   └── tests/                 # Core domain tests
│
├── infrastructure/            # Infrastructure components (SCAFFOLD - Phase B)
│   ├── cache/                 # Redis cache (disabled in Phase A)
│   ├── rate_limit/            # Rate limiter (disabled in Phase A)
│   ├── metrics/               # Prometheus metrics (disabled in Phase A)
│   └── tracing/               # OpenTelemetry tracing (disabled in Phase A)
│
├── migrations/                # Database migrations
│   ├── 001_initial_schema.sql
│   ├── 002_immutability_triggers.sql
│   ├── 003_rls_policies.sql
│   └── seed_phase_a.sql       # Phase A test data
│
├── shared/                    # Shared utilities
│   └── api_routes.py          # Centralized route definitions
│
├── .env.example               # Phase A configuration template
├── requirements-phase-a.txt   # Phase A dependencies (minimal)
├── Dockerfile                 # Docker image (optimized for Phase A)
└── README.md                  # This file
```

---

## 🔧 Configuration Reference

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://atlas_user:PASSWORD@localhost:5433/arsaka_puguh

# JWT Authentication
JWT_SECRET_KEY=CHANGE_THIS_TO_RANDOM_32_CHAR_STRING
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# Tenant (Phase A: Single tenant)
ALLOWED_TENANT_IDS=550e8400-e29b-41d4-a716-446655440000
```

### Phase A Feature Flags

```bash
# Infrastructure (ALL DISABLED)
REDIS_ENABLED=false
RATE_LIMIT_ENABLED=false
ENABLE_METRICS=false
ENABLE_TRACING=false

# Connection Pool (MINIMAL)
POOL_SIZE=2
MAX_OVERFLOW=3

# Logging (DEBUG MODE)
LOG_LEVEL=DEBUG
LOG_FORMAT=json
```

See `.env.example` for complete configuration.

---

## 🧪 Testing

### Phase A Test Data

Seed data (`migrations/seed_phase_a.sql`) includes:

**Rules** (4 total):
1. Auto-approve small expenses (< $100)
2. Require approval for medium expenses ($100-$1000)
3. Require CFO approval for large expenses (≥ $1000)
4. Purchase order approval (multi-condition)

**Test Users** (Hardcoded in JWT, no users table):
- `user-admin-001` (admin role)
- `user-approver-001` (finance_manager role)

**Sample Data**:
- 2 decisions (1 auto-approved, 1 pending approval)
- 1 workflow (pending approval)
- 2 events (logged to event_log)

### Manual Testing

```bash
# 1. Health check
curl http://localhost:8001/health

# 2. List rules
curl http://localhost:8001/api/v1/rules

# 3. Create decision (requires JWT token)
curl -X POST http://localhost:8001/api/v1/decisions \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "decision_type": "expense.approval",
    "context": {
      "amount": 500,
      "description": "Test expense",
      "requester": "user-admin-001"
    },
    "idempotency_key": "test-123"
  }'

# 4. Approve workflow
curl -X POST http://localhost:8001/api/v1/workflows/{workflow_id}/approve \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🚨 Troubleshooting

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -p 5433 -U atlas_user -d arsaka_puguh -c "SELECT 1"

# Verify DATABASE_URL in .env
cat .env | grep DATABASE_URL
```

### Health Check Fails

```bash
# Check application logs
docker logs <container-id>

# Verify port is exposed
curl http://localhost:8001/health

# Check CORS configuration
curl -v http://localhost:8001/health -H "Origin: http://localhost:3000"
```

### JWT Token Issues

```bash
# Generate test JWT token (requires Python)
python << 'EOF'
from jose import jwt
import datetime

payload = {
    "user_id": "user-admin-001",
    "email": "admin@example.com",
    "role": "admin",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}

token = jwt.encode(payload, "YOUR_JWT_SECRET_KEY", algorithm="HS256")
print(token)
EOF
```

---

## 📚 Documentation

### Architecture Docs (Root Directory)

- **`CORE_VS_SCAFFOLD.md`** - What's permanent vs temporary
- **`PHASE_A_SIMPLIFICATION_PLAN.md`** - What was cut and why
- **`PHASE_A_CONFIGURATION.md`** - Complete .env guide
- **`REFOCUS_REPORT.md`** - Refocus effort summary

### Deployment Docs (Root Directory)

- **`NOMAD_DEPLOYMENT_PHASE_A.md`** - Complete Nomad deployment guide
- **`NOMAD_QUICKSTART.md`** - 15-minute quick deploy
- **`nomad/README.md`** - Job files reference

### API Documentation

- **Swagger UI**: http://localhost:8001/api/docs
- **ReDoc**: http://localhost:8001/api/redoc
- **OpenAPI JSON**: http://localhost:8001/api/openapi.json

---

## 🔄 Phase B Migration Path

When ready for Phase B (production hardening):

1. **Enable Infrastructure**:
   ```bash
   REDIS_ENABLED=true
   REDIS_URL=redis://redis.service.consul:6379
   RATE_LIMIT_ENABLED=true
   ENABLE_METRICS=true
   ENABLE_TRACING=true
   ```

2. **Scale Resources**:
   ```bash
   POOL_SIZE=10
   MAX_OVERFLOW=10  # Total: 20 connections
   ```

3. **Install Additional Dependencies**:
   ```bash
   pip install redis[hiredis]==5.0.1 slowapi==0.1.9 prometheus-client==0.19.0
   ```

4. **Deploy Monitoring Stack**:
   - Prometheus for metrics collection
   - Grafana for dashboards
   - Jaeger for distributed tracing

**All Phase B features are already tested** (119 unit tests verify fail-open behavior).

---

## 🎯 Success Criteria (Phase A)

Deployment successful if:

- ✅ Health endpoint returns 200 OK
- ✅ API documentation accessible at `/api/docs`
- ✅ Can create decisions via API (with JWT token)
- ✅ Rules are evaluated correctly (auto-approve < $100, require approval $100-$1000)
- ✅ Workflows transition correctly (PENDING → APPROVED/REJECTED)
- ✅ Events logged to `event_log` table
- ✅ Structured logs visible in JSON format

---

## 📖 Additional Resources

- **Architecture Standards**: `/docs/` (in project root)
- **Database Migrations**: `/migrations/README.md`
- **API Routes**: `/shared/api_routes.py`
- **Test Suite**: `/tests/` (119 unit tests)

---

**Document Version**: 1.0
**Last Updated**: 2026-01-09
**Status**: Ready for Phase A Deployment
