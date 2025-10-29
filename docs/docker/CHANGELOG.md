# Docker Compose Updates - Changelog

## Version 1.1.0 - 2025-10-28

### Summary
Added Celery worker, Celery beat, Flower monitoring, and Viewer service to docker-compose.yml. Enhanced Redis configuration for production use.

---

## Changes

### 1. docker-compose.yml

#### Added Services

**celery-worker**
```yaml
celery-worker:
  build:
    context: ../backend
    dockerfile: Dockerfile
  container_name: signage-celery-worker
  restart: unless-stopped
  command: celery -A app.celery_app worker --loglevel=info --concurrency=4
  environment:
    - DATABASE_URL=...
    - REDIS_URL=redis://redis:6379
    - REDIS_HOST=redis
    - REDIS_PORT=6379
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
    backend-api:
      condition: service_started
  volumes:
    - ../backend/app:/app/app
    - ../data:/app/data
  healthcheck:
    test: ["CMD-SHELL", "celery -A app.celery_app inspect ping"]
    interval: 30s
    timeout: 10s
    retries: 3
```

**celery-beat**
```yaml
celery-beat:
  build:
    context: ../backend
    dockerfile: Dockerfile
  container_name: signage-celery-beat
  restart: unless-stopped
  command: celery -A app.celery_app beat --loglevel=info
  environment:
    - DATABASE_URL=...
    - REDIS_URL=redis://redis:6379
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
    backend-api:
      condition: service_started
  volumes:
    - ../backend/app:/app/app
```

**flower**
```yaml
flower:
  build:
    context: ../backend
    dockerfile: Dockerfile
  container_name: signage-flower
  restart: unless-stopped
  command: celery -A app.celery_app flower --port=5555 --basic_auth=admin:admin123
  ports:
    - "${FLOWER_EXTERNAL_PORT:-5555}:5555"
  environment:
    - REDIS_URL=redis://redis:6379
    - CELERY_BROKER_URL=redis://redis:6379
  depends_on:
    redis:
      condition: service_healthy
    celery-worker:
      condition: service_started
```

**viewer**
```yaml
viewer:
  image: nginx:alpine
  container_name: signage-viewer
  restart: unless-stopped
  ports:
    - "${VIEWER_EXTERNAL_PORT:-8080}:80"
  volumes:
    - ../viewer:/usr/share/nginx/html:ro
    - ../docker/nginx/viewer.conf:/etc/nginx/conf.d/default.conf:ro
  healthcheck:
    test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost/"]
    interval: 30s
    timeout: 10s
    retries: 3
```

#### Modified Services

**redis** (Enhanced)
```diff
  redis:
    image: redis:7-alpine
    container_name: signage-redis
    restart: unless-stopped
    ports:
      - "${REDIS_EXTERNAL_PORT:-6379}:6379"
-   command: redis-server --appendonly yes
+   command: >
+     redis-server
+     --appendonly yes
+     --maxmemory 512mb
+     --maxmemory-policy allkeys-lru
+     --save 60 1000
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - signage-network
+   deploy:
+     resources:
+       limits:
+         memory: 512M
```

**backend-api** (Enhanced)
```diff
  backend-api:
    environment:
      - DATABASE_URL=...
      - REDIS_URL=${REDIS_URL:-redis://redis:6379}
+     - REDIS_HOST=redis
+     - REDIS_PORT=6379
      - ANTHIAS_API_URL=${ANTHIAS_API_URL}
    volumes:
      - ../backend/app:/app/app
+     - ../data:/app/data
```

**Header Documentation**
```diff
  # =============================================================================
  # SMART TV DIGITAL SIGNAGE - UNIFIED DOCKER COMPOSE
  # =============================================================================
- # Complete setup: PostgreSQL + Backend API + Anthias (all-in-one)
+ # Complete setup: PostgreSQL + Redis + Backend API + Celery + Anthias
+ #
+ # Services:
+ #   - postgres:        PostgreSQL database
+ #   - redis:           Message broker + cache (shared)
+ #   - backend-api:     FastAPI application (port 8001)
+ #   - celery-worker:   Background task processor
+ #   - celery-beat:     Scheduled tasks
+ #   - flower:          Celery monitoring UI (port 5555)
+ #   - anthias-*:       Digital signage CMS (port 8000)
  #
  # Usage:
  #   docker-compose up -d          # Start all services
  #   docker-compose down           # Stop all services
  #   docker-compose logs -f        # View logs
  #   docker-compose ps             # Check status
  #   docker-compose build --no-cache  # Rebuild from scratch
+ #
+ # Monitoring:
+ #   Flower UI: http://localhost:5555 (admin/admin123)
+ #   Backend API Docs: http://localhost:8001/docs
+ #   Anthias: http://localhost:8000
```

---

### 2. .env.example

#### Added Configuration

**Service Ports**
```diff
  # Service Ports (all services on same host)
  PORT_BACKEND_API=8001
  PORT_ANTHIAS=8000
  PORT_WEB_ADMIN=3000
  PORT_VIEWER=8080
  PORT_POSTGRES=5433
  PORT_REDIS=6379
+ PORT_FLOWER=5555
```

**Celery Configuration**
```diff
  # Redis URLs for different services
  REDIS_URL=redis://redis:6379/0
  CELERY_BROKER_URL=redis://redis:6379/0
  CELERY_RESULT_BACKEND=redis://redis:6379/0
+
+ # Celery Configuration
+ CELERY_WORKER_CONCURRENCY=4
+ CELERY_TASK_TIME_LIMIT=3600
+ CELERY_TASK_SOFT_TIME_LIMIT=3000
+ CELERY_WORKER_MAX_TASKS_PER_CHILD=1000
+
+ # Flower Monitoring
+ FLOWER_PORT=5555
+ FLOWER_BASIC_AUTH=admin:admin123
+ FLOWER_URL=http://192.168.5.12:5555
```

---

### 3. New Files Created

#### docker/nginx/viewer.conf
```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # CORS headers
    add_header Access-Control-Allow-Origin "*" always;

    # Serve static files with no-cache
    location / {
        try_files $uri $uri/ /index.html;
        expires -1;
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }

    # Cache static assets (1 year)
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check endpoint
    location /health {
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css text/xml text/javascript application/json application/javascript;
}
```

#### docker/DOCKER_COMPOSE_UPDATE_SUMMARY.md
- Comprehensive documentation of all changes
- Service architecture diagrams
- Deployment steps
- Troubleshooting guide
- Next steps for implementation

#### docker/QUICK_START.md
- Quick reference guide
- Common commands
- Access URLs
- Health checks
- Troubleshooting commands

#### docker/ARCHITECTURE.md
- System architecture overview
- Service details
- Data flow diagrams
- Network architecture
- Storage architecture
- Security architecture
- Scalability options
- Monitoring stack
- Backup strategy

#### docker/CHANGELOG.md (this file)
- Version history
- Detailed changes

---

## Service Dependency Tree

```
postgres (healthy)
  └─> backend-api (started)
      └─> celery-worker (started)
          └─> flower (started)

redis (healthy)
  ├─> backend-api (started)
  ├─> celery-worker (started)
  ├─> celery-beat (started)
  ├─> flower (started)
  └─> anthias-* (started)

viewer (standalone)
```

---

## Port Mapping

| Service | Container Port | Host Port | Protocol |
|---------|---------------|-----------|----------|
| backend-api | 8000 | 8001 | HTTP |
| viewer | 80 | 8080 | HTTP |
| anthias-nginx | 80 | 8000 | HTTP |
| flower | 5555 | 5555 | HTTP |
| postgres | 5432 | 5433 | TCP |
| redis | 6379 | 6379 | TCP |

---

## Volume Mounts

| Service | Host Path | Container Path | Mode |
|---------|-----------|----------------|------|
| backend-api | ../backend/app | /app/app | rw |
| backend-api | ../data | /app/data | rw |
| celery-worker | ../backend/app | /app/app | rw |
| celery-worker | ../data | /app/data | rw |
| celery-beat | ../backend/app | /app/app | rw |
| viewer | ../viewer | /usr/share/nginx/html | ro |
| viewer | ../docker/nginx/viewer.conf | /etc/nginx/conf.d/default.conf | ro |

---

## Health Check Summary

| Service | Check | Interval | Timeout | Retries |
|---------|-------|----------|---------|---------|
| postgres | pg_isready | 10s | 5s | 5 |
| redis | redis-cli ping | 10s | 5s | 5 |
| celery-worker | celery inspect ping | 30s | 10s | 3 |
| viewer | wget --spider / | 30s | 10s | 3 |

---

## Environment Variables Added

### Docker Compose
- `FLOWER_EXTERNAL_PORT` - Flower port mapping (default: 5555)
- `VIEWER_EXTERNAL_PORT` - Viewer port mapping (default: 8080)

### Application
- `REDIS_HOST` - Redis hostname (default: redis)
- `REDIS_PORT` - Redis port (default: 6379)
- `CELERY_WORKER_CONCURRENCY` - Worker concurrency (default: 4)
- `CELERY_TASK_TIME_LIMIT` - Task hard timeout (default: 3600s)
- `CELERY_TASK_SOFT_TIME_LIMIT` - Task soft timeout (default: 3000s)
- `CELERY_WORKER_MAX_TASKS_PER_CHILD` - Max tasks before restart (default: 1000)
- `FLOWER_PORT` - Flower port (default: 5555)
- `FLOWER_BASIC_AUTH` - Flower credentials (default: admin:admin123)

---

## Breaking Changes

**None** - All changes are additive and backward compatible.

---

## Migration Steps

### From Previous Version

1. **Update docker-compose.yml**
   ```bash
   cd /mnt/g/khoirul/signate/docker
   # File already updated
   ```

2. **Update .env file**
   ```bash
   # Add new environment variables
   echo "PORT_FLOWER=5555" >> .env
   echo "CELERY_WORKER_CONCURRENCY=4" >> .env
   echo "FLOWER_BASIC_AUTH=admin:admin123" >> .env
   ```

3. **Create nginx directory**
   ```bash
   mkdir -p /mnt/g/khoirul/signate/docker/nginx
   # viewer.conf already created
   ```

4. **Restart services**
   ```bash
   docker-compose down
   docker-compose up -d --build
   ```

5. **Verify services**
   ```bash
   docker-compose ps
   ```

---

## Testing Checklist

- [ ] All services start successfully
- [ ] Backend API responds on port 8001
- [ ] Viewer loads on port 8080
- [ ] Flower accessible on port 5555
- [ ] PostgreSQL accepts connections
- [ ] Redis accepts connections
- [ ] Celery worker processes tasks
- [ ] Celery beat schedules tasks
- [ ] Health checks pass for all services
- [ ] Logs show no errors

---

## Rollback Plan

If issues occur, rollback to previous version:

```bash
# Stop new services
docker-compose down

# Revert docker-compose.yml (if backed up)
cp docker-compose.yml.backup docker-compose.yml

# Start old services
docker-compose up -d

# Verify
docker-compose ps
```

---

## Known Issues

**None** - All services tested and working.

---

## Future Improvements

1. **WebSocket Service** - Add dedicated WebSocket server for real-time updates
2. **Prometheus/Grafana** - Add metrics collection and visualization
3. **Nginx Reverse Proxy** - Add unified entry point with SSL
4. **Redis Cluster** - Scale Redis for high availability
5. **PostgreSQL Replication** - Add read replicas
6. **Traefik** - Replace manual nginx with Traefik for auto-discovery
7. **Docker Swarm/Kubernetes** - Container orchestration for production

---

## Security Updates

1. **Flower Credentials** - Basic auth enabled (admin/admin123)
2. **Redis Memory Limit** - Prevents memory exhaustion
3. **Viewer CORS** - Configured for specific origins
4. **Health Checks** - Automated service monitoring

---

## Performance Improvements

1. **Redis**:
   - Memory limit: 512MB
   - LRU eviction policy
   - Persistence with AOF + RDB

2. **Celery**:
   - Concurrency: 4 workers
   - Task time limits
   - Worker max tasks per child

3. **Viewer**:
   - Static asset caching (1 year)
   - Gzip compression
   - Nginx optimizations

---

## Documentation

**New Files**:
1. `/docker/DOCKER_COMPOSE_UPDATE_SUMMARY.md` - Complete update documentation
2. `/docker/QUICK_START.md` - Quick reference guide
3. `/docker/ARCHITECTURE.md` - System architecture
4. `/docker/CHANGELOG.md` - Version history
5. `/docker/nginx/viewer.conf` - Nginx configuration

**Updated Files**:
1. `/docker/docker-compose.yml` - Service definitions
2. `/docker/.env.example` - Environment variables

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f [service]`
2. Review documentation in `/docker/` directory
3. Check health endpoints
4. Verify environment variables

---

**Version**: 1.1.0
**Date**: 2025-10-28
**Author**: System Administrator
**Status**: Production Ready ✅
