# MICS Technical Design

## The Key Insight

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│  PROBLEM: Setiap AI platform punya struktur berbeda                             │
│                                                                                 │
│  Claude Code    Cursor         OpenAI          Gemini        Generic           │
│  ┌─────────┐   ┌─────────┐    ┌─────────┐    ┌─────────┐   ┌─────────┐        │
│  │claude.md│   │.cursor  │    │System   │    │System   │   │README   │        │
│  │skills   │   │rules    │    │Prompt   │    │Instruct │   │docs     │        │
│  │MCP      │   │context  │    │Functions│    │Tools    │   │         │        │
│  │hooks    │   │commands │    │GPTs     │    │Grounding│   │         │        │
│  └─────────┘   └─────────┘    └─────────┘    └─────────┘   └─────────┘        │
│                                                                                 │
│  SOLUTION: Universal Agent Definition → Platform Adapters                       │
│                                                                                 │
│                    ┌─────────────────────────────────────┐                      │
│                    │   MANTRA UNIVERSAL AGENT FORMAT     │                      │
│                    │                                     │                      │
│                    │   - Agent definition (YAML/JSON)    │                      │
│                    │   - Platform-agnostic               │                      │
│                    │   - Contains all context            │                      │
│                    └─────────────────────────────────────┘                      │
│                                      │                                          │
│            ┌─────────────┬───────────┼───────────┬─────────────┐               │
│            ▼             ▼           ▼           ▼             ▼               │
│       ┌─────────┐   ┌─────────┐ ┌─────────┐ ┌─────────┐  ┌─────────┐          │
│       │ Claude  │   │ Cursor  │ │ OpenAI  │ │ Gemini  │  │ Generic │          │
│       │ Adapter │   │ Adapter │ │ Adapter │ │ Adapter │  │ Adapter │          │
│       └─────────┘   └─────────┘ └─────────┘ └─────────┘  └─────────┘          │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Universal Agent Format (UAF)

```yaml
# Universal Agent Format v1.0
# Platform-agnostic agent definition

$schema: "https://mantra.dev/schemas/agent-v1.json"
version: "1.0"

agent:
  id: "deployment-agent"
  name: "Deployment Agent"
  description: "Handles production deployments with safety checks"
  version: "1.0.0"

  # ═══════════════════════════════════════════════════════════════════════════
  # WHEN TO ACTIVATE
  # ═══════════════════════════════════════════════════════════════════════════

  triggers:
    # Keyword matching (fast, first-pass)
    keywords:
      primary:
        - "deploy"
        - "release"
        - "ship"
      secondary:
        - "push to prod"
        - "go live"
        - "production"

    # Semantic intents (for complex cases)
    intents:
      - "DEPLOYMENT"
      - "RELEASE"
      - "ROLLOUT"

    # Context conditions
    conditions:
      - target_includes: ["backend", "frontend", "api", "service"]
      - environment_includes: ["staging", "production", "prod"]

  # ═══════════════════════════════════════════════════════════════════════════
  # WHAT DECISIONS TO CONSIDER
  # ═══════════════════════════════════════════════════════════════════════════

  decision_context:
    # Groups to search
    groups:
      - id: "EVO"
        relevance: "high"
        reason: "Execution & Evolution - deployment procedures"
      - id: "CTL"
        relevance: "high"
        reason: "Control & Policy - security requirements"
      - id: "ARCH"
        relevance: "medium"
        reason: "Architecture - system boundaries"

    # Specific features
    features:
      required:
        - "F15"  # Environment & Promotion Rules
        - "F13"  # Decision Lifecycle
      optional:
        - "F14"  # Reversibility & Exit Strategy
        - "F11"  # Security & Compliance

    # Tags to search
    tags:
      required: ["INFRA", "CICD"]
      optional: ["DEVOPS", "SECURITY"]

    # Semantic search queries
    search_queries:
      - "production deployment requirements"
      - "release process"
      - "deployment security"

  # ═══════════════════════════════════════════════════════════════════════════
  # AGENT PROMPT
  # ═══════════════════════════════════════════════════════════════════════════

  prompt:
    # Core identity
    identity: |
      You are the Deployment Agent, responsible for safe and reliable
      production deployments. You ensure all deployments follow
      established procedures and pass required checks.

    # Critical rules (always included, high priority)
    critical_rules:
      - rule: "NEVER deploy without passing tests"
        severity: "blocking"
      - rule: "NEVER skip health checks"
        severity: "blocking"
      - rule: "ALWAYS have rollback plan ready"
        severity: "blocking"
      - rule: "ALWAYS notify stakeholders before production deploy"
        severity: "warning"

    # Behavioral guidelines
    behavior:
      - "Ask for confirmation before destructive operations"
      - "Log all deployment steps"
      - "Check current state before making changes"
      - "Verify success after each step"

    # Template with placeholders
    template: |
      # Deployment Agent

      ## Current Task
      - Target: {{target}}
      - Environment: {{environment}}
      - Version: {{version}}

      ## Critical Rules
      {{#each critical_rules}}
      - [{{severity}}] {{rule}}
      {{/each}}

      ## Relevant Decisions
      {{#each decisions}}
      ### {{code}}: {{title}}
      {{statement}}

      Constraints:
      {{#each constraints}}
      - {{type}}: {{statement}}
      {{/each}}
      {{/each}}

      ## Deployment Checklist
      {{#each checklist}}
      {{@index}}. [ ] {{step}}
         {{#if command}}Command: `{{command}}`{{/if}}
         {{#if blocking}}⚠️ BLOCKING{{/if}}
      {{/each}}

      ## Codebase Context
      - Deploy config: {{codebase.deploy_config}}
      - Current version: {{codebase.current_version}}
      - Last deployment: {{codebase.last_deploy}}

  # ═══════════════════════════════════════════════════════════════════════════
  # CHECKLIST
  # ═══════════════════════════════════════════════════════════════════════════

  checklist:
    pre_deploy:
      - id: "tests"
        step: "Run all tests"
        command: "bun test"
        blocking: true
        validation:
          type: "exit_code"
          expected: 0

      - id: "migrations"
        step: "Check database migrations"
        command: "alembic check"
        blocking: true
        validation:
          type: "output_contains"
          expected: "No new migrations"

      - id: "lint"
        step: "Run linting"
        command: "bun lint"
        blocking: false

    deploy:
      - id: "build"
        step: "Build Docker image"
        command: "docker build -t {{image}}:{{version}} ."
        blocking: true

      - id: "push"
        step: "Push to registry (if remote)"
        command: "docker push {{image}}:{{version}}"
        blocking: true
        condition: "registry_enabled"

      - id: "deploy"
        step: "Deploy via Nomad"
        command: "nomad job run {{nomad_file}}"
        blocking: true

    post_deploy:
      - id: "health"
        step: "Verify health endpoint"
        command: "curl -f {{health_url}}"
        blocking: true
        retry:
          attempts: 5
          delay: 10s

      - id: "smoke"
        step: "Run smoke tests"
        command: "bun test:smoke"
        blocking: false

      - id: "notify"
        step: "Notify team"
        blocking: false

  # ═══════════════════════════════════════════════════════════════════════════
  # VALIDATION RULES
  # ═══════════════════════════════════════════════════════════════════════════

  validation:
    pre_conditions:
      - name: "clean_working_directory"
        check: "git status --porcelain | wc -l"
        expected: "0"
        message: "Working directory must be clean"

      - name: "on_correct_branch"
        check: "git branch --show-current"
        expected: ["main", "master", "release/*"]
        message: "Must be on main/master or release branch"

    post_conditions:
      - name: "service_healthy"
        check: "curl -sf {{health_url}}/health"
        expected: "HTTP 200"
        message: "Service must respond to health check"

  # ═══════════════════════════════════════════════════════════════════════════
  # PLATFORM ADAPTERS
  # ═══════════════════════════════════════════════════════════════════════════

  platform_adapters:
    claude:
      # How to present this agent in Claude Code
      mcp_tool_hints:
        - "Call mantra_get_task_context at the start of deployment"
        - "Use mantra_validate before executing commands"
      skill_integration:
        invoke_via: "/deploy"
        hooks:
          - "post-edit-lint"

    cursor:
      # How to inject into .cursorrules
      rules_format: |
        # Deployment Rules (from MANTRA)
        {{rendered_prompt}}

    openai:
      # Function calling format
      function_hints:
        - function: "get_deployment_context"
          description: "Get deployment requirements from MANTRA"

    generic:
      # Plain markdown export
      markdown_format: |
        # Deployment Guide

        {{rendered_prompt}}

        ## Commands
        ```bash
        {{#each checklist}}
        # {{step}}
        {{command}}
        {{/each}}
        ```
```

---

## Context Assembly Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        CONTEXT ASSEMBLY PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  INPUT                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ {                                                                        │   │
│  │   "intent": "deploy backend to production",                              │   │
│  │   "platform": "claude-code",                                             │   │
│  │   "project": "signate/ARSAKA_MANTRA",                                     │   │
│  │   "additional_context": {                                                │   │
│  │     "branch": "main",                                                    │   │
│  │     "version": "1.0.6"                                                   │   │
│  │   }                                                                      │   │
│  │ }                                                                        │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  STAGE 1: INTENT RECOGNITION                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                          │   │
│  │  1. Keyword extraction: ["deploy", "backend", "production"]              │   │
│  │                                                                          │   │
│  │  2. Keyword → Agent mapping:                                             │   │
│  │     - "deploy" matches deployment-agent (score: 0.95)                    │   │
│  │     - "backend" matches backend-agent (score: 0.70)                      │   │
│  │     → Winner: deployment-agent                                           │   │
│  │                                                                          │   │
│  │  3. If ambiguous, use semantic similarity:                               │   │
│  │     embed(intent) <-> embed(agent.description)                           │   │
│  │                                                                          │   │
│  │  Output: {                                                               │   │
│  │    "agent_id": "deployment-agent",                                       │   │
│  │    "confidence": 0.95,                                                   │   │
│  │    "task_type": "DEPLOYMENT",                                            │   │
│  │    "target": "backend",                                                  │   │
│  │    "environment": "production"                                           │   │
│  │  }                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  STAGE 2: AGENT LOADING                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                          │   │
│  │  1. Load agent definition: deployment-agent.yaml                         │   │
│  │                                                                          │   │
│  │  2. Validate agent version compatibility                                 │   │
│  │                                                                          │   │
│  │  3. Extract context requirements:                                        │   │
│  │     - decision_groups: [EVO, CTL]                                        │   │
│  │     - decision_features: [F15, F13, F14, F11]                            │   │
│  │     - decision_tags: [INFRA, CICD]                                       │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  STAGE 3: DECISION RETRIEVAL                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                          │   │
│  │  1. Query decisions by group/feature:                                    │   │
│  │     SELECT * FROM decisions                                              │   │
│  │     WHERE group_id IN ('EVO', 'CTL')                                     │   │
│  │       AND feature_id IN ('F15', 'F13', 'F14', 'F11')                     │   │
│  │                                                                          │   │
│  │  2. Filter by tags:                                                      │   │
│  │     WHERE tags && ARRAY['INFRA', 'CICD']                                 │   │
│  │                                                                          │   │
│  │  3. Semantic search for additional relevance:                            │   │
│  │     mantra_search("production deployment requirements")                  │   │
│  │                                                                          │   │
│  │  4. Rank and limit:                                                      │   │
│  │     - Top 10 most relevant                                               │   │
│  │     - Prioritize by blast_radius and scope                               │   │
│  │                                                                          │   │
│  │  Output: List[Decision] (top 10)                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  STAGE 4: CONSTRAINT EXTRACTION                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                          │   │
│  │  From retrieved decisions, extract:                                      │   │
│  │                                                                          │   │
│  │  1. PROHIBITIONS (blocking):                                             │   │
│  │     - "NEVER deploy without tests"                                       │   │
│  │     - "NEVER skip health checks"                                         │   │
│  │                                                                          │   │
│  │  2. REQUIREMENTS (mandatory):                                            │   │
│  │     - "Must use Nomad for deployment"                                    │   │
│  │     - "Must verify migrations"                                           │   │
│  │                                                                          │   │
│  │  3. LIMITATIONS (advisory):                                              │   │
│  │     - "Production deploy only during business hours"                     │   │
│  │                                                                          │   │
│  │  4. INVARIANTS (always true):                                            │   │
│  │     - "All deployments are logged"                                       │   │
│  │     - "Rollback is always possible"                                      │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  STAGE 5: CODEBASE CONTEXT                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                          │   │
│  │  1. Find deployment-related files:                                       │   │
│  │     - nomad/*.nomad                                                      │   │
│  │     - Dockerfile                                                         │   │
│  │     - docker-compose.yml                                                 │   │
│  │                                                                          │   │
│  │  2. Extract current state:                                               │   │
│  │     - Current version from package.json / pyproject.toml                 │   │
│  │     - Last deploy from git tags or deploy logs                           │   │
│  │                                                                          │   │
│  │  3. Identify relevant configs:                                           │   │
│  │     - Environment variables needed                                       │   │
│  │     - Secrets required                                                   │   │
│  │                                                                          │   │
│  │  Output: {                                                               │   │
│  │    "deploy_config": "nomad/mantra-backend.nomad",                        │   │
│  │    "dockerfile": "backend/Dockerfile",                                   │   │
│  │    "current_version": "1.0.5",                                           │   │
│  │    "last_deploy": "2026-01-26T10:30:00Z"                                 │   │
│  │  }                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  STAGE 6: TEMPLATE RENDERING                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                          │   │
│  │  1. Load agent prompt template                                           │   │
│  │                                                                          │   │
│  │  2. Inject variables:                                                    │   │
│  │     - {{target}} → "backend"                                             │   │
│  │     - {{environment}} → "production"                                     │   │
│  │     - {{decisions}} → [Decision objects]                                 │   │
│  │     - {{constraints}} → [Constraint objects]                             │   │
│  │     - {{checklist}} → [ChecklistItem objects]                            │   │
│  │     - {{codebase}} → Codebase context object                             │   │
│  │                                                                          │   │
│  │  3. Render with Jinja2/Handlebars                                        │   │
│  │                                                                          │   │
│  │  Output: Rendered prompt string                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  STAGE 7: PLATFORM ADAPTATION                                                   │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                                                                          │   │
│  │  Input: platform = "claude-code"                                         │   │
│  │                                                                          │   │
│  │  Claude Adapter:                                                         │   │
│  │  1. Format as MCP response                                               │   │
│  │  2. Include tool hints                                                   │   │
│  │  3. Optimize for context window                                          │   │
│  │                                                                          │   │
│  │  Output format per platform:                                             │   │
│  │  - claude-code: MCP JSON response                                        │   │
│  │  - cursor: .cursorrules format                                           │   │
│  │  - openai: Function response format                                      │   │
│  │  - generic: Markdown                                                     │   │
│  │                                                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  OUTPUT                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ {                                                                        │   │
│  │   "task_context": {                                                      │   │
│  │     "agent": "deployment-agent",                                         │   │
│  │     "prompt": "# Deployment Agent\n\nYou are deploying...",              │   │
│  │     "decisions": [...],                                                  │   │
│  │     "constraints": {                                                     │   │
│  │       "prohibitions": [...],                                             │   │
│  │       "requirements": [...],                                             │   │
│  │       "limitations": [...]                                               │   │
│  │     },                                                                   │   │
│  │     "checklist": [...],                                                  │   │
│  │     "codebase_context": {...}                                            │   │
│  │   },                                                                     │   │
│  │   "meta": {                                                              │   │
│  │     "token_estimate": 2500,                                              │   │
│  │     "decisions_count": 8,                                                │   │
│  │     "assembly_time_ms": 45                                               │   │
│  │   }                                                                      │   │
│  │ }                                                                        │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

```sql
-- Agent definitions
CREATE TABLE agents (
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

    -- Checklist
    checklist_pre_deploy JSONB DEFAULT '[]',
    checklist_deploy JSONB DEFAULT '[]',
    checklist_post_deploy JSONB DEFAULT '[]',

    -- Validation
    validation_pre JSONB DEFAULT '[]',
    validation_post JSONB DEFAULT '[]',

    -- Platform adapters
    adapter_claude JSONB DEFAULT '{}',
    adapter_cursor JSONB DEFAULT '{}',
    adapter_openai JSONB DEFAULT '{}',
    adapter_generic JSONB DEFAULT '{}',

    -- Metadata
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Agent version history
CREATE TABLE agent_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(100) REFERENCES agents(agent_id),
    version VARCHAR(20) NOT NULL,
    definition JSONB NOT NULL,  -- Full agent definition at this version
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    change_summary TEXT
);

-- Context request logs (for learning)
CREATE TABLE context_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_intent TEXT NOT NULL,
    request_platform VARCHAR(50),
    request_project VARCHAR(255),

    matched_agent_id VARCHAR(100),
    confidence_score FLOAT,

    decisions_returned INT,
    token_estimate INT,
    assembly_time_ms INT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Intent → Agent mapping cache
CREATE TABLE intent_agent_cache (
    intent_hash VARCHAR(64) PRIMARY KEY,  -- SHA256 of normalized intent
    intent_text TEXT NOT NULL,
    agent_id VARCHAR(100) REFERENCES agents(agent_id),
    confidence FLOAT NOT NULL,
    hit_count INT DEFAULT 1,
    last_hit_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_agents_active ON agents(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_agents_keywords ON agents USING GIN(trigger_keywords);
CREATE INDEX idx_context_requests_agent ON context_requests(matched_agent_id);
CREATE INDEX idx_intent_cache_agent ON intent_agent_cache(agent_id);
```

---

## MCP Tool Definitions

```python
# mantra_mcp/tools/context.py

MANTRA_CONTEXT_TOOLS = [
    {
        "name": "mantra_get_task_context",
        "description": """
            Get intelligent context for a task from MANTRA.

            This tool will:
            1. Recognize the task type from your intent
            2. Load the appropriate task agent with specialized prompts
            3. Find relevant decisions that apply to this task
            4. Provide a checklist of steps to follow
            5. Include constraints and prohibitions

            WHEN TO USE:
            - At the START of any significant task (deployment, feature implementation, etc.)
            - When you need guidance on project conventions
            - When you want to ensure compliance with established decisions

            The response includes:
            - agent: The specialized agent prompt for this task type
            - decisions: Relevant architectural/process decisions
            - constraints: Things you MUST do or MUST NOT do
            - checklist: Step-by-step procedure
            - codebase_context: Relevant files and current state
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "description": "The user's request or task description (e.g., 'deploy backend to production')"
                },
                "target": {
                    "type": "string",
                    "description": "What is being worked on (backend, frontend, database, etc.)"
                },
                "environment": {
                    "type": "string",
                    "description": "Target environment if relevant (dev, staging, production)"
                },
                "additional_context": {
                    "type": "object",
                    "description": "Any additional context (version, branch, etc.)"
                }
            },
            "required": ["intent"]
        }
    },

    {
        "name": "mantra_validate_actions",
        "description": """
            Validate proposed actions against MANTRA decisions.

            Before executing significant actions, use this to check if they
            comply with established decisions and constraints.

            Returns:
            - valid: Whether the actions are allowed
            - violations: Any decisions or constraints violated
            - warnings: Advisory notes
            - suggestions: How to make actions compliant
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_type": {
                    "type": "string",
                    "description": "Type of task (DEPLOYMENT, DEVELOPMENT, DATABASE, etc.)"
                },
                "proposed_actions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of actions you plan to take"
                }
            },
            "required": ["task_type", "proposed_actions"]
        }
    },

    {
        "name": "mantra_list_agents",
        "description": """
            List all available task agents.

            Use this to discover what specialized agents are available
            for different task types.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["infrastructure", "development", "quality", "workflow", "all"],
                    "description": "Filter by agent category"
                }
            }
        }
    },

    {
        "name": "mantra_get_checklist",
        "description": """
            Get the checklist for a specific task type.

            Returns a step-by-step checklist with commands
            that should be executed for the task.
        """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_type": {
                    "type": "string",
                    "description": "Type of task (deployment, database-migration, etc.)"
                },
                "target": {
                    "type": "string",
                    "description": "Target system (backend, frontend, etc.)"
                }
            },
            "required": ["task_type"]
        }
    }
]
```

---

## Example Responses

### Claude Code MCP Response

```json
{
  "task_context": {
    "agent": {
      "id": "deployment-agent",
      "name": "Deployment Agent",
      "version": "1.0.0"
    },

    "prompt": "# Deployment Agent\n\n## Current Task\n- Target: backend\n- Environment: production\n- Version: 1.0.6\n\n## Critical Rules\n- [blocking] NEVER deploy without passing tests\n- [blocking] NEVER skip health checks\n- [blocking] ALWAYS have rollback plan ready\n\n## Relevant Decisions\n\n### EVO-F15-001: Production Deployment via Nomad\nAll production deployments SHALL use HashiCorp Nomad for orchestration.\n\nConstraints:\n- REQUIREMENT: Nomad job file must be version controlled\n- REQUIREMENT: Health checks must be defined\n\n### CTL-F11-002: Deployment Security\nProduction deployments SHALL pass security scan before release.\n\n## Deployment Checklist\n1. [ ] Run tests: `bun test`\n2. [ ] Check migrations: `alembic check`\n3. [ ] Build image: `docker build -t arsaka-mantra-api:v1.0.6 .`\n4. [ ] Deploy: `nomad job run mantra-backend.nomad`\n5. [ ] Verify health: `curl http://31.97.111.175:8002/health`\n\n## Codebase Context\n- Deploy config: nomad/mantra-backend.nomad\n- Current version: 1.0.5\n- Last deployment: 2026-01-26",

    "decisions": [
      {
        "decision_id": "uuid-1",
        "decision_code": "EVO-F15-001",
        "statement": "All production deployments SHALL use HashiCorp Nomad",
        "group_id": "EVO",
        "feature_id": "F15",
        "constraints": [
          {"type": "REQUIREMENT", "statement": "Nomad job file must be version controlled"},
          {"type": "REQUIREMENT", "statement": "Health checks must be defined"}
        ]
      },
      {
        "decision_id": "uuid-2",
        "decision_code": "CTL-F11-002",
        "statement": "Production deployments SHALL pass security scan",
        "group_id": "CTL",
        "feature_id": "F11"
      }
    ],

    "constraints": {
      "prohibitions": [
        "NEVER deploy without passing tests",
        "NEVER skip health checks",
        "NEVER push directly to main without PR"
      ],
      "requirements": [
        "Use Nomad for deployment",
        "Define health checks",
        "Version control all configs"
      ],
      "limitations": []
    },

    "checklist": [
      {"id": "tests", "step": "Run all tests", "command": "bun test", "blocking": true},
      {"id": "migrations", "step": "Check migrations", "command": "alembic check", "blocking": true},
      {"id": "build", "step": "Build Docker image", "command": "docker build -t arsaka-mantra-api:v1.0.6 .", "blocking": true},
      {"id": "deploy", "step": "Deploy via Nomad", "command": "nomad job run nomad/mantra-backend.nomad", "blocking": true},
      {"id": "health", "step": "Verify health", "command": "curl -f http://31.97.111.175:8002/health", "blocking": true}
    ],

    "codebase_context": {
      "deploy_config": "nomad/mantra-backend.nomad",
      "dockerfile": "backend/Dockerfile",
      "current_version": "1.0.5",
      "last_deploy": "2026-01-26T10:30:00Z",
      "health_endpoint": "http://31.97.111.175:8002/health"
    }
  },

  "meta": {
    "agent_confidence": 0.95,
    "decisions_count": 8,
    "token_estimate": 2500,
    "assembly_time_ms": 45
  },

  "hints": {
    "tool_suggestions": [
      "Use mantra_validate_actions before executing commands",
      "Use mantra_get_decision for full decision details"
    ]
  }
}
```

---

## Summary

Key points dari MICS architecture:

1. **Universal Agent Format (UAF)** - Platform-agnostic agent definitions
2. **Context Assembly Pipeline** - 7-stage pipeline untuk assemble context
3. **Priority System** - Clear hierarchy ketika ada conflict
4. **Progressive Disclosure** - Minimal core context + on-demand retrieval
5. **Platform Adapters** - Convert UAF ke format native tiap platform
6. **Learning Loop** - Track usage untuk improve intent recognition
