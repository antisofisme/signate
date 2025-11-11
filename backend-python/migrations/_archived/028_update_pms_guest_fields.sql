-- Migration: Update PMS Guest fields for template processing
-- Description: Add additional fields to pms_guests table for enhanced template variables

-- Add new fields to pms_guests table
ALTER TABLE pms_guests
ADD COLUMN IF NOT EXISTS title VARCHAR(50),
ADD COLUMN IF NOT EXISTS balance DECIMAL(10, 2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS loyalty_level VARCHAR(50),
ADD COLUMN IF NOT EXISTS language VARCHAR(10),
ADD COLUMN IF NOT EXISTS special_requests TEXT;

-- Add index for faster language-based queries
CREATE INDEX IF NOT EXISTS idx_pms_guests_language ON pms_guests(language);

-- Add index for loyalty level reporting
CREATE INDEX IF NOT EXISTS idx_pms_guests_loyalty ON pms_guests(loyalty_level);

-- Update column names to match API (if using different names)
-- Note: We're keeping the original column names but the API/model handles the mapping