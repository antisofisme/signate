# EXAMPLE-G3-002: Approval Authority

> **Example Decision**: Copy and adapt for your organization.

## Decision Record

| Field | Value |
|-------|-------|
| **decision_id** | `EXAMPLE-G3-002` |
| **group_id** | GROUP-3 (Control, Policy & Risk) |
| **feature_id** | F-10 (Approval & Authority Model) |
| **version** | 1.0.0 |
| **scope** | ORGANIZATION |
| **blast_radius** | HIGH |
| **created_by** | [Your Name] |
| **created_at** | [Date] |
| **supersedes** | null |

---

## Statement

**Production deployments require approval from two authorized approvers: one from the owning team and one from platform/SRE.**

---

## Rationale

Dual approval for production because:

1. **Four Eyes Principle**: Two independent reviewers catch issues single reviewer might miss.

2. **Separation of Duties**: Team knows the code, SRE knows the infrastructure. Both perspectives needed.

3. **Accountability**: Clear record of who approved. No "it just got deployed."

4. **Risk Mitigation**: Production incidents are expensive. Extra approval step is cheap insurance.

5. **Knowledge Sharing**: SRE sees all deployments, builds organizational knowledge of changes.

---

## Authority Matrix

### Deployment Approvals

| Environment | Approvers Required | Who Can Approve |
|-------------|-------------------|-----------------|
| Development | 0 | Self (auto-deploy) |
| Staging | 1 | Team member |
| Production | 2 | 1 Team Lead + 1 SRE |
| Production (hotfix) | 1 | On-call SRE (post-incident review required) |

### Approver Qualifications

| Role | Can Approve | Requirements |
|------|-------------|--------------|
| Team Lead | Own team's deployments | Completed deployment training |
| Senior Engineer | Own team's deployments | 6+ months tenure, Lead designation |
| SRE | Any deployment | SRE team member |
| On-call | Hotfixes only | Current on-call rotation |

---

## Approval Workflow

```
1. Developer creates deployment request
   └── Includes: change description, rollback plan, monitoring checklist

2. Team approver reviews
   └── Checks: code review complete, tests passing, documentation updated
   └── Approves or requests changes

3. SRE approver reviews
   └── Checks: infrastructure impact, scaling, monitoring, alerts
   └── Approves or requests changes

4. Both approvals received
   └── Deployment unlocked
   └── Audit record created

5. Developer triggers deployment
   └── Approval expires after 24 hours (must re-approve if stale)
```

---

## Constraints

### PROHIBITION
1. **P-001**: Self-approval for production MUST NOT be allowed
2. **P-002**: Single approver MUST NOT satisfy production deployment requirement
3. **P-003**: Approvers MUST NOT approve without reviewing the change
4. **P-004**: Approval authority MUST NOT be delegated to automation

### REQUIREMENT
1. **R-001**: Production deployments MUST have two approvals before proceeding
2. **R-002**: At least one approver MUST be from platform/SRE team
3. **R-003**: Approvals MUST be recorded with approver identity and timestamp
4. **R-004**: Approvals MUST expire after 24 hours

### LIMITATION
1. **L-001**: Emergency hotfixes can have single SRE approval (post-incident review required)
2. **L-002**: Approval authority limited to designated roles (no ad-hoc grants)

---

## Invariants

These properties are ALWAYS true:

1. Production deployments have approval record
2. No self-approval for production
3. SRE perspective always included in production approval
4. Approval trail is immutable

---

## Implementation Reference

### Deployment Request Schema

```yaml
deployment_request:
  id: "deploy-2025-01-24-001"
  service: "payment-service"
  environment: "production"
  requester: "dev_alice"
  change_description: "Add PayPal integration"
  rollback_plan: "Revert to v2.3.1, disable PayPal feature flag"
  approvals:
    - approver: "lead_bob"
      role: "team_lead"
      approved_at: "2025-01-24T10:00:00Z"
      checklist:
        code_review: true
        tests_passing: true
        documentation: true
    - approver: "sre_charlie"
      role: "sre"
      approved_at: "2025-01-24T10:30:00Z"
      checklist:
        infrastructure_impact: "low"
        monitoring_configured: true
        alerts_configured: true
  status: "approved"
  expires_at: "2025-01-25T10:30:00Z"
```

### Approval Check

```python
def can_deploy(deployment: Deployment) -> Tuple[bool, str]:
    """Check if deployment has required approvals."""

    if deployment.environment != "production":
        return True, "Non-production, no approval required"

    approvals = deployment.approvals

    # Check team approval
    team_approval = next(
        (a for a in approvals if a.role in ["team_lead", "senior_engineer"]),
        None
    )
    if not team_approval:
        return False, "Missing team approval"

    # Check SRE approval
    sre_approval = next(
        (a for a in approvals if a.role == "sre"),
        None
    )
    if not sre_approval:
        return False, "Missing SRE approval"

    # Check expiration
    if any(a.is_expired() for a in [team_approval, sre_approval]):
        return False, "Approval expired (24h limit)"

    # Check self-approval
    if deployment.requester in [team_approval.approver, sre_approval.approver]:
        return False, "Self-approval not allowed"

    return True, "Approved"
```

### UI Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Deployment Request: payment-service → production            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Change: Add PayPal integration                             │
│  Requester: Alice (dev_alice)                              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Team Approval                           [APPROVED]  │   │
│  │ Approver: Bob (lead_bob)                           │   │
│  │ Time: 2025-01-24 10:00 AM                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ SRE Approval                            [APPROVED]  │   │
│  │ Approver: Charlie (sre_charlie)                    │   │
│  │ Time: 2025-01-24 10:30 AM                          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Status: READY TO DEPLOY                                    │
│  Expires: 2025-01-25 10:30 AM (23 hours remaining)         │
│                                                             │
│                              [Deploy to Production]         │
└─────────────────────────────────────────────────────────────┘
```

---

## Exception Handling

### Emergency Hotfix Process

When production is down and dual approval would cause unacceptable delay:

1. On-call SRE can single-approve hotfix
2. Deployment proceeds immediately
3. **Within 24 hours**: Post-incident review with missing approver
4. Review can result in: approval ratification or rollback requirement

```
Hotfix Approval:
- approver: "oncall_dave"
- type: "emergency_single_approval"
- justification: "Production P1: payment processing down"
- post_incident_review_required: true
- review_deadline: "2025-01-25T10:00:00Z"
```

---

## Related Decisions

- EXAMPLE-G3-001: Access Control (defines permission model)
- EXAMPLE-G4-001: API Versioning (may require approval for breaking changes)
- [Future]: Incident Response Process (GROUP-3/F-12)

---

## Evolution Path

Approval authority may evolve when:
- Team size changes
- Risk tolerance changes
- Automation capabilities improve

Example evolution:
```
v1.0.0: "Dual approval: Team + SRE"
v1.1.0: "Dual approval + automated canary validation"
v2.0.0: "Progressive delivery with automatic rollback (approval for feature, not deployment)"
```

---

## Template Notes

**When adapting this example:**

1. Define your environments and approval requirements
2. Specify who can approve (roles, qualifications)
3. Document the approval workflow
4. Include exception handling (emergencies)
5. Show implementation in your deployment system
