# ADR Template: Architectural Decision Record

Use this template for ANY decision not locked in Layer 0-3.

**Note**: Decisions already made in Layers 0-3 do NOT need ADR.
This template is for **new choices** (frameworks, libraries, implementation details).

---

## ADR-NNN: [Decision Title]

**Status**: PROPOSED / ACCEPTED / REJECTED / SUPERSEDED

**Date**: [YYYY-MM-DD]

**Affects**: [Which layer/component]

---

## Problem Statement

What decision needs to be made? Why?

**Context**: What constraints from Layer 0-3 apply?

---

## Options Considered

### Option A: [Name]

**Pros**:
- Item 1
- Item 2

**Cons**:
- Item 1
- Item 2

**Compliance with JARVIS contracts**:
- ✅ or ❌ Layer 1-DEC-004 (CLI interaction)
- ✅ or ❌ JARVIS-L3-ARCH-002 (threading)
- etc.

---

### Option B: [Name]

[Same structure as Option A]

---

### Option C: [Alternative Rejected]

**Why rejected** (this prevents re-debate in 6 months):
- Violates JARVIS-L3-ARCH-002 (threading model)
- Adds external dependency (game launcher incompatible)
- Requires state persistence (Layer 0-DEC-002 forbids)

---

## Decision

**We will use Option [X].**

**Rationale**:
- Aligns with Layer [N] contracts
- Maintains single-writer threading model
- Deterministic behavior (can be tested)

---

## Constraints & Requirements

**From architecture layers**:

- [List which Layer 0-3 contracts apply]
- STT must block (JARVIS-L3-ARCH-002)
- No persistent state (JARVIS-DEC-002)
- Fire-and-forget CLI (JARVIS-L1-DEC-004)

**This decision must ensure**:
- [ ] No async STT
- [ ] No race conditions (single-writer rule)
- [ ] No silent errors
- [ ] Command path isolated from voice path
- [ ] etc.

---

## Implementation Notes

**Where**: [Which file/component]

**How**: [Brief outline, not full code]

**Testing**:
- [ ] Unit test for pure function behavior
- [ ] Integration test with adjacent components
- [ ] Invariant test (if touching Layer 1-3)

---

## Compliance Verification

- [ ] Reviewed against Layer 0-3 documents
- [ ] Passes architectural invariant tests
- [ ] Does NOT change any locked contract
- [ ] Code review references this ADR

---

## Related

- **JARVIS-Layer-N**: [Which architecture layer is affected]
- **Other ADRs**: [If depends on other decisions]

---

## Revision History

| Date | Status | Notes |
|------|--------|-------|
| [Date] | PROPOSED | Initial proposal |
| [Date] | ACCEPTED | [Details] |

