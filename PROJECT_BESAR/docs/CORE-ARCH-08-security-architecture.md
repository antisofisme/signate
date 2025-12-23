# ARCH-08: Security Architecture & Constitution

This document establishes the **security philosophy and constitutional framework** for PROJECT_BESAR. Security in large cloud-based, multi-tenant applications is not a feature or checklist—it is **enforced discipline built into architecture**.

All other security specifications (SEC-01, SEC-02), standards (STD-17), and implementation patterns derive from these principles.

---

## Core Security Principles

These five principles guide every architecture decision in PROJECT_BESAR:

### 1. Assume Breach
Design systems assuming compromise will occur. Focus on:
- Rapid detection and response
- Limiting blast radius (isolation, segmentation)
- Recovery capabilities (backup, audit trails)
- Never rely on "it won't happen"

### 2. Defense in Depth
Security is layered. No single control is trusted:
- Application-level validation (input, business rules)
- Database constraints (tenant_id, foreign keys, checks)
- Infrastructure controls (network, IAM, firewalls)
- Each layer independent and hardened

### 3. Default Deny
Explicit permission required for all access:
- Deny network traffic by default, allow specific routes
- Deny data access by default, require explicit role/permission
- Deny configuration changes by default, require approval workflow
- Users get minimum required permissions, never "admin by default"

### 4. Detect → Respond → Recover
Security is continuous, not one-time:
- **Detect**: Centralized logging, anomaly detection, alerting
- **Respond**: Incident playbooks, kill switches, feature flags for rollback
- **Recover**: Backup/restore procedures tested regularly, audit trails for forensics

### 5. AI = Junior Developer, Not Decision Maker
- AI coding assistance (generation) requires human review
- AI cannot make security decisions independently
- Static analysis tools must validate AI output
- AI never has production/secrets access
- Invariant violations reject AI-generated code outright

---

## Crown Jewels (Highest Priority Protection)

These are the most critical assets. Compromise here affects entire business:

1. **Identity & Tenant Boundary**
   - User authentication (proof of identity)
   - Tenant isolation (which organization's data user accesses)
   - If compromised: complete data exposure, cross-tenant breach

2. **Accounting & Ledger**
   - Financial records, revenue tracking, payment history
   - Append-only, immutable (never deleted or modified)
   - If compromised: financial fraud, audit failure, legal liability

3. **Event & Workflow Finance**
   - Transactional events (payments, refunds, charges)
   - Must be idempotent (no double-charge if replayed)
   - If compromised: fraud, duplicate charges, money loss

4. **Secrets & Credentials**
   - API keys, database passwords, encryption keys
   - Third-party service credentials
   - If compromised: entire infrastructure compromised

**Protection Strategy for Crown Jewels:**
- Immutable audit trails (who accessed, when, what action)
- Encryption at rest and in transit
- Dual approval for sensitive changes (two people must approve)
- Network isolation (only necessary services can access)
- Monitoring and alerting on access patterns

---

## Non-Negotiable Invariants

These rules **cannot be violated**, even by accident or under pressure:

### Identity & Tenancy
```
INVARIANT: User NEVER determines tenant_id
```
- Tenant context injected by system, never from user request
- Example: Instead of `POST /api/guests?tenant_id=123`, system derives tenant from authentication token
- Prevents: accidental/intentional access to other tenant's data

### Financial Data
```
INVARIANT: Ledger entries are APPEND-ONLY
```
- Financial records never deleted or updated
- Corrections use reversals (new entries reversing old ones)
- Prevents: audit failure, fraud, compliance violation

```
INVARIANT: Financial events are IDEMPOTENT
```
- Replaying same payment event twice = same result (not double charge)
- Use idempotency keys in payment processors
- Prevents: fraud, money loss, customer complaints

### Secrets
```
INVARIANT: Secrets NEVER appear in logs, frontend, or code
```
- Logs must strip credentials
- Frontend code has no API keys or passwords
- Code repositories use secret manager, never `.env` files
- Prevents: accidental exposure, security breach

### Multi-Tenant
```
INVARIANT: Cross-tenant access is EXPLICIT & APPROVED
```
- No implicit access to other tenant's data
- Superadmin does NOT automatically bypass tenant boundaries
- Admin accessing another tenant's data requires explicit permission and audit log
- Prevents: data leakage, unauthorized access

---

## Security Domains (1-17)

### 1. Identity & Access Control

**Principles:**
- No shared accounts (every person has unique identity)
- No root accounts (distribution of privilege)
- Least privilege (each user/service has minimum required access)
- Multi-factor authentication (MFA) for human users
- Short-lived tokens with rotation

**Implementation:**
- Authentication: OAuth2/OIDC for users, JWT for services
- Authorization: Role-Based Access Control (RBAC) with granular permissions
- MFA: Required for all human users, optional/enforced for high-privilege operations
- Token lifetime: < 1 hour for frontend, < 15 min for API operations
- Token rotation: Automatic before expiry

**Related Documents:**
- SEC-01: Security & Authentication (detailed patterns and code examples)

---

### 2. Application Security (OWASP)

**Mandatory Controls:**
- **Input validation**: All user inputs validated against whitelist (not blacklist)
- **Output encoding**: HTML encoding, JavaScript encoding to prevent XSS
- **CSRF protection**: Same-site cookies, CSRF tokens for state-changing operations
- **XSS protection**: Content Security Policy (CSP) headers, no inline scripts
- **Injection protection**: Parameterized queries, no SQL string concatenation
- **Authentication bypass**: No weak password reset, no session fixation
- **Broken access control**: Every endpoint validates user has permission
- **Security misconfiguration**: Infrastructure as code, immutable configuration
- **Sensitive data exposure**: Encryption in transit (TLS), encryption at rest
- **Insufficient logging**: Centralized logging with proper security events

**Rate Limiting & Abuse Detection:**
- API rate limits per user/IP (prevent brute force, DoS)
- Account lockout after failed login attempts
- Suspicious activity detection (impossible travel, unusual locations)
- Kill switch: Feature flag to disable feature/tenant if under attack

**State Machine Validation:**
- Business workflows modeled as state machines
- Only valid state transitions allowed
- Example: Order cannot go from "cancelled" back to "pending"

---

### 3. Multi-Tenant Security

**Principles:**
- Tenant context is **injected by system**, never derived from user request
- Database enforces tenant isolation via constraints
- Cross-tenant queries default to forbidden

**Implementation:**
- Tenant ID in authentication token (JWT claim)
- Request middleware extracts and validates tenant ID
- All queries filtered by tenant ID (database constraint)
- No cross-tenant JOINs unless explicitly allowed and audited
- Superadmin = person, not role (explicit access logging required)

**Example (Wrong):**
```sql
-- WRONG: User could pass ?tenant_id=999 to access other tenant
SELECT * FROM guests WHERE tenant_id = ?tenant_id;
```

**Example (Correct):**
```sql
-- CORRECT: Tenant ID from auth token, immutable
const tenantId = req.user.tenant_id;  // From JWT
const guests = await db.query(
  'SELECT * FROM guests WHERE tenant_id = $1',
  [tenantId]
);
```

**Related Documents:**
- ARCH-05: Frontend Architecture (tenant picker, context management)
- ARCH-06: Repository Governance (multi-repository per business capability)

---

### 4. Event & Async Security

**Principles:**
- Events are contracts between services
- Event messages can be replayed or arrive out-of-order
- Each consumer must be idempotent

**Implementation:**
- **Schema versioning**: Events include version, consumers handle multiple versions
- **HMAC signatures**: Events are signed by publisher, verified by consumers
- **Idempotency**: Consumers use idempotency key (event ID + consumer ID) to prevent double-processing
- **Dead-letter queue**: Failed events sent to DLQ for manual review
- **Replay protection**: Timestamp and sequence checks prevent old events from being replayed

**Example Event Contract:**
```json
{
  "id": "evt-uuid-12345",
  "version": 1,
  "type": "payment.charged",
  "timestamp": "2025-12-21T10:30:00Z",
  "tenant_id": "org-123",
  "data": {
    "amount": 100,
    "currency": "USD",
    "order_id": "ord-456"
  },
  "signature": "hmac-sha256-hash"
}
```

**Consumer Implementation:**
```typescript
async function handlePaymentCharged(event: PaymentChargedEvent) {
  // Check idempotency
  const exists = await db.query(
    'SELECT id FROM processed_events WHERE event_id = $1 AND consumer = $2',
    [event.id, 'billing-service']
  );
  if (exists) return;  // Already processed

  // Verify signature
  const valid = verifyHMAC(event, event.signature);
  if (!valid) throw new Error('Invalid signature');

  // Process event (version-aware)
  if (event.version === 1) {
    await chargeGuest(event.data.amount, event.data.order_id);
  }

  // Mark as processed
  await db.query(
    'INSERT INTO processed_events (event_id, consumer) VALUES ($1, $2)',
    [event.id, 'billing-service']
  );
}
```

**Related Documents:**
- STD-03: Registries & Events (event schema and publishing patterns)
- STD-04: Real-time, Jobs, Search (event delivery and ordering)

---

### 5. Data & Financial Security

**Encryption:**
- **In transit**: TLS 1.3 for all network communication (HTTP/2 enforced HTTPS)
- **At rest**: Database encryption at storage layer (Neon default)
- **Field-level**: Sensitive fields (KTP, credit card, PII) encrypted with AES-256-GCM

**Immutability & Audit:**
- Accounting/ledger entries: append-only, never updated/deleted
- Audit trail: capture WHO, WHAT, WHEN for sensitive operations
- Append-only audit table with database trigger preventing modification

**Period Lock:**
- Once a period (month/quarter) is closed, no changes allowed
- Forces corrections to be in new period only
- Prevents: retroactive manipulation of financial records

**Dual Approval:**
- Sensitive operations require two approvals (e.g., large refund, contract change)
- Different users perform initiation and approval
- Audit log captures both approvers

**Example (Refund with Dual Approval):**
```
1. Admin A initiates refund of $500
   → Status: "pending_approval"
   → Audit log: "refund initiated by admin_a"

2. Admin B reviews and approves
   → Status: "approved"
   → Audit log: "refund approved by admin_b"

3. System executes refund
   → Status: "completed"
   → Immutable ledger entry created
   → Cannot be undone, only reversed with new entry
```

**Related Documents:**
- SEC-02: Data Protection & Privacy (field-level encryption, GDPR compliance)

---

### 6. Cloud & Infrastructure Security

**Network:**
- **Default deny**: Firewall/security groups block all by default
- **Database**: Non-public (private VPC, no internet access)
- **Internal services**: Private network only, no direct internet access
- **API Gateway**: Public endpoint, all other services private

**Identity & Access (IAM):**
- Least privilege: Each service/person has minimum required permissions
- No shared credentials: Service-to-service uses short-lived signed tokens
- No "poweruser" role: Deny by default, explicit permission required

**Infrastructure as Code:**
- All infrastructure (networks, firewalls, databases) defined in code
- Changes reviewed before deployment
- Drift detection: alerts if manual changes made to production
- Immutable deployments: infrastructure not modified in-place

**Monitoring & Logging:**
- All resource access logged (who accessed what, when)
- Failed access attempts logged and alerted
- Regular access reviews (quarterly) to remove unused permissions

---

### 7. Secrets Management

**Principles:**
- Secrets stored in dedicated secret manager (not environment variables)
- Rotation policy: automatic rotation every 30-90 days
- Scoped access: service only gets secrets it needs

**Implementation:**
- Secret manager: HashiCorp Vault or cloud provider equivalent (AWS Secrets Manager, GCP Secret Manager)
- No secrets in code repositories (prevent git history leakage)
- No secrets in environment files (`.env` files are local dev only, never committed)
- No secrets in logs or error messages
- Application reads secrets from manager at startup

**Example (Wrong):**
```bash
# WRONG: Secret in environment file
export DATABASE_PASSWORD=super_secret_123
```

**Example (Correct):**
```typescript
// CORRECT: Read from secret manager at startup
import { SecretsManager } from 'aws-sdk';

const secretsManager = new SecretsManager();
const dbPassword = await secretsManager.getSecretValue({
  SecretId: 'prod/database/password'
});
```

**Rotation Policy:**
- Database passwords: 30-day rotation
- API keys: 60-day rotation
- Encryption keys: 90-day rotation
- Manual rotation forced if compromise suspected

---

### 8. Observability & Detection

**Centralized Logging:**
- All application logs sent to centralized system (Elastic, Datadog, Splunk, etc.)
- Structured JSON logging with consistent schema
- Sensitive data stripped before logging

**Append-Only Audit Log:**
- Separate, immutable audit log for sensitive operations
- Triggers prevent modification/deletion
- Retention policy: minimum 7 years for financial data

**Metrics & Tracing:**
- Application metrics: request rate, error rate, latency percentiles
- Distributed tracing: trace_id linking requests across services
- Error tracing: stack traces with context (user, tenant, operation)

**Anomaly Detection & Alerting:**
- Baseline behavior learned (normal request patterns)
- Alerts on deviations:
  - Impossible travel (user in NYC then Tokyo in 5 minutes)
  - Unusual data access (admin accessing data not normally used)
  - Spike in errors (potential attack or outage)
  - Failed authentication spikes (brute force attempt)

**Example Alert:**
```
Alert: "High rate of failed logins from IP 192.168.1.100"
  → Trigger: > 10 failed attempts in 1 minute
  → Action: Send to security team, auto-block IP for 1 hour
  → Escalate: If from cloud provider IP, investigate immediately
```

**Related Documents:**
- STD-17: Logging & Observability Standard (detailed logging schema and implementation)

---

### 9. CI/CD & Supply Chain Security

**Dependency Management:**
- Dependency scanning: automated checks for known vulnerabilities (npm audit, Snyk, etc.)
- Pinned dependencies: versions fixed, not floating (prevents surprise updates)
- Regular updates: scheduled updates reviewed and tested

**Build Security:**
- SAST (Static Application Security Testing): code analysis for vulnerabilities
- Secret scanning: automated scanning for leaked credentials
- Container scanning: image vulnerability scanning before deployment
- Signed artifacts: build artifacts signed, signature verified before deployment

**Deployment:**
- Immutable build artifacts: artifact built once, never modified
- Verified container images: only official, verified minimal images used
- Infrastructure as code: all deployments from code, reviewed before execution
- Separate environments: dev, staging, production with different secrets/configs

**Example Vulnerability Scanning:**
```bash
# Scan dependencies
npm audit

# SAST scan
sonarqube scan

# Secret scanning
git-secrets scan

# Container scanning
trivy image myapp:latest

# All must pass before deployment
```

**Related Documents:**
- STD-18: Release & Update Management (immutable artifacts, manifest)

---

### 10. Abuse, Failure & Recovery

**Idempotency:**
- Critical operations protected with idempotency keys
- Duplicate requests = same result, no side effects
- Example: Payment with idempotency key prevents double-charge if request retried

**Rate Limiting:**
- Per-user rate limits (prevent brute force, excessive API usage)
- Per-IP rate limits (prevent botnet attacks)
- Soft limits: warning when approaching threshold
- Hard limits: rejection when exceeded
- Different limits for different operations (login: strict, read: lenient)

**Kill Switch:**
- Feature flags allow instant disabling of features
- Per-tenant kill switch (disable feature for one customer without affecting others)
- Global kill switch (disable feature entirely)
- No code deployment needed

**Backup & Restore:**
- Regular backups (daily or more frequent)
- Restore testing: regularly restore from backups to verify integrity
- Selective restore: ability to restore specific tenant's data to point-in-time
- Retention policy: backups kept for minimum 30 days

**Example Kill Switch:**
```typescript
if (features.isEnabled('new-payment-method')) {
  // Use new payment processor
  return newPaymentProcessor.process(payment);
} else {
  // Fall back to old processor
  return legacyPaymentProcessor.process(payment);
}

// If new processor has bug:
// 1. Set feature flag to false
// 2. All new requests use old processor
// 3. No code deployment, no downtime
// 4. Fix bug, redeploy, re-enable
```

**Related Documents:**
- STD-08: Backup, Webhook & Reports (backup and restore procedures)
- ARCH-07: Design Patterns (feature flags, optimistic UI)

---

### 11. Configuration & Change Management

**Immutable Configuration:**
- Configuration not modifiable in running system
- Changes via code commit and CI/CD pipeline
- Prevents accidental misconfigurations

**Environment Separation:**
- Development: relaxed settings, debug mode enabled
- Staging: production-like, full validation
- Production: strict settings, no debug, monitoring enabled
- Different secrets and databases for each environment

**Configuration Audit:**
- All configuration changes tracked in git
- Code review before configuration change
- Audit log showing who changed what, when
- Rollback capability: previous configuration versions available

**Feature Flags as Configuration:**
- Feature flags allow configuration changes without code deployment
- Centralized flag management (not scattered in code)
- Version controlled for audit trail

---

### 12. Human & Process Security

**Access Control:**
- No shared accounts: every person unique identity
- No "urgent bypass": security controls apply even under pressure
- Access review: quarterly review of who has access to what

**Onboarding Checklist:**
- New team member gets minimum required permissions
- Temporary elevated access requires explicit time limit and reason
- Permissions documented for later review

**Offboarding Checklist:**
- All access revoked immediately upon departure
- API keys rotated
- Data exports retained for audit (in case of legal dispute)
- Exit interview: confirm no data copied, no credentials retained

**Example Offboarding:**
```
Day 1: Employee notifies departure
  ❌ Revoke all system access
  ❌ Rotate service accounts used by employee
  ❌ Export employee-created data (for audit)
  ❌ Review laptop/phone for sensitive data

Day 2: Remove from all repositories and infrastructure
  ❌ Git repository access removed
  ❌ Cloud IAM roles removed
  ❌ VPN/ssh keys disabled

Day 30: Confirm no access remains
  ❌ Check cloud audit logs for employee access
  ❌ Confirm no active sessions
  ❌ Final review of employee-owned resources
```

---

### 13. AI Usage Rules

**Policy:**
- All AI-generated code requires human review before merge
- AI assistance permitted for low-risk tasks (documentation, tests, boilerplate)
- AI cannot make security decisions independently

**Security Contract for AI:**
- All prompts to AI include relevant security contract/requirements
- AI output is not final—static analysis must validate
- AI output violating invariants is rejected immediately

**Restrictions:**
- AI never has production access
- AI never has access to secrets or credentials
- AI never has access to customer data
- AI prompts never include sensitive information

**Example AI-Safe Prompt:**
```
"Write a React component for user profile page.
Follow this Security Contract:
- DO NOT make API calls (let parent component handle)
- DO NOT store auth tokens (pass as prop)
- DO NOT use direct innerHTML (use React safely)
- DO validate all props are defined before use"
```

**Example AI-Unsafe Prompt:**
```
// WRONG: Includes secrets
"Write code using API key xyz123abc to fetch user data"

// WRONG: Makes security decision
"Add a feature to let users upload files without validation"

// WRONG: Accesses production
"Modify the production database directly"
```

---

### 14. Mental Model (The Core Philosophy)

Security in PROJECT_BESAR is not:
- ❌ A checklist ("did we do all 17 items?")
- ❌ A feature ("add security module")
- ❌ Trust-based ("our developers are careful")

Security is:
- ✅ **Enforced discipline built into architecture**
- ✅ **Assume humans make mistakes—systems prevent them**
- ✅ **Defense in depth—no single point of failure**
- ✅ **Continuous—detection, response, recovery**

**Core Insight:**
```
"If it requires manual discipline to be secure, it will eventually fail.
 If security requires human decision-making, someone will decide wrong.
 If you can click it manually, you can do it wrong.
 If the system doesn't enforce it, it will be violated."
```

**Corollary:**
- Rate limiting is automatic, not "developers should limit requests"
- Secrets in manager is required, not "developers should not commit secrets"
- Audit logs are immutable (database triggers), not "don't modify audit logs"
- Tenant isolation is database-enforced, not "remember to filter by tenant_id"

---

## Security Architecture Layers

### Layer 1: Identity & Authentication
- User proves identity (username/password, OAuth2, SSO)
- System issues short-lived token (JWT, session cookie)
- Token contains claims (user_id, tenant_id, roles)

### Layer 2: Authorization
- Every request authenticated (token validated)
- Every endpoint authorized (user has permission for operation)
- Every database query filtered by tenant_id

### Layer 3: Data Protection
- Secrets encrypted and managed
- PII encrypted at field level
- Ledger entries append-only and immutable
- Audit trail captures all sensitive access

### Layer 4: Infrastructure
- Network: default deny, explicit allow
- Secrets: manager, rotation, scoped access
- Monitoring: centralized logs, anomaly detection
- Incident response: kill switches, rollback capability

### Layer 5: Supply Chain
- Code: SAST, secret scanning, code review
- Dependencies: scanning, pinned versions
- Build: signed, verified artifacts
- Deployment: infrastructure as code, environment separation

---

## Compliance Checklist

Use this checklist to verify security architecture compliance:

**Core Principles**
- [ ] Assume breach: system can detect compromise within 24 hours
- [ ] Defense in depth: ≥3 independent security layers for crown jewels
- [ ] Default deny: explicit permission required for all access
- [ ] Detect-respond-recover: automated alerts, kill switches, backup/restore tested

**Crown Jewels**
- [ ] Identity: MFA enabled, short-lived tokens, no shared accounts
- [ ] Tenant: tenant_id injected by system, database constraints enforce isolation
- [ ] Ledger: append-only, immutable, dual approval for changes
- [ ] Secrets: managed (not in code), rotated, scoped access

**Identity & Access (Domain 1)**
- [ ] No root accounts or shared credentials
- [ ] MFA required for all human users
- [ ] Tokens expire (< 1 hour frontend, < 15 min API)
- [ ] Least privilege: each user has minimum required access
- [ ] Regular access reviews (quarterly)

**Application Security (Domain 2)**
- [ ] Input validation on all user input (whitelist, not blacklist)
- [ ] Output encoding (HTML, JavaScript, URL context)
- [ ] CSRF protection (tokens, same-site cookies)
- [ ] XSS prevention (CSP, no inline scripts)
- [ ] SQL injection prevention (parameterized queries)
- [ ] Rate limiting (per-user, per-IP)
- [ ] State machines for business workflows

**Multi-Tenant (Domain 3)**
- [ ] Tenant context injected from auth token, not request
- [ ] All queries filtered by tenant_id
- [ ] Database constraints enforce tenant isolation
- [ ] No cross-tenant queries by default
- [ ] Superadmin access logged and audited

**Events & Async (Domain 4)**
- [ ] Event schema versioned
- [ ] Events signed (HMAC)
- [ ] Consumers idempotent (idempotency keys)
- [ ] Dead-letter queue for failed events
- [ ] Replay protection (timestamp checks)

**Data & Financial (Domain 5)**
- [ ] TLS 1.3 for all network communication
- [ ] Encryption at rest (database level)
- [ ] Field-level encryption for PII/finance
- [ ] Ledger append-only with audit trail
- [ ] Period lock prevents retroactive changes
- [ ] Dual approval for sensitive operations

**Cloud & Infrastructure (Domain 6)**
- [ ] Firewall: default deny, explicit allow rules
- [ ] Databases: non-public, private VPC only
- [ ] IAM: least privilege, no shared credentials
- [ ] Infrastructure as code, version controlled
- [ ] Immutable deployments (no in-place modifications)

**Secrets (Domain 7)**
- [ ] Secrets in manager, not environment files
- [ ] Rotation policy (30-90 days)
- [ ] Scoped access (service only gets needed secrets)
- [ ] No secrets in logs, code, or frontend
- [ ] Secrets never in git history

**Observability (Domain 8)**
- [ ] Centralized logging for all applications
- [ ] Structured JSON logs with consistent schema
- [ ] Append-only audit log for sensitive operations
- [ ] Metrics and distributed tracing enabled
- [ ] Anomaly detection and alerting configured

**CI/CD & Supply Chain (Domain 9)**
- [ ] Dependency scanning enabled (SAST)
- [ ] Secret scanning before deployment
- [ ] Pinned dependencies (not floating versions)
- [ ] Container image scanning
- [ ] Build artifacts signed and immutable

**Abuse, Failure, Recovery (Domain 10)**
- [ ] Idempotency keys for critical operations
- [ ] Rate limiting (soft and hard limits)
- [ ] Feature flags for instant rollback
- [ ] Kill switch per-tenant and global
- [ ] Backup/restore tested regularly

**Configuration (Domain 11)**
- [ ] All configuration in code, immutable at runtime
- [ ] Environment separation (dev/staging/prod)
- [ ] Configuration audit trail (git history)
- [ ] Feature flags managed centrally

**Human & Process (Domain 12)**
- [ ] No shared accounts
- [ ] No "urgent bypass" of security controls
- [ ] Onboarding checklist for access provisioning
- [ ] Offboarding checklist for access revocation
- [ ] Quarterly access reviews

**AI Usage (Domain 13)**
- [ ] All AI prompts include Security Contract
- [ ] AI output validated by static analysis
- [ ] AI never has prod/secrets access
- [ ] Code review required for AI-generated security code
- [ ] AI output violating invariants rejected

---

## Cross-References

- **SEC-01**: Security & Authentication — identity patterns, OAuth2, JWT implementation
- **SEC-02**: Data Protection & Privacy — encryption, GDPR compliance, audit trails
- **STD-08**: Backup & Restore — backup procedures, selective restore, testing
- **STD-17**: Logging & Observability — structured logging, centralized logs, metrics
- **STD-18**: Release & Update Management — supply chain security, artifact signing
- **ARCH-05**: Frontend Architecture — authentication flow, token management, permission masking
- **ARCH-06**: Repository Governance — access control by role, multi-repository architecture
- **ARCH-07**: Design Patterns — idempotency, feature flags, error handling

---

## Final Principle

> **"Security is discipline enforced by systems, not trust in people."**
>
> If it can be clicked manually, it can be done wrong.
> If it's not enforced by the system, it will eventually be violated.
> If humans must remember to be secure, they will fail.
>
> **Design systems where the secure path is the only easy path.**
