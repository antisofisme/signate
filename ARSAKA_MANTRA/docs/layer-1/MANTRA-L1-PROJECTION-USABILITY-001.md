# MANTRA-L1-PROJECTION-USABILITY-001: Projection Comprehension Analysis

**Document Type**: Usability Analysis (Non-Authoritative)
**Version**: 1.0.0
**Status**: DRAFT - FOR HUMAN REVIEW
**Generated**: 2025-01-24
**Authority**: NONE (AI-generated observation per MANTRA-LAW-001 §6)

---

## 0. Purpose

Evaluate each frozen projection (per MANTRA-L1-PROJECTION-FREEZE-001) for:
- Human comprehension risk
- AI comprehension risk
- Evidence of friction

This report does NOT propose solutions. Friction documentation only.

---

## 1. Matrix Overview Projection

**Per MANTRA-L1-PROJECTION-CATALOG-001 §1**

### 1.1 Human Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| Terminology | "Group" and "Feature" are abstract labels. No embedded meaning. |
| Navigation | User sees 16 cells. Must click to understand content. No preview. |
| Information Density | Count-only display. "5 decisions" provides no insight into WHAT decisions. |
| Mental Model | Requires prior knowledge of 4x4 structure to interpret. |

**Evidence**: DecisionMatrix.tsx shows only counts. Human must drill down for meaning.

### 1.2 AI Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| Semantic Extraction | Counts are numerically extractable but semantically empty. |
| Cross-Reference | Cannot determine decision relationships from matrix alone. |
| Pattern Detection | Can detect distribution anomalies (empty cells, clustering). |
| Context Loss | Grid structure provides no narrative context. |

**Evidence**: API `/api/v1/grouped` returns nested structure but AI cannot infer decision quality or relevance from counts.

### 1.3 Friction Summary

- Human: Must drill down for any meaningful information
- AI: Can count but cannot reason about decision content
- Neither: Cannot assess completeness or coverage from matrix alone

---

## 2. Decision List Projection

**Per MANTRA-L1-PROJECTION-CATALOG-001 §2**

### 2.1 Human Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| Statement Truncation | Long statements may be truncated in list view. |
| Version Ambiguity | Multiple versions appear as separate rows. No visual chain. |
| Supersedes Navigation | Supersedes field shows UUID. Not human-readable. |
| Sorting Absence | No defined sort order. Chronological? Alphabetical? |

**Evidence**: DecisionList.tsx shows decision_id (UUID), version, supersedes (UUID). Human sees opaque identifiers.

### 2.2 AI Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| UUID Correlation | AI can match UUIDs but no semantic meaning in identifiers. |
| Version Parsing | Semver format parseable but relationship not explicit. |
| Chain Reconstruction | Supersedes field allows chain building but requires traversal. |
| Temporal Order | created_at field allows ordering but not always present in projection. |

**Evidence**: API returns raw decision objects. AI must construct version chains programmatically.

### 2.3 Friction Summary

- Human: UUIDs are not readable. Must click through to understand relationships.
- AI: Can parse structure but must traverse supersedes to build history.
- Neither: No indication of "how many versions exist" without counting.

---

## 3. Decision Detail Projection

**Per MANTRA-L1-PROJECTION-CATALOG-001 §3**

### 3.1 Human Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| Constraint Complexity | Constraints array may have many items. No grouping. |
| Invariant Abstraction | Invariants are technical statements. May require domain knowledge. |
| Related Decisions | UUID array. Must click each to understand relationship. |
| Scope Meaning | "ORGANIZATION", "DOMAIN", "APPLICATION" labels without explanation. |

**Evidence**: DecisionDetail.tsx renders all fields but scope/blast_radius are enum values without definitions.

### 3.2 AI Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| Statement Analysis | Natural language statement is parseable but may be ambiguous. |
| Constraint Extraction | Constraint type (PROHIBITION/REQUIREMENT/LIMITATION) is classifiable. |
| Invariant Validation | Invariant strings are assertions but no formal specification. |
| Cross-Reference Resolution | related_decisions requires separate API calls. |

**Evidence**: Decision schema is well-defined but relationships require multi-step resolution.

### 3.3 Friction Summary

- Human: Technical language, abstract scopes, UUID references
- AI: Can parse all fields but must make multiple calls for full context
- Neither: No explanation of what scope/blast_radius levels MEAN

---

## 4. Evolution Timeline Projection

**Per MANTRA-L1-PROJECTION-CATALOG-001 §4**

### 4.1 Human Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| Chain Visualization | Linear chain not inherently visible. Must be constructed. |
| Rationale Diff | No diff view between versions. Must read full rationale each time. |
| Entry Point | Which version to start reading? Oldest? Newest? |
| Branch Handling | Supersedes is single UUID. What if multiple decisions supersede one? |

**Evidence**: No dedicated timeline component exists. Frontend shows supersedes field only.

### 4.2 AI Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| Chain Traversal | Must recursively follow supersedes until null. |
| Change Detection | No explicit "what changed" field between versions. |
| Branch Detection | Single supersedes means linear chain only. Branching requires reverse lookup. |
| Temporal Gaps | Time between versions not semantically meaningful without context. |

**Evidence**: Schema allows only single supersedes. AI cannot detect "superseded by" without full scan.

### 4.3 Friction Summary

- Human: No visual timeline exists in current implementation
- AI: Must traverse chain, cannot detect reverse relationships efficiently
- Neither: No diff or change summary between versions

---

## 5. Scope Projection

**Per MANTRA-L1-PROJECTION-CATALOG-001 §5**

### 5.1 Human Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| Scope Labels | ORGANIZATION/DOMAIN/APPLICATION have no embedded definitions. |
| Blast Radius Labels | LOW/MEDIUM/HIGH/CRITICAL are relative without baseline. |
| Cross-Group Display | No visualization of cross-group impact exists. |
| Impact Area | "FE/BE/Infra/CI-CD" mentioned in catalog but not in schema. |

**Evidence**: Schema has scope and blast_radius enums but no technical_area field.

### 5.2 AI Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| Enum Parsing | Scope and blast_radius are enumerable and classifiable. |
| Impact Calculation | No formula for determining scope or blast_radius. |
| Cross-Reference | Cannot determine impact area (FE/BE/Infra) from current schema. |
| Aggregation | Can count decisions per scope/blast_radius but meaning unclear. |

**Evidence**: Catalog mentions "FE/BE/Infra/CI-CD" display but schema does not include these fields.

### 5.3 Friction Summary

- Human: Abstract labels without definitions or examples
- AI: Can classify but cannot interpret meaning
- Both: Schema and catalog have terminology mismatch (technical_area missing)

---

## 6. Relationship / Impact Projection

**Per MANTRA-L1-PROJECTION-CATALOG-001 §6**

### 6.1 Human Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| UUID List | related_decisions is UUID array. No context. |
| Relationship Type | No indication WHY decisions are related. |
| Bidirectionality | A relates to B, but does B know about A? |
| Graph Complexity | Many relationships become unreadable quickly. |

**Evidence**: Schema has related_decisions array but no relationship_type field.

### 6.2 AI Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| Graph Construction | Can build adjacency graph from related_decisions. |
| Cycle Detection | Can detect circular relationships. |
| Cluster Analysis | Can identify decision clusters. |
| Semantic Relationship | Cannot determine relationship nature (dependency, conflict, complement). |

**Evidence**: related_decisions provides structure but no semantics.

### 6.3 Friction Summary

- Human: UUID lists with no explanation of relationship type
- AI: Can build graphs but cannot classify relationship nature
- Neither: No indication if relationships are mutual or directional

---

## 7. Change Summary Projection

**Per MANTRA-L1-PROJECTION-CATALOG-001 §7**

### 7.1 Human Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| Time Window | "Recent changes" undefined. Last day? Week? |
| Change Type | No explicit "new" vs "superseded" marking. |
| Impact Summary | Which features affected by changes? Not aggregated. |
| Notification Absence | How does human know changes occurred? |

**Evidence**: No change summary endpoint or component exists in current implementation.

### 7.2 AI Comprehension Risk

| Risk Factor | Observation |
|-------------|-------------|
| Temporal Query | Can filter by created_at but no "changes since" endpoint. |
| Delta Computation | Must compare snapshots to determine changes. |
| Supersedes Detection | New decision superseding old requires matching UUIDs. |
| Feature Impact | Must aggregate by feature_id to understand impact scope. |

**Evidence**: No dedicated change tracking. AI must compare temporal snapshots.

### 7.3 Friction Summary

- Human: No change summary implementation exists
- AI: Must compute changes manually from timestamps
- Neither: No notification or subscription mechanism

---

## 8. Cross-Projection Findings

### 8.1 Common Human Friction

| Friction Point | Affected Projections | Count |
|----------------|---------------------|-------|
| UUID opacity | 2, 3, 4, 6 | 4 |
| Abstract labels without definition | 1, 3, 5 | 3 |
| No visual chain/graph | 4, 6 | 2 |
| Missing implementation | 4, 7 | 2 |

### 8.2 Common AI Friction

| Friction Point | Affected Projections | Count |
|----------------|---------------------|-------|
| Multi-step resolution required | 3, 4, 6 | 3 |
| No semantic relationship data | 4, 6 | 2 |
| Schema/catalog terminology mismatch | 5 | 1 |
| No dedicated endpoints | 7 | 1 |

### 8.3 Implementation Gap Matrix

| Projection | Catalog Defined | Frontend Exists | API Exists |
|------------|-----------------|-----------------|------------|
| 1. Matrix Overview | Yes | Yes | Yes |
| 2. Decision List | Yes | Yes | Yes |
| 3. Decision Detail | Yes | Yes | Yes |
| 4. Evolution Timeline | Yes | Partial | No |
| 5. Scope Projection | Yes | Partial | No |
| 6. Relationship Projection | Yes | Partial | No |
| 7. Change Summary | Yes | No | No |

---

## 9. Evidence Summary

### 9.1 Frontend Files Reviewed

| File | Projection Coverage |
|------|---------------------|
| DecisionMatrix.tsx | #1 Matrix Overview |
| DecisionList.tsx | #2 Decision List |
| DecisionDetail.tsx | #3 Decision Detail (partial #4, #5, #6) |
| Dashboard.tsx | N/A (structural counts only) |

### 9.2 Schema Fields vs Projection Needs

| Projection Need | Schema Field | Status |
|-----------------|--------------|--------|
| Version chain | supersedes | Present |
| Relationship graph | related_decisions | Present |
| Technical area (FE/BE/Infra) | N/A | Missing |
| Relationship type | N/A | Missing |
| Change notification | N/A | Missing |

---

## 10. Conclusion

This analysis documents friction without proposing solutions.

**Recorded Friction**:
- 4 projections have implementation gaps
- UUID opacity affects 4 of 7 projections
- Schema/catalog terminology has 1 mismatch
- No dedicated timeline, scope, relationship, or change endpoints

**Human Action Required**:
- Review friction points
- Determine if friction is acceptable
- Record decisions about addressing or accepting friction

---

**END OF USABILITY ANALYSIS**

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2025-01-24 | Initial usability analysis |
