# ARSAKA_PUGUH Phase A - Deployment Checklist

**Target**: VPS Production Server (31.97.111.175)
**Environment**: Phase A (Visibility & Debugging)
**Deployment Method**: Nomad + Consul + Traefik

---

## ✅ Pre-Deployment Checklist

### 1. Generate Secrets (MANDATORY)

**Generate JWT Secret** (32+ characters):
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Output: `_______________________________________`

**Generate PostgreSQL Password** (24+ characters):
```bash
python -c "import secrets; print(secrets.token_urlsafe(24))"
```
Output: `_______________________________`

### 2. Update Configuration Files

**Local Configuration** (`backend/.env`):
- [ ] Copy `.env.example` to `.env`
- [ ] Update `DATABASE_URL` with PostgreSQL password
- [ ] Update `JWT_SECRET_KEY` with generated secret
- [ ] Update `CORS_ORIGINS` with frontend domain (if different)
- [ ] Verify `ALLOWED_TENANT_IDS` matches seed data

**Nomad Job Files**:
- [ ] Update `nomad/postgres.nomad` → `POSTGRES_PASSWORD` (line 80)
- [ ] Update `nomad/backend-api.nomad` → `DATABASE_URL` password (line 105)
- [ ] Update `nomad/backend-api.nomad` → `JWT_SECRET_KEY` (line 108)
- [ ] Update `nomad/backend-api.nomad` → `CORS_ORIGINS` if needed (line 137)

### 3. Verify Backend Code

**Run Verification Script**:
```bash
cd backend
./verify_phase_a.sh
```

Expected output: `✅ All checks passed!`

**Check File Count**:
```bash
# Expected files
ls -1 backend/.env.example
ls -1 backend/requirements-phase-a.txt
ls -1 backend/Dockerfile
ls -1 backend/.dockerignore
ls -1 backend/verify_phase_a.sh
ls -1 backend/migrations/seed_phase_a.sql
ls -1 backend/migrations/run_migrations.sh
```

All files should exist ✅

### 4. VPS Prerequisites

**SSH to VPS** and verify:
```bash
ssh root@31.97.111.175
```

- [ ] Nomad installed: `nomad version` (v1.11.1+)
- [ ] Consul installed: `consul version` (v1.22.2+)
- [ ] Traefik running: `systemctl status traefik` or Docker check
- [ ] Namespace created: `nomad namespace list | grep puguh`
- [ ] Host volume configured: `ls -la /opt/nomad/volumes/puguh/postgres`

**Create namespace** (if not exists):
```bash
nomad namespace apply -description "PUGUH Control Plane" puguh
```

**Create host volume** (if not exists):
```bash
sudo mkdir -p /opt/nomad/volumes/puguh/postgres
sudo chown -R nomad:nomad /opt/nomad/volumes/puguh
```

**Verify Nomad client config** has host volume:
```bash
sudo nano /etc/nomad.d/nomad.hcl

# Should contain:
client {
  host_volume "puguh_postgres_data" {
    path      = "/opt/nomad/volumes/puguh/postgres"
    read_only = false
  }
}
```

If modified, restart Nomad:
```bash
sudo systemctl restart nomad
```

---

## 🚀 Deployment Steps

### Step 1: Upload Files to VPS

**Option A: Automated** (recommended):
```bash
cd nomad
./upload_to_vps.sh 31.97.111.175 root
```

**Option B: Manual**:
```bash
# From local machine
scp -r backend/ root@31.97.111.175:/root/arsaka-puguh/
scp -r nomad/ root@31.97.111.175:/root/arsaka-puguh/
```

**Verify upload**:
```bash
ssh root@31.97.111.175 "ls -la /root/arsaka-puguh/"
```

Expected: `backend/` and `nomad/` directories

---

### Step 2: Configure Secrets on VPS

**SSH to VPS**:
```bash
ssh root@31.97.111.175
cd /root/arsaka-puguh
```

**Update backend .env**:
```bash
cd backend
cp .env.example .env
nano .env

# Update these lines:
# DATABASE_URL=postgresql+asyncpg://atlas_user:YOUR_POSTGRES_PASSWORD@puguh-postgres.service.consul:5433/arsaka_puguh
# JWT_SECRET_KEY=YOUR_JWT_SECRET
```

**Update Nomad job files**:
```bash
cd ../nomad

# PostgreSQL password
nano postgres.nomad
# Line 80: POSTGRES_PASSWORD = "YOUR_POSTGRES_PASSWORD"

# Backend configuration
nano backend-api.nomad
# Line 105: DATABASE_URL = "postgresql+asyncpg://atlas_user:YOUR_POSTGRES_PASSWORD@..."
# Line 108: JWT_SECRET_KEY = "YOUR_JWT_SECRET"
```

---

### Step 3: Deploy to Nomad

**Make deployment script executable**:
```bash
chmod +x deploy.sh
```

**Deploy all services**:
```bash
./deploy.sh all
```

**Expected output**:
```
[INFO] Checking prerequisites...
[INFO] Prerequisites OK
[INFO] Deploying PostgreSQL database...
==> Monitoring evaluation "..."
    Evaluation triggered by job "puguh-postgres"
[INFO] PostgreSQL is running!
[WARN] ⚠️  MANUAL STEP: Run migrations manually
[INFO] Deploying Backend API...
[INFO] Backend API is running!
[INFO] ✓ Health check passed!
```

---

### Step 4: Run Database Migrations

**Get PostgreSQL container ID**:
```bash
docker ps | grep postgres
```

Output: `<container-id>  postgres:15-alpine  ...`

**Copy migration files to container**:
```bash
CONTAINER_ID=<your-container-id>

docker cp /root/arsaka-puguh/backend/migrations/001_initial_schema.sql $CONTAINER_ID:/tmp/
docker cp /root/arsaka-puguh/backend/migrations/002_immutability_triggers.sql $CONTAINER_ID:/tmp/
docker cp /root/arsaka-puguh/backend/migrations/003_rls_policies.sql $CONTAINER_ID:/tmp/
docker cp /root/arsaka-puguh/backend/migrations/seed_phase_a.sql $CONTAINER_ID:/tmp/
```

**Run migrations**:
```bash
docker exec -i $CONTAINER_ID psql -U atlas_user -d arsaka_puguh -f /tmp/001_initial_schema.sql
docker exec -i $CONTAINER_ID psql -U atlas_user -d arsaka_puguh -f /tmp/002_immutability_triggers.sql
docker exec -i $CONTAINER_ID psql -U atlas_user -d arsaka_puguh -f /tmp/003_rls_policies.sql
docker exec -i $CONTAINER_ID psql -U atlas_user -d arsaka_puguh -f /tmp/seed_phase_a.sql
```

**Verify tables created**:
```bash
docker exec -i $CONTAINER_ID psql -U atlas_user -d arsaka_puguh -c "\dt"
```

Expected: 8 tables (decisions, workflows, workflow_transitions, rules, event_log, operations_audit, idempotency_cache, schema_migrations)

**Verify seed data**:
```bash
docker exec -i $CONTAINER_ID psql -U atlas_user -d arsaka_puguh -c "SELECT COUNT(*) FROM rules;"
```

Expected: 4 rules

---

### Step 5: Verify Deployment

**Check Nomad job status**:
```bash
./deploy.sh status
```

Expected:
- `puguh-postgres`: running (1/1)
- `puguh-backend`: running (1/1)

**Check Consul services**:
```bash
consul catalog services | grep puguh
```

Expected:
- `puguh-postgres`
- `puguh-backend`

**Test health endpoint** (direct):
```bash
curl http://127.0.0.1:8001/health
```

Expected:
```json
{
  "service": "core",
  "status": "healthy",
  "version": "1.0.0-phase-a",
  "environment": "phase-a-staging",
  ...
}
```

**Test health endpoint** (via Traefik):
```bash
curl http://31.97.111.175/health
```

Expected: Same JSON response

**Test API documentation**:
```bash
curl http://127.0.0.1:8001/api/docs
```

Expected: HTML page (Swagger UI)

---

## ✅ Post-Deployment Verification

### Functional Tests

**1. Health Check**:
```bash
curl http://127.0.0.1:8001/health | jq
```
- [ ] Status: "healthy"
- [ ] Environment: "phase-a-staging"
- [ ] Infrastructure.redis: false
- [ ] Infrastructure.rate_limiting: false
- [ ] Pool.size: 2
- [ ] Warning message present

**2. API Documentation**:
```bash
curl -I http://127.0.0.1:8001/api/docs
```
- [ ] HTTP 200 OK
- [ ] Content-Type: text/html

**3. Database Connection**:
```bash
docker exec <postgres-container-id> psql -U atlas_user -d arsaka_puguh -c "SELECT 1;"
```
- [ ] Returns: 1

**4. Seed Data Verification**:
```bash
# Rules
docker exec <postgres-container-id> psql -U atlas_user -d arsaka_puguh -c "SELECT rule_name FROM rules WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000';"

# Decisions
docker exec <postgres-container-id> psql -U atlas_user -d arsaka_puguh -c "SELECT decision_type, outcome FROM decisions WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000';"

# Workflows
docker exec <postgres-container-id> psql -U atlas_user -d arsaka_puguh -c "SELECT current_state FROM workflows WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000';"
```
- [ ] 4 rules present
- [ ] 2 decisions present
- [ ] 1 workflow (PENDING_APPROVAL)

### Infrastructure Tests

**5. Service Discovery** (Consul DNS):
```bash
dig @127.0.0.1 -p 8600 puguh-postgres.service.consul
dig @127.0.0.1 -p 8600 puguh-backend.service.consul
```
- [ ] Both resolve to IP addresses

**6. Traefik Routing**:
```bash
curl http://127.0.0.1:8081/api/http/routers | jq '.[] | select(.name | contains("puguh"))'
```
- [ ] Router exists for `puguh-backend`
- [ ] Rule matches configured domain/path

**7. Logs**:
```bash
./deploy.sh logs backend
```
- [ ] Logs show: "ARSAKA_PUGUH Core Service started successfully"
- [ ] No error messages
- [ ] Pool size logged as 2

---

## 🚨 Troubleshooting

### Issue: Namespace not found

**Fix**:
```bash
nomad namespace apply -description "PUGUH Control Plane" puguh
```

### Issue: Host volume not configured

**Fix**:
```bash
sudo nano /etc/nomad.d/nomad.hcl
# Add host_volume block
sudo systemctl restart nomad
```

### Issue: Backend can't connect to database

**Debug**:
```bash
# Check PostgreSQL running
nomad job status -namespace=puguh puguh-postgres

# Check Consul DNS
dig @127.0.0.1 -p 8600 puguh-postgres.service.consul

# Check backend logs
./deploy.sh logs backend
```

### Issue: Traefik not routing

**Debug**:
```bash
# Check service tags
nomad job inspect -namespace=puguh puguh-backend | jq '.Job.TaskGroups[].Tasks[].Services[].Tags'

# Check Traefik routers
curl http://127.0.0.1:8081/api/http/routers | jq
```

**Full Troubleshooting**: See `NOMAD_QUICKSTART.md` § Troubleshooting

---

## 📊 Success Criteria

Deployment is successful if ALL criteria met:

**Infrastructure**:
- [x] PostgreSQL running (Nomad job status)
- [x] Backend API running (Nomad job status)
- [x] Services registered in Consul
- [x] Traefik routing works

**Functionality**:
- [x] Health endpoint returns 200 OK
- [x] API docs accessible
- [x] 4 rules loaded in database
- [x] 2 decisions + 1 workflow in seed data

**Configuration**:
- [x] Pool size = 2 (from health endpoint)
- [x] Infrastructure features disabled (redis=false, metrics=false)
- [x] Phase A warning visible

**End-to-End** (Optional - requires JWT token):
- [ ] Can create decision via API
- [ ] Decision auto-approved if < $100
- [ ] Decision requires approval if $100-$1000
- [ ] Workflow transitions work

---

## 📖 Documentation Reference

**Quickstart**: `NOMAD_QUICKSTART.md` - 15-minute deployment
**Complete Guide**: `NOMAD_DEPLOYMENT_PHASE_A.md` - Step-by-step
**Configuration**: `PHASE_A_CONFIGURATION.md` - .env reference
**Backend**: `backend/README.md` - Backend usage
**Job Files**: `nomad/README.md` - Nomad reference

---

## 🔄 Rollback Procedure

If deployment fails:

**Stop all services**:
```bash
./deploy.sh stop
```

**Remove data** (if needed):
```bash
# WARNING: Deletes all data!
docker volume rm puguh_postgres_data
```

**Redeploy**:
```bash
./deploy.sh all
```

---

## 📞 Support

**If stuck**:
1. Check logs: `./deploy.sh logs [postgres|backend]`
2. Check status: `./deploy.sh status`
3. Review troubleshooting section above
4. Check Nomad UI: http://31.97.111.175:4646/ui/jobs?namespace=puguh
5. Check Consul UI: http://31.97.111.175:8500/ui/services

---

**Document Version**: 1.0
**Last Updated**: 2026-01-09
**Status**: Ready for Deployment
