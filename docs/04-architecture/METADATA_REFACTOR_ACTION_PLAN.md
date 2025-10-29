# Metadata Refactor: Detailed Action Plan

## Objectives
1. Eliminate 4-field metadata duplication between PostgreSQL and Anthias
2. Make Anthias pure file storage (like S3)
3. Reduce playlist generation latency by ~130ms
4. Establish PostgreSQL as single source of truth

## Phase 1: URI Caching (Backward Compatible) - 5 Hours

### 1.1 Create Database Migration (0.5h)
```bash
File: backend/alembic/versions/add_anthias_file_uri_column.py

CREATE TABLE migration:
- Add column: anthias_file_uri VARCHAR(500)
- Create index: idx_anthias_file_uri
- Make nullable for backward compatibility
```

### 1.2 Update Content Model (0.5h)
```python
File: backend/app/models/content.py

Add field:
    anthias_file_uri = Column(String(500), nullable=True)

Update __repr__ and to_dict():
    Include anthias_file_uri in responses
```

### 1.3 Update Upload Flow (1h)
```python
File: backend/app/api/content.py:113-141 (upload_content endpoint)

After upload_asset() call:
    1. Extract uri from anthias_asset response
    2. Save to content.anthias_file_uri
    3. Test: verify uri is stored before commit
```

### 1.4 Update Schemas (0.5h)
```python
File: backend/app/schemas/content.py

Update ContentResponse:
    Add field: anthias_file_uri: Optional[str]

Update ContentUploadResponse:
    Include anthias_file_uri in response
```

### 1.5 Create Backfill Script (1h)
```python
File: backend/scripts/migrate_anthias_uris.py

for content in db.query(Content).filter(Content.anthias_file_uri.is_(None)).all():
    try:
        asset = await anthias_service.get_asset(content.anthias_asset_id)
        content.anthias_file_uri = asset.get('uri')
        db.commit()
        print(f"Migrated content {content.id}")
    except Exception as e:
        print(f"Failed to migrate {content.id}: {e}")
        db.rollback()
```

### 1.6 Test Phase 1 (1.5h)
- [x] Unit test: Content model stores uri
- [x] Integration test: Upload stores uri
- [x] Integration test: Existing content can be queried
- [x] Script test: Backfill works on small dataset

---

## Phase 2: Optimize Playlist Generation (2 Hours)

### 2.1 Refactor Playlist Endpoint (2h)
```python
File: backend/app/api/client.py:131-188 (get_device_playlist)

BEFORE:
- For each content:
  1. Get content.anthias_asset_id
  2. Call anthias_service.get_asset() → Anthias API (130ms)
  3. Extract uri from response
  4. Convert to URL

AFTER:
- For each content:
  1. Get content.anthias_file_uri (cached)
  2. Skip Anthias API call
  3. Convert cached uri to URL directly

Code changes:
```python
# OLD CODE (lines 131-177)
anthias_asset_url = f"{settings.ANTHIAS_API_URL}/api/v1/assets/{content.anthias_asset_id}"
response = client.get(anthias_asset_url)  # REMOVE THIS
asset_data = response.json()
asset_uri = asset_data.get('uri')

# NEW CODE
asset_uri = content.anthias_file_uri  # Use cache

# If uri is None (pre-migration content):
if not asset_uri:
    # Fallback: fetch from Anthias
    asset = await anthias_service.get_asset(content.anthias_asset_id)
    asset_uri = asset.get('uri')
```

### 2.2 Test Phase 2 (included above)
- [x] Unit test: Cache used instead of API call
- [x] Performance test: Measure latency improvement
- [x] Fallback test: Works if uri is None

---

## Phase 3: Update Content CRUD (Remove Metadata Sync) - 3 Hours

### 3.1 Update PUT/PATCH Endpoints (1.5h)
```python
File: backend/app/api/content.py (all CRUD endpoints)

Endpoints affected:
- PATCH /api/contents/{id} (update content)
- DELETE /api/contents/{id} (delete content)
- PUT /api/contents/{id} (replace content)

For UPDATE operations:
- Update PostgreSQL fields
- DO NOT sync to Anthias
- Logging: note that Anthias metadata not updated

Example:
    # OLD: await anthias_service.update_asset(...)
    # NEW: [REMOVE THIS BLOCK]

For DELETE operations:
- Keep deleting from Anthias (to cleanup files)
- This is correct
```

### 3.2 Simplify AnthiasService (1.5h)
```python
File: backend/app/services/anthias_service.py

1. update_asset() method:
   - Remove name, duration, is_enabled parameters
   - Method becomes unused (optional: deprecate with warning)

2. upload_asset() method:
   - Remove name, duration, is_enabled parameters
   - ONLY take file + optional asset_id
   - Return uri in response
   - Simplify from 100+ lines to ~50 lines

3. Documentation:
   - Update docstrings: "Anthias is file storage only"
   - Note: metadata managed in PostgreSQL
```

---

## Phase 4: Data Migration (1 Hour)

### 4.1 Backfill Existing Content (0.5h)
```bash
# Run script to populate anthias_file_uri for all existing content
python backend/scripts/migrate_anthias_uris.py --dry-run
# Verify: all contents have uri populated

python backend/scripts/migrate_anthias_uris.py --execute
# Backfill complete
```

### 4.2 Verify Migration (0.5h)
```sql
-- Verify all content has uri
SELECT COUNT(*) as with_uri FROM contents WHERE anthias_file_uri IS NOT NULL;
SELECT COUNT(*) as without_uri FROM contents WHERE anthias_file_uri IS NULL;
-- Should have: with_uri = total, without_uri = 0
```

---

## Phase 5: Testing (3 Hours)

### 5.1 Unit Tests (1h)
```python
File: backend/tests/test_content_model.py

- test_content_with_uri_cache
- test_uri_extraction_from_upload
- test_playlist_uses_cached_uri
```

### 5.2 Integration Tests (1h)
```python
File: backend/tests/test_content_api.py

- test_upload_stores_uri
- test_playlist_generation_uses_cache
- test_content_update_without_anthias_sync
- test_delete_removes_from_anthias
- test_fallback_if_uri_none
```

### 5.3 Performance Tests (1h)
```python
File: backend/tests/test_performance.py

- Measure playlist endpoint latency (before/after)
- Measure Anthias API call count
- Benchmark: should be -130ms per request, ~90%+ fewer API calls
```

---

## Phase 6: Documentation (1 Hour)

### 6.1 Update Architecture Docs
```markdown
File: backend/ARCHITECTURE.md

Section: Metadata Management
- Explain: PostgreSQL as source of truth
- Explain: Anthias as file storage only
- Note: URI caching for performance
- Note: No metadata sync needed
```

### 6.2 Update API Documentation
```markdown
File: backend/API_DOCUMENTATION.md

Content Upload Endpoint:
- Note: uri stored in PostgreSQL after upload
- Update: removed metadata sync to Anthias

Content Update Endpoint:
- Note: updates PostgreSQL metadata only
- Note: Anthias files unchanged
```

### 6.3 Create Runbook
```markdown
File: backend/RUNBOOKS.md

Section: Metadata Refactoring Runbook
1. Pre-checks: verify DB migration applied
2. Backfill: run migration script
3. Verify: check row counts
4. Deploy: push new code
5. Monitor: watch playlist latency metrics
```

---

## Implementation Timeline

| Phase | Duration | Start | End | Status |
|-------|----------|-------|-----|--------|
| Phase 1: URI Caching | 5h | Day 1 | Day 1 | Pending |
| Phase 2: Optimize Playlist | 2h | Day 1 | Day 1 | Pending |
| Phase 3: Update CRUD | 3h | Day 2 | Day 2 | Pending |
| Phase 4: Data Migration | 1h | Day 2 | Day 2 | Pending |
| Phase 5: Testing | 3h | Day 2 | Day 3 | Pending |
| Phase 6: Documentation | 1h | Day 3 | Day 3 | Pending |
| **Total** | **15h** | - | - | Pending |

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Code review approved
- [ ] Database migration tested on staging
- [ ] Performance improvement verified
- [ ] Rollback plan documented

### Deployment Steps
```bash
# 1. Deploy code (both frontend + backend)
git push origin feature/metadata-refactor

# 2. Apply migration in production
alembic upgrade head

# 3. Run backfill script
python backend/scripts/migrate_anthias_uris.py --execute

# 4. Verify migration complete
python backend/scripts/verify_migration.py

# 5. Monitor metrics
# - Watch: /metrics/api/playlist/latency
# - Watch: /metrics/anthias/api_calls
# - Expected: -130ms latency, -95% API calls

# 6. If issues: Rollback (no data loss, field is optional)
git revert HEAD
```

### Post-Deployment Monitoring
- Playlist latency metrics
- Error rates in playlist endpoint
- Anthias API call count
- Cache hit rate for uri field

---

## Risk Mitigation

### Risk: Migration doesn't populate all URIs
**Mitigation:**
- Dry-run backfill script first
- Verify count of populated uris
- Fallback code handles None uri gracefully

### Risk: Playlist endpoint breaks during transition
**Mitigation:**
- Cache is optional (nullable field)
- Fallback logic fetches from Anthias if cache empty
- Zero downtime deployment

### Risk: Inconsistency during transition
**Mitigation:**
- All reads use PostgreSQL after Phase 2
- Anthias metadata becomes unused (not a problem)
- No data loss

---

## Success Criteria

1. **Performance:** Playlist latency reduced by ~130ms (-33%)
2. **Consistency:** All updates immediate (no async sync)
3. **Reliability:** Fewer external dependencies
4. **Code Quality:** Simpler AnthiasService, clearer architecture
5. **Data:** Zero data loss, backward compatible

---

## Rollback Plan (if needed)

### Option 1: Keep Running (Recommended)
- No rollback needed
- Cache field is optional
- Code gracefully handles None uri

### Option 2: Full Rollback
```bash
# Revert code
git revert HEAD

# Keep database schema (no harm)
# anthias_file_uri column unused but present

# Playlist endpoint falls back to Anthias calls
# Performance returns to baseline
```

---

## Notes for Implementation Team

1. **Start with Phase 1** - low risk, immediate benefits
2. **Test thoroughly** - especially fallback paths
3. **Monitor metrics** - verify latency improvement
4. **Document well** - architecture is clearer after this
5. **Gradual rollout** - deploy to staging first
