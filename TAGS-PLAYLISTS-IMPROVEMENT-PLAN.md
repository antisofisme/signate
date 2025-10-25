# Tags & Playlists UI/UX Improvement Plan

## 📋 Current Status Review

### ✅ What's Already Working

#### Tags (web-admin/src/pages/Tags.jsx)
- ✅ Basic CRUD operations (Create, Read, Update, Delete)
- ✅ Grid layout with tag cards
- ✅ Color picker for tags
- ✅ Device count display
- ✅ TagFormModal - Create/Edit modal
- ✅ AssignTagModal - Assign devices to tags
- ✅ React Query integration
- ✅ Toast notifications

#### Playlists (web-admin/src/pages/Playlists.jsx)
- ✅ Basic CRUD structure
- ✅ Grid layout with playlist cards
- ✅ Content count & duration display
- ✅ Active/Inactive status
- ✅ React Query integration
- ⚠️ Modals commented out (not implemented yet)

---

## 🔍 Data Structure Requirements

### Tag Data Model
```json
{
  "id": 1,
  "tag_name": "Lobby",
  "description": "All lobby displays",
  "color": "#3B82F6",
  "device_count": 5,
  "created_at": "2025-01-01T00:00:00Z",
  "devices": [
    {"id": 1, "name": "TV Lobby 1"},
    {"id": 2, "name": "TV Lobby 2"}
  ]
}
```

### Playlist Data Model
```json
{
  "id": 1,
  "name": "Morning Show",
  "description": "Morning content rotation",
  "is_active": true,
  "content_count": 5,
  "total_duration": 180,
  "schedule": {
    "start_time": "07:00",
    "end_time": "10:00",
    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
  },
  "assigned_devices": [
    {"id": 1, "name": "TV Lobby 1"},
    {"id": 2, "name": "TV Lobby 2"}
  ],
  "assigned_tags": [
    {"id": 1, "tag_name": "Lobby"}
  ],
  "content_items": [
    {
      "id": 1,
      "content_id": 10,
      "content_name": "brand-video.mp4",
      "content_type": "video",
      "duration": 30,
      "order_index": 0
    },
    {
      "id": 2,
      "content_id": 11,
      "content_name": "promo-banner.jpg",
      "content_type": "image",
      "duration": 10,
      "order_index": 1
    }
  ]
}
```

---

## 🚨 Missing Features & Functionality Gaps

### Tags Page - Missing Features

#### 🔴 High Priority
1. **View Devices in Tag**
   - Show list of devices assigned to a tag
   - Quick device management within tag
   - Device status (online/offline) in tag view

2. **Bulk Tag Assignment**
   - Select multiple devices
   - Assign/unassign tags in bulk
   - Filter devices by various criteria

3. **Tag Statistics**
   - Content assigned through this tag
   - Playlists using this tag
   - Usage analytics

#### 🟡 Medium Priority
4. **Tag Filtering & Search**
   - Search tags by name
   - Filter by device count
   - Sort by various criteria

5. **Tag Hierarchy** (Optional)
   - Parent-child tag relationships
   - E.g., "Jakarta" → "Jakarta Lobby", "Jakarta Office"

### Playlists Page - Missing Features

#### 🔴 High Priority
1. **Playlist Content Management Modal**
   - Add content to playlist
   - Remove content from playlist
   - Reorder content (drag & drop)
   - Set individual content duration
   - Preview playlist

2. **Playlist Assignment Modal**
   - Assign playlist to devices
   - Assign playlist to tags (bulk)
   - View current assignments
   - Unassign functionality

3. **Playlist Scheduling**
   - Start time / End time
   - Day of week selection
   - Date range (optional)
   - Priority when multiple playlists overlap

#### 🟡 Medium Priority
4. **Playlist Preview Player**
   - Visual preview of playlist content
   - See content order and duration
   - Simulate playback

5. **Playlist Duplication**
   - Clone existing playlist
   - Quick way to create similar playlists

6. **Playlist Templates**
   - Save playlist as template
   - Create from template

#### 🟢 Low Priority
7. **Advanced Scheduling**
   - Multiple schedule slots per playlist
   - Holiday schedules
   - Exception dates

---

## 📐 Component Architecture

### Tags Page Structure
```
Tags.jsx (Main Page)
  ├─ TagFormModal.jsx ✅ (Create/Edit)
  ├─ AssignTagModal.jsx ✅ (Assign devices to tag)
  └─ TagDevicesModal.jsx ❌ NEW - View & manage devices in tag
```

### Playlists Page Structure
```
Playlists.jsx (Main Page)
  ├─ PlaylistFormModal.jsx ❌ NEW - Create/Edit playlist
  ├─ PlaylistContentModal.jsx ❌ NEW - Manage content in playlist
  │   ├─ Content list with drag & drop
  │   ├─ Add content button → ContentSelectorModal
  │   └─ Duration editor per content
  ├─ PlaylistAssignmentModal.jsx ❌ NEW - Assign to devices/tags
  └─ PlaylistPreviewModal.jsx ❌ NEW - Preview playlist (optional)
```

---

## 🎯 Implementation Plan

### Phase 1: Playlists Core Functionality (Priority: 🔴 HIGH)

#### Task 1.1: Create PlaylistFormModal
**File**: `web-admin/src/components/playlists/modals/PlaylistFormModal.jsx`
**Status**: ⬜ TODO
**Features**:
- Name, description fields
- Active/Inactive toggle
- Basic schedule (start time, end time)
- Day of week selection
- Submit & Cancel buttons

#### Task 1.2: Create PlaylistContentModal
**File**: `web-admin/src/components/playlists/modals/PlaylistContentModal.jsx`
**Status**: ⬜ TODO
**Features**:
- List current playlist content
- Add content button (opens ContentSelectorModal)
- Remove content button
- Drag & drop reordering
- Duration editor per item
- Save order & durations

#### Task 1.3: Create ContentSelectorModal (for Playlists)
**File**: `web-admin/src/components/playlists/modals/ContentSelectorModal.jsx`
**Status**: ⬜ TODO
**Features**:
- Browse all available content
- Search & filter content
- Select multiple content
- Add selected to playlist

#### Task 1.4: Create PlaylistAssignmentModal
**File**: `web-admin/src/components/playlists/modals/PlaylistAssignmentModal.jsx`
**Status**: ⬜ TODO
**Features**:
- Tab 1: Assign to Devices
  - Device list with checkboxes
  - Search devices
  - Current assignments highlighted
- Tab 2: Assign to Tags
  - Tag list with checkboxes
  - Current assignments highlighted
- Save assignments

#### Task 1.5: Update Playlists.jsx
**File**: `web-admin/src/pages/Playlists.jsx`
**Status**: ⬜ TODO
**Changes**:
- Uncomment modal integrations
- Wire up all modals
- Add "Manage Content" button
- Add "Assign to Devices/Tags" button

---

### Phase 2: Tags Enhancement (Priority: 🟡 MEDIUM)

#### Task 2.1: Create TagDevicesModal
**File**: `web-admin/src/components/tags/modals/TagDevicesModal.jsx`
**Status**: ⬜ TODO
**Features**:
- List devices in tag
- Device status (online/offline)
- Remove device from tag
- Add more devices

#### Task 2.2: Enhance Tags.jsx
**File**: `web-admin/src/pages/Tags.jsx`
**Status**: ⬜ TODO
**Features**:
- Add "View Devices" button on tag card
- Show device list in modal
- Add search/filter for tags

#### Task 2.3: Tag Statistics Dashboard
**File**: `web-admin/src/components/tags/TagStatsCard.jsx`
**Status**: ⬜ TODO
**Features**:
- Content count through tag
- Playlist count using tag
- Device online/offline ratio

---

### Phase 3: Advanced Features (Priority: 🟢 LOW)

#### Task 3.1: Playlist Preview Player
**File**: `web-admin/src/components/playlists/modals/PlaylistPreviewModal.jsx`
**Status**: ⬜ TODO
**Features**:
- Visual preview of content
- Simulate playback
- Show transitions

#### Task 3.2: Playlist Duplication
**File**: Enhance `Playlists.jsx`
**Status**: ⬜ TODO
**Features**:
- Duplicate button
- Clone playlist with content
- Edit name before saving

#### Task 3.3: Advanced Scheduling
**File**: Enhance `PlaylistFormModal.jsx`
**Status**: ⬜ TODO
**Features**:
- Multiple schedule slots
- Holiday schedules
- Date ranges

---

## 🔧 API Endpoints Required

### Tags API (Already exists in api.js)
```javascript
✅ tagsAPI.list()
✅ tagsAPI.create(data)
✅ tagsAPI.update(id, data)
✅ tagsAPI.delete(id)
✅ tagsAPI.assign(data)
✅ tagsAPI.unassign(data)
✅ tagsAPI.getDevices(id)
```

### Playlists API (Already exists in api.js)
```javascript
✅ playlistsAPI.list()
✅ playlistsAPI.create(data)
✅ playlistsAPI.update(id, data)
✅ playlistsAPI.delete(id)
✅ playlistsAPI.getContent(id)
✅ playlistsAPI.assignContent(id, data)
✅ playlistsAPI.removeContent(id, contentId)
✅ playlistsAPI.reorderContent(id, data)

❌ NEW NEEDED:
- playlistsAPI.assignToDevices(id, deviceIds)
- playlistsAPI.assignToTags(id, tagIds)
- playlistsAPI.getAssignments(id)
- playlistsAPI.unassignFromDevices(id, deviceIds)
- playlistsAPI.unassignFromTags(id, tagIds)
```

---

## 📊 Progress Tracking

### Overall Progress: 30%

| Phase | Tasks | Completed | In Progress | TODO | Progress |
|-------|-------|-----------|-------------|------|----------|
| **Phase 1: Playlists Core** | 5 | 0 | 0 | 5 | 0% |
| **Phase 2: Tags Enhancement** | 3 | 0 | 0 | 3 | 0% |
| **Phase 3: Advanced Features** | 3 | 0 | 0 | 3 | 0% |
| **TOTAL** | **11** | **0** | **0** | **11** | **0%** |

---

## 🎨 UI/UX Considerations

### Design Consistency
- Follow existing design patterns from Devices & Content pages
- Use same color scheme and component library
- Maintain consistent button styles and layouts

### User Flow
1. **Create Playlist** → Add Content → Assign to Devices/Tags
2. **Create Tag** → Assign Devices → Use tag for bulk content/playlist assignment
3. **Content** → Can be assigned directly OR via Playlist
4. **Devices** → Can receive content directly, via playlist, or via tag

### Performance
- Lazy load modals
- Pagination for large content lists
- Debounced search
- Optimistic UI updates

---

## 🚀 Next Steps

### Immediate Actions (Start with Phase 1)
1. ✅ Create this plan document
2. ⬜ Create folder structure: `web-admin/src/components/playlists/modals/`
3. ⬜ Implement PlaylistFormModal
4. ⬜ Implement PlaylistContentModal with drag & drop
5. ⬜ Implement ContentSelectorModal
6. ⬜ Implement PlaylistAssignmentModal
7. ⬜ Wire up all modals in Playlists.jsx
8. ⬜ Add new API endpoints if needed
9. ⬜ Testing & bug fixes
10. ⬜ Move to Phase 2 (Tags Enhancement)

---

## 📝 Notes

- Modals use React Portal for better UX
- Drag & drop using `react-beautiful-dnd` or similar library
- Schedule validation (start time < end time)
- Prevent playlist overlap conflicts (show warning)
- Auto-save drafts for better UX (optional)

---

**Last Updated**: 2025-01-25
**Version**: 1.0
**Status**: Ready for Implementation
