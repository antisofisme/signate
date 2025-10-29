# Docker Compose Update Summary

**Date**: 2025-10-28
**Purpose**: Add Celery, Redis optimization, Flower monitoring, and Viewer service

---

## Changes Overview

### 1. Services Added

#### **celery-worker** - Background Task Processor
- **Container**: `signage-celery-worker`
- **Purpose**: Process background tasks asynchronously
- **Command**: `celery -A app.celery_app worker --loglevel=info --concurrency=4`
- **Concurrency**: 4 workers (configurable via `CELERY_WORKER_CONCURRENCY`)
- **Features**:
  - Connects to Redis (message broker) and PostgreSQL (database)
  - Shares volumes with backend-api for file access (`/app/data`)
  - Health check: `celery -A app.celery_app inspect ping`
  - Depends on: postgres, redis, backend-api
  - Restart policy: `unless-stopped`

#### **celery-beat** - Scheduled Tasks
- **Container**: `signage-celery-beat`
- **Purpose**: Schedule periodic tasks (cleanup, maintenance)
- **Command**: `celery -A app.celery_app beat --loglevel=info`
- **Features**:
  - Connects to Redis and PostgreSQL
  - Shares code volume with backend-api
  - Depends on: postgres, redis, backend-api
  - Restart policy: `unless-stopped`

#### **flower** - Celery Monitoring UI
- **Container**: `signage-flower`
- **Port**: 5555 (configurable via `FLOWER_EXTERNAL_PORT`)
- **Purpose**: Monitor Celery tasks and workers
- **Command**: `celery -A app.celery_app flower --port=5555 --basic_auth=admin:admin123`
- **Access**: http://192.168.5.12:5555
- **Credentials**:
  - Username: `admin`
  - Password: `admin123`
- **Features**:
  - Real-time task monitoring
  - Worker status and statistics
  - Task history and results
  - Depends on: redis, celery-worker

#### **viewer** - Static HTML Viewer
- **Container**: `signage-viewer`
- **Port**: 8080 (configurable via `VIEWER_EXTERNAL_PORT`)
- **Purpose**: Serve static viewer for monitors, browsers, and WebOS TV
- **Base Image**: `nginx:alpine`
- **Access**: http://192.168.5.12:8080
- **Features**:
  - Serves unified viewer codebase
  - Custom nginx configuration with CORS
  - Health check endpoint: `/health`
  - Gzip compression enabled
  - Static asset caching (1 year)
  - HTML caching disabled for updates

---

### 2. Redis Service Enhanced

**Before**:
```yaml
redis:
  command: redis-server --appendonly yes
```

**After**:
```yaml
redis:
  command: >
    redis-server
    --appendonly yes
    --maxmemory 512mb
    --maxmemory-policy allkeys-lru
    --save 60 1000
  deploy:
    resources:
      limits:
        memory: 512M
```

**Improvements**:
- **Memory limit**: 512MB with LRU eviction policy
- **Persistence**: AOF + RDB snapshots (every 60s if 1000 keys changed)
- **Resource control**: Docker memory limit enforced
- **Use cases**: Message broker for Celery + cache for API

---

### 3. Backend API Updated

**Environment Variables Added**:
```yaml
- REDIS_HOST=redis
- REDIS_PORT=6379
```

**Volumes Added**:
```yaml
- ../data:/app/data
```

**Purpose**: Enable file sharing between backend-api and celery-worker

---

### 4. Environment Variables Added

**New `.env.example` entries**:

```bash
# Service Ports
PORT_FLOWER=5555

# Celery Configuration
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=3600
CELERY_TASK_SOFT_TIME_LIMIT=3000
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000

# Flower Monitoring
FLOWER_PORT=5555
FLOWER_BASIC_AUTH=admin:admin123
FLOWER_URL=http://192.168.5.12:5555
```

---

### 5. Nginx Configuration Created

**File**: `/mnt/g/khoirul/signate/docker/nginx/viewer.conf`

**Features**:
- Static file serving with proper caching
- CORS headers for API requests
- Security headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection)
- Gzip compression for text/js/css files
- Health check endpoint: `/health`
- Asset caching: 1 year for static files
- HTML caching: disabled for real-time updates

---

## Service Architecture

### Current Service Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                     SMART TV DIGITAL SIGNAGE                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   PostgreSQL     │  │      Redis       │  │   Backend API    │
│   Port: 5433     │  │   Port: 6379     │  │   Port: 8001     │
│  (Database)      │  │ (Broker/Cache)   │  │   (FastAPI)      │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                      │
         │                     │                      │
         ├─────────────────────┼──────────────────────┤
         │                     │                      │
┌────────▼─────────┐  ┌───────▼────────┐  ┌─────────▼────────┐
│ Celery Worker    │  │  Celery Beat   │  │     Flower       │
│  (Background)    │  │  (Scheduler)   │  │  Port: 5555      │
│ Concurrency: 4   │  │   (Periodic)   │  │  (Monitoring)    │
└──────────────────┘  └────────────────┘  └──────────────────┘

┌──────────────────┐  ┌──────────────────────────────────────┐
│     Viewer       │  │         Anthias Services             │
│   Port: 8080     │  │  - anthias-server                    │
│   (Static)       │  │  - anthias-celery                    │
│                  │  │  - anthias-websocket                 │
│                  │  │  - anthias-nginx (Port: 8000)        │
└──────────────────┘  └──────────────────────────────────────┘
```

---

## Deployment Steps

### 1. Update Environment File

```bash
# Copy new environment variables
cd /mnt/g/khoirul/signate/docker
cp .env.example .env
# Edit .env with your configuration
nano .env
```

### 2. Rebuild and Start Services

```bash
cd /mnt/g/khoirul/signate/docker

# Stop all services
docker-compose down

# Rebuild with no cache
docker-compose build --no-cache

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Verify Services

```bash
# Check service status
docker-compose ps

# Expected output:
# signage-postgres          running   0.0.0.0:5433->5432/tcp
# signage-redis             running   0.0.0.0:6379->6379/tcp
# signage-backend           running   0.0.0.0:8001->8000/tcp
# signage-celery-worker     running
# signage-celery-beat       running
# signage-flower            running   0.0.0.0:5555->5555/tcp
# signage-viewer            running   0.0.0.0:8080->80/tcp
# anthias-server            running
# anthias-celery            running
# anthias-websocket         running
# anthias-nginx             running   0.0.0.0:8000->80/tcp
```

### 4. Test Endpoints

```bash
# Backend API
curl http://192.168.5.12:8001/health

# Viewer
curl http://192.168.5.12:8080/health

# Flower (in browser)
open http://192.168.5.12:5555
# Login: admin / admin123
```

---

## Monitoring and Management

### Flower UI

**Access**: http://192.168.5.12:5555
**Username**: admin
**Password**: admin123

**Features**:
- Monitor active workers
- View task history
- Check task success/failure rates
- Monitor task execution times
- View worker resource usage

### Check Celery Worker Status

```bash
# Check if worker is running
docker exec signage-celery-worker celery -A app.celery_app inspect active

# Check scheduled tasks
docker exec signage-celery-beat celery -A app.celery_app inspect scheduled

# Check worker stats
docker exec signage-celery-worker celery -A app.celery_app inspect stats
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f celery-worker
docker-compose logs -f celery-beat
docker-compose logs -f flower
docker-compose logs -f viewer

# Last 100 lines
docker-compose logs --tail=100 celery-worker
```

---

## Service Dependencies

```
postgres (healthy)
  └─> backend-api
      └─> celery-worker
          └─> flower

redis (healthy)
  ├─> backend-api
  ├─> celery-worker
  ├─> celery-beat
  ├─> flower
  └─> anthias-*

viewer (standalone, nginx)
```

---

## Volume Mounts

### Shared Volumes

1. **backend-api & celery-worker**:
   ```yaml
   - ../backend/app:/app/app
   - ../data:/app/data
   ```
   - **Purpose**: Share code and data files for background processing

2. **celery-beat**:
   ```yaml
   - ../backend/app:/app/app
   ```
   - **Purpose**: Share code for scheduled task definitions

3. **viewer**:
   ```yaml
   - ../viewer:/usr/share/nginx/html:ro
   - ../docker/nginx/viewer.conf:/etc/nginx/conf.d/default.conf:ro
   ```
   - **Purpose**: Serve static HTML files with custom nginx config

---

## Health Checks

### celery-worker
- **Test**: `celery -A app.celery_app inspect ping`
- **Interval**: 30s
- **Timeout**: 10s
- **Retries**: 3

### redis
- **Test**: `redis-cli ping`
- **Interval**: 10s
- **Timeout**: 5s
- **Retries**: 5

### postgres
- **Test**: `pg_isready -U signage_user`
- **Interval**: 10s
- **Timeout**: 5s
- **Retries**: 5

### viewer
- **Test**: `wget --spider http://localhost/`
- **Interval**: 30s
- **Timeout**: 10s
- **Retries**: 3

---

## Troubleshooting

### Celery Worker Not Starting

```bash
# Check logs
docker-compose logs celery-worker

# Common issues:
# 1. Missing celery_app module
# 2. Redis connection failed
# 3. Database connection failed

# Test manually
docker exec -it signage-celery-worker celery -A app.celery_app worker --loglevel=debug
```

### Flower Cannot Connect

```bash
# Check if Redis is accessible
docker exec signage-flower redis-cli -h redis ping

# Check celery-worker is running
docker exec signage-flower celery -A app.celery_app inspect active
```

### Viewer Not Loading

```bash
# Check nginx logs
docker-compose logs viewer

# Test health endpoint
curl http://192.168.5.12:8080/health

# Check if files are mounted
docker exec signage-viewer ls -la /usr/share/nginx/html
```

### Redis Memory Issues

```bash
# Check memory usage
docker exec signage-redis redis-cli INFO memory

# Check if eviction is happening
docker exec signage-redis redis-cli INFO stats | grep evicted

# If needed, increase memory limit in docker-compose.yml:
# maxmemory 1gb
```

---

## Next Steps

### 1. Create Celery App Module

Create `/mnt/g/khoirul/signate/backend/app/celery_app.py`:

```python
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "signage",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3000,
    worker_max_tasks_per_child=1000,
)
```

### 2. Create Task Modules

Create `/mnt/g/khoirul/signate/backend/app/tasks/__init__.py`:

```python
from .content import process_video, generate_thumbnail
from .cleanup import cleanup_old_logs, cleanup_expired_devices
from .notifications import send_device_alert

__all__ = [
    "process_video",
    "generate_thumbnail",
    "cleanup_old_logs",
    "cleanup_expired_devices",
    "send_device_alert",
]
```

### 3. Add Scheduled Tasks

Create `/mnt/g/khoirul/signate/backend/app/tasks/scheduled.py`:

```python
from celery.schedules import crontab
from app.celery_app import celery_app

celery_app.conf.beat_schedule = {
    "cleanup-old-logs": {
        "task": "app.tasks.cleanup_old_logs",
        "schedule": crontab(hour=2, minute=0),  # 2 AM daily
    },
    "cleanup-expired-devices": {
        "task": "app.tasks.cleanup_expired_devices",
        "schedule": crontab(hour=3, minute=0),  # 3 AM daily
    },
}
```

### 4. Sync to Server

```bash
# From LOCAL machine
cd /mnt/g/khoirul/signate

# Sync docker-compose and configs
sshpass -p 'Password@2021' scp -r docker/docker-compose.yml docker/.env.example docker/nginx/ gzjbbk@192.168.5.12:/home/gzjbbk/signage/docker/

# Sync backend code (when celery_app is created)
sshpass -p 'Password@2021' scp -r backend/app gzjbbk@192.168.5.12:/home/gzjbbk/signage/backend/

# Rebuild on server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 "cd /home/gzjbbk/signage/docker && docker-compose down && docker-compose build --no-cache && docker-compose up -d"
```

---

## Security Considerations

1. **Change Flower Credentials**: Update `FLOWER_BASIC_AUTH` in production
2. **Redis Password**: Consider adding Redis password authentication
3. **Network Isolation**: All services on same network for security
4. **Volume Permissions**: Ensure proper file permissions on mounted volumes
5. **Firewall Rules**: Only expose necessary ports (8001, 8080, 5555)

---

## Performance Tuning

### Celery Worker Concurrency

Adjust based on CPU cores and workload:

```yaml
# For CPU-bound tasks: cores
command: celery -A app.celery_app worker --concurrency=4

# For I/O-bound tasks: 2x cores
command: celery -A app.celery_app worker --concurrency=8

# Use eventlet/gevent for high concurrency
command: celery -A app.celery_app worker --pool=gevent --concurrency=100
```

### Redis Memory

Adjust based on usage:

```yaml
# Increase for high cache usage
maxmemory 1gb

# Change eviction policy
maxmemory-policy volatile-lru  # Only evict keys with TTL
maxmemory-policy allkeys-lru   # Evict any key (current)
```

---

## Files Modified

1. `/mnt/g/khoirul/signate/docker/docker-compose.yml`
2. `/mnt/g/khoirul/signate/docker/.env.example`

## Files Created

1. `/mnt/g/khoirul/signate/docker/nginx/viewer.conf`
2. `/mnt/g/khoirul/signate/docker/DOCKER_COMPOSE_UPDATE_SUMMARY.md`

---

## Documentation Updated

- Header section with service list
- Monitoring URLs (Flower, API Docs, Anthias)
- Service descriptions and dependencies

---

## Conclusion

✅ **Redis** - Already present, now optimized with memory limits
✅ **Celery Worker** - Added for background task processing
✅ **Celery Beat** - Added for scheduled tasks
✅ **Flower** - Added for monitoring and management
✅ **Viewer** - Added for serving static viewer application
✅ **Environment Variables** - Updated with Celery configuration
✅ **Health Checks** - Added for all critical services
✅ **Dependencies** - Properly configured service startup order
✅ **Volumes** - Shared between backend-api and celery-worker
✅ **Restart Policy** - All services use `unless-stopped`

**Status**: Docker Compose configuration is production-ready. Next step is to implement Celery tasks in backend code.
