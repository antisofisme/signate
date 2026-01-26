# ATLAS_PUGUH — Nomad Deployment Guide (Phase A)

**Target**: VPS with Nomad + Consul + Traefik stack
**Namespace**: `puguh`
**Phase**: A (Minimal Visible System)
**Date**: 2026-01-08

---

## 🎯 Overview

Deploy ATLAS_PUGUH to **existing Nomad stack** dengan minimal configuration:
- **1 PostgreSQL** database
- **1 Backend API** (FastAPI)
- **Traefik routing** (auto-discovery via Consul)
- **No Redis** (disabled for Phase A)
- **No monitoring** (defer to Phase B)

**Infrastructure**:
- Nomad orchestrator (already running)
- Consul service discovery (already running)
- Traefik reverse proxy (already running in `shared` namespace)
- Docker runtime (already installed)

---

## 📋 Prerequisites

### Server Status (VPS)
✅ Must be running:
- [x] Docker Engine (v29.1.3+)
- [x] Nomad (v1.11.1+) - server + client mode
- [x] Consul (v1.22.2+) - agent mode
- [x] Traefik (v3.2+) - deployed in `shared` namespace

**Verify**:
```bash
# SSH ke VPS
ssh root@31.97.111.175  # atau IP VPS Anda

# Check services
docker --version
nomad version
consul version
nomad job status -namespace=shared traefik
```

**Expected Output**:
```
Docker version 29.1.3
Nomad v1.11.1
Consul v1.22.2
Traefik: running (1/1 allocations)
```

---

### Namespace Setup

**Verify `puguh` namespace exists**:
```bash
nomad namespace list
```

**Expected Output**:
```
Name     Description
default  Default shared namespace
puguh    PUGUH Control Plane services  ✅
semar    SEMAR Console services
pandawa  PANDAWA Suite applications
shared   Shared infrastructure
```

**If namespace doesn't exist**, create it:
```bash
nomad namespace apply \
  -description "PUGUH Control Plane - Decision Engine & Workflow" \
  puguh
```

---

## 📦 Deployment Architecture

### Phase A Components

```
                       Internet
                           │
                    ┌──────▼──────┐
                    │   Traefik   │  (shared namespace)
                    │   Port 80   │
                    └──────┬──────┘
                           │
          ┏━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━┓
          ┃     Nomad Cluster (puguh)       ┃
          ┗━━━━━━━━━━━━━━━━┯━━━━━━━━━━━━━━━┛
                           │
              ┌────────────┴────────────┐
              │                         │
         ┌────▼────┐              ┌────▼────┐
         │ Backend │              │ PostgreSQL │
         │  API    │─────────────▶│ Database │
         │ (8001)  │              │ (5433)   │
         └─────────┘              └──────────┘
              │
              │ (service discovery)
              ▼
         ┌─────────┐
         │ Consul  │
         └─────────┘
```

---

## 🚀 Deployment Steps

### Step 1: Upload Job Files

**From Local** (Windows):
```bash
# Dari folder ATLAS_PUGUH
scp -r nomad/ root@31.97.111.175:/root/atlas-puguh/

# Struktur yang di-upload:
# /root/atlas-puguh/nomad/
# ├── postgres.nomad
# ├── backend-api.nomad
# └── deploy.sh
```

**Or manually create** on VPS:
```bash
# SSH ke VPS
ssh root@31.97.111.175

# Create directory
mkdir -p /root/atlas-puguh/nomad
cd /root/atlas-puguh/nomad
```

---

### Step 2: Deploy PostgreSQL Database

**Deploy**:
```bash
cd /root/atlas-puguh/nomad

# Deploy to puguh namespace
nomad job run -namespace=puguh postgres.nomad
```

**Expected Output**:
```
==> Monitoring evaluation "..."
    Evaluation triggered by job "puguh-postgres"
==> Monitoring allocation "..."
    Allocation "..." created: node "...", group "db"

    Recent Events:
      Task "postgresql" started
```

**Verify**:
```bash
# Check job status
nomad job status -namespace=puguh puguh-postgres

# Check Consul service registration
consul catalog services | grep postgres

# Check logs
ALLOC_ID=$(nomad job allocs -namespace=puguh puguh-postgres | awk 'NR==2{print $1}')
nomad alloc logs -namespace=puguh $ALLOC_ID postgresql
```

**Expected**:
```
# Job status
Status: running (1/1 allocations)

# Consul
puguh-postgres

# Logs
PostgreSQL init process complete; ready for start up.
database system is ready to accept connections
```

---

### Step 3: Run Database Migrations

**Option A: From VPS directly**:
```bash
# Connect to running PostgreSQL container
docker ps | grep postgres
CONTAINER_ID=<postgres-container-id>

# Copy migration files to container
docker cp /root/atlas-puguh/backend/migrations/. $CONTAINER_ID:/tmp/migrations/

# Run migrations
docker exec -i $CONTAINER_ID psql -U atlas_user -d atlas_puguh << 'EOF'
-- Create tables
\i /tmp/migrations/001_create_organizations.sql
\i /tmp/migrations/002_create_users.sql
\i /tmp/migrations/003_create_decisions.sql
\i /tmp/migrations/004_create_workflows.sql
\i /tmp/migrations/005_create_events.sql
\i /tmp/migrations/006_create_rules.sql
\i /tmp/migrations/007_create_idempotency_keys.sql
EOF

# Load seed data (Phase A)
docker exec -i $CONTAINER_ID psql -U atlas_user -d atlas_puguh < /root/atlas-puguh/backend/migrations/seed_phase_a.sql
```

**Option B: Use Nomad exec** (if exec plugin enabled):
```bash
# Get allocation ID
ALLOC_ID=$(nomad job allocs -namespace=puguh puguh-postgres | awk 'NR==2{print $1}')

# Run migrations
nomad alloc exec -namespace=puguh $ALLOC_ID \
  psql -U atlas_user -d atlas_puguh -f /tmp/migrations/001_create_organizations.sql
```

**Verify migrations**:
```bash
# Check tables created
docker exec -i $CONTAINER_ID psql -U atlas_user -d atlas_puguh -c "\dt"

# Expected output:
#  public | decisions
#  public | events
#  public | idempotency_keys
#  public | organizations
#  public | rules
#  public | users
#  public | workflows
```

---

### Step 4: Deploy Backend API

**Deploy**:
```bash
cd /root/atlas-puguh/nomad

# Deploy to puguh namespace
nomad job run -namespace=puguh backend-api.nomad
```

**Expected Output**:
```
==> Monitoring evaluation "..."
    Evaluation triggered by job "puguh-backend"
==> Monitoring allocation "..."
    Allocation "..." created: node "...", group "api"

    Recent Events:
      Task "fastapi" started
      Task "fastapi" healthy
```

**Verify**:
```bash
# Check job status
nomad job status -namespace=puguh puguh-backend

# Check Consul service registration
consul catalog services | grep puguh-backend

# Check logs
ALLOC_ID=$(nomad job allocs -namespace=puguh puguh-backend | awk 'NR==2{print $1}')
nomad alloc logs -namespace=puguh $ALLOC_ID fastapi

# Test health endpoint
curl http://127.0.0.1:8001/health
```

**Expected**:
```json
{
  "status": "healthy",
  "environment": "phase-a-staging",
  "database": "connected",
  "cache": "disabled",
  "rate_limiter": "disabled",
  "warnings": [
    "⚠️ NON-PRODUCTION ENVIRONMENT — DATA MAY BE DELETED"
  ]
}
```

---

### Step 5: Verify Traefik Routing

**Check Traefik discovered the service**:
```bash
# Via Consul
curl http://127.0.0.1:8500/v1/catalog/service/puguh-backend

# Via Traefik API
curl http://127.0.0.1:8081/api/http/routers | jq '.[] | select(.name | contains("puguh"))'
```

**Test external access** (if DNS configured):
```bash
# From local machine
curl https://api-puguh.atlashub.com/health

# Or via IP (if no DNS)
curl http://31.97.111.175/health  # Traefik should route to puguh-backend
```

---

## 🔍 Verification Checklist

### Database Verification

- [ ] PostgreSQL job running (`nomad job status -namespace=puguh puguh-postgres`)
- [ ] Consul service registered (`consul catalog services | grep postgres`)
- [ ] Database accessible (`docker exec ... psql -U atlas_user -d atlas_puguh -c "SELECT 1"`)
- [ ] Tables created (`\dt` shows 7 tables)
- [ ] Seed data loaded (2 users, 1 tenant, 2 rules)

### Backend Verification

- [ ] Backend job running (`nomad job status -namespace=puguh puguh-backend`)
- [ ] Consul service registered (`consul catalog services | grep puguh-backend`)
- [ ] Health check passing (`curl http://127.0.0.1:8001/health`)
- [ ] Can connect to database (health endpoint shows "database": "connected")
- [ ] Traefik routing works (external access via domain/IP)

### End-to-End Verification

- [ ] Login works (`POST /api/v1/auth/login` with admin/admin123)
- [ ] Create decision works (`POST /api/v1/decisions`)
- [ ] Approve workflow works (`POST /api/v1/workflows/:id/approve`)
- [ ] Decision list works (`GET /api/v1/decisions`)
- [ ] Audit trail works (events table has records)

---

## 🛠️ Common Operations

### Viewing Logs

```bash
# Get allocation ID
ALLOC_ID=$(nomad job allocs -namespace=puguh <job-name> | awk 'NR==2{print $1}')

# View logs (follow mode)
nomad alloc logs -namespace=puguh -f $ALLOC_ID <task-name>

# Examples:
nomad alloc logs -namespace=puguh -f $ALLOC_ID postgresql  # Database logs
nomad alloc logs -namespace=puguh -f $ALLOC_ID fastapi     # Backend logs
```

### Restarting Services

```bash
# Restart by stopping and re-running
nomad job stop -namespace=puguh puguh-backend
nomad job run -namespace=puguh backend-api.nomad

# Or use purge (clears allocations)
nomad job stop -namespace=puguh -purge puguh-backend
nomad job run -namespace=puguh backend-api.nomad
```

### Updating Configuration

```bash
# Edit job file
nano /root/atlas-puguh/nomad/backend-api.nomad

# Re-deploy (Nomad will do rolling update)
nomad job run -namespace=puguh backend-api.nomad
```

### Scaling

```bash
# Edit job file: change count
nano /root/atlas-puguh/nomad/backend-api.nomad
# Change: count = 2  (from count = 1)

# Re-deploy
nomad job run -namespace=puguh backend-api.nomad

# Verify
nomad job status -namespace=puguh puguh-backend
# Should show: running (2/2 allocations)
```

---

## 🚨 Troubleshooting

### Issue: Job Fails to Start

**Symptoms**: Job status shows "failed" or "pending"

**Debug**:
```bash
# Check job status
nomad job status -namespace=puguh <job-name>

# Check allocation status
ALLOC_ID=$(nomad job allocs -namespace=puguh <job-name> | awk 'NR==2{print $1}')
nomad alloc status -namespace=puguh $ALLOC_ID

# Check events
nomad alloc status -namespace=puguh $ALLOC_ID | grep -A 20 "Recent Events"

# Check logs
nomad alloc logs -namespace=puguh $ALLOC_ID <task-name>
```

**Common Issues**:
- **Port conflict**: Static port already in use (change to dynamic port)
- **Docker image pull failed**: Check internet connectivity
- **Volume mount failed**: Check host volume is configured in Nomad client
- **Resource constraints**: Not enough CPU/memory (reduce resources in job file)

---

### Issue: Database Connection Failed

**Symptoms**: Backend health check shows "database": "disconnected"

**Debug**:
```bash
# Check PostgreSQL is running
nomad job status -namespace=puguh puguh-postgres

# Check PostgreSQL logs
ALLOC_ID=$(nomad job allocs -namespace=puguh puguh-postgres | awk 'NR==2{print $1}')
nomad alloc logs -namespace=puguh $ALLOC_ID postgresql

# Check Consul service discovery
consul catalog service puguh-postgres

# Test connection from backend container
BACKEND_ALLOC=$(nomad job allocs -namespace=puguh puguh-backend | awk 'NR==2{print $1}')
nomad alloc exec -namespace=puguh $BACKEND_ALLOC \
  psql -h puguh-postgres.service.consul -p 5433 -U atlas_user -d atlas_puguh -c "SELECT 1"
```

**Solution**:
- Verify `DATABASE_URL` in backend job file uses Consul DNS: `puguh-postgres.service.consul:5433`
- Check PostgreSQL is accepting connections (not in recovery mode)
- Verify credentials match between job files

---

### Issue: Traefik Not Routing

**Symptoms**: External access returns 404 or "Service Unavailable"

**Debug**:
```bash
# Check Traefik can see the service
curl http://127.0.0.1:8081/api/http/routers | jq

# Check Consul service registration
consul catalog service puguh-backend

# Check Traefik tags on service
nomad job inspect -namespace=puguh puguh-backend | jq '.Job.TaskGroups[].Tasks[].Services[].Tags'
```

**Solution**:
- Verify `traefik.enable=true` tag is present
- Verify `traefik.http.routers.<name>.rule=Host(...)` tag is correct
- Check Traefik dashboard: http://31.97.111.175:8081/dashboard/
- Verify DNS points to VPS IP (or use IP directly for testing)

---

## 📊 Resource Monitoring

### Current Allocations

```bash
# View all jobs in puguh namespace
nomad job status -namespace=puguh

# View resource usage
nomad node status -verbose

# View allocation details
nomad alloc status -namespace=puguh <alloc-id>
```

### Expected Resource Usage (Phase A)

| Service | CPU (MHz) | Memory (MB) | Disk (GB) |
|---------|-----------|-------------|-----------|
| PostgreSQL | 500 | 512 | 1-2 |
| Backend API | 200 | 256 | 0.1 |
| **Total** | **700** | **768** | **~2** |

**VPS Capacity**: 2 CPU cores (2000 MHz), 8 GB RAM → **35% CPU, 10% RAM utilized**

---

## 🔐 Security Notes (Phase A)

### Current Security Status

**⚠️ Phase A Security Model** (Internal Testing Only):
- ❌ No SSL/TLS (HTTP only)
- ❌ Database password in job file (plain text)
- ❌ JWT secret in job file (plain text)
- ❌ No ACL enabled (Nomad/Consul)
- ✅ IP whitelisting at Cloudflare/Traefik level (external only)
- ✅ Consul service discovery (internal DNS)

**For Production (Phase B/C)**:
- [ ] Use Vault for secrets management
- [ ] Enable SSL/TLS with Let's Encrypt
- [ ] Enable Nomad ACL with namespace policies
- [ ] Enable Consul ACL
- [ ] Encrypt inter-service communication (Consul Connect)
- [ ] Use HTTPS-only (disable HTTP)

---

## 🎯 Success Criteria

Phase A deployment is successful if:

### Deployment

- [x] PostgreSQL running and healthy
- [x] Backend API running and healthy
- [x] Both services registered in Consul
- [x] Traefik routing works (external access)

### Functionality

- [x] Login works (admin/approver credentials)
- [x] Create decision works (POST /decisions)
- [x] Approve workflow works (POST /workflows/:id/approve)
- [x] Decision list works (GET /decisions)
- [x] Audit trail works (events table populated)

### Observability

- [x] Logs accessible via `nomad alloc logs`
- [x] Health checks passing (Consul + Nomad)
- [x] Services discoverable via Consul DNS

---

## 🔄 Phase A → Phase B Transition

### What Changes in Phase B

**Infrastructure**:
- Enable Prometheus metrics (`ENABLE_METRICS=true`)
- Add monitoring dashboard (Grafana)
- Add centralized logging (Loki)

**Security**:
- Enable SSL/TLS (Let's Encrypt via Traefik)
- Move secrets to Vault
- Enable Nomad ACL

**Still Disabled** (defer to Phase C):
- Redis caching (`REDIS_ENABLED=false`)
- Backend rate limiting (`RATE_LIMIT_ENABLED=false`)

---

## 📖 Related Documentation

1. **Phase A Configuration**: `PHASE_A_CONFIGURATION.md`
2. **CORE vs SCAFFOLD**: `CORE_VS_SCAFFOLD.md`
3. **Simplification Plan**: `PHASE_A_SIMPLIFICATION_PLAN.md`
4. **Nomad Tutorial**: `/root/tutorial-nomad-stack/`
5. **ATLASHUB Setup**: `/root/tutorial-nomad-stack/ATLASHUB_SETUP_COMPLETE.md`

---

## 📞 Quick Reference

### Essential Commands

```bash
# Deploy
nomad job run -namespace=puguh <job-file>.nomad

# Status
nomad job status -namespace=puguh <job-name>

# Logs
ALLOC_ID=$(nomad job allocs -namespace=puguh <job-name> | awk 'NR==2{print $1}')
nomad alloc logs -namespace=puguh -f $ALLOC_ID <task-name>

# Stop
nomad job stop -namespace=puguh <job-name>

# Restart (re-deploy)
nomad job stop -namespace=puguh <job-name>
nomad job run -namespace=puguh <job-file>.nomad

# Health Check
curl http://127.0.0.1:8001/health

# Database Access
docker exec -it <postgres-container-id> psql -U atlas_user -d atlas_puguh
```

---

**Document Version**: 1.0
**Last Updated**: 2026-01-08
**Status**: Ready for Deployment
**Next**: Create Nomad job files (`postgres.nomad`, `backend-api.nomad`)
