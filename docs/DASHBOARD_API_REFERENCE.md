# Dashboard API Quick Reference

## Overview Metrics Endpoints

### 1. Total & Online Devices
```bash
GET /api/v1/devices
Query Params: 
  - organization_id (auto)
  - status: pending|active|inactive|online|offline
  - limit: 1000

Response: { data: Device[], total: int }
Device fields: id, device_name, status, last_seen, device_type
```

**Calculation:**
- Total devices: `response.total`
- Online devices: Filter by `last_seen > now() - 5 minutes`
- Offline devices: Filter by `status = 'inactive'` OR `last_seen < now() - 5 minutes`

---

### 2. Organization Health Summary
```bash
GET /api/v1/organizations/{organization_id}/health/summary
Requires: Bearer token with matching org_id

Response: {
  total_devices: int,
  healthy_devices: int,
  warning_devices: int,
  critical_devices: int,
  offline_devices: int,
  devices_with_errors: int
}
```

**Usage:** Display health donut chart with status counts

---

### 3. Content Count & Storage
```bash
GET /api/v1/contents
Query Params:
  - organization_id (auto)
  - is_active: true
  - limit: 1000

Response: { data: Content[], total: int }

GET /api/v1/contents/stats
Response: {
  total_files: int,
  total_storage_bytes: int,
  by_type: {
    video: { count: int, size_bytes: int },
    image: { count: int, size_bytes: int },
    audio: { count: int, size_bytes: int }
  }
}
```

**Calculations:**
- Total content: response.total
- Total storage: Convert bytes to GB (divide by 1024^3)
- Storage by type: Use by_type breakdown for pie chart

---

### 4. Active Playlists
```bash
GET /api/v1/playlists
Query Params:
  - organization_id (auto)
  - is_active: true
  - limit: 100

Response: { data: Playlist[], total: int }
Playlist fields: id, name, description, is_active, created_at
```

**Calculation:** Count active playlists from response.total

---

### 5. Playback Statistics (24h)
```bash
GET /api/v1/analytics/stats
Query Params:
  - organization_id (auto)
  - start_date: ISO string (now - 24h)
  - end_date: ISO string (now)

Response: {
  total_plays: int,
  completed_plays: int,
  unique_content: int,
  unique_devices: int,
  total_watch_time_seconds: int,
  total_watch_time_hours: float,
  completion_rate: float (0-100),
  period_start: string,
  period_end: string
}
```

**Display:**
- Watch time: Format as "X hours" or "X days, Y hours"
- Completion rate: Show as percentage with color (green if > 80%)
- Average duration: total_watch_time_seconds / completed_plays

---

## Device Health Section

### 6. Device Health with Latest Metrics
```bash
GET /api/v1/devices/{device_id}/health
Requires: Bearer token

Response: {
  health: {
    id: int,
    device_id: int,
    cpu_usage: float (0-100),
    memory_usage: float (0-100),
    memory_total_mb: int,
    memory_used_mb: int,
    disk_usage: float (0-100),
    disk_total_gb: int,
    disk_used_gb: int,
    network_latency_ms: int,
    network_download_mbps: float,
    network_upload_mbps: float,
    connection_quality: string (excellent|good|fair|poor),
    display_resolution: string (e.g., "1920x1080"),
    display_refresh_rate: int,
    gpu_usage: float (0-100),
    player_version: string,
    player_uptime_hours: int,
    content_errors_count: int,
    last_error_message: string,
    last_error_at: datetime,
    overall_status: string (healthy|warning|critical|offline),
    alert_triggered: boolean,
    alert_message: string
  },
  alerts: [{ /* alert details */ }]
}
```

**Usage:** Show health card for each device with latest metrics

---

### 7. Device Health History (Charts)
```bash
GET /api/v1/devices/{device_id}/health/history
Query Params:
  - hours: 1-168 (default: 24)

Response: {
  history: [
    {
      timestamp: datetime,
      cpu_usage: float,
      memory_usage: float,
      disk_usage: float,
      network_latency_ms: int,
      overall_status: string
    },
    ...
  ],
  count: int
}
```

**Usage:** Time-series chart showing health metrics over time

---

## Content Analytics Section

### 8. Top Content (24h)
```bash
GET /api/v1/analytics/content-performance
Query Params:
  - organization_id (auto)
  - start_date: ISO string
  - end_date: ISO string
  - limit: 5-100 (default: 10)

Response: [
  {
    content_id: int,
    title: string,
    content_type: string (image|video|audio),
    total_plays: int,
    completed_plays: int,
    avg_duration_seconds: float,
    last_played_at: datetime,
    unique_devices: int,
    completion_rate: float (0-100)
  },
  ...
]
```

**Display:** Table with content title, plays, completion rate, devices

---

### 9. Content Storage Breakdown
```bash
GET /api/v1/contents/stats
Response: {
  total_files: int,
  total_storage_bytes: int,
  by_type: {
    video: { count: int, size_bytes: int },
    image: { count: int, size_bytes: int },
    audio: { count: int, size_bytes: int }
  }
}
```

**Display:** Pie chart or horizontal stacked bar chart

---

## Activity Feed Section

### 10. Recent Audit Logs
```bash
GET /api/v1/audit-logs
Query Params:
  - organization_id (auto)
  - limit: 10-100 (default: 20)
  - offset: 0

Response: {
  data: [
    {
      id: int,
      user_id: int,
      organization_id: int,
      action: string (user.create|device.activate|content.upload|...),
      resource_type: string (user|device|content|tag|playlist),
      resource_id: int,
      details: object (JSON),
      ip_address: string,
      user_agent: string,
      created_at: datetime
    },
    ...
  ],
  total: int
}
```

**Display:** Activity feed grouped by time, with human-readable action descriptions

---

## Analytics Timeline Section

### 11. Playback Timeline Chart
```bash
GET /api/v1/analytics/timeline
Query Params:
  - organization_id (auto)
  - start_date: ISO string
  - end_date: ISO string
  - interval: day|week|month

Response: {
  data: [
    {
      period: datetime,
      total_plays: int,
      completed_plays: int,
      unique_content: int,
      unique_devices: int,
      total_watch_time_seconds: int
    },
    ...
  ],
  interval: string,
  start_date: string,
  end_date: string
}
```

**Display:** Multi-line chart with:
- Total plays (primary)
- Completed plays (stacked)
- Unique devices (secondary axis)
- Unique content (secondary axis)

---

## Device Engagement Section

### 12. Device Engagement Analytics
```bash
GET /api/v1/analytics/device-engagement
Query Params:
  - organization_id (auto)
  - start_date: ISO string
  - end_date: ISO string
  - limit: 5-100

Response: [
  {
    device_id: int,
    device_name: string,
    total_plays: int,
    unique_content: int,
    last_playback_at: datetime,
    total_watch_time_seconds: int,
    total_watch_time_hours: float
  },
  ...
]
```

**Display:** Table showing device engagement metrics

---

## Device Groups Section

### 13. Device Group Statistics
```bash
GET /api/v1/devices/groups/{group_id}/stats
Requires: Bearer token

Response: {
  total_devices: int,
  online_devices: int,
  offline_devices: int,
  pending_devices: int,
  healthy_devices: int,
  warning_devices: int,
  critical_devices: int
}
```

**Display:** Summary card showing group health and status

---

### 14. Devices in Group
```bash
GET /api/v1/devices/groups/{group_id}/devices
Query Params:
  - recursive: true|false (include child groups)

Response: {
  devices: [int, ...], // device IDs
  count: int
}
```

**Usage:** Get list of device IDs in group, then fetch details for each

---

## Complete Dashboard Query Example

### Frontend Implementation Pattern

```typescript
// 1. Fetch all core data in parallel
const [
  devicesResult,
  healthSummary,
  analyticsStats,
  contentStats,
  topContent,
  auditLogs
] = await Promise.all([
  fetch('/api/v1/devices'),
  fetch('/api/v1/organizations/{orgId}/health/summary'),
  fetch('/api/v1/analytics/stats?start_date=...&end_date=...'),
  fetch('/api/v1/contents/stats'),
  fetch('/api/v1/analytics/content-performance?limit=5&start_date=...&end_date=...'),
  fetch('/api/v1/audit-logs?limit=10')
]);

// 2. Process responses and calculate metrics
const devices = devicesResult.data;
const totalDevices = devices.length;
const onlineDevices = devices.filter(d => d.last_seen > 5_mins_ago).length;

// 3. Render dashboard with data
// - Show overview metrics
// - Display health summary
// - List top content
// - Show activity feed
// etc.
```

---

## Query Parameter Notes

### Date/Time Format
- ISO 8601 format: `2024-11-12T23:38:00Z` or `2024-11-12`
- JavaScript: `new Date().toISOString()`
- Python: `datetime.utcnow().isoformat() + 'Z'`

### Status Values
- Device status: `pending`, `active`, `inactive`
- Device connectivity: `online`, `offline` (calculated from last_seen)
- Health status: `healthy`, `warning`, `critical`, `offline`

### Intervals for Timeline
- `day`: Daily aggregation
- `week`: Weekly aggregation (Monday-Sunday)
- `month`: Monthly aggregation

### Cache Recommendations
- Device list: 30 seconds (changes frequently)
- Device health: 60 seconds
- Content list: 300 seconds
- Analytics: 300 seconds (historical data)
- Audit logs: 10 seconds (should be fresh)

---

## Error Handling

All endpoints return standard response:

### Success Response
```json
{
  "success": true,
  "data": { /* actual data */ },
  "message": "Success message"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message",
  "status_code": 400
}
```

### Common Status Codes
- 200: Success
- 400: Bad request (invalid parameters)
- 401: Unauthorized (missing/invalid token)
- 403: Forbidden (insufficient permissions)
- 404: Not found (resource doesn't exist)
- 500: Server error

---

## Authentication

All endpoints (except public registration/login) require:
```
Header: Authorization: Bearer {token}
```

Token automatically scopes results to user's organization.

---

## Usage Tips

1. **Batch Device Details**: If you need health for multiple devices, fetch them in parallel
2. **Pagination**: Use `limit` and `offset` for large result sets
3. **Filtering**: Use query parameters to reduce data transfer
4. **Caching**: Use stale-while-revalidate pattern for better UX
5. **Real-time**: Use WebSocket for device status changes instead of polling
6. **Aggregation**: Pre-aggregate data on backend when possible (analytics endpoints already do this)

