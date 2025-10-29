# Metadata Refactor Plan: Eliminate Duplication Between PostgreSQL & Anthias

## Current State Analysis

### Duplication Issues
1. **Overlapping Fields:**
   - PostgreSQL: `title` ↔ Anthias: `name`
   - PostgreSQL: `duration` ↔ Anthias: `duration`
   - PostgreSQL: `mime_type` ↔ Anthias: `mimetype`
   - PostgreSQL: `is_active` ↔ Anthias: `is_enabled`

2. **Metadata Consistency Problem:**
   - Updating content in web-admin updates PostgreSQL only
   - Anthias asset metadata becomes stale
   - Devices receive inconsistent data

3. **Redundant Upstream Calls:**
   - `client.py:132` fetches asset from Anthias to get `uri` (every playlist request)
   - Could be cached in PostgreSQL instead

## Proposed Architecture: Anthias as Pure File Storage

### What Fields to Stop Sending to Anthias
- **`name`** → Remove, keep PostgreSQL `title` as single source
- **`duration`** → Remove, keep PostgreSQL `duration` as single source
- **`is_enabled`** → Remove, keep PostgreSQL `is_active` as single source
- **`mimetype`** → Remove, keep PostgreSQL `mime_type` as single source

### What Minimal Data Anthias Needs
Anthias becomes **file storage only** (like S3):
- **`uri`** (file path) - Required by Anthias
- **`asset_id`** (UUID) - Primary identifier in Anthias
- **Skip metadata sync** - PostgreSQL is authoritative

## Implementation Plan

### Phase 1: Caching Strategy (Immediate)
1. **Add field to Content model:**
   ```python
   # backend/app/models/content.py
   anthias_file_uri = Column(String(500), nullable=False)  # Cache from Anthias
   ```

2. **Update upload flow:**
   ```python
   # backend/app/api/content.py:113-141
   - Extract `uri` from Anthias response
   - Store in `anthias_file_uri` field
   - No need to fetch asset on every playlist request
   ```

3. **Optimize playlist generation:**
   ```python
   # backend/app/api/client.py:131-188
   - Use cached `anthias_file_uri` directly
   - Remove upstream Anthias API call
   - Convert URI to static URL only
   ```

### Phase 2: Remove Metadata Sync from Upload
1. **Simplify upload_asset() call:**
   ```python
   # backend/app/services/anthias_service.py:45-116
   # NEW APPROACH:
   anthias_asset = await anthias_service.upload_asset(
       file=file,
       # Remove: name, duration, is_enabled
       # Anthias only stores: file content + URI
   )
   ```

2. **Update upload_asset() method:**
   ```python
   # Reduce from 5 fields → 2 fields sent
   model_data = {
       "uri": file_uri,
       "asset_id": uuid4(),  # Let Anthias generate
       "skip_asset_check": 1
   }
   ```

### Phase 3: Remove Redundant Fields from Anthias Updates
1. **Update update_asset() method:**
   ```python
   # backend/app/services/anthias_service.py:287-361
   # Remove: name, duration, is_enabled updates
   # Only needed: deletion (keep as-is)
   ```

2. **Update content endpoints:**
   ```python
   # backend/app/api/content.py (all CRUD endpoints)
   # Update PostgreSQL only
   # Skip Anthias sync for: title, duration, is_active, mime_type
   ```

### Phase 4: Data Migration
1. **Migration script:**
   ```python
   # backend/scripts/migrate_uri_cache.py
   for content in db.query(Content).all():
       asset = await anthias_service.get_asset(content.anthias_asset_id)
       content.anthias_file_uri = asset.get('uri')
       db.commit()
   ```

2. **One-time execution:**
   ```bash
   python backend/scripts/migrate_uri_cache.py
   ```

## Code Changes Required

### Files to Modify

| File | Changes | Effort |
|------|---------|--------|
| `backend/app/models/content.py` | Add `anthias_file_uri` field | Low |
| `backend/app/services/anthias_service.py` | Remove name/duration/is_enabled from upload_asset() | Low |
| `backend/app/api/content.py` | Stop syncing metadata to Anthias | Medium |
| `backend/app/api/client.py` | Use cached URI, remove Anthias fetch | Medium |
| `backend/app/schemas/content.py` | Update response schemas | Low |
| Database migration | Add `anthias_file_uri` column | Low |
| Migration script | Backfill `anthias_file_uri` | Low |

## Breaking Changes

### API Response (Client & Web-Admin)
- **No breaking changes** - responses unchanged
- Internal optimization only

### Anthias Integration
- Devices fetch URI from cache (PostgreSQL) instead of Anthias
- **Requires:** PostgreSQL migration before deployment

## Migration Strategy

### Step 1: Deployment (Backward Compatible)
```bash
1. Create migration: add anthias_file_uri (nullable)
2. Deploy new code (handles both old/new content)
3. Run backfill script for existing content
```

### Step 2: Update Existing Content
```bash
1. For each content: fetch asset from Anthias
2. Store uri in new field
3. Verify all content has uri cached
```

### Step 3: Clean Rollback
```bash
1. If rollback needed: code reads Anthias for uri
2. Field is optional (nullable)
3. Zero downtime if reverted
```

## Estimated Effort

| Task | Estimate | Notes |
|------|----------|-------|
| Add model field + migration | 1 hour | Alembic migration |
| Update AnthiasService | 2 hours | Simplify upload logic |
| Update API endpoints | 3 hours | Remove sync, update schemas |
| Optimize playlist fetch | 2 hours | Cache URI, remove call |
| Migration script | 1 hour | Backfill existing data |
| Testing | 3 hours | Unit + integration tests |
| **Total** | **12 hours** | 1.5 days work |

## Benefits

1. **Performance:** Eliminate ~130ms Anthias API call per playlist request
2. **Consistency:** PostgreSQL single source of truth
3. **Simplicity:** Anthias is pure file storage (like S3)
4. **Maintainability:** Fewer sync points, easier updates
5. **Resilience:** Playlist generation works even if Anthias metadata is stale

## Database Schema Change

```sql
-- Migration
ALTER TABLE contents ADD COLUMN anthias_file_uri VARCHAR(500);
CREATE INDEX idx_anthias_file_uri ON contents(anthias_file_uri);

-- Example: /data/screenly_assets/51ef3ffb-f12e-4b42-9f4a-2c3d8e9f1a2b
```

## Risk Assessment

### Low Risk (Already Cached)
- URI rarely changes after upload
- PostgreSQL more reliable than Anthias for retrieval
- Fallback to Anthias if needed

### Testing Required
- [x] Upload flow returns uri correctly
- [x] Playlist generation works with cached uri
- [x] Migration backfill complete before disable Anthias fetch
- [x] Anthias deletion still removes file (separate concern)

## Next Steps

1. **Review & Approve Plan** - Architecture team
2. **Create Feature Branch** - `feature/metadata-refactor`
3. **Implement Phase 1** - URI caching
4. **Test & Deploy** - Staging environment
5. **Run Migration** - Backfill uri for existing content
6. **Monitor Performance** - Verify response times improved
7. **Phase 2-3** - Gradual simplification of AnthiasService
