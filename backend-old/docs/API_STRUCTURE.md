# Smart TV Digital Signage API - Structure Overview

## API Hierarchy and Organization

```
Smart TV Digital Signage API (92 endpoints)
├── Authentication (4 endpoints) ✅
│   ├── POST /api/auth/login - User login
│   ├── POST /api/auth/refresh - Refresh access token
│   ├── GET /api/auth/me - Get current user
│   └── POST /api/auth/logout - Logout (client-side)
│
├── Devices (20 endpoints) ✅
│   ├── Registration & Lifecycle
│   │   ├── POST /api/devices/monitor/register - Self-registration (NO AUTH)
│   │   ├── POST /api/devices/monitor - Generate activation code
│   │   ├── POST /api/devices/tv - Register TV device
│   │   ├── POST /api/devices/monitor/activate - Activate device (NO AUTH)
│   │   ├── GET /api/devices/check-activation/{code} - Check status (NO AUTH)
│   │   └── POST /api/devices/{id}/release - Release device
│   │
│   ├── Management
│   │   ├── GET /api/devices - List all devices
│   │   ├── GET /api/devices/{id} - Get device details
│   │   ├── PUT /api/devices/{id} - Update device
│   │   ├── DELETE /api/devices/{id} - Delete device
│   │   └── POST /api/devices/{id}/replace-with-pending/{pending_id} - Replace device
│   │
│   ├── Monitoring
│   │   ├── POST /api/devices/heartbeat - Device heartbeat (NO AUTH)
│   │   └── GET /api/devices/{id}/preview - Content preview
│   │
│   ├── Remote Commands
│   │   ├── POST /api/devices/{id}/commands - Queue command
│   │   ├── POST /api/devices/{id}/commands/reset - Queue reset
│   │   ├── GET /api/devices/{id}/commands/pending - Get commands (NO AUTH)
│   │   └── POST /api/devices/{id}/commands/{cmd_id}/execute - Mark executed (NO AUTH)
│   │
│   └── Content Assignment
│       ├── GET /api/devices/{id}/content - Get device content
│       ├── POST /api/devices/{id}/content - Assign content
│       └── DELETE /api/devices/{id}/content/{content_id} - Unassign content
│
├── Content (10 endpoints) ✅
│   ├── CRUD Operations
│   │   ├── POST /api/content/upload - Upload media file
│   │   ├── GET /api/content - List all content
│   │   ├── GET /api/content/{id} - Get content details
│   │   ├── PATCH /api/content/{id} - Update content
│   │   └── DELETE /api/content/{id} - Delete content
│   │
│   ├── Assignment Management
│   │   ├── POST /api/content/{id}/assign - Assign to device/tag
│   │   ├── DELETE /api/content/{id}/assign - Unassign
│   │   └── GET /api/content/{id}/assignments - Get all assignments
│   │
│   └── Media Serving
│       ├── GET /api/content/{id}/image - Serve image file
│       └── GET /api/content/{id}/video - Serve video file
│
├── Playlists (14 endpoints) ✅
│   ├── Playlist CRUD
│   │   ├── GET /api/playlists - List all playlists
│   │   ├── POST /api/playlists - Create playlist
│   │   ├── GET /api/playlists/{id} - Get playlist details
│   │   ├── PATCH /api/playlists/{id} - Update playlist
│   │   └── DELETE /api/playlists/{id} - Delete playlist
│   │
│   ├── Content Management
│   │   ├── GET /api/playlists/{id}/content - Get playlist content
│   │   ├── POST /api/playlists/{id}/content - Add content
│   │   ├── DELETE /api/playlists/{id}/content/{item_id} - Remove content
│   │   └── PATCH /api/playlists/{id}/reorder - Reorder content
│   │
│   └── Assignment Management
│       ├── GET /api/playlists/{id}/assignments - Get assignments
│       ├── POST /api/playlists/{id}/assign/devices - Assign to devices
│       ├── POST /api/playlists/{id}/assign/tags - Assign to tags
│       ├── DELETE /api/playlists/{id}/assign/devices - Unassign from devices
│       └── DELETE /api/playlists/{id}/assign/tags - Unassign from tags
│
├── Tags (9 endpoints) ✅
│   ├── Tag CRUD
│   │   ├── GET /api/tags - List all tags
│   │   ├── POST /api/tags - Create tag
│   │   ├── GET /api/tags/{id} - Get tag details
│   │   ├── PATCH /api/tags/{id} - Update tag
│   │   └── DELETE /api/tags/{id} - Delete tag
│   │
│   └── Device Assignment
│       ├── POST /api/tags/{id}/assign - Assign devices to tag
│       ├── DELETE /api/tags/{id}/assign - Remove devices from tag
│       ├── GET /api/tags/{id}/devices - Get tag devices
│       └── GET /api/tags/{id}/content - Get tag content
│
├── Client (2 endpoints) ✅ (NO AUTH REQUIRED)
│   ├── GET /api/client/playlist - Get device playlist
│   └── GET /api/client/status - Get device status
│
├── Settings (4 endpoints) ✅
│   ├── GET /api/settings/system - Get system settings
│   ├── PUT /api/settings/system - Update system settings
│   ├── GET /api/settings/anthias - Get Anthias settings
│   └── PUT /api/settings/anthias - Update Anthias settings
│
├── Device Logs (4 endpoints) ✅
│   ├── GET /api/devices/{id}/logs - Get device logs
│   ├── POST /api/devices/{id}/logs - Create log entry (NO AUTH)
│   ├── DELETE /api/devices/{id}/logs - Delete device logs
│   └── GET /api/logs - Get all logs (admin)
│
├── Speed Test (5 endpoints) ✅
│   ├── POST /api/speedtest/run - Run speed test
│   ├── GET /api/speedtest/results/{id} - Get test results
│   ├── GET /api/speedtest/history - Get test history
│   ├── DELETE /api/speedtest/results/{id} - Delete result
│   └── GET /api/speedtest/device/{device_id}/history - Get device history
│
├── Firebird Integration (8 endpoints) ⚠️ (Optional)
│   ├── POST /api/firebird/connect - Test connection
│   ├── GET /api/firebird/configs - List configs
│   ├── POST /api/firebird/configs - Create config
│   ├── GET /api/firebird/configs/{id} - Get config
│   ├── PUT /api/firebird/configs/{id} - Update config
│   ├── DELETE /api/firebird/configs/{id} - Delete config
│   ├── POST /api/firebird/sync - Sync data
│   └── GET /api/firebird/status - Get sync status
│
├── WebSocket (1 endpoint) ✅
│   └── WS /api/ws/{device_id} - WebSocket connection
│
├── Quick Wins Demo (8 endpoints) ℹ️ (DEBUG MODE ONLY)
│   ├── GET /api/demo/success - Success response example
│   ├── GET /api/demo/error - Error response example
│   ├── GET /api/demo/validation-error - Validation error example
│   ├── GET /api/demo/not-found - 404 error example
│   ├── GET /api/demo/server-error - 500 error example
│   ├── GET /api/demo/pagination - Pagination example
│   ├── POST /api/demo/create - Create example
│   └── GET /api/demo/with-meta - Response with metadata
│
└── System (4 endpoints) ✅ (NO AUTH REQUIRED)
    ├── GET / - API info
    ├── GET /health - Health check
    ├── GET /api/ping - Ping endpoint
    └── GET /debug/settings - Debug settings (DEBUG mode)
```

## Endpoint Statistics

### By HTTP Method

| Method | Count | Usage |
|--------|-------|-------|
| GET | 35 | 38.0% - Data retrieval |
| POST | 35 | 38.0% - Create/Actions |
| DELETE | 10 | 10.9% - Remove resources |
| PATCH | 7 | 7.6% - Partial updates |
| PUT | 5 | 5.4% - Full updates |

### By Authentication

| Type | Count | Percentage |
|------|-------|------------|
| **Auth Required** | 70 | 76.1% |
| **No Auth** | 22 | 23.9% |

### No Auth Endpoints (22)

**Device Operations (15):**
- POST /api/devices/monitor/register
- POST /api/devices/monitor/activate
- GET /api/devices/check-activation/{code}
- POST /api/devices/heartbeat
- GET /api/devices/{id}/commands/pending
- POST /api/devices/{id}/commands/{cmd_id}/execute
- POST /api/devices/{id}/logs

**Client Operations (2):**
- GET /api/client/playlist
- GET /api/client/status

**System Operations (4):**
- GET /
- GET /health
- GET /api/ping
- GET /debug/settings

**Demo Operations (8, DEBUG only):**
- All /api/demo/* endpoints

### By Category Priority

| Priority | Categories | Endpoints |
|----------|-----------|-----------|
| **Core** | Devices, Content, Playlists, Tags | 53 (57.6%) |
| **Essential** | Authentication, Client, Settings | 10 (10.9%) |
| **Monitoring** | Device Logs, Speed Test | 9 (9.8%) |
| **Optional** | Firebird Integration | 8 (8.7%) |
| **System** | WebSocket, Health, Demo | 13 (14.1%) |

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     WEB ADMIN (React)                        │
│                    http://localhost:3000                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ JWT Bearer Auth
                       │ HTTP/REST
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              BACKEND API (FastAPI)                           │
│              http://192.168.5.12:8001                        │
├──────────────────────────────────────────────────────────────┤
│  Auth        │ Devices    │ Content   │ Playlists  │ Tags   │
│  (4 eps)     │ (20 eps)   │ (10 eps)  │ (14 eps)   │ (9 eps)│
└────┬─────────┴──────┬─────┴─────┬─────┴──────┬─────┴────┬───┘
     │                │           │            │          │
     │                ↓           ↓            ↓          │
     │         ┌──────────────────────────────────┐       │
     │         │    PostgreSQL Database           │       │
     │         │    port 5433                     │       │
     │         │    - Users, Devices, Content     │       │
     │         │    - Playlists, Tags, Logs       │       │
     │         └──────────────────────────────────┘       │
     │                                                     │
     │                ┌─────────────────────┐             │
     │                │  Anthias CMS        │             │
     │                │  port 8000          │             │
     │                │  - Media Storage    │             │
     │                │  - File Management  │             │
     │                └─────────────────────┘             │
     │                                                     │
     └───────────────────────────────────────────────────┘
                       │ NO AUTH
                       │ HTTP/REST
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                  VIEWER (Device Client)                      │
│                  http://192.168.5.12:8080                    │
├──────────────────────────────────────────────────────────────┤
│  - Self-registration (POST /devices/monitor/register)       │
│  - Heartbeat (POST /devices/heartbeat) every 30s            │
│  - Poll commands (GET /devices/{id}/commands/pending)       │
│  - Fetch playlist (GET /client/playlist)                    │
└──────────────────────────────────────────────────────────────┘
         │                │                │
         ↓                ↓                ↓
    ┌─────────┐    ┌──────────┐    ┌──────────┐
    │ Chrome  │    │  webOS   │    │ Firefox  │
    │ Browser │    │  TV      │    │ Browser  │
    └─────────┘    └──────────┘    └──────────┘
```

## Request/Response Flow

### 1. Device Registration Flow

```
Viewer                    API                     Database
  │                        │                         │
  │ Generate 6-digit code  │                         │
  │────────────────────────│                         │
  │                        │                         │
  │ POST /devices/monitor/register                   │
  │  {activation_code, device_name}                  │
  │───────────────────────→│                         │
  │                        │ INSERT device (pending) │
  │                        │────────────────────────→│
  │                        │←────────────────────────│
  │←───────────────────────│                         │
  │ 201 Created (device_id)│                         │
  │                        │                         │
  │ Poll every 5s          │                         │
  │ GET /check-activation/{code}                     │
  │───────────────────────→│ SELECT device           │
  │                        │────────────────────────→│
  │                        │←────────────────────────│
  │←───────────────────────│                         │
  │ {"activated": false}   │                         │
  │                        │                         │
```

### 2. Content Upload Flow

```
Admin                     API                 Anthias             Database
  │                        │                     │                  │
  │ POST /content/upload   │                     │                  │
  │  multipart/form-data   │                     │                  │
  │───────────────────────→│                     │                  │
  │                        │ Upload file         │                  │
  │                        │────────────────────→│                  │
  │                        │←────────────────────│                  │
  │                        │ (asset_id, URL)     │                  │
  │                        │                     │                  │
  │                        │ Extract metadata (FFprobe)             │
  │                        │────────────────────────────────────────│
  │                        │                     │                  │
  │                        │ INSERT content      │                  │
  │                        │─────────────────────────────────────→ │
  │                        │←────────────────────────────────────── │
  │←───────────────────────│                     │                  │
  │ 201 Created (content)  │                     │                  │
```

### 3. Heartbeat Flow

```
Viewer                    API                     Database
  │                        │                         │
  │ POST /devices/heartbeat│                         │
  │  {device_id, screen_info}                        │
  │───────────────────────→│                         │
  │                        │ UPDATE device           │
  │                        │  SET last_seen = NOW()  │
  │                        │────────────────────────→│
  │                        │←────────────────────────│
  │←───────────────────────│                         │
  │ 200 OK (rotation, volume)                        │
  │                        │                         │
  │ GET /devices/{id}/commands/pending               │
  │───────────────────────→│                         │
  │                        │ SELECT commands         │
  │                        │  WHERE status='pending' │
  │                        │────────────────────────→│
  │                        │←────────────────────────│
  │←───────────────────────│                         │
  │ 200 OK (commands[])    │                         │
  │                        │                         │
  │ Execute command        │                         │
  │ POST /devices/{id}/commands/{cmd_id}/execute     │
  │───────────────────────→│                         │
  │                        │ UPDATE command          │
  │                        │  SET status='executed'  │
  │                        │────────────────────────→│
  │                        │←────────────────────────│
  │←───────────────────────│                         │
  │ 200 OK                 │                         │
```

## Resource Relationships

```
User (Admin)
  │
  │ creates/manages
  │
  ├──→ Content (Media Files)
  │     │
  │     │ assigned to
  │     │
  │     ├──→ Device (direct assignment)
  │     │     │
  │     │     │ has
  │     │     ├──→ Tags
  │     │     ├──→ Playlists
  │     │     ├──→ Device Logs
  │     │     ├──→ Device Commands
  │     │     └──→ Speed Test Results
  │     │
  │     └──→ Tag (tag-based assignment)
  │           │
  │           │ applied to
  │           └──→ Devices (many)
  │
  └──→ Playlist
        │
        │ contains
        ├──→ Content Items (ordered)
        │
        │ assigned to
        ├──→ Devices (direct)
        └──→ Tags (bulk)
```

## API Conventions

### URL Structure
```
/api/{category}/{resource}/{id}/{sub-resource}/{sub-id}/{action}

Examples:
/api/devices/1/content - Device content
/api/devices/1/commands/pending - Pending commands
/api/playlists/1/assign/devices - Assign playlist to devices
/api/content/1/image - Serve image file
```

### Response Format (Quick Wins)

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2025-10-27T10:30:00Z",
    "request_id": "uuid-v4"
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": { ... }
  },
  "meta": {
    "timestamp": "2025-10-27T10:30:00Z",
    "request_id": "uuid-v4"
  }
}
```

### Naming Conventions

- **Endpoints:** lowercase with hyphens (`/check-activation`, `/speed-test`)
- **JSON keys:** snake_case (`device_name`, `content_type`)
- **Resource IDs:** `{resource}_id` in requests, `id` in responses
- **Collections:** plural nouns (`/devices`, `/playlists`)
- **Actions:** verb at end (`/assign`, `/execute`, `/release`)

---

**Last Updated:** 2025-10-27
**API Version:** 1.0.0
