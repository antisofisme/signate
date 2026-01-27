# MICS v2.0 Final Architecture
# MANTRA Intelligent Context System

**Version**: 2.0
**Status**: Ready for Implementation
**Last Updated**: 2026-01-27
**Research Basis**: Cross-Agent Deep Dive + Industry Standards

---

## Executive Summary

MICS v2.0 adalah arsitektur untuk menjadikan MANTRA sebagai **Intelligent Context Orchestrator** yang dapat:
1. Menyediakan constitutional rules ke AI assistants di berbagai platform
2. Meng-inject task-specific agent prompts dengan checklist dan constraints
3. Menjaga konsistensi across Claude, OpenAI, Cursor, Gemini, dan platform lainnya
4. Mencegah hallucination dengan grounding ke MANTRA decisions

Arsitektur ini divalidasi melalui riset mendalam terhadap:
- AGENTS.md specification (60K+ projects, 25+ tools)
- Model Context Protocol (MCP) best practices
- Agent2Agent (A2A) protocol analysis
- Context engineering patterns dari Anthropic, Google, AWS

---

## Two Perspectives: Builder vs User

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        PERBEDAAN PERSPEKTIF PENGGUNAAN                              │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────┐  ┌─────────────────────────────────────┐   │
│  │     MANTRA INTERNAL (Kita Build)    │  │    USER'S PROJECT (User Setup)      │   │
│  ├─────────────────────────────────────┤  ├─────────────────────────────────────┤   │
│  │                                     │  │                                     │   │
│  │  ATLAS_MANTRA/                      │  │  their-project/                     │   │
│  │  ├── backend/                       │  │  ├── AGENTS.md  ← ~30-50 lines     │   │
│  │  │   ├── mcp/        ← MCP Server   │  │  ├── (optional symlinks)           │   │
│  │  │   ├── context/    ← Pipeline     │  │  └── (their code...)               │   │
│  │  │   ├── memory/     ← State        │  │                                     │   │
│  │  │   └── agents/     ← Definitions  │  │  That's it!                         │   │
│  │  └── ...                            │  │  MANTRA provides everything else    │   │
│  │                                     │  │  via MCP/API.                       │   │
│  │  Complex implementation             │  │                                     │   │
│  │  Hosted on our server               │  │  Minimal setup                      │   │
│  │  User tidak perlu tahu detail       │  │  User hanya connect ke MANTRA       │   │
│  │                                     │  │                                     │   │
│  └─────────────────────────────────────┘  └─────────────────────────────────────┘   │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Part A: User Experience (Untuk Pengguna MANTRA)

### Apa yang User Perlu Lakukan

User yang ingin menggunakan MANTRA di project mereka hanya perlu **2 langkah sederhana**:

#### Step 1: Connect ke MANTRA MCP Server

Tambahkan konfigurasi MCP di AI assistant/IDE mereka:

**Claude Code** (`~/.claude/settings.json`):
```json
{
  "mcpServers": {
    "mantra": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-remote", "http://31.97.111.175:8002/mcp"]
    }
  }
}
```

**Cursor** (Settings → Features → MCP Servers):
```json
{
  "mantra": {
    "url": "http://31.97.111.175:8002/mcp"
  }
}
```

**Windsurf** (Settings → AI → MCP Configuration):
```json
{
  "mcpServers": {
    "mantra": {
      "serverUrl": "http://31.97.111.175:8002/mcp",
      "transport": "http"
    }
  }
}
```

**Trae** (`~/.trae/config.json`):
```json
{
  "mcp": {
    "servers": {
      "mantra": {
        "endpoint": "http://31.97.111.175:8002/mcp"
      }
    }
  }
}
```

**Antigravity / Other AI IDEs** (Generic MCP):
```json
{
  "mcp_servers": [
    {
      "name": "mantra",
      "url": "http://31.97.111.175:8002/mcp",
      "type": "http"
    }
  ]
}
```

**VS Code + Continue/Cody/Other Extensions**:
Lihat dokumentasi extension masing-masing untuk MCP configuration.

> **Note**: Jika IDE tidak support MCP, MANTRA juga menyediakan REST API di
> `http://31.97.111.175:8002/api/v1/context/task` yang bisa dipanggil manual.

#### Step 2: Tambahkan AGENTS.md di Project Root

Buat file `AGENTS.md` di root project (~30-50 lines):

```markdown
# [Project Name] - Agent Guidelines

## MANTRA Integration

This project uses MANTRA for architectural governance.

**Before making significant changes**, the AI assistant should:
1. Call `mantra_get_task_context` with the task intent
2. Follow the returned constraints and checklist
3. Respect Layer 0 principles (immutable)
4. Check relevant Layer 1 decisions

## Project Commands

| Task | Command |
|------|---------|
| Build | `npm run build` |
| Test | `npm test` |
| Lint | `npm run lint` |

## Boundaries

### Always Do
- Run tests before committing
- Follow existing code patterns

### Ask First
- Adding new dependencies
- Changing API contracts

### Never Do
- Violate MANTRA decisions
- Skip the deployment checklist
- Commit secrets or .env files
```

#### Step 3: Done!

Sekarang ketika user menggunakan AI assistant:
- AI akan otomatis memanggil MANTRA tools
- AI mendapat context, constraints, checklist dari MANTRA
- AI mengikuti decisions yang sudah ada
- Tidak perlu setup kompleks di project user

### Optional: Symlinks untuk Multi-Platform

Jika user pakai multiple AI tools, bisa buat symlinks:

```bash
# Di project root
ln -s AGENTS.md CLAUDE.md      # Untuk Claude Code
ln -s AGENTS.md .cursorrules   # Untuk Cursor
```

### User's Project Structure (Minimal)

```
user-project/
├── AGENTS.md                 ← Required (~30-50 lines)
├── CLAUDE.md → AGENTS.md     ← Optional symlink
├── .cursorrules → AGENTS.md  ← Optional symlink
│
├── src/                      ← User's code (unchanged)
├── package.json              ← User's config (unchanged)
└── ...                       ← Everything else unchanged
```

---

## Part B: MANTRA Internal Architecture (Yang Kita Build)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              MICS v2.0 ARCHITECTURE                                  │
│                         (Hosted di MANTRA Server)                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  USER'S AI ASSISTANT                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Claude Code / Cursor / OpenAI / Gemini                                     │    │
│  │  Reads: AGENTS.md → "Call mantra_get_task_context"                          │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                               │
│                                      │ MCP/API Call                                  │
│                                      ▼                                               │
│  ════════════════════════════════════════════════════════════════════════════════   │
│                          MANTRA SERVER (31.97.111.175)                               │
│  ════════════════════════════════════════════════════════════════════════════════   │
│                                                                                      │
│  MCP SERVER LAYER                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  RESOURCES (App)     TOOLS (Model)      PROMPTS (User)                      │    │
│  │  • Schema            • validate         • /review-decision                  │    │
│  │  • Layer 0           • search           • /draft-decision                   │    │
│  │  • Audit             • get_lineage      • /check-compliance                 │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                               │
│  CONTEXT ASSEMBLY PIPELINE           ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Intent → Agent → Decisions → Compress → Position Optimize                  │    │
│  │  (5 stages with token budget management)                                    │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                               │
│  MEMORY LAYER                        ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Working (in-context) → Session (Redis) → Semantic (MANTRA DB)              │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                      │                                               │
│  OUTPUT LAYER                        ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────┐    │
│  │  Claude │ Cursor │ OpenAI │ Gemini │ Generic Markdown                       │    │
│  └─────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                      │
│  FUTURE: A2A (Prepared, Not Implemented)                                             │
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐    │
│     /.well-known/agent-card.json  (Ready when A2A v1.0 releases)                    │
│  └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### MANTRA Internal File Structure

```
ATLAS_MANTRA/                        # ← MANTRA repository (kita develop)
│
├── backend/
│   ├── app.py                       # Existing FastAPI app
│   │
│   ├── mcp/                         # NEW: MCP Server Module
│   │   ├── __init__.py
│   │   ├── server.py                # Main MCP server
│   │   ├── resources.py             # Resources handlers
│   │   ├── tools.py                 # Tools handlers
│   │   ├── prompts.py               # Prompts handlers
│   │   └── adapters/                # Platform-specific formatters
│   │       ├── __init__.py
│   │       ├── claude.py
│   │       ├── cursor.py
│   │       ├── openai.py
│   │       └── generic.py
│   │
│   ├── context/                     # NEW: Context Assembly Pipeline
│   │   ├── __init__.py
│   │   ├── pipeline.py              # 5-stage assembly
│   │   ├── intent.py                # Intent recognition
│   │   ├── agent_selector.py        # Agent selection
│   │   ├── decision_retriever.py    # Decision fetching
│   │   ├── compressor.py            # Token budget management
│   │   └── position_optimizer.py    # Start/end placement
│   │
│   ├── memory/                      # NEW: Memory Layer
│   │   ├── __init__.py
│   │   ├── session.py               # Session state
│   │   └── cache.py                 # Redis integration
│   │
│   ├── agents/                      # NEW: Agent Definitions (YAML)
│   │   ├── deployment.yaml          # Deployment agent
│   │   ├── frontend.yaml            # Frontend development
│   │   ├── backend.yaml             # Backend development
│   │   ├── database.yaml            # Database operations
│   │   └── review.yaml              # Code review
│   │
│   └── core/                        # Existing MANTRA core
│       ├── api/
│       ├── domain/
│       └── ...
│
├── docs/
│   ├── MICS-v2-FINAL-ARCHITECTURE.md  # This document
│   └── ...
│
└── a2a/                             # FUTURE: A2A preparation (docs only)
    └── agent-card.json              # Agent Card schema (not implemented)
```

---

## Key Architectural Decisions

### 1. MCP Three-Primitive Design

| Primitive | Control | MANTRA Use |
|-----------|---------|------------|
| **Resources** | App-controlled | Schema, Layer 0 principles, Audit trails |
| **Tools** | Model-controlled | validate, search, get, lineage |
| **Prompts** | User-controlled | /review-decision, /draft-decision |

### 2. Token Budget Tiers

```
TIER 1: CRITICAL (~500 tokens) - Position: START (first 20%)
  • Agent identity & role
  • Layer 0 principles (summarized)
  • PROHIBITIONS (blocking constraints)

TIER 2: IMPORTANT (~1500 tokens) - Position: NEAR START
  • Active decisions for current task
  • Requirements & limitations
  • Checklist steps

TIER 3: SUPPLEMENTARY (~1000 tokens) - Position: END (last 10%)
  • Codebase context
  • Tool hints & suggestions

TIER 4: REFERENCE (Load on-demand via MCP tools)
  • Full decision details
  • History, audit trails
  • Related decisions
```

**Key Insight**: Avoid middle of context ("lost in the middle" problem).

### 3. Priority Hierarchy (Conflict Resolution)

```
P0: Safety & Security (non-negotiable)
P1: MANTRA Layer 0 (constitutional - immutable)
P2: MANTRA Layer 1 (decisions - append-only)
P3: Task Agent Prompts
P4: Platform Instructions (claude.md, .cursorrules)
P5: Codebase Patterns
P6: Session Preferences
```

### 4. A2A Strategy: Wait but Prepare

- **Now**: Design API as A2A-compatible, document as "future Skills"
- **Later**: Implement /.well-known/agent-card.json when A2A v1.0 releases

### 5. Error Recovery Pattern

Return rich errors for AI recovery:
```json
{
  "isError": true,
  "error_code": "DECISION_NOT_FOUND",
  "what_happened": "Decision with ID 'xyz' not found",
  "why": "ID is incorrect or decision was deleted",
  "valid_alternatives": ["abc-123", "def-456"],
  "how_to_fix": "Use mantra_search_decisions to find correct ID",
  "retry_allowed": true
}
```

### 6. Cross-Model Structured Format

Use YAML with explicit section markers for consistent parsing across Claude/GPT/Gemini.

---

## Implementation Phases

### Phase 0: Foundation (1-2 days)
- [ ] Create example AGENTS.md template for users
- [ ] Document user onboarding flow
- [ ] Define token budgets
- [ ] Document API as "future A2A Skills"

### Phase 1: MCP Server Core (3-4 days)
- [ ] MCP server setup (Python)
- [ ] Resources: schema, layer-0, audit
- [ ] Tools: validate, search, get, lineage
- [ ] Prompts: /review, /draft
- [ ] Error handling (isError pattern)

### Phase 2: Context Assembly Pipeline (3-4 days)
- [ ] Intent Recognition
- [ ] Agent Selection
- [ ] Decision Retrieval
- [ ] Compression & Tiering
- [ ] Position Optimization

### Phase 3: Memory & State (2-3 days)
- [ ] Working Memory
- [ ] Session Memory (Redis)
- [ ] Semantic Memory integration

### Phase 4: Platform Adapters (2-3 days)
- [ ] Claude adapter
- [ ] Cursor adapter
- [ ] OpenAI adapter
- [ ] Generic Markdown

### Phase 5: Metrics & Monitoring (1-2 days)
- [ ] CARE metrics (Completeness, Accuracy, Relevance, Efficiency)
- [ ] Performance monitoring (<100ms P95)

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Assembly Latency | <100ms P95 |
| Token Utilization | <50% of budget |
| Decision Recall | >95% relevant decisions |
| Cross-Platform Consistency | >90% same output class |
| Error Recovery | >90% |
| Layer 0 Compliance | 100% |

---

## Summary: Who Does What

| Component | Location | Who Maintains |
|-----------|----------|---------------|
| MCP Server | MANTRA backend | MANTRA team |
| Context Pipeline | MANTRA backend | MANTRA team |
| Agent Definitions | MANTRA backend | MANTRA team |
| Platform Adapters | MANTRA backend | MANTRA team |
| AGENTS.md template | MANTRA docs | MANTRA team provides template |
| User's AGENTS.md | User's project | User (copy template, customize) |
| MCP config | User's AI settings | User (one-time setup) |

**User effort**: ~10 minutes setup
**MANTRA provides**: Everything else

---

## Research Sources

1. **AGENTS.md**: agents.md, OpenAI Codex docs, GitHub blog
2. **MCP**: modelcontextprotocol.io, Anthropic docs
3. **A2A**: a2a-protocol.org, Google Developers blog
4. **Context Engineering**: Anthropic, LangChain, Manus.im
5. **Memory**: AWS AgentCore, Mem0, MongoDB

---

## Approval Checklist

Before implementation:

- [ ] User approves overall architecture
- [ ] User understands: complex stuff in MANTRA, simple setup for users
- [ ] Token budget targets confirmed
- [ ] Priority hierarchy accepted
- [ ] A2A "wait and prepare" strategy agreed
- [ ] Implementation phases timeline accepted
