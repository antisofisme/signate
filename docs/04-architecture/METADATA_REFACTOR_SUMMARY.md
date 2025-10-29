# Metadata Refactor: Quick Summary

## Problem
- PostgreSQL and Anthias store overlapping metadata: name, duration, mimetype, is_enabled
- Updating content in web-admin doesn't sync to Anthias (stale assets)
- Every playlist request fetches asset metadata from Anthias (130ms latency)
- Unnecessary architectural coupling

## Solution
Make Anthias pure file storage (like S3). PostgreSQL is single source of truth.

## Changes

### Stop Sending These Fields to Anthias
| Field | Move To PostgreSQL | Impact |
|-------|-------------------|--------|
| `name` | `title` | Already done |
| `duration` | `duration` | Already done |
| `mimetype` | `mime_type` | Already done |
| `is_enabled` | `is_active` | Already done |

### Minimal Anthias Data (File Storage Only)
- **Keep:** `uri` (file path), `asset_id` (UUID)
- **Remove:** metadata sync from AnthiasService

### Code Changes Required
1. **Model:** Add `anthias_file_uri` column (cache URI from upload)
2. **Upload:** Stop sending name/duration/is_enabled to Anthias
3. **Playlist:** Use cached URI instead of Anthias API call (-130ms)
4. **Updates:** Only update PostgreSQL, not Anthias metadata

## By The Numbers

| Metric | Current | After |
|--------|---------|-------|
| Fields sent to Anthias | 5 | 2 |
| Playlist fetch time | 250ms+ | ~120ms |
| Sync points | Multiple | Single (PostgreSQL) |
| Data consistency | Eventual | Immediate |
| Anthias coupling | Tight | Loose |

## Migration Effort
- **Coding:** 8 hours
- **Testing:** 3 hours
- **Backfill:** 1 hour
- **Total:** ~12 hours (1.5 days)

## Files Affected
```
backend/app/models/content.py          (+1 field)
backend/app/services/anthias_service.py (simplify upload)
backend/app/api/content.py             (remove sync)
backend/app/api/client.py              (use cache)
backend/app/schemas/content.py         (update responses)
Database migration                      (add column)
```

## Breaking Changes
- **None** - purely internal optimization

## Benefits
✓ Eliminate redundant Anthias API calls (-130ms per request)
✓ Single source of truth (PostgreSQL)
✓ Simpler service design (Anthias = file storage)
✓ Better consistency (no stale metadata)
✓ Easier maintenance (fewer sync points)

## Risk Level
**Low** - URI caching is safe, optional, testable independently
