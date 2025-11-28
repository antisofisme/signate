-- Migration 054: Add 'released' status to devices table
-- Created: 2025-11-28
-- Description: Add 'released' status for devices that are deleted from device list
--              but still belong to their organization (Unsigned Pool)

BEGIN;

-- ============================================================================
-- 1. UPDATE STATUS CONSTRAINT
-- ============================================================================
-- Drop existing constraint and add new one with 'released' status

ALTER TABLE devices DROP CONSTRAINT IF EXISTS devices_status_check;

ALTER TABLE devices ADD CONSTRAINT devices_status_check
    CHECK (status IN ('pending', 'active', 'inactive', 'released'));

-- ============================================================================
-- 2. UPDATE COMMENTS
-- ============================================================================

COMMENT ON COLUMN devices.status IS
    'Device status: pending (new device awaiting activation), active (operational), inactive (not playing content), released (deleted from device list - shows in Unsigned Pool)';

COMMENT ON COLUMN devices.released_at IS
    'Timestamp when device was released/moved to Unsigned Pool';

-- ============================================================================
-- STATUS DEFINITIONS:
-- ============================================================================
-- pending   = Player baru request kode, belum di-assign ke organization
--             organization_id = NULL
--             TIDAK muncul di CMS manapun
--
-- active    = Device aktif dan ter-assign ke organization
--             organization_id = org yang assign
--             Muncul di Device List
--
-- inactive  = Device tidak sedang play content (tapi masih aktif)
--             organization_id = org yang assign
--             Muncul di Device List
--
-- released  = Device di-delete dari Device List oleh admin
--             organization_id = TETAP (org yang sama)
--             Muncul di Unsigned Pool (hanya untuk org yang sama)
--             Bisa di-claim ulang dari Unsigned Pool
-- ============================================================================

COMMIT;
