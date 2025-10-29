-- Migration: Add URI caching to contents table
-- Phase: Metadata Refactor Phase 1
-- Purpose: Cache anthias_file_uri in PostgreSQL to avoid API calls on every request
-- Author: Backend System Architect
-- Date: 2025-10-29
--
-- BREAKING CHANGES:
-- - None (backward compatible - adds new nullable column)
--
-- DEPLOYMENT NOTES:
-- 1. Run this migration before deploying new backend code
-- 2. After migration, existing content will have NULL anthias_file_uri
-- 3. Next upload will populate the field automatically
-- 4. Optional: Run backfill script to populate existing records (see bottom)
--
-- PERFORMANCE IMPACT:
-- - Reduces 1 API call per content item on list/get operations
-- - Index on anthias_file_uri enables fast lookups
-- - No impact on existing queries

-- ============================================================================
-- UP MIGRATION
-- ============================================================================

-- Step 1: Add anthias_file_uri column to contents table
-- This will store the full file URI from Anthias (e.g., "/data/screenly_assets/abc123.jpg")
ALTER TABLE contents
ADD COLUMN anthias_file_uri VARCHAR(500) NULL;

-- Step 2: Add index for fast lookups by URI
-- Useful for reverse lookups (finding content by URI)
CREATE INDEX idx_contents_anthias_file_uri
ON contents(anthias_file_uri)
WHERE anthias_file_uri IS NOT NULL;

-- Step 3: Add comment for documentation
COMMENT ON COLUMN contents.anthias_file_uri IS
'Cached file URI from Anthias API (e.g., /data/screenly_assets/abc123.jpg).
Used to construct anthias_url without API calls.
Populated automatically on upload. NULL for legacy content uploaded before this migration.';

-- Step 4: Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 014_add_uri_caching completed successfully';
    RAISE NOTICE 'New column: contents.anthias_file_uri (VARCHAR(500), NULL)';
    RAISE NOTICE 'New index: idx_contents_anthias_file_uri';
    RAISE NOTICE 'Backward compatible: Existing content will have NULL anthias_file_uri';
END $$;


-- ============================================================================
-- DOWN MIGRATION (ROLLBACK)
-- ============================================================================

-- Uncomment below to rollback (remove in reverse order)

/*
-- Step 1: Drop index
DROP INDEX IF EXISTS idx_contents_anthias_file_uri;

-- Step 2: Drop column
ALTER TABLE contents
DROP COLUMN IF EXISTS anthias_file_uri;

-- Step 3: Log rollback completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 014_add_uri_caching rolled back successfully';
    RAISE NOTICE 'Removed: contents.anthias_file_uri column';
    RAISE NOTICE 'Removed: idx_contents_anthias_file_uri index';
END $$;
*/


-- ============================================================================
-- OPTIONAL: BACKFILL SCRIPT FOR EXISTING CONTENT
-- ============================================================================

-- This script populates anthias_file_uri for existing content
-- Run this AFTER deploying new backend code (optional)
--
-- IMPORTANT: This requires Anthias API to be available
-- The backend service will need to:
-- 1. Query all content with NULL anthias_file_uri
-- 2. Call anthias_service.get_asset(asset_id) for each
-- 3. Extract 'uri' field from response
-- 4. Update contents.anthias_file_uri
--
-- Example Python backfill script (run via FastAPI endpoint or management command):
/*
from app.core.database import SessionLocal
from app.models.content import Content
from app.services.anthias_service import anthias_service
import asyncio

async def backfill_uri_cache():
    db = SessionLocal()
    try:
        # Get all content with NULL anthias_file_uri
        contents = db.query(Content).filter(
            Content.anthias_file_uri.is_(None),
            Content.anthias_asset_id.isnot(None)
        ).all()

        print(f"Backfilling {len(contents)} content records...")

        for content in contents:
            try:
                # Fetch asset details from Anthias
                asset = await anthias_service.get_asset(content.anthias_asset_id)
                uri = asset.get('uri')

                if uri:
                    content.anthias_file_uri = uri
                    print(f"✓ Content {content.id}: {uri}")
                else:
                    print(f"✗ Content {content.id}: No URI found")
            except Exception as e:
                print(f"✗ Content {content.id}: Error - {e}")

        db.commit()
        print(f"Backfill completed: {len(contents)} records processed")
    finally:
        db.close()

# Run: asyncio.run(backfill_uri_cache())
*/


-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check if migration was applied
SELECT
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'contents'
AND column_name = 'anthias_file_uri';

-- Check if index was created
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'contents'
AND indexname = 'idx_contents_anthias_file_uri';

-- Count content with cached URIs vs without
SELECT
    COUNT(*) FILTER (WHERE anthias_file_uri IS NOT NULL) AS with_uri_cache,
    COUNT(*) FILTER (WHERE anthias_file_uri IS NULL) AS without_uri_cache,
    COUNT(*) AS total_content
FROM contents;

-- Sample content records showing new field
SELECT
    id,
    title,
    anthias_asset_id,
    anthias_url,
    anthias_file_uri,
    created_at
FROM contents
ORDER BY created_at DESC
LIMIT 5;


-- ============================================================================
-- MIGRATION METADATA
-- ============================================================================

-- Migration: 014_add_uri_caching.sql
-- Phase: Metadata Refactor Phase 1
-- Dependencies: 013_add_analytics_system.sql
-- Rollback: See DOWN MIGRATION section above
-- Testing: Upload new content and verify anthias_file_uri is populated
-- Documentation: See METADATA_REFACTOR_ACTION_PLAN.md
