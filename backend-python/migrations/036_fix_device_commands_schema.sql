-- Fix device_commands table schema
-- Add missing columns for enhanced command tracking

ALTER TABLE device_commands
    ADD COLUMN IF NOT EXISTS command_data JSONB,
    ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 5,
    ADD COLUMN IF NOT EXISTS failed_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS result JSONB,
    ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_device_commands_priority ON device_commands(priority);
CREATE INDEX IF NOT EXISTS idx_device_commands_retry ON device_commands(retry_count) WHERE retry_count > 0;

-- Add comments
COMMENT ON COLUMN device_commands.command_data IS 'Structured command data (JSON)';
COMMENT ON COLUMN device_commands.priority IS 'Command priority (1-10, higher = more urgent)';
COMMENT ON COLUMN device_commands.failed_at IS 'Timestamp when command failed';
COMMENT ON COLUMN device_commands.result IS 'Command execution result (JSON)';
COMMENT ON COLUMN device_commands.retry_count IS 'Number of retry attempts';
COMMENT ON COLUMN device_commands.max_retries IS 'Maximum number of retries allowed';
