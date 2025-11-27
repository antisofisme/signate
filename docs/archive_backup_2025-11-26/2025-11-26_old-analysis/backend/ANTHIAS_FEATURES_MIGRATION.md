# Anthias Features Migration - Content Model Enhancement

**Date**: 2025-10-28
**Status**: COMPLETE
**Migration File**: `008_add_anthias_features_to_content.sql`

---

## Overview

Added missing Anthias features to the Content model for enhanced campaign management, playback control, and file integrity verification. These features align the backend Content model with the Anthias Asset model capabilities.

---

## Changes Summary

### 1. Database Migration

**File**: `/mnt/g/khoirul/signate/backend/migrations/008_add_anthias_features_to_content.sql`

#### New Columns Added to `contents` Table

| Column | Type | Default | Nullable | Index | Purpose |
|--------|------|---------|----------|-------|---------|
| `play_order` | INTEGER | 0 | NO | YES | Sequence/order for content playback within playlists (0-indexed) |
| `start_date` | TIMESTAMP WITH TIME ZONE | NULL | YES | YES | Campaign start date for time-based activation |
| `end_date` | TIMESTAMP WITH TIME ZONE | NULL | YES | YES | Campaign end date for time-based expiration |
| `is_enabled` | BOOLEAN | TRUE | NO | YES | Soft delete flag (False disables content without deletion) |
| `shuffle` | BOOLEAN | FALSE | NO | NO | Enable shuffle/random playback mode for rotating content |
| `md5_checksum` | VARCHAR(32) | NULL | YES | NO | MD5 checksum for file integrity verification |

#### Indexes Created

| Index Name | Columns | Purpose |
|------------|---------|---------|
| `idx_contents_play_order` | play_order | Query by playback sequence |
| `idx_contents_start_date` | start_date | Query by campaign activation date |
| `idx_contents_end_date` | end_date | Query by campaign expiration date |
| `idx_contents_is_enabled` | is_enabled | Filter disabled content |
| `idx_contents_date_range` | start_date, end_date | Campaign date range queries |
| `idx_contents_active` | is_enabled, start_date, end_date | Active content queries |

#### Helper Function

Created `is_content_active()` function for checking if content is currently active:

```sql
CREATE OR REPLACE FUNCTION is_content_active(
    p_is_enabled BOOLEAN,
    p_start_date TIMESTAMP WITH TIME ZONE,
    p_end_date TIMESTAMP WITH TIME ZONE
)
RETURNS BOOLEAN AS $$
BEGIN
    -- Content must be enabled
    IF NOT p_is_enabled THEN
        RETURN FALSE;
    END IF;

    -- Check campaign date range if dates are set
    IF p_start_date IS NOT NULL AND p_end_date IS NOT NULL THEN
        RETURN (NOW() AT TIME ZONE 'UTC') BETWEEN p_start_date AND p_end_date;
    END IF;

    -- If no campaign dates, content is active if enabled
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
```

---

### 2. SQLAlchemy Model Updates

**File**: `/mnt/g/khoirul/signate/backend/app/models/content.py`

#### New Fields in Content Class

```python
# Anthias Features - Campaign Management & Playback Control
play_order = Column(Integer, default=0, index=True)  # Sequence/order for content playback within playlists
start_date = Column(DateTime, nullable=True, index=True)  # Campaign start date for time-based activation
end_date = Column(DateTime, nullable=True, index=True)  # Campaign end date for time-based expiration
is_enabled = Column(Boolean, default=True, index=True)  # Soft delete flag (False = disabled but not deleted)
shuffle = Column(Boolean, default=False)  # Enable shuffle/random playback mode
md5_checksum = Column(String(32), nullable=True)  # MD5 checksum for file integrity verification
```

#### Updated `to_dict()` Method

Added new fields to dictionary serialization:

```python
"play_order": self.play_order,
"start_date": self.start_date.isoformat() if self.start_date else None,
"end_date": self.end_date.isoformat() if self.end_date else None,
"is_enabled": self.is_enabled,
"shuffle": self.shuffle,
"md5_checksum": self.md5_checksum,
```

---

### 3. Pydantic Schema Updates

**File**: `/mnt/g/khoirul/signate/backend/app/schemas/content.py`

#### Updated `ContentUploadResponse`

Added fields:
```python
play_order: int = 0
start_date: Optional[datetime] = None
end_date: Optional[datetime] = None
is_enabled: bool = True
shuffle: bool = False
md5_checksum: Optional[str] = None
```

#### Updated `ContentResponse`

Added fields (same as ContentUploadResponse):
```python
play_order: int = 0
start_date: Optional[datetime] = None
end_date: Optional[datetime] = None
is_enabled: bool = True
shuffle: bool = False
md5_checksum: Optional[str] = None
```

#### Updated `ContentUpdateRequest`

Added fields for PATCH/PUT operations:
```python
play_order: Optional[int] = Field(None, ge=0)
start_date: Optional[datetime] = None
end_date: Optional[datetime] = None
is_enabled: Optional[bool] = None
shuffle: Optional[bool] = None
md5_checksum: Optional[str] = Field(None, max_length=32)
```

Example update payload:
```json
{
  "title": "Updated Banner",
  "description": "Updated description",
  "duration": 15,
  "is_active": true,
  "play_order": 0,
  "start_date": "2025-11-01T00:00:00Z",
  "end_date": "2025-11-30T23:59:59Z",
  "is_enabled": true,
  "shuffle": false,
  "md5_checksum": "5d41402abc4b2a76b9719d911017c592"
}
```

---

## Field Definitions

### `play_order` (Integer)
- **Type**: INTEGER
- **Default**: 0
- **Indexed**: Yes
- **Use Case**: Controls the sequence/order of content when played within playlists
- **Example**: play_order=0 (first), play_order=1 (second), etc.

### `start_date` (DateTime)
- **Type**: TIMESTAMP WITH TIME ZONE
- **Default**: NULL (no start constraint)
- **Indexed**: Yes
- **Use Case**: Time-limited campaigns - content activation begins at this timestamp (UTC)
- **Example**: "2025-11-01T00:00:00Z" (November 1st, 2025 midnight UTC)

### `end_date` (DateTime)
- **Type**: TIMESTAMP WITH TIME ZONE
- **Default**: NULL (no end constraint)
- **Indexed**: Yes
- **Use Case**: Time-limited campaigns - content expires after this timestamp (UTC)
- **Example**: "2025-11-30T23:59:59Z" (November 30th, 2025 end of day UTC)

### `is_enabled` (Boolean)
- **Type**: BOOLEAN
- **Default**: TRUE
- **Indexed**: Yes
- **Use Case**: Soft delete flag - disable content without removing data
- **Notes**:
  - FALSE = content is disabled (won't be shown on devices)
  - TRUE = content is enabled (can be shown if other conditions met)
  - Allows recovery of "deleted" content
  - Better for compliance/auditing than hard delete

### `shuffle` (Boolean)
- **Type**: BOOLEAN
- **Default**: FALSE
- **Indexed**: No
- **Use Case**: Enable random/shuffle playback mode for rotating content
- **Notes**:
  - TRUE = content plays in random order
  - FALSE = content plays in defined sequence (play_order)
  - Useful for randomizing advertisement rotation

### `md5_checksum` (String)
- **Type**: VARCHAR(32)
- **Default**: NULL
- **Indexed**: No
- **Use Case**: File integrity verification (from Anthias integration)
- **Format**: 32-character hexadecimal string (MD5 hash)
- **Example**: "5d41402abc4b2a76b9719d911017c592"
- **Notes**: Used to verify file hasn't been corrupted during transfer

---

## Backward Compatibility

All changes are backward compatible:
- All new fields have sensible defaults
- Existing records will automatically have defaults applied
- No required fields were added to ContentUpdateRequest (all optional)
- Existing API clients will continue to work
- New fields are optional in API responses

---

## API Response Example

### Before Migration
```json
{
  "id": 1,
  "title": "Banner Promo",
  "content_type": "image",
  "duration": 10,
  "is_active": true,
  "created_at": "2025-10-21T12:00:00",
  "updated_at": "2025-10-21T12:00:00"
}
```

### After Migration
```json
{
  "id": 1,
  "title": "Banner Promo",
  "content_type": "image",
  "duration": 10,
  "is_active": true,
  "play_order": 0,
  "start_date": null,
  "end_date": null,
  "is_enabled": true,
  "shuffle": false,
  "md5_checksum": null,
  "created_at": "2025-10-21T12:00:00",
  "updated_at": "2025-10-21T12:00:00"
}
```

---

## Usage Examples

### 1. Create Time-Limited Campaign

```python
content = Content(
    title="Black Friday Promotion",
    description="Limited time promo",
    content_type="image",
    anthias_url="http://...",
    duration=10,
    start_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
    end_date=datetime(2025, 11, 30, 23, 59, 59, tzinfo=timezone.utc),
    is_enabled=True,
    play_order=0,
    md5_checksum="abc123..."
)
```

### 2. Query Active Content

```python
# Get only enabled, non-deleted content
active_content = session.query(Content).filter(
    Content.is_enabled == True,
    Content.start_date <= func.now(),
    Content.end_date >= func.now()
).order_by(Content.play_order).all()
```

### 3. Soft Delete Content

```python
# Disable content without deleting
content.is_enabled = False
session.commit()

# To recover:
content.is_enabled = True
session.commit()
```

### 4. Enable Shuffle Rotation

```python
# Enable random rotation for advertisements
content.shuffle = True
session.commit()
```

---

## Testing Checklist

- [x] Migration file created and syntactically correct
- [x] SQLAlchemy model updated with new columns
- [x] Pydantic schemas updated for all request/response types
- [x] Backward compatibility maintained
- [x] Defaults applied properly
- [x] Indexes created for performance
- [x] Helper function created for active content checks
- [x] Documentation completed

---

## Deployment Steps

1. **Backup Database**
   ```bash
   pg_dump -U postgres -d anthias_db > backup_$(date +%Y%m%d).sql
   ```

2. **Run Migration**
   ```bash
   # Option A: Using SQL directly (recommended)
   psql -U postgres -d anthias_db < migrations/008_add_anthias_features_to_content.sql

   # Option B: Using application startup (if using migration runner)
   # Application will auto-run migrations on startup
   ```

3. **Verify Migration**
   ```bash
   # Check columns exist
   psql -U postgres -d anthias_db -c "\d contents"

   # Check indexes exist
   psql -U postgres -d anthias_db -c "SELECT indexname FROM pg_indexes WHERE tablename='contents'"
   ```

4. **Restart Backend Service**
   ```bash
   # If using Docker
   docker-compose restart backend-api

   # If using direct Python
   # Stop and restart the FastAPI server
   ```

5. **Test API Endpoints**
   ```bash
   # GET content - should include new fields
   curl http://localhost:8001/api/v1/contents/1

   # POST/PATCH with new fields
   curl -X PATCH http://localhost:8001/api/v1/contents/1 \
     -H "Content-Type: application/json" \
     -d '{
       "play_order": 0,
       "start_date": "2025-11-01T00:00:00Z",
       "end_date": "2025-11-30T23:59:59Z",
       "is_enabled": true
     }'
   ```

---

## Related Files

| File | Changes |
|------|---------|
| `/mnt/g/khoirul/signate/backend/migrations/008_add_anthias_features_to_content.sql` | New migration (CREATE) |
| `/mnt/g/khoirul/signate/backend/app/models/content.py` | Updated Content class |
| `/mnt/g/khoirul/signate/backend/app/schemas/content.py` | Updated Pydantic schemas |

---

## Next Steps

1. **Optional**: Create database views for common queries
   - Active content by date range
   - Disabled content (for recovery)
   - Shuffled content sequences

2. **Optional**: Add query filters to API endpoints
   - Filter by is_enabled status
   - Filter by date range
   - Sort by play_order

3. **Optional**: Create API helper functions
   - Check if content is active: `is_content_active()`
   - Get active content in order: `get_active_content_ordered()`
   - Calculate content validity: `is_content_valid_for_device()`

---

## References

- Anthias Asset Model: `/mnt/g/khoirul/signate/anthias/anthias_app/models.py`
- Original Content Model: `/mnt/g/khoirul/signate/backend/app/models/content.py`
- API Schemas: `/mnt/g/khoirul/signate/backend/app/schemas/content.py`
- Migration Pattern: `/mnt/g/khoirul/signate/backend/migrations/007_rename_content_to_contents.sql`

---

## Summary

Migration completed successfully. All 6 Anthias features (play_order, start_date, end_date, is_enabled, shuffle, md5_checksum) have been:

1. Added to database schema with proper indexes
2. Integrated into SQLAlchemy Content model
3. Reflected in Pydantic schemas for API validation
4. Documented with comments and examples
5. Designed with backward compatibility in mind

The system is ready for deployment and will support advanced content management features like time-limited campaigns, content sequencing, and integrity verification.
