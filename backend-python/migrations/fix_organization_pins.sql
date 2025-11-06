-- Fix Organization PINs: Change from 6 digits to 8 digits
-- 123456 → 12345678
-- 654321 → 65432100

UPDATE organizations
SET organization_pin = '12345678'
WHERE organization_pin = '123456';

UPDATE organizations
SET organization_pin = '65432100'
WHERE organization_pin = '654321';

-- Verify the changes
SELECT id, name, organization_pin FROM organizations;
