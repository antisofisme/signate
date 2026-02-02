# MANTRA Implementation Checklist

## Status Legend
- [x] Complete
- [ ] Pending
- [~] In Progress

---

## Phase 0: Schema Design (COMPLETE)

### Validated
- [x] 21-field MCPDecision schema
- [x] Intent-based field selection (6 intents: LIST, ENFORCE, UNDERSTAND, REVIEW, EXPLORE, FULL)
- [x] Stress test passing 100% (18/18 tests)
- [x] Relationship fields: depends_on, supersedes, priority_rank
- [x] Constraint type mapping (DecisionV3 ↔ RFC2119)
- [x] ValidityState as computed field (not stored)

### Documentation
- [x] SCHEMA_VALIDATED.md - Design documentation
- [x] stress_test_simulation.py - Validation tests

---

## Phase 1: Core Implementation (COMPLETE)

### 1. LifecycleEvent Table ✅
**Purpose**: Track decision lifecycle without violating immutability

- [x] Create `lifecycle.py` model with LifecycleEvent, LifecycleStatus
- [x] Create SQL migration `033_lifecycle_events.sql`
- [x] Add validation: only valid transitions allowed (via DB trigger)
- [x] Add audit trail integration (LifecycleManager)
- [ ] Create `lifecycle_repository.py` for data access (optional)
- [ ] Create API endpoints: GET /decisions/{id}/lifecycle, POST /decisions/{id}/lifecycle (optional)

**Schema**:
```sql
CREATE TABLE lifecycle_events (
    event_id UUID PRIMARY KEY,
    decision_id UUID NOT NULL,
    status VARCHAR(20) NOT NULL,  -- DRAFT, REVIEW, APPROVED, DEPRECATED
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL,
    reason TEXT,
    previous_status VARCHAR(20),
    CONSTRAINT fk_decision FOREIGN KEY (decision_id) REFERENCES decisions(decision_id)
);
```

### 2. Gate 2 AI Validation ✅
**Purpose**: Real AI-powered validation replacing placeholder

- [x] Create `gate2_ai_validator.py` with Gate2AIValidator class
- [x] Implement semantic consistency check
- [x] Implement conflict detection with existing decisions
- [x] Implement quality scoring (completeness, clarity, specificity, consistency, actionability)
- [x] Create fallback for when AI unavailable (rule-based heuristics)
- [ ] Add configurable LLM backend (Claude API) - future enhancement
- [ ] Add caching for repeated validations - future enhancement

**Validation Checks** (implemented):
1. Statement-Rationale alignment (keyword overlap)
2. Constraint feasibility (enforceability check)
3. Conflict with existing decisions (MUST vs MUST_NOT detection)
4. Quality score calculation (5 dimensions)

### 3. Circular Dependency Prevention ✅
**Purpose**: Prevent invalid dependency graphs at write time

- [x] Create `dependency_validator.py`
- [x] Implement cycle detection algorithm (DFS-based)
- [x] Return clear error messages with cycle path
- [x] Add max depth limit (configurable, default 10)
- [x] Implement self-reference detection
- [x] Implement missing reference detection
- [x] Create convenience function `validate_dependencies()`
- [ ] Add validation hook to decision creation/update API (integration)

**Features**:
- `CyclicDependencyError` with full cycle path
- `SelfReferenceError` detection
- `MissingReferenceError` detection
- `ExcessiveDepthError` warning
- Graph statistics (nodes, edges, depth)

### 4. PRD_EXPORT Mode ✅
**Purpose**: Export decisions as PRD documentation

- [x] Add PRD_EXPORT to QueryIntent enum
- [x] Create PRD field selection (all content + relationships)
- [x] Implement markdown generator with hierarchy
- [x] Support 3 section styles: HIERARCHICAL, PRIORITY, FLAT
- [x] Support filtering by domain/aspect/tags
- [x] Add table of contents generation
- [x] Support multiple formats: Markdown, JSON, HTML
- [x] Add dependency annotations
- [x] Add supersedes annotations

**Output Formats**:
- Markdown (default) - `.to_markdown()`
- JSON (structured) - `.to_json()`
- HTML (styled) - `.to_html()`

---

## Phase 2: Field-Level Relationships (COMPLETE)

### FieldRelation Model ✅
- [x] Create `field_relation.py` model
- [x] Create SQL migration `034_field_relations.sql`
- [x] Implement field path addressing (e.g., "constraints[0].rule")
- [x] Add validation for field path existence
- [x] RelationGraph for managing relations

### Relation Types ✅
- [x] CONFLICTS_WITH - Contradicting rules
- [x] STRENGTHENS - Makes stricter
- [x] WEAKENS - Makes looser
- [x] IMPLEMENTS - Specific implementation of abstract
- [x] ENFORCES - Invariant guarantees constraint
- [x] REFERENCES - Non-dependency reference

### Detection & Analysis ✅
- [x] Automated conflict detection (rule-based heuristics)
- [x] Impact analysis when field changes
- [x] Impact analysis for decision deprecation
- [x] Transitive impact chains (follows IMPLEMENTS/ENFORCES)
- [ ] AI-powered semantic similarity (future enhancement)
- [ ] Visualization of field relationship graph (UI feature)

---

## Phase 3: Integration (FUTURE)

### PUGUH Platform Integration
- [ ] Add tenant_id to all models
- [ ] Integrate with PUGUH auth system
- [ ] Integrate with PUGUH billing
- [ ] Add API key support

### MCP Server
- [ ] Implement MCP Resources for decisions
- [ ] Implement MCP Tools for CRUD
- [ ] Implement MCP Prompts for common queries
- [ ] Add streaming support for large result sets

---

## Testing Requirements

### Unit Tests
- [ ] LifecycleEvent model tests
- [ ] Gate 2 validation tests
- [ ] Circular dependency detection tests
- [ ] PRD export tests

### Integration Tests
- [ ] Full decision lifecycle flow
- [ ] Validation pipeline (Gate 1 → Gate 2 → Gate 3)
- [ ] Dependency graph operations
- [ ] PRD generation with real data

### Stress Tests
- [x] Token budget tests (4 modes)
- [x] Relevance precision tests
- [x] Dependency resolution tests
- [x] Circular dependency detection
- [x] Conflict detection
- [x] Supersedes chain validation

---

## Files to Create/Modify

### New Files
```
core/domain/lifecycle.py          # LifecycleEvent model
core/validation/gate2_validator.py # AI validation
core/validation/dependency_validator.py # Cycle detection
core/retrieval/prd_export.py      # PRD generation
migrations/030_lifecycle_events.sql
```

### Modify
```
core/domain/schema_mcp.py         # Add lifecycle_status helper
core/retrieval/intent.py          # Add PRD_EXPORT intent
core/retrieval/engine.py          # Integrate PRD export
core/api/decisions.py             # Add lifecycle endpoints
```

---

## Progress Tracking

| Task | Status | Started | Completed |
|------|--------|---------|-----------|
| Schema Design | ✅ Complete | 2024-01-29 | 2024-01-30 |
| LifecycleEvent | ✅ Complete | 2024-01-30 | 2024-01-30 |
| Gate 2 AI | ✅ Complete | 2024-01-30 | 2024-01-30 |
| Circular Dep | ✅ Complete | 2024-01-30 | 2024-01-30 |
| PRD Export | ✅ Complete | 2024-01-30 | 2024-01-30 |
| FieldRelation Model | ✅ Complete | 2024-01-30 | 2024-01-30 |
| Conflict Detection | ✅ Complete | 2024-01-30 | 2024-01-30 |
| Impact Analysis | ✅ Complete | 2024-01-30 | 2024-01-30 |

## Files Created

### Phase 1
```
core/domain/lifecycle.py              # LifecycleEvent, LifecycleManager
core/validation/__init__.py           # Validation module exports
core/validation/gate2_ai_validator.py # AI-powered Gate 2
core/validation/dependency_validator.py # Circular dep prevention
core/retrieval/prd_export.py          # PRD document generation
migrations/033_lifecycle_events.sql   # Lifecycle DB schema
```

### Phase 2
```
core/domain/field_relation.py         # FieldRelation, RelationGraph
core/analysis/__init__.py             # Analysis module exports
core/analysis/conflict_detector.py    # Field-level conflict detection
core/analysis/impact_analyzer.py      # Impact analysis for changes
migrations/034_field_relations.sql    # Field relations DB schema
```

## Files Modified

```
core/domain/schema_mcp.py            # 21-field schema with relationships
core/retrieval/__init__.py           # Added PRD export
core/retrieval/intent.py             # Added PRD_EXPORT intent
```
