# ARSAKA_MANTRA Deployment Guide

## Quick Deploy

```bash
# From project root
./scripts/deploy-vps.sh
```

This script automatically:
1. ✅ Syncs code to VPS
2. ✅ Builds Docker image
3. ✅ Sets Consul KV (if missing)
4. ✅ Verifies PostgreSQL is running
5. ✅ Deploys Nomad job
6. ✅ Runs database migrations (if needed)
7. ✅ Verifies health check

## Manual Deploy Steps

If you need to deploy manually, follow these steps **IN ORDER**:

### Step 1: Sync Code
```bash
rsync -avz --exclude '__pycache__' --exclude '.git' \
  ./ARSAKA_MANTRA/ root@31.97.111.175:/root/arsaka-mantra/
```

### Step 2: Build Docker Image (BEFORE nomad job run!)
```bash
ssh root@31.97.111.175 "cd /root/arsaka-mantra/backend && docker build -t arsaka-mantra-api:v1.0.0 ."
```

### Step 3: Set Consul KV (BEFORE nomad job run!)
```bash
ssh root@31.97.111.175 "consul kv put mantra/db_password 'mantra_password'"
```

### Step 4: Verify PostgreSQL is Running
```bash
ssh root@31.97.111.175 "nomad job status -namespace=mantra mantra-postgres"
# Should show: Status = running
```

### Step 5: Deploy Backend
```bash
ssh root@31.97.111.175 "cd /root/arsaka-mantra/nomad && nomad job run -namespace=mantra mantra-backend.nomad"
```

### Step 6: Run Migrations
```bash
# Find postgres container
PG_CONTAINER=$(ssh root@31.97.111.175 "docker ps --format '{{.Names}}' | grep postgres | grep mantra")

# Run migrations
for f in /root/arsaka-mantra/backend/migrations/*.sql; do
  ssh root@31.97.111.175 "docker exec -i $PG_CONTAINER psql -U mantra_owner -d arsaka_mantra < $f"
done
```

### Step 7: Verify
```bash
curl http://31.97.111.175:8002/health
```

## Common Issues

### Issue: "Failed to pull image"
**Cause**: Docker image not built before `nomad job run`
**Fix**: Build image first (Step 2)

### Issue: "Missing: kv.block(mantra/db_password)"
**Cause**: Consul KV not set
**Fix**: Set Consul KV (Step 3)

### Issue: Empty database / No tables
**Cause**: Migrations not run
**Fix**: Run migrations (Step 6)

### Issue: Backend keeps failing (11+ attempts)
**Cause**: Multiple prerequisites missing
**Fix**: Use `./scripts/deploy-vps.sh` which handles everything

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      VPS (31.97.111.175)                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐     ┌─────────────┐                   │
│  │   Consul    │────▶│ mantra/     │                   │
│  │   (KV)      │     │ db_password │                   │
│  └─────────────┘     └─────────────┘                   │
│         │                                               │
│         ▼                                               │
│  ┌─────────────┐                                       │
│  │   Nomad     │                                       │
│  └─────────────┘                                       │
│         │                                               │
│    ┌────┴────┐                                         │
│    ▼         ▼                                         │
│ ┌──────┐  ┌──────────┐                                 │
│ │ PG   │  │ Backend  │◀── arsaka-mantra-api:v1.0.0     │
│ │:5434 │  │ :8002    │    (must be built first!)      │
│ └──────┘  └──────────┘                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Checklist Before Deploy

- [ ] Docker image built on VPS
- [ ] Consul KV `mantra/db_password` set
- [ ] PostgreSQL job running
- [ ] Migrations exist in `/backend/migrations/`
