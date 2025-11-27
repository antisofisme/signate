# Celery Transcoding - Quick Reference Card

One-page reference for developers.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ CLIENT (Browser / Mobile App)                                       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ↓
                    ┌─────────────────────────┐
                    │   FastAPI Backend       │
                    │   (port 8001)          │
                    │                         │
                    │ POST /api/content/upload
                    │ ├─ Validate file       │
                    │ ├─ Save temporarily    │
                    │ ├─ Create task in DB   │
                    │ ├─ Queue to Redis      │
                    │ └─ Return 202 + task_id
                    │                         │
                    │ GET /api/tasks/{id}     │
                    │ └─ Return progress %   │
                    │                         │
                    │ GET /api/tasks/active   │
                    │ └─ List all active     │
                    └─────────────────────────┘
                        │               │
            ┌───────────┴───────────────┴───────────┐
            │                                       │
            ↓                                       ↓
      ┌──────────────┐                      ┌──────────────┐
      │   Redis      │ ◄──────────────────► │  PostgreSQL  │
      │ (port 6379)  │                      │ (port 5433)  │
      │              │                      │              │
      │ • Broker     │                      │ • Task state │
      │ • Cache      │                      │ • Progress   │
      │ • Results    │                      │ • Errors     │
      └──────────────┘                      └──────────────┘
            ↑
            │ Dequeue
            │
      ┌─────────────────────────────────────────────────────────┐
      │ Celery Worker (4 concurrency)                          │
      │                                                        │
      │ transcode_video(task_id, source, format, res, bitrate)
      │ ├─ Set status = PROCESSING                            │
      │ ├─ Download source video                              │
      │ ├─ Run FFmpeg:                                        │
      │ │  └─ Parse progress → Update Redis every 10%         │
      │ ├─ Upload result to storage                           │
      │ ├─ Create Content in DB                               │
      │ ├─ Set status = COMPLETED                             │
      │ └─ On error: Retry 3x with exponential backoff        │
      └─────────────────────────────────────────────────────────┘
            │
            ↓
      ┌──────────────────┐
      │ FFmpeg Process   │
      │                  │
      │ ffmpeg -i input  │
      │  -c:v h264       │
      │  -s 1920x1080    │
      │  -b:v 5000k      │
      │  -progress pipe:1│
      │  output.mp4      │
      └──────────────────┘
```

---

## Task Lifecycle

```
1. Upload Request
   POST /api/content/upload?transcode=true
   │
   ├─ Validate file → 400 Bad Request
   │
   ├─ Create TranscodingTask (PENDING)
   │   └─ INSERT into DB
   │
   ├─ Queue Celery task
   │   └─ LPUSH to Redis queue
   │
   └─ Response: 202 Accepted + {task_id: 1}


2. Background Processing
   Celery Worker dequeues from Redis
   │
   ├─ Task status = PROCESSING
   ├─ Redis progress = 0%
   │
   ├─ Download source video
   │  └─ Redis progress = 5%
   │
   ├─ Run FFmpeg
   │  ├─ Parse progress: 0s → 10% → 20% ... → 90%
   │  └─ Redis progress updated every 10%
   │
   ├─ On success:
   │  ├─ Upload result
   │  ├─ Create Content in DB
   │  ├─ Task status = COMPLETED
   │  ├─ Redis progress = 100%
   │  └─ Return {task_id, content_id}
   │
   └─ On failure:
      ├─ Retry attempt 1 (after 5s)
      ├─ Retry attempt 2 (after 10s)
      ├─ Retry attempt 3 (after 20s)
      ├─ Task status = FAILED
      └─ Error message stored in DB


3. Progress Polling
   Client polls GET /api/tasks/{task_id}
   │
   ├─ Query DB for task status
   ├─ Query Redis for progress %
   │
   └─ Response: {
        status: "processing",
        progress: 45,
        message: "Transcoding... 45%",
        eta_seconds: 120
      }


4. Completion
   When status = COMPLETED
   │
   ├─ Progress = 100%
   ├─ content_id populated
   ├─ Temp files cleaned up
   │
   └─ Client can now use content_id
```

---

## Database Schema

```
transcoding_tasks table:
┌─────────────────────────────────┐
│ id (PK)                         │ ← Auto-increment
├─────────────────────────────────┤
│ content_id (FK)                 │ ← Filled after transcode
│ source_file_path                │ ← /tmp/upload_xyz.mp4
│ source_file_size                │ ← Bytes
│ source_anthias_asset_id         │ ← Source video asset ID
│ target_format                   │ ← h264, h265, vp9
│ target_resolution               │ ← 1920x1080
│ target_bitrate                  │ ← 5000 kbps
├─────────────────────────────────┤
│ status                          │ ← pending|processing|completed|failed
│ progress                        │ ← 0-100
│ celery_task_id                  │ ← Celery UUID
│ error_message                   │ ← If failed
│ error_code                      │ ← TRANSCODE_FAILED, etc.
│ retry_count                     │ ← 0-3
│ retry_details                   │ ← JSON array of attempts
├─────────────────────────────────┤
│ created_at                      │ ← 2025-10-29 10:30:00
│ started_at                      │ ← 2025-10-29 10:31:00
│ completed_at                    │ ← 2025-10-29 10:45:00
│ updated_at                      │ ← Auto-updated
└─────────────────────────────────┘
```

---

## Redis Key Schema

```
transcoding::{task_id}::progress
  Type: String (JSON)
  Value: {
    "percentage": 45,
    "status": "processing",
    "message": "Transcoding... 45%",
    "eta": 120
  }
  TTL: 24 hours
  Updated: Every 10% progress

transcoding::active_tasks
  Type: Set
  Members: [1, 2, 3, ...]
  TTL: 24 hours
  Purpose: Quick lookup of active task IDs

transcoding::{task_id}::metadata
  Type: String (JSON)
  Value: {
    "source_file_path": "/tmp/upload_xyz.mp4",
    "target_format": "h264",
    "created_at": "2025-10-29T10:30:00Z"
  }
  TTL: 24 hours
  Purpose: Quick task info lookup
```

---

## API Endpoints

### 1. Upload with Transcoding
```
POST /api/content/upload
Content-Type: multipart/form-data

Request:
{
  file: <binary>,
  title: "My Video",
  transcode: true,
  target_format: "h264",
  target_resolution: "1920x1080",
  target_bitrate: 5000
}

Response: 202 Accepted
{
  "status": "success",
  "data": {
    "task_id": 1,
    "message": "Video queued for transcoding"
  }
}
```

### 2. Get Task Status
```
GET /api/tasks/1

Response: 200 OK
{
  "task_id": 1,
  "status": "processing",
  "progress": 45,
  "message": "Transcoding... 45%",
  "eta_seconds": 120,
  "content_id": null,
  "error": null,
  "retry_count": 0,
  "created_at": "2025-10-29T10:30:00Z",
  "started_at": "2025-10-29T10:31:00Z",
  "completed_at": null
}
```

### 3. List Active Tasks
```
GET /api/tasks/active

Response: 200 OK
{
  "active_count": 2,
  "tasks": [
    {
      "task_id": 1,
      "status": "processing",
      "progress": 45,
      "created_at": "2025-10-29T10:30:00Z"
    },
    {
      "task_id": 2,
      "status": "pending",
      "progress": 0,
      "created_at": "2025-10-29T10:35:00Z"
    }
  ]
}
```

### 4. Cancel Task
```
DELETE /api/tasks/1

Response: 204 No Content
```

---

## Code Structure

```
backend/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   └── transcoding_task.py ← NEW
│   │
│   ├── tasks/
│   │   ├── __init__.py ← NEW (directory)
│   │   └── transcoding.py ← NEW (Celery task)
│   │
│   ├── api/
│   │   └── tasks.py ← NEW (API endpoints)
│   │
│   ├── services/
│   │   └── redis_service.py ← NEW (Redis client)
│   │
│   ├── celery_app.py ← NEW or VERIFY
│   ├── main.py ← MODIFY (add router)
│   └── core/
│       ├── config.py (verify Redis URL)
│       └── database.py
│
database/
└── migrations/
    └── 002_add_transcoding_tasks.sql ← NEW

docker/
└── docker-compose.yml (already has celery-worker)

Dockerfile ← MODIFY (add FFmpeg)
```

---

## Configuration

### .env
```bash
# Redis (Celery Broker + Result Backend)
REDIS_URL=redis://redis:6379

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### docker-compose.yml (celery-worker)
```yaml
celery-worker:
  command: celery -A app.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=1000
```

### celery_app.py
```python
app.conf.update(
    broker_url=settings.REDIS_URL,
    result_backend=settings.REDIS_URL,
    task_serializer='json',
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 min
    result_expires=86400,  # 24 hours
)
```

---

## FFmpeg Command

```bash
ffmpeg \
  -i source.mp4 \
  -c:v h264 \           # Video codec (h264, h265, vp9)
  -s 1920x1080 \        # Resolution
  -b:v 5000k \          # Video bitrate
  -c:a aac \            # Audio codec
  -b:a 128k \           # Audio bitrate
  -preset fast \        # Speed preset (ultrafast...veryslow)
  -crf 25 \             # Quality (0-51, lower = better)
  -progress pipe:1 \    # Progress output
  -y output.mp4         # Output file

Progress format:
out_time_ms=1234567  # Milliseconds of video processed
```

---

## Monitoring

### Flower UI
```
URL: http://192.168.5.12:5555
User: admin
Pass: admin123

Shows:
- Active tasks (real-time)
- Task history
- Worker status
- Failed tasks
- Execution times
```

### Docker Logs
```bash
# Worker logs
docker logs -f signage-celery-worker

# Backend logs
docker logs -f signage-backend

# Redis logs
docker logs -f signage-redis
```

### Redis CLI
```bash
# Check keys
docker exec signage-redis redis-cli keys "transcoding*"

# Get progress
docker exec signage-redis redis-cli GET "transcoding::1::progress"

# List active tasks
docker exec signage-redis redis-cli SMEMBERS "transcoding::active_tasks"
```

---

## Troubleshooting

### Problem: "Task not found"
```
Check: Task ID correct?
Check: Database has table?
  → psql -U signage_user -d signage_db -c "SELECT * FROM transcoding_tasks"
Check: Redis connected?
  → redis-cli PING → should return PONG
```

### Problem: "FFmpeg not found"
```
Fix: Update Dockerfile
  RUN apt-get install -y ffmpeg

Rebuild: docker-compose build --no-cache
```

### Problem: High memory usage
```
Fix: Reduce concurrency in docker-compose.yml
  --concurrency=2

Restart: docker-compose restart celery-worker
```

### Problem: Task stuck in PROCESSING
```
Check: Task exists in Redis?
  → redis-cli SMEMBERS "transcoding::active_tasks"

Fix: Remove stuck task
  → redis-cli SREM "transcoding::active_tasks" {task_id}

Restart: docker-compose restart celery-worker
```

---

## Performance Presets

```
FFmpeg Preset Performance (1GB 1080p video):

ultrafast:  2 minutes   (poor quality)
superfast:  3 minutes
veryfast:   4 minutes
faster:     5 minutes
fast:       8 minutes   (good speed/quality balance)
medium:    12 minutes   (default, balanced)
slow:      20 minutes
slower:    30 minutes
veryslow:  40 minutes   (best quality)

Recommended: Use "fast" for real-time, "medium" for archival
```

---

## Retry Logic

```
Attempt 1: Immediate failure
  └─ Wait 5 seconds (5 * 2^1 = 10s with jitter)

Attempt 2: If still fails
  └─ Wait 10 seconds (5 * 2^2 = 20s with jitter)

Attempt 3: If still fails
  └─ Wait 20 seconds (5 * 2^3 = 80s with jitter)

Attempt 4: All retries exhausted
  └─ Mark task as FAILED
  └─ Store error message in DB
  └─ Remove from active_tasks set
```

---

## Status Codes

### Upload Endpoint
- **201 Created**: Image uploaded without transcoding
- **202 Accepted**: Video queued for transcoding
- **400 Bad Request**: Invalid file or parameters
- **500 Internal Server Error**: Upload failed

### Task Status Endpoint
- **200 OK**: Task found, returning status
- **404 Not Found**: Task ID doesn't exist

### Cancel Endpoint
- **204 No Content**: Task cancelled successfully
- **400 Bad Request**: Cannot cancel completed/failed task
- **404 Not Found**: Task ID doesn't exist

---

## Testing Commands

### Test Upload
```bash
curl -X POST "http://192.168.5.12:8001/api/content/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test.mp4" \
  -F "title=Test" \
  -F "transcode=true" \
  -F "target_format=h264" \
  -F "target_resolution=1920x1080" \
  -F "target_bitrate=5000"
```

### Test Status Polling
```bash
# Poll every 2 seconds for 1 minute
for i in {1..30}; do
  curl "http://192.168.5.12:8001/api/tasks/1" | jq '.data | {progress, status, eta_seconds}'
  sleep 2
done
```

### Test Active Tasks
```bash
curl "http://192.168.5.12:8001/api/tasks/active" | jq '.data'
```

---

## Deployment Steps

1. **Create files** (7 new files)
2. **Update imports** (models/__init__.py, main.py)
3. **Create migration** (database schema)
4. **Update Dockerfile** (add FFmpeg)
5. **Rebuild**: `docker-compose build --no-cache`
6. **Restart**: `docker-compose down && docker-compose up -d`
7. **Test**: Use curl commands above

---

## Important Notes

✅ Already configured in your setup:
- Redis (broker + result backend)
- Celery workers (concurrency 4)
- PostgreSQL (for persistence)
- Flower UI (monitoring)
- Docker Compose (orchestration)

✅ This implementation provides:
- Async processing (non-blocking)
- Progress tracking (0-100% real-time)
- Automatic retries (3 times with backoff)
- Error logging (detailed messages)
- Job persistence (survives restart)
- Horizontal scaling (via concurrency)
- Production monitoring (Flower + logs)

---

**For full details, see:**
- CELERY_TRANSCODING_ARCHITECTURE.md (system design)
- CELERY_IMPLEMENTATION_GUIDE.md (step-by-step)
- CELERY_CODE_SNIPPETS.md (ready-to-use code)
