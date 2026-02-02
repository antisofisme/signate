# ARSAKA_PUGUH Phase A — Nomad Deployment Quickstart

**TL;DR**: Deploy ARSAKA_PUGUH ke VPS dengan Nomad dalam 15 menit

---

## 📋 Pre-Flight Checklist

✅ **Server Requirements**:
- [x] VPS dengan Nomad + Consul + Traefik sudah running
- [x] SSH access ke VPS
- [x] Namespace `puguh` sudah dibuat
- [x] Host volume configured: `/opt/nomad/volumes/puguh/postgres`

**Verify** (dari VPS):
```bash
nomad version          # Should show v1.11.1+
consul version         # Should show v1.22.2+
nomad namespace list   # Should show 'puguh'
```

---

## 🚀 Quick Deploy (5 Commands)

### Step 1: Upload Files ke VPS

**Dari Windows** (local machine):
```bash
# Upload Nomad job files + deployment script
scp -r /mnt/f/WINDSURF/neliti_code/signate/ARSAKA_PUGUH/nomad root@31.97.111.175:/root/arsaka-puguh/

# Upload backend code (pilih salah satu):
# Option A: Upload all backend code
scp -r /mnt/f/WINDSURF/neliti_code/signate/ARSAKA_PUGUH/backend root@31.97.111.175:/root/arsaka-puguh/

# Option B: Build Docker image locally, push to registry (recommended)
# (Requires Docker registry setup - see Phase B)
```

---

### Step 2: SSH ke VPS

```bash
ssh root@31.97.111.175
cd /root/arsaka-puguh/nomad
```

---

### Step 3: Deploy All Services

```bash
# Make script executable
chmod +x deploy.sh

# Deploy PostgreSQL + Backend API
./deploy.sh all
```

**What This Does**:
1. ✅ Deploy PostgreSQL (port 5433)
2. ⏳ Wait for PostgreSQL to be healthy
3. ⚠️ **MANUAL**: Prompt you to run migrations (see Step 4)
4. ✅ Deploy Backend API (dynamic port, routed via Traefik)
5. ✅ Register services in Consul
6. ✅ Configure Traefik routing

**Expected Output**:
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
{
  "status": "healthy",
  "environment": "phase-a-staging",
  "database": "connected",
  ...
}
```

---

### Step 4: Run Database Migrations

**Get PostgreSQL container ID**:
```bash
docker ps | grep postgres
# Note the container ID
```

**Run migrations**:
```bash
# Replace <container-id> with actual container ID
CONTAINER_ID=<container-id>

# Copy migration files
docker cp /root/arsaka-puguh/backend/migrations/. $CONTAINER_ID:/tmp/migrations/

# Run all migrations
docker exec -i $CONTAINER_ID psql -U atlas_user -d arsaka_puguh << 'EOF'
\i /tmp/migrations/001_create_organizations.sql
\i /tmp/migrations/002_create_users.sql
\i /tmp/migrations/003_create_decisions.sql
\i /tmp/migrations/004_create_workflows.sql
\i /tmp/migrations/005_create_events.sql
\i /tmp/migrations/006_create_rules.sql
\i /tmp/migrations/007_create_idempotency_keys.sql
EOF

# Load seed data (Phase A: 1 tenant, 2 users, 2 rules)
docker exec -i $CONTAINER_ID psql -U atlas_user -d arsaka_puguh < /root/arsaka-puguh/backend/migrations/seed_phase_a.sql

# Verify tables created
docker exec -i $CONTAINER_ID psql -U atlas_user -d arsaka_puguh -c "\dt"
```

**Expected Output**:
```
 Schema |      Name       | Type  |   Owner
--------+-----------------+-------+------------
 public | decisions       | table | atlas_user
 public | events          | table | atlas_user
 public | idempotency_keys| table | atlas_user
 public | organizations   | table | atlas_user
 public | rules           | table | atlas_user
 public | users           | table | atlas_user
 public | workflows       | table | atlas_user
```

---

### Step 5: Verify Deployment

```bash
# Check status
./deploy.sh status

# Test health endpoint
curl http://127.0.0.1:8001/health | jq

# Test login (should return JWT token)
curl -X POST http://127.0.0.1:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq
```

**Expected**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": "user-admin-001",
    "username": "admin",
    "role": "admin",
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

---

## 🎯 Success Criteria

Phase A deployment **successful** if:

- [x] PostgreSQL running: `nomad job status -namespace=puguh puguh-postgres`
- [x] Backend API running: `nomad job status -namespace=puguh puguh-backend`
- [x] Health check passes: `curl http://127.0.0.1:8001/health`
- [x] Login works: `curl -X POST .../auth/login` returns JWT
- [x] Services registered in Consul: `consul catalog services | grep puguh`
- [x] Traefik routing works: `curl http://31.97.111.175/health` (or domain)

---

## 🛠️ Common Commands

### View Logs

```bash
# Backend logs (follow mode)
./deploy.sh logs backend

# PostgreSQL logs
./deploy.sh logs postgres

# Or manually:
ALLOC_ID=$(nomad job allocs -namespace=puguh puguh-backend | awk 'NR==2{print $1}')
nomad alloc logs -namespace=puguh -f $ALLOC_ID fastapi
```

---

### Restart Services

```bash
# Restart backend (re-deploy)
nomad job stop -namespace=puguh puguh-backend
nomad job run -namespace=puguh backend-api.nomad

# Or use script:
./deploy.sh backend  # Redeploys (updates)
```

---

### Stop All Services

```bash
./deploy.sh stop
```

---

### Database Access

```bash
# Get container ID
docker ps | grep postgres

# Access psql
docker exec -it <container-id> psql -U atlas_user -d arsaka_puguh

# Check users
arsaka_puguh=# SELECT username, role FROM users;
#  username | role
# ----------+---------
#  admin    | admin
#  approver | approver
```

---

## 🚨 Troubleshooting

### Issue: "Namespace 'puguh' not found"

**Fix**:
```bash
nomad namespace apply -description "PUGUH Control Plane" puguh
```

---

### Issue: "Host volume 'puguh_postgres_data' not configured"

**Fix** (on Nomad client):
```bash
# Edit Nomad client config
sudo nano /etc/nomad.d/nomad.hcl

# Add this block:
client {
  host_volume "puguh_postgres_data" {
    path      = "/opt/nomad/volumes/puguh/postgres"
    read_only = false
  }
}

# Create directory
sudo mkdir -p /opt/nomad/volumes/puguh/postgres
sudo chown -R nomad:nomad /opt/nomad/volumes/puguh

# Restart Nomad
sudo systemctl restart nomad
```

---

### Issue: Backend Can't Connect to Database

**Debug**:
```bash
# Check PostgreSQL is running
nomad job status -namespace=puguh puguh-postgres

# Check Consul DNS resolution
dig @127.0.0.1 -p 8600 puguh-postgres.service.consul

# Check logs
./deploy.sh logs backend
```

**Common Fixes**:
- Verify `DATABASE_URL` in backend job file uses Consul DNS
- Check PostgreSQL is accepting connections (not in recovery mode)
- Verify credentials match

---

### Issue: "404 Not Found" from External Access

**Debug**:
```bash
# Check Traefik can see the service
curl http://127.0.0.1:8081/api/http/routers | jq '.[] | select(.name | contains("puguh"))'

# Check service tags
nomad job inspect -namespace=puguh puguh-backend | jq '.Job.TaskGroups[].Tasks[].Services[].Tags'
```

**Fix**:
- Verify `traefik.enable=true` tag is present
- Verify routing rule matches your domain/path
- Check Traefik dashboard: http://31.97.111.175:8081/dashboard/

---

## 📊 Resource Usage (Phase A)

**Current Allocation**:
| Service | CPU | Memory | Disk |
|---------|-----|--------|------|
| PostgreSQL | 500 MHz | 512 MB | 1-2 GB |
| Backend API | 500 MHz | 512 MB | 100 MB |
| **Total** | **1000 MHz** | **1024 MB** | **~2 GB** |

**VPS Capacity**: 2 cores (2000 MHz), 8 GB RAM
**Utilization**: ~50% CPU, ~13% RAM

---

## 🔐 Security Reminders (Phase A)

**⚠️ Current Security Status** (Development/Testing Only):
- ❌ No SSL/TLS (HTTP only)
- ❌ Secrets in job files (plain text)
- ❌ No ACL enabled
- ✅ IP whitelisting (Cloudflare/Traefik)

**Before Production (Phase B)**:
- [ ] Move secrets to Vault
- [ ] Enable SSL/TLS (Let's Encrypt)
- [ ] Enable Nomad/Consul ACL
- [ ] Use HTTPS-only

---

## 🎯 Next Steps

### Immediate (After Deploy):
1. **Manual Testing**:
   - Login with `admin/admin123`
   - Create decision via API
   - Approve workflow
   - Verify audit trail

2. **Frontend Deployment** (Optional):
   - Deploy React frontend (separate Nomad job)
   - Point to backend API via Consul DNS

### Short-Term (Phase B):
- Enable Prometheus metrics
- Add monitoring dashboard (Grafana)
- Enable SSL/TLS via Traefik + Let's Encrypt
- Move secrets to Vault

---

## 📖 Documentation

**Full Guides**:
- **Detailed**: `NOMAD_DEPLOYMENT_PHASE_A.md` - Complete deployment guide
- **Configuration**: `PHASE_A_CONFIGURATION.md` - Environment variables reference
- **CORE vs SCAFFOLD**: `CORE_VS_SCAFFOLD.md` - What's permanent vs temporary
- **Simplification Plan**: `PHASE_A_SIMPLIFICATION_PLAN.md` - What was cut and why
- **Nomad Tutorial**: `/root/tutorial-nomad-stack/` - Nomad stack setup guide

---

## 🆘 Support

**If stuck**:
1. Check logs: `./deploy.sh logs [postgres|backend]`
2. Check status: `./deploy.sh status`
3. Review full guide: `NOMAD_DEPLOYMENT_PHASE_A.md`
4. Check Nomad UI: http://31.97.111.175:4646/ui/jobs?namespace=puguh
5. Check Consul UI: http://31.97.111.175:8500/ui/services

---

**Quick Reference**:
```bash
# Deploy
./deploy.sh all

# Status
./deploy.sh status

# Logs
./deploy.sh logs backend

# Stop
./deploy.sh stop

# Health
curl http://127.0.0.1:8001/health

# Login
curl -X POST http://127.0.0.1:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

---

**Document Version**: 1.0
**Last Updated**: 2026-01-08
**Status**: Ready for Use
