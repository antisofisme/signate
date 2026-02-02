# MANTRA-L1-AI-WORKFLOW-SPECIFICATION-001

## AI Workflow Specification for ARSAKA_MANTRA

**Document ID**: MANTRA-L1-AI-WORKFLOW-SPECIFICATION-001
**Version**: 1.0.0
**Status**: ACTIVE
**Parent Document**: MANTRA-L1-AI-OPERATIONAL-GUIDELINES-001

---

## 1. Overview

This document provides detailed workflow specifications for AI assistants collaborating with humans in ARSAKA_MANTRA decision management. It defines the step-by-step process from receiving human input to producing actionable suggestions.

---

## 2. Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AI ASSISTANCE WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────┐                                                           │
│  │ HUMAN INPUT   │ "Kita mau fokus ke pasar enterprise"                     │
│  └───────┬───────┘                                                           │
│          │                                                                   │
│          ▼                                                                   │
│  ┌─────────────────────────────────────────┐                                │
│  │ STEP 1: INPUT CLASSIFICATION            │                                │
│  │                                         │                                │
│  │ Question Type Analysis:                 │                                │
│  │ • WHY/WHAT? → GROUP-1 (Intent)         │                                │
│  │ • HOW/WHERE? → GROUP-2 (Architecture)  │                                │
│  │ • CAN/MUST NOT? → GROUP-3 (Control)    │                                │
│  │ • CHANGE? → GROUP-4 (Evolution)        │                                │
│  │                                         │                                │
│  │ Result: GROUP-1 / F-01 (Vision)        │                                │
│  └───────────────┬─────────────────────────┘                                │
│                  │                                                           │
│                  ▼                                                           │
│  ┌─────────────────────────────────────────┐                                │
│  │ STEP 2: EVALUATION                      │                                │
│  │                                         │                                │
│  │ GROUP-1 Criteria:                       │                                │
│  │ ☐ Is vision clear and measurable?      │                                │
│  │ ☐ Does it align with existing?         │                                │
│  │ ☐ Are success criteria defined?        │                                │
│  │                                         │                                │
│  │ Findings: Missing success criteria     │                                │
│  └───────────────┬─────────────────────────┘                                │
│                  │                                                           │
│                  ▼                                                           │
│  ┌─────────────────────────────────────────┐                                │
│  │ STEP 3: COMPARISON                      │                                │
│  │                                         │                                │
│  │ Query: GET /decisions?group_id=GROUP-1  │                                │
│  │                                         │                                │
│  │ Found related:                          │                                │
│  │ • DECISION-001: "Focus on SMB market"  │                                │
│  │   → POTENTIAL CONFLICT                  │                                │
│  │                                         │                                │
│  │ Analysis:                               │                                │
│  │ • Same feature (F-01)                   │                                │
│  │ • Opposite target market                │                                │
│  │ • Recommend: supersedes chain           │                                │
│  └───────────────┬─────────────────────────┘                                │
│                  │                                                           │
│                  ▼                                                           │
│  ┌─────────────────────────────────────────┐                                │
│  │ STEP 4: SUGGESTION GENERATION           │                                │
│  │                                         │                                │
│  │ AI SUGGESTIONS:                         │                                │
│  │                                         │                                │
│  │ 1. Add measurable success criteria     │                                │
│  │    "Because F-01 decisions need..."    │                                │
│  │                                         │                                │
│  │ 2. Create supersedes chain to          │                                │
│  │    DECISION-001 (market strategy       │                                │
│  │    change requires evolution)          │                                │
│  │                                         │                                │
│  │ 3. Consider blast_radius: HIGH         │                                │
│  │    (affects entire sales strategy)     │                                │
│  └───────────────┬─────────────────────────┘                                │
│                  │                                                           │
│                  ▼                                                           │
│  ┌─────────────────────────────────────────┐                                │
│  │ STEP 5: OUTPUT                          │                                │
│  │                                         │                                │
│  │ ## Classification                       │                                │
│  │ GROUP-1 / F-01: Vision & Outcome       │                                │
│  │                                         │                                │
│  │ ## Analysis                             │                                │
│  │ [Evaluation findings]                   │                                │
│  │                                         │                                │
│  │ ## Comparison                           │                                │
│  │ [Conflict with DECISION-001]           │                                │
│  │                                         │                                │
│  │ ## AI SUGGESTIONS                       │                                │
│  │ [Labeled suggestions with reasoning]   │                                │
│  │                                         │                                │
│  │ ## Draft (FOR HUMAN REVIEW)            │                                │
│  │ { ... prepared decision JSON ... }     │                                │
│  │                                         │                                │
│  │ ⚠️ Human review required               │                                │
│  └───────────────┬─────────────────────────┘                                │
│                  │                                                           │
│                  ▼                                                           │
│  ┌───────────────┐                                                           │
│  │ HUMAN REVIEW  │ → APPROVE / MODIFY / REJECT                              │
│  └───────────────┘                                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Step 1: Input Classification (Detailed)

### 3.1 Classification Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    INPUT CLASSIFICATION FLOW                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Human Input: "Kami mau fokus ke pasar SMB"                     │
│        │                                                         │
│        ▼                                                         │
│  ┌──────────────────────────────────────────────┐               │
│  │ STEP 1: Identify Question Being Answered     │               │
│  │                                              │               │
│  │ WHY/WHAT? → GROUP-1 (Intent)                │               │
│  │ HOW/WHERE? → GROUP-2 (Architecture)         │               │
│  │ CAN/MUST NOT? → GROUP-3 (Control)           │               │
│  │ CHANGE? → GROUP-4 (Evolution)               │               │
│  └──────────────────────────────────────────────┘               │
│        │                                                         │
│        ▼ Answer: "WHAT are we focusing on?" = GROUP-1            │
│                                                                  │
│  ┌──────────────────────────────────────────────┐               │
│  │ STEP 2: Identify Specific Feature           │               │
│  │                                              │               │
│  │ GROUP-1 Features:                           │               │
│  │ F-01: Vision & Outcome (long-term goals)    │ ← MATCH       │
│  │ F-02: Problem Statement (what problem?)     │               │
│  │ F-03: Scope & Non-Goals (in/out scope)      │               │
│  │ F-04: Principles & Values (trade-offs)      │               │
│  └──────────────────────────────────────────────┘               │
│        │                                                         │
│        ▼ Classification: GROUP-1 / F-01 (Vision & Outcome)       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Classification Matrix

| Group | Question Pattern | Features |
|-------|-----------------|----------|
| **GROUP-1 (Intent)** | "What are we trying to achieve?" | F-01: Vision, F-02: Problem, F-03: Scope, F-04: Principles |
| **GROUP-2 (Architecture)** | "How do we structure it?" | F-05: Domain, F-06: Service, F-07: Data, F-08: Integration |
| **GROUP-3 (Control)** | "What rules apply?" | F-09: Policy, F-10: Authority, F-11: Security, F-12: Risk |
| **GROUP-4 (Evolution)** | "How does it change?" | F-13: Lifecycle, F-14: Rollback, F-15: Promotion, F-16: Consistency |

### 3.3 Feature Keywords

| Feature | Common Keywords |
|---------|----------------|
| F-01 | goal, vision, outcome, target, aim, objective, achieve |
| F-02 | problem, issue, challenge, pain point, need, solve |
| F-03 | scope, include, exclude, boundary, in-scope, out-of-scope |
| F-04 | principle, value, trade-off, priority, guideline |
| F-05 | domain, bounded context, aggregate, entity, concept |
| F-06 | service, module, component, microservice, boundary |
| F-07 | data, ownership, schema, database, storage |
| F-08 | API, integration, contract, interface, protocol |
| F-09 | rule, policy, must, should, allowed, forbidden |
| F-10 | approval, authority, permission, role, who can |
| F-11 | security, encryption, authentication, compliance, GDPR |
| F-12 | risk, failure, fallback, resilience, disaster |
| F-13 | lifecycle, evolve, version, change, supersede |
| F-14 | rollback, revert, undo, exit, migration |
| F-15 | promotion, staging, production, environment, gate |
| F-16 | consistency, drift, alignment, synchronize |

---

## 4. Step 2: Evaluation (Detailed)

### 4.1 Evaluation Matrix by Group

```
┌─────────────────────────────────────────────────────────────────┐
│               GROUP-SPECIFIC EVALUATION CRITERIA                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ GROUP-1 (Intent): Evaluate CLARITY & ALIGNMENT                   │
│ ├── Is the vision clear and measurable?                         │
│ ├── Does it align with existing vision statements?              │
│ ├── Are success criteria defined?                               │
│ └── Compare against: Other GROUP-1 decisions in same scope      │
│                                                                  │
│ GROUP-2 (Architecture): Evaluate CONSISTENCY & BOUNDARIES        │
│ ├── Are boundaries clearly defined?                             │
│ ├── Does it conflict with existing architecture decisions?      │
│ ├── Are integration contracts specified?                        │
│ └── Compare against: Other GROUP-2 decisions for overlap        │
│                                                                  │
│ GROUP-3 (Control): Evaluate ENFORCEABILITY & COMPLETENESS        │
│ ├── Can the policy be enforced?                                 │
│ ├── Are exceptions documented?                                  │
│ ├── Is authority chain clear?                                   │
│ └── Compare against: Other GROUP-3 for conflicts/redundancy     │
│                                                                  │
│ GROUP-4 (Evolution): Evaluate SAFETY & REVERSIBILITY             │
│ ├── Is the change strategy safe?                                │
│ ├── Is there rollback plan?                                     │
│ ├── Are promotion rules clear?                                  │
│ └── Compare against: Other GROUP-4 for consistency              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Evaluation Checklist Templates

#### GROUP-1 (Intent) Checklist

```markdown
## GROUP-1 Evaluation: Intent & Purpose

### Clarity Check
☐ Statement is declarative and unambiguous
☐ Terms are defined (no jargon without explanation)
☐ Scope is explicit (organization/domain/application)

### Measurability Check
☐ Success criteria are quantifiable
☐ Timeline or milestone is specified
☐ Progress can be tracked

### Alignment Check
☐ No contradiction with existing GROUP-1 decisions
☐ Supports organizational mission
☐ Stakeholders are identified

### Findings
- [List issues found]
- [List suggestions]
```

#### GROUP-2 (Architecture) Checklist

```markdown
## GROUP-2 Evaluation: Architecture & Structure

### Boundary Check
☐ Domain/service boundaries are explicit
☐ Ownership is clear (who is responsible)
☐ Interface contracts are defined

### Consistency Check
☐ No overlap with existing boundaries
☐ Integration points are documented
☐ Data flow is traceable

### Completeness Check
☐ Dependencies are listed
☐ Constraints are documented
☐ Migration path is considered

### Findings
- [List issues found]
- [List suggestions]
```

#### GROUP-3 (Control) Checklist

```markdown
## GROUP-3 Evaluation: Control & Governance

### Enforceability Check
☐ Rule can be technically enforced
☐ Violations can be detected
☐ Consequences are defined

### Completeness Check
☐ Edge cases are covered
☐ Exceptions are documented
☐ Authority chain is clear

### Consistency Check
☐ No conflict with existing policies
☐ Hierarchy is respected
☐ Scope is appropriate

### Findings
- [List issues found]
- [List suggestions]
```

#### GROUP-4 (Evolution) Checklist

```markdown
## GROUP-4 Evaluation: Evolution & Change

### Safety Check
☐ Rollback plan exists
☐ Risk assessment is complete
☐ Impact analysis is documented

### Reversibility Check
☐ Changes can be undone
☐ Data migration is reversible
☐ Downtime is acceptable

### Consistency Check
☐ Aligns with existing evolution patterns
☐ Promotion gates are defined
☐ Version strategy is clear

### Findings
- [List issues found]
- [List suggestions]
```

---

## 5. Step 3: Comparison (Detailed)

### 5.1 Comparison Algorithm

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPARISON ALGORITHM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INPUT: Draft decision D                                        │
│                                                                  │
│  Step 1: Find Related Decisions                                  │
│  ─────────────────────────────                                   │
│  Query: GET /decisions?group_id={D.group_id}                    │
│  Filter: Same scope or broader scope                            │
│                                                                  │
│  Step 2: Check for Conflicts                                     │
│  ───────────────────────────                                     │
│  For each existing decision E:                                   │
│  │                                                               │
│  ├─ Same feature_id?                                            │
│  │  └─ YES → Check statement similarity                         │
│  │     ├─ Similar: POTENTIAL REDUNDANCY                         │
│  │     └─ Opposite: CONTRADICTION                               │
│  │                                                               │
│  ├─ Different feature_id but same group?                        │
│  │  └─ Check for logical conflicts                              │
│  │                                                               │
│  ├─ In supersedes chain?                                        │
│  │  └─ YES → EVOLUTION (acceptable)                             │
│  │                                                               │
│  └─ Overlapping scope?                                          │
│     └─ YES → Check if constraints conflict                      │
│                                                                  │
│  Step 3: Generate Report                                         │
│  ──────────────────────                                          │
│  {                                                               │
│    "conflicts": [                                                │
│      {                                                           │
│        "existing_decision_id": "...",                           │
│        "conflict_type": "CONTRADICTION | REDUNDANCY | OVERLAP", │
│        "explanation": "New statement contradicts existing...",  │
│        "severity": "HIGH | MEDIUM | LOW",                       │
│        "suggestion": "Consider supersedes chain or modify..."   │
│      }                                                           │
│    ],                                                            │
│    "related_decisions": ["...", "..."],                         │
│    "recommendation": "PROCEED | REVIEW | REVISE"                │
│  }                                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Conflict Types

| Type | Description | Resolution |
|------|-------------|------------|
| **CONTRADICTION** | Statements are mutually exclusive | Supersedes chain or scope narrowing |
| **REDUNDANCY** | Statements are essentially identical | Merge or reference existing |
| **OVERLAP** | Scopes intersect with different rules | Clarify boundaries |
| **EVOLUTION** | Natural version progression | Use supersedes pointer |

### 5.3 Comparison Output Template

```markdown
## Comparison with Existing Decisions

### Related Decisions Found: 3

| Decision ID | Feature | Statement Summary | Relation |
|-------------|---------|-------------------|----------|
| DECISION-001 | F-01 | "Focus on SMB" | CONTRADICTION |
| DECISION-005 | F-03 | "Exclude B2C" | ALIGNMENT |
| DECISION-012 | F-01 | "Global expansion" | OVERLAP |

### Conflicts Analysis

#### 1. CONTRADICTION with DECISION-001
- **Existing**: "Our primary market focus is SMB (Small & Medium Business)"
- **Your Draft**: "Our primary market focus is Enterprise"
- **Severity**: HIGH
- **Explanation**: Both cannot be true simultaneously for same scope

**AI SUGGESTION**: Create new decision with `supersedes: "DECISION-001"` to explicitly evolve market strategy.

#### 2. OVERLAP with DECISION-012
- **Existing**: "Expand into APAC region by 2025"
- **Your Draft**: "Focus on Enterprise in North America"
- **Severity**: MEDIUM
- **Explanation**: Geographic scope may conflict

**AI SUGGESTION**: Clarify if this applies to specific region only, or update DECISION-012 scope.

### Recommendation: REVIEW
Human review required to resolve conflicts before storing.
```

---

## 6. Step 4: Suggestion Generation (Detailed)

### 6.1 Suggestion Categories

| Category | When to Suggest |
|----------|-----------------|
| **Structural** | Missing required fields, format issues |
| **Content** | Vague wording, missing rationale |
| **Conflict Resolution** | Contradictions with existing |
| **Enhancement** | Constraints, invariants that could help |
| **Scope** | Inappropriate blast_radius or scope |

### 6.2 Suggestion Templates

#### Missing Required Field

```markdown
AI SUGGESTION: Missing required field

The draft is missing the `rationale` field which is required per MANTRA-SCHEMA-001.

Rationale should explain WHY this decision is being made, not just WHAT.

Example format:
"Because [context/problem], we decide to [statement] in order to [expected outcome]."

Would you like me to draft a rationale based on the context you've provided?
```

#### Conflict Resolution

```markdown
AI SUGGESTION: Conflict resolution needed

Your draft conflicts with existing decision DECISION-001.

**Option A: Supersede**
- Create new decision with `supersedes: "DECISION-001"`
- This creates version evolution (1.0.0 → 2.0.0)
- Old decision remains for audit trail

**Option B: Narrow Scope**
- Change your scope from ORGANIZATION to DOMAIN
- This allows both decisions to coexist
- Apply: D.scope = "DOMAIN" if only affects engineering

**Option C: Modify Statement**
- Rephrase to complement rather than contradict
- Example: "In addition to SMB, expand to Enterprise segment"

Which approach would you prefer?
```

#### Enhancement

```markdown
AI SUGGESTION: Consider adding constraints

For F-11 (Security & Compliance) decisions, it's recommended to include enforcement constraints.

Suggested constraints:
[
  {
    "constraint_id": "C-001",
    "type": "REQUIREMENT",
    "statement": "All PII must be encrypted with AES-256 minimum"
  },
  {
    "constraint_id": "C-002",
    "type": "PROHIBITION",
    "statement": "PII must not be logged in plaintext"
  }
]

Would you like me to add these to your draft?
```

### 6.3 Suggestion Formatting Rules

1. **Always prefix with "AI SUGGESTION:"**
2. **Explain the reasoning** (Why is this suggested?)
3. **Reference specifications** (Which rule/standard?)
4. **Provide alternatives** (When applicable)
5. **End with question** (Engage human decision)

---

## 7. Step 5: Output Format

### 7.1 Complete Output Template

```markdown
## Classification
GROUP-X / F-YY: [Feature Name]

**Confidence**: HIGH | MEDIUM | LOW
**Alternative Classification**: [If applicable]

---

## Analysis

### Evaluation Summary
- **Clarity**: ✅ Clear / ⚠️ Needs work / ❌ Unclear
- **Completeness**: ✅ Complete / ⚠️ Missing fields / ❌ Incomplete
- **Consistency**: ✅ Consistent / ⚠️ Potential issues / ❌ Conflicts

### Evaluation Details
[Group-specific evaluation findings]

---

## Comparison with Existing

### Related Decisions
[Table of related decisions]

### Conflicts Found
[List of conflicts with severity and explanation]

### Recommendation
**[PROCEED | REVIEW | REVISE]**
[Explanation of recommendation]

---

## AI SUGGESTIONS (Human Review Required)

### 1. [Suggestion Title]
[Detailed suggestion with reasoning]

### 2. [Suggestion Title]
[Detailed suggestion with reasoning]

---

## Draft Decision (FOR HUMAN REVIEW)

```json
{
  "group_id": "GROUP-X",
  "feature_id": "F-YY",
  "statement": "[Prepared statement]",
  "rationale": "[HUMAN TO COMPLETE if missing]",
  "constraints": [],
  "invariants": [],
  "scope": "[Inferred or specified]",
  "blast_radius": "[Suggested based on analysis]",
  "version": "1.0.0",
  "created_by": "[Human identifier - NOT AI]",
  "supersedes": null,
  "related_decisions": []
}
```

---

⚠️ **This is an AI-assisted draft. Human must review and submit.**

- [ ] I have reviewed the classification
- [ ] I have reviewed the suggestions
- [ ] I confirm the statement accurately reflects my intent
- [ ] I have filled in all required fields
- [ ] I am ready to submit via POST /decisions
```

---

## 8. Human-AI Collaboration Patterns

### 8.1 Pattern: Iterative Refinement

```
Human: "We need to protect customer data"

AI: [Classification] GROUP-3 / F-11 (Security)
    [Evaluation] Vague statement, missing specifics
    [Suggestion] Clarify what "protect" means
    [Question] "Do you mean encryption, access control, or both?"

Human: "We mean encryption at rest and in transit"

AI: [Updated Draft]
    {
      "statement": "All customer PII must be encrypted at rest and in transit",
      "constraints": [
        {"type": "REQUIREMENT", "statement": "AES-256 for at-rest"},
        {"type": "REQUIREMENT", "statement": "TLS 1.3 for in-transit"}
      ]
    }
    [Question] "Should I also add access control constraints?"

Human: "Yes, add RBAC"

AI: [Final Draft Ready]
    [Suggestion] Added RBAC constraint
    [Status] Ready for human review
```

### 8.2 Pattern: Conflict Detection

```
Human: "Our API should return XML"

AI: [Classification] GROUP-2 / F-08 (Integration)
    [Comparison] Found DECISION-001: "API responses must be JSON"
    [Conflict] CONTRADICTION detected
    [Options]
    A) Supersede DECISION-001 (change all to XML)
    B) Narrow scope (XML for specific endpoint)
    C) Coexist (support both formats)
    [Question] "Which approach do you prefer?"

Human: "Let's support both"

AI: [Updated Draft]
    "statement": "API supports both JSON (default) and XML formats"
    "supersedes": null  // No supersede needed
    "related_decisions": ["DECISION-001"]
```

### 8.3 Pattern: Gap Detection

```
AI: [Proactive Analysis]
    Found gap in GROUP-3 decisions:
    - F-09 (Policy): 5 decisions
    - F-10 (Authority): 3 decisions
    - F-11 (Security): 0 decisions  ← GAP
    - F-12 (Risk): 2 decisions

    [Suggestion] Consider adding security decisions for:
    - Data encryption policies
    - Authentication requirements
    - Compliance standards (GDPR, etc.)

    Would you like me to help draft any of these?
```

---

## 9. Error Handling

### 9.1 Classification Uncertainty

```
AI: I'm unable to confidently classify this input.

The statement "We should be more careful" could be:
- GROUP-1 / F-04 (Principles) if interpreted as a value statement
- GROUP-3 / F-09 (Policy) if interpreted as a rule
- GROUP-4 / F-12 (Risk) if interpreted as risk mitigation

Could you clarify:
1. What specific area should "more careful" apply to?
2. Is this a guiding principle or an enforceable rule?
3. What triggered this concern?
```

### 9.2 Validation Failure

```
AI: Validation returned 3 violations:

1. [S-001] Missing required field: rationale
   → Add explanation for WHY this decision is needed

2. [D-005] Feature F-01 not compatible with GROUP-2
   → Change group_id to GROUP-1 for vision statements

3. [L-003] created_by must be human identifier
   → Replace "system" with your user identifier

Draft needs corrections. Would you like help fixing these?
```

---

## 10. References

- MANTRA-L1-AI-OPERATIONAL-GUIDELINES-001: Authority Boundaries
- MANTRA-L1-AI-CLASSIFICATION-GUIDE-001: Classification Details
- MANTRA-SCHEMA-001: Decision Schema
- MANTRA-LAW-001: Constitutional Law

---

**Document Status**: ACTIVE
**Last Updated**: 2025-01-25
**Maintained By**: ARSAKA_MANTRA Team
