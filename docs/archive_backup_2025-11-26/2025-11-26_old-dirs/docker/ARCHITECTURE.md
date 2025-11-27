# Smart TV Digital Signage - Service Architecture

## System Overview

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    SMART TV DIGITAL SIGNAGE SYSTEM                         │
│                         Server: 192.168.5.12                               │
└───────────────────────────────────────────────────────────────────────────┘

                                   CLIENTS
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
              ┌──────────┐     ┌──────────┐     ┌──────────┐
              │ Web Admin│     │  Viewer  │     │  WebOS   │
              │   :3000  │     │  :8080   │     │    TV    │
              └────┬─────┘     └────┬─────┘     └────┬─────┘
                   │                │                 │
                   └────────────────┼─────────────────┘
                                    │
                              ┌─────▼─────┐
                              │  Nginx    │
                              │  Reverse  │
                              │   Proxy   │
                              └─────┬─────┘
                                    │
            ────────────────────────┴────────────────────────
                                DOCKER NETWORK
            ────────────────────────────────────────────────
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌──────────────┐ ┌──────────┐ ┌────────────────┐
            │  Backend API │ │  Viewer  │ │    Anthias     │
            │    :8001     │ │  :8080   │ │     :8000      │
            │   FastAPI    │ │  Nginx   │ │   (Legacy)     │
            └──────┬───────┘ └──────────┘ └────────────────┘
                   │
                   ├─────────────────────────────────────────┐
                   │                                         │
                   ▼                                         ▼
         ┌────────────────┐                       ┌───────────────────┐
         │   PostgreSQL   │                       │      Redis        │
         │     :5433      │◄──────────────────────│      :6379        │
         │   (Database)   │                       │  (Broker/Cache)   │
         └────────────────┘                       └─────────┬─────────┘
                                                            │
                                    ┌───────────────────────┼─────┐
                                    │                       │     │
                                    ▼                       ▼     ▼
                          ┌──────────────┐      ┌──────────────────┐
                          │Celery Worker │      │  Celery Beat     │
                          │(Background)  │      │  (Scheduler)     │
                          │Concurrency:4 │      │   (Periodic)     │
                          └──────┬───────┘      └──────────────────┘
                                 │
                                 ▼
                          ┌─────────────┐
                          │   Flower    │
                          │    :5555    │
                          │ (Monitoring)│
                          └─────────────┘
```

---

## Service Details

### 1. **Backend API** (Port 8001)
**Technology**: FastAPI (Python)
**Container**: `signage-backend`

**Responsibilities**:
- RESTful API endpoints
- Device management (registration, activation, heartbeat)
- Content management (upload, CRUD)
- Playlist management
- Tag management
- User authentication & authorization
- Real-time device status

**Dependencies**:
- PostgreSQL (database)
- Redis (cache + session storage)

**Health Check**: `curl http://192.168.5.12:8001/health`

---

### 2. **Viewer** (Port 8080)
**Technology**: Static HTML + JavaScript
**Container**: `signage-viewer` (Nginx Alpine)

**Responsibilities**:
- Display content on TVs, monitors, browsers
- Device registration with activation code
- Playlist playback
- Heartbeat mechanism
- Content caching
- Multi-language support
- Command execution from backend

**Features**:
- Unified codebase for all platforms
- Works on WebOS TV, Tizen, browser
- Offline mode with caching
- Service worker for PWA
- HLS video streaming support

**Health Check**: `curl http://192.168.5.12:8080/health`

---

### 3. **PostgreSQL** (Port 5433)
**Technology**: PostgreSQL 15 Alpine
**Container**: `signage-postgres`

**Responsibilities**:
- Primary data storage
- Device registry
- Content metadata
- Playlist definitions
- User accounts
- Activity logs
- Tag management

**Configuration**:
- Connection pool: 2-10 connections
- Auto-initialization with `init.sql`
- Persistent volume for data

**Health Check**: `pg_isready -U signage_user`

---

### 4. **Redis** (Port 6379)
**Technology**: Redis 7 Alpine
**Container**: `signage-redis`

**Responsibilities**:
- **Message Broker**: Celery task queue
- **Cache**: API response caching
- **Session Store**: User sessions
- **Pub/Sub**: Real-time updates

**Configuration**:
- Memory limit: 512MB
- Eviction policy: allkeys-lru
- AOF persistence enabled
- RDB snapshots: every 60s if 1000 keys changed

**Shared By**:
- Backend API (cache)
- Celery Worker (broker)
- Celery Beat (broker)
- Anthias services

**Health Check**: `redis-cli ping`

---

### 5. **Celery Worker** (Background)
**Technology**: Celery (Python)
**Container**: `signage-celery-worker`

**Responsibilities**:
- Video processing (transcoding, thumbnails)
- Image optimization
- Bulk operations
- Report generation
- Email notifications
- Data cleanup
- External API integrations

**Configuration**:
- Concurrency: 4 workers (configurable)
- Task time limit: 3600s (1 hour)
- Soft time limit: 3000s (50 minutes)
- Max tasks per child: 1000

**Task Types**:
- `app.tasks.process_video` - Video processing
- `app.tasks.generate_thumbnail` - Thumbnail creation
- `app.tasks.send_notification` - Alerts
- `app.tasks.bulk_update` - Batch operations

**Health Check**: `celery -A app.celery_app inspect ping`

---

### 6. **Celery Beat** (Scheduler)
**Technology**: Celery Beat (Python)
**Container**: `signage-celery-beat`

**Responsibilities**:
- Schedule periodic tasks
- Database cleanup
- Log rotation
- Device status checks
- Content expiry checks
- Report generation

**Scheduled Tasks**:
```python
# Daily at 2 AM: Cleanup old logs
cleanup_old_logs.apply_async()

# Daily at 3 AM: Remove expired devices
cleanup_expired_devices.apply_async()

# Every hour: Update device statistics
update_device_stats.apply_async()
```

---

### 7. **Flower** (Port 5555)
**Technology**: Flower (Celery Monitoring)
**Container**: `signage-flower`

**Responsibilities**:
- Monitor Celery workers
- View task history
- Track success/failure rates
- Worker resource usage
- Task execution times

**Access**:
- URL: http://192.168.5.12:5555
- Username: `admin`
- Password: `admin123`

**Features**:
- Real-time task monitoring
- Worker management
- Task filtering and search
- Task result inspection
- Worker statistics

---

### 8. **Anthias** (Port 8000)
**Technology**: Screenly OSE (Legacy)
**Containers**:
- `anthias-server` - Main application
- `anthias-celery` - Background tasks
- `anthias-websocket` - Real-time updates
- `anthias-nginx` - Reverse proxy

**Status**: Legacy system being phased out
**Note**: Backend API is the primary system

---

## Data Flow

### Device Registration Flow
```
Viewer (TV) → Backend API → PostgreSQL
     │              │
     └──────────────┴─────→ Generate activation code

Admin Panel → Backend API → Activate device
                  ↓
            Update PostgreSQL
                  ↓
            Notify via Redis
                  ↓
            Viewer receives confirmation
```

### Content Upload Flow
```
Web Admin → Backend API → Save to /data/content
                ↓
         Store metadata in PostgreSQL
                ↓
         Trigger Celery task
                ↓
      Celery Worker processes:
         - Generate thumbnail
         - Optimize image/video
         - Update metadata
                ↓
         Update PostgreSQL
                ↓
         Clear Redis cache
```

### Playlist Playback Flow
```
Viewer → Backend API → Check cache (Redis)
           │ (miss)
           ↓
    Query PostgreSQL
           ↓
    Fetch playlist + content
           ↓
    Cache in Redis (5 min TTL)
           ↓
    Return to Viewer
           ↓
    Viewer displays content
           ↓
    Send heartbeat every 30s
```

### Background Task Flow
```
API Request → Trigger Celery task
                    ↓
              Send to Redis queue
                    ↓
         Celery Worker picks up task
                    ↓
              Execute task logic
                    ↓
         Update PostgreSQL
                    ↓
         Store result in Redis
                    ↓
         Notify via WebSocket
```

---

## Network Architecture

### Docker Network: `signage-network`
**Type**: Bridge
**Subnet**: Auto-assigned

**Internal DNS**:
- `postgres` → PostgreSQL container
- `redis` → Redis container
- `backend-api` → Backend API container
- `celery-worker` → Celery Worker container
- `celery-beat` → Celery Beat container
- `flower` → Flower container
- `viewer` → Viewer Nginx container
- `anthias-nginx` → Anthias Nginx container

**External Ports**:
- 8001 → backend-api:8000
- 8080 → viewer:80
- 8000 → anthias-nginx:80
- 5555 → flower:5555
- 5433 → postgres:5432
- 6379 → redis:6379

---

## Storage Architecture

### Persistent Volumes

1. **postgres-data**
   - Path: `/var/lib/postgresql/data`
   - Purpose: Database files
   - Backup: Daily via cron

2. **redis-data**
   - Path: `/data`
   - Purpose: Redis AOF + RDB files
   - Backup: Included in volume backup

3. **anthias-data**
   - Path: `/data`
   - Purpose: Anthias configuration
   - Status: Legacy

### Mounted Directories

1. **Backend Code** (`../backend/app`)
   - Mounted to: `backend-api:/app/app`
   - Mounted to: `celery-worker:/app/app`
   - Purpose: Hot reload in development

2. **Content Storage** (`../data`)
   - Mounted to: `backend-api:/app/data`
   - Mounted to: `celery-worker:/app/data`
   - Purpose: Uploaded content files

3. **Viewer Files** (`../viewer`)
   - Mounted to: `viewer:/usr/share/nginx/html`
   - Purpose: Static HTML/JS/CSS

4. **Nginx Config** (`../docker/nginx/viewer.conf`)
   - Mounted to: `viewer:/etc/nginx/conf.d/default.conf`
   - Purpose: Custom Nginx configuration

---

## Security Architecture

### Authentication Flow
```
Client → Backend API → Verify JWT token
              ↓
      Check PostgreSQL (user table)
              ↓
      Validate permissions
              ↓
      Return authorized response
```

### API Security
- **CORS**: Configured for specific origins
- **JWT**: HS256 algorithm
- **Rate Limiting**: 100 requests/minute per IP
- **Input Validation**: Pydantic models
- **SQL Injection Prevention**: SQLAlchemy ORM

### Network Security
- **Internal Network**: All services on same Docker network
- **Firewall**: Only expose necessary ports
- **HTTPS**: Use reverse proxy (Nginx/Traefik) in production

---

## Scalability

### Horizontal Scaling Options

1. **Backend API**
   ```yaml
   backend-api:
     deploy:
       replicas: 3
   ```

2. **Celery Workers**
   ```yaml
   celery-worker:
     deploy:
       replicas: 5
   ```

3. **Load Balancer**
   - Add Nginx/HAProxy
   - Round-robin to API replicas

### Vertical Scaling

1. **PostgreSQL**
   - Increase connection pool
   - Add read replicas
   - Use PgBouncer

2. **Redis**
   - Increase memory limit
   - Use Redis Cluster
   - Add Redis Sentinel

3. **Celery**
   - Increase concurrency
   - Add more worker types
   - Use priority queues

---

## Monitoring Stack

### Application Monitoring
- **Flower**: Celery task monitoring
- **FastAPI**: Built-in `/metrics` endpoint
- **Logs**: Centralized via docker-compose logs

### Infrastructure Monitoring (Future)
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **Alertmanager**: Alert notifications

### Health Checks
- PostgreSQL: Every 10s
- Redis: Every 10s
- Celery Worker: Every 30s
- Viewer: Every 30s

---

## Backup Strategy

### Database Backup
```bash
# Daily at 2 AM
docker exec signage-postgres pg_dump \
  -U signage_user signage_db \
  > /backups/db_$(date +%Y%m%d).sql
```

### Volume Backup
```bash
# Weekly
docker run --rm \
  -v postgres-data:/data \
  -v /backups:/backups \
  alpine tar czf /backups/volumes_$(date +%Y%m%d).tar.gz /data
```

### Retention Policy
- Daily backups: Keep 7 days
- Weekly backups: Keep 4 weeks
- Monthly backups: Keep 12 months

---

## Disaster Recovery

### Recovery Time Objective (RTO)
- **Target**: < 1 hour
- **Database**: Restore from latest backup
- **Volumes**: Restore from volume backup
- **Services**: Rebuild with docker-compose

### Recovery Steps
1. Stop all services
2. Restore PostgreSQL backup
3. Restore volume backups
4. Restart services
5. Verify health checks
6. Test critical workflows

---

## Performance Metrics

### Target SLAs
- **API Response Time**: < 200ms (p95)
- **Viewer Load Time**: < 2s
- **Task Processing**: < 5s (simple tasks)
- **Uptime**: 99.5%

### Bottlenecks
- Database queries (optimize with indexes)
- Video processing (scale Celery workers)
- Cache misses (increase Redis memory)

---

## Future Enhancements

1. **WebSocket Support**: Real-time device updates
2. **Multi-tenancy**: Organization isolation
3. **CDN Integration**: Content delivery optimization
4. **Analytics**: Usage metrics and insights
5. **Auto-scaling**: Dynamic worker scaling
6. **High Availability**: PostgreSQL replication
7. **Distributed Caching**: Redis Cluster

---

**Last Updated**: 2025-10-28
**Version**: 1.0.0
