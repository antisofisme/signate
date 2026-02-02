-- ============================================================================
-- Migration 010: Projects Table
-- ============================================================================
-- Adds project support for tenant isolation:
-- 1. Create projects table
-- 2. Add project_id to rules, decisions, workflows (optional, NULL = tenant-level)
-- 3. Create indexes and constraints
-- ============================================================================

-- ============================================================================
-- 1. PROJECTS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS projects (
    project_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,

    -- Identification
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,

    -- Environment
    environment VARCHAR(20) NOT NULL DEFAULT 'development',

    -- Settings
    settings JSONB NOT NULL DEFAULT '{}',

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES users(user_id),

    -- Constraints
    CONSTRAINT projects_slug_unique UNIQUE (tenant_id, slug),
    CONSTRAINT projects_check_environment CHECK (
        environment IN ('production', 'staging', 'development', 'testing')
    )
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_projects_tenant ON projects(tenant_id);
CREATE INDEX IF NOT EXISTS idx_projects_slug ON projects(tenant_id, slug);
CREATE INDEX IF NOT EXISTS idx_projects_active ON projects(tenant_id, is_active) WHERE is_active = TRUE AND is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_projects_environment ON projects(tenant_id, environment);

-- ============================================================================
-- 2. ADD PROJECT_ID TO EXISTING TABLES (NULLABLE - for hybrid scope)
-- ============================================================================

-- Rules: project_id NULL = tenant-level rule (shared across all projects)
ALTER TABLE rules ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_rules_project ON rules(project_id) WHERE project_id IS NOT NULL;

-- Decisions: project_id required for all decisions
ALTER TABLE decisions ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_decisions_project ON decisions(project_id) WHERE project_id IS NOT NULL;

-- Workflows: project_id required for workflows
ALTER TABLE workflows ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(project_id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_workflows_project ON workflows(project_id) WHERE project_id IS NOT NULL;

-- ============================================================================
-- 3. PROJECT MEMBERSHIPS (Optional - for project-level access control)
-- ============================================================================

CREATE TABLE IF NOT EXISTS project_memberships (
    project_id UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Role within project
    role VARCHAR(20) NOT NULL DEFAULT 'member',

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (project_id, user_id),

    CONSTRAINT project_memberships_check_role CHECK (
        role IN ('admin', 'member', 'viewer')
    )
);

CREATE INDEX IF NOT EXISTS idx_project_memberships_user ON project_memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_project_memberships_project ON project_memberships(project_id);

-- ============================================================================
-- 4. TRIGGERS
-- ============================================================================

DROP TRIGGER IF EXISTS trigger_update_projects_updated_at ON projects;
CREATE TRIGGER trigger_update_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trigger_update_project_memberships_updated_at ON project_memberships;
CREATE TRIGGER trigger_update_project_memberships_updated_at
    BEFORE UPDATE ON project_memberships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 5. GRANTS
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_runtime_role') THEN
        GRANT SELECT, INSERT, UPDATE, DELETE ON projects TO app_runtime_role;
        GRANT SELECT, INSERT, UPDATE, DELETE ON project_memberships TO app_runtime_role;
    END IF;
END $$;

-- ============================================================================
-- 6. HELPER FUNCTIONS
-- ============================================================================

-- Function to check if user has access to project
CREATE OR REPLACE FUNCTION user_has_project_access(
    p_user_id UUID,
    p_project_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    v_tenant_id UUID;
    v_has_tenant_access BOOLEAN;
    v_has_project_access BOOLEAN;
BEGIN
    -- Get project's tenant
    SELECT tenant_id INTO v_tenant_id
    FROM projects WHERE project_id = p_project_id AND is_deleted = FALSE;

    IF v_tenant_id IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Check tenant membership
    SELECT EXISTS (
        SELECT 1 FROM tenant_memberships
        WHERE tenant_id = v_tenant_id AND user_id = p_user_id AND status = 'active'
    ) INTO v_has_tenant_access;

    IF NOT v_has_tenant_access THEN
        RETURN FALSE;
    END IF;

    -- Check if project memberships are used (if table is empty, all tenant members have access)
    SELECT EXISTS (
        SELECT 1 FROM project_memberships WHERE project_id = p_project_id
    ) INTO v_has_project_access;

    IF NOT v_has_project_access THEN
        -- No project-level restrictions, tenant access is sufficient
        RETURN TRUE;
    END IF;

    -- Check project membership
    RETURN EXISTS (
        SELECT 1 FROM project_memberships
        WHERE project_id = p_project_id AND user_id = p_user_id
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE projects IS 'Projects within tenants for resource isolation';
COMMENT ON COLUMN projects.environment IS 'Deployment environment (production, staging, development, testing)';
COMMENT ON COLUMN projects.settings IS 'Project-specific settings as JSON';

COMMENT ON TABLE project_memberships IS 'Optional project-level access control (if empty, all tenant members have access)';

COMMENT ON COLUMN rules.project_id IS 'Project scope (NULL = tenant-level rule, shared across all projects)';
COMMENT ON COLUMN decisions.project_id IS 'Project scope for decision';
COMMENT ON COLUMN workflows.project_id IS 'Project scope for workflow';

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

COMMENT ON SCHEMA public IS 'ARSAKA_PUGUH SaaS Platform - Migration 010: Projects table';
