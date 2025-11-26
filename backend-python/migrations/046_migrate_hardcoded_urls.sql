-- Migration: 046
-- Description: Migrate hardcoded URLs to use PUBLIC_BASE_URL
-- Date: 2025-11-24
-- Purpose: Replace http://192.168.5.12:8001 with https://api.zhmhotels.online in database

BEGIN;

-- 1. Backup current state (optional - for rollback)
-- CREATE TABLE IF NOT EXISTS contents_url_backup AS
-- SELECT id, file_url, thumbnail_url, hls_master_playlist_url
-- FROM contents
-- WHERE file_url LIKE '%192.168.5.12:8001%'
--    OR thumbnail_url LIKE '%192.168.5.12:8001%'
--    OR hls_master_playlist_url LIKE '%192.168.5.12:8001%';

-- 2. Update file_url (content files)
UPDATE contents
SET file_url = REPLACE(file_url, 'http://192.168.5.12:8001', 'https://api.zhmhotels.online')
WHERE file_url LIKE '%http://192.168.5.12:8001%';

-- 3. Update thumbnail_url
UPDATE contents
SET thumbnail_url = REPLACE(thumbnail_url, 'http://192.168.5.12:8001', 'https://api.zhmhotels.online')
WHERE thumbnail_url LIKE '%http://192.168.5.12:8001%';

-- 4. Update hls_master_playlist_url (video streaming)
UPDATE contents
SET hls_master_playlist_url = REPLACE(hls_master_playlist_url, 'http://192.168.5.12:8001', 'https://api.zhmhotels.online')
WHERE hls_master_playlist_url LIKE '%http://192.168.5.12:8001%';

-- 5. Verify migration results
-- Show count of migrated records
DO $$
DECLARE
    file_url_count INTEGER;
    thumbnail_url_count INTEGER;
    hls_url_count INTEGER;
BEGIN
    -- Count updated file_urls
    SELECT COUNT(*) INTO file_url_count
    FROM contents
    WHERE file_url LIKE '%https://api.zhmhotels.online%';

    -- Count updated thumbnail_urls
    SELECT COUNT(*) INTO thumbnail_url_count
    FROM contents
    WHERE thumbnail_url LIKE '%https://api.zhmhotels.online%';

    -- Count updated hls_urls
    SELECT COUNT(*) INTO hls_url_count
    FROM contents
    WHERE hls_master_playlist_url LIKE '%https://api.zhmhotels.online%';

    RAISE NOTICE 'Migration completed:';
    RAISE NOTICE '  - file_url: % records migrated', file_url_count;
    RAISE NOTICE '  - thumbnail_url: % records migrated', thumbnail_url_count;
    RAISE NOTICE '  - hls_master_playlist_url: % records migrated', hls_url_count;
END $$;

-- 6. Verify no old URLs remain
DO $$
DECLARE
    remaining_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO remaining_count
    FROM contents
    WHERE file_url LIKE '%192.168.5.12:8001%'
       OR thumbnail_url LIKE '%192.168.5.12:8001%'
       OR hls_master_playlist_url LIKE '%192.168.5.12:8001%';

    IF remaining_count > 0 THEN
        RAISE WARNING 'Still % records with old URLs remaining!', remaining_count;
    ELSE
        RAISE NOTICE 'Success: No old URLs remaining in database';
    END IF;
END $$;

COMMIT;

-- Rollback script (if needed):
-- BEGIN;
-- UPDATE contents
-- SET file_url = REPLACE(file_url, 'https://api.zhmhotels.online', 'http://192.168.5.12:8001')
-- WHERE file_url LIKE '%https://api.zhmhotels.online%';
--
-- UPDATE contents
-- SET thumbnail_url = REPLACE(thumbnail_url, 'https://api.zhmhotels.online', 'http://192.168.5.12:8001')
-- WHERE thumbnail_url LIKE '%https://api.zhmhotels.online%';
--
-- UPDATE contents
-- SET hls_master_playlist_url = REPLACE(hls_master_playlist_url, 'https://api.zhmhotels.online', 'http://192.168.5.12:8001')
-- WHERE hls_master_playlist_url LIKE '%https://api.zhmhotels.online%';
-- COMMIT;
