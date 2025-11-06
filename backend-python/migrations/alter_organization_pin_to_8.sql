-- Step 1: Alter the column type from character(6) to character(8)
ALTER TABLE organizations
ALTER COLUMN organization_pin TYPE character(8);

-- Step 2: Update existing PINs from 6 digits to 8 digits
UPDATE organizations
SET organization_pin = '12345678'
WHERE organization_pin = '123456';

UPDATE organizations
SET organization_pin = '65432100'
WHERE organization_pin = '654321';

-- Step 3: Verify the changes
SELECT id, name, organization_pin, length(organization_pin) as pin_length FROM organizations;
