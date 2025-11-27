# Phase 2: Anthias Storage Services Analysis

**Document Version**: 1.0
**Date**: 2025-10-29
**Focus**: Production-safe re-enablement strategy for 4 disabled storage services

---

## Executive Summary

**Current State**: Backend API (port 8001) handles ALL operations including file uploads through httpx API calls to port 8000 (Anthias). However, there are NO storage services running on port 8000. The backend expects Anthias API but the services are commented out.

**Critical Finding**: The system is PARTIALLY BROKEN. Backend is configured to upload to `ANTHIAS_API_URL=http://192.168.5.12:8000`, but NO services are listening on that port.

**Risk Level**: HIGH - Any content upload operation will fail immediately.

---

## 1. Service Architecture Analysis

### 1.1 The Four Disabled Services

```
┌─────────────────────────────────────────────────────────────────┐
│                    ANTHIAS STORAGE STACK                         │
│                        (Port 8000)                               │
└─────────────────────────────────────────────────────────────────┘

┌───────────────────┐
│  storage-nginx    │  Port: 8000 (external) → 80 (internal)
│  (Reverse Proxy)  │  Role: CORS-enabled reverse proxy
└─────────┬─────────┘  Dependencies: storage-server, storage-websocket
          │            Volumes: nginx.conf, anthias-assets, staticfiles
          │
     ┌────┴─────────────────────────────────┐
     │                                       │
┌────▼──────────────┐            ┌─────────▼────────────┐
│  storage-server   │            │  storage-websocket   │
│  (Django API)     │            │  (Real-time Events)  │
└────┬──────────────┘            └──────────────────────┘
     │  Port: 8080 (internal)       Port: 9999 (internal)
     │  Role: File storage API       Role: WebSocket server
     │  Dependencies: redis           Dependencies: redis
     │  Volumes: anthias-data,        Volumes: anthias-data
     │           anthias-assets,
     │           staticfiles
     │
┌────▼──────────────┐
│  storage-celery   │
│  (Background)     │  No external port
└───────────────────┘  Role: Async tasks (file processing, cleanup)
                       Dependencies: redis, storage-server
                       Volumes: anthias-data, anthias-assets
```

### 1.2 Service Responsibilities

#### storage-server (Django API)
- **Purpose**: Core Anthias API v1 endpoints
- **Handles**:
  - `POST /api/v1/file_asset` - Upload file, return URI
  - `POST /api/v1/assets` - Create asset record
  - `GET /api/v1/assets` - List assets
  - `GET /api/v1/assets/{id}` - Get asset details
  - `GET /api/v1/assets/{id}/content` - Download asset (base64)
  - `DELETE /api/v1/assets/{id}` - Delete asset
  - `PUT /api/v1/assets/{id}` - Update asset metadata
- **Storage**: Files saved to `/data/screenly_assets/` volume
- **Database**: Uses internal SQLite (NOT our PostgreSQL)
- **Port**: 8080 (internal only, accessed via nginx)

#### storage-celery (Background Worker)
- **Purpose**: Asynchronous task processing
- **Handles**:
  - Video thumbnail generation
  - Image optimization/resizing
  - File format conversion
  - Asset cleanup/garbage collection
  - Scheduled tasks (check expired content)
- **Communication**: Via Redis (CELERY_BROKER_URL)
- **Depends On**: storage-server must be running first

#### storage-websocket (Real-time Updates)
- **Purpose**: Push notifications to viewers
- **Handles**:
  - Asset update notifications
  - Playlist change events
  - Device command broadcasts
- **Port**: 9999 (internal), accessed via nginx at `/ws`
- **Protocol**: WebSocket over ZMQ (Zero Message Queue)
- **Note**: Our current viewer does NOT use this (polls API instead)

#### storage-nginx (Reverse Proxy)
- **Purpose**: Single entry point with CORS
- **Handles**:
  - CORS headers for cross-origin requests
  - Request routing to server/websocket
  - Static file serving (`/screenly_assets`)
  - API proxying with proper headers
- **Port**: 8000 (external) → 80 (internal)
- **Critical**: This is what backend expects at `ANTHIAS_API_URL`

---

## 2. Current Backend Integration

### 2.1 How Backend Uploads Files (anthias_service.py)

```python
# Line 28-29
self.base_url = settings.ANTHIAS_API_URL  # http://192.168.5.12:8000
self.public_url = settings.ANTHIAS_PUBLIC_URL  # http://192.168.5.12:8000

# Line 84-87: STEP 1 - Upload file
files = {"file_upload": (file.filename, file_content, file.content_type)}
upload_response = await client.post(
    self._get_api_url("file_asset"),  # POST /api/v1/file_asset
    files=files
)

# Line 118-120: STEP 2 - Create asset
create_response = await client.post(
    self._get_api_url("assets"),  # POST /api/v1/assets
    data={"model": json.dumps(model_data)}
)
```

**What Happens Now (with services disabled)**:
```
Backend → httpx.post("http://192.168.5.12:8000/api/v1/file_asset")
                                    ↓
                          ❌ Connection Refused
                          (No service listening on port 8000)
```

### 2.2 Environment Variables

**Used by Backend**:
- `ANTHIAS_API_URL` - Line 28 (anthias_service.py) - **CRITICAL**
- `ANTHIAS_PUBLIC_URL` - Line 29 (anthias_service.py)
- `ANTHIAS_INTERNAL_URL` - Only in config.py, NOT used in code

**Used by Storage Services** (.env):
```bash
ANTHIAS_HOME=/data                                    # Storage root
ANTHIAS_LISTEN=0.0.0.0                               # Bind address
CELERY_BROKER_URL=redis://redis:6379/0               # Task queue
CELERY_RESULT_BACKEND=redis://redis:6379/0           # Task results
ZMQ_PUBLISHER_PORT=10001                             # WebSocket pub
ZMQ_COLLECTOR_PORT=5558                              # WebSocket sub
```

---

## 3. Files & Dependencies Check

### 3.1 Dockerfiles Status

| File | Path | Status | Issues |
|------|------|--------|--------|
| Dockerfile.server | anthias/docker/ | ✅ EXISTS | Multi-stage build with Node.js |
| Dockerfile.celery | anthias/docker/ | ✅ EXISTS | Uses requirements.txt |
| Dockerfile.websocket | anthias/docker/ | ✅ EXISTS | Uses requirements-websocket.txt |
| Dockerfile.nginx | anthias/docker/ | ✅ EXISTS | Simple nginx image |

### 3.2 Required Files

| File | Path | Purpose | Status |
|------|------|---------|--------|
| nginx.development.conf | anthias/docker/nginx/ | ✅ | Nginx routing config |
| start_server.sh | anthias/bin/ | ✅ | Django server startup |
| requirements.txt | anthias/requirements/ | ⚠️ UNKNOWN | Python dependencies |
| requirements-websocket.txt | anthias/requirements/ | ⚠️ UNKNOWN | WebSocket deps |

**Action Required**: Verify requirements files exist before building.

### 3.3 Volume Directories

| Volume | Mount Point | Local Path | Status | Purpose |
|--------|-------------|------------|--------|---------|
| anthias-data | /data | Docker volume | ✅ AUTO | Anthias config/database |
| anthias-assets | /data/screenly_assets | ./anthias-assets | ✅ EXISTS (empty) | Uploaded files |
| staticfiles | /data/screenly/staticfiles | ./anthias/staticfiles | ⚠️ CHECK | Django static files |

**Current State**: `anthias-assets/` directory exists but is EMPTY (no test uploads yet).

---

## 4. Integration Impact Analysis

### 4.1 What Works Now (WITHOUT Storage Services)

✅ **Backend API operations**:
- User authentication
- Device registration
- Playlist management
- Schedule management
- Guest info display
- Activity logging

✅ **Database operations**:
- PostgreSQL on port 5433
- All CRUD operations
- Migrations applied

✅ **Viewer operations**:
- Device activation via 6-digit code
- Heartbeat reporting
- Dashboard online/offline status

### 4.2 What FAILS Now (WITHOUT Storage Services)

❌ **Content upload** (`POST /api/content/upload`):
```python
# backend/app/api/routes/content.py
asset_data = await anthias_service.upload_asset(file)
# ↓
# httpx.RequestError: Cannot connect to Anthias service
# HTTPException(503, "Cannot connect to Anthias service")
```

❌ **Content listing with asset details** (`GET /api/content`):
```python
# If content.anthias_asset_id exists, tries to fetch from Anthias
asset_data = await anthias_service.get_asset(content.anthias_asset_id)
# ↓ May fail if asset was uploaded before
```

❌ **Content deletion** (`DELETE /api/content/{id}`):
```python
# Tries to delete from Anthias storage
await anthias_service.delete_asset(content.anthias_asset_id)
# ↓ Will fail silently (404 considered success)
```

❌ **Content URL generation for viewer**:
```python
# backend/app/api/client.py:172
direct_content_url = f"{settings.ANTHIAS_API_URL}/api/v1/assets/{content.anthias_asset_id}/content"
# ↓ URL points to non-existent service
```

### 4.3 Database State

**Content table** (backend PostgreSQL):
- Has column: `anthias_asset_id` (String, nullable)
- Current entries: UNKNOWN (need to check)
- Risk: If there are existing content records with anthias_asset_id, viewer will fail to load them

**Anthias internal database** (SQLite in anthias-data volume):
- Location: `/data/.screenly/screenly.db`
- Status: Will be created fresh when storage-server starts
- Risk: NO existing data to migrate (clean slate)

---

## 5. Risks & Mitigation

### 5.1 HIGH Risk Issues

#### Risk 1: Port Conflict with Existing Service
**Description**: Another service may be using port 8000
**Likelihood**: Medium
**Impact**: High (services won't start)

**Detection**:
```bash
# On server 192.168.5.12
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 "netstat -tuln | grep :8000"
```

**Mitigation**:
- Check port availability before enabling
- If conflict, change ANTHIAS_EXTERNAL_PORT in .env
- Update backend ANTHIAS_API_URL to match

#### Risk 2: Missing Dependencies in Anthias Build
**Description**: Dockerfile may fail due to missing files
**Likelihood**: Medium
**Impact**: High (build failure)

**Detection**:
```bash
# Check requirements files
ls -la /mnt/g/khoirul/signate/anthias/requirements/
```

**Mitigation**:
- Verify all COPY sources exist before build
- Test build locally first
- Have rollback ready

#### Risk 3: Volume Permission Issues
**Description**: Docker may not have write access to bind mounts
**Likelihood**: Low (Linux host)
**Impact**: Medium (file uploads fail)

**Detection**:
```bash
# After starting services
docker logs signage-storage-server | grep -i "permission denied"
```

**Mitigation**:
- Ensure anthias-assets/ has 777 permissions
- Use docker volumes instead of bind mounts if issues persist

### 5.2 MEDIUM Risk Issues

#### Risk 4: CORS Configuration Conflicts
**Description**: Multiple CORS sources (backend + nginx) may conflict
**Likelihood**: Medium
**Impact**: Medium (API calls blocked)

**Current State**:
- Backend FastAPI has CORS middleware (lines 104-113 in main.py)
- Nginx has CORS headers (lines 26-39 in nginx.development.conf)

**Mitigation**:
- Keep backend CORS for port 8001 endpoints
- Let nginx handle CORS for port 8000 endpoints
- They operate on different ports, so no conflict expected

#### Risk 5: Redis Dependency Startup Order
**Description**: Celery/WebSocket may start before Redis ready
**Likelihood**: Low (depends_on configured)
**Impact**: Medium (services crash and restart)

**Mitigation**:
- Already configured in docker-compose:
  ```yaml
  depends_on:
    - redis
    - storage-server
  ```
- Docker will handle startup order
- Services will restart automatically (restart: unless-stopped)

### 5.3 LOW Risk Issues

#### Risk 6: Existing Content Records Orphaned
**Description**: Content in DB with anthias_asset_id but file doesn't exist
**Likelihood**: Low (no uploads yet)
**Impact**: Low (viewer shows error for those items)

**Detection**:
```sql
-- Check for content with anthias_asset_id
SELECT id, name, anthias_asset_id FROM contents WHERE anthias_asset_id IS NOT NULL;
```

**Mitigation**:
- If found, provide admin UI to re-upload or delete
- Or run migration script to clear orphaned anthias_asset_id

---

## 6. Step-by-Step Enablement Plan

### Phase 2A: Pre-Flight Checks (5 minutes)

**On Local Machine**:
```bash
cd /mnt/g/khoirul/signate

# 1. Verify all Dockerfiles exist
ls -la anthias/docker/Dockerfile.{server,celery,websocket,nginx}

# 2. Verify requirements files
ls -la anthias/requirements/requirements*.txt

# 3. Verify nginx config
ls -la anthias/docker/nginx/nginx.development.conf

# 4. Check if staticfiles directory exists (needed by nginx)
ls -la anthias/staticfiles/ 2>/dev/null || echo "WARN: staticfiles not found"

# 5. Verify anthias-assets writable
touch anthias-assets/.test && rm anthias-assets/.test || echo "ERROR: Cannot write"
```

**On Server (192.168.5.12)**:
```bash
# Connect to server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

# 1. Check port 8000 availability
netstat -tuln | grep :8000
# Expected: NO output (port free)

# 2. Check current backend status
docker ps | grep signage-backend
# Expected: signage-backend running

# 3. Check existing content uploads
docker exec signage-postgres psql -U signage_user -d signage_db \
  -c "SELECT id, name, anthias_asset_id FROM contents WHERE anthias_asset_id IS NOT NULL;"
# Expected: 0 rows (no uploads yet)

# 4. Check disk space for assets
df -h /home/gzjbbk/prototipe2/anthias-assets
# Expected: At least 10GB free
```

**Go/No-Go Decision**:
- ✅ All Dockerfiles exist
- ✅ Port 8000 free
- ✅ No orphaned content records
- ✅ Sufficient disk space
→ **PROCEED to Phase 2B**

---

### Phase 2B: Enable Single Service (storage-nginx) (10 minutes)

**Why nginx first?**
- Lightweight (just routing)
- No dependencies on other storage services initially
- Can test port binding without complex services
- Quick rollback if port conflict

**Steps**:

1. **Uncomment nginx service ONLY** (lines 312-328):
```bash
cd /mnt/g/khoirul/signate

# Edit docker-compose.yml
nano docker/docker-compose.yml

# Change lines 312-328:
# FROM:
# # storage-nginx:
# TO:
storage-nginx:

# Save and exit
```

2. **Build and start nginx** (on server):
```bash
# Sync to server
sshpass -p 'Password@2021' scp -r docker/docker-compose.yml \
  gzjbbk@192.168.5.12:/home/gzjbbk/prototipe2/docker/

# Connect to server
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

# Navigate to project
cd /home/gzjbbk/prototipe2

# Build nginx only (will fail because storage-server not running, this is EXPECTED)
docker-compose -f docker/docker-compose.yml build storage-nginx

# DON'T start yet - it depends on storage-server which doesn't exist
```

3. **Expected Result**:
- Build succeeds (nginx image created)
- Service NOT started (depends_on: storage-server)

**Validation**:
```bash
# Check image built
docker images | grep storage-nginx
# Expected: Image exists with recent timestamp

# Check service NOT running
docker ps | grep storage-nginx
# Expected: NO output (not started yet)
```

**Decision Point**:
- ✅ Build succeeded → Continue to Phase 2C
- ❌ Build failed → Check build logs, fix issues, rollback

**Rollback**:
```bash
# If build fails, just re-comment the service
cd /home/gzjbbk/prototipe2
nano docker/docker-compose.yml
# Re-add '#' to lines 312-328
```

---

### Phase 2C: Enable Core Services (server + nginx) (20 minutes)

**Steps**:

1. **Uncomment storage-server** (lines 247-267):
```bash
cd /mnt/g/khoirul/signate
nano docker/docker-compose.yml

# Uncomment entire storage-server block
# Verify environment variables match .env
```

2. **Sync and build on server**:
```bash
# Sync
sshpass -p 'Password@2021' scp -r docker/docker-compose.yml \
  gzjbbk@192.168.5.12:/home/gzjbbk/prototipe2/docker/

# Connect
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

# Build storage-server (this will take 5-10 minutes - compiles Node.js assets)
cd /home/gzjbbk/prototipe2
docker-compose -f docker/docker-compose.yml build storage-server

# Start BOTH server and nginx together
docker-compose -f docker/docker-compose.yml up -d storage-server storage-nginx
```

3. **Wait for startup** (30 seconds):
```bash
# Watch logs
docker logs -f signage-storage-server

# Wait for:
# "Listening at: http://0.0.0.0:8080"
# Press Ctrl+C when seen
```

4. **Validation Tests**:
```bash
# Test 1: Check services running
docker ps | grep storage
# Expected:
# signage-storage-server   Up
# signage-storage-nginx    Up

# Test 2: Check nginx accessible
curl -I http://192.168.5.12:8000/
# Expected: HTTP/1.1 502 Bad Gateway (OK - server not ready yet)
# or HTTP/1.1 200 OK (server ready)

# Test 3: Check server internal
docker exec signage-storage-server curl -I http://localhost:8080/
# Expected: HTTP/1.1 200 OK

# Test 4: Test API endpoint
curl http://192.168.5.12:8000/api/v1/assets
# Expected: [] (empty array - no assets yet)

# Test 5: Check from backend container
docker exec signage-backend curl http://192.168.5.12:8000/api/v1/assets
# Expected: [] (backend can reach Anthias)
```

**Success Criteria**:
- ✅ Both containers running (UP status)
- ✅ Port 8000 responding
- ✅ API returns valid JSON
- ✅ Backend can connect
→ **PROCEED to Phase 2D**

**If Failed**:
```bash
# Check logs
docker logs signage-storage-server --tail 100
docker logs signage-storage-nginx --tail 100

# Common issues:
# 1. Port 8000 already in use → Change ANTHIAS_EXTERNAL_PORT
# 2. Permission denied on volumes → chmod 777 anthias-assets
# 3. Missing requirements → Check anthias/requirements/ exists

# Rollback
docker-compose -f docker/docker-compose.yml down
nano docker/docker-compose.yml  # Re-comment services
```

---

### Phase 2D: Enable Background Services (celery + websocket) (10 minutes)

**Steps**:

1. **Uncomment celery and websocket** (lines 272-307):
```bash
cd /mnt/g/khoirul/signate
nano docker/docker-compose.yml

# Uncomment:
# - storage-celery (lines 272-289)
# - storage-websocket (lines 294-307)
```

2. **Sync and start**:
```bash
sshpass -p 'Password@2021' scp -r docker/docker-compose.yml \
  gzjbbk@192.168.5.12:/home/gzjbbk/prototipe2/docker/

sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12

cd /home/gzjbbk/prototipe2
docker-compose -f docker/docker-compose.yml build storage-celery storage-websocket
docker-compose -f docker/docker-compose.yml up -d storage-celery storage-websocket
```

3. **Validation**:
```bash
# Check all 4 services running
docker ps | grep storage
# Expected: 4 containers (server, nginx, celery, websocket)

# Check celery logs
docker logs signage-storage-celery --tail 20
# Expected: "celery@anthias ready"

# Check websocket logs
docker logs signage-storage-websocket --tail 20
# Expected: "WebSocket server started"
```

**Success Criteria**:
- ✅ All 4 storage containers running
- ✅ Celery worker connected to Redis
- ✅ WebSocket server listening
→ **Phase 2 COMPLETE**

---

### Phase 2E: End-to-End Testing (15 minutes)

**Test 1: Upload Content via Backend API**
```bash
# From local machine or Postman

# 1. Login to get token
curl -X POST http://192.168.5.12:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token'

# Save token as TOKEN variable

# 2. Upload test image
curl -X POST http://192.168.5.12:8001/api/content/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test-image.jpg" \
  -F "name=Test Image" \
  -F "content_type=image" \
  -F "duration=10"

# Expected:
# {
#   "id": 1,
#   "name": "Test Image",
#   "anthias_asset_id": "abc123def456",
#   "file_url": "http://192.168.5.12:8000/screenly_assets/abc123def456_test-image.jpg"
# }
```

**Test 2: Verify File Stored**
```bash
# On server
ls -lh /home/gzjbbk/prototipe2/anthias-assets/
# Expected: See uploaded file with anthias_asset_id prefix

# Check file size
du -h /home/gzjbbk/prototipe2/anthias-assets/*
```

**Test 3: Fetch Content from Viewer**
```bash
# Simulate viewer requesting playlist
curl http://192.168.5.12:8001/api/client/content/DEVICE_CODE_HERE

# Expected:
# {
#   "playlist_id": 1,
#   "contents": [
#     {
#       "id": 1,
#       "url": "http://192.168.5.12:8000/screenly_assets/...",
#       "duration": 10,
#       "type": "image"
#     }
#   ]
# }
```

**Test 4: Verify Celery Processing**
```bash
# Upload a video (if celery processes it, should create thumbnail)
curl -X POST http://192.168.5.12:8001/api/content/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test-video.mp4" \
  -F "name=Test Video" \
  -F "content_type=video"

# Check celery logs for task
docker logs signage-storage-celery --tail 50 | grep -i task
# Expected: See task processing logs
```

**Test 5: Delete Content**
```bash
# Delete uploaded content
curl -X DELETE http://192.168.5.12:8001/api/content/1 \
  -H "Authorization: Bearer $TOKEN"

# Verify file removed from storage
ls -la /home/gzjbbk/prototipe2/anthias-assets/
# Expected: File should be gone
```

**Success Criteria**:
- ✅ Upload succeeds
- ✅ File appears in anthias-assets/
- ✅ Viewer can fetch content URL
- ✅ Content URL accessible from browser
- ✅ Delete removes file
→ **Phase 2 PRODUCTION READY**

---

## 7. Monitoring & Health Checks

### 7.1 Service Health Endpoints

**After enablement, add to monitoring**:

```bash
# Storage Server Health
curl http://192.168.5.12:8000/api/v1/assets
# Expected: 200 OK, JSON array

# Backend Health Check
curl http://192.168.5.12:8001/health
# Should now show Anthias as "healthy"

# Check individual container health
docker ps --format "table {{.Names}}\t{{.Status}}" | grep storage
```

### 7.2 Disk Space Monitoring

```bash
# Alert if anthias-assets > 80% of allocated space
df -h /home/gzjbbk/prototipe2/anthias-assets | awk 'NR==2 {print $5}' | sed 's/%//'
# Expected: < 80
```

### 7.3 Error Monitoring

**Add to log aggregation**:
```bash
# Backend connection errors to Anthias
docker logs signage-backend 2>&1 | grep "Cannot connect to Anthias"

# Storage server errors
docker logs signage-storage-server 2>&1 | grep -i "error\|exception"

# Celery task failures
docker logs signage-storage-celery 2>&1 | grep -i "failed\|error"
```

---

## 8. Rollback Strategy

### 8.1 Quick Rollback (< 2 minutes)

**If Phase 2C fails (server + nginx)**:
```bash
# On server
cd /home/gzjbbk/prototipe2

# Stop storage services
docker-compose -f docker/docker-compose.yml down storage-server storage-nginx

# Re-comment in docker-compose.yml
nano docker/docker-compose.yml
# Add '#' back to lines 247-328

# Restart only working services
docker-compose -f docker/docker-compose.yml up -d
```

**Backend continues working** for all non-upload operations.

### 8.2 Data Preservation

**Even after rollback**:
- ✅ PostgreSQL data intact (separate volume)
- ✅ Uploaded files preserved (anthias-assets/ bind mount)
- ✅ User data, devices, playlists all safe

**To fully clean up** (if needed):
```bash
# Remove storage images
docker rmi $(docker images | grep storage | awk '{print $3}')

# Clear uploaded files (ONLY if starting fresh)
rm -rf /home/gzjbbk/prototipe2/anthias-assets/*

# Clear Anthias data volume
docker volume rm signate_anthias-data
```

---

## 9. Post-Enablement Checklist

After successful enablement, update these:

### 9.1 Documentation Updates

- [ ] Update CLAUDE.md with storage services status
- [ ] Add storage endpoints to API documentation
- [ ] Document file size limits (MAX_UPLOAD_SIZE=100MB)
- [ ] Update architecture diagram with storage layer

### 9.2 Configuration Updates

- [ ] Verify ANTHIAS_API_URL in all .env files
- [ ] Add storage health check to monitoring
- [ ] Configure backup for anthias-assets/
- [ ] Set up log rotation for storage services

### 9.3 Testing Updates

- [ ] Add upload tests to integration test suite
- [ ] Test viewer with uploaded content
- [ ] Test content deletion workflow
- [ ] Verify CORS from web-admin

### 9.4 Operational Updates

- [ ] Train team on new upload workflow
- [ ] Document troubleshooting for upload failures
- [ ] Set up alerts for disk space
- [ ] Plan for content backup strategy

---

## 10. Known Limitations & Future Work

### 10.1 Current Limitations

1. **Anthias uses internal SQLite** - Not integrated with our PostgreSQL
   - Asset metadata duplicated in two databases
   - No referential integrity between systems
   - **Future**: Migrate to single database or sync mechanism

2. **No CDN integration** - Files served directly from server
   - Single point of failure
   - No geographic distribution
   - **Future**: Add CloudFlare or S3 integration

3. **WebSocket not used by viewer** - Viewer polls API instead
   - Less real-time updates
   - More API load
   - **Future**: Migrate viewer to WebSocket for push updates

4. **No multi-region support** - Single server deployment
   - No failover
   - No load balancing
   - **Future**: Multi-region architecture with data replication

### 10.2 Optimization Opportunities

1. **Direct file serving** - Bypass backend for content delivery
   - Viewer could fetch directly from storage-nginx:8000
   - Reduces backend load
   - **Requires**: CORS configuration in nginx

2. **Celery task optimization** - Async thumbnail generation
   - Currently blocking on upload
   - Could return immediately and process in background
   - **Requires**: Job status API

3. **Content compression** - Reduce storage and bandwidth
   - Image optimization (WebP conversion)
   - Video transcoding (adaptive bitrate)
   - **Requires**: Additional Celery tasks

---

## 11. Decision Matrix

| Scenario | Recommendation | Rationale |
|----------|---------------|-----------|
| **No uploads needed yet** | ❌ WAIT | No urgency, avoid complexity |
| **Testing uploads locally** | ✅ ENABLE on dev first | Safe testing environment |
| **Production upload requirement** | ✅ ENABLE with Phase 2C plan | Follow incremental plan |
| **High traffic expected** | ⚠️ ENABLE + monitoring | Add disk space alerts |
| **Limited disk space (< 10GB)** | ❌ WAIT | Risk of disk full |
| **Tight deadline (< 1 hour)** | ❌ WAIT | Insufficient testing time |

---

## 12. Appendix: Quick Reference

### 12.1 Critical Commands

```bash
# Check all storage services status
docker ps | grep storage

# View storage logs (all services)
docker logs signage-storage-server --tail 50
docker logs signage-storage-celery --tail 50
docker logs signage-storage-websocket --tail 50
docker logs signage-storage-nginx --tail 50

# Test Anthias API
curl http://192.168.5.12:8000/api/v1/assets

# Restart single service
docker-compose -f docker/docker-compose.yml restart storage-server

# Full restart
docker-compose -f docker/docker-compose.yml restart storage-server storage-nginx storage-celery storage-websocket

# Emergency stop
docker-compose -f docker/docker-compose.yml down storage-server storage-nginx storage-celery storage-websocket
```

### 12.2 File Locations

| Item | Path |
|------|------|
| Docker Compose | `/home/gzjbbk/prototipe2/docker/docker-compose.yml` |
| Uploaded Files | `/home/gzjbbk/prototipe2/anthias-assets/` |
| Anthias Code | `/home/gzjbbk/prototipe2/anthias/` |
| Backend Config | `/home/gzjbbk/prototipe2/backend/app/core/config.py` |
| Environment | `/home/gzjbbk/prototipe2/.env` |

### 12.3 Port Reference

| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| storage-server | 8080 | - | Django API (internal only) |
| storage-celery | - | - | Background tasks |
| storage-websocket | 9999 | - | WebSocket (internal only) |
| storage-nginx | 80 | 8000 | Public API gateway |

---

## Conclusion

**Current State**: Backend is configured to use Anthias storage API on port 8000, but services are disabled. Content upload will fail immediately.

**Recommended Action**:
- **If uploads not needed yet**: WAIT, keep disabled
- **If testing uploads**: Enable on dev environment first
- **If production ready**: Follow Phase 2C plan (enable server + nginx first)

**Confidence Level**: HIGH
- All Dockerfiles exist and appear complete
- Configuration properly separated in .env
- Rollback strategy is simple and safe
- No data loss risk (PostgreSQL separate)

**Estimated Enablement Time**: 45 minutes (including testing)

**Go-Live Criteria**:
1. Port 8000 confirmed available
2. All pre-flight checks passed
3. At least 30 minutes for testing
4. Rollback plan communicated to team
5. Monitoring in place for disk space

---

**Document Owner**: Cloud Architect
**Review Date**: 2025-10-29
**Next Review**: After Phase 2 enablement
