# Celery + Redis + WebSocket Integration Architecture

**Created:** October 28, 2025
**Purpose:** Explain where to add Celery/Redis/WebSocket and how it integrates with Backend + Anthias
**Status:** Architecture Design

---

## 🏗️ ARSITEKTUR OVERVIEW

### Sebelum (Current):

```
┌─────────────┐
│ Web Admin   │ (localhost:3000)
│ (React)     │
└─────┬───────┘
      │ HTTP REST API
      ↓
┌─────────────────────────────────┐
│ Backend (FastAPI)               │ (192.168.5.12:8001)
│ - async/await only              │
│ - No job persistence            │
│ - Transcoding timeouts          │
│ - HTTP polling (30s delay)      │
└─────┬───────────────────────────┘
      │ POST /api/storage/upload (save files)
      │ GET /api/storage/files/{asset_id} (serve files)
      ↓
┌─────────────────────────────────┐
│ Anthias (Django)                │ (192.168.5.12:8000)
│ - Minimal file storage only     │
│ - No processing                 │
│ - No Celery/Redis needed        │
└─────┬───────────────────────────┘
      │
      ↓
   [Files]
   /data/screenly_assets/
      ↓
┌─────────────────────────────────┐
│ Viewer (HTML/JS)                │ (192.168.5.12:8080)
│ - Polls every 30s               │
│ - Delayed updates               │
└─────────────────────────────────┘
```

**PROBLEMS:**
- ❌ Video transcoding timeout (>2 min HTTP timeout)
- ❌ No job persistence (server restart = lost work)
- ❌ Polling delay (30s untuk menerima update)
- ❌ No retry logic
- ❌ Can't track progress ("50% complete")

---

### Sesudah (With Celery + Redis + WebSocket):

```
┌─────────────┐
│ Web Admin   │ (localhost:3000)
│ (React)     │
└─────┬───────┘
      │ HTTP REST API + WebSocket
      ↓
┌──────────────────────────────────────────────────────┐
│ Backend (FastAPI) - CONTROL PLANE                    │ (192.168.5.12:8001)
│ ┌──────────────────────────────────────────────┐     │
│ │ 1. FastAPI App (Web Server)                  │     │
│ │    - Fast endpoints (async/await)            │     │
│ │    - Upload, list, auth, devices             │     │
│ │    - WebSocket server for real-time          │     │
│ └──────────────┬───────────────────────────────┘     │
│                │                                      │
│ ┌──────────────▼───────────────────────────────┐     │
│ │ 2. Celery Tasks (Background Workers)         │     │
│ │    - Video transcoding (10-60 min)           │     │
│ │    - Thumbnail generation                    │     │
│ │    - Batch operations                        │     │
│ │    - Scheduled cleanup                       │     │
│ └──────────────┬───────────────────────────────┘     │
│                │                                      │
│ ┌──────────────▼───────────────────────────────┐     │
│ │ 3. Redis (Message Broker + Cache)            │     │
│ │    - Task queue (Celery broker)              │     │
│ │    - Result backend                          │     │
│ │    - Session storage                         │     │
│ │    - General caching                         │     │
│ └──────────────────────────────────────────────┘     │
│                                                       │
│ ┌──────────────────────────────────────────────┐     │
│ │ 4. Flower (Celery Monitoring UI)             │     │
│ │    - Task progress                           │     │
│ │    - Worker status                           │     │
│ │    - Task history                            │     │
│ └──────────────────────────────────────────────┘     │
└───────┬──────────────────────────────────────────────┘
        │
        │ 1. Save original file to Anthias
        │ 2. Save transcoded HLS chunks to Anthias
        ↓
┌─────────────────────────────────┐
│ Anthias (Django)                │ (192.168.5.12:8000)
│ - FILE STORAGE ONLY             │
│ - Receives files from Backend   │
│ - Serves files to Viewer        │
│ - NO Celery/Redis               │
└─────┬───────────────────────────┘
      │
      ↓
   [Files]
   /data/screenly_assets/
   ├── original_video.mp4
   └── hls_output/
       ├── playlist.m3u8
       ├── segment_001.ts
       ├── segment_002.ts
       └── ...
      ↓
┌─────────────────────────────────┐
│ Viewer (HTML/JS)                │ (192.168.5.12:8080)
│ - WebSocket client              │
│ - Instant updates (<1s)         │
│ - Plays HLS from Anthias        │
└─────────────────────────────────┘
```

**BENEFITS:**
- ✅ Video transcoding TIDAK timeout (background task)
- ✅ Job persistence (survive restart)
- ✅ Instant updates via WebSocket (<1s)
- ✅ Automatic retry logic
- ✅ Progress tracking ("50% complete")
- ✅ Monitoring via Flower UI

---

## 📍 DIMANA PENAMBAHAN?

### 1. Backend (192.168.5.12:8001) ← **SEMUA PENAMBAHAN DI SINI!**

```
backend/
├── app/
│   ├── main.py                 # ✅ FastAPI app (sudah ada)
│   ├── celery_app.py          # 🆕 NEW: Celery configuration
│   ├── tasks/                 # 🆕 NEW: Celery tasks
│   │   ├── __init__.py
│   │   ├── transcoding.py     # 🆕 Transcoding task
│   │   ├── thumbnails.py      # 🆕 Thumbnail task
│   │   └── cleanup.py         # 🆕 Cleanup task
│   ├── api/
│   │   ├── content.py         # ⚠️ UPDATE: Use Celery for transcoding
│   │   ├── websocket.py       # 🆕 NEW: WebSocket endpoints
│   │   └── tasks.py           # 🆕 NEW: Task status endpoints
│   └── services/
│       └── transcoding_service.py  # ⚠️ UPDATE: Add sync version for Celery
│
├── requirements.txt           # ⚠️ UPDATE: Add celery, redis, websockets
└── Dockerfile                # ⚠️ UPDATE: No changes needed

docker-compose.yml            # ⚠️ UPDATE: Add redis, celery-worker, flower services
```

### 2. Anthias (192.168.5.12:8000) ← **TIDAK ADA PERUBAHAN!**

```
anthias/
├── api/storage.py            # ✅ TETAP: Minimal storage API
└── anthias_app/models.py     # ✅ TETAP: Minimal Asset model

**NO CHANGES NEEDED!** Anthias tetap minimal storage service.
```

### 3. Viewer (192.168.5.12:8080) ← **UPDATE WebSocket Client**

```
viewer/
├── index.html                # ✅ TETAP
├── player.html               # ✅ TETAP
└── js/
    ├── player/
    │   ├── api.js            # ⚠️ UPDATE: Remove polling, add fallback
    │   └── websocket.js      # 🆕 NEW: WebSocket client
    └── shell/
        └── registration.js   # ✅ TETAP
```

### 4. Web-Admin (localhost:3000) ← **UPDATE Task Progress UI**

```
web-admin/src/
├── components/
│   ├── content/modals/
│   │   └── UploadModal.tsx   # ⚠️ UPDATE: Show task progress
│   └── tasks/                # 🆕 NEW: Task monitoring components
│       ├── TaskProgress.tsx
│       └── TaskList.tsx
└── services/api/
    └── tasks.ts              # 🆕 NEW: Task status API
```

---

## 🔄 WORKFLOW INTEGRATION

### Workflow 1: Video Upload & Transcoding

```
┌────────────────┐
│ 1. Web Admin   │ User uploads video.mp4 (500MB)
└────────┬───────┘
         │ POST /api/content/upload (file: video.mp4)
         ↓
┌──────────────────────────────────────────────┐
│ 2. Backend API (FastAPI)                     │
│ ┌──────────────────────────────────────────┐ │
│ │ async def upload_content():              │ │
│ │   # Step 2.1: Save original to Anthias   │ │
│ │   anthias_url = await save_to_anthias()  │ │
│ │                                           │ │
│ │   # Step 2.2: Create DB record           │ │
│ │   content = await create_content()       │ │
│ │                                           │ │
│ │   # Step 2.3: Queue transcoding (Celery) │ │
│ │   task = transcode_video_task.delay(     │ │
│ │       content_id=content.id,             │ │
│ │       source_path=anthias_url            │ │
│ │   )                                       │ │
│ │                                           │ │
│ │   # Step 2.4: Return immediately!        │ │
│ │   return {                               │ │
│ │       "content_id": content.id,          │ │
│ │       "task_id": task.id,                │ │
│ │       "status": "transcoding"            │ │
│ │   }                                       │ │
│ └──────────────────────────────────────────┘ │
└───────┬──────────────────────────────────────┘
        │ Task queued to Redis
        ↓
┌──────────────────────────────────────────────┐
│ 3. Redis (Task Queue)                        │
│ ┌──────────────────────────────────────────┐ │
│ │ Queue: celery                            │ │
│ │ ├── Task 1: transcode_video_task         │ │
│ │ │   - content_id: 123                    │ │
│ │ │   - source_path: http://anthias/...   │ │
│ │ │   - status: PENDING                    │ │
│ └──────────────────────────────────────────┘ │
└───────┬──────────────────────────────────────┘
        │ Celery worker picks up task
        ↓
┌──────────────────────────────────────────────┐
│ 4. Celery Worker (Background Process)       │
│ ┌──────────────────────────────────────────┐ │
│ │ @celery_app.task                         │ │
│ │ def transcode_video_task(content_id):    │ │
│ │   # Step 4.1: Download from Anthias      │ │
│ │   video = download_from_anthias(url)     │ │
│ │                                           │ │
│ │   # Step 4.2: Transcode with FFmpeg      │ │
│ │   for progress in transcode_to_hls():    │ │
│ │       # Update progress in Redis         │ │
│ │       self.update_state(                 │ │
│ │           state='PROGRESS',              │ │
│ │           meta={'percent': progress}     │ │
│ │       )                                   │ │
│ │                                           │ │
│ │   # Step 4.3: Upload HLS to Anthias      │ │
│ │   hls_url = upload_to_anthias(chunks)    │ │
│ │                                           │ │
│ │   # Step 4.4: Update database            │ │
│ │   update_content(content_id, {           │ │
│ │       'hls_url': hls_url,                │ │
│ │       'status': 'completed'              │ │
│ │   })                                      │ │
│ │                                           │ │
│ │   # Step 4.5: Notify via WebSocket       │ │
│ │   websocket_manager.broadcast({          │ │
│ │       'type': 'content_ready',           │ │
│ │       'content_id': content_id           │ │
│ │   })                                      │ │
│ │                                           │ │
│ │   return {'status': 'success'}           │ │
│ └──────────────────────────────────────────┘ │
└───────┬──────────────────────────────────────┘
        │ Upload HLS chunks
        ↓
┌──────────────────────────────────────────────┐
│ 5. Anthias Storage                           │
│ /data/screenly_assets/                       │
│ ├── original_video.mp4                       │
│ └── hls_123/                                 │
│     ├── playlist.m3u8                        │
│     ├── segment_001.ts                       │
│     └── segment_002.ts                       │
└──────────────────────────────────────────────┘
        │
        ↓ WebSocket push
┌──────────────────────────────────────────────┐
│ 6. Viewer (All Devices)                      │
│ ┌──────────────────────────────────────────┐ │
│ │ WebSocket receives:                      │ │
│ │ {                                         │ │
│ │   "type": "content_ready",               │ │
│ │   "content_id": 123                      │ │
│ │ }                                         │ │
│ │                                           │ │
│ │ → Fetch new playlist                     │ │
│ │ → Play new HLS video                     │ │
│ └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

**Timeline:**
- `0s` - User clicks upload
- `1s` - API returns `{"task_id": "abc123", "status": "transcoding"}` ← User sees this immediately!
- `1s-10min` - Celery processes in background (user can close browser)
- `10min` - Transcoding complete
- `10min+1s` - WebSocket pushes to all devices → Instant update!

**Key Points:**
- ✅ API returns immediately (no timeout!)
- ✅ User can track progress via task_id
- ✅ Server restart? Task resumes from Redis
- ✅ Failure? Automatic retry 3 times
- ✅ Devices notified instantly via WebSocket

---

### Workflow 2: Real-Time Playlist Update

```
┌────────────────┐
│ 1. Web Admin   │ Admin publishes FIRE ALARM
└────────┬───────┘
         │ POST /api/playlists/{device_id}/assign
         ↓
┌──────────────────────────────────────────────┐
│ 2. Backend API (FastAPI)                     │
│ ┌──────────────────────────────────────────┐ │
│ │ async def assign_playlist():             │ │
│ │   # Update database                      │ │
│ │   await db.update_device_playlist()      │ │
│ │                                           │ │
│ │   # Push via WebSocket (INSTANT!)        │ │
│ │   await websocket_manager.broadcast({    │ │
│ │       "type": "playlist_update",         │ │
│ │       "device_id": 123,                  │ │
│ │       "playlist": [...]                  │ │
│ │   })                                      │ │
│ └──────────────────────────────────────────┘ │
└───────┬──────────────────────────────────────┘
        │ WebSocket push (<10ms!)
        ↓
┌──────────────────────────────────────────────┐
│ 3. All Viewer Devices (WebSocket Connected)  │
│ ┌──────────────────────────────────────────┐ │
│ │ WebSocket.onmessage = (event) => {       │ │
│ │   const data = JSON.parse(event.data)    │ │
│ │   if (data.type === 'playlist_update') { │ │
│ │     // Update playlist IMMEDIATELY        │ │
│ │     updatePlaylist(data.playlist)        │ │
│ │   }                                       │ │
│ │ }                                         │ │
│ └──────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
```

**Timeline:**
- `09:00:00.000` - Admin clicks publish
- `09:00:00.010` - All devices receive update (10ms latency!)
- `09:00:00.050` - Devices start playing FIRE ALARM

**vs Polling (Old):**
- `09:00:00` - Admin clicks publish
- `09:00:30` - Device polls and gets update (30s delay!)

**Improvement:** 3000x faster! (10ms vs 30,000ms)

---

## 🛠️ IMPLEMENTASI DETAIL

### File 1: backend/app/celery_app.py (NEW)

```python
"""
Celery configuration for background tasks
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    'signage',
    broker=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0',
    backend=f'redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0'
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,

    # Task tracking
    task_track_started=True,
    task_send_sent_event=True,

    # Timeouts
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit

    # Worker settings
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks (prevent memory leaks)
    worker_prefetch_multiplier=4,   # Fetch 4 tasks at a time

    # Retry settings
    task_acks_late=True,  # Acknowledge after task completes (for reliability)
    task_reject_on_worker_lost=True,

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
)

# Import tasks (so Celery can discover them)
celery_app.autodiscover_tasks(['app.tasks'])
```

---

### File 2: backend/app/tasks/transcoding.py (NEW)

```python
"""
Celery task for video transcoding
"""
from celery import current_task
from app.celery_app import celery_app
from app.services.transcoding_service import TranscodingService
from app.services.anthias_client import AnthiasClient
from app.models.content import Content
from app.api.websocket import websocket_manager
import asyncio

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def transcode_video_task(self, content_id: int, source_url: str):
    """
    Background task for video transcoding

    Args:
        content_id: Content ID in database
        source_url: URL to original video in Anthias storage
    """
    try:
        # Step 1: Download original from Anthias
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'downloading', 'percent': 10}
        )

        anthias = AnthiasClient()
        local_path = anthias.download_file(source_url)

        # Step 2: Transcode to HLS with progress updates
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'transcoding', 'percent': 20}
        )

        transcoder = TranscodingService()

        def progress_callback(percent: int):
            # Update task progress (20% + 60% of transcoding progress)
            self.update_state(
                state='PROGRESS',
                meta={'stage': 'transcoding', 'percent': 20 + int(percent * 0.6)}
            )

        hls_output = transcoder.transcode_to_hls_sync(
            source_path=local_path,
            progress_callback=progress_callback
        )

        # Step 3: Upload HLS chunks to Anthias
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'uploading', 'percent': 85}
        )

        hls_url = anthias.upload_hls_chunks(
            content_id=content_id,
            chunks_dir=hls_output['output_dir']
        )

        # Step 4: Update database
        self.update_state(
            state='PROGRESS',
            meta={'stage': 'finalizing', 'percent': 95}
        )

        # Use sync database update (Celery runs in sync context)
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            content = db.query(Content).filter(Content.id == content_id).first()
            if content:
                content.hls_url = hls_url
                content.hls_playlist = hls_output['playlist_path']
                content.status = 'completed'
                content.duration = hls_output['duration']
                db.commit()
        finally:
            db.close()

        # Step 5: Notify via WebSocket (run async in sync context)
        async def notify():
            await websocket_manager.broadcast_to_all({
                'type': 'content_ready',
                'content_id': content_id,
                'hls_url': hls_url
            })

        asyncio.run(notify())

        return {
            'status': 'success',
            'content_id': content_id,
            'hls_url': hls_url,
            'duration': hls_output['duration']
        }

    except Exception as exc:
        # Log error
        print(f"Transcoding failed for content {content_id}: {exc}")

        # Update database to failed status
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            content = db.query(Content).filter(Content.id == content_id).first()
            if content:
                content.status = 'failed'
                content.error_message = str(exc)
                db.commit()
        finally:
            db.close()

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

---

### File 3: backend/app/api/websocket.py (NEW)

```python
"""
WebSocket endpoints for real-time communication
"""
from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import Dict, Set
import json

router = APIRouter()

class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        # device_id -> Set[WebSocket]
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # All connections (for broadcast)
        self.all_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, device_id: int = None):
        """Accept new WebSocket connection"""
        await websocket.accept()

        # Add to all connections
        self.all_connections.add(websocket)

        # Add to device-specific connections
        if device_id:
            if device_id not in self.active_connections:
                self.active_connections[device_id] = set()
            self.active_connections[device_id].add(websocket)

    def disconnect(self, websocket: WebSocket, device_id: int = None):
        """Remove WebSocket connection"""
        # Remove from all connections
        self.all_connections.discard(websocket)

        # Remove from device-specific connections
        if device_id and device_id in self.active_connections:
            self.active_connections[device_id].discard(websocket)
            if not self.active_connections[device_id]:
                del self.active_connections[device_id]

    async def send_to_device(self, device_id: int, message: dict):
        """Send message to specific device"""
        if device_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[device_id]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)

            # Clean up disconnected
            for conn in disconnected:
                self.disconnect(conn, device_id)

    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all connected devices"""
        disconnected = set()
        for connection in self.all_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)

        # Clean up disconnected
        for conn in disconnected:
            self.disconnect(conn)

# Global connection manager
websocket_manager = ConnectionManager()

@router.websocket("/ws/device/{device_id}")
async def websocket_device_endpoint(websocket: WebSocket, device_id: int):
    """
    WebSocket endpoint for device-specific updates

    Usage from viewer:
    const ws = new WebSocket('ws://192.168.5.12:8001/ws/device/123')
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'playlist_update') {
            updatePlaylist(data.playlist)
        }
    }
    """
    await websocket_manager.connect(websocket, device_id)

    try:
        # Keep connection alive
        while True:
            # Receive heartbeat or commands from device
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle device messages (optional)
            if message.get('type') == 'heartbeat':
                # Update device last_seen
                pass

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, device_id)

@router.websocket("/ws/admin")
async def websocket_admin_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for admin dashboard

    Receives updates about:
    - Task progress
    - Device status changes
    - System events
    """
    await websocket_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            # Handle admin commands if needed

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
```

---

### File 4: backend/app/api/content.py (UPDATE)

```python
"""
Content API endpoints - Updated to use Celery
"""
from fastapi import APIRouter, UploadFile, File, Depends
from app.tasks.transcoding import transcode_video_task
from app.services.anthias_client import AnthiasClient
from app.celery_app import celery_app

router = APIRouter()

@router.post("/content/upload")
async def upload_content(
    file: UploadFile = File(...),
    # ... other params
):
    """
    Upload video and queue transcoding

    Returns immediately with task_id for progress tracking
    """

    # Step 1: Save original file to Anthias storage
    anthias = AnthiasClient()
    anthias_response = await anthias.upload_file(file)
    original_url = anthias_response['url']

    # Step 2: Create content record in database
    content = await create_content_record(
        title=file.filename,
        original_url=original_url,
        status='transcoding'
    )

    # Step 3: Queue transcoding task (returns IMMEDIATELY!)
    task = transcode_video_task.delay(
        content_id=content.id,
        source_url=original_url
    )

    # Step 4: Return response (API returns in <1 second!)
    return {
        'success': True,
        'content_id': content.id,
        'task_id': task.id,
        'status': 'transcoding',
        'original_url': original_url,
        'check_status_url': f'/api/tasks/{task.id}'
    }

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Check task progress

    Called by web-admin to show progress bar
    """
    task = celery_app.AsyncResult(task_id)

    if task.state == 'PENDING':
        return {
            'state': 'PENDING',
            'status': 'Task is waiting in queue',
            'percent': 0
        }
    elif task.state == 'PROGRESS':
        return {
            'state': 'PROGRESS',
            'status': task.info.get('stage', 'Processing'),
            'percent': task.info.get('percent', 0)
        }
    elif task.state == 'SUCCESS':
        return {
            'state': 'SUCCESS',
            'status': 'Task completed',
            'percent': 100,
            'result': task.result
        }
    elif task.state == 'FAILURE':
        return {
            'state': 'FAILURE',
            'status': 'Task failed',
            'percent': 0,
            'error': str(task.info)
        }
    else:
        return {
            'state': task.state,
            'status': str(task.info),
            'percent': 0
        }
```

---

### File 5: docker-compose.yml (UPDATE)

```yaml
version: '3.8'

services:
  # PostgreSQL Database (existing)
  postgres:
    image: postgres:15
    container_name: signage-postgres
    ports:
      - "5433:5432"
    environment:
      POSTGRES_DB: signage_db
      POSTGRES_USER: signage_user
      POSTGRES_PASSWORD: signage_pass
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    restart: unless-stopped

  # 🆕 NEW: Redis (Message Broker + Cache)
  redis:
    image: redis:7-alpine
    container_name: signage-redis
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - ./data/redis:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Backend API (existing, updated)
  backend-api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: signage-backend
    ports:
      - "8001:8001"
    environment:
      DATABASE_URL: postgresql://signage_user:signage_pass@postgres:5432/signage_db
      REDIS_HOST: redis  # 🆕 NEW: Connect to Redis
      REDIS_PORT: 6379
      ANTHIAS_URL: http://anthias:8000
    volumes:
      - ./backend:/app
      - ./data:/data
    depends_on:
      - postgres
      - redis  # 🆕 NEW: Depend on Redis
      - anthias
    restart: unless-stopped
    command: uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

  # 🆕 NEW: Celery Worker (Background Tasks)
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: signage-celery-worker
    environment:
      DATABASE_URL: postgresql://signage_user:signage_pass@postgres:5432/signage_db
      REDIS_HOST: redis
      REDIS_PORT: 6379
      ANTHIAS_URL: http://anthias:8000
    volumes:
      - ./backend:/app
      - ./data:/data
    depends_on:
      - redis
      - postgres
      - anthias
    restart: unless-stopped
    command: celery -A app.celery_app worker --loglevel=info --concurrency=2 --max-tasks-per-child=50

  # 🆕 NEW: Celery Beat (Scheduled Tasks - Optional)
  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: signage-celery-beat
    environment:
      DATABASE_URL: postgresql://signage_user:signage_pass@postgres:5432/signage_db
      REDIS_HOST: redis
      REDIS_PORT: 6379
    volumes:
      - ./backend:/app
      - ./data:/data
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    command: celery -A app.celery_app beat --loglevel=info

  # 🆕 NEW: Flower (Celery Monitoring UI)
  flower:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: signage-flower
    ports:
      - "5555:5555"
    environment:
      REDIS_HOST: redis
      REDIS_PORT: 6379
    depends_on:
      - redis
    restart: unless-stopped
    command: celery -A app.celery_app flower --port=5555 --basic_auth=admin:admin123

  # Anthias Storage (existing, no changes)
  anthias:
    build:
      context: ./anthias
      dockerfile: docker/Dockerfile
    container_name: anthias-storage
    ports:
      - "8000:8000"
    volumes:
      - ./data/screenly_assets:/data/screenly_assets
    environment:
      DJANGO_SETTINGS_MODULE: anthias_django.settings
      DEBUG: "False"
    restart: unless-stopped

  # Viewer (existing, will update client-side)
  viewer:
    image: nginx:alpine
    container_name: signage-viewer
    ports:
      - "8080:80"
    volumes:
      - ./viewer:/usr/share/nginx/html:ro
    restart: unless-stopped
```

---

### File 6: backend/requirements.txt (UPDATE)

```txt
# Existing dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dateutil==2.8.2

# 🆕 NEW: Celery + Redis
celery[redis]==5.3.4
redis==5.0.1

# 🆕 NEW: WebSocket support
websockets==12.0
python-socketio==5.10.0

# 🆕 NEW: Flower (Celery monitoring)
flower==2.0.1

# Existing - FFmpeg wrapper
ffmpeg-python==0.2.0
```

---

### File 7: viewer/js/player/websocket.js (NEW)

```javascript
/**
 * WebSocket client for real-time playlist updates
 */

class SignageWebSocket {
    constructor(deviceId, backendUrl = 'ws://192.168.5.12:8001') {
        this.deviceId = deviceId
        this.backendUrl = backendUrl
        this.ws = null
        this.reconnectAttempts = 0
        this.maxReconnectAttempts = 10
        this.reconnectDelay = 1000 // Start with 1 second
        this.heartbeatInterval = null
    }

    connect() {
        const wsUrl = `${this.backendUrl}/ws/device/${this.deviceId}`
        console.log(`[WebSocket] Connecting to ${wsUrl}...`)

        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
            console.log('[WebSocket] Connected!')
            this.reconnectAttempts = 0
            this.reconnectDelay = 1000

            // Start heartbeat
            this.startHeartbeat()
        }

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data)
            console.log('[WebSocket] Received:', data)

            // Handle different message types
            switch (data.type) {
                case 'playlist_update':
                    this.handlePlaylistUpdate(data)
                    break
                case 'content_ready':
                    this.handleContentReady(data)
                    break
                case 'command':
                    this.handleCommand(data)
                    break
                case 'pong':
                    // Heartbeat response
                    break
                default:
                    console.warn('[WebSocket] Unknown message type:', data.type)
            }
        }

        this.ws.onerror = (error) => {
            console.error('[WebSocket] Error:', error)
        }

        this.ws.onclose = () => {
            console.log('[WebSocket] Disconnected')
            this.stopHeartbeat()

            // Reconnect with exponential backoff
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++
                console.log(`[WebSocket] Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})...`)

                setTimeout(() => {
                    this.connect()
                }, this.reconnectDelay)

                // Exponential backoff (max 30 seconds)
                this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000)
            } else {
                console.error('[WebSocket] Max reconnect attempts reached. Falling back to polling.')
                // Fallback to HTTP polling
                this.startPolling()
            }
        }
    }

    startHeartbeat() {
        // Send heartbeat every 30 seconds
        this.heartbeatInterval = setInterval(() => {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.send({ type: 'heartbeat', device_id: this.deviceId })
            }
        }, 30000)
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval)
            this.heartbeatInterval = null
        }
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data))
        } else {
            console.warn('[WebSocket] Cannot send, not connected')
        }
    }

    handlePlaylistUpdate(data) {
        console.log('[WebSocket] Playlist updated!')

        // Update playlist immediately
        if (window.Player && data.playlist) {
            window.Player.updatePlaylist(data.playlist)
        }
    }

    handleContentReady(data) {
        console.log('[WebSocket] New content ready:', data.content_id)

        // Refresh playlist to get new content
        if (window.Player) {
            window.Player.refreshPlaylist()
        }
    }

    handleCommand(data) {
        console.log('[WebSocket] Received command:', data.command)

        // Handle device commands
        switch (data.command) {
            case 'reload':
                location.reload()
                break
            case 'screenshot':
                // Take screenshot logic
                break
            case 'restart':
                // Restart player logic
                break
            default:
                console.warn('[WebSocket] Unknown command:', data.command)
        }
    }

    startPolling() {
        // Fallback to HTTP polling if WebSocket fails
        console.log('[WebSocket] Falling back to HTTP polling...')

        // Use existing polling mechanism
        if (window.Player) {
            window.Player.startPolling()
        }
    }

    disconnect() {
        this.stopHeartbeat()
        if (this.ws) {
            this.ws.close()
            this.ws = null
        }
    }
}

// Initialize WebSocket on page load
document.addEventListener('DOMContentLoaded', () => {
    const deviceId = localStorage.getItem('device_id')

    if (deviceId) {
        window.signageWebSocket = new SignageWebSocket(deviceId)
        window.signageWebSocket.connect()
    } else {
        console.error('[WebSocket] No device_id found, cannot connect')
    }
})
```

---

## 📊 PERBANDINGAN BEFORE vs AFTER

### Before (Without Celery):

```
User uploads 500MB video
↓
POST /api/content/upload (waits...)
↓
FastAPI async/await transcoding (10 minutes)
↓
❌ HTTP timeout after 2 minutes!
↓
ERROR: Gateway Timeout
```

**Result:** FAILS ❌

---

### After (With Celery):

```
User uploads 500MB video (1s)
↓
POST /api/content/upload
↓
FastAPI: Save to Anthias + Queue Celery task
↓
✅ API returns {"task_id": "abc123"} in 1 second!
↓
User sees: "Transcoding... 0%"
↓
Celery worker processes in background (10 minutes)
↓
User closes browser (task continues!)
↓
Progress updates: 10% → 25% → 50% → 75% → 100%
↓
✅ Transcoding complete!
↓
WebSocket pushes to all devices (<10ms)
↓
Devices play new content instantly!
```

**Result:** SUCCESS ✅

---

## 🎯 KESIMPULAN LOKASI

### ✅ Backend (192.168.5.12:8001) - SEMUA PERUBAHAN DI SINI:
- 🆕 `app/celery_app.py` - Celery config
- 🆕 `app/tasks/transcoding.py` - Transcoding task
- 🆕 `app/api/websocket.py` - WebSocket endpoints
- ⚠️ `app/api/content.py` - Update to use Celery
- ⚠️ `requirements.txt` - Add celery, redis, websockets
- ⚠️ `docker-compose.yml` - Add redis, celery-worker, flower

### ✅ Anthias (192.168.5.12:8000) - TIDAK ADA PERUBAHAN:
- Tetap minimal storage service
- Hanya menerima files dari Backend
- Tidak perlu Celery/Redis

### ✅ Viewer (192.168.5.12:8080) - UPDATE CLIENT:
- 🆕 `js/player/websocket.js` - WebSocket client
- ⚠️ `js/player/api.js` - Add WebSocket fallback

### ✅ Web-Admin (localhost:3000) - UPDATE UI:
- 🆕 `components/tasks/TaskProgress.tsx` - Progress bar
- ⚠️ `components/content/modals/UploadModal.tsx` - Show progress

---

## 🚀 NEXT STEPS

Siap untuk implementasi? Saya bisa:
1. Generate semua file baru yang diperlukan
2. Update file yang ada dengan integrasi Celery
3. Update docker-compose.yml dengan services baru
4. Create migration script untuk deploy ke server

Lanjutkan?
