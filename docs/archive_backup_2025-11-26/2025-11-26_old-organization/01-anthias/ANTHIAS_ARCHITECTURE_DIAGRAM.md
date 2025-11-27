# Anthias Storage Integration - Architecture Diagrams

**System:** Smart TV Digital Signage
**Integration:** Backend API ↔ Anthias Storage Service
**Status:** ✅ Production Ready

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Content Upload Flow](#content-upload-flow)
3. [Content Serving Flow](#content-serving-flow)
4. [Content Deletion Flow](#content-deletion-flow)
5. [Data Flow Architecture](#data-flow-architecture)
6. [Storage Architecture](#storage-architecture)
7. [Deployment Architecture](#deployment-architecture)
8. [Error Handling Flow](#error-handling-flow)

---

## System Overview

```
┌───────────────────────────────────────────────────────────────────────┐
│                         SMART TV DIGITAL SIGNAGE                       │
│                         Production Architecture                        │
└───────────────────────────────────────────────────────────────────────┘

                              SERVER: 192.168.5.12

┌─────────────────────┐           ┌─────────────────────┐
│    Web Admin UI     │           │   TV Viewer App     │
│   (Port 3000)       │           │   (Port 8080)       │
│   React + Vite      │           │   Vanilla JS        │
│                     │           │                     │
│  - Upload content   │           │  - Display content  │
│  - Manage devices   │           │  - Auto-update      │
│  - Configure tags   │           │  - Device control   │
└──────────┬──────────┘           └──────────┬──────────┘
           │                                  │
           │ HTTP/WebSocket                  │ HTTP/WebSocket
           │                                  │
           └─────────────┬────────────────────┘
                         │
                         ▼
          ┌──────────────────────────────────────┐
          │      Backend API (Port 8001)         │
          │         FastAPI + Python             │
          ├──────────────────────────────────────┤
          │  ✓ Content Management                │
          │  ✓ Device Management                 │
          │  ✓ User Authentication               │
          │  ✓ WebSocket Real-time Updates       │
          │  ✓ API Request/Response Handling     │
          └───┬──────────────┬──────────────┬────┘
              │              │              │
              │              │              │
    ┌─────────▼──────┐  ┌───▼──────┐  ┌───▼────────────┐
    │  PostgreSQL    │  │  Redis   │  │    Anthias     │
    │  (Port 5433)   │  │(Port 6379│  │  (Port 8000)   │
    │                │  │          │  │                │
    │ - Content      │  │ - Cache  │  │ - File Storage │
    │   Metadata     │  │ - Session│  │ - Asset Mgmt   │
    │ - Devices      │  │ - Locks  │  │ - File Serving │
    │ - Users        │  │          │  │                │
    │ - Tags         │  │          │  │                │
    └────────────────┘  └──────────┘  └────────┬───────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │   File System         │
                                    │   /data/screenly_     │
                                    │        assets/        │
                                    │                       │
                                    │  - uuid1 (video)      │
                                    │  - uuid2 (image)      │
                                    │  - uuid3 (video)      │
                                    └───────────────────────┘
```

---

## Content Upload Flow

### High-Level Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌────────────┐     ┌──────────┐
│  User   │────▶│Web Admin│────▶│ Backend │────▶│  Anthias   │────▶│File      │
│         │     │         │     │   API   │     │  Storage   │     │System    │
└─────────┘     └─────────┘     └─────────┘     └────────────┘     └──────────┘
   Select           Upload          Validate       2-Step Upload      Store
   File             Request         + Metadata     Process            File
                                    Extraction
                                         │
                                         ▼
                                   ┌─────────┐
                                   │PostgreSQL│
                                   │         │
                                   │ Save    │
                                   │Metadata │
                                   └─────────┘
```

### Detailed Upload Sequence

```
User/Browser          Web Admin           Backend API          Anthias Storage       PostgreSQL
      │                   │                     │                      │                  │
      │ Select file       │                     │                      │                  │
      ├──────────────────▶│                     │                      │                  │
      │                   │                     │                      │                  │
      │                   │ FormData:           │                      │                  │
      │                   │ - file (binary)     │                      │                  │
      │                   │ - title             │                      │                  │
      │                   │ - description       │                      │                  │
      │                   │ - duration          │                      │                  │
      │                   ├────────────────────▶│                      │                  │
      │                   │ POST /api/content/  │                      │                  │
      │                   │      upload         │                      │                  │
      │                   │                     │                      │                  │
      │                   │                     │ 1. Validate file type│                  │
      │                   │                     │    (image/video only)│                  │
      │                   │                     │                      │                  │
      │                   │                     │ 2. Extract metadata  │                  │
      │                   │                     │    (FFprobe)         │                  │
      │                   │                     │    - Resolution      │                  │
      │                   │                     │    - Codec           │                  │
      │                   │                     │    - Duration        │                  │
      │                   │                     │    - Bitrate         │                  │
      │                   │                     │                      │                  │
      │                   │                     │ 3. Upload to Anthias │                  │
      │                   │                     │ ──────────────────────▶                 │
      │                   │                     │ POST /file_asset     │                  │
      │                   │                     │ (Step 1: Upload file)│                  │
      │                   │                     │                      │                  │
      │                   │                     │◁──────────────────────                  │
      │                   │                     │ {"uri": "/data/..."}│                  │
      │                   │                     │                      │                  │
      │                   │                     │ ──────────────────────▶                 │
      │                   │                     │ POST /assets         │                  │
      │                   │                     │ (Step 2: Create asset│                  │
      │                   │                     │  with URI)           │                  │
      │                   │                     │                      │                  │
      │                   │                     │◁──────────────────────                  │
      │                   │                     │ {"asset_id": "uuid"} │                  │
      │                   │                     │                      │                  │
      │                   │                     │ 4. Save to database  │                  │
      │                   │                     │ ─────────────────────────────────────▶  │
      │                   │                     │ INSERT INTO contents │                  │
      │                   │                     │ - title, description │                  │
      │                   │                     │ - anthias_asset_id   │                  │
      │                   │                     │ - anthias_url        │                  │
      │                   │                     │ - resolution, codec  │                  │
      │                   │                     │ - metadata...        │                  │
      │                   │                     │                      │                  │
      │                   │                     │◁────────────────────────────────────────│
      │                   │                     │ content record       │                  │
      │                   │                     │                      │                  │
      │                   │◁────────────────────│                      │                  │
      │                   │ 201 Created         │                      │                  │
      │                   │ {                   │                      │                  │
      │                   │   "id": 1,          │                      │                  │
      │                   │   "anthias_url": ...│                      │                  │
      │                   │   "metadata": {...} │                      │                  │
      │                   │ }                   │                      │                  │
      │◁──────────────────│                     │                      │                  │
      │ Upload success    │                     │                      │                  │
      │ Show preview      │                     │                      │                  │
```

### Anthias 2-Step Upload Process

```
Backend API                     Anthias Storage Service
     │                                    │
     │  STEP 1: Upload File              │
     ├──────────────────────────────────▶ │
     │ POST /api/v1/file_asset           │
     │                                    │
     │ Content-Type: multipart/form-data │
     │ file_upload: (filename, bytes)    │
     │                                    │
     │                                    │ ┌──────────────────┐
     │                                    │ │  1. Receive file │
     │                                    │ │  2. Generate UUID│
     │                                    │ │  3. Save to disk │
     │                                    │ │     /data/       │
     │                                    │ │     screenly_    │
     │                                    │ │     assets/uuid  │
     │                                    │ └──────────────────┘
     │                                    │
     │ ◁──────────────────────────────────│
     │ 200 OK                             │
     │ {                                  │
     │   "uri": "/data/screenly_assets/   │
     │           abc-123-def-456"         │
     │ }                                  │
     │                                    │
     │                                    │
     │  STEP 2: Create Asset             │
     ├──────────────────────────────────▶ │
     │ POST /api/v1/assets                │
     │                                    │
     │ Content-Type: application/x-www-   │
     │               form-urlencoded      │
     │ model: {                           │
     │   "name": "Product Demo",          │
     │   "uri": "/data/.../abc-123-...",  │
     │   "mimetype": "video",             │
     │   "duration": "30",                │
     │   "is_enabled": 1                  │
     │ }                                  │
     │                                    │
     │                                    │ ┌──────────────────┐
     │                                    │ │  1. Create asset │
     │                                    │ │     record       │
     │                                    │ │  2. Link to file │
     │                                    │ │  3. Generate ID  │
     │                                    │ └──────────────────┘
     │                                    │
     │ ◁──────────────────────────────────│
     │ 200 OK                             │
     │ {                                  │
     │   "asset_id": "xyz-789-abc-123",   │
     │   "uri": "/data/.../abc-123-...",  │
     │   "name": "Product Demo",          │
     │   "mimetype": "video"              │
     │ }                                  │
     │                                    │
```

---

## Content Serving Flow

### High-Level Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌────────────┐
│TV Viewer│────▶│ Backend │────▶│  Anthias│────▶│Response    │
│         │     │   API   │     │ Storage │     │with        │
│         │     │ (Proxy) │     │         │     │Content-Type│
└─────────┘     └─────────┘     └─────────┘     └────────────┘
  Request        Get metadata    Get file         Serve
  image/video    from DB         content          to client
```

### Detailed Serving Sequence

```
TV Viewer / Browser       Backend API            PostgreSQL         Anthias Storage
       │                       │                      │                    │
       │ GET /api/content/1/   │                      │                    │
       │        image          │                      │                    │
       ├──────────────────────▶│                      │                    │
       │                       │                      │                    │
       │                       │ SELECT * FROM        │                    │
       │                       │ contents WHERE id=1  │                    │
       │                       ├─────────────────────▶│                    │
       │                       │                      │                    │
       │                       │◁─────────────────────│                    │
       │                       │ Content record:      │                    │
       │                       │ - anthias_asset_id   │                    │
       │                       │ - mime_type          │                    │
       │                       │                      │                    │
       │                       │ GET /api/v1/assets/  │                    │
       │                       │     {asset_id}/      │                    │
       │                       │     content          │                    │
       │                       ├──────────────────────────────────────────▶│
       │                       │                      │                    │
       │                       │                      │   ┌──────────────┐ │
       │                       │                      │   │1. Read file  │ │
       │                       │                      │   │   from disk  │ │
       │                       │                      │   │2. Encode to  │ │
       │                       │                      │   │   base64     │ │
       │                       │                      │   └──────────────┘ │
       │                       │                      │                    │
       │                       │◁──────────────────────────────────────────│
       │                       │ {                    │                    │
       │                       │   "content": "base64"│                    │
       │                       │ }                    │                    │
       │                       │                      │                    │
       │                       │ Decode base64 to     │                    │
       │                       │ binary bytes         │                    │
       │                       │                      │                    │
       │◁──────────────────────│                      │                    │
       │ 200 OK                │                      │                    │
       │ Content-Type: image/  │                      │                    │
       │               jpeg    │                      │                    │
       │ [binary image data]   │                      │                    │
       │                       │                      │                    │
       │ Display image         │                      │                    │
       │                       │                      │                    │
```

### Why Proxy Instead of Direct Access?

```
❌ WITHOUT PROXY (Doesn't work for browsers):

TV Viewer ──────────────────▶ Anthias Storage
                              http://anthias:8000/data/screenly_assets/uuid

Problem:
- File has NO extension (uuid only)
- No Content-Type header
- Browser doesn't know if it's JPG, PNG, MP4, etc.
- Browser can't display file


✅ WITH PROXY (Works correctly):

TV Viewer ──▶ Backend API ──▶ Anthias Storage
              (Add headers)    (Get file)

1. Backend fetches mime_type from database (e.g., "image/jpeg")
2. Backend requests file content from Anthias
3. Backend adds Content-Type: image/jpeg header
4. Browser receives file with correct type
5. Browser displays image correctly
```

---

## Content Deletion Flow

### Deletion Sequence

```
Web Admin             Backend API            Anthias Storage       PostgreSQL
    │                      │                       │                   │
    │ DELETE /api/content/1│                       │                   │
    ├─────────────────────▶│                       │                   │
    │                      │                       │                   │
    │                      │ SELECT * FROM         │                   │
    │                      │ contents WHERE id=1   │                   │
    │                      ├───────────────────────────────────────────▶
    │                      │                       │                   │
    │                      │◁──────────────────────────────────────────│
    │                      │ content record with   │                   │
    │                      │ anthias_asset_id      │                   │
    │                      │                       │                   │
    │                      │ DELETE /api/v1/assets/│                   │
    │                      │        {asset_id}     │                   │
    │                      ├──────────────────────▶│                   │
    │                      │                       │                   │
    │                      │                       │ ┌───────────────┐ │
    │                      │                       │ │1. Delete asset│ │
    │                      │                       │ │   record      │ │
    │                      │                       │ │2. Delete file │ │
    │                      │                       │ │   from disk   │ │
    │                      │                       │ └───────────────┘ │
    │                      │                       │                   │
    │                      │◁──────────────────────│                   │
    │                      │ 204 No Content        │                   │
    │                      │                       │                   │
    │                      │ DELETE FROM contents  │                   │
    │                      │ WHERE id=1            │                   │
    │                      ├───────────────────────────────────────────▶
    │                      │                       │                   │
    │                      │ (Cascades to:)        │                   │
    │                      │ - content_assignments │                   │
    │                      │ - playlist_contents   │                   │
    │                      │                       │                   │
    │                      │◁──────────────────────────────────────────│
    │                      │ Success               │                   │
    │                      │                       │                   │
    │                      │ Invalidate cache      │                   │
    │                      │ (content_list_*)      │                   │
    │                      │                       │                   │
    │◁─────────────────────│                       │                   │
    │ 200 OK               │                       │                   │
    │ {"message": "Deleted"}                       │                   │
    │                      │                       │                   │
```

---

## Data Flow Architecture

### Content Metadata vs File Storage

```
┌──────────────────────────────────────────────────────────────────┐
│                       CONTENT DATA FLOW                          │
└──────────────────────────────────────────────────────────────────┘

┌─────────────────────┐                    ┌────────────────────────┐
│   PostgreSQL DB     │                    │   Anthias File System  │
│   (Metadata Store)  │                    │   (Binary Storage)     │
├─────────────────────┤                    ├────────────────────────┤
│                     │                    │                        │
│ Content Table:      │                    │ /data/screenly_assets/ │
│                     │                    │                        │
│ ┌─────────────────┐ │                    │ ┌────────────────────┐ │
│ │ id: 1           │ │    References      │ │ abc-123-def-456    │ │
│ │ title: "Demo"   │ │◀──────────────────▶│ │ (no extension)     │ │
│ │ anthias_asset_id│ │    asset_id        │ │                    │ │
│ │ anthias_url     │ │                    │ │ File Type: video/  │ │
│ │ mime_type       │ │                    │ │            mp4     │ │
│ │ resolution      │ │                    │ │ Size: 10MB         │ │
│ │ codec           │ │                    │ └────────────────────┘ │
│ │ duration        │ │                    │                        │
│ │ width, height   │ │                    │ ┌────────────────────┐ │
│ │ bitrate         │ │                    │ │ xyz-789-abc-123    │ │
│ │ created_at      │ │                    │ │ (no extension)     │ │
│ └─────────────────┘ │                    │ │                    │ │
│                     │                    │ │ File Type: image/  │ │
│ ┌─────────────────┐ │                    │ │            jpeg    │ │
│ │ id: 2           │ │    References      │ │ Size: 2MB          │ │
│ │ title: "Banner" │ │◀──────────────────▶│ └────────────────────┘ │
│ │ anthias_asset_id│ │    asset_id        │                        │
│ │ anthias_url     │ │                    │                        │
│ │ ...             │ │                    │                        │
│ └─────────────────┘ │                    │                        │
│                     │                    │                        │
└─────────────────────┘                    └────────────────────────┘

         │                                            │
         │                                            │
         ▼                                            ▼
   Used by viewers                             Served to clients
   for playlists,                              when requested
   scheduling,                                 (via backend proxy)
   filtering
```

### Data Consistency Model

```
┌──────────────────────────────────────────────────────────────────┐
│              SOURCE OF TRUTH FOR DIFFERENT DATA                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────┐         ┌───────────────────────────┐
│   PostgreSQL = PRIMARY   │         │  Anthias = FILE STORAGE   │
│   SOURCE OF TRUTH        │         │  ONLY                     │
├──────────────────────────┤         ├───────────────────────────┤
│                          │         │                           │
│ ✓ Content metadata       │         │ ✓ Binary file data        │
│   (title, description)   │         │   (video/image bytes)     │
│                          │         │                           │
│ ✓ Display settings       │         │ ✗ Metadata NOT used       │
│   (duration, timing)     │         │   (DB has priority)       │
│                          │         │                           │
│ ✓ Media metadata         │         │ ✗ Asset properties        │
│   (resolution, codec)    │         │   ignored by viewers      │
│                          │         │                           │
│ ✓ Assignments            │         │                           │
│   (device, tag links)    │         │                           │
│                          │         │                           │
│ ✓ Scheduling             │         │                           │
│   (start/end dates)      │         │                           │
│                          │         │                           │
└──────────────────────────┘         └───────────────────────────┘

Why This Design?
- Viewers need fast metadata access (DB query)
- File serving is handled by backend proxy (adds headers)
- Anthias update failures don't break viewer functionality
- Single source of truth prevents inconsistencies
```

---

## Storage Architecture

### File System Layout

```
SERVER: 192.168.5.12
/
├── data/
│   ├── screenly_assets/          # Anthias file storage
│   │   ├── abc-123-def-456       # Video file (no extension)
│   │   ├── xyz-789-ghi-012       # Image file (no extension)
│   │   ├── mno-345-pqr-678       # Another video
│   │   └── ...
│   │
│   ├── hls/                      # HLS transcoding output
│   │   ├── 1/                    # Content ID 1
│   │   │   ├── master.m3u8       # Master playlist
│   │   │   ├── 1080p.m3u8        # 1080p variant
│   │   │   ├── 1080p_000.ts      # Video segments
│   │   │   ├── 1080p_001.ts
│   │   │   ├── 720p.m3u8
│   │   │   ├── 720p_000.ts
│   │   │   └── ...
│   │   │
│   │   ├── 2/                    # Content ID 2
│   │   └── ...
│   │
│   └── database/                 # PostgreSQL data
│       └── postgres_data/
│
└── home/
    └── gzjbbk/
        └── signage/
            ├── backend/          # Backend API code
            ├── web-admin/        # Web admin UI code
            ├── viewer/           # TV viewer app code
            └── docker-compose.yml
```

### Database Schema (Content-Related Tables)

```sql
-- Contents table (metadata)
CREATE TABLE contents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    content_type VARCHAR(20) NOT NULL,  -- 'image' or 'video'

    -- Anthias integration
    anthias_url VARCHAR(500) NOT NULL,
    anthias_asset_id VARCHAR(100),

    -- File info
    file_size BIGINT,
    mime_type VARCHAR(100),

    -- Media metadata
    resolution VARCHAR(50),
    width INTEGER,
    height INTEGER,
    codec VARCHAR(50),
    fps FLOAT,
    bitrate INTEGER,
    video_duration FLOAT,

    -- Display settings
    duration INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Content assignments (device/tag relationships)
CREATE TABLE content_assignments (
    id SERIAL PRIMARY KEY,
    content_id INTEGER REFERENCES contents(id) ON DELETE CASCADE,
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_contents_anthias_asset_id ON contents(anthias_asset_id);
CREATE INDEX idx_contents_is_active ON contents(is_active);
CREATE INDEX idx_content_assignments_content_id ON content_assignments(content_id);
CREATE INDEX idx_content_assignments_device_id ON content_assignments(device_id);
CREATE INDEX idx_content_assignments_tag_id ON content_assignments(tag_id);
```

---

## Deployment Architecture

### Docker Services

```
┌────────────────────────────────────────────────────────────────┐
│                    Docker Compose Stack                         │
└────────────────────────────────────────────────────────────────┘

┌──────────────────────┐    ┌──────────────────────┐
│  signage-backend     │    │  signage-postgres    │
│  (Port 8001)         │───▶│  (Port 5433)         │
│                      │    │                      │
│  Image: python:3.12  │    │  Image: postgres:15  │
│  Framework: FastAPI  │    │  Volume: db_data     │
│  Volumes:            │    └──────────────────────┘
│  - ./backend:/app    │              │
│  - /data:/data       │              │
└──────────┬───────────┘              │
           │                          │
           │                          ▼
           │              ┌──────────────────────┐
           │              │  Redis               │
           │              │  (Port 6379)         │
           └─────────────▶│                      │
                          │  Image: redis:7      │
                          │  Volume: redis_data  │
                          └──────────────────────┘


Anthias (Separate Docker Stack):
┌──────────────────────┐
│  anthias-nginx       │
│  (Port 8000)         │
│                      │
│  Anthias Screenly    │
│  Volume: /data       │
└──────────────────────┘
```

### Network Flow

```
External Clients              Server Network              Internal Services
     │                             │                            │
     │                             │                            │
┌────▼─────┐              ┌────────▼────────┐        ┌────────▼────────┐
│ Browser  │──────────────│  192.168.5.12   │        │ Docker Network  │
│ TV App   │  HTTP/HTTPS  │  (Server IP)    │        │ (Internal)      │
└──────────┘              └─────────────────┘        └─────────────────┘
     │                             │                          │
     │                             │                          │
     ├─────────────────────────────┼──────────────────────────┤
     │                             │                          │
     │  Port 3000                  │                          │
     │  Web Admin UI               │                          │
     │                             │                          │
     │  Port 8001                  │                   backend-api:8001
     │  Backend API                │                   └─────┬──────┘
     │                             │                          │
     │  Port 8000                  │                   anthias:8000
     │  Anthias Storage            │                          │
     │                             │                          │
     │  Port 8080                  │                          │
     │  TV Viewer                  │                          │
     │                             │                          │
     │  Port 5433                  │                   postgres:5432
     │  PostgreSQL                 │                   (mapped to 5433)
     │                             │                          │
     └─────────────────────────────┴──────────────────────────┘
```

---

## Error Handling Flow

### Upload Error Handling

```
┌──────────────────────────────────────────────────────────────┐
│                  UPLOAD ERROR SCENARIOS                       │
└──────────────────────────────────────────────────────────────┘

Scenario 1: Invalid File Type
────────────────────────────────
User ──▶ Backend ──X──▶ Anthias
           │
           └──▶ 400 Bad Request
                "Unsupported file type"


Scenario 2: Anthias Connection Failed
──────────────────────────────────────
User ──▶ Backend ──X──▶ Anthias (offline)
           │
           └──▶ 503 Service Unavailable
                "Cannot connect to Anthias"


Scenario 3: Anthias Upload Failed (Step 1)
───────────────────────────────────────────
User ──▶ Backend ──▶ Anthias
                     POST /file_asset ──X
           │
           └──▶ 500 Internal Server Error
                "Failed to upload file to Anthias"


Scenario 4: Anthias Asset Creation Failed (Step 2)
───────────────────────────────────────────────────
User ──▶ Backend ──▶ Anthias
                     POST /file_asset ──✓
                     POST /assets ──X
           │
           ├──▶ File uploaded but asset not created
           │    (orphaned file in Anthias)
           │
           └──▶ 500 Internal Server Error
                "Failed to create asset in Anthias"


Scenario 5: Database Save Failed
─────────────────────────────────
User ──▶ Backend ──▶ Anthias ──✓
           │         (file & asset created)
           │
           ├──▶ PostgreSQL ──X
           │    (constraint violation, etc.)
           │
           ├──▶ Rollback: Delete asset from Anthias
           │
           └──▶ 500 Internal Server Error
                "Upload failed" + details


Scenario 6: Success with Anthias Sync Warning
──────────────────────────────────────────────
User ──▶ Backend ──▶ Anthias ──✓
           │         (upload success)
           │
           ├──▶ PostgreSQL ──✓
           │    (metadata saved)
           │
           ├──▶ Anthias update ──X
           │    (optional sync failed)
           │
           └──▶ 200 OK (success)
                Log: "Anthias sync failed (non-critical)"
```

### Serving Error Handling

```
┌──────────────────────────────────────────────────────────────┐
│                  SERVING ERROR SCENARIOS                      │
└──────────────────────────────────────────────────────────────┘

Scenario 1: Content Not Found in Database
──────────────────────────────────────────
Viewer ──▶ Backend ──▶ PostgreSQL ──X
             │         (content_id not found)
             │
             └──▶ 404 Not Found
                  "Content with ID X not found"


Scenario 2: No Anthias Asset ID
────────────────────────────────
Viewer ──▶ Backend ──▶ PostgreSQL ──✓
             │         (but anthias_asset_id is NULL)
             │
             └──▶ 404 Not Found
                  "Content has no associated Anthias asset"


Scenario 3: Anthias Asset Not Found
────────────────────────────────────
Viewer ──▶ Backend ──▶ Anthias ──X
             │         GET /assets/{id}/content
             │         (asset deleted from Anthias)
             │
             └──▶ 404 Not Found
                  "Asset not found in Anthias"


Scenario 4: Anthias Connection Failed
──────────────────────────────────────
Viewer ──▶ Backend ──X──▶ Anthias (offline)
             │
             └──▶ 503 Service Unavailable
                  "Cannot connect to Anthias service"
```

### Deletion Error Handling

```
┌──────────────────────────────────────────────────────────────┐
│                  DELETION ERROR SCENARIOS                     │
└──────────────────────────────────────────────────────────────┘

Scenario 1: Content Not Found
──────────────────────────────
Admin ──▶ Backend ──▶ PostgreSQL ──X
            │         (content_id not found)
            │
            └──▶ 404 Not Found
                 "Content with ID X not found"


Scenario 2: Anthias Delete Failed (Non-Critical)
─────────────────────────────────────────────────
Admin ──▶ Backend ──▶ Anthias ──X
            │         (asset already deleted or error)
            │
            ├──▶ Log warning
            │    "Anthias delete failed (continuing)"
            │
            ├──▶ PostgreSQL ──✓
            │    (delete metadata anyway)
            │
            └──▶ 200 OK (success)
                 "Content deleted successfully"


Scenario 3: Database Constraint Violation
──────────────────────────────────────────
Admin ──▶ Backend ──▶ Anthias ──✓
            │         (asset deleted)
            │
            ├──▶ PostgreSQL ──X
            │    (foreign key constraint, etc.)
            │
            ├──▶ Rollback attempted
            │    (can't restore Anthias file)
            │
            └──▶ 500 Internal Server Error
                 "Delete failed" + details
                 WARNING: Orphaned Anthias asset
```

---

## Conclusion

This architecture provides:

✅ **Separation of Concerns**
- Backend API: Business logic & orchestration
- Anthias: File storage & serving
- PostgreSQL: Metadata & relationships

✅ **Scalability**
- Stateless backend (horizontal scaling)
- Anthias handles file serving load
- Database optimized with indexes

✅ **Reliability**
- PostgreSQL as single source of truth
- Graceful degradation (Anthias failures logged, not fatal)
- Comprehensive error handling

✅ **Performance**
- Redis caching for frequent queries
- Async operations throughout
- Efficient file serving via Anthias

✅ **Maintainability**
- Clear component boundaries
- Well-documented flows
- Standard API patterns (Quick Wins)

For implementation details, see:
- **Integration Summary:** `/ANTHIAS_INTEGRATION_SUMMARY.md`
- **API Guide:** `/ANTHIAS_API_GUIDE.md`
- **API Docs (Swagger):** `http://192.168.5.12:8001/docs`
