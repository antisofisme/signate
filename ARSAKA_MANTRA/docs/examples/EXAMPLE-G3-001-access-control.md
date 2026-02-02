# EXAMPLE-G3-001: Access Control Policy

> **Example Decision**: Copy and adapt for your organization.

## Decision Record

| Field | Value |
|-------|-------|
| **decision_id** | `EXAMPLE-G3-001` |
| **group_id** | GROUP-3 (Control, Policy & Risk) |
| **feature_id** | F-09 (Policy & Rules) |
| **version** | 1.0.0 |
| **scope** | ORGANIZATION |
| **blast_radius** | CRITICAL |
| **created_by** | [Your Name] |
| **created_at** | [Date] |
| **supersedes** | null |

---

## Statement

**Access to Personally Identifiable Information (PII) requires explicit permission grant. No role has implicit PII access.**

---

## Rationale

Explicit PII permission because:

1. **Least Privilege**: Not everyone who needs system access needs PII access. Engineer fixing a bug doesn't need customer emails.

2. **Audit Trail**: Explicit grants create auditable record of who has PII access and when it was granted.

3. **Compliance**: GDPR Article 25 requires "data protection by design." Explicit permission is a technical control.

4. **Breach Containment**: If credentials are compromised, damage is limited to granted permissions, not all data.

5. **Access Review**: Explicit grants enable periodic access reviews. Can't review what isn't tracked.

---

## Policy Definition

### PII Categories

| Category | Examples | Sensitivity |
|----------|----------|-------------|
| **Identity** | Name, email, phone | HIGH |
| **Financial** | Bank account, tax ID | CRITICAL |
| **Location** | Address, GPS data | HIGH |
| **Health** | Medical records | CRITICAL |
| **Behavioral** | Purchase history, preferences | MEDIUM |

### Permission Model

```
Permission Format: pii.{category}.{action}

Examples:
- pii.identity.read      # Read names, emails
- pii.identity.export    # Export identity data
- pii.financial.read     # Read financial data
- pii.all.admin          # Full PII access (rare)
```

### Grant Process

```
1. Requester submits PII access request
   └── Justification required
   └── Duration specified (default: 90 days)

2. Manager approval
   └── Verifies business need

3. Security team review
   └── For CRITICAL categories

4. Grant created with expiration
   └── Logged in audit trail

5. Periodic review (quarterly)
   └── Revoke if no longer needed
```

---

## Constraints

### PROHIBITION
1. **P-001**: Roles MUST NOT have implicit PII access (including Admin role)
2. **P-002**: PII permissions MUST NOT be permanent (max 1 year, review required)
3. **P-003**: PII data MUST NOT be accessible without audit logging
4. **P-004**: PII permissions MUST NOT be self-granted

### REQUIREMENT
1. **R-001**: All PII access MUST have explicit permission grant
2. **R-002**: PII permission grants MUST have business justification
3. **R-003**: PII access MUST be logged with accessor identity and timestamp
4. **R-004**: PII permissions MUST expire (default: 90 days)

### LIMITATION
1. **L-001**: Maximum 5 CRITICAL PII permission holders per team
2. **L-002**: PII export permissions require VP-level approval

---

## Invariants

These properties are ALWAYS true:

1. No implicit PII access exists in any role
2. Every PII access is logged
3. Every PII permission has an expiration date
4. Every PII permission has an approval trail

---

## Implementation Reference

### Permission Check

```python
def check_pii_access(user_id: str, pii_category: str, action: str) -> bool:
    """
    Check if user has explicit PII permission.
    Never returns True based on role alone.
    """
    permission = f"pii.{pii_category}.{action}"

    # Check explicit grant
    grant = permission_repo.find_grant(
        user_id=user_id,
        permission=permission
    )

    if not grant:
        return False

    if grant.expires_at < now():
        return False

    # Log access attempt
    audit_log.record(
        actor=user_id,
        permission=permission,
        action="access_check",
        result="granted"
    )

    return True
```

### API Protection

```python
@router.get("/customers/{id}")
@requires_permission("pii.identity.read")
async def get_customer(id: str, current_user: User):
    # Permission decorator checks explicit grant
    # Not role-based, not implicit
    return customer_service.get(id)
```

### Grant Schema

```sql
CREATE TABLE pii_permission_grants (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    permission VARCHAR(100) NOT NULL,  -- e.g., "pii.identity.read"
    justification TEXT NOT NULL,
    granted_by UUID NOT NULL,
    approved_by UUID NOT NULL,
    granted_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    revoked_by UUID,
    CONSTRAINT valid_expiration CHECK (expires_at > granted_at)
);
```

---

## Audit Trail

```
┌─────────────────────────────────────────────────────────────────┐
│ PII Access Log                                                   │
├─────────────────────────────────────────────────────────────────┤
│ 2025-01-24 10:00:00 | user_123 | pii.identity.read | GRANTED    │
│ 2025-01-24 10:00:01 | user_123 | accessed customer cust_456     │
│ 2025-01-24 10:05:00 | user_789 | pii.financial.read | DENIED    │
│ 2025-01-24 10:10:00 | admin_01 | granted pii.identity.read to   │
│                     |          | user_789 (expires: 2025-04-24) │
└─────────────────────────────────────────────────────────────────┘
```

---

## Related Decisions

- EXAMPLE-G2-002: Data Ownership (defines what data exists where)
- EXAMPLE-G3-002: Approval Authority (defines who can approve grants)
- [Future]: Data Retention Policy (GROUP-3/F-11)

---

## Evolution Path

Access control may evolve when:
- New PII categories are introduced
- Compliance requirements change
- Automation opportunities arise

Example evolution:
```
v1.0.0: "Explicit PII permission required"
v1.1.0: "Explicit PII permission + just-in-time access for support"
v2.0.0: "Zero-trust PII access with continuous verification"
```

---

## Template Notes

**When adapting this example:**

1. Define your PII categories and sensitivity levels
2. Document the grant/approval workflow
3. Specify expiration and review policies
4. Include audit logging requirements
5. Show implementation patterns (code/schema)
