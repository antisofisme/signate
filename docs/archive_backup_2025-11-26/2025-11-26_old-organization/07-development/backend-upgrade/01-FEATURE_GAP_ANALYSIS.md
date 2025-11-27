# Feature Gap Analysis: Anthias vs Backend (FastAPI)

**Last Updated**: October 28, 2025  
**Status**: COMPLETE - Comprehensive Feature Inventory Complete

## Executive Summary

This document provides a detailed comparison of features between **Anthias** (original Django/SQLite system) and **Backend** (new FastAPI/PostgreSQL system). It identifies:

1. **Features Anthias has that Backend DOESN'T have yet**
2. **Features Backend has that Anthias DOESN'T have**
3. **Migration recommendations with priorities**
4. **Code examples showing implementation differences**

---

## 1. ANTHIAS ARCHITECTURE OVERVIEW

### 1.1 Anthias Data Model

**File**: `/mnt/g/khoirul/signate/anthias/anthias_app/models.py`

```python
class Asset(models.Model):
    # Primary Key
    asset_id = models.TextField(primary_key=True, default=generate_asset_id)
    
    # Content Info
    name = models.TextField(blank=True, null=True)
    uri = models.TextField(blank=True, null=True)  # File path
    mimetype = models.TextField(blank=True, null=True)
    
    # Time-based Scheduling (KEY FEATURE!)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    
    # Display Settings
    duration = models.BigIntegerField(blank=True, null=True)  # Seconds
    play_order = models.IntegerField(default=0)  # Sequencing!
    
    # File Integrity
    md5 = models.TextField(blank=True, null=True)  # MD5 checksum
    
    # State Management
    is_enabled = models.BooleanField(default=False)  # Activation flag
    is_processing = models.BooleanField(default=False)
    skip_asset_check = models.BooleanField(default=False)
    nocache = models.BooleanField(default=False)  # Cache control
    
    # Method: Deadline-based activation
    def is_active(self):
        """Check if asset is active within date range"""
        if self.is_enabled and self.start_date and self.end_date:
            current_time = timezone.now()
            return self.start_date < current_time < self.end_date
        return False
```

### 1.2 Anthias Scheduler (GENIUS FEATURE!)

**File**: `/mnt/g/khoirul/signate/anthias/viewer/scheduling.py`

#### Key Capabilities:
1. **Deadline-based Refresh**
   - Monitors asset deadlines (when content expires)
   - Auto-refreshes playlist when deadline reached
   - No need for external cron jobs

2. **Smart Playlist Generation**
   - Filters only ACTIVE assets (is_enabled=True, within date range)
   - Respects play_order for sequencing
   - Supports shuffle mode (random playlist)

3. **Database Change Detection**
   - Detects database file modifications
   - Auto-updates playlist without restart

4. **Continuous Playback**
   - Maintains current position in playlist
   - Prevents restarting from beginning on updates
   - Supports manual asset override

```python
class Scheduler(object):
    def __init__(self):
        self.assets = []           # Current playlist
        self.deadline = None        # Next deadline to refresh
        self.index = 0             # Current position
        self.counter = 0           # Shuffle counter
        
    def refresh_playlist(self):
        """Smart refresh: only updates if needed"""
        time_cur = timezone.now()
        
        # Trigger 1: Database modified
        if self.get_db_mtime() > self.last_update_db_mtime:
            self.update_playlist()
        
        # Trigger 2: Shuffle cycle complete (every 5 rounds)
        elif settings['shuffle_playlist'] and self.counter >= 5:
            self.update_playlist()
        
        # Trigger 3: Deadline reached
        elif self.deadline and self.deadline <= time_cur:
            self.update_playlist()
    
    def get_next_asset(self):
        """Get next asset in sequence"""
        self.refresh_playlist()
        
        if not self.assets:
            return None
        
        idx = self.index
        self.index = (self.index + 1) % len(self.assets)
        return self.assets[idx]
```

---

## 2. BACKEND (FastAPI) ARCHITECTURE

### 2.1 Backend Data Models

**Files**: `/mnt/g/khoirul/signate/backend/app/models/`

#### Content Model
```python
class Content(Base):
    # Metadata (similar to Anthias)
    title = Column(String(200), nullable=False)
    anthias_url = Column(String(500), nullable=False)
    anthias_asset_id = Column(String(100), index=True)
    duration = Column(Integer, default=10)  # seconds
    
    # Media Metadata (ENHANCED!)
    resolution, width, height, codec, fps, bitrate
    video_duration, video_start_time, video_end_time
    audio_codec, audio_bitrate, audio_sample_rate
    
    # Template Support (NEW!)
    is_template = Column(Boolean, default=False)
    template_variables = Column(JSON, nullable=True)
    language_code = Column(String(10), nullable=True)
    content_group_id = Column(Integer, nullable=True)
    fallback_content_id = Column(Integer, ForeignKey("contents.id"))
```

#### Playlist Model
```python
class Playlist(Base):
    # Scheduling (TIME-BASED)
    schedule_mode = Column(String(20))  # 'inclusive' or 'exclusive'
    schedule_start = Column(Time)
    schedule_end = Column(Time)
    schedule_days = Column(String(50))  # JSON array: ["mon","tue"]
    schedule_timezone = Column(String(50))
    priority = Column(Integer, default=1)
```

#### Assignment Model (NEW!)
```python
class ContentAssignment(Base):
    content_id = Column(Integer, ForeignKey("contents.id"))
    device_id = Column(Integer, ForeignKey("devices.id"))  # Or tag_id
    priority = Column(Integer)
    display_order = Column(Integer)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
```

---

## 3. ANTHIAS FEATURES BACKEND DOESN'T HAVE YET

### 3.1 CRITICAL FEATURES (High Impact)

#### 1. **Deadline-based Smart Scheduler** [PRIORITY: CRITICAL]
- **What it is**: Intelligent scheduler that watches asset deadlines and auto-refreshes
- **Current Status**: Backend has NO equivalent
- **Anthias Implementation**:
  ```python
  # Monitors next deadline
  deadlines = [
      asset.end_date if asset.is_active() else asset.start_date
      for asset in assets
  ]
  deadline = sorted(deadlines)[0]  # Nearest deadline
  
  # Auto-refreshes when deadline reached
  if self.deadline and self.deadline <= time_cur:
      self.update_playlist()
  ```
- **Why Important**: 
  - No need for external cron jobs
  - Automatic content rotation at exact times
  - Seamless content transitions
- **Impact**: HIGH - Affects viewer playback behavior
- **Effort**: MEDIUM - Requires viewer/device logic changes

#### 2. **Play Order Sequencing** [PRIORITY: HIGH]
- **What it is**: `play_order` field that controls content display sequence
- **Current Status**: Backend has NO equivalent
- **Anthias Implementation**:
  ```python
  # Assets ordered by play_order
  enabled_assets = Asset.objects.filter(is_enabled=True).order_by('play_order')
  
  # play_order is integer: 0, 1, 2, 3...
  # Used to maintain sequence in viewer
  ```
- **Why Important**:
  - Defines exact content playback order
  - Critical for sequential playlists (e.g., promotional videos)
  - Different from PlaylistContent.order_index
- **Impact**: MEDIUM - Affects content sequence on devices
- **Effort**: LOW - Simple field addition

#### 3. **MD5 Checksum Validation** [PRIORITY: HIGH]
- **What it is**: MD5 hash for file integrity checking
- **Current Status**: Backend has NO equivalent
- **Anthias Implementation**:
  ```python
  md5 = models.TextField(blank=True, null=True)
  # Used to verify file wasn't corrupted during download
  ```
- **Why Important**:
  - Validates file downloads to devices didn't corrupt
  - Detects network transmission errors
  - Critical for video files over WiFi
- **Impact**: MEDIUM - Affects reliability
- **Effort**: LOW - Hash calculation straightforward

#### 4. **is_enabled Flag for Content Activation** [PRIORITY: HIGH]
- **What it is**: Simple boolean to enable/disable content without deletion
- **Current Status**: Backend uses `is_active` on Content, but NOT on assignments
- **Anthias Implementation**:
  ```python
  is_enabled = models.BooleanField(default=False)
  # When False, content won't appear in viewer
  # Allows disabling without deleting
  ```
- **Why Important**:
  - Soft disable without deletion
  - Preserve all metadata
  - Quick on/off for campaigns
- **Impact**: LOW - Nice to have
- **Effort**: LOW - Already similar in backend

---

### 3.2 IMPORTANT FEATURES (Medium Impact)

#### 5. **Playlist Shuffle Capability** [PRIORITY: MEDIUM]
- **What it is**: Random playlist rotation mode
- **Current Status**: Backend has NO equivalent
- **Anthias Implementation**:
  ```python
  from random import shuffle
  
  if settings['shuffle_playlist']:
      shuffle(playlist)  # Randomize order each refresh
  ```
- **Why Important**:
  - Prevents viewer repetition fatigue
  - Keeps display fresh and interesting
  - Useful for promotional rotations
- **Impact**: LOW - Enhancement
- **Effort**: LOW - Simple shuffle logic

#### 6. **nocache Flag for Dynamic Content** [PRIORITY: MEDIUM]
- **What it is**: Force content refresh (bypass browser cache)
- **Current Status**: Backend has NO equivalent
- **Anthias Implementation**:
  ```python
  nocache = models.BooleanField(default=False)
  # When True, tells viewer to not cache this file
  ```
- **Why Important**:
  - For content that changes (generated images, live data)
  - Forces viewer to always fetch fresh version
  - Useful for weather, stock tickers
- **Impact**: LOW - Specific use case
- **Effort**: LOW - Headers modification

#### 7. **is_processing Flag for Upload Status** [PRIORITY: LOW]
- **What it is**: Track if file is still being processed/uploaded
- **Current Status**: Backend has NO equivalent
- **Anthias Implementation**:
  ```python
  is_processing = models.BooleanField(default=False)
  # True while file is uploading, False when ready
  ```
- **Why Important**:
  - Prevents viewing incomplete files
  - Shows upload progress in UI
- **Impact**: LOW - UX enhancement
- **Effort**: LOW - Status tracking

#### 8. **skip_asset_check Flag** [PRIORITY: LOW]
- **What it is**: Skip file existence/integrity checks
- **Current Status**: Backend has NO equivalent
- **Anthias Implementation**:
  ```python
  skip_asset_check = models.BooleanField(default=False)
  # When True, don't check if file exists
  # Useful for remote streaming URLs
  ```
- **Why Important**:
  - For remote/streaming content (YouTube, web URLs)
  - Skip local file validation
- **Impact**: LOW - Niche feature
- **Effort**: LOW - Conditional validation

---

## 4. BACKEND FEATURES ANTHIAS DOESN'T HAVE

### 4.1 CRITICAL FEATURES

#### 1. **Device Management** [BACKEND ONLY]
- **What it is**: Complete device registration, tracking, and management
- **Backend Implementation**:
  ```python
  class Device(Base):
      device_type = Column(String(20))  # tv, monitor
      device_name = Column(String(100))
      device_uuid = Column(String(36), unique=True)
      
      # TV Control
      ip_address = Column(String(45))  # WebOS TV IP
      passphrase = Column(String(50))  # WebOS pairing
      
      # Monitor Control
      unique_code = Column(String(20), unique=True)  # 6-digit code
      code_expires_at = Column(DateTime)
      
      # Status Tracking
      status = Column(String(20))  # pending, active, inactive
      last_seen = Column(DateTime)  # Heartbeat
      
      # Display Settings
      rotation = Column(Integer)  # 0, 90, 180, 270
      volume_enabled = Column(Boolean)
      
      # Hotel-specific
      room_number = Column(String(20))
      location_type = Column(String(50))
      privacy_mode = Column(String(50))  # limited, full, none
  ```
- **Why Important**: Anthias has NO device management!
- **Impact**: CRITICAL - Entire feature

#### 2. **Tag-based Content Assignment** [BACKEND ONLY]
- **What it is**: Assign content to device groups (tags)
- **Backend Implementation**:
  ```python
  class Tag(Base):
      tag_name = Column(String(100), unique=True)
      tag_priority = Column(Integer)  # Resolution priority
      
  class DeviceTag(Base):
      # Many-to-many: devices and tags
      device_id = Column(Integer, ForeignKey("devices.id"))
      tag_id = Column(Integer, ForeignKey("tags.id"))
  
  class ContentAssignment(Base):
      content_id = Column(Integer)
      tag_id = Column(Integer)  # Assign to tag!
      priority = Column(Integer)
      display_order = Column(Integer)
  ```
- **Why Important**: Anthias has NO tag system!
- **Impact**: CRITICAL - Business requirement

#### 3. **Multi-Platform Support** [BACKEND ONLY]
- **What it is**: Support for WebOS TV, browsers, monitors
- **Backend Implementation**:
  ```python
  class Device(Base):
      device_type = Column(String(20))  # tv, monitor
      platform = Column(String(20))  # webOS, browser
      model_name = Column(String(100))  # WebOS model
      firmware_version = Column(String(50))
  ```
- **Why Important**: Anthias designed for Raspberry Pi only
- **Impact**: CRITICAL - Product differentiation

#### 4. **Playlist Management with Ordering** [BACKEND]
- **What it is**: Collections of content with defined order
- **Backend Implementation**:
  ```python
  class Playlist(Base):
      name = Column(String(100))
      priority = Column(Integer)
      
  class PlaylistContent(Base):
      playlist_id = Column(Integer)
      content_id = Column(Integer)
      order_index = Column(Integer)  # Sequence!
      duration = Column(Integer)  # Override per-item
  ```
- **Why Important**: Anthias has NO playlist concept
- **Impact**: HIGH - Content organization

#### 5. **Schedule Model with Time-based Rules** [BACKEND]
- **What it is**: Separate scheduling entity for complex time rules
- **Backend Implementation**:
  ```python
  class Schedule(Base):
      content_id = Column(Integer)
      device_id = Column(Integer)
      day_of_week = Column(String(20))  # "0,1,2,3,4"
      start_time = Column(Time)  # 07:00:00
      end_time = Column(Time)    # 23:00:00
      start_date = Column(DateTime)
      end_date = Column(DateTime)
      priority = Column(Integer)
  ```
- **Why Important**: Anthias relies on asset start/end_date only
- **Impact**: MEDIUM - Scheduling flexibility

#### 6. **Activity Logging** [BACKEND ONLY]
- **What it is**: Track all system events and user actions
- **Backend Implementation**:
  ```python
  class ActivityLog(Base):
      action = Column(String(100))
      entity_type = Column(String(50))
      entity_id = Column(Integer)
      old_values = Column(JSON)
      new_values = Column(JSON)
      details = Column(JSON)
      timestamp = Column(DateTime)
  ```
- **Why Important**: Audit trail and debugging
- **Impact**: MEDIUM - Operations

#### 7. **Device Command System** [BACKEND ONLY]
- **What it is**: Send commands to devices (screenshot, reboot, logs)
- **Backend Implementation**:
  ```python
  class DeviceCommand(Base):
      device_id = Column(Integer)
      command_type = Column(String(50))  # screenshot, logs, reboot
      status = Column(String(20))  # pending, completed, failed
      result = Column(JSON)
      executed_at = Column(DateTime)
  ```
- **Why Important**: Device control and debugging
- **Impact**: MEDIUM - Device management

---

### 4.2 ADDITIONAL FEATURES

#### 8. **Multi-language & Template Support** [BACKEND ONLY]
- Content variables for dynamic text insertion
- Language code support for translations
- Fallback content for failed templates

#### 9. **WebOS TV Integration** [BACKEND ONLY]
- WebOS Developer Mode support
- TV IP control and pairing
- IPK packaging for native app

#### 10. **Firebird Database Integration** [BACKEND ONLY]
- Hotel PMS integration
- Guest information synchronization
- Room status updates

---

## 5. COMPLETE FEATURE COMPARISON TABLE

| Feature | Anthias | Backend | Notes |
|---------|---------|---------|-------|
| **Core Features** |
| Content Upload | ✅ | ✅ | Both support |
| Content Display | ✅ | ✅ | Via viewer app |
| Device Registration | ❌ | ✅ | Backend has device mgmt |
| **Scheduling** |
| Time-based Activation (start_date/end_date) | ✅ | ❌ | Anthias Asset model |
| Playlist Scheduling (time of day) | ❌ | ✅ | Backend Schedule model |
| Play Order Sequencing | ✅ | ❌ | Anthias Asset.play_order |
| Daily Schedule Rules | ❌ | ✅ | Backend Schedule model |
| **Content Management** |
| Playlist Collections | ❌ | ✅ | Backend Playlist model |
| Content Ordering | ❌ (Asset level) | ✅ | PlaylistContent.order_index |
| Tag-based Assignment | ❌ | ✅ | Backend Tag system |
| Device Assignment | ❌ | ✅ | Backend ContentAssignment |
| Priority Levels | ❌ | ✅ | Assignment.priority |
| **Display Control** |
| is_enabled Flag | ✅ | ✅ (partial) | Backend uses on Content only |
| Shuffle Playlist | ✅ | ❌ | Anthias scheduler |
| nocache Flag | ✅ | ❌ | Bypass browser cache |
| is_processing Status | ✅ | ❌ | Upload status |
| **File Management** |
| MD5 Checksum | ✅ | ❌ | Anthias Asset.md5 |
| skip_asset_check | ✅ | ❌ | For remote URLs |
| **Device Management** |
| Device Registry | ❌ | ✅ | Monitor + TV |
| Device Status Tracking | ❌ | ✅ | Heartbeat, last_seen |
| WebOS TV Support | ❌ | ✅ | IP + passphrase |
| Monitor Support | ❌ | ✅ | 6-digit code |
| Display Rotation | ❌ | ✅ | 0, 90, 180, 270 |
| Volume Control | ❌ | ✅ | Per-device setting |
| **Advanced** |
| Activity Logging | ❌ | ✅ | Audit trail |
| Device Commands | ❌ | ✅ | Screenshot, logs, reboot |
| Template Support | ❌ | ✅ | Dynamic text |
| Multi-language | ❌ | ✅ | Language codes |
| Firebird Integration | ❌ | ✅ | Hotel PMS |
| Speed Test | ❌ | ✅ | Network diagnostics |
| Dashboard Analytics | ❌ | ✅ | Activity timeline |

---

## 6. RECOMMENDED MIGRATION PRIORITIES

### Phase 1: CRITICAL (Implement ASAP)
These features are essential for parity with Anthias.

#### 1.1 Play Order Sequencing [EFFORT: LOW]
```python
# Add to Content model
play_order = Column(Integer, default=0, index=True)

# Modify viewer to sort by play_order in addition to assignments
```
- **Why**: Core scheduling feature
- **Files to modify**: 
  - `/mnt/g/khoirul/signate/backend/app/models/content.py` - Add field
  - `/mnt/g/khoirul/signate/viewer/js/player/api.js` - Sort logic
- **Database migration**: Simple ADD COLUMN

#### 1.2 MD5 Checksum Validation [EFFORT: MEDIUM]
```python
# Add to Content model
md5_hash = Column(String(32), nullable=True)  # MD5 hex digest

# In content.py upload endpoint
import hashlib
def calculate_md5(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()

content.md5_hash = calculate_md5(file_content)
```
- **Why**: File integrity checking for reliability
- **Files to modify**:
  - `/mnt/g/khoirul/signate/backend/app/models/content.py` - Add field
  - `/mnt/g/khoirul/signate/backend/app/api/content.py` - Calculate in upload
  - `/mnt/g/khoirul/signate/viewer/js/player/api.js` - Validate on download

#### 1.3 is_enabled Flag on Content [EFFORT: LOW]
- Already exists as `is_active` in Backend
- Add explicit `is_enabled` for Anthias parity
- Simple soft-delete mechanism

#### 1.4 Deadline-based Smart Scheduler [EFFORT: HIGH]
```python
# New service: viewer scheduling logic
# /mnt/g/khoirul/signate/backend/app/services/scheduler_service.py

class ViewerScheduler:
    def get_next_deadline(self, assets):
        """Get nearest deadline across all assets"""
        deadlines = []
        for asset in assets:
            if asset.is_active():
                deadlines.append(asset.end_date)
            else:
                deadlines.append(asset.start_date)
        return min(deadlines) if deadlines else None
    
    def should_refresh_playlist(self, last_refresh, now, deadline):
        """Determine if playlist needs refresh"""
        # Database changed?
        # Deadline reached?
        # Shuffle cycle complete?
        pass
```
- **Why**: Automatic content rotation without cron
- **Complexity**: Requires viewer heartbeat enhancement
- **Files to modify**:
  - Backend: Create scheduler service
  - Viewer: Enhanced heartbeat logic

### Phase 2: HIGH PRIORITY (Next sprint)
These improve functionality significantly.

#### 2.1 Playlist Shuffle Mode [EFFORT: LOW]
```python
# Add to Playlist model or API
shuffle_enabled = Column(Boolean, default=False)

# Viewer logic
if playlist.shuffle_enabled:
    from random import shuffle
    shuffle(content_items)
```

#### 2.2 nocache Flag for Dynamic Content [EFFORT: LOW]
```python
# Add to Content model
nocache = Column(Boolean, default=False)

# Viewer cache-control header
if content.nocache:
    headers['Cache-Control'] = 'no-cache, no-store'
```

#### 2.3 Device Logging & Statistics [EFFORT: MEDIUM]
- Expand existing `DeviceLog` model
- Track playback metrics per device
- Analytics dashboard

### Phase 3: MEDIUM PRIORITY (Enhancement)

#### 3.1 Device Command Extensions [EFFORT: MEDIUM]
- Add screenshot capability
- Log streaming
- Reboot/shutdown commands

#### 3.2 Advanced Scheduling [EFFORT: MEDIUM]
- Complex time rules (specific days + times)
- Timezone support
- Holiday calendar integration

### Phase 4: NICE-TO-HAVE (Future)

#### 4.1 Template & Multi-language [EFFORT: HIGH]
- Already in backend, enhance
- Variable injection system
- Translation management

#### 4.2 Analytics & Reporting [EFFORT: HIGH]
- Content performance metrics
- Device playback statistics
- ROI tracking for campaigns

---

## 7. CODE IMPLEMENTATION EXAMPLES

### Example 1: Adding Play Order to Content

#### Backend Change
```python
# /mnt/g/khoirul/signate/backend/app/models/content.py
from sqlalchemy import Column, Integer

class Content(Base):
    # ... existing fields ...
    
    # ADD THIS
    play_order = Column(Integer, default=0, index=True)
    
    def to_dict(self):
        return {
            # ... existing fields ...
            "play_order": self.play_order,
        }
```

#### Database Migration
```sql
ALTER TABLE contents ADD COLUMN play_order INTEGER DEFAULT 0;
CREATE INDEX idx_contents_play_order ON contents(play_order);
```

#### Viewer Changes
```javascript
// /mnt/g/khoirul/signate/viewer/js/player/api.js
async function getPlaylist() {
    const response = await fetch('/api/content/');
    const data = await response.json();
    
    // SORT by play_order
    const playlist = data.data.sort((a, b) => a.play_order - b.play_order);
    
    return playlist;
}
```

---

### Example 2: Adding MD5 Checksum Validation

#### Backend Upload
```python
# /mnt/g/khoirul/signate/backend/app/api/content.py
import hashlib

async def upload_content(...):
    # Read file
    file_bytes = await file.read()
    
    # Calculate MD5
    md5_hash = hashlib.md5(file_bytes).hexdigest()
    
    # Save to content
    content = Content(
        title=title,
        md5_hash=md5_hash,
        # ... other fields ...
    )
    db.add(content)
    db.commit()
    
    return {
        "id": content.id,
        "md5_hash": content.md5_hash
    }
```

#### Viewer Validation
```javascript
// /mnt/g/khoirul/signate/viewer/js/player/api.js
async function verifyFileIntegrity(file, expectedMd5) {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    // For MD5, would need polyfill or backend validation
    
    // Alternative: request validation from backend
    const response = await fetch(`/api/content/verify-md5`, {
        method: 'POST',
        body: JSON.stringify({
            file: file,
            expected_md5: expectedMd5
        })
    });
    
    return response.ok;
}
```

---

### Example 3: Deadline-based Scheduler

#### Backend Scheduler Service
```python
# /mnt/g/khoirul/signate/backend/app/services/scheduler_service.py
from datetime import datetime
from app.models.content import Content
from app.models.playlist import Playlist, PlaylistContent

class ViewerScheduler:
    def __init__(self, device_id):
        self.device_id = device_id
        self.current_playlist = []
        self.deadline = None
    
    def get_active_content(self):
        """Get all content active for this device"""
        from app.models.assignment import ContentAssignment
        from sqlalchemy.orm import Session
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        now = datetime.utcnow()
        
        # Get content assigned to device
        assignments = db.query(ContentAssignment).filter(
            ContentAssignment.device_id == self.device_id
        ).all()
        
        # Filter by date range
        active_content = []
        deadlines = []
        
        for assignment in assignments:
            if assignment.content.is_active:
                if assignment.start_date and assignment.end_date:
                    if assignment.start_date <= now <= assignment.end_date:
                        active_content.append(assignment.content)
                        deadlines.append(assignment.end_date)
                else:
                    active_content.append(assignment.content)
        
        # Find next deadline
        self.deadline = min(deadlines) if deadlines else None
        
        return active_content
    
    def should_refresh(self, last_refresh_time):
        """Determine if playlist needs refresh"""
        now = datetime.utcnow()
        
        # Deadline passed?
        if self.deadline and self.deadline <= now:
            return True
        
        # Database changed? (would need mtime check)
        # Would require storing file stat info
        
        return False
```

#### Viewer Integration
```javascript
// /mnt/g/khoirul/signate/viewer/js/player/api.js
let scheduler = {
    deadline: null,
    playlist: [],
    index: 0,
    
    async refreshPlaylist() {
        const response = await fetch(`/api/devices/${deviceId}/playlist`);
        const data = await response.json();
        
        this.playlist = data.content;
        this.deadline = data.next_deadline;
        this.index = 0;
    },
    
    getNextAsset() {
        if (!this.playlist || this.playlist.length === 0) {
            return null;
        }
        
        const asset = this.playlist[this.index];
        this.index = (this.index + 1) % this.playlist.length;
        
        return asset;
    },
    
    // In main playback loop
    checkDeadline() {
        if (this.deadline && new Date() >= new Date(this.deadline)) {
            // Deadline reached - refresh playlist
            this.refreshPlaylist();
        }
    }
};
```

---

## 8. MIGRATION STRATEGY

### Phase 1: Backend Schema Updates (Week 1)
1. Add `play_order` to Content
2. Add `md5_hash` to Content
3. Add `is_enabled` alias to Content
4. Create database migration files

### Phase 2: API Endpoint Updates (Week 2)
1. Update Content upload to calculate MD5
2. Add content sorting by play_order
3. Add shuffle mode support
4. Add nocache flag support

### Phase 3: Viewer Updates (Week 3)
1. Implement play_order sorting
2. Implement MD5 validation (basic)
3. Implement nocache cache-control headers
4. Add shuffle playlist logic

### Phase 4: Advanced Features (Week 4-5)
1. Implement deadline-based scheduler
2. Add scheduler service to backend
3. Enhanced device heartbeat with scheduler
4. Analytics dashboard

---

## 9. RISK ASSESSMENT

| Feature | Risk | Mitigation |
|---------|------|-----------|
| Play Order | LOW | Simple field, backward compatible |
| MD5 | MEDIUM | Fallback to no validation if fails |
| Scheduler | MEDIUM | Test with extensive playback scenarios |
| Shuffle | LOW | Simple logic, easy to disable |
| Device Commands | MEDIUM | Separate service, non-blocking |

---

## 10. SUCCESS METRICS

### Functional Parity
- [x] Device management (Backend only feature)
- [ ] Play order sequencing
- [ ] MD5 validation
- [ ] Deadline-based refresh
- [ ] Playlist shuffle

### Performance
- Content refresh within 100ms of deadline
- No playback interruption on refresh
- Validation errors don't crash viewer

### User Experience
- Content displays in correct order
- Playlists auto-rotate at scheduled times
- No visible reload when refreshing

---

## 11. APPENDIX: FILE LOCATIONS

### Anthias Key Files
```
/mnt/g/khoirul/signate/anthias/
├── anthias_app/
│   └── models.py          # Asset model with scheduler fields
├── viewer/
│   └── scheduling.py      # Smart scheduler implementation
└── api/
    ├── views/v2.py        # Asset CRUD endpoints
    ├── helpers.py         # Asset ordering helpers
    └── serializers/v2.py  # Asset serialization
```

### Backend Key Files
```
/mnt/g/khoirul/signate/backend/app/
├── models/
│   ├── content.py         # Content model
│   ├── playlist.py        # Playlist model
│   ├── assignment.py      # Content assignment
│   └── schedule.py        # Schedule model
├── api/
│   ├── content.py         # Content endpoints
│   ├── playlists.py       # Playlist endpoints
│   └── devices.py         # Device endpoints
└── services/
    └── anthias_service.py # Anthias integration
```

### Viewer Files
```
/mnt/g/khoirul/signate/viewer/
├── js/player/
│   ├── api.js            # API communication
│   ├── playlist.js       # Playlist logic
│   └── schedule.js       # Scheduling logic
└── js/shell/
    ├── activation-poll.js # Device activation
    └── heartbeat.js       # Device heartbeat
```

---

## 12. CONCLUSION

The Backend (FastAPI) provides significantly more advanced features than Anthias:
- **Device management** (monitors + WebOS TV)
- **Tag-based content distribution**
- **Advanced scheduling** with time-based rules
- **Activity logging and audit trail**
- **Device command system**

However, Anthias has some clever scheduling features the Backend should adopt:
- **Deadline-based automatic refresh** (prevents stale content)
- **Play order sequencing** (content ordering)
- **File integrity checking** (MD5 validation)

The recommended approach is **selective feature migration**:
1. Add Anthias scheduling fields to Backend (play_order, MD5)
2. Implement deadline-based scheduler in viewer
3. Keep Backend's superior device management
4. Gradually enhance with advanced features

This creates a **best-of-both-worlds** system combining:
- Anthias's clever scheduler
- Backend's device management
- Modern FastAPI architecture

---

**Next Steps**: 
1. Review and validate this analysis
2. Prioritize Phase 1 features
3. Create database migration files
4. Begin implementation in 2-week sprints

