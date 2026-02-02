# Phase A Configuration Guide

**Purpose**: Minimal `.env` configuration for Phase A deployment
**Target**: Visible, debuggable system (NOT production-ready)

---

## 📋 Complete `.env` for Phase A

Create file: `backend/.env.phase-a`

```bash
# =============================================================================
# ARSAKA_PUGUH — PHASE A CONFIGURATION (MINIMAL VISIBLE SYSTEM)
# =============================================================================
#
# ⚠️ WARNING: This is NOT a production configuration
# ⚠️ Purpose: Manual testing, debugging, flow validation
# ⚠️ Security: IP-whitelisted access only
#
# =============================================================================

# -----------------------------------------------------------------------------
# ENVIRONMENT
# -----------------------------------------------------------------------------
ENVIRONMENT=phase-a-staging

# -----------------------------------------------------------------------------
# DATABASE (REQUIRED)
# -----------------------------------------------------------------------------
# PostgreSQL connection URL
# Format: postgresql+asyncpg://user:password@host:port/database

DATABASE_URL=postgresql+asyncpg://atlas_user:CHANGE_THIS_PASSWORD@localhost:5433/arsaka_puguh

# -----------------------------------------------------------------------------
# AUTHENTICATION (MINIMAL)
# -----------------------------------------------------------------------------
# JWT secret key (REQUIRED - minimum 32 characters)
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"

JWT_SECRET_KEY=CHANGE_THIS_TO_RANDOM_32_CHAR_STRING

# JWT algorithm (HS256 is sufficient for Phase A)
JWT_ALGORITHM=HS256

# JWT token expiration (60 minutes for Phase A manual testing)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# -----------------------------------------------------------------------------
# TENANT (HARDCODED)
# -----------------------------------------------------------------------------
# Single tenant whitelist (Phase A: 1 tenant only)
ALLOWED_TENANT_IDS=550e8400-e29b-41d4-a716-446655440000

# -----------------------------------------------------------------------------
# INFRASTRUCTURE - CACHING (DISABLED)
# -----------------------------------------------------------------------------
# Redis caching DISABLED for Phase A (no value for 1 tenant, 2 users)
REDIS_ENABLED=false

# Redis URL (leave empty, fail-open will handle this)
REDIS_URL=

# -----------------------------------------------------------------------------
# INFRASTRUCTURE - RATE LIMITING (DISABLED)
# -----------------------------------------------------------------------------
# Backend rate limiting DISABLED for Phase A (Cloudflare provides this)
RATE_LIMIT_ENABLED=false

# -----------------------------------------------------------------------------
# INFRASTRUCTURE - OBSERVABILITY (MINIMAL)
# -----------------------------------------------------------------------------
# Logging level (DEBUG for Phase A - verbose logs for debugging)
LOG_LEVEL=DEBUG

# Log format (JSON for structured logging - easier to grep)
LOG_FORMAT=json

# Prometheus metrics DISABLED for Phase A (no monitoring dashboard)
ENABLE_METRICS=false

# Jaeger tracing DISABLED for Phase A (monolithic system, no distributed tracing)
ENABLE_TRACING=false

# Jaeger endpoint (leave empty)
JAEGER_ENDPOINT=

# -----------------------------------------------------------------------------
# INFRASTRUCTURE - DATABASE CONNECTION POOLING (MINIMAL)
# -----------------------------------------------------------------------------
# Core pool size (Phase A: 2 users → 2 connections)
POOL_SIZE=2

# Max overflow (burst capacity up to 5 connections total)
MAX_OVERFLOW=3

# Pool timeout (fast failure - don't wait 30 seconds)
POOL_TIMEOUT=10

# Pool recycle (1 hour - recycle stale connections)
POOL_RECYCLE=3600

# Pool pre-ping (validate connection before use)
POOL_PRE_PING=true

# -----------------------------------------------------------------------------
# API CONFIGURATION
# -----------------------------------------------------------------------------
# CORS origins (allow frontend access)
CORS_ORIGINS=http://localhost:3000,http://192.168.5.12:3000,http://72.61.209.158:3000,https://admin.zhmhotels.online

# API base URL (for Swagger docs)
API_BASE_URL=http://localhost:8001

# -----------------------------------------------------------------------------
# PHASE A WARNINGS (DISPLAYED IN RESPONSES)
# -----------------------------------------------------------------------------
# Phase A banner (shown in health check, API responses)
PHASE_A_WARNING=⚠️ NON-PRODUCTION ENVIRONMENT — DATA MAY BE DELETED WITHOUT NOTICE

# API version (marked as unstable)
API_VERSION=phase-a-unstable

# =============================================================================
# END OF PHASE A CONFIGURATION
# =============================================================================
```

---

## 🔒 Security Notes

### Secrets to Change

**CRITICAL**: Change these before deployment:

1. **DATABASE_URL**:
   ```bash
   # BAD (example password)
   DATABASE_URL=postgresql+asyncpg://atlas_user:CHANGE_THIS_PASSWORD@localhost:5433/arsaka_puguh

   # GOOD (random password)
   DATABASE_URL=postgresql+asyncpg://atlas_user:K7m3Qp9Xz2Lv8Bn4Wc1Yr6Hf5Gd@localhost:5433/arsaka_puguh
   ```

2. **JWT_SECRET_KEY**:
   ```bash
   # Generate random key
   python -c "import secrets; print(secrets.token_urlsafe(32))"

   # Example output:
   JWT_SECRET_KEY=Xk9Lm3Qp7Bn4Wc2Yr6Hf5Gd8Zv1Ts0Rj
   ```

### Phase A Security Model

**Protection Layers**:
1. **Cloudflare Firewall**: Block all IPs except office/home IPs
2. **IP Whitelisting**: Configure allowed IPs in Cloudflare
3. **JWT Authentication**: Require login for all API access
4. **Single Tenant**: No cross-tenant access (only 1 tenant exists)

**What's NOT Protected** (intentionally):
- ❌ Rate limiting (Cloudflare provides this)
- ❌ Advanced auth (no MFA, no password policies)
- ❌ Audit export (events are logged, but no export API)

**Phase A Threat Model**:
- ✅ Protected: External attackers (IP whitelisted)
- ✅ Protected: Unauthorized access (JWT required)
- ⚠️ NOT Protected: Malicious internal users (trusted environment)
- ⚠️ NOT Protected: DDoS attacks (Cloudflare mitigates, but backend has no rate limiting)

---

## 🔧 Configuration Validation

### Required Variables

**MUST be set** (application won't start without these):
- `DATABASE_URL` - PostgreSQL connection
- `JWT_SECRET_KEY` - JWT signing key (min 32 chars)

### Optional Variables with Defaults

**Can be omitted** (will use defaults):
- `ENVIRONMENT` → defaults to `development`
- `JWT_ALGORITHM` → defaults to `HS256`
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` → defaults to `30`
- `LOG_LEVEL` → defaults to `INFO`
- `POOL_SIZE` → defaults to `10` (Phase A should override to `2`)

### Disabled Features

**MUST be explicitly disabled for Phase A**:
- `REDIS_ENABLED=false` (no caching)
- `RATE_LIMIT_ENABLED=false` (no backend rate limiting)
- `ENABLE_METRICS=false` (no Prometheus)
- `ENABLE_TRACING=false` (no Jaeger)

---

## 🐳 Docker Compose Configuration

### `docker/docker-compose.phase-a.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: atlas-postgres-phase-a
    environment:
      POSTGRES_DB: arsaka_puguh
      POSTGRES_USER: atlas_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}  # From .env
    ports:
      - "5433:5432"
    volumes:
      - postgres_data_phase_a:/var/lib/postgresql/data
      - ../backend/migrations:/docker-entrypoint-initdb.d:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U atlas_user"]
      interval: 10s
      timeout: 5s
      retries: 5
    labels:
      - "com.atlas.phase=A"
      - "com.atlas.warning=NON-PRODUCTION"

  # Backend API
  backend:
    build:
      context: ../backend
      dockerfile: ../docker/Dockerfile.phase-a
    container_name: atlas-backend-phase-a
    env_file:
      - ../backend/.env.phase-a
    environment:
      # Override DATABASE_URL to use container hostname
      DATABASE_URL: postgresql+asyncpg://atlas_user:${DB_PASSWORD}@postgres:5432/arsaka_puguh
    ports:
      - "8001:8001"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    labels:
      - "com.atlas.phase=A"
      - "com.atlas.warning=NON-PRODUCTION"
    restart: unless-stopped

volumes:
  postgres_data_phase_a:
    labels:
      - "com.atlas.phase=A"
      - "com.atlas.warning=DATA-MAY-BE-DELETED"

networks:
  default:
    name: atlas-phase-a-network
```

### `docker/Dockerfile.phase-a`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies (Phase 1 only, no Phase 2 dependencies)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Phase A warning banner
ENV PHASE_A_WARNING="⚠️ NON-PRODUCTION ENVIRONMENT — DATA MAY BE DELETED"

# Run application
CMD ["uvicorn", "core.app:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "debug"]
```

**Note**: Use `core.app:app` (Phase 1 app), NOT `core.app_v2:app` (Phase 2 app)

---

## 🗄️ Database Seed Data

### `backend/migrations/seed_phase_a.sql`

```sql
-- =============================================================================
-- ARSAKA_PUGUH — Phase A Seed Data
-- =============================================================================
-- Purpose: Minimal data for manual testing (1 tenant, 2 users, 2 rules)
-- =============================================================================

-- 1 tenant (hardcoded UUID)
INSERT INTO organizations (id, name, is_active, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'Demo Tenant Phase A', true, NOW())
ON CONFLICT (id) DO NOTHING;

-- 2 users (admin + approver)
-- Password for both: admin123 (bcrypt hash)
INSERT INTO users (id, username, password_hash, organization_id, role, is_active, created_at) VALUES
('user-admin-001', 'admin', '$2b$12$KK.KGcUEcVCSYotdWlLOP.7oHoGtQbdqWUbBVsvf36r2ne56ywwd2',
 '550e8400-e29b-41d4-a716-446655440000', 'admin', true, NOW()),
('user-approver-001', 'approver', '$2b$12$KK.KGcUEcVCSYotdWlLOP.7oHoGtQbdqWUbBVsvf36r2ne56ywwd2',
 '550e8400-e29b-41d4-a716-446655440000', 'approver', true, NOW())
ON CONFLICT (id) DO NOTHING;

-- 2 test rules (purchase approval)
INSERT INTO rules (id, tenant_id, rule_name, decision_type, conditions, action, is_active, created_at) VALUES
('rule-auto-approve-small', '550e8400-e29b-41d4-a716-446655440000',
 'Auto Approve Small Purchases', 'purchase_approval',
 '{"amount": {"$lt": 1000}}', 'APPROVE', true, NOW()),
('rule-auto-reject-large', '550e8400-e29b-41d4-a716-446655440000',
 'Auto Reject Large Purchases', 'purchase_approval',
 '{"amount": {"$gt": 10000}}', 'REJECT', true, NOW())
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- Credentials for Phase A:
-- =============================================================================
-- Username: admin
-- Password: admin123
-- Role: admin (can create decisions)
--
-- Username: approver
-- Password: approver123  -- NOTE: Use admin123 for simplicity (same hash)
-- Role: approver (can approve/reject decisions)
-- =============================================================================
```

**Load seed data**:
```bash
# After docker-compose up
docker exec -i atlas-postgres-phase-a psql -U atlas_user -d arsaka_puguh < backend/migrations/seed_phase_a.sql
```

---

## ✅ Configuration Verification

### Startup Checks

**After starting backend (`docker-compose up`)**, verify:

1. **Health Check**:
   ```bash
   curl http://localhost:8001/health

   # Expected response:
   {
     "status": "healthy",
     "environment": "phase-a-staging",
     "database": "connected",
     "cache": "disabled",  # Redis disabled
     "rate_limiter": "disabled",  # Rate limiting disabled
     "warnings": [
       "⚠️ NON-PRODUCTION ENVIRONMENT — DATA MAY BE DELETED"
     ]
   }
   ```

2. **Logs Check** (verify disabled features):
   ```bash
   docker logs atlas-backend-phase-a 2>&1 | grep -i redis
   # Expected: "Redis disabled" or no Redis connection attempts

   docker logs atlas-backend-phase-a 2>&1 | grep -i "rate limit"
   # Expected: "Rate limiting disabled"

   docker logs atlas-backend-phase-a 2>&1 | grep -i metrics
   # Expected: "Metrics disabled"
   ```

3. **Login Test**:
   ```bash
   curl -X POST http://localhost:8001/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin123"}'

   # Expected response:
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer",
     "user": {
       "user_id": "user-admin-001",
       "username": "admin",
       "role": "admin",
       "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
     },
     "_meta": {
       "api_version": "phase-a-unstable",
       "warning": "⚠️ API response shape is UNSTABLE"
     }
   }
   ```

4. **Database Check**:
   ```bash
   docker exec -it atlas-postgres-phase-a psql -U atlas_user -d arsaka_puguh -c "SELECT username, role FROM users;"

   # Expected:
   #  username | role
   # ----------+---------
   #  admin    | admin
   #  approver | approver
   ```

---

## 🚀 Deployment Checklist

### Pre-Deployment

- [ ] Created `.env.phase-a` with required variables
- [ ] Changed `DATABASE_URL` password (no default password)
- [ ] Changed `JWT_SECRET_KEY` to random 32+ char string
- [ ] Set `REDIS_ENABLED=false`
- [ ] Set `RATE_LIMIT_ENABLED=false`
- [ ] Set `ENABLE_METRICS=false`
- [ ] Set `ENABLE_TRACING=false`
- [ ] Set `POOL_SIZE=2` (minimal)

### Deployment

- [ ] Run `docker-compose -f docker/docker-compose.phase-a.yml up -d`
- [ ] Verify PostgreSQL started (`docker ps` shows `atlas-postgres-phase-a`)
- [ ] Verify backend started (`docker ps` shows `atlas-backend-phase-a`)
- [ ] Load seed data (`psql < migrations/seed_phase_a.sql`)
- [ ] Health check passes (`curl http://localhost:8001/health`)

### Post-Deployment

- [ ] Login test passes (admin credentials work)
- [ ] Create decision test passes (POST /decisions works)
- [ ] Approve workflow test passes (POST /workflows/:id/approve works)
- [ ] Decision list test passes (GET /decisions returns data)
- [ ] Logs show structured JSON format
- [ ] No Redis connection errors in logs
- [ ] No rate limiting errors in logs

---

## 🔄 Configuration Evolution

### Phase A → Phase B Migration

**What Changes**:
```bash
# Phase B: Add monitoring
ENABLE_METRICS=true  # Enable Prometheus metrics
ENABLE_TRACING=false  # Still no tracing (monolithic)

# Phase B: Keep disabled
REDIS_ENABLED=false  # Still no caching (< 10 tenants)
RATE_LIMIT_ENABLED=false  # Cloudflare still sufficient
```

### Phase B → Phase C Migration

**What Changes**:
```bash
# Phase C: Enable caching (when > 10 tenants)
REDIS_ENABLED=true
REDIS_URL=redis://redis:6379

# Phase C: Enable backend rate limiting (public access)
RATE_LIMIT_ENABLED=true

# Phase C: Multi-tenant (remove hardcoded tenant)
ALLOWED_TENANT_IDS=  # Empty = allow all (with database validation)

# Phase C: Increase pool size (more concurrent users)
POOL_SIZE=10
MAX_OVERFLOW=10
```

---

## 📖 Summary

**Phase A Configuration Philosophy**:
> Start with MINIMAL configuration. Add complexity only when MEASURED need arises.

**Disabled for Phase A** (via configuration):
- ❌ Redis caching
- ❌ Backend rate limiting
- ❌ Prometheus metrics
- ❌ Jaeger tracing

**Minimal for Phase A**:
- ✅ Connection pool (size 2, not 20)
- ✅ JWT auth (hardcoded users)
- ✅ Single tenant (hardcoded whitelist)
- ✅ Structured logging (DEBUG level)

**Safe Because**:
- All disabled features have fail-open behavior (system works without them)
- Minimal configuration reduces debugging surface
- Can re-enable features in Phase B/C when needed

**Next Steps**:
1. Create `.env.phase-a` using template above
2. Deploy using `docker-compose.phase-a.yml`
3. Verify health check + login test
4. Proceed with manual flow testing

---

**Document Version**: 1.0
**Last Updated**: 2026-01-08
**Status**: Active (Phase A Reference)
