# ANTHIAS - QUICK REFERENCE GUIDE

## TL;DR: What is Anthias?

**Anthias** (formerly Screenly OSE) is an intelligent digital signage CMS that:
- Stores media files in organized asset management system
- Schedules content playback by time windows (start_date, end_date)
- Manages playlists with dynamic ordering (play_order)
- Detects database changes and updates playlists seamlessly
- Provides REST APIs for remote management
- Runs on various hardware (Raspberry Pi, x86, cloud VMs)

**NOT just file storage** - it's a complete content management & scheduling system.

---

## CORE FILES BY FUNCTION

### Asset Data Model (SINGLE SOURCE OF TRUTH)
```
File: /mnt/g/khoirul/signate/anthias/anthias_app/models.py (41 lines)

Asset Table Schema:
  asset_id         → UUID primary key
  name             → Content name
  uri              → File path (/data/screenly_assets/...)
  md5              → File checksum
  start_date       → When to activate
  end_date         → When to deactivate
  duration         → Display duration (seconds)
  mimetype         → image/video/etc
  is_enabled       → Active/inactive toggle
  is_processing    → Upload state
  play_order       → Sequence in playlist
  skip_asset_check → Skip validation
```

### Scheduling Engine (THE HEART - 148 lines)
```
File: /mnt/g/khoirul/signate/anthias/viewer/scheduling.py

Key Functions:
  Scheduler.__init__()           → Initialize with current playlist
  Scheduler.get_next_asset()     → Get asset to play now
  Scheduler.refresh_playlist()   → Check if playlist needs update
  Scheduler.update_playlist()    → Rebuild from database
  generate_asset_list()          → Filter enabled assets by time

Key Algorithm (Deadline-Based Refresh):
  1. Get all deadlines (end_date for active, start_date for inactive)
  2. Find nearest deadline
  3. Only refresh when deadline is reached OR database changes detected
  4. Minimizes unnecessary updates - GENIUS!
```

### REST API Endpoints
```
File: /mnt/g/khoirul/signate/anthias/api/views/
├── v1.py   (206 lines)  - Legacy PUT /assets/{id}
├── v1_1.py (88 lines)   - GET /assets, GET /assets/{id}
├── v1_2.py (127 lines)  - PATCH /assets/{id} (partial)
└── v2.py   (529 lines)  - Current comprehensive API

Key Endpoints:
  GET    /api/v1/assets/             - List all assets
  POST   /api/v1/assets/             - Create asset
  GET    /api/v1/assets/{id}/        - Get asset detail
  PATCH  /api/v2/assets/{id}/        - Update asset
  DELETE /api/v1/assets/{id}/        - Delete asset
  POST   /api/v1/assets/{id}/content - Upload file
```

### File Upload Handling
```
File: /mnt/g/khoirul/signate/anthias/api/views/mixins.py (lines 141-243)

FileAssetViewMixin:
  - POST file upload
  - MIME type validation
  - Save to screenly_assets/ directory
  - Generate MD5 checksum
  - Set is_processing → False when done
```

### Backup & Recovery
```
File: /mnt/g/khoirul/signate/anthias/api/views/mixins.py (lines 48-118)

BackupViewMixin.post()
  → Creates tar.gz of:
     - All settings from screenly.conf
     - All image/video files
     - Asset metadata from database
  → Returns backup file name

RecoverViewMixin.post()
  → Restore from tar.gz backup
  → Stop viewer during restore
  → Resume viewer after complete
```

### Configuration Management
```
File: /mnt/g/khoirul/signate/anthias/settings.py (231 lines)

Class: AnthiasSettings(UserDict)
  - Loads screenly.conf on startup
  - ConfigParser-based (.conf files)
  - Mutable at runtime
  - Password hashing

Key Settings:
  [main]
    assetdir: screenly_assets
    database: screenly.db
    websocket_port: 9999
  [viewer]
    resolution: 1920x1080
    shuffle_playlist: false
    default_duration: 10
    player_name: ""

ZmqPublisher:
  - Send commands to viewer
  - Port 10001 (TCP)
  - Commands: play, stop, next, prev
```

### Background Jobs (Async Task Queue)
```
File: /mnt/g/khoirul/signate/anthias/celery_tasks.py (94 lines)

Celery Setup:
  Broker: Redis (localhost:6379)
  Backend: Redis (same)
  Result TTL: 6 hours

Tasks:
  cleanup()              - Runs every 60 minutes
                        → Remove .tmp files
  get_display_power()    - Runs every 5 minutes
                        → Query TV power via CEC
  reboot_anthias()       - One-off
                        → Graceful reboot via Balena/systemctl
  shutdown_anthias()     - One-off
                        → Graceful shutdown
```

### Device Detection & Diagnostics
```
File: /mnt/g/khoirul/signate/anthias/lib/device_helper.py (46 lines)

parse_cpu_info():
  - Extract from /proc/cpuinfo
  - CPU count, serial, hardware, revision, model

get_device_type():
  - Check /proc/device-tree/model
  - Return: pi5, pi4, pi3, pi2, pi1, x86

File: /mnt/g/khoirul/signate/anthias/lib/diagnostics.py (106 lines)

System Diagnostics:
  get_display_power()     - Query TV status via CEC
  get_uptime()            - From /proc/uptime
  get_load_avg()          - CPU load (1/5/15 min)
  get_git_*()             - Build info (branch, hash)
  try_connectivity()      - Test internet (Google, BBC)
  get_debian_version()    - OS info
  get_raspberry_*()       - Pi-specific info
```

### Authentication
```
File: /mnt/g/khoirul/signate/anthias/lib/auth.py (170 lines)

Classes:
  NoAuth               - No authentication
  BasicAuth            - Username/password
  
Decorator:
  @authorized          - Protect endpoints
  
Flow:
  Request → Check auth backend
          → If no auth: proceed
          → If basic: validate header
          → If invalid: 401 Unauthorized
```

---

## ARCHITECTURE PATTERNS

### 1. Asset Lifecycle

```
UPLOAD → is_processing=True
  ↓
File saved to /data/screenly_assets/{uuid}
  ↓
is_processing=False, is_enabled=False
  ↓
Admin activates + sets dates
  ↓
is_enabled=True, start_date=T1, end_date=T2
  ↓
Scheduler detects (checks database mtime)
  ↓
Filters: is_enabled=True, start_date < now < end_date
  ↓
Adds to active playlist by play_order
  ↓
Viewer displays until end_date
  ↓
Scheduler removes (deadline reached)
```

### 2. Intelligent Refresh Mechanism

```
Scheduler.refresh_playlist() checks:
  1. Database modification time
     If newer than last check → UPDATE_PLAYLIST
  2. Deadline comparison
     If current_time >= nearest_deadline → UPDATE_PLAYLIST
  3. Shuffle counter
     If shuffle_playlist=true AND counter >= 5 → UPDATE_PLAYLIST

This prevents constant database queries!
Only updates when NECESSARY.
```

### 3. Non-Disruptive Updates

```
Old playlist: [asset1, asset2, asset3]
Current position: playing asset2

Admin adds asset4 at end:
New playlist would be: [asset1, asset2, asset3, asset4]

Scheduler checks: Are the assets in same order?
  YES → Keep playing asset2, don't restart!
  NO → Restart at beginning

This prevents jarring display resets.
```

### 4. Multi-Version API Backward Compatibility

```
V1   clients → /api/v1/assets/         (PUT updates)
V1.1 clients → /api/v1.1/assets/       (GET support)
V1.2 clients → /api/v1.2/assets/       (PATCH support)
V2   clients → /api/v2/assets/         (comprehensive)

All versions use same Asset model!
No data conflicts.
Smooth upgrade path.
```

---

## WHAT WE'RE USING (Signate/Anthias Integration)

### Content Lifecycle in Our System

```
User uploads via /content/upload
  ↓
Backend calls anthias_service.upload_asset()
  → File sent to Anthias API
  → Anthias creates Asset with is_processing=True
  → File saved to /data/screenly_assets/
  → is_processing set to False
  ↓
Anthias returns asset_id, uri
  ↓
Our backend saves to PostgreSQL:
  Content {
    title: "...",
    anthias_asset_id: "abc123def456",
    anthias_url: "http://anthias:8000/screenly_assets/...",
    duration: 10,
    video_duration: 45,
    resolution: "1920x1080",
    ...
  }
  ↓
Viewer requests playlist
  ↓
Backend fetches content assignments
  ↓
Builds list with Anthias URLs
  ↓
Viewer downloads from Anthias
  ↓
Viewer plays (displays for duration seconds)
```

### What We're NOT Using (Yet)

```
✗ Scheduling (start_date, end_date)
  → We don't set these in Anthias
  → We build playlists manually

✗ Playlist Ordering (play_order)
  → We manage order in our Playlist model
  → Don't leverage Anthias field

✗ Asset Activation Toggle (is_enabled)
  → We filter in our code
  → Don't use Anthias is_enabled

✗ Intelligent Refresh (deadline tracking)
  → We poll every N seconds
  → Don't use Anthias Scheduler

✗ Backup/Recovery
  → Could use for disaster recovery
  → Not implemented yet

✗ Device Diagnostics API
  → Could monitor device health
  → Not implemented yet
```

---

## KEY INSIGHTS

### 1. Scheduler is the Secret Sauce

The scheduler (148 lines in viewer/scheduling.py) is incredibly efficient:
- **Doesn't poll every frame** - only when necessary
- **Deadline-based refresh** - smart change detection
- **Non-disruptive updates** - compares before updating
- **Handles edge cases** - shuffling, positioning, etc.

This is WHY Anthias works so well on Raspberry Pi with limited resources.

### 2. Single Source of Truth

Everything revolves around the Asset table:
- Viewer reads from it
- API writes to it
- Scheduler monitors it
- Backup includes it

No schema conflicts if we respect this.

### 3. Multi-Version API is Mature

Anthias has been evolving for 10+ years:
- V1 is old but still works
- V1.1 added GET
- V1.2 added PATCH
- V2 is current

This shows professional software design.

### 4. Platform Separation is Clean

Core business logic (scheduling, ordering, settings):
- Platform-agnostic
- Database-agnostic (supports SQLite and PostgreSQL)
- File system-agnostic (just stores paths)

Platform-specific stuff (CEC, GStreamer, Pi detection):
- Isolated in viewer and diagnostics
- Not baked into core

### 5. We Should Respect These Patterns

```
DO:
✓ Use Asset model as-is
✓ Call Anthias APIs through official endpoints
✓ Treat Asset table as read-only from our perspective
✓ Store cross-references (asset_id) in our models
✓ Keep configuration separate

DON'T:
✗ Modify Asset schema
✗ Duplicate Asset management
✗ Query Asset table directly (use API)
✗ Import Django models in our FastAPI code
✗ Create sync issues between systems
```

---

## FILES TO REFERENCE

### For Understanding Scheduling
- `/mnt/g/khoirul/signate/anthias/viewer/scheduling.py` - Core algorithm
- `/mnt/g/khoirul/signate/anthias/tests/test_scheduler.py` - Test cases

### For Understanding Asset Management
- `/mnt/g/khoirul/signate/anthias/anthias_app/models.py` - Schema
- `/mnt/g/khoirul/signate/anthias/api/views/v2.py` - Latest API

### For Understanding File Operations
- `/mnt/g/khoirul/signate/anthias/api/views/mixins.py` - Upload/backup/recovery

### For Understanding Configuration
- `/mnt/g/khoirul/signate/anthias/settings.py` - Config system
- `/mnt/g/khoirul/signate/anthias/.screenly/screenly.conf` - Example config

### For Understanding Our Integration
- `/mnt/g/khoirul/signate/backend/app/services/anthias_service.py` - Our API client
- `/mnt/g/khoirul/signate/backend/app/api/content.py` - Upload logic
- `/mnt/g/khoirul/signate/backend/app/api/client.py` - Playlist building

---

## NEXT STEPS

### To Better Understand Anthias
1. Read `/mnt/g/khoirul/signate/anthias/viewer/scheduling.py` (148 lines - very clear)
2. Read `/mnt/g/khoirul/signate/anthias/anthias_app/models.py` (41 lines - simple schema)
3. Try calling Anthias API manually to understand flows

### To Leverage More Features
1. Map our Playlist → Anthias Asset scheduling
2. Use play_order for content ordering
3. Track video_duration from Asset metadata
4. Implement backup/recovery for migration

### To Maintain Healthy Integration
1. Never modify Asset schema
2. Always call through API (not direct DB)
3. Keep both systems loosely coupled
4. Test migrations with Anthias updates

