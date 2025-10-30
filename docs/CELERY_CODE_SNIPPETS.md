# Celery Transcoding - Ready-to-Use Code Snippets

Copy-paste ready code for quick integration.

---

## 1. TranscodingTask Model

```python
# /mnt/g/khoirul/signate/backend/app/models/transcoding_task.py

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum, JSON
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TranscodingStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscodingTask(Base):
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

---

## 2. Celery Task - Transcoding Logic

```python
# /mnt/g/khoirul/signate/backend/app/tasks/transcoding.py

from celery import shared_task
from celery.utils.log import get_task_logger
import json
import subprocess
import os
from datetime import datetime
from app.core.database import SessionLocal
from app.models.transcoding_task import TranscodingTask, TranscodingStatus

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
def transcode_video(self, task_id: int, source_anthias_asset_id: str,
                   target_format: str = "h264", target_resolution: str = "1920x1080",
                   target_bitrate: int = 5000):
    """Transcode video to target format with progress tracking"""

    db = SessionLocal()

    try:
        from app.services.redis_service import redis_client

        task_record = db.query(TranscodingTask).filter(TranscodingTask.id == task_id).first()
        if not task_record:
            logger.error(f"Task {task_id} not found")
            return {"error": "Task not found"}

        task_record.celery_task_id = self.request.id
        task_record.status = TranscodingStatus.PROCESSING
        task_record.started_at = datetime.utcnow()
        db.commit()

        logger.info(f"Starting transcode for task {task_id}")

        progress_key = f"transcoding::{task_id}::progress"
        redis_client.setex(progress_key, 86400, json.dumps({
            "percentage": 0,
            "status": "processing",
            "message": "Initializing transcoding...",
            "eta": None
        }))

        redis_client.sadd("transcoding::active_tasks", task_id)

        source_file_path = task_record.source_file_path
        output_file_path = f"{source_file_path}.transcoded.mp4"

        ffmpeg_cmd = [
            "ffmpeg", "-i", source_file_path,
            "-c:v", target_format, "-s", target_resolution,
            "-b:v", f"{target_bitrate}k",
            "-c:a", "aac", "-b:a", "128k",
            "-progress", "pipe:1", "-y", output_file_path
        ]

        logger.info(f"Starting FFmpeg: {' '.join(ffmpeg_cmd)}")

        duration = _get_video_duration(source_file_path)
        logger.info(f"Source duration: {duration}s")

        process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, universal_newlines=True, bufsize=1)

        last_progress_update = 0
        for line in process.stdout:
            if line.startswith("out_time_ms="):
                current_time_ms = int(line.split("=")[1])
                current_time_s = current_time_ms / 1_000_000
                progress_pct = int((current_time_s / duration) * 100)
                progress_pct = min(progress_pct, 95)

                if progress_pct >= last_progress_update + 10:
                    redis_client.setex(progress_key, 86400, json.dumps({
                        "percentage": progress_pct,
                        "status": "processing",
                        "message": f"Transcoding... {progress_pct}%",
                        "eta": (100 - progress_pct) * 10
                    }))
                    logger.info(f"Task {task_id} progress: {progress_pct}%")
                    last_progress_update = progress_pct

        returncode = process.wait()
        if returncode != 0:
            stderr = process.stderr.read()
            logger.error(f"FFmpeg failed: {stderr}")
            raise Exception(f"FFmpeg error: {stderr}")

        redis_client.setex(progress_key, 86400, json.dumps({
            "percentage": 95,
            "status": "processing",
            "message": "Finalizing transcoding...",
            "eta": None
        }))

        task_record.status = TranscodingStatus.COMPLETED
        task_record.completed_at = datetime.utcnow()
        task_record.progress = 100
        db.commit()

        redis_client.setex(progress_key, 86400, json.dumps({
            "percentage": 100,
            "status": "completed",
            "message": "Transcoding completed",
            "content_id": task_record.content_id
        }))

        redis_client.srem("transcoding::active_tasks", task_id)

        try:
            if os.path.exists(source_file_path):
                os.remove(source_file_path)
            if os.path.exists(output_file_path):
                os.remove(output_file_path)
        except Exception as e:
            logger.warning(f"Cleanup error: {e}")

        logger.info(f"Task {task_id} completed")
        return {"task_id": task_id, "status": "completed"}

    except Exception as exc:
        logger.error(f"Transcode error (retry {self.request.retries}): {exc}", exc_info=True)

        try:
            task_record = db.query(TranscodingTask).filter(TranscodingTask.id == task_id).first()
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
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1:noinvert_match=1", file_path],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    except Exception as e:
        logger.warning(f"FFprobe error: {e}, defaulting to 60s")
        return 60.0
```

---

## 3. Tasks API Router

```python
# /mnt/g/khoirul/signate/backend/app/api/tasks.py

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
def get_task_status(task_id: int, request: Request, db: Session = Depends(get_db)):
    """Get transcoding task status and progress"""

    request_id = get_request_id(request)
    task_record = db.query(TranscodingTask).filter(TranscodingTask.id == task_id).first()

    if not task_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found")

    from app.services.redis_service import redis_client
    progress_key = f"transcoding::{task_id}::progress"
    progress_data = redis_client.get(progress_key)

    progress = message = eta = 0
    if progress_data:
        pj = json.loads(progress_data)
        progress = pj.get("percentage", 0)
        message = pj.get("message", "")
        eta = pj.get("eta")

    logger.info("Task status retrieved", request_id=request_id, task_id=task_id, status=task_record.status.value, progress=progress)

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
def list_active_tasks(request: Request, db: Session = Depends(get_db)):
    """List all active transcoding tasks"""

    request_id = get_request_id(request)
    from app.services.redis_service import redis_client

    active_task_ids = redis_client.smembers("transcoding::active_tasks")
    tasks = db.query(TranscodingTask).filter(TranscodingTask.id.in_(active_task_ids) if active_task_ids else False).all()

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

    logger.info("Active tasks listed", request_id=request_id, count=len(task_list))
    return {"active_count": len(task_list), "tasks": task_list}
```

---

## 4. Redis Service

```python
# /mnt/g/khoirul/signate/backend/app/services/redis_service.py

import redis
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, max_connections=20)

def get_redis():
    return redis_client
```

---

## 5. Update Models __init__.py

```python
# Add to /mnt/g/khoirul/signate/backend/app/models/__init__.py

from app.models.transcoding_task import TranscodingTask, TranscodingStatus
```

---

## 6. Update main.py

```python
# In /mnt/g/khoirul/signate/backend/app/main.py

# Line ~62: Add tasks to imports
from app.api import auth, devices, content, client, tags, logs, websocket, speedtest, playlists, firebird, activities, tasks

# Add this router after other include_router calls (around line 72):
app.include_router(tasks.router, prefix="/api", tags=["Tasks"])
```

---

## 7. Create Celery App Config

```python
# /mnt/g/khoirul/signate/backend/app/celery_app.py

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


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
```

---

## 8. Create Tasks Directory

```bash
mkdir -p /mnt/g/khoirul/signate/backend/app/tasks
touch /mnt/g/khoirul/signate/backend/app/tasks/__init__.py
```

---

## 9. Database Migration SQL

```sql
-- /mnt/g/khoirul/signate/database/migrations/002_add_transcoding_tasks.sql

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

---

## 10. Update Dockerfile

```dockerfile
# Add to /mnt/g/khoirul/signate/backend/Dockerfile

# Install FFmpeg (for video transcoding)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*
```

---

## 11. Quick Test Script

```bash
#!/bin/bash
# test_transcoding.sh

SERVER="192.168.5.12"
PORT="8001"

# Upload with transcoding
echo "Uploading video for transcoding..."
RESPONSE=$(curl -s -X POST "http://${SERVER}:${PORT}/api/content/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_video.mp4" \
  -F "title=Test Transcode" \
  -F "transcode=true" \
  -F "target_format=h264" \
  -F "target_resolution=1920x1080" \
  -F "target_bitrate=5000")

echo "Response: $RESPONSE"
TASK_ID=$(echo $RESPONSE | grep -o '"task_id":[0-9]*' | grep -o '[0-9]*')
echo "Task ID: $TASK_ID"

# Poll progress every 5 seconds
for i in {1..60}; do
    STATUS=$(curl -s "http://${SERVER}:${PORT}/api/tasks/${TASK_ID}")
    echo "Progress update $i: $STATUS"
    sleep 5
done
```

---

## 12. Environment Variables (.env)

```bash
# Add/verify in /mnt/g/khoirul/signate/.env

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
REDIS_URL=redis://redis:6379

# For local development
# CELERY_BROKER_URL=redis://localhost:6379/0
# CELERY_RESULT_BACKEND=redis://localhost:6379/0
# REDIS_URL=redis://localhost:6379
```

---

## 13. Example API Usage

### Upload with Transcoding

```bash
curl -X POST "http://192.168.5.12:8001/api/content/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@video.mp4" \
  -F "title=My Video" \
  -F "description=Test video" \
  -F "transcode=true" \
  -F "target_format=h264" \
  -F "target_resolution=1920x1080" \
  -F "target_bitrate=5000"

# Response (202 Accepted):
{
  "status": "success",
  "data": {
    "task_id": 1,
    "message": "Video queued for transcoding",
    "status": "processing"
  }
}
```

### Check Task Status

```bash
curl "http://192.168.5.12:8001/api/tasks/1"

# Response:
{
  "task_id": 1,
  "status": "processing",
  "progress": 45,
  "message": "Transcoding... 45%",
  "eta_seconds": 120,
  "content_id": null,
  "error": null,
  "created_at": "2025-10-29T10:30:00+00:00",
  "started_at": "2025-10-29T10:31:00+00:00",
  "completed_at": null
}
```

### List Active Tasks

```bash
curl "http://192.168.5.12:8001/api/tasks/active"

# Response:
{
  "active_count": 2,
  "tasks": [
    {
      "task_id": 1,
      "status": "processing",
      "progress": 45,
      "created_at": "2025-10-29T10:30:00+00:00"
    },
    {
      "task_id": 2,
      "status": "processing",
      "progress": 10,
      "created_at": "2025-10-29T10:35:00+00:00"
    }
  ]
}
```

---

## 14. Docker Compose Verification

```bash
# Check services
docker-compose -f docker/docker-compose.yml ps

# Watch logs
docker logs -f signage-celery-worker

# Access Flower
open http://192.168.5.12:5555
# Login: admin / admin123

# Check Redis keys
docker exec signage-redis redis-cli keys "transcoding*"
```

---

## 15. Common FFmpeg Presets

```python
# Adjust in transcode_video() function

# Ultra-fast (quality loss)
ffmpeg_cmd = [..., "-preset", "ultrafast", "-crf", "28", ...]

# Fast (acceptable quality)
ffmpeg_cmd = [..., "-preset", "fast", "-crf", "25", ...]

# Medium (balanced)
ffmpeg_cmd = [..., "-preset", "medium", "-crf", "23", ...]

# Slow (high quality)
ffmpeg_cmd = [..., "-preset", "slow", "-crf", "20", ...]

# Very slow (best quality)
ffmpeg_cmd = [..., "-preset", "veryslow", "-crf", "18", ...]

# CRF values: 0-51
# 0 = lossless, 28 = default, 51 = worst quality
```

---

## Installation Order

1. Create model file (transcoding_task.py)
2. Update models/__init__.py
3. Create tasks directory and transcoding.py
4. Create api/tasks.py
5. Update main.py
6. Create services/redis_service.py (if not exists)
7. Create/verify celery_app.py
8. Create database migration
9. Update Dockerfile
10. Update .env
11. Restart Docker containers
12. Test with curl commands

This should cover all the code needed for working Celery transcoding!
