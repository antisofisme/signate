# Docker Audit - Action Plan

**Date:** 2025-10-28
**Based on:** docker-audit.md
**Priority:** Critical to Nice-to-Have

---

## 🔴 CRITICAL - Fix Immediately (Week 1)

### 1. Add Backend API Health Check
**Impact:** High - Service dependencies rely on health status
**Effort:** Low (5 minutes)

```yaml
# Add to docker/docker-compose.yml under backend-api service
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  start_period: 40s
  retries: 3
```

### 2. Fix Hardcoded Flower Credentials
**Impact:** Critical Security Issue
**Effort:** Low (5 minutes)

```yaml
# Change in docker/docker-compose.yml
# FROM:
command: celery -A app.celery_app flower --port=5555 --basic_auth=admin:admin123

# TO:
command: celery -A app.celery_app flower --port=5555 --basic_auth=${FLOWER_BASIC_AUTH}

# Add to .env:
FLOWER_BASIC_AUTH=admin:strong_password_here
```

### 3. Remove Development Mode from Production
**Impact:** Security Risk - Exposes debug information
**Effort:** Low (5 minutes)

```bash
# Edit: backend/scripts/docker-entrypoint.sh
# Change line 39-43 FROM:
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \          # ⬅️ REMOVE THIS LINE
    --log-level info

# TO:
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level info \
    --workers 4
```

### 4. Close Redis External Port
**Impact:** Critical Security Issue - Exposed database
**Effort:** Low (2 minutes)

```yaml
# In docker/docker-compose.yml, remove or comment:
redis:
  # ports:
  #   - "6379:6379"  # ⬅️ REMOVE THIS - only needed internally
```

### 5. Resolve Missing Anthias Dockerfiles
**Impact:** High - Services won't start
**Effort:** Medium (30 minutes)

**Option A: Remove Anthias (if deprecated)**
```bash
# Comment out or remove anthias-* services from docker/docker-compose.yml
```

**Option B: Restore from backup**
```bash
cd /mnt/g/khoirul/signate/anthias/docker
tar -xzf docker-backup-before-cleanup-20251028-180112.tar.gz
```

---

## 🔴 HIGH PRIORITY - Fix This Week

### 6. Add Resource Limits
**Impact:** Prevents OOM kills and resource starvation
**Effort:** Medium (30 minutes)

```yaml
# Add to each service in docker/docker-compose.yml

postgres:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '2.0'
      reservations:
        memory: 1G

backend-api:
  deploy:
    resources:
      limits:
        memory: 1G
        cpus: '2.0'
      reservations:
        memory: 512M

celery-worker:
  deploy:
    resources:
      limits:
        memory: 4G  # Video processing needs more
        cpus: '4.0'
      reservations:
        memory: 2G

celery-beat:
  deploy:
    resources:
      limits:
        memory: 256M
        cpus: '0.5'

flower:
  deploy:
    resources:
      limits:
        memory: 512M
        cpus: '1.0'

viewer:
  deploy:
    resources:
      limits:
        memory: 256M
        cpus: '1.0'
```

### 7. Configure Logging Driver
**Impact:** Prevents disk space issues from unbounded logs
**Effort:** Low (10 minutes)

```yaml
# Add to docker/docker-compose.yml globally or per service

# Option 1: Global (add at top level)
x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
    labels: "service,environment"

# Then reference in each service:
services:
  postgres:
    logging: *default-logging

# Option 2: Add to each service individually
postgres:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

### 8. Remove PostgreSQL Port Exposure (Production Only)
**Impact:** Security - Database shouldn't be publicly accessible
**Effort:** Low (2 minutes)

```yaml
# In docker/docker-compose.yml
postgres:
  # Comment out for production:
  # ports:
  #   - "5433:5432"  # Only for development/debugging
```

### 9. Add Missing Health Checks
**Effort:** Low (15 minutes)

```yaml
# Add to docker/docker-compose.yml

celery-beat:
  healthcheck:
    test: ["CMD-SHELL", "celery -A app.celery_app status | grep -q 'celery@' || exit 1"]
    interval: 60s
    timeout: 10s
    retries: 3

flower:
  healthcheck:
    test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:5555/"]
    interval: 30s
    timeout: 10s
    retries: 3

# For Anthias services (if kept):
anthias-nginx:
  healthcheck:
    test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost/"]
    interval: 30s
    timeout: 10s
    retries: 3
```

### 10. Create .dockerignore Files
**Effort:** Low (10 minutes)

```bash
# Create: backend/.dockerignore
cat > /mnt/g/khoirul/signate/backend/.dockerignore << 'EOF'
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.env
.env.*
!.env.example
.git/
.gitignore
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
.vscode/
.idea/
*.log
.DS_Store
EOF

# Create: web-admin/.dockerignore
cat > /mnt/g/khoirul/signate/web-admin/.dockerignore << 'EOF'
node_modules/
.git/
.gitignore
.env
.env.*
!.env.example
dist/
build/
.vscode/
.idea/
*.log
.DS_Store
coverage/
EOF
```

---

## 🟡 MEDIUM PRIORITY - Next 2 Weeks

### 11. Consolidate .env.example Files
**Effort:** Low (5 minutes)

```bash
# Remove outdated root .env.example
rm /mnt/g/khoirul/signate/.env.example

# Or replace with pointer:
cat > /mnt/g/khoirul/signate/.env.example << 'EOF'
# DEPRECATED: This file is outdated
# Please use the comprehensive configuration file:
# docker/.env.example (249 lines, fully documented)
#
# Copy command:
# cp docker/.env.example docker/.env
EOF
```

### 12. Add Redis Authentication
**Effort:** Medium (20 minutes)

```yaml
# In docker/docker-compose.yml
redis:
  command: >
    redis-server
    --appendonly yes
    --maxmemory 512mb
    --maxmemory-policy allkeys-lru
    --save 60 1000
    --requirepass ${REDIS_PASSWORD}

# Update all services using Redis:
backend-api:
  environment:
    - REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379

# Add to docker/.env:
REDIS_PASSWORD=your_strong_redis_password_here
```

### 13. Implement Web Admin Production Dockerfile
**Effort:** Medium (1 hour)

```dockerfile
# Create: web-admin/Dockerfile.prod
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
```

### 14. Add Environment-Specific Compose Files
**Effort:** Medium (1 hour)

```bash
# Create: docker/docker-compose.prod.yml
# Production overrides:
# - Remove source code mounts
# - Remove port exposures
# - Add resource limits
# - Disable reload
# - Add production entrypoint

# Usage:
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 15. Automate Database Backups
**Effort:** Medium (30 minutes)

```bash
# Add to docker/docker-compose.yml
db-backup:
  image: postgres:15-alpine
  container_name: signage-db-backup
  environment:
    - POSTGRES_USER=${POSTGRES_USER}
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    - POSTGRES_DB=${POSTGRES_DB}
  volumes:
    - ./backup-database.sh:/backup.sh:ro
    - /backups:/backups
  command: >
    sh -c "
      while true; do
        echo 'Starting backup at $(date)'
        /backup.sh
        sleep 86400
      done
    "
  depends_on:
    postgres:
      condition: service_healthy
  networks:
    - signage-network
  restart: unless-stopped
```

### 16. Update CLAUDE.md
**Effort:** Low (10 minutes)

Add missing services:
```markdown
## Service Ports (ALL ON SERVER)
- **Port 8000**: Anthias (Digital Signage CMS)
- **Port 8001**: Backend API (FastAPI in Docker) ✅ RUNNING
- **Port 3000**: Web Admin (React/Vite Dev Mode) - Run locally
- **Port 5433**: PostgreSQL Database ✅ RUNNING
- **Port 5555**: Flower (Celery Monitoring) ✅ RUNNING  # ⬅️ ADD THIS
- **Port 6379**: Redis (Internal Only) ✅ RUNNING       # ⬅️ ADD THIS
- **Port 8080**: Viewer (Static HTML) ✅ RUNNING
```

---

## 💡 NICE TO HAVE - Next Month

### 17. Add Monitoring Stack (Prometheus + Grafana)
**Effort:** High (4 hours)

```yaml
# Add to docker/docker-compose.yml
prometheus:
  image: prom/prometheus:latest
  container_name: signage-prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - prometheus-data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
  networks:
    - signage-network
  restart: unless-stopped

grafana:
  image: grafana/grafana:latest
  container_name: signage-grafana
  ports:
    - "3001:3000"
  volumes:
    - grafana-data:/var/lib/grafana
    - ./grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
  environment:
    - GF_SECURITY_ADMIN_USER=admin
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
  networks:
    - signage-network
  restart: unless-stopped

volumes:
  prometheus-data:
  grafana-data:
```

### 18. Implement Network Segmentation
**Effort:** Medium (2 hours)

```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

services:
  postgres:
    networks:
      - backend  # Not accessible from outside

  backend-api:
    networks:
      - frontend
      - backend
```

### 19. Add TLS/SSL Support
**Effort:** High (3 hours)

```yaml
# Add reverse proxy with Let's Encrypt
nginx-proxy:
  image: jwilder/nginx-proxy:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - /var/run/docker.sock:/tmp/docker.sock:ro
    - ./certs:/etc/nginx/certs:ro
  networks:
    - frontend

letsencrypt:
  image: jrcs/letsencrypt-nginx-proxy-companion
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - ./certs:/etc/nginx/certs
```

### 20. Add Image Scanning
**Effort:** Medium (1 hour)

```bash
# Add to CI/CD pipeline
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image signage-backend:latest

# Or use Snyk
snyk container test signage-backend:latest
```

---

## Quick Wins (Do First) ⚡

These can be done in under 30 minutes total:

1. ✅ Fix Flower credentials (5 min)
2. ✅ Add backend health check (5 min)
3. ✅ Close Redis port (2 min)
4. ✅ Remove --reload flag (5 min)
5. ✅ Create .dockerignore files (10 min)

**Total time:** ~30 minutes
**Impact:** Fixes 4 critical security issues

---

## Implementation Order

### Day 1 (Critical Fixes - 1 hour)
1. Fix Flower credentials
2. Add backend health check
3. Close Redis external port
4. Remove --reload flag
5. Create .dockerignore files
6. Test deployment

### Day 2 (Resource Management - 2 hours)
1. Add resource limits to all services
2. Configure logging driver
3. Add missing health checks
4. Test resource constraints

### Week 2 (Security Hardening - 4 hours)
1. Add Redis authentication
2. Remove PostgreSQL port exposure (prod)
3. Consolidate .env files
4. Update CLAUDE.md
5. Security audit

### Week 3-4 (Production Readiness - 8 hours)
1. Implement web-admin Dockerfile
2. Create production compose file
3. Automate backups
4. Add monitoring stack
5. Document disaster recovery

---

## Testing Checklist

After each change:

```bash
# 1. Validate compose file
cd /mnt/g/khoirul/signate/docker
docker-compose config

# 2. Build images
docker-compose build --no-cache

# 3. Start services
docker-compose up -d

# 4. Check health
docker-compose ps
docker-compose logs -f

# 5. Test endpoints
curl http://192.168.5.12:8001/health
curl http://192.168.5.12:8080/health

# 6. Check resource usage
docker stats
```

---

## Rollback Plan

If issues occur:

```bash
# 1. Stop services
docker-compose down

# 2. Restore from git
git checkout HEAD -- docker/docker-compose.yml
git checkout HEAD -- backend/scripts/docker-entrypoint.sh

# 3. Restart
docker-compose up -d

# 4. Verify
docker-compose ps
```

---

## Success Metrics

After implementing all critical and high priority items:

- ✅ All services have health checks
- ✅ No hardcoded credentials
- ✅ All services have resource limits
- ✅ Logs rotate automatically
- ✅ No unnecessary ports exposed
- ✅ Production mode enabled
- ✅ Security score > 70%
- ✅ All services start successfully
- ✅ Zero critical vulnerabilities

---

**Created:** 2025-10-28
**Owner:** DevOps Team
**Review:** Weekly until all critical items resolved
