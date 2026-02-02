-- Migration: 034_field_relations.sql
-- Purpose: Field-level relationships between decisions
-- Phase 2 of MANTRA implementation

-- ============================================================================
-- FIELD RELATIONS TABLE
-- ============================================================================
-- Stores relationships between individual fields across decisions.
-- Enables conflict detection, impact analysis, and traceability.

CREATE TABLE IF NOT EXISTS field_relations (
    -- Primary key
    relation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source (from)
    source_decision_id UUID NOT NULL,
    source_field_path TEXT NOT NULL,  -- e.g., "constraints[0].rule"

    -- Target (to)
    target_decision_id UUID NOT NULL,
    target_field_path TEXT NOT NULL,

    -- Relationship type
    relation_type VARCHAR(20) NOT NULL CHECK (relation_type IN (
        'CONFLICTS_WITH',  -- Directly contradicts
        'STRENGTHENS',     -- Makes stricter
        'WEAKENS',         -- Makes looser
        'IMPLEMENTS',      -- Specific implementation
        'ENFORCES',        -- Invariant guarantees constraint
        'REFERENCES'       -- Non-binding reference
    )),

    -- Confidence & source
    confidence VARCHAR(10) NOT NULL DEFAULT 'MEDIUM' CHECK (confidence IN (
        'CERTAIN',   -- Human verified
        'HIGH',      -- >80% confident
        'MEDIUM',    -- 50-80% confident
        'LOW'        -- <50%, needs review
    )),

    detection_source VARCHAR(15) NOT NULL DEFAULT 'RULE_BASED' CHECK (detection_source IN (
        'HUMAN',       -- Manually created
        'AI_DETECTED', -- AI detected
        'RULE_BASED'   -- Heuristic detection
    )),

    -- Description
    description TEXT,
    rationale TEXT,

    -- Similarity score for AI-detected (0.0 - 1.0)
    similarity_score FLOAT CHECK (similarity_score IS NULL OR (similarity_score >= 0 AND similarity_score <= 1)),

    -- Audit
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Verification
    verified_by TEXT,
    verified_at TIMESTAMPTZ,

    -- Prevent duplicate relations (same source-target-type)
    CONSTRAINT uq_field_relation UNIQUE (
        source_decision_id,
        source_field_path,
        target_decision_id,
        target_field_path,
        relation_type
    ),

    -- Prevent self-reference (same decision AND field)
    CONSTRAINT no_self_reference CHECK (
        NOT (source_decision_id = target_decision_id AND source_field_path = target_field_path)
    )
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Lookup by source decision
CREATE INDEX IF NOT EXISTS idx_field_rel_source_decision
    ON field_relations(source_decision_id);

-- Lookup by target decision
CREATE INDEX IF NOT EXISTS idx_field_rel_target_decision
    ON field_relations(target_decision_id);

-- Lookup by relation type (e.g., "get all conflicts")
CREATE INDEX IF NOT EXISTS idx_field_rel_type
    ON field_relations(relation_type);

-- Lookup by source field path
CREATE INDEX IF NOT EXISTS idx_field_rel_source_path
    ON field_relations(source_decision_id, source_field_path);

-- Lookup by target field path
CREATE INDEX IF NOT EXISTS idx_field_rel_target_path
    ON field_relations(target_decision_id, target_field_path);

-- Find unverified relations
CREATE INDEX IF NOT EXISTS idx_field_rel_unverified
    ON field_relations(verified_at) WHERE verified_at IS NULL;

-- Find conflicts specifically (common query)
CREATE INDEX IF NOT EXISTS idx_field_rel_conflicts
    ON field_relations(source_decision_id, target_decision_id)
    WHERE relation_type = 'CONFLICTS_WITH';

-- ============================================================================
-- VIEW: Conflict Summary
-- ============================================================================

CREATE OR REPLACE VIEW field_relation_conflicts AS
SELECT
    r.relation_id,
    r.source_decision_id,
    r.source_field_path,
    r.target_decision_id,
    r.target_field_path,
    r.confidence,
    r.detection_source,
    r.description,
    r.created_at,
    r.verified_at IS NOT NULL as is_verified,
    -- Join with decisions would go here if we had FK
    r.similarity_score
FROM field_relations r
WHERE r.relation_type = 'CONFLICTS_WITH'
ORDER BY
    r.confidence DESC,
    r.created_at DESC;

-- ============================================================================
-- VIEW: Relation Statistics
-- ============================================================================

CREATE OR REPLACE VIEW field_relation_stats AS
SELECT
    relation_type,
    COUNT(*) as total_count,
    COUNT(*) FILTER (WHERE verified_at IS NOT NULL) as verified_count,
    COUNT(*) FILTER (WHERE verified_at IS NULL) as unverified_count,
    AVG(similarity_score) FILTER (WHERE similarity_score IS NOT NULL) as avg_similarity,
    COUNT(DISTINCT source_decision_id) as source_decisions,
    COUNT(DISTINCT target_decision_id) as target_decisions
FROM field_relations
GROUP BY relation_type;

-- ============================================================================
-- FUNCTION: Find all relations for a decision
-- ============================================================================

CREATE OR REPLACE FUNCTION get_decision_relations(p_decision_id UUID)
RETURNS TABLE (
    relation_id UUID,
    direction TEXT,
    other_decision_id UUID,
    field_path TEXT,
    other_field_path TEXT,
    relation_type VARCHAR(20),
    confidence VARCHAR(10),
    is_verified BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    -- Outgoing relations (this decision is source)
    SELECT
        r.relation_id,
        'OUTGOING'::TEXT as direction,
        r.target_decision_id as other_decision_id,
        r.source_field_path as field_path,
        r.target_field_path as other_field_path,
        r.relation_type,
        r.confidence,
        r.verified_at IS NOT NULL as is_verified
    FROM field_relations r
    WHERE r.source_decision_id = p_decision_id

    UNION ALL

    -- Incoming relations (this decision is target)
    SELECT
        r.relation_id,
        'INCOMING'::TEXT as direction,
        r.source_decision_id as other_decision_id,
        r.target_field_path as field_path,
        r.source_field_path as other_field_path,
        r.relation_type,
        r.confidence,
        r.verified_at IS NOT NULL as is_verified
    FROM field_relations r
    WHERE r.target_decision_id = p_decision_id

    ORDER BY relation_type, is_verified DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNCTION: Find impact chain (what depends on a field)
-- ============================================================================

CREATE OR REPLACE FUNCTION get_field_impact_chain(
    p_decision_id UUID,
    p_field_path TEXT,
    p_max_depth INT DEFAULT 10
)
RETURNS TABLE (
    depth INT,
    relation_id UUID,
    affected_decision_id UUID,
    affected_field_path TEXT,
    relation_type VARCHAR(20)
) AS $$
WITH RECURSIVE impact_chain AS (
    -- Base case: direct relations from the field
    SELECT
        1 as depth,
        r.relation_id,
        r.target_decision_id as affected_decision_id,
        r.target_field_path as affected_field_path,
        r.relation_type
    FROM field_relations r
    WHERE r.source_decision_id = p_decision_id
      AND r.source_field_path = p_field_path

    UNION ALL

    -- Recursive case: follow IMPLEMENTS and ENFORCES chains
    SELECT
        ic.depth + 1,
        r.relation_id,
        r.target_decision_id,
        r.target_field_path,
        r.relation_type
    FROM impact_chain ic
    JOIN field_relations r ON
        r.source_decision_id = ic.affected_decision_id
        AND r.source_field_path = ic.affected_field_path
    WHERE ic.depth < p_max_depth
      AND r.relation_type IN ('IMPLEMENTS', 'ENFORCES')
)
SELECT * FROM impact_chain
ORDER BY depth, relation_type;
$$ LANGUAGE sql;

-- ============================================================================
-- FUNCTION: Add or update relation
-- ============================================================================

CREATE OR REPLACE FUNCTION upsert_field_relation(
    p_source_decision_id UUID,
    p_source_field_path TEXT,
    p_target_decision_id UUID,
    p_target_field_path TEXT,
    p_relation_type VARCHAR(20),
    p_confidence VARCHAR(10),
    p_detection_source VARCHAR(15),
    p_description TEXT,
    p_rationale TEXT,
    p_created_by TEXT,
    p_similarity_score FLOAT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_relation_id UUID;
BEGIN
    INSERT INTO field_relations (
        source_decision_id,
        source_field_path,
        target_decision_id,
        target_field_path,
        relation_type,
        confidence,
        detection_source,
        description,
        rationale,
        created_by,
        similarity_score
    )
    VALUES (
        p_source_decision_id,
        p_source_field_path,
        p_target_decision_id,
        p_target_field_path,
        p_relation_type,
        p_confidence,
        p_detection_source,
        p_description,
        p_rationale,
        p_created_by,
        p_similarity_score
    )
    ON CONFLICT (source_decision_id, source_field_path, target_decision_id, target_field_path, relation_type)
    DO UPDATE SET
        confidence = EXCLUDED.confidence,
        description = EXCLUDED.description,
        rationale = EXCLUDED.rationale,
        similarity_score = EXCLUDED.similarity_score
        -- Don't update detection_source or created_by on conflict
    RETURNING relation_id INTO v_relation_id;

    RETURN v_relation_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- FUNCTION: Verify a relation
-- ============================================================================

CREATE OR REPLACE FUNCTION verify_field_relation(
    p_relation_id UUID,
    p_verified_by TEXT,
    p_new_confidence VARCHAR(10) DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE field_relations
    SET
        verified_at = NOW(),
        verified_by = p_verified_by,
        confidence = COALESCE(p_new_confidence, 'CERTAIN')
    WHERE relation_id = p_relation_id
      AND verified_at IS NULL;

    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE field_relations IS
    'Field-level relationships between decisions. '
    'Enables conflict detection, impact analysis, and traceability.';

COMMENT ON COLUMN field_relations.source_field_path IS
    'Field path in source decision. Format: field[index].subfield';

COMMENT ON COLUMN field_relations.relation_type IS
    'Type of relationship: CONFLICTS_WITH, STRENGTHENS, WEAKENS, IMPLEMENTS, ENFORCES, REFERENCES';

COMMENT ON COLUMN field_relations.confidence IS
    'Confidence level: CERTAIN (human verified), HIGH (>80%), MEDIUM (50-80%), LOW (<50%)';

COMMENT ON FUNCTION get_field_impact_chain IS
    'Find all fields affected by changing a specific field, following IMPLEMENTS/ENFORCES chains.';
