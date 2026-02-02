# CHAT Layer 1: Architecture Decisions

**TYPE**: Architecture Repository
**STATUS**: ACTIVE
**SUBORDINATE TO**: Layer 0

---

## Notice

This directory contains architecture decisions implementing Layer 0 Laws.

All decisions are subordinate to Layer 0 — conflicts resolve to Layer 0.

---

## Documents

| Document | Type | Implements |
|----------|------|------------|
| CHAT-L1-ARCH-001 | Architecture Decision | Core Interfaces — all interface definitions |
| CHAT-L1-ARCH-002 | Architecture Decision | Tech Stack — Qdrant, OpenAI, PostgreSQL choices |
| CHAT-L1-ARCH-003 | Architecture Decision | Memory Architecture — 4-layer implementation |
| CHAT-L1-ARCH-004 | Architecture Decision | RAG Pipeline — retrieval and generation flow |
| CHAT-L1-ARCH-005 | Architecture Decision | Multi-Tenant — tenant configuration model |
| CHAT-L1-ARCH-006 | Architecture Decision | Project Structure — directory organization |

---

## Relationship to Layer 0

| Layer 0 Law | Layer 1 Decisions |
|-------------|-------------------|
| CHAT-LAW-001 Modular | CHAT-L1-ARCH-001, CHAT-L1-ARCH-006 |
| CHAT-LAW-002 Interface-First | CHAT-L1-ARCH-001 |
| CHAT-LAW-003 Memory Hierarchy | CHAT-L1-ARCH-003 |
| CHAT-LAW-004 Multi-Tenant | CHAT-L1-ARCH-005 |
| CHAT-LAW-005 No Vendor Lock-in | CHAT-L1-ARCH-002 |
| CHAT-LAW-006 Append-Only | CHAT-L1-ARCH-003 |

---

## Precedence

Layer 1 implements. Layer 1 does not redefine.

Layer 0 prevails in all conflicts.

---

**END OF README**
