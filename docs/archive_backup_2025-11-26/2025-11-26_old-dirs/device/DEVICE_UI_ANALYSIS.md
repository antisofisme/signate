# Device Management UI Analysis - web-admin-old

## Overview
The device management system in web-admin-old provides a comprehensive interface for managing digital signage devices. It supports multiple device types (TV apps via WebOS/Tizen/Android TV, and browser-based monitors) with features for registration, activation, monitoring, and content assignment.

---

## 1. DEVICE UI SCREENS & VIEWS

### 1.1 Devices List Page (Devices.jsx)
**Route:** `/devices`
**Purpose:** Main hub for device management - displays all devices organized by status

#### Layout Structure
```
┌─ Sticky Header (PageHeader with search/sort/stats)
├─ Pending Approval Section (Yellow banner if devices pending)
│  └─ PendingDeviceCard list (auto-refresh every 5 seconds)
├─ Main Content Area (Scrollable)
│  ├─ Active Devices Table
│  │  ├─ Columns: ID, Device, Platform, IP, Code, Status, Last Seen, Actions
│  │  └─ Row Actions: Activate (if pending), Edit, View Logs, Delete
│  └─ Released Devices Table (Inactive section)
└─ Modals (opened from table actions)
```

#### Key Features
- **Real-time refresh:** 5-second auto-refresh via TanStack Query to show new pending devices
- **Three device categories:**
  - Pending (awaiting admin approval)
  - Active (registered & operational)
  - Inactive/Released (devices set to inactive status)
- **Search:** Query by device name, IP address, or activation code
- **Sort options:** Newest, Oldest, Name A-Z, Name Z-A
- **Status filters:** All, Pending, Active, Inactive, Browser, App
- **Statistics bar:** Clickable badges showing device counts by status
- **Empty state:** Shows helpful message when no devices registered

#### Data Displayed
| Column | Content | Type |
|--------|---------|------|
| ID | Sequential device ID | Number (monospaced) |
| Device | Name + icon (TV/Monitor) | String with icon |
| Platform | webOS, Tizen, Chrome, etc. | String |
| IP Address | Network IP | String (monospaced) |
| Code | 6-digit activation code | String (green, bold) |
| Status | pending/active/inactive | Badge |
| Last Seen | Timestamp of heartbeat | Date string |
| Actions | 4 buttons | Icons |

---

### 1.2 Device Detail Modal (DeviceDetailModal.jsx)
**Triggered:** Click on device table row
**Purpose:** Comprehensive device information, management, and monitoring dashboard

#### Layout Structure
```
┌─ Fixed Header (gradient bg with device name, online/offline indicator)
├─ Quick Actions Bar (5 buttons)
│  ├─ Edit Device
│  ├─ View Logs
│  ├─ Speed History
│  ├─ Preview Content
│  └─ Delete Device
├─ Scrollable Content
│  ├─ Tags Section
│  │  ├─ Add/Remove tags
│  │  └─ Tag selector UI
│  ├─ Playlists Section
│  │  ├─ Add/Remove playlists
│  │  └─ Playlist selector with status
│  ├─ Content Section
│  │  ├─ Direct Assignments (add/remove)
│  │  └─ Inherited from Tags (read-only)
│  ├─ Device Information Block
│  │  ├─ ID, Platform, IP, Code, Status
│  │  ├─ Last Seen, Screen Resolution
│  ├─ Network Speed History
│  │  ├─ Latest Speed Stats (Download/Upload/Quality)
│  │  ├─ Line chart (10 test history)
│  │  └─ Run Speed Test button
│  │
└─ Footer (Close button)
```

#### Real-time Features
- **Online/Offline Status:** Green circle (online) or Red circle (offline)
  - Online = last_seen within 60 seconds
  - Based on heartbeat mechanism (device sends every 30s)
- **Auto-refreshing data:**
  - Speed test history auto-refreshes every 60 seconds
  - Device data updates on tag/playlist assignment
- **Live logging:** Speed test results appear 15-20 seconds after triggering

#### Content Management Integration
- **Three-level content assignment:**
  1. Direct assignments (priority-based)
  2. Playlist assignments (with priority)
  3. Tag-based inheritance (read-only display)
- **Content selector:** Modal overlay showing available content with thumbnails
- **Tag & Playlist management:** Quick add/remove via selectors

#### Speed Testing
- **Manual speed test:** Queues command to device
- **Results display:**
  - Download/Upload speeds in Mbps
  - Quality badge (Good/Fair/Poor)
  - 10-test history chart with timeline
  - Metrics: Latency, Jitter, Packet Loss
  - DNS server info
- **Quality thresholds:**
  - Good: ≥25 Mbps download, ≥10 Mbps upload
  - Fair: ≥10 Mbps download, ≥5 Mbps upload
  - Poor: Below fair thresholds

---

### 1.3 Device Edit Modal (DeviceEditModal.jsx)
**Triggered:** "Edit Device" button or row Edit icon
**Purpose:** Modify device settings and display configuration

#### Sections
1. **Device Information (Editable)**
   - Device ID (read-only)
   - Device Name (editable text input)
   - Device Type (read-only)
   - Status dropdown (Pending, Active, Inactive)
   - IP Address (read-only)
   - Last Seen (read-only)

2. **Replace with Pending Device (Browser devices only)**
   - Purpose: Reconnect inactive devices with new viewers
   - Shows list of pending browser devices
   - Allows selection and replacement
   - Merges pending device data and deletes pending record
   - Only shows for browser/monitor devices (not TV platforms)

3. **Display Settings (Editable)**
   - Screen Rotation: 0°, 90°, 180°, 270°
   - Video Audio: Toggle On/Off
   - Applies to viewer app immediately

4. **Display Information (Read-only)**
   - Screen Resolution (width x height)
   - Viewport Size
   - Device Pixel Ratio
   - User Agent
   - Connection Type & Speed (e.g., "WiFi (54Mbps)")

#### Actions
- **Save Changes:** Updates device settings in backend
- **Release Device:** 
  - Confirmation dialog with device details
  - Queues reset command to device
  - Changes status to pending
  - Generates new activation code
  - Keeps content assignments
- **Footer layout:** Release button (left), Cancel/Save buttons (right)

---

### 1.4 Device Logs Modal (DeviceLogsModal.jsx)
**Triggered:** "View Logs" button or row FileText icon
**Purpose:** Real-time log streaming and historical log viewing

#### Layout Structure
```
┌─ Fixed Header
│  ├─ Title: "Device Logs"
│  ├─ Device info (name, ID)
│  └─ Connection status indicator (green/red dot)
├─ Fixed Filter Bar
│  ├─ Level filters: ALL, LOG, INFO, WARN, ERROR
│  └─ Count badges for each level
├─ Scrollable Log View
│  ├─ Terminal-style background (dark gray-900)
│  ├─ Log entries with:
│  │  ├─ Timestamp (HH:MM:SS)
│  │  ├─ Level badge (colored)
│  │  ├─ Source tag (purple)
│  │  └─ Message (monospace)
│  └─ Auto-scroll to newest
└─ Fixed Footer
   ├─ Log counts (Total, Filtered)
   ├─ Real-time status note
   └─ Action buttons: Export, Clear
```

#### Features
- **WebSocket real-time streaming:**
  - Connects to `/api/ws/logs/{device_id}`
  - Displays "Connected (real-time)" when active
  - Falls back to cached logs if connection fails
  - Status messages: Connected, Loaded, Failed, Disconnected

- **Log filtering:**
  - Level-based (all, log, info, warn, error)
  - Shows counts per level
  - Filters live as you select

- **Log display:**
  - Timestamp: Localized to user's timezone (id-ID format by default)
  - Color coding: red (error), yellow (warn), blue (info), gray (debug)
  - Monospace font for readability
  - Hover effects for visual feedback
  - Auto-scroll to bottom on new logs

- **Actions:**
  - **Export:** Downloads logs as .txt file (formatted with timestamps)
  - **Clear:** Deletes all device logs after confirmation
  - **Search:** Filter by level (not full-text search)

---

### 1.5 Pending Device Card (PendingDeviceCard.jsx)
**Location:** Displayed in "Pending Approval" section on Devices page
**Purpose:** Quick approval interface for new registrations

#### Layout
```
┌─ Yellow bordered card
├─ Left: Device icon (blue circle for TV, green for Monitor)
├─ Center: Device info
│  ├─ Device name (bold)
│  ├─ IP address (monospace)
│  ├─ Platform badge (webOS = purple, others = gray)
│  ├─ Activation code (yellow, large)
│  └─ Last seen timestamp
└─ Right: Green "Approve" button
```

#### Information Displayed
- Device icon (based on platform detection)
- Device name
- IP address
- Platform (webOS, Chrome, Safari, etc.)
- Unique 6-digit activation code (highlighted in yellow)
- Last seen timestamp ("Waiting for connection..." if never seen)

#### Interaction
- Click "Approve" button to activate device
- Confirmation shows device name and code
- Updates device status to "active"

---

### 1.6 Speed Test History Modal (SpeedHistoryModal.jsx)
**Triggered:** "Speed History" button in Device Detail Modal
**Purpose:** Detailed speed test history with metrics

#### Layout
```
┌─ Header: "Speed Test History - {device_name}"
├─ Info: Showing X of Y tests
├─ Table:
│  ├─ Columns:
│  │  ├─ Tested At (date & time)
│  │  ├─ Download (Mbps, green)
│  │  ├─ Upload (Mbps, blue)
│  │  ├─ Quality (Good/Fair/Poor badge)
│  │  ├─ Metrics (Latency, Jitter, Loss)
│  │  └─ DNS Server
│  └─ Rows: 20 most recent tests
├─ Quality Legend Box
│  ├─ Good: ≥25 Mbps DL, ≥10 Mbps UL
│  ├─ Fair: ≥10 Mbps DL, ≥5 Mbps UL
│  └─ Poor: Below fair thresholds
└─ Auto-refresh: Every 10 seconds
```

#### Data
- Displays last 20 speed tests
- Ordered by newest first
- Shows metrics: Download, Upload, Quality, Latency, Jitter, Packet Loss
- DNS server information

---

### 1.7 Content Assignment Modal (AssignContentModal.jsx)
**Triggered:** Click on device row (opens, not explicitly shown in row click handler but structure indicates availability)
**Purpose:** Two-column content assignment interface

#### Layout
```
┌─ Full-screen modal
├─ Fixed Header: "Assign Content: {device_name}"
├─ Two-column grid:
│  ├─ LEFT: Available Content
│  │  ├─ Title: "Available Content (X items)"
│  │  └─ Scrollable list
│  │     └─ Content cards:
│  │        ├─ Thumbnail (16x16 with video preview)
│  │        ├─ Title, Type badge, Duration
│  │        ├─ Segment info if applicable
│  │        └─ Arrow indicator (blue on hover)
│  │
│  └─ RIGHT: Assigned Content
│     ├─ Title: "Assigned Content (X items)"
│     └─ Scrollable list
│        └─ Content cards:
│           ├─ Arrow indicator (red on hover)
│           ├─ Thumbnail
│           ├─ Title, Type badge, Duration
│           └─ Segment info if applicable
│
└─ No explicit footer (full-screen layout)
```

#### Interaction
- **Assign:** Click content on left side
- **Unassign:** Click content on right side
- **Visual feedback:** Hover states with color changes
- **Bidirectional:** Arrow indicators show direction of assignment

#### Content Display
- Thumbnail preview (16x16 pixels)
- Title (truncated if long)
- Type badge (IMAGE, VIDEO)
- Duration in seconds
- Video segment info if set (start_time - end_time)

---

### 1.8 Device Preview Page (DevicePreview.jsx)
**Route:** `/devices/{id}/preview`
**Purpose:** Full-screen preview of device content playback sequence

#### Layout
```
┌─ Fixed Header
│  ├─ Back button
│  ├─ Title: "🎬 Preview: {device_name}"
│  └─ Info: "X content items • Total duration • Y loops/hour"
├─ Warning section (if conflicts/issues)
│  └─ Alert list with icons
├─ Main Preview Area
│  ├─ Player (PreviewPlayer component)
│  │  └─ Shows current content (image or video)
│  └─ Playback Controls
│     ├─ Previous button
│     ├─ Play/Pause toggle
│     ├─ Next button
│     ├─ Restart button
│     └─ Current/Total counter
│
├─ Sequence List (SequenceList component)
│  ├─ Scrollable list of all content items
│  ├─ Current item highlighted
│  ├─ Source badges (Direct, Playlist, Tag)
│  └─ Click to jump to item
│
└─ States:
   ├─ Loading: Spinner with "Loading preview..."
   ├─ Error: Alert with error message
   └─ Empty: "No Content Assigned" message
```

#### Features
- **Real-time playback preview**
  - Auto-advance based on content duration
  - Manual controls: Play/Pause, Next/Prev, Restart
  - Jump to specific content in sequence
  - Loop indication (content repeats at end)

- **Content sequence info**
  - Total duration calculation
  - Loops per hour estimation
  - Warnings for conflicts or missing content

- **Responsive player**
  - Image or video playback
  - Auto-scales to screen size
  - Dark background for display simulation

---

## 2. USER WORKFLOWS

### 2.1 Device Activation Flow (TV Device - WebOS/Tizen)
```
1. Admin → Devices page
2. Sees "Pending Approval" section with new TV
3. Reviews device info: Name, IP, Code, Platform
4. Clicks "Approve" button
5. Confirmation: "Activate {device_name}?"
6. Backend updates status to 'active'
7. Device moves to "Active Devices" table
8. TV viewer receives update and recognizes as active
```

### 2.2 Device Activation Flow (Browser Device - Monitor)
```
1. User opens viewer URL on monitor/browser
2. System generates 6-digit activation code
3. Code displays on viewer
4. Admin sees device in "Pending Approval" section
5. Admin clicks "Approve"
6. Backend marks device as 'active'
7. Viewer receives confirmation and starts displaying content
8. Device moves to "Active Devices" table
```

### 2.3 Content Assignment (Single Device)
```
1. Admin → Devices page
2. Click device row → Device Detail Modal opens
3. Scroll to "Content" section
4. Click "+ Add Content" button
5. Content selector appears (scrollable list)
6. Click content to assign
7. Content appears in "Direct Assignments" list
8. Can add multiple content items
9. Content plays in order on device
10. Close modal to return to device list
```

### 2.4 Tag Assignment (Bulk Content)
```
1. Admin → Devices page
2. Click device row → Device Detail Modal opens
3. Scroll to "Tags" section
4. Click "+ Add Tag" button
5. Tag selector shows available tags (color-coded)
6. Click tag to assign
7. Tag badge appears with remove button (X)
8. Scroll to "Inherited from Tags" subsection
9. View all content from assigned tags (preview, max 3 items shown)
10. Tag content plays on device automatically
```

### 2.5 Playlist Assignment
```
1. Admin → Devices page
2. Click device row → Device Detail Modal opens
3. Scroll to "Playlists" section
4. Click "+ Add Playlist" button
5. Playlist selector shows available playlists
6. Click playlist to assign
7. Playlist info appears with:
   - Playlist name
   - Priority indicator
   - Active status
   - Description (if available)
8. Can assign multiple playlists
9. All playlist content plays on device
```

### 2.6 Device Settings Modification
```
1. Admin → Devices page
2. Click Edit button (pencil icon) → Edit Modal opens
3. Editable fields:
   - Device Name (text input)
   - Status (dropdown: pending, active, inactive)
4. Display Settings (for viewer):
   - Screen Rotation (0°, 90°, 180°, 270°)
   - Video Audio (On/Off toggle)
5. View read-only info:
   - Device ID, Type, IP, Last Seen
   - Screen Resolution, Viewport, DPI
   - User Agent, Connection info
6. Optional: Replace with Pending Device (browser only)
   - Select pending device from dropdown
   - Merges viewer data
7. Click "Save Changes"
8. Settings update and modal closes
```

### 2.7 Device Release/Reset Flow
```
1. Admin → Devices page
2. Click Edit button → Edit Modal opens
3. Look for "Release Device" button (only shows if status = active)
4. Click "Release Device"
5. Confirmation dialog shows:
   - Device name & code
   - Actions that will happen:
     * Reset command queued
     * Status → pending
     * New activation code generated
     * Content assignments kept
6. Confirm → Device resets
7. Device moves to "Released Devices" section
8. Can be reactivated with new code or re-approved
```

### 2.8 Device Monitoring/Inspection
```
1. Admin → Devices page
2. Click device row → Detail Modal opens
3. View online status (green/red circle)
4. Click "View Logs" button → Logs Modal opens
5. See real-time log stream (if WebSocket available)
6. Filter by level (All, Log, Info, Warn, Error)
7. Export logs as .txt file
8. Clear all logs after confirmation
9. Close modal
10. Back in Detail modal, check "Speed History"
11. View speed test history table (20 tests)
12. See Download/Upload speeds, Quality badge
13. Click "Run Speed Test" (if device online)
14. Test queued, results appear in 15-20 seconds
```

### 2.9 Device Preview (Pre-assignment check)
```
1. Admin → Devices page
2. Click device row → Detail Modal opens
3. Click "Preview" button (opens new window)
4. Full-screen preview page loads
5. View content sequence:
   - Current playing content (image or video)
   - Playback controls (Play/Pause, Next/Prev, Restart)
   - Sequence list on side (click to jump)
6. Review:
   - Total duration
   - Loops per hour
   - Content order
   - Any warnings/conflicts
7. Close preview and return to devices
```

### 2.10 Device Deletion
```
1. Admin → Devices page
2. Click Delete button (trash icon) on row
   OR
   Open Detail Modal → Click "Delete" button
3. Confirmation: "Delete this device?"
4. Confirm deletion
5. Device removed from system
6. Associated assignments cleared
7. Toast notification: "Device deleted successfully"
8. Page refreshes to show updated list
```

### 2.11 Replace Inactive Device with New Viewer
```
1. Device loses connection → status becomes 'inactive'
2. Admin → Devices page
3. Click Edit button → Edit Modal opens
4. "Reconnect with Pending Viewer" section shows
5. Dropdown lists available pending browser devices
6. Select pending device to replace with
7. Orange warning box explains action:
   "Will reconnect and reactivate inactive device"
   "Pending device will be merged and deleted"
8. Click "Save Changes"
9. Inactive device now active with new code
10. Pending device record deleted
```

---

## 3. REAL-TIME FEATURES

### 3.1 Device Status Updates
- **Auto-refresh interval:** 5 seconds (Devices list page)
- **Update trigger:** New devices register via activation code
- **Implementation:** TanStack Query `refetchInterval: 5000`
- **Display:** Pending devices appear immediately in yellow section
- **Heartbeat mechanism:**
  - Device sends heartbeat every 30 seconds
  - `last_seen` timestamp updated on server
  - Admin sees current status in table

### 3.2 Online/Offline Status
- **Online indicator:** Green circle (Device Detail Modal header)
- **Offline indicator:** Red circle (Device Detail Modal header)
- **Calculation:** `now - last_seen < 60 seconds = online`
- **Timeout:** 60 seconds (2x heartbeat interval of 30s)
- **Update:** Automatic when Device Detail Modal opens/reloads

### 3.3 Speed Test Results
- **Manual trigger:** Click "Run Speed Test" button in Detail Modal
- **Backend queuing:** Command sent to device immediately
- **Result timing:** 15-20 seconds for results to appear
- **Auto-refresh:** Speed test history refreshes every 60 seconds
- **Display:** Line chart with last 10 tests, stats cards

### 3.4 Device Logs (WebSocket Streaming)
- **Connection:** WebSocket to `/api/ws/logs/{device_id}`
- **Initial load:** Fetches last logs via REST API
- **Real-time:** New logs stream as they occur
- **Display:** Auto-scrolls to bottom, shows timestamp & level
- **Status indicators:** "Connected (real-time)", "Loaded", "Failed"
- **Fallback:** Shows cached logs if WebSocket unavailable

### 3.5 Content Synchronization
- **Assignment propagation:** Immediate update to device
- **Multi-level:** Direct, Playlist, Tag assignments all sync
- **Device command:** New assignment triggers content download
- **Playback update:** Device updates playlist within seconds
- **Cache invalidation:** TanStack Query invalidates on assign/unassign

### 3.6 Tag Content Updates
- **Lazy loading:** Tag content fetched only when tags assigned
- **Refetch trigger:** useEffect watches tag ID changes
- **Display:** Shows up to 3 items, "+N more" if additional
- **Read-only:** Tag content cannot be managed per-device

---

## 4. FORMS & VALIDATION

### 4.1 Device Edit Form
```
Field: device_name
- Type: Text input
- Validation: Required, string
- Max length: Typically 255 chars
- Character set: Alphanumeric + spaces, special chars

Field: status
- Type: Select dropdown
- Options: pending, active, inactive
- Validation: One of three values
- Default: Current device status

Field: rotation
- Type: Select dropdown
- Options: 0, 90, 180, 270
- Unit: Degrees
- Default: 0 (normal)
- Display: "0° (Normal)", "90° (Clockwise)", etc.

Field: volume_enabled
- Type: Toggle buttons (On/Off)
- Values: true, false
- Display: "🔊 On" or "🔇 Off"
- Default: true
```

### 4.2 TV Registration Form (TVRegisterModal)
```
Field: device_name
- Type: Text input
- Placeholder: "e.g., TV - Living Room"
- Required: Yes
- Validation: Non-empty string

Field: ip_address
- Type: Text input
- Placeholder: "192.168.1.100"
- Required: Yes
- Validation: Valid IPv4 format (x.x.x.x)
- Error message: "Invalid IPv4 address format (e.g., 192.168.1.100)"
- Error trigger: On submit if invalid

Field: passphrase
- Type: Text input
- Placeholder: "Enter device passphrase"
- Required: Yes
- Validation: Non-empty string
- Purpose: Device authentication

Validation Flow:
1. User enters data
2. Click "Register TV"
3. IP validation runs (custom isValidIPv4 check)
4. If invalid, show error message above field
5. If valid, submit form
6. Toast notification on success/error
```

### 4.3 Content Assignment
- **No explicit form:** Click-based assignment
- **Validation:** Prevents duplicate assignments (UI filters them)
- **Mutation error handling:** Shows toast on assignment failure

### 4.4 Tag/Playlist Assignment
- **Selection UI:** Dropdown or list selector
- **Validation:** Prevents duplicate assignments (shows only unassigned)
- **Error handling:** Toast notifications on failure

---

## 5. INTEGRATION WITH OTHER UI FEATURES

### 5.1 Device-Content Integration
```
Assignment paths:
1. Device Detail Modal → Content section → Add Content
2. Content page → Assign to Device
3. Playlist page → Assign to Devices
4. Tag page → Assign to Devices

Display shows:
- Direct assignments (priority-based order)
- Inherited from tags (read-only)
- Inherited from playlists (read-only)
- Three-level hierarchy visualization
```

### 5.2 Device-Playlist Integration
```
Features:
- Add/remove playlists in Device Detail
- Show playlist status (Active/Inactive)
- Display priority level
- Show description
- Multiple playlist support (priority-based playback)
```

### 5.3 Device-Tag Integration
```
Features:
- Add/remove tags (color-coded)
- Auto-expand tag content preview
- Show content count per tag
- Display first 3 items, "+N more"
- Read-only inherited content display
```

### 5.4 Device-Preview Integration
```
Features:
- Launch preview from Device Detail
- Shows full sequence (direct + tags + playlists)
- Display order and duration
- Warning/conflict indicators
- Jump to specific content
```

### 5.5 Dashboard Integration
```
Features:
- Device stats widgets (All, Pending, Active, Inactive, Browser, App)
- Click stats to filter device list
- Real-time counts update with 5-sec refresh
- Color-coded badges (blue, yellow, green, gray, purple)
```

---

## 6. ERROR HANDLING & USER FEEDBACK

### 6.1 Toast Notifications
```
Success cases:
- "Device activated successfully!"
- "Device updated successfully!"
- "Tag assigned!"
- "Device deleted successfully!"
- "Speed test command queued successfully..."
- "Logs cleared successfully"

Error cases:
- "Failed to activate device"
- "Failed to update device"
- "Failed to assign tag"
- "Failed to delete device"
- "Session expired. Please login again." (401)
- "You do not have permission..." (403)
- Custom error detail from backend

Display:
- Position: bottom-right
- Duration: 3-4 seconds (success), 4-5 seconds (error)
- Color: green (success), red (error)
```

### 6.2 Confirmation Dialogs
```
Used for destructive actions:
- Device deletion: "Delete this device?"
- Device release: Multi-line confirmation showing device name, code, effects
- Log clearing: "Clear all logs for this device?"
- Custom messages with device details
- Blocks action if user cancels
```

### 6.3 Validation Feedback
```
IP validation (TV Register):
- Field error: Red border
- Error message: Below field
- Clears on user input

Status/form errors:
- Toast notification
- User can retry
- Specific error details shown
```

### 6.4 Empty States
```
No devices:
- Icon: Monitor icon (lucide)
- Title: "No Devices Yet"
- Message: "Devices will appear here once they register..."
- Action: Link to viewer app

No speed tests:
- Icon: Activity icon
- Message: "No speed test data available"
- Info: "Viewer will perform speed test every 30 minutes"

No logs:
- Message: "Waiting for logs..."

No content assigned:
- Message: "No content assigned"
- Instructions: "Click content from left to assign"
```

---

## 7. PERFORMANCE & OPTIMIZATION

### 7.1 Query Optimization
```
Devices list:
- refetchInterval: 5000ms (5 seconds)
- limit: 2000 (load all devices)
- Cached by TanStack Query

Device details:
- Fetches on modal open
- Auto-invalidated on mutations

Speed test history:
- Auto-refresh: 60 seconds
- Limit: Last 10 for chart, 20 for table
- No polling if modal closed

Logs:
- Initial fetch: Last N logs
- WebSocket for real-time
- No polling (event-driven)
```

### 7.2 Component Memoization
```
Memoized components:
- DeviceTableRow (memo)
- PendingDeviceCard (memo)

Purpose:
- Prevent unnecessary re-renders in large lists
- Improve performance with 100+ devices

State management:
- TanStack Query for server state
- Zustand for auth state
- Local useState for UI state
```

### 7.3 Modal Optimization
```
Features:
- Scrollable content area (flex-1 overflow-y-auto)
- Fixed header/footer (don't scroll)
- Lazy loading where applicable
- Close clears selected device from state
```

---

## 8. ACCESSIBILITY & RESPONSIVE DESIGN

### 8.1 Responsive Layout
```
Mobile (sm):
- Sticky header with padding
- Vertical layout for forms
- Single column content
- Hamburger menu (if applicable)

Tablet (md/lg):
- Two-column layouts adapt
- Table columns may wrap
- Modals full-height

Desktop (xl):
- Full layout with sidebar
- Multi-column tables
- Side panels for details
```

### 8.2 Keyboard Navigation
```
Supported:
- Tab navigation through buttons
- Enter to submit forms
- Escape to close modals (via Modal component)
- Ctrl+Click to open preview in new tab

Not explicitly implemented:
- Arrow keys for list navigation
- Vim bindings
- Custom shortcuts
```

### 8.3 Dark Mode Support
```
Classes used:
- dark:bg-gray-800 (dark backgrounds)
- dark:text-gray-100 (dark text)
- dark:border-gray-700 (dark borders)

Full support:
- All modals
- Tables
- Forms
- Badges and indicators

Theme toggle:
- Controlled by app-level ThemeContext
```

---

## 9. DATA STRUCTURE EXAMPLES

### 9.1 Device Object
```json
{
  "id": 1,
  "device_name": "TV - Living Room",
  "device_type": "tv",
  "status": "active",
  "ip_address": "192.168.1.100",
  "pairing_code": null,
  "unique_code": "123456",
  "platform": "webOS",
  "last_seen": "2024-01-15T10:30:00",
  "created_at": "2024-01-10T08:00:00",
  "updated_at": "2024-01-15T10:30:00",
  "screen_width": 1920,
  "screen_height": 1080,
  "viewport_width": 1920,
  "viewport_height": 1080,
  "device_pixel_ratio": 1.0,
  "user_agent": "Mozilla/5.0...",
  "connection_type": "WiFi",
  "connection_speed": 54,
  "rotation": 0,
  "volume_enabled": true,
  "tags": [
    { "id": 1, "tag_name": "Lobby", "color": "#FF5733" }
  ],
  "playlists": [
    { "id": 1, "name": "Main Playlist", "priority": 0 }
  ]
}
```

### 9.2 DeviceLog Object
```json
{
  "id": 1,
  "device_id": 1,
  "log_level": "info",
  "message": "Device connected",
  "timestamp": "2024-01-15T10:30:00Z",
  "source": "viewer",
  "metadata": {}
}
```

### 9.3 SpeedTestResult Object
```json
{
  "id": 1,
  "device_id": 1,
  "download_speed": 45.67,
  "upload_speed": 12.34,
  "latency": 25,
  "jitter": 3,
  "packet_loss": 0.5,
  "quality": "good",
  "tested_at": "2024-01-15T10:30:00Z",
  "dns_server": "8.8.8.8",
  "server_location": "Jakarta"
}
```

---

## 10. KEY UI PATTERNS

### 10.1 Card-based Layout
```
Used for:
- Pending device cards (yellow bordered)
- Assigned playlist/content display
- Tag display (colored badges)
- Speed stats (green/blue/gray boxes)

Pattern:
- Visual icon on left
- Text info in center
- Action on right (button/remove)
- Hover effects for interactivity
```

### 10.2 Two-column Layout
```
Used for:
- Content assignment modal (Available | Assigned)
- Speed history modal (Metrics | Charts)

Pattern:
- Left: Source items (clickable)
- Right: Destination items (clickable to remove)
- Visual cues (arrows, color changes)
- Smooth transitions
```

### 10.3 Sticky Header Pattern
```
Used for:
- Devices page header (search, sort, stats)
- Device modals (header with gradient)
- Logs modal (filter bar)

Benefits:
- Always visible controls
- Improved UX on scroll
- Clear context
```

### 10.4 Modal Overlay Pattern
```
Structure:
- Backdrop overlay (dark, clickable to close)
- Modal container (centered or full)
- Header (fixed, gradient)
- Content (scrollable)
- Footer (fixed, sticky buttons)

Sizes:
- lg: 512px
- 2xl: 672px
- 4xl: 896px
- full: 100% screen
```

---

## 11. SUMMARY TABLE

| Screen | Purpose | Primary Actions | Real-time | Modals |
|--------|---------|-----------------|-----------|--------|
| Devices List | Device overview | Search, Sort, Filter, Approve | 5s auto-refresh | 5 modals |
| Device Detail | Comprehensive mgmt | Assign content/tags/playlists | Online status, Speed test | Speed history |
| Device Edit | Settings management | Update settings, Release device | N/A | Replace pending |
| Device Logs | Log monitoring | Filter, Export, Clear | WebSocket stream | - |
| Pending Card | Quick approval | Approve device | - | - |
| Speed History | Speed analytics | View metrics | 10s auto-refresh | - |
| Content Assign | Content management | Assign/unassign content | Immediate | - |
| Device Preview | Playback verification | Play/Pause, Navigate | - | - |

---

## 12. RECOMMENDED PATTERNS FOR NEW IMPLEMENTATION

Based on this analysis, the new cms-vite/backend-python implementation should maintain:

1. **Three-tier device categorization** (Pending, Active, Inactive)
2. **Rich device detail modal** with multiple management sections
3. **Real-time status indicators** with 30-second heartbeat
4. **WebSocket for logs** and event streaming
5. **Content assignment flexibility** (direct, playlist, tag-based)
6. **Speed test integration** for network monitoring
7. **Device preview** before content goes live
8. **Responsive modals** with fixed header/footer
9. **Toast notifications** for all operations
10. **Confirmation dialogs** for destructive actions

