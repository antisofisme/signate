# MANTRA Schema Version Matrix

This document describes the different schema versions in MANTRA and the migration path between them.

## Overview

MANTRA uses multiple schema versions optimized for different use cases:

| Version | File | Fields | Purpose |
|---------|------|--------|---------|
| **V2** | `schema_base.py` | ~80 | Extended fields, temporal validity |
| **V3** | `schema_v3.py` | 100+ | Full enhanced (CURRENT PRODUCTION) |
| **MCP** | `schema_mcp.py` | 24 | Minimal for AI context |

## Canonical Import Path

**Always import from `schema.py` facade:**

```python
# CORRECT - Use the facade
from core.domain.schema import (
    Decision,           # Alias for DecisionV3
    DecisionCreate,     # Alias for DecisionCreateV3
    DomainId, AspectId, # Enums
    Constraint,         # Sub-models
    AuthorshipMetadata, # Authorship info
    generate_decision_code,
)

# AVOID - Direct imports (for internal use only)
from core.domain.schema_v3 import DecisionV3
from core.domain.schema_mcp import MCPDecision
```

## Schema Comparison

### V3 (Production Schema)

The current production schema with all fields:

```
DecisionV3
├── Identity
│   ├── decision_id (UUID)
│   └── decision_code (human-readable)
├── Classification
│   ├── domain_id (INT, ARCH, CTL, EVO)
│   └── aspect_id (A01-A16)
├── Content - Layer A (Executive Summary)
│   ├── statement (10-200 words)
│   ├── rationale (20-500 words)
│   ├── constraints[] (Constraint model)
│   └── invariants[] (strings)
├── Content - Layer B (Detailed Specification)
│   ├── detailed_content (Markdown, unlimited)
│   ├── sections[] (ContentSection model)
│   └── content_summary (auto-generated)
├── Core Metadata
│   ├── scope (ORGANIZATION, DOMAIN, APPLICATION)
│   ├── blast_radius (LOW, MEDIUM, HIGH, CRITICAL)
│   ├── version (semver X.Y.Z)
│   ├── tags[] (area tags)
│   └── tech_stack[] (technologies)
├── Authorship
│   ├── created_by, created_at
│   └── approved_by, approved_at
├── Relations
│   ├── supersedes
│   ├── related_decisions[] (deprecated)
│   └── relations[] (typed Relation model)
├── V2 Enhancements
│   ├── temporal_validity (TemporalValidity)
│   ├── stakeholders[] (Stakeholder)
│   ├── approvals[] (ApprovalRecord)
│   ├── compliance_references[] (ComplianceReference)
│   ├── quality_metadata (QualityMetadata)
│   └── implementation_guidance (ImplementationGuidance)
└── V3 Enhancements
    ├── amendments[] (MetadataEnrichment - LAW §10.7 compliant)
    ├── constraint_relations[] (ConstraintRelation)
    ├── blocker_tracking[] (Blocker)
    ├── team_adoption[] (TeamAdoption)
    ├── notification_subscriptions[] (NotificationSubscription)
    ├── disambiguation_support (DisambiguationSupport)
    ├── coverage_registry (ExpectedCoverage)
    └── learning_paths[] (LearningPath)
```

### MCP Schema (AI-Optimized)

Minimal 24-field schema for AI context windows:

```
MCPDecision
├── Identity
│   ├── decision_id
│   └── decision_code
├── Classification
│   ├── domain_id, aspect_id
│   └── scope, blast_radius
├── Content (Summarized)
│   ├── statement
│   ├── rationale
│   └── constraints[] (MCPConstraint)
├── Metadata
│   ├── version
│   ├── validity (ACTIVE, SUPERSEDED, DEPRECATED)
│   ├── impact_level
│   ├── superseded_by
│   └── related_count
└── Summary
    ├── key_points[] (3-5 bullet points)
    └── embedding_text (optimized for vector search)
```

## Migration Paths

### V3 → MCP (Compression)

Use when: Injecting decisions into AI context

```python
from core.domain.schema import from_full_decision

# Convert V3 decision to MCP format
result = from_full_decision(decision_v3.model_dump(), strict=False)

if result.success:
    mcp_decision = result.decision
    # Use mcp_decision in AI context
else:
    # Handle conversion warnings
    for warning in result.warnings:
        print(f"Warning: {warning.message}")
```

### V1/V2 → V3 (Upgrade)

Use when: Migrating old decisions

```python
from core.domain.schema import migrate_to_current

# Migrate any version to V3
decision_v3 = migrate_to_current(old_decision_dict)
```

### Dict → V3 (Parsing)

Use when: Creating from API input

```python
from core.domain.schema import Decision, DecisionCreate

# From create DTO
create_dto = DecisionCreate(**request_data)

# To full decision
decision = Decision(
    decision_id=str(uuid.uuid4()),
    **create_dto.model_dump(),
    created_at=datetime.utcnow(),
)
```

## Field Compatibility Matrix

| Field | V2 | V3 | MCP | Notes |
|-------|:--:|:--:|:---:|-------|
| decision_id | ✓ | ✓ | ✓ | UUID |
| decision_code | ✓ | ✓ | ✓ | Human-readable |
| domain_id | ✓ | ✓ | ✓ | Enum |
| aspect_id | ✓ | ✓ | ✓ | Enum |
| statement | ✓ | ✓ | ✓ | |
| rationale | ✓ | ✓ | ✓ | |
| constraints | ✓ | ✓ | ✓ | Different models |
| invariants | ✓ | ✓ | - | Folded into key_points |
| scope | ✓ | ✓ | ✓ | |
| blast_radius | ✓ | ✓ | ✓ | |
| version | ✓ | ✓ | ✓ | |
| tags | ✓ | ✓ | - | |
| tech_stack | ✓ | ✓ | - | |
| supersedes | ✓ | ✓ | - | |
| relations | ✓ | ✓ | - | |
| temporal_validity | ✓ | ✓ | - | V2+ only |
| stakeholders | ✓ | ✓ | - | V2+ only |
| amendments | - | ✓ | - | V3 only |
| learning_paths | - | ✓ | - | V3 only |
| key_points | - | - | ✓ | MCP only |
| embedding_text | - | - | ✓ | MCP only |

## Enum Mappings

### DomainId (4 domains)

```python
DomainId.INT   # Intent and Direction (WHY/WHAT)
DomainId.ARCH  # Architecture and Boundaries (HOW/WHERE)
DomainId.CTL   # Control, Policy and Risk (CAN/MUST NOT)
DomainId.EVO   # Execution and Evolution (CHANGE SAFELY)
```

### AspectId (16 aspects)

```python
# DOMAIN-1 (INT)
AspectId.A01  # Vision and Outcome
AspectId.A02  # Problem Statement
AspectId.A03  # Scope and Non-Goals
AspectId.A04  # Principles and Values

# DOMAIN-2 (ARCH)
AspectId.A05  # Domain and Bounded Context
AspectId.A06  # Service and Module Boundary
AspectId.A07  # Data Ownership and Sovereignty
AspectId.A08  # Integration and Contract Model

# DOMAIN-3 (CTL)
AspectId.A09  # Policy and Rules
AspectId.A10  # Approval and Authority Model
AspectId.A11  # Security and Compliance Posture
AspectId.A12  # Risk and Blast Radius

# DOMAIN-4 (EVO)
AspectId.A13  # Decision Lifecycle
AspectId.A14  # Reversibility and Exit Strategy
AspectId.A15  # Environment and Promotion Rules
AspectId.A16  # Anti-Drift and Consistency
```

### Constraint Type Mapping (V3 ↔ MCP)

```python
CONSTRAINT_TYPE_MAPPING = {
    ConstraintType.PROHIBITION: "MUST_NOT",
    ConstraintType.REQUIREMENT: "MUST",
    ConstraintType.LIMITATION: "MAY_WITH_CONDITIONS",
    ConstraintType.PREFERENCE: "SHOULD",
    ConstraintType.EXCEPTION: "EXCEPT_WHEN",
}
```

## Best Practices

### 1. Always Use the Facade

```python
# ✅ Good
from core.domain.schema import Decision, DomainId

# ❌ Avoid
from core.domain.schema_v3 import DecisionV3
```

### 2. Use MCP for AI Context

```python
# When injecting into LLM context:
mcp_decisions = [from_full_decision(d).decision for d in decisions]
context = format_for_llm(mcp_decisions)
```

### 3. Validate Before Storage

```python
from core.use_cases.validate_decision import validate_decision

result = validate_decision(decision_dict)
if result.status == ValidationStatus.PASS:
    await store_decision(decision_dict)
```

### 4. Handle Migration Warnings

```python
result = from_full_decision(v3_decision, strict=False)
if result.warnings:
    for w in result.warnings:
        logger.warning(f"Field {w.field}: {w.message}")
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| V1 | 2024-01 | Initial schema (deprecated) |
| V2 | 2024-03 | Temporal validity, governance |
| V3 | 2024-06 | Full enhanced, LAW §10.7 compliant |
| MCP | 2024-06 | AI-optimized 24-field schema |
| schema.py | 2024-12 | Facade consolidation |

## Related Documentation

- `MANTRA-LAW-001.md` - Constitutional Law
- `MANTRA-SCHEMA-001.md` - Schema Specification
- `field_meta.py` - Field Metadata per LAW AMENDMENT-004
- `validator.py` - Three-Gate Validation System
