# MANTRA Intelligent Context System (MICS)

## Vision

MANTRA bukan hanya database decision, tapi **Intelligent Context Orchestrator** yang:
1. Menyediakan constitutional rules ke AI assistants
2. Meng-inject task-specific agent prompts
3. Menjaga konsistensi across different AI platforms
4. Mencegah hallucination dengan grounding ke real decisions

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                              USER REQUEST                                       │
│                     "Deploy backend to production"                              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         AI ASSISTANT (Any Platform)                             │
│                    Claude Code / Cursor / OpenAI / Gemini                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Platform-specific layer:                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ Claude: claude.md + skills + MCP                                         │   │
│  │ Cursor: .cursorrules + context                                           │   │
│  │ OpenAI: Custom Instructions + Functions                                  │   │
│  │ Gemini: System Instructions + Tools                                      │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         MCP / API CALL                                   │   │
│  │                                                                          │   │
│  │   mantra_get_task_context({                                              │   │
│  │     "intent": "deploy backend to production",                            │   │
│  │     "platform": "claude-code",                                           │   │
│  │     "project": "signate"                                                 │   │
│  │   })                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                                                                 │
│                    MANTRA INTELLIGENT CONTEXT SYSTEM                            │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │                     1. INTENT RECOGNIZER                                   │ │
│  │                                                                            │ │
│  │  Input: "deploy backend to production"                                     │ │
│  │  Output:                                                                   │ │
│  │    - task_type: DEPLOYMENT                                                 │ │
│  │    - target: backend                                                       │ │
│  │    - environment: production                                               │ │
│  │    - risk_level: HIGH                                                      │ │
│  │                                                                            │ │
│  │  Methods:                                                                  │ │
│  │    - Keyword matching (fast)                                               │ │
│  │    - Semantic similarity (accurate)                                        │ │
│  │    - LLM classification (complex cases)                                    │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                          │
│                                      ▼                                          │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │                     2. CONTEXT ASSEMBLER                                   │ │
│  │                                                                            │ │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │ │
│  │  │ Decision Store  │  │ Agent Registry  │  │ Codebase Index  │            │ │
│  │  │                 │  │                 │  │                 │            │ │
│  │  │ - EVO decisions │  │ - deploy-agent  │  │ - nomad/*.nomad │            │ │
│  │  │ - CTL decisions │  │ - prompts       │  │ - Dockerfile    │            │ │
│  │  │ - Constraints   │  │ - checklists    │  │ - configs       │            │ │
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │ │
│  │           │                    │                    │                      │ │
│  │           └────────────────────┼────────────────────┘                      │ │
│  │                                ▼                                           │ │
│  │                    ┌─────────────────────┐                                 │ │
│  │                    │   MERGED CONTEXT    │                                 │ │
│  │                    └─────────────────────┘                                 │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                      │                                          │
│                                      ▼                                          │
│  ┌───────────────────────────────────────────────────────────────────────────┐ │
│  │                     3. PLATFORM ADAPTER                                    │ │
│  │                                                                            │ │
│  │  Input: Merged context + target platform                                   │ │
│  │  Output: Platform-optimized context                                        │ │
│  │                                                                            │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │ │
│  │  │ Claude      │ │ OpenAI      │ │ Cursor      │ │ Generic     │          │ │
│  │  │ Adapter     │ │ Adapter     │ │ Adapter     │ │ Adapter     │          │ │
│  │  │             │ │             │ │             │ │             │          │ │
│  │  │ Output:     │ │ Output:     │ │ Output:     │ │ Output:     │          │ │
│  │  │ MCP-native  │ │ Function    │ │ .cursor     │ │ Markdown    │          │ │
│  │  │ response    │ │ response    │ │ rules       │ │ prompt      │          │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │ │
│  └───────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            RESPONSE TO AI ASSISTANT                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  {                                                                              │
│    "agent": {                                                                   │
│      "name": "deployment-agent",                                                │
│      "prompt": "You are deploying to production. Critical rules:\n..."         │
│    },                                                                           │
│                                                                                 │
│    "decisions": [                                                               │
│      {                                                                          │
│        "code": "EVO-F15-001",                                                   │
│        "statement": "Production deployments SHALL use Nomad...",                │
│        "constraints": [...]                                                     │
│      }                                                                          │
│    ],                                                                           │
│                                                                                 │
│    "checklist": [                                                               │
│      "□ Run tests: bun test",                                                   │
│      "□ Check migrations: alembic check",                                       │
│      "□ Build image: docker build...",                                          │
│      "□ Deploy: nomad job run..."                                               │
│    ],                                                                           │
│                                                                                 │
│    "prohibitions": [                                                            │
│      "NEVER push directly to main without PR",                                  │
│      "NEVER deploy without passing tests"                                       │
│    ],                                                                           │
│                                                                                 │
│    "codebase_context": {                                                        │
│      "deploy_config": "nomad/mantra-backend.nomad",                             │
│      "current_version": "1.0.5",                                                │
│      "last_deploy": "2026-01-26"                                                │
│    }                                                                            │
│  }                                                                              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Task Agent Registry

Agents are specialized prompts + configurations for specific task types.

```yaml
# agents/deployment-agent.yaml
agent_id: deployment-agent
name: Deployment Agent
version: 1.0.0

# When to activate this agent
triggers:
  keywords:
    - deploy
    - release
    - ship
    - push to prod
    - production
  intents:
    - DEPLOYMENT
    - RELEASE
    - ROLLOUT

# Which MANTRA decisions to consider
context_sources:
  decision_groups:
    - EVO  # Execution & Evolution
    - CTL  # Control & Policy
  decision_features:
    - F13  # Decision Lifecycle
    - F14  # Reversibility & Exit Strategy
    - F15  # Environment & Promotion Rules
    - F11  # Security & Compliance
  decision_tags:
    - INFRA
    - CICD
    - DEVOPS

# The agent prompt template
prompt_template: |
  # Deployment Agent

  You are executing a production deployment. Follow these rules strictly:

  ## Critical Constraints
  {{#each constraints}}
  - {{type}}: {{statement}}
  {{/each}}

  ## Deployment Procedure
  {{#each checklist}}
  {{@index}}. {{step}}
  {{/each}}

  ## Relevant Decisions
  {{#each decisions}}
  - **{{code}}**: {{statement}}
  {{/each}}

  ## Current Codebase State
  - Deploy config: {{codebase.deploy_config}}
  - Current version: {{codebase.current_version}}
  - Target: {{target}}
  - Environment: {{environment}}

# Checklist for this task type
checklist:
  - step: "Run all tests"
    command: "bun test"
    blocking: true
  - step: "Check database migrations"
    command: "alembic check"
    blocking: true
  - step: "Build Docker image"
    command: "docker build -t {{image_name}}:{{version}} ."
    blocking: true
  - step: "Deploy via Nomad"
    command: "nomad job run {{nomad_file}}"
    blocking: true
  - step: "Verify deployment health"
    command: "curl {{health_endpoint}}"
    blocking: true
  - step: "Update version tracking"
    blocking: false

# Validation rules
validation:
  pre_deploy:
    - tests_pass: true
    - migrations_clean: true
    - no_uncommitted_changes: true
  post_deploy:
    - health_check_pass: true
    - no_errors_in_logs: true
```

### 2. Agent Types

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            AGENT REGISTRY                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  INFRASTRUCTURE AGENTS                                                          │
│  ├── deployment-agent      → Deploy to staging/production                       │
│  ├── database-agent        → Migrations, schema changes                         │
│  ├── docker-agent          → Container management                               │
│  └── infra-agent           → Infrastructure changes                             │
│                                                                                 │
│  DEVELOPMENT AGENTS                                                             │
│  ├── frontend-agent        → React, UI development                              │
│  ├── backend-agent         → FastAPI, Python development                        │
│  ├── api-agent             → API design and implementation                      │
│  └── database-model-agent  → SQLAlchemy models, queries                         │
│                                                                                 │
│  QUALITY AGENTS                                                                 │
│  ├── review-agent          → Code review                                        │
│  ├── test-agent            → Test writing                                       │
│  ├── security-agent        → Security audit                                     │
│  └── performance-agent     → Performance optimization                           │
│                                                                                 │
│  WORKFLOW AGENTS                                                                │
│  ├── planning-agent        → Task planning                                      │
│  ├── documentation-agent   → Doc writing                                        │
│  └── refactor-agent        → Code refactoring                                   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Context Priority System

When multiple sources provide instructions, use this priority:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         CONTEXT PRIORITY (Highest → Lowest)                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  LEVEL 0: MANTRA CORE PRINCIPLES (IMMUTABLE)                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ - AI = ZERO for decision authorship                                      │   │
│  │ - HUMAN ONLY for constitutional changes                                  │   │
│  │ - Security constraints                                                   │   │
│  │ These CANNOT be overridden by any other context                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  LEVEL 1: MANTRA DECISIONS (APPEND-ONLY)                                        │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ - Architectural decisions                                                │   │
│  │ - Technology choices                                                     │   │
│  │ - Process requirements                                                   │   │
│  │ Can only be changed via supersedes mechanism                             │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  LEVEL 2: TASK AGENT PROMPTS                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ - Task-specific instructions                                             │   │
│  │ - Checklists and procedures                                              │   │
│  │ - Best practices for task type                                           │   │
│  │ Must not conflict with Level 0/1                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  LEVEL 3: PLATFORM INSTRUCTIONS                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ - claude.md                                                              │   │
│  │ - .cursorrules                                                           │   │
│  │ - Custom GPT instructions                                                │   │
│  │ Can be enhanced by MANTRA, not overridden                                │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  LEVEL 4: CODEBASE PATTERNS                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ - Existing code patterns                                                 │   │
│  │ - File structure conventions                                             │   │
│  │ - Dependency versions                                                    │   │
│  │ Should follow, unless MANTRA says otherwise                              │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  LEVEL 5: USER PREFERENCES                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │ - Runtime preferences                                                    │   │
│  │ - Session-specific overrides                                             │   │
│  │ Lowest priority, can adjust non-critical aspects                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4. Context Window Optimization

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      CONTEXT WINDOW STRATEGY                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  Problem: AI context windows are limited (8K-200K tokens)                       │
│  Solution: Progressive disclosure with on-demand retrieval                      │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                     ALWAYS INCLUDE (Core Context)                        │   │
│  │                         ~500-1000 tokens                                 │   │
│  │                                                                          │   │
│  │  - Active agent prompt (condensed)                                       │   │
│  │  - Critical PROHIBITIONS                                                 │   │
│  │  - Immediate checklist steps                                             │   │
│  │  - Current task summary                                                  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                   INCLUDE IF RELEVANT (Dynamic Context)                  │   │
│  │                         ~1000-3000 tokens                                │   │
│  │                                                                          │   │
│  │  - Decisions matching current task (top 5-10)                            │   │
│  │  - Related codebase files (summaries)                                    │   │
│  │  - Recent related decisions                                              │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                          │
│                                      ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                   AVAILABLE ON-DEMAND (MCP Tools)                        │   │
│  │                         Retrieved as needed                              │   │
│  │                                                                          │   │
│  │  - Full decision details: mantra_get_decision(id)                        │   │
│  │  - Decision search: mantra_search(query)                                 │   │
│  │  - Relation graph: mantra_get_relations(id)                              │   │
│  │  - Historical context: mantra_get_history(id)                            │   │
│  │  - Validation: mantra_validate(proposal)                                 │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  FLOW:                                                                          │
│  1. AI receives task with core context                                          │
│  2. AI identifies if more context needed                                        │
│  3. AI calls MANTRA MCP tools to retrieve specific context                      │
│  4. AI continues with enriched understanding                                    │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Platform Adapters

### Claude Code (MCP)

```typescript
// MCP Tool: mantra_get_task_context
{
  name: "mantra_get_task_context",
  description: `
    Get intelligent context for a task. MANTRA will:
    1. Recognize task intent
    2. Load appropriate agent prompt
    3. Find relevant decisions
    4. Provide checklist and constraints

    Call this at the START of any significant task.
  `,
  inputSchema: {
    type: "object",
    properties: {
      intent: {
        type: "string",
        description: "The user's request or task description"
      },
      target: {
        type: "string",
        description: "What is being worked on (backend, frontend, etc.)"
      },
      additional_context: {
        type: "object",
        description: "Any additional context"
      }
    },
    required: ["intent"]
  }
}
```

### Cursor (.cursorrules)

```markdown
# MANTRA Integration for Cursor

## Auto-Injected Rules from MANTRA

### Core Principles
- AI = ZERO for decision authorship
- Follow established architectural decisions
- Validate against MANTRA before implementation

### Active Agent: {agent_name}
{agent_prompt}

### Relevant Decisions
{decisions_markdown}

### Constraints
{constraints_markdown}

### Checklist
{checklist_markdown}
```

### OpenAI (Function Calling)

```json
{
  "name": "get_mantra_context",
  "description": "Retrieve project context and constraints from MANTRA",
  "parameters": {
    "type": "object",
    "properties": {
      "task_type": {
        "type": "string",
        "enum": ["DEPLOYMENT", "FRONTEND", "BACKEND", "DATABASE", "REVIEW"]
      },
      "target": {
        "type": "string"
      }
    }
  }
}
```

### Generic (Markdown Export)

For platforms without direct integration, export as markdown:

```markdown
# Task Context from MANTRA

## Agent: Deployment Agent

You are deploying to production. Follow these rules:

## Decisions to Follow
- EVO-F15-001: Production deployments SHALL use Nomad...

## Constraints
- PROHIBITION: Direct push to main without PR
- REQUIREMENT: All tests must pass

## Checklist
1. [ ] Run tests
2. [ ] Build image
3. [ ] Deploy
4. [ ] Verify
```

---

## Data Model

### Agent Definition

```python
@dataclass
class TaskAgent:
    agent_id: str
    name: str
    version: str

    # Triggers
    trigger_keywords: List[str]
    trigger_intents: List[str]

    # Context sources
    decision_groups: List[str]
    decision_features: List[str]
    decision_tags: List[str]

    # Templates
    prompt_template: str
    checklist: List[ChecklistItem]

    # Validation
    pre_conditions: List[ValidationRule]
    post_conditions: List[ValidationRule]

    # Metadata
    created_by: str
    created_at: datetime
    version_history: List[AgentVersion]
```

### Context Response

```python
@dataclass
class TaskContext:
    # Task identification
    task_type: str
    intent: str
    target: Optional[str]
    environment: Optional[str]

    # Agent
    agent: TaskAgent
    rendered_prompt: str

    # Decisions
    relevant_decisions: List[Decision]
    constraints: List[Constraint]
    prohibitions: List[str]

    # Checklist
    checklist: List[ChecklistItem]

    # Codebase
    codebase_context: Dict[str, Any]

    # Metadata
    priority_order: List[str]
    context_token_estimate: int
```

---

## API Endpoints

### REST API

```
POST /api/v1/context/task
  Request:
    {
      "intent": "deploy backend to production",
      "platform": "claude-code",
      "project": "signate"
    }
  Response:
    TaskContext (JSON)

GET /api/v1/agents
  List all available agents

GET /api/v1/agents/{agent_id}
  Get specific agent configuration

POST /api/v1/agents
  Create new agent (HUMAN ONLY)

GET /api/v1/context/export/{format}
  Export context in specific format (cursorrules, markdown, etc.)
```

### MCP Tools

```
mantra_get_task_context(intent, target?, context?)
  → TaskContext

mantra_list_agents()
  → List[AgentSummary]

mantra_get_agent(agent_id)
  → TaskAgent

mantra_validate_task(task_description, proposed_actions)
  → ValidationResult

mantra_get_checklist(task_type)
  → List[ChecklistItem]
```

---

## Implementation Phases

### Phase 1: Agent Registry (Week 1)
- [ ] Create Agent model and database schema
- [ ] Build agent CRUD API
- [ ] Create initial agents: deployment, frontend, backend
- [ ] Agent validation rules

### Phase 2: Intent Recognition (Week 1-2)
- [ ] Keyword-based intent recognition
- [ ] Intent-to-agent mapping
- [ ] Fallback to semantic search

### Phase 3: Context Assembly (Week 2)
- [ ] Decision retrieval by agent config
- [ ] Template rendering with Jinja2/Handlebars
- [ ] Checklist generation
- [ ] Codebase context extraction

### Phase 4: Platform Adapters (Week 2-3)
- [ ] Claude MCP adapter
- [ ] Generic markdown adapter
- [ ] Cursor rules adapter
- [ ] OpenAI function adapter

### Phase 5: Integration & Testing (Week 3)
- [ ] End-to-end testing
- [ ] Context window optimization
- [ ] Performance tuning
- [ ] Documentation

---

## Success Metrics

1. **Consistency**: Same task produces consistent results across platforms
2. **Accuracy**: AI follows MANTRA decisions without hallucination
3. **Speed**: Context retrieval < 200ms
4. **Coverage**: 90%+ of common tasks have appropriate agents
5. **Adoption**: AI assistants proactively use MANTRA context

---

## Example Flow: Deploy Backend

```
USER: "Deploy the MANTRA backend to production"

AI ASSISTANT (Claude Code):
  1. Recognizes deployment task
  2. Calls mantra_get_task_context({
       intent: "deploy MANTRA backend to production",
       target: "backend",
       platform: "claude-code"
     })

MANTRA RESPONSE:
  {
    agent: "deployment-agent",
    prompt: "You are deploying to production...",
    decisions: [
      "EVO-F15-001: Use Nomad for deployments",
      "CTL-F11-002: Production requires approval"
    ],
    constraints: [
      "PROHIBITION: No direct push to main",
      "REQUIREMENT: Tests must pass"
    ],
    checklist: [
      "1. Run tests",
      "2. Build image",
      "3. Deploy via Nomad",
      "4. Verify health"
    ],
    codebase_context: {
      nomad_file: "nomad/mantra-backend.nomad",
      current_version: "1.0.5"
    }
  }

AI ASSISTANT:
  Now executes deployment following the provided context,
  checking off items and respecting constraints.
```

---

## Future Enhancements

1. **Learning**: Track which decisions are frequently referenced per task type
2. **Auto-suggestion**: Suggest new agents based on usage patterns
3. **Conflict detection**: Warn when task might violate decisions
4. **Multi-project**: Support different MANTRA instances per project
5. **Version sync**: Keep agent prompts in sync with decision updates
