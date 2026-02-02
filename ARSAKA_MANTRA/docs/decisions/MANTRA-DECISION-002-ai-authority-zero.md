# MANTRA-DECISION-002: AI Authority Zero

> **Self-Validation**: This decision about MANTRA is recorded IN MANTRA.

## Decision Record

| Field | Value |
|-------|-------|
| **decision_id** | `MANTRA-DECISION-002` |
| **group_id** | GROUP-3 |
| **feature_id** | F-10 (Approval & Authority Model) |
| **version** | 1.0.0 |
| **scope** | ORGANIZATION |
| **blast_radius** | CRITICAL |
| **created_by** | ARSAKA_MANTRA Core Team |
| **created_at** | 2025-01-24 |
| **supersedes** | null |

---

## Statement

**AI authority in decision-making is ZERO. AI cannot create, approve, modify, or finalize decisions. Only humans have decision authority.**

---

## Rationale

Human authority is non-negotiable because:

1. **Accountability**: Humans can be held accountable for decisions. AI cannot face consequences, cannot be fired, cannot go to court.

2. **Legal Standing**: In most jurisdictions, decisions affecting people/organizations must have human accountability. "The AI decided" is not a legal defense.

3. **Judgment**: Decisions require contextual judgment that considers ethics, relationships, politics, and nuance. AI lacks this holistic understanding.

4. **Override Capability**: Humans must always be able to override, challenge, or reverse decisions. If AI has authority, override becomes technically and organizationally complex.

5. **Trust**: Stakeholders trust decisions made by identifiable humans, not black-box algorithms.

---

## What AI CAN Do

AI is a powerful **tool** but not an **authority**:

| AI CAN | AI CANNOT |
|--------|-----------|
| Analyze existing decisions | Create new decisions |
| Detect conflicts between decisions | Resolve conflicts |
| Suggest decision wording | Approve decision wording |
| Flag gaps in decision coverage | Fill gaps with decisions |
| Generate reports | Act on reports |
| Assist human drafting | Submit drafts as final |

---

## Constraints

### PROHIBITION
1. **P-001**: API endpoints for create/approve MUST require human authentication
2. **P-002**: `created_by` and `approved_by` fields MUST be human identifiers
3. **P-003**: Automated systems MUST NOT call decision creation endpoints
4. **P-004**: AI assistants MUST NOT have API keys for write operations

### REQUIREMENT
1. **R-001**: Every decision MUST have identifiable human creator
2. **R-002**: Every decision MUST have identifiable human approver
3. **R-003**: Audit trail MUST distinguish human vs AI actions
4. **R-004**: AI suggestions MUST be clearly labeled as suggestions

### LIMITATION
1. **L-001**: "AI-assisted" decisions are valid IF human approves final version
2. **L-002**: AI can draft, human must review and submit

---

## Invariants

These properties are ALWAYS true:

1. Every stored decision has a human `created_by`
2. Every stored decision has a human approver (explicit or implicit)
3. AI cannot directly write to decision store
4. `actor_type: "ai"` never appears in decision creation audit logs

---

## Implementation Reference

Per MANTRA-LAW-001 §6:

```python
# backend/core/domain/decision.py
@dataclass
class AuditEntry:
    actor: str
    actor_type: str  # "human" or "ai"

    def __post_init__(self):
        if self.actor_type not in ("human", "ai"):
            raise ValueError("actor_type must be 'human' or 'ai'")

        # AI cannot create decisions - enforced at API layer
        # actor_type is for AUDIT purposes, not authorization
```

```python
# backend/core/api/routes.py
@router.post("/decisions")
async def store_decision(request: StoreRequest):
    # stored_by MUST be human identifier
    # This is enforced by authentication middleware
    # No API keys issued to automated systems for write operations
```

---

## Related Decisions

- MANTRA-DECISION-001: Immutability Principle (AI cannot modify either)
- MANTRA-DECISION-003: Status Field Removal (no automated status transitions)

---

## Practical Implications

### For Development Teams

```
Allowed workflow:
1. Developer asks AI: "Draft a decision about API versioning"
2. AI generates draft
3. Developer reviews, modifies, approves
4. Developer submits to MANTRA (human action)
5. Decision recorded with developer as created_by

NOT allowed:
1. CI/CD pipeline automatically creates decision
2. AI agent submits decision via API
3. Automated approval based on rules
```

### For Compliance

```
Auditor: "Who decided to deprecate the v1 API?"
Answer: "John Smith, Engineering Lead, on 2025-01-15"

NOT acceptable:
Answer: "The system automatically decided based on usage metrics"
```

---

## Evolution Path

This decision is foundational to MANTRA's philosophy. If AI authority is ever considered:

1. Requires constitutional amendment (Layer 0)
2. Must address accountability gap
3. Must address legal implications
4. Create MANTRA-DECISION-002 v2.0.0 with full rationale
