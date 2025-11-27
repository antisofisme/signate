# Playlist Service - File Inventory

## Complete File Listing

### 1. DATABASE MIGRATION FILES
```
/mnt/g/khoirul/signate/backend-python/migrations/
├── 005_create_playlists_tables.sql          # Initial schema (playlists, playlist_contents, playlist_assignments)
├── 029_add_tag_playlist_assignment.sql      # Tag support (priority, assigned_playlist_id)
├── 030_add_device_playlist_assignment.sql   # Device assignment (assigned_playlist_id)
├── 031_add_playlist_flags.sql               # is_default, is_pms_template flags
└── 035_add_device_playlist_assignment.sql   # Additional schema
```

### 2. MODELS & DATABASE LAYER
```
/mnt/g/khoirul/signate/backend-python/services/playlist/repositories/
├── models.py                                # SQLAlchemy models (PlaylistModel, PlaylistContentModel, PlaylistAssignmentModel)
└── playlist_repo.py                         # Repository implementation with org filtering and cache invalidation
```

### 3. DOMAIN LAYER
```
/mnt/g/khoirul/signate/backend-python/services/playlist/domain/
├── playlist.py                              # Domain entities (Playlist, PlaylistContent, PlaylistAssignment)
├── interfaces.py                            # Repository interface (IPlaylistRepository)
└── content_resolver.py                      # Content resolution engine (schedule/direct/tag/PMS/default)
```

### 4. USE CASES (Business Logic)
```
/mnt/g/khoirul/signate/backend-python/services/playlist/use_cases/
├── create_playlist.py                       # CreatePlaylistUseCase (with quota check)
├── list_playlists.py                        # ListPlaylistsUseCase
├── get_playlist.py                          # GetPlaylistUseCase
├── update_playlist.py                       # UpdatePlaylistUseCase
├── delete_playlist.py                       # DeletePlaylistUseCase
├── manage_playlist_content.py               # AddContentToPlaylistUseCase, GetPlaylistContentUseCase, RemoveContentFromPlaylistUseCase, ReorderPlaylistContentUseCase
└── manage_playlist_assignments.py           # GetPlaylistAssignmentsUseCase, AssignPlaylistToDevicesUseCase, AssignPlaylistToTagsUseCase, UnassignPlaylistFromDevicesUseCase, UnassignPlaylistFromTagsUseCase
```

### 5. API & ROUTES
```
/mnt/g/khoirul/signate/backend-python/services/playlist/
├── routes.py                                # Admin API endpoints (auth required, audit logged)
│                                            # - CRUD: create, list, get, update, delete playlists
│                                            # - Content: add, list, remove, reorder
│                                            # - Assignments: get, assign/unassign devices/tags
│                                            # - Resolution: resolve content for device
└── client_routes.py                         # Client API endpoints (public, no auth)
                                            # - get_playlist_for_device (for player/viewer)
```

### 6. DATA TRANSFER OBJECTS
```
/mnt/g/khoirul/signate/backend-python/services/playlist/
└── dtos.py                                  # Request/Response models
                                            # - PlaylistCreateRequest, PlaylistUpdateRequest
                                            # - AddContentRequest, ReorderContentRequest
                                            # - AssignDevicesRequest, AssignTagsRequest
                                            # - PlaylistResponse, PlaylistListResponse
                                            # - PlaylistContentItemResponse, PlaylistContentListResponse
                                            # - BulkOperationResponse, PlaylistAssignmentsResponse
```

### 7. INITIALIZATION
```
/mnt/g/khoirul/signate/backend-python/services/playlist/
├── __init__.py                              # Package initialization
├── use_cases/__init__.py
├── repositories/__init__.py
└── domain/__init__.py
```

---

## File Count Summary

| Category | Count | Total Lines |
|----------|-------|-------------|
| Migrations | 5 | ~200 lines |
| Models | 1 | ~94 lines |
| Repositories | 1 | ~722 lines |
| Domain Entities | 2 | ~241 lines (playlist.py + interfaces.py) |
| Content Resolver | 1 | ~350+ lines |
| Use Cases | 8 | ~250 lines |
| Routes | 2 | ~756 lines (routes.py + client_routes.py) |
| DTOs | 1 | ~143 lines |
| Init Files | 4 | Minimal |
| **TOTAL** | **25** | **~3,000+ lines** |

---

## Key File Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                       API ROUTES                             │
│  routes.py (admin)      │    client_routes.py (public)       │
└──────────────┬──────────┴────────────────┬────────────────────┘
               │                          │
               ├─ get_current_user (auth) └─ No auth
               ├─ AuditLogger
               └─ FastAPI DI
                   │
        ┌──────────┴──────────┐
        │   USE CASES (8)      │
        │  - CRUD (5)          │
        │  - Content (4)       │
        │  - Assignments (5)   │
        └──────────┬───────────┘
                   │
        ┌──────────┴──────────┐
        │   REPOSITORY (1)     │
        │ PlaylistRepository   │
        │ - Org filtering      │
        │ - Cache invalidation │
        └──────────┬───────────┘
                   │
        ┌──────────┴──────────┐
        │  MODELS (1)          │
        │ - PlaylistModel      │
        │ - PlaylistContentModel│
        │ - PlaylistAssignmentModel
        └──────────┬───────────┘
                   │
        ┌──────────┴──────────┐
        │  DATABASE (5)        │
        │ - playlists          │
        │ - playlist_contents  │
        │ - playlist_assignments
        │ - tags (with assignment)
        │ - devices (with assignment)
        └──────────────────────┘
```

---

## Critical Files by Concern

### Multi-Tenancy & Security
- `repositories/playlist_repo.py` - organization_id filtering on every query
- `routes.py` - current_user.organization_id enforced in all use cases
- `client_routes.py` - multi-tenancy check for device ownership

### Cache Invalidation (P0-7 Critical)
- `repositories/playlist_repo.py` - `_invalidate_content_resolver_cache()` method
- Called on: create, update, delete, add_content, remove_content, reorder, assign/unassign

### Audit Logging
- `routes.py` - Every mutation endpoint calls `audit_logger.log_action()`
- Actions: playlist.create, .update, .delete, .add_content, .remove_content, .reorder_content, .assign_devices, .assign_tags, .unassign_devices, .unassign_tags

### Ordering & Duration
- `repositories/models.py` - PlaylistContentModel.order_index and .duration fields
- `repositories/playlist_repo.py` - reorder_playlist_contents() and calculate_playlist_stats()
- `domain/playlist.py` - PlaylistContent.update_order() and .update_duration()

### Content Resolution
- `domain/content_resolver.py` - ContentResolver class with 5-level priority resolution
- `routes.py` - GET /resolve/{device_id} endpoint
- `client_routes.py` - get_playlist_for_device() endpoint

---

## Code Quality Metrics

| Metric | Value |
|--------|-------|
| Total Lines | ~3,000+ |
| Main Files | 15 |
| Fully Implemented | ✅ Yes |
| Audit Logging | ✅ Yes (10 actions) |
| Cache Invalidation | ✅ Yes (P0-7 critical fix) |
| Multi-Tenancy | ✅ Yes (org_id always filtered) |
| RBAC Ready | ✅ Yes (via get_current_user) |
| Error Handling | ✅ Yes (400, 403, 404, 500) |
| Bulk Operations | ✅ Yes (with feedback) |
| Soft Delete Support | ✅ Yes (deleted_at field) |
| Quota Enforcement | ✅ Yes (P0-9 critical fix) |

---

## Integration Points

### External Service Dependencies
1. **Authentication** - `shared.auth.get_current_user`
2. **Database** - `shared.database.get_db` (PostgreSQL)
3. **Cache** - `shared.cache` (Redis, likely)
4. **Audit** - `services.audit.repositories.audit_log_repo.AuditLogRepository`
5. **Content** - `services.content.repositories.models.ContentModel`
6. **Device** - `services.device.repositories.models.DeviceModel`
7. **Tags** - `services.tag.repositories.models.TagModel`
8. **Organization** - `services.organization.domain.quota_service.OrganizationQuotaService`
9. **Schedule** - `services.schedule.repositories.schedule_repo.ScheduleRepository` (for content resolution)
10. **PMS** - `services.pms.repositories.pms_repo.PMSRepository` (for hotel integration, optional)

---

## API Endpoint Summary

### Admin Endpoints (17 total)
**Playlist CRUD (5)**
- POST `/api/v1/playlists` - Create
- GET `/api/v1/playlists` - List
- GET `/api/v1/playlists/{id}` - Get
- PATCH `/api/v1/playlists/{id}` - Update
- DELETE `/api/v1/playlists/{id}` - Delete

**Content Management (4)**
- GET `/api/v1/playlists/{id}/content` - List content
- POST `/api/v1/playlists/{id}/content` - Add content
- DELETE `/api/v1/playlists/{id}/content/{item_id}` - Remove content
- PATCH `/api/v1/playlists/{id}/reorder` - Reorder content

**Assignments (5)**
- GET `/api/v1/playlists/{id}/assignments` - Get assignments
- POST `/api/v1/playlists/{id}/assign/devices` - Assign to devices
- POST `/api/v1/playlists/{id}/assign/tags` - Assign to tags
- DELETE `/api/v1/playlists/{id}/assign/devices` - Unassign from devices
- DELETE `/api/v1/playlists/{id}/assign/tags` - Unassign from tags

**Content Resolution (2)**
- GET `/api/v1/playlists/resolve/{device_id}` - Resolve content for device (admin)
- GET `/api/v1/client/playlist` - Get content for device (public, no auth)

---

## Database Schema Overview

### Tables (3 main, 2 extended)
1. **playlists** (18 columns)
   - Core: id, name, description, is_active, priority, schedule
   - Multi-tenancy: organization_id
   - User tracking: created_by_id
   - Audit: created_at, updated_at, deleted_at
   - Extra: is_default, is_pms_template, background_audio_id

2. **playlist_contents** (7 columns)
   - Junction: playlist_id, content_id
   - Ordering: order_index
   - Duration: duration (override)
   - Control: is_muted
   - Audit: created_at

3. **playlist_assignments** (5 columns)
   - Polymorphic: playlist_id, device_id (nullable), tag_id (nullable)
   - Audit: created_at
   - Constraint: Exactly one of device_id or tag_id

4. **devices** (extended)
   - Added column: assigned_playlist_id (FK to playlists)

5. **tags** (extended)
   - Added columns: priority, assigned_playlist_id (FK to playlists)

### Constraints
- Primary keys on all tables
- Foreign keys with CASCADE delete for data integrity
- CHECK constraint ensuring device_id XOR tag_id in assignments
- UNIQUE constraints preventing duplicates
- Composite UNIQUE (organization_id, name, deleted_at) on playlists

### Indexes
- organization_id (critical for multi-tenancy)
- created_by_id, is_active, deleted_at
- Composite (playlist_id, order_index) for ordering

---
