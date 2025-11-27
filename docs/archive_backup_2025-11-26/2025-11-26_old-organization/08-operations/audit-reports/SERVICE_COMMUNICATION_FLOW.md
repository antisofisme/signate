# Service Communication Flow Diagrams

**Visual Reference for Integration Audit**

---

## 1. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         INTERNET                                 │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         │ HTTPS
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│                   LOAD BALANCER / NGINX                          │
│                   (Optional - Future)                            │
└────────────────────────┬─────────────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          │              │              │
┌─────────▼─────┐ ┌──────▼──────┐ ┌────▼─────────┐
│  Web Admin    │ │   Viewer    │ │   WebOS TV   │
│ (localhost:   │ │ (port 8080) │ │   App        │
│   3000)       │ │             │ │ (webos-local)│
└───────┬───────┘ └──────┬──────┘ └────┬─────────┘
        │                │             │
        │ HTTP/REST      │ HTTP/REST   │ HTTP/REST
        │ WebSocket      │ WebSocket   │ WebSocket
        │                │             │
        └────────────────┼─────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────────┐
│              BACKEND API (FastAPI - Port 8001)                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  API Routers:                                              │  │
│  │  auth • devices • content • playlists • tags • settings   │  │
│  │  client • firebird • analytics • templates • commands     │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Middleware:                                               │  │
│  │  Request ID • Logging • CORS • Streaming • Exception      │  │
│  └────────────────────────────────────────────────────────────┘  │
└──┬────────────────┬────────────────┬────────────────┬───────────┘
   │                │                │                │
   │ SQLAlchemy     │ Redis Py       │ httpx          │ Celery
   │ ORM            │                │                │
   │                │                │                │
┌──▼────────┐  ┌────▼────┐  ┌────────▼──────┐  ┌─────▼──────┐
│PostgreSQL │  │  Redis  │  │    Anthias    │  │   Celery   │
│(port 5433)│  │(port    │  │  (port 8000)  │  │   Workers  │
│           │  │  6379)  │  │               │  │            │
│ Metadata  │  │ Cache   │  │ File Storage  │  │ Background │
│ Relations │  │ Broker  │  │ File Serving  │  │   Tasks    │
└───────────┘  └─────────┘  └───────────────┘  └────────────┘
```

---

## 2. Content Upload Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                      UPLOAD JOURNEY                                    │
└────────────────────────────────────────────────────────────────────────┘

Step 1: User Uploads File
──────────────────────────
┌─────────────┐
│  Web Admin  │
│             │  User selects video/image
│  [Browse]   │  ────────────┐
│  [Upload]   │              │
└─────────────┘              │
                             │
                             ▼
                    ┌────────────────┐
                    │  File Selected │
                    │  - video.mp4   │
                    │  - 50 MB       │
                    └────────────────┘

Step 2: POST Request to Backend
────────────────────────────────
┌─────────────┐
│  Web Admin  │  POST /api/content/upload
└──────┬──────┘  Content-Type: multipart/form-data
       │         {
       │           file: [binary data],
       │           title: "Product Demo",
       │           description: "New product showcase",
       │           duration: 30,
       │           transcode_on_upload: true
       │         }
       │
       ▼
┌──────────────────────────────────────────────────────┐
│            Backend API (content.py)                  │
├──────────────────────────────────────────────────────┤
│ ✓ Validate file type                                │
│ ✓ Check file size (max 100 MB)                      │
│ ✓ Extract metadata:                                 │
│   - Video: ffprobe (duration, resolution, codec)    │
│   - Image: PIL (dimensions, format)                 │
│ ✓ Generate thumbnail (for videos)                   │
└──────────────────────────────────────────────────────┘
       │
       │
       ▼
Step 3: Upload to Anthias Storage
──────────────────────────────────
┌──────────────────────────────────────────────────────┐
│          anthias_service.upload_asset()              │
├──────────────────────────────────────────────────────┤
│ Step 3a: POST /api/v1/file_asset                     │
│   ├─→ Upload binary file                            │
│   └─→ Receive URI: "/data/screenly_assets/xyz.mp4" │
│                                                      │
│ Step 3b: POST /api/v1/assets                         │
│   ├─→ Create asset with URI                         │
│   └─→ Receive anthias_asset_id: "abc123"           │
└──────────────────────────────────────────────────────┘
       │
       │ Return anthias_asset_id
       ▼
┌──────────────────────────────────────────────────────┐
│      Backend Saves to PostgreSQL                    │
├──────────────────────────────────────────────────────┤
│ INSERT INTO content (                                │
│   title,                                             │
│   description,                                       │
│   duration,                                          │
│   mime_type,                                         │
│   file_size,                                         │
│   anthias_asset_id,  ← Link to Anthias              │
│   file_path,                                         │
│   transcoding_status  ← "pending"                   │
│ )                                                    │
└──────────────────────────────────────────────────────┘
       │
       │ Invalidate cache
       │ Return ContentResponse
       ▼
┌─────────────┐
│  Web Admin  │  Receives:
└─────────────┘  {
                   "success": true,
                   "data": {
                     "id": 42,
                     "title": "Product Demo",
                     "anthias_asset_id": "abc123",
                     "transcoding_status": "pending"
                   },
                   "meta": {
                     "request_id": "xyz789",
                     "timestamp": "2025-10-28T10:00:00Z"
                   }
                 }

Step 4: Background Transcoding (Async)
───────────────────────────────────────
IF transcode_on_upload = true:

┌──────────────────────────────────────────────────────┐
│     Celery Task: transcode_video_task                │
├──────────────────────────────────────────────────────┤
│ 1. Download video from Anthias                      │
│ 2. FFmpeg transcode to HLS (multiple qualities):    │
│    ├─→ /data/hls/42/1080p/playlist.m3u8            │
│    ├─→ /data/hls/42/720p/playlist.m3u8             │
│    ├─→ /data/hls/42/480p/playlist.m3u8             │
│    └─→ /data/hls/42/360p/playlist.m3u8             │
│ 3. Update PostgreSQL:                                │
│    ├─→ hls_playlist_url = "/data/hls/42/..."       │
│    └─→ transcoding_status = "completed"            │
│ 4. Publish WebSocket event: "content_transcoded"    │
└──────────────────────────────────────────────────────┘
       │
       │ WebSocket notification
       ▼
┌─────────────┐
│  Web Admin  │  Receives real-time update
└─────────────┘  Status changes: pending → completed
                 Button appears: "View HLS"
```

---

## 3. Content Playback Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                    PLAYBACK JOURNEY                                    │
└────────────────────────────────────────────────────────────────────────┘

Step 1: Device Requests Playlist
─────────────────────────────────
┌─────────────┐
│   Viewer    │  GET /api/client/playlist
│  (Monitor)  │      ?device_id=12345
└──────┬──────┘      &language=en
       │
       │
       ▼
┌──────────────────────────────────────────────────────┐
│       Backend API (client.py)                        │
├──────────────────────────────────────────────────────┤
│ 1. Validate device_id                                │
│ 2. Check device is activated                         │
│ 3. Query assigned playlists (by priority)            │
│ 4. Query assigned content (by priority)              │
│ 5. Build playlist response with URLs                 │
└──────────────────────────────────────────────────────┘
       │
       │ Database queries
       ▼
┌──────────────────────────────────────────────────────┐
│           PostgreSQL Queries                         │
├──────────────────────────────────────────────────────┤
│ SELECT * FROM devices WHERE id = 12345               │
│ SELECT * FROM playlist_assignments                   │
│   WHERE device_id = 12345                            │
│   ORDER BY priority DESC                             │
│ SELECT * FROM content                                │
│   JOIN content_assignments                           │
│   WHERE device_id = 12345                            │
│   ORDER BY priority DESC                             │
└──────────────────────────────────────────────────────┘
       │
       │
       ▼
Step 2: Backend Builds Response
────────────────────────────────
┌──────────────────────────────────────────────────────┐
│     For Each Content Item:                           │
├──────────────────────────────────────────────────────┤
│ IF content.hls_playlist_url EXISTS:                  │
│   ├─→ Use HLS adaptive streaming                    │
│   └─→ URL: http://192.168.5.12:8001/data/hls/...   │
│                                                      │
│ ELSE IF content.mime_type = "video":                 │
│   ├─→ Use Anthias direct video                      │
│   └─→ URL: http://192.168.5.12:8000/screenly_...   │
│                                                      │
│ ELSE (image):                                        │
│   ├─→ Use Anthias direct image                      │
│   └─→ URL: http://192.168.5.12:8000/screenly_...   │
└──────────────────────────────────────────────────────┘
       │
       │ Apply translations (if language != 'en')
       │
       ▼
┌─────────────┐
│   Viewer    │  Receives playlist:
└─────────────┘  {
                   "playlist": [
                     {
                       "content_id": 42,
                       "title": "Product Demo",
                       "type": "video",
                       "duration": 30,
                       "url": "http://192.168.5.12:8001/data/hls/42/playlist.m3u8",
                       "mime_type": "video/mp4"
                     },
                     {
                       "content_id": 43,
                       "title": "Company Logo",
                       "type": "image",
                       "duration": 10,
                       "url": "http://192.168.5.12:8000/screenly_assets/logo.png",
                       "mime_type": "image/png"
                     }
                   ]
                 }

Step 3: Viewer Plays Content
─────────────────────────────

┌─────────────────────────────────────────────────────────────────┐
│         Path A: HLS Video (Adaptive Streaming)                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. Initialize HLS.js player                                     │
│ 2. Request master playlist:                                     │
│    GET /data/hls/42/playlist.m3u8                               │
│                                                                 │
│ 3. Backend streaming middleware serves:                         │
│    ├─→ Supports HTTP Range requests                           │
│    ├─→ Bandwidth throttling (10 MB/s)                         │
│    └─→ Analytics tracking                                      │
│                                                                 │
│ 4. Player auto-selects quality:                                 │
│    └─→ 720p (based on bandwidth)                              │
│                                                                 │
│ 5. Request video segments:                                      │
│    GET /data/hls/42/720p/segment_001.ts                        │
│    GET /data/hls/42/720p/segment_002.ts                        │
│    GET /data/hls/42/720p/segment_003.ts                        │
│    ... (continues)                                              │
│                                                                 │
│ 6. Player switches quality dynamically:                         │
│    └─→ 480p (if bandwidth drops)                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│      Path B: Direct Media (Image/Legacy Video)                  │
├─────────────────────────────────────────────────────────────────┤
│ 1. Request file from Anthias:                                   │
│    GET http://192.168.5.12:8000/screenly_assets/logo.png       │
│                                                                 │
│ 2. Anthias Nginx serves file directly                           │
│    ├─→ No backend involvement                                  │
│    ├─→ No analytics tracking                                   │
│    └─→ Simple HTTP file serving                                │
│                                                                 │
│ 3. Viewer displays image for specified duration                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Device Registration Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                 DEVICE REGISTRATION JOURNEY                            │
└────────────────────────────────────────────────────────────────────────┘

Step 1: Monitor Generates Code
───────────────────────────────
┌─────────────┐
│   Monitor   │  On startup, generate 6-digit code
│  (Browser)  │  POST /api/devices/monitor
└──────┬──────┘  {
       │           "device_name": "Lobby TV",
       │           "location": "Main Lobby"
       │         }
       │
       ▼
┌──────────────────────────────────────────────────────┐
│       Backend API (devices.py)                       │
├──────────────────────────────────────────────────────┤
│ 1. Generate random 6-digit code: "482719"           │
│ 2. Set expiry: now + 5 minutes                       │
│ 3. Create pending device record:                     │
│    ├─→ device_type: "monitor"                       │
│    ├─→ status: "pending"                            │
│    ├─→ activation_code: "482719"                    │
│    └─→ activation_code_expiry: timestamp            │
│ 4. Return code to monitor                            │
└──────────────────────────────────────────────────────┘
       │
       │
       ▼
┌─────────────┐
│   Monitor   │  Displays code on screen:
└─────────────┘  ┌─────────────────────┐
                 │  Activation Code:   │
                 │      482719         │
                 │                     │
                 │  Enter this code    │
                 │  in Web Admin       │
                 └─────────────────────┘

Step 2: Monitor Polls for Activation
─────────────────────────────────────
┌─────────────┐
│   Monitor   │  Every 5 seconds:
└──────┬──────┘  POST /api/devices/monitor/activate
       │         {
       │           "activation_code": "482719"
       │         }
       │
       │  ┌──────────────────────────────┐
       │  │ Loop every 5 seconds         │
       │  │ Timeout after 5 minutes      │
       │  └──────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│       Backend API (devices.py)                       │
├──────────────────────────────────────────────────────┤
│ 1. Find device by activation_code                    │
│ 2. Check if activated:                               │
│    ├─→ NOT YET: Return 404 (keep polling)          │
│    └─→ ACTIVATED: Return device_id                  │
└──────────────────────────────────────────────────────┘

Step 3: Admin Activates Device
───────────────────────────────
┌─────────────┐
│  Web Admin  │  Admin sees pending device:
└──────┬──────┘  ┌──────────────────────────┐
       │         │ Pending Devices          │
       │         │ • Lobby TV               │
       │         │   Code: 482719           │
       │         │   [Activate]             │
       │         └──────────────────────────┘
       │
       │  Admin clicks [Activate]
       │
       ▼
┌──────────────────────────────────────────────────────┐
│       Backend API (devices.py)                       │
├──────────────────────────────────────────────────────┤
│ PUT /api/devices/{id}/activate                       │
│ 1. Find device by id                                 │
│ 2. Update:                                           │
│    ├─→ status: "active"                             │
│    ├─→ activated_at: now                            │
│    └─→ activation_code: null (clear)                │
│ 3. Invalidate cache                                  │
│ 4. Publish WebSocket: "device_activated"            │
└──────────────────────────────────────────────────────┘
       │
       │ WebSocket notification
       ▼
┌─────────────┐
│  Web Admin  │  Dashboard updates real-time
└─────────────┘  Device moves to "Active Devices" list

Step 4: Monitor Receives Activation
────────────────────────────────────
┌─────────────┐
│   Monitor   │  Next poll receives:
└─────────────┘  {
                   "success": true,
                   "device_id": 12345,
                   "message": "Device activated"
                 }
       │
       │ Store device_id in localStorage
       │
       ▼
┌─────────────┐
│   Monitor   │  ┌────────────────────────┐
└─────────────┘  │ ✓ Activated!          │
                 │                        │
                 │ Loading content...     │
                 └────────────────────────┘
       │
       │ Start heartbeat (every 30s)
       │ Load playlist
       ▼
```

---

## 5. Real-time Updates (WebSocket)

```
┌────────────────────────────────────────────────────────────────────────┐
│                    WEBSOCKET COMMUNICATION                             │
└────────────────────────────────────────────────────────────────────────┘

Connection Establishment
────────────────────────
┌─────────────┐
│  Web Admin  │  Connect:
└──────┬──────┘  ws://192.168.5.12:8001/api/ws/dashboard
       │         Authorization: Bearer {jwt_token}
       │
       ▼
┌──────────────────────────────────────────────────────┐
│       Backend WebSocket Handler                      │
├──────────────────────────────────────────────────────┤
│ 1. Validate JWT token                                │
│ 2. Add client to connection pool                     │
│ 3. Subscribe to Redis PubSub channels:               │
│    ├─→ device_events                                │
│    ├─→ content_events                               │
│    └─→ playlist_events                              │
└──────────────────────────────────────────────────────┘

Event Publishing Flow
─────────────────────
Example: Content Upload Complete

┌──────────────────────────────────────────────────────┐
│  Backend API (content.py)                            │
├──────────────────────────────────────────────────────┤
│ After saving content:                                │
│ 1. Publish to Redis:                                 │
│    redis.publish("content_events", {                 │
│      "event": "content_uploaded",                   │
│      "content_id": 42,                              │
│      "title": "New Video"                           │
│    })                                               │
└──────────────────────────────────────────────────────┘
       │
       │ Redis PubSub
       ▼
┌──────────────────────────────────────────────────────┐
│       WebSocket Handler                              │
├──────────────────────────────────────────────────────┤
│ 1. Receive message from Redis                        │
│ 2. Broadcast to all connected clients:               │
│    ws.send_json({                                    │
│      "type": "content_uploaded",                    │
│      "data": {...}                                  │
│    })                                               │
└──────────────────────────────────────────────────────┘
       │
       │ WebSocket message
       ▼
┌─────────────┐
│  Web Admin  │  Receives:
└─────────────┘  {
                   "type": "content_uploaded",
                   "data": {
                     "content_id": 42,
                     "title": "New Video"
                   }
                 }
       │
       │ Update UI without refresh
       ▼
   Content list auto-updates
```

---

## 6. Error Flow Examples

```
┌────────────────────────────────────────────────────────────────────────┐
│                      ERROR HANDLING FLOW                               │
└────────────────────────────────────────────────────────────────────────┘

Scenario A: Resource Not Found
───────────────────────────────
┌─────────────┐
│  Web Admin  │  GET /api/content/999
└──────┬──────┘  (Content ID doesn't exist)
       │
       ▼
┌──────────────────────────────────────────────────────┐
│       Backend API (content.py)                       │
├──────────────────────────────────────────────────────┤
│ db.query(Content).filter(id=999).first()             │
│ └─→ Returns None                                     │
│                                                      │
│ raise NotFoundException(                             │
│   message="Content not found",                      │
│   details={"content_id": 999}                       │
│ )                                                   │
└──────────────────────────────────────────────────────┘
       │
       │ Exception handler catches
       ▼
┌──────────────────────────────────────────────────────┐
│    Exception Handler (Quick Wins Format)             │
├──────────────────────────────────────────────────────┤
│ Return 404 with standardized error:                  │
│ {                                                    │
│   "success": false,                                  │
│   "error": {                                         │
│     "code": "RESOURCE_NOT_FOUND",                   │
│     "message": "Content not found",                 │
│     "field": null,                                   │
│     "details": {                                     │
│       "content_id": 999                             │
│     }                                               │
│   },                                                │
│   "meta": {                                         │
│     "request_id": "abc123",                         │
│     "timestamp": "2025-10-28T10:00:00Z"            │
│   }                                                 │
│ }                                                   │
└──────────────────────────────────────────────────────┘
       │
       │ HTTP 404 response
       ▼
┌─────────────┐
│  Web Admin  │  Axios interceptor transforms:
└─────────────┘  error.response.data = {
                   detail: "Content not found",
                   code: "RESOURCE_NOT_FOUND",
                   content_id: 999
                 }
       │
       │ Component catches
       ▼
   Display toast: "Content not found"


Scenario B: Validation Error
─────────────────────────────
┌─────────────┐
│  Web Admin  │  POST /api/content/upload
└──────┬──────┘  {
       │           title: "",  ← Empty!
       │           file: null  ← Missing!
       │         }
       │
       ▼
┌──────────────────────────────────────────────────────┐
│       Backend API (FastAPI)                          │
├──────────────────────────────────────────────────────┤
│ Pydantic validation fails automatically:             │
│ └─→ title required                                   │
│ └─→ file required                                    │
│                                                      │
│ FastAPI returns 422 Unprocessable Entity             │
└──────────────────────────────────────────────────────┘
       │
       │ HTTP 422 response
       ▼
┌─────────────┐
│  Web Admin  │  Receives validation errors:
└─────────────┘  {
                   "detail": [
                     {
                       "loc": ["body", "title"],
                       "msg": "field required",
                       "type": "value_error.missing"
                     },
                     {
                       "loc": ["body", "file"],
                       "msg": "field required",
                       "type": "value_error.missing"
                     }
                   ]
                 }
       │
       │ Display field-specific errors
       ▼
   Show red borders on empty fields
   Display error messages below inputs
```

---

**End of Flow Diagrams**

For detailed implementation, see:
- **Full Audit Report:** `/docs/audit-reports/integration-audit.md`
- **API Documentation:** `/docs/API_ENDPOINTS_DOCUMENTATION.md`
