# Celery Task Architecture for Video Transcoding

## Overview

This document defines a production-ready Celery task architecture for asynchronous video transcoding in the Smart TV Digital Signage system.

**Key Benefits:**
- Video upload returns immediately (task_id)
- Background transcoding doesn't block API
- Progress tracking via Redis (0-100%)
- Persistent task state survives server restart
- Automatic retries with exponential backoff
- Monitoring via Flower UI
- Graceful error handling and recovery

---

## 1. Architecture Design

### 1.1 Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Backend (port 8001)                                │
├─────────────────────────────────────────────────────────────┤
│ POST /api/content/upload                                   │
│  → Validate + Store → Queue transcoding task → Return 202 │
│                                                             │
│ GET /api/tasks/{task_id}                                   │
│  → Check Redis for progress/status                         │
│                                                             │
│ GET /api/tasks/active                                      │
│  → List all active transcoding tasks                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
              ┌───────────────────────┐
              │ Redis (Broker + Cache)│ (port 6379)
              ├───────────────────────┤
              │ Queue: transcoding    │
              │ Result Backend        │
              │ Progress Keys         │
              └───────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Celery Workers (4 concurrency)                             │
├─────────────────────────────────────────────────────────────┤
│ transcoding_task()                                          │
│  → Download source video                                   │
│  → Transcode to target format                              │
│  → Update progress every 10% to Redis                      │
│  → Upload transcoded video                                 │
│  → Save metadata to PostgreSQL                             │
│  → Retry 3 times on failure (exponential backoff)          │
└─────────────────────────────────────────────────────────────┘
                          ↓
              ┌───────────────────────┐
              │ PostgreSQL Database   │ (port 5433)
              ├───────────────────────┤
              │ TranscodingTask Model │
              │ Content Model         │
              └───────────────────────┘
```

### 1.2 Task Flow

```
1. Upload Request (API)
   ├─ POST /api/content/upload
   ├─ Validate file (size, format, duration)
   ├─ Store raw video in temporary location
   ├─ Create TranscodingTask record (PENDING)
   ├─ Queue transcoding task → Redis
   ├─ Return 202 Accepted + {task_id, content_id}
   └─ ✓ API returns immediately

2. Background Transcoding (Worker)
   ├─ Dequeue from Redis
   ├─ Set status = PROCESSING in DB
   ├─ Update Redis progress = 0%
   ├─ Download source video from Anthias
   ├─ Start FFmpeg transcoding
   │  ├─ Monitor progress via ffmpeg -progress pipe
   │  └─ Update Redis every 10% progress
   ├─ Handle errors with retry logic:
   │  ├─ Retry 1 (after 5s): exponential backoff
   │  ├─ Retry 2 (after 25s): exponential backoff
   │  └─ Retry 3 (after 125s): final attempt
   ├─ On success:
   │  ├─ Upload transcoded video to Anthias
   │  ├─ Create new Content record
   │  ├─ Update TranscodingTask (COMPLETED)
   │  ├─ Set progress = 100%
   │  └─ ✓ Content ready for assignment
   └─ On failure:
      ├─ Set status = FAILED
      ├─ Store error message in DB
      ├─ Log to monitoring system
      └─ Admin notified

3. Progress Polling (Client)
   ├─ GET /api/tasks/{task_id}
   ├─ Return status + progress % from Redis
   └─ Repeat until status = COMPLETED or FAILED

4. Task Persistence
   ├─ PostgreSQL: TranscodingTask table
   ├─ Redis: task::{task_id}::progress key (TTL 24h)
   ├─ Task survives:
   │  ├─ Server restart (query DB for status)
   │  ├─ Worker restart (Celery result backend)
   │  └─ Network interruption (retry logic)
```

---

## 2. Database Model

### 2.1 TranscodingTask Model

File: `/mnt/g/khoirul/signate/backend/app/models/transcoding_task.py`

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
    PENDING = "pending"           # Queued, not started
    PROCESSING = "processing"     # Currently transcoding
    COMPLETED = "completed"       # Successfully transcoded
    FAILED = "failed"             # Failed after retries


class TranscodingTask(Base):
    """
    Transcoding task model for tracking async video processing

    Attributes:
        id: Primary key / Task ID
        content_id: Source content being transcoded (nullable - created after transcode)
        source_file_path: Path to source video file (temp location)
        source_file_size: Size of source video in bytes
        source_anthias_asset_id: Anthias asset ID of source
        target_format: Target codec/format (e.g., "h264", "h265")
        target_resolution: Target resolution (e.g., "1920x1080")
        target_bitrate: Target bitrate in kbps
        status: Current status (PENDING, PROCESSING, COMPLETED, FAILED)
        progress: Progress percentage (0-100)
        celery_task_id: Celery task UUID for tracking
        error_message: Error message if failed
        error_code: Error code for categorization
        retry_count: Number of retries attempted (0-3)
        retry_details: JSON array of retry attempts with timestamps
        estimated_time_remaining: Estimated seconds until completion
        created_at: Timestamp when task was created
        started_at: Timestamp when processing started
        completed_at: Timestamp when processing finished
        updated_at: Timestamp of last update
    """

    __tablename__ = "transcoding_tasks"

    # Primary Key / Task ID
    id = Column(Integer, primary_key=True, index=True)

    # Source Content
    content_id = Column(Integer, nullable=True, index=True)  # Filled after successful transcode
    source_file_path = Column(String(500), nullable=False)
    source_file_size = Column(Integer, nullable=False)  # bytes
    source_anthias_asset_id = Column(String(100), nullable=True)

    # Target Configuration
    target_format = Column(String(50), default="h264")  # h264, h265, vp9
    target_resolution = Column(String(50), nullable=True)  # 1920x1080, 1280x720
    target_bitrate = Column(Integer, nullable=True)  # kbps

    # Status & Progress
    status = Column(
        SQLEnum(TranscodingStatus),
        default=TranscodingStatus.PENDING,
        index=True
    )
    progress = Column(Integer, default=0)  # 0-100

    # Celery Integration
    celery_task_id = Column(String(100), unique=True, index=True)  # Celery task UUID

    # Error Handling
    error_message = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)  # INVALID_FILE, TRANSCODE_FAILED, UPLOAD_FAILED, TIMEOUT
    retry_count = Column(Integer, default=0)
    retry_details = Column(JSON, nullable=True)  # [{attempt: 1, error: "...", timestamp: "..."}]

    # Timing Estimates
    estimated_time_remaining = Column(Integer, nullable=True)  # seconds

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

---

## 3. Redis Key Schema

### 3.1 Key Design

All keys use pattern: `transcoding::{task_id}::{key_name}`

```
# Task Progress (expires after 24 hours)
transcoding::{task_id}::progress
  → Value: { "percentage": 45, "status": "processing", "eta": 120 }
  → TTL: 24 hours
  → Updated by: Celery worker every 10% progress

# Task Status (expires after 24 hours)
transcoding::{task_id}::status
  → Value: { "status": "processing", "message": "Transcoding H.264..." }
  → TTL: 24 hours
  → Updated by: Celery worker on status changes

# Active Tasks Set (for listing)
transcoding::active_tasks
  → Type: Set
  → Members: [task_id_1, task_id_2, task_id_3]
  → TTL: 24 hours
  → Updated by: Worker on start/completion

# Task Metadata (for quick lookup)
transcoding::{task_id}::metadata
  → Value: {
      "source_file_path": "/tmp/upload_xyz.mp4",
      "target_format": "h264",
      "created_at": "2025-10-29T10:30:00Z",
      "estimated_duration": 300
    }
  → TTL: 24 hours
  → Created by: API on task creation
```

### 3.2 Redis Access Pattern

```python
# Get progress
progress_key = f"transcoding::{task_id}::progress"
progress = redis_client.get(progress_key)
# Returns: {"percentage": 45, "status": "processing", "eta": 120}

# Update progress (from worker)
redis_client.setex(
    f"transcoding::{task_id}::progress",
    86400,  # 24 hours TTL
    json.dumps({"percentage": 50, "status": "processing", "eta": 100})
)

# Add to active tasks
redis_client.sadd("transcoding::active_tasks", task_id)

# Mark as complete
redis_client.srem("transcoding::active_tasks", task_id)
redis_client.setex(
    f"transcoding::{task_id}::progress",
    86400,
    json.dumps({"percentage": 100, "status": "completed"})
)
```

---

## 4. Celery Task Implementation

### 4.1 Task Function

File: `/mnt/g/khoirul/signate/backend/app/tasks/transcoding.py`

```python
"""
Celery task for asynchronous video transcoding
Handles transcoding, progress tracking, retries, and error handling
"""

from celery import shared_task, current_task
from celery.utils.log import get_task_logger
from sqlalchemy.orm import Session
import json
import subprocess
import os
import re
from datetime import datetime
from app.core.database import SessionLocal
from app.models.transcoding_task import TranscodingTask, TranscodingStatus
from app.core.config import settings
from app.services.anthias_service import anthias_service
from app.services.redis_service import redis_client
from app.models.content import Content

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,  # 5 seconds initial delay
    autoretry_for=(Exception,),
    retry_backoff=True,  # exponential backoff
    retry_backoff_max=600,  # max 10 minutes between retries
    retry_jitter=True,  # add randomness to prevent thundering herd
)
def transcode_video(
    self,
    task_id: int,
    source_anthias_asset_id: str,
    target_format: str = "h264",
    target_resolution: str = "1920x1080",
    target_bitrate: int = 5000,  # kbps
):
    """
    Transcode video to target format with progress tracking

    Args:
        task_id: TranscodingTask ID in database
        source_anthias_asset_id: Anthias asset ID of source video
        target_format: Target codec (h264, h265, vp9)
        target_resolution: Target resolution (1920x1080, 1280x720, etc.)
        target_bitrate: Target bitrate in kbps

    Returns:
        dict: {
            "task_id": task_id,
            "status": "completed",
            "content_id": new_content_id,
            "output_file_size": bytes
        }

    Raises:
        Exception: On transcode failure (triggers retry)
    """

    db = SessionLocal()

    try:
        # Fetch task from database
        task_record = db.query(TranscodingTask).filter(
            TranscodingTask.id == task_id
        ).first()

        if not task_record:
            logger.error(f"TranscodingTask {task_id} not found")
            return {"error": "Task not found", "task_id": task_id}

        # Update Celery task ID for tracking
        task_record.celery_task_id = self.request.id

        # Set to PROCESSING
        task_record.status = TranscodingStatus.PROCESSING
        task_record.started_at = datetime.utcnow()
        db.commit()

        logger.info(f"Starting transcode for task {task_id}")

        # Update Redis: task started
        progress_key = f"transcoding::{task_id}::progress"
        redis_client.setex(
            progress_key,
            86400,  # 24 hours
            json.dumps({
                "percentage": 0,
                "status": "processing",
                "message": "Downloading source video...",
                "eta": None
            })
        )

        # Add to active tasks set
        redis_client.sadd("transcoding::active_tasks", task_id)

        # ============================================================
        # Step 1: Download source video from Anthias
        # ============================================================
        logger.info(f"Downloading video from Anthias: {source_anthias_asset_id}")

        source_file_path = task_record.source_file_path
        if not os.path.exists(source_file_path):
            # Download from Anthias
            source_video_bytes = await anthias_service.get_asset_content(
                source_anthias_asset_id
            )

            # Ensure directory exists
            os.makedirs(os.path.dirname(source_file_path), exist_ok=True)

            # Write to disk
            with open(source_file_path, 'wb') as f:
                f.write(source_video_bytes)

            logger.info(f"Downloaded video: {source_file_path}")

        # Update Redis: downloaded
        redis_client.setex(
            progress_key,
            86400,
            json.dumps({
                "percentage": 5,
                "status": "processing",
                "message": "Source video downloaded. Starting transcode...",
                "eta": None
            })
        )

        # ============================================================
        # Step 2: Transcode with FFmpeg
        # ============================================================
        output_file_path = f"{source_file_path}.transcoded.mp4"

        # Build FFmpeg command
        ffmpeg_cmd = [
            "ffmpeg",
            "-i", source_file_path,
            "-c:v", target_format,  # Video codec
            "-s", target_resolution,  # Resolution
            "-b:v", f"{target_bitrate}k",  # Bitrate
            "-c:a", "aac",  # Audio codec
            "-b:a", "128k",  # Audio bitrate
            "-progress", "pipe:1",  # Progress output to stdout
            "-y",  # Overwrite output file
            output_file_path
        ]

        logger.info(f"Starting FFmpeg: {' '.join(ffmpeg_cmd)}")

        # Track transcoding progress
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1  # Line buffering
        )

        # Get source duration for progress calculation
        source_duration = await _get_video_duration(source_file_path)
        logger.info(f"Source video duration: {source_duration}s")

        # Process FFmpeg output
        last_progress_update = 0
        for line in process.stdout:
            if line.startswith("out_time_ms="):
                current_time_ms = int(line.split("=")[1])
                current_time_s = current_time_ms / 1_000_000

                # Calculate progress percentage
                progress_pct = int((current_time_s / source_duration) * 100)
                progress_pct = min(progress_pct, 95)  # Cap at 95% until complete

                # Update Redis every 10% or every second
                if progress_pct >= last_progress_update + 10:
                    estimated_remaining = (100 - progress_pct) / 10  # rough estimate

                    redis_client.setex(
                        progress_key,
                        86400,
                        json.dumps({
                            "percentage": progress_pct,
                            "status": "processing",
                            "message": f"Transcoding... {progress_pct}%",
                            "eta": estimated_remaining * 10  # rough estimate in seconds
                        })
                    )

                    logger.info(f"Task {task_id} progress: {progress_pct}%")
                    last_progress_update = progress_pct

        # Wait for FFmpeg to complete
        returncode = process.wait()
        stderr = process.stderr.read()

        if returncode != 0:
            logger.error(f"FFmpeg failed: {stderr}")
            task_record.error_code = "TRANSCODE_FAILED"
            task_record.error_message = stderr[:500]
            task_record.status = TranscodingStatus.FAILED
            task_record.retry_count = self.request.retries
            db.commit()

            # Raise to trigger retry
            raise Exception(f"FFmpeg transcoding failed: {stderr}")

        # Update Redis: transcode complete
        redis_client.setex(
            progress_key,
            86400,
            json.dumps({
                "percentage": 95,
                "status": "processing",
                "message": "Uploading transcoded video to storage...",
                "eta": None
            })
        )

        logger.info(f"Transcode complete: {output_file_path}")

        # ============================================================
        # Step 3: Upload transcoded video to Anthias
        # ============================================================
        logger.info("Uploading transcoded video to Anthias...")

        with open(output_file_path, 'rb') as f:
            transcoded_bytes = f.read()

        anthias_asset = await anthias_service.upload_asset(
            file_data=transcoded_bytes,
            name=f"{task_record.source_file_path.split('/')[-1]}_transcoded",
            duration=None,  # Auto-detect from metadata
            is_enabled=True
        )

        anthias_asset_id = anthias_asset["asset_id"]
        anthias_url = await anthias_service.get_asset_url(anthias_asset_id)

        logger.info(f"Uploaded to Anthias: {anthias_asset_id}")

        # ============================================================
        # Step 4: Create Content record in database
        # ============================================================
        logger.info("Creating Content record in database...")

        content = Content(
            title=f"{task_record.source_file_path.split('/')[-1]} (Transcoded)",
            description=f"Transcoded to {target_format} {target_resolution} {target_bitrate}kbps",
            content_type="video",
            anthias_url=anthias_url,
            anthias_asset_id=anthias_asset_id,
            duration=source_duration,
            is_active=True,
            file_size=os.path.getsize(output_file_path),
            mime_type="video/mp4",
            resolution=target_resolution,
            codec=target_format
        )

        db.add(content)
        db.flush()  # Get content.id
        db.commit()

        logger.info(f"Created Content record: {content.id}")

        # ============================================================
        # Step 5: Update task record
        # ============================================================
        task_record.content_id = content.id
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
                "message": "Transcoding completed successfully",
                "content_id": content.id
            })
        )

        # Remove from active tasks
        redis_client.srem("transcoding::active_tasks", task_id)

        # Clean up temporary files
        try:
            os.remove(source_file_path)
            os.remove(output_file_path)
            logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.warning(f"Failed to clean temporary files: {e}")

        logger.info(f"Task {task_id} completed successfully. Content ID: {content.id}")

        return {
            "task_id": task_id,
            "status": "completed",
            "content_id": content.id,
            "output_file_size": os.path.getsize(output_file_path)
        }

    except Exception as exc:
        logger.error(f"Transcode failed (retry {self.request.retries}): {exc}", exc_info=True)

        # Update database with retry info
        try:
            task_record = db.query(TranscodingTask).filter(
                TranscodingTask.id == task_id
            ).first()

            if task_record:
                # Record retry attempt
                retry_details = task_record.retry_details or []
                retry_details.append({
                    "attempt": self.request.retries,
                    "error": str(exc)[:200],
                    "timestamp": datetime.utcnow().isoformat()
                })
                task_record.retry_details = retry_details
                task_record.retry_count = self.request.retries

                # Mark as failed if final retry
                if self.request.retries >= 3:
                    task_record.status = TranscodingStatus.FAILED
                    task_record.error_message = str(exc)[:500]
                    task_record.error_code = "TRANSCODE_FAILED"
                    task_record.completed_at = datetime.utcnow()

                    # Update Redis
                    redis_client.setex(
                        f"transcoding::{task_id}::progress",
                        86400,
                        json.dumps({
                            "percentage": task_record.progress,
                            "status": "failed",
                            "error": str(exc)[:200]
                        })
                    )
                    redis_client.srem("transcoding::active_tasks", task_id)

                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update task record: {db_error}")

        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=5 * (2 ** self.request.retries))

    finally:
        db.close()


async def _get_video_duration(file_path: str) -> float:
    """
    Get video duration using FFprobe

    Args:
        file_path: Path to video file

    Returns:
        float: Duration in seconds
    """
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
        logger.warning(f"Failed to get video duration: {e}, defaulting to 60s")
        return 60.0
```

### 4.2 Celery Configuration

File: `/mnt/g/khoirul/signate/backend/app/celery_app.py`

```python
"""
Celery application configuration
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings
import logging

# Create Celery app
app = Celery(
    "signage_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configuration
app.conf.update(
    # Broker settings
    broker_url=settings.REDIS_URL,
    result_backend=settings.REDIS_URL,

    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,

    # Task execution settings
    task_track_started=True,  # Track when task starts
    task_time_limit=3600,  # Hard time limit: 1 hour
    task_soft_time_limit=3300,  # Soft time limit: 55 minutes

    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    result_extended=True,  # Store extended info

    # Worker settings
    worker_prefetch_multiplier=1,  # Only prefetch 1 task at a time
    worker_max_tasks_per_child=1000,  # Reload worker after 1000 tasks

    # Periodic task schedule (Celery Beat)
    beat_schedule={
        'cleanup-old-transcoding-tasks': {
            'task': 'app.tasks.transcoding.cleanup_old_tasks',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        },
    },
)

# Load tasks
app.autodiscover_tasks(['app.tasks'])

logger = logging.getLogger(__name__)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
```

---

## 5. API Endpoints

### 5.1 Upload Endpoint (Modified)

File: `/mnt/g/khoirul/signate/backend/app/api/content.py`

```python
@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_content(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    duration: int = Form(10),
    transcode: bool = Form(False),  # NEW: Enable transcoding
    target_format: str = Form("h264"),  # NEW: h264, h265, vp9
    target_resolution: str = Form("1920x1080"),  # NEW
    target_bitrate: int = Form(5000),  # NEW: kbps
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Upload content and optionally queue for transcoding

    Returns 202 Accepted with task_id if transcode=true
    Returns 201 Created with content_id if transcode=false

    Args:
        transcode: Enable background transcoding (default: False)
        target_format: Target codec for transcoding
        target_resolution: Target resolution
        target_bitrate: Target bitrate in kbps

    Returns (if transcode=true):
        {
            "status": "accepted",
            "task_id": 123,
            "message": "Video queued for transcoding"
        }
    """

    request_id = get_request_id(request)

    logger.info(
        "Content upload started",
        request_id=request_id,
        transcode=transcode
    )

    try:
        # Validate file type
        if not file.content_type or not (
            file.content_type.startswith("image/") or
            file.content_type.startswith("video/")
        ):
            raise BadRequestException(
                message=f"Unsupported file type: {file.content_type}"
            )

        # Determine content type
        content_type = "image" if file.content_type.startswith("image/") else "video"

        # Save file temporarily
        temp_file_path = f"/tmp/upload_{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        with open(temp_file_path, 'wb') as f:
            f.write(await file.read())

        # Upload to Anthias
        anthias_asset = await anthias_service.upload_asset(
            file=file,
            name=title,
            duration=duration,
            is_enabled=True
        )

        # If not transcoding, create Content now and return 201
        if not transcode or content_type != "video":
            content = Content(
                title=title,
                description=description,
                content_type=content_type,
                anthias_url=await anthias_service.get_asset_url(anthias_asset["asset_id"]),
                anthias_asset_id=anthias_asset["asset_id"],
                duration=duration,
                is_active=True,
                file_size=os.path.getsize(temp_file_path)
            )
            db.add(content)
            db.commit()
            db.refresh(content)

            return success_response(
                data={"id": content.id, "title": content.title},
                status_code=status.HTTP_201_CREATED,
                request_id=request_id
            )

        # NEW: Queue for transcoding
        task_record = TranscodingTask(
            source_file_path=temp_file_path,
            source_file_size=os.path.getsize(temp_file_path),
            source_anthias_asset_id=anthias_asset["asset_id"],
            target_format=target_format,
            target_resolution=target_resolution,
            target_bitrate=target_bitrate,
            status=TranscodingStatus.PENDING
        )
        db.add(task_record)
        db.commit()
        db.refresh(task_record)

        # Queue Celery task
        celery_task = transcode_video.delay(
            task_id=task_record.id,
            source_anthias_asset_id=anthias_asset["asset_id"],
            target_format=target_format,
            target_resolution=target_resolution,
            target_bitrate=target_bitrate
        )

        task_record.celery_task_id = celery_task.id
        db.commit()

        logger.info(
            "Video queued for transcoding",
            request_id=request_id,
            task_id=task_record.id,
            celery_task_id=celery_task.id
        )

        return success_response(
            data={
                "task_id": task_record.id,
                "message": "Video queued for transcoding",
                "status": "processing"
            },
            status_code=status.HTTP_202_ACCEPTED,
            request_id=request_id
        )

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise InternalServerException(message="Upload failed")
```

### 5.2 Task Status Endpoint (NEW)

File: `/mnt/g/khoirul/signate/backend/app/api/tasks.py`

```python
"""
Task management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.transcoding_task import TranscodingTask
from app.middleware.request_id import get_request_id
from app.services.redis_service import redis_client
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
    """
    Get transcoding task status and progress

    Returns:
        {
            "task_id": 123,
            "status": "processing",
            "progress": 45,
            "message": "Transcoding... 45%",
            "eta_seconds": 120,
            "content_id": null,
            "error": null,
            "created_at": "2025-10-29T10:30:00Z",
            "started_at": "2025-10-29T10:31:00Z",
            "completed_at": null
        }
    """

    request_id = get_request_id(request)

    # Get from database
    task_record = db.query(TranscodingTask).filter(
        TranscodingTask.id == task_id
    ).first()

    if not task_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    # Get progress from Redis (real-time)
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
        status=task_record.status,
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
    """
    List all active transcoding tasks

    Returns:
        {
            "active_count": 3,
            "tasks": [
                {
                    "task_id": 123,
                    "status": "processing",
                    "progress": 45,
                    "created_at": "2025-10-29T10:30:00Z"
                }
            ]
        }
    """

    request_id = get_request_id(request)

    # Get active tasks from Redis set
    active_task_ids = redis_client.smembers("transcoding::active_tasks")

    # Fetch from database
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


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_task(
    task_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Cancel a pending or processing transcoding task

    Only works for PENDING and PROCESSING tasks.
    Cannot cancel COMPLETED or FAILED tasks.
    """

    request_id = get_request_id(request)

    task_record = db.query(TranscodingTask).filter(
        TranscodingTask.id == task_id
    ).first()

    if not task_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    if task_record.status not in ["pending", "processing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task in status: {task_record.status.value}"
        )

    # Revoke Celery task
    if task_record.celery_task_id:
        from app.celery_app import app as celery_app
        celery_app.control.revoke(task_record.celery_task_id, terminate=True)

    # Update database
    task_record.status = TranscodingStatus.FAILED
    task_record.error_message = "Cancelled by user"
    task_record.error_code = "CANCELLED"
    db.commit()

    # Remove from Redis
    redis_client.srem("transcoding::active_tasks", task_id)

    logger.info(
        "Task cancelled",
        request_id=request_id,
        task_id=task_id
    )

    return None
```

### 5.3 Include in Main Router

File: `/mnt/g/khoirul/signate/backend/app/main.py`

```python
from app.api import tasks as tasks_api

# Add to routers
app.include_router(
    tasks_api.router,
    prefix="/api",
    tags=["Tasks"]
)
```

---

## 6. Error Handling Strategy

### 6.1 Error Codes & Actions

| Error Code | Cause | Action | Retry? |
|-----------|-------|--------|--------|
| `INVALID_FILE` | File corrupted/unsupported | Skip (mark FAILED) | No |
| `TRANSCODE_FAILED` | FFmpeg error | Retry 3x with backoff | Yes |
| `UPLOAD_FAILED` | Anthias upload error | Retry 3x with backoff | Yes |
| `TIMEOUT` | Task exceeded time limit | Skip (mark FAILED) | No |
| `CANCELLED` | User cancelled | Skip (mark FAILED) | No |
| `OUT_OF_DISK` | Insufficient disk space | Manual intervention | No |

### 6.2 Retry Logic

```
Attempt 1: Immediate
Attempt 2: Wait 5s (5 * 2^1 = 10s with jitter)
Attempt 3: Wait 20s (5 * 2^2 = 20s with jitter)
Attempt 4: Wait 80s (5 * 2^3 = 80s with jitter)

Max retries: 3
Total max wait: ~115 seconds
```

---

## 7. Monitoring & Observability

### 7.1 Flower UI

Access at `http://192.168.5.12:5555`
- Credentials: `admin` / `admin123`
- Monitor: Active tasks, completed tasks, failures
- View: Task details, retry history, execution time

### 7.2 Logging

```python
# Structured logs with context
logger.info(
    "Task started",
    request_id=request_id,
    task_id=task_id,
    celery_task_id=celery_task.id,
    target_format=target_format
)

# Progress tracking
logger.info(f"Task {task_id} progress: {progress}%")

# Error tracking
logger.error(
    "Transcode failed",
    request_id=request_id,
    task_id=task_id,
    error=str(e),
    exc_info=True
)
```

### 7.3 Alerts

Set up alerts for:
- Task failure rate > 10%
- Task processing time > 30 minutes
- Redis memory > 80%
- Worker health check fails

---

## 8. Database Migrations

### 8.1 Migration Script

File: `database/migrations/002_add_transcoding_tasks.sql`

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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_content FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE SET NULL
);

CREATE INDEX idx_transcoding_tasks_status ON transcoding_tasks(status);
CREATE INDEX idx_transcoding_tasks_created_at ON transcoding_tasks(created_at);
CREATE INDEX idx_transcoding_tasks_celery_task_id ON transcoding_tasks(celery_task_id);
```

---

## 9. Deployment Checklist

- [ ] Add TranscodingTask model to `/app/models/__init__.py`
- [ ] Create migration file and run: `alembic upgrade head`
- [ ] Add transcoding tasks module: `/app/tasks/transcoding.py`
- [ ] Update celery_app.py with task configuration
- [ ] Create tasks API router: `/app/api/tasks.py`
- [ ] Update content.py upload endpoint to support transcode parameter
- [ ] Include tasks router in main.py
- [ ] Add FFmpeg and FFprobe to Dockerfile: `RUN apt-get install -y ffmpeg`
- [ ] Test with docker-compose: `docker-compose up -d`
- [ ] Verify Celery worker and Flower are running
- [ ] Monitor: `docker logs signage-celery-worker`
- [ ] Access Flower: `http://192.168.5.12:5555`

---

## 10. Testing

### 10.1 Integration Test

```bash
# Test upload with transcoding
curl -X POST "http://192.168.5.12:8001/api/content/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_video.mp4" \
  -F "title=Test Video" \
  -F "transcode=true" \
  -F "target_format=h264" \
  -F "target_resolution=1920x1080" \
  -F "target_bitrate=5000"

# Returns: {"task_id": 1, "status": "processing"}

# Poll for progress
curl "http://192.168.5.12:8001/api/tasks/1"

# List active tasks
curl "http://192.168.5.12:8001/api/tasks/active"
```

---

## 11. Performance Tuning

### 11.1 Celery Worker Config

```yaml
# docker-compose.yml
celery-worker:
  command: celery -A app.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=100 \
    --prefetch-multiplier=1
```

- `concurrency=4`: Process 4 videos in parallel (adjust based on CPU cores)
- `max-tasks-per-child=100`: Reload worker after 100 tasks (memory leak prevention)
- `prefetch-multiplier=1`: Only fetch 1 task at a time (prevents task hoarding)

### 11.2 FFmpeg Optimization

```python
# Fast transcoding (lose quality)
ffmpeg_cmd = [
    "ffmpeg",
    "-i", source_file_path,
    "-c:v", "h264",
    "-preset", "fast",  # ultrafast, superfast, veryfast, faster, fast, medium
    "-crf", "28",  # 0-51 (lower = better quality, slower)
    ...
]

# Balanced (quality vs speed)
"-preset", "medium",
"-crf", "23",

# High quality (slow)
"-preset", "slow",
"-crf", "18",
```

---

## 12. Future Enhancements

1. **Batch transcoding**: Queue multiple videos simultaneously
2. **Webhook notifications**: POST to external URL on completion
3. **Thumbnail generation**: Capture frame at 10% progress
4. **Multiple output formats**: Create H.264, H.265, WebP in one task
5. **Watermarking**: Add logo during transcoding
6. **Hardware acceleration**: NVIDIA NVENC for faster transcoding
7. **Adaptive bitrate**: Generate multiple bitrate versions for streaming
8. **Subtitle extraction**: Extract and store subtitle tracks

---

## Summary

This architecture provides:

✅ **Async processing** - Upload returns immediately (202 Accepted)
✅ **Progress tracking** - Real-time progress via Redis
✅ **Retry resilience** - 3 retries with exponential backoff
✅ **Job persistence** - Task state in PostgreSQL + Redis
✅ **Status tracking** - pending → processing → completed/failed
✅ **Monitoring** - Flower UI + structured logging
✅ **Error handling** - Graceful failures with error codes
✅ **Scalability** - Horizontal scaling via worker concurrency

Estimated transcoding time for a 10-minute 1080p video:
- **Fast preset**: 2-3 minutes
- **Medium preset**: 5-8 minutes
- **Slow preset**: 15-20 minutes

Adjust concurrency and FFmpeg settings based on server resources.
