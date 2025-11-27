# Anthias Storage Integration - Backend Summary

**Status:** ✅ **ALREADY INTEGRATED** (Production Ready)

**Date:** 2025-10-28
**Backend Path:** `/mnt/g/khoirul/signate/backend`
**Anthias URL:** `http://192.168.5.12:8000`
**Backend URL:** `http://192.168.5.12:8001`

---

## Executive Summary

The backend is **already fully integrated** with Anthias minimal storage service. All content upload, storage, serving, and deletion operations go through Anthias. The integration is production-ready and follows best practices.

---

## Architecture Overview

```
┌─────────────────┐
│   Web Admin     │
│  (Port 3000)    │
│   React/Vite    │
└────────┬────────┘
         │ HTTP/HTTPS
         │ Content Upload
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│              Backend API (Port 8001)                     │
│                    FastAPI                               │
├─────────────────────────────────────────────────────────┤
│  POST /api/content/upload                               │
│  ├─► Validate file type (image/video)                   │
│  ├─► Extract metadata (FFprobe)                         │
│  ├─► Upload to Anthias ──────────────┐                  │
│  ├─► Get Anthias asset_id            │                  │
│  ├─► Save metadata to PostgreSQL     │                  │
│  └─► Return content with URLs        │                  │
│                                       │                  │
│  GET /api/content/{id}/image         │                  │
│  GET /api/content/{id}/video         │                  │
│  └─► Proxy to Anthias (with Content-Type) ─┐           │
│                                       │     │            │
│  DELETE /api/content/{id}            │     │            │
│  ├─► Delete from Anthias ────────────┼─────┤            │
│  └─► Delete from PostgreSQL          │     │            │
└───────────────────────────────────────┼─────┼────────────┘
                                        │     │
                                        ▼     ▼
                          ┌───────────────────────────────┐
                          │   Anthias Storage Service      │
                          │       (Port 8000)              │
                          ├───────────────────────────────┤
                          │  POST /api/v1/file_asset      │
                          │  POST /api/v1/assets          │
                          │  GET /api/v1/assets/{id}      │
                          │  GET /api/v1/assets/{id}/content│
                          │  PUT /api/v1/assets/{id}      │
                          │  DELETE /api/v1/assets/{id}   │
                          └───────────┬───────────────────┘
                                      │
                                      ▼
                          ┌───────────────────────────────┐
                          │    File System Storage         │
                          │  /data/screenly_assets/        │
                          │  ├── uuid1 (no extension)      │
                          │  ├── uuid2 (no extension)      │
                          │  └── uuid3 (no extension)      │
                          └───────────────────────────────┘
```

---

## Integration Points

### 1. Content Upload Flow

**Endpoint:** `POST /api/content/upload`
**File:** `/backend/app/api/content.py` (Lines 42-300)

**Process:**
1. **Validate** file type (image/video only)
2. **Extract metadata** using FFprobe (resolution, codec, duration, etc.)
3. **Upload to Anthias** using `anthias_service.upload_asset()`
   - Step 1: Upload file → GET file URI
   - Step 2: Create asset → GET asset_id
4. **Save to PostgreSQL:**
   - Content metadata (title, description, duration)
   - Anthias references (`anthias_asset_id`, `anthias_url`)
   - Media metadata (resolution, codec, bitrate, etc.)
5. **Return response** with content ID and URLs

**Code Reference:**
```python
# Upload to Anthias (lines 119-128)
anthias_asset = await anthias_service.upload_asset(
    file=file,
    name=title,
    duration=duration,
    is_enabled=is_active
)

# Get Anthias URL (line 128)
anthias_url = await anthias_service.get_asset_url(anthias_asset["asset_id"])

# Save to database (lines 172-193)
content = Content(
    title=title,
    anthias_url=anthias_url,
    anthias_asset_id=anthias_asset["asset_id"],
    # ... other fields
)
```

---

### 2. Content Serving Flow

**Endpoints:**
- `GET /api/content/{content_id}/image` (Lines 1094-1145)
- `GET /api/content/{content_id}/video` (Lines 1148-1206)

**Process:**
1. **Fetch metadata** from PostgreSQL (content record)
2. **Get asset content** from Anthias using `anthias_service.get_asset_content()`
3. **Serve with correct Content-Type** (from database mime_type)
4. **Support video streaming** (Accept-Ranges headers)

**Why Proxy?**
- Anthias stores files **without extensions** (e.g., `/data/screenly_assets/uuid`)
- Browsers need correct `Content-Type` headers to display images/videos
- Backend adds headers based on database metadata

**Code Reference:**
```python
# Fetch from Anthias (line 1132)
image_bytes = await anthias_service.get_asset_content(content.anthias_asset_id)

# Serve with correct Content-Type (line 1138)
return Response(content=image_bytes, media_type=content.mime_type)
```

---

### 3. Content Deletion Flow

**Endpoint:** `DELETE /api/content/{content_id}`
**File:** `/backend/app/api/content.py` (Lines 623-715)

**Process:**
1. **Fetch content** from PostgreSQL
2. **Delete from Anthias** using `anthias_service.delete_asset()`
3. **Delete from PostgreSQL** (cascades to assignments)
4. **Invalidate cache**

**Code Reference:**
```python
# Delete from Anthias (line 678)
if anthias_asset_id:
    await anthias_service.delete_asset(anthias_asset_id)

# Delete from database (lines 686-687)
db.delete(content)
db.commit()
```

---

### 4. Content Update Flow

**Endpoint:** `PATCH /api/content/{content_id}`
**File:** `/backend/app/api/content.py` (Lines 475-620)

**Process:**
1. **Update PostgreSQL first** (source of truth for viewers)
2. **Optionally sync to Anthias** (for consistency)
3. **If Anthias sync fails** → Log warning, continue (non-critical)

**Why PostgreSQL First?**
- Viewers use our database, not Anthias metadata
- Anthias is just file storage, not metadata store

**Code Reference:**
```python
# Update database first (lines 525-541)
if content_data.title is not None:
    content.title = content_data.title
db.commit()

# Try to sync with Anthias (optional, lines 547-568)
try:
    await anthias_service.update_asset(...)
except Exception as anthias_error:
    logger.warning("Anthias sync failed (non-critical)")
```

---

## Anthias Service Implementation

**File:** `/backend/app/services/anthias_service.py`
**Status:** ✅ Production Ready

### Service Methods

| Method | Purpose | Anthias Endpoint |
|--------|---------|------------------|
| `upload_asset()` | Upload file (2-step) | `POST /file_asset` + `POST /assets` |
| `get_asset()` | Get asset metadata | `GET /assets/{id}` |
| `get_asset_url()` | Get public URL | Constructs from URI |
| `get_asset_content()` | Get file bytes (base64) | `GET /assets/{id}/content` |
| `update_asset()` | Update metadata | `PUT /assets/{id}` |
| `delete_asset()` | Delete asset | `DELETE /assets/{id}` |
| `list_assets()` | List all assets | `GET /assets` |
| `check_connection()` | Health check | `GET /assets` (5s timeout) |

### Upload Process (2-Step)

**Why 2-Step?**
Anthias API design separates file upload from asset creation.

```python
# Step 1: Upload file
POST /api/v1/file_asset
Files: {"file_upload": (filename, bytes, content_type)}
Response: {"uri": "/data/screenly_assets/uuid"}

# Step 2: Create asset
POST /api/v1/assets
Data: {"model": json({
    "name": "My Video",
    "uri": "/data/screenly_assets/uuid",
    "mimetype": "video",
    "duration": "10",
    "is_enabled": 1
})}
Response: {"asset_id": "uuid", ...}
```

---

## Database Schema

**File:** `/backend/app/models/content.py`

### Content Model Fields

**Anthias Integration:**
```python
anthias_url = Column(String(500), nullable=False)     # Full URL to asset
anthias_asset_id = Column(String(100), index=True)    # Asset UUID
```

**Media Metadata (Extracted via FFprobe):**
```python
resolution = Column(String(50))        # e.g., "1920x1080"
width = Column(Integer)                # pixels
height = Column(Integer)               # pixels
codec = Column(String(50))             # video/image codec
fps = Column(Float)                    # frame rate
bitrate = Column(Integer)              # kbps
video_duration = Column(Float)         # actual video duration
audio_codec = Column(String(50))       # audio codec
audio_bitrate = Column(Integer)        # kbps
audio_sample_rate = Column(Integer)    # Hz
```

**Campaign Management:**
```python
play_order = Column(Integer, default=0)           # Playback sequence
start_date = Column(DateTime, nullable=True)      # Activation time
end_date = Column(DateTime, nullable=True)        # Expiration time
is_enabled = Column(Boolean, default=True)        # Soft delete flag
shuffle = Column(Boolean, default=False)          # Random playback
```

**HLS Transcoding (Phase 3.1):**
```python
hls_master_playlist_path = Column(String(500))    # master.m3u8 path
transcoding_status = Column(String(20))           # pending/processing/completed/failed
transcoding_progress = Column(Integer)            # 0-100%
hls_variants = Column(JSON)                       # Available quality levels
```

---

## Configuration

### Environment Variables

**File:** `/backend/.env`

```bash
# Anthias Integration
ANTHIAS_URL=http://192.168.5.12:8000
ANTHIAS_API_URL=http://192.168.5.12:8000
ANTHIAS_USER=admin
ANTHIAS_PASSWORD=admin
```

**File:** `/backend/app/core/config.py` (Lines 54-71)

```python
class Settings(BaseSettings):
    # Anthias URLs
    ANTHIAS_API_URL: str = "http://localhost:8000"        # External API
    ANTHIAS_INTERNAL_URL: str = "http://anthias-nginx"    # Internal (Docker)
    ANTHIAS_PUBLIC_URL: str = "http://localhost:8000"     # Public access
    ANTHIAS_API_KEY: str = ""                             # API key (if needed)
```

### URL Types Explained

1. **ANTHIAS_API_URL**: Backend → Anthias API calls (upload, delete)
2. **ANTHIAS_PUBLIC_URL**: Clients → Direct asset access (browsers, viewers)
3. **ANTHIAS_INTERNAL_URL**: Docker network (not used in current setup)

---

## API Endpoints Summary

### Content Management

| Method | Endpoint | Purpose | Anthias Involved? |
|--------|----------|---------|-------------------|
| POST | `/api/content/upload` | Upload content | ✅ Upload + Create |
| GET | `/api/content/` | List content | ❌ PostgreSQL only |
| GET | `/api/content/{id}` | Get content details | ❌ PostgreSQL only |
| PATCH | `/api/content/{id}` | Update metadata | ⚠️ Optional sync |
| DELETE | `/api/content/{id}` | Delete content | ✅ Delete asset |
| GET | `/api/content/{id}/image` | Serve image | ✅ Fetch content |
| GET | `/api/content/{id}/video` | Serve video | ✅ Fetch content |

### Content Assignment

| Method | Endpoint | Purpose | Anthias Involved? |
|--------|----------|---------|-------------------|
| POST | `/api/content/{id}/assign` | Assign to device/tag | ❌ PostgreSQL only |
| GET | `/api/content/{id}/assignments` | Get assignments | ❌ PostgreSQL only |
| DELETE | `/api/content/{id}/assign` | Unassign content | ❌ PostgreSQL only |

---

## Error Handling

### Upload Failures

**Scenario 1: Anthias Connection Failed**
```json
{
  "success": false,
  "error": "InternalServerException",
  "message": "Upload failed",
  "details": {
    "error": "Cannot connect to Anthias service"
  },
  "status_code": 503
}
```

**Scenario 2: Invalid File Type**
```json
{
  "success": false,
  "error": "BadRequestException",
  "message": "Unsupported file type: application/pdf. Only images and videos are supported.",
  "details": {
    "content_type": "application/pdf",
    "filename": "document.pdf"
  },
  "status_code": 400
}
```

### Deletion Failures

**Scenario: Asset Already Deleted in Anthias**
- Backend logs warning
- Continues with database deletion
- Returns success (idempotent)

---

## Metadata Extraction

**Tool:** FFprobe (part of FFmpeg)
**File:** `/backend/app/utils/media_metadata.py`

### Extracted Metadata

**Images:**
- Resolution (width x height)
- Format (JPEG, PNG, GIF)
- Color space
- File size

**Videos:**
- Resolution (width x height)
- Video codec (H.264, H.265, VP9)
- Frame rate (fps)
- Bitrate (video + audio)
- Duration (seconds)
- Audio codec (AAC, MP3, etc.)
- Audio sample rate (Hz)

### Usage in Upload

```python
# Extract metadata (lines 134-160)
metadata = MediaMetadataExtractor.extract_metadata(temp_file_path, content_type)

# Auto-set video duration (lines 164-169)
if content_type == "video" and metadata.get("duration"):
    final_duration = int(metadata["duration"])
```

---

## Caching Strategy

### Cache Invalidation

**Trigger:** Content upload, update, or delete
**Action:** Invalidate `content_list` prefix

```python
# After successful operation
from app.core.cache import invalidate_by_prefix
invalidate_by_prefix("content_list")
```

### Cache Keys

- `content_list:{skip}:{limit}:{content_type}:{is_active}` - List endpoint
- Device playlists are cached separately

---

## Testing Anthias Integration

### Health Check

```bash
# Test backend health
curl http://192.168.5.12:8001/health

# Test Anthias connection
curl http://192.168.5.12:8000/api/v1/assets
```

### Upload Test

```bash
# Upload image
curl -X POST http://192.168.5.12:8001/api/content/upload \
  -F "file=@test.jpg" \
  -F "title=Test Image" \
  -F "duration=10"

# Response
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Test Image",
    "anthias_asset_id": "uuid-here",
    "anthias_url": "http://192.168.5.12:8000/data/screenly_assets/uuid-here"
  }
}
```

### Serve Test

```bash
# Serve image (with correct Content-Type)
curl http://192.168.5.12:8001/api/content/1/image > test_downloaded.jpg

# Verify headers
curl -I http://192.168.5.12:8001/api/content/1/image
# Content-Type: image/jpeg
# Content-Length: 123456
```

---

## Production Deployment Checklist

### ✅ Already Configured

- [x] Anthias service running (port 8000)
- [x] Backend service running (port 8001)
- [x] PostgreSQL database (port 5433)
- [x] CORS configured for web admin
- [x] Content upload/serve/delete working
- [x] Metadata extraction working
- [x] Error handling implemented
- [x] Caching strategy in place

### ⚠️ Recommended Enhancements

1. **Health Check Enhancement**
   - Add Anthias connectivity status to `/health` endpoint
   - Monitor Anthias availability

2. **Environment Variable Cleanup**
   - Remove deprecated `ANTHIAS_USER` and `ANTHIAS_PASSWORD` (not used in code)
   - Standardize URL variable names

3. **Monitoring**
   - Add metrics for Anthias upload success/failure rates
   - Track Anthias response times
   - Alert on Anthias connection failures

4. **Backup Strategy**
   - Backup Anthias `/data/screenly_assets/` directory
   - Backup PostgreSQL content metadata
   - Ensure both are in sync

---

## Migration Path (If Needed)

### Current State
- Backend → Anthias (Port 8000) → File System

### Future Options

**Option 1: Direct Storage** (Remove Anthias)
- Backend → PostgreSQL + Direct File System
- Store files in `/data/content/{id}.{ext}`
- Pros: Simpler stack, one less service
- Cons: Lose Anthias features, need to implement file serving

**Option 2: Cloud Storage** (Replace Anthias)
- Backend → PostgreSQL + S3/Cloud Storage
- Store files in cloud bucket
- Pros: Scalable, CDN-ready, managed backups
- Cons: Cost, external dependency, network latency

**Option 3: Keep Current** (Recommended)
- Backend → Anthias → File System
- Pros: Working, tested, production-ready
- Cons: Extra service to maintain

**Recommendation:** Keep current setup. Anthias is proven, stable, and handles file storage concerns.

---

## Troubleshooting

### Issue 1: Upload Fails with "Cannot connect to Anthias"

**Diagnosis:**
```bash
# Check Anthias is running
curl http://192.168.5.12:8000/api/v1/assets

# Check backend can reach Anthias
docker exec signage-backend curl http://anthias:8000/api/v1/assets
```

**Solution:**
- Verify Anthias service is running
- Check Docker network connectivity
- Verify ANTHIAS_API_URL in .env

### Issue 2: Images/Videos Don't Display in Browser

**Diagnosis:**
```bash
# Check Content-Type header
curl -I http://192.168.5.12:8001/api/content/1/image

# Should show: Content-Type: image/jpeg
```

**Solution:**
- Verify mime_type field in database is correct
- Check proxy endpoints are working
- Ensure Anthias asset_id is valid

### Issue 3: Deleted Content Still Showing

**Diagnosis:**
```bash
# Check if asset deleted in Anthias
curl http://192.168.5.12:8000/api/v1/assets/{asset_id}
# Should return 404

# Check if deleted from database
# Query content table
```

**Solution:**
- Both Anthias and PostgreSQL must be deleted
- Check deletion endpoint logs
- Verify cascade deletion working

---

## Security Considerations

### Current Implementation

1. **File Type Validation** ✅
   - Only image/* and video/* allowed
   - Checked via content_type
   - Prevents malicious file uploads

2. **File Size Limits** ✅
   - MAX_UPLOAD_SIZE: 100MB (configurable)
   - Prevents DoS attacks

3. **Content-Type Headers** ✅
   - Set based on database mime_type
   - Prevents MIME confusion attacks

### Recommended Additions

1. **Authentication**
   - Add authentication to upload endpoint
   - Currently uses `get_optional_user` (optional auth)
   - Consider making authentication required

2. **Rate Limiting**
   - Limit uploads per IP/user
   - Prevent abuse

3. **File Scanning**
   - Scan uploaded files for malware
   - Integrate ClamAV or similar

4. **Access Control**
   - Restrict content serving to authenticated users
   - Consider signed URLs with expiration

---

## Performance Optimization

### Current Optimizations

1. **Async Operations** ✅
   - All Anthias API calls are async
   - Non-blocking I/O

2. **Connection Pooling** ✅
   - httpx client with timeout
   - Efficient network usage

3. **Metadata Caching** ✅
   - Content list cached (5 minutes)
   - Reduces database queries

### Recommended Improvements

1. **CDN Integration**
   - Serve static assets via CDN
   - Reduce backend load

2. **Thumbnail Generation**
   - Generate thumbnails on upload
   - Faster preview loading

3. **Video Transcoding**
   - Already implemented (HLS Phase 3.1)
   - Multiple quality levels
   - Adaptive bitrate streaming

---

## API Flow Diagrams

### Upload Sequence

```
Web Admin                Backend                 Anthias               PostgreSQL
    |                       |                       |                       |
    |-- POST /upload ------>|                       |                       |
    |                       |-- Validate file       |                       |
    |                       |-- Extract metadata    |                       |
    |                       |                       |                       |
    |                       |-- POST /file_asset -->|                       |
    |                       |<-- {"uri": "..."}  ---|                       |
    |                       |                       |                       |
    |                       |-- POST /assets ------>|                       |
    |                       |<-- {"asset_id": ...}--|                       |
    |                       |                       |                       |
    |                       |-- INSERT content -------------------->|       |
    |                       |<-- content record  ------------------|       |
    |                       |                       |                       |
    |<-- 201 Created -------|                       |                       |
```

### Serve Sequence

```
Viewer                  Backend                 Anthias               PostgreSQL
   |                       |                       |                       |
   |-- GET /content/1 ---->|                       |                       |
   |                       |-- SELECT content ------------------>|         |
   |                       |<-- metadata ------------------------|         |
   |                       |                       |                       |
   |                       |-- GET /content ------>|                       |
   |                       |<-- base64 bytes ------|                       |
   |                       |                       |                       |
   |<-- 200 OK + bytes ----|                       |                       |
   |   (Content-Type set)  |                       |                       |
```

### Delete Sequence

```
Web Admin                Backend                 Anthias               PostgreSQL
    |                       |                       |                       |
    |-- DELETE /1 --------->|                       |                       |
    |                       |-- SELECT content ------------------>|         |
    |                       |<-- metadata ------------------------|         |
    |                       |                       |                       |
    |                       |-- DELETE /asset ----->|                       |
    |                       |<-- 204 No Content ----|                       |
    |                       |                       |                       |
    |                       |-- DELETE content ------------------>|         |
    |                       |<-- success -------------------------|         |
    |                       |                       |                       |
    |<-- 204 No Content ----|                       |                       |
```

---

## Conclusion

The backend is **fully integrated** with Anthias minimal storage service and is **production-ready**. All content operations (upload, serve, update, delete) properly interact with Anthias for file storage while maintaining metadata in PostgreSQL.

### Key Strengths

✅ **2-Step Upload** - Follows Anthias API design correctly
✅ **Metadata Extraction** - Rich media metadata via FFprobe
✅ **Proxy Serving** - Correct Content-Type headers for browsers
✅ **Error Handling** - Comprehensive exception handling
✅ **Async Operations** - Non-blocking I/O for performance
✅ **Caching** - Intelligent cache invalidation
✅ **Database Schema** - Anthias references + media metadata

### Next Steps (Optional)

1. **Add Anthias Health Check** - Monitor connectivity
2. **Enhance Monitoring** - Track upload success rates
3. **Implement Backups** - Sync Anthias files + PostgreSQL
4. **Add Authentication** - Secure upload endpoint
5. **CDN Integration** - Improve content delivery performance

**Overall Assessment:** The integration is well-architected, follows best practices, and is ready for production use.
