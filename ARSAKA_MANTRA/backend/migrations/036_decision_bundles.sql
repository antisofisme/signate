-- Migration: 036_decision_bundles.sql
-- Purpose: Decision bundles for atomic retrieval
-- Groups of related decisions that are always retrieved together

-- ============================================================================
-- DECISION BUNDLES TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS decision_bundles (
    -- Primary key
    bundle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    code VARCHAR(50) NOT NULL UNIQUE,  -- BDL-REACT-001
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,

    -- Classification
    bundle_type VARCHAR(20) NOT NULL DEFAULT 'TOPIC' CHECK (bundle_type IN (
        'TOPIC',      -- Related by subject matter
        'WORKFLOW',   -- Sequential steps
        'CHECKLIST',  -- All-or-nothing
        'CONTEXT',    -- Context-specific
        'STARTER'     -- Onboarding
    )),

    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT' CHECK (status IN (
        'DRAFT',
        'ACTIVE',
        'DEPRECATED',
        'ARCHIVED'
    )),

    -- Matching
    scope_paths TEXT[] DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    trigger_keywords TEXT[] DEFAULT '{}',

    -- Versioning
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',

    -- Retrieval hints
    estimated_tokens INT DEFAULT 0,

    -- Audit
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT chk_bundle_code_format CHECK (code ~ '^BDL-[A-Z]+-[0-9]{3}$'),
    CONSTRAINT chk_bundle_name_length CHECK (char_length(name) >= 5),
    CONSTRAINT chk_bundle_desc_length CHECK (char_length(description) >= 20)
);

-- ============================================================================
-- BUNDLE MEMBERS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS bundle_members (
    -- Composite primary key
    bundle_id UUID NOT NULL REFERENCES decision_bundles(bundle_id) ON DELETE CASCADE,
    decision_id UUID NOT NULL,

    -- Role within bundle
    role VARCHAR(20) NOT NULL DEFAULT 'SUPPORTING' CHECK (role IN (
        'PRIMARY',     -- Core, always included
        'SUPPORTING',  -- Additional context
        'OPTIONAL',    -- Only if requested
        'REFERENCE'    -- Linked but not auto-included
    )),

    -- Ordering (for WORKFLOW bundles)
    sort_order INT NOT NULL DEFAULT 0,

    -- Notes
    notes TEXT,

    -- Audit
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    added_by TEXT,

    PRIMARY KEY (bundle_id, decision_id)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Bundle lookups
CREATE INDEX IF NOT EXISTS idx_bundles_code ON decision_bundles(code);
CREATE INDEX IF NOT EXISTS idx_bundles_status ON decision_bundles(status);
CREATE INDEX IF NOT EXISTS idx_bundles_type ON decision_bundles(bundle_type);

-- Scope/tag matching
CREATE INDEX IF NOT EXISTS idx_bundles_scope_paths ON decision_bundles USING GIN(scope_paths);
CREATE INDEX IF NOT EXISTS idx_bundles_tags ON decision_bundles USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_bundles_keywords ON decision_bundles USING GIN(trigger_keywords);

-- Member lookups
CREATE INDEX IF NOT EXISTS idx_bundle_members_decision ON bundle_members(decision_id);
CREATE INDEX IF NOT EXISTS idx_bundle_members_role ON bundle_members(bundle_id, role);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Bundle summary with member counts
CREATE OR REPLACE VIEW bundle_summary AS
SELECT
    b.bundle_id,
    b.code,
    b.name,
    b.bundle_type,
    b.status,
    b.estimated_tokens,
    COUNT(m.decision_id) as total_members,
    COUNT(m.decision_id) FILTER (WHERE m.role = 'PRIMARY') as primary_count,
    COUNT(m.decision_id) FILTER (WHERE m.role = 'SUPPORTING') as supporting_count,
    b.created_at,
    b.updated_at
FROM decision_bundles b
LEFT JOIN bundle_members m ON b.bundle_id = m.bundle_id
GROUP BY b.bundle_id;

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Get all decision IDs for a bundle
CREATE OR REPLACE FUNCTION get_bundle_decisions(
    p_bundle_code VARCHAR,
    p_include_optional BOOLEAN DEFAULT FALSE,
    p_include_reference BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
    decision_id UUID,
    role VARCHAR(20),
    sort_order INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT m.decision_id, m.role, m.sort_order
    FROM bundle_members m
    JOIN decision_bundles b ON m.bundle_id = b.bundle_id
    WHERE b.code = p_bundle_code
      AND b.status = 'ACTIVE'
      AND (
          m.role IN ('PRIMARY', 'SUPPORTING')
          OR (p_include_optional AND m.role = 'OPTIONAL')
          OR (p_include_reference AND m.role = 'REFERENCE')
      )
    ORDER BY m.sort_order;
END;
$$ LANGUAGE plpgsql;

-- Find bundles matching scope
CREATE OR REPLACE FUNCTION find_bundles_by_scope(
    p_scope_path TEXT,
    p_limit INT DEFAULT 10
)
RETURNS TABLE (
    bundle_id UUID,
    code VARCHAR,
    name VARCHAR,
    match_type TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.bundle_id,
        b.code,
        b.name,
        CASE
            WHEN p_scope_path = ANY(b.scope_paths) THEN 'EXACT'
            WHEN EXISTS (
                SELECT 1 FROM unnest(b.scope_paths) s
                WHERE p_scope_path LIKE s || '.%'
            ) THEN 'PARENT'
            ELSE 'MATCH'
        END as match_type
    FROM decision_bundles b
    WHERE b.status = 'ACTIVE'
      AND (
          p_scope_path = ANY(b.scope_paths)
          OR '*' = ANY(b.scope_paths)
          OR EXISTS (
              SELECT 1 FROM unnest(b.scope_paths) s
              WHERE p_scope_path LIKE s || '.%'
          )
      )
    ORDER BY
        CASE WHEN p_scope_path = ANY(b.scope_paths) THEN 0 ELSE 1 END,
        b.name
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGER: Update timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_bundle_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_bundle_updated
    BEFORE UPDATE ON decision_bundles
    FOR EACH ROW
    EXECUTE FUNCTION update_bundle_timestamp();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE decision_bundles IS
    'Groups of related decisions for atomic retrieval. '
    'When a bundle is requested, all PRIMARY and SUPPORTING members are returned together.';

COMMENT ON TABLE bundle_members IS
    'Membership of decisions in bundles with roles and ordering.';

COMMENT ON COLUMN bundle_members.role IS
    'PRIMARY: Core decision, always included. '
    'SUPPORTING: Additional context, included by default. '
    'OPTIONAL: Only included if explicitly requested. '
    'REFERENCE: Linked but not auto-included.';
