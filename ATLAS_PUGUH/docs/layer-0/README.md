# INFRA Layer 0: Foundation Design

**STATUS**: COMPLETE & LOCKED (2025-12-27)

This layer defines the **foundational concepts** of Infra SaaS:
- What is a Decision and how does it flow?
- How is tenancy isolated?
- How are Rules, Workflows, and Approvals structured?

All 10 foundational questions are answered. No unresolved contradictions.

---

## Documents

### 1. [INFRA-DEC-001: Decision Model](./INFRA-DEC-001-decision-model.md)

**Answers**: What is a Decision? What are the outcomes? How does it flow?

**Key Concepts**:
- **Decision**: Atomic authorization query → one of 3 outcomes (ALLOWED, DENIED, REQUIRE_APPROVAL)
- **Decision Type**: Naming convention `{module}.{entity}.{action}` (locked)
- **Decision Outcome**: Immutable after decided
- **Rule Matching**: Single rule_matched (first-match-wins, v1)
- **Fail-Closed**: No matching rule → DENIED (security principle)

**Examples**: 5 concrete decisions (accounting, PMS, inventory, procurement)

---

### 2. [INFRA-DEC-002: Tenancy Model & Isolation Boundaries](./INFRA-DEC-002-tenancy-model.md)

**Answers**: How is multi-tenancy isolated? Who validates entities?

**Key Concepts**:
- **Tenant Isolation**: 4 hard boundaries (rules, audit logs, workflows, context)
- **Context Propagation**: SDK → Core validates → Rules (tenant-scoped) → Storage (partitioned)
- **Entity Ownership**: Delegated to application adapter (Infra trusts, audits)
- **Organization Metadata**: organization_name is non-logical (display/audit only)
- **Cross-Tenant Safety**: Forbidden scenarios explicit (guard rails)

---

### 3. [INFRA-DEC-003: Rule & Workflow Abstraction](./INFRA-DEC-003-rule-workflow-abstraction.md)

**Answers**: How are rules structured? How do approvals work?

**Key Concepts**:
- **Rules**: Form-based configuration (no code), deterministic evaluation
- **Rule Evaluation Order**: Explicit list (no priority field), first-match-wins
- **Conditions**: Numeric, string, boolean, compound (nesting max depth = 3)
- **Approvers**: Role identifiers (not user IDs), user resolution via app adapter
- **Workflows**: Sequential state machine (PENDING → APPROVED/REJECTED/ESCALATED/DELEGATED)
- **Extension Hooks**: Async, non-blocking, fire-and-forget

---

## Quick Reference: 10 Foundational Questions

| # | Question | Answer Summary | Document |
|---|----------|---------------|---------
| 1 | What is a Decision? | Atomic authorization query with 3 outcomes | INFRA-DEC-001 |
| 2 | What outcomes? | ALLOWED, DENIED, REQUIRE_APPROVAL | INFRA-DEC-001 |
| 3 | Decision type naming? | `{module}.{entity}.{action}` (locked format) | INFRA-DEC-001 |
| 4 | No matching rule? | DENIED (fail-closed, logged SECURITY_EVENT) | INFRA-DEC-001 |
| 5 | Outcome mutable? | NO - immutable forever | INFRA-DEC-001 |
| 6 | Tenant isolation? | 4 hard boundaries (rules, logs, workflows, context) | INFRA-DEC-002 |
| 7 | organization_name used in logic? | NO - metadata only (display/audit) | INFRA-DEC-002 |
| 8 | Entity ownership validation? | Delegated to app adapter (Infra audits) | INFRA-DEC-002 |
| 9 | Rule evaluation? | Form-based, explicit order, first-match-wins | INFRA-DEC-003 |
| 10 | Approval orchestration? | Sequential workflows, role-based approvers | INFRA-DEC-003 |

---

## Design Principles (All Locked)

✅ **Domain-Agnostic**: No business logic, only abstractions
✅ **SDK-First**: Contracts designed for SDK, not CMS-first
✅ **Multi-Tenant Safe**: Isolation from day 1
✅ **Immutable Decisions**: outcome never changes
✅ **Fail-Closed**: Missing rules → DENIED
✅ **First-Match-Wins**: Rule evaluation deterministic
✅ **Roles Not Users**: Approvers by role, user resolution delegated
✅ **Async Non-Blocking**: Extension hooks don't block critical path
✅ **Audit Trail**: Decisions/workflows immutable + logged
✅ **Explainability**: Decision traceable to rule + version + context

---

## What's NOT in Layer 0

These are **deferred to Layer 1+**:

- **SDK Method Signatures** → Layer 1a
- **CMS API Endpoints** → Layer 1b
- **Events & Webhooks** → Layer 1c
- **Data Model & Schema** → Layer 1d
- **Implementation Details** → Layer 2+

---

## Reading Order

**For Quick Orientation:**
1. Read this README (you are here)
2. Skim LAYER-0-VERIFICATION.md (coverage & consistency check)
3. Read INFRA-DEC-001 (understand Decision flow)
4. Read INFRA-DEC-002 (understand tenant isolation)
5. Read INFRA-DEC-003 (understand rules & workflows)

**For Deep Dive:**
1. Start with INFRA-DEC-001 (foundational concepts)
2. Review 5 concrete examples (decision types, outcomes)
3. Study INFRA-DEC-002 sections on guard rails
4. Study INFRA-DEC-003 sections on condition syntax & workflows
5. Cross-reference LAYER-0-VERIFICATION for consistency

---

## Next Phase: Layer 1

When ready, Layer 1 will define:

- **1a**: SDK Contracts (method signatures, request/response)
- **1b**: CMS API (rule/workflow management endpoints)
- **1c**: Events (emitted events, webhook delivery)
- **1d**: Data Model (schema, indexes, partitioning)

See LAYER-0-VERIFICATION.md § 8 for detailed Layer 1 scope.

---

## Version History

| Date | Event | Status |
|------|-------|--------|
| 2025-12-27 | INFRA-DEC-001 Created | LOCKED |
| 2025-12-27 | INFRA-DEC-002 Created | LOCKED |
| 2025-12-27 | INFRA-DEC-003 Created | LOCKED |
| 2025-12-27 | LAYER-0-VERIFICATION Created | COMPLETE |
| 2025-12-27 | Files reorganized to layer-0/ | ORGANIZED |

**Layer 0 is FROZEN** (no further changes without user approval)
