# MANTRA-LAW-001-AMENDMENT-003: Authorship Clarification

**Document Type**: Constitutional Law Amendment
**Amends**: MANTRA-LAW-001 v1.1.0 §2.3
**Version**: 1.0.0
**Status**: PROPOSED
**Effective**: Upon Human Approval
**Authority**: Human Decision Only

---

## Amendment Summary

This amendment adds §2.3.1 to clarify the meaning of "human-authored" in the context of AI-assisted workflows, while preserving the absolute prohibition on AI decision authority.

---

## Rationale

### Problem Statement

MANTRA-LAW-001 §2.3 states decisions are INVALID if they lack "human-authored statement" or "human-authored rationale." This creates ambiguity in AI-assisted workflows where:

1. AI generates draft content (statement, rationale, constraints)
2. Human reviews, modifies, and approves the content
3. Human submits the decision under their identity

The question: Is AI-generated-human-approved content "human-authored"?

### Current Legal Gap

§2.3 says "human-authored" but does not define:
- Whether "authored" means "originally written" or "submitted under authority"
- Whether AI-assisted drafting invalidates human authorship
- How to track content provenance while maintaining validity

### Resolution

This amendment clarifies that **authorship = submission with identity**, meaning:
- The human who submits content is the author (legally responsible)
- AI may assist in content generation (as a tool)
- Content provenance SHOULD be tracked but does not affect validity
- Human approval of AI-generated content transfers authorship to the human

This mirrors legal precedent where humans using tools (spell-checkers, templates, co-authors) retain authorship through submission.

---

## §2.3.1 Authorship Definition

### §2.3.1.1 Authorship Determination

**Authorship** is determined by **submission with identity**, not by original creation.

A decision is **human-authored** if:
1. A human submits the decision content, AND
2. The human's identity is recorded as the author (`authored_by` field), AND
3. The human accepts responsibility for the content's accuracy and applicability

### §2.3.1.2 AI-Assisted Content

AI MAY assist in generating decision content (statement, rationale, constraints, invariants) under these conditions:

| Condition | Requirement |
|-----------|-------------|
| Draft Generation | AI MAY generate draft content for human review |
| Human Review | Human MUST review AI-generated content before submission |
| Human Modification | Human MAY modify, accept, or reject AI-generated content |
| Submission Authority | Only human MAY submit content as a decision |
| Authorship Transfer | Upon human submission, authorship transfers to the submitting human |
| Provenance Tracking | Content generator SHOULD be recorded in `content_by` field |

### §2.3.1.3 Content Provenance

Systems MAY track content provenance using:

| Field | Description | Required |
|-------|-------------|----------|
| `authored_by` | Human who submitted/approved content | REQUIRED |
| `authored_at` | When human submitted/approved | REQUIRED |
| `content_by` | Content generator (e.g., `ai:claude-opus-4-5`) | OPTIONAL |
| `content_at` | When content was generated | OPTIONAL |

**Note**: `content_by` is informational. It does not affect decision validity.

### §2.3.1.4 Validity Rules

A decision remains VALID if:
- `authored_by` is a human identifier (not `ai:*`)
- `authored_at` is recorded
- Content meets all other validity requirements in §2.3

A decision is INVALID if:
- `authored_by` is an AI identifier (`ai:*`)
- `authored_by` is missing or empty
- No human reviewed AI-generated content before submission

### §2.3.1.5 Examples

**VALID**:
```
authored_by: john.doe@company.com  (human)
content_by: ai:claude-opus-4-5     (AI generated draft)
```
Explanation: Human (john.doe) reviewed and submitted AI-generated content. John is the author.

**VALID**:
```
authored_by: jane.smith@company.com  (human)
content_by: jane.smith@company.com   (human wrote directly)
```
Explanation: Human wrote and submitted. Jane is the author.

**INVALID**:
```
authored_by: ai:claude-opus-4-5  (AI!)
content_by: ai:claude-opus-4-5
```
Explanation: AI cannot be author. Violates §2.3 and §6.

---

## Relationship to Other Sections

### §6 AI Authority (Unchanged)

This amendment does NOT change §6. AI authority remains ZERO.

- §6.2: AI MAY read, detect, flag, generate advisory, produce analysis
- §6.3: AI MUST NOT create identifiers, assign to groups, change status, approve, finalize

**Clarification**: AI generating draft content falls under §6.2 "produce analysis for human review."

### §10.7 Metadata Enrichment (Compatible)

Per AMENDMENT-002 §10.7.2:
- `enriched_by` MAY be AI identifier
- `approved_by` MUST be human identifier

This is consistent with §2.3.1:
- Content generation (enriched_by/content_by) = tool activity
- Authorship/approval (authored_by/approved_by) = human authority

---

## Schema Implementation Requirements

### Required Field Updates

1. **Add `content_by` field** (Optional):
   ```python
   content_by: Optional[str] = Field(
       default=None,
       description="Content generator: 'ai:claude-opus-4-5' or human ID"
   )
   ```

2. **Validate `authored_by`** (Required):
   ```python
   @field_validator("authored_by")
   @classmethod
   def validate_human_author(cls, v):
       if v.startswith("ai:"):
           raise ValueError(
               f"authored_by must be human, got '{v}'. "
               f"Per LAW §2.3.1, authorship requires human submission."
           )
       return v
   ```

### MCP Schema Compliance

The MCP-optimized schema (`schema_mcp.py`) implements:
- `authored_by`: REQUIRED, human only
- `authored_at`: REQUIRED
- `content_by`: OPTIONAL, informational

---

## Backward Compatibility

### Existing Decisions

- Decisions without `content_by` remain VALID (field is optional)
- Existing `authored_by` (previously `created_by` or `approved_by`) remains valid
- No migration required for existing decisions

### New Decisions

- New decisions SHOULD include `content_by` for provenance tracking
- Systems MAY auto-populate `content_by` when AI assists

---

## Amendment Process Compliance

Per MANTRA-LAW-001 §8.3, this amendment:

- [x] Has human authorship (proposed for human approval)
- [x] Has explicit statement of change (§2.3.1 addition)
- [x] Has recorded rationale (authorship clarification)
- [ ] Requires version increment (upon approval → v1.2.0)

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
| 1.0.0 | 2026-01-29 | Initial proposal: §2.3.1 authorship clarification |

---

**END OF AMENDMENT**
