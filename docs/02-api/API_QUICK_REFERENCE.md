# API Quick Reference Guide

**Last Updated:** October 28, 2025
**Documentation Files:**
- `API_ENDPOINTS_DOCUMENTATION.md` - Comprehensive endpoint reference (30KB)
- `API_STRUCTURE_SUMMARY.md` - Router overview and architecture (16KB)

---

## Absolute Path Guide

All files are located at `/mnt/g/khoirul/signate/backend/app/api/`

| Router File | Endpoints | Auth | Primary Use |
|---|---|---|---|
| **auth.py** | 4 | Mixed | User login/logout |
| **devices.py** | 20+ | Mixed | Device registration, heartbeat, commands |
| **content.py** | 11 | Required | Upload, manage, serve content |
| **tags.py** | 11 | Required | Group devices with tags |
| **playlists.py** | 8+ | Required | Create content playlists |
| **activities.py** | 5 | Required | Audit activity logs |
| **settings.py** | 4 | Required | System info, backup, cache |
| **logs.py** | 4 | Mixed | Device console logs |
| **speedtest.py** | 5 | Mixed | Network speed testing |
| **firebird.py** | 6+ | Required | Firebird DB integration |
| **client.py** | 2 | None | Viewer endpoints |
| **websocket.py** | TBD | - | Real-time features |

---

## Most Important Endpoints

### Device Registration Flow
```
1. POST /api/devices/monitor
   → Returns: unique_code, code_expires_at
   
2. POST /api/devices/monitor/register (NO AUTH)
   → Device sends: activation_code, device_name, platform
   → Returns: device object with status="pending"
   
3. POST /api/devices/monitor/activate (NO AUTH)
   → Device sends: unique_code
   → Returns: device object with status="active"
```

### Device Heartbeat
```
POST /api/devices/heartbeat (NO AUTH)
- Called by device every 30-60 seconds
- Updates: last_seen, ip_address, platform info
- Returns: device status + rotation/volume settings
```

### Content to Viewer
```
1. GET /api/client/playlist?device_id=1 (NO AUTH)
   → Returns: Content with Anthias URLs
   
2. Browser/Player fetches content directly from:
   http://192.168.5.12:8000/screenly_assets/{filename}
```

### Administrative Commands
```
1. POST /api/devices/{id}/commands/reset
   → Queue reset command
   
2. Device polls: GET /api/devices/{id}/commands/pending (NO AUTH)
   → Gets pending commands
   
3. Device executes and reports:
   POST /api/devices/{id}/commands/{cmd_id}/execute (NO AUTH)
```

---

## Authentication

### Login
```bash
curl -X POST http://192.168.5.12:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
```

### Response
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

### Using Token
```bash
curl http://192.168.5.12:8001/api/devices \
  -H "Authorization: Bearer {access_token}"
```

---

## Common Operations

### List Devices
```
GET /api/devices?skip=0&limit=100&device_type=monitor&status_filter=active
```

### Create Content
```
POST /api/content/upload
- multipart/form-data
- Fields: file, title, description, duration, is_active
```

### Assign Content to Device
```
POST /api/content/{content_id}/assign
{
  "device_id": 1,
  "priority": 10
}
```

### Create Tag
```
POST /api/tags
{
  "tag_name": "floor1",
  "description": "First floor",
  "color": "#FF5733"
}
```

### Assign Tag to Device
```
POST /api/tags/assign
{
  "tag_id": 1,
  "device_id": 1
}
```

---

## Response Format

### Success (200/201/204)
```json
{
  "success": true,
  "data": { ... },
  "request_id": "uuid"
}
```

### Paginated
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

### Error (4xx/5xx)
```json
{
  "detail": "Error message",
  "status_code": 404,
  "request_id": "uuid"
}
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 410 | Gone (expired) |
| 500 | Server Error |

---

## Device Statuses

| Status | Meaning |
|--------|---------|
| **pending** | Waiting for admin approval |
| **active** | Receiving content & commands |
| **inactive** | Released, awaiting reactivation |

---

## Command Types

| Type | Effect |
|------|--------|
| **reset** | Clear storage, generate new code |
| **reload** | Reload page to fetch new code |
| **refresh** | Refresh content (partial reload) |
| **run_speed_test** | Execute network speed test |

---

## Device Lifecycle

```
Monitor Device:
┌─────────────────┐
│ Self-Register   │ (NO AUTH) POST /monitor/register
│ Status: pending │
└────────┬────────┘
         │
         │ Admin approves in Web Admin
         ↓
┌─────────────────┐
│ Poll Activation │ (NO AUTH) GET /check-activation/{code}
└────────┬────────┘
         │
         │ User taps activation code
         ↓
┌─────────────────┐
│ Activate        │ (NO AUTH) POST /monitor/activate
│ Status: active  │
└────────┬────────┘
         │
         │ Device comes online
         ↓
┌─────────────────┐
│ Send Heartbeat  │ (NO AUTH) POST /heartbeat
│ Fetch Playlist  │ (NO AUTH) GET /client/playlist
│ Poll Commands   │ (NO AUTH) GET /commands/pending
└─────────────────┘
```

---

## Key Files to Reference

### Complete Documentation
- `/mnt/g/khoirul/signate/API_ENDPOINTS_DOCUMENTATION.md` (30KB)
  - Every endpoint with request/response examples
  - All query parameters
  - Error codes and messages

### Architecture Overview
- `/mnt/g/khoirul/signate/API_STRUCTURE_SUMMARY.md` (16KB)
  - 15 router modules explained
  - Database models
  - Design patterns
  - Integration points

### Code Location
- `/mnt/g/khoirul/signate/backend/app/api/` (15 router files)
  - Each file 1-3KB
  - FastAPI routers with endpoints
  - Structured logging
  - Custom exception handling

---

## Testing

### Health Check
```bash
curl http://192.168.5.12:8001/health
```

### API Docs
```
http://192.168.5.12:8001/docs
```

### Ping
```bash
curl http://192.168.5.12:8001/api/ping
```

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Missing/invalid token | Login and get new token |
| 404 Not Found | Device/content doesn't exist | Check ID in URL |
| 409 Conflict | Resource already exists | Use different name/ID |
| 410 Gone | Code expired | Generate new code |
| 400 Bad Request | Invalid parameters | Check request format |

---

## API Base URL

**Production:** `http://192.168.5.12:8001`
**Port:** 8001
**Health:** `/health`
**Docs:** `/docs`

---

## Related Documentation

See `/CLAUDE.md` for:
- Server information and deployment
- Service ports and URLs
- CORS configuration
- Development setup
- Synchronization requirements

---

## Quick Stats

- **Total Endpoints:** ~90-100
- **Authentication Required:** ~65%
- **No Authentication:** ~35% (device clients)
- **Average Response Time:** <100ms
- **Database:** PostgreSQL
- **Cache:** Redis (optional)
- **External Storage:** Anthias

