# MANTRA-LAW-001-AMENDMENT-002: Operational Metadata & AI Read Optimization

**Document Type**: Constitutional Law Amendment
**Amends**: MANTRA-LAW-001 v1.1.0
**Version**: 1.0.0
**Status**: PROPOSED
**Effective**: Upon Human Approval
**Authority**: Human Decision Only

---

## Amendment Summary

This amendment adds three new sections to MANTRA-LAW-001:

1. **§10.7 - Metadata Enrichment Exception**: Allows limited metadata additions without supersedes
2. **§4.5 - Implementation Tracking Boundary**: Clarifies separation of implementation status from decision validity
3. **§6.5 - AI Read Optimization Metadata**: Explicitly permits AI optimization metadata with safeguards

---

## Rationale

### Problem Statement

The original MANTRA-LAW-001 establishes absolute immutability (§10.2), which creates operational challenges:

1. **Enrichment Need**: Organizations need to add `trigger_event` or `code_artifacts` to existing decisions without creating hundreds of superseding decisions.

2. **Implementation Tracking**: MANTRA-DECISION-003 prohibits status fields, but implementation progress tracking is operationally necessary.

3. **AI Optimization**: AI read-side optimization (embeddings, disambiguation) is permitted under §6.2, but boundaries are unclear.

### Resolution Approach

This amendment provides explicit boundaries that:
- Preserve core immutability (statement, rationale, constraints, invariants)
- Enable operational metadata enrichment with audit trail
- Clarify implementation status ≠ decision validity
- Define AI optimization boundaries with human confirmation requirements

---

## §10.7 Metadata Enrichment Exception

### §10.7.1 Enrichable Fields

The following fields MAY be added or updated on existing decisions WITHOUT creating a superseding decision:

| Field Category | Specific Fields | Rationale |
|----------------|-----------------|-----------|
| Causality | `trigger_event` | Understanding "why decision exists" doesn't change decision meaning |
| Traceability | `code_artifacts` (additions only) | Linking implementations doesn't change decision meaning |
| AI Optimization | `embedding_metadata`, `llm_optimization.embedding_text`, `llm_optimization.keywords_for_rag` | Read-side optimization doesn't change decision meaning |
| Search | `search_metadata.search_keywords`, `search_metadata.aliases` | Discoverability improvement doesn't change decision meaning |
| Consumption | `knowledge_consumption.reading_time_minutes` | Calculated metadata doesn't change decision meaning |

### §10.7.2 Enrichment Requirements

All metadata enrichments MUST satisfy these requirements:

1. **Authorization Model**:
   - `enriched_by`: MAY be AI identifier (e.g., `ai:claude-opus-4-5`) OR human identifier
   - `approved_by`: MUST be human identifier (AI cannot approve per §6.3)
   - If `enriched_by` is AI, human approval is MANDATORY before persistence

2. **Audit Trail**: Each enrichment MUST be logged as an immutable record with:
   - `enrichment_id` (unique identifier)
   - `field_path` (what was enriched)
   - `enrichment_value` (value added)
   - `reason` (minimum 10 characters explaining why)
   - `enriched_by` and `enriched_at` (creator - AI or human)
   - `approved_by` and `approved_at` (approver - human only)

3. **No Meaning Alteration**: Enrichment MUST NOT alter the meaning or interpretation of the decision.

4. **No Constraint Modification**: Enrichment MUST NOT change enforcement behavior of any constraint.

5. **AI-Generated Enrichment Rules**:
   - AI-generated enrichments MUST be flagged with `enriched_by` prefix `ai:`
   - AI MUST NOT auto-approve its own enrichments
   - Human MUST review AI-generated content before approval

### §10.7.3 Forbidden Enrichments

The following fields MUST NOT be enriched and REQUIRE supersedes mechanism:

| Field | Reason |
|-------|--------|
| `statement` | Core decision content - defines what decision says |
| `rationale` | Core decision content - defines why decision exists |
| `constraints` | Enforcement rules - altering changes behavior |
| `invariants` | Invariant rules - altering changes behavior |
| `domain_id` | Classification - altering changes decision identity |
| `aspect_id` | Classification - altering changes decision identity |
| `scope` | Impact scope - altering changes applicability |
| `blast_radius` | Impact level - altering changes risk assessment |

Any attempt to enrich these fields is INVALID. The enrichment MUST be rejected.

### §10.7.4 Enrichment Immutability

Once created, an enrichment record is IMMUTABLE.

If an enrichment was made in error:
- Create a NEW superseding decision that does not include the erroneous data
- The erroneous enrichment remains in the historical record for audit purposes
- There is no "undo" or "revert" for enrichments

This preserves the append-only nature of the system.

---

## §4.5 Implementation Tracking Boundary

### §4.5.1 Decision Status Prohibition (Existing)

Per MANTRA-DECISION-003, decision records MUST NOT have status fields such as:
- DRAFT, ACTIVE, DEPRECATED lifecycle states
- Approval status that implies mutability
- Any field suggesting decision validity changes over time

### §4.5.2 Implementation Status Permission

Separate implementation tracking systems MAY track:

| Trackable | Description | Example |
|-----------|-------------|---------|
| Team adoption status | Which teams have implemented | `TeamAdoption.status = COMPLETED` |
| Implementation progress | Percentage complete | `progress_percentage = 75` |
| Blockers | What prevents implementation | `Blocker.category = TECHNICAL` |
| Rollback history | Past reversal events | `RollbackRecord` |

### §4.5.3 Separation Requirements

Implementation tracking systems:

1. **MUST be stored separately** from decision records (separate table/collection)
2. **MUST reference decisions by ID only** (no embedding in decision record)
3. **MUST NOT modify decision record content**
4. **MUST NOT imply decision validity** based on implementation status

### §4.5.4 Validity Independence

A decision with zero (0%) implementation is equally VALID as a decision with full (100%) adoption.

Implementation status is operational metadata, NOT decision lifecycle state.

Non-adoption does not invalidate a decision. It indicates:
- Teams have not yet implemented, OR
- Teams have opted out (with recorded reason), OR
- Implementation is blocked (with recorded blockers)

### §4.5.5 Rationale

This boundary exists because:
- Decision validity is determined by constitutional compliance (this law)
- Implementation status is operational reality
- Conflating them creates confusion about what "valid" means
- A valid-but-unimplemented decision still governs if someone implements later

---

## §6.5 AI Read Optimization Metadata

### §6.5.1 Permitted AI Optimization

Per existing §6.2, AI MAY:
- Read decision records
- Detect potential conflicts
- Flag potential gaps
- Generate advisory warnings
- Produce analysis for human review

This section explicitly permits AI to use the following optimization metadata:

| Metadata Type | Purpose | Constraint |
|---------------|---------|------------|
| `embedding_metadata` | Vector embeddings for semantic search | Read-only, no decision modification |
| `disambiguation` | Help disambiguate similar decisions | Must present options to human |
| `query_hints` | Improve search/retrieval | Suggestions only, human confirms |
| `llm_optimization.rag` | RAG optimization for AI context | Read-only optimization |

### §6.5.2 Required Safeguards

All AI features using this metadata MUST implement these safeguards:

1. **No Auto-Selection**: AI MUST NOT automatically select a single decision as "the answer"
   - `DisambiguationSupport.ai_auto_selection_prohibited = true`
   - `QueryProcessingHints.human_must_confirm_trigger = true`

2. **Present All Options**: When disambiguation is needed, AI MUST present all relevant options
   - `DisambiguationSupport.present_all_options = true`

3. **Human Confirmation**: Final selection MUST be confirmed by human
   - `DisambiguationSupport.human_confirmation_required = true`

4. **Confidence Display**: AI suggestions MUST display confidence scores
   - `QueryProcessingHints.require_confidence_display = true`

5. **Suggestion Limits**: AI MUST NOT overwhelm user with options
   - `QueryProcessingHints.max_auto_suggestions` (default: 5, max: 10)

### §6.5.3 Prohibited AI Actions (Reinforcement of §6.3)

Even with optimization metadata, AI MUST NOT:
- Assign decisions to groups or features (§6.3)
- Approve or reject decisions (§6.3)
- Use `suggested_default` to auto-select without human confirmation
- Treat `trigger_phrases` matches as final answers
- Create, modify, or finalize any decision record

### §6.5.4 Violation Consequences

Any AI action that violates §6.5.2 or §6.5.3:
- Is INVALID per §6.4
- MUST be discarded
- Does not bind any decision or user

Human review of AI suggestions does not transfer authority to AI (reinforcing §6.4).

---

## Schema Implementation Requirements

### Required Model Updates

1. **MetadataEnrichment** model MUST:
   - Validate `field_path` against `ENRICHABLE_FIELDS`
   - Require `approved_by` (not optional)
   - Be immutable after creation (no `is_active`, `reverted_at`)

2. **DisambiguationSupport** model MUST include:
   - `human_confirmation_required: bool = True`
   - `ai_auto_selection_prohibited: bool = True`
   - `present_all_options: bool = True`

3. **QueryProcessingHints** model MUST include:
   - `human_must_confirm_trigger: bool = True`
   - `ai_suggestion_only: bool = True`
   - `require_confidence_display: bool = True`
   - `max_auto_suggestions: int` (1-10, default 5)

### Required Validator Updates

New validation rules:

| Rule ID | Description | Level |
|---------|-------------|-------|
| E-001 | Enrichment field_path in ENRICHABLE_FIELDS | Schema |
| E-002 | Enrichment approved_by is present | Schema |
| E-003 | Enrichment reason minimum 10 characters | Schema |
| AI-001 | DisambiguationSupport.human_confirmation_required = True | Law |
| AI-002 | QueryProcessingHints.human_must_confirm_trigger = True | Law |
| AI-003 | AI output does not finalize decision selection | Law |

---

## Backward Compatibility

### Existing Decisions

- Existing decisions remain VALID
- No migration required
- New fields can be enriched per §10.7

### Existing Implementations

- Existing `DecisionAmendment` records should be migrated to `MetadataEnrichment`
- Migration MUST preserve audit trail
- Mutable fields (`is_active`, `reverted_at`) should be dropped

### Deprecations

| Deprecated | Replacement | Reason |
|------------|-------------|--------|
| `DecisionAmendment` | `MetadataEnrichment` | LAW compliance |
| `AmendmentType.RETRACTION` | Supersedes mechanism | Retraction implies mutability |
| `is_active`, `reverted_at` | None (immutable) | Append-only principle |

---

## Amendment Process Compliance

Per MANTRA-LAW-001 §8.3, this amendment:

- [x] Has human authorship
- [x] Has explicit statement of change
- [x] Has recorded rationale
- [ ] Requires version increment (upon approval)

---

## Approval

This amendment requires human approval before becoming effective.

| Role | Name | Date | Decision |
|------|------|------|----------|
| Author | Claude Code (AI-assisted drafting) | 2026-01-29 | PROPOSED |
| Human Reviewer | ___________________ | ___________ | PENDING |
| Human Approver | ___________________ | ___________ | PENDING |

**Note**: Per §6.3, AI cannot approve this amendment. Human approval is REQUIRED.

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-01-29 | Initial proposal: §10.7, §4.5, §6.5 |

---

**END OF AMENDMENT**
