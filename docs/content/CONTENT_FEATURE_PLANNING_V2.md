# 📋 CONTENT FEATURE - PLANNING & IMPLEMENTATION GUIDE (V2)

**Tanggal:** 2025-11-06 (Updated)
**Status:** Ready to Implement - Custom Storage Architecture
**Estimasi:** 3-4 minggu
**Priority:** High

---

## 🎯 EXECUTIVE SUMMARY

Fitur Content adalah sistem upload dan management untuk media files (gambar, video, audio) yang akan ditampilkan di digital signage devices. Sistem ini akan:

- ✅ **Custom Storage System** - File storage sendiri tanpa dependency eksternal
- ✅ Support multiple media formats (Image, Video, Audio)
- ✅ Celery untuk async processing (transcoding, thumbnail generation)
- ✅ Multi-tenant isolation (per organization)
- ✅ Metadata extraction otomatis (resolution, codec, duration, dll)
- ✅ Tag-based organization
- ✅ Audit logging lengkap
- ✅ Scalable architecture (local → MinIO/S3 migration ready)

---

## 🗄️ CUSTOM STORAGE ARCHITECTURE

### Opsi Storage Strategy

Kita akan implement **2-phase approach**:

#### Phase 1: Local Filesystem (Immediate Implementation)
**Pros:**
- ✅ Zero external dependencies
- ✅ Simple implementation
- ✅ Full control
- ✅ No API rate limits
- ✅ Fast development

**Cons:**
- ⚠️ Tidak scalable horizontal (single server)
- ⚠️ Manual backup management
- ⚠️ Disk space management

#### Phase 2: MinIO / S3 (Future Enhancement)
**Pros:**
- ✅ Horizontal scalability
- ✅ Built-in redundancy
- ✅ CDN integration ready
- ✅ S3-compatible API

**Implementation:** Easy migration karena abstraction layer

---

### Local Filesystem Structure

```
/data/signage/content/
├── uploads/                          # Original uploaded files
│   ├── images/
│   │   ├── 2025/
│   │   │   ├── 01/                   # Organized by year/month
│   │   │   │   ├── org_4/            # Multi-tenant: per organization
│   │   │   │   │   ├── abc123.jpg
│   │   │   │   │   └── def456.png
│   │   │   │   └── org_5/
│   │   │   │       └── ghi789.webp
│   │   │   └── 02/
│   │   └── 2024/
│   ├── videos/
│   │   └── 2025/
│   │       └── 01/
│   │           └── org_4/
│   │               ├── video123.mp4  # Original video
│   │               └── video456.webm
│   └── audio/
│       └── 2025/
│           └── 01/
│               └── org_4/
│                   ├── audio123.mp3
│                   └── audio456.aac
│
├── thumbnails/                       # Auto-generated thumbnails
│   └── 2025/
│       └── 01/
│           └── org_4/
│               ├── video123_thumb.jpg
│               └── image123_thumb.jpg
│
├── transcoded/                       # HLS transcoded videos
│   └── 2025/
│       └── 01/
│           └── org_4/
│               └── video123/         # Per-video directory
│                   ├── master.m3u8   # HLS master playlist
│                   ├── 1080p.m3u8
│                   ├── 720p.m3u8
│                   ├── 480p.m3u8
│                   └── segments/
│                       ├── 1080p_0000.ts
│                       ├── 1080p_0001.ts
│                       ├── 720p_0000.ts
│                       └── ...
│
└── temp/                             # Temporary processing files
    └── uploads/                      # Temp during upload
        └── session_xxx/
```

**Key Design Decisions:**

1. **Organization-based Isolation**
   - Each file path contains `org_id`
   - Easy to identify and migrate organization data
   - Backup per-organization

2. **Time-based Partitioning**
   - Year/Month folders
   - Easy to archive old content
   - Better filesystem performance

3. **Type-based Separation**
   - images/, videos/, audio/
   - Different processing pipelines
   - Easy to apply type-specific optimizations

4. **Unique Filenames**
   - UUID + original extension
   - Prevents name collisions
   - Secure (no path traversal)

---

### File Serving Strategy

#### Option A: Direct Nginx Serving (Recommended for Start)

**Nginx Configuration:**
```nginx
server {
    listen 8001;
    server_name 192.168.5.12;

    # API endpoints
    location /api/ {
        proxy_pass http://backend-api:8000;
        # ... proxy settings
    }

    # Static file serving (content files)
    location /content/ {
        alias /data/signage/content/uploads/;

        # Security: Only allow authenticated access via signed URLs
        # (implemented via backend token validation)

        # Performance
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;

        # Caching
        expires 30d;
        add_header Cache-Control "public, immutable";

        # CORS for device access
        add_header Access-Control-Allow-Origin *;
    }

    # HLS streaming
    location /streaming/ {
        alias /data/signage/content/transcoded/;

        # HLS specific
        add_header Cache-Control "no-cache";
        types {
            application/vnd.apple.mpegurl m3u8;
            video/mp2t ts;
        }
    }

    # Thumbnails
    location /thumbnails/ {
        alias /data/signage/content/thumbnails/;
        expires 7d;
        add_header Cache-Control "public";
    }
}
```

**File URL Structure:**
```
Original Files:
http://192.168.5.12:8001/content/images/2025/01/org_4/abc123.jpg

HLS Streaming:
http://192.168.5.12:8001/streaming/2025/01/org_4/video123/master.m3u8

Thumbnails:
http://192.168.5.12:8001/thumbnails/2025/01/org_4/video123_thumb.jpg
```

#### Option B: Backend API Serving (More Control, Slower)

**Use Case:** Ketika perlu fine-grained access control atau analytics

```python
@router.get("/serve/{content_id}")
async def serve_content(
    content_id: int,
    token: str = Query(...),  # Signed token for auth
    current_user: dict = Depends(verify_token)
):
    """
    Serve file via backend with authentication
    - Validates token
    - Checks organization access
    - Logs download (analytics)
    - Streams file
    """
    content = content_repo.find_by_id(content_id, current_user["organization_id"])

    # Log download event
    analytics_logger.log_download(content_id, current_user["user_id"])

    # Stream file
    return FileResponse(
        path=content.file_path,
        media_type=content.mime_type,
        filename=content.original_filename
    )
```

**Recommendation:** Start with **Option A (Nginx)** untuk performance, tambahkan **Option B** kalau butuh analytics/fine-grained access control.

---

## 📁 DATABASE SCHEMA (Updated)

### Table: `contents`

```sql
CREATE TABLE contents (
    -- Identity
    id                      SERIAL PRIMARY KEY,
    title                   VARCHAR(200) NOT NULL,
    description             TEXT,
    content_type            VARCHAR(20) NOT NULL, -- 'image', 'video', 'audio'

    -- File Storage (Custom System - NO Anthias fields!)
    file_path               VARCHAR(500) NOT NULL,  -- /data/signage/content/uploads/images/2025/01/org_4/abc123.jpg
    file_url                VARCHAR(500) NOT NULL,  -- http://192.168.5.12:8001/content/images/2025/01/org_4/abc123.jpg
    storage_key             VARCHAR(255) NOT NULL UNIQUE, -- Unique identifier: images/2025/01/org_4/abc123.jpg

    -- Display Settings
    duration                INTEGER DEFAULT 10 NOT NULL, -- seconds
    is_active               BOOLEAN DEFAULT true,

    -- File Metadata
    file_size               BIGINT, -- bytes
    mime_type               VARCHAR(100),
    original_filename       VARCHAR(255),
    file_extension          VARCHAR(20), -- .jpg, .mp4, .mp3

    -- Media Properties (extracted via FFprobe)
    resolution              VARCHAR(50), -- "1920x1080"
    width                   INTEGER,
    height                  INTEGER,
    codec                   VARCHAR(50), -- "h264", "vp9", "aac"
    fps                     FLOAT, -- frames per second
    bitrate                 INTEGER, -- kbps

    -- Video/Audio Specific
    media_duration          FLOAT, -- actual media length in seconds
    video_start_time        FLOAT DEFAULT 0,
    video_end_time          FLOAT, -- NULL = play to end
    audio_codec             VARCHAR(50),
    audio_bitrate           INTEGER,
    audio_sample_rate       INTEGER,
    audio_channels          INTEGER DEFAULT 2,

    -- Transcoding (HLS for video)
    transcoding_status      VARCHAR(50), -- pending/processing/completed/failed
    transcoding_job_id      VARCHAR(200), -- Celery task ID
    transcoding_progress    INTEGER DEFAULT 0, -- 0-100%
    transcoding_error       TEXT,
    hls_master_playlist_path VARCHAR(500), -- /data/signage/content/transcoded/.../master.m3u8
    hls_master_playlist_url  VARCHAR(500), -- http://192.168.5.12:8001/streaming/.../master.m3u8
    hls_variants            JSONB, -- [{resolution, bitrate, path}, ...]

    -- Thumbnail
    thumbnail_path          VARCHAR(500),
    thumbnail_url           VARCHAR(500),
    thumbnail_generated_at  TIMESTAMP,

    -- Checksum & Validation
    file_hash               VARCHAR(64), -- SHA256 hash for integrity check
    upload_status           VARCHAR(20) DEFAULT 'pending', -- pending/processing/completed/failed

    -- Multi-tenant
    organization_id         INTEGER NOT NULL REFERENCES organizations(id),
    uploaded_by             INTEGER REFERENCES users(id),

    -- Audit
    created_at              TIMESTAMP DEFAULT NOW(),
    updated_at              TIMESTAMP DEFAULT NOW(),
    deleted_at              TIMESTAMP, -- Soft delete

    -- Indexes
    INDEX idx_organization_id (organization_id),
    INDEX idx_content_type (content_type),
    INDEX idx_is_active (is_active),
    INDEX idx_storage_key (storage_key),
    INDEX idx_created_at (created_at),
    INDEX idx_upload_status (upload_status)
);

-- Unique constraint: Prevent duplicate files
CREATE UNIQUE INDEX idx_unique_file_hash_org
ON contents(file_hash, organization_id)
WHERE deleted_at IS NULL;
```

**Key Changes from Anthias Version:**
- ❌ Removed: `anthias_url`, `anthias_asset_id`, `anthias_file_uri`
- ✅ Added: `file_path`, `file_url`, `storage_key` (our custom system)
- ✅ Added: `file_hash` (SHA256 for deduplication & integrity)
- ✅ Added: `upload_status` (track upload progress)
- ✅ Added: `file_extension` (easier file type handling)

---

## 🔄 UPLOAD FLOW (Custom Storage)

```
┌─────────────┐
│   Browser   │ User selects file
│  (CMS-Vite) │ (image/video/audio)
└──────┬──────┘
       │ FormData + metadata
       │ POST /api/v1/content/upload
       ▼
┌─────────────────────────────────────────────────────┐
│    Backend-Python (FastAPI)                         │
│  ┌──────────────────────────────────────────────┐  │
│  │ 1. Validate File                             │  │
│  │    - Type check (MIME)                       │  │
│  │    - Size limit validation                   │  │
│  │    - Extension validation                    │  │
│  │    - Calculate SHA256 hash                   │  │
│  │    - Check duplicate (hash + org_id)         │  │
│  └────────────────┬─────────────────────────────┘  │
│                   ▼                                  │
│  ┌──────────────────────────────────────────────┐  │
│  │ 2. Generate Storage Path                     │  │
│  │    storage_key = generate_storage_key(       │  │
│  │        content_type='image',                 │  │
│  │        org_id=4,                             │  │
│  │        extension='.jpg'                      │  │
│  │    )                                         │  │
│  │    # Result: images/2025/01/org_4/abc123.jpg│  │
│  │                                              │  │
│  │    file_path = /data/signage/content/       │  │
│  │                uploads/[storage_key]         │  │
│  │    file_url = http://192.168.5.12:8001/     │  │
│  │               content/[storage_key]          │  │
│  └────────────────┬─────────────────────────────┘  │
│                   ▼                                  │
│  ┌──────────────────────────────────────────────┐  │
│  │ 3. Save File to Disk                         │  │
│  │    - Create directory structure              │  │
│  │    - Stream file to disk (chunked)           │  │
│  │    - Set file permissions (644)              │  │
│  │    - Verify write success                    │  │
│  └────────────────┬─────────────────────────────┘  │
│                   ▼                                  │
│  ┌──────────────────────────────────────────────┐  │
│  │ 4. Extract Metadata (FFprobe)                │  │
│  │    - Resolution (width x height)             │  │
│  │    - Codec (H.264, VP9, AAC, etc)            │  │
│  │    - Duration (for video/audio)              │  │
│  │    - Bitrate, FPS, Audio info                │  │
│  └────────────────┬─────────────────────────────┘  │
│                   ▼                                  │
│  ┌──────────────────────────────────────────────┐  │
│  │ 5. Save to PostgreSQL                        │  │
│  │    - Content metadata                        │  │
│  │    - file_path, file_url, storage_key        │  │
│  │    - file_hash (SHA256)                      │  │
│  │    - Multi-tenant organization_id            │  │
│  │    - upload_status = 'completed'             │  │
│  └────────────────┬─────────────────────────────┘  │
│                   ▼                                  │
│  ┌──────────────────────────────────────────────┐  │
│  │ 6. Queue Celery Tasks (Async)                │  │
│  │    Video: transcode_to_hls.delay(id)         │  │
│  │    Image: generate_thumbnail.delay(id)       │  │
│  │    All: extract_enhanced_metadata.delay(id)  │  │
│  └────────────────┬─────────────────────────────┘  │
│                   ▼                                  │
│  ┌──────────────────────────────────────────────┐  │
│  │ 7. Return Response                           │  │
│  │    {                                         │  │
│  │      id, title, content_type,                │  │
│  │      file_url, thumbnail_url,                │  │
│  │      upload_status: 'completed',             │  │
│  │      metadata: {...}                         │  │
│  │    }                                         │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│   Celery Worker (Background Tasks)      │
│  ┌────────────────────────────────────┐ │
│  │ Video Transcoding (if video)       │ │
│  │ - FFmpeg to HLS format             │ │
│  │ - Multi-bitrate (480p/720p/1080p) │ │
│  │ - Save to /transcoded/             │ │
│  │ - Update DB: hls_master_playlist_* │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │ Thumbnail Generation               │ │
│  │ - Extract video frame / resize img │ │
│  │ - Save to /thumbnails/             │ │
│  │ - Update DB: thumbnail_*           │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

---

## 🛠️ FILE STORAGE SERVICE IMPLEMENTATION

### Storage Service Interface

```python
# backend-python/services/content/services/storage_service.py

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict
import hashlib
import shutil
from datetime import datetime
import uuid
from fastapi import UploadFile

class IStorageService(ABC):
    """Interface for content storage"""

    @abstractmethod
    async def save_file(
        self,
        file: UploadFile,
        content_type: str,
        organization_id: int
    ) -> Dict[str, str]:
        """
        Save uploaded file to storage

        Returns:
            {
                'storage_key': 'images/2025/01/org_4/abc123.jpg',
                'file_path': '/data/signage/content/uploads/...',
                'file_url': 'http://192.168.5.12:8001/content/...',
                'file_hash': 'sha256...',
                'file_size': 1234567
            }
        """
        pass

    @abstractmethod
    async def delete_file(self, storage_key: str) -> bool:
        """Delete file from storage"""
        pass

    @abstractmethod
    async def file_exists(self, storage_key: str) -> bool:
        """Check if file exists"""
        pass

    @abstractmethod
    async def get_file_info(self, storage_key: str) -> Optional[Dict]:
        """Get file metadata"""
        pass


class LocalFilesystemStorage(IStorageService):
    """Local filesystem storage implementation"""

    def __init__(
        self,
        base_path: str = "/data/signage/content",
        base_url: str = "http://192.168.5.12:8001"
    ):
        self.base_path = Path(base_path)
        self.base_url = base_url
        self.uploads_dir = self.base_path / "uploads"
        self.thumbnails_dir = self.base_path / "thumbnails"
        self.transcoded_dir = self.base_path / "transcoded"

        # Ensure directories exist
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        self.transcoded_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(
        self,
        file: UploadFile,
        content_type: str,
        organization_id: int
    ) -> Dict[str, str]:
        """
        Save file to local filesystem with organized structure

        Path structure: {type}/{year}/{month}/org_{org_id}/{uuid}.{ext}
        """
        # Generate unique filename
        file_extension = Path(file.filename).suffix.lower()
        unique_id = str(uuid.uuid4())

        # Create storage key
        now = datetime.now()
        storage_key = (
            f"{content_type}s/"  # images/, videos/, audio/ (plural)
            f"{now.year}/"
            f"{now.month:02d}/"
            f"org_{organization_id}/"
            f"{unique_id}{file_extension}"
        )

        # Full file path
        file_path = self.uploads_dir / storage_key
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate hash while saving (streaming)
        sha256_hash = hashlib.sha256()
        file_size = 0

        try:
            # Save file in chunks (memory efficient)
            with file_path.open("wb") as f:
                while chunk := await file.read(8192):  # 8KB chunks
                    f.write(chunk)
                    sha256_hash.update(chunk)
                    file_size += len(chunk)

            # Set file permissions (readable by nginx)
            file_path.chmod(0o644)

            # Generate URL
            file_url = f"{self.base_url}/content/{storage_key}"

            return {
                'storage_key': storage_key,
                'file_path': str(file_path),
                'file_url': file_url,
                'file_hash': sha256_hash.hexdigest(),
                'file_size': file_size
            }

        except Exception as e:
            # Cleanup on failure
            if file_path.exists():
                file_path.unlink()
            raise StorageException(f"Failed to save file: {e}")

    async def delete_file(self, storage_key: str) -> bool:
        """Delete file from filesystem"""
        file_path = self.uploads_dir / storage_key

        try:
            if file_path.exists():
                file_path.unlink()

                # Also delete associated files
                self._delete_thumbnails(storage_key)
                self._delete_transcoded(storage_key)

                return True
            return False
        except Exception as e:
            raise StorageException(f"Failed to delete file: {e}")

    async def file_exists(self, storage_key: str) -> bool:
        """Check if file exists"""
        file_path = self.uploads_dir / storage_key
        return file_path.exists()

    async def get_file_info(self, storage_key: str) -> Optional[Dict]:
        """Get file metadata from filesystem"""
        file_path = self.uploads_dir / storage_key

        if not file_path.exists():
            return None

        stat = file_path.stat()
        return {
            'file_size': stat.st_size,
            'modified_at': datetime.fromtimestamp(stat.st_mtime),
            'created_at': datetime.fromtimestamp(stat.st_ctime),
        }

    def _delete_thumbnails(self, storage_key: str):
        """Delete associated thumbnail files"""
        # storage_key: images/2025/01/org_4/abc123.jpg
        # thumbnail: thumbnails/2025/01/org_4/abc123_thumb.jpg

        parts = Path(storage_key).parts
        if len(parts) >= 4:
            thumb_key = f"{parts[1]}/{parts[2]}/{parts[3]}/{Path(parts[4]).stem}_thumb.jpg"
            thumb_path = self.thumbnails_dir / thumb_key
            if thumb_path.exists():
                thumb_path.unlink()

    def _delete_transcoded(self, storage_key: str):
        """Delete HLS transcoded directory"""
        parts = Path(storage_key).parts
        if len(parts) >= 4:
            transcoded_dir = self.transcoded_dir / f"{parts[1]}/{parts[2]}/{parts[3]}/{Path(parts[4]).stem}"
            if transcoded_dir.exists():
                shutil.rmtree(transcoded_dir)


# Storage service singleton
_storage_service: Optional[IStorageService] = None

def get_storage_service() -> IStorageService:
    """Get storage service instance (dependency injection)"""
    global _storage_service

    if _storage_service is None:
        # TODO: Read from config
        _storage_service = LocalFilesystemStorage(
            base_path="/data/signage/content",
            base_url="http://192.168.5.12:8001"
        )

    return _storage_service
```

---

## 📝 UPDATED UPLOAD USE CASE

```python
# backend-python/services/content/use_cases/upload_content.py

from fastapi import UploadFile
from typing import Dict, Optional
from ..domain.interfaces import IContentRepository
from ..domain.content import Content
from ..services.storage_service import IStorageService
from shared.errors import ValidationError, DuplicateError
import os

class UploadContentUseCase:
    """Upload content with custom storage"""

    def __init__(
        self,
        content_repo: IContentRepository,
        storage_service: IStorageService,
        metadata_extractor
    ):
        self.content_repo = content_repo
        self.storage = storage_service
        self.metadata = metadata_extractor

    # Supported formats
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mkv', '.avi', '.mov'}
    AUDIO_EXTENSIONS = {'.mp3', '.aac', '.m4a', '.ogg', '.wav', '.flac'}

    MAX_SIZES = {
        'image': 50 * 1024 * 1024,   # 50 MB
        'video': 500 * 1024 * 1024,  # 500 MB
        'audio': 100 * 1024 * 1024,  # 100 MB
    }

    async def execute(
        self,
        file: UploadFile,
        title: str,
        organization_id: int,
        uploaded_by: int,
        description: Optional[str] = None,
        duration: int = 10,
        is_active: bool = True
    ) -> Content:
        """
        Execute upload content use case

        Steps:
        1. Validate file (type, size, extension)
        2. Save to local filesystem via StorageService
        3. Check for duplicates (hash-based)
        4. Extract metadata via FFprobe
        5. Save to database
        6. Queue background tasks
        """

        # 1. Validate file
        content_type = self._validate_file(file)

        # 2. Save file to storage
        storage_result = await self.storage.save_file(
            file=file,
            content_type=content_type,
            organization_id=organization_id
        )

        # 3. Check for duplicate files (same hash + org)
        existing = self.content_repo.find_by_hash(
            file_hash=storage_result['file_hash'],
            organization_id=organization_id
        )
        if existing:
            # Cleanup uploaded file
            await self.storage.delete_file(storage_result['storage_key'])
            raise DuplicateError(
                f"File already exists: {existing.title} (ID: {existing.id})"
            )

        # 4. Extract metadata
        metadata = await self.metadata.extract(
            file_path=storage_result['file_path'],
            content_type=content_type
        )

        # 5. Auto-set duration for video/audio
        if content_type in ['video', 'audio'] and metadata.get('duration'):
            duration = int(metadata['duration'])

        # 6. Create domain entity
        content = Content(
            id=None,
            title=title,
            description=description,
            content_type=content_type,

            # Storage fields (custom system)
            file_path=storage_result['file_path'],
            file_url=storage_result['file_url'],
            storage_key=storage_result['storage_key'],
            file_hash=storage_result['file_hash'],
            file_size=storage_result['file_size'],

            organization_id=organization_id,
            uploaded_by=uploaded_by,
            duration=duration,
            is_active=is_active,

            # Metadata
            mime_type=file.content_type,
            original_filename=file.filename,
            file_extension=os.path.splitext(file.filename)[1].lower(),
            resolution=metadata.get('resolution'),
            width=metadata.get('width'),
            height=metadata.get('height'),
            # ... other metadata fields

            upload_status='completed'
        )

        # Validate business rules
        content.__post_init__()

        # 7. Save to database
        saved_content = self.content_repo.create(content)

        # 8. Queue background tasks
        if content_type == 'video':
            from app.tasks.content_tasks import transcode_to_hls
            transcode_to_hls.delay(saved_content.id)

        if content_type in ['video', 'image']:
            from app.tasks.content_tasks import generate_thumbnail
            generate_thumbnail.delay(saved_content.id)

        return saved_content

    def _validate_file(self, file: UploadFile) -> str:
        """Validate file type and extension"""
        filename = file.filename.lower()
        ext = os.path.splitext(filename)[1]

        if ext in self.IMAGE_EXTENSIONS:
            content_type = 'image'
        elif ext in self.VIDEO_EXTENSIONS:
            content_type = 'video'
        elif ext in self.AUDIO_EXTENSIONS:
            content_type = 'audio'
        else:
            raise ValidationError(
                f"Unsupported file extension: {ext}"
            )

        # Validate MIME type
        mime = file.content_type
        if content_type == 'image' and not mime.startswith('image/'):
            raise ValidationError(f"MIME mismatch. Expected image/*, got {mime}")
        elif content_type == 'video' and not mime.startswith('video/'):
            raise ValidationError(f"MIME mismatch. Expected video/*, got {mime}")
        elif content_type == 'audio' and not mime.startswith('audio/'):
            raise ValidationError(f"MIME mismatch. Expected audio/*, got {mime}")

        return content_type
```

---

## 🎬 CELERY TASKS (Updated for Custom Storage)

```python
# backend-python/tasks/content_tasks.py

from celery import shared_task
import subprocess
from pathlib import Path
from PIL import Image
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def transcode_to_hls(self, content_id: int):
    """
    Transcode video to HLS format using FFmpeg

    Creates multi-bitrate variants:
    - 1080p @ 5000 kbps
    - 720p  @ 2500 kbps
    - 480p  @ 1000 kbps
    """
    from services.content.repositories.content_repo import ContentRepository
    from services.content.services.storage_service import get_storage_service

    repo = ContentRepository()
    storage = get_storage_service()

    try:
        # Get content
        content = repo.find_by_id_internal(content_id)
        if not content:
            raise ValueError(f"Content {content_id} not found")

        # Update status
        repo.update_transcoding_status(content_id, 'processing', self.request.id)

        # Parse storage key: videos/2025/01/org_4/abc123.mp4
        input_path = Path(content.file_path)
        storage_parts = Path(content.storage_key).parts

        # Output directory: transcoded/2025/01/org_4/abc123/
        output_dir = (
            Path("/data/signage/content/transcoded") /
            storage_parts[1] / storage_parts[2] / storage_parts[3] /
            input_path.stem
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        # FFmpeg HLS transcoding command
        master_playlist = output_dir / "master.m3u8"

        cmd = [
            'ffmpeg',
            '-i', str(input_path),

            # 1080p variant
            '-vf', 'scale=-2:1080',
            '-c:v', 'libx264',
            '-b:v', '5000k',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-f', 'hls',
            '-hls_time', '6',
            '-hls_playlist_type', 'vod',
            '-hls_segment_filename', str(output_dir / '1080p_%03d.ts'),
            str(output_dir / '1080p.m3u8'),

            # 720p variant
            '-vf', 'scale=-2:720',
            '-c:v', 'libx264',
            '-b:v', '2500k',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-f', 'hls',
            '-hls_time', '6',
            '-hls_playlist_type', 'vod',
            '-hls_segment_filename', str(output_dir / '720p_%03d.ts'),
            str(output_dir / '720p.m3u8'),

            # 480p variant
            '-vf', 'scale=-2:480',
            '-c:v', 'libx264',
            '-b:v', '1000k',
            '-c:a', 'aac',
            '-b:a', '96k',
            '-f', 'hls',
            '-hls_time', '6',
            '-hls_playlist_type', 'vod',
            '-hls_segment_filename', str(output_dir / '480p_%03d.ts'),
            str(output_dir / '480p.m3u8'),
        ]

        # Execute FFmpeg
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")

        # Create master playlist manually
        with master_playlist.open('w') as f:
            f.write('#EXTM3U\n')
            f.write('#EXT-X-VERSION:3\n')
            f.write('#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080\n')
            f.write('1080p.m3u8\n')
            f.write('#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720\n')
            f.write('720p.m3u8\n')
            f.write('#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION=854x480\n')
            f.write('480p.m3u8\n')

        # Generate URLs
        hls_storage_key = f"{storage_parts[1]}/{storage_parts[2]}/{storage_parts[3]}/{input_path.stem}/master.m3u8"
        hls_url = f"http://192.168.5.12:8001/streaming/{hls_storage_key}"

        # Update database
        repo.update_hls_info(
            content_id=content_id,
            master_playlist_path=str(master_playlist),
            master_playlist_url=hls_url,
            variants=[
                {'resolution': '1080p', 'bitrate': 5000, 'playlist': '1080p.m3u8'},
                {'resolution': '720p', 'bitrate': 2500, 'playlist': '720p.m3u8'},
                {'resolution': '480p', 'bitrate': 1000, 'playlist': '480p.m3u8'},
            ]
        )

        repo.update_transcoding_status(content_id, 'completed', self.request.id)

        logger.info(f"Transcoding completed for content {content_id}")
        return {"status": "success", "content_id": content_id}

    except Exception as e:
        logger.error(f"Transcoding failed for content {content_id}: {e}")
        repo.update_transcoding_status(content_id, 'failed', self.request.id, str(e))
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True)
def generate_thumbnail(self, content_id: int):
    """
    Generate thumbnail for video or image

    - Video: Extract frame at 5 seconds
    - Image: Create optimized thumbnail (400x300)
    """
    from services.content.repositories.content_repo import ContentRepository

    repo = ContentRepository()

    try:
        content = repo.find_by_id_internal(content_id)
        if not content:
            raise ValueError(f"Content {content_id} not found")

        input_path = Path(content.file_path)
        storage_parts = Path(content.storage_key).parts

        # Output path: thumbnails/2025/01/org_4/abc123_thumb.jpg
        thumbnail_dir = (
            Path("/data/signage/content/thumbnails") /
            storage_parts[1] / storage_parts[2] / storage_parts[3]
        )
        thumbnail_dir.mkdir(parents=True, exist_ok=True)
        thumbnail_path = thumbnail_dir / f"{input_path.stem}_thumb.jpg"

        if content.content_type == 'video':
            # Extract frame at 5 seconds using FFmpeg
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-ss', '5',  # Seek to 5 seconds
                '-vframes', '1',  # Extract 1 frame
                '-vf', 'scale=400:-1',  # Width 400px, maintain aspect ratio
                '-y',  # Overwrite
                str(thumbnail_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True)

        elif content.content_type == 'image':
            # Resize image using Pillow
            with Image.open(input_path) as img:
                img.thumbnail((400, 300), Image.Resampling.LANCZOS)
                img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)

        # Generate URL
        thumbnail_key = f"{storage_parts[1]}/{storage_parts[2]}/{storage_parts[3]}/{input_path.stem}_thumb.jpg"
        thumbnail_url = f"http://192.168.5.12:8001/thumbnails/{thumbnail_key}"

        # Update database
        repo.update_thumbnail(
            content_id=content_id,
            thumbnail_path=str(thumbnail_path),
            thumbnail_url=thumbnail_url
        )

        logger.info(f"Thumbnail generated for content {content_id}")
        return {"status": "success", "thumbnail_url": thumbnail_url}

    except Exception as e:
        logger.error(f"Thumbnail generation failed for content {content_id}: {e}")
        raise self.retry(exc=e, countdown=30, max_retries=2)


@shared_task
def cleanup_orphaned_files():
    """
    Daily cleanup task: Remove files for deleted content
    """
    from services.content.repositories.content_repo import ContentRepository
    from services.content.services.storage_service import get_storage_service

    repo = ContentRepository()
    storage = get_storage_service()

    # Find soft-deleted content older than 30 days
    orphaned = repo.find_deleted_content(days=30)

    for content in orphaned:
        try:
            # Delete from filesystem
            await storage.delete_file(content.storage_key)

            # Hard delete from database
            repo.hard_delete(content.id)

            logger.info(f"Cleaned up content {content.id}")
        except Exception as e:
            logger.error(f"Failed to cleanup content {content.id}: {e}")

    return {"cleaned": len(orphaned)}
```

---

## 🚀 DOCKER & NGINX CONFIGURATION

### Docker Compose Update

```yaml
# docker/docker-compose.yml

services:
  backend-api:
    build: ../backend-python
    volumes:
      - ../backend-python:/app
      - signage-content:/data/signage/content  # Content storage volume
    environment:
      - STORAGE_BASE_PATH=/data/signage/content
      - STORAGE_BASE_URL=http://192.168.5.12:8001

  nginx:
    image: nginx:alpine
    ports:
      - "8001:8001"
    volumes:
      - ./nginx/content.conf:/etc/nginx/conf.d/content.conf
      - signage-content:/data/signage/content:ro  # Read-only for nginx
    depends_on:
      - backend-api

  celery-worker:
    build: ../backend-python
    command: celery -A app.tasks worker --loglevel=info --concurrency=4
    volumes:
      - ../backend-python:/app
      - signage-content:/data/signage/content  # Read-write for processing
    depends_on:
      - redis
      - postgres

volumes:
  signage-content:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/signage/content  # Host path
```

### Nginx Configuration

```nginx
# docker/nginx/content.conf

server {
    listen 8001;
    server_name 192.168.5.12;

    client_max_body_size 500M;  # Max upload size

    # API endpoints (proxy to backend)
    location /api/ {
        proxy_pass http://backend-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Timeouts for large uploads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Original content files
    location /content/ {
        alias /data/signage/content/uploads/;

        # Performance
        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;

        # Caching
        expires 30d;
        add_header Cache-Control "public, immutable";

        # CORS
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, OPTIONS";

        # Security
        add_header X-Content-Type-Options nosniff;
    }

    # HLS streaming
    location /streaming/ {
        alias /data/signage/content/transcoded/;

        # HLS MIME types
        types {
            application/vnd.apple.mpegurl m3u8;
            video/mp2t ts;
        }

        # No cache for playlists (they can change)
        add_header Cache-Control "no-cache";

        # Cache segments
        location ~* \.ts$ {
            expires 1d;
            add_header Cache-Control "public";
        }

        # CORS
        add_header Access-Control-Allow-Origin *;
    }

    # Thumbnails
    location /thumbnails/ {
        alias /data/signage/content/thumbnails/;

        expires 7d;
        add_header Cache-Control "public";
        add_header Access-Control-Allow-Origin *;
    }
}
```

---

## 💡 MIGRATION STRATEGY (Future: MinIO/S3)

Karena kita design dengan **abstraction layer** (`IStorageService`), migrasi ke MinIO atau S3 di masa depan sangat mudah:

### MinIO Storage Implementation (Future)

```python
# backend-python/services/content/services/minio_storage.py

from minio import Minio
from ..services.storage_service import IStorageService

class MinIOStorage(IStorageService):
    """MinIO S3-compatible storage implementation"""

    def __init__(
        self,
        endpoint: str = "minio:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        bucket: str = "signage-content",
        secure: bool = False
    ):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket = bucket

        # Create bucket if not exists
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    async def save_file(
        self,
        file: UploadFile,
        content_type: str,
        organization_id: int
    ) -> Dict[str, str]:
        """Upload file to MinIO"""
        storage_key = self._generate_storage_key(...)

        # Upload to MinIO
        self.client.put_object(
            bucket_name=self.bucket,
            object_name=storage_key,
            data=file.file,
            length=-1,  # Unknown size, stream upload
            content_type=file.content_type,
            part_size=10*1024*1024  # 10MB parts
        )

        # Generate presigned URL (temporary access)
        file_url = self.client.presigned_get_object(
            bucket_name=self.bucket,
            object_name=storage_key,
            expires=timedelta(days=7)
        )

        return {
            'storage_key': storage_key,
            'file_path': f"s3://{self.bucket}/{storage_key}",
            'file_url': file_url,
            # ...
        }
```

**Migration Steps:**
1. Update config: `STORAGE_TYPE=minio`
2. Run data migration script (copy local files to MinIO)
3. Update database URLs
4. Switch storage service implementation
5. Done! Zero code changes in use cases/routes

---

## ✅ BENEFITS CUSTOM STORAGE vs ANTHIAS

| Aspect | Custom Storage (Ours) | Anthias |
|--------|----------------------|---------|
| **Control** | ✅ Full control | ❌ Limited |
| **Dependency** | ✅ Zero external | ❌ Depends on Anthias |
| **Customization** | ✅ Easy to modify | ❌ Fixed API |
| **Scalability** | ✅ MinIO/S3 ready | ❌ Anthias only |
| **Multi-tenant** | ✅ Built-in | ⚠️ Manual |
| **Performance** | ✅ Direct nginx | ⚠️ API overhead |
| **Backup** | ✅ Standard tools | ⚠️ Anthias-specific |
| **Maintenance** | ✅ Our responsibility | ❌ Depends on Anthias updates |
| **Cost** | ✅ Free (self-hosted) | ✅ Free (self-hosted) |

---

## 📅 UPDATED TIMELINE

| Phase | Tasks | Duration | Notes |
|-------|-------|----------|-------|
| **Phase 0** | Storage Service Implementation | 1-2 days | New phase |
| **Phase 1** | Database Models (updated schema) | 1-2 days | Remove Anthias fields |
| **Phase 2** | Domain Layer | 2-3 days | Same |
| **Phase 3** | Repository Implementation | 2-3 days | Updated for new schema |
| **Phase 4** | Use Cases (with custom storage) | 3-4 days | Updated |
| **Phase 5** | API Routes | 2-3 days | Same |
| **Phase 6** | Frontend | 3-4 days | Same |
| **Phase 7** | Celery Tasks (updated) | 2-3 days | Updated for filesystem |
| **Phase 8** | Nginx Configuration | 1 day | New - file serving |
| **Phase 9** | Testing & QA | 2-3 days | Same |
| **Phase 10** | Deployment | 1 day | Docker volumes |
| | | | |
| **TOTAL** | **Complete Implementation** | **20-28 days** | **3-4 weeks** |

---

## 🎯 SUMMARY

### Key Changes dari Anthias ke Custom Storage:

1. ✅ **Storage Service Layer** - Abstraction untuk flexibility
2. ✅ **Local Filesystem** - Primary storage (Phase 1)
3. ✅ **Nginx Direct Serving** - Better performance
4. ✅ **Updated Database Schema** - Custom fields, no Anthias references
5. ✅ **File Organization** - Type/Year/Month/Org structure
6. ✅ **Hash-based Deduplication** - Save storage space
7. ✅ **Migration Ready** - Easy switch to MinIO/S3 later
8. ✅ **Full Control** - Customize everything

### Advantages:

- 🚀 **Faster Development** - No external API integration
- 🛠️ **More Flexible** - Easy to add features
- 📈 **Scalable** - MinIO/S3 migration path clear
- 💰 **Cost Effective** - No external service fees
- 🔒 **Secure** - Full control over data
- 🎯 **Clean Architecture** - Follows our patterns

---

## 🏗️ BACKEND SERVICE STRUCTURE (Clean Architecture)

**Following Backend-Python README patterns exactly:**

### Directory Structure

```
backend-python/services/content/
├── domain/                         # 📦 CORE - Business Logic (No dependencies)
│   ├── __init__.py
│   ├── content.py                 # Content entity (pure Python dataclass)
│   └── interfaces.py              # IContentRepository interface
├── use_cases/                     # 🎯 APPLICATION LOGIC (1 file = 1 use case)
│   ├── __init__.py
│   ├── upload_content.py          # Upload & save content
│   ├── list_content.py            # List content with filters
│   ├── get_content.py             # Get single content by ID
│   ├── update_content.py          # Update content metadata
│   ├── delete_content.py          # Soft delete content
│   └── get_content_stats.py       # Get storage statistics
├── repositories/                  # 🔧 INFRASTRUCTURE - Database
│   ├── __init__.py
│   ├── models.py                  # SQLAlchemy ContentModel
│   └── content_repo.py            # ContentRepository implementation
├── infrastructure/                # 🔧 INFRASTRUCTURE - Storage
│   ├── __init__.py
│   └── storage/
│       ├── __init__.py
│       ├── interfaces.py          # IStorageService interface
│       ├── local_storage.py       # LocalFilesystemStorage
│       └── metadata_extractor.py  # FFprobe metadata extraction
├── dtos.py                        # 📝 Request/Response DTOs (Pydantic)
└── routes.py                      # 🌐 HTTP - FastAPI endpoints with DI
```

**Dependency Flow:**
```
routes.py → use_cases/ → domain/ interfaces
              ↓
          repositories/ + infrastructure/
```

### Integration with Shared Utilities

#### 1. API Routes Registration

**Add to:** `backend-python/shared/api_routes.py`

```python
# shared/api_routes.py

API_V1 = "/api/v1"

# ... existing routes ...

class ContentRoutes:
    """Content endpoints"""
    BASE = f"{API_V1}/content"
    LIST = f"{API_V1}/content"                          # GET - List content
    GET = lambda id: f"{API_V1}/content/{id}"           # GET - Get by ID
    UPLOAD = f"{API_V1}/content/upload"                 # POST - Upload file
    UPDATE = lambda id: f"{API_V1}/content/{id}"        # PUT - Update metadata
    DELETE = lambda id: f"{API_V1}/content/{id}"        # DELETE - Soft delete
    STATS = f"{API_V1}/content/stats"                   # GET - Storage stats

    # File serving (via backend - optional)
    SERVE = lambda id: f"{API_V1}/content/{id}/serve"   # GET - Serve file
```

#### 2. Error Handling with Shared Utilities

**Use existing:** `backend-python/shared/errors.py`

```python
# In use_cases/upload_content.py
from shared.errors import ValidationError, DuplicateError, StorageException

class UploadContentUseCase:
    def execute(self, ...):
        # Validate file type
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValidationError(
                f"File type {ext} not supported",
                details={"supported": list(self.SUPPORTED_EXTENSIONS)}
            )

        # Check duplicate
        if existing_content:
            raise DuplicateError(
                f"File already exists",
                details={"existing_id": existing_content.id}
            )
```

#### 3. Response Formatting

**Use existing:** `backend-python/shared/responses.py`

```python
# In routes.py
from shared.responses import success_response, error_response, paginated_response

@router.post(ContentRoutes.UPLOAD)
async def upload_content(
    file: UploadFile,
    title: str = Form(...),
    # ... other params
):
    try:
        content = await upload_use_case.execute(...)

        return success_response(
            data=ContentResponse.from_entity(content),
            message="Content uploaded successfully",
            status_code=201
        )
    except ValidationError as e:
        return error_response(
            message=str(e),
            details=e.details,
            status_code=400
        )

@router.get(ContentRoutes.LIST)
async def list_content(
    skip: int = 0,
    limit: int = 20,
    content_type: Optional[str] = None
):
    contents, total = list_use_case.execute(skip, limit, content_type)

    return paginated_response(
        data=[ContentResponse.from_entity(c) for c in contents],
        total=total,
        skip=skip,
        limit=limit
    )
```

#### 4. Audit Logging Integration

**Use existing:** `backend-python/shared/logging.py` + `services/audit/`

```python
# In routes.py
from shared.logging import AuditLogger
from services.audit.use_cases.create_audit_log import CreateAuditLogUseCase
from services.audit.repositories.audit_log_repo import get_audit_log_repository

# Dependency injection for audit logger
def get_audit_logger(
    create_audit_log_use_case = Depends(get_create_audit_log_use_case)
) -> AuditLogger:
    return AuditLogger(create_audit_log_use_case=create_audit_log_use_case)

@router.post(ContentRoutes.UPLOAD)
async def upload_content(
    # ... params
    audit_logger: AuditLogger = Depends(get_audit_logger),
    request: Request
):
    content = await upload_use_case.execute(...)

    # Log audit trail
    await audit_logger.log_action(
        user_id=current_user["id"],
        organization_id=current_user["organization_id"],
        action="content.upload",
        resource_type="content",
        resource_id=content.id,
        details={
            "title": content.title,
            "content_type": content.content_type,
            "file_size": content.file_size,
            "mime_type": content.mime_type
        },
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

    return success_response(...)
```

### Domain Layer Example

```python
# domain/content.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from shared.errors import ValidationError

@dataclass
class Content:
    """Content domain entity - Pure business logic"""

    id: Optional[int]
    title: str
    description: Optional[str]
    content_type: str  # 'image', 'video', 'audio'

    # Storage fields (custom system)
    file_path: str
    file_url: str
    storage_key: str
    file_hash: str
    file_size: int

    # Display settings
    duration: int
    is_active: bool

    # File metadata
    mime_type: str
    original_filename: str
    file_extension: str
    resolution: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

    # Multi-tenant
    organization_id: int
    uploaded_by: int

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    # Valid types
    VALID_TYPES = ['image', 'video', 'audio']

    def __post_init__(self):
        """Validate business rules"""
        if not self.title or len(self.title.strip()) == 0:
            raise ValidationError("Title is required")

        if len(self.title) > 200:
            raise ValidationError("Title must be <= 200 characters")

        if self.content_type not in self.VALID_TYPES:
            raise ValidationError(
                f"Content type must be one of: {', '.join(self.VALID_TYPES)}"
            )

        if self.duration < 1:
            raise ValidationError("Duration must be at least 1 second")

        if self.file_size < 0:
            raise ValidationError("File size cannot be negative")

    def is_image(self) -> bool:
        return self.content_type == 'image'

    def is_video(self) -> bool:
        return self.content_type == 'video'

    def is_audio(self) -> bool:
        return self.content_type == 'audio'

    def is_deleted(self) -> bool:
        return self.deleted_at is not None
```

```python
# domain/interfaces.py

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from .content import Content

class IContentRepository(ABC):
    """Content repository interface"""

    @abstractmethod
    def create(self, content: Content) -> Content:
        """Create new content"""
        pass

    @abstractmethod
    def find_by_id(self, content_id: int, organization_id: int) -> Optional[Content]:
        """Find content by ID (org-scoped)"""
        pass

    @abstractmethod
    def find_all(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
        content_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Content], int]:
        """List content with filters (returns items + total count)"""
        pass

    @abstractmethod
    def find_by_hash(self, file_hash: str, organization_id: int) -> Optional[Content]:
        """Find content by file hash (deduplication check)"""
        pass

    @abstractmethod
    def update(self, content: Content) -> Content:
        """Update content metadata"""
        pass

    @abstractmethod
    def soft_delete(self, content_id: int, organization_id: int) -> bool:
        """Soft delete content (set deleted_at)"""
        pass

    @abstractmethod
    def get_storage_stats(self, organization_id: int) -> dict:
        """Get storage statistics"""
        pass
```

### Dependency Injection in Routes

```python
# routes.py

from fastapi import APIRouter, Depends, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.api_routes import ContentRoutes
from shared.responses import success_response, error_response, paginated_response
from shared.errors import ValidationError, NotFoundError

from .repositories.content_repo import ContentRepository
from .infrastructure.storage.local_storage import LocalFilesystemStorage
from .infrastructure.storage.metadata_extractor import MetadataExtractor
from .use_cases.upload_content import UploadContentUseCase
from .use_cases.list_content import ListContentUseCase
from .use_cases.get_content import GetContentUseCase
from .use_cases.update_content import UpdateContentUseCase
from .use_cases.delete_content import DeleteContentUseCase
from .dtos import ContentResponse, ContentUpdateRequest

router = APIRouter(prefix="/api/v1/content", tags=["content"])

# Dependency injection functions
def get_content_repository(db: Session = Depends(get_db)) -> ContentRepository:
    return ContentRepository(db)

def get_storage_service() -> LocalFilesystemStorage:
    return LocalFilesystemStorage(
        base_path="/data/signage/content",
        base_url="http://192.168.5.12:8001"
    )

def get_metadata_extractor() -> MetadataExtractor:
    return MetadataExtractor()

def get_upload_content_use_case(
    content_repo: ContentRepository = Depends(get_content_repository),
    storage_service: LocalFilesystemStorage = Depends(get_storage_service),
    metadata_extractor: MetadataExtractor = Depends(get_metadata_extractor)
) -> UploadContentUseCase:
    return UploadContentUseCase(content_repo, storage_service, metadata_extractor)

def get_list_content_use_case(
    content_repo: ContentRepository = Depends(get_content_repository)
) -> ListContentUseCase:
    return ListContentUseCase(content_repo)

# Endpoints
@router.post("/upload", response_model=dict)
async def upload_content(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    duration: int = Form(10),
    is_active: bool = Form(True),
    upload_use_case: UploadContentUseCase = Depends(get_upload_content_use_case),
    current_user: dict = Depends(get_current_user),  # From auth service
    request: Request
):
    """Upload content file"""
    try:
        content = await upload_use_case.execute(
            file=file,
            title=title,
            description=description,
            organization_id=current_user["organization_id"],
            uploaded_by=current_user["id"],
            duration=duration,
            is_active=is_active
        )

        return success_response(
            data=ContentResponse.from_entity(content),
            message="Content uploaded successfully",
            status_code=201
        )
    except ValidationError as e:
        return error_response(str(e), status_code=400, details=e.details)
    except Exception as e:
        return error_response(f"Upload failed: {str(e)}", status_code=500)

@router.get("", response_model=dict)
async def list_content(
    skip: int = 0,
    limit: int = 20,
    content_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    list_use_case: ListContentUseCase = Depends(get_list_content_use_case),
    current_user: dict = Depends(get_current_user)
):
    """List content with filters"""
    contents, total = list_use_case.execute(
        organization_id=current_user["organization_id"],
        skip=skip,
        limit=limit,
        content_type=content_type,
        is_active=is_active
    )

    return paginated_response(
        data=[ContentResponse.from_entity(c) for c in contents],
        total=total,
        skip=skip,
        limit=limit
    )
```

### DTOs Example

```python
# dtos.py

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime

class ContentUploadRequest(BaseModel):
    """Upload content request"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    duration: int = Field(10, ge=1, le=3600)
    is_active: bool = True

class ContentUpdateRequest(BaseModel):
    """Update content metadata request"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    duration: Optional[int] = Field(None, ge=1, le=3600)
    is_active: Optional[bool] = None

class ContentResponse(BaseModel):
    """Content response"""
    id: int
    title: str
    description: Optional[str]
    content_type: str

    file_url: str
    thumbnail_url: Optional[str]
    hls_master_playlist_url: Optional[str]

    duration: int
    is_active: bool

    file_size: int
    mime_type: str
    original_filename: str
    resolution: Optional[str]

    organization_id: int
    uploaded_by: int

    created_at: datetime
    updated_at: datetime

    @staticmethod
    def from_entity(content) -> "ContentResponse":
        """Convert domain entity to response DTO"""
        return ContentResponse(
            id=content.id,
            title=content.title,
            description=content.description,
            content_type=content.content_type,
            file_url=content.file_url,
            thumbnail_url=content.thumbnail_url,
            hls_master_playlist_url=content.hls_master_playlist_url,
            duration=content.duration,
            is_active=content.is_active,
            file_size=content.file_size,
            mime_type=content.mime_type,
            original_filename=content.original_filename,
            resolution=content.resolution,
            organization_id=content.organization_id,
            uploaded_by=content.uploaded_by,
            created_at=content.created_at,
            updated_at=content.updated_at
        )

class ContentStatsResponse(BaseModel):
    """Storage statistics response"""
    total_files: int
    total_size_bytes: int
    total_size_readable: str
    by_type: Dict[str, Dict[str, Any]]
```

---

## 🎨 FRONTEND FEATURE STRUCTURE (Modular + Clean + Centralized)

**Following CMS-Vite README patterns exactly:**

### Directory Structure

```
cms-vite/src/features/content/
├── components/                    # Feature-specific UI components
│   ├── ContentTable.tsx          # Main content list table
│   ├── ContentCard.tsx           # Grid view card
│   ├── ContentModal.tsx          # View/Edit content modal
│   ├── UploadModal.tsx           # Upload content modal
│   ├── ContentFilters.tsx        # Filter controls (type, active, search)
│   ├── ContentActions.tsx        # Bulk actions (delete, activate)
│   ├── ContentTypeBadge.tsx      # Type indicator badge
│   ├── ContentStatusBadge.tsx    # Active/Inactive badge
│   ├── ContentPreview.tsx        # Image/video preview
│   ├── UploadProgress.tsx        # Upload progress bar
│   └── ContentStats.tsx          # Storage statistics widget
├── hooks/                        # React Query + custom hooks
│   ├── useContent.ts            # Query: List content
│   ├── useContentById.ts        # Query: Get single content
│   ├── useUploadContent.ts      # Mutation: Upload file
│   ├── useUpdateContent.ts      # Mutation: Update metadata
│   ├── useDeleteContent.ts      # Mutation: Delete content
│   ├── useContentStats.ts       # Query: Storage stats
│   └── useContentFilters.ts     # Custom: Filter state management
├── services/                     # API calls (feature-specific)
│   └── contentApi.ts            # Content API client
└── types/                        # TypeScript types
    └── content.ts               # Content interfaces
```

### Integration with Centralized API

#### 1. Add Endpoints to Centralized Config

**Update:** `cms-vite/src/lib/api/endpoints.ts`

```typescript
// lib/api/endpoints.ts

export const API_ENDPOINTS = {
  // ... existing endpoints ...

  // Content
  CONTENT: {
    LIST: `${API_V1}/content`,                              // GET
    GET: (id: number) => `${API_V1}/content/${id}`,        // GET
    UPLOAD: `${API_V1}/content/upload`,                    // POST (multipart)
    UPDATE: (id: number) => `${API_V1}/content/${id}`,     // PUT
    DELETE: (id: number) => `${API_V1}/content/${id}`,     // DELETE
    STATS: `${API_V1}/content/stats`,                      // GET
  },
} as const;
```

#### 2. Content API Service

```typescript
// features/content/services/contentApi.ts

import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type { Content, ContentUpload, ContentUpdate, ContentStats } from '../types/content';

export const contentApi = {
  /**
   * List content with filters
   */
  getAll: async (params?: {
    skip?: number;
    limit?: number;
    content_type?: 'image' | 'video' | 'audio';
    is_active?: boolean;
  }) => {
    const response = await apiClient.get(API_ENDPOINTS.CONTENT.LIST, { params });
    return response.data;
  },

  /**
   * Get content by ID
   */
  getById: async (id: number) => {
    const response = await apiClient.get(API_ENDPOINTS.CONTENT.GET(id));
    return response.data.data;
  },

  /**
   * Upload content file
   */
  upload: async (data: ContentUpload, onUploadProgress?: (progress: number) => void) => {
    const formData = new FormData();
    formData.append('file', data.file);
    formData.append('title', data.title);
    if (data.description) formData.append('description', data.description);
    formData.append('duration', data.duration.toString());
    formData.append('is_active', data.is_active.toString());

    const response = await apiClient.post(API_ENDPOINTS.CONTENT.UPLOAD, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onUploadProgress?.(progress);
        }
      },
    });

    return response.data.data;
  },

  /**
   * Update content metadata
   */
  update: async (id: number, data: ContentUpdate) => {
    const response = await apiClient.put(API_ENDPOINTS.CONTENT.UPDATE(id), data);
    return response.data.data;
  },

  /**
   * Delete content (soft delete)
   */
  delete: async (id: number) => {
    const response = await apiClient.delete(API_ENDPOINTS.CONTENT.DELETE(id));
    return response.data;
  },

  /**
   * Get storage statistics
   */
  getStats: async () => {
    const response = await apiClient.get(API_ENDPOINTS.CONTENT.STATS);
    return response.data.data;
  },
};
```

#### 3. React Query Hooks

```typescript
// features/content/hooks/useContent.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contentApi } from '../services/contentApi';
import { useToast } from '@/lib/notifications/toast';
import type { ContentUpload, ContentUpdate } from '../types/content';

const QUERY_KEY = 'content';

/**
 * List content with filters
 */
export function useContent(params?: {
  skip?: number;
  limit?: number;
  content_type?: 'image' | 'video' | 'audio';
  is_active?: boolean;
}) {
  return useQuery({
    queryKey: [QUERY_KEY, 'list', params],
    queryFn: () => contentApi.getAll(params),
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Get single content by ID
 */
export function useContentById(id: number) {
  return useQuery({
    queryKey: [QUERY_KEY, 'detail', id],
    queryFn: () => contentApi.getById(id),
    enabled: !!id,
  });
}

/**
 * Upload content mutation
 */
export function useUploadContent() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (data: { upload: ContentUpload; onProgress?: (progress: number) => void }) =>
      contentApi.upload(data.upload, data.onProgress),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      toast({
        title: 'Upload berhasil',
        description: 'Content berhasil diupload',
        variant: 'success',
      });
    },

    onError: (error: any) => {
      toast({
        title: 'Upload gagal',
        description: error.response?.data?.message || 'Terjadi kesalahan saat upload',
        variant: 'destructive',
      });
    },
  });
}

/**
 * Update content mutation
 */
export function useUpdateContent() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ContentUpdate }) =>
      contentApi.update(id, data),

    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY, 'detail', variables.id] });
      toast({
        title: 'Update berhasil',
        description: 'Content berhasil diupdate',
        variant: 'success',
      });
    },

    onError: (error: any) => {
      toast({
        title: 'Update gagal',
        description: error.response?.data?.message || 'Terjadi kesalahan',
        variant: 'destructive',
      });
    },
  });
}

/**
 * Delete content mutation
 */
export function useDeleteContent() {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: (id: number) => contentApi.delete(id),

    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [QUERY_KEY] });
      toast({
        title: 'Hapus berhasil',
        description: 'Content berhasil dihapus',
        variant: 'success',
      });
    },

    onError: (error: any) => {
      toast({
        title: 'Hapus gagal',
        description: error.response?.data?.message || 'Terjadi kesalahan',
        variant: 'destructive',
      });
    },
  });
}

/**
 * Get storage statistics
 */
export function useContentStats() {
  return useQuery({
    queryKey: [QUERY_KEY, 'stats'],
    queryFn: () => contentApi.getStats(),
    staleTime: 60000, // 1 minute
  });
}
```

#### 4. TypeScript Types

```typescript
// features/content/types/content.ts

export interface Content {
  id: number;
  title: string;
  description?: string;
  content_type: 'image' | 'video' | 'audio';

  file_url: string;
  thumbnail_url?: string;
  hls_master_playlist_url?: string;

  duration: number;
  is_active: boolean;

  file_size: number;
  mime_type: string;
  original_filename: string;
  resolution?: string;

  organization_id: number;
  uploaded_by: number;

  created_at: string;
  updated_at: string;
}

export interface ContentUpload {
  file: File;
  title: string;
  description?: string;
  duration: number;
  is_active: boolean;
}

export interface ContentUpdate {
  title?: string;
  description?: string;
  duration?: number;
  is_active?: boolean;
}

export interface ContentStats {
  total_files: number;
  total_size_bytes: number;
  total_size_readable: string;
  by_type: {
    [key: string]: {
      count: number;
      size_bytes: number;
      size_readable: string;
    };
  };
}

export interface ContentListParams {
  skip?: number;
  limit?: number;
  content_type?: 'image' | 'video' | 'audio';
  is_active?: boolean;
}
```

#### 5. Component Example (Upload Modal)

```typescript
// features/content/components/UploadModal.tsx

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/shared/components/ui/dialog';
import { Button } from '@/shared/components/ui/button';
import { Input } from '@/shared/components/ui/input';
import { Textarea } from '@/shared/components/ui/textarea';
import { useUploadContent } from '../hooks/useContent';
import { UploadProgress } from './UploadProgress';
import type { ContentUpload } from '../types/content';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function UploadModal({ isOpen, onClose }: UploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const { register, handleSubmit, reset, formState: { errors } } = useForm<Omit<ContentUpload, 'file'>>();
  const uploadMutation = useUploadContent();

  const onSubmit = async (data: Omit<ContentUpload, 'file'>) => {
    if (!file) return;

    await uploadMutation.mutateAsync({
      upload: { ...data, file },
      onProgress: setUploadProgress,
    });

    reset();
    setFile(null);
    setUploadProgress(0);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Upload Content</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          {/* File input */}
          <div>
            <Input
              type="file"
              accept="image/*,video/*,audio/*"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
          </div>

          {/* Title */}
          <div>
            <Input
              placeholder="Content title"
              {...register('title', { required: 'Title is required' })}
            />
            {errors.title && <p className="text-red-500 text-sm">{errors.title.message}</p>}
          </div>

          {/* Description */}
          <div>
            <Textarea
              placeholder="Description (optional)"
              {...register('description')}
            />
          </div>

          {/* Duration */}
          <div>
            <Input
              type="number"
              placeholder="Duration (seconds)"
              defaultValue={10}
              {...register('duration', { required: true, min: 1 })}
            />
          </div>

          {/* Upload progress */}
          {uploadMutation.isPending && (
            <UploadProgress progress={uploadProgress} />
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!file || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? 'Uploading...' : 'Upload'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

#### 6. Page Component

```typescript
// pages/content/ContentPage.tsx

import { useState } from 'react';
import { Button } from '@/shared/components/ui/button';
import { ContentTable } from '@/features/content/components/ContentTable';
import { ContentFilters } from '@/features/content/components/ContentFilters';
import { UploadModal } from '@/features/content/components/UploadModal';
import { ContentStats } from '@/features/content/components/ContentStats';
import { useContent } from '@/features/content/hooks/useContent';
import { Upload } from 'lucide-react';

export default function ContentPage() {
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [filters, setFilters] = useState({
    skip: 0,
    limit: 20,
    content_type: undefined,
    is_active: undefined,
  });

  const { data, isLoading, error } = useContent(filters);

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Content Management</h1>
          <p className="text-gray-500">Upload and manage media content</p>
        </div>
        <Button onClick={() => setUploadModalOpen(true)}>
          <Upload className="mr-2 h-4 w-4" />
          Upload Content
        </Button>
      </div>

      {/* Storage Stats */}
      <ContentStats />

      {/* Filters */}
      <ContentFilters filters={filters} onFiltersChange={setFilters} />

      {/* Content Table */}
      <ContentTable
        data={data?.data || []}
        isLoading={isLoading}
        error={error}
        pagination={{
          total: data?.total || 0,
          skip: filters.skip,
          limit: filters.limit,
          onPageChange: (skip) => setFilters({ ...filters, skip }),
        }}
      />

      {/* Upload Modal */}
      <UploadModal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
      />
    </div>
  );
}
```

---

**Next Action:** Start Phase 0 - Implement Storage Service Layer

**Questions?** Review this document and start coding! 🚀
