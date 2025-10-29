# New Endpoints - Quick Reference Card

**Date:** October 28, 2025
**Status:** ✅ READY FOR USE

---

## 🌐 GET /api/languages

**Purpose:** Get list of supported languages for multi-language content

### Request
```bash
curl -X GET http://192.168.5.12:8001/api/languages
```

### Response
```json
{
  "success": true,
  "data": {
    "languages": [
      {"code": "en", "name": "English", "native_name": "English", "direction": "ltr"},
      {"code": "id", "name": "Indonesian", "native_name": "Bahasa Indonesia", "direction": "ltr"},
      {"code": "zh", "name": "Chinese", "native_name": "中文", "direction": "ltr"}
    ],
    "default_language": "en",
    "total_count": 3
  },
  "meta": {
    "timestamp": "2025-10-28T12:00:00Z",
    "request_id": "abc-123",
    "version": "1.0.0"
  }
}
```

**Auth:** Optional (public endpoint)
**Used By:** Viewer (language-manager.js)

---

## 📅 Schedule Management Endpoints

### 1. GET /api/schedules - List All Schedules

**Purpose:** Get all schedules with optional filtering

#### Request
```bash
# List all schedules
curl -X GET http://192.168.5.12:8001/api/schedules

# Filter by device
curl -X GET http://192.168.5.12:8001/api/schedules?device_id=123

# Filter by content
curl -X GET http://192.168.5.12:8001/api/schedules?content_id=456

# Filter by active status
curl -X GET http://192.168.5.12:8001/api/schedules?is_active=true

# Multiple filters
curl -X GET http://192.168.5.12:8001/api/schedules?device_id=123&is_active=true
```

#### Response
```json
{
  "success": true,
  "data": {
    "total": 3,
    "items": [
      {
        "id": 1,
        "schedule_name": "Morning News",
        "device_id": 123,
        "content_id": 456,
        "day_of_week": "0,1,2,3,4",
        "start_time": "08:00:00",
        "end_time": "17:00:00",
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": null,
        "is_active": true,
        "priority": 100,
        "notes": "Business hours",
        "created_at": "2025-10-28T12:00:00Z",
        "updated_at": "2025-10-28T12:00:00Z"
      }
    ]
  },
  "meta": {
    "timestamp": "2025-10-28T12:00:00Z",
    "request_id": "xyz-789",
    "version": "1.0.0"
  }
}
```

---

### 2. POST /api/schedules - Create Schedule

**Purpose:** Create a new content schedule

#### Request
```bash
curl -X POST http://192.168.5.12:8001/api/schedules \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_name": "Morning News",
    "device_id": 123,
    "content_id": 456,
    "day_of_week": "0,1,2,3,4",
    "start_time": "08:00:00",
    "end_time": "17:00:00",
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": null,
    "is_active": true,
    "priority": 100,
    "notes": "Display during business hours"
  }'
```

#### Field Descriptions
| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `schedule_name` | ✅ Yes | string | Name of schedule (1-100 chars) |
| `content_id` | ✅ Yes | integer | Content ID to schedule |
| `device_id` | ❌ No | integer | Device ID (optional, can be tag-based) |
| `day_of_week` | ❌ No | string | Days "0,1,2,3,4" (0=Mon, 6=Sun) |
| `start_time` | ❌ No | time | Start time "HH:MM:SS" |
| `end_time` | ❌ No | time | End time "HH:MM:SS" |
| `start_date` | ❌ No | datetime | Start date ISO format |
| `end_date` | ❌ No | datetime | End date ISO format |
| `is_active` | ❌ No | boolean | Active status (default: true) |
| `priority` | ❌ No | integer | Priority 1-1000 (default: 100) |
| `notes` | ❌ No | string | Admin notes (max 1000 chars) |

#### Response
```json
{
  "success": true,
  "data": {
    "id": 1,
    "schedule_name": "Morning News",
    // ... full schedule object
    "created_at": "2025-10-28T12:00:00Z"
  },
  "meta": {
    "timestamp": "2025-10-28T12:00:00Z",
    "request_id": "def-456",
    "version": "1.0.0"
  }
}
```

**Status Code:** 201 Created

---

### 3. GET /api/schedules/{id} - Get Single Schedule

**Purpose:** Retrieve a specific schedule by ID

#### Request
```bash
curl -X GET http://192.168.5.12:8001/api/schedules/1
```

#### Response
```json
{
  "success": true,
  "data": {
    "id": 1,
    "schedule_name": "Morning News",
    "device_id": 123,
    "content_id": 456,
    // ... full schedule details
  },
  "meta": {
    "timestamp": "2025-10-28T12:00:00Z",
    "request_id": "ghi-789",
    "version": "1.0.0"
  }
}
```

**Error Response (404):**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Schedule with ID 1 not found",
    "field": null,
    "details": {"resource_type": "Schedule", "resource_id": 1}
  },
  "meta": {
    "timestamp": "2025-10-28T12:00:00Z",
    "request_id": "jkl-012",
    "version": "1.0.0"
  }
}
```

---

### 4. PUT /api/schedules/{id} - Update Schedule

**Purpose:** Update an existing schedule (partial updates supported)

#### Request
```bash
# Update single field
curl -X PUT http://192.168.5.12:8001/api/schedules/1 \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# Update multiple fields
curl -X PUT http://192.168.5.12:8001/api/schedules/1 \
  -H "Content-Type: application/json" \
  -d '{
    "priority": 150,
    "notes": "Updated schedule"
  }'
```

#### All Fields Optional
- Any field from ScheduleCreate can be updated
- Only provided fields will be updated
- Validation still applies

#### Response
```json
{
  "success": true,
  "data": {
    "id": 1,
    "schedule_name": "Morning News",
    "is_active": false,
    "priority": 150,
    // ... updated schedule
    "updated_at": "2025-10-28T13:00:00Z"
  },
  "meta": {
    "timestamp": "2025-10-28T13:00:00Z",
    "request_id": "mno-345",
    "version": "1.0.0"
  }
}
```

---

### 5. DELETE /api/schedules/{id} - Delete Schedule

**Purpose:** Delete a schedule

#### Request
```bash
curl -X DELETE http://192.168.5.12:8001/api/schedules/1
```

#### Response
```json
{
  "success": true,
  "data": {
    "message": "Schedule 'Morning News' deleted successfully",
    "deleted_id": 1
  },
  "meta": {
    "timestamp": "2025-10-28T13:00:00Z",
    "request_id": "pqr-678",
    "version": "1.0.0"
  }
}
```

---

## 🔐 Authentication

**Current Status:** Optional authentication (public endpoints)
**Production Ready:** Yes, can enforce auth by changing:
```python
# From:
current_user: Optional[User] = Depends(get_optional_user)

# To:
current_user: User = Depends(get_current_active_user)
```

**Add Token:**
```bash
curl -X GET http://192.168.5.12:8001/api/schedules \
  -H "Authorization: Bearer your_jwt_token"
```

---

## ⚠️ Validation Rules

### Day of Week Format
- **Valid:** `"0,1,2,3,4"` (weekdays)
- **Valid:** `"5,6"` (weekends)
- **Valid:** `"0,2,4"` (Mon, Wed, Fri)
- **Invalid:** `"7"` (only 0-6 allowed)
- **Invalid:** `"Mon,Tue"` (must be numbers)

### Time Ranges
- `end_time` must be after `start_time`
- Format: `"HH:MM:SS"` (24-hour)
- Examples: `"08:00:00"`, `"17:30:00"`, `"23:59:59"`

### Date Ranges
- `end_date` must be after `start_date`
- Format: ISO 8601 with timezone
- Example: `"2025-01-01T00:00:00Z"`

### Priority
- Range: 1-1000
- Default: 100
- Higher number = higher priority

---

## 🧪 Testing Commands

### Quick Test Script
```bash
#!/bin/bash
API="http://192.168.5.12:8001"

# Test languages
echo "1. Testing GET /api/languages..."
curl -s "$API/api/languages" | jq '.success'

# Test schedule list
echo "2. Testing GET /api/schedules..."
curl -s "$API/api/schedules" | jq '.data.total'

# Test schedule create
echo "3. Testing POST /api/schedules..."
SCHEDULE_ID=$(curl -s -X POST "$API/api/schedules" \
  -H "Content-Type: application/json" \
  -d '{"schedule_name":"Test","content_id":1,"is_active":true,"priority":100}' \
  | jq -r '.data.id')
echo "Created schedule ID: $SCHEDULE_ID"

# Test schedule get
echo "4. Testing GET /api/schedules/$SCHEDULE_ID..."
curl -s "$API/api/schedules/$SCHEDULE_ID" | jq '.data.schedule_name'

# Test schedule update
echo "5. Testing PUT /api/schedules/$SCHEDULE_ID..."
curl -s -X PUT "$API/api/schedules/$SCHEDULE_ID" \
  -H "Content-Type: application/json" \
  -d '{"priority":200}' \
  | jq '.data.priority'

# Test schedule delete
echo "6. Testing DELETE /api/schedules/$SCHEDULE_ID..."
curl -s -X DELETE "$API/api/schedules/$SCHEDULE_ID" | jq '.success'

echo "All tests passed! ✅"
```

---

## 📊 Response Format (Quick Wins Standard)

All endpoints follow the Quick Wins standardized response format:

### Success Response
```json
{
  "success": true,
  "data": { /* actual payload */ },
  "meta": {
    "timestamp": "2025-10-28T12:00:00Z",
    "request_id": "unique-id",
    "version": "1.0.0"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "field": "field_name",  // for validation errors
    "details": { /* additional context */ }
  },
  "meta": {
    "timestamp": "2025-10-28T12:00:00Z",
    "request_id": "unique-id",
    "version": "1.0.0"
  }
}
```

### HTTP Status Codes
| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Validation error |
| 404 | Not Found | Resource doesn't exist |
| 500 | Server Error | Internal error |

---

## 🔗 API Documentation

**Interactive Docs:** http://192.168.5.12:8001/docs

Try out the endpoints directly in your browser!

---

## 📞 Support

**Questions?**
- Review: `MISSING_ENDPOINTS_IMPLEMENTATION_COMPLETE.md`
- Check logs: `docker logs signage-backend`
- API docs: http://192.168.5.12:8001/docs

---

**Quick Reference Version:** 1.0
**Last Updated:** October 28, 2025
