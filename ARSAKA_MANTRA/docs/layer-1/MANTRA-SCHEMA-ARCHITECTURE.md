# MANTRA Schema Architecture

**Document Type**: Technical Architecture
**Version**: 1.0.0
**Status**: ACTIVE
**Purpose**: Define the 3-tier schema architecture for MANTRA decision management

---

## Overview

MANTRA uses a **3-tier schema architecture** to serve different use cases optimally:

| Tier | Schema | Fields | Purpose | Token Budget |
|------|--------|--------|---------|--------------|
| **Tier 1** | `MCPDecision` | 18 | AI Context (MCP) | ~500-1500 tokens |
| **Tier 2** | `DecisionV3` | 100+ | UI/Dashboard | N/A |
| **Tier 3** | Separate Tables | Variable | Analytics/Tracking | N/A |

---

## Tier 1: MCP Core Schema (18 Fields)

### Purpose
Minimal schema for AI assistants (Claude Code, IDE AIs) via Model Context Protocol.

### Design Principles
1. **Token Budget**: Fit within ~3000 token context window
2. **Flat Structure**: No deep nesting (max 1 level)
3. **Direct Access**: Fields named for immediate comprehension
4. **LAW Compliant**: Uses 4×4 taxonomy (Domain/Aspect)

### Fields

| Category | Field | Type | Required | Description |
|----------|-------|------|----------|-------------|
| **Identity** | `decision_id` | UUID | Yes | Primary key |
| | `code` | string | Yes | Human-readable: ARCH-A06-001 |
| | `version` | string | Yes | Semantic version X.Y.Z |
| **Classification** | `domain_id` | enum | Yes | LAW §3: INT, ARCH, CTL, EVO |
| | `aspect_id` | enum | Yes | LAW §3: A01-A16 |
| | `status` | enum | No | ACTIVE/SUPERSEDED/SUNSET |
| **Content** | `statement` | string | Yes | WHAT (1-3 sentences) |
| | `rationale` | string | Yes | WHY (max 500 words) |
| | `constraints` | list | No | MUST/SHOULD rules |
| | `invariants` | list | No | Always-true assertions |
| **Context** | `applies_to` | list | No | File patterns, keywords |
| | `examples` | list | No | Good/bad examples |
| | `tags` | list | No | Searchable tags |
| **Authorship** | `authored_by` | string | Yes | Human author (LAW §2.3) |
| | `authored_at` | datetime | Yes | When approved |
| | `content_by` | string | No | Content generator (AI/human) |
| **Retrieval** | `impact` | enum | No | CRITICAL/IMPORTANT/REFERENCE |
| | `summary` | string | Yes | One-line summary |

### Token Budget Tiers

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Context Window                         │
│                      (~3000 tokens)                          │
├─────────────────────────────────────────────────────────────┤
│  CRITICAL (~500 tokens)                                      │
│  └─ Always included, foundational decisions                  │
├─────────────────────────────────────────────────────────────┤
│  IMPORTANT (~1500 tokens)                                    │
│  └─ Included when context matches (keywords, file patterns)  │
├─────────────────────────────────────────────────────────────┤
│  REFERENCE (on-demand)                                       │
│  └─ Retrieved only when explicitly requested                 │
└─────────────────────────────────────────────────────────────┘
```

### Usage Example

```python
from domain import MCPDecision, MCPDecisionCollection, ImpactLevel, DomainId, AspectId

# Create decision
decision = MCPDecision(
    code="ARCH-A06-001",
    version="1.0.0",
    domain_id=DomainId.ARCH,
    aspect_id=AspectId.A06,
    statement="All frontend projects MUST use feature-based folder structure.",
    rationale="Improves discoverability and enables lazy loading.",
    constraints=[
        {"id": "C-001", "type": "MUST", "rule": "Each feature has its own folder"},
    ],
    authored_by="john.doe@company.com",
    content_by="ai:claude-opus-4-5",
    impact=ImpactLevel.CRITICAL,
    summary="Use feature-based folder structure for React projects"
)

# Get context for AI injection
context_text = decision.to_context_text(level="standard")

# Collection with budget management
collection = MCPDecisionCollection([decision])
relevant = collection.get_context_window(
    max_tokens=3000,
    keywords=["react", "frontend"],
    file_path="src/features/auth/LoginForm.tsx"
)
```

---

## Tier 2: Full Schema (100+ Fields)

### Purpose
Complete schema for dashboard, admin UI, and human consumption.

### Design Principles
1. **Rich Metadata**: Full governance, compliance, tracking
2. **Nested Structures**: Complex sub-models for detailed info
3. **Backward Compatible**: All v1/v2 fields preserved
4. **Human-Friendly**: Designed for UI forms and reports

### Field Categories

| Category | Field Count | Examples |
|----------|-------------|----------|
| Identity | 2 | decision_id, decision_code |
| Classification | 2 | domain_id, aspect_id |
| Core Content | 4 | statement, rationale, constraints, invariants |
| Extended Content | 3 | detailed_content, sections, content_summary |
| Metadata | 5 | scope, blast_radius, version, tags, tech_stack |
| Authorship | 4 | created_by, created_at, approved_by, approved_at |
| Relations | 3 | supersedes, related_decisions, relations |
| Temporal | 1 | temporal_validity |
| Governance | 4 | stakeholders, approvals, approval_workflow |
| Compliance | 2 | compliance_references, audit_trail_id |
| Versioning | 4 | change_type, change_summary, migration_guide, breaking_changes |
| Quality | 1 | quality_metadata |
| Implementation | 3 | implementation_guidance, anti_patterns |
| Knowledge | 1 | knowledge_consumption |
| Applicability | 1 | applicability |
| Traceability | 1 | code_artifacts |
| Search | 1 | search_metadata |
| LLM | 1 | llm_optimization |
| Causality | 1 | trigger_event |
| Progress | 1 | implementation_status |
| Stability | 1 | stability |
| Impact | 1 | impact_analysis |
| Analytics | 1 | usage_analytics |
| Enrichments | 2 | amendments, stale_reference_warnings |
| Summary | 1 | structured_summary |
| Embedding | 1 | embedding_metadata |
| Adoption | 4 | team_adoptions, adoption_target, adoption_timeline |
| Blockers | 1 | structured_blockers |
| Disambiguation | 2 | disambiguation, query_hints |
| Enhanced | 3 | enhanced_implementation, rollback_history, enhanced_stability |

### Migration

```python
from domain import DecisionV3, from_full_decision, MCPDecision

# Full schema → MCP schema
full_decision = DecisionV3(...)  # 100+ fields
mcp_decision = from_full_decision(full_decision.model_dump())  # 18 fields
```

---

## Tier 3: Analytics Tables (Separate)

### Purpose
Mutable operational data stored separately from immutable decisions.

### Design Principles
1. **Separation**: Per LAW §4.5, implementation status ≠ decision validity
2. **Mutable**: Can be updated without creating new decision versions
3. **Reference Only**: Links to decisions by ID, never embeds

### Tables

| Table | Purpose | LAW Reference |
|-------|---------|---------------|
| `decision_team_adoptions` | Team adoption tracking | §4.5.2 |
| `decision_blockers` | Implementation blockers | §4.5.3 |
| `metadata_enrichments` | Enrichment audit trail | §10.7 |
| `decision_usage_analytics` | Retrieval/access stats | - |
| `decision_embeddings` | Vector embeddings | §6.5 |

### Schema Example

```sql
-- Team adoption (separate from decision)
CREATE TABLE decision_team_adoptions (
    id UUID PRIMARY KEY,
    decision_id UUID REFERENCES decisions(decision_id),
    team_id VARCHAR(100) NOT NULL,
    team_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- NOT_STARTED, IN_PROGRESS, COMPLETED
    progress_percentage INT DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Metadata enrichment (immutable per §10.7.4)
CREATE TABLE metadata_enrichments (
    enrichment_id UUID PRIMARY KEY,
    decision_id UUID REFERENCES decisions(decision_id),
    field_path VARCHAR(255) NOT NULL,
    enrichment_value JSONB NOT NULL,
    reason TEXT NOT NULL,
    enriched_by VARCHAR(255) NOT NULL,  -- Can be ai:*
    enriched_at TIMESTAMP NOT NULL,
    approved_by VARCHAR(255) NOT NULL,  -- Must be human
    approved_at TIMESTAMP NOT NULL,
    -- Immutable: no is_active, no reverted_at
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Taxonomy (4 Domains × 4 Aspects per Domain = 16)

### Domain-Aspect Matrix

```
         A01    A02    A03    A04    A05    A06    A07    A08
INT      ✓      ✓      ✓      ✓      -      -      -      -
ARCH     -      -      -      -      ✓      ✓      ✓      ✓
CTL      -      -      -      -      -      -      -      -
EVO      -      -      -      -      -      -      -      -

         A09    A10    A11    A12    A13    A14    A15    A16
INT      -      -      -      -      -      -      -      -
ARCH     -      -      -      -      -      -      -      -
CTL      ✓      ✓      ✓      ✓      -      -      -      -
EVO      -      -      -      -      ✓      ✓      ✓      ✓
```

### Domain Definitions (LAW §3)

| Domain | Code | Scope | Aspects |
|--------|------|-------|---------|
| Intent & Direction | `INT` | WHY/WHAT | A01-A04 |
| Architecture & Boundaries | `ARCH` | HOW/WHERE | A05-A08 |
| Control, Policy & Risk | `CTL` | CAN/MUST NOT | A09-A12 |
| Execution & Evolution | `EVO` | CHANGE SAFELY | A13-A16 |

### Aspect Definitions

| Aspect | Name | Domain |
|--------|------|--------|
| A01 | Vision & Outcome | INT |
| A02 | Problem Statement | INT |
| A03 | Scope & Non-Goals | INT |
| A04 | Principles & Values | INT |
| A05 | Domain & Bounded Context | ARCH |
| A06 | Service & Module Boundary | ARCH |
| A07 | Data Ownership & Sovereignty | ARCH |
| A08 | Integration & Contract Model | ARCH |
| A09 | Policy & Rules | CTL |
| A10 | Approval & Authority Model | CTL |
| A11 | Security & Compliance Posture | CTL |
| A12 | Risk & Blast Radius | CTL |
| A13 | Decision Lifecycle | EVO |
| A14 | Reversibility & Exit Strategy | EVO |
| A15 | Environment & Promotion Rules | EVO |
| A16 | Anti-Drift & Consistency | EVO |

---

## Implementation Notes

### 1. MCP Server Integration

```python
# MCP Resource Provider
@mcp_server.list_resources()
async def list_decisions():
    decisions = await db.get_active_decisions()
    collection = MCPDecisionCollection([
        from_full_decision(d) for d in decisions
    ])
    return collection.to_mcp_resources()

# MCP Tool for context
@mcp_server.tool("get_decision_context")
async def get_context(file_path: str = None, keywords: list = None):
    decisions = await db.get_active_decisions()
    collection = MCPDecisionCollection([
        from_full_decision(d) for d in decisions
    ])
    return collection.get_combined_context(
        max_tokens=3000,
        keywords=keywords,
        file_path=file_path
    )
```

### 2. Dashboard Integration

```python
# Dashboard uses full schema
@router.get("/decisions/{id}")
async def get_decision(id: str):
    decision = await db.get_decision(id)
    return DecisionV3(**decision)  # Full 100+ fields

# MCP endpoint uses minimal schema
@router.get("/mcp/decisions/{id}")
async def get_mcp_decision(id: str):
    decision = await db.get_decision(id)
    return from_full_decision(decision)  # 18 fields
```

### 3. Token Budget Management

```python
def get_context_for_ai(file_path: str, keywords: list) -> str:
    """Get decisions for AI context with token budget."""
    decisions = db.get_active_decisions()
    collection = MCPDecisionCollection([
        from_full_decision(d) for d in decisions
    ])

    # Get within budget
    relevant = collection.get_context_window(
        max_tokens=3000,
        keywords=keywords,
        file_path=file_path
    )

    # Format for injection
    return collection.get_combined_context(level="standard")
```

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-01-29 | Initial 3-tier architecture definition |

---

**END OF DOCUMENT**
