# Widgets API - Quick Reference Guide

**Base URL:** `http://192.168.5.12:8001/api/widgets`
**Status:** ✅ Production Ready
**Total Endpoints:** 12

---

## Widget Types

| Type | Name | Description | External Service |
|------|------|-------------|------------------|
| `clock` | Clock | Display time and date | No |
| `weather` | Weather | Weather information | Yes (API key) |
| `calendar` | Calendar | Calendar events | No |
| `countdown` | Countdown | Countdown timers | No |
| `iframe` | iFrame | Embed external URLs | No |
| `text` | Text | Text messages | No |
| `pms` | PMS Integration | Property Management System | Yes (Firebird) |

---

## Endpoints Reference

### 1. List Widgets
```http
GET /api/widgets?page=1&limit=10&widget_type=clock&is_active=true
```

**Query Parameters:**
- `page` (int, default=1): Page number (1-indexed)
- `limit` (int, default=10, max=100): Items per page
- `widget_type` (string, optional): Filter by type
- `is_active` (boolean, optional): Filter by active status

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "widget_type": "clock",
      "widget_name": "Main Clock",
      "position": "top-right",
      "is_overlay": true,
      "is_active": true,
      "config": { "format": "HH:mm:ss", "timezone": "Asia/Jakarta" },
      "created_at": "2025-10-28T10:00:00Z",
      "updated_at": "2025-10-28T10:00:00Z"
    }
  ],
  "meta": {
    "total": 15,
    "page": 1,
    "page_size": 10,
    "total_pages": 2,
    "request_id": "abc123"
  }
}
```

---

### 2. Create Widget
```http
POST /api/widgets
Content-Type: application/json
```

**Request Body (Clock):**
```json
{
  "widget_type": "clock",
  "widget_name": "Lobby Clock",
  "clock_config": {
    "format": "HH:mm:ss",
    "timezone": "Asia/Jakarta",
    "show_date": true,
    "font_size": 48,
    "color": "#FFFFFF"
  },
  "position": "top-right",
  "is_overlay": true,
  "is_active": true
}
```

**Request Body (Weather):**
```json
{
  "widget_type": "weather",
  "widget_name": "Jakarta Weather",
  "weather_config": {
    "api_key": "your_api_key",
    "location": "Jakarta",
    "units": "metric",
    "show_forecast": true,
    "forecast_days": 3,
    "refresh_interval": 1800
  },
  "position": "top-left",
  "is_overlay": true
}
```

**Request Body (Countdown):**
```json
{
  "widget_type": "countdown",
  "widget_name": "Event Countdown",
  "countdown_config": {
    "target_date": "2026-01-01T00:00:00Z",
    "title": "New Year 2026",
    "format": "DHms",
    "show_when_passed": true,
    "passed_message": "Happy New Year!"
  },
  "position": "center"
}
```

---

### 3. Get Widget by ID
```http
GET /api/widgets/{widget_id}
```

**Example:**
```bash
curl http://192.168.5.12:8001/api/widgets/1
```

---

### 4. Update Widget (PUT or PATCH)
```http
PUT /api/widgets/{widget_id}
PATCH /api/widgets/{widget_id}  # Alias for frontend compatibility
Content-Type: application/json
```

**Request Body (Partial Update):**
```json
{
  "widget_name": "Updated Clock Name",
  "is_active": false,
  "clock_config": {
    "timezone": "America/New_York"
  }
}
```

---

### 5. Delete Widget
```http
DELETE /api/widgets/{widget_id}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Widget 'Main Clock' deleted successfully",
    "widget_id": 1,
    "widget_type": "clock"
  }
}
```

---

### 6. Get Widget Types
```http
GET /api/widgets/types/list
```

**Response:**
```json
{
  "success": true,
  "data": {
    "types": [
      {
        "type": "clock",
        "name": "Clock",
        "description": "Display time and date information",
        "icon": "clock",
        "config_schema": { "properties": {...} },
        "requires_external_service": false
      }
    ]
  }
}
```

---

### 7. Assign Widget to Devices
```http
POST /api/widgets/{widget_id}/assign
Content-Type: application/json
```

**Request Body:**
```json
{
  "device_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Widget assigned to 3 device(s)",
    "assignments": [
      {
        "widget_id": 1,
        "device_id": 1,
        "device_name": "TV-001",
        "assigned_at": "2025-10-28T12:00:00Z"
      }
    ]
  }
}
```

---

### 8. Unassign Widget from Devices
```http
DELETE /api/widgets/{widget_id}/assign
Content-Type: application/json
```

**Request Body:**
```json
{
  "device_ids": [1, 2]
}
```

---

### 9. Get Assigned Devices
```http
GET /api/widgets/{widget_id}/assigned-devices
```

**Response:**
```json
{
  "success": true,
  "data": {
    "widget_id": 1,
    "widget_name": "Main Clock",
    "assigned_devices": [
      {
        "device_id": 1,
        "device_name": "TV-001",
        "location": "Lobby",
        "status": "online"
      }
    ],
    "total_assigned": 1
  }
}
```

---

### 10. Preview Widget Configuration
```http
POST /api/widgets/preview
Content-Type: application/json
```

**Request Body:**
```json
{
  "widget_type": "clock",
  "config": {
    "format": "HH:mm:ss",
    "timezone": "Asia/Jakarta"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "rendered_html": "<div>Preview HTML...</div>",
    "data": { "format": "HH:mm:ss" },
    "error": null
  }
}
```

---

### 11. Test Weather API
```http
POST /api/widgets/test-weather-api?api_key=YOUR_KEY&location=Jakarta
```

**Response:**
```json
{
  "success": true,
  "data": {
    "success": true,
    "message": "Weather API connection successful",
    "location": "Jakarta",
    "sample_data": {
      "temperature": 28.5,
      "condition": "Sunny",
      "humidity": 65
    }
  }
}
```

---

## Configuration Examples

### Clock Widget Config
```json
{
  "format": "HH:mm:ss",          // Time format
  "timezone": "Asia/Jakarta",    // Timezone
  "show_date": true,             // Show date
  "date_format": "DD MMMM YYYY", // Date format
  "font_size": 48,               // Font size (12-200)
  "color": "#FFFFFF"             // Text color (hex)
}
```

### Weather Widget Config
```json
{
  "api_key": "your_api_key",     // Weather API key (required)
  "location": "Jakarta",         // Location (required)
  "units": "metric",             // metric/imperial/kelvin
  "show_forecast": true,         // Show forecast
  "forecast_days": 3,            // Days (1-7)
  "refresh_interval": 1800       // Seconds (min 300)
}
```

### Calendar Widget Config
```json
{
  "calendar_url": "https://...",  // iCal/ICS feed URL
  "display_mode": "upcoming",     // upcoming/month/week
  "max_events": 5,                // Max events (1-20)
  "show_past_events": false,      // Show past events
  "days_ahead": 7                 // Days to look ahead (1-90)
}
```

### Countdown Widget Config
```json
{
  "target_date": "2026-01-01T00:00:00Z",  // Target datetime (required)
  "title": "New Year 2026",               // Title (required)
  "format": "DHms",                       // D=days, H=hours, m=minutes, s=seconds
  "show_when_passed": true,               // Show after target passed
  "passed_message": "Happy New Year!"     // Message when countdown reaches zero
}
```

### iFrame Widget Config
```json
{
  "url": "https://example.com",  // URL to embed (required)
  "refresh_interval": 0,         // Auto-refresh (0=disabled)
  "allow_interaction": true,     // Allow user interaction
  "sandbox_mode": false          // Enable iframe sandbox
}
```

### Text Widget Config
```json
{
  "message": "Welcome!",         // Text message (required, max 1000 chars)
  "font_size": 32,               // Font size (12-200)
  "color": "#FFFFFF",            // Text color (hex)
  "background_color": "#000000", // Background color (hex)
  "alignment": "center",         // left/center/right
  "animation": "fade"            // fade/slide/scroll
}
```

### PMS Widget Config
```json
{
  "firebird_config_id": 1,                      // Firebird config ID (required)
  "query_template": "SELECT * FROM ...",       // SQL query (required)
  "display_fields": ["GUEST_NAME", "ROOM"],    // Fields to display (required)
  "refresh_interval": 60,                      // Seconds (min 10)
  "format_template": "<div>{GUEST_NAME}</div>" // HTML template
}
```

---

## Error Responses

### Not Found (404)
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Widget with ID 999 not found",
    "field": null,
    "details": {"widget_id": 999}
  },
  "meta": {
    "timestamp": "2025-10-28T12:00:00Z",
    "request_id": "abc123"
  }
}
```

### Bad Request (400)
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid widget_type. Must be one of: clock, weather, calendar, countdown, iframe, text, pms",
    "field": "widget_type",
    "details": null
  },
  "meta": {
    "timestamp": "2025-10-28T12:00:00Z",
    "request_id": "abc123"
  }
}
```

---

## Frontend Integration

### React Query Example
```javascript
import { useQuery, useMutation } from '@tanstack/react-query'
import { widgetsAPI } from '../../services/api'

// List widgets
const { data: widgetsData } = useQuery({
  queryKey: ['widgets', 'clock'],
  queryFn: () => widgetsAPI.list('clock').then(res => res.data.data)
})

// Create widget
const createMutation = useMutation({
  mutationFn: widgetsAPI.create,
  onSuccess: () => {
    queryClient.invalidateQueries(['widgets'])
  }
})

// Usage
createMutation.mutate({
  widget_type: 'clock',
  widget_name: 'Test Clock',
  clock_config: { format: 'HH:mm:ss', timezone: 'Asia/Jakarta' }
})
```

### API Service (JavaScript)
```javascript
export const widgetsAPI = {
  list: (type) => api.get('/api/widgets', { params: { type } }),
  create: (data) => api.post('/api/widgets', data),
  get: (id) => api.get(`/api/widgets/${id}`),
  update: (id, data) => api.patch(`/api/widgets/${id}`, data),
  delete: (id) => api.delete(`/api/widgets/${id}`),
  assign: (id, data) => api.post(`/api/widgets/${id}/assign`, data),
  unassign: (id, data) => api.delete(`/api/widgets/${id}/assign`, { data })
}
```

---

## Testing with cURL

### List all widgets
```bash
curl http://192.168.5.12:8001/api/widgets
```

### Create clock widget
```bash
curl -X POST http://192.168.5.12:8001/api/widgets \
  -H "Content-Type: application/json" \
  -d '{
    "widget_type": "clock",
    "widget_name": "Test Clock",
    "clock_config": {
      "format": "HH:mm:ss",
      "timezone": "Asia/Jakarta"
    }
  }'
```

### Get widget by ID
```bash
curl http://192.168.5.12:8001/api/widgets/1
```

### Update widget
```bash
curl -X PATCH http://192.168.5.12:8001/api/widgets/1 \
  -H "Content-Type: application/json" \
  -d '{
    "widget_name": "Updated Clock",
    "is_active": false
  }'
```

### Delete widget
```bash
curl -X DELETE http://192.168.5.12:8001/api/widgets/1
```

### Assign to devices
```bash
curl -X POST http://192.168.5.12:8001/api/widgets/1/assign \
  -H "Content-Type: application/json" \
  -d '{"device_ids": [1, 2, 3]}'
```

---

## Common Use Cases

### 1. Create and Deploy Clock Widget
```bash
# 1. Create clock widget
curl -X POST http://192.168.5.12:8001/api/widgets \
  -H "Content-Type: application/json" \
  -d '{
    "widget_type": "clock",
    "widget_name": "Lobby Clock",
    "clock_config": {
      "format": "HH:mm:ss",
      "timezone": "Asia/Jakarta",
      "show_date": true
    },
    "position": "top-right",
    "is_overlay": true
  }'

# 2. Assign to devices (using widget_id from response)
curl -X POST http://192.168.5.12:8001/api/widgets/1/assign \
  -H "Content-Type: application/json" \
  -d '{"device_ids": [1, 2, 3]}'
```

### 2. List Active Weather Widgets
```bash
curl "http://192.168.5.12:8001/api/widgets?widget_type=weather&is_active=true"
```

### 3. Update Widget Configuration
```bash
curl -X PATCH http://192.168.5.12:8001/api/widgets/1 \
  -H "Content-Type: application/json" \
  -d '{
    "clock_config": {
      "timezone": "America/New_York"
    }
  }'
```

### 4. Deactivate Widget (Without Deleting)
```bash
curl -X PATCH http://192.168.5.12:8001/api/widgets/1 \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'
```

---

## Support

**API Documentation:** http://192.168.5.12:8001/docs
**Full Migration Report:** SPRINT2_PART1_WIDGETS_MIGRATION_REPORT.md
**Status:** ✅ Production Ready
