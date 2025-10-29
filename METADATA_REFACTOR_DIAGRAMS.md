# Metadata Refactor: Visual Diagrams & Flowcharts

## 1. Current State: Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEB ADMIN INTERFACE                          │
│                  (React/TypeScript)                             │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─→ UPLOAD CONTENT
             │   ├─ File
             │   ├─ Title
             │   ├─ Description
             │   ├─ Duration (seconds)
             │   └─ Is Active (boolean)
             │
             │   1. POST /api/contents/upload
             │      ├─→ FastAPI Backend (content.py)
             │      │   │
             │      │   ├─→ Upload to Anthias
             │      │   │   ├─ name = title
             │      │   │   ├─ duration = duration ← DUPLICATE
             │      │   │   ├─ mimetype = file.mime_type ← DUPLICATE
             │      │   │   └─ is_enabled = is_active ← DUPLICATE
             │      │   │
             │      │   ├─→ Extract metadata (FFprobe)
             │      │   │   ├─ resolution
             │      │   │   ├─ codec
             │      │   │   ├─ bitrate
             │      │   │   └─ video_duration
             │      │   │
             │      │   └─→ Save to PostgreSQL
             │      │       ├─ title ← SOURCE OF TRUTH
             │      │       ├─ duration ← SOURCE OF TRUTH
             │      │       ├─ mime_type ← SOURCE OF TRUTH
             │      │       ├─ is_active ← SOURCE OF TRUTH
             │      │       ├─ anthias_asset_id
             │      │       ├─ anthias_url
             │      │       ├─ [metadata fields]
             │      │       └─ created_at
             │
             ├─→ EDIT CONTENT
             │   └─ PATCH /api/contents/{id}
             │       ├─→ Update PostgreSQL ✓
             │       │   └─ title, duration, description, etc.
             │       │
             │       └─→ Sync to Anthias? ✗ NOT IMPLEMENTED
             │           (metadata becomes STALE!)
             │
             └─→ VIEW PLAYLISTS
                 └─ GET /api/client/playlist
                     │
                     ├─→ Query PostgreSQL
                     │   └─ Get all assigned content
                     │
                     └─→ For each content:
                         ├─ Get content.anthias_asset_id
                         ├─ SYNC API CALL TO ANTHIAS! (130ms latency)
                         │   GET /api/v1/assets/{asset_id}
                         │   Response:
                         │   {
                         │     "asset_id": "...",
                         │     "uri": "/data/screenly_assets/xxx",
                         │     "name": "old_title", ← STALE if updated!
                         │     "duration": 10,
                         │     "mimetype": "video/mp4",
                         │     "is_enabled": 1
                         │   }
                         │
                         ├─ Extract uri
                         ├─ Convert to URL
                         ├─ Build playlist item with:
                         │   ├─ url (from uri)
                         │   ├─ duration (from PostgreSQL, not Anthias)
                         │   ├─ mime_type (from PostgreSQL, not Anthias)
                         │   └─ title (from PostgreSQL, not Anthias)
                         │
                         └─ Return playlist
```

## 2. Proposed State: Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    WEB ADMIN INTERFACE                          │
│                  (React/TypeScript)                             │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─→ UPLOAD CONTENT
             │   ├─ File
             │   ├─ Title
             │   ├─ Description
             │   ├─ Duration (seconds)
             │   └─ Is Active (boolean)
             │
             │   1. POST /api/contents/upload
             │      ├─→ FastAPI Backend (content.py)
             │      │   │
             │      │   ├─→ Upload to Anthias
             │      │   │   └─ file only (pure storage!)
             │      │   │       Response: { uri, asset_id }
             │      │   │
             │      │   ├─→ Extract metadata (FFprobe)
             │      │   │   ├─ resolution
             │      │   │   ├─ codec
             │      │   │   ├─ bitrate
             │      │   │   └─ video_duration
             │      │   │
             │      │   └─→ Save to PostgreSQL ✓ FULL METADATA
             │      │       ├─ title ← SOURCE OF TRUTH
             │      │       ├─ duration ← SOURCE OF TRUTH
             │      │       ├─ mime_type ← SOURCE OF TRUTH
             │      │       ├─ is_active ← SOURCE OF TRUTH
             │      │       ├─ anthias_asset_id (for deletion)
             │      │       ├─ anthias_file_uri ← NEW! (cached)
             │      │       ├─ [metadata fields]
             │      │       └─ created_at
             │
             ├─→ EDIT CONTENT
             │   └─ PATCH /api/contents/{id}
             │       └─→ Update PostgreSQL ✓ IMMEDIATELY EFFECTIVE
             │           ├─ title ✓
             │           ├─ duration ✓
             │           ├─ description ✓
             │           └─ is_active ✓
             │           (No Anthias sync needed!)
             │
             └─→ VIEW PLAYLISTS
                 └─ GET /api/client/playlist
                     │
                     ├─→ Query PostgreSQL
                     │   └─ Get all assigned content
                     │
                     └─→ For each content:
                         ├─ Get content from PostgreSQL
                         ├─ Use content.anthias_file_uri (CACHED!)
                         │   ✓ NO API CALL TO ANTHIAS!
                         │   ✓ 130ms latency saved!
                         │
                         ├─ Convert uri to URL:
                         │   /data/screenly_assets/xxx
                         │   → http://server:8000/screenly_assets/xxx
                         │
                         ├─ Build playlist item with:
                         │   ├─ url (from cached uri)
                         │   ├─ duration (from PostgreSQL)
                         │   ├─ mime_type (from PostgreSQL)
                         │   └─ title (from PostgreSQL)
                         │
                         └─ Return playlist FAST (250ms → 120ms)
```

## 3. Sequence Diagram: Upload Content

### Current Sequence
```
User                 Browser         Backend          Anthias         PostgreSQL
│                     │                │                │               │
├─ Upload Form ────→  │                │                │               │
│                     │ POST /upload  │                │               │
│                     ├───────────────→│                │               │
│                     │                │                │               │
│                     │                ├─ Upload File ─→│               │
│                     │                │                │               │
│                     │                │            (Process)           │
│                     │                │                │               │
│                     │                │← Return URI ───│               │
│                     │                │    + asset_id  │               │
│                     │                │                │               │
│                     │                ├─ Create Asset ─→│               │
│                     │                │ (name, duration,│               │
│                     │                │  mimetype,      │               │
│                     │                │  is_enabled)    │               │
│                     │                │                │               │
│                     │                │            (Store)            │
│                     │                │                │               │
│                     │                │← Return asset ──│               │
│                     │                │                │               │
│                     │                ├─ Save to DB ──────────────────→│
│                     │                │                │               │
│                     │                │                │        (Store)│
│                     │                │                │               │
│                     │← Response ──────┤                │               │
│                     │                │                │               │
│← Show Success ──────│                │                │               │

Issues:
❌ Metadata duplicated in Anthias
❌ If user edits title in web admin, Anthias shows old "name"
❌ Playlist requests will fetch stale data from Anthias
```

### Proposed Sequence
```
User                 Browser         Backend          Anthias         PostgreSQL
│                     │                │                │               │
├─ Upload Form ────→  │                │                │               │
│                     │ POST /upload  │                │               │
│                     ├───────────────→│                │               │
│                     │                │                │               │
│                     │                ├─ Upload File ─→│               │
│                     │                │                │               │
│                     │                │            (Process)           │
│                     │                │                │               │
│                     │                │← Return URI ───│               │
│                     │                │    + asset_id  │               │
│                     │                │                │               │
│                     │                ├─ Save to DB ──────────────────→│
│                     │                │ (Include URI  │               │
│                     │                │  in cached    │               │
│                     │                │  field)       │               │
│                     │                │                │        (Store)│
│                     │                │                │               │
│                     │← Response ──────┤                │               │
│                     │                │                │               │
│← Show Success ──────│                │                │               │

Benefits:
✓ No metadata duplication
✓ Updates to PostgreSQL = immediate effect
✓ Playlist requests use cached URI (no Anthias call)
✓ Simple, clean architecture
```

## 4. Class Diagram: Content Model

### Current Model
```
┌──────────────────────────────────┐
│         Content (Current)         │
├──────────────────────────────────┤
│ Attributes:                      │
│ • id: int                        │
│ • title: str                     │ ← PostgreSQL
│ • description: str               │    SOURCE OF TRUTH
│ • content_type: str              │
│ • anthias_url: str               │
│ • anthias_asset_id: str          │
│ • duration: int                  │ ← PostgreSQL
│ • file_size: int                 │    SOURCE OF TRUTH
│ • mime_type: str                 │ ← PostgreSQL
│ • resolution: str                │    SOURCE OF TRUTH
│ • width: int                     │
│ • height: int                    │
│ • codec: str                     │
│ • fps: float                     │
│ • bitrate: int                   │
│ • video_duration: float          │
│ • audio_codec: str               │
│ • audio_bitrate: int             │
│ • audio_sample_rate: int         │
│ • is_active: bool                │ ← PostgreSQL
│ • [template fields]              │    SOURCE OF TRUTH
│ • created_at: datetime           │
│ • updated_at: datetime           │
├──────────────────────────────────┤
│ Methods:                         │
│ • to_dict()                      │
│ • get_playback_duration()        │
└──────────────────────────────────┘

Data Duplication (Anthias):
┌──────────────────────────────────┐
│    Anthias Asset (Mirror)        │
├──────────────────────────────────┤
│ • asset_id: str                  │
│ • uri: str                       │
│ • name: str          ← SAME AS  │
│ • duration: int        POSTGRESQL│
│ • mimetype: str        BUT STALE!│
│ • is_enabled: bool               │
└──────────────────────────────────┘
```

### Proposed Model
```
┌──────────────────────────────────┐
│      Content (Proposed)          │
├──────────────────────────────────┤
│ Attributes:                      │
│ • id: int                        │
│ • title: str                     │ ← SINGLE SOURCE OF TRUTH
│ • description: str               │
│ • content_type: str              │
│ • anthias_asset_id: str          │ (for deletion only)
│ • anthias_file_uri: str (NEW!)   │ (cached from Anthias)
│ • duration: int                  │ ← SINGLE SOURCE OF TRUTH
│ • file_size: int                 │
│ • mime_type: str                 │ ← SINGLE SOURCE OF TRUTH
│ • resolution: str                │
│ • width: int                     │
│ • height: int                    │
│ • codec: str                     │
│ • fps: float                     │
│ • bitrate: int                   │
│ • video_duration: float          │
│ • audio_codec: str               │
│ • audio_bitrate: int             │
│ • audio_sample_rate: int         │
│ • is_active: bool                │ ← SINGLE SOURCE OF TRUTH
│ • [template fields]              │
│ • created_at: datetime           │
│ • updated_at: datetime           │
├──────────────────────────────────┤
│ Methods:                         │
│ • to_dict()                      │
│ • get_playback_duration()        │
│ • get_content_url()              │
└──────────────────────────────────┘

Anthias (Pure Storage):
┌──────────────────────────────────┐
│  Anthias Asset (File Storage)    │
├──────────────────────────────────┤
│ • asset_id: str                  │
│ • uri: str                       │
│ (metadata managed in PostgreSQL) │
└──────────────────────────────────┘

No Duplication!
Anthias = File Storage Only
PostgreSQL = Metadata + Cache
```

## 5. Database Schema Comparison

### Current Schema
```sql
-- PostgreSQL: contents table
CREATE TABLE contents (
    id INT PRIMARY KEY,
    title VARCHAR(200),           -- ← SOURCE
    description TEXT,
    duration INT,                 -- ← SOURCE (Anthias also has this)
    mime_type VARCHAR(100),        -- ← SOURCE (Anthias also has this)
    is_active BOOLEAN,             -- ← SOURCE (Anthias also has this)
    anthias_asset_id VARCHAR(100),
    anthias_url VARCHAR(500),
    [+ 20 more metadata columns]
    created_at DATETIME,
    updated_at DATETIME
);

-- Anthias: assets table
-- Stores:
-- - name (DUPLICATE of title)
-- - duration (DUPLICATE of duration)
-- - mimetype (DUPLICATE of mime_type)
-- - is_enabled (DUPLICATE of is_active)
```

### Proposed Schema
```sql
-- PostgreSQL: contents table
ALTER TABLE contents ADD COLUMN anthias_file_uri VARCHAR(500);
CREATE INDEX idx_anthias_file_uri ON contents(anthias_file_uri);

CREATE TABLE contents (
    id INT PRIMARY KEY,
    title VARCHAR(200),           -- ← SINGLE SOURCE
    description TEXT,
    duration INT,                 -- ← SINGLE SOURCE
    mime_type VARCHAR(100),        -- ← SINGLE SOURCE
    is_active BOOLEAN,             -- ← SINGLE SOURCE
    anthias_asset_id VARCHAR(100), -- (for deletion ref only)
    anthias_file_uri VARCHAR(500), -- NEW: cache URI
    [+ 20 more metadata columns]
    created_at DATETIME,
    updated_at DATETIME
);

-- Anthias: assets table
-- Stores ONLY:
-- - uri (file path)
-- - asset_id (identifier)
-- No metadata duplication!
```

## 6. Performance Comparison

### Current Performance Profile
```
Playlist Request Timeline (Current):
─────────────────────────────────────

t=0ms    Device GET /api/client/playlist
│
├─→ t=10ms   Query PostgreSQL
│            Get 5 content items
│
├─→ t=50ms   For content #1:
│            GET /api/v1/assets/{id} to Anthias
│            Network latency: 25ms
│            Processing: 5ms
│            → t=80ms
│
├─→ t=105ms  For content #2:
│            Same process: 25ms latency
│            → t=130ms
│
├─→ t=155ms  For content #3:
│            → t=180ms
│
├─→ t=205ms  For content #4:
│            → t=230ms
│
├─→ t=255ms  For content #5:
│            → t=280ms
│
└─→ t=290ms  Response sent to device

Total: ~290ms (mostly waiting for Anthias)
Anthias API calls: 5
```

### Proposed Performance Profile
```
Playlist Request Timeline (Proposed):
───────────────────────────────────────

t=0ms    Device GET /api/client/playlist
│
├─→ t=10ms   Query PostgreSQL
│            Get 5 content items WITH cached URI
│
├─→ t=15ms   For content #1-5:
│            Use cached uri directly
│            No network calls needed
│            Process URI → URL: <1ms per item
│
└─→ t=120ms  Response sent to device

Total: ~120ms (purely database bound)
Anthias API calls: 0
Latency saved: ~170ms (58% improvement)
```

### Graph
```
Response Time Comparison:

Current:   [████████████████████████████] 290ms
Proposed:  [█████████████] 120ms

Latency Reduction: 170ms (-58%)
API Calls Reduction: 5 → 0 (-100%)
```

## 7. Integration Timeline Diagram

```
Week 1                  Week 2                  Week 3
──────────────────────────────────────────────────────────────

Day 1-2: Design Review & Approval
│   ├─ Review architecture
│   ├─ Approve approach
│   └─ Get sign-off

Day 3-4: Phase 1 Implementation
│   ├─ Add model field
│   ├─ Database migration
│   ├─ Update upload flow
│   └─ Create backfill script

Day 5: Phase 2 Implementation
│   ├─ Optimize playlist endpoint
│   └─ Remove Anthias API calls

Day 6-7: Phase 3-4 Implementation
│   ├─ Update CRUD endpoints
│   └─ Run data migration

                        Day 8: Testing
                        │   ├─ Unit tests
                        │   ├─ Integration tests
                        │   ├─ Performance tests
                        │   └─ All passing ✓

                        Day 9: Documentation
                        │   ├─ Update API docs
                        │   ├─ Update architecture docs
                        │   └─ Create runbooks

                        Day 10: Staging Deployment
                        │   ├─ Deploy to staging
                        │   ├─ Run full test suite
                        │   ├─ Verify metrics
                        │   └─ Final sign-off

                                            Day 11-12: Production
                                            │   ├─ Deploy code
                                            │   ├─ Run migration
                                            │   ├─ Monitor metrics
                                            │   └─ Verify success ✓

                                            Day 13: Optimization
                                            │   └─ Phase 3 optional
                                            │       simplification
```

## 8. Risk/Benefit Matrix

```
                    HIGH
                  BENEFIT
                    │
                    │   ✓ URI Caching
                    │   (Quick Wins)
                    │   +130ms perf
                    │   +consistency
    LOW ────────────┼────────────── HIGH
    RISK             │              RISK
                    │   ⚠ Remove Metadata Sync
                    │   (Phase 3)
                    │   +simplicity
                    │   -requires testing
                    │
                   LOW
                 BENEFIT

Recommendation: Start with URI Caching (high benefit, low risk)
                Then Phase 2 (optimization, proven low risk)
                Then Phase 3 (optional, if time permits)
```

---

**All diagrams are in ASCII art for compatibility and documentation.**
