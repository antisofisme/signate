# INFRA Documentation - Master Index

**PROJECT**: ATLAS PUGUH - Infra Authorization Engine
**STATUS**: Active Development

> **Easy to leave, hard to want to leave.**

---

## Quick Start

New to PUGUH? Start here:

| Document | Purpose |
|----------|---------|
| [VALUE-001: Why PUGUH?](./value/VALUE-001-why-puguh.md) | Understand the problem PUGUH solves |
| [VALUE-002: ROI Analysis](./value/VALUE-002-roi-analysis.md) | Build vs. buy analysis |
| [GUIDE-001: Quick Start](./guides/GUIDE-001-quick-start.md) | Your first authorization check in 5 minutes |
| [GUIDE-004: Migration](./guides/GUIDE-004-migration.md) | How to leave PUGUH (yes, really) |

---

## Documentation Overview

```
docs/
├── value/                    ← WHY use PUGUH
│   ├── VALUE-001-why-puguh.md
│   └── VALUE-002-roi-analysis.md
│
├── guides/                   ← HOW to use PUGUH
│   ├── GUIDE-001-quick-start.md
│   └── GUIDE-004-migration.md
│
└── layer-*/                  ← Technical specifications
```

---

## Value Proposition

| Document | Summary |
|----------|---------|
| [VALUE-001](./value/VALUE-001-why-puguh.md) | Why centralized authorization matters, easy-to-leave philosophy |
| [VALUE-002](./value/VALUE-002-roi-analysis.md) | Build vs. buy: $400K+ savings, 80-95% cost reduction |

## Guides

| Document | Summary |
|----------|---------|
| [GUIDE-001](./guides/GUIDE-001-quick-start.md) | 5-minute quick start, first authorization check |
| [GUIDE-004](./guides/GUIDE-004-migration.md) | Complete migration guide - export, transform, migrate |

---

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Three Decisions** | ALLOWED, DENIED, REQUIRE_APPROVAL - no ambiguity |
| **Fail-Closed** | No matching rule = DENIED |
| **Tenant Isolation** | Complete data separation per tenant |
| **Audit Everything** | Every decision logged with full context |
| **OpenFGA Compatible** | Standard authorization model, portable rules |

---

## Technical Documentation

Infra technical documentation is organized into **4 layers**, each building on the previous:

| Layer | Purpose | Document Count |
|-------|---------|---------------|
| [Layer 0](./layer-0/) | Foundation Design - Core concepts | 6 documents |
| [Layer 1](./layer-1/) | SDK Contracts & Events - API surface | 2 documents |
| [Layer 2](./layer-2/) | Architecture & Boundaries - System design | 4 documents |
| [Layer 3](./layer-3/) | Implementation Standards - Coding guides | 6 documents |

---

## Quick Navigation

### Layer 0: Foundation Design
> **What is Infra? What are the core concepts?**

- [README](./layer-0/README.md) - Layer overview
- [INFRA-DEC-001](./layer-0/INFRA-DEC-001-decision-model.md) - Decision model (ALLOWED, DENIED, REQUIRE_APPROVAL)
- [INFRA-DEC-002](./layer-0/INFRA-DEC-002-tenancy-model.md) - Tenancy & isolation
- [INFRA-DEC-003](./layer-0/INFRA-DEC-003-rule-workflow-abstraction.md) - Rules & workflows
- [INFRA-DEC-004](./layer-0/INFRA-DEC-004-control-plane-overview.md) - Control plane functions (OVERLAY)
- [INFRA-DEC-005](./layer-0/INFRA-DEC-005-enforcement-anti-bypass.md) - Enforcement rules (OVERLAY)
- [INFRA-DEC-006](./layer-0/INFRA-DEC-006-event-audit-immutable-facts.md) - Event & audit immutability (OVERLAY)

---

### Layer 1: SDK Contracts & Events
> **How do applications interact with Infra?**

- [README](./layer-1/README.md) - Layer overview
- [INFRA-LAY1-001](./layer-1/INFRA-LAY1-001-sdk-contracts.md) - SDK method signatures
- [INFRA-LAY1-002](./layer-1/INFRA-LAY1-002-event-model.md) - Event types & delivery

---

### Layer 2: Architecture & Boundaries
> **How is Infra architected as a system?**

- [README](./layer-2/README.md) - Layer overview
- [INFRA-LAY2-001](./layer-2/INFRA-LAY2-001-service-boundaries.md) - Service responsibilities
- [INFRA-LAY2-002](./layer-2/INFRA-LAY2-002-critical-path-sequences.md) - Critical path flows
- [INFRA-LAY2-003](./layer-2/INFRA-LAY2-003-data-persistence-model.md) - Data storage model
- [INFRA-LAY2-004](./layer-2/INFRA-LAY2-004-monitoring-observability.md) - Observability requirements

---

### Layer 3: Implementation Standards
> **How should Infra components be coded?**

- [README](./layer-3/README.md) - Layer overview
- [INFRA-LAY3-001](./layer-3/INFRA-LAY3-001-sdk-implementation-standards.md) - SDK standards
- [INFRA-LAY3-002](./layer-3/INFRA-LAY3-002-core-service-implementation-standards.md) - Core service standards
- [INFRA-LAY3-003](./layer-3/INFRA-LAY3-003-cms-implementation-standards.md) - CMS standards
- [INFRA-LAY3-004](./layer-3/INFRA-LAY3-004-data-layer-implementation-standards.md) - Data layer standards
- [INFRA-LAY3-005](./layer-3/INFRA-LAY3-005-event-logging-implementation-standards.md) - Event & logging standards
- [INFRA-LAY3-006](./layer-3/INFRA-LAY3-006-testing-verification-standards.md) - Testing standards

---

## Other Documents

| Document | Purpose |
|----------|---------|
| [INFRA-MVP-PLAN](./INFRA-MVP-PLAN.md) | MVP implementation plan |
| [planning/](./planning/) | Planning and roadmap documents |

---

## Reading Order for New Team Members

1. **Start with Layer 0** - Understand core concepts
   - Read [Layer 0 README](./layer-0/README.md) first
   - Then INFRA-DEC-001, 002, 003 (core documents)
   - Then overlay documents (004, 005, 006)

2. **Then Layer 1** - Understand API surface
   - SDK contracts and events

3. **Then Layer 2** - Understand system architecture
   - Service boundaries and data flow

4. **Finally Layer 3** - Implementation details
   - Only when ready to code

---

## Document Naming Convention

```
INFRA-{CATEGORY}-{NUMBER}-{descriptor}.md

Categories:
- DEC    = Foundation Decision documents (Layer 0)
- LAY1   = Layer 1 documents
- LAY2   = Layer 2 documents
- LAY3   = Layer 3 documents
```

---

## Key Principles (Quick Reference)

| Principle | Description |
|-----------|-------------|
| **Fail-Closed** | No matching rule → DENIED |
| **Immutable Decisions** | Outcome never changes after decided |
| **First-Match-Wins** | Rule evaluation order is deterministic |
| **Tenant Isolation** | Hard boundary at every operation |
| **Audit Everything** | Every decision and action is logged |
| **AI is Advisor, Not Actor** | AI cannot make decisions or mutations |

---

## Integration Model

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Application                         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Service A  │  │  Service B  │  │  Service C  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          │                                  │
│                    ┌─────┴─────┐                            │
│                    │ PUGUH SDK │  ← Thin, replaceable       │
│                    └─────┬─────┘                            │
└──────────────────────────┼──────────────────────────────────┘
                           │
                     ┌─────┴─────┐
                     │  PUGUH    │  ← Hosted service
                     │  Engine   │    (your data, our infra)
                     └───────────┘
```

**SDK in your code**: Thin, standard interfaces, easy to replace
**Engine hosted**: Rules, decisions, workflows, audit trail

---

## Summary

| Aspect | PUGUH Approach |
|--------|----------------|
| **Integration** | Thin SDK, OpenFGA-compatible |
| **Lock-in** | None - standard formats, full export |
| **Value** | Decision audit, workflow automation, compliance |
| **Migration** | 1-2 weeks, complete guide provided |
| **Pricing** | Per decision, predictable |

---

**Easy to leave. Hard to want to leave.**
