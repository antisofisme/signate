-- Migration: Change organization.organization_pin from 8 digits to 6 digits
-- Reason: Player hard reset will use 6-digit organization PIN instead of default admin123
-- Date: 2025-01-09

-- Step 1: Alter column type from VARCHAR(8) to VARCHAR(6)
ALTER TABLE organizations
ALTER COLUMN organization_pin TYPE VARCHAR(6);

-- Step 2: Update existing PINs from 8 digits to 6 digits (remove last 2 digits)
-- Example: '12345678' → '123456', '65432100' → '654321'
UPDATE organizations
SET organization_pin = SUBSTRING(organization_pin FROM 1 FOR 6)
WHERE organization_pin IS NOT NULL
  AND LENGTH(organization_pin) = 8;

-- Step 3: Verify the changes
SELECT id, name, organization_pin, LENGTH(organization_pin) AS pin_length
FROM organizations
WHERE organization_pin IS NOT NULL;

-- Step 4: Add comment
COMMENT ON COLUMN organizations.organization_pin IS 'Organization 6-digit PIN for device hard reset (optional)';
