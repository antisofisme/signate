# MANTRA-L1-AI-CLASSIFICATION-GUIDE-001

## AI Classification Guide for ATLAS_MANTRA

**Document ID**: MANTRA-L1-AI-CLASSIFICATION-GUIDE-001
**Version**: 1.0.0
**Status**: ACTIVE
**Parent Document**: MANTRA-L1-AI-OPERATIONAL-GUIDELINES-001

---

## 1. Overview

This document provides detailed guidance for AI assistants on classifying human input into the ATLAS_MANTRA 4x4 decision taxonomy. Accurate classification is essential for proper evaluation, comparison, and suggestion generation.

---

## 2. The 4x4 Taxonomy

### 2.1 Group Overview

| Group | Name | Focus | Question Pattern |
|-------|------|-------|------------------|
| **GROUP-1** | Intent & Purpose | WHY we do things | "What are we trying to achieve?" |
| **GROUP-2** | Architecture & Structure | HOW we build things | "How do we structure it?" |
| **GROUP-3** | Control & Governance | WHAT rules apply | "What is allowed/forbidden?" |
| **GROUP-4** | Evolution & Change | HOW things change | "How does it evolve?" |

### 2.2 Feature Overview

```
GROUP-1: Intent & Purpose (WHY)
├── F-01: Vision & Outcome       → Long-term goals, success criteria
├── F-02: Problem Statement      → Pain points, challenges to solve
├── F-03: Scope & Non-Goals      → What's in/out of scope
└── F-04: Principles & Values    → Guiding principles, trade-offs

GROUP-2: Architecture & Structure (HOW)
├── F-05: Domain Boundary        → Bounded contexts, aggregates
├── F-06: Service Boundary       → Modules, microservices, components
├── F-07: Data Ownership         → Database, schema, storage
└── F-08: Integration Contract   → APIs, protocols, interfaces

GROUP-3: Control & Governance (WHAT RULES)
├── F-09: Policy                 → Business rules, operational policies
├── F-10: Authority              → Approval chains, permissions
├── F-11: Security & Compliance  → Encryption, authentication, regulations
└── F-12: Risk & Resilience      → Failure handling, disaster recovery

GROUP-4: Evolution & Change (HOW IT CHANGES)
├── F-13: Decision Lifecycle     → How decisions evolve, versioning
├── F-14: Rollback & Exit        → Undo strategies, migration plans
├── F-15: Promotion & Gates      → Environment promotion, release gates
└── F-16: Consistency & Anti-Drift → Alignment, synchronization
```

---

## 3. Classification Decision Tree

### 3.1 Primary Classification (Group Selection)

```
                           Human Input
                               │
                               ▼
              ┌────────────────┴────────────────┐
              │   What question does it answer? │
              └────────────────┬────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
    "WHY/WHAT                "HOW/WHERE            "CAN/MUST
    should we?"              do we?"               (NOT)?"
         │                     │                     │
         ▼                     ▼                     ▼
    ┌─────────┐           ┌─────────┐          ┌─────────┐
    │ GROUP-1 │           │ GROUP-2 │          │ GROUP-3 │
    │ Intent  │           │ Arch    │          │ Control │
    └─────────┘           └─────────┘          └─────────┘
                               │
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
               "CHANGE/                "RULE/
               EVOLVE?"                POLICY?"
                    │                     │
                    ▼                     │
               ┌─────────┐                │
               │ GROUP-4 │                │
               │ Evolve  │                │
               └─────────┘                │
                                          │
                                 (Already GROUP-3)
```

### 3.2 Secondary Classification (Feature Selection)

After determining the Group, use these feature-specific criteria:

#### GROUP-1 Features

| Feature | Key Indicator | Example Phrases |
|---------|---------------|-----------------|
| F-01 | Future state, success | "Our goal is...", "We want to achieve...", "By 2025, we will..." |
| F-02 | Pain points, challenges | "The problem is...", "We need to solve...", "Users struggle with..." |
| F-03 | Boundaries | "We will focus on...", "Out of scope is...", "We won't do..." |
| F-04 | Trade-offs, values | "We prioritize X over Y", "Our principle is...", "We value..." |

#### GROUP-2 Features

| Feature | Key Indicator | Example Phrases |
|---------|---------------|-----------------|
| F-05 | Concept boundaries | "This domain includes...", "Order aggregate owns...", "Bounded by..." |
| F-06 | System components | "The service handles...", "Module X is responsible for...", "Component Y..." |
| F-07 | Data location | "Data is stored in...", "Schema belongs to...", "Database X owns..." |
| F-08 | Communication | "API contract is...", "Integration via...", "Protocol for..." |

#### GROUP-3 Features

| Feature | Key Indicator | Example Phrases |
|---------|---------------|-----------------|
| F-09 | Rules, must/should | "Policy is...", "Rule states...", "Must always...", "Should never..." |
| F-10 | Approval, permission | "Approval required from...", "Only X can...", "Authority to..." |
| F-11 | Security, compliance | "Must encrypt...", "GDPR requires...", "Authentication using..." |
| F-12 | Failure, recovery | "If failure occurs...", "Fallback is...", "Risk of...", "Recovery plan..." |

#### GROUP-4 Features

| Feature | Key Indicator | Example Phrases |
|---------|---------------|-----------------|
| F-13 | Versioning, evolution | "Version X will...", "Evolves to...", "Supersedes..." |
| F-14 | Undo, exit | "Can rollback by...", "Exit strategy is...", "Revert using..." |
| F-15 | Environments, gates | "Promote to prod when...", "Gate criteria...", "Staging requires..." |
| F-16 | Alignment, sync | "Must stay consistent with...", "Prevent drift by...", "Align with..." |

---

## 4. Classification Examples

### 4.1 GROUP-1 (Intent) Examples

#### F-01: Vision & Outcome

```
Human Input: "Kami mau fokus ke pasar enterprise untuk meningkatkan revenue"

Classification: GROUP-1 / F-01
Reasoning:
- Talks about long-term goal (focus on enterprise)
- Mentions outcome (increase revenue)
- Future-oriented statement

Draft:
{
  "group_id": "GROUP-1",
  "feature_id": "F-01",
  "statement": "Focus on enterprise market to increase revenue",
  "rationale": "[HUMAN TO COMPLETE: Why enterprise? What revenue target?]"
}
```

#### F-02: Problem Statement

```
Human Input: "User churn rate tinggi karena onboarding kompleks"

Classification: GROUP-1 / F-02
Reasoning:
- Identifies a problem (high churn rate)
- Specifies cause (complex onboarding)
- Describes pain point

Draft:
{
  "group_id": "GROUP-1",
  "feature_id": "F-02",
  "statement": "User churn is high due to complex onboarding process",
  "rationale": "[HUMAN TO COMPLETE: What is current churn rate? Target?]"
}
```

#### F-03: Scope & Non-Goals

```
Human Input: "Kita fokus B2B saja, B2C out of scope"

Classification: GROUP-1 / F-03
Reasoning:
- Explicit boundary definition (B2B in, B2C out)
- Scope statement
- Non-goal clearly stated

Draft:
{
  "group_id": "GROUP-1",
  "feature_id": "F-03",
  "statement": "B2B is in scope; B2C is explicitly out of scope",
  "rationale": "[HUMAN TO COMPLETE: Why exclude B2C?]"
}
```

#### F-04: Principles & Values

```
Human Input: "Kita utamakan user experience daripada feature completeness"

Classification: GROUP-1 / F-04
Reasoning:
- Trade-off statement (UX over features)
- Value prioritization
- Guiding principle

Draft:
{
  "group_id": "GROUP-1",
  "feature_id": "F-04",
  "statement": "User experience is prioritized over feature completeness",
  "rationale": "[HUMAN TO COMPLETE: When did this trade-off become necessary?]"
}
```

### 4.2 GROUP-2 (Architecture) Examples

#### F-05: Domain Boundary

```
Human Input: "Order domain meliputi cart, checkout, dan payment"

Classification: GROUP-2 / F-05
Reasoning:
- Defines domain boundary (Order)
- Lists included concepts (cart, checkout, payment)
- Bounded context definition

Draft:
{
  "group_id": "GROUP-2",
  "feature_id": "F-05",
  "statement": "Order domain encompasses cart, checkout, and payment concepts",
  "rationale": "[HUMAN TO COMPLETE: Why are these grouped together?]"
}
```

#### F-06: Service Boundary

```
Human Input: "Payment service terpisah dari Order service"

Classification: GROUP-2 / F-06
Reasoning:
- Service separation decision
- Component boundary
- Microservice architecture

Draft:
{
  "group_id": "GROUP-2",
  "feature_id": "F-06",
  "statement": "Payment service is separated from Order service",
  "rationale": "[HUMAN TO COMPLETE: Scalability? Security? Team ownership?]"
}
```

#### F-07: Data Ownership

```
Human Input: "Customer data dimiliki oleh CRM service, bukan Order"

Classification: GROUP-2 / F-07
Reasoning:
- Data ownership assignment
- Clear owner specification
- Data domain boundary

Draft:
{
  "group_id": "GROUP-2",
  "feature_id": "F-07",
  "statement": "Customer data is owned by CRM service, not Order service",
  "rationale": "[HUMAN TO COMPLETE: How do other services access customer data?]"
}
```

#### F-08: Integration Contract

```
Human Input: "API response harus JSON dengan format standar"

Classification: GROUP-2 / F-08
Reasoning:
- API contract specification
- Format standardization
- Integration protocol

Draft:
{
  "group_id": "GROUP-2",
  "feature_id": "F-08",
  "statement": "API responses must be JSON following standard format",
  "constraints": [
    {"type": "REQUIREMENT", "statement": "Response must include status, data, and error fields"}
  ]
}
```

### 4.3 GROUP-3 (Control) Examples

#### F-09: Policy

```
Human Input: "Refund hanya bisa dilakukan dalam 30 hari"

Classification: GROUP-3 / F-09
Reasoning:
- Business rule/policy
- Time constraint
- Operational rule

Draft:
{
  "group_id": "GROUP-3",
  "feature_id": "F-09",
  "statement": "Refunds can only be processed within 30 days of purchase",
  "constraints": [
    {"type": "LIMITATION", "statement": "30-day window from purchase date"}
  ]
}
```

#### F-10: Authority

```
Human Input: "Expense di atas $1000 harus approval manager"

Classification: GROUP-3 / F-10
Reasoning:
- Approval chain specification
- Authority threshold
- Permission requirement

Draft:
{
  "group_id": "GROUP-3",
  "feature_id": "F-10",
  "statement": "Expenses exceeding $1000 require manager approval",
  "constraints": [
    {"type": "REQUIREMENT", "statement": "Manager must approve within 48 hours"}
  ]
}
```

#### F-11: Security & Compliance

```
Human Input: "Semua PII harus dienkripsi"

Classification: GROUP-3 / F-11
Reasoning:
- Security requirement
- Data protection
- Compliance-related

Draft:
{
  "group_id": "GROUP-3",
  "feature_id": "F-11",
  "statement": "All Personally Identifiable Information (PII) must be encrypted",
  "constraints": [
    {"type": "REQUIREMENT", "statement": "AES-256 for at-rest encryption"},
    {"type": "REQUIREMENT", "statement": "TLS 1.3 for in-transit encryption"}
  ],
  "blast_radius": "CRITICAL"
}
```

#### F-12: Risk & Resilience

```
Human Input: "Kalau payment gateway down, pakai fallback provider"

Classification: GROUP-3 / F-12
Reasoning:
- Failure scenario handling
- Fallback strategy
- Resilience planning

Draft:
{
  "group_id": "GROUP-3",
  "feature_id": "F-12",
  "statement": "When primary payment gateway is down, use fallback provider",
  "invariants": [
    "Payment processing must remain available 99.9% of the time"
  ]
}
```

### 4.4 GROUP-4 (Evolution) Examples

#### F-13: Decision Lifecycle

```
Human Input: "Keputusan ini menggantikan policy lama tentang pricing"

Classification: GROUP-4 / F-13
Reasoning:
- Decision replacement/evolution
- Supersedes relationship
- Version management

Draft:
{
  "group_id": "GROUP-4",
  "feature_id": "F-13",
  "statement": "This decision supersedes the previous pricing policy",
  "supersedes": "[OLD_DECISION_ID]",
  "version": "2.0.0"
}
```

#### F-14: Rollback & Exit

```
Human Input: "Kalau migrasi gagal, kita bisa rollback ke v1"

Classification: GROUP-4 / F-14
Reasoning:
- Rollback strategy
- Exit plan
- Migration safety

Draft:
{
  "group_id": "GROUP-4",
  "feature_id": "F-14",
  "statement": "If migration fails, system can rollback to v1",
  "constraints": [
    {"type": "REQUIREMENT", "statement": "Rollback must complete within 30 minutes"},
    {"type": "REQUIREMENT", "statement": "No data loss during rollback"}
  ]
}
```

#### F-15: Promotion & Gates

```
Human Input: "Deploy ke prod butuh approval dari QA dan Security"

Classification: GROUP-4 / F-15
Reasoning:
- Promotion criteria
- Gate requirements
- Release process

Draft:
{
  "group_id": "GROUP-4",
  "feature_id": "F-15",
  "statement": "Production deployment requires approval from QA and Security teams",
  "constraints": [
    {"type": "REQUIREMENT", "statement": "QA sign-off on test results"},
    {"type": "REQUIREMENT", "statement": "Security scan must pass with no critical findings"}
  ]
}
```

#### F-16: Consistency & Anti-Drift

```
Human Input: "Semua service harus pakai config yang sama dari central repo"

Classification: GROUP-4 / F-16
Reasoning:
- Consistency requirement
- Anti-drift measure
- Centralized control

Draft:
{
  "group_id": "GROUP-4",
  "feature_id": "F-16",
  "statement": "All services must use configuration from central repository",
  "invariants": [
    "Configuration drift between services is prevented",
    "Changes propagate to all services within 5 minutes"
  ]
}
```

---

## 5. Ambiguous Cases

### 5.1 Multi-Classification Scenarios

Some inputs could fit multiple classifications. Handle as follows:

#### Scenario: "Semua API harus menggunakan OAuth2"

Could be:
- **GROUP-2 / F-08** (Integration Contract) - API standard
- **GROUP-3 / F-11** (Security) - Authentication requirement

**Resolution**: Ask for clarification:
```
AI: This statement could be classified as:

A) Integration Contract (GROUP-2 / F-08)
   → Focuses on API standardization
   → Other services must implement OAuth2 client

B) Security Policy (GROUP-3 / F-11)
   → Focuses on authentication requirement
   → Security compliance mandate

Which aspect is more important for this decision?
```

#### Scenario: "We prioritize availability over consistency"

Could be:
- **GROUP-1 / F-04** (Principles) - Value statement
- **GROUP-3 / F-12** (Resilience) - Technical decision

**Resolution**: Consider context:
- If discussing organizational values → GROUP-1 / F-04
- If discussing specific system design → GROUP-3 / F-12

### 5.2 Compound Statements

When input contains multiple decisions, split them:

```
Human Input: "API harus JSON, dan semua endpoint harus authenticated"

Split into:
1. "API responses must be JSON" → GROUP-2 / F-08
2. "All endpoints must be authenticated" → GROUP-3 / F-11

AI Response:
"This statement contains two separate decisions. I recommend creating two entries:

Decision 1 (API Format):
- GROUP-2 / F-08 (Integration Contract)
- Statement: API responses must use JSON format

Decision 2 (Authentication):
- GROUP-3 / F-11 (Security)
- Statement: All API endpoints must require authentication

Should I prepare drafts for both?"
```

---

## 6. Input Normalization

### 6.1 Filler Word Removal

| Original | Normalized |
|----------|-----------|
| "Jadi sebenernya kita mau..." | "We want..." |
| "Kayaknya lebih baik kalau..." | "It's better if..." |
| "Menurut gue sih..." | "[Statement without hedging]" |
| "Mungkin kita bisa..." | "We should..." |

### 6.2 Statement Formatting

**Convert to declarative, active voice:**

| Original | Normalized |
|----------|-----------|
| "Shouldn't we encrypt data?" | "Data must be encrypted" |
| "It would be nice if..." | "The system should..." |
| "Maybe we should consider..." | "We decide to..." |
| "What if we..." | "We will..." |

### 6.3 Scope Inference

| Context Clues | Inferred Scope |
|---------------|----------------|
| "Semua...", "Seluruh perusahaan..." | ORGANIZATION |
| "Di tim X...", "Untuk domain Y..." | DOMAIN |
| "Service ini...", "Aplikasi A..." | APPLICATION |

---

## 7. Consistency Checklist

Before finalizing classification, verify:

```
☐ Group matches Feature (F-01 to F-04 → GROUP-1, etc.)
☐ Statement is declarative (not question or suggestion)
☐ Single decision per entry (compound statements split)
☐ Appropriate scope selected
☐ Blast radius matches impact level
☐ No ambiguity in classification
☐ Keywords align with feature description
```

---

## 8. Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────┐
│                 CLASSIFICATION QUICK REFERENCE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Question → Group                                                │
│  ─────────────────                                               │
│  WHY?    → GROUP-1 (Intent)                                     │
│  HOW?    → GROUP-2 (Architecture)                               │
│  RULES?  → GROUP-3 (Control)                                    │
│  CHANGE? → GROUP-4 (Evolution)                                  │
│                                                                  │
│  Keywords → Feature                                              │
│  ────────────────                                                │
│  goal, vision, outcome        → F-01                            │
│  problem, pain, challenge     → F-02                            │
│  scope, include, exclude      → F-03                            │
│  principle, value, trade-off  → F-04                            │
│  domain, context, aggregate   → F-05                            │
│  service, module, component   → F-06                            │
│  data, schema, storage        → F-07                            │
│  API, contract, integration   → F-08                            │
│  rule, policy, must/should    → F-09                            │
│  approval, authority, role    → F-10                            │
│  security, encrypt, comply    → F-11                            │
│  risk, failure, resilience    → F-12                            │
│  version, evolve, lifecycle   → F-13                            │
│  rollback, exit, revert       → F-14                            │
│  promote, gate, environment   → F-15                            │
│  consistency, drift, align    → F-16                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 9. References

- MANTRA-L1-AI-OPERATIONAL-GUIDELINES-001: Authority Boundaries
- MANTRA-L1-AI-WORKFLOW-SPECIFICATION-001: Complete Workflow
- MANTRA-SCHEMA-001: Decision Schema
- MANTRA-DEC-001: Group Definitions
- MANTRA-DEC-002: Feature Definitions

---

**Document Status**: ACTIVE
**Last Updated**: 2025-01-25
**Maintained By**: ATLAS_MANTRA Team
