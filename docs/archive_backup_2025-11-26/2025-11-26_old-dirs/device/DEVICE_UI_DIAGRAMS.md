# Device Management UI - Visual Diagrams

## 1. User Journey Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DEVICE MANAGEMENT WORKFLOWS                           │
└─────────────────────────────────────────────────────────────────────────────┘

DEVICE ACTIVATION
─────────────────
   Viewer App              Web Admin                 Backend
   (Device)            (Admin Dashboard)         (Server)
        │                     │                       │
        ├─ Register ─────────→│                       │
        │  (with code)        │                       │
        │                     ├─ Create device ─────→│
        │                     │  (status: pending)    │
        │                     │←─ Device record ──────┤
        │                     │                       │
        │                 [Pending Section Shows]    │
        │                     │                       │
        │                     ├─ Approve ────────────→│
        │                     │                       ├─ Update status
        │                     │                       │  to "active"
        │                     │←─ Status updated ────┤
        │←─ Notification ──────────────────────────────┤
        │  (now active)       │                       │


CONTENT ASSIGNMENT
──────────────────
   Device            Web Admin               Backend
      │                 │                       │
      │ (watching)      │                       │
      │             Device Detail Modal       │
      │             │ Click: + Add Content    │
      │             ├─────────────────────→  │
      │             │ Assign content X       │
      │             ├─────────────────────→  │
      │             │                    [Save to DB]
      │             │←──────── ACK ──────────┤
      │←──────── Command ─────────────────────┤
      │ (Content X)     │                     │
      ├─ Download ──────────────────────→    │
      │ Content         │                     │
      │                 │                     │
      └─ Play content ──────────────────────→ (Monitor)


DEVICE MONITORING
─────────────────
   Web Admin               Backend              Device
      │                      │                    │
      │ Open Device Detail   │                    │
      │ Modal               │                    │
      │ [Show: Online/Offline]
      │ (based on last_seen) │                    │
      │                      │ [Heartbeat: 30s]   │
      │                      │←──────────────────┤
      │ [Update: last_seen]  │                    │
      │                      │                    │
      │ Click: Run Speed Test│                    │
      ├─────────────────────→│                    │
      │                      ├─ Queue command ───→│
      │                      │                    ├─ Run test
      │                      │←──── Results ──────┤
      │                      │ (15-20 seconds)    │
      │ [Show speed chart]   │                    │
      │ (60s auto-refresh)   │                    │


LOGGING & DEBUGGING
───────────────────
   Web Admin          Backend              Device
      │                  │                   │
      │ Open Logs Modal  │                   │
      │                  │ Load initial logs │
      ├─────────────────→│←──────────────────┤
      │                  │←─ Log history ─────┤
      │                  │                   │
      │ [WebSocket Connect]                  │
      │ /api/ws/logs/{id}│                   │
      ├─────────────────→│                   │
      │                  │←─ [Connected] ────┤
      │                  │                   │
      │                  │←─ Log stream ──────┤
      │ [Live logs appear]                   │
      │                  │                   │
      │ Click: Export    │                   │
      │ [Download .txt]  │                   │
      │                  │                   │
      │ Click: Clear     │                   │
      ├─────────────────→│                   │
      │                  ├─ Delete logs ─────→│
      │                  │                   │


DEVICE RELEASE/RESET
────────────────────
   Device            Web Admin                Backend
      │                 │                        │
      │ (Active)        │                        │
      │             Edit Device Modal        │
      │             Click: Release Device    │
      │             [Confirmation dialog]    │
      │             │ Confirm               │
      │             ├────────────────────→  │
      │             │                    [Queue reset cmd]
      │             │                    [New code gen]
      │             │←────── Confirm ─────┤
      │←──────── Reset command ────────────→│
      │ ├─ Clear data                       │
      │ ├─ Re-init viewer                   │
      │ ├─ Get new code                     │
      │ └─ Display new code                 │
      │                                     │
      │ (Now pending again)                 │
      │ Waiting for admin approval          │
```

## 2. Screen Layout Hierarchy

```
DEVICES PAGE (/devices)
├─ Sticky Header (PageHeader)
│  ├─ Title: "Devices"
│  ├─ Search bar (name, IP, code)
│  ├─ Sort dropdown (newest, oldest, name)
│  └─ Stats badges (clickable filters)
│     ├─ All Devices (blue)
│     ├─ Pending (yellow)
│     ├─ Active (green)
│     ├─ Inactive (gray)
│     ├─ Browser (purple)
│     └─ App (blue)
│
├─ Pending Approval Section (Yellow banner)
│  └─ PendingDeviceCard × N
│     ├─ Icon (TV/Monitor)
│     ├─ Device info
│     │  ├─ Name
│     │  ├─ IP
│     │  ├─ Platform badge
│     │  ├─ Code (yellow, large)
│     │  └─ Last seen
│     └─ Approve button (green)
│
├─ Active Devices Table
│  ├─ Header row
│  │  ├─ ID
│  │  ├─ Device + icon
│  │  ├─ Platform
│  │  ├─ IP Address
│  │  ├─ Code
│  │  ├─ Status
│  │  ├─ Last Seen
│  │  └─ Actions (sticky)
│  │
│  └─ Data rows × N
│     ├─ Click row → Device Detail Modal
│     └─ Action buttons
│        ├─ Activate (if pending)
│        ├─ Edit (pencil)
│        ├─ View Logs (file)
│        └─ Delete (trash)
│
└─ Inactive/Released Devices Table
   └─ Same structure as Active


DEVICE DETAIL MODAL
├─ Sticky Header
│  ├─ Device icon
│  ├─ Device name (large)
│  ├─ Online/Offline indicator (green/red circle)
│  └─ Close button
│
├─ Quick Actions Bar
│  ├─ Edit Device
│  ├─ View Logs
│  ├─ Speed History
│  ├─ Preview Content
│  └─ Delete Device
│
├─ Scrollable Content
│  ├─ Tags Section
│  │  ├─ Header + Add button
│  │  ├─ Tag selector (if adding)
│  │  └─ Assigned tags (with X to remove)
│  │
│  ├─ Playlists Section
│  │  ├─ Header + Add button
│  │  ├─ Playlist selector (if adding)
│  │  └─ Assigned playlists (with description)
│  │
│  ├─ Content Section
│  │  ├─ Direct Assignments subsection
│  │  │  ├─ Header + Add button
│  │  │  ├─ Content selector (if adding)
│  │  │  └─ Assigned content items
│  │  │
│  │  └─ Inherited from Tags subsection (read-only)
│  │     ├─ Tag group × N
│  │     │  ├─ Tag badge + color
│  │     │  └─ Content list (max 3 shown)
│  │     └─ "+N more..." text
│  │
│  ├─ Device Information Block
│  │  ├─ ID, Platform, IP
│  │  ├─ Activation Code
│  │  ├─ Status (badge)
│  │  ├─ Last Seen
│  │  └─ Screen Resolution
│  │
│  └─ Network Speed History Block
│     ├─ Header + Run Speed Test button
│     ├─ Speed Stats (3 cards)
│     │  ├─ Download (green)
│     │  ├─ Upload (blue)
│     │  └─ Quality (color-coded)
│     ├─ Speed Chart (Line chart, 10 tests)
│     └─ Quality Legend
│
└─ Sticky Footer
   └─ Close button


DEVICE EDIT MODAL
├─ Sticky Header
│  ├─ Device icon
│  ├─ "Edit Device Settings"
│  └─ Close button
│
├─ Scrollable Content
│  ├─ Device Information Section
│  │  ├─ Device ID (read-only)
│  │  ├─ Device Name (text input)
│  │  ├─ Device Type (read-only)
│  │  ├─ Status (dropdown)
│  │  ├─ IP Address (read-only)
│  │  └─ Last Seen (read-only)
│  │
│  ├─ Replace with Pending Device (browser only)
│  │  ├─ Explanation text
│  │  ├─ Pending device selector (dropdown)
│  │  └─ Warning box (orange)
│  │
│  ├─ Display Settings Section
│  │  ├─ Screen Rotation (dropdown 0/90/180/270)
│  │  └─ Video Audio (toggle buttons)
│  │
│  └─ Display Information Block (read-only)
│     ├─ Screen Resolution
│     ├─ Viewport Size
│     ├─ Device Pixel Ratio
│     ├─ User Agent
│     └─ Connection (type + speed)
│
└─ Sticky Footer
   ├─ Release Device button (left, if active)
   └─ Cancel / Save buttons (right)


DEVICE LOGS MODAL
├─ Sticky Header
│  ├─ Title: "Device Logs"
│  ├─ Device name & ID
│  ├─ Connection status (green/red dot + text)
│  └─ Close button
│
├─ Fixed Filter Bar
│  ├─ Filter label
│  └─ Level buttons (5) with count badges
│     ├─ ALL
│     ├─ LOG
│     ├─ INFO
│     ├─ WARN
│     └─ ERROR
│
├─ Scrollable Log View (Terminal style)
│  └─ Log entries × N
│     ├─ Timestamp (HH:MM:SS)
│     ├─ Level badge (colored)
│     ├─ Source tag (purple, optional)
│     └─ Message text
│
└─ Sticky Footer
   ├─ Log counts: Total | Filtered
   ├─ Real-time status note
   └─ Buttons
      ├─ Export (with icon)
      └─ Clear (with icon)


CONTENT ASSIGNMENT MODAL (Full-screen)
├─ Fixed Header
│  ├─ Device icon
│  ├─ Title: "Assign Content: {device_name}"
│  └─ Close button
│
├─ Two-column grid (scrollable)
│  ├─ LEFT: Available Content
│  │  ├─ Header: "Available Content (X items)"
│  │  └─ Content list (scrollable)
│  │     └─ Content card × N (click to assign)
│  │        ├─ Thumbnail preview
│  │        ├─ Title
│  │        ├─ Type badge + Duration
│  │        ├─ Segment info (if applicable)
│  │        └─ Arrow indicator (→, blue on hover)
│  │
│  └─ RIGHT: Assigned Content
│     ├─ Header: "Assigned Content (X items)"
│     └─ Content list (scrollable)
│        └─ Content card × N (click to unassign)
│           ├─ Arrow indicator (←, red on hover)
│           ├─ Thumbnail preview
│           ├─ Title
│           ├─ Type badge + Duration
│           └─ Segment info (if applicable)
│
└─ No explicit footer (full-screen modal, click outside to close)


DEVICE PREVIEW PAGE (/devices/{id}/preview)
├─ Fixed Header
│  ├─ Back button
│  ├─ Title: "🎬 Preview: {device_name}"
│  └─ Info: "X items • Duration • Y loops/hour"
│
├─ Warning Section (if warnings exist)
│  └─ Alert box with warning list
│
├─ Main Preview Area
│  ├─ Player
│  │  └─ Current content (image or video)
│  │
│  └─ Controls
│     ├─ Previous button (←)
│     ├─ Play/Pause toggle
│     ├─ Next button (→)
│     ├─ Restart button
│     └─ Counter: "X / Y"
│
└─ Sequence List (right sidebar)
   ├─ Title: "Sequence"
   └─ Content list (scrollable)
      └─ Item × N
         ├─ Highlight (if current)
         ├─ Content title
         ├─ Duration
         ├─ Source badge (Direct/Playlist/Tag)
         └─ Click to jump
```

## 3. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DEVICE DATA FLOW ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────────────┘

DEVICES LIST PAGE
─────────────────
   TanStack Query
   ├─ Query Key: ['devices']
   ├─ Fetch Fn: GET /api/devices (limit: 2000)
   ├─ Interval: 5 seconds
   └─ Cached data
       │
       ├→ Pending Devices
       │  ├─ Filter: status === 'pending'
       │  └─ Render: PendingDeviceCard × N
       │
       ├→ Active Devices
       │  ├─ Filter: status === 'active'
       │  └─ Render: DeviceTableRow × N
       │
       └→ Inactive Devices
          ├─ Filter: status === 'inactive'
          └─ Render: DeviceTableRow × N


DEVICE DETAIL MODAL
───────────────────
   Multiple TanStack Queries (Parallel)
   │
   ├─ Devices Query
   │  ├─ Key: ['devices']
   │  ├─ useMemo: Find current device from list
   │  └─ Auto-update on invalidation
   │
   ├─ Tags Query
   │  ├─ Key: ['tags']
   │  ├─ Fetch: GET /api/tags
   │  └─ Compute: assignedTagIds (from device.tags)
   │
   ├─ Playlists Query
   │  ├─ Key: ['playlists']
   │  ├─ Fetch: GET /api/playlists
   │  └─ Compute: assignedPlaylistIds
   │
   ├─ Content Query
   │  ├─ Key: ['content']
   │  ├─ Fetch: GET /api/content
   │  └─ Compute: availableContent
   │
   ├─ Device Content Query
   │  ├─ Key: ['devices', device.id, 'content']
   │  ├─ Fetch: GET /api/devices/{id}/content
   │  └─ Display: Direct assignments list
   │
   ├─ Tag Content Queries (Dynamic)
   │  ├─ Key: ['devices', device.id, 'tag-content', ...]
   │  ├─ Fetch: Promise.all(tag.id → GET /api/tags/{id}/content)
   │  ├─ Trigger: useEffect watches device.tags
   │  └─ Display: Inherited content section
   │
   └─ Speed Test History Query
      ├─ Key: ['devices', device.id, 'speedtest', 'history-chart']
      ├─ Fetch: GET /api/speedtest/devices/{id}/speedtest?limit=10
      ├─ Interval: 60 seconds
      └─ Display: Chart + Stats


DEVICE EDIT MODAL
─────────────────
   Form State (useState)
   │
   ├─ device_name
   ├─ status
   ├─ rotation
   ├─ volume_enabled
   └─ selectedPendingId
       │
       ├→ On Save
       │  ├─ POST /api/devices/{id}/replace-with-pending/{pendingId}
       │  │  (if selectedPendingId)
       │  │
       │  └─ PUT /api/devices/{id}
       │     ├─ device_name
       │     ├─ status
       │     ├─ rotation
       │     └─ volume_enabled
       │
       └→ Invalidate: ['devices'] (auto-refetch)


DEVICE LOGS MODAL
─────────────────
   Dual Data Source
   │
   ├─ Initial Load (REST)
   │  ├─ GET /api/devices/{id}/logs
   │  └─ Store in logs[] state
   │
   └─ Real-time Stream (WebSocket)
      ├─ Connect: ws://server/api/ws/logs/{device_id}
      ├─ On message: Append to logs[] state
      │  └─ Auto-scroll to newest
      │
      └─ On error/close: Show cached logs
         └─ Status: "Loaded (no real-time updates)"
         
       
SPEED TEST RESULTS
──────────────────
   Manual Trigger
   │
   ├─ User clicks "Run Speed Test"
   │  │
   │  ├→ POST /api/devices/{id}/commands
   │     └─ { command_type: 'run_speed_test' }
   │
   ├→ Toast: "Speed test command queued..."
   │
   └→ Auto-invalidate after 15 seconds
      ├─ queryClient.invalidateQueries(['devices', id, 'speedtest'])
      │  
      └→ Refetch displays new results
         └─ Update chart & stats
```

## 4. State Management Flow

```
DEVICE STATE HIERARCHY
─────────────────────

APP LEVEL (Zustand)
└─ authStore
   ├─ user
   ├─ token
   └─ roles

FEATURE LEVEL (TanStack Query)
├─ devices (auto-refresh: 5s)
├─ tags (on-demand)
├─ playlists (on-demand)
├─ content (on-demand)
└─ speed tests (auto-refresh: 60s)

COMPONENT LEVEL (useState)
├─ Devices page
│  ├─ searchQuery
│  ├─ sortBy
│  ├─ activeFilter
│  ├─ selectedDevice
│  ├─ showDeviceDetailModal
│  ├─ showDeviceEditModal
│  └─ showLogsModal
│
├─ Device Detail Modal
│  ├─ showTagSelector
│  ├─ showPlaylistSelector
│  ├─ showContentSelector
│  └─ showSpeedHistory
│
├─ Device Edit Modal
│  ├─ formData
│  │  ├─ device_name
│  │  ├─ status
│  │  ├─ rotation
│  │  └─ volume_enabled
│  ├─ isSaving
│  ├─ isReleasing
│  ├─ pendingDevices
│  └─ selectedPendingId
│
└─ Device Logs Modal
   ├─ logs[]
   ├─ filteredLogs[]
   ├─ selectedLevel
   ├─ isConnected
   └─ connectionStatus


MUTATION FLOW
─────────────

Input → Mutation → onSuccess → Invalidation → Refetch → Update UI
  │        │           │             │           │          │
  │        │           │             │           │          └─ Display new data
  │        │           │             │           └─ TanStack Query
  │        │           │             └─ Clear cache for stale data
  │        │           └─ Toast notification
  │        └─ API call (POST/PUT/DELETE)
  └─ User action (click/submit)

Example: Assign Tag
────────────────────
User clicks "Add Tag"
  │
  ├→ assignTagMutation.mutate(tagId)
  │  │
  │  ├→ POST /api/tags/assign
  │  │  { device_id, tag_id }
  │  │
  │  └→ onSuccess
  │     │
  │     ├→ queryClient.invalidateQueries(['devices'])
  │     │  └─ Triggers refetch
  │     │
  │     └→ Toast: "Tag assigned!"
  │        │
  │        └→ useEffect watches device.tags
  │           └→ Refetch tag content
  │
  └→ UI updates
     ├─ Tag badge appears in Device Detail
     ├─ Tag content loads in "Inherited from Tags"
     └─ Available tags dropdown updates


REFRESH CYCLES
──────────────

Every 5 seconds (Devices List)
└─ Refetch ['devices']
   ├─ Update pending devices count
   ├─ Show new pending device cards
   ├─ Update last_seen in tables
   └─ Keep all stats current

Every 60 seconds (Device Detail Modal open)
└─ Refetch ['devices', {id}, 'speedtest', 'history-chart']
   ├─ Update speed chart with latest test
   ├─ Update speed stats cards
   └─ Auto-refresh if user watching

Every 30 seconds (Device heartbeat)
└─ Viewer sends heartbeat to server
   ├─ Server updates device.last_seen
   ├─ Marks device as "online" (if seen < 60s)
   ├─ Next 5s refresh shows updated timestamp
   └─ Online status indicator updates

WebSocket real-time (Logs Modal)
└─ New logs stream in
   ├─ Append to logs[]
   ├─ Filter by selected level
   ├─ Auto-scroll to newest
   └─ Count badges update
```

## 5. Modal Opening/Closing Flow

```
MODAL STACK
───────────

Devices Page
  │
  ├─ Device row clicked
  │  │
  │  └─ setSelectedDevice(device)
  │     setShowDeviceDetailModal(true)
  │        │
  │        ├─ Device Detail Modal opens
  │        │  ├─ Shows all device data
  │        │  │
  │        │  ├─ Edit button clicked
  │        │  │  │
  │        │  │  ├─ onClose()
  │        │  │  │  └─ Close Detail Modal
  │        │  │  │
  │        │  │  └─ onEdit(device)
  │        │  │     ├─ setSelectedDevice(device)
  │        │  │     └─ setShowDeviceEditModal(true)
  │        │  │        │
  │        │  │        └─ Device Edit Modal opens
  │        │  │           │
  │        │  │           ├─ User saves changes
  │        │  │           │  │
  │        │  │           │  ├─ POST/PUT request
  │        │  │           │  │
  │        │  │           │  └─ onClose()
  │        │  │           │     ├─ Close Edit Modal
  │        │  │           │     └─ Refetch devices
  │        │  │           │
  │        │  │           └─ User closes
  │        │  │              └─ onClose()
  │        │  │
  │        │  ├─ View Logs button clicked
  │        │  │  │
  │        │  │  ├─ onClose()
  │        │  │  │
  │        │  │  └─ onViewLogs(device)
  │        │  │     ├─ setSelectedDevice(device)
  │        │  │     └─ setShowLogsModal(true)
  │        │  │        │
  │        │  │        └─ Device Logs Modal opens
  │        │  │           ├─ Load initial logs (REST)
  │        │  │           ├─ Connect WebSocket
  │        │  │           ├─ Filter logs
  │        │  │           ├─ Export / Clear actions
  │        │  │           │
  │        │  │           └─ onClose()
  │        │  │              ├─ Close Logs Modal
  │        │  │              ├─ Close WebSocket
  │        │  │              └─ Return to Devices
  │        │  │
  │        │  ├─ Preview button clicked
  │        │  │  │
  │        │  │  └─ window.open(`/devices/{id}/preview`, '_blank')
  │        │  │     └─ New tab/window opens
  │        │  │        ├─ Load preview data
  │        │  │        ├─ Play/Pause/Next/Prev controls
  │        │  │        ├─ Close original modal when done
  │        │  │        └─ Or keep both open
  │        │  │
  │        │  ├─ Speed History button clicked
  │        │  │  │
  │        │  │  └─ setShowSpeedHistory(true)
  │        │  │     │
  │        │  │     └─ Speed History Modal opens
  │        │  │        ├─ Show table of 20 tests
  │        │  │        ├─ Auto-refresh every 10s
  │        │  │        │
  │        │  │        └─ onClose()
  │        │  │           └─ Close Speed History
  │        │  │
  │        │  └─ Close button / outside click
  │        │     │
  │        │     └─ onClose()
  │        │        ├─ setShowDeviceDetailModal(false)
  │        │        ├─ setSelectedDevice(null)
  │        │        └─ Return to Devices page
  │        │
  │        └─ etc...
  │
  └─ (All modals cleared when page closes)
```

## 6. Real-Time Update Timeline

```
DEVICE LIFECYCLE EXAMPLE
────────────────────────

T=0s:  New device registers
       └─ Server creates: status='pending', unique_code='123456'

T=0-5s: Admin sees device in pending list (within 5s refresh)
        └─ PendingDeviceCard appears

T=5s:  Heartbeat received
       └─ last_seen updated on server

T=5s:  Admin clicks "Approve"
       ├─ POST /api/devices/{id} (status='active')
       └─ Device instantly moves to Active table

T=5s:  [Assume detail modal open]
       Admin sees device online (< 60s heartbeat)
       └─ Green circle indicator

T=10s: Second heartbeat
       └─ last_seen updated again

T=15s: Admin clicks "Run Speed Test"
       ├─ POST /api/devices/{id}/commands
       └─ Command queued to device

T=20s: Device receives command, runs test
       └─ Connects to speed test server

T=30s: Test completes, results sent to server
       └─ Speed test saved in DB

T=32s: Auto-invalidate triggers (T+15s from trigger)
       ├─ queryClient.invalidateQueries(['devices', id, 'speedtest'])
       └─ New results appear in modal

T=40s: Admin opens Speed History Modal
       ├─ Fetches GET /api/speedtest/devices/{id}/speedtest
       └─ Shows last 20 tests including the new one

T=40s: Speed History auto-refreshes every 10s
       └─ Updates if new test added

T=100s: Device goes offline (no heartbeat for 60s)
        ├─ last_seen still exists (but > 60s ago)
        └─ Online indicator turns RED in detail modal
           (if still open)

T=120s: Detail modal refresh
        ├─ Recalculates: now - last_seen = 120s > 60s timeout
        └─ Confirms offline status
```

