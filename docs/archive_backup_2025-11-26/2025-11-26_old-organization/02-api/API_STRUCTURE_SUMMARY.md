# Backend API Structure - Complete Overview

## Summary
This document provides a comprehensive summary of all 15 API router modules and their endpoint organization.

**Project:** Smart TV Digital Signage Backend API
**Framework:** FastAPI + SQLAlchemy
**Base URL:** `http://192.168.5.12:8001`
**Database:** PostgreSQL

---

## Table of Contents

1. [Router Files Overview](#router-files-overview)
2. [Endpoint Statistics](#endpoint-statistics)
3. [Authentication & Security](#authentication--security)
4. [Database Models Involved](#database-models-involved)
5. [Quick Reference by Router](#quick-reference-by-router)

---

## Router Files Overview

### 1. **auth.py** - Authentication (4 endpoints)
**Location:** `/backend/app/api/auth.py`
**Prefix:** `/api/auth`
**Authentication:** POST login/refresh (NO AUTH), GET me & POST logout (AUTH required)

**Endpoints:**
- `POST /api/auth/login` - Authenticate user, return access+refresh tokens
- `POST /api/auth/refresh` - Refresh access token using refresh token
- `GET /api/auth/me` - Get current user information
- `POST /api/auth/logout` - Logout (token invalidation client-side)

**Key Features:**
- JWT token generation (access: 30 min, refresh: 7 days)
- Password hashing with verification
- User active status validation

---

### 2. **devices.py** - Device Management (20+ endpoints)
**Location:** `/backend/app/api/devices.py`
**Prefix:** `/api/devices`
**Authentication:** Most require AUTH, some (heartbeat, monitor/activate) NO AUTH

**Core Device Management:**
- `GET /` - List devices with filters (device_type, status)
- `GET /{device_id}` - Get device details
- `GET /{device_id}/preview` - Get content preview with resolution breakdown
- `POST /tv` - Register TV device
- `POST /monitor` - Generate activation code for monitor
- `POST /monitor/register` - Self-register monitor (NO AUTH)
- `POST /monitor/activate` - Activate monitor with code (NO AUTH)
- `PUT /{device_id}` - Update device info
- `DELETE /{device_id}` - Delete device (with reset command)
- `POST /{device_id}/release` - Release device (keep record)
- `POST /{device_id}/replace-with-pending/{pending_device_id}` - Replace code

**Activation & Heartbeat:**
- `GET /check-activation/{code}` - Check activation status (NO AUTH)
- `POST /heartbeat` - Device heartbeat (NO AUTH, updates last_seen)

**Device Commands:**
- `POST /{device_id}/commands` - Queue generic command
- `POST /{device_id}/commands/reset` - Queue reset command
- `GET /{device_id}/commands/pending` - Get pending commands (NO AUTH)
- `POST /{device_id}/commands/{command_id}/execute` - Mark command executed (NO AUTH)

**Content Assignments:**
- `GET /{device_id}/content` - Get direct content assignments
- `POST /{device_id}/content` - Assign content to device
- `DELETE /{device_id}/content/{content_id}` - Unassign content

**Supported Device Types:** tv, monitor
**Device Statuses:** pending, active, inactive

---

### 3. **content.py** - Content Management (11 endpoints)
**Location:** `/backend/app/api/content.py`
**Prefix:** `/api/content`
**Authentication:** Most require AUTH

**Content Operations:**
- `POST /upload` - Upload file to Anthias + save metadata
- `GET /` - List content with filters
- `GET /{content_id}` - Get content details
- `PATCH /{content_id}` - Update content metadata
- `DELETE /{content_id}` - Delete from Anthias + database

**Content Assignments:**
- `POST /{content_id}/assign` - Assign to device or tag
- `GET /{content_id}/assignments` - Get all assignments
- `DELETE /{content_id}/assign` - Unassign from device/tag

**Content Serving:**
- `GET /{content_id}/image` - Proxy serve image with correct MIME type
- `GET /{content_id}/video` - Proxy serve video (with range request support)

**Integration:** Anthias (file storage), FFprobe (metadata extraction)
**Supported Types:** image, video
**Metadata Stored:** resolution, bitrate, fps, codec, duration, file_size

---

### 4. **tags.py** - Device Tags (11 endpoints)
**Location:** `/backend/app/api/tags.py`
**Prefix:** `/api/tags`
**Authentication:** Most require AUTH

**Tag CRUD:**
- `GET /` - List tags with device counts (sortable)
- `POST /` - Create tag
- `GET /{tag_id}` - Get tag details
- `PATCH /{tag_id}` - Update tag
- `DELETE /{tag_id}` - Delete tag

**Tag-Device Relations:**
- `POST /assign` - Assign tag to device
- `DELETE /assign` - Remove tag from device
- `GET /{tag_id}/devices` - Get devices with tag

**Content Relations:**
- `GET /{tag_id}/content` - Get content assigned to tag

**Tag Attributes:** tag_name (unique), description, color
**Sort Options:** newest, oldest, name_asc, name_desc

---

### 5. **playlists.py** - Playlist Management (8+ endpoints)
**Location:** `/backend/app/api/playlists.py`
**Prefix:** `/api/playlists`
**Authentication:** Most require AUTH

**Playlist CRUD:**
- `GET /` - List playlists with content count + duration
- `POST /` - Create playlist
- `GET /{playlist_id}` - Get playlist details
- `PATCH /{playlist_id}` - Update playlist
- `DELETE /{playlist_id}` - Delete playlist

**Playlist Properties:** name, description, is_active, priority, schedule
**Calculated:** content_count, total_duration

---

### 6. **activities.py** - Activity Logging (5 endpoints)
**Location:** `/backend/app/api/activities.py`
**Prefix:** `/api` (activities routes)
**Authentication:** All require AUTH

**Activity Queries:**
- `GET /activities` - List activities with filters (action_type, entity_type, date range, user)
- `GET /activities/stats` - Get statistics (today, week, month, by_type, by_entity)
- `GET /activities/{activity_id}` - Get specific activity

**Activity Management:**
- `POST /activities` - Create activity log entry (for manual logging)
- `DELETE /activities/cleanup` - Delete old activities (retention policy)

**Tracked Actions:** DEVICE_APPROVED, CONTENT_UPLOADED, etc.
**Entity Types:** device, content, playlist, tag, system
**Data Captured:** user_id, timestamp, ip_address, user_agent, details

---

### 7. **settings.py** - System Settings (4 endpoints)
**Location:** `/backend/app/api/settings.py`
**Prefix:** `/api/settings`
**Authentication:** All require AUTH

**System Information:**
- `GET /system/info` - Backend/database uptime, version, environment
- `GET /system/backup` - Create + download SQL backup
- `POST /system/clear-cache` - Clear connection pool + caches
- `GET /system/database-stats` - Table sizes, row counts, indexes

**Metrics Returned:** 
- Backend uptime, restart count
- Database uptime, restart count
- Database size, media storage used
- Python version, environment type

---

### 8. **logs.py** - Device Console Logs (4 endpoints)
**Location:** `/backend/app/api/logs.py`
**Prefix:** `/api` (logs routes)
**Authentication:** POST endpoints NO AUTH, GET/DELETE require AUTH

**Client Endpoints (NO AUTH):**
- `POST /client/logs` - Submit single log from device
- `POST /client/logs/batch` - Submit multiple logs in batch

**Admin Endpoints (AUTH):**
- `GET /devices/{device_id}/logs` - Get device logs with filters
- `DELETE /devices/{device_id}/logs` - Delete device logs

**Log Levels:** log, warn, error, info
**Storage:** Redis (real-time) + PostgreSQL (persistent)
**Retention:** 24 hours (auto-cleanup)

---

### 9. **speedtest.py** - Network Speed Testing (5 endpoints)
**Location:** `/backend/app/api/speedtest.py`
**Prefix:** `/api/speedtest`
**Authentication:** Upload/download NO AUTH, results/history mostly AUTH optional

**Speed Test Utilities:**
- `POST /upload` - Receive data (discarded) for upload speed measurement
- `GET /download` - Return dummy data for download speed measurement (default 1MB)

**Results Storage:**
- `POST /devices/{device_id}/speedtest` - Store test result (NO AUTH)
- `GET /devices/{device_id}/speedtest` - Get test history
- `GET /devices/{device_id}/speedtest/latest` - Get most recent test

**Quality Calculation:**
- Good: Download ≥25 Mbps AND Upload ≥10 Mbps
- Fair: Download ≥10 Mbps AND Upload ≥5 Mbps
- Poor: Below fair

**Retention Policy:** Keep last 100 tests per device (auto-delete older)

---

### 10. **firebird.py** - Firebird Database Integration (6+ endpoints)
**Location:** `/backend/app/api/firebird.py`
**Prefix:** `/api/firebird`
**Authentication:** All require AUTH

**Configuration Management:**
- `POST /configs` - Create Firebird config (encrypts API key)
- `GET /configs` - List configs with filters
- `GET /configs/{config_id}` - Get specific config
- `PATCH /configs/{config_id}` - Update config
- `DELETE /configs/{config_id}` - Delete config

**Operations:**
- `POST /configs/{config_id}/test` - Test connection
- `POST /query` - Execute read-only SELECT query
- `GET /health` - Health status of all configs

**Security:** 
- Encrypted credential storage
- Read-only queries only (SQL injection prevention)
- Connection pooling with resource limits

---

### 11. **client.py** - Client/Device Endpoints (2 endpoints)
**Location:** `/backend/app/api/client.py`
**Prefix:** `/api/client`
**Authentication:** Both NO AUTH (for device clients)

**Viewer Endpoints:**
- `GET /playlist` - Get device's content playlist
  - Returns: Anthias static file URLs for content
  - Deduplicates content (device + tag assignments)
  - Sorted by priority (highest first)
  
- `GET /status` - Check device status
  - Returns: active/pending/inactive, is_active flag
  - Used by devices to verify authorization

**Content Resolution:** Direct > Playlist > Tag based on priority

---

### 12. **auth.py** (Advanced) - Not Main Auth Router
**Helper Dependencies:** Used by other routers for `get_current_user`, `get_current_active_user`, `get_optional_user`

---

### 13. **websocket.py** - WebSocket Support
**Location:** `/backend/app/api/websocket.py`
**Status:** Minimal implementation (for future real-time features)

---

### 14. **quickwins_demo.py** - Demo Endpoints (DEBUG mode only)
**Location:** `/backend/app/api/quickwins_demo.py`
**Prefix:** `/api/demo` (when DEBUG=true)
**Purpose:** Showcase Quick Wins patterns

---

### 15. **v1/organizations.py** - Organizations (Legacy)
**Location:** `/backend/app/api/v1/organizations.py`
**Status:** Not currently registered in main.py

---

## Endpoint Statistics

```
Total Router Files:          15
Active Routers:              13 (registered in main.py)
Total API Endpoints:         ~90-100 endpoints

Breakdown by Function:
- Device Management:         20+ endpoints
- Content Management:        11 endpoints
- Tags:                      11 endpoints
- Playlists:                 8+ endpoints
- Activities:                5 endpoints
- Speed Test:                5 endpoints
- Device Logs:               4 endpoints
- Settings/System:           4 endpoints
- Firebird Integration:      6+ endpoints
- Client/Device:             2 endpoints
- Authentication:            4 endpoints
- Root/Health:               3 endpoints
```

---

## Authentication & Security

### JWT Authentication
- **Access Token Duration:** 30 minutes (configurable)
- **Refresh Token Duration:** 7 days (configurable)
- **Token Type:** Bearer token in Authorization header
- **Hash Algorithm:** HS256

### Endpoints Without Authentication (NO AUTH)
These are called by device clients (which don't have auth tokens):
- Monitor registration and activation
- Device heartbeat submission
- Activation code checking
- Pending command retrieval and execution
- Client playlist fetching
- Device status checking
- Speed test upload/download
- Speed test result submission
- Device log submission (batch and single)

### Endpoints Requiring Authentication
All administrative endpoints for:
- User info retrieval
- Device management
- Content management
- Tag management
- Playlist management
- Activity logs
- System settings
- Device log admin operations
- Speed test history
- Firebird integration

---

## Database Models Involved

### Core Models:
1. **User** - Admin/management users
2. **Device** - TV/Monitor devices
3. **Content** - Images/videos (stored in Anthias)
4. **Tag** - Device grouping tags
5. **DeviceTag** - Device-to-tag many-to-many relationship
6. **ContentAssignment** - Content-to-device/tag assignments
7. **Playlist** - Content playlists
8. **PlaylistContent** - Playlist-to-content items
9. **PlaylistAssignment** - Playlist-to-device assignments
10. **Schedule** - Time-based scheduling
11. **DeviceCommand** - Remote command queue
12. **DeviceLog** - Console logs from devices
13. **ActivityLog** - System activity audit trail
14. **DeviceSpeedTest** - Network speed test results
15. **FirebirdConfig** - Firebird database integrations

---

## Quick Reference by Router

### Router Priority (by frequency of use)
1. **devices.py** - Core device management (TV/Monitor registration, heartbeat)
2. **content.py** - Content upload, assignment, serving
3. **client.py** - Used by viewers constantly (playlist, status)
4. **tags.py** - Device grouping and content assignment
5. **activities.py** - Audit logging
6. **playlists.py** - Content organization
7. **logs.py** - Device console debugging
8. **settings.py** - System administration
9. **speedtest.py** - Network diagnostics
10. **firebird.py** - Legacy database integration
11. **auth.py** - Admin authentication
12. **websocket.py** - Future real-time features
13. **quickwins_demo.py** - Development/demo only
14. **v1/organizations.py** - Legacy, not active

---

## Key Design Patterns

### 1. Content Resolution Hierarchy
**Priority Order:**
1. Device-specific content assignments
2. Playlist assignments to device
3. Tag-based content (content assigned to device's tags)

### 2. Device Lifecycle
```
Self-Register (monitor_register) 
  → Pending (waiting for approval)
  → Activate (monitor_activate or admin approval)
  → Active (receiving content/commands)
  → Release (admin action, becomes inactive)
  → Delete (cascades all assignments)
```

### 3. Command Queue System
- Commands queued for devices
- Devices poll pending commands via heartbeat
- Commands executed client-side
- Execution status reported back
- Auto-expire after 7 days

### 4. Real-time Monitoring
- Heartbeat every 30-60 seconds
- Device online/offline determined by last_seen < 5 min
- Activity logging for all admin actions
- Speed test trend monitoring

---

## Integration Points

### External Services:
1. **Anthias** - File storage and serving
2. **PostgreSQL** - Primary data store
3. **Redis** - Real-time log streaming (optional)
4. **Firebird** - Legacy database queries (optional)

### Internal Dependencies:
- **StructuredLogger** - All routers use for logging
- **Custom Exceptions** - NotFoundException, BadRequestException, etc.
- **Request ID Middleware** - All requests tracked
- **CORS Middleware** - Cross-origin support

---

## Standardization

### Response Format (All Endpoints):
```json
{
  "success": true,
  "data": { ... },
  "request_id": "uuid"
}
```

### Pagination (List Endpoints):
```json
{
  "success": true,
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 50,
    "items": [ ... ]
  }
}
```

### Error Format:
```json
{
  "detail": "Error message",
  "error_type": "ExceptionType",
  "status_code": 400,
  "request_id": "uuid"
}
```

---

## Testing Notes

### Key Endpoints for Testing:
- **Health Check:** `GET /health`
- **API Docs:** `GET /docs` (Swagger UI)
- **Ping:** `GET /api/ping`

### Demo Endpoints (DEBUG mode):
- `GET /api/demo/*` - Quick Wins pattern examples
- `GET /debug/settings` - Current configuration

---

## File Size Reference
**API code total:** ~30KB across 15 router files
**Documentation:** Complete at `/API_ENDPOINTS_DOCUMENTATION.md`

