-- Fix tags table for multi-tenant support
-- Add organization_id column if missing and update constraints

-- Add organization_id if not exists
ALTER TABLE tags
    ADD COLUMN IF NOT EXISTS organization_id INTEGER REFERENCES organizations(id);

-- Make priority NOT NULL if needed (migration 029 already added it)
ALTER TABLE tags
    ALTER COLUMN priority SET DEFAULT 50,
    ALTER COLUMN priority SET NOT NULL;

-- Drop old unique constraint on tag_name (if exists)
ALTER TABLE tags DROP CONSTRAINT IF EXISTS tags_tag_name_key;

-- Add unique constraint per organization (only if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'unique_tag_name_per_org'
    ) THEN
        ALTER TABLE tags ADD CONSTRAINT unique_tag_name_per_org UNIQUE (organization_id, tag_name);
    END IF;
END $$;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tags_organization ON tags(organization_id);
CREATE INDEX IF NOT EXISTS idx_tags_org_tagname_lookup ON tags(organization_id, tag_name);

-- Add comments
COMMENT ON COLUMN tags.organization_id IS 'Organization ID for multi-tenant isolation';
COMMENT ON CONSTRAINT unique_tag_name_per_org ON tags IS 'Tag names must be unique within an organization';
