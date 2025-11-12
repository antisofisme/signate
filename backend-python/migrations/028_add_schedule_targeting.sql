-- Add targeting fields to schedules table
-- Allows schedules to target specific devices, tags, or all devices

ALTER TABLE schedules 
    ADD COLUMN IF NOT EXISTS device_ids JSONB,
    ADD COLUMN IF NOT EXISTS tag_ids JSONB,
    ADD COLUMN IF NOT EXISTS apply_to_all BOOLEAN DEFAULT FALSE;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_schedules_device_ids ON schedules USING GIN(device_ids);
CREATE INDEX IF NOT EXISTS idx_schedules_tag_ids ON schedules USING GIN(tag_ids);
CREATE INDEX IF NOT EXISTS idx_schedules_apply_to_all ON schedules(apply_to_all) WHERE apply_to_all = TRUE;

-- Add comments
COMMENT ON COLUMN schedules.device_ids IS 'Array of device IDs this schedule applies to';
COMMENT ON COLUMN schedules.tag_ids IS 'Array of tag IDs - schedule applies to devices with these tags';
COMMENT ON COLUMN schedules.apply_to_all IS 'If true, schedule applies to all devices in organization';
