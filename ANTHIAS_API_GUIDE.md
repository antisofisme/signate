# Anthias Integration - API Developer Guide

**Backend:** FastAPI (Port 8001)
**Anthias Storage:** Port 8000
**Status:** ✅ Production Ready

---

## Quick Reference

### Upload Content
```bash
curl -X POST http://192.168.5.12:8001/api/content/upload \
  -F "file=@video.mp4" \
  -F "title=Product Demo" \
  -F "description=New product showcase" \
  -F "duration=30" \
  -F "is_active=true"
```

### Get Content List
```bash
curl http://192.168.5.12:8001/api/content/
```

### Serve Content (Image)
```bash
curl http://192.168.5.12:8001/api/content/1/image > image.jpg
```

### Delete Content
```bash
curl -X DELETE http://192.168.5.12:8001/api/content/1
```

### Health Check
```bash
curl http://192.168.5.12:8001/health
```

---

## API Endpoints

### 1. Upload Content

**Endpoint:** `POST /api/content/upload`

**Description:**
Upload image or video file to Anthias storage and save metadata to database.

**Request:**
- **Method:** POST (multipart/form-data)
- **Authentication:** Optional (Bearer token)

**Form Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file` | File | ✅ Yes | - | Image or video file |
| `title` | String | ✅ Yes | - | Display title |
| `description` | String | ❌ No | "" | Content description |
| `duration` | Integer | ❌ No | 10 | Display duration (seconds) |
| `is_active` | Boolean | ❌ No | true | Active status |
| `transcode_on_upload` | Boolean | ❌ No | false | Auto HLS transcoding (video only) |
| `transcode_quality_levels` | String | ❌ No | "1080p,720p,480p" | Quality levels (comma-separated) |

**Supported File Types:**
- Images: `image/jpeg`, `image/png`, `image/gif`
- Videos: `video/mp4`, `video/mpeg`, `video/quicktime`

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Product Demo",
    "description": "New product showcase",
    "content_type": "video",
    "anthias_url": "http://192.168.5.12:8000/data/screenly_assets/abc-123",
    "anthias_asset_id": "abc-123-def-456",
    "duration": 30,
    "is_active": true,
    "file_size": 10485760,
    "mime_type": "video/mp4",
    "resolution": "1920x1080",
    "width": 1920,
    "height": 1080,
    "codec": "h264",
    "fps": 30.0,
    "bitrate": 5000,
    "video_duration": 45.5,
    "audio_codec": "aac",
    "audio_bitrate": 128,
    "audio_sample_rate": 48000,
    "created_at": "2025-10-28T10:30:00Z",
    "updated_at": "2025-10-28T10:30:00Z",
    "transcoding_status": null
  },
  "request_id": "req_abc123"
}
```

**Error Responses:**

**400 Bad Request** - Invalid file type
```json
{
  "success": false,
  "error": "BadRequestException",
  "message": "Unsupported file type: application/pdf. Only images and videos are supported.",
  "details": {
    "content_type": "application/pdf",
    "filename": "document.pdf"
  },
  "request_id": "req_abc123",
  "status_code": 400
}
```

**500 Internal Server Error** - Upload failed
```json
{
  "success": false,
  "error": "InternalServerException",
  "message": "Upload failed",
  "details": {
    "error": "Failed to upload file to Anthias: Connection refused"
  },
  "request_id": "req_abc123",
  "status_code": 500
}
```

**503 Service Unavailable** - Anthias unreachable
```json
{
  "success": false,
  "error": "InternalServerException",
  "message": "Upload failed",
  "details": {
    "error": "Cannot connect to Anthias service"
  },
  "request_id": "req_abc123",
  "status_code": 503
}
```

**Example cURL:**
```bash
# Upload video with auto-transcoding
curl -X POST http://192.168.5.12:8001/api/content/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@product_demo.mp4" \
  -F "title=Product Demo" \
  -F "description=New product showcase" \
  -F "duration=30" \
  -F "is_active=true" \
  -F "transcode_on_upload=true" \
  -F "transcode_quality_levels=1080p,720p,480p"

# Upload image
curl -X POST http://192.168.5.12:8001/api/content/upload \
  -F "file=@banner.jpg" \
  -F "title=Sale Banner" \
  -F "duration=10"
```

**Upload Flow:**
1. Backend validates file type (image/video only)
2. Backend extracts metadata using FFprobe (resolution, codec, duration, etc.)
3. Backend uploads file to Anthias (2-step process)
   - Step 1: POST `/file_asset` → Get file URI
   - Step 2: POST `/assets` → Create asset with URI → Get asset_id
4. Backend saves metadata to PostgreSQL with Anthias references
5. If `transcode_on_upload=true` and video, triggers HLS transcoding (background)
6. Returns content object with all metadata

---

### 2. List Content

**Endpoint:** `GET /api/content/`

**Description:**
Get paginated list of all content with optional filters.

**Request:**
- **Method:** GET
- **Authentication:** Optional

**Query Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `skip` | Integer | ❌ No | 0 | Number of records to skip (pagination) |
| `limit` | Integer | ❌ No | 100 | Max records to return |
| `content_type` | String | ❌ No | - | Filter by type: `image` or `video` |
| `is_active` | Boolean | ❌ No | - | Filter by active status |

**Response (200 OK):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Product Demo",
      "description": "New product showcase",
      "content_type": "video",
      "anthias_url": "http://192.168.5.12:8000/data/screenly_assets/abc-123",
      "anthias_asset_id": "abc-123-def-456",
      "duration": 30,
      "is_active": true,
      "file_size": 10485760,
      "mime_type": "video/mp4",
      "resolution": "1920x1080",
      "width": 1920,
      "height": 1080,
      "created_at": "2025-10-28T10:30:00Z",
      "updated_at": "2025-10-28T10:30:00Z"
    },
    {
      "id": 2,
      "title": "Sale Banner",
      "content_type": "image",
      "anthias_url": "http://192.168.5.12:8000/data/screenly_assets/xyz-789",
      "anthias_asset_id": "xyz-789-abc-123",
      "duration": 10,
      "is_active": true,
      "resolution": "1920x1080",
      "created_at": "2025-10-28T11:00:00Z",
      "updated_at": "2025-10-28T11:00:00Z"
    }
  ],
  "pagination": {
    "total": 50,
    "page": 1,
    "page_size": 100,
    "total_pages": 1
  },
  "request_id": "req_abc123"
}
```

**Example cURL:**
```bash
# Get all content
curl http://192.168.5.12:8001/api/content/

# Get only videos
curl "http://192.168.5.12:8001/api/content/?content_type=video"

# Get inactive content
curl "http://192.168.5.12:8001/api/content/?is_active=false"

# Pagination
curl "http://192.168.5.12:8001/api/content/?skip=0&limit=10"
curl "http://192.168.5.12:8001/api/content/?skip=10&limit=10"
```

---

### 3. Get Content Details

**Endpoint:** `GET /api/content/{content_id}`

**Description:**
Get detailed information about specific content.

**Request:**
- **Method:** GET
- **Authentication:** Optional

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_id` | Integer | ✅ Yes | Content ID |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Product Demo",
    "description": "New product showcase",
    "content_type": "video",
    "anthias_url": "http://192.168.5.12:8000/data/screenly_assets/abc-123",
    "anthias_asset_id": "abc-123-def-456",
    "duration": 30,
    "is_active": true,
    "file_size": 10485760,
    "mime_type": "video/mp4",
    "resolution": "1920x1080",
    "width": 1920,
    "height": 1080,
    "codec": "h264",
    "fps": 30.0,
    "bitrate": 5000,
    "video_duration": 45.5,
    "created_at": "2025-10-28T10:30:00Z",
    "updated_at": "2025-10-28T10:30:00Z"
  },
  "request_id": "req_abc123"
}
```

**Error Response (404 Not Found):**
```json
{
  "success": false,
  "error": "NotFoundException",
  "message": "Content with ID 999 not found",
  "resource_type": "Content",
  "resource_id": 999,
  "request_id": "req_abc123",
  "status_code": 404
}
```

**Example cURL:**
```bash
curl http://192.168.5.12:8001/api/content/1
```

---

### 4. Update Content

**Endpoint:** `PATCH /api/content/{content_id}`

**Description:**
Update content metadata (partial update). File cannot be changed - delete and re-upload instead.

**Request:**
- **Method:** PATCH
- **Content-Type:** application/json
- **Authentication:** Optional

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_id` | Integer | ✅ Yes | Content ID |

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "duration": 45,
  "video_start_time": 5.0,
  "video_end_time": 40.0,
  "is_active": false
}
```

**Body Parameters (All Optional):**

| Parameter | Type | Description |
|-----------|------|-------------|
| `title` | String | New title |
| `description` | String | New description |
| `duration` | Integer | Display duration (seconds) |
| `video_start_time` | Float | Video start time (seconds) |
| `video_end_time` | Float | Video end time (seconds, null = play to end) |
| `is_active` | Boolean | Active status |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Updated Title",
    "description": "Updated description",
    "duration": 45,
    "is_active": false,
    "video_start_time": 5.0,
    "video_end_time": 40.0,
    // ... other fields unchanged
  },
  "request_id": "req_abc123"
}
```

**Error Response (404 Not Found):**
```json
{
  "success": false,
  "error": "NotFoundException",
  "message": "Content with ID 999 not found",
  "resource_type": "Content",
  "resource_id": 999,
  "request_id": "req_abc123",
  "status_code": 404
}
```

**Example cURL:**
```bash
# Update title and description
curl -X PATCH http://192.168.5.12:8001/api/content/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Product Demo",
    "description": "Enhanced showcase with new features"
  }'

# Deactivate content
curl -X PATCH http://192.168.5.12:8001/api/content/1 \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# Set video segment timing
curl -X PATCH http://192.168.5.12:8001/api/content/1 \
  -H "Content-Type: application/json" \
  -d '{
    "video_start_time": 10.0,
    "video_end_time": 30.0,
    "duration": 20
  }'
```

**Update Behavior:**
1. **Database updated first** (source of truth for viewers)
2. **Anthias sync attempted** (optional, best-effort)
3. **If Anthias sync fails** → Warning logged, update still succeeds
4. **Cache invalidated** automatically

---

### 5. Delete Content

**Endpoint:** `DELETE /api/content/{content_id}`

**Description:**
Delete content from both Anthias storage and database. Cascades to all assignments.

**Request:**
- **Method:** DELETE
- **Authentication:** Optional

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_id` | Integer | ✅ Yes | Content ID |

**Response (200 OK):**
```json
{
  "success": true,
  "data": {
    "message": "Content 1 deleted successfully"
  },
  "request_id": "req_abc123"
}
```

**Error Response (404 Not Found):**
```json
{
  "success": false,
  "error": "NotFoundException",
  "message": "Content with ID 999 not found",
  "resource_type": "Content",
  "resource_id": 999,
  "request_id": "req_abc123",
  "status_code": 404
}
```

**Example cURL:**
```bash
curl -X DELETE http://192.168.5.12:8001/api/content/1
```

**Deletion Flow:**
1. Fetch content from database
2. Delete file from Anthias (using `anthias_asset_id`)
3. Delete metadata from PostgreSQL (cascades to `content_assignments`)
4. Invalidate cache
5. Return success

**Cascade Behavior:**
- Deletes all `content_assignments` (device/tag assignments)
- Removes content from all playlists
- Removes content from device schedules

---

### 6. Serve Content (Image)

**Endpoint:** `GET /api/content/{content_id}/image`

**Description:**
Serve image content with correct Content-Type header. Proxies to Anthias.

**Request:**
- **Method:** GET
- **Authentication:** Optional

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_id` | Integer | ✅ Yes | Content ID |

**Response (200 OK):**
- **Content-Type:** `image/jpeg`, `image/png`, or `image/gif` (from database)
- **Body:** Binary image data

**Error Responses:**

**404 Not Found** - Content not found
```json
{
  "detail": "Content with ID 999 not found"
}
```

**404 Not Found** - No Anthias asset
```json
{
  "detail": "Content has no associated Anthias asset"
}
```

**500 Internal Server Error** - Failed to fetch from Anthias
```json
{
  "detail": "Failed to serve image: Connection refused"
}
```

**Example cURL:**
```bash
# Download image
curl http://192.168.5.12:8001/api/content/1/image > image.jpg

# View headers
curl -I http://192.168.5.12:8001/api/content/1/image
# HTTP/1.1 200 OK
# Content-Type: image/jpeg
# Content-Length: 123456

# Display in browser
open http://192.168.5.12:8001/api/content/1/image
```

**Why Proxy?**
- Anthias stores files **without extensions** (e.g., `/data/screenly_assets/abc-123`)
- Browsers need correct `Content-Type` header to display images
- Backend fetches file from Anthias and adds header from database `mime_type`

**Image Display in HTML:**
```html
<img src="http://192.168.5.12:8001/api/content/1/image" alt="Content">
```

---

### 7. Serve Content (Video)

**Endpoint:** `GET /api/content/{content_id}/video`

**Description:**
Serve video content with correct Content-Type and streaming support. Proxies to Anthias.

**Request:**
- **Method:** GET
- **Authentication:** Optional

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_id` | Integer | ✅ Yes | Content ID |

**Response (200 OK):**
- **Content-Type:** `video/mp4`, `video/mpeg`, or `video/quicktime` (from database)
- **Accept-Ranges:** bytes
- **Content-Length:** {size}
- **Body:** Binary video data

**Error Responses:** Same as image endpoint

**Example cURL:**
```bash
# Download video
curl http://192.168.5.12:8001/api/content/1/video > video.mp4

# Stream video (HTML5 video tag)
<video controls>
  <source src="http://192.168.5.12:8001/api/content/1/video" type="video/mp4">
</video>
```

**Streaming Support:**
- **Accept-Ranges: bytes** - Enables seeking in video player
- **Content-Length** header - Allows progress bar
- **Progressive download** - Video starts playing before full download

**For HLS Streaming:**
Use HLS endpoints instead (if content is transcoded):
```bash
GET /hls/{content_id}/master.m3u8  # Adaptive bitrate
GET /hls/{content_id}/1080p.m3u8   # Specific quality
```

---

### 8. Assign Content to Device/Tag

**Endpoint:** `POST /api/content/{content_id}/assign`

**Description:**
Assign content to a device or tag. Content will show on assigned devices.

**Request:**
- **Method:** POST
- **Content-Type:** application/json
- **Authentication:** Optional

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_id` | Integer | ✅ Yes | Content ID |

**Request Body:**
```json
{
  "device_id": 5,
  "tag_id": null,
  "priority": 10
}
```

**Body Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `device_id` | Integer | ⚠️ Conditional | Device ID (use device_id OR tag_id, not both) |
| `tag_id` | Integer | ⚠️ Conditional | Tag ID (use device_id OR tag_id, not both) |
| `priority` | Integer | ❌ No | Display priority (default 0) |

**Response (201 Created):**
```json
{
  "success": true,
  "data": {
    "id": 10,
    "content_id": 1,
    "device_id": 5,
    "tag_id": null,
    "priority": 10,
    "created_at": "2025-10-28T12:00:00Z"
  },
  "request_id": "req_abc123"
}
```

**Error Responses:**

**400 Bad Request** - No target specified
```json
{
  "success": false,
  "error": "BadRequestException",
  "message": "Must assign to either device_id or tag_id",
  "details": {"content_id": 1},
  "status_code": 400
}
```

**400 Bad Request** - Both targets specified
```json
{
  "success": false,
  "error": "BadRequestException",
  "message": "Cannot assign to both device_id and tag_id",
  "details": {"content_id": 1, "device_id": 5, "tag_id": 2},
  "status_code": 400
}
```

**409 Conflict** - Assignment already exists
```json
{
  "success": false,
  "error": "ConflictException",
  "message": "Assignment already exists",
  "details": {"content_id": 1, "device_id": 5},
  "status_code": 409
}
```

**Example cURL:**
```bash
# Assign to specific device
curl -X POST http://192.168.5.12:8001/api/content/1/assign \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 5,
    "priority": 10
  }'

# Assign to tag (all devices with tag)
curl -X POST http://192.168.5.12:8001/api/content/1/assign \
  -H "Content-Type: application/json" \
  -d '{
    "tag_id": 2,
    "priority": 5
  }'
```

---

### 9. Health Check

**Endpoint:** `GET /health`

**Description:**
Check system health including Anthias connectivity.

**Request:**
- **Method:** GET
- **Authentication:** None

**Response (200 OK):**
```json
{
  "status": "healthy",
  "environment": "development",
  "database": "connected",
  "redis": "connected",
  "anthias": "connected",
  "services": {
    "database": {
      "status": "connected",
      "critical": true
    },
    "redis": {
      "status": "connected",
      "critical": false
    },
    "anthias": {
      "status": "connected",
      "critical": false,
      "url": "http://192.168.5.12:8000",
      "impact": "File uploads will fail if disconnected"
    }
  }
}
```

**Status Values:**
- `healthy` - All services connected
- `degraded` - Some non-critical services down (Redis or Anthias)
- `unhealthy` - Critical services down (Database)

**Example cURL:**
```bash
curl http://192.168.5.12:8001/health
```

---

## Complete Upload Example (JavaScript)

```javascript
// Upload content with metadata extraction
async function uploadContent(file, title, description = "", duration = 10) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("title", title);
  formData.append("description", description);
  formData.append("duration", duration);
  formData.append("is_active", "true");

  // Enable auto-transcoding for videos
  if (file.type.startsWith("video/")) {
    formData.append("transcode_on_upload", "true");
    formData.append("transcode_quality_levels", "1080p,720p,480p");
  }

  try {
    const response = await fetch("http://192.168.5.12:8001/api/content/upload", {
      method: "POST",
      body: formData,
      // Note: Don't set Content-Type header, browser will set it with boundary
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Upload failed");
    }

    const result = await response.json();
    console.log("Upload successful:", result.data);

    return result.data;

  } catch (error) {
    console.error("Upload error:", error);
    throw error;
  }
}

// Usage
const fileInput = document.getElementById("file-input");
fileInput.addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (file) {
    const content = await uploadContent(
      file,
      "Product Demo",
      "New product showcase",
      30
    );

    // Display uploaded content
    if (content.content_type === "image") {
      const img = document.createElement("img");
      img.src = `http://192.168.5.12:8001/api/content/${content.id}/image`;
      document.body.appendChild(img);
    } else {
      const video = document.createElement("video");
      video.src = `http://192.168.5.12:8001/api/content/${content.id}/video`;
      video.controls = true;
      document.body.appendChild(video);
    }
  }
});
```

---

## Error Handling Best Practices

### Checking Anthias Connectivity

```javascript
async function checkAnthiasStatus() {
  const response = await fetch("http://192.168.5.12:8001/health");
  const health = await response.json();

  if (health.anthias === "disconnected") {
    console.warn("Anthias storage is offline. File uploads will fail.");
    return false;
  }

  return true;
}

// Before upload
if (await checkAnthiasStatus()) {
  await uploadContent(file, title);
} else {
  alert("File upload unavailable. Please try again later.");
}
```

### Retry Logic

```javascript
async function uploadWithRetry(file, title, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await uploadContent(file, title);
    } catch (error) {
      console.log(`Upload attempt ${attempt} failed:`, error);

      if (attempt < maxRetries) {
        // Exponential backoff: 1s, 2s, 4s
        const delay = Math.pow(2, attempt - 1) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw error; // All retries exhausted
      }
    }
  }
}
```

---

## Performance Optimization

### Upload Progress Tracking

```javascript
async function uploadWithProgress(file, title, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    // Track upload progress
    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) {
        const percent = (event.loaded / event.total) * 100;
        onProgress(percent);
      }
    });

    xhr.addEventListener("load", () => {
      if (xhr.status === 201) {
        const result = JSON.parse(xhr.responseText);
        resolve(result.data);
      } else {
        reject(new Error("Upload failed"));
      }
    });

    xhr.addEventListener("error", () => {
      reject(new Error("Network error"));
    });

    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title);

    xhr.open("POST", "http://192.168.5.12:8001/api/content/upload");
    xhr.send(formData);
  });
}

// Usage
await uploadWithProgress(file, "Video", (percent) => {
  console.log(`Upload progress: ${percent.toFixed(1)}%`);
  progressBar.style.width = `${percent}%`;
});
```

### Lazy Image Loading

```javascript
// Load thumbnail first, full image later
function displayContentImage(contentId) {
  const img = document.createElement("img");

  // Load low-quality placeholder (if available)
  img.src = `/api/content/${contentId}/thumbnail`; // If you implement this

  // Load full quality when visible
  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      img.src = `http://192.168.5.12:8001/api/content/${contentId}/image`;
      observer.disconnect();
    }
  });

  observer.observe(img);
  return img;
}
```

---

## Security Considerations

### File Type Validation

```javascript
const ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif"];
const ALLOWED_VIDEO_TYPES = ["video/mp4", "video/mpeg", "video/quicktime"];

function validateFile(file) {
  const isImage = ALLOWED_IMAGE_TYPES.includes(file.type);
  const isVideo = ALLOWED_VIDEO_TYPES.includes(file.type);

  if (!isImage && !isVideo) {
    throw new Error(`Invalid file type: ${file.type}`);
  }

  return true;
}
```

### File Size Validation

```javascript
const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

function validateFileSize(file) {
  if (file.size > MAX_FILE_SIZE) {
    throw new Error(`File too large: ${(file.size / 1024 / 1024).toFixed(1)}MB (max 100MB)`);
  }

  return true;
}
```

---

## Monitoring & Analytics

### Track Upload Success Rate

```javascript
let uploadStats = {
  total: 0,
  success: 0,
  failed: 0
};

async function monitoredUpload(file, title) {
  uploadStats.total++;

  try {
    const result = await uploadContent(file, title);
    uploadStats.success++;
    return result;
  } catch (error) {
    uploadStats.failed++;
    throw error;
  }
}

// Log stats
console.log(`Upload success rate: ${(uploadStats.success / uploadStats.total * 100).toFixed(1)}%`);
```

---

## Troubleshooting

### Common Issues

**1. Upload fails with "Cannot connect to Anthias service"**

**Diagnosis:**
```bash
# Check Anthias is running
curl http://192.168.5.12:8000/api/v1/assets

# Check health endpoint
curl http://192.168.5.12:8001/health
```

**Solution:**
- Verify Anthias service is running on port 8000
- Check ANTHIAS_API_URL in backend .env file
- Verify network connectivity between backend and Anthias

**2. Images don't display in browser**

**Diagnosis:**
```bash
# Check Content-Type header
curl -I http://192.168.5.12:8001/api/content/1/image
```

**Solution:**
- Verify proxy endpoint is working
- Check mime_type in database is correct
- Ensure anthias_asset_id is valid

**3. Upload succeeds but content not showing**

**Diagnosis:**
```bash
# Check content record exists
curl http://192.168.5.12:8001/api/content/1

# Check is_active status
```

**Solution:**
- Verify is_active is true
- Check content assignment to device/tag
- Clear browser/app cache

---

## API Response Standards

All Quick Wins API responses follow this format:

**Success Response:**
```json
{
  "success": true,
  "data": { /* actual response data */ },
  "request_id": "req_abc123"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "ExceptionName",
  "message": "Human-readable error message",
  "details": { /* additional error context */ },
  "request_id": "req_abc123",
  "status_code": 400
}
```

**Paginated Response:**
```json
{
  "success": true,
  "data": [ /* array of items */ ],
  "pagination": {
    "total": 50,
    "page": 1,
    "page_size": 10,
    "total_pages": 5
  },
  "request_id": "req_abc123"
}
```

---

## Conclusion

The Anthias integration provides a robust, production-ready content storage solution. All file operations (upload, serve, delete) are handled transparently through the backend API, with Anthias serving as the storage layer and PostgreSQL as the metadata store.

For additional help, refer to:
- **Main Documentation:** `/ANTHIAS_INTEGRATION_SUMMARY.md`
- **API Docs:** `http://192.168.5.12:8001/docs` (Swagger UI)
- **Health Check:** `http://192.168.5.12:8001/health`
