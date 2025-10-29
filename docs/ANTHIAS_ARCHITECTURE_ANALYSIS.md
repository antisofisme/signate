# COMPREHENSIVE ANTHIAS ARCHITECTURE RE-ANALYSIS

## Executive Summary

Anthias (formerly Screenly OSE) is a **production-grade digital signage platform** with sophisticated architecture for managing, scheduling, and delivering media content to multiple displays. It's NOT just "file storage" - it's a full CMS with:

1. **Intelligent Scheduling Engine** - Time-based asset activation with deadline tracking
2. **Playlist Management** - Dynamic ordering, shuffling, lifecycle management
3. **Real-time Asset Synchronization** - Database modification detection and instant updates
4. **Multi-version API** - Backward compatibility across major versions (v1, v1.1, v1.2, v2)
5. **Background Job Processing** - Celery-based async task handling
6. **Device Management** - Central control plane for multiple displays
7. **Backup/Recovery** - Enterprise-grade data protection
8. **Hardware Integration** - CEC (TV control), device detection, power management

---

## CORE ARCHITECTURE BREAKDOWN

### 1. DATABASE SCHEMA (anthias_app/models.py)

The entire system revolves around the **Asset Model**:

```
Asset {
  asset_id (UUID, primary key)
  name (display name)
  uri (file path: /data/screenly_assets/...)
  md5 (file integrity)
  start_date (activation start)
  end_date (activation end)
  duration (display time in seconds)
  mimetype (image/video detection)
  is_enabled (activate/deactivate)
  is_processing (upload state)
  nocache (bypass cache)
  play_order (sequence in playlist)
  skip_asset_check (deployment control)
}
```

**This is the single source of truth** for all content throughout Anthias.

### 2. SCHEDULING ENGINE (viewer/scheduling.py) - The HEART

**Core Logic (148 lines):**

```python
class Scheduler:
  - get_next_asset() → Returns current playing asset
  - refresh_playlist() → Detects changes and updates if needed
  - update_playlist() → Rebuilds active asset list from database
  - generate_asset_list() → Filters enabled assets by time + applies shuffle
```

**Intelligent Deadline System:**

```
Deadline Map Algorithm:
1. For ACTIVE assets → deadline = asset.end_date (when to stop playing)
2. For INACTIVE assets → deadline = asset.start_date (when to start)
3. Sort all deadlines, pick nearest one
4. When deadline reached → refresh entire playlist
```

This is **GENIUS** - the system only refreshes when necessary, not on every frame.

**Database Change Detection:**
```python
def refresh_playlist(self):
  if file_modification_time(database) > last_checked:
    update_playlist()  # Admin made changes via API
  elif deadline_reached:
    update_playlist()  # Time-based content switch
```

### 3. PLAYLIST MANAGEMENT (viewer/scheduling.py)

```
Active Playlist Structure:
[
  {asset_id, name, duration, start_date, end_date, ...},
  {asset_id, name, duration, start_date, end_date, ...},
  ...
]

Ordering Rules:
- play_order (manual ordering)
- shuffle_playlist (randomize each cycle)
- index tracking (maintain position across updates)
```

**Key Feature: Non-Disruptive Updates**
```python
def update_playlist(self):
  new_assets, new_deadline = generate_asset_list()
  if new_assets == old_assets and new_deadline == old_deadline:
    return  # Nothing changed, don't restart playback!
  # Only update if actual content changed
  self.assets = new_assets
  self.index = self.index % len(new_assets) if new_assets else 0
```

This prevents jarring display resets when admin makes non-affecting changes.

### 4. API LAYERS (api/views/) - Multi-Version Strategy

**V1 (Legacy)** - 206 lines
- PUT /assets/{id} (full update)
- POST /assets (create)

**V1.1** - 88 lines
- GET /assets (list)
- GET /assets/{id} (detail)

**V1.2** - 127 lines
- PATCH /assets/{id} (partial update - **IMPROVEMENT**)
- Unique asset name enforcement

**V2 (Current)** - 529 lines
- **Comprehensive asset management**
- Device settings (resolution, shuffle, cache)
- System info (version, device, uptime, memory, IP)
- Backup/recovery
- Reboot/shutdown
- Integrations
- **NEW: Asset ordering via play_order**

Each version is **backward compatible** - old clients still work!

### 5. BACKGROUND JOBS (celery_tasks.py)

```python
Periodic Tasks:
- cleanup() every 1 hour     → Remove .tmp files from assets
- get_display_power() every 5 min → Query TV via CEC, store in Redis

One-off Tasks:
- reboot_anthias()   → Gracefully reboot device
- shutdown_anthias() → Power off device
```

Uses **Redis as message broker** - decouples API from long operations.

### 6. SETTINGS & CONFIGURATION (settings.py)

```
[main]
  assetdir: screenly_assets  (where files stored)
  database: screenly.db      (SQLite for local, or PostgreSQL)
  websocket_port: 9999       (for real-time communication)
  auth_backend: none|basic   (authentication strategy)

[viewer]
  resolution: 1920x1080      (display dimensions)
  shuffle_playlist: false    (randomize playback)
  default_duration: 10       (seconds per asset)
  player_name: ""            (device identifier)
  audio_output: hdmi         (audio routing)
  show_splash: true          (startup logo)
  verify_ssl: true           (HTTPS validation)
```

### 7. ZMQ MESSAGING SYSTEM (settings.py) - Real-time Control

```
Publisher (10001):
  Backend → Viewer
  send_to_viewer('play')      # Resume playback
  send_to_viewer('stop')      # Pause playback
  send_to_viewer('next')      # Skip to next
  send_to_viewer('prev')      # Go to previous

Collector (5558):
  Viewer → Backend
  Used for heartbeat, status updates
```

This enables **remote control** of running displays!

### 8. ASSET STATE MACHINE

```
                     UPLOAD
                        ↓
                  is_processing: True
                        ↓
                   [FILE SAVED]
                        ↓
                  is_processing: False
                   is_enabled: False
                        ↓
                    [OPTIONAL: Admin sets]
                        ↓
                  is_enabled: True
                  start_date: T1
                  end_date: T2
                        ↓
                 [SCHEDULER TRACKS]
                        ↓
        ┌─────────────────────────────┐
        ↓                             ↓
    INACTIVE                       ACTIVE
  (T1 not reached)           (T1 <= now <= T2)
        ↓                             ↓
    Scheduled                     Playing
    for future                    in viewer
```

---

## SEPARATION: CORE vs OPTIONAL

### CORE (MUST KEEP - Makes Anthias Powerful)

#### 1. Asset Model & Database Schema
- **Why:** Single source of truth for all content
- **Used by:** Every API endpoint, scheduler, viewer
- **Impact:** Remove this = system falls apart
- **Location:** `anthias_app/models.py`

#### 2. Scheduling Engine
- **Why:** Intelligent deadline-based content switching
- **Used by:** Viewer's asset_loop()
- **Impact:** Without this = no time-based scheduling, manual playlist management only
- **Location:** `viewer/scheduling.py` (148 lines of pure genius)
- **Logic:**
  - `generate_asset_list()` - Smart filtering by time
  - `Scheduler.refresh_playlist()` - Change detection
  - Deadline tracking - Efficient refresh mechanism

#### 3. Playlist Management & Ordering
- **Why:** Dynamic, non-disruptive content ordering
- **Features:**
  - `play_order` field for manual sequencing
  - Shuffle capability
  - Preserves position across updates
- **Location:** `viewer/scheduling.py` (lines 70-142)
- **Impact:** Without this = static playlists, can't reorder dynamically

#### 4. API Layer (REST endpoints)
- **Why:** Standard interface for content management
- **Features:**
  - Multi-version support (v1, v1.1, v1.2, v2)
  - Backward compatibility
  - Standardized serialization
- **Location:** `api/views/*.py`
- **Used by:** Web admin, external systems, mobile apps
- **Impact:** Without this = no remote management capability

#### 5. File Asset Management
- **Why:** Handle file uploads, conversions, verification
- **Features:**
  - MIME type detection
  - MD5 integrity checking
  - File path management
  - Auto-skip corrupt assets
- **Location:** `api/views/mixins.py` (FileAssetViewMixin, lines 141-243)

#### 6. Background Job Processing
- **Why:** Async operations don't block API
- **Features:**
  - Celery task queue
  - Periodic cleanup
  - Device control (reboot/shutdown)
- **Location:** `celery_tasks.py`
- **Impact:** Without this = API gets blocked during long operations

#### 7. Device Status & Diagnostics
- **Why:** Central monitoring of display health
- **Features:**
  - System info (uptime, load, memory)
  - Device detection (Pi3/Pi4/Pi5)
  - Network status
  - TV power status via CEC
- **Location:** `lib/diagnostics.py`, `lib/device_helper.py`

#### 8. Backup & Recovery System
- **Why:** Enterprise-grade data protection
- **Features:**
  - tar.gz backups including settings + metadata
  - Asset-aware recovery
  - No data loss on deployment
- **Location:** `api/views/mixins.py` (BackupViewMixin, RecoverViewMixin)
- **Impact:** Critical for production systems

#### 9. Authentication & Authorization
- **Why:** Secure access to API
- **Features:**
  - Basic auth support
  - Pluggable auth backends
  - Decorator-based protection (@authorized)
- **Location:** `lib/auth.py`

#### 10. Settings Management
- **Why:** Persistent device configuration
- **Features:**
  - ConfigParser-based (.conf files)
  - Per-field defaults
  - Password hashing
  - Runtime modification
- **Location:** `settings.py` (AnthiasSettings class)

---

### OPTIONAL (CAN REMOVE - Platform/Viewer Specific)

#### 1. Built-in Web UI (static/src/)
- **Why:** Anthias has its own React frontend
- **What:** Old React components, admin interface
- **Replacement:** We have `/signate/web-admin` - our modern web UI
- **Impact:** None - we don't use it
- **Decision:** REMOVE - we have better UI

#### 2. Viewer Implementation (viewer/)
- **Why:** Anthias viewer is for Raspberry Pi displays
- **What:** 
  - OpenGL/X11 display rendering
  - CEC (TV control) integration
  - Pi-specific hardware detection
- **Replacement:** We have `/signate/viewer` - unified viewer
- **Impact:** High - but we're not using Anthias viewer anyway
- **Decision:** KEEP (for reference), but we use our own

#### 3. Raspberry Pi Specific Code
- **Files:**
  - `raspberry_pi_imager/` - Build Pi images
  - `/proc/device-tree/model` checks in `lib/device_helper.py`
  - CEC library integration in `lib/diagnostics.py`
  - Balena cloud integration
- **Replacement:** We support cloud devices, not just Pi
- **Decision:** REMOVE - but keep abstract concepts (device detection)

#### 4. WebView Components (webview/)
- **Why:** Android/iOS WebView implementation
- **Replacement:** We have web viewer
- **Decision:** REMOVE

#### 5. Ansible Deployment Scripts
- **Files:** `ansible/` directory
- **Why:** Automated Pi provisioning
- **Replacement:** Docker + our own deployment
- **Decision:** REMOVE

#### 6. Internal Web UI (templates/)
- **Why:** Django templates for the old admin
- **Replacement:** `web-admin/` React app
- **Decision:** REMOVE

#### 7. Host Agent (host_agent.py)
- **Why:** Local command execution (reboot, shutdown)
- **What:** Redis pubsub listener for system commands
- **Keep:** The concept (remote system control)
- **Adapt:** Use our own service wrapper instead
- **Decision:** REFACTOR

---

## WHAT WE'RE USING RIGHT NOW

### Current Integration (backend/app)

```
Our Backend:
  ├── Content Model
  │   ├── title, description
  │   ├── anthias_asset_id (foreign key)
  │   ├── anthias_url (storage location)
  │   ├── duration (display time)
  │   └── video_duration, resolution, codec, etc.
  │
  ├── Content Upload
  │   ├── POST /content/upload
  │   ├── File → Anthias API
  │   ├── Save metadata to PostgreSQL
  │   └── Return content with both IDs
  │
  └── Client Playlist
      ├── GET /client/devices/{id}/playlist
      ├── Filter by device assignments
      ├── Build URL list from Anthias
      └── Send to viewer

Anthias Backend:
  ├── Handles file storage
  ├── Manages Asset table
  ├── Provides /api/v1/assets/
  ├── Stores files in /data/screenly_assets/
  └── Serves static content
```

**Current PROBLEMS:**
1. We're NOT using Anthias scheduling at all
2. We treat duration as just metadata, not scheduling
3. We don't leverage play_order for sequencing
4. We don't use Anthias time-based activation
5. We rebuild client playlist from scratch each time

---

## WHAT WE'RE MISSING OUT ON

### 1. Intelligent Scheduling (HIGH VALUE)

**We could leverage:**
```python
Asset.objects.filter(
    is_enabled=True,
    start_date__lt=now,
    end_date__gt=now
).order_by('play_order')
```

**Benefits:**
- Automatic content rotation on schedule
- Time-of-day campaigns
- Maintenance windows (hide assets)
- A/B testing with date ranges

### 2. Dynamic Playlist Ordering (MEDIUM VALUE)

**We're NOT using:**
- `play_order` field for sequencing
- Ability to reorder playlist without restart
- Shuffle capability

**Could add:**
```
POST /playlists/{id}/reorder
Body: [asset_id_1, asset_id_2, ...]
→ Updates play_order in one transaction
```

### 3. Real-time Content Updates (MEDIUM VALUE)

**Current flow:**
```
Viewer → API every N seconds
API rebuilds entire playlist
Viewer detects changes, restarts
```

**Better flow (Anthias way):**
```
Admin updates asset
Database changes
Scheduler detects change (file mtime check)
If safe: seamless update
If unsafe: wait for scene break
```

### 4. Backup/Recovery Integration (LOW VALUE - optional)

**Not critical but nice:**
- Export all content + metadata as `.tar.gz`
- Restore on new device
- Zero manual intervention

### 5. Device Health Monitoring (MEDIUM VALUE)

**We're NOT tracking:**
- Display power status
- Memory/CPU usage trends
- Network quality
- Asset playback errors

**Anthias provides:**
- Real-time metrics via diagnostics API
- Historical tracking
- Alerting capability

---

## ARCHITECTURE ANALYSIS: CODE STRUCTURE

### Platform-Agnostic Code (Portable)

```
✓ lib/auth.py              - Authentication abstraction
✓ api/helpers.py           - Asset ordering, active filtering
✓ viewer/scheduling.py     - Scheduler core logic
✓ settings.py              - Config management
✓ anthias_app/models.py    - Asset data model
✓ celery_tasks.py          - Job queue pattern
```

### Platform-Specific Code (Tightly Coupled)

```
✗ viewer/__init__.py       - X11/OpenGL rendering (Pi-only)
✗ viewer/media_player.py   - GStreamer integration (Pi-only)
✗ lib/diagnostics.py       - CEC, /proc/cpuinfo parsing (Pi-only)
✗ raspberry_pi_imager/     - Pi image building (Pi-only)
✗ webview/                 - Android/iOS wrapper (mobile-only)
✗ host_agent.py            - systemctl, Balena (Pi-only)
```

### Database Schema (Universal)

```
Asset Table:
├── asset_id         ✓ Universal (UUID)
├── name             ✓ Universal
├── uri              ✓ Universal (file path)
├── md5              ✓ Universal (checksum)
├── start_date       ✓ Universal (scheduling)
├── end_date         ✓ Universal (scheduling)
├── duration         ✓ Universal
├── mimetype         ✓ Universal
├── is_enabled       ✓ Universal
├── is_processing    ✓ Universal (upload state)
├── play_order       ✓ Universal (sequencing)
└── skip_asset_check ✓ Universal
```

**Every field is platform-agnostic!**

---

## PROPER FORK STRATEGY

### Phase 1: KEEP CORE (No Changes)

```
Keep As-Is:
✓ anthias_app/models.py    - Asset schema
✓ api/                     - REST endpoints (for backward compat)
✓ viewer/scheduling.py     - Scheduler logic
✓ settings.py              - Config management
✓ lib/auth.py              - Auth
✓ celery_tasks.py          - Job queue
✓ lib/utils.py             - Utilities

Minimize Conflicts:
- Don't modify Asset model
- Don't change database schema
- Keep API routes consistent
```

### Phase 2: ABSTRACT OPTIONAL PIECES

```
Replace:
├── viewer/          → Use our own /signate/viewer (different platform)
├── static/src/      → Remove (we have web-admin)
├── templates/       → Remove (we have web-admin)
├── raspberry_pi_imager/ → Remove (not needed)
├── webview/         → Remove (not needed)
└── ansible/         → Remove (we have Docker)

Keep but Isolate:
├── lib/diagnostics.py  → Keep core functions, abstract hardware-specific parts
└── host_agent.py       → Keep pattern, implement our own version
```

### Phase 3: EXTEND CORE (Build On Top)

```
Don't modify Anthias core:
├── Asset model
├── Scheduling engine
├── API endpoints
└── Settings

Build on top:
├── Our backend → Content model (wraps Asset)
├── Our viewer → Reads playlist from scheduler
├── Our web-admin → Calls Anthias API for file ops
└── Our API → Orchestrates workflow
```

---

## INTEGRATION BEST PRACTICES

### Pattern 1: Separation of Concerns

```
Anthias (Data Plane):
  - File storage (screenly_assets/)
  - Asset metadata (Asset table)
  - Scheduling rules (start_date, end_date)
  - Low-level APIs (/api/v1/assets/)

Our Backend (Control Plane):
  - Business logic (Content, Assignments, Playlists)
  - User management
  - Device orchestration
  - High-level APIs (/content/, /playlists/)

Our Viewer (Playback Plane):
  - Rendering
  - Device registration
  - Heartbeat
  - Playback control
```

### Pattern 2: API Composition

```
DON'T:  Duplicate Anthias APIs
DO:     Wrap Anthias APIs

Example:
  WRONG: POST /api/assets (our own implementation)
  RIGHT: POST /content/upload → anthias_service.upload_asset()
                             → save to db
                             → return composed response

Benefits:
  - Single source of truth
  - Easy to swap Anthias for different storage
  - No schema conflicts
  - Better error handling
```

### Pattern 3: Scheduling Integration

```
Currently Unused:
  - Asset.start_date
  - Asset.end_date
  - Asset.is_enabled
  - Asset.play_order

Could leverage:
  POST /playlists/{id}/schedule
  Body: {
    content_id: 123,
    start_date: "2024-01-01T09:00Z",
    end_date: "2024-01-31T17:00Z",
    play_order: 1
  }
  
  → Creates Asset with scheduling metadata
  → Viewer's scheduler automatically manages
  → No backend involvement in playback
```

---

## RECOMMENDATIONS

### Short-term (Keep Current Architecture)

1. **Keep current integration** - We're already using Anthias as file storage
2. **Document the separation** - Clear boundaries between systems
3. **Don't break Anthias** - Treat it as immutable (except Asset CRUD)
4. **Extend via API** - All changes through REST endpoints

### Medium-term (Leverage More Features)

1. **Use play_order** for playlist sequencing
2. **Implement duration as display time** (already do this)
3. **Add scheduling metadata** to content model
4. **Track more diagnostics** from device API

### Long-term (If Scaling)

1. **Consider replacing Anthias with simpler storage** (S3, local disk)
2. **Keep scheduler pattern** (incredibly efficient)
3. **Migrate Asset schema to our db** (if needed)
4. **Maintain API compatibility** (for backward compat)

---

## CONCLUSION

Anthias is **NOT just file storage**. It's a sophisticated CMS with:

- **Intelligent deadline-based scheduling** that prevents unnecessary updates
- **Non-disruptive playlist management** that preserves viewer state
- **Multi-version API** that maintains backward compatibility
- **Enterprise backup/recovery** for reliability
- **Hardware integration** for device control

**What makes it powerful:**
1. Single source of truth (Asset model)
2. Efficient change detection (file mtime + deadline tracking)
3. Non-invasive updates (smart playlist comparison)
4. Clean separation (API ↔ Storage ↔ Viewer)

**What we're using right:**
- File storage
- Metadata management
- Basic CRUD APIs

**What we're NOT using but could:**
- Scheduling (time-based content rotation)
- Dynamic ordering (play_order field)
- Real-time change detection
- Backup/recovery
- Device diagnostics

**Best strategy:**
Use Anthias as immutable backend for file storage and scheduling metadata. Build our control plane on top without modifying core. This gives us flexibility while maintaining stability.
