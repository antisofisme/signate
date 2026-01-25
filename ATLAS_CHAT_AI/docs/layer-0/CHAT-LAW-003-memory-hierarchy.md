# CHAT-LAW-003: Memory Hierarchy

**Status**: IMMUTABLE
**Created**: 2026-01-25
**Category**: Memory System

---

## Statement

> Memory system HARUS terdiri dari 4 layer yang terstruktur:
> Working Memory → Episodic Memory → Semantic Memory → Temporal Memory

---

## Rationale

Seperti memori manusia, AI chat membutuhkan berbagai jenis memori:
- **Immediate recall** - apa yang baru saja dibicarakan
- **Event memory** - percakapan kemarin, minggu lalu
- **Fact memory** - user suka kopi, user kerja di tech company
- **Time-based memory** - "bulan lalu kita bahas X"

Hierarchy ini memungkinkan context yang relevan tanpa overload token.

---

## Memory Layers

### Layer 1: Working Memory

```
Type: In-memory (per session)
Scope: Current conversation only
Lifetime: Session duration
Storage: RAM / Redis
```

**Contains**:
- Current session messages (last N messages)
- Active context window
- Pending user intent

**Characteristics**:
- Fastest access (< 1ms)
- Lost on session end
- Limited by context window

### Layer 2: Episodic Memory

```
Type: Persistent (PostgreSQL)
Scope: Per user, per session
Lifetime: Permanent (unless deleted by user)
Storage: PostgreSQL + Vector embeddings
```

**Contains**:
- All chat sessions
- All messages per session
- Session summaries
- Session embeddings (for similarity search)

**Characteristics**:
- Searchable by time, session, content
- Summarized for long sessions
- Linked to specific events/conversations

### Layer 3: Semantic Memory

```
Type: Persistent (PostgreSQL + Vector)
Scope: Per user (cross-session)
Lifetime: Permanent
Storage: PostgreSQL + Qdrant
```

**Contains**:
- User facts extracted from conversations
- User preferences
- User knowledge (what they know/don't know)
- Relationships (people, projects user mentioned)

**Characteristics**:
- Accumulated over time
- Confidence scores (some facts more certain)
- Can be corrected/updated

**Examples**:
```json
{"fact": "User works at Signate", "confidence": 0.95}
{"fact": "User prefers TypeScript over JavaScript", "confidence": 0.8}
{"fact": "User is building a hospitality platform", "confidence": 0.9}
```

### Layer 4: Temporal Memory

```
Type: Aggregated summaries
Scope: Per user, time-based
Lifetime: Permanent
Storage: PostgreSQL
```

**Contains**:
- Daily summaries
- Weekly summaries
- Monthly summaries
- Topic frequency over time

**Characteristics**:
- Auto-generated from episodic memory
- Compressed representation
- Enables "last month we discussed..."

---

## Memory Flow

```
User Message
     │
     ▼
┌─────────────────┐
│ Working Memory  │◄── Fast access, current context
└────────┬────────┘
         │ Save after session
         ▼
┌─────────────────┐
│ Episodic Memory │◄── Full history, searchable
└────────┬────────┘
         │ Extract facts
         ▼
┌─────────────────┐
│ Semantic Memory │◄── User knowledge base
└────────┬────────┘
         │ Aggregate periodically
         ▼
┌─────────────────┐
│ Temporal Memory │◄── Time-based summaries
└─────────────────┘
```

---

## Constraints

### REQUIREMENT
- Working Memory HARUS di-flush ke Episodic saat session end
- Semantic Memory extraction HARUS dilakukan async (tidak blocking chat)
- Temporal Memory aggregation HARUS dijadwalkan (cron, tidak real-time)

### PROHIBITION
- DILARANG akses Episodic Memory untuk setiap message (terlalu lambat)
- DILARANG menyimpan raw messages di Semantic Memory (hanya extracted facts)
- DILARANG menghapus Episodic Memory tanpa user consent

### LIMITATION
- Working Memory: Maksimal 20 messages atau 4000 tokens
- Episodic summary: Dibuat setelah 30 messages per session
- Semantic extraction: Maksimal 100 facts per user
- Temporal aggregation: Daily at midnight, weekly on Sunday

---

## Context Assembly Priority

Saat membangun context untuk LLM:

```
Priority 1: Working Memory (current conversation)
Priority 2: Semantic Memory (relevant user facts)
Priority 3: Episodic Memory (similar past conversations)
Priority 4: Temporal Memory (if user asks about past)
```

Token budget distribution:
```
Working Memory:  50% of context window
Semantic Facts:  15%
Episodic Search: 25%
Temporal:        10% (only when relevant)
```

---

## Invariants

1. Setiap message HARUS masuk Working Memory dulu
2. Session end HARUS trigger flush ke Episodic
3. Semantic facts HARUS punya source (session_id, message_id)
4. Temporal summaries HARUS traceable ke Episodic entries
