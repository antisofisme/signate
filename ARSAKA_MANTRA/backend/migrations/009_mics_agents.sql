-- MICS (MANTRA Intelligent Context System) Database Schema
-- Per MICS-TECHNICAL-DESIGN.md
--
-- Creates tables for:
-- 1. Agent definitions (stored version of YAML agents)
-- 2. Agent version history
-- 3. Context request logs (for learning/analytics)
-- 4. Intent → Agent mapping cache
--
-- Run as: mantra_owner (has CREATE privilege)

-- ============================================================================
-- Agent Definitions
-- ============================================================================

CREATE TABLE IF NOT EXISTS agents (
    agent_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(20) NOT NULL,

    -- Trigger configuration (JSONB)
    trigger_keywords JSONB NOT NULL DEFAULT '[]',
    trigger_intents JSONB NOT NULL DEFAULT '[]',
    trigger_conditions JSONB DEFAULT '{}',

    -- Decision context configuration
    decision_groups TEXT[] NOT NULL DEFAULT '{}',
    decision_features TEXT[] NOT NULL DEFAULT '{}',
    decision_tags TEXT[] NOT NULL DEFAULT '{}',
    search_queries TEXT[] DEFAULT '{}',

    -- Prompts and templates
    prompt_identity TEXT,
    prompt_critical_rules JSONB DEFAULT '[]',
    prompt_behavior JSONB DEFAULT '[]',
    prompt_template TEXT NOT NULL,

    -- Checklist (JSONB with pre_deploy, deploy, post_deploy phases)
    checklist_pre_deploy JSONB DEFAULT '[]',
    checklist_deploy JSONB DEFAULT '[]',
    checklist_post_deploy JSONB DEFAULT '[]',

    -- Validation rules
    validation_pre JSONB DEFAULT '[]',
    validation_post JSONB DEFAULT '[]',

    -- Platform adapters
    adapter_claude JSONB DEFAULT '{}',
    adapter_cursor JSONB DEFAULT '{}',
    adapter_openai JSONB DEFAULT '{}',
    adapter_generic JSONB DEFAULT '{}',

    -- Metadata
    created_by VARCHAR(255) NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

COMMENT ON TABLE agents IS 'MICS agent definitions - stored version of YAML agents';
COMMENT ON COLUMN agents.trigger_keywords IS 'Primary and secondary keywords for intent matching';
COMMENT ON COLUMN agents.decision_groups IS 'MANTRA groups this agent should query (EVO, CTL, ARCH, etc.)';
COMMENT ON COLUMN agents.prompt_template IS 'Handlebars/Jinja2 template for rendering agent prompt';


-- ============================================================================
-- Agent Version History
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) REFERENCES agents(agent_id) ON DELETE CASCADE,
    version VARCHAR(20) NOT NULL,
    definition JSONB NOT NULL,  -- Full agent definition at this version
    created_by VARCHAR(255) NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    change_summary TEXT,

    UNIQUE(agent_id, version)
);

COMMENT ON TABLE agent_versions IS 'Version history for agents - enables rollback and audit';


-- ============================================================================
-- Context Request Logs (for learning and analytics)
-- ============================================================================

CREATE TABLE IF NOT EXISTS context_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Request info
    request_intent TEXT NOT NULL,
    request_platform VARCHAR(50),
    request_project VARCHAR(255),
    request_target VARCHAR(100),
    request_environment VARCHAR(50),

    -- Matching result
    matched_agent_id VARCHAR(100) REFERENCES agents(agent_id) ON DELETE SET NULL,
    confidence_score FLOAT,
    match_method VARCHAR(50),  -- 'keyword', 'semantic', 'fallback'

    -- Response metrics
    decisions_returned INT,
    token_estimate INT,
    assembly_time_ms INT,

    -- Error tracking
    error_occurred BOOLEAN DEFAULT FALSE,
    error_message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE context_requests IS 'Logs of context assembly requests - for learning and optimization';


-- ============================================================================
-- Intent → Agent Mapping Cache
-- ============================================================================

CREATE TABLE IF NOT EXISTS intent_agent_cache (
    intent_hash VARCHAR(64) PRIMARY KEY,  -- SHA256 of normalized intent
    intent_text TEXT NOT NULL,
    agent_id VARCHAR(100) REFERENCES agents(agent_id) ON DELETE CASCADE,
    confidence FLOAT NOT NULL,
    hit_count INT DEFAULT 1,
    last_hit_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE intent_agent_cache IS 'Cache of intent to agent mappings for fast lookup';


-- ============================================================================
-- Indexes
-- ============================================================================

-- Agents
CREATE INDEX IF NOT EXISTS idx_agents_active ON agents(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_agents_keywords ON agents USING GIN(trigger_keywords);
CREATE INDEX IF NOT EXISTS idx_agents_groups ON agents USING GIN(decision_groups);

-- Agent Versions
CREATE INDEX IF NOT EXISTS idx_agent_versions_agent ON agent_versions(agent_id);
CREATE INDEX IF NOT EXISTS idx_agent_versions_created ON agent_versions(created_at DESC);

-- Context Requests
CREATE INDEX IF NOT EXISTS idx_context_requests_agent ON context_requests(matched_agent_id);
CREATE INDEX IF NOT EXISTS idx_context_requests_created ON context_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_requests_platform ON context_requests(request_platform);

-- Intent Cache
CREATE INDEX IF NOT EXISTS idx_intent_cache_agent ON intent_agent_cache(agent_id);
CREATE INDEX IF NOT EXISTS idx_intent_cache_hits ON intent_agent_cache(hit_count DESC);


-- ============================================================================
-- Insert Built-in Agents
-- ============================================================================

INSERT INTO agents (
    agent_id, name, description, version,
    trigger_keywords, trigger_intents,
    decision_groups, decision_features, decision_tags,
    prompt_identity, prompt_critical_rules, prompt_template,
    created_by
) VALUES
-- Deployment Agent
(
    'deployment-agent',
    'Deployment Agent',
    'Handles production deployments with safety checks',
    '1.0.0',
    '{"primary": ["deploy", "release", "ship"], "secondary": ["production", "staging", "rollout"]}',
    '["DEPLOYMENT", "RELEASE", "ROLLOUT"]',
    ARRAY['EVO', 'CTL'],
    ARRAY['F15', 'F13', 'F14', 'F11'],
    ARRAY['INFRA', 'CICD', 'DEVOPS'],
    'You are the Deployment Agent, responsible for safe and reliable production deployments.',
    '[{"rule": "NEVER deploy without passing tests", "severity": "blocking"}, {"rule": "NEVER skip health checks", "severity": "blocking"}, {"rule": "ALWAYS have rollback plan ready", "severity": "blocking"}]',
    '# Deployment Agent\n\n{{identity}}\n\n## Current Task\n- Target: {{target}}\n- Environment: {{environment}}\n\n## Critical Rules\n{{#each critical_rules}}\n- [{{severity}}] {{rule}}\n{{/each}}',
    'system'
),
-- Database Agent
(
    'database-agent',
    'Database Agent',
    'Handles database operations, migrations, and schema changes',
    '1.0.0',
    '{"primary": ["database", "migration", "schema"], "secondary": ["query", "index", "sql"]}',
    '["DATABASE", "MIGRATION", "SCHEMA"]',
    ARRAY['ARCH', 'CTL'],
    ARRAY['F07', 'F05', 'F09', 'F12'],
    ARRAY['DB', 'MIGRATION'],
    'You are the Database Agent, responsible for safe database operations.',
    '[{"rule": "NEVER modify production schema directly", "severity": "blocking"}, {"rule": "ALWAYS use migrations", "severity": "blocking"}, {"rule": "ALWAYS backup before destructive operations", "severity": "blocking"}]',
    '# Database Agent\n\n{{identity}}\n\n## Critical Rules\n{{#each critical_rules}}\n- [{{severity}}] {{rule}}\n{{/each}}',
    'system'
),
-- Backend Agent
(
    'backend-agent',
    'Backend Development Agent',
    'Handles backend API development with Clean Architecture',
    '1.0.0',
    '{"primary": ["backend", "api", "endpoint"], "secondary": ["service", "fastapi", "python"]}',
    '["BACKEND", "API_DEVELOPMENT", "SERVICE_IMPLEMENTATION"]',
    ARRAY['ARCH', 'CTL', 'STD'],
    ARRAY['F08', 'F06', 'F09', 'F11'],
    ARRAY['BE', 'API'],
    'You are the Backend Agent, responsible for API development following Clean Architecture.',
    '[{"rule": "Add authentication to all new endpoints unless explicitly public", "severity": "blocking"}, {"rule": "Validate all input with Pydantic models", "severity": "blocking"}, {"rule": "Never expose internal errors to clients", "severity": "blocking"}]',
    '# Backend Agent\n\n{{identity}}\n\n## Critical Rules\n{{#each critical_rules}}\n- [{{severity}}] {{rule}}\n{{/each}}',
    'system'
),
-- Frontend Agent
(
    'frontend-agent',
    'Frontend Development Agent',
    'Handles frontend development with React patterns',
    '1.0.0',
    '{"primary": ["frontend", "react", "component"], "secondary": ["ui", "css", "tailwind"]}',
    '["FRONTEND", "UI_DEVELOPMENT", "COMPONENT_CREATION"]',
    ARRAY['ARCH', 'INT'],
    ARRAY['F06', 'F01', 'F03'],
    ARRAY['FE', 'UI'],
    'You are the Frontend Agent, responsible for React development with consistent patterns.',
    '[{"rule": "Add proper TypeScript types", "severity": "blocking"}, {"rule": "Use shared components from /shared", "severity": "warning"}, {"rule": "Use Tailwind CSS for styling", "severity": "warning"}]',
    '# Frontend Agent\n\n{{identity}}\n\n## Critical Rules\n{{#each critical_rules}}\n- [{{severity}}] {{rule}}\n{{/each}}',
    'system'
),
-- Security Agent
(
    'security-agent',
    'Security Review Agent',
    'Reviews code for security vulnerabilities and ensures compliance',
    '1.0.0',
    '{"primary": ["security", "auth", "authentication"], "secondary": ["authorization", "permission", "vulnerability"]}',
    '["SECURITY_REVIEW", "AUTH", "VULNERABILITY_CHECK"]',
    ARRAY['CTL'],
    ARRAY['F11', 'F12'],
    ARRAY['SECURITY', 'AUTH'],
    'You are the Security Agent, responsible for ensuring code is secure.',
    '[{"rule": "NEVER hardcode secrets, passwords, or API keys", "severity": "blocking"}, {"rule": "ALWAYS validate and sanitize user input", "severity": "blocking"}, {"rule": "Use parameterized queries to prevent SQL injection", "severity": "blocking"}]',
    '# Security Agent\n\n{{identity}}\n\n## Critical Rules\n{{#each critical_rules}}\n- [{{severity}}] {{rule}}\n{{/each}}',
    'system'
)
ON CONFLICT (agent_id) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    version = EXCLUDED.version,
    trigger_keywords = EXCLUDED.trigger_keywords,
    trigger_intents = EXCLUDED.trigger_intents,
    decision_groups = EXCLUDED.decision_groups,
    decision_features = EXCLUDED.decision_features,
    decision_tags = EXCLUDED.decision_tags,
    prompt_identity = EXCLUDED.prompt_identity,
    prompt_critical_rules = EXCLUDED.prompt_critical_rules,
    prompt_template = EXCLUDED.prompt_template,
    updated_at = NOW();


-- ============================================================================
-- Grants (for mantra_app role)
-- ============================================================================

-- mantra_app can read agents but not modify them
GRANT SELECT ON agents TO mantra_app;
GRANT SELECT ON agent_versions TO mantra_app;

-- mantra_app can insert context requests (for logging)
GRANT SELECT, INSERT ON context_requests TO mantra_app;

-- mantra_app can read and update intent cache
GRANT SELECT, INSERT, UPDATE ON intent_agent_cache TO mantra_app;


-- ============================================================================
-- Verification
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'MICS agents migration complete';
    RAISE NOTICE 'Tables created: agents, agent_versions, context_requests, intent_agent_cache';
    RAISE NOTICE 'Built-in agents: deployment-agent, database-agent, backend-agent, frontend-agent, security-agent';
END $$;
