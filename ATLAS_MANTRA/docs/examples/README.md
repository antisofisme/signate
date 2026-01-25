# MANTRA Example Decisions

> **Real-World Templates**: Copy and adapt these examples for your organization.

This directory contains example decisions across all 4 Groups, demonstrating how to use MANTRA for common organizational decisions.

---

## Example Index

### GROUP-1: Intent & Direction (WHY/WHAT)

| ID | Feature | Statement |
|----|---------|-----------|
| [EXAMPLE-G1-001](./EXAMPLE-G1-001-product-vision.md) | F-01 | Our product focuses on B2B SaaS market |
| [EXAMPLE-G1-002](./EXAMPLE-G1-002-problem-scope.md) | F-02 | We solve the enterprise scheduling problem |

### GROUP-2: Architecture & Boundaries (HOW/WHERE)

| ID | Feature | Statement |
|----|---------|-----------|
| [EXAMPLE-G2-001](./EXAMPLE-G2-001-service-boundary.md) | F-06 | Payment is a standalone microservice |
| [EXAMPLE-G2-002](./EXAMPLE-G2-002-data-ownership.md) | F-07 | Customer data owned by CRM domain |

### GROUP-3: Control, Policy & Risk (CAN/MUST NOT)

| ID | Feature | Statement |
|----|---------|-----------|
| [EXAMPLE-G3-001](./EXAMPLE-G3-001-access-control.md) | F-09 | PII access requires explicit permission grant |
| [EXAMPLE-G3-002](./EXAMPLE-G3-002-approval-authority.md) | F-10 | Production deployments require two approvers |

### GROUP-4: Execution & Evolution (CHANGE)

| ID | Feature | Statement |
|----|---------|-----------|
| [EXAMPLE-G4-001](./EXAMPLE-G4-001-api-versioning.md) | F-15 | All public APIs use URL versioning |
| [EXAMPLE-G4-002](./EXAMPLE-G4-002-deprecation-policy.md) | F-14 | APIs deprecated with 12-month notice |

---

## How to Use These Examples

### 1. Identify Similar Decision

Find an example that matches your decision type:
- **Vision decisions** → EXAMPLE-G1-001
- **Problem definition** → EXAMPLE-G1-002
- **Service boundaries** → EXAMPLE-G2-001
- **Data ownership** → EXAMPLE-G2-002
- **Access policies** → EXAMPLE-G3-001
- **Approval workflows** → EXAMPLE-G3-002
- **API standards** → EXAMPLE-G4-001
- **Deprecation rules** → EXAMPLE-G4-002

### 2. Copy Structure

Each example follows the same structure:
```markdown
# Decision Record
- decision_id, group_id, feature_id, version, scope, blast_radius
- created_by, created_at, supersedes

# Statement
- Clear, one-sentence decision

# Rationale
- WHY this decision (required)

# Constraints
- PROHIBITION: What MUST NOT happen
- REQUIREMENT: What MUST happen
- LIMITATION: Boundaries

# Invariants
- What is ALWAYS true

# Implementation Reference
- Code/config that implements this

# Related Decisions
- Links to other decisions
```

### 3. Adapt for Your Context

Replace:
- Organization-specific details
- Technical stack references
- Team names and roles
- Dates and versions

Keep:
- Structure and format
- Constraint categories
- Rationale depth

---

## Example Decision Flow

```
1. Identify need for decision
   "We need to decide how APIs are versioned"

2. Find matching example
   → EXAMPLE-G4-001 (API Versioning)

3. Copy and adapt
   - Change statement to your specific rule
   - Update rationale for your context
   - Adjust constraints as needed

4. Record in MANTRA
   - POST /api/v1/decisions
   - Or use MANTRA UI

5. Share with team
   - Decision is now permanent and searchable
```

---

## Best Practices from Examples

### Writing Good Statements

**Good** (from examples):
- "All public APIs MUST use URL versioning with format /api/v{major}/"
- "Customer data is owned by the CRM domain and MUST NOT be directly accessed by other services"

**Avoid**:
- "We should probably version our APIs"
- "Customer data belongs to CRM sort of"

### Writing Good Rationale

**Good** (from examples):
- "URL versioning is explicit, cacheable, and doesn't require header inspection. Major version in URL allows breaking changes without client coordination."

**Avoid**:
- "Because it's good practice"
- "Everyone does it this way"

### Defining Clear Constraints

**Good** (from examples):
- PROHIBITION: "APIs MUST NOT be removed without 12-month deprecation notice"
- REQUIREMENT: "All breaking changes MUST increment major version"
- LIMITATION: "Deprecation notice cannot be shortened once published"

**Avoid**:
- Vague prohibitions without specific conditions
- Requirements without enforcement mechanism
- Limitations that can be easily bypassed

---

## Questions?

- **Format questions**: See [GUIDE-001-getting-started](../guides/GUIDE-001-getting-started.md)
- **Philosophy questions**: See [VALUE-001-why-mantra](../value/VALUE-001-why-mantra.md)
- **System decisions**: See [decisions/](../decisions/) for how MANTRA itself is recorded
