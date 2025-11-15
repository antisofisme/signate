# Playlist Management API Endpoints

**Base URL:** `http://192.168.5.12:8001/api/v1`
**Authentication:** Bearer Token (JWT)
**API Version:** v1
**Last Updated:** 2025-11-14

---

## Endpoint Mapping

### 1. Playlist CRUD

#### Create Playlist
```
POST /api/v1/playlists
```
**Headers:**
- `Authorization: Bearer <token>`
- `Content-Type: application/json`

**Request Body:**
```json
{
  "name": "string (required, 1-255 chars)",
  "description": "string (optional)",
  "is_active": "boolean (default: true)",
  "priority": "integer (default: 0, >= 0)",
  "schedule": {
    "days": ["monday", "tuesday", ...],
    "start_time": "HH:MM",
    "end_time": "HH:MM",
    "timezone": "Asia/Jakarta"
  }
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "...",
    "description": "...",
    "is_active": true,
    "priority": 5,
    "schedule": {...},
    "organization_id": 4,
    "created_by_id": 9,
    "created_at": "2025-11-14T10:30:00Z",
    "updated_at": null,
    "content_count": 0,
    "total_duration": 0
  }
}
```

---

#### List Playlists
```
GET /api/v1/playlists?skip=0&limit=100&is_active=true
```
**Query Parameters:**
- `skip` (optional): Skip N records (default: 0)
- `limit` (optional): Max results (default: 100)
- `is_active` (optional): Filter by active status

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "total": 15,
    "items": [
      {
        "id": 1,
        "name": "...",
        "is_active": true,
        "priority": 5,
        ...
      }
    ]
  }
}
```

---

#### Get Single Playlist
```
GET /api/v1/playlists/{playlist_id}
```
**Path Parameters:**
- `playlist_id`: Playlist ID (integer)

**Response:** `200 OK` or `404 Not Found`

---

#### Update Playlist
```
PATCH /api/v1/playlists/{playlist_id}
```
**Request Body:** (all fields optional)
```json
{
  "name": "string",
  "description": "string",
  "is_active": "boolean",
  "priority": "integer",
  "schedule": {...}
}
```

**Response:** `200 OK` or `400 Bad Request`

---

#### Delete Playlist
```
DELETE /api/v1/playlists/{playlist_id}
```
**Response:** `200 OK` or `404 Not Found`

**Note:** Cascade deletes all playlist_items

---

### 2. Content Management

#### Get Playlist Content
```
GET /api/v1/playlists/{playlist_id}/content
```
**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "total": 5,
    "items": [
      {
        "id": 101,
        "playlist_id": 1,
        "content_id": 10,
        "order_index": 1,
        "duration": 15,
        "created_at": "...",
        "content_name": "Banner.jpg",
        "content_type": "image"
      }
    ]
  }
}
```

---

#### Add Content to Playlist (Bulk)
```
POST /api/v1/playlists/{playlist_id}/content
```
**Request Body:**
```json
{
  "content_ids": [1, 2, 3, 4, 5]
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "message": "Added 5 content(s), skipped 1 duplicates",
    "added": 5,
    "skipped_duplicate": [3],
    "skipped_missing": []
  }
}
```

---

#### Remove Content from Playlist
```
DELETE /api/v1/playlists/{playlist_id}/content/{content_item_id}
```
**Path Parameters:**
- `playlist_id`: Playlist ID
- `content_item_id`: PlaylistContent ID (not content_id!)

**Response:** `200 OK` or `404 Not Found`

---

#### Reorder Playlist Content
```
PATCH /api/v1/playlists/{playlist_id}/reorder
```
**Request Body:**
```json
{
  "content_items": [
    {
      "id": 101,
      "order_index": 1,
      "duration": 15
    },
    {
      "id": 102,
      "order_index": 2,
      "duration": 20
    }
  ]
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "message": "Reordered 2 content item(s)",
    "updated_count": 2
  }
}
```

---

### 3. Device/Tag Assignments

#### Get Playlist Assignments
```
GET /api/v1/playlists/{playlist_id}/assignments
```
**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "devices": [
      {
        "id": 10,
        "device_name": "Lobby Display",
        "location": "Main Lobby"
      }
    ],
    "tags": [
      {
        "id": 5,
        "name": "Lobby Screens",
        "color": "#FF5733"
      }
    ]
  }
}
```

---

#### Assign Playlist to Devices (Bulk)
```
POST /api/v1/playlists/{playlist_id}/assign/devices
```
**Request Body:**
```json
{
  "device_ids": [10, 11, 12]
}
```

**Response:** `201 Created`
```json
{
  "success": true,
  "data": {
    "message": "Assigned to 3 device(s)",
    "assigned": 3,
    "skipped_duplicate": []
  }
}
```

---

#### Assign Playlist to Tags (Bulk)
```
POST /api/v1/playlists/{playlist_id}/assign/tags
```
**Request Body:**
```json
{
  "tag_ids": [5, 6]
}
```

**Response:** `201 Created` (same structure as device assignment)

---

#### Unassign Playlist from Devices
```
DELETE /api/v1/playlists/{playlist_id}/assign/devices
```
**Request Body:**
```json
{
  "device_ids": [10, 11]
}
```

**Response:** `200 OK`
```json
{
  "success": true,
  "data": {
    "message": "Unassigned from 2 device(s)",
    "removed": 2
  }
}
```

---

#### Unassign Playlist from Tags
```
DELETE /api/v1/playlists/{playlist_id}/assign/tags
```
**Request Body:**
```json
{
  "tag_ids": [5]
}
```

**Response:** `200 OK` (same structure as device unassignment)

---

### 4. Content Resolver

#### Resolve Content for Device
```
GET /api/v1/playlists/resolve/{device_id}
```
**Path Parameters:**
- `device_id`: Device ID (integer)

**Response:** `200 OK` or `404 Not Found`

**Success Response:**
```json
{
  "device_id": 10,
  "playlist_id": 21,
  "playlist_name": "Morning Lobby Content",
  "resolution_type": "direct_assignment",
  "priority": 5,
  "content_items": [
    {
      "id": 101,
      "content_id": 1,
      "order_index": 1,
      "duration": 15,
      "content_url": "http://192.168.5.12:8001/api/v1/contents/1/download",
      "content_type": "image",
      "content_name": "Banner.jpg"
    }
  ],
  "total_duration": 35,
  "loop": true
}
```

**Resolution Types:**
- `scheduled` - Active scheduled playlist (highest priority)
- `direct_assignment` - Directly assigned to device
- `tag_assignment` - Assigned via device tags
- `pms_guest` - PMS guest-specific content
- `pms_room` - PMS room content
- `default` - Organization default playlist

**404 Response:**
```json
{
  "detail": "No content available for this device"
}
```

---

## Resolution Logic

The content resolver determines playlist priority in this order:

1. **Active Scheduled Playlists** (highest)
   - Within schedule time window
   - `is_active = true`
   - Sorted by `priority` DESC

2. **Direct Device Assignments**
   - Playlist → Device assignments
   - Sorted by `priority` DESC

3. **Tag-Based Assignments**
   - Device has tags
   - Playlists assigned to those tags
   - Sorted by `priority` DESC

4. **PMS Content** (hotel integration)
   - Guest-specific content
   - Room-based content
   - Hotel default

5. **Default Playlist** (lowest)
   - Organization default
   - Always available

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Cannot access devices from other organizations"
}
```

### 404 Not Found
```json
{
  "detail": "Playlist not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Too many requests. Please try again in 120 seconds."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error message"
}
```

---

## Authentication

All endpoints require JWT Bearer token authentication (except health checks).

### Get Token
```
POST /api/v1/auth/login
```
**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "id": 9,
      "username": "admin",
      "organization_id": 4,
      "role": "ADMIN"
    }
  }
}
```

### Using Token
Add header to all requests:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

---

## Rate Limiting

- **Login:** 5 requests per minute per IP
- **API Endpoints:** 100 requests per minute per user
- **Content Resolution:** 120 requests per minute per device

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1699999999
```

---

## Pagination

List endpoints support pagination:

```
GET /api/v1/playlists?skip=0&limit=20
```

- `skip`: Number of records to skip (default: 0)
- `limit`: Max records to return (default: 100, max: 1000)

Response includes total count:
```json
{
  "data": {
    "total": 156,
    "items": [...]
  }
}
```

---

## Webhooks / WebSocket

Real-time updates via WebSocket:

### Admin Dashboard
```
ws://192.168.5.12:8001/api/ws/admin?token=<jwt_token>
```

**Events:**
- `playlist_created`
- `playlist_updated`
- `playlist_deleted`
- `playlist_assigned`
- `playlist_unassigned`

### Device Updates
```
ws://192.168.5.12:8001/api/ws/{device_id}?token=<jwt_token>
```

**Events:**
- `content_update` - Playlist content changed
- `assignment_changed` - New playlist assigned
- `command_received` - Device command

---

## Testing

### cURL Examples

**Create Playlist:**
```bash
curl -X POST "http://192.168.5.12:8001/api/v1/playlists" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Playlist",
    "is_active": true,
    "priority": 5
  }'
```

**Add Content:**
```bash
curl -X POST "http://192.168.5.12:8001/api/v1/playlists/1/content" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content_ids": [1, 2, 3]}'
```

**Assign to Device:**
```bash
curl -X POST "http://192.168.5.12:8001/api/v1/playlists/1/assign/devices" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"device_ids": [10]}'
```

**Resolve Content:**
```bash
curl -X GET "http://192.168.5.12:8001/api/v1/playlists/resolve/10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Postman Collection

Import the following URL to Postman:
```
http://192.168.5.12:8001/api/v1/openapi.json
```

Or use Swagger UI:
```
http://192.168.5.12:8001/docs
```

---

## Database Tables

### playlists
```sql
CREATE TABLE playlists (
  id INTEGER PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  priority INTEGER NOT NULL DEFAULT 0,
  schedule JSONB,
  organization_id INTEGER NOT NULL REFERENCES organizations(id),
  created_by_id INTEGER REFERENCES users(id),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE
);
```

### playlist_items
```sql
CREATE TABLE playlist_items (
  id INTEGER PRIMARY KEY,
  playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
  content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
  order_index INTEGER NOT NULL,
  duration INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### device_playlists
```sql
CREATE TABLE device_playlists (
  id INTEGER PRIMARY KEY,
  device_id INTEGER NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
  playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### tag_playlists
```sql
CREATE TABLE tag_playlists (
  id INTEGER PRIMARY KEY,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## SDK Examples

### Python
```python
import requests

BASE_URL = "http://192.168.5.12:8001/api/v1"
token = "eyJhbGciOiJIUzI1NiIs..."

headers = {"Authorization": f"Bearer {token}"}

# Create playlist
response = requests.post(
    f"{BASE_URL}/playlists",
    json={
        "name": "Morning Playlist",
        "is_active": True,
        "priority": 5
    },
    headers=headers
)
playlist_id = response.json()["data"]["id"]

# Add content
requests.post(
    f"{BASE_URL}/playlists/{playlist_id}/content",
    json={"content_ids": [1, 2, 3]},
    headers=headers
)

# Assign to device
requests.post(
    f"{BASE_URL}/playlists/{playlist_id}/assign/devices",
    json={"device_ids": [10]},
    headers=headers
)

# Resolve content
response = requests.get(
    f"{BASE_URL}/playlists/resolve/10",
    headers=headers
)
content = response.json()
```

### JavaScript (Axios)
```javascript
const axios = require('axios');

const BASE_URL = 'http://192.168.5.12:8001/api/v1';
const token = 'eyJhbGciOiJIUzI1NiIs...';

const headers = { Authorization: `Bearer ${token}` };

// Create playlist
const { data: playlist } = await axios.post(
  `${BASE_URL}/playlists`,
  {
    name: 'Morning Playlist',
    is_active: true,
    priority: 5
  },
  { headers }
);

// Add content
await axios.post(
  `${BASE_URL}/playlists/${playlist.data.id}/content`,
  { content_ids: [1, 2, 3] },
  { headers }
);

// Resolve content
const { data: content } = await axios.get(
  `${BASE_URL}/playlists/resolve/10`,
  { headers }
);
```

---

## Support

- **API Documentation:** http://192.168.5.12:8001/docs
- **Health Check:** http://192.168.5.12:8001/health
- **Metrics:** http://192.168.5.12:8001/metrics

---

**Last Updated:** 2025-11-14
**API Version:** v1
**Server:** http://192.168.5.12:8001
