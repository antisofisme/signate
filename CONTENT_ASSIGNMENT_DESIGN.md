# Content Assignment System Design
**Digital Signage - Content Distribution & Preview System**

Last Updated: 2025-10-26
Status: Design Phase - Enhanced with Hotel-Specific Features
Version: 2.0 (Hotel Edition)

---

## Table of Contents
1. [Overview](#overview)
2. [Content Sources Hierarchy](#content-sources-hierarchy)
3. [Database Schema](#database-schema)
4. [Playlist Scheduling](#playlist-scheduling)
5. [Content Resolution Logic](#content-resolution-logic)
6. [Preview System](#preview-system)
7. [UI/UX Flow](#uiux-flow)
8. [API Design](#api-design)
9. [Implementation Roadmap](#implementation-roadmap)
10. [Hotel-Specific Features](#hotel-specific-features) ⭐ NEW
11. [External Data Integration](#external-data-integration) ⭐ NEW
12. [Guest Personalization System](#guest-personalization-system) ⭐ NEW
13. [Multi-Language Support](#multi-language-support) ⭐ NEW
14. [Security & Privacy](#security--privacy) ⭐ NEW
15. [Template System](#template-system) ⭐ NEW

---

## Overview

Devices can receive content from multiple sources with different priorities:

```
Priority (Highest to Lowest):
┌─────────────────────────────────────┐
│ 1. Direct Content Assignment        │ ← Highest (override all)
│    (Per-device manual)               │
├─────────────────────────────────────┤
│ 2. Playlist Assignment               │ ← Priority based on playlist.priority
│    (Per-device or per-tag)           │
├─────────────────────────────────────┤
│ 3. Tag-based Content                 │ ← Content assigned to tags
│    (Inherited from device tags)      │
├─────────────────────────────────────┤
│ 4. Widget Assignment (Future)        │ ← Widget overlays
│    (Per-device or global)            │
└─────────────────────────────────────┘
```

---

## Content Sources Hierarchy

### 1. Direct Content Assignment
- **Definition:** Content manually assigned to specific device
- **Priority:** HIGHEST (999)
- **Use Case:** Device-specific content (e.g., "This promo only on Lobby TV 1")
- **Table:** `content_assignments` with `device_id` set
- **Override:** Overrides ALL playlist and tag content

### 2. Playlist Assignment
- **Definition:** Playlist assigned to device or tag
- **Priority:** Based on `playlist.priority` (user-defined)
- **Use Case:** Rotating content groups (e.g., "Morning News" playlist)
- **Table:** `playlist_assignments`
- **Scheduling:** Can have time-based schedules (06:00-12:00)
- **Modes:**
  - INCLUSIVE (default): Add to rotation
  - EXCLUSIVE: Replace all other content during schedule

### 3. Tag-based Content
- **Definition:** Content assigned to tag, inherited by all devices with that tag
- **Priority:** Based on `tag.tag_priority`
- **Use Case:** Group content (e.g., "All Lobby devices show safety video")
- **Table:** `content_assignments` with `tag_id` set
- **Scalability:** Efficient for bulk assignment

### 4. Widget Assignment (Future Feature)
- **Definition:** Dynamic overlays (weather, clock, news ticker)
- **Priority:** N/A (overlays, not in sequence)
- **Use Case:** Real-time information display
- **Behavior:** Can be in playlist sequence OR overlay

---

## Database Schema

### Current Schema

#### `content_assignments` (Existing)
```sql
content_assignments:
├─ id SERIAL PRIMARY KEY
├─ content_id INT FK → content(id)
├─ device_id INT FK → devices(id) [NULLABLE]
├─ tag_id INT FK → tags(id) [NULLABLE]
├─ priority INT DEFAULT 0
├─ created_at TIMESTAMP
└─ CONSTRAINT: device_id OR tag_id (mutually exclusive)
```

### Proposed Schema Changes

#### 1. Enhance `content_assignments`
```sql
ALTER TABLE content_assignments ADD COLUMN:
├─ display_order INT DEFAULT 0           -- Order within same source group
├─ is_active BOOLEAN DEFAULT TRUE        -- Soft delete/disable
├─ start_date TIMESTAMP NULL             -- Scheduling start (future)
├─ end_date TIMESTAMP NULL               -- Scheduling end (future)
├─ notes TEXT NULL                       -- Admin notes
└─ updated_at TIMESTAMP DEFAULT NOW()
```

**Rationale:**
- `display_order`: Controls sequence within Direct or Tag assignments
- `priority`: Keep for backward compatibility, or rename to `assignment_priority`
- `is_active`: Temporary disable without deletion
- Scheduling fields: Future-proof for time-based content

#### 2. Enhance `tags`
```sql
ALTER TABLE tags ADD COLUMN:
└─ tag_priority INT DEFAULT 0            -- Priority among tags
```

**Rationale:**
- Control tag order: "Safety" tag before "Promotion" tag
- Affects playback order of tag-based content

#### 3. Enhance `playlists`
```sql
ALTER TABLE playlists ADD COLUMN:
├─ schedule_mode ENUM('inclusive', 'exclusive') DEFAULT 'inclusive'
├─ schedule_start TIME NULL              -- e.g., "06:00:00"
├─ schedule_end TIME NULL                -- e.g., "12:00:00"
├─ schedule_days VARCHAR(50) NULL        -- JSON: ["mon","tue","wed"]
└─ schedule_timezone VARCHAR(50) DEFAULT 'Asia/Jakarta'
```

**Rationale:**
- `schedule_mode`:
  - `inclusive`: Add to existing rotation
  - `exclusive`: Replace ALL other content during schedule
- Schedule fields: Time-based playlist activation

---

## Playlist Scheduling

### Schedule Modes

#### INCLUSIVE Mode (Default)
**Behavior:** Playlist content ADDS to existing rotation during schedule

```
Device: Lobby TV
├─ Playlist "Breakfast Promo" (INCLUSIVE, 06:00-10:00, Priority 10)
├─ Playlist "General Info" (INCLUSIVE, Always, Priority 5)
└─ Direct: "Welcome Banner"

08:00 (in schedule):
└─ Play: Breakfast Promo + General Info + Welcome Banner
   └─ All combined, ordered by priority

11:00 (out of schedule):
└─ Play: General Info + Welcome Banner
   └─ Breakfast Promo excluded
```

**Use Cases:**
- Promotional content during peak hours
- Seasonal greetings without removing base content
- Time-sensitive announcements

---

#### EXCLUSIVE Mode
**Behavior:** Playlist content REPLACES all other content during schedule

```
Device: Conference Room TV
├─ Playlist "Meeting Schedule" (EXCLUSIVE, 09:00-17:00, Priority 10)
└─ Playlist "After Hours" (INCLUSIVE, Always, Priority 5)

10:00 (in schedule):
└─ ONLY Meeting Schedule
   └─ After Hours content HIDDEN

18:00 (out of schedule):
└─ After Hours content
   └─ Meeting Schedule HIDDEN
```

**Use Cases:**
- Emergency announcements (fire drill)
- Event-specific content (conference, exhibition)
- Meeting room schedules

---

### Conflict Resolution

**If multiple EXCLUSIVE playlists overlap:**
```
Priority Order:
1. Highest priority EXCLUSIVE wins
2. If same priority → Oldest created_at wins
3. Other playlists excluded during that time
```

**Example:**
```
10:00-11:00:
├─ Playlist A (EXCLUSIVE, Priority 10)
└─ Playlist B (EXCLUSIVE, Priority 10)
Result: Playlist A wins (older created_at)
```

---

## Content Resolution Logic

### Playback Sequence Algorithm

```python
def resolve_device_content(device_id, current_time):
    """
    Resolve final playback sequence for a device
    Returns ordered list of content to play
    """
    final_sequence = []

    # Step 1: Check for EXCLUSIVE playlists active now
    exclusive_playlists = get_active_exclusive_playlists(device_id, current_time)

    if exclusive_playlists:
        # EXCLUSIVE mode: Return ONLY highest priority exclusive playlist
        highest_priority = max(exclusive_playlists, key=lambda p: (p.priority, -p.created_at))
        return get_playlist_content(highest_priority.id)

    # Step 2: No exclusive playlists, proceed with normal resolution

    # 2a. Direct Assignments (Highest Priority)
    direct_content = get_direct_assignments(device_id)
        .filter(is_active=True)
        .order_by('display_order')
    final_sequence.extend(direct_content)

    # 2b. Playlists (by priority, highest first)
    inclusive_playlists = get_active_inclusive_playlists(device_id, current_time)
        .order_by('-priority', 'created_at')

    for playlist in inclusive_playlists:
        playlist_content = get_playlist_content(playlist.id)
            .filter(is_active=True)
            .order_by('order')
        final_sequence.extend(playlist_content)

    # 2c. Tag-based Content (by tag priority)
    device_tags = get_device_tags(device_id).order_by('-tag_priority')

    for tag in device_tags:
        tag_content = get_tag_content(tag.id)
            .filter(is_active=True)
            .order_by('display_order')
        final_sequence.extend(tag_content)

    # Step 3: Get widgets (overlays, not in sequence)
    widgets = get_device_widgets(device_id)

    return {
        'content_sequence': final_sequence,
        'widgets': widgets,
        'total_duration': sum(c.duration for c in final_sequence),
        'mode': 'exclusive' if exclusive_playlists else 'inclusive'
    }
```

---

### Priority Handling

#### Multiple Playlists with Same Priority

**Decision:** SEQUENTIAL (all from first playlist, then all from second)

```
Device has:
├─ Playlist A (priority 10, 3 items)
├─ Playlist B (priority 10, 2 items)  ← Same priority!
└─ Playlist C (priority 5, 4 items)

Playback Order:
1. A-Item1
2. A-Item2
3. A-Item3
4. B-Item1  ← After A finishes
5. B-Item2
6. C-Item1
7. C-Item2
8. C-Item3
9. C-Item4
10. Loop back to #1
```

**Sub-sorting:** If same priority → order by `created_at ASC` (older first)

**Rationale:**
- Simplicity: Easy to understand and debug
- Predictability: Same order every time
- Control: Admin can set exact order via priority

---

#### Tag Content Order

**Decision:** By tag priority, then by display_order within tag

```
Device has tags:
├─ "Safety" (tag_priority=10, 3 content)
└─ "Promotion" (tag_priority=5, 2 content)

Playback:
1. All content from "Safety" (ordered by display_order)
2. Then all content from "Promotion" (ordered by display_order)
```

**Rationale:**
- Real-world: Safety before promotion
- Flexible: Can reorder tags without touching content
- Granular: Control order within each tag

---

## Preview System

### Preview Page Design

**Location:** Separate page `/devices/:id/preview` (opens in new tab)

**Rationale:**
- Full screen for better preview experience
- Dedicated page without distractions
- Shareable link
- Can keep device detail modal open in another tab

---

### Preview UI Mockup

```
┌─────────────────────────────────────────────────────────┐
│  🎬 Preview: Lobby TV 1                                 │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                         │
│  ⚡ Real-time preview of content playback              │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │                                                  │  │
│  │  📺 Video Player (1920x1080)                    │  │
│  │  ┌──────────────────────────────────────────┐  │  │
│  │  │                                          │  │  │
│  │  │        [Content Preview Here]            │  │  │
│  │  │                                          │  │  │
│  │  │  ☁️ 25°C          Current: Item 1/10    │  │  │
│  │  │                            🕐 14:30      │  │  │
│  │  └──────────────────────────────────────────┘  │  │
│  │                                                  │  │
│  │  Playing: Welcome Banner.jpg (00:03/00:10)      │  │
│  │  Source: Direct Assignment 🎯                   │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  🎬 Playback Sequence (Total: 1m 25s, ~42 loops/hr)   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                         │
│  1. 📹 Promo Video.mp4                  ▶️ [15s]      │
│     └─ Source: Direct Assignment 🎯                    │
│                                                         │
│  2. 🖼️ Welcome Banner.jpg               ▶️ [10s]      │
│     └─ Source: Direct Assignment 🎯                    │
│                                                         │
│  3. 📹 Morning News.mp4                 ▶️ [20s]      │
│     └─ Source: Playlist "Morning" (P:10) 📋           │
│                                                         │
│  4. 🖼️ Special Offer.jpg                ▶️ [10s]      │
│     └─ Source: Playlist "Morning" (P:10) 📋           │
│                                                         │
│  5. 📹 General Ad 1.mp4                 ▶️ [15s]      │
│     └─ Source: Playlist "General Ads" (P:5) 📋        │
│                                                         │
│  6. 📹 Lobby Announcement.mp4           ▶️ [15s]      │
│     └─ Source: Tag "Lobby" (TP:10) 🏷️                │
│                                                         │
│  [↻ Then loop back to #1]                             │
│                                                         │
│  ⚠️ Widgets (Overlays):                               │
│  • ☁️ Weather Widget (Bottom Left)                    │
│  • 🕐 Clock Widget (Top Right)                        │
│                                                         │
│  [⏮️ Prev] [⏸️ Pause] [⏭️ Next] [↻ Restart]        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### Content Source Badges

**Visual Indicators:**
- 🎯 **Direct Assignment** → Red badge (Priority: 999)
- 📋 **Playlist** → Blue badge (Priority: user-defined, shown)
- 🏷️ **Tag** → Purple badge (Tag Priority shown)
- 🧩 **Widget** → Green badge (Overlay)

---

## UI/UX Flow

### Content Assignment Methods

#### Method 1: Device → Content (Device-centric)
**Use Case:** "I want to configure this specific device"

```
Flow:
1. Devices Page → Click device row
2. Device Detail Modal opens
3. Click [Content] tab
4. Section: Direct Assignments
   └─ [+ Add Content] button
      └─ Opens content selector
         └─ Select content → Set order → Save
5. Section: Playlists (already assigned in Playlists tab)
6. Section: Tag-based (inherited, view-only)
```

**Advantages:**
- Contextual: See all device info in one place
- Comprehensive: See all content sources
- Quick setup for individual device

---

#### Method 2: Content → Devices (Content-centric)
**Use Case:** "I want this video to play on multiple devices"

```
Flow:
1. Content Page → Click content card
2. Content menu → [Assign to Devices]
3. Device selector modal:
   ├─ [Select Devices] tab
   │  └─ Checkboxes for devices → Set order → Save
   └─ [Select Tags] tab
      └─ Checkboxes for tags → Set order → Save
```

**Advantages:**
- Bulk operation: Assign to many devices at once
- Efficient: One content to many destinations
- Tag-based: Assign to tag for automatic distribution

---

#### Method 3: Tag → Content (Tag-centric)
**Use Case:** "All Lobby devices should show these videos"

```
Flow:
1. Tags Page → Click tag
2. Tag Detail Modal
3. Tab: [Assigned Content]
4. [+ Add Content] button
   └─ Content selector
      └─ Select multiple content → Set order → Save
```

**Advantages:**
- Centralized: Manage tag content in one place
- Scalable: One assignment affects all tagged devices
- Organized: See all content for a tag

---

### Preview Access

**Button Location:** Device Detail Modal header

```
Device Detail Modal:
┌─────────────────────────────────────┐
│ 📺 Lobby TV 1          [🎬 Preview] │  ← Opens in new tab
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ [Device Info] [Tags] [Content] ... │
└─────────────────────────────────────┘
```

**Alternate Access:**
- Device table row → Right-click → "Preview Content"
- Dashboard → Device card → [👁️ Preview] icon

---

## API Design

### Endpoint: Get Device Content Preview

```http
GET /api/devices/{device_id}/preview
```

**Query Parameters:**
- `simulate_time` (optional): Simulate specific time (for testing schedules)
  - Example: `?simulate_time=2025-10-26T08:00:00`

**Response:**
```json
{
  "device_id": 99,
  "device_name": "Lobby TV 1",
  "preview_generated_at": "2025-10-26T14:30:00Z",
  "current_mode": "inclusive",  // or "exclusive"
  "total_duration_seconds": 85,
  "loops_per_hour": 42,

  "content_sequence": [
    {
      "sequence_number": 1,
      "content_id": 5,
      "title": "Welcome Banner",
      "description": "Main lobby welcome screen",
      "content_type": "image",
      "duration": 10,
      "anthias_url": "http://192.168.5.12:8000/assets/5.jpg",
      "thumbnail_url": "http://192.168.5.12:8000/assets/5_thumb.jpg",

      "source": {
        "type": "direct",  // direct | playlist | tag
        "id": null,
        "name": "Direct Assignment",
        "priority": 999,
        "badge_color": "red",
        "badge_icon": "🎯"
      }
    },
    {
      "sequence_number": 2,
      "content_id": 12,
      "title": "Morning Promo Video",
      "description": "Breakfast special promotion",
      "content_type": "video",
      "duration": 15,
      "anthias_url": "http://192.168.5.12:8000/assets/12.mp4",
      "thumbnail_url": "http://192.168.5.12:8000/assets/12_thumb.jpg",

      "source": {
        "type": "playlist",
        "id": 3,
        "name": "Morning Playlist",
        "priority": 10,
        "badge_color": "blue",
        "badge_icon": "📋",
        "schedule": {
          "mode": "inclusive",
          "active": true,
          "start": "06:00:00",
          "end": "12:00:00",
          "days": ["mon", "tue", "wed", "thu", "fri"]
        }
      }
    },
    {
      "sequence_number": 3,
      "content_id": 8,
      "title": "Safety Guidelines",
      "description": "Emergency procedures",
      "content_type": "image",
      "duration": 15,
      "anthias_url": "http://192.168.5.12:8000/assets/8.jpg",
      "thumbnail_url": "http://192.168.5.12:8000/assets/8_thumb.jpg",

      "source": {
        "type": "tag",
        "id": 1,
        "name": "Lobby",
        "priority": 10,  // tag_priority
        "badge_color": "purple",
        "badge_icon": "🏷️"
      }
    }
  ],

  "widgets": [
    {
      "widget_id": 1,
      "widget_type": "weather",
      "position": "bottom-left",
      "is_overlay": true,
      "config": {
        "location": "Jakarta",
        "update_interval": 300
      }
    },
    {
      "widget_id": 2,
      "widget_type": "clock",
      "position": "top-right",
      "is_overlay": true,
      "config": {
        "format": "24h",
        "timezone": "Asia/Jakarta"
      }
    }
  ],

  "warnings": [
    {
      "type": "schedule_conflict",
      "severity": "warning",
      "message": "Playlist 'Morning' and 'Breakfast' both scheduled at 08:00-10:00",
      "details": {
        "playlist_ids": [3, 7],
        "time_range": "08:00-10:00"
      }
    },
    {
      "type": "no_content_source",
      "severity": "info",
      "message": "No direct content assignments",
      "recommendation": "Consider adding device-specific content"
    }
  ],

  "metadata": {
    "total_sources": 3,
    "source_breakdown": {
      "direct": 1,
      "playlist": 1,
      "tag": 1
    },
    "total_unique_content": 3,
    "average_content_duration": 13.33,
    "estimated_variety": "high"  // high | medium | low
  }
}
```

---

### Additional Endpoints

#### Assign Content to Device (Direct)
```http
POST /api/devices/{device_id}/content
Content-Type: application/json

{
  "content_id": 5,
  "display_order": 1,
  "is_active": true
}
```

#### Assign Content to Tag
```http
POST /api/tags/{tag_id}/content
Content-Type: application/json

{
  "content_id": 8,
  "display_order": 1,
  "is_active": true
}
```

#### Bulk Assign Content
```http
POST /api/content/{content_id}/assign
Content-Type: application/json

{
  "device_ids": [1, 2, 3],
  "tag_ids": [5, 6],
  "display_order": 1
}
```

---

## Implementation Roadmap

### Phase 0: Hotel Integration Foundation ⭐ NEW
**Estimated Time:** 6 hours
**Priority:** HIGH (Required for hotel deployment)

- [ ] Database schema for hotel features
  - [ ] Create `external_data_sources` table
  - [ ] Create `device_guest_mappings` table
  - [ ] Create `content_templates` table
  - [ ] Create `widget_data_sources` table (future)
  - [ ] Create `room_configurations` table
  - [ ] Enhance `devices` table (room_number, location_type, privacy_mode)
  - [ ] Enhance `content` table (is_template, language_code, content_group_id)
  - [ ] Create `widgets` table (future)

- [ ] PMS Integration framework
  - [ ] Create base `PMSIntegration` class
  - [ ] Implement Opera PMS adapter
  - [ ] Implement Mews PMS adapter
  - [ ] Create data mapping utilities
  - [ ] Setup webhook endpoints

- [ ] Security & Privacy foundation
  - [ ] Implement data encryption utilities
  - [ ] Create access control policies
  - [ ] Setup audit logging
  - [ ] Implement data retention cleanup job

- [ ] Testing
  - [ ] Test PMS mock integration
  - [ ] Test guest data sync
  - [ ] Test encryption/decryption
  - [ ] Test data cleanup

---

### Phase 1: Database Schema (PRIORITY)
**Estimated Time:** 2 hours

- [ ] Create migration for `content_assignments` enhancements
  - [ ] Add `display_order` column
  - [ ] Add `is_active` column
  - [ ] Add `start_date`, `end_date` columns
  - [ ] Add `notes` column
  - [ ] Add `updated_at` column

- [ ] Create migration for `tags` enhancements
  - [ ] Add `tag_priority` column
  - [ ] Set default values for existing tags

- [ ] Create migration for `playlists` enhancements
  - [ ] Add `schedule_mode` ENUM column
  - [ ] Add `schedule_start` TIME column
  - [ ] Add `schedule_end` TIME column
  - [ ] Add `schedule_days` VARCHAR column
  - [ ] Add `schedule_timezone` VARCHAR column

- [ ] Update SQLAlchemy models to match schema
- [ ] Test migrations on development database
- [ ] Deploy migrations to production

---

### Phase 2: Backend API - Preview Endpoint (PRIORITY)
**Estimated Time:** 4 hours

- [ ] Create preview service (`/backend/app/services/preview.py`)
  - [ ] Implement `resolve_device_content()` function
  - [ ] Implement EXCLUSIVE playlist logic
  - [ ] Implement INCLUSIVE playlist logic
  - [ ] Implement priority-based sorting
  - [ ] Implement tag priority sorting

- [ ] Create preview endpoint (`/api/devices/{id}/preview`)
  - [ ] Add route in devices API
  - [ ] Create response schema
  - [ ] Add warning/conflict detection
  - [ ] Add metadata generation

- [ ] Write unit tests
  - [ ] Test exclusive mode
  - [ ] Test inclusive mode
  - [ ] Test priority conflicts
  - [ ] Test empty content scenarios

- [ ] API documentation (auto-generated by FastAPI)

---

### Phase 3: Backend API - Assignment Endpoints
**Estimated Time:** 3 hours

- [ ] Device direct content assignment
  - [ ] POST `/api/devices/{id}/content`
  - [ ] DELETE `/api/devices/{id}/content/{content_id}`
  - [ ] GET `/api/devices/{id}/content` (list)

- [ ] Tag content assignment
  - [ ] POST `/api/tags/{id}/content`
  - [ ] DELETE `/api/tags/{id}/content/{content_id}`
  - [ ] GET `/api/tags/{id}/content` (list)

- [ ] Bulk assignment
  - [ ] POST `/api/content/{id}/assign`

- [ ] Update existing endpoints
  - [ ] Update device detail to include direct content
  - [ ] Update tag detail to include assigned content

---

### Phase 4: Frontend - Device Detail Modal Enhancement
**Estimated Time:** 4 hours

- [ ] Add [Content] tab to DeviceDetailModal
  - [ ] Section: Direct Assignments
    - [ ] [+ Add Content] button
    - [ ] Content selector modal
    - [ ] Display order input
    - [ ] Delete assignment button

  - [ ] Section: Playlists (link to existing tab)

  - [ ] Section: Tag-based Content (read-only view)
    - [ ] Show inherited content from tags
    - [ ] Group by tag
    - [ ] Show tag priority

- [ ] Add [🎬 Preview] button to modal header
  - [ ] Opens `/devices/:id/preview` in new tab

---

### Phase 5: Frontend - Preview Page
**Estimated Time:** 6 hours

- [ ] Create Preview page (`/src/pages/DevicePreview.jsx`)
  - [ ] Full-screen video/image player
  - [ ] Content sequence list
  - [ ] Source badges with colors
  - [ ] Playback controls (prev/next/pause)
  - [ ] Auto-advance to next content
  - [ ] Widget overlay simulation

- [ ] Create PreviewPlayer component
  - [ ] Video player with auto-advance
  - [ ] Image display with timer
  - [ ] Transition effects
  - [ ] Widget overlays

- [ ] Create SequenceList component
  - [ ] Scrollable content list
  - [ ] Current item highlight
  - [ ] Source badges
  - [ ] Duration display
  - [ ] Click to jump to item

- [ ] Add warning/alert display
  - [ ] Schedule conflicts
  - [ ] Missing content warnings
  - [ ] Recommendations

---

### Phase 6: Frontend - Content Assignment UI
**Estimated Time:** 5 hours

- [ ] Content Page enhancements
  - [ ] Add [Assign to Devices] button on content card
  - [ ] Device/Tag selector modal
  - [ ] Bulk assignment UI

- [ ] Tags Page enhancements
  - [ ] Add [Assigned Content] section to tag detail
  - [ ] Content assignment UI
  - [ ] Display order management

- [ ] Playlist scheduling UI
  - [ ] Add schedule mode selector (inclusive/exclusive)
  - [ ] Time picker for start/end
  - [ ] Day selector (weekdays)
  - [ ] Timezone selector

---

### Phase 7: Testing & Polish
**Estimated Time:** 3 hours

- [ ] End-to-end testing
  - [ ] Assign direct content
  - [ ] Assign tag content
  - [ ] Create scheduled playlist
  - [ ] Test exclusive mode
  - [ ] Test priority conflicts
  - [ ] Test preview accuracy

- [ ] UI/UX polish
  - [ ] Loading states
  - [ ] Error handling
  - [ ] Toast notifications
  - [ ] Responsive design

- [ ] Documentation
  - [ ] Update user guide
  - [ ] Add screenshots
  - [ ] Video tutorial (optional)

---

### Phase 8: Widget System (ENHANCED with Hotel Features)
**Estimated Time:** 8 hours (was TBD)

- [ ] Widget framework with external data
  - [ ] Base widget class
  - [ ] Data source integration
  - [ ] Overlay rendering
  - [ ] Refresh mechanism

- [ ] Hotel-specific widgets
  - [ ] Guest welcome widget
  - [ ] Weather widget (guest home city)
  - [ ] Room service status widget
  - [ ] Housekeeping dashboard widget

- [ ] Standard widgets
  - [ ] Clock widget
  - [ ] News ticker widget
  - [ ] Custom widget API

---

### Phase 9: Personalization System ⭐ NEW
**Estimated Time:** 10 hours
**Priority:** HIGH (Required for hotel deployment)

- [ ] Template content support
  - [ ] Variable substitution engine (Jinja2/Handlebars)
  - [ ] Dynamic asset generation (PIL/Canvas)
  - [ ] Language-based content selection
  - [ ] Fallback content handling

- [ ] Guest context resolution
  - [ ] Real-time guest mapping
  - [ ] Check-in/check-out event triggers
  - [ ] Preference-based content filtering
  - [ ] Tier-based content access

- [ ] Multi-language system
  - [ ] Content translation management
  - [ ] Auto-language selection
  - [ ] Fallback language handling
  - [ ] Widget localization

- [ ] Preview with personalization
  - [ ] Simulate guest context
  - [ ] Test different guest types (VIP, regular)
  - [ ] Variable preview mode
  - [ ] Multi-language preview

- [ ] PMS Integration implementation
  - [ ] Opera PMS live integration
  - [ ] Mews PMS live integration
  - [ ] Webhook handling
  - [ ] Data sync cron jobs

---

## Key Design Decisions Summary

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Tag Content** | Separate table (`content_assignments` with `tag_id`) | Granular control, can set different order per tag |
| **Scheduling Mode** | HYBRID (inclusive default, exclusive option) | Flexibility for both normal and emergency use cases |
| **Priority Conflicts** | SEQUENTIAL (all from high → all from low) | Simplicity, predictability, easy to debug |
| **Tag Order** | By `tag_priority`, then `display_order` within tag | Control tag importance, granular content order |
| **Preview Location** | Separate page `/devices/:id/preview` | Full screen, better UX, shareable link |
| **API Resolution** | Backend endpoint with complete logic | Single source of truth, consistent across clients |
| **UI Flow** | Bi-directional (device→content AND content→device) | Supports different workflows and use cases |

---

---

## 10. Hotel-Specific Features

### Overview

The digital signage system is enhanced with hotel-specific capabilities to support:
- **Guest Personalization**: Welcome messages, preferences, language
- **Room Management**: Device-to-room mapping, status tracking
- **PMS Integration**: Real-time data sync with Property Management Systems
- **Multi-language**: Auto-selection based on guest nationality
- **Staff Operations**: Housekeeping displays, maintenance alerts

### Hotel Use Case Example

```
Room 305 - Deluxe Suite
Guest: Mr. John Smith (USA, VIP Gold Member, Birthday: Today)
├─ Check-in: 2025-10-26 14:00
├─ Check-out: 2025-10-27 12:00
├─ Preferences: English, Vegetarian, No alcohol
├─ Special: Anniversary celebration
└─ Home City: New York

In-Room TV Should Display:
1. "Welcome Mr. John Smith! 🎂 Happy Birthday!"
2. Weather widget showing New York weather
3. Hotel facilities (English language)
4. Restaurant menu (filtered: vegetarian, no alcohol)
5. Anniversary dinner promotion
6. Flight status to JFK (auto-detected from checkout date)
7. Housekeeping: "Your room will be serviced at 10:00 AM"

Staff Tablet (Housekeeping) Should Display:
1. Room 305: Occupied, VIP Gold, Clean
2. Room 306: Checkout today, Priority cleaning
3. Room 307: Maintenance required (AC issue)
```

### Key Features

#### 1. **Device Location Types**
```sql
location_type in devices:
├─ guest_room    → In-room TV with guest personalization
├─ public_area   → Lobby, restaurant (general content)
├─ staff_area    → Back-office displays (operations data)
└─ meeting_room  → Conference rooms (event schedules)
```

#### 2. **Privacy Modes**
```sql
privacy_mode in devices:
├─ full          → Show guest name, preferences, billing
├─ limited       → Show welcome, no PII details
└─ none          → Generic content only
```

#### 3. **Guest Data Lifecycle**
```
1. Guest Checks In (PMS webhook)
   └→ Create device_guest_mapping
   └→ Fetch guest profile (name, nationality, preferences)
   └→ Update content to personalized

2. During Stay
   └→ Sync preferences changes
   └→ Update room service status
   └→ Track guest activities

3. Guest Checks Out
   └→ Set is_active = false
   └→ Reset device to default content
   └→ Schedule data deletion (7 days retention)
```

---

## 11. External Data Integration

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Web Admin UI                        │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              Backend API (FastAPI)                  │
│  ┌──────────────────────────────────────────────┐  │
│  │        Integration Layer                     │  │
│  │  ┌────────────┐  ┌────────────┐             │  │
│  │  │ PMS Adapter│  │ POS Adapter│  ...        │  │
│  │  └──────┬─────┘  └──────┬─────┘             │  │
│  └─────────┼────────────────┼───────────────────┘  │
└────────────┼────────────────┼──────────────────────┘
             │                │
      ┌──────▼─────┐   ┌─────▼──────┐
      │  Opera PMS │   │ Square POS │
      │    Cloud   │   │    API     │
      └────────────┘   └────────────┘
```

### Supported PMS Systems

#### 1. **Oracle Opera Cloud**
- API Type: REST + OAuth2
- Data Points: Guest profile, reservations, room status
- Webhook Support: Yes (check-in, check-out events)
- Real-time: < 5 seconds

#### 2. **Mews PMS**
- API Type: REST + API Key
- Data Points: Reservations, services, billing
- Webhook Support: Yes
- Real-time: < 3 seconds

#### 3. **Cloudbeds**
- API Type: REST + OAuth2
- Data Points: Bookings, guest data
- Webhook Support: Limited
- Polling: 30 seconds

#### 4. **Protel**
- API Type: SOAP/REST
- Data Points: Reservations, guest profiles
- Webhook Support: No (polling only)
- Polling: 60 seconds

### Data Synchronization

#### **Webhook-based (Preferred)**
```python
# Backend receives webhook from PMS
POST /api/webhooks/pms/checkin
{
  "event": "guest_checkin",
  "room_number": "305",
  "guest": {
    "id": "G12345",
    "name": "John Smith",
    "nationality": "US",
    "language": "en",
    "loyalty_tier": "gold"
  },
  "reservation": {
    "check_in": "2025-10-26T14:00:00Z",
    "check_out": "2025-10-27T12:00:00Z"
  }
}

# Backend processes:
1. Find device by room_number
2. Create/Update device_guest_mapping
3. Trigger content refresh for device
4. Send WebSocket update to viewer
```

#### **Polling-based (Fallback)**
```python
# Cron job runs every 30-60 seconds
async def sync_pms_data():
    for room in active_rooms:
        guest_data = await pms_adapter.get_room_guest(room.number)
        if guest_data:
            update_guest_mapping(room.device_id, guest_data)
        else:
            clear_guest_mapping(room.device_id)  # Checkout
```

### Caching Strategy

```python
# Redis cache layer
cache_keys = {
    'guest_profile:{guest_id}': 3600,      # 1 hour
    'room_status:{room_num}': 300,         # 5 minutes
    'pms_availability': 60,                # 1 minute
}

# Cache invalidation triggers
triggers = [
    'guest_checkin',    # Clear guest cache
    'guest_checkout',   # Clear guest + room cache
    'room_cleaned',     # Clear room status cache
]
```

---

## 12. Guest Personalization System

### Template Variables

#### **Available Variables**
```javascript
{
  // Guest Info
  guest_name: "John Smith",
  guest_first_name: "John",
  guest_last_name: "Smith",
  guest_title: "Mr.",
  guest_nationality: "US",
  guest_language: "en",
  guest_home_city: "New York",

  // Loyalty
  loyalty_tier: "gold",          // gold, silver, regular
  loyalty_points: 12500,
  loyalty_benefits: ["late_checkout", "free_breakfast"],

  // Reservation
  room_number: "305",
  room_type: "deluxe_suite",
  check_in_date: "2025-10-26",
  check_out_date: "2025-10-27",
  nights_count: 1,

  // Preferences
  dietary: ["vegetarian"],
  temperature_preference: "cool",  // cool, warm
  pillow_type: "soft",
  special_occasions: ["birthday", "anniversary"],

  // Dynamic
  current_charges: 250.00,
  minibar_items: [...],
  room_service_orders: [...]
}
```

### Template Syntax

#### **Simple Variable Substitution**
```html
<!-- Template content -->
<h1>Welcome {{guest_title}} {{guest_last_name}}!</h1>
<p>Room {{room_number}} • {{room_type}}</p>

<!-- Rendered for John Smith -->
<h1>Welcome Mr. Smith!</h1>
<p>Room 305 • Deluxe Suite</p>
```

#### **Conditional Display**
```html
{{#if loyalty_tier == "gold"}}
  <div class="vip-banner">
    🌟 VIP Gold Member - Enjoy complimentary late checkout!
  </div>
{{/if}}

{{#if special_occasions includes "birthday"}}
  <div class="birthday">
    🎂 Happy Birthday {{guest_first_name}}!
  </div>
{{/if}}
```

#### **Loops**
```html
<h3>Your Benefits:</h3>
<ul>
{{#each loyalty_benefits}}
  <li>{{benefit_name}}</li>
{{/each}}
</ul>
```

### Dynamic Asset Generation

For visual content with text overlays:

```python
from PIL import Image, ImageDraw, ImageFont

def generate_welcome_banner(template, guest_data):
    """
    Generate personalized welcome banner image
    """
    # Load template image
    img = Image.open(template.base_image_path)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype('arial.ttf', 72)

    # Render text with guest name
    welcome_text = f"Welcome {guest_data['guest_name']}!"
    draw.text((100, 200), welcome_text, font=font, fill=(255,255,255))

    # Add loyalty badge if VIP
    if guest_data['loyalty_tier'] == 'gold':
        badge = Image.open('assets/gold_badge.png')
        img.paste(badge, (800, 50))

    # Save to temp storage
    output_path = f"/tmp/welcome_{guest_data['guest_id']}.jpg"
    img.save(output_path)

    return output_path
```

### Tier-based Content Filtering

```python
def get_content_for_guest(device_id, guest_data):
    """
    Filter content based on guest loyalty tier
    """
    base_content = get_device_content(device_id)

    # Filter by tier
    if guest_data['loyalty_tier'] == 'gold':
        # Include VIP-only content
        vip_content = get_content_by_tag('vip_only')
        base_content = vip_content + base_content

    # Filter by dietary preferences
    if 'vegetarian' in guest_data.get('dietary', []):
        # Remove non-vegetarian menu promos
        base_content = [c for c in base_content
                       if 'meat' not in c.tags]

    return base_content
```

---

## 13. Multi-Language Support

### Content Translation Management

#### **Content Language Variants**
```sql
-- content table structure
{
  id: 1,
  content_group_id: 100,        -- Group translations
  language_code: "en",
  title: "Welcome to Paradise Hotel",
  anthias_url: "/assets/welcome_en.jpg",
  is_template: false
}

{
  id: 2,
  content_group_id: 100,        -- Same group
  language_code: "zh",
  title: "欢迎来到天堂酒店",
  anthias_url: "/assets/welcome_zh.jpg",
  is_template: false
}

{
  id: 3,
  content_group_id: 100,        -- Same group
  language_code: "ja",
  title: "パラダイスホテルへようこそ",
  anthias_url: "/assets/welcome_ja.jpg",
  is_template: false
}
```

#### **Language Selection Logic**
```python
def select_content_language(content_group, guest_language):
    """
    Select appropriate language variant
    """
    # 1. Try exact match
    exact_match = content_group.variants.filter(
        language_code=guest_language
    )
    if exact_match:
        return exact_match

    # 2. Try language family (zh-CN → zh)
    base_language = guest_language.split('-')[0]
    family_match = content_group.variants.filter(
        language_code__startswith=base_language
    )
    if family_match:
        return family_match[0]

    # 3. Fallback to English
    fallback = content_group.variants.filter(
        language_code='en'
    )
    if fallback:
        return fallback

    # 4. Return first available
    return content_group.variants[0]
```

### Supported Languages (Phase 1)

```python
LANGUAGES = {
    'en': 'English',
    'zh': 'Chinese (Simplified)',
    'ja': 'Japanese',
    'ko': 'Korean',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'ar': 'Arabic',
    'ru': 'Russian',
    'pt': 'Portuguese'
}

# Auto-detect from guest nationality
NATIONALITY_TO_LANGUAGE = {
    'US': 'en', 'GB': 'en', 'AU': 'en',
    'CN': 'zh', 'TW': 'zh', 'HK': 'zh',
    'JP': 'ja',
    'KR': 'ko',
    'ES': 'es', 'MX': 'es', 'AR': 'es',
    'FR': 'fr',
    'DE': 'de',
    'SA': 'ar', 'AE': 'ar',
    'RU': 'ru',
    'BR': 'pt', 'PT': 'pt'
}
```

### Widget Localization

```javascript
// Weather widget example
{
  "type": "weather",
  "translations": {
    "en": {
      "temperature": "Temperature",
      "humidity": "Humidity",
      "forecast": "Forecast"
    },
    "zh": {
      "temperature": "温度",
      "humidity": "湿度",
      "forecast": "预报"
    },
    "ja": {
      "temperature": "気温",
      "humidity": "湿度",
      "forecast": "予報"
    }
  },
  "current_language": "{{guest_language}}"
}
```

---

## 14. Security & Privacy

### GDPR & Privacy Compliance

#### **Data Classification**
```
Personal Data (PII):
├─ Level 1 (High Sensitive):
│  ├─ Full name
│  ├─ Passport number
│  ├─ Payment information
│  └─ Health data (dietary, medical needs)
│
├─ Level 2 (Medium Sensitive):
│  ├─ Email, phone
│  ├─ Nationality
│  ├─ Room number
│  └─ Billing details
│
└─ Level 3 (Low Sensitive):
   ├─ Language preference
   ├─ Temperature preference
   └─ Special occasions
```

#### **Encryption Standards**
```sql
-- Database encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt guest names
guest_name_encrypted = pgp_sym_encrypt(
    guest_name,
    :encryption_key,
    'cipher-algo=aes256'
);

-- Decrypt when needed
guest_name = pgp_sym_decrypt(
    guest_name_encrypted,
    :encryption_key
);
```

#### **Encryption in Application**
```python
from cryptography.fernet import Fernet
import os

class GuestDataEncryption:
    def __init__(self):
        # Key from environment or secrets manager
        self.key = os.getenv('GUEST_DATA_KEY').encode()
        self.cipher = Fernet(self.key)

    def encrypt_pii(self, data: str) -> bytes:
        """Encrypt personally identifiable information"""
        return self.cipher.encrypt(data.encode())

    def decrypt_pii(self, encrypted: bytes) -> str:
        """Decrypt PII for authorized use"""
        return self.cipher.decrypt(encrypted).decode()
```

### Access Control

#### **Role-Based Access Control (RBAC)**
```sql
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE,
    permissions JSONB
);

INSERT INTO roles (name, permissions) VALUES
('admin', '["read_all", "write_all", "delete_all"]'),
('manager', '["read_all", "write_content", "view_guest_data"]'),
('staff', '["read_room_status", "update_room_status"]'),
('viewer', '["read_public_data"]');

-- Policy enforcement
CREATE TABLE data_access_policies (
    id SERIAL PRIMARY KEY,
    role VARCHAR(50),
    resource_type VARCHAR(50),
    allowed_fields JSONB,
    denied_fields JSONB,
    conditions JSONB
);

-- Example: Staff can see room status but not guest names
INSERT INTO data_access_policies (role, resource_type, allowed_fields, denied_fields)
VALUES (
    'staff',
    'device_guest_mapping',
    '["room_number", "check_in_date", "check_out_date", "is_active"]',
    '["guest_name", "guest_nationality", "loyalty_tier", "preferences"]'
);
```

#### **Audit Logging**
```python
class AuditLog:
    @staticmethod
    async def log_access(user_id, action, resource_type, resource_id, guest_id=None):
        """
        Log all access to guest PII
        """
        await db.execute("""
            INSERT INTO data_access_logs
            (user_id, action, resource_type, resource_id, guest_id, ip_address, timestamp)
            VALUES ($1, $2, $3, $4, $5, $6, NOW())
        """, user_id, action, resource_type, resource_id, guest_id, request.client.host)

        # Alert if suspicious pattern
        recent_accesses = await db.fetch("""
            SELECT COUNT(*) FROM data_access_logs
            WHERE user_id = $1 AND timestamp > NOW() - INTERVAL '5 minutes'
        """, user_id)

        if recent_accesses[0]['count'] > 50:
            await send_security_alert(f"Suspicious activity: User {user_id}")

# Usage in API
@router.get("/api/guests/{guest_id}")
async def get_guest_data(guest_id: str, current_user: User):
    # Log access
    await AuditLog.log_access(
        user_id=current_user.id,
        action="read",
        resource_type="guest_data",
        resource_id=guest_id,
        guest_id=guest_id
    )

    # Check permissions
    if not current_user.has_permission("read_guest_data"):
        raise HTTPException(403, "Forbidden")

    # Return only allowed fields based on role
    guest_data = await get_guest(guest_id)
    return filter_by_permissions(guest_data, current_user.role)
```

### Data Retention & Deletion

#### **Automatic Cleanup**
```sql
-- Scheduled job (runs daily)
CREATE OR REPLACE FUNCTION cleanup_guest_data()
RETURNS void AS $$
BEGIN
    -- Soft delete guest mappings 7 days after checkout
    UPDATE device_guest_mappings
    SET
        guest_name = '[REDACTED]',
        guest_nationality = NULL,
        preferences = NULL,
        is_active = FALSE,
        deleted_at = NOW()
    WHERE
        check_out_date < NOW() - INTERVAL '7 days'
        AND deleted_at IS NULL;

    -- Hard delete after 90 days (compliance)
    DELETE FROM device_guest_mappings
    WHERE deleted_at < NOW() - INTERVAL '90 days';

    -- Cleanup audit logs older than retention policy
    DELETE FROM data_access_logs
    WHERE timestamp < NOW() - INTERVAL '2 years';
END;
$$ LANGUAGE plpgsql;

-- Schedule with pg_cron
SELECT cron.schedule('cleanup-guest-data', '0 2 * * *', 'SELECT cleanup_guest_data()');
```

#### **Right to be Forgotten (GDPR)**
```python
@router.delete("/api/guests/{guest_id}/forget")
async def forget_guest(guest_id: str, current_user: User):
    """
    Immediately delete all guest data (GDPR compliance)
    """
    if not current_user.has_permission("delete_guest_data"):
        raise HTTPException(403)

    # Log the deletion request
    await AuditLog.log_access(
        user_id=current_user.id,
        action="forget",
        resource_type="guest_data",
        resource_id=guest_id,
        guest_id=guest_id
    )

    # Delete from all tables
    await db.execute("""
        DELETE FROM device_guest_mappings WHERE guest_id = $1;
        DELETE FROM guest_preferences WHERE guest_id = $1;
        DELETE FROM cached_guest_data WHERE guest_id = $1;
    """, guest_id)

    # Clear from cache
    await redis.delete(f"guest:{guest_id}")

    return {"message": "Guest data deleted", "guest_id": guest_id}
```

---

## 15. Template System

### Template Engine

We use **Jinja2** for template rendering (Python side) and **Handlebars** for client-side rendering.

#### **Server-side Templates (Jinja2)**
```python
from jinja2 import Template

def render_content_template(content, guest_context):
    """
    Render content with guest variables
    """
    if not content.is_template:
        return content

    # Create Jinja2 template
    template = Template(content.title)
    rendered_title = template.render(**guest_context)

    # Clone content with rendered values
    rendered_content = content.copy()
    rendered_content.title = rendered_title

    # If template requires dynamic asset generation
    if content.template_variables:
        rendered_content.anthias_url = generate_dynamic_asset(
            content, guest_context
        )

    return rendered_content

# Example usage
guest_context = {
    'guest_name': 'John Smith',
    'guest_title': 'Mr.',
    'room_number': '305',
    'loyalty_tier': 'gold'
}

content = {
    'title': 'Welcome {{guest_title}} {{guest_name}} to Room {{room_number}}!',
    'is_template': True
}

rendered = render_content_template(content, guest_context)
# Result: "Welcome Mr. John Smith to Room 305!"
```

#### **Client-side Templates (Handlebars)**
```javascript
// viewer.js
import Handlebars from 'handlebars';

function renderWidget(widgetTemplate, guestData) {
  const template = Handlebars.compile(widgetTemplate);
  return template(guestData);
}

// Example widget template
const welcomeTemplate = `
  <div class="welcome-widget">
    <h1>Welcome {{guest_title}} {{guest_last_name}}!</h1>
    {{#if loyalty_tier}}
      <div class="loyalty-badge loyalty-{{loyalty_tier}}">
        {{loyalty_tier}} Member
      </div>
    {{/if}}
    {{#if special_occasions}}
      {{#each special_occasions}}
        <div class="occasion">🎉 {{this}}</div>
      {{/each}}
    {{/if}}
  </div>
`;

const rendered = renderWidget(welcomeTemplate, {
  guest_title: 'Mr.',
  guest_last_name: 'Smith',
  loyalty_tier: 'gold',
  special_occasions: ['Birthday', 'Anniversary']
});
```

### Dynamic Asset Generation

For graphics with embedded text:

```python
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import qrcode

class AssetGenerator:
    def __init__(self, templates_path='/app/templates'):
        self.templates_path = templates_path
        self.cache = {}  # In-memory cache

    def generate_welcome_banner(self, guest_data, template_id='default'):
        """
        Generate personalized welcome banner
        """
        cache_key = f"welcome_{template_id}_{guest_data['guest_id']}"

        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Load base template
        template_path = f"{self.templates_path}/welcome_{template_id}.png"
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)

        # Load fonts
        title_font = ImageFont.truetype('fonts/Arial_Bold.ttf', 96)
        subtitle_font = ImageFont.truetype('fonts/Arial.ttf', 48)

        # Render guest name
        name_text = f"Welcome {guest_data['guest_title']} {guest_data['guest_last_name']}!"

        # Center text
        text_bbox = draw.textbbox((0, 0), name_text, font=title_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_x = (img.width - text_width) // 2

        # Add text shadow
        draw.text((text_x+5, 305), name_text, font=title_font, fill=(0,0,0,128))
        # Add main text
        draw.text((text_x, 300), name_text, font=title_font, fill=(255,255,255))

        # Add loyalty badge if VIP
        if guest_data.get('loyalty_tier') in ['gold', 'platinum']:
            badge = Image.open(f"assets/badge_{guest_data['loyalty_tier']}.png")
            badge = badge.resize((150, 150))
            img.paste(badge, (img.width - 200, 50), badge)

        # Add room number
        room_text = f"Room {guest_data['room_number']}"
        draw.text((text_x, 450), room_text, font=subtitle_font, fill=(255,255,255))

        # Save to storage
        output_path = f"/tmp/welcome_{guest_data['guest_id']}.jpg"
        img.save(output_path, quality=90)

        # Cache
        self.cache[cache_key] = output_path

        return output_path

    def generate_qr_code(self, data, guest_id):
        """
        Generate QR code for room service, WiFi, etc.
        """
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        output_path = f"/tmp/qr_{guest_id}.png"
        img.save(output_path)

        return output_path
```

### Template Content Examples

#### **Welcome Screen Template**
```json
{
  "id": 1,
  "title": "Welcome {{guest_title}} {{guest_last_name}}!",
  "content_type": "image",
  "is_template": true,
  "template_variables": ["guest_title", "guest_last_name", "room_number", "loyalty_tier"],
  "template_engine": "pil",
  "base_image": "/templates/welcome_base.png",
  "text_layers": [
    {
      "text": "Welcome {{guest_title}} {{guest_last_name}}!",
      "position": {"x": "center", "y": 300},
      "font": "Arial Bold",
      "size": 96,
      "color": "#FFFFFF"
    },
    {
      "text": "Room {{room_number}}",
      "position": {"x": "center", "y": 450},
      "font": "Arial",
      "size": 48,
      "color": "#FFFFFF"
    }
  ],
  "conditions": [
    {
      "if": "loyalty_tier == 'gold'",
      "then": {"overlay": "/assets/gold_badge.png", "position": {"x": 1700, "y": 50}}
    }
  ]
}
```

#### **Restaurant Menu Template**
```json
{
  "id": 2,
  "title": "Today's Menu",
  "content_type": "video",
  "is_template": true,
  "template_variables": ["dietary_preferences", "guest_language"],
  "filters": [
    {
      "field": "menu_items",
      "condition": "{{#if 'vegetarian' in dietary_preferences}}",
      "filter_out": ["meat", "seafood"]
    }
  ],
  "language_variants": {
    "en": "/content/menu_en.mp4",
    "zh": "/content/menu_zh.mp4",
    "ja": "/content/menu_ja.mp4"
  }
}
```

### Fallback Strategy

```python
def resolve_template_content(content, guest_context):
    """
    Resolve template with fallback strategy
    """
    try:
        # Try rendering with full context
        return render_template(content, guest_context)
    except VariableNotFound as e:
        # Try with default values
        safe_context = {**DEFAULT_GUEST_CONTEXT, **guest_context}
        try:
            return render_template(content, safe_context)
        except Exception:
            # Use fallback content
            if content.fallback_content_id:
                fallback = get_content(content.fallback_content_id)
                return fallback
            else:
                # Return generic version
                return content.to_generic()

DEFAULT_GUEST_CONTEXT = {
    'guest_name': 'Valued Guest',
    'guest_title': 'Dear',
    'guest_first_name': 'Guest',
    'guest_last_name': '',
    'room_number': '---',
    'loyalty_tier': 'regular'
}
```

---
## Next Steps

1. **Review this document** with team for approval
2. **Start Phase 1** (Database Schema) immediately
3. **Parallel work possible:**
   - Backend dev: Phases 2-3
   - Frontend dev: Phases 4-6 (mock data initially)
4. **Integration testing** after Phase 6
5. **Deploy to production** after Phase 7

---

## Notes

- Widget system (Phase 8) is marked as **FUTURE** - not in current scope
- Scheduling feature in playlists is **INCLUDED** in current scope
- All migrations must be **backward compatible**
- API must support **pagination** for large content lists
- Preview page should **cache API response** for performance
- Consider **rate limiting** on preview endpoint (expensive query)

---

**Document maintained by:** Claude Code
**For questions/updates:** Reference this document before making architectural changes
