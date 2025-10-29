# Commands API Quick Reference

**Last Updated:** 2025-10-28
**API Version:** 1.0.0
**Base URL:** `http://192.168.5.12:8001/api/commands`

---

## 🚀 Command Execution

### Execute Single Command
```http
POST /api/commands/execute
```

**Request:**
```json
{
  "device_id": 1,
  "command_type": "volume",
  "parameters": {"volume": 50},
  "priority": 5,
  "reason": "Adjust for presentation"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "device_id": 1,
    "command_type": "volume",
    "status": "pending",
    "risk_level": "low",
    "created_at": "2025-10-28T10:30:00Z"
  },
  "meta": {
    "timestamp": "2025-10-28T10:30:00Z",
    "request_id": "abc123",
    "version": "1.0.0"
  }
}
```

### Execute Batch Command
```http
POST /api/commands/batch
```

**Request:**
```json
{
  "device_ids": [1, 2, 3],
  "command_type": "reboot",
  "execution_mode": "sequential",
  "priority": 5,
  "reason": "Scheduled maintenance"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "batch_id": "batch-abc123",
    "total": 3,
    "successful": 2,
    "failed": 1,
    "results": [
      {"device_id": 1, "success": true, "command_id": 101},
      {"device_id": 2, "success": true, "command_id": 102},
      {"device_id": 3, "success": false, "error": "Device offline"}
    ]
  },
  "meta": {...}
}
```

---

## 📊 Command Status & Management

### Get Command Status
```http
GET /api/commands/{command_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "device_id": 1,
    "command_type": "volume",
    "status": "completed",
    "created_at": "2025-10-28T10:30:00Z",
    "completed_at": "2025-10-28T10:30:05Z",
    "result": {"success": true, "previous_volume": 70, "new_volume": 50}
  },
  "meta": {...}
}
```

### List All Commands (Paginated)
```http
GET /api/commands/?page=1&limit=20&status=pending
```

**Query Parameters:**
- `page` (default: 1) - Page number (1-indexed)
- `limit` (default: 100, max: 1000) - Items per page
- `device_id` (optional) - Filter by device
- `status` (optional) - Filter by status

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [...],
    "status_breakdown": {
      "pending": 5,
      "running": 2,
      "completed": 140,
      "failed": 3
    }
  },
  "meta": {
    "timestamp": "2025-10-28T10:30:00Z",
    "request_id": "abc123",
    "version": "1.0.0",
    "total": 150,
    "page": 1,
    "page_size": 20,
    "total_pages": 8
  }
}
```

### Get Device Commands (Paginated)
```http
GET /api/commands/device/{device_id}?page=1&limit=20
```

Same response format as list all commands.

---

## 🛠️ Command Actions

### Cancel Command
```http
DELETE /api/commands/{command_id}
```

**Request:**
```json
{
  "reason": "Accidental command"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "status": "cancelled",
    ...
  },
  "meta": {...}
}
```

### Retry Failed Command
```http
POST /api/commands/{command_id}/retry
```

**Request:**
```json
{
  "reset_parameters": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 124,  // New command ID
    "device_id": 1,
    "status": "pending",
    ...
  },
  "meta": {...}
}
```

---

## ℹ️ Information & Utilities

### List Available Commands
```http
GET /api/commands/available/list
```

**Response:**
```json
{
  "success": true,
  "data": {
    "commands": [
      {
        "command_type": "volume",
        "risk_level": "low",
        "rate_limit": 10,
        "timeout": 5,
        "requires_2fa": false,
        "requires_approval": false,
        "allowed_roles": ["admin", "operator", "editor"]
      },
      ...
    ],
    "total": 11
  },
  "meta": {...}
}
```

### Check Command Permission
```http
GET /api/commands/permissions/{command_type}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "command_type": "shell",
    "allowed": false,
    "reason": "Requires one of: admin",
    "requires_2fa": true,
    "requires_approval": true
  },
  "meta": {...}
}
```

### Get Rate Limit Info
```http
GET /api/commands/rate-limit/{device_id}/{command_type}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "command_type": "shell",
    "device_id": 1,
    "limit": 1,
    "remaining": 0,
    "reset_at": "2025-10-28T10:35:00Z"
  },
  "meta": {...}
}
```

---

## 🔧 Internal Endpoints (Device-Called)

### Mark Command Executed
```http
POST /api/commands/{command_id}/execute
```

Called by device viewer after successful command execution.

### Mark Command Failed
```http
POST /api/commands/{command_id}/fail?error_message=Connection timeout
```

Called by device viewer if command execution fails.

---

## 🧹 Background Tasks

### Cleanup Expired Commands
```http
POST /api/commands/cleanup/expired
```

**Response:**
```json
{
  "success": true,
  "data": {
    "expired_count": 15,
    "message": "Marked 15 commands as expired"
  },
  "meta": {...}
}
```

---

## 📋 Command Types

### Risk Levels

**LOW (Safe commands):**
- `volume` - Volume control (10/min)
- `brightness` - Brightness control (10/min)
- `screenshot` - Capture screenshot (5/min)
- `network_test` - Network diagnostics (5/min)

**MEDIUM (System commands):**
- `reboot` - Reboot device (3/min)
- `clear_cache` - Clear cache (5/min)
- `reload` - Reload content (5/min)
- `refresh` - Refresh page (5/min)
- `reset` - Reset settings (3/min)

**HIGH (Requires 2FA):**
- `update` - System update (1/min)

**CRITICAL (Requires 2FA + Approval):**
- `shell` - Shell command execution (1/min)

---

## 🔄 Command Status Lifecycle

```
PENDING → SENT → RUNNING → COMPLETED
                     ↓
                   FAILED (can retry)
                     ↓
                CANCELLED (by admin)
                     ↓
                 EXPIRED (24h timeout)
```

---

## ⚠️ Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Command 123 not found",
    "field": null,
    "details": {
      "resource_type": "command",
      "resource_id": 123
    }
  },
  "meta": {
    "timestamp": "2025-10-28T10:30:00Z",
    "request_id": "abc123",
    "version": "1.0.0"
  }
}
```

**Common Error Codes:**
- `NOT_FOUND` (404) - Command or resource not found
- `BAD_REQUEST` (400) - Invalid request parameters
- `VALIDATION_ERROR` (422) - Request validation failed
- `RATE_LIMIT_EXCEEDED` (429) - Too many requests
- `FORBIDDEN` (403) - Insufficient permissions
- `INTERNAL_SERVER_ERROR` (500) - Server error

---

## 🔐 Authentication

All endpoints require authentication (except internal device endpoints).

**Header:**
```http
Authorization: Bearer <jwt_token>
```

---

## 📝 Frontend Migration Notes

### Old Format (Before Migration)
```javascript
// Old pagination
const response = await fetch('/api/commands/?offset=0&limit=20');
const data = await response.json();
console.log(data.commands);  // Direct array
console.log(data.total);
```

### New Format (After Migration)
```javascript
// New pagination
const response = await fetch('/api/commands/?page=1&limit=20');
const result = await response.json();
console.log(result.data.items);  // Nested in data
console.log(result.meta.total);   // In meta
console.log(result.meta.total_pages);  // Calculated
```

### Helper Function for Migration
```javascript
// Compatibility wrapper
async function fetchCommands(page = 1, limit = 20, filters = {}) {
  const params = new URLSearchParams({
    page,
    limit,
    ...filters
  });

  const response = await fetch(`/api/commands/?${params}`);
  const result = await response.json();

  if (!result.success) {
    throw new Error(result.error.message);
  }

  return {
    commands: result.data.items,
    statusBreakdown: result.data.status_breakdown,
    pagination: {
      total: result.meta.total,
      page: result.meta.page,
      pageSize: result.meta.page_size,
      totalPages: result.meta.total_pages
    }
  };
}
```

---

## 🧪 Testing Examples

### Using curl

**Execute command:**
```bash
curl -X POST http://192.168.5.12:8001/api/commands/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "device_id": 1,
    "command_type": "volume",
    "parameters": {"volume": 50}
  }'
```

**List commands:**
```bash
curl -X GET "http://192.168.5.12:8001/api/commands/?page=1&limit=10" \
  -H "Authorization: Bearer <token>"
```

### Using JavaScript

**Execute command:**
```javascript
const response = await fetch('/api/commands/execute', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    device_id: 1,
    command_type: 'volume',
    parameters: { volume: 50 }
  })
});

const result = await response.json();
if (result.success) {
  console.log('Command queued:', result.data.id);
}
```

---

## 📚 Additional Resources

- **Full Migration Report:** `/backend/COMMANDS_MIGRATION_REPORT.md`
- **API Documentation:** `http://192.168.5.12:8001/docs`
- **Schema Definitions:** `/backend/app/schemas/command.py`
- **Service Logic:** `/backend/app/services/command_service.py`

---

**Need Help?**
- Check migration report for detailed breaking changes
- Review error responses for debugging
- Use request_id from meta for log tracing
- Monitor structured logs for security events
