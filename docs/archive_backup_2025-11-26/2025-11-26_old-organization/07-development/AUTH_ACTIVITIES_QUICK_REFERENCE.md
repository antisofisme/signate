# Auth & Activities API - Quick Reference

**Date:** October 28, 2025
**Status:** ✅ All endpoints migrated to Quick Wins pattern

---

## Authentication Endpoints

### 1. POST /api/auth/login
**Login with username/password**

**Request:**
```bash
curl -X POST http://192.168.5.12:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer",
    "expires_in": 900
  },
  "meta": {
    "timestamp": "2025-10-28T12:00:00Z",
    "request_id": "abc-123-def",
    "version": "1.0.0"
  }
}
```

---

### 2. POST /api/auth/refresh
**Refresh access token using refresh token**

**Request:**
```bash
curl -X POST http://192.168.5.12:8001/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGci..."
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer",
    "expires_in": 900
  },
  "meta": {
    "timestamp": "2025-10-28T12:15:00Z",
    "request_id": "def-456-ghi",
    "version": "1.0.0"
  }
}
```

---

### 3. GET /api/auth/me
**Get current user information**

**Request:**
```bash
curl http://192.168.5.12:8001/api/auth/me \
  -H "Authorization: Bearer eyJhbGci..."
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true,
    "is_superuser": true,
    "created_at": "2025-01-01T00:00:00Z",
    "last_login": "2025-10-28T12:00:00Z"
  },
  "meta": {
    "timestamp": "2025-10-28T12:20:00Z",
    "request_id": "ghi-789-jkl",
    "version": "1.0.0"
  }
}
```

---

### 4. POST /api/auth/logout
**Logout (client-side token removal)**

**Request:**
```bash
curl -X POST http://192.168.5.12:8001/api/auth/logout \
  -H "Authorization: Bearer eyJhbGci..."
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Successfully logged out"
  },
  "meta": {
    "timestamp": "2025-10-28T12:25:00Z",
    "request_id": "jkl-012-mno",
    "version": "1.0.0"
  }
}
```

**Note:** JWT tokens are stateless - actual invalidation happens client-side.

---

## Activity Log Endpoints

### 5. GET /api/activities
**List activity logs with filtering and pagination**

**Request:**
```bash
# Basic pagination
curl "http://192.168.5.12:8001/api/activities?page=1&limit=50" \
  -H "Authorization: Bearer eyJhbGci..."

# With filters
curl "http://192.168.5.12:8001/api/activities?page=1&limit=50&action_type=DEVICE_APPROVED&entity_type=device" \
  -H "Authorization: Bearer eyJhbGci..."
```

**Query Parameters:**
- `page` (int, default: 1) - Page number (1-indexed)
- `limit` (int, default: 50, max: 500) - Items per page
- `action_type` (string, optional) - Filter by action (e.g., DEVICE_APPROVED)
- `entity_type` (string, optional) - Filter by entity (e.g., device, content)
- `entity_id` (int, optional) - Filter by specific entity ID
- `user_id` (int, optional) - Filter by user who performed action
- `start_date` (datetime, optional) - Filter from date
- `end_date` (datetime, optional) - Filter to date

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "timestamp": "2025-10-28T10:30:00Z",
      "user_id": 1,
      "action_type": "DEVICE_APPROVED",
      "entity_type": "device",
      "entity_id": 123,
      "entity_name": "Conference Room TV",
      "details": {"approved_by": "admin"},
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "created_at": "2025-10-28T10:30:00Z",
      "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com"
      }
    }
  ],
  "meta": {
    "timestamp": "2025-10-28T12:30:00Z",
    "request_id": "mno-345-pqr",
    "version": "1.0.0",
    "total": 150,
    "page": 1,
    "page_size": 50,
    "total_pages": 3
  }
}
```

---

### 6. GET /api/activities/stats
**Get activity statistics**

**Request:**
```bash
curl http://192.168.5.12:8001/api/activities/stats \
  -H "Authorization: Bearer eyJhbGci..."
```

**Response:**
```json
{
  "success": true,
  "data": {
    "today": 42,
    "this_week": 187,
    "this_month": 823,
    "by_type": {
      "DEVICE_APPROVED": 25,
      "DEVICE_REGISTERED": 12,
      "CONTENT_UPLOADED": 103,
      "PLAYLIST_CREATED": 15,
      "TAG_ASSIGNED": 32
    },
    "by_entity": {
      "device": 45,
      "content": 120,
      "playlist": 22,
      "tag": 35
    }
  },
  "meta": {
    "timestamp": "2025-10-28T12:35:00Z",
    "request_id": "pqr-678-stu",
    "version": "1.0.0"
  }
}
```

---

### 7. GET /api/activities/{activity_id}
**Get single activity log by ID**

**Request:**
```bash
curl http://192.168.5.12:8001/api/activities/42 \
  -H "Authorization: Bearer eyJhbGci..."
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 42,
    "timestamp": "2025-10-28T10:30:00Z",
    "user_id": 1,
    "action_type": "DEVICE_APPROVED",
    "entity_type": "device",
    "entity_id": 123,
    "entity_name": "Conference Room TV",
    "details": {
      "approved_by": "admin",
      "reason": "Verified device"
    },
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "created_at": "2025-10-28T10:30:00Z",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com"
    }
  },
  "meta": {
    "timestamp": "2025-10-28T12:40:00Z",
    "request_id": "stu-901-vwx",
    "version": "1.0.0"
  }
}
```

**Error (Not Found):**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Activity log with ID 999 not found",
    "field": null,
    "details": {
      "resource_type": "ActivityLog",
      "resource_id": 999
    }
  },
  "meta": {
    "timestamp": "2025-10-28T12:40:00Z",
    "request_id": "stu-901-vwx",
    "version": "1.0.0"
  }
}
```

---

### 8. POST /api/activities
**Create activity log (manual/external integration)**

**Request:**
```bash
curl -X POST http://192.168.5.12:8001/api/activities \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{
    "action_type": "DEVICE_APPROVED",
    "entity_type": "device",
    "entity_id": 123,
    "entity_name": "Conference Room TV",
    "details": {
      "approved_by": "admin",
      "reason": "Verified device"
    }
  }'
```

**Request Body:**
```json
{
  "action_type": "DEVICE_APPROVED",      // Required
  "entity_type": "device",               // Required
  "entity_id": 123,                      // Optional
  "entity_name": "Conference Room TV",   // Optional
  "details": {                           // Optional
    "approved_by": "admin",
    "reason": "Verified device"
  },
  "user_id": 1,                         // Optional (auto-populated from token)
  "ip_address": "192.168.1.100",        // Optional (auto-populated)
  "user_agent": "Mozilla/5.0..."        // Optional (auto-populated)
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 43,
    "timestamp": "2025-10-28T12:45:00Z",
    "user_id": 1,
    "action_type": "DEVICE_APPROVED",
    "entity_type": "device",
    "entity_id": 123,
    "entity_name": "Conference Room TV",
    "details": {
      "approved_by": "admin",
      "reason": "Verified device"
    },
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "created_at": "2025-10-28T12:45:00Z",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@example.com"
    }
  },
  "meta": {
    "timestamp": "2025-10-28T12:45:00Z",
    "request_id": "vwx-234-yz0",
    "version": "1.0.0"
  }
}
```

**Note:** Most activity logging should use the `activity_logger` utility automatically. This endpoint is for external integrations.

---

### 9. DELETE /api/activities/cleanup
**Delete old activity logs (maintenance)**

**Request:**
```bash
# Default 90 days retention
curl -X DELETE http://192.168.5.12:8001/api/activities/cleanup \
  -H "Authorization: Bearer eyJhbGci..."

# Custom retention period
curl -X DELETE "http://192.168.5.12:8001/api/activities/cleanup?retention_days=30" \
  -H "Authorization: Bearer eyJhbGci..."
```

**Query Parameters:**
- `retention_days` (int, default: 90, min: 1) - Number of days to retain

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Deleted 425 activity logs older than 90 days",
    "deleted_count": 425,
    "retention_days": 90,
    "cutoff_date": "2025-07-30T12:50:00Z"
  },
  "meta": {
    "timestamp": "2025-10-28T12:50:00Z",
    "request_id": "yz0-567-abc",
    "version": "1.0.0"
  }
}
```

**Error (Invalid Parameter):**
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "Retention days must be at least 1",
    "field": null,
    "details": {
      "retention_days": 0,
      "minimum": 1
    }
  },
  "meta": {
    "timestamp": "2025-10-28T12:50:00Z",
    "request_id": "yz0-567-abc",
    "version": "1.0.0"
  }
}
```

---

## Activity Action Types

Common action types used in the system:

### Device Actions
- `DEVICE_REGISTERED` - Device registered with activation code
- `DEVICE_APPROVED` - Device approved by admin
- `DEVICE_REJECTED` - Device rejected by admin
- `DEVICE_RELEASED` - Device released/deactivated
- `DEVICE_UPDATED` - Device settings updated
- `DEVICE_DELETED` - Device removed from system

### Content Actions
- `CONTENT_UPLOADED` - New content uploaded
- `CONTENT_UPDATED` - Content metadata updated
- `CONTENT_ASSIGNED` - Content assigned to device/tag
- `CONTENT_UNASSIGNED` - Content unassigned from device/tag
- `CONTENT_DELETED` - Content removed

### Playlist Actions
- `PLAYLIST_CREATED` - New playlist created
- `PLAYLIST_UPDATED` - Playlist modified
- `PLAYLIST_DELETED` - Playlist removed
- `PLAYLIST_ASSIGNED` - Playlist assigned to device/tag
- `PLAYLIST_UNASSIGNED` - Playlist unassigned

### Tag Actions
- `TAG_CREATED` - New tag created
- `TAG_UPDATED` - Tag modified
- `TAG_DELETED` - Tag removed
- `TAG_ASSIGNED` - Tag assigned to entity
- `TAG_UNASSIGNED` - Tag removed from entity

### User Actions
- `USER_LOGIN` - User logged in
- `USER_LOGOUT` - User logged out
- `USER_CREATED` - New user account created
- `USER_UPDATED` - User account modified

### System Actions
- `SETTINGS_CHANGED` - System settings modified
- `SYSTEM_STARTUP` - System started
- `SYSTEM_SHUTDOWN` - System shut down

---

## Entity Types

- `device` - Smart TV / display device
- `content` - Media content (image/video)
- `playlist` - Content playlist
- `tag` - Organization tag
- `user` - User account
- `system` - System-level entity
- `assignment` - Assignment relationship

---

## Error Codes

All endpoints may return these error codes:

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Authentication required or token invalid |
| `FORBIDDEN` | 403 | User lacks permission |
| `NOT_FOUND` | 404 | Resource not found |
| `BAD_REQUEST` | 400 | Invalid request parameters |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `INTERNAL_SERVER_ERROR` | 500 | Unexpected server error |

---

## Common Usage Patterns

### Frontend Integration (axios)

```typescript
// Login
const loginResponse = await axios.post('/api/auth/login', {
  username: 'admin',
  password: 'admin123'
});
const { access_token, refresh_token } = loginResponse.data.data;

// Store tokens
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);

// Get current user
const userResponse = await axios.get('/api/auth/me', {
  headers: { Authorization: `Bearer ${access_token}` }
});
const currentUser = userResponse.data.data;

// Get activities with pagination
const activitiesResponse = await axios.get('/api/activities', {
  params: { page: 1, limit: 50 },
  headers: { Authorization: `Bearer ${access_token}` }
});
const { data: activities, meta } = activitiesResponse.data;
console.log(`Page ${meta.page} of ${meta.total_pages}`);

// Filter activities
const filteredResponse = await axios.get('/api/activities', {
  params: {
    page: 1,
    limit: 50,
    action_type: 'DEVICE_APPROVED',
    entity_type: 'device'
  },
  headers: { Authorization: `Bearer ${access_token}` }
});

// Get activity stats
const statsResponse = await axios.get('/api/activities/stats', {
  headers: { Authorization: `Bearer ${access_token}` }
});
const stats = statsResponse.data.data;

// Logout
await axios.post('/api/auth/logout', null, {
  headers: { Authorization: `Bearer ${access_token}` }
});
localStorage.removeItem('access_token');
localStorage.removeItem('refresh_token');
```

---

## Migration Notes

All endpoints now use **Quick Wins standardized response format**:

### Success Response
```json
{
  "success": true,
  "data": { /* actual payload */ },
  "meta": {
    "timestamp": "2025-10-28T12:00:00Z",
    "request_id": "abc-123-def",
    "version": "1.0.0",
    // For paginated responses:
    "total": 150,
    "page": 1,
    "page_size": 50,
    "total_pages": 3
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Resource not found",
    "field": null,
    "details": {}
  },
  "meta": {
    "timestamp": "2025-10-28T12:00:00Z",
    "request_id": "abc-123-def",
    "version": "1.0.0"
  }
}
```

### Backward Compatibility
The axios interceptor automatically handles both old and new response formats, ensuring zero breaking changes during migration.

---

**Last Updated:** October 28, 2025
**API Version:** 1.0.0
**Standardization Status:** 52.1% (87/167 endpoints)
