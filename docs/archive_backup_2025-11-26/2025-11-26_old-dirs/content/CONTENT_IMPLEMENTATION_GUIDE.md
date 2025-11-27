# 📋 CONTENT FEATURE - IMPLEMENTATION GUIDE

**Status:** 60% Complete - Core backend implemented
**Last Updated:** 2025-01-06
**Token Used:** ~128k

---

## ✅ COMPLETED (60%)

### Backend Infrastructure ✅
1. ✅ **Domain Layer** (`services/content/domain/`)
   - `content.py` - Content entity dengan business logic validation
   - `interfaces.py` - IContentRepository interface dengan semua methods

2. ✅ **Infrastructure Layer** (`services/content/infrastructure/storage/`)
   - `interfaces.py` - IStorageService interface
   - `local_storage.py` - LocalFilesystemStorage implementation (save, delete, exists)
   - `metadata_extractor.py` - FFprobe/Pillow untuk extract metadata

3. ✅ **Database Layer** (`services/content/repositories/`)
   - `models.py` - ContentModel SQLAlchemy (LENGKAP dengan semua fields)
   - `content_repo.py` - ContentRepository implementation (create, find_by_id, find_all, dll)

4. ✅ **DTOs** (`services/content/dtos.py`)
   - ContentUploadRequest, ContentUpdateRequest
   - ContentResponse, ContentStatsResponse
   - PaginatedContentResponse

5. ✅ **Use Cases** (`services/content/use_cases/`)
   - `upload_content.py` - **CORE** - Upload dengan validation, storage, metadata extraction

---

## 🔄 TODO (40%) - STEP BY STEP

### BACKEND (Priority: HIGH)

#### Step 1: Create Remaining Use Cases

**File:** `backend-python/services/content/use_cases/list_content.py`
```python
"""
List Content Use Case
"""

from typing import Tuple, List, Optional
from ..domain.content import Content
from ..domain.interfaces import IContentRepository


class ListContentUseCase:
    """List content with filters and pagination"""

    def __init__(self, content_repo: IContentRepository):
        self.content_repo = content_repo

    def execute(
        self,
        organization_id: int,
        skip: int = 0,
        limit: int = 20,
        content_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[Content], int]:
        """
        List content with filters

        Returns:
            Tuple of (content list, total count)
        """
        return self.content_repo.find_all(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            content_type=content_type,
            is_active=is_active
        )
```

**File:** `backend-python/services/content/use_cases/get_content.py`
```python
"""
Get Content Use Case
"""

from typing import Optional
from ..domain.content import Content
from ..domain.interfaces import IContentRepository


class GetContentUseCase:
    """Get single content by ID"""

    def __init__(self, content_repo: IContentRepository):
        self.content_repo = content_repo

    def execute(self, content_id: int, organization_id: int) -> Optional[Content]:
        """
        Get content by ID (organization-scoped)

        Raises:
            ValueError: If content not found
        """
        content = self.content_repo.find_by_id(content_id, organization_id)

        if not content:
            raise ValueError(f"Content {content_id} not found")

        return content
```

#### Step 2: Update shared/api_routes.py

**File:** `backend-python/shared/api_routes.py`

**ADD** this class after existing routes:

```python
class ContentRoutes:
    """Content endpoints"""
    BASE = f"{API_V1}/content"
    LIST = f"{API_V1}/content"                          # GET - List content
    GET = lambda id: f"{API_V1}/content/{id}"           # GET - Get by ID
    UPLOAD = f"{API_V1}/content/upload"                 # POST - Upload file
    UPDATE = lambda id: f"{API_V1}/content/{id}"        # PUT - Update metadata
    DELETE = lambda id: f"{API_V1}/content/{id}"        # DELETE - Soft delete
    STATS = f"{API_V1}/content/stats"                   # GET - Storage stats
```

#### Step 3: Create Content Routes

**File:** `backend-python/services/content/routes.py`

```python
"""
Content API Routes
FastAPI endpoints with dependency injection
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, HTTPException
from typing import Optional
from sqlalchemy.orm import Session

from shared.database import get_db
from shared.api_routes import ContentRoutes
from shared.responses import success_response, error_response, paginated_response

from .repositories.content_repo import get_content_repository
from .infrastructure.storage.local_storage import get_storage_service
from .infrastructure.storage.metadata_extractor import get_metadata_extractor

from .use_cases.upload_content import UploadContentUseCase
from .use_cases.list_content import ListContentUseCase
from .use_cases.get_content import GetContentUseCase

from .dtos import ContentResponse, PaginatedContentResponse
from .domain.interfaces import IContentRepository
from .infrastructure.storage.interfaces import IStorageService
from .infrastructure.storage.metadata_extractor import MetadataExtractor

router = APIRouter(prefix="/api/v1/content", tags=["content"])


# Dependency injection functions
def get_upload_content_use_case(
    content_repo: IContentRepository = Depends(get_content_repository),
    storage_service: IStorageService = Depends(get_storage_service),
    metadata_extractor: MetadataExtractor = Depends(get_metadata_extractor)
) -> UploadContentUseCase:
    return UploadContentUseCase(content_repo, storage_service, metadata_extractor)


def get_list_content_use_case(
    content_repo: IContentRepository = Depends(get_content_repository)
) -> ListContentUseCase:
    return ListContentUseCase(content_repo)


def get_get_content_use_case(
    content_repo: IContentRepository = Depends(get_content_repository)
) -> GetContentUseCase:
    return GetContentUseCase(content_repo)


# Temporary mock auth - REPLACE with real auth from auth service
def get_current_user():
    """TODO: Replace with real auth middleware"""
    return {
        "id": 1,
        "organization_id": 4,  # HARDCODED for testing
        "username": "admin"
    }


# API Endpoints
@router.post("/upload", response_model=dict)
async def upload_content(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    duration: int = Form(10),
    is_active: bool = Form(True),
    upload_use_case: UploadContentUseCase = Depends(get_upload_content_use_case),
    current_user: dict = Depends(get_current_user),
    request: Request = None
):
    """
    Upload content file

    - Supports: image (jpg, png, webp), video (mp4, webm), audio (mp3, aac)
    - Max sizes: Image 50MB, Video 500MB, Audio 100MB
    - Auto-extracts metadata (resolution, duration, codec)
    - Deduplication via file hash
    """
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
            data=ContentResponse.from_entity(content).dict(),
            message="Content uploaded successfully",
            status_code=201
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("", response_model=dict)
async def list_content(
    skip: int = 0,
    limit: int = 20,
    content_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    list_use_case: ListContentUseCase = Depends(get_list_content_use_case),
    current_user: dict = Depends(get_current_user)
):
    """
    List content with filters

    Query params:
    - skip: Offset for pagination (default 0)
    - limit: Number of records (default 20)
    - content_type: Filter by type (image/video/audio)
    - is_active: Filter by active status (true/false)
    """
    try:
        contents, total = list_use_case.execute(
            organization_id=current_user["organization_id"],
            skip=skip,
            limit=limit,
            content_type=content_type,
            is_active=is_active
        )

        return paginated_response(
            data=[ContentResponse.from_entity(c).dict() for c in contents],
            total=total,
            skip=skip,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")


@router.get("/{content_id}", response_model=dict)
async def get_content(
    content_id: int,
    get_use_case: GetContentUseCase = Depends(get_get_content_use_case),
    current_user: dict = Depends(get_current_user)
):
    """Get single content by ID"""
    try:
        content = get_use_case.execute(content_id, current_user["organization_id"])

        return success_response(
            data=ContentResponse.from_entity(content).dict()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get failed: {str(e)}")
```

#### Step 4: Register Routes in main.py

**File:** `backend-python/main.py`

**ADD** these imports and registration:

```python
# Add import
from services.content.routes import router as content_router

# Add route registration (after existing routes)
app.include_router(content_router)
```

#### Step 5: Create Database Migration

**File:** `backend-python/migrations/create_contents_table.sql`

```sql
-- Create contents table
CREATE TABLE IF NOT EXISTS contents (
    -- Identity
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    content_type VARCHAR(20) NOT NULL,

    -- File Storage (Custom System)
    file_path VARCHAR(500) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    storage_key VARCHAR(255) NOT NULL UNIQUE,
    file_hash VARCHAR(64) NOT NULL,

    -- Display Settings
    duration INTEGER DEFAULT 10 NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,

    -- File Metadata
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_extension VARCHAR(20) NOT NULL,

    -- Media Properties
    resolution VARCHAR(50),
    width INTEGER,
    height INTEGER,
    codec VARCHAR(50),
    fps FLOAT,
    bitrate INTEGER,

    -- Video/Audio Specific
    media_duration FLOAT,
    video_start_time FLOAT DEFAULT 0.0 NOT NULL,
    video_end_time FLOAT,
    audio_codec VARCHAR(50),
    audio_bitrate INTEGER,
    audio_sample_rate INTEGER,
    audio_channels INTEGER DEFAULT 2 NOT NULL,

    -- Transcoding (HLS)
    transcoding_status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    transcoding_job_id VARCHAR(200),
    transcoding_progress INTEGER DEFAULT 0 NOT NULL,
    transcoding_error TEXT,
    hls_master_playlist_path VARCHAR(500),
    hls_master_playlist_url VARCHAR(500),
    hls_variants JSONB,

    -- Thumbnail
    thumbnail_path VARCHAR(500),
    thumbnail_url VARCHAR(500),
    thumbnail_generated_at TIMESTAMP WITH TIME ZONE,

    -- Upload Status
    upload_status VARCHAR(20) DEFAULT 'pending' NOT NULL,

    -- Multi-tenant
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_content_org_active ON contents(organization_id, is_active);
CREATE INDEX idx_content_org_type ON contents(organization_id, content_type);
CREATE INDEX idx_content_org_created ON contents(organization_id, created_at);
CREATE INDEX idx_content_hash_org ON contents(file_hash, organization_id);
CREATE INDEX idx_content_storage_key ON contents(storage_key);
```

**Run migration:**
```bash
# On server
docker exec -i signage-postgres psql -U signage_user -d signage_db < /path/to/create_contents_table.sql
```

#### Step 6: Test Backend API

**Create test directory on server:**
```bash
ssh gzjbbk@192.168.5.12
mkdir -p /data/signage/content/{uploads,thumbnails,transcoded,temp}
chmod -R 755 /data/signage/content
```

**Test with curl:**
```bash
# Test upload
curl -X POST http://192.168.5.12:8001/api/v1/content/upload \
  -F "file=@test-image.jpg" \
  -F "title=Test Image" \
  -F "description=Testing upload" \
  -F "duration=10" \
  -F "is_active=true"

# Test list
curl http://192.168.5.12:8001/api/v1/content

# Test get by ID
curl http://192.168.5.12:8001/api/v1/content/1
```

---

### FRONTEND (Priority: MEDIUM)

#### Step 7: Create Frontend Types

**File:** `cms-vite/src/features/content/types/content.ts`

```typescript
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

  transcoding_status: string;
  transcoding_progress: number;
  upload_status: string;

  organization_id: number;
  uploaded_by?: number;

  created_at: string;
  updated_at?: string;
}

export interface ContentUpload {
  file: File;
  title: string;
  description?: string;
  duration: number;
  is_active: boolean;
}
```

#### Step 8: Update API Endpoints Config

**File:** `cms-vite/src/lib/api/endpoints.ts`

**ADD:**
```typescript
CONTENT: {
  LIST: `${API_V1}/content`,
  GET: (id: number) => `${API_V1}/content/${id}`,
  UPLOAD: `${API_V1}/content/upload`,
  UPDATE: (id: number) => `${API_V1}/content/${id}`,
  DELETE: (id: number) => `${API_V1}/content/${id}`,
  STATS: `${API_V1}/content/stats`,
},
```

#### Step 9: Create API Service

**File:** `cms-vite/src/features/content/services/contentApi.ts`

```typescript
import { apiClient } from '@/lib/api/client';
import { API_ENDPOINTS } from '@/lib/api/endpoints';
import type { Content, ContentUpload } from '../types/content';

export const contentApi = {
  getAll: async (params?: {
    skip?: number;
    limit?: number;
    content_type?: 'image' | 'video' | 'audio';
    is_active?: boolean;
  }) => {
    const response = await apiClient.get(API_ENDPOINTS.CONTENT.LIST, { params });
    return response.data;
  },

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
};
```

---

## 🎯 NEXT SESSION TASKS

1. **Complete Backend Testing**
   - Run migration
   - Test upload endpoint dengan Postman/curl
   - Test list endpoint
   - Verify file storage di `/data/signage/content/uploads/`

2. **Frontend Implementation** (if backend works)
   - Create React Query hooks
   - Create UploadModal component
   - Create ContentTable component
   - Create ContentPage

3. **Optional Enhancements**
   - Celery tasks untuk transcoding
   - Thumbnail generation
   - Audit logging integration

---

## 📝 NOTES

- **Authentication:** Currently using mock auth in routes.py. Replace dengan real auth dari auth service!
- **File Permissions:** Pastikan `/data/signage/content/` directory exists dan writable
- **Dependencies:** Perlu install `Pillow` untuk image metadata extraction
- **FFprobe:** Perlu install `ffmpeg` di server untuk video/audio metadata

---

**Ready untuk dilanjutkan!** 🚀
