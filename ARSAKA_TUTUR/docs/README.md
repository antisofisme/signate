# ARSAKA_TUTUR Documentation

**TYPE**: Law and Specification Repository
**STATUS**: Active
**AUTHORITY**: Human Decision Only

> **Build once. Use everywhere.**

---

## Quick Start

New to CHAT_AI? Start here:

| Document | Purpose |
|----------|---------|
| [VALUE-001: Why CHAT_AI?](./value/VALUE-001-why-chat-ai.md) | Understand why a shared AI chat infrastructure |
| [GUIDE-001: Quick Start](./guides/GUIDE-001-quick-start.md) | Get running and send first message in 10 minutes |

---

## Documentation Structure

```
docs/
├── README.md                 ← This file (start here)
│
├── value/                    ← WHY use CHAT_AI
│   └── VALUE-001-why-chat-ai.md
│
├── guides/                   ← HOW to use CHAT_AI
│   └── GUIDE-001-quick-start.md
│
├── layer-0/                  ← Constitutional Laws (IMMUTABLE)
│   ├── CHAT-LAW-001-modular-architecture.md
│   ├── CHAT-LAW-002-interface-first-design.md
│   ├── CHAT-LAW-003-memory-hierarchy.md
│   ├── CHAT-LAW-004-multi-tenant-isolation.md
│   ├── CHAT-LAW-005-no-vendor-lock-in.md
│   └── CHAT-LAW-006-append-only-history.md
│
├── layer-1/                  ← Architecture Decisions
│   ├── CHAT-L1-ARCH-001-core-interfaces.md
│   ├── CHAT-L1-ARCH-002-tech-stack.md
│   ├── CHAT-L1-ARCH-003-memory-architecture.md
│   ├── CHAT-L1-ARCH-004-rag-pipeline.md
│   ├── CHAT-L1-ARCH-005-multi-tenant.md
│   └── CHAT-L1-ARCH-006-project-structure.md
│
├── layer-2/                  ← Implementation Specifications
│   ├── CHAT-L2-SPEC-001-database-schema.md
│   ├── CHAT-L2-SPEC-002-api-endpoints.md
│   ├── CHAT-L2-SPEC-003-qdrant-collections.md
│   ├── CHAT-L2-SPEC-004-configuration.md
│   └── CHAT-L2-SPEC-005-implementation-phases.md
│
└── layer-3/                  ← Operational Guidelines
    ├── CHAT-L3-OPS-001-deployment.md
    ├── CHAT-L3-OPS-002-monitoring.md
    ├── CHAT-L3-OPS-003-troubleshooting.md
    └── CHAT-L3-OPS-004-tenant-onboarding.md
```

---

## User Documentation

### Value Proposition

| Document | Summary |
|----------|---------|
| [VALUE-001](./value/VALUE-001-why-chat-ai.md) | Why shared AI chat infrastructure, multi-tenant benefits, easy to leave |

### Guides

| Document | Summary |
|----------|---------|
| [GUIDE-001](./guides/GUIDE-001-quick-start.md) | 10-minute quick start, Docker setup, first message |

---

## Technical Documentation

> **Notice**: Layer documentation contains constitutional law and binding specifications.
> It is not guidance. See User Documentation above for onboarding.

### Layer Structure

```
layer-0/              ← Constitutional Law (IMMUTABLE)
layer-1/              ← Architecture Decisions (STABLE)
layer-2/              ← Implementation Specifications (ACTIVE)
layer-3/              ← Operational Guidelines (ACTIVE)
```

---

### Layer 0: Constitutional Laws

Contains immutable laws governing ARSAKA_TUTUR architecture.

| Document | Type | Status |
|----------|------|--------|
| [CHAT-LAW-001](./layer-0/CHAT-LAW-001-modular-architecture.md) | Law | IMMUTABLE |
| [CHAT-LAW-002](./layer-0/CHAT-LAW-002-interface-first-design.md) | Law | IMMUTABLE |
| [CHAT-LAW-003](./layer-0/CHAT-LAW-003-memory-hierarchy.md) | Law | IMMUTABLE |
| [CHAT-LAW-004](./layer-0/CHAT-LAW-004-multi-tenant-isolation.md) | Law | IMMUTABLE |
| [CHAT-LAW-005](./layer-0/CHAT-LAW-005-no-vendor-lock-in.md) | Law | IMMUTABLE |
| [CHAT-LAW-006](./layer-0/CHAT-LAW-006-append-only-history.md) | Law | IMMUTABLE |

Non-compliance with Layer 0 is a violation.

---

### Layer 1: Architecture Decisions

Contains architecture decisions implementing Layer 0 Laws.

| Document | Type | Status |
|----------|------|--------|
| [CHAT-L1-ARCH-001](./layer-1/CHAT-L1-ARCH-001-core-interfaces.md) | Architecture | ACTIVE |
| [CHAT-L1-ARCH-002](./layer-1/CHAT-L1-ARCH-002-tech-stack.md) | Architecture | ACTIVE |
| [CHAT-L1-ARCH-003](./layer-1/CHAT-L1-ARCH-003-memory-architecture.md) | Architecture | ACTIVE |
| [CHAT-L1-ARCH-004](./layer-1/CHAT-L1-ARCH-004-rag-pipeline.md) | Architecture | ACTIVE |
| [CHAT-L1-ARCH-005](./layer-1/CHAT-L1-ARCH-005-multi-tenant.md) | Architecture | ACTIVE |
| [CHAT-L1-ARCH-006](./layer-1/CHAT-L1-ARCH-006-project-structure.md) | Architecture | ACTIVE |

Layer 1 implements. Layer 1 does not redefine.

Layer 0 prevails in all conflicts.

---

### Layer 2: Implementation Specifications

Contains implementation specifications derived from Layer 1 Architecture.

| Document | Type | Status |
|----------|------|--------|
| [CHAT-L2-SPEC-001](./layer-2/CHAT-L2-SPEC-001-database-schema.md) | Specification | ACTIVE |
| [CHAT-L2-SPEC-002](./layer-2/CHAT-L2-SPEC-002-api-endpoints.md) | Specification | ACTIVE |
| [CHAT-L2-SPEC-003](./layer-2/CHAT-L2-SPEC-003-qdrant-collections.md) | Specification | ACTIVE |
| [CHAT-L2-SPEC-004](./layer-2/CHAT-L2-SPEC-004-configuration.md) | Specification | ACTIVE |
| [CHAT-L2-SPEC-005](./layer-2/CHAT-L2-SPEC-005-implementation-phases.md) | Specification | ACTIVE |

Layer 2 specifies. Layer 2 does not redefine architecture.

Layer 0 and Layer 1 prevail in all conflicts.

---

### Layer 3: Operational Guidelines

Contains operational guidelines for running ARSAKA_TUTUR.

| Document | Type | Status |
|----------|------|--------|
| [CHAT-L3-OPS-001](./layer-3/CHAT-L3-OPS-001-deployment.md) | Operations | ACTIVE |
| [CHAT-L3-OPS-002](./layer-3/CHAT-L3-OPS-002-monitoring.md) | Operations | ACTIVE |
| [CHAT-L3-OPS-003](./layer-3/CHAT-L3-OPS-003-troubleshooting.md) | Operations | ACTIVE |
| [CHAT-L3-OPS-004](./layer-3/CHAT-L3-OPS-004-tenant-onboarding.md) | Operations | ACTIVE |

Layer 3 guides operations. Layer 3 does not define architecture or specifications.

All higher layers prevail in conflicts.

---

### Layer Status

| Layer | Purpose | Status |
|-------|---------|--------|
| layer-0 | Constitutional Law | IMMUTABLE |
| layer-1 | Architecture Decisions | STABLE |
| layer-2 | Implementation Specs | ACTIVE |
| layer-3 | Operational Guidelines | ACTIVE |

---

### Precedence Rule

**LAW > Architecture > Specification > Operations**

---

### Immutability Rules

All Layer 0 documents are constitutional and immutable.

Higher layers MAY reference Layer 0 documents but MUST NOT:
- Redefine core principles
- Alter component boundaries
- Expand tenant isolation rules
- Introduce alternative interpretations

Any violation is INVALID per Layer 0 Laws.

---

## Core Principles

| Principle | Description |
|-----------|-------------|
| **Modular** | Components are swappable without system changes |
| **Interface-First** | Access through abstractions, not implementations |
| **Memory Hierarchy** | 4-layer memory system (Working, Episodic, Semantic, Temporal) |
| **Multi-Tenant** | Absolute data isolation between tenants |
| **No Lock-in** | Can migrate vendors without data loss |
| **Append-Only** | Chat history is immutable for audit |

---

## 4-Layer Memory System

```
WORKING MEMORY (In-Memory)
├── Current conversation context
├── Active session state
└── Immediate recall

EPISODIC MEMORY (PostgreSQL + Vector)
├── Past sessions
├── Conversation history
└── Retrievable by similarity

SEMANTIC MEMORY (PostgreSQL)
├── User facts
├── Preferences
└── Extracted knowledge

TEMPORAL MEMORY (PostgreSQL)
├── Time-based summaries
├── Daily/weekly/monthly rollups
└── Long-term context
```

---

## Technology

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Vector DB | Qdrant | Self-hosted, Rust performance, 2025 production-proven |
| Embeddings | OpenAI | text-embedding-3-small, cost-effective, portable |
| Primary DB | PostgreSQL | ACID, existing, mature |
| LLM | Multi-provider | OpenAI, DeepSeek, Claude, Groq - switchable |

---

**Build once. Use everywhere.**
