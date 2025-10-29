# Smart TV Digital Signage - Backend API Documentation

## Overview
Complete API endpoint documentation for the Digital Signage Backend (FastAPI).
- Base URL: `http://192.168.5.12:8001`
- API Docs: `http://192.168.5.12:8001/docs` (if enabled)

---

## Table of Contents
1. [Authentication Endpoints](#authentication-endpoints)
2. [Device Management Endpoints](#device-management-endpoints)
3. [Content Management Endpoints](#content-management-endpoints)
4. [Tags Endpoints](#tags-endpoints)
5. [Playlists Endpoints](#playlists-endpoints)
6. [Activities/Logs Endpoints](#activities-logs-endpoints)
7. [Settings/System Endpoints](#settings-system-endpoints)
8. [Device Logs Endpoints](#device-logs-endpoints)
9. [Speed Test Endpoints](#speed-test-endpoints)
10. [Firebird Integration Endpoints](#firebird-integration-endpoints)
11. [Client Endpoints](#client-endpoints)
12. [Root & Health Endpoints](#root--health-endpoints)

---

## Authentication Endpoints
**Prefix:** `/api/auth`

### POST /api/auth/login
Login endpoint - authenticate user and return JWT tokens

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "token_type": "bearer",
    "expires_in": 3600
  },
  "request_id": "string"
}
```

**Errors:**
- `401`: Invalid credentials
- `403`: Inactive user

---

### POST /api/auth/refresh
Refresh access token using refresh token

**Request:**
```json
{
  "refresh_token": "string"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access_token": "string",
    "refresh_token": "string",
    "token_type": "bearer",
    "expires_in": 3600
  },
  "request_id": "string"
}
```

---

### GET /api/auth/me
Get current authenticated user information

**Response (200):**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "is_active": true,
  "is_superuser": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

**Errors:**
- `401`: Not authenticated

---

### POST /api/auth/logout
Logout endpoint (token invalidation handled client-side)

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

---

## Device Management Endpoints
**Prefix:** `/api/devices`

### GET /api/devices
List all devices with optional filters

**Query Parameters:**
- `skip` (int, default: 0): Pagination offset
- `limit` (int, default: 100): Page size
- `device_type` (string): Filter by type (tv/monitor)
- `status_filter` (string): Filter by status (pending/active/inactive)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total": 10,
    "page": 1,
    "page_size": 100,
    "items": [
      {
        "id": 1,
        "device_type": "monitor",
        "device_name": "Device 1",
        "ip_address": "192.168.1.100",
        "unique_code": "123456",
        "code_expires_at": "2025-10-28T14:30:00Z",
        "platform": "Chrome",
        "model_name": "Dell Monitor",
        "firmware_version": "1.0",
        "status": "active",
        "last_seen": "2025-10-28T14:20:00Z",
        "created_at": "2025-10-25T10:00:00Z",
        "updated_at": "2025-10-28T14:20:00Z",
        "screen_width": 1920,
        "screen_height": 1080,
        "viewport_width": 1920,
        "viewport_height": 1000,
        "device_pixel_ratio": 1,
        "user_agent": "Mozilla/5.0...",
        "connection_type": "ethernet",
        "connection_speed": "1000",
        "rotation": 0,
        "volume_enabled": false,
        "tags": [
          {
            "id": 1,
            "tag_name": "floor1",
            "color": "#FF5733"
          }
        ],
        "playlists": [
          {
            "id": 1,
            "name": "Morning Playlist",
            "description": "Content for morning hours",
            "is_active": true,
            "priority": 1
          }
        ]
      }
    ]
  },
  "request_id": "string"
}
```

---

### GET /api/devices/{device_id}
Get device by ID

**Response (200):** Same as individual device in list above

---

### GET /api/devices/{device_id}/preview
Get content preview for a device with resolution breakdown

**Query Parameters:**
- `preview_time` (string, ISO 8601): Specific time to preview (default: now)
- `include_inactive` (bool, default: false): Include inactive content

**Response (200):**
```json
{
  "device_id": 1,
  "device_name": "Device 1",
  "preview_time": "2025-10-28T14:30:00Z",
  "resolution_algorithm": "SEQUENTIAL_PRIORITY",
  "direct_content": [...],
  "playlist_content": [...],
  "tag_content": [...],
  "final_playlist": [...]
}
```

---

### POST /api/devices/tv
Register a new TV device

**Request:**
```json
{
  "device_name": "TV Room 1",
  "ip_address": "192.168.1.50",
  "passphrase": "secret"
}
```

**Response (201):**
Device object (same as GET /api/devices/{device_id})

**Errors:**
- `409`: IP already registered

---

### POST /api/devices/monitor
Generate activation code for monitor device

**Request:**
```json
{
  "device_name": "Monitor 1"
}
```

**Response (201):**
```json
{
  "device_id": 1,
  "device_name": "Monitor 1",
  "unique_code": "123456",
  "code_expires_at": "2025-10-28T14:10:00Z",
  "status": "pending"
}
```

---

### POST /api/devices/monitor/register
Self-registration endpoint for monitor devices (NO AUTH)

**Request:**
```json
{
  "activation_code": "123456",
  "device_name": "Monitor 1",
  "platform": "Chrome",
  "model_name": "Dell Monitor"
}
```

**Response (201):**
Device object

**Errors:**
- `409`: Activation code already exists

---

### POST /api/devices/monitor/activate
Activate monitor using activation code (NO AUTH)

**Request:**
```json
{
  "unique_code": "123456"
}
```

**Response (200):**
Device object with status="active"

**Errors:**
- `404`: Invalid code
- `409`: Already activated
- `410`: Code expired

---

### PUT /api/devices/{device_id}
Update device information

**Request (partial update):**
```json
{
  "device_name": "New Name",
  "status": "active",
  "rotation": 90,
  "volume_enabled": true
}
```

**Response (200):**
Device object

---

### DELETE /api/devices/{device_id}
Delete device (queues reset command before deletion)

**Response (204):** No content

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Device {id} deleted successfully"
  }
}
```

---

### POST /api/devices/{device_id}/release
Release device (reset but keep record)

**Response (200):**
Device object with status="inactive"

---

### POST /api/devices/{device_id}/replace-with-pending/{pending_device_id}
Replace target device's code with a pending device

**Response (200):**
Device object with new code

---

### GET /api/devices/check-activation/{activation_code}
Check if an activation code has been activated (NO AUTH)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "activated": true/false,
    "expired": false,
    "device_id": 1,
    "device_name": "Monitor 1",
    "message": "string"
  }
}
```

---

### POST /api/devices/heartbeat
Device heartbeat endpoint (NO AUTH)

**Request:**
```json
{
  "device_id": 1,
  "ip_address": "192.168.1.100",
  "platform": "Chrome",
  "model_name": "Dell",
  "firmware_version": "1.0",
  "screen_width": 1920,
  "screen_height": 1080,
  "viewport_width": 1920,
  "viewport_height": 1000,
  "device_pixel_ratio": 1,
  "user_agent": "Mozilla/5.0...",
  "connection_type": "ethernet",
  "connection_speed": "1000"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "device_id": 1,
    "status": "active",
    "last_seen": "2025-10-28T14:30:00Z",
    "message": "Heartbeat recorded successfully",
    "rotation": 0,
    "volume_enabled": false
  }
}
```

---

## Device Command Endpoints
**Prefix:** `/api/devices`

### POST /api/devices/{device_id}/commands
Queue a command for device

**Request:**
```json
{
  "command_type": "reset|refresh|reload|run_speed_test|etc",
  "reason": "manual_reset"
}
```

**Response (201):**
```json
{
  "id": 1,
  "device_id": 1,
  "command_type": "reset",
  "reason": "manual_reset",
  "status": "pending",
  "created_at": "2025-10-28T14:30:00Z",
  "executed_at": null,
  "expires_at": "2025-11-04T14:30:00Z"
}
```

---

### POST /api/devices/{device_id}/commands/reset
Queue a reset command for device

**Query Parameters:**
- `reason` (string, default: "manual_reset"): Reset reason

**Response (201):**
Command object

---

### GET /api/devices/{device_id}/commands/pending
Get pending commands for device (NO AUTH)

**Response (200):**
```json
{
  "commands": [
    {
      "id": 1,
      "device_id": 1,
      "command_type": "reset",
      "reason": "manual_reset",
      "status": "pending",
      "created_at": "2025-10-28T14:30:00Z",
      "executed_at": null,
      "expires_at": "2025-11-04T14:30:00Z"
    }
  ],
  "total": 1
}
```

---

### POST /api/devices/{device_id}/commands/{command_id}/execute
Mark command as executed (NO AUTH)

**Response (200):**
```json
{
  "message": "Command executed successfully",
  "command_id": 1,
  "device_id": 1,
  "executed_at": "2025-10-28T14:31:00Z"
}
```

---

## Content Assignment Endpoints
**Prefix:** `/api/devices`

### GET /api/devices/{device_id}/content
Get all content directly assigned to a device

**Response (200):**
```json
[
  {
    "id": 1,
    "content_id": 5,
    "device_id": 1,
    "tag_id": null,
    "priority": 10,
    "created_at": "2025-10-28T14:30:00Z"
  }
]
```

---

### POST /api/devices/{device_id}/content
Assign content directly to a device

**Request:**
```json
{
  "content_id": 5,
  "priority": 10,
  "display_order": 1,
  "is_active": true
}
```

**Response (201):**
Content assignment object

**Errors:**
- `404`: Device or content not found
- `400`: Device is not active
- `409`: Assignment already exists

---

### DELETE /api/devices/{device_id}/content/{content_id}
Remove content assignment from a device

**Response (204):** No content

---

## Content Management Endpoints
**Prefix:** `/api/content`

### POST /api/content/upload
Upload content file to Anthias and save metadata

**Request (multipart/form-data):**
- `file` (UploadFile): Image or video file
- `title` (string): Content title
- `description` (string, optional): Content description
- `duration` (int, default: 10): Display duration in seconds
- `is_active` (bool, default: true): Whether content is active

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Promo Video",
    "description": "Product promotion",
    "content_type": "video",
    "anthias_url": "http://anthias.server/asset/...",
    "anthias_asset_id": "51ef3ffb...",
    "duration": 30,
    "is_active": true,
    "file_size": 1024000,
    "mime_type": "video/mp4",
    "resolution": "1920x1080",
    "width": 1920,
    "height": 1080,
    "codec": "h264",
    "fps": 30,
    "bitrate": "2500k",
    "video_duration": 30,
    "audio_codec": "aac",
    "audio_bitrate": "128k",
    "audio_sample_rate": 44100,
    "created_at": "2025-10-28T14:30:00Z",
    "updated_at": "2025-10-28T14:30:00Z"
  }
}
```

**Errors:**
- `400`: Invalid file type
- `500`: Upload failed

---

### GET /api/content/
List all content with optional filters

**Query Parameters:**
- `skip` (int, default: 0): Pagination offset
- `limit` (int, default: 100): Page size
- `content_type` (string): Filter by type (image/video)
- `is_active` (bool): Filter by active status

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total": 5,
    "page": 1,
    "page_size": 100,
    "items": [
      {
        "id": 1,
        "title": "Content 1",
        "description": "Description",
        "content_type": "video",
        "anthias_url": "...",
        "anthias_asset_id": "...",
        "duration": 30,
        "is_active": true,
        "file_size": 1024000,
        "mime_type": "video/mp4",
        "resolution": "1920x1080",
        "width": 1920,
        "height": 1080,
        "created_at": "2025-10-28T14:30:00Z",
        "updated_at": "2025-10-28T14:30:00Z"
      }
    ]
  }
}
```

---

### GET /api/content/{content_id}
Get content by ID

**Response (200):**
Individual content object (same as above)

---

### PATCH /api/content/{content_id}
Update content metadata (partial update)

**Request:**
```json
{
  "title": "New Title",
  "description": "New description",
  "duration": 45,
  "video_start_time": 5,
  "video_end_time": 50,
  "is_active": false
}
```

**Response (200):**
Updated content object

---

### DELETE /api/content/{content_id}
Delete content from Anthias and database

**Response (204):** No content

---

### POST /api/content/{content_id}/assign
Assign content to a device or tag

**Request:**
```json
{
  "device_id": 1,
  "tag_id": null,
  "priority": 10
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "content_id": 5,
    "device_id": 1,
    "tag_id": null,
    "priority": 10,
    "created_at": "2025-10-28T14:30:00Z"
  }
}
```

**Errors:**
- `400`: Must specify device_id or tag_id (not both)
- `404`: Device, content, or tag not found
- `409`: Assignment already exists

---

### GET /api/content/{content_id}/assignments
Get all assignments for a content

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "content_id": 5,
      "device_id": 1,
      "tag_id": null,
      "priority": 10,
      "created_at": "2025-10-28T14:30:00Z"
    }
  ]
}
```

---

### DELETE /api/content/{content_id}/assign
Unassign content from a device or tag

**Request:**
```json
{
  "device_id": 1,
  "tag_id": null
}
```

**Response (204):** No content

---

### GET /api/content/{content_id}/image
Proxy endpoint to serve content image with correct Content-Type

**Response (200):** Binary image data

---

### GET /api/content/{content_id}/video
Proxy endpoint to serve content video with correct Content-Type

**Response (200):** Binary video data (supports range requests)

---

## Tags Endpoints
**Prefix:** `/api/tags`

### GET /api/tags
Get all tags with device counts

**Query Parameters:**
- `sort_by` (string): newest|oldest|name_asc|name_desc

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total": 5,
    "items": [
      {
        "id": 1,
        "tag_name": "floor1",
        "description": "First floor devices",
        "color": "#FF5733",
        "device_count": 10,
        "created_at": "2025-10-28T14:30:00Z",
        "updated_at": "2025-10-28T14:30:00Z"
      }
    ]
  }
}
```

---

### POST /api/tags
Create a new tag

**Request:**
```json
{
  "tag_name": "floor1",
  "description": "First floor",
  "color": "#FF5733"
}
```

**Response (201):**
Tag object with device_count=0

**Errors:**
- `409`: Tag name already exists

---

### GET /api/tags/{tag_id}
Get a single tag by ID

**Response (200):**
Tag object

---

### PATCH /api/tags/{tag_id}
Update a tag

**Request:**
```json
{
  "tag_name": "floor1_updated",
  "description": "Updated description",
  "color": "#33FF57"
}
```

**Response (200):**
Updated tag object

---

### DELETE /api/tags/{tag_id}
Delete a tag

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Tag deleted successfully"
  }
}
```

---

### POST /api/tags/assign
Assign a tag to a device

**Request:**
```json
{
  "tag_id": 1,
  "device_id": 1
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "message": "Tag assigned successfully"
  }
}
```

**Errors:**
- `400`: Device is not active
- `404`: Tag or device not found

---

### DELETE /api/tags/assign
Remove a tag from a device

**Request (body):**
```json
{
  "tag_id": 1,
  "device_id": 1
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Tag unassigned successfully"
  }
}
```

---

### GET /api/tags/{tag_id}/devices
Get all devices with this tag

**Response (200):**
```json
{
  "success": true,
  "data": {
    "tag": { ... },
    "devices": [ ... ]
  }
}
```

---

### GET /api/tags/{tag_id}/content
Get all content assigned to a tag

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "content_id": 5,
      "device_id": null,
      "tag_id": 1,
      "priority": 10,
      "created_at": "2025-10-28T14:30:00Z"
    }
  ]
}
```

---

## Playlists Endpoints
**Prefix:** `/api/playlists`

### GET /api/playlists
Get all playlists with content counts and total duration

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total": 5,
    "items": [
      {
        "id": 1,
        "name": "Morning Playlist",
        "description": "Content for morning",
        "is_active": true,
        "priority": 1,
        "content_count": 10,
        "total_duration": 300,
        "created_at": "2025-10-28T14:30:00Z",
        "updated_at": "2025-10-28T14:30:00Z"
      }
    ]
  }
}
```

---

### POST /api/playlists
Create a new playlist

**Request:**
```json
{
  "name": "Morning Playlist",
  "description": "Content for morning hours",
  "is_active": true,
  "priority": 1,
  "schedule": {
    "start_time": "06:00",
    "end_time": "12:00"
  }
}
```

**Response (201):**
Playlist object with content_count=0

---

### GET /api/playlists/{playlist_id}
Get a single playlist by ID

**Response (200):**
Playlist object (see list response for structure)

---

### PATCH /api/playlists/{playlist_id}
Update a playlist (partial)

**Request:**
```json
{
  "name": "Updated Name",
  "description": "Updated description",
  "is_active": false,
  "priority": 2
}
```

**Response (200):**
Updated playlist object

---

### DELETE /api/playlists/{playlist_id}
Delete a playlist

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Playlist deleted successfully"
  }
}
```

---

## Activities/Logs Endpoints
**Prefix:** `/api` (activities)

### GET /api/activities
Get list of activity logs with filtering

**Query Parameters:**
- `skip` (int, default: 0): Pagination offset
- `limit` (int, default: 50): Page size (max: 500)
- `action_type` (string): Filter by action (e.g., DEVICE_APPROVED)
- `entity_type` (string): Filter by entity type (device, content, etc)
- `entity_id` (int): Filter by specific entity
- `user_id` (int): Filter by user
- `start_date` (ISO 8601): From date
- `end_date` (ISO 8601): To date

**Response (200):**
```json
{
  "total": 100,
  "items": [
    {
      "id": 1,
      "timestamp": "2025-10-28T14:30:00Z",
      "user_id": 1,
      "action_type": "DEVICE_APPROVED",
      "entity_type": "device",
      "entity_id": 5,
      "entity_name": "Device 1",
      "details": { "status": "pending" },
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2025-10-28T14:30:00Z",
      "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com"
      }
    }
  ]
}
```

---

### GET /api/activities/stats
Get activity statistics

**Response (200):**
```json
{
  "today": 15,
  "this_week": 120,
  "this_month": 500,
  "by_type": {
    "DEVICE_APPROVED": 100,
    "CONTENT_UPLOADED": 200
  },
  "by_entity": {
    "device": 250,
    "content": 150
  }
}
```

---

### GET /api/activities/{activity_id}
Get a single activity log by ID

**Response (200):**
Activity log object (see list above)

---

### POST /api/activities
Create a new activity log entry

**Request:**
```json
{
  "action_type": "DEVICE_APPROVED",
  "entity_type": "device",
  "entity_id": 5,
  "entity_name": "Device 1",
  "details": { "status": "pending" },
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

**Response (201):**
Activity log object

---

### DELETE /api/activities/cleanup
Delete activity logs older than retention period

**Query Parameters:**
- `retention_days` (int, default: 90): Days to retain

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Deleted X activity logs older than 90 days",
    "deleted_count": 500,
    "retention_days": 90,
    "cutoff_date": "2025-07-30T14:30:00Z"
  }
}
```

---

## Settings/System Endpoints
**Prefix:** `/api/settings`

### GET /api/settings/system/info
Get system information

**Response (200):**
```json
{
  "success": true,
  "data": {
    "version": "1.0.0",
    "backend_uptime": "2d 5h 30m",
    "backend_uptime_seconds": 184200,
    "backend_restart_count": 2,
    "database_uptime": "5d 12h 45m",
    "database_uptime_seconds": 475500,
    "database_restart_count": 1,
    "database_size": 1024000,
    "media_storage_used": 10240000,
    "python_version": "3.9.0",
    "environment": "production",
    "database_type": "PostgreSQL",
    "cache_enabled": true
  }
}
```

---

### GET /api/settings/system/backup
Create and download database backup

**Response (200):**
SQL dump file (application/sql)

---

### POST /api/settings/system/clear-cache
Clear system cache

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "System cache cleared successfully",
    "cleared_at": "2025-10-28T14:30:00Z"
  }
}
```

---

### GET /api/settings/system/database-stats
Get detailed database statistics

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total_size_bytes": 1024000,
    "table_count": 15,
    "tables": [
      {
        "schema": "public",
        "table": "devices",
        "size": "512KB",
        "size_bytes": 524288
      }
    ]
  }
}
```

---

## Device Logs Endpoints
**Prefix:** `/api` (device logs)

### POST /api/client/logs
Create a device log entry (NO AUTH)

**Request:**
```json
{
  "device_id": 1,
  "log_level": "error|warn|log|info",
  "message": "Error message",
  "source": "main.js:123"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "device_id": 1,
    "log_level": "error",
    "message": "Error message",
    "source": "main.js:123",
    "timestamp": "2025-10-28T14:30:00Z"
  }
}
```

---

### POST /api/client/logs/batch
Create multiple device log entries (NO AUTH)

**Request:**
```json
{
  "device_id": 1,
  "logs": [
    {
      "level": "error",
      "message": "Error 1",
      "source": "main.js:123",
      "timestamp": "2025-10-28T14:30:00Z"
    },
    {
      "level": "warn",
      "message": "Warning 1",
      "source": "utils.js:45"
    }
  ]
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "message": "2 logs created successfully",
    "logs_created": 2,
    "device_id": 1
  }
}
```

---

### GET /api/devices/{device_id}/logs
Get logs for a specific device

**Query Parameters:**
- `log_level` (string): Filter by level (log/warn/error/info)
- `hours` (int, default: 24): Get logs from last N hours
- `limit` (int, default: 1000): Max logs to return
- `offset` (int, default: 0): Pagination offset

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 1000,
    "items": [
      {
        "id": 1,
        "device_id": 1,
        "log_level": "error",
        "message": "Error message",
        "source": "main.js:123",
        "timestamp": "2025-10-28T14:30:00Z"
      }
    ]
  }
}
```

---

### DELETE /api/devices/{device_id}/logs
Delete logs for a specific device

**Query Parameters:**
- `older_than_hours` (int, optional): Delete logs older than N hours (default: all)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "message": "Deleted 500 logs for device 1",
    "logs_deleted": 500,
    "device_id": 1,
    "older_than_hours": 24
  }
}
```

---

## Speed Test Endpoints
**Prefix:** `/api/speedtest`

### POST /api/speedtest/upload
Upload speed test endpoint

Simply receives data and discards it. Used for measuring upload speed.

**Response (200):**
```
OK
```

---

### GET /api/speedtest/download
Download speed test endpoint

**Query Parameters:**
- `bytes` (int, default: 1000000): Size of dummy data to return

**Response (200):**
Binary dummy data

---

### POST /api/speedtest/devices/{device_id}/speedtest
Store speed test result for a device (NO AUTH)

**Request:**
```json
{
  "download_speed": 25.5,
  "upload_speed": 10.2,
  "latency": 45,
  "jitter": 2,
  "packet_loss": 0.1,
  "dns_server": "8.8.8.8",
  "test_duration_ms": 5000,
  "server_endpoint": "speedtest.example.com",
  "error_message": null
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "device_id": 1,
    "download_speed": 25.5,
    "upload_speed": 10.2,
    "latency": 45,
    "jitter": 2,
    "packet_loss": 0.1,
    "dns_server": "8.8.8.8",
    "quality": "good",
    "tested_at": "2025-10-28T14:30:00Z",
    "test_duration_ms": 5000,
    "server_endpoint": "speedtest.example.com",
    "error_message": null
  }
}
```

**Quality Thresholds:**
- Good: Download ≥25 Mbps AND Upload ≥10 Mbps
- Fair: Download ≥10 Mbps AND Upload ≥5 Mbps
- Poor: Below fair thresholds

---

### GET /api/speedtest/devices/{device_id}/speedtest
Get speed test history for a device

**Query Parameters:**
- `limit` (int, default: 20, max: 100): Number of tests
- `offset` (int, default: 0): Pagination offset

**Response (200):**
```json
{
  "success": true,
  "data": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "items": [ ... speed tests ... ]
  }
}
```

---

### GET /api/speedtest/devices/{device_id}/speedtest/latest
Get latest speed test result for a device

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 50,
    "device_id": 1,
    "download_speed": 28.3,
    "upload_speed": 11.5,
    "latency": 42,
    "jitter": 1,
    "packet_loss": 0,
    "dns_server": "8.8.8.8",
    "quality": "good",
    "tested_at": "2025-10-28T14:30:00Z",
    "test_duration_ms": 5000,
    "server_endpoint": "speedtest.example.com",
    "error_message": null
  }
}
```

---

## Firebird Integration Endpoints
**Prefix:** `/api/firebird`

### POST /api/firebird/configs
Create Firebird configuration

**Request:**
```json
{
  "config_key": "firebird_prod",
  "api_endpoint": "http://firebird.example.com",
  "api_key": "username:password",
  "refresh_interval": 300,
  "is_active": true,
  "notes": "Production database"
}
```

**Response (201):**
Firebird config object (API key encrypted)

---

### GET /api/firebird/configs
List Firebird configurations

**Query Parameters:**
- `is_active` (bool): Filter by active status
- `skip` (int, default: 0)
- `limit` (int, default: 100)

**Response (200):**
List of Firebird configs

---

### GET /api/firebird/configs/{config_id}
Get specific Firebird configuration

**Response (200):**
Firebird config object

---

### PATCH /api/firebird/configs/{config_id}
Update Firebird configuration

**Request:**
```json
{
  "api_endpoint": "http://new-firebird.example.com",
  "is_active": false
}
```

**Response (200):**
Updated config object

---

### DELETE /api/firebird/configs/{config_id}
Delete Firebird configuration

**Response (204):** No content

---

### POST /api/firebird/configs/{config_id}/test
Test Firebird configuration connection

**Response (200):**
```json
{
  "success": true,
  "message": "Connection successful"
}
```

---

### POST /api/firebird/query
Execute read-only query on Firebird

**Request:**
```json
{
  "config_id": 1,
  "query": "SELECT * FROM some_table WHERE id = 1"
}
```

**Response (200):**
```json
{
  "rows": [ ... query results ... ],
  "row_count": 10,
  "columns": ["id", "name", "value"]
}
```

---

### GET /api/firebird/health
Get Firebird health status

**Response (200):**
```json
{
  "configs": [
    {
      "config_id": 1,
      "config_key": "firebird_prod",
      "status": "healthy|disconnected|error",
      "last_check": "2025-10-28T14:30:00Z",
      "error_message": null
    }
  ]
}
```

---

## Client Endpoints
**Prefix:** `/api/client`

### GET /api/client/playlist
Get playlist for a device (NO AUTH)

**Query Parameters:**
- `device_id` (int): Device ID

**Response (200):**
```json
{
  "device_id": 1,
  "device_name": "Device 1",
  "device_type": "monitor",
  "total_items": 5,
  "playlist": [
    {
      "content_id": 5,
      "title": "Content 1",
      "content_type": "video",
      "url": "http://anthias.server/screenly_assets/...",
      "duration": 30,
      "mime_type": "video/mp4"
    }
  ]
}
```

---

### GET /api/client/status
Check device status (NO AUTH)

**Query Parameters:**
- `device_id` (int): Device ID

**Response (200):**
```json
{
  "device_id": 1,
  "status": "active|pending|inactive",
  "is_active": true,
  "message": "Device is active and authorized"
}
```

---

## Root & Health Endpoints

### GET /
Root endpoint - API info

**Response (200):**
```json
{
  "message": "Smart TV Digital Signage - Backend API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "environment": "production"
}
```

---

### GET /health
Health check endpoint

**Response (200):**
```json
{
  "status": "healthy",
  "environment": "production",
  "database": "connected",
  "redis": "connected"
}
```

---

### GET /api/ping
Ping endpoint for monitoring

**Response (200):**
```json
{
  "ping": "pong"
}
```

---

## Debug Endpoints (DEBUG mode only)

### GET /debug/settings
View current settings (DEBUG mode)

**Response (200):**
```json
{
  "PROJECT_NAME": "Smart TV Digital Signage",
  "ENVIRONMENT": "development",
  "DEBUG": true,
  "DATABASE_URL": "postgresql://...",
  "REDIS_URL": "redis://...",
  "ANTHIAS_API_URL": "http://localhost:8000",
  "CORS_ORIGINS": ["http://localhost:3000", "http://192.168.5.12:8080"]
}
```

---

## Standard Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "request_id": "uuid"
}
```

### Paginated Response
```json
{
  "success": true,
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 50,
    "items": [ ... ]
  },
  "request_id": "uuid"
}
```

### Error Response
```json
{
  "detail": "Error message",
  "error_type": "NotFoundException|BadRequestException|...",
  "status_code": 404,
  "request_id": "uuid"
}
```

---

## Authentication

All endpoints except those marked with **(NO AUTH)** require JWT authentication.

**Authorization Header:**
```
Authorization: Bearer {access_token}
```

**Token Expiry:**
- Access token: 30 minutes (default)
- Refresh token: 7 days (default)

---

## Error Codes

| Status | Type | Description |
|--------|------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 204 | No Content | Success, no response body |
| 400 | BadRequest | Invalid request |
| 401 | Unauthorized | Invalid/missing credentials |
| 403 | Forbidden | Not authorized |
| 404 | NotFound | Resource not found |
| 409 | Conflict | Resource already exists |
| 410 | Gone | Resource expired |
| 500 | InternalError | Server error |

