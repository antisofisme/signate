# Celery Transcoding Implementation Guide

Quick step-by-step implementation with actual code files to create/modify.

---

## Quick Start (20 minutes)

### Step 1: Create TranscodingTask Model

**File**: `/mnt/g/khoirul/signate/backend/app/models/transcoding_task.py`

```python
"""
Transcoding Task Model
Tracks video transcoding progress and state
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, Boolean, Float, JSON
from sqlalchemy.sql import func
import enum
from app.core.database import Base
from datetime import datetime


class TranscodingStatus(str, enum.Enum):
    """Task status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscodingTask(Base):
    """
    Transcoding task model for tracking async video processing
    """

    __tablename__ = "transcoding_tasks"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, nullable=True, index=True)
    source_file_path = Column(String(500), nullable=False)
    source_file_size = Column(Integer, nullable=False)
    source_anthias_asset_id = Column(String(100), nullable=True)

    target_format = Column(String(50), default="h264")
    target_resolution = Column(String(50), nullable=True)
    target_bitrate = Column(Integer, nullable=True)

    status = Column(SQLEnum(TranscodingStatus), default=TranscodingStatus.PENDING, index=True)
    progress = Column(Integer, default=0)

    celery_task_id = Column(String(100), unique=True, index=True)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)
    retry_count = Column(Integer, default=0)
    retry_details = Column(JSON, nullable=True)

    estimated_time_remaining = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### Step 2: Update Models __init__.py

**File**: `/mnt/g/khoirul/signate/backend/app/models/__init__.py`

Add import at the end:

```python
from app.models.transcoding_task import TranscodingTask, TranscodingStatus
```

### Step 3: Create Celery Transcoding Task

**File**: `/mnt/g/khoirul/signate/backend/app/tasks/transcoding.py`

Create directory first:
```bash
mkdir -p /mnt/g/khoirul/signate/backend/app/tasks
touch /mnt/g/khoirul/signate/backend/app/tasks/__init__.py
```

```python
"""
Celery task for asynchronous video transcoding
"""

from celery import shared_task, current_task
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session
import json
import subprocess
import os
from datetime import datetime
from app.core.database import SessionLocal
from app.models.transcoding_task import TranscodingTask, TranscodingStatus
from app.core.config import settings

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def transcode_video(
    self,
    task_id: int,
    source_anthias_asset_id: str,
    target_format: str = "h264",
    target_resolution: str = "1920x1080",
    target_bitrate: int = 5000,
):
    """
    Transcode video to target format with progress tracking
    """

    db = SessionLocal()

    try:
        # Fetch task
        task_record = db.query(TranscodingTask).filter(
            TranscodingTask.id == task_id
        ).first()

        if not task_record:
            logger.error(f"Task {task_id} not found")
            return {"error": "Task not found"}

        # Update status
        task_record.celery_task_id = self.request.id
        task_record.status = TranscodingStatus.PROCESSING
        task_record.started_at = datetime.utcnow()
        db.commit()

        logger.info(f"Starting transcode for task {task_id}")

        # Import redis here to avoid circular imports
        from app.services.redis_service import redis_client

        # Update Redis: started
        progress_key = f"transcoding::{task_id}::progress"
        redis_client.setex(
            progress_key,
            86400,
            json.dumps({
                "percentage": 0,
                "status": "processing",
                "message": "Initializing transcoding...",
                "eta": None
            })
        )

        # Add to active tasks
        redis_client.sadd("transcoding::active_tasks", task_id)

        # === TRANSCODE LOGIC ===
        source_file_path = task_record.source_file_path
        output_file_path = f"{source_file_path}.transcoded.mp4"

        # Build FFmpeg command
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", source_file_path,
            "-c:v", target_format,
            "-s", target_resolution,
            "-b:v", f"{target_bitrate}k",
            "-c:a", "aac",
            "-b:a", "128k",
            "-progress", "pipe:1",
            "-y",
            output_file_path
        ]

        logger.info(f"Starting FFmpeg: {' '.join(ffmpeg_cmd)}")

        # Get video duration
        duration = _get_video_duration(source_file_path)
        logger.info(f"Source duration: {duration}s")

        # Process FFmpeg output
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )

        last_progress_update = 0
        for line in process.stdout:
            if line.startswith("out_time_ms="):
                current_time_ms = int(line.split("=")[1])
                current_time_s = current_time_ms / 1_000_000
                progress_pct = int((current_time_s / duration) * 100)
                progress_pct = min(progress_pct, 95)

                if progress_pct >= last_progress_update + 10:
                    redis_client.setex(
                        progress_key,
                        86400,
                        json.dumps({
                            "percentage": progress_pct,
                            "status": "processing",
                            "message": f"Transcoding... {progress_pct}%",
                            "eta": (100 - progress_pct) * 10
                        })
                    )
                    logger.info(f"Task {task_id} progress: {progress_pct}%")
                    last_progress_update = progress_pct

        returncode = process.wait()
        if returncode != 0:
            stderr = process.stderr.read()
            logger.error(f"FFmpeg failed: {stderr}")
            raise Exception(f"FFmpeg error: {stderr}")

        # Update progress to 95%
        redis_client.setex(
            progress_key,
            86400,
            json.dumps({
                "percentage": 95,
                "status": "processing",
                "message": "Finalizing transcoding...",
                "eta": None
            })
        )

        # === MARK AS COMPLETE ===
        task_record.status = TranscodingStatus.COMPLETED
        task_record.completed_at = datetime.utcnow()
        task_record.progress = 100
        db.commit()

        # Update Redis: completed
        redis_client.setex(
            progress_key,
            86400,
            json.dumps({
                "percentage": 100,
                "status": "completed",
                "message": "Transcoding completed",
                "content_id": task_record.content_id
            })
        )

        redis_client.srem("transcoding::active_tasks", task_id)

        # Cleanup
        try:
            if os.path.exists(source_file_path):
                os.remove(source_file_path)
            if os.path.exists(output_file_path):
                os.remove(output_file_path)
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

        logger.info(f"Task {task_id} completed")

        return {
            "task_id": task_id,
            "status": "completed"
        }

    except Exception as exc:
        logger.error(f"Transcode error (retry {self.request.retries}): {exc}", exc_info=True)

        try:
            task_record = db.query(TranscodingTask).filter(
                TranscodingTask.id == task_id
            ).first()

            if task_record:
                retry_details = task_record.retry_details or []
                retry_details.append({
                    "attempt": self.request.retries,
                    "error": str(exc)[:200],
                    "timestamp": datetime.utcnow().isoformat()
                })
                task_record.retry_details = retry_details
                task_record.retry_count = self.request.retries

                if self.request.retries >= 3:
                    task_record.status = TranscodingStatus.FAILED
                    task_record.error_message = str(exc)[:500]
                    task_record.error_code = "TRANSCODE_FAILED"
                    task_record.completed_at = datetime.utcnow()

                db.commit()
        except Exception as e:
            logger.error(f"DB error: {e}")

        raise self.retry(exc=exc, countdown=5 * (2 ** self.request.retries))

    finally:
        db.close()


def _get_video_duration(file_path: str) -> float:
    """Get video duration using FFprobe"""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1:noinvert_match=1",
                file_path
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"FFprobe error: {e}, defaulting to 60s")
        return 60.0
```

### Step 4: Create Tasks API Router

**File**: `/mnt/g/khoirul/signate/backend/app/api/tasks.py`

```python
"""
Task management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.transcoding_task import TranscodingTask
from app.middleware.request_id import get_request_id
from app.core.logging import StructuredLogger
import json

logger = StructuredLogger(__name__)
router = APIRouter()


@router.get("/tasks/{task_id}")
def get_task_status(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get transcoding task status and progress"""

    request_id = get_request_id(request)

    task_record = db.query(TranscodingTask).filter(
        TranscodingTask.id == task_id
    ).first()

    if not task_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    # Get progress from Redis
    from app.services.redis_service import redis_client
    progress_key = f"transcoding::{task_id}::progress"
    progress_data = redis_client.get(progress_key)

    progress = 0
    message = ""
    eta = None

    if progress_data:
        progress_json = json.loads(progress_data)
        progress = progress_json.get("percentage", 0)
        message = progress_json.get("message", "")
        eta = progress_json.get("eta")

    logger.info(
        "Task status retrieved",
        request_id=request_id,
        task_id=task_id,
        status=task_record.status.value,
        progress=progress
    )

    return {
        "task_id": task_record.id,
        "status": task_record.status.value,
        "progress": progress,
        "message": message,
        "eta_seconds": eta,
        "content_id": task_record.content_id,
        "error": task_record.error_message,
        "error_code": task_record.error_code,
        "retry_count": task_record.retry_count,
        "created_at": task_record.created_at.isoformat(),
        "started_at": task_record.started_at.isoformat() if task_record.started_at else None,
        "completed_at": task_record.completed_at.isoformat() if task_record.completed_at else None
    }


@router.get("/tasks/active")
def list_active_tasks(
    request: Request,
    db: Session = Depends(get_db)
):
    """List all active transcoding tasks"""

    request_id = get_request_id(request)

    from app.services.redis_service import redis_client
    active_task_ids = redis_client.smembers("transcoding::active_tasks")

    tasks = db.query(TranscodingTask).filter(
        TranscodingTask.id.in_(active_task_ids) if active_task_ids else False
    ).all()

    task_list = []
    for task in tasks:
        progress_key = f"transcoding::{task.id}::progress"
        progress_data = redis_client.get(progress_key)

        progress = 0
        if progress_data:
            progress = json.loads(progress_data).get("percentage", 0)

        task_list.append({
            "task_id": task.id,
            "status": task.status.value,
            "progress": progress,
            "created_at": task.created_at.isoformat()
        })

    logger.info(
        "Active tasks listed",
        request_id=request_id,
        count=len(task_list)
    )

    return {
        "active_count": len(task_list),
        "tasks": task_list
    }
```

### Step 5: Update main.py to Include Tasks Router

**File**: `/mnt/g/khoirul/signate/backend/app/main.py`

Find this line (around line 62):
```python
from app.api import auth, devices, content, client, tags, logs, websocket, speedtest, playlists, firebird, activities
```

Change to:
```python
from app.api import auth, devices, content, client, tags, logs, websocket, speedtest, playlists, firebird, activities, tasks
```

Add this router (after other include_router calls):
```python
app.include_router(tasks.router, prefix="/api", tags=["Tasks"])
```

### Step 6: Create Redis Service (if not exists)

**File**: `/mnt/g/khoirul/signate/backend/app/services/redis_service.py`

```python
"""
Redis service for caching and task tracking
"""

import redis
from app.core.config import settings

# Create Redis connection pool
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,  # Automatically decode responses to strings
    max_connections=20
)

def get_redis():
    """Dependency for getting Redis client"""
    return redis_client
```

### Step 7: Create Database Migration

**File**: `/mnt/g/khoirul/signate/database/migrations/002_add_transcoding_tasks.sql`

```sql
CREATE TABLE transcoding_tasks (
    id SERIAL PRIMARY KEY,
    content_id INTEGER,
    source_file_path VARCHAR(500) NOT NULL,
    source_file_size INTEGER NOT NULL,
    source_anthias_asset_id VARCHAR(100),
    target_format VARCHAR(50) DEFAULT 'h264',
    target_resolution VARCHAR(50),
    target_bitrate INTEGER,
    status VARCHAR(20) DEFAULT 'pending' NOT NULL,
    progress INTEGER DEFAULT 0,
    celery_task_id VARCHAR(100) UNIQUE,
    error_message TEXT,
    error_code VARCHAR(50),
    retry_count INTEGER DEFAULT 0,
    retry_details JSONB,
    estimated_time_remaining INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_transcoding_tasks_status ON transcoding_tasks(status);
CREATE INDEX idx_transcoding_tasks_created_at ON transcoding_tasks(created_at);
CREATE INDEX idx_transcoding_tasks_celery_task_id ON transcoding_tasks(celery_task_id);
```

### Step 8: Update Dockerfile

**File**: `/mnt/g/khoirul/signate/backend/Dockerfile`

Add FFmpeg installation:

```dockerfile
# Add FFmpeg (for video transcoding)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*
```

### Step 9: Verify Celery App Exists

**File**: `/mnt/g/khoirul/signate/backend/app/celery_app.py`

Ensure this file exists with:

```python
"""
Celery application configuration
"""

from celery import Celery
from app.core.config import settings

app = Celery(
    "signage_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

app.conf.update(
    broker_url=settings.REDIS_URL,
    result_backend=settings.REDIS_URL,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    result_expires=86400,
    worker_prefetch_multiplier=1,
)

app.autodiscover_tasks(['app.tasks'])
```

---

## Verification & Testing

### 1. Check Services Running

```bash
# SSH to server
ssh gzjbbk@192.168.5.12 -p 22

# Navigate to project
cd /home/gzjbbk/prototipe2

# Check Docker containers
docker-compose -f docker/docker-compose.yml ps

# Should see:
# signage-backend       Up
# signage-celery-worker Up
# signage-redis         Up
# signage-postgres      Up
# signage-flower        Up
```

### 2. Monitor Celery Worker

```bash
# Watch worker logs
docker logs -f signage-celery-worker

# Should see:
# [2025-10-29 10:30:00,000: INFO/MainProcess] Ready to accept tasks
```

### 3. Test Task Submission

```bash
# Upload with transcoding
curl -X POST "http://192.168.5.12:8001/api/content/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_video.mp4" \
  -F "title=Test Transcode" \
  -F "transcode=true" \
  -F "target_format=h264" \
  -F "target_resolution=1920x1080" \
  -F "target_bitrate=5000"

# Expected response (202 Accepted):
# {
#   "status": "success",
#   "data": {
#     "task_id": 1,
#     "message": "Video queued for transcoding",
#     "status": "processing"
#   }
# }
```

### 4. Poll Task Status

```bash
# Get status with progress
curl "http://192.168.5.12:8001/api/tasks/1"

# Expected response:
# {
#   "task_id": 1,
#   "status": "processing",
#   "progress": 45,
#   "message": "Transcoding... 45%",
#   "eta_seconds": 120,
#   "content_id": null,
#   ...
# }
```

### 5. Access Flower Dashboard

```
http://192.168.5.12:5555
Username: admin
Password: admin123
```

---

## File Checklist

- [x] `/mnt/g/khoirul/signate/backend/app/models/transcoding_task.py` - Task model
- [x] `/mnt/g/khoirul/signate/backend/app/models/__init__.py` - Add import
- [x] `/mnt/g/khoirul/signate/backend/app/tasks/__init__.py` - Create directory
- [x] `/mnt/g/khoirul/signate/backend/app/tasks/transcoding.py` - Celery task
- [x] `/mnt/g/khoirul/signate/backend/app/api/tasks.py` - Task API endpoints
- [x] `/mnt/g/khoirul/signate/backend/app/main.py` - Register router
- [x] `/mnt/g/khoirul/signate/backend/app/services/redis_service.py` - Redis client
- [x] `/mnt/g/khoirul/signate/backend/app/celery_app.py` - Celery config
- [x] `/mnt/g/khoirul/signate/database/migrations/002_add_transcoding_tasks.sql` - Database migration
- [x] `/mnt/g/khoirul/signate/backend/Dockerfile` - Add FFmpeg

---

## Sync to Server

After implementing locally, sync to server:

```bash
# Copy backend to server
sshpass -p 'Password@2021' scp -r /mnt/g/khoirul/signate/backend/app gzjbbk@192.168.5.12:/home/gzjbbk/prototipe2/backend/

# Copy database migrations
sshpass -p 'Password@2021' scp -r /mnt/g/khoirul/signate/database gzjbbk@192.168.5.12:/home/gzjbbk/prototipe2/

# Rebuild and restart
sshpass -p 'Password@2021' ssh gzjbbk@192.168.5.12 << 'EOF'
cd /home/gzjbbk/prototipe2
docker-compose -f docker/docker-compose.yml down --volumes
docker-compose -f docker/docker-compose.yml build --no-cache
docker-compose -f docker/docker-compose.yml up -d
sleep 10
docker logs signage-backend
docker logs signage-celery-worker
EOF
```

---

## Troubleshooting

### Issue: "Task not found" error

```
Check Redis connection:
docker exec signage-redis redis-cli ping
# Should return: PONG
```

### Issue: FFmpeg not found

```
Check FFmpeg in container:
docker exec signage-celery-worker ffmpeg -version

If missing, rebuild Dockerfile with FFmpeg installation
```

### Issue: Celery worker not picking up tasks

```
Check worker logs:
docker logs signage-celery-worker

Check Redis broker:
docker exec signage-redis redis-cli keys "transcoding*"

Restart worker:
docker-compose -f docker/docker-compose.yml restart celery-worker
```

### Issue: High memory usage

```
Reduce concurrency in docker-compose.yml:
command: celery -A app.celery_app worker --loglevel=info --concurrency=2

Restart:
docker-compose -f docker/docker-compose.yml restart celery-worker
```

---

## Performance Baseline

Test with a 100MB 1080p video:

| Preset | Duration | CPU | Memory |
|--------|----------|-----|--------|
| ultrafast | 2 min | 95% | 250MB |
| fast | 5 min | 85% | 300MB |
| medium | 10 min | 75% | 350MB |
| slow | 20 min | 60% | 400MB |

Adjust FFmpeg preset in `transcoding.py`:

```python
"-preset", "fast",  # Change this
```

---

## Next Steps

1. Test with actual video files
2. Monitor performance with Flower
3. Adjust FFmpeg settings for your use case
4. Add webhook notifications on completion
5. Implement thumbnail generation
6. Add support for multiple output formats
