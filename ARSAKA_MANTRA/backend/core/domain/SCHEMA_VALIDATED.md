# MCPDecision Schema v2.1 - Validated Design

## Summary

The 21-field MCPDecision schema has been validated through stress testing for 3 core use cases:
1. **AI Retriever** - Token-efficient context injection
2. **PRD/Spec Export** - Complete documentation generation
3. **Relationship Tracking** - Dependencies, conflicts, supersedes chains

## Stress Test Results (100% Pass Rate)

```
AI Retriever Tests:
✓ Token budget (LIST): 304/1500 tokens, 8 decisions
✓ Token budget (ENFORCE): 656/1500 tokens, 8 decisions
✓ Token budget (UNDERSTAND): 744/1500 tokens, 8 decisions
✓ Token budget (FULL): 1500/1500 tokens, 3 decisions
✓ Relevance precision: 100%
✓ Dependency resolution: All resolved

PRD Export Tests:
✓ Completeness: 0 issues
✓ Hierarchy: 100% domain coverage
✓ Markdown export: 14KB generated

Relationship Tests:
✓ Circular deps: 0 cycles
✓ Supersedes chain: Valid (max depth 4)
✓ Graph integrity: 50 nodes, 42 edges
```

## Schema Fields (21 Total)

### Identity (3)
| Field | Type | Description |
|-------|------|-------------|
| `decision_id` | UUID | Primary key |
| `code` | string | Human-readable code: DOMAIN-ASPECT-SEQ |
| `version` | string | Semantic version X.Y.Z |

### Classification (3)
| Field | Type | Description |
|-------|------|-------------|
| `domain_id` | enum | INT, ARCH, CTL, EVO |
| `aspect_id` | enum | A01-A16 |
| `validity_state` | enum | CURRENT, SUPERSEDED, EXPIRED (computed) |

### Core Content (4)
| Field | Type | Description |
|-------|------|-------------|
| `statement` | string | WHAT: The decision (50-1500 chars) |
| `rationale` | string | WHY: The reasoning (100-4000 chars) |
| `constraints` | List[MCPConstraint] | MUST/SHOULD rules (max 30) |
| `invariants` | List[string] | Always-true assertions (max 20) |

### Context Matching (3)
| Field | Type | Description |
|-------|------|-------------|
| `applies_to` | List[string] | File patterns, keywords |
| `examples` | List[string] | Good/bad examples (max 10) |
| `tags` | List[string] | Searchable tags |

### Authorship (3)
| Field | Type | Description |
|-------|------|-------------|
| `authored_by` | string | Human author (REQUIRED per LAW §2.3) |
| `authored_at` | datetime | Approval timestamp |
| `content_by` | string? | Content generator (ai:claude-opus-4-5 or human) |

### Retrieval (2)
| Field | Type | Description |
|-------|------|-------------|
| `impact` | enum | CRITICAL (~500 tok), IMPORTANT (~1500), REFERENCE |
| `summary` | string | One-line summary (max 150 chars) |

### Relationships (3) - NEW
| Field | Type | Description |
|-------|------|-------------|
| `depends_on` | List[string] | Decision IDs this depends on |
| `supersedes` | string? | Decision ID this replaces |
| `priority_rank` | int | 1-100 for PRD ordering |

## Intent-Based Field Selection

| Intent | Fields Returned | ~Tokens |
|--------|-----------------|---------|
| LIST | code, summary, domain_id, impact | 30 |
| ENFORCE | code, statement, constraints | 150 |
| UNDERSTAND | code, statement, rationale, tags | 300 |
| REVIEW | code, constraints, invariants, examples | 250 |
| EXPLORE | code, statement, constraints, tags, applies_to | 200 |
| FULL | All 21 fields | 500 |

## Constraint Type Mapping

### DecisionV3 → MCP (RFC2119)
```
PROHIBITION → MUST_NOT
REQUIREMENT → MUST
LIMITATION  → MAY
PREFERENCE  → SHOULD
EXCEPTION   → MAY
```

### MCP (RFC2119) → DecisionV3
```
MUST     → REQUIREMENT
MUST_NOT → PROHIBITION
SHOULD   → PREFERENCE
MAY      → LIMITATION
```

## Key Design Decisions

### 1. `validity_state` is Computed, Not Stored
Per LAW §2.3 (immutability), decisions cannot have mutable status. Validity is derived from:
- `supersedes` chain (if superseded by another)
- `temporal_validity.sunset_date` (if expired)

### 2. `lifecycle_status` in Separate Table
To preserve decision immutability while tracking lifecycle:
```sql
CREATE TABLE lifecycle_events (
    event_id UUID PRIMARY KEY,
    decision_id UUID REFERENCES decisions(decision_id),
    status VARCHAR(20),  -- DRAFT, REVIEW, APPROVED, DEPRECATED
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL,
    reason TEXT
);
```

### 3. Dependency Graph Validation
- Circular dependencies: Detected and blocked
- Broken references: Flagged during validation
- Conflict detection: Based on overlapping `applies_to` + inverse constraint types

## Files Modified

- `core/domain/schema_mcp.py` - Updated to 21 fields
- `tests/stress_test_simulation.py` - Validation tests

## Next Steps

1. Implement LifecycleEvent table and API
2. Add real Gate 2 AI validation
3. Implement circular dependency prevention at write time
4. Add PRD_EXPORT mode to retrieval engine
