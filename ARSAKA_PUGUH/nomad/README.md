# ARSAKA_PUGUH - Nomad Deployment Files

**Phase A**: Minimal Visible System
**Target**: VPS with Nomad + Consul + Traefik stack

---

## 📦 Files in This Directory

| File | Purpose |
|------|---------|
| `postgres.nomad` | PostgreSQL database job definition |
| `backend-api.nomad` | Backend API (FastAPI) job definition |
| `deploy.sh` | Deployment automation script |
| `README.md` | This file |

---

## 🚀 Quick Start

```bash
# 1. Upload to VPS
scp -r nomad/ root@31.97.111.175:/root/arsaka-puguh/

# 2. SSH to VPS
ssh root@31.97.111.175
cd /root/arsaka-puguh/nomad

# 3. Deploy all services
chmod +x deploy.sh
./deploy.sh all

# 4. Run migrations (manual step - see quickstart guide)
# 5. Verify deployment
./deploy.sh status
```

**Full Guide**: See `../NOMAD_QUICKSTART.md` for complete deployment instructions.

---

## 📋 Job File Reference

### `postgres.nomad`

**Purpose**: Deploy PostgreSQL 15 database

**Key Configuration**:
- **Namespace**: `puguh`
- **Port**: 5433 (static, mapped to container port 5432)
- **Volume**: `puguh_postgres_data` (host volume for persistence)
- **Resources**: 500 MHz CPU, 512 MB RAM
- **Service Name**: `puguh-postgres.service.consul`

**Important Variables** (update before deploy):
```hcl
env {
  POSTGRES_DB       = "arsaka_puguh"
  POSTGRES_USER     = "atlas_user"
  POSTGRES_PASSWORD = "CHANGE_THIS_PASSWORD_PRODUCTION"  # TODO
}
```

**Deploy**:
```bash
nomad job run -namespace=puguh postgres.nomad
```

---

### `backend-api.nomad`

**Purpose**: Deploy FastAPI backend API

**Key Configuration**:
- **Namespace**: `puguh`
- **Port**: Dynamic (Nomad assigns, mapped to container port 8001)
- **Resources**: 500 MHz CPU, 512 MB RAM
- **Service Name**: `puguh-backend.service.consul`
- **Traefik Routing**: Auto-discovered, routed to `api.puguh.arsaka.io`

**Important Variables** (update before deploy):
```hcl
env {
  # Database (uses Consul DNS)
  DATABASE_URL = "postgresql+asyncpg://atlas_user:PASSWORD@puguh-postgres.service.consul:5433/arsaka_puguh"

  # JWT Secret
  JWT_SECRET_KEY = "CHANGE_THIS_TO_RANDOM_32_CHAR_STRING_PRODUCTION"

  # Phase A: Infrastructure DISABLED
  REDIS_ENABLED = "false"
  RATE_LIMIT_ENABLED = "false"
  ENABLE_METRICS = "false"
  ENABLE_TRACING = "false"

  # Phase A: Minimal connection pooling
  POOL_SIZE = "2"
  MAX_OVERFLOW = "3"
}
```

**Deploy**:
```bash
nomad job run -namespace=puguh backend-api.nomad
```

---

### `deploy.sh`

**Purpose**: Automation script for deployment operations

**Usage**:
```bash
./deploy.sh [command]
```

**Commands**:
- `all` - Deploy PostgreSQL + Backend API (recommended for first deploy)
- `postgres` - Deploy PostgreSQL only
- `backend` - Deploy Backend API only
- `status` - Show deployment status
- `logs [job]` - Follow logs (postgres|backend)
- `stop` - Stop all services

**Examples**:
```bash
# First time deployment
./deploy.sh all

# Check status
./deploy.sh status

# Follow backend logs
./deploy.sh logs backend

# Stop all services
./deploy.sh stop
```

---

## 🔧 Configuration Checklist

Before deploying, update these values in job files:

### PostgreSQL (`postgres.nomad`)
- [ ] `POSTGRES_PASSWORD` - Change from default
- [ ] Host volume path configured in Nomad client config

### Backend API (`backend-api.nomad`)
- [ ] `DATABASE_URL` password matches PostgreSQL
- [ ] `JWT_SECRET_KEY` - Generate random 32+ char string
- [ ] `CORS_ORIGINS` - Add your frontend domain
- [ ] Traefik routing rule - Update domain if needed

**Generate JWT Secret**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📊 Resource Requirements

**Per Service**:
| Service | CPU | Memory | Disk |
|---------|-----|--------|------|
| PostgreSQL | 500 MHz | 512 MB | 1-2 GB |
| Backend API | 500 MHz | 512 MB | 100 MB |

**Total**: ~1 GHz CPU, ~1 GB RAM, ~2 GB disk

**VPS Minimum**: 2 cores, 2 GB RAM, 10 GB disk

---

## 🔍 Verification

After deployment, verify:

```bash
# 1. Jobs running
nomad job status -namespace=puguh

# 2. Services registered
consul catalog services | grep puguh

# 3. Health checks
curl http://127.0.0.1:8001/health

# 4. Login test
curl -X POST http://127.0.0.1:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 5. Traefik routing
curl http://31.97.111.175/health  # Via Traefik
```

---

## 🚨 Troubleshooting

### Jobs not starting
```bash
# Check job status
nomad job status -namespace=puguh <job-name>

# Check allocation events
ALLOC_ID=$(nomad job allocs -namespace=puguh <job-name> | awk 'NR==2{print $1}')
nomad alloc status -namespace=puguh $ALLOC_ID

# View logs
nomad alloc logs -namespace=puguh $ALLOC_ID <task-name>
```

### Database connection failed
```bash
# Check PostgreSQL is running
nomad job status -namespace=puguh puguh-postgres

# Check Consul DNS
dig @127.0.0.1 -p 8600 puguh-postgres.service.consul

# Test connection from backend
BACKEND_ALLOC=$(nomad job allocs -namespace=puguh puguh-backend | awk 'NR==2{print $1}')
nomad alloc exec -namespace=puguh $BACKEND_ALLOC \
  psql -h puguh-postgres.service.consul -p 5433 -U atlas_user -d arsaka_puguh
```

### Traefik not routing
```bash
# Check Traefik sees the service
curl http://127.0.0.1:8081/api/http/routers | jq

# Check service tags
nomad job inspect -namespace=puguh puguh-backend | jq '.Job.TaskGroups[].Tasks[].Services[].Tags'

# Traefik dashboard
xdg-open http://31.97.111.175:8081/dashboard/
```

---

## 📖 Documentation

**Quickstart**: `../NOMAD_QUICKSTART.md` - 15-minute deployment guide

**Full Guide**: `../NOMAD_DEPLOYMENT_PHASE_A.md` - Complete deployment documentation

**Configuration**: `../PHASE_A_CONFIGURATION.md` - Environment variables reference

**Architecture**: `../CORE_VS_SCAFFOLD.md` - CORE vs SCAFFOLD components

**Nomad Tutorial**: `/root/tutorial-nomad-stack/` - Nomad stack setup guide

---

## 🎯 Success Criteria

Deployment is successful if:
- [x] Both jobs show "running" status
- [x] Health check returns 200 OK
- [x] Login API returns JWT token
- [x] Services registered in Consul
- [x] Traefik routes external requests correctly

---

## 🔄 Next Steps

**After Phase A Deployment**:
1. Run database migrations (manual step)
2. Test end-to-end flow (login → create → approve → audit)
3. Proceed to Phase B:
   - Enable Prometheus metrics
   - Add monitoring dashboard
   - Enable SSL/TLS via Traefik

---

**Document Version**: 1.0
**Last Updated**: 2026-01-08
**Status**: Ready for Use
