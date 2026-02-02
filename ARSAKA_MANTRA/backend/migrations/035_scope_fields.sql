-- Migration: 035_scope_fields.sql
-- Purpose: Add hierarchical scope fields to decisions
-- Enables scope-aware conflict detection to minimize false positives

-- ============================================================================
-- ADD SCOPE COLUMNS TO DECISIONS TABLE
-- ============================================================================
-- scope_path: Hierarchical path (e.g., "fe.react.css.tailwind")
-- scope_inheritance: Whether decision applies to child scopes
-- scope_tags: Additional scope metadata for cross-cutting concerns

ALTER TABLE decisions ADD COLUMN IF NOT EXISTS scope_path TEXT DEFAULT '*';
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS scope_inheritance BOOLEAN DEFAULT TRUE;
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS scope_tags TEXT[] DEFAULT '{}';

-- ============================================================================
-- CONSTRAINTS
-- ============================================================================

-- Validate scope_path format
-- Valid: '*' (global), 'fe', 'fe.react', 'fe.react.css.tailwind', 'be.*'
ALTER TABLE decisions ADD CONSTRAINT chk_scope_path_format
    CHECK (scope_path ~ '^(\*|[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*(\.\*)?|\*)$');

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Index for scope_path lookups
CREATE INDEX IF NOT EXISTS idx_decisions_scope_path
    ON decisions(scope_path);

-- Index for scope_tags using GIN for array containment queries
CREATE INDEX IF NOT EXISTS idx_decisions_scope_tags
    ON decisions USING GIN(scope_tags);

-- Partial index for inheriting scopes (common query: "what inherits?")
CREATE INDEX IF NOT EXISTS idx_decisions_scope_inheriting
    ON decisions(scope_path)
    WHERE scope_inheritance = TRUE;

-- ============================================================================
-- FUNCTION: Check if two scopes can conflict
-- ============================================================================

CREATE OR REPLACE FUNCTION scopes_can_conflict(
    p_scope_a TEXT,
    p_scope_b TEXT,
    p_inheritance_a BOOLEAN DEFAULT TRUE,
    p_inheritance_b BOOLEAN DEFAULT TRUE
)
RETURNS TABLE (
    can_conflict BOOLEAN,
    reason TEXT
) AS $$
DECLARE
    v_segments_a TEXT[];
    v_segments_b TEXT[];
    v_min_len INT;
BEGIN
    -- Global scope can conflict with anything
    IF p_scope_a = '*' OR p_scope_b = '*' THEN
        RETURN QUERY SELECT TRUE, 'Global scope';
        RETURN;
    END IF;

    -- Same scope always can conflict
    IF p_scope_a = p_scope_b THEN
        RETURN QUERY SELECT TRUE, 'Same scope';
        RETURN;
    END IF;

    -- Parse segments (strip trailing .* if present)
    v_segments_a := string_to_array(regexp_replace(p_scope_a, '\.\*$', ''), '.');
    v_segments_b := string_to_array(regexp_replace(p_scope_b, '\.\*$', ''), '.');

    v_min_len := LEAST(array_length(v_segments_a, 1), array_length(v_segments_b, 1));

    -- Check if one is ancestor of the other
    IF v_segments_a[1:v_min_len] = v_segments_b[1:v_min_len] THEN
        -- One is ancestor/descendant of the other
        IF array_length(v_segments_a, 1) < array_length(v_segments_b, 1) THEN
            -- A is parent of B
            IF p_inheritance_a THEN
                RETURN QUERY SELECT TRUE, 'Parent scope with inheritance: ' || p_scope_a || ' -> ' || p_scope_b;
                RETURN;
            END IF;
        ELSE
            -- B is parent of A
            IF p_inheritance_b THEN
                RETURN QUERY SELECT TRUE, 'Child of inherited scope: ' || p_scope_b || ' -> ' || p_scope_a;
                RETURN;
            END IF;
        END IF;
    END IF;

    -- Different branches - cannot conflict
    RETURN QUERY SELECT FALSE, 'Different scope branches: ' || p_scope_a || ' vs ' || p_scope_b;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- FUNCTION: Get scope relation type
-- ============================================================================

CREATE TYPE scope_relation AS ENUM (
    'SAME',       -- Identical scopes
    'PARENT',     -- A is parent of B
    'CHILD',      -- A is child of B
    'SIBLING',    -- Same parent, different branch
    'COUSIN',     -- Different parent branches
    'UNRELATED'   -- No common ancestor beyond global
);

CREATE OR REPLACE FUNCTION get_scope_relation(
    p_scope_a TEXT,
    p_scope_b TEXT
)
RETURNS scope_relation AS $$
DECLARE
    v_segments_a TEXT[];
    v_segments_b TEXT[];
    v_common_prefix INT := 0;
    v_i INT;
BEGIN
    -- Global scope handling
    IF p_scope_a = '*' OR p_scope_b = '*' THEN
        IF p_scope_a = p_scope_b THEN
            RETURN 'SAME';
        ELSIF p_scope_a = '*' THEN
            RETURN 'PARENT';
        ELSE
            RETURN 'CHILD';
        END IF;
    END IF;

    -- Same scope
    IF p_scope_a = p_scope_b THEN
        RETURN 'SAME';
    END IF;

    -- Parse segments
    v_segments_a := string_to_array(regexp_replace(p_scope_a, '\.\*$', ''), '.');
    v_segments_b := string_to_array(regexp_replace(p_scope_b, '\.\*$', ''), '.');

    -- Find common prefix length
    FOR v_i IN 1..LEAST(array_length(v_segments_a, 1), array_length(v_segments_b, 1)) LOOP
        IF v_segments_a[v_i] = v_segments_b[v_i] THEN
            v_common_prefix := v_common_prefix + 1;
        ELSE
            EXIT;
        END IF;
    END LOOP;

    -- Determine relationship
    IF v_common_prefix = 0 THEN
        RETURN 'UNRELATED';
    END IF;

    IF v_common_prefix = array_length(v_segments_a, 1) THEN
        RETURN 'PARENT';  -- A is prefix of B
    ELSIF v_common_prefix = array_length(v_segments_b, 1) THEN
        RETURN 'CHILD';   -- B is prefix of A
    ELSIF v_common_prefix = array_length(v_segments_a, 1) - 1
          AND v_common_prefix = array_length(v_segments_b, 1) - 1 THEN
        RETURN 'SIBLING'; -- Same parent, different last segment
    ELSE
        RETURN 'COUSIN';  -- Share some ancestry
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- FUNCTION: Find decisions by scope
-- ============================================================================

CREATE OR REPLACE FUNCTION get_decisions_by_scope(
    p_scope_path TEXT,
    p_include_ancestors BOOLEAN DEFAULT TRUE,
    p_include_descendants BOOLEAN DEFAULT TRUE
)
RETURNS TABLE (
    decision_id UUID,
    decision_code TEXT,
    scope_path TEXT,
    scope_inheritance BOOLEAN,
    relation scope_relation
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.decision_id,
        d.decision_code,
        d.scope_path,
        d.scope_inheritance,
        get_scope_relation(p_scope_path, d.scope_path) as relation
    FROM decisions d
    WHERE
        -- Exact match
        d.scope_path = p_scope_path
        -- Global scope (always applies)
        OR d.scope_path = '*'
        -- Ancestors (if requested and they inherit)
        OR (
            p_include_ancestors
            AND d.scope_inheritance = TRUE
            AND p_scope_path LIKE d.scope_path || '.%'
        )
        -- Descendants (if requested)
        OR (
            p_include_descendants
            AND d.scope_path LIKE p_scope_path || '.%'
        )
    ORDER BY
        -- Global first, then exact match, then ancestors by depth, then descendants
        CASE
            WHEN d.scope_path = '*' THEN 0
            WHEN d.scope_path = p_scope_path THEN 1
            WHEN p_scope_path LIKE d.scope_path || '.%' THEN 2
            ELSE 3
        END,
        array_length(string_to_array(d.scope_path, '.'), 1);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- VIEW: Scope Statistics
-- ============================================================================

CREATE OR REPLACE VIEW scope_statistics AS
SELECT
    -- Top-level scope (first segment)
    CASE
        WHEN scope_path = '*' THEN '*'
        ELSE split_part(scope_path, '.', 1)
    END as top_level_scope,
    COUNT(*) as decision_count,
    COUNT(*) FILTER (WHERE scope_inheritance = TRUE) as inheriting_count,
    COUNT(*) FILTER (WHERE scope_inheritance = FALSE) as non_inheriting_count,
    array_agg(DISTINCT unnest_tags.tag) FILTER (WHERE unnest_tags.tag IS NOT NULL) as all_tags
FROM decisions
LEFT JOIN LATERAL unnest(scope_tags) as unnest_tags(tag) ON TRUE
GROUP BY
    CASE
        WHEN scope_path = '*' THEN '*'
        ELSE split_part(scope_path, '.', 1)
    END
ORDER BY decision_count DESC;

-- ============================================================================
-- VIEW: Scope Tree (hierarchical view)
-- ============================================================================

CREATE OR REPLACE VIEW scope_tree AS
WITH RECURSIVE scope_hierarchy AS (
    -- Base: top-level scopes
    SELECT
        scope_path,
        1 as depth,
        ARRAY[split_part(scope_path, '.', 1)] as path_array,
        COUNT(*) as direct_decisions
    FROM decisions
    WHERE scope_path != '*'
    GROUP BY scope_path

    UNION ALL

    -- Recursive: aggregate up the tree
    SELECT
        regexp_replace(sh.scope_path, '\.[^.]+$', '') as scope_path,
        sh.depth - 1 as depth,
        sh.path_array[1:array_length(sh.path_array, 1)-1] as path_array,
        sh.direct_decisions
    FROM scope_hierarchy sh
    WHERE array_length(sh.path_array, 1) > 1
)
SELECT
    scope_path,
    MAX(depth) as max_depth,
    SUM(direct_decisions) as total_decisions
FROM scope_hierarchy
GROUP BY scope_path
ORDER BY scope_path;

-- ============================================================================
-- BACKFILL EXISTING DECISIONS
-- ============================================================================
-- Set default scope based on domain_id if scope_path is still default

UPDATE decisions
SET scope_path = CASE
    -- Architecture decisions are typically global or cross-cutting
    WHEN domain_id = 'ARCH' THEN '*'
    -- Control decisions are typically global
    WHEN domain_id = 'CTL' THEN '*'
    -- Evolution decisions are typically global
    WHEN domain_id = 'EVO' THEN '*'
    -- Integration decisions might be scoped, default to global
    WHEN domain_id = 'INT' THEN '*'
    ELSE '*'
END
WHERE scope_path = '*' OR scope_path IS NULL;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON COLUMN decisions.scope_path IS
    'Hierarchical scope path (e.g., "fe.react.css.tailwind"). '
    'Use "*" for global scope, "path.*" for wildcard.';

COMMENT ON COLUMN decisions.scope_inheritance IS
    'If TRUE, this decision applies to all child scopes under scope_path. '
    'If FALSE, only applies to exact scope_path match.';

COMMENT ON COLUMN decisions.scope_tags IS
    'Additional scope metadata for cross-cutting concerns. '
    'Examples: security, performance, accessibility.';

COMMENT ON FUNCTION scopes_can_conflict IS
    'Determine if two decisions can conflict based on their scope paths. '
    'Returns FALSE for decisions in different branches (e.g., fe.react vs fe.vue).';

COMMENT ON FUNCTION get_scope_relation IS
    'Get the relationship between two scopes: SAME, PARENT, CHILD, SIBLING, COUSIN, UNRELATED.';

COMMENT ON FUNCTION get_decisions_by_scope IS
    'Find all decisions relevant to a given scope path, including ancestors and descendants.';
