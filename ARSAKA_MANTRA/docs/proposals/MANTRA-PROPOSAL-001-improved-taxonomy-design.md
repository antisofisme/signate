# MANTRA-PROPOSAL-001: Improved Decision Taxonomy Design

**Document Type**: PROPOSAL (for human review)
**Version**: 1.0.0
**Status**: DRAFT
**Created**: 2025-01-29
**Author**: Architecture Analysis

---

## Executive Summary

This document proposes an improved taxonomy for MANTRA that expands coverage from ~75% to 95%+ of real-world organizational decisions while maintaining the system's core principles of simplicity, memorability, and mutual exclusivity.

**Key Finding**: The current 4x4 taxonomy (16 cells) is well-designed for technical/architectural decisions but has systematic gaps for:
- **People & Organization** decisions (team structure, skills, hiring)
- **Resource & Economics** decisions (budget, cost, capacity)
- **Quality & Standards** decisions (metrics, SLAs, acceptance criteria)
- **Temporal & Scheduling** decisions (timing, deadlines, roadmap)

**Proposed Solution**: Expand to a **6x4 taxonomy (24 cells)** by adding two new domains while keeping the 4 universal aspects.

---

## 1. Gap Analysis of Current Taxonomy

### 1.1 Current Coverage (4 Domains x 4 Aspects)

```
Current Domains:
├── INT  (Intent & Direction)     → WHY / WHAT
├── ARCH (Architecture)           → HOW / WHERE
├── CTL  (Control & Policy)       → CAN / MUST NOT
└── EVO  (Evolution & Change)     → CHANGE SAFELY
```

### 1.2 Identified Gaps

| Gap Category | Example Decisions | Current Workaround | Problem |
|--------------|-------------------|-------------------|---------|
| **People/Team** | "Team X owns service Y" | F-05 (Domain) or F-10 (Authority) | Conflates ownership with structure |
| **Skills/Competency** | "We need 2 senior engineers for migration" | No fit | Forces artificial categorization |
| **Budget/Cost** | "Max $50K for infrastructure" | F-09 (Policy) or F-12 (Risk) | Cost is not policy, not risk |
| **Capacity/Resource** | "Production needs 16GB RAM minimum" | F-06 (Service) | Conflates capacity with architecture |
| **Quality Metrics** | "API latency must be < 200ms" | F-08 (Contract) or F-12 (Risk) | Quality is not just contract |
| **SLA/Targets** | "99.9% uptime required" | F-12 (Risk) | SLA is not risk assessment |
| **Timing/Schedule** | "Feature X launches Q3 2025" | F-01 (Vision) | Schedule is not vision |
| **Deadlines** | "Migration must complete by Dec 31" | No fit | Forces into wrong category |
| **Dependencies** | "Can't start B until A completes" | F-13 (Lifecycle) | Temporal dependency != lifecycle |
| **Sequence/Order** | "Always run tests before deploy" | F-15 (Promotion) | Partial fit only |

### 1.3 Coverage Estimation

**Current taxonomy coverage by decision type**:

| Decision Type | Estimated Volume | Current Coverage |
|---------------|------------------|------------------|
| Technical/Architectural | 30% | 95% |
| Process/Policy | 25% | 85% |
| People/Organization | 15% | 40% |
| Resource/Budget | 15% | 30% |
| Quality/Performance | 10% | 60% |
| Timing/Schedule | 5% | 20% |

**Weighted coverage**: ~72%

---

## 2. Design Options Evaluated

### Option A: Expand Aspects (4x5 = 20 cells)

Add a 5th aspect to each domain for "cross-cutting" concerns.

**Rejected**:
- Breaks the clean 4-aspect structure
- Aspects become domain-specific (complexity increases)
- Doesn't address the fundamental domain gaps

### Option B: Add Meta-Domain (5x4 = 20 cells)

Add a "META" domain for decisions about decisions.

**Rejected**:
- Meta-decisions are rare (< 2% of decisions)
- Can be handled via existing EVO domain (F-13 Lifecycle)
- Adds complexity without addressing main gaps

### Option C: Expand to 6 Domains (6x4 = 24 cells) - RECOMMENDED

Add two new domains:
- **RES** (Resources & Economics) - WHO/HOW MUCH
- **QTM** (Quality, Timing & Metrics) - HOW WELL/WHEN

**Advantages**:
- Addresses all identified gaps
- Maintains 4 universal aspects per domain
- Clear mutual exclusivity
- Memorable acronym: **I-A-C-E-R-Q** (Intent, Architecture, Control, Evolution, Resources, Quality)

### Option D: Restructure to 5x5 (25 cells)

Complete redesign with 5 domains and 5 aspects.

**Rejected**:
- Too disruptive for backward compatibility
- 25 cells exceeds cognitive limit
- Aspects become harder to remember

---

## 3. Recommended Taxonomy: 6 Domains x 4 Aspects

### 3.1 Complete Domain Structure

```
NEW TAXONOMY (6 Domains × 4 Aspects = 24 Decision Categories)

┌─────────────────────────────────────────────────────────────────────────────────┐
│                           INTENT & DIRECTION (INT)                               │
│                           Question: WHY? WHAT?                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│ A01: Vision & Outcome      │ Long-term goals, desired end state, success        │
│ A02: Problem Statement     │ Pain points, challenges, motivation for change     │
│ A03: Scope & Non-Goals     │ What's included/excluded, boundaries               │
│ A04: Principles & Values   │ Core beliefs, guiding philosophy, trade-offs       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ARCHITECTURE & BOUNDARIES (ARCH)                          │
│                          Question: HOW? WHERE?                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│ A05: Domain & Bounded Ctx  │ Business domains, DDD contexts, logical grouping   │
│ A06: Service & Module      │ Microservices, packages, component boundaries      │
│ A07: Data Ownership        │ Data location, sovereignty, GDPR considerations    │
│ A08: Integration Contract  │ APIs, protocols, inter-service communication       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                         CONTROL, POLICY & RISK (CTL)                             │
│                         Question: CAN? MUST NOT?                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│ A09: Policy & Rules        │ Governance rules, standards, conventions           │
│ A10: Approval & Authority  │ Who approves what, sign-off requirements           │
│ A11: Security & Compliance │ Authentication, encryption, audit, regulations     │
│ A12: Risk & Blast Radius   │ Impact assessment, failure modes, mitigation       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                          EXECUTION & EVOLUTION (EVO)                             │
│                        Question: HOW TO CHANGE SAFELY?                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│ A13: Decision Lifecycle    │ How decisions evolve, versioning strategy          │
│ A14: Reversibility & Exit  │ Rollback plans, migration paths, exit strategies   │
│ A15: Environment & Gates   │ Dev/staging/prod, deployment gates, promotion      │
│ A16: Anti-Drift            │ Preventing deviation, enforcement, consistency     │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                         RESOURCES & ECONOMICS (RES) *NEW*                        │
│                        Question: WHO? HOW MUCH?                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│ A17: Team & Ownership      │ Team structure, responsibilities, accountability   │
│ A18: Skills & Capacity     │ Competencies required, staffing needs, headcount   │
│ A19: Budget & Cost         │ Financial constraints, spending limits, ROI        │
│ A20: Infrastructure Quota  │ Hardware limits, cloud resources, capacity planning│
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────┐
│                      QUALITY, TIMING & METRICS (QTM) *NEW*                       │
│                       Question: HOW WELL? WHEN?                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│ A21: Performance Targets   │ Latency, throughput, response time requirements    │
│ A22: Quality Standards     │ Code quality, test coverage, acceptance criteria   │
│ A23: SLA & Availability    │ Uptime targets, reliability requirements           │
│ A24: Schedule & Milestones │ Deadlines, timelines, roadmap commitments          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Domain Summary Table

| Code | Domain Name | Question | Scope | New? |
|------|-------------|----------|-------|------|
| INT | Intent & Direction | WHY / WHAT | Purpose, goals, boundaries | No |
| ARCH | Architecture & Boundaries | HOW / WHERE | Structure, ownership, contracts | No |
| CTL | Control, Policy & Risk | CAN / MUST NOT | Rules, authority, security | No |
| EVO | Execution & Evolution | CHANGE SAFELY | Lifecycle, rollback, drift | No |
| **RES** | **Resources & Economics** | **WHO / HOW MUCH** | **People, budget, capacity** | **Yes** |
| **QTM** | **Quality, Timing & Metrics** | **HOW WELL / WHEN** | **Performance, SLA, schedule** | **Yes** |

### 3.3 Mnemonic for Memorability

**IACE-RQ** (pronounced "I Ace Our Queue")
- **I**ntent
- **A**rchitecture
- **C**ontrol
- **E**volution
- **R**esources
- **Q**uality

Or think of it as:
- **WHY** → INT (Intent)
- **HOW** → ARCH (Architecture)
- **WHAT RULES** → CTL (Control)
- **WHAT IF CHANGE** → EVO (Evolution)
- **WHO/HOW MUCH** → RES (Resources)
- **HOW WELL/WHEN** → QTM (Quality & Timing)

---

## 4. Aspect Definitions (Complete)

### 4.1 Universal Aspect Categories

All 6 domains share the same 4 aspect categories (questions), but the specific aspects differ:

| Aspect Position | Category | Question |
|-----------------|----------|----------|
| X1 | Strategic/Goal | What's the objective? |
| X2 | Operational/Current | What's the situation? |
| X3 | Boundary/Limits | What's the boundary? |
| X4 | Governance/Control | How is it maintained? |

### 4.2 Complete Aspect Definitions

#### INT (Intent) Aspects - A01 to A04

| ID | Name | Definition | Keywords |
|----|------|------------|----------|
| A01 | Vision & Outcome | Long-term goals, desired end state, success criteria | goal, vision, outcome, target, achieve |
| A02 | Problem Statement | Pain points, challenges, problems to solve | problem, issue, pain, challenge, struggle |
| A03 | Scope & Non-Goals | What's included/excluded, explicit boundaries | scope, include, exclude, out-of-scope, limit |
| A04 | Principles & Values | Guiding beliefs, trade-offs, non-negotiables | principle, value, prioritize, trade-off, belief |

#### ARCH (Architecture) Aspects - A05 to A08

| ID | Name | Definition | Keywords |
|----|------|------------|----------|
| A05 | Domain & Bounded Context | Business domain boundaries, DDD contexts | domain, context, aggregate, boundary, entity |
| A06 | Service & Module Boundary | Technical component structure, microservices | service, module, component, microservice, package |
| A07 | Data Ownership & Sovereignty | Data storage, ownership, GDPR, location | data, database, storage, own, schema |
| A08 | Integration & Contract Model | APIs, protocols, communication patterns | API, contract, protocol, interface, integration |

#### CTL (Control) Aspects - A09 to A12

| ID | Name | Definition | Keywords |
|----|------|------------|----------|
| A09 | Policy & Rules | Governance rules, coding standards | policy, rule, must, should, standard, convention |
| A10 | Approval & Authority Model | Who approves what, permission levels | approval, authority, permission, role, sign-off |
| A11 | Security & Compliance Posture | Authentication, encryption, audit, regulations | security, encrypt, auth, compliance, GDPR, audit |
| A12 | Risk & Blast Radius | Impact assessment, failure modes | risk, impact, failure, fallback, blast radius |

#### EVO (Evolution) Aspects - A13 to A16

| ID | Name | Definition | Keywords |
|----|------|------------|----------|
| A13 | Decision Lifecycle | How decisions evolve, versioning | version, evolve, supersede, lifecycle, deprecate |
| A14 | Reversibility & Exit Strategy | Rollback plans, migration paths | rollback, exit, revert, migration, undo |
| A15 | Environment & Promotion Rules | Deployment gates, environment rules | environment, promote, deploy, staging, production |
| A16 | Anti-Drift & Consistency | Preventing deviation, enforcement | drift, consistency, align, enforce, sync |

#### RES (Resources) Aspects - A17 to A20 *NEW*

| ID | Name | Definition | Keywords |
|----|------|------------|----------|
| A17 | Team & Ownership | Team structure, responsibilities, accountability | team, owner, responsible, accountable, structure |
| A18 | Skills & Capacity | Competencies required, staffing, headcount | skill, competency, hire, staff, headcount, expertise |
| A19 | Budget & Cost | Financial constraints, spending limits, ROI | budget, cost, spend, money, ROI, investment |
| A20 | Infrastructure Quota | Hardware limits, cloud resources, capacity | capacity, resource, limit, quota, instance, memory |

#### QTM (Quality & Timing) Aspects - A21 to A24 *NEW*

| ID | Name | Definition | Keywords |
|----|------|------------|----------|
| A21 | Performance Targets | Latency, throughput, response time | performance, latency, throughput, response, speed |
| A22 | Quality Standards | Code quality, test coverage, acceptance | quality, coverage, test, acceptance, criteria |
| A23 | SLA & Availability | Uptime targets, reliability requirements | SLA, uptime, availability, reliability, 99.9% |
| A24 | Schedule & Milestones | Deadlines, timelines, roadmap | schedule, deadline, timeline, milestone, date, Q1 |

---

## 5. Classification Decision Tree

### 5.1 Primary Classification (Domain Selection)

```
                              Human Input
                                  │
                                  ▼
               ┌──────────────────┴──────────────────┐
               │   What question does it answer?      │
               └──────────────────┬──────────────────┘
                                  │
    ┌─────────┬─────────┬─────────┼─────────┬─────────┬─────────┐
    ▼         ▼         ▼         ▼         ▼         ▼
  "WHY?"    "HOW?"   "RULES?"  "CHANGE?" "WHO/$$?"  "WHEN/
                                                     QUALITY?"
    │         │         │         │         │         │
    ▼         ▼         ▼         ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│  INT  │ │ ARCH  │ │  CTL  │ │  EVO  │ │  RES  │ │  QTM  │
└───────┘ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘
```

### 5.2 Detailed Decision Flow

```
Step 1: Is it about PURPOSE/GOALS?
├── YES → INT (Intent)
│   ├── Future/Vision → A01
│   ├── Problem/Challenge → A02
│   ├── In/Out of scope → A03
│   └── Trade-offs/Values → A04
└── NO → Continue

Step 2: Is it about STRUCTURE/DESIGN?
├── YES → ARCH (Architecture)
│   ├── Business domain → A05
│   ├── Service/Module → A06
│   ├── Data location → A07
│   └── API/Protocol → A08
└── NO → Continue

Step 3: Is it about RULES/PERMISSIONS?
├── YES → CTL (Control)
│   ├── General rule → A09
│   ├── Who can approve → A10
│   ├── Security/Compliance → A11
│   └── Risk/Impact → A12
└── NO → Continue

Step 4: Is it about CHANGE/EVOLUTION?
├── YES → EVO (Evolution)
│   ├── Version/Lifecycle → A13
│   ├── Rollback/Exit → A14
│   ├── Deploy/Promote → A15
│   └── Drift/Consistency → A16
└── NO → Continue

Step 5: Is it about PEOPLE/MONEY?
├── YES → RES (Resources)
│   ├── Team structure → A17
│   ├── Skills/Hiring → A18
│   ├── Budget/Cost → A19
│   └── Infrastructure → A20
└── NO → Continue

Step 6: Is it about QUALITY/TIMING?
├── YES → QTM (Quality & Timing)
│   ├── Performance target → A21
│   ├── Quality metric → A22
│   ├── SLA/Uptime → A23
│   └── Schedule/Deadline → A24
└── NO → Reconsider: May need to split decision
```

### 5.3 Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DECISION CLASSIFICATION QUICK REFERENCE                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  QUESTION → DOMAIN                                                           │
│  ──────────────────                                                          │
│  WHY/WHAT?      → INT  (Intent)                                             │
│  HOW/WHERE?     → ARCH (Architecture)                                       │
│  CAN/MUST NOT?  → CTL  (Control)                                            │
│  CHANGE SAFELY? → EVO  (Evolution)                                          │
│  WHO/HOW MUCH?  → RES  (Resources)       *NEW*                              │
│  HOW WELL/WHEN? → QTM  (Quality/Timing)  *NEW*                              │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  INT: vision, problem, scope, principle                                      │
│  ARCH: domain, service, data, API                                           │
│  CTL: policy, approval, security, risk                                      │
│  EVO: lifecycle, rollback, promote, drift                                   │
│  RES: team, skill, budget, capacity                                         │
│  QTM: performance, quality, SLA, schedule                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Migration Mapping (Old to New)

### 6.1 Backward Compatibility

All existing decisions in INT, ARCH, CTL, EVO domains remain valid. The new taxonomy is **additive**, not breaking.

### 6.2 Re-classification Candidates

Some decisions currently in suboptimal categories may benefit from re-classification:

| Current | Example | Recommended New | Reason |
|---------|---------|-----------------|--------|
| CTL/A09 | "Budget max $50K for infra" | RES/A19 | Budget is resource, not policy |
| ARCH/A05 | "Team Alpha owns Auth service" | RES/A17 | Team ownership is resource |
| CTL/A12 | "SLA must be 99.9% uptime" | QTM/A23 | SLA is quality target, not risk |
| INT/A01 | "Launch Q3 2025" | QTM/A24 | Timeline is schedule, not vision |
| ARCH/A06 | "Need 16GB RAM minimum" | RES/A20 | Capacity is resource |
| CTL/A09 | "Max 200ms latency" | QTM/A21 | Latency is performance target |
| ARCH/A08 | "95% test coverage" | QTM/A22 | Coverage is quality standard |
| CTL/A10 | "DevOps team deploys" | RES/A17 | Team responsibility |

### 6.3 Migration Strategy

1. **Phase 1**: Add RES and QTM domains to schema (no existing data affected)
2. **Phase 2**: New decisions use new taxonomy
3. **Phase 3**: Optional re-classification of existing decisions (human-reviewed)
4. **Phase 4**: Update AI classifier training

---

## 7. Examples by Category

### 7.1 INT (Intent) Examples

| Aspect | Example Decision | Statement |
|--------|------------------|-----------|
| A01 | Vision | "We aim to become the leading enterprise hospitality platform in Southeast Asia by 2027" |
| A02 | Problem | "Hotels currently use 5+ disconnected systems for operations, causing data silos and inefficiency" |
| A03 | Scope | "Phase 1 includes PMS and POS modules; HRM is out of scope until Q4" |
| A04 | Principle | "We prioritize user experience over feature completeness in all design decisions" |

### 7.2 ARCH (Architecture) Examples

| Aspect | Example Decision | Statement |
|--------|------------------|-----------|
| A05 | Domain | "The Order domain encompasses cart, checkout, and payment processing" |
| A06 | Service | "Payment service is deployed as an independent microservice with its own database" |
| A07 | Data | "Customer PII is stored only in the Identity service database, never replicated" |
| A08 | Integration | "All inter-service communication uses REST over HTTPS with JSON payloads" |

### 7.3 CTL (Control) Examples

| Aspect | Example Decision | Statement |
|--------|------------------|-----------|
| A09 | Policy | "All code changes require at least one approved review before merge" |
| A10 | Authority | "Infrastructure changes require sign-off from both DevOps lead and Security" |
| A11 | Security | "All PII must be encrypted at rest using AES-256 and in transit using TLS 1.3" |
| A12 | Risk | "Payment gateway failure must not block checkout; fallback to secondary provider" |

### 7.4 EVO (Evolution) Examples

| Aspect | Example Decision | Statement |
|--------|------------------|-----------|
| A13 | Lifecycle | "Decisions evolve via supersedes chain; original remains for audit trail" |
| A14 | Rollback | "All production deployments must support rollback within 15 minutes" |
| A15 | Promotion | "Production deployment requires passing all tests + security scan + QA sign-off" |
| A16 | Drift | "Infrastructure configuration is managed via Terraform; manual changes are prohibited" |

### 7.5 RES (Resources) Examples *NEW*

| Aspect | Example Decision | Statement |
|--------|------------------|-----------|
| A17 | Team | "The Platform team is responsible for shared infrastructure and DevOps tooling" |
| A18 | Skills | "Each product team must have at least one senior engineer with cloud architecture experience" |
| A19 | Budget | "Infrastructure budget for 2025 is capped at $200K; any excess requires CFO approval" |
| A20 | Capacity | "Production database instances must have minimum 32GB RAM and 8 vCPUs" |

### 7.6 QTM (Quality & Timing) Examples *NEW*

| Aspect | Example Decision | Statement |
|--------|------------------|-----------|
| A21 | Performance | "API response time must be under 200ms for 95th percentile of requests" |
| A22 | Quality | "All production code must have minimum 80% test coverage and pass linting" |
| A23 | SLA | "Core booking API must maintain 99.9% availability (8.76 hours max downtime/year)" |
| A24 | Schedule | "MVP launch deadline is September 30, 2025; no feature creep after August 15" |

---

## 8. Cross-Cutting Concerns

### 8.1 Handling Multi-Aspect Decisions

When a decision spans multiple aspects, use `related_decisions` to link:

**Example**: "Team Alpha owns Auth service and must maintain 99.9% uptime"

Split into:
1. **RES/A17**: "Team Alpha owns the Auth service" (team ownership)
2. **QTM/A23**: "Auth service must maintain 99.9% uptime" (SLA)
3. Link via `related_decisions`

### 8.2 Meta-Decisions (Decisions about Decisions)

Meta-decisions remain in **EVO/A13** (Decision Lifecycle):
- "All decisions must be reviewed quarterly"
- "Deprecated decisions remain visible for 1 year"

### 8.3 Cross-Domain Dependencies

Use `depends_on` relation type:
- QTM/A24 (Schedule) may depend on RES/A18 (Skills availability)
- RES/A20 (Capacity) may depend on QTM/A21 (Performance targets)

---

## 9. Implementation Considerations

### 9.1 Schema Changes

```python
# New DomainId enum
class DomainId(str, Enum):
    INT = "INT"    # Intent & Direction
    ARCH = "ARCH"  # Architecture & Boundaries
    CTL = "CTL"    # Control, Policy & Risk
    EVO = "EVO"    # Execution & Evolution
    RES = "RES"    # Resources & Economics (NEW)
    QTM = "QTM"    # Quality, Timing & Metrics (NEW)

# Extended AspectId enum
class AspectId(str, Enum):
    # Existing A01-A16...

    # RES Domain (NEW)
    A17 = "A17"  # Team & Ownership
    A18 = "A18"  # Skills & Capacity
    A19 = "A19"  # Budget & Cost
    A20 = "A20"  # Infrastructure Quota

    # QTM Domain (NEW)
    A21 = "A21"  # Performance Targets
    A22 = "A22"  # Quality Standards
    A23 = "A23"  # SLA & Availability
    A24 = "A24"  # Schedule & Milestones

# Updated matrix
DOMAIN_ASPECT_MATRIX = {
    DomainId.INT: [AspectId.A01, AspectId.A02, AspectId.A03, AspectId.A04],
    DomainId.ARCH: [AspectId.A05, AspectId.A06, AspectId.A07, AspectId.A08],
    DomainId.CTL: [AspectId.A09, AspectId.A10, AspectId.A11, AspectId.A12],
    DomainId.EVO: [AspectId.A13, AspectId.A14, AspectId.A15, AspectId.A16],
    DomainId.RES: [AspectId.A17, AspectId.A18, AspectId.A19, AspectId.A20],  # NEW
    DomainId.QTM: [AspectId.A21, AspectId.A22, AspectId.A23, AspectId.A24],  # NEW
}
```

### 9.2 Database Migration

```sql
-- Migration: Add new domain values
ALTER TYPE domain_id ADD VALUE 'RES';
ALTER TYPE domain_id ADD VALUE 'QTM';

-- Migration: Add new aspect values
ALTER TYPE aspect_id ADD VALUE 'A17';
ALTER TYPE aspect_id ADD VALUE 'A18';
ALTER TYPE aspect_id ADD VALUE 'A19';
ALTER TYPE aspect_id ADD VALUE 'A20';
ALTER TYPE aspect_id ADD VALUE 'A21';
ALTER TYPE aspect_id ADD VALUE 'A22';
ALTER TYPE aspect_id ADD VALUE 'A23';
ALTER TYPE aspect_id ADD VALUE 'A24';
```

### 9.3 UI Changes

```typescript
// New domain colors
export const DOMAIN_COLORS: Record<string, string> = {
  'INT': '#2563EB',   // Blue
  'ARCH': '#7C3AED',  // Purple
  'CTL': '#DC2626',   // Red
  'EVO': '#059669',   // Green
  'RES': '#F59E0B',   // Amber (NEW)
  'QTM': '#0891B2',   // Cyan (NEW)
}
```

---

## 10. Extensibility

### 10.1 Future-Proofing

The 6x4 structure allows for:
- Adding 2 more domains to reach 8x4 (32 cells) - maximum recommended
- Aspect ranges are sequential (A01-A04, A05-A08, etc.) - easy to extend

### 10.2 Reserved Ranges

| Range | Status | Purpose |
|-------|--------|---------|
| A01-A24 | Active | Current taxonomy |
| A25-A32 | Reserved | Future Domain 7 and 8 |
| A33+ | Unused | Major revision only |

### 10.3 Governance for Expansion

Per MANTRA-LAW-001, taxonomy changes require:
1. Human authorship
2. Constitutional amendment process
3. Migration plan for existing decisions

---

## 11. Projected Coverage Improvement

| Decision Type | Old Coverage | New Coverage | Improvement |
|---------------|--------------|--------------|-------------|
| Technical/Architectural | 95% | 95% | - |
| Process/Policy | 85% | 90% | +5% |
| People/Organization | 40% | 95% | +55% |
| Resource/Budget | 30% | 95% | +65% |
| Quality/Performance | 60% | 95% | +35% |
| Timing/Schedule | 20% | 95% | +75% |
| **Weighted Total** | **~72%** | **~95%** | **+23%** |

---

## 12. Decision Matrix Visualization

```
                    │ X1: Strategic │ X2: Current  │ X3: Boundary │ X4: Control  │
                    │    Goal       │   Situation  │    Limits    │  Governance  │
────────────────────┼───────────────┼──────────────┼──────────────┼──────────────┤
INT  (WHY/WHAT)     │ A01 Vision    │ A02 Problem  │ A03 Scope    │ A04 Principles│
                    │               │              │              │              │
────────────────────┼───────────────┼──────────────┼──────────────┼──────────────┤
ARCH (HOW/WHERE)    │ A05 Domain    │ A06 Service  │ A07 Data     │ A08 Contract │
                    │               │              │              │              │
────────────────────┼───────────────┼──────────────┼──────────────┼──────────────┤
CTL  (CAN/MUSTNOT)  │ A09 Policy    │ A10 Authority│ A11 Security │ A12 Risk     │
                    │               │              │              │              │
────────────────────┼───────────────┼──────────────┼──────────────┼──────────────┤
EVO  (CHANGE SAFE)  │ A13 Lifecycle │ A14 Rollback │ A15 Promote  │ A16 Drift    │
                    │               │              │              │              │
────────────────────┼───────────────┼──────────────┼──────────────┼──────────────┤
RES  (WHO/HOW MUCH) │ A17 Team      │ A18 Skills   │ A19 Budget   │ A20 Capacity │
        *NEW*       │               │              │              │              │
────────────────────┼───────────────┼──────────────┼──────────────┼──────────────┤
QTM  (WELL/WHEN)    │ A21 Perf      │ A22 Quality  │ A23 SLA      │ A24 Schedule │
        *NEW*       │               │              │              │              │
────────────────────┴───────────────┴──────────────┴──────────────┴──────────────┘

TOTAL: 6 Domains × 4 Aspects = 24 Decision Categories
```

---

## 13. Recommendation Summary

### Adopt the 6x4 Taxonomy (24 cells)

**Why**:
1. **Coverage**: Increases from ~72% to ~95% of real-world decisions
2. **Memorability**: IACE-RQ mnemonic, 6 domains is still manageable
3. **Backward Compatible**: All existing INT/ARCH/CTL/EVO decisions remain valid
4. **Clear Boundaries**: Each domain answers a distinct question
5. **Extensible**: Room to grow to 8x4 if needed in future

**Trade-off Acknowledged**:
- 24 cells vs 16 cells = 50% more complexity
- Mitigated by clear decision tree and AI classifier assistance

### Implementation Priority

1. **P0**: Update schema to allow RES/QTM domains and A17-A24 aspects
2. **P1**: Update AI classifier with new taxonomy
3. **P2**: Update frontend UI (colors, labels, matrix view)
4. **P3**: Optional migration of misclassified historical decisions

---

## Appendix A: Alternative Names Considered

| Final | Alternatives Considered | Rejection Reason |
|-------|------------------------|------------------|
| RES | PPL (People), ORG (Organization), CAP (Capacity) | RES covers people+budget+capacity |
| QTM | MET (Metrics), TIM (Timing), NFR (Non-Functional) | QTM covers quality+timing+metrics |

## Appendix B: Comparison with Enterprise Frameworks

| Framework | Domains | MANTRA Equivalent |
|-----------|---------|-------------------|
| TOGAF (EA) | Business, Data, Application, Technology | INT, ARCH |
| ITIL | Service Strategy, Design, Transition, Operation | INT, ARCH, EVO, CTL |
| SAFe | Portfolio, Program, Team | RES, QTM |
| ISO 27001 | Policies, Organization, Assets, Access | CTL, RES |

MANTRA's 6-domain model unifies perspectives from multiple frameworks.

---

**END OF PROPOSAL**

*This document requires human review and approval before implementation.*
*Per MANTRA-LAW-001, taxonomy changes require constitutional amendment.*
