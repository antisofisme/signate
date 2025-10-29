# Content API Quick Reference

**File:** `/mnt/g/khoirul/signate/backend/app/api/content.py`
**Status:** ✅ 100% Quick Wins Compliant
**Last Updated:** 2025-10-28

---

## Endpoints Summary

| Method | Path | Purpose | Auth | Breaking Changes |
|--------|------|---------|------|------------------|
| POST | `/upload` | Upload content file | Optional | None |
| GET | `/` | List content | Optional | ⚠️ Pagination: skip→page |
| GET | `/{content_id}` | Get single content | Optional | None |
| PATCH | `/{content_id}` | Update content | Optional | None |
| DELETE | `/{content_id}` | Delete content | Optional | None |
| POST | `/{content_id}/assign` | Assign to device/tag | Optional | None |
| GET | `/{content_id}/assignments` | List assignments | Optional | None |
| DELETE | `/{content_id}/assign` | Unassign from device/tag | Optional | None |
| GET | `/{content_id}/image` | Serve image proxy | Public | None |
| GET | `/{content_id}/video` | Serve video proxy | Public | None |

---

## 1. Upload Content

**Endpoint:** `POST /api/content/upload`

**Request:**
```bash
curl -X POST "http://192.168.5.12:8001/api/content/upload" \
  -F "file=@banner.jpg" \
  -F "title=Lobby Banner" \
  -F "description=Promotional banner for lobby display" \
  -F "duration=15" \
  -F "is_active=true"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Lobby Banner",
    "description": "Promotional banner for lobby display",
    "content_type": "image",
    "anthias_url": "http://192.168.5.12:8000/data/screenly_assets/abc123.jpg",
    "anthias_asset_id": "abc123",
    "duration": 15,
    "is_active": true,
    "file_size": 1024000,
    "mime_type": "image/jpeg",
    "resolution": "1920x1080",
    "width": 1920,
    "height": 1080,
    "created_at": "2025-10-28T10:00:00Z"
  },
  "meta": {
    "timestamp": "2025-10-28T10:00:00Z",
    "request_id": "abc-123"
  }
}
```

**Notes:**
- Supports image (jpeg, png, gif) and video (mp4, avi, mov)
- Auto-extracts metadata using FFprobe
- For videos, duration auto-set to video length
- Uploads to Anthias for storage

---

## 2. List Content (UPDATED)

**Endpoint:** `GET /api/content`

**Parameters:**
- `page` (int, default 1) - Page number (1-indexed) ⚠️ NEW
- `limit` (int, default 100) - Items per page
- `content_type` (string, optional) - Filter: "image" or "video"
- `is_active` (boolean, optional) - Filter by active status

**Old Request (DEPRECATED):**
```bash
curl "http://192.168.5.12:8001/api/content?skip=20&limit=10"
```

**New Request:**
```bash
curl "http://192.168.5.12:8001/api/content?page=3&limit=10"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Lobby Banner",
      "content_type": "image",
      "anthias_url": "http://192.168.5.12:8000/data/screenly_assets/abc123.jpg",
      "duration": 15,
      "is_active": true,
      "created_at": "2025-10-28T10:00:00Z",
      "updated_at": "2025-10-28T10:00:00Z"
    }
  ],
  "meta": {
    "total": 150,
    "page": 3,
    "page_size": 10,
    "total_pages": 15,
    "timestamp": "2025-10-28T10:00:00Z",
    "request_id": "abc-123"
  }
}
```

**Migration:**
```javascript
// Before
const skip = (currentPage - 1) * limit;
fetch(`/api/content?skip=${skip}&limit=${limit}`);

// After
fetch(`/api/content?page=${currentPage}&limit=${limit}`);
```

---

## 3. Get Single Content

**Endpoint:** `GET /api/content/{content_id}`

**Request:**
```bash
curl "http://192.168.5.12:8001/api/content/1"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Lobby Banner",
    "description": "Promotional banner",
    "content_type": "image",
    "anthias_url": "http://192.168.5.12:8000/data/screenly_assets/abc123.jpg",
    "anthias_asset_id": "abc123",
    "duration": 15,
    "is_active": true,
    "file_size": 1024000,
    "mime_type": "image/jpeg",
    "resolution": "1920x1080",
    "width": 1920,
    "height": 1080,
    "codec": "jpeg",
    "created_at": "2025-10-28T10:00:00Z",
    "updated_at": "2025-10-28T10:00:00Z"
  },
  "meta": {
    "timestamp": "2025-10-28T10:00:00Z",
    "request_id": "abc-123"
  }
}
```

**Error (404):**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Content with ID 999 not found",
    "details": {
      "resource_type": "Content",
      "resource_id": 999
    }
  },
  "meta": {
    "timestamp": "2025-10-28T10:00:00Z",
    "request_id": "abc-123"
  }
}
```

---

## 4. Update Content

**Endpoint:** `PATCH /api/content/{content_id}`

**Request:**
```bash
curl -X PATCH "http://192.168.5.12:8001/api/content/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Banner",
    "duration": 20,
    "is_active": false
  }'
```

**Request Body (partial update):**
```json
{
  "title": "Updated Banner",
  "description": "New description",
  "duration": 20,
  "video_start_time": 10.0,
  "video_end_time": 30.0,
  "is_active": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Updated Banner",
    "duration": 20,
    "is_active": false,
    "updated_at": "2025-10-28T10:30:00Z"
  },
  "meta": {
    "timestamp": "2025-10-28T10:30:00Z",
    "request_id": "abc-123"
  }
}
```

**Notes:**
- Database updated first (source of truth)
- Anthias sync attempted but non-critical
- If Anthias sync fails, request still succeeds

---

## 5. Delete Content

**Endpoint:** `DELETE /api/content/{content_id}`

**Request:**
```bash
curl -X DELETE "http://192.168.5.12:8001/api/content/1"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Content 1 deleted successfully"
  },
  "meta": {
    "timestamp": "2025-10-28T10:30:00Z",
    "request_id": "abc-123"
  }
}
```

**Notes:**
- Deletes from Anthias first (file storage)
- Then deletes from PostgreSQL
- Cascades to content_assignments

---

## 6. Assign Content

**Endpoint:** `POST /api/content/{content_id}/assign`

**Request:**
```bash
# Assign to specific device
curl -X POST "http://192.168.5.12:8001/api/content/1/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 5,
    "priority": 10
  }'

# Assign to tag (all devices with tag)
curl -X POST "http://192.168.5.12:8001/api/content/1/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "tag_id": 3,
    "priority": 5
  }'
```

**Request Body:**
```json
{
  "device_id": 5,      // Either device_id OR tag_id (not both)
  "tag_id": null,
  "priority": 10
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "content_id": 1,
    "device_id": 5,
    "tag_id": null,
    "priority": 10,
    "created_at": "2025-10-28T10:00:00Z"
  },
  "meta": {
    "timestamp": "2025-10-28T10:00:00Z",
    "request_id": "abc-123"
  }
}
```

**Validation:**
- Must assign to EITHER device_id OR tag_id (not both, not neither)
- Device must have status "active"
- Content, device, and tag must exist
- Prevents duplicate assignments

---

## 7. Get Content Assignments

**Endpoint:** `GET /api/content/{content_id}/assignments`

**Request:**
```bash
curl "http://192.168.5.12:8001/api/content/1/assignments"
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "content_id": 1,
      "device_id": 5,
      "tag_id": null,
      "priority": 10,
      "created_at": "2025-10-28T10:00:00Z"
    },
    {
      "id": 2,
      "content_id": 1,
      "device_id": null,
      "tag_id": 3,
      "priority": 5,
      "created_at": "2025-10-28T10:05:00Z"
    }
  ],
  "meta": {
    "timestamp": "2025-10-28T10:30:00Z",
    "request_id": "abc-123"
  }
}
```

---

## 8. Unassign Content

**Endpoint:** `DELETE /api/content/{content_id}/assign`

**Request:**
```bash
# Unassign from device
curl -X DELETE "http://192.168.5.12:8001/api/content/1/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 5
  }'

# Unassign from tag
curl -X DELETE "http://192.168.5.12:8001/api/content/1/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "tag_id": 3
  }'
```

**Request Body:**
```json
{
  "device_id": 5,
  "tag_id": null
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": "Content 1 unassigned successfully"
  },
  "meta": {
    "timestamp": "2025-10-28T10:30:00Z",
    "request_id": "abc-123"
  }
}
```

---

## 9. Serve Image Proxy

**Endpoint:** `GET /api/content/{content_id}/image`

**Purpose:** Proxies image from Anthias with correct Content-Type headers

**Request:**
```bash
curl "http://192.168.5.12:8001/api/content/1/image" -o image.jpg
```

**Response:**
- HTTP 200 with binary image data
- `Content-Type: image/jpeg` (or appropriate MIME type)

**Error Response (404):**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Content with ID 999 not found",
    "details": {
      "resource_type": "Content",
      "resource_id": 999
    }
  },
  "meta": {
    "timestamp": "2025-10-28T10:30:00Z",
    "request_id": "abc-123"
  }
}
```

**Use Cases:**
- Display thumbnails in Web Admin
- Preview images before assignment
- Direct image serving to viewers

---

## 10. Serve Video Proxy

**Endpoint:** `GET /api/content/{content_id}/video`

**Purpose:** Proxies video from Anthias with streaming headers

**Request:**
```bash
curl "http://192.168.5.12:8001/api/content/1/video" -o video.mp4
```

**Response:**
- HTTP 200 with binary video data
- `Content-Type: video/mp4` (or appropriate MIME type)
- `Accept-Ranges: bytes` (for streaming support)
- `Content-Length: <size>` (file size in bytes)

**Error Response (404):**
```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Content with ID 999 not found",
    "details": {
      "resource_type": "Content",
      "resource_id": 999
    }
  },
  "meta": {
    "timestamp": "2025-10-28T10:30:00Z",
    "request_id": "abc-123"
  }
}
```

**Use Cases:**
- Video preview in Web Admin
- Direct video serving to viewers
- Range request support for seeking

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| NOT_FOUND | 404 | Content, device, or tag not found |
| BAD_REQUEST | 400 | Invalid parameters or validation failure |
| CONFLICT | 409 | Assignment already exists |
| INTERNAL_SERVER_ERROR | 500 | Upload failed, Anthias error, or server error |

---

## TypeScript Types

```typescript
interface Content {
  id: number;
  title: string;
  description?: string;
  content_type: 'image' | 'video';
  anthias_url: string;
  anthias_asset_id: string;
  duration: number;
  is_active: boolean;
  file_size?: number;
  mime_type?: string;
  resolution?: string;
  width?: number;
  height?: number;
  codec?: string;
  fps?: number;
  bitrate?: number;
  video_duration?: number;
  video_start_time?: number;
  video_end_time?: number;
  audio_codec?: string;
  audio_bitrate?: number;
  audio_sample_rate?: number;
  created_at: string;
  updated_at: string;
}

interface ContentAssignment {
  id: number;
  content_id: number;
  device_id?: number;
  tag_id?: number;
  priority: number;
  created_at: string;
}

interface PaginatedResponse<T> {
  success: true;
  data: T[];
  meta: {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
    timestamp: string;
    request_id: string;
  };
}
```

---

## Frontend Integration

### Content Service (TypeScript)

```typescript
// src/services/api/content.ts

export const contentApi = {
  // List content with NEW pagination
  list: async (page = 1, limit = 10, filters = {}) => {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
      ...filters
    });
    return api.get(`/content?${params}`);
  },

  // Get single content
  get: async (id: number) => {
    return api.get(`/content/${id}`);
  },

  // Upload content
  upload: async (file: File, metadata: {
    title: string;
    description?: string;
    duration?: number;
    is_active?: boolean;
  }) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', metadata.title);
    if (metadata.description) formData.append('description', metadata.description);
    formData.append('duration', (metadata.duration || 10).toString());
    formData.append('is_active', (metadata.is_active ?? true).toString());

    return api.post('/content/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  // Update content
  update: async (id: number, data: Partial<Content>) => {
    return api.patch(`/content/${id}`, data);
  },

  // Delete content
  delete: async (id: number) => {
    return api.delete(`/content/${id}`);
  },

  // Assign content
  assign: async (contentId: number, assignment: {
    device_id?: number;
    tag_id?: number;
    priority?: number;
  }) => {
    return api.post(`/content/${contentId}/assign`, assignment);
  },

  // Get assignments
  getAssignments: async (contentId: number) => {
    return api.get(`/content/${contentId}/assignments`);
  },

  // Unassign content
  unassign: async (contentId: number, assignment: {
    device_id?: number;
    tag_id?: number;
  }) => {
    return api.delete(`/content/${contentId}/assign`, { data: assignment });
  },

  // Get image URL
  getImageUrl: (contentId: number) => {
    return `${API_BASE_URL}/content/${contentId}/image`;
  },

  // Get video URL
  getVideoUrl: (contentId: number) => {
    return `${API_BASE_URL}/content/${contentId}/video`;
  }
};
```

---

## Testing Checklist

- [ ] Upload image content
- [ ] Upload video content
- [ ] List content with page=1
- [ ] List content with page=2
- [ ] Filter by content_type=image
- [ ] Filter by is_active=true
- [ ] Get single content by ID
- [ ] Get non-existent content (404)
- [ ] Update content metadata
- [ ] Delete content
- [ ] Assign content to device
- [ ] Assign content to tag
- [ ] Get content assignments
- [ ] Unassign content from device
- [ ] Unassign content from tag
- [ ] Serve image via proxy
- [ ] Serve video via proxy
- [ ] Test error responses have new format

---

## Performance Notes

- **Upload:** Can take 10-30s for large videos (FFprobe extraction)
- **List:** Efficient query with indexes on created_at
- **Image/Video Proxy:** Streams from Anthias, suitable for preview
- **Pagination:** Use reasonable page_size (10-50) for best performance

---

## Architecture Notes

### Database-First Strategy
- PostgreSQL is the **source of truth** for all content metadata
- Viewers read from PostgreSQL, NOT from Anthias
- Anthias is used only for file storage

### Anthias Sync
- Upload: Anthias must succeed (critical)
- Update: Anthias sync is optional (graceful degradation)
- Delete: Anthias deletion attempted but non-blocking

### Metadata Extraction
- FFprobe used for video/image metadata
- Extracted: resolution, codec, fps, bitrate, duration
- Auto-set video duration from video_duration field
