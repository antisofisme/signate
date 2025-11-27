# Playlist Service - Comprehensive Analysis

## Project Overview
**Service**: Playlist Management System  
**Location**: `/mnt/g/khoirul/signate/backend-python/services/playlist/`  
**Framework**: FastAPI (Python)  
**Architecture**: Clean Architecture with Domain-Driven Design  
**Status**: Fully implemented with audit logging and cache invalidation

---

## 1. DATABASE MODELS

### 1.1 Table Structure

#### **playlists** (Core Table)
```sql
CREATE TABLE playlists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    priority INTEGER DEFAULT 0 NOT NULL,
    schedule JSONB,  -- Flexible schedule config
    is_default BOOLEAN DEFAULT FALSE,  -- 🐛 Added in models.py (migration 031)
    is_pms_template BOOLEAN DEFAULT FALSE,  -- 🐛 Added for hotel PMS integration
    background_audio_id INTEGER REFERENCES contents(id),  -- Playlist-level audio
    
    -- Multi-tenancy & User tracking
    organization_id INTEGER NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    
    -- Audit timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes: organization_id, created_by_id, is_active, deleted_at
-- Unique Constraint: (organization_id, name, deleted_at)
```

#### **playlist_contents** (Junction Table - Many-to-Many)
```sql
CREATE TABLE playlist_contents (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    content_id INTEGER NOT NULL REFERENCES contents(id) ON DELETE CASCADE,
    
    -- Ordering and duration
    order_index INTEGER NOT NULL DEFAULT 0,  -- 0-based ordering
    duration INTEGER,  -- Override content duration (in seconds)
    is_muted BOOLEAN DEFAULT FALSE,  -- Per-content mute control
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints: prevent duplicate content in same playlist
    CONSTRAINT unique_playlist_content UNIQUE (playlist_id, content_id)
);

-- Indexes: playlist_id, content_id, (playlist_id, order_index)
```

#### **playlist_assignments** (Polymorphic - Device OR Tag)
```sql
CREATE TABLE playlist_assignments (
    id SERIAL PRIMARY KEY,
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    
    -- Polymorphic: either device_id OR tag_id (not both)
    device_id INTEGER REFERENCES devices(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Validation Constraints
    CONSTRAINT check_assignment_type CHECK (
        (device_id IS NOT NULL AND tag_id IS NULL) OR
        (device_id IS NULL AND tag_id IS NOT NULL)
    ),
    CONSTRAINT unique_playlist_device UNIQUE (playlist_id, device_id),
    CONSTRAINT unique_playlist_tag UNIQUE (playlist_id, tag_id)
);

-- Indexes: playlist_id, device_id, tag_id
```

---

## 2. MODELS & DOMAIN ENTITIES

### 2.1 SQLAlchemy Models
**File**: `/mnt/g/khoirul/signate/backend-python/services/playlist/repositories/models.py`

```python
class PlaylistModel(Base):
    """Playlist SQLAlchemy model"""
    __tablename__ = "playlists"
    
    # Fields
    id, name, description, is_active, priority, schedule
    is_default, is_pms_template, background_audio_id
    organization_id, created_by_id
    created_at, updated_at, deleted_at
    
    # Relationships
    contents: List[PlaylistContentModel]  # back_populates, cascade delete
    assignments: List[PlaylistAssignmentModel]  # back_populates, cascade delete

class PlaylistContentModel(Base):
    """Playlist content junction model"""
    __tablename__ = "playlist_contents"
    
    # Fields
    id, playlist_id, content_id, order_index, duration, is_muted
    created_at
    
    # Relationships
    playlist: PlaylistModel

class PlaylistAssignmentModel(Base):
    """Playlist assignment model (polymorphic: device OR tag)"""
    __tablename__ = "playlist_assignments"
    
    # Fields
    id, playlist_id, device_id (nullable), tag_id (nullable)
    created_at
    
    # Relationships
    playlist: PlaylistModel
```

### 2.2 Domain Entities
**File**: `/mnt/g/khoirul/signate/backend-python/services/playlist/domain/playlist.py`

```python
class Playlist:
    """Pure Python domain object - Business logic encapsulation"""
    
    def __init__(
        name, organization_id, description, is_active, priority, schedule,
        is_default, is_pms_template, created_by_id, created_at, updated_at,
        deleted_at, content_count, total_duration
    )
    
    # Business logic methods
    def update_details(name, description, is_active, priority, schedule)
    def activate(), deactivate(), soft_delete()
    def is_deleted() -> bool
    def to_dict() -> Dict[str, Any]
    
    # Validation in __init__ via _validate()
    - name cannot be empty or > 255 chars
    - priority must be >= 0
    - organization_id required

class PlaylistContent:
    """Playlist content item entity"""
    
    def __init__(
        playlist_id, content_id, order_index,
        id, duration, created_at
    )
    
    # Business logic
    def update_order(new_order)
    def update_duration(new_duration)
    def to_dict() -> Dict[str, Any]
    
    # Validation
    - order_index >= 0
    - duration > 0 (if set)

class PlaylistAssignment:
    """Playlist assignment entity (to device or tag)"""
    
    def __init__(
        playlist_id, id, device_id, tag_id, created_at
    )
    
    # Business logic
    def is_device_assignment() -> bool
    def is_tag_assignment() -> bool
    def to_dict() -> Dict[str, Any]
    
    # Validation
    - Must have device_id OR tag_id (not both, not neither)
```

---

## 3. DATA TRANSFER OBJECTS (DTOs)

### 3.1 Request DTOs
**File**: `/mnt/g/khoirul/signate/backend-python/services/playlist/dtos.py`

```python
class PlaylistCreateRequest:
    """Create playlist request"""
    name: str  # Required, 1-255 chars
    description: Optional[str]
    is_active: bool = True
    priority: int = 0  # >= 0
    schedule: Optional[Dict[str, Any]]

class PlaylistUpdateRequest:
    """Patch update (all fields optional)"""
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    schedule: Optional[Dict[str, Any]] = None

class AddContentRequest:
    """Add content to playlist (bulk)"""
    content_ids: List[int]  # min_items=1

class ReorderContentRequest:
    """Reorder and update duration"""
    content_items: List[Dict[str, Any]]  # [{id, order_index, duration?}, ...]

class AssignDevicesRequest:
    """Assign to devices (bulk)"""
    device_ids: List[int]  # min_items=1

class AssignTagsRequest:
    """Assign to tags (bulk)"""
    tag_ids: List[int]  # min_items=1
```

### 3.2 Response DTOs

```python
class PlaylistResponse:
    """Single playlist response"""
    id, name, description, is_active, priority, schedule
    organization_id, created_by, created_at, updated_at, deleted_at
    content_count: int = 0  # Computed
    total_duration: int = 0  # Computed (seconds)

class PlaylistListResponse:
    """List response"""
    total: int
    items: List[PlaylistResponse]

class PlaylistContentItemResponse:
    """Playlist content item"""
    id, playlist_id, content_id, order_index, duration
    created_at
    content_name: Optional[str]  # Enriched
    content_type: Optional[str]  # Enriched

class PlaylistContentListResponse:
    """Content list response"""
    total: int
    items: List[PlaylistContentItemResponse]

class BulkOperationResponse:
    """Bulk operation results"""
    success: bool = True
    message: str
    added: Optional[int]  # For add operations
    assigned: Optional[int]  # For assign operations
    skipped_missing: Optional[List[int]]
    skipped_duplicate: Optional[List[int]]

class PlaylistAssignmentsResponse:
    """Device and tag assignments"""
    devices: List[DeviceInfoResponse]
    tags: List[TagInfoResponse]
```

---

## 4. REPOSITORY PATTERN (Data Access Layer)

### 4.1 Repository Interface
**File**: `/mnt/g/khoirul/signate/backend-python/services/playlist/domain/interfaces.py`

```python
class IPlaylistRepository(ABC):
    """Contracts for data access"""
    
    # CRUD Operations
    @abstractmethod
    def create(playlist: Playlist) -> Playlist
    @abstractmethod
    def find_all(organization_id, skip, limit, is_active, include_deleted) -> Tuple[List[Playlist], int]
    @abstractmethod
    def find_by_id(playlist_id, organization_id) -> Optional[Playlist]
    @abstractmethod
    def update(playlist: Playlist) -> Playlist
    @abstractmethod
    def delete(playlist_id, organization_id, soft) -> bool
    
    # Content Management
    @abstractmethod
    def get_playlist_contents(playlist_id, organization_id) -> List[PlaylistContent]
    @abstractmethod
    def add_contents_to_playlist(playlist_id, content_ids, organization_id) -> Dict[str, Any]
    @abstractmethod
    def remove_content_from_playlist(playlist_content_id, playlist_id, organization_id) -> bool
    @abstractmethod
    def reorder_playlist_contents(playlist_id, content_items, organization_id) -> int
    
    # Device/Tag Assignments
    @abstractmethod
    def get_playlist_assignments(playlist_id, organization_id) -> Dict[str, Any]
    @abstractmethod
    def assign_to_devices(playlist_id, device_ids, organization_id) -> Dict[str, Any]
    @abstractmethod
    def assign_to_tags(playlist_id, tag_ids, organization_id) -> Dict[str, Any]
    @abstractmethod
    def unassign_from_devices(playlist_id, device_ids, organization_id) -> int
    @abstractmethod
    def unassign_from_tags(playlist_id, tag_ids, organization_id) -> int
    
    # Utility
    @abstractmethod
    def calculate_playlist_stats(playlist_id, organization_id) -> Dict[str, int]
```

### 4.2 Repository Implementation
**File**: `/mnt/g/khoirul/signate/backend-python/services/playlist/repositories/playlist_repo.py`

#### Key Features:

**Multi-Tenancy Enforcement**
```python
def find_by_id(self, playlist_id: int, organization_id: int) -> Optional[Playlist]:
    """Organization filter is ALWAYS applied"""
    playlist_model = self.db.query(PlaylistModel).filter(
        and_(
            PlaylistModel.id == playlist_id,
            PlaylistModel.organization_id == organization_id,  # ✅ CRITICAL
            PlaylistModel.deleted_at.is_(None)
        )
    ).first()
```

**Cache Invalidation (P0-7 Critical Fix)**
```python
def _invalidate_content_resolver_cache(self, playlist_id: int, organization_id: int):
    """
    When playlist changes, invalidate cache for:
    1. All directly assigned devices
    2. All devices with tags that reference the playlist
    3. Organization-wide content resolution
    
    CRITICAL: Ensures devices get updated content on next resolution
    """
    # Direct device assignments
    device_assignments = self.db.query(PlaylistAssignmentModel).filter(
        PlaylistAssignmentModel.playlist_id == playlist_id,
        PlaylistAssignmentModel.device_id.isnot(None)
    ).all()
    for assignment in device_assignments:
        cache.delete(f"content_resolution:{assignment.device_id}")
    
    # Tag assignments -> find all devices with those tags
    tag_assignments = self.db.query(PlaylistAssignmentModel).filter(
        PlaylistAssignmentModel.playlist_id == playlist_id,
        PlaylistAssignmentModel.tag_id.isnot(None)
    ).all()
    for tag_assignment in tag_assignments:
        device_tags = self.db.query(DeviceTagModel).filter(
            DeviceTagModel.tag_id == tag_assignment.tag_id
        ).all()
        for device_tag in device_tags:
            cache.delete(f"content_resolution:{device_tag.device_id}")
    
    # Pattern-based cache invalidation
    cache.invalidate_pattern(f"content_resolution:org_{organization_id}:*")
```

**Bulk Content Management**
```python
def add_contents_to_playlist(
    self, playlist_id: int, content_ids: List[int], organization_id: int
) -> Dict[str, Any]:
    """
    Returns: {
        "added": int,
        "skipped_missing": [ids_not_found],
        "skipped_duplicate": [already_in_playlist]
    }
    
    Process:
    1. Verify playlist belongs to org
    2. Validate content exists and belongs to org
    3. Check for existing items
    4. Bulk insert with auto-incrementing order_index
    5. Invalidate content resolver cache
    """
```

**Ordering & Duration Handling**
```python
def reorder_playlist_contents(
    self, playlist_id: int, content_items: List[Dict[str, Any]], organization_id: int
) -> int:
    """
    Bulk update order_index and duration overrides
    
    Input: [{"id": 1, "order_index": 0, "duration": 30}, ...]
    Returns: count of updated items
    
    Cache invalidation applied after update
    """
```

**Statistics Calculation**
```python
def calculate_playlist_stats(self, playlist_id: int, organization_id: int) -> Dict[str, int]:
    """
    Returns: {"content_count": int, "total_duration": int (seconds)}
    
    Duration logic:
    1. Use playlist_content.duration if set (override)
    2. Fallback to content.duration (accepts N+1 queries - rare case)
    """
```

---

## 5. USE CASES (Business Logic Layer)

### 5.1 Playlist CRUD Use Cases

**File**: `/mnt/g/khoirul/signate/backend-python/services/playlist/use_cases/`

```python
class CreatePlaylistUseCase:
    """
    Create new playlist with organization validation
    
    Enforcement:
    - Organization quota check (CRITICAL FIX P0-9)
    - Domain entity validation
    - Persistence via repository
    
    def execute(
        name, organization_id, description, is_active, priority, schedule, created_by
    ) -> Playlist:
        # 1. Check quota atomically
        quota_service.enforce_playlist_quota_atomic(organization_id)
        # 2. Create domain entity (validates)
        playlist = Playlist(...)
        # 3. Persist
        return repository.create(playlist)
    """

class ListPlaylistsUseCase:
    """
    List playlists with pagination and filters
    
    def execute(
        organization_id, skip, limit, is_active, include_deleted
    ) -> Tuple[List[Playlist], int]
        # Delegates to repository with org filter
    """

class GetPlaylistUseCase:
    """Get single playlist by ID with org filter"""

class UpdatePlaylistUseCase:
    """
    Update playlist with validation
    
    Process:
    1. Load existing playlist (with org filter)
    2. Call domain entity update_details()
    3. Persist changes
    4. Cache invalidation automatic via repository
    """

class DeletePlaylistUseCase:
    """Hard delete with cascade to contents and assignments"""
```

### 5.2 Content Management Use Cases

```python
class AddContentToPlaylistUseCase:
    """Bulk add content with duplicate detection"""
    def execute(playlist_id, content_ids, organization_id) -> Dict

class GetPlaylistContentUseCase:
    """Fetch content items ordered by order_index"""
    def execute(playlist_id, organization_id) -> List[PlaylistContent]

class RemoveContentFromPlaylistUseCase:
    """Remove single content item"""
    def execute(playlist_content_id, playlist_id, organization_id) -> bool

class ReorderPlaylistContentUseCase:
    """Bulk reorder items and update durations"""
    def execute(playlist_id, content_items, organization_id) -> int
```

### 5.3 Assignment Use Cases

```python
class GetPlaylistAssignmentsUseCase:
    """Fetch device and tag assignments"""
    def execute(playlist_id, organization_id) -> Dict[str, Any]
    # Returns: {"devices": [...], "tags": [...]}

class AssignPlaylistToDevicesUseCase:
    """Bulk assign to devices"""
    def execute(playlist_id, device_ids, organization_id) -> Dict[str, Any]
    # Validates device ownership, detects duplicates

class AssignPlaylistToTagsUseCase:
    """Bulk assign to tags"""
    def execute(playlist_id, tag_ids, organization_id) -> Dict[str, Any]

class UnassignPlaylistFromDevicesUseCase:
    """Bulk unassign from devices"""
    def execute(playlist_id, device_ids, organization_id) -> int

class UnassignPlaylistFromTagsUseCase:
    """Bulk unassign from tags"""
    def execute(playlist_id, tag_ids, organization_id) -> int
```

---

## 6. API ROUTES (FastAPI Endpoints)

### 6.1 Admin Routes
**File**: `/mnt/g/khoirul/signate/backend-python/services/playlist/routes.py`

#### Dependency Injection Pattern
```python
# All dependencies use FastAPI's Depends()
def get_playlist_repository(db: Session = Depends(get_db)) -> IPlaylistRepository
def get_audit_logger(create_audit_use_case = Depends(...)) -> AuditLogger
def get_create_playlist_use_case(repo = Depends(...)) -> CreatePlaylistUseCase

# Route example
@router.post("", status_code=status.HTTP_201_CREATED)
def create_playlist(
    request_body: PlaylistCreateRequest,
    use_case: CreatePlaylistUseCase = Depends(get_create_playlist_use_case),
    current_user: dict = Depends(get_current_user),  # ✅ Auth required
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
```

#### Playlist CRUD Endpoints

| Endpoint | Method | Auth | Audit | Description |
|----------|--------|------|-------|-------------|
| `/api/v1/playlists` | POST | ✅ | ✅ | Create playlist |
| `/api/v1/playlists` | GET | ✅ | ❌ | List playlists |
| `/api/v1/playlists/{id}` | GET | ✅ | ❌ | Get single playlist |
| `/api/v1/playlists/{id}` | PATCH | ✅ | ✅ | Update playlist |
| `/api/v1/playlists/{id}` | DELETE | ✅ | ✅ | Delete playlist |

**Key Security Pattern**:
```python
# Organization context from authenticated user
playlist = use_case.execute(
    ...,
    organization_id=current_user.organization_id  # ✅ Always enforced
)
```

#### Content Management Endpoints

| Endpoint | Method | Auth | Audit | Description |
|----------|--------|------|-------|-------------|
| `/api/v1/playlists/{id}/content` | GET | ✅ | ❌ | Get content items (ordered) |
| `/api/v1/playlists/{id}/content` | POST | ✅ | ✅ | Add content (bulk) |
| `/api/v1/playlists/{id}/content/{item_id}` | DELETE | ✅ | ✅ | Remove content |
| `/api/v1/playlists/{id}/reorder` | PATCH | ✅ | ✅ | Reorder content |

#### Assignment Endpoints

| Endpoint | Method | Auth | Audit | Description |
|----------|--------|------|-------|-------------|
| `/api/v1/playlists/{id}/assignments` | GET | ✅ | ❌ | Get assignments |
| `/api/v1/playlists/{id}/assign/devices` | POST | ✅ | ✅ | Assign to devices (bulk) |
| `/api/v1/playlists/{id}/assign/tags` | POST | ✅ | ✅ | Assign to tags (bulk) |
| `/api/v1/playlists/{id}/assign/devices` | DELETE | ✅ | ✅ | Unassign from devices |
| `/api/v1/playlists/{id}/assign/tags` | DELETE | ✅ | ✅ | Unassign from tags |

#### Content Resolution (Advanced)

```python
@router.get("/resolve/{device_id}", response_model=ContentResolution)
def resolve_content_for_device(
    device_id: int,
    playlist_repo: IPlaylistRepository = Depends(get_playlist_repository),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Determine what content should play on a device
    
    Resolution priority order:
    1. Active schedules (time/day based)
    2. Direct device assignments
    3. Tag-based assignments
    4. PMS content (hotel rooms)
    5. Default playlist
    
    Returns: ContentResolution with playlist and metadata
    """
```

### 6.2 Client Routes (Public - No Auth)
**File**: `/mnt/g/khoirul/signate/backend-python/services/playlist/client_routes.py`

```python
@router.get("/api/v1/client/playlist")
def get_playlist_for_device(device_id: int = Query(...)):
    """
    Get content assigned to device (PUBLIC endpoint)
    
    NO AUTHENTICATION REQUIRED - Players use this to fetch content
    
    Assignment priority (checked in order):
    1. Direct content assignments (ContentAssignmentModel)
    2. Playlist assignments (via assigned_playlist_id)
    
    Returns: PlaylistSyncResponse
        - playlist: Content object with items, or None
        - device_settings: Volume, rotation, background audio
        - has_changes: Always True (for caching)
        - message: Status message
    
    Content URL priority:
    - HLS URL for videos (adaptive bitrate)
    - Direct file URL fallback
    
    Per-content controls:
    - is_muted: Per-item mute flag
    - duration: Override (from playlist_contents.duration)
    """
```

---

## 7. AUDIT LOGGING

### 7.1 Audit Log Integration

**Pattern**: Every mutation endpoint logs to audit trail

```python
# DI for audit logger
def get_audit_logger(create_audit_use_case = Depends(...)) -> AuditLogger:
    return AuditLogger(create_audit_log_use_case=create_audit_use_case)

# Usage in endpoint
@router.post("")
def create_playlist(..., audit_logger: AuditLogger = Depends(get_audit_logger)):
    playlist = use_case.execute(...)
    
    audit_logger.log_action(
        user_id=current_user.id,
        action="playlist.create",  # Action type
        resource_type="playlist",   # Resource
        resource_id=playlist.id,    # Which resource
        details={"name": playlist.name, "is_active": playlist.is_active},
        organization_id=current_user.organization_id
    )
```

### 7.2 Audited Actions

| Action | Endpoint | Details Logged |
|--------|----------|----------------|
| `playlist.create` | POST /playlists | name, is_active |
| `playlist.update` | PATCH /playlists/{id} | name, is_active |
| `playlist.delete` | DELETE /playlists/{id} | deleted: true |
| `playlist.add_content` | POST /playlists/{id}/content | content_count, added |
| `playlist.remove_content` | DELETE /playlists/{id}/content/{item} | content_item_id |
| `playlist.reorder_content` | PATCH /playlists/{id}/reorder | updated_count |
| `playlist.assign_devices` | POST /playlists/{id}/assign/devices | device_count, assigned |
| `playlist.assign_tags` | POST /playlists/{id}/assign/tags | tag_count, assigned |
| `playlist.unassign_devices` | DELETE /playlists/{id}/assign/devices | removed_count |
| `playlist.unassign_tags` | DELETE /playlists/{id}/assign/tags | removed_count |

---

## 8. CONTENT RESOLUTION ENGINE

**File**: `/mnt/g/khoirul/signate/backend-python/services/playlist/domain/content_resolver.py`

### 8.1 Resolution Architecture

```python
class ContentResolver:
    """
    Intelligent content routing engine
    
    Determines what playlist/content plays on a device based on:
    - Active schedules (time-based)
    - Device assignments
    - Tag assignments
    - PMS integration (hotel rooms)
    - Organization defaults
    """
    
    def resolve_content_for_device(
        device_id: int,
        current_time: Optional[datetime] = None,
        use_cache: bool = True
    ) -> Optional[ContentResolution]:
        """
        Resolution sequence (highest to lowest priority):
        
        1. Active Schedules
           - Check for time/day-based schedules
           - Filter by applicable device targets
           - Return highest priority schedule's playlist
        
        2. Direct Device Assignment
           - Check device.assigned_playlist_id
           - Return if playlist is active
        
        3. Tag-Based Assignment
           - Get device tags
           - Find highest priority tag playlist
           - Return if playlist is active
        
        4. PMS Content
           - For hotel rooms (device.room_number set)
           - Fetch guest info from PMS
           - Use PMS template playlist
        
        5. Default Playlist
           - Organization default or first active playlist
           - Lowest priority fallback
        """
        
        # Cache check: 5-minute TTL
        if use_cache:
            cached = cache.get(f"content_resolution:{device_id}")
            if cached:
                return ContentResolution(**cached)
        
        # Resolution steps...
        
        # Cache result
        if use_cache:
            cache.set(cache_key, resolution.__dict__, ttl=300)
        
        return resolution
```

### 8.2 Resolution Result

```python
@dataclass
class ContentResolution:
    """Result of content resolution"""
    playlist_id: int
    playlist_name: str
    resolution_type: str  # 'schedule', 'direct', 'tag', 'pms', 'default'
    priority: int        # Used for conflict resolution
    schedule_id: Optional[int]  # If resolved via schedule
    tag_id: Optional[int]       # If resolved via tag
    pms_data: Optional[Dict]    # If resolved via PMS
    content_items: List[Dict]   # The actual content to play
```

---

## 9. MULTI-TENANCY IMPLEMENTATION

### 9.1 Organization Isolation

**Pattern**: Every query includes `organization_id` filter

```python
# ✅ CORRECT: Always filter by organization
def find_by_id(self, playlist_id: int, organization_id: int) -> Optional[Playlist]:
    playlist_model = self.db.query(PlaylistModel).filter(
        and_(
            PlaylistModel.id == playlist_id,
            PlaylistModel.organization_id == organization_id  # ✅ CRITICAL
        )
    ).first()

# ✅ Content validation includes org check
valid_content_ids = self.db.query(ContentModel.id).filter(
    and_(
        ContentModel.id.in_(content_ids),
        ContentModel.organization_id == organization_id  # ✅ CRITICAL
    )
).all()

# ✅ Device/Tag validation includes org check
valid_device_ids = self.db.query(DeviceModel.id).filter(
    and_(
        DeviceModel.id.in_(device_ids),
        DeviceModel.organization_id == organization_id  # ✅ CRITICAL
    )
).all()
```

### 9.2 User Context

```python
# From authenticated user (via FastAPI Depends)
current_user: dict = {
    "id": int,              # User ID
    "organization_id": int, # Organization context
    "role": str,            # RBAC role
}

# Always extracted and passed to use cases
playlist = use_case.execute(
    ...,
    organization_id=current_user.organization_id,
    created_by=current_user.id
)
```

### 9.3 Quota Enforcement

```python
# In CreatePlaylistUseCase
quota_service.enforce_playlist_quota_atomic(organization_id)
# Enforces organization-level playlist limits
# CRITICAL FIX P0-9: Prevents quota exhaustion
```

---

## 10. CACHE INVALIDATION STRATEGY

### 10.1 Cache Keys

```python
# Content resolution cache
f"content_resolution:{device_id}"  # Single device cache (5-min TTL)

# Organization-level pattern
f"content_resolution:org_{organization_id}:*"  # Wildcard invalidation
```

### 10.2 Invalidation Triggers

**When to invalidate**:
1. **Playlist modified** (name, active status, priority)
2. **Content added/removed** from playlist
3. **Content reordered** in playlist
4. **Device assigned** to playlist
5. **Device unassigned** from playlist
6. **Tag assigned** to playlist
7. **Tag unassigned** from playlist

**Implementation**:
```python
def _invalidate_content_resolver_cache(self, playlist_id: int, organization_id: int):
    """
    Clear cache for:
    1. All devices directly assigned to playlist
    2. All devices with tags assigned to playlist
    3. Organization pattern cache
    """
    # Direct device invalidation
    for device_id in direct_assigned_devices:
        cache.delete(f"content_resolution:{device_id}")
    
    # Tag-based device invalidation
    for device_id in tag_assigned_devices:
        cache.delete(f"content_resolution:{device_id}")
    
    # Pattern invalidation
    cache.invalidate_pattern(f"content_resolution:org_{organization_id}:*")
```

---

## 11. KEY PATTERNS & BEST PRACTICES

### 11.1 Dependency Injection

```python
# FastAPI @inject pattern
@router.post("")
def create_playlist(
    request_body: PlaylistCreateRequest,
    use_case: CreatePlaylistUseCase = Depends(get_create_playlist_use_case),
    current_user: dict = Depends(get_current_user),
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    """All dependencies injected via FastAPI's DI system"""
```

### 11.2 Domain Entity Validation

```python
# Validation in domain entity __init__
def __init__(self, name: str, organization_id: int, ...):
    self.name = name
    self.organization_id = organization_id
    self._validate()  # Automatic validation

def _validate(self):
    """Business rules validation"""
    if not self.name or len(self.name.strip()) == 0:
        raise ValueError("Playlist name cannot be empty")
    if not self.organization_id:
        raise ValueError("Organization ID is required")
```

### 11.3 Bulk Operations with Feedback

```python
def add_contents_to_playlist(...) -> Dict[str, Any]:
    """Returns detailed feedback"""
    return {
        "added": 5,                    # Successfully added
        "skipped_missing": [99, 100],  # Not found
        "skipped_duplicate": [1, 2]    # Already in playlist
    }
```

### 11.4 Ordered Results

```python
# Always ordered by order_index for consistency
content_models = self.db.query(PlaylistContentModel).filter(
    PlaylistContentModel.playlist_id == playlist_id
).order_by(PlaylistContentModel.order_index).all()  # ✅ Guaranteed order
```

---

## 12. ERROR HANDLING

### 12.1 HTTP Status Codes

| Status | Scenario |
|--------|----------|
| 201 | Resource created successfully |
| 200 | Read or successful update |
| 400 | Validation error (empty name, duplicate, etc.) |
| 403 | Forbidden (org isolation violated) |
| 404 | Resource not found |
| 500 | Server error |

### 12.2 Validation Errors

```python
# From domain entity
try:
    playlist = Playlist(name="", org_id=1)  # Fails validation
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

---

## 13. SUMMARY TABLE

| Aspect | Implementation |
|--------|-----------------|
| **Multi-Tenancy** | organization_id ALWAYS filtered |
| **User Context** | created_by_id tracked in DB |
| **RBAC** | Via get_current_user middleware |
| **Audit Logging** | Every mutation logged with action, resource, details |
| **Cache** | 5-min TTL on content resolution, invalidated on changes |
| **Ordering** | order_index in DB, ordered results guaranteed |
| **Bulk Ops** | Feedback on added/skipped/duplicates |
| **Content Resolver** | Priority-based: schedule > direct > tag > PMS > default |
| **Soft Delete** | deleted_at field support (not used in hard delete) |
| **Quota** | Enforced atomically per organization |

---

## 14. CRITICAL FIXES & NOTES

### P0-7: Content Resolver Cache Invalidation
```
When playlist changes, must invalidate cache for all affected devices.
Without this, devices continue playing stale content.
Fixed in: _invalidate_content_resolver_cache()
```

### P0-9: Playlist Quota Enforcement
```
Organization quota must be checked atomically.
Fixed in: CreatePlaylistUseCase with quota_service.enforce_playlist_quota_atomic()
```

### FIX: created_by Field Naming
```
Model uses: created_by_id (matches database)
Entity uses: created_by_id (direct assignment)
Migration 005: created_by column → Model uses created_by_id (correct)
```

---

## 15. MIGRATION TIMELINE

| File | Description | Status |
|------|-------------|--------|
| 005_create_playlists_tables.sql | Initial schema | ✅ |
| 029_add_tag_playlist_assignment.sql | Tag support | ✅ |
| 030_add_device_playlist_assignment.sql | Device direct assignment | ✅ |
| 031_add_playlist_flags.sql | is_default, is_pms_template | ✅ |
| 035_add_device_playlist_assignment.sql | Additional schema | ✅ |

---
