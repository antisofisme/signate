# Device Implementation Analysis - Backend-Old

## Executive Summary

The device implementation in `backend-old` represents a sophisticated multi-device digital signage system with:
- **Dual device type support**: TV (WebOS/native) + Monitor (browser-based)
- **Self-registration flow**: Devices generate their own activation codes and activate without admin intervention
- **JWT-based device authentication**: 30-day tokens for secure device-API communication
- **Remote command queue system**: Admin-to-device instruction execution
- **Network monitoring**: Speed testing and connectivity tracking
- **Flexible content assignment**: Direct device, tag-based, and playlist-based content routing
- **Multi-tenancy support**: Organization-level isolation and device management

---

## Database Schema & Tables

### Core Device Tables

#### 1. **devices** (Main device registry)
```sql
Column Name               | Type           | Purpose
--------------------------|----------------|-------------------------------------
id                        | Integer (PK)   | Unique device identifier
device_type               | String(20)     | 'tv' or 'monitor'
device_name               | String(100)    | Display name (e.g., "Lobby TV 1")
ip_address                | String(45)     | IPv4/IPv6 address
passphrase                | String(50)     | WebOS TV pairing passphrase
unique_code               | String(20)     | 6-char activation code (monitors)
code_expires_at           | DateTime       | When activation code expires (10 min default)
device_uuid               | String(36)     | UUID v4 permanent identifier
platform                  | String(20)     | 'webOS', 'browser', 'Tizen', etc.
model_name                | String(100)    | Device model (e.g., "LG OLED55C1PUB")
firmware_version          | String(50)     | OS/firmware version
status                    | String(20)     | pending, active, inactive, maintenance
last_seen                 | DateTime       | Last heartbeat timestamp
screen_width              | Integer        | Display width in pixels
screen_height             | Integer        | Display height in pixels
viewport_width            | Integer        | Viewport width (may differ from screen)
viewport_height           | Integer        | Viewport height
device_pixel_ratio        | Float          | DPR for high-DPI displays
user_agent                | Text           | Browser/client user agent
connection_type           | String(50)     | '4g', 'wifi', 'ethernet', etc.
connection_speed          | Float          | Connection speed in Mbps
rotation                  | Integer        | 0, 90, 180, 270 degrees
volume_enabled            | Boolean        | Whether device audio is enabled
room_number               | String(20)     | Hotel room ID (optional)
location_type             | String(50)     | guest_room, public_area, staff_area, meeting_room
supports_personalization  | Boolean        | Can show personalized content
privacy_mode              | String(50)     | full, limited, none (guest data visibility)
organization_id           | Integer (FK)   | Multi-tenancy: org isolation
created_by                | Integer (FK)   | User who registered device
created_at                | DateTime       | Registration timestamp
updated_at                | DateTime       | Last modification timestamp
released_at               | DateTime       | When device was released (orphaned)
```

**Indexes**: device_type, status, last_seen, organization_id, unique_code, device_uuid

**Relationships**:
- ← tags (DeviceTag) - Many-to-many
- ← playlist_assignments (PlaylistAssignment) - One-to-many
- ← content_assignments (ContentAssignment) - One-to-many
- ← device_logs (DeviceLog) - One-to-many
- ← device_commands (DeviceCommand) - One-to-many
- ← device_speed_tests (DeviceSpeedTest) - One-to-many
- → organization (Organization)
- → creator (User)

---

#### 2. **device_logs** (Remote debugging)
```sql
Column Name      | Type           | Purpose
-----------------|----------------|-------------------------------------
id               | Integer (PK)   | Log entry ID
device_id        | Integer (FK)   | Which device
log_level        | String(20)     | 'log', 'warn', 'error', 'info'
message          | Text           | Log message content
source           | String(255)    | File/function where log originated
timestamp        | DateTime       | When log was recorded
```

**Use**: Devices send console logs to backend for remote debugging. Helps diagnose viewer issues without physical access.

---

#### 3. **device_commands** (Remote instruction queue)
```sql
Column Name      | Type           | Purpose
-----------------|----------------|-------------------------------------
id               | Integer (PK)   | Command ID
device_id        | Integer (FK)   | Target device
command_type     | String(20)     | 'reset', 'refresh', 'reload', 'run_speed_test'
reason           | String(100)    | Why command was issued
status           | String(20)     | 'pending', 'executed', 'expired'
created_at       | DateTime       | When command was queued
executed_at      | DateTime       | When device executed it
expires_at       | DateTime       | Auto-expire if not executed (7 days default)
```

**Command Types**:
- **reset**: Clear localStorage + IndexedDB + reload (device shows activation screen)
- **refresh**: Clear content cache only
- **reload**: Reload player only
- **run_speed_test**: Execute network speed test

**Flow**:
1. Admin queues command via API
2. Device polls `/devices/{id}/commands/pending` during heartbeat
3. Device executes command locally (e.g., localStorage.clear())
4. Device confirms via POST `/devices/{id}/commands/{cmd_id}/execute`
5. Command status → executed

---

#### 4. **device_speed_tests** (Network monitoring)
```sql
Column Name        | Type           | Purpose
-------------------|----------------|-------------------------------------
id                 | Integer (PK)   | Test record ID
device_id          | Integer (FK)   | Which device
download_speed     | Decimal(10,2)  | Mbps
upload_speed       | Decimal(10,2)  | Mbps
latency            | Integer        | Ping in milliseconds
jitter             | Integer        | Network jitter in ms
packet_loss        | Decimal(5,2)   | Loss percentage (0.00-100.00)
dns_server         | String(45)     | DNS server IP used
quality            | String(20)     | 'good', 'fair', 'poor'
tested_at          | DateTime       | Test timestamp
test_duration_ms   | Integer        | How long test took
server_endpoint    | String(255)    | Which speed test server
error_message      | Text           | Failure details if partial fail
```

**Quality Thresholds**:
- **Good**: Download ≥25 Mbps AND Upload ≥10 Mbps
- **Fair**: Download ≥10 Mbps AND Upload ≥5 Mbps
- **Poor**: Below fair

**Retention**: Keep last 100 tests per device (auto-delete older)

---

### Device-Relationship Junction Tables

#### 5. **device_tags** (Many-to-many: Device ↔ Tag)
```sql
device_id   | Integer (FK, PK)     | Device ID
tag_id      | Integer (FK, PK)     | Tag ID
assigned_at | DateTime             | When tag was assigned to device
```

**Purpose**: Devices can belong to multiple tags (e.g., device tagged as "Floor 1", "Meeting Room", "Premium")

**Cascade**: Delete device → delete device_tags records

---

#### 6. **playlist_assignments** (Playlist to Device/Tag)
```sql
id          | Integer (PK)         | Assignment ID
playlist_id | Integer (FK)         | Which playlist
device_id   | Integer (FK, nullable) | Direct device assignment
tag_id      | Integer (FK, nullable) | Tag-based assignment
created_at  | DateTime             | When assigned
```

**Constraint**: EITHER device_id OR tag_id, NOT both

**Example**:
- Playlist "Lobby TV Schedule" → assigned to device 5
- Playlist "Guest Room Content" → assigned to tag 12 (all guest rooms)

---

#### 7. **content_assignments** (Content to Device/Tag)
```sql
id          | Integer (PK)         | Assignment ID
content_id  | Integer (FK)         | Which content
device_id   | Integer (FK, nullable) | Direct device assignment
tag_id      | Integer (FK, nullable) | Tag-based assignment
priority    | Integer              | Display priority (higher wins)
display_order | Integer            | Order within same priority
is_active   | Boolean              | Soft delete flag
start_date  | DateTime (tz)        | Schedule start (optional)
end_date    | DateTime (tz)        | Schedule end (optional)
notes       | Text                 | Admin notes
created_at  | DateTime (tz)        | When assigned
updated_at  | DateTime (tz)        | Last modified
```

**Constraint**: EITHER device_id OR tag_id, NOT both

**Example Content Routing**:
- Direct: Video assigned to specific device → plays immediately
- Tag-based: Video assigned to "Premium Devices" tag → all devices with tag play it
- Soft delete: is_active=False → effectively removed but record preserved

---

## Device Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVICE LIFECYCLE FLOW                        │
└─────────────────────────────────────────────────────────────────┘

VIEWER (Device Client)          BACKEND API              ADMIN (Web UI)
─────────────────────────────────────────────────────────────────

1. REGISTRATION (Self-initiated)
──────────────────────────────

Viewer boots              POST /devices/monitor/register
─────────────────► (no auth required)
                        Create device record
                        Generate unique_code
                        Set code_expires_at = now + 10 min
                        status = "pending"
                        ◄─────────────────
Receive code            Display on screen
("123456")


2. ACTIVATION (Admin approval)
────────────────────────────

Admin sees pending         [Web UI shows pending device]
device in list
                          PUT /devices/{id}
                          status = "active"
                          ◄─────────────────
Device polls             GET /check-activation/{code}
every 5 sec             returns: { activated: true, device_token: "..." }
                          ◄─────────────────
Get JWT token
Store locally


3. HEARTBEAT (Continuous connection)
──────────────────────────────────────

Every 30 sec            POST /heartbeat
                        (auth: Bearer <device_token>)
                        Update: last_seen = now
                        Update: platform, resolution, network info
                        ◄─────────────────
Receive config          (response includes rotation, volume_enabled)
Check for commands      GET /commands/pending
                        ◄─────────────────
Execute commands        If "reset" received:
                          1. localStorage.clear()
                          2. indexedDB.delete()
                          3. location.reload()
                        POST /commands/{id}/execute
                        ◄─────────────────


4. CONTENT FETCHING
──────────────────

Device needs             GET /content/device/{id}
content list             (resolution algorithm determines content)
                          ◄─────────────────
Receive playlist        Display content in rotation


5. MONITORING
─────────────

Admin checks             GET /devices/{id}
device status           Shows: status, last_seen, tags, playlists
                        ◄─────────────────

Device offline          If last_seen > 5 minutes
detection               → status shows "OFFLINE" in UI


6. RELEASE
──────────

Admin triggers           POST /devices/{id}/release
release action
                        Queue RESET command
                        Update: status = "inactive"
                        Clear: unique_code, code_expires_at
                        ◄─────────────────
Device executes         Sees reset command
reset command           Clears storage
                        Reloads page
                        Generates NEW activation code
                        Re-registers as PENDING device


7. DELETE
─────────

Admin deletes           DELETE /devices/{id}
device
                        Queue RESET command (grace period)
                        CASCADE: delete tags, assignments, logs
                        Delete device record
                        ◄─────────────────
```

---

## API Endpoint Reference

### Device Registration & Activation

#### 1. POST `/devices/tv`
**Purpose**: Register TV device (WebOS)
**Auth**: None (or optional user)
**Request**:
```json
{
  "device_name": "Lobby TV 1",
  "ip_address": "192.168.1.100",
  "passphrase": "123456"
}
```
**Response**: { device, token, token_expires_at }

**Status**: TV devices activate immediately as "active"

---

#### 2. POST `/devices/monitor`
**Purpose**: Generate activation code for monitor
**Auth**: Authenticated user (admin)
**Request**: { device_name: "Reception Monitor" }
**Response**: { device_id, device_name, unique_code, code_expires_at, status: "pending" }

**Code expires in 10 minutes**

---

#### 3. POST `/devices/monitor/register`
**Purpose**: Self-registration (monitor generates its own code)
**Auth**: NONE - No authentication required
**Request**:
```json
{
  "organization_pin": "12345678",
  "activation_code": "123456",
  "device_name": "Monitor-123456",
  "platform": "Chrome",
  "model_name": "LG 24UP550"
}
```
**Response**: DeviceResponse

**Key Features**:
- No auth required (for browser clients)
- Organization validated via PIN
- Device determines its own device_type (tv/monitor) based on platform
- IP auto-detected from request

---

#### 4. POST `/devices/monitor/activate`
**Purpose**: Activate pending device using code
**Auth**: NONE
**Request**: { unique_code: "ABC123" }
**Response**: { device, token, token_expires_at }

**Status**: Sets device.status = "active" and returns JWT token

---

#### 5. GET `/devices/check-activation/{code}`
**Purpose**: Poll activation status (called by pending devices)
**Auth**: NONE
**Response**:
```json
{
  "activated": boolean,
  "expired": boolean,
  "device_id": int,
  "device_token": "jwt...",
  "message": string
}
```

**Used By**: Devices waiting for approval to detect when code becomes active

---

### Device Management

#### 6. GET `/devices`
**Purpose**: List all devices (with optional filters)
**Auth**: Optional user
**Query Params**:
- skip: Pagination offset
- limit: Page size (max 100)
- device_type: Filter by "tv" or "monitor"
- status_filter: Filter by status

**Response**: { total, page, page_size, data: [DeviceResponse] }

**Org Filter**: If authenticated user has organization_id, auto-filters to that org

---

#### 7. GET `/devices/{id}`
**Purpose**: Get device details
**Auth**: Optional user
**Response**: DeviceResponse with tags and playlists populated

---

#### 8. PUT `/devices/{id}`
**Purpose**: Update device settings
**Auth**: Optional user
**Request**:
```json
{
  "device_name": "Updated Name",
  "status": "active",
  "rotation": 90,
  "volume_enabled": false
}
```

**Updatable Fields**: device_name, status, rotation, volume_enabled

---

#### 9. DELETE `/devices/{id}`
**Purpose**: Delete device permanently
**Auth**: Required (authenticated user)
**Flow**:
1. Queue RESET command (grace period for device to process)
2. CASCADE delete: tags, assignments, logs, commands, speed tests
3. Return 204 No Content

---

#### 10. POST `/devices/{id}/release`
**Purpose**: Release device without deletion
**Auth**: Required
**Response**: Updated DeviceResponse

**Differences from DELETE**:
- Device record stays in database (for history)
- Status → "inactive"
- Code cleared (unique_code = NULL)
- Assignments preserved
- Device can re-register as NEW pending device after reset

---

#### 11. POST `/devices/{id}/replace-with-pending/{pending_id}`
**Purpose**: Replace inactive device's code with new pending device
**Auth**: Optional user
**Scenario**: Device loses connection → generates new code → admin uses this to transfer code to old device
**Response**: Updated target device with new code

---

### Device Heartbeat & Commands

#### 12. POST `/devices/heartbeat`
**Purpose**: Device heartbeat (keep-alive + status update)
**Auth**: REQUIRED (Bearer token from activation)
**Request**:
```json
{
  "device_id": 1,
  "ip_address": "192.168.1.50",
  "platform": "webOS",
  "screen_width": 1920,
  "screen_height": 1080,
  "connection_type": "wifi",
  "connection_speed": 45.5
}
```
**Response**: { device_id, status, last_seen, message, rotation, volume_enabled }

**Updates**:
- last_seen timestamp
- Platform info (if provided)
- Display settings (resolution, DPR, user agent, connection info)
- IP address (auto-detected or provided)

**Frequency**: Called every 30-60 seconds by device

---

#### 13. GET `/devices/{id}/commands/pending`
**Purpose**: Fetch pending commands (called by device during heartbeat)
**Auth**: NONE (or device auth)
**Response**:
```json
{
  "commands": [
    {
      "id": 1,
      "device_id": 1,
      "command_type": "reset",
      "reason": "released_by_admin",
      "status": "pending",
      "created_at": "2025-10-24T10:00:00",
      "expires_at": "2025-10-31T10:00:00"
    }
  ],
  "total": 1
}
```

**Filters**: Only non-expired pending commands

---

#### 14. POST `/devices/{id}/commands/{cmd_id}/execute`
**Purpose**: Mark command as executed
**Auth**: NONE (device calls after executing)
**Response**: { message, command_id, device_id, executed_at }

**Updates**: command.status = "executed", command.executed_at = now

---

#### 15. POST `/devices/{id}/commands`
**Purpose**: Queue generic command
**Auth**: REQUIRED (authenticated user)
**Request**: { command_type, reason }
**Response**: DeviceCommandResponse

**Supported command_type**: reset, refresh, reload, run_speed_test

---

#### 16. POST `/devices/{id}/commands/reset`
**Purpose**: Queue reset command specifically
**Auth**: REQUIRED
**Query Param**: reason (optional, defaults to "manual_reset")
**Response**: DeviceCommandResponse

---

### Content Assignment

#### 17. GET `/devices/{id}/content`
**Purpose**: Get direct content assignments (not via playlist/tag)
**Auth**: Optional user
**Response**: List[ContentAssignmentResponse]

**Only returns assignments where device_id={id} AND tag_id=NULL**

---

#### 18. POST `/devices/{id}/content`
**Purpose**: Assign content directly to device
**Auth**: Optional user
**Request**: { content_id, priority, display_order, is_active }
**Response**: ContentAssignmentResponse

**Validation**:
- Device must be active
- Content must exist
- Assignment must not already exist

---

#### 19. DELETE `/devices/{id}/content/{content_id}`
**Purpose**: Remove content assignment
**Auth**: Optional user
**Response**: 204 No Content

---

### Device Preview & Analysis

#### 20. GET `/devices/{id}/preview`
**Purpose**: Get content preview (what will play on this device)
**Auth**: Optional user
**Query Params**:
- preview_time: ISO 8601 datetime (defaults to now)
- include_inactive: Include inactive content sources

**Response**: DevicePreviewResponse

**Algorithm**: Determines content by priority:
1. Direct assignments (highest priority)
2. Tag-based assignments
3. Playlist-based content
Considers: scheduling, priority, is_active flags

---

### Device Authentication

#### 21. POST `/devices/refresh`
**Purpose**: Refresh device JWT token
**Auth**: NONE (but send current token)
**Request**: { token: "existing_jwt" }
**Response**: { token, token_expires_at }

**Use Case**: Device approaching token expiry refreshes token before expiration

---

## Device Authentication (JWT)

### Token Generation
```python
Token Payload:
{
  "device_id": 1,
  "device_type": "monitor",
  "mac_address": "unique_code_or_ip",
  "activated_at": "2025-10-24T10:00:00",
  "type": "device",  # Distinguish from user tokens
  "exp": <expiry_timestamp>,
  "iat": <issued_timestamp>,
  "iss": "signage-backend"
}

Expiry: 30 days from issuance
Algorithm: HS256
Secret: settings.SECRET_KEY
```

### Token Usage
```
Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Verification:
  1. Decode JWT
  2. Verify signature
  3. Check type == "device"
  4. Extract device_id
  5. Fetch device from DB
  6. Verify device.status == "active"
  7. Update device.last_seen
```

### Token Refresh Logic
```
When token expiry < 7 days remaining:
  payload["needs_refresh"] = True
Device should call POST /devices/refresh to get new token
Old token remains valid until natural expiry
```

### Backward Compatibility
- Old method: ?device_id=1 query parameter (deprecated, logs warning)
- New method: Authorization Bearer token (preferred)

---

## Device Status States

```
pending    → Device registered but not yet approved by admin
          → Code expires in 10 minutes
          → Cannot access content
          
active     → Device approved and fully operational
          → Can fetch content, receive commands, heartbeat
          → Shows as "online" if last_seen < 5 minutes
          → Shows as "offline" if last_seen > 5 minutes
          
inactive   → Device released by admin
          → Status set after release action
          → Cannot fetch content
          → Can still receive commands (e.g., reset)
          
maintenance → Device temporarily disabled by admin
          → Can see in UI but won't receive content
```

---

## Content Resolution Algorithm

When device requests content, backend applies this priority:

```
1. EXCLUSIVE MODE (if any exclusive playlist assigned)
   → Use ONLY playlist content, ignore other sources
   
2. INCLUSIVE MODE (default)
   → Merge from all sources by priority:
   
   Priority Order:
   ├─ Direct content assignments (device_id set)
   │  └─ Sorted by: priority DESC, display_order ASC
   │
   ├─ Tag-based assignments (device has tag_id)
   │  └─ Sorted by: tag_priority DESC, then content priority
   │
   └─ Playlist-based (playlist assigned to device/tag)
      └─ Sorted by: playlist priority DESC
      └─ Respects playlist scheduling
      └─ Respects content scheduling (start_date, end_date)
      
Additional Filters:
  • is_active = true (soft delete check)
  • Current timestamp within start_date..end_date (if set)
  • Device must be active (status = "active")
```

---

## Device Tags & Organization

### Tag Structure
```
Table: tags
├─ id (PK)
├─ tag_name: String (e.g., "Floor 1", "Premium Displays")
├─ description: Text
├─ color: Hex (for UI display)
├─ tag_priority: Integer (for content resolution)
├─ organization_id (FK) - Multi-tenancy
└─ created_at: DateTime
```

### Device-Tag Relationship
```
Table: device_tags
├─ device_id (FK, PK)
├─ tag_id (FK, PK)
└─ assigned_at: DateTime
```

**Example Usage**:
- All guest room TVs tagged with "Guest Rooms"
- Content assigned to "Guest Rooms" tag plays on all tagged devices
- Device can have multiple tags simultaneously

---

## Device Monitoring Features

### 1. Last Seen Tracking
- Updated every heartbeat
- Used to determine online/offline status
- Threshold: > 5 minutes = "offline"
- Shows in device list and analytics

### 2. Speed Testing
- Device polls for speed_test command
- Runs network speed test (Speedtest.net integration)
- Records: download, upload, latency, jitter, packet_loss, quality
- Quality classification: good, fair, poor
- Last 100 results kept per device (auto-cleanup)

### 3. Device Logs
- Device sends console logs to `/devices/{id}/logs`
- Levels: log, warn, error, info
- Helps debug viewer issues remotely
- No auth required (device sends with device_id)

### 4. Connection Info Tracking
- Platform: webOS, browser, Tizen, etc.
- Model: Device model name
- Firmware: OS version
- Screen resolution: Physical + viewport
- Device pixel ratio: For high-DPI displays
- Connection: wifi, ethernet, 4g, etc.
- Connection speed: Detected Mbps

---

## Multi-Tenancy & Organization Isolation

All device operations respect organization boundaries:

```
Device Model Fields:
├─ organization_id (FK) - REQUIRED
└─ created_by (FK) - User who registered device

Query Filtering:
├─ Authenticated user has organization_id
├─ List queries auto-filter to user's org
└─ Cross-org access returns 404 (not found)

Device Registration:
├─ TV (admin): User's org assigned to device
├─ Monitor (viewer): Organization determined by PIN
└─ Self-register: Must provide valid organization PIN
```

---

## Device Lifecycle Events

### Device Created (Pending)
- triggered by: POST /devices/monitor/register or POST /devices/monitor
- Status: pending
- Code expires: now + 10 minutes
- last_seen: NULL (never seen)
- Activity logged: device_creation

### Device Activated
- Triggered by: Device calls /check-activation or admin sets status=active
- Status: pending → active
- last_seen: Updated
- JWT token issued
- Activity logged: device_activation

### Device Heartbeat
- Triggered by: Device POST /heartbeat every 30-60 seconds
- Updates: last_seen, platform info, resolution, connection info
- Frequency: Continuous while active
- No activity log (too frequent)

### Device Released
- Triggered by: Admin POST /devices/{id}/release
- Status: active → inactive
- Released_at: Timestamp
- Code cleared: unique_code = NULL
- Assignments: Preserved for re-activation
- Commands queued: RESET command sent
- Activity logged: device_release

### Device Deleted
- Triggered by: Admin DELETE /devices/{id}
- Cascade deletes: tags, assignments, logs, commands, speed_tests
- Records deleted: NO RECOVERY possible
- Commands queued: RESET command before deletion
- Activity logged: device_deletion

---

## Security Features

### 1. JWT Device Authentication
- 30-day token expiration
- Token refresh when < 7 days remaining
- Signature verification using SECRET_KEY
- Device must be active to use token

### 2. Activation Code Security
- 6-digit alphanumeric code
- Excludes confusing chars (0, O, 1, I)
- 10-minute expiration
- Unique constraint per system
- Tied to organization via PIN

### 3. Organization Isolation
- All queries filtered by organization_id
- Device cannot access other org's content
- Cross-org attempts return 404

### 4. Command Expiration
- Commands auto-expire after 7 days
- Device cannot execute expired commands
- Prevents stale command execution

### 5. Status-Based Access Control
- Only "active" devices can fetch content
- Inactive devices cannot authenticate
- Pending devices cannot access API

---

## Integration Points

### With Content
```
Device + Content:
├─ Direct assignment: Device → Content
├─ Tag assignment: Device (has tags) → Content (assigned to tags)
└─ Playlist: Device/Tag → Playlist → PlaylistContent → Content
```

### With Playlists
```
Device + Playlist:
├─ Direct: Device → PlaylistAssignment → Playlist
├─ Tag-based: Device (has tags) → Playlist (assigned to tags)
└─ Resolution: Applies scheduling, priority, exclusive mode
```

### With Tags
```
Device + Tags:
├─ N-to-N relationship via device_tags table
├─ Tags used for content grouping
├─ Tags have priority (tag_priority) for content resolution
└─ Content can be assigned to tags instead of individual devices
```

### With Organizations
```
Device + Organization:
├─ organization_id FK (required)
├─ Multi-tenant isolation
├─ Device limited to org's content
└─ PIN-based device registration (self-register with org PIN)
```

### With Users
```
Device + Users:
├─ created_by FK (who registered device)
├─ Activity logs track user actions on device
└─ User's org determines accessible devices
```

---

## Performance Considerations

### Indexes
- device_type, status, last_seen (quick filtering)
- organization_id (multi-tenant queries)
- unique_code (activation lookup)
- device_uuid (permanent ID lookup)

### Eager Loading
- List endpoint uses joinedload(tags) and joinedload(playlist_assignments)
- Avoids N+1 query problem when populating nested data

### Pagination
- Default limit: 100 devices per page
- Skip/limit pattern for cursor pagination

### Cleanup
- Speed tests: Keep 100 most recent per device
- Commands: Auto-expire after 7 days
- Logs: Indefinite retention (consider cleanup policy)

---

## Known Limitations & Future Improvements

1. **Speed Test Integration**
   - Currently command queued but execution depends on viewer implementation
   - No automatic scheduling (manual trigger only)

2. **Device Logs**
   - No log retention policy defined
   - Could implement rolling window (keep 30 days)

3. **IP Address Changes**
   - Device IP can change (mobile, DHCP) but unique_code stays
   - Device UUID for permanent identification (not yet fully utilized)

4. **Concurrent Commands**
   - Device can have multiple pending commands
   - Execution order depends on device polling
   - No priority system for command execution

5. **Token Refresh**
   - Automatic refresh hint available but not enforced
   - Device must manually call refresh endpoint

---

## Summary Table

| Aspect | Details |
|--------|---------|
| **Device Types** | TV (WebOS/native), Monitor (browser) |
| **Registration** | Self-registration with PIN for org, or admin-generated |
| **Activation** | 6-digit code + admin approval (10-min code expiry) |
| **Authentication** | JWT tokens (30-day expiration) |
| **Heartbeat** | Every 30-60 seconds + status updates |
| **Commands** | reset, refresh, reload, run_speed_test (7-day auto-expire) |
| **Content Assignment** | Direct, tag-based, or playlist-based |
| **Monitoring** | last_seen, speed tests, network stats, remote logs |
| **Multi-Tenancy** | Organization-level isolation |
| **Relationships** | Tags, Playlists, Content, Logs, Commands, SpeedTests |
| **Status States** | pending, active, inactive, maintenance |
| **Cascade Delete** | Device deletion removes all related records |

