# Scheduler & Playlist Manager - Quick Reference

## 🚀 Quick Start

### API Endpoints

```bash
# Get active playlist for device 123
GET /api/playlists/devices/123/active?shuffle=false

# Get next deadline for device 123
GET /api/playlists/devices/123/next-deadline
```

---

## 📋 Service Usage

### ContentScheduler

```python
from app.services.scheduler import ContentScheduler

# Initialize
scheduler = ContentScheduler(
    db=db,
    device_id=123,
    shuffle_enabled=False,
    request_id="req-123"
)

# Get active content with deadline
content_list, next_deadline = scheduler.get_active_content()

# Get next refresh time
next_refresh = scheduler.get_next_refresh_time()

# Calculate deadline for specific content
deadline = scheduler.calculate_deadline(
    content=content_obj,
    assignment_start=start_datetime,
    assignment_end=end_datetime
)
```

### PlaylistManager

```python
from app.services.playlist_manager import PlaylistManager

# Initialize
manager = PlaylistManager(
    db=db,
    device_id=123,
    shuffle_enabled=False,
    request_id="req-123"
)

# Generate playlist
playlist = manager.generate_playlist(device_id=123, apply_shuffle=False)

# Check for changes
has_changed, new_hash = manager.has_playlist_changed(
    device_id=123,
    previous_hash="abc123..."
)

# Get metadata
metadata = manager.get_playlist_metadata(device_id=123)
```

---

## 📊 Response Examples

### Active Playlist Response

```json
{
  "success": true,
  "data": {
    "playlist": [
      {
        "content_id": 1,
        "title": "Welcome Video",
        "content_type": "video",
        "anthias_url": "http://192.168.5.12:8000/assets/abc123.mp4",
        "duration": 30,
        "order_index": 0,
        "playlist_id": 5,
        "playlist_name": "Morning Playlist",
        "source": "playlist",
        "is_active": true
      },
      {
        "content_id": 2,
        "title": "Emergency Alert",
        "content_type": "image",
        "anthias_url": "http://192.168.5.12:8000/assets/def456.jpg",
        "duration": 10,
        "priority": 10,
        "display_order": 0,
        "source": "direct_assignment",
        "start_date": "2025-10-28T08:00:00Z",
        "end_date": "2025-10-28T12:00:00Z",
        "deadline": "2025-10-28T12:00:00Z",
        "is_active": true
      }
    ],
    "next_deadline": "2025-10-28T12:00:00Z",
    "total_items": 2,
    "total_duration": 40,
    "shuffle_enabled": false
  },
  "request_id": "req-123"
}
```

### Next Deadline Response

```json
{
  "success": true,
  "data": {
    "device_id": 123,
    "next_deadline": "2025-10-28T12:00:00Z",
    "seconds_until_deadline": 3600,
    "has_deadline": true
  },
  "request_id": "req-123"
}
```

---

## 🔧 Content Sources

### 1. Playlist Assignments

Content assigned via playlists:

```
Device → PlaylistAssignment → Playlist → PlaylistContent → Content
```

**Features**:
- Ordered by `order_index`
- Custom duration override
- No scheduling (always active)
- Source: `"playlist"`

**Database Flow**:
```sql
-- Get playlists for device
SELECT * FROM playlist_assignments WHERE device_id = 123

-- Get content from playlist
SELECT * FROM playlist_content WHERE playlist_id = 5 ORDER BY order_index

-- Get content details
SELECT * FROM contents WHERE id IN (...)
```

### 2. Direct Content Assignments

Content directly assigned to device or tags:

```
Device → ContentAssignment → Content
Device → DeviceTag → ContentAssignment (tag_id) → Content
```

**Features**:
- Ordered by `priority` (desc) + `display_order`
- **Scheduling**: `start_date`, `end_date`
- Source: `"direct_assignment"`
- Deadline calculation enabled

**Database Flow**:
```sql
-- Get device tags
SELECT tag_id FROM device_tags WHERE device_id = 123

-- Get direct assignments
SELECT * FROM content_assignments
WHERE (device_id = 123 OR tag_id IN (...))
  AND is_active = true
ORDER BY priority DESC, display_order

-- Get content details
SELECT * FROM contents WHERE id IN (...)
```

---

## ⏰ Deadline Algorithm

### Calculation Logic

```python
def calculate_deadline(content, start_date, end_date):
    now = datetime.now(timezone.utc)

    if not start_date or not end_date:
        return None  # No scheduling - always active

    is_active = (start_date <= now < end_date)

    if is_active:
        return end_date  # Content expires
    else:
        return start_date  # Content activates
```

### Examples

**Example 1: Active Content**
```
Now: 2025-10-28 10:00:00
Start: 2025-10-28 08:00:00
End: 2025-10-28 12:00:00

is_active = True (10:00 is between 08:00 and 12:00)
deadline = 2025-10-28 12:00:00 (expires at noon)
```

**Example 2: Future Content**
```
Now: 2025-10-28 10:00:00
Start: 2025-10-28 14:00:00
End: 2025-10-28 18:00:00

is_active = False (10:00 is before 14:00)
deadline = 2025-10-28 14:00:00 (activates at 14:00)
```

**Example 3: Expired Content**
```
Now: 2025-10-28 10:00:00
Start: 2025-10-28 06:00:00
End: 2025-10-28 08:00:00

is_active = False (10:00 is after 08:00)
deadline = 2025-10-28 06:00:00 (already passed)
```

---

## 🔄 Refresh Triggers

### When to Refresh Playlist

```python
should_refresh = (
    playlist_hash_changed OR
    (shuffle_enabled AND counter >= 5) OR
    (deadline_reached)
)
```

### Trigger Details

1. **Content Changed**:
   - Playlist hash changed
   - New content added/removed
   - Content order changed

2. **Shuffle Threshold**:
   - Only when shuffle enabled
   - Counter increments after each full playlist cycle
   - Refresh when counter >= 5

3. **Deadline Reached**:
   - Current time >= nearest deadline
   - Content activating or expiring
   - Automatic refresh needed

---

## 🎲 Shuffle Mode

### How It Works

```python
playlist = [A, B, C, D, E]

# With shuffle=False
cycle 1: A → B → C → D → E (repeat)
cycle 2: A → B → C → D → E (repeat)
...

# With shuffle=True
cycle 1: C → A → E → B → D (random)
cycle 2: B → D → A → C → E (random)
cycle 3: E → C → D → A → B (random)
cycle 4: A → E → C → B → D (random)
cycle 5: D → B → A → E → C (random)
-- counter >= 5, reshuffle playlist --
cycle 6: C → D → E → A → B (new random order)
```

### Implementation

```python
if shuffle_enabled and len(playlist) > 1:
    from random import shuffle
    shuffle(playlist)  # In-place randomization
```

---

## 📊 Playlist Metadata

### Structure

```json
{
  "device_id": 123,
  "total_playlists": 2,
  "total_items": 10,
  "total_duration": 300,
  "playlist_hash": "abc123...",
  "shuffle_enabled": false,
  "generated_at": "2025-10-28T10:00:00Z"
}
```

### Hash Calculation

```python
# Create stable signature (content_id + order_index)
signature = [
    (item['content_id'], item['order_index'])
    for item in playlist_items
]

# Generate SHA256 hash
import hashlib
import json
hash_value = hashlib.sha256(
    json.dumps(signature, sort_keys=True).encode()
).hexdigest()
```

---

## 🏷️ Tag-Based Assignments

### How Tags Work

```
Device → DeviceTag → Tag
Tag → PlaylistAssignment → Playlist
Tag → ContentAssignment → Content
```

### Example

```
Device 123:
  - Tags: ["lobby", "floor-1"]

Assignments:
  - Playlist "Morning Show" → Tag "lobby"
  - Content "Emergency Alert" → Tag "floor-1"

Result:
  Device 123 receives:
    - Playlist "Morning Show" (via "lobby" tag)
    - Content "Emergency Alert" (via "floor-1" tag)
```

### Query

```python
# Get device tags
device_tags = db.query(DeviceTag.tag_id).filter(
    DeviceTag.device_id == 123
).all()

tag_ids = [tag_id[0] for tag_id in device_tags]

# Get playlists assigned to tags
playlists = db.query(PlaylistAssignment).filter(
    PlaylistAssignment.tag_id.in_(tag_ids)
).all()
```

---

## 🎯 Priority Ordering

### Direct Assignments

Content assignments have priority:

```python
# Higher priority = displayed first
Content A: priority=10, display_order=0
Content B: priority=10, display_order=1
Content C: priority=5, display_order=0

Order: A → B → C
```

### Playlists

Playlists also have priority:

```python
Playlist X: priority=10
Playlist Y: priority=5

# Content from Playlist X appears first
```

### SQL Query

```sql
SELECT * FROM content_assignments
WHERE device_id = 123
ORDER BY priority DESC, display_order ASC
```

---

## 🧪 Testing Examples

### Test Active Content

```python
from app.services.scheduler import ContentScheduler

scheduler = ContentScheduler(db=db, device_id=123)

# Get active content
content_list, deadline = scheduler.get_active_content()

assert len(content_list) > 0
assert all(item['is_active'] for item in content_list)
print(f"Next deadline: {deadline}")
```

### Test Playlist Generation

```python
from app.services.playlist_manager import PlaylistManager

manager = PlaylistManager(db=db, device_id=123, shuffle_enabled=True)

# Generate playlist
playlist = manager.generate_playlist()

assert len(playlist) > 0
print(f"Generated {len(playlist)} items")

# Check shuffle
playlist2 = manager.generate_playlist()
assert playlist != playlist2  # Different order
```

### Test Change Detection

```python
manager = PlaylistManager(db=db, device_id=123)

# First fetch
playlist1 = manager.generate_playlist()
hash1 = manager.calculate_playlist_hash(playlist1)

# Add content to playlist...
# db.add(new_content)
# db.commit()

# Check for changes
has_changed, hash2 = manager.has_playlist_changed(123, hash1)

assert has_changed == True
assert hash1 != hash2
```

---

## 🚨 Error Handling

### Device Not Found

```python
try:
    scheduler = ContentScheduler(db=db, device_id=999)
    content = scheduler.get_active_content()
except NotFoundException as e:
    print(f"Device not found: {e.message}")
    # Response: 404 with proper error message
```

### No Playlists Assigned

```python
manager = PlaylistManager(db=db, device_id=123)
playlist = manager.generate_playlist()

# Returns empty list if no assignments
assert isinstance(playlist, list)
if not playlist:
    print("No content assigned to device")
```

### Invalid Scheduling

```python
# Content with start_date but no end_date
# Deadline calculation returns None
# Content treated as always active
```

---

## 📈 Performance Tips

### 1. Cache Playlist Hash

```python
# Cache for 5 minutes
from app.core.cache import cache

hash_key = f"playlist_hash:{device_id}"
cached_hash = cache.get(hash_key)

if not cached_hash:
    playlist = manager.generate_playlist()
    cached_hash = manager.calculate_playlist_hash(playlist)
    cache.set(hash_key, cached_hash, ttl=300)
```

### 2. Batch Device Queries

```python
# Get playlists for multiple devices at once
device_ids = [123, 124, 125]

assignments = db.query(PlaylistAssignment).filter(
    PlaylistAssignment.device_id.in_(device_ids)
).all()
```

### 3. Preload Content

```python
# Use joinedload to avoid N+1 queries
from sqlalchemy.orm import joinedload

playlists = db.query(Playlist).options(
    joinedload(Playlist.content_items)
).filter(Playlist.id.in_(playlist_ids)).all()
```

---

## 🔍 Debugging

### Enable Debug Logging

```python
from app.core.logging import StructuredLogger

logger = StructuredLogger(__name__)
logger.set_level("DEBUG")

# Now all logger.debug() calls will be output
```

### Check Deadline Calculation

```python
scheduler = ContentScheduler(db=db, device_id=123)

content_list, deadline = scheduler.get_device_content(include_inactive=True)

for item in content_list:
    print(f"Content: {item['title']}")
    print(f"  Active: {item['is_active']}")
    print(f"  Deadline: {item.get('deadline')}")
    print(f"  Source: {item.get('source')}")
```

### Inspect Playlist Hash

```python
manager = PlaylistManager(db=db, device_id=123)

playlist = manager.generate_playlist()
hash_value = manager.calculate_playlist_hash(playlist)

print(f"Playlist hash: {hash_value}")
print(f"Total items: {len(playlist)}")

# Check what's included in hash
signature = [(item['content_id'], item.get('order_index', 0)) for item in playlist]
print(f"Signature: {signature}")
```

---

## 📝 Common Patterns

### Pattern 1: Poll for Updates

```python
# Device polls every N seconds based on deadline
import time

while True:
    # Get next deadline
    response = requests.get(f"/api/playlists/devices/{device_id}/next-deadline")
    data = response.json()["data"]

    if data["has_deadline"]:
        sleep_seconds = min(data["seconds_until_deadline"], 300)  # Max 5 min
    else:
        sleep_seconds = 300  # Default: check every 5 minutes

    time.sleep(sleep_seconds)

    # Fetch updated playlist
    response = requests.get(f"/api/playlists/devices/{device_id}/active")
    playlist = response.json()["data"]["playlist"]
    # Update display...
```

### Pattern 2: WebSocket Real-Time Updates

```python
# Server pushes updates when playlist changes
import asyncio

async def watch_playlist(device_id):
    manager = PlaylistManager(db, device_id)
    last_hash = None

    while True:
        playlist = manager.generate_playlist()
        current_hash = manager.calculate_playlist_hash(playlist)

        if current_hash != last_hash:
            # Playlist changed - notify device
            await websocket.send_json({
                "type": "playlist_update",
                "device_id": device_id,
                "playlist": playlist
            })
            last_hash = current_hash

        await asyncio.sleep(30)  # Check every 30 seconds
```

### Pattern 3: Scheduled Content Rotation

```python
# Morning playlist: 6am - 12pm
# Afternoon playlist: 12pm - 6pm
# Evening playlist: 6pm - 12am

morning_assignment = ContentAssignment(
    content_id=1,
    device_id=123,
    start_date=datetime(2025, 10, 28, 6, 0, 0),
    end_date=datetime(2025, 10, 28, 12, 0, 0)
)

afternoon_assignment = ContentAssignment(
    content_id=2,
    device_id=123,
    start_date=datetime(2025, 10, 28, 12, 0, 0),
    end_date=datetime(2025, 10, 28, 18, 0, 0)
)

# Scheduler automatically switches at noon
```

---

## 🎓 Best Practices

1. **Always Use Request IDs**: Enables request tracing
2. **Handle Empty Playlists**: Gracefully handle devices with no content
3. **Cache Wisely**: Cache hashes and metadata, not full playlists
4. **Use Deadlines**: Set next poll interval based on deadline
5. **Monitor Errors**: Log all exceptions with context
6. **Validate Dates**: Ensure start_date < end_date
7. **Test Edge Cases**: No content, expired content, future content
8. **Use UTC**: All datetimes should be timezone-aware UTC

---

## 📚 Related Documentation

- **API Endpoints**: See `API_ENDPOINTS_DOCUMENTATION.md`
- **Database Models**: See `app/models/*.py`
- **Full Implementation**: See `SCHEDULER_IMPLEMENTATION_COMPLETE.md`

---

**Last Updated**: 2025-10-28
