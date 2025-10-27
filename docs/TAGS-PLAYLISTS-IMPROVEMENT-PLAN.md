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
Tags.jsx (Main Page) ✅ Enhanced with search
  ├─ TagFormModal.jsx ✅ (Create/Edit)
  ├─ AssignTagModal.jsx ✅ (Assign devices to tag)
  └─ TagDevicesModal.jsx ✅ DONE - View & manage devices in tag
```

### Playlists Page Structure
```
Playlists.jsx (Main Page) ✅ Fully wired
  ├─ PlaylistFormModal.jsx ✅ DONE - Create/Edit playlist
  ├─ PlaylistContentModal.jsx ✅ DONE - Manage content in playlist
  │   ├─ Content list with drag & drop ✅
  │   ├─ Add content button → ContentSelectorModal ✅
  │   └─ Duration editor per content ✅
  ├─ ContentSelectorModal.jsx ✅ DONE - Browse and select content
  ├─ PlaylistAssignmentModal.jsx ✅ DONE - Assign to devices/tags
  └─ PlaylistPreviewModal.jsx ❌ TODO - Preview playlist (optional)
```

---

## 🎯 Implementation Plan

### Phase 1: Playlists Core Functionality (Priority: 🔴 HIGH)

#### Task 1.1: Create PlaylistFormModal ✅
**File**: `web-admin/src/components/playlists/modals/PlaylistFormModal.jsx`
**Status**: ✅ DONE
**Features**:
- Name, description fields
- Active/Inactive toggle
- Basic schedule (start time, end time)
- Day of week selection
- Submit & Cancel buttons

#### Task 1.2: Create PlaylistContentModal ✅
**File**: `web-admin/src/components/playlists/modals/PlaylistContentModal.jsx`
**Status**: ✅ DONE
**Features**:
- List current playlist content
- Add content button (opens ContentSelectorModal)
- Remove content button
- Drag & drop reordering with HTML5 native API
- Duration editor per item
- Save order & durations

#### Task 1.3: Create ContentSelectorModal (for Playlists) ✅
**File**: `web-admin/src/components/playlists/modals/ContentSelectorModal.jsx`
**Status**: ✅ DONE
**Features**:
- Browse all available content
- Search & filter content by name and type
- Select multiple content with visual feedback
- Add selected to playlist with duplicate prevention

#### Task 1.4: Create PlaylistAssignmentModal ✅
**File**: `web-admin/src/components/playlists/modals/PlaylistAssignmentModal.jsx`
**Status**: ✅ DONE
**Features**:
- Tab 1: Assign to Devices
  - Device list with assign/remove buttons
  - Device status indicators
  - Current assignments highlighted
- Tab 2: Assign to Tags
  - Tag list with assign/remove buttons
  - Current assignments highlighted
- Real-time query updates after mutations

#### Task 1.5: Update Playlists.jsx ✅
**File**: `web-admin/src/pages/Playlists.jsx`
**Status**: ✅ DONE
**Changes**:
- Imported all modal components
- Wired up all modals with proper state management
- Added "Content" button for managing playlist content
- Added "Assign" button for device/tag assignment
- Improved button layout to 2-row format
- Added API endpoints for playlist assignments

---

### Phase 2: Tags Enhancement (Priority: 🟡 MEDIUM)

#### Task 2.1: Create TagDevicesModal ✅
**File**: `web-admin/src/components/tags/modals/TagDevicesModal.jsx`
**Status**: ✅ DONE
**Features**:
- List devices in tag with status indicators (online/offline)
- Device information display (name, type, IP, status)
- Remove device from tag with confirmation
- Add more devices button (opens AssignTagModal)
- Empty state with call-to-action
- Loading states and error handling

#### Task 2.2: Enhance Tags.jsx ✅
**File**: `web-admin/src/pages/Tags.jsx`
**Status**: ✅ DONE
**Features**:
- Added "View Devices" button on tag card
- Show device list in TagDevicesModal
- Added search/filter for tags (searches name and description)
- Real-time filtering with useMemo optimization
- Improved button layout to 2-row format
- Empty state for search results with clear button

#### Task 2.3: Tag Statistics Dashboard ✅
**File**: `web-admin/src/components/tags/TagStatsCard.jsx`
**Status**: ✅ DONE
**Features**:
- Device online/offline ratio with visual progress bar
- Real-time statistics from device data
- Content count through tag (placeholder - requires backend)
- Playlist count using tag (placeholder - requires backend)
- TagStatsModal wrapper for displaying statistics
- Stats button added to each tag card

---

### Phase 3: Advanced Features (Priority: 🟢 LOW)

#### Task 3.1: Playlist Preview Player ✅
**File**: `web-admin/src/components/playlists/modals/PlaylistPreviewModal.jsx` + Enhanced `Playlists.jsx`
**Status**: ✅ DONE
**Features**:
- Created PlaylistPreviewModal component with interactive preview
- Visual display of current content item with styled background
- Play/Pause/Next/Previous playback controls
- Auto-advance simulation with progress bar
- Clickable playlist items list for navigation
- Duration formatting and display
- Content type icons (video, image, html)
- Playing indicator with animated bars
- Info boxes with helpful instructions
- Preview button added to playlist cards (4-row layout)
- Modal integrated with proper state management

#### Task 3.2: Playlist Duplication ✅
**File**: `web-admin/src/components/playlists/modals/DuplicatePlaylistModal.jsx` + Enhanced `Playlists.jsx`
**Status**: ✅ DONE
**Features**:
- Created DuplicatePlaylistModal component
- Pre-fills name with "Copy of [Original Name]"
- User can edit name and description before duplicating
- Duplicates playlist structure and content
- Preserves schedule settings
- Does NOT copy device/tag assignments (starts as inactive)
- Duplicate button added to playlist cards
- Modal integrated with proper state management

#### Task 3.3: Advanced Scheduling ✅
**File**: Enhanced `PlaylistFormModal.jsx`
**Status**: ✅ DONE
**Features**:
- Priority field (1-10) for handling overlapping playlists
- Date range support (start_date & end_date) for limiting playlist duration
- Validation for date range consistency
- Clear UI with helpful hints and placeholders
- Backward compatible with existing playlists

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

✅ NEW ADDED:
- playlistsAPI.assignToDevices(id, data)
- playlistsAPI.assignToTags(id, data)
- playlistsAPI.getAssignments(id)
- playlistsAPI.unassignFromDevices(id, data)
- playlistsAPI.unassignFromTags(id, data)
```

---

## 📊 Progress Tracking

### Overall Progress: 100% 🎉

| Phase | Tasks | Completed | In Progress | TODO | Progress |
|-------|-------|-----------|-------------|------|----------|
| **Phase 1: Playlists Core** | 5 | 5 | 0 | 0 | 100% ✅ |
| **Phase 2: Tags Enhancement** | 3 | 3 | 0 | 0 | 100% ✅ |
| **Phase 3: Advanced Features** | 3 | 3 | 0 | 0 | 100% ✅ |
| **TOTAL** | **11** | **11** | **0** | **0** | **100% 🎉** |

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

### Completed ✅
1. ✅ Create this plan document
2. ✅ Create folder structure: `web-admin/src/components/playlists/modals/`
3. ✅ Implement PlaylistFormModal
4. ✅ Implement PlaylistContentModal with drag & drop
5. ✅ Implement ContentSelectorModal
6. ✅ Implement PlaylistAssignmentModal
7. ✅ Wire up all modals in Playlists.jsx
8. ✅ Add new API endpoints for playlist assignments
9. ✅ Implement TagDevicesModal
10. ✅ Enhance Tags.jsx with search and View Devices
11. ✅ Implement Tag Statistics Dashboard
12. ✅ Implement Playlist Duplication feature
13. ✅ Implement Playlist Preview Player
14. ✅ Implement Advanced Scheduling

### 🎉 ALL TASKS COMPLETED! 🎉
All planned features have been successfully implemented.

---

## 📝 Notes

- Modals use React Portal for better UX
- Drag & drop using `react-beautiful-dnd` or similar library
- Schedule validation (start time < end time)
- Prevent playlist overlap conflicts (show warning)
- Auto-save drafts for better UX (optional)

---

**Last Updated**: 2025-01-26
**Version**: 2.0 🎉
**Status**: Phase 1 Complete ✅ | Phase 2 Complete ✅ | Phase 3 Complete ✅ | **Overall: 100% 🎉**
