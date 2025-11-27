# Comprehensive Dashboard Analysis - Signate Digital Signage System

## Executive Summary

The Signate platform has a robust backend with rich data models and multiple services that can be leveraged to build a comprehensive dashboard. Current implementation is minimal (placeholder UI), but the backend provides extensive API endpoints for analytics, device monitoring, content management, and system health.

---

## 1. BACKEND API ENDPOINTS AVAILABLE

### A. Analytics Service (`/api/v1/analytics`)
**Current Endpoints:**
- `GET /dashboard` - Complete analytics dashboard with stats, top content, top devices
- `GET /stats` - Overall playback statistics
- `GET /content-performance` - Content performance analytics
- `GET /device-engagement` - Device engagement analytics
- `GET /timeline` - Playback timeline data (day/week/month intervals)
- `POST /playback/start` - Log playback start
- `PUT /playback/{log_id}/end` - Log playback end

**Data Available:**
- Total plays, completed plays, completion rate
- Average playback duration
- Content performance metrics (plays, devices, completion rate)
- Device engagement metrics (watch time, unique content)
- Timeline data with intervals (daily, weekly, monthly)
- Error tracking and playback quality data

### B. Device Management (`/api/v1/devices`)
**Key Endpoints:**
- `GET /devices` - List all devices with status (online/offline/pending/active/inactive)
- `GET /devices/{id}` - Single device details
- `GET /devices/{id}/logs` - Device logs
- `GET /devices/{id}/commands` - Pending commands
- `GET /devices/{id}/health` - Latest health metrics
- `GET /devices/{id}/health/history` - Historical health data (up to 7 days)
- `GET /devices/{id}/speed-tests` - Network speed test history

**Device Groups:**
- `GET /devices/groups` - All groups
- `GET /devices/groups/roots` - Root groups (hierarchy)
- `GET /devices/groups/{id}/stats` - Group statistics
- `GET /devices/groups/{id}/devices` - Devices in group
- `GET /devices/groups/{id}/children` - Child groups

**Data Available:**
- Device status (online/offline/pending/active/inactive)
- Last seen timestamp
- Network info (IP, connection type, connection speed)
- Platform info (WebOS, browser, etc.)
- Device metadata (screen resolution, firmware version)
- Room mapping (for hotel context)
- Assigned playlist
- Tags

### C. Device Health Monitoring (`/api/v1/devices/{id}/health`)
**Health Metrics Tracked:**
- CPU usage (%)
- Memory usage (%, total MB, used MB)
- Disk usage (%, total GB, used GB)
- Network metrics (latency ms, download/upload Mbps, quality)
- Display metrics (resolution, refresh rate, GPU %)
- Player metrics (version, uptime hours, error count)
- Health status (healthy/warning/critical/offline)
- Alerts (triggered, message)

**Organization-wide Health:**
- `GET /organizations/{id}/health/summary` - Organization health summary
  - Total devices
  - Healthy/warning/critical/offline device counts
  - Devices with errors

### D. Content Management (`/api/v1/contents`)
**Endpoints:**
- `GET /contents` - List all content
- `GET /contents/{id}` - Content details
- `GET /contents/stats` - Content storage statistics

**Content Data:**
- Content type (image, video, audio)
- File metadata (size, MIME type, hash)
- Media properties (resolution, codec, FPS, bitrate)
- Upload status (pending/processing/completed/failed)
- Transcoding status (HLS for video)
- Thumbnail info
- Organization & uploader tracking
- Timestamps (created, updated, deleted)

**Storage Stats Tracked:**
- Total file count
- Total storage used
- Storage by content type
- Organization quota tracking

### E. Playlist Management (`/api/v1/playlists`)
**Endpoints:**
- `GET /playlists` - List playlists
- `GET /playlists/{id}` - Playlist details
- `GET /playlists/{id}/content` - Content in playlist
- `GET /playlists/{id}/assignments` - Device/tag assignments

**Playlist Data:**
- Name, description, priority
- Is active, is default, is PMS template
- Content list with order and duration
- Device assignments
- Tag assignments
- Creator and timestamps

### F. Audit & Activity Logging (`/api/v1/audit-logs`)
**Endpoints:**
- `GET /audit-logs` - List audit logs
- `GET /audit-logs/{id}` - Single audit log

**Audit Data Tracked:**
- User ID (who performed action)
- Action type (user.create, device.activate, content.upload, etc.)
- Resource type and ID
- IP address and User agent
- Custom details (JSON)
- Timestamps

**Valid Actions:**
- user.create, user.update, user.delete, user.change_password
- organization.create, organization.update, organization.delete
- device.create, device.update, device.delete, device.activate
- content.upload, content.delete, content.assign
- tag.create, tag.update, tag.delete
- auth.login, auth.logout, auth.register

### G. Session Management (`/api/v1/sessions`)
**Endpoints:**
- `GET /sessions` - List user's sessions
- `GET /sessions/stats` - Session statistics
- `GET /sessions/active` - Active sessions

**Session Data:**
- Active sessions count
- Session duration
- Device/IP tracking
- Last activity timestamp

### H. Organization Stats
**Endpoints:**
- `GET /organizations/{id}` - Organization details
- Organization health summary
- User count in organization
- Device count in organization

### I. Tags (`/api/v1/tags`)
**Endpoints:**
- `GET /tags` - List tags
- `GET /tags/{id}/usage` - Tag usage statistics
- Content tagged count
- Device tagged count

---

## 2. DATABASE MODELS & DATA STRUCTURE

### Key Models Tracking Metrics:

#### A. Device Model
```
- id, device_type, device_name, organization_id
- unique_code, device_uuid, status
- ip_address, platform, firmware_version
- screen dimensions, pixel ratio, user_agent
- connection_type, connection_speed
- last_seen, created_at, updated_at
- assigned_playlist_id, room_number
- location_type, supports_personalization
- Many-to-Many: tags, commands, health_metrics
```

#### B. DeviceHealthMetricModel
```
- id, device_id, organization_id
- CPU, memory, disk usage (%)
- Network: latency, download/upload speed, quality
- Display: resolution, refresh rate, GPU usage
- Player: version, uptime, error count
- overall_status, alert_triggered
- Extra metadata (JSON)
- Timestamps: recorded_at, created_at
```

#### C. ContentModel
```
- id, title, content_type, file_path, storage_key, file_hash
- duration, is_active
- file_size, mime_type, file_extension
- Media: resolution, width, height, codec, fps, bitrate
- Audio: codec, bitrate, sample_rate, channels
- Transcoding: status, progress, HLS paths
- Thumbnail: path, URL, generated_at
- upload_status, organization_id, uploaded_by
- created_at, updated_at, deleted_at
```

#### D. ContentPlaybackLog (Analytics)
```
- id, content_id, device_id, playlist_id, organization_id
- started_at, ended_at, duration_seconds, expected_duration
- completed (boolean)
- device_info (JSON), playback_quality
- error_count, error_details (JSON)
- created_at
```

#### E. PlaylistModel
```
- id, name, description, is_active, priority
- is_default, is_pms_template
- organization_id, created_by
- created_at, updated_at, deleted_at
- Relationships: contents, assignments
```

#### F. AuditLog
```
- id, user_id, organization_id
- action (string), resource_type, resource_id
- details (JSON), ip_address, user_agent
- created_at
```

#### G. DeviceCommand
```
- id, device_id, organization_id
- command_type, command_data (JSON)
- status, priority
- sent_at, executed_at, failed_at
- result (JSON), error_message
- retry_count, max_retries, expires_at
- created_by, created_at, updated_at
```

---

## 3. CURRENT DASHBOARD IMPLEMENTATION

### File: `/cms-vite/src/pages/DashboardPage.tsx`

**Current State:**
- Minimal placeholder implementation
- Shows:
  - Welcome message with user name
  - User information section (username, email, role, active status)
  - 3 stat cards with hardcoded "0" values:
    - Total Devices
    - Active Content
    - Playlists

**What's Missing:**
- No API integration
- No data fetching
- No real metrics
- No charts or visualizations
- No activity feeds
- No system health overview
- No recent actions
- No quick actions

---

## 4. RECOMMENDED DASHBOARD SECTIONS

### Section 1: Overview Metrics (Top Row)
**Cards with Key Numbers:**
1. **Total Devices** 
   - Endpoint: `GET /api/v1/devices`
   - Data: Count all devices
   - Color: Varies by status distribution

2. **Devices Online** (Last 5 minutes)
   - Endpoint: `GET /api/v1/devices` + filter by last_seen
   - Calculate: last_seen > 5 minutes ago
   - Color: Green if > 80% online, yellow if 50-80%, red if < 50%

3. **Total Content**
   - Endpoint: `GET /api/v1/contents`
   - Data: Count active content
   - Add: Storage usage from stats

4. **Active Playlists**
   - Endpoint: `GET /api/v1/playlists`
   - Data: Count is_active=true playlists
   - Add: Devices assigned

5. **Total Watch Time (24h)**
   - Endpoint: `GET /api/v1/analytics/stats?start_date=...&end_date=...`
   - Data: total_watch_time_hours
   - Format: "X hours" or "X days"

6. **Completion Rate (24h)**
   - Endpoint: `GET /api/v1/analytics/stats`
   - Data: completion_rate (%)
   - Trend: Show change from previous 24h

---

### Section 2: Device Health Overview
**Organization Health Summary:**
- Endpoint: `GET /api/v1/organizations/{org_id}/health/summary`
- Display:
  ```
  Total: 50 devices
  Healthy: 45 (90%) - Green
  Warning: 3 (6%)  - Yellow
  Critical: 1 (2%) - Red
  Offline: 1 (2%)  - Gray
  ```
- Visual: Donut chart or horizontal bar chart
- Click to drill down into each status group

**Top Issues (Critical & Warning):**
- Fetch all device health summaries
- Filter by status != healthy
- Show top 5 with:
  - Device name, room, status
  - Alert message
  - Latest metric (e.g., "CPU 92%")
  - Time of last metric

---

### Section 3: Device Status Grid (Expandable by Location)
**Device Monitoring List:**
- Endpoint: `GET /api/v1/devices` + `GET /api/v1/devices/{id}/health`
- Display columns:
  - Device name (link to detail page)
  - Room/Location (from device.room_number)
  - Status badge (online/offline/pending)
  - Last seen (human-readable: "2 mins ago")
  - Health status (green/yellow/red)
  - Assigned playlist
  - Quick actions (view logs, send command)

**Filtering & Grouping:**
- Filter by: location, status, health
- Group by: device group/hierarchy
- Sort by: status, last_seen, health

---

### Section 4: Content Analytics
**Top Content (Last 24h or Configurable):**
- Endpoint: `GET /api/v1/analytics/content-performance?limit=5`
- Display table:
  - Content title (link to detail)
  - Type (video, image, audio)
  - Total plays, Completed plays
  - Completion rate (%), Unique devices
  - Last played (timestamp)
  - Quick action: view details

**Content Storage Breakdown:**
- Endpoint: `GET /api/v1/contents/stats`
- Display:
  - Total files: 120
  - Total storage: 50.5 GB
  - By type: Videos (35GB), Images (12GB), Audio (3.5GB)
  - % of quota used (if quota exists)
- Visual: Pie chart or horizontal stacked bar

---

### Section 5: Playlist & Schedule Overview
**Active Playlists:**
- Endpoint: `GET /api/v1/playlists?is_active=true`
- Show:
  - Playlist name, description
  - Device count (from assignments)
  - Content count
  - Created date
  - Last modified

**Devices by Playlist:**
- Endpoint: `GET /api/v1/playlists/{id}/assignments`
- Group devices by assigned playlist
- Show: "Playlist A: 25 devices", "Playlist B: 18 devices"

---

### Section 6: Activity Feed & Recent Actions
**Recent Audit Logs:**
- Endpoint: `GET /api/v1/audit-logs?limit=10&sort=created_at:desc`
- Display items:
  - Action: "User 'John' activated device 'Room 101'"
  - Resource: Device, Content, Playlist, User
  - Timestamp: "5 mins ago"
  - User: "John Doe"
- Group by: hour or 30 mins
- Filter: show last 10 actions across all resource types

**Filter Options:**
- By action type (create, update, delete, upload, activate)
- By resource type (device, content, user)
- By user
- By time range

---

### Section 7: Playback Timeline (Historical View)
**Timeline Chart:**
- Endpoint: `GET /api/v1/analytics/timeline?interval=day&start_date=...&end_date=...`
- Data points:
  - Total plays (line chart)
  - Completed plays (stacked)
  - Unique devices (secondary axis)
  - Unique content (secondary axis)
- Time range selector: 7 days, 30 days, custom
- Interval selector: Day, Week, Month

---

### Section 8: System Health & Performance
**Backend Health Indicators:**
- Database status (connectivity, query performance)
- Storage service status (capacity, errors)
- Cache status (hit rate if applicable)
- WebSocket connections (live device count)

**Quick Diagnostics:**
- Last sync with PMS (if configured)
- Transcoding queue status (pending, in-progress)
- Error logs summary (last hour)
- Slowest queries/operations

---

### Section 9: Quick Actions Panel
**Common Tasks Shortcuts:**
- Upload Content (modal)
- Create Playlist (modal)
- Add Device (modal)
- Create Schedule (modal)
- Send Command to Group (modal)
- View Offline Devices (link to devices page with filter)
- Generate Report (export)

---

### Section 10: Key Metrics Summary Cards
**Additional Metric Cards:**
1. **Average Session Duration** (24h)
   - Calc from: playback_log where completed=true, AVG(duration_seconds)

2. **Error Rate** (24h)
   - Calc: errors / total_plays * 100
   - From: ContentPlaybackLog where error_count > 0

3. **Network Issues**
   - Count devices where: connection_quality != 'excellent'
   - Or: network_latency_ms > 200ms

4. **Device Commands Pending**
   - Count: DeviceCommand where status='pending'
   - Show: "5 commands waiting" with urgency indicator

5. **Storage Remaining**
   - Calc: total_quota - current_used
   - Show: percentage and absolute value
   - Alert if > 90% used

6. **Active Users**
   - Count: Session where last_activity > now() - 5 mins
   - Or: From auth logs

---

## 5. API INTEGRATION PRIORITIES

### Priority 1 (Must Have)
1. Device list with status (online/offline)
2. Device count by status
3. Content count
4. Playlist count
5. Organization health summary

### Priority 2 (Should Have)
1. Analytics dashboard (top content, device engagement)
2. Device health metrics
3. Recent audit logs
4. Content storage stats
5. Playback timeline chart

### Priority 3 (Nice to Have)
1. Device health history charts
2. Device health alerts
3. Tag usage analytics
4. Session statistics
5. PMS sync status
6. Transcoding queue status

---

## 6. FRONTEND IMPLEMENTATION NOTES

### File Structure
```
cms-vite/src/features/dashboard/
├── api/
│   └── dashboardApi.ts          (API client functions)
├── components/
│   ├── OverviewCards.tsx         (Top metrics)
│   ├── DeviceHealthSummary.tsx   (Health donut)
│   ├── DeviceMonitoringList.tsx  (Device grid)
│   ├── ContentAnalytics.tsx      (Top content)
│   ├── ActivityFeed.tsx          (Audit logs)
│   ├── PlaybackTimeline.tsx      (Chart)
│   └── QuickActions.tsx          (Shortcuts)
├── hooks/
│   └── useDashboard.ts           (Data fetching with TanStack Query)
└── types/
    └── dashboard.ts             (TypeScript types)
```

### State Management
- Use **TanStack Query** for server state (API data)
- Use **Zustand** for global state if needed (filters, selected period)
- Cache queries with appropriate stale times (60s for health, 300s for analytics)

### Real-time Updates
- WebSocket for device status changes
- Periodic polling for health metrics (30s interval)
- Analytics updates every 5 minutes

---

## 7. DATA FLOW EXAMPLES

### Example 1: Device Status Dashboard
```
1. Query: GET /api/v1/devices
   Response: Array of devices with status, last_seen, etc.
2. For each device with status != online:
   Query: GET /api/v1/devices/{id}/health
   Get: latest health metrics
3. Aggregate: Count by status
4. Display: Overview cards + Device list
5. Refresh: Every 30 seconds via polling
```

### Example 2: Content Performance
```
1. Date range: last 24h
2. Query: GET /api/v1/analytics/content-performance?limit=10&start_date=...&end_date=...
   Response: List of content with plays, completion rate, etc.
3. Query: GET /api/v1/contents/stats
   Response: Storage breakdown
4. Display: Content table + Storage chart
5. Refresh: Every 5 minutes
```

### Example 3: Activity Feed
```
1. Query: GET /api/v1/audit-logs?limit=20&sort=created_at:desc
   Response: List of audit logs
2. Transform: Group by timestamp (hour/30min)
3. Display: Activity feed with human-readable descriptions
4. Refresh: Real-time via WebSocket if available, else polling 10s
```

---

## 8. ADDITIONAL INSIGHTS FOR DEVELOPMENT

### Response Handling
All backend endpoints return:
```json
{
  "success": true,
  "data": { /* actual data */ },
  "message": "Success message"
}
```

Errors return:
```json
{
  "success": false,
  "error": "Error message",
  "status_code": 400
}
```

### Authentication
All dashboard endpoints require:
- Bearer token in Authorization header
- Token scoped to organization_id (automatically filtered in queries)

### Pagination
Some endpoints support:
- `limit`: number of results
- `offset`: for pagination
- Examples in analytics: limit=10 (default), ge=1, le=100

### Filtering
Device list supports filtering by:
- organization_id (automatic)
- status
- last_seen
- device_type

Analytics support filtering by:
- start_date, end_date (ISO format)
- organization_id (automatic)

---

## 9. PERFORMANCE CONSIDERATIONS

### Query Optimization
- Use `limit` parameters to avoid fetching all data
- Combine related queries (e.g., devices + health in parallel)
- Cache device list (30s stale time), health metrics (60s)
- Lazy load detailed views

### Data Volume
- Device health metrics: 1 per device per 5 minutes = ~12 per day per device
- Audit logs: Variable, but typically 10-50 per day
- Analytics: Aggregated, not individual records

### Recommended Cache Times
- Device list: 30s (changes frequently)
- Device health: 60s (updated less frequently)
- Content list: 300s (rarely changes)
- Analytics dashboard: 300s (historical data)
- Audit logs: 10s (should be fresh)

---

## 10. SUMMARY TABLE

| Data Type | Endpoint | Update Freq | Cache | Priority |
|-----------|----------|-------------|-------|----------|
| Device Status | GET /devices | 30s | 30s | P1 |
| Device Health | GET /devices/{id}/health | 60s | 60s | P2 |
| Content Stats | GET /contents/stats | 300s | 300s | P2 |
| Analytics | GET /analytics/dashboard | 300s | 300s | P2 |
| Audit Logs | GET /audit-logs | 10s | 10s | P2 |
| Playback Timeline | GET /analytics/timeline | 300s | 300s | P3 |
| Playlists | GET /playlists | 300s | 300s | P2 |
| Health Summary | GET /orgs/{id}/health/summary | 60s | 60s | P2 |
| Device Groups | GET /devices/groups | 300s | 300s | P3 |

---

## Conclusion

The backend is well-structured with comprehensive APIs available for building a rich, informative dashboard. The recommended approach is:

1. **Phase 1**: Implement core metrics (device counts, health, content)
2. **Phase 2**: Add analytics and activity monitoring
3. **Phase 3**: Enhance with historical charts and advanced filters

All necessary endpoints and data models are in place. Frontend development can proceed with confidence that backend support is available for all planned features.
