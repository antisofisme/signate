# Playlist Service - Quick Reference Guide

## Overview

**Service**: Playlist Management System  
**Location**: `/mnt/g/khoirul/signate/backend-python/services/playlist/`  
**Framework**: FastAPI + SQLAlchemy  
**Total Code**: ~3,000+ lines across 25 files  

---

## Key Findings

### 1. Multi-Tenancy (organization_id)

**Implementation**: ALWAYS filtered on every database query

```python
# Pattern used consistently across repo
def find_by_id(self, playlist_id: int, organization_id: int):
    return self.db.query(PlaylistModel).filter(
        and_(
            PlaylistModel.id == playlist_id,
            PlaylistModel.organization_id == organization_id  # ✅ CRITICAL
        )
    ).first()
```

**Key Points**:
- Every read operation includes org_id filter
- Every write operation validates org ownership
- User context extracted from `current_user.organization_id` (FastAPI)
- Multi-tenant isolation is enforced at repository level

---

### 2. User Context Tracking (created_by_id)

**Database Field**: `created_by_id` in `playlists` table

```python
# Creation captures user
playlist = Playlist(
    ...,
    created_by_id=current_user.id  # ✅ Tracked
)

# In model
class PlaylistModel(Base):
    created_by_id = Column(Integer, ForeignKey("users.id"))
```

**Tracked In**:
- Playlist creation (created_by_id)
- Audit logs (user_id)
- Response DTOs (created_by field)

**NOT tracked**:
- Content additions (no individual update tracking)
- Assignments (no individual update tracking)
- Use `audit_logs` table for detailed change history

---

### 3. RBAC Permissions (get_current_user)

**Implementation**: FastAPI middleware dependency

```python
from shared.auth import get_current_user, CurrentUser

@router.post("")
def create_playlist(
    request_body: PlaylistCreateRequest,
    current_user: dict = Depends(get_current_user),  # ✅ Auth required
    ...
):
    # current_user has: id, organization_id, role
```

**Security Pattern**:
- All admin endpoints require authentication
- User role comes from `current_user.role`
- Organization isolation enforced via `current_user.organization_id`
- Client endpoints (players) have NO authentication required

**RBAC NOT explicitly implemented**:
- Playlist service does NOT check `current_user.role`
- All authenticated users can create/edit playlists
- RBAC should be added at middleware level if needed
- Recommended: Require CONTENT_MANAGER or ADMIN role for mutations

---

### 4. Audit Logging (audit_logger)

**Implementation**: Every mutation endpoint logs action

```python
@router.post("")
def create_playlist(
    ...,
    audit_logger: AuditLogger = Depends(get_audit_logger)
):
    playlist = use_case.execute(...)
    
    # ✅ Always log
    audit_logger.log_action(
        user_id=current_user.id,
        action="playlist.create",       # Action type
        resource_type="playlist",       # Resource
        resource_id=playlist.id,        # Which resource
        details={"name": ...},          # What changed
        organization_id=current_user.organization_id
    )
```

**Logged Actions** (10 total):
1. `playlist.create` - Create playlist
2. `playlist.update` - Update details
3. `playlist.delete` - Delete playlist
4. `playlist.add_content` - Add content items
5. `playlist.remove_content` - Remove content
6. `playlist.reorder_content` - Reorder items
7. `playlist.assign_devices` - Assign to devices
8. `playlist.assign_tags` - Assign to tags
9. `playlist.unassign_devices` - Unassign from devices
10. `playlist.unassign_tags` - Unassign from tags

**Details Logged**: Varies by action (name, added count, removed count, etc.)

---

### 5. Relationship with Content Items

**Three-Layer Relationship**:

```
Playlists (1) ──── PlaylistContents (Many) ──── Contents (1)
                   (junction table)
   id                 id                           id
   name              playlist_id                   title
                     content_id                    file_url
                     order_index                   duration
                     duration (override)           type
                     is_muted
```

**Key Features**:
- Content can be in MULTIPLE playlists
- Each inclusion has separate order_index
- Duration can be OVERRIDDEN per playlist
- Per-content mute flag (is_muted)
- Duplicate content prevented via UNIQUE(playlist_id, content_id)

**Database**:
- Foreign keys: CASCADE delete both sides
- Content removal from DB cascades to all playlists
- Adding to playlist: validates content belongs to org

---

### 6. Playlist Item Ordering

**Implementation**: order_index column in playlist_contents

```python
# Stored in DB (0-based)
class PlaylistContentModel(Base):
    order_index = Column(Integer, not null, default=0)

# Always retrieved ordered
def get_playlist_contents(...):
    return self.db.query(PlaylistContentModel)\
        .order_by(PlaylistContentModel.order_index).all()

# Reorder via bulk update
def reorder_playlist_contents(..., content_items: List[Dict]):
    # Input: [{"id": 1, "order_index": 0}, {"id": 2, "order_index": 1}, ...]
    for item_data in content_items:
        playlist_content.order_index = item_data["order_index"]
```

**Ordering Guarantees**:
- Always fetched with .order_by(order_index)
- Reorder accepts arbitrary indices (can have gaps)
- Statistics correctly sum durations (respects order)
- Player receives ordered items

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│  API ROUTES (routes.py + client_routes.py)         │
│  - Endpoint handlers                                 │
│  - Input validation (Pydantic DTOs)                 │
│  - DI: repositories, use cases, audit logger        │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│  USE CASES (business logic layer)                    │
│  - CreatePlaylistUseCase                             │
│  - ListPlaylistsUseCase                              │
│  - GetPlaylistUseCase                                │
│  - UpdatePlaylistUseCase                             │
│  - DeletePlaylistUseCase                             │
│  - AddContentToPlaylistUseCase                       │
│  - RemoveContentFromPlaylistUseCase                  │
│  - ReorderPlaylistContentUseCase                     │
│  - AssignPlaylistToDevicesUseCase                    │
│  - AssignPlaylistToTagsUseCase                       │
│  - And 5 more...                                     │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│  DOMAIN ENTITIES (pure Python objects)               │
│  - Playlist (validation, business logic)             │
│  - PlaylistContent (ordering, duration logic)        │
│  - PlaylistAssignment (device/tag polymorphism)      │
│  - IPlaylistRepository (interface)                   │
│  - ContentResolver (5-level priority resolution)     │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│  REPOSITORY (data access + cache invalidation)       │
│  - PlaylistRepository implements IPlaylistRepository │
│  - Organization isolation (org_id filtering)         │
│  - Cache invalidation on mutations (P0-7 critical)   │
│  - Bulk operations with feedback                     │
│  - Statistics calculation                            │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│  SQLALCHEMY MODELS (ORM mappings)                    │
│  - PlaylistModel                                     │
│  - PlaylistContentModel                              │
│  - PlaylistAssignmentModel                           │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────────┐
│  DATABASE (PostgreSQL)                               │
│  - playlists (18 columns)                            │
│  - playlist_contents (7 columns)                     │
│  - playlist_assignments (5 columns)                  │
│  - Extended: devices, tags                           │
└──────────────────────────────────────────────────────┘
```

---

## Critical Implementations

### Cache Invalidation (P0-7 Fix)

**File**: `repositories/playlist_repo.py`  
**Method**: `_invalidate_content_resolver_cache()`

```python
def _invalidate_content_resolver_cache(self, playlist_id: int, organization_id: int):
    """
    When playlist changes, clear cache for:
    1. All devices directly assigned to playlist
    2. All devices with tags assigned to playlist
    3. Organization pattern cache
    
    Without this, devices continue playing stale content!
    """
    # 1. Direct device cache
    for assignment in direct_device_assignments:
        cache.delete(f"content_resolution:{device_id}")
    
    # 2. Tag-based device cache
    for device_tag in devices_with_tags:
        cache.delete(f"content_resolution:{device_id}")
    
    # 3. Organization pattern
    cache.invalidate_pattern(f"content_resolution:org_{organization_id}:*")
```

**Called on**:
- Playlist creation (via update method call)
- Playlist update
- Playlist deletion
- Content added/removed/reordered
- Device assignment/unassignment
- Tag assignment/unassignment

---

### Content Resolution (5-Level Priority)

**File**: `domain/content_resolver.py`  
**Class**: `ContentResolver`

```python
def resolve_content_for_device(device_id) -> ContentResolution:
    """
    Priority order (highest to lowest):
    
    1. SCHEDULES (time-based)
       - Check for active schedules
       - Return highest priority
    
    2. DIRECT ASSIGNMENT
       - Check device.assigned_playlist_id
       - Return if active
    
    3. TAG-BASED ASSIGNMENT
       - Get device tags
       - Find highest priority tag playlist
    
    4. PMS CONTENT (Hotel rooms)
       - If device.room_number set
       - Fetch guest info from PMS
       - Use PMS template playlist
    
    5. DEFAULT PLAYLIST
       - Organization default
       - Or first active playlist
       - Fallback (lowest priority)
    
    Returns: ContentResolution with playlist + metadata
    Caches: 5-minute TTL on result
    """
```

---

### Quota Enforcement (P0-9 Fix)

**File**: `use_cases/create_playlist.py`

```python
def execute(...) -> Playlist:
    # 1. Check quota atomically
    quota_service.enforce_playlist_quota_atomic(organization_id)
    
    # 2. Create entity
    playlist = Playlist(...)
    
    # 3. Persist
    return repository.create(playlist)
```

**Prevents**: Organization from exceeding playlist limits

---

## Database Schema Quick View

### playlists Table
```
id (PK)
name (VARCHAR 255)
description (TEXT)
is_active (BOOL)
priority (INT)
schedule (JSONB)
is_default (BOOL)
is_pms_template (BOOL)
background_audio_id (FK)
organization_id (FK) ✅ Multi-tenancy
created_by_id (FK) ✅ User tracking
created_at (TIMESTAMP)
updated_at (TIMESTAMP)
deleted_at (TIMESTAMP) - Soft delete support
```

### playlist_contents Table
```
id (PK)
playlist_id (FK)
content_id (FK)
order_index (INT) ✅ Ordering
duration (INT) ✅ Override
is_muted (BOOL) ✅ Per-content control
created_at (TIMESTAMP)

UNIQUE (playlist_id, content_id)
INDEX (playlist_id, order_index)
```

### playlist_assignments Table
```
id (PK)
playlist_id (FK)
device_id (FK, nullable) ✅ Polymorphic
tag_id (FK, nullable) ✅ Polymorphic
created_at (TIMESTAMP)

CHECK ((device_id IS NOT NULL AND tag_id IS NULL) OR
       (device_id IS NULL AND tag_id IS NOT NULL))
UNIQUE (playlist_id, device_id)
UNIQUE (playlist_id, tag_id)
```

---

## File Locations (Absolute Paths)

### Core Implementation
- `/mnt/g/khoirul/signate/backend-python/services/playlist/repositories/models.py`
- `/mnt/g/khoirul/signate/backend-python/services/playlist/repositories/playlist_repo.py`
- `/mnt/g/khoirul/signate/backend-python/services/playlist/domain/playlist.py`
- `/mnt/g/khoirul/signate/backend-python/services/playlist/domain/interfaces.py`
- `/mnt/g/khoirul/signate/backend-python/services/playlist/domain/content_resolver.py`

### Routes
- `/mnt/g/khoirul/signate/backend-python/services/playlist/routes.py` (Admin)
- `/mnt/g/khoirul/signate/backend-python/services/playlist/client_routes.py` (Public)

### Use Cases
- `/mnt/g/khoirul/signate/backend-python/services/playlist/use_cases/create_playlist.py`
- `/mnt/g/khoirul/signate/backend-python/services/playlist/use_cases/list_playlists.py`
- `/mnt/g/khoirul/signate/backend-python/services/playlist/use_cases/manage_playlist_content.py`
- `/mnt/g/khoirul/signate/backend-python/services/playlist/use_cases/manage_playlist_assignments.py`

### DTOs
- `/mnt/g/khoirul/signate/backend-python/services/playlist/dtos.py`

### Migrations
- `/mnt/g/khoirul/signate/backend-python/migrations/005_create_playlists_tables.sql`
- `/mnt/g/khoirul/signate/backend-python/migrations/029_add_tag_playlist_assignment.sql`
- `/mnt/g/khoirul/signate/backend-python/migrations/030_add_device_playlist_assignment.sql`
- `/mnt/g/khoirul/signate/backend-python/migrations/031_add_playlist_flags.sql`

---

## Common Code Patterns

### 1. Creating a Playlist
```python
# Endpoint
@router.post("")
def create_playlist(request: PlaylistCreateRequest, current_user: dict = ...):
    use_case = CreatePlaylistUseCase(repository)
    playlist = use_case.execute(
        name=request.name,
        organization_id=current_user.organization_id,  # ✅
        created_by=current_user.id,  # ✅
        ...
    )
    audit_logger.log_action(...)  # ✅
    return success_response(data=playlist.to_dict())
```

### 2. Adding Content to Playlist
```python
result = use_case.add_content(
    playlist_id=1,
    content_ids=[10, 11, 12],
    organization_id=current_user.organization_id  # ✅
)
# Returns: {added: 3, skipped_missing: [], skipped_duplicate: []}
```

### 3. Resolving Content for Device
```python
resolution = resolver.resolve_content_for_device(device_id)
# Returns: ContentResolution with:
# - playlist_id, playlist_name
# - resolution_type (schedule/direct/tag/pms/default)
# - priority, content_items
# - Optional metadata (schedule_id, tag_id, pms_data)
```

---

## Testing Checklist

- [ ] Verify organization isolation (query device from different org = 404)
- [ ] Audit logs created for all mutations
- [ ] Cache invalidated when playlist changes
- [ ] Content ordering preserved (order_index)
- [ ] Bulk operations return correct feedback
- [ ] Quota enforcement prevents over-creation
- [ ] Content resolution respects priority order
- [ ] Public client endpoint accessible without auth
- [ ] Admin endpoints require auth
- [ ] Duration overrides work correctly
- [ ] Soft delete with deleted_at column
- [ ] Polymorphic assignments (device XOR tag)

---

## Summary

| Aspect | Status | Key File |
|--------|--------|----------|
| Models | ✅ Complete | models.py |
| DTOs | ✅ Complete | dtos.py |
| Repository | ✅ Complete | playlist_repo.py |
| Use Cases | ✅ Complete | manage_*.py |
| Routes | ✅ Complete | routes.py |
| Multi-Tenancy | ✅ Enforced | Every query |
| Audit Logging | ✅ Implemented | 10 actions |
| Cache | ✅ Critical P0-7 | _invalidate_cache() |
| Ordering | ✅ Via order_index | playlist_contents |
| Duration Override | ✅ Per-item | playlist_contents |
| Content Resolution | ✅ 5 priority levels | content_resolver.py |
| User Tracking | ✅ created_by_id | playlists table |
| RBAC Ready | ⚠️ Basic | Needs role checks |
| Soft Delete | ✅ deleted_at | playlists table |
| Quota | ✅ P0-9 fix | CreatePlaylistUseCase |

---
