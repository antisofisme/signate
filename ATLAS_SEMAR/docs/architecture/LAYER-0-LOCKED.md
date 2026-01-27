# JARVIS LAYER 0: LOCKED

**Status**: ✅ LOCKED FOR LAYER 1 EXECUTION
**Date**: 2025-12-28
**Approval**: Architecture Review Completed, Clarifications Applied

---

## Pre-Lock Confirmation

All foundational concepts (JARVIS-DEC-001, 002, 003) are locked and ready.

Three clarifications have been applied per architectural review:

### ✅ Clarification 1: Utterance Length Scope (JARVIS-DEC-001)

**Added**: Explicit scope statement

```
Jarvis is optimized for short, command-like utterances (< 10 seconds audio).
Long-form dictation is explicitly out of scope for MVP.

* MVP design targets: quick commands, brief questions, code snippets
* Long utterances (> 10s): degraded UX, consider manual typing instead
* Phase 2 (streaming STT): may improve long-utterance latency if needed
* Current design intentionally accepts this limitation to keep implementation simple
```

**Impact**: Clarifies MVP scope, prevents over-engineering for long-form use cases

**Verification**:
- Document updated: JARVIS-DEC-001 (after SLA Tiers section)
- No design changes required (clarification only)

---

### ✅ Clarification 2: Safety Scanning Scope (JARVIS-DEC-003)

**Added**: Explicit implementation rule

```
⚠️ Safety scanning applies ONLY to non-command voice input, NOT to command parsing.

Flow:
  User input received
  ↓
  → Is this a command? (exact/prefix match)
     ├─ YES → Process as command (NO safety scan)
     └─ NO → Treat as voice input
            → Apply safety scan
            → If dangerous: show confirmation gate
            → If safe: send to Claude

Rationale: Commands are structured and user-intentional. Voice input is free-form
and may accidentally contain dangerous patterns.
```

**Impact**: Prevents implementors from mistakenly scanning command parsing (common error)

**Verification**:
- Document updated: JARVIS-DEC-003 (Safety Model section header)
- No design changes required (clarification only)

---

## Layer 0 Architecture Summary

| Document | Status | Concept |
|----------|--------|---------|
| JARVIS-DEC-001 | ✅ LOCKED | Audio Pipeline & Latency Model |
| JARVIS-DEC-002 | ✅ LOCKED | Single-Session & State Model |
| JARVIS-DEC-003 | ✅ LOCKED | Command Grammar & Safety Model |

---

## Core Architectural Guarantees (LOCKED)

### JARVIS-DEC-001: Audio Pipeline & Latency

**Guarantees**:
- ✅ Push-to-talk hard hotkey activation (no always-listening)
- ✅ End-to-end latency ≤ 2s (hard SLA)
- ✅ Whisper local in MVP (≤ 1s STT)
- ✅ Fallback to manual typing on STT failure
- ✅ Optimized for short utterances (< 10s), long-form out of scope

**Non-Negotiable Constraints**:
- ❌ No always-listening background processing
- ❌ No cloud STT in critical path (MVP)
- ❌ No latency trade-offs that exceed 2s

---

### JARVIS-DEC-002: Single-Session & State Model

**Guarantees**:
- ✅ Session = Claude CLI lifetime (Jarvis dies with Claude)
- ✅ In-memory state only (no persistence across sessions)
- ✅ Mode as local state (affects prompt shaping, NOT stored in chat)
- ✅ No conversation history in Jarvis
- ✅ No secondary memory (Claude is sole brain)

**Non-Negotiable Constraints**:
- ❌ No persistent user preferences
- ❌ No cross-session memory
- ❌ No voice input history
- ❌ No decision cache
- ❌ Mode never embedded as system prompt

---

### JARVIS-DEC-003: Command Grammar & Safety Model

**Guarantees**:
- ✅ Commands use STRICT deterministic grammar (exact/prefix match only)
- ✅ No semantic guessing in MVP
- ✅ Safety detection for 4 categories (file ops, git, database, system)
- ✅ Safety scanning applies to voice input only (NOT command parsing)
- ✅ Explicit Y/N confirmation required (no voice confirmation)
- ✅ 6 supported commands: kirim, ulang, ringkas (Phase 2), jelaskan (Phase 2), mode, help

**Non-Negotiable Constraints**:
- ❌ No fuzzy NLU in MVP
- ❌ No semantic intent detection
- ❌ No auto-confirmation of dangerous operations
- ❌ No voice "yes" confirmation (explicit Y key only)

---

## Compatibility with Game Launcher Model

✅ **CONFIRMED**: Layer 0 is fully compatible with game launcher deployment model

**Why**:
- No network dependency in critical path
- No authentication in audio pipeline
- No license checking in audio/STT/command processing
- No tenant model or multi-user system
- No web control or cloud reasoning

**Implication**: Phase 2 launcher can be added without modifying a single line of Layer 0

---

## Phase 1 Scope (LOCKED)

**In Scope**:
- ✅ Audio pipeline (hotkey → VAD → STT → text)
- ✅ Session management (state, mode, last_transcription)
- ✅ Command grammar (strict parsing, 6 commands)
- ✅ Safety gates (keyword detection, explicit confirmation)
- ✅ Basic observability (metrics collection)

**Out of Scope (Deferred to Phase 2)**:
- ❌ Streaming STT (for long utterances)
- ❌ Cloud STT fallback
- ❌ ringkas/jelaskan commands
- ❌ Fuzzy command matching
- ❌ Session persistence/recovery
- ❌ Launcher (licensing, authentication, updates)
- ❌ Auxiliary LLM integration

---

## Layer 0 Success Criteria (LOCKED)

Before Layer 1, verify:

**Audio Pipeline**:
- ✅ Push-to-talk hotkey works (F12 or configurable)
- ✅ End-to-end latency ≤ 2s for 90% of short queries (p90 SLA)
- ✅ Whisper local ≤ 800ms (p95)
- ✅ STT failure handling: graceful fallback to manual input
- ✅ Metrics: capture latency, VAD time, STT time, e2e latency logged

**Session Management**:
- ✅ Mode persists during Claude CLI session
- ✅ Mode resets to "default" on Claude CLI exit
- ✅ last_transcription cleared on new voice input
- ✅ No conversation history stored
- ✅ Session state in-memory only (no persistence)

**Command Grammar & Safety**:
- ✅ Command parser: exact/prefix match only
- ✅ Case-insensitive, whitespace-flexible
- ✅ Safety scan: keyword detection (file, git, DB, system)
- ✅ Safety scan: voice input only (NOT command parsing)
- ✅ Confirmation: explicit Y/N key (no voice confirmation)
- ✅ All 6 commands functional: kirim, ulang, mode, help (+ placeholders for ringkas, jelaskan)

**Integration**:
- ✅ Audio pipeline → text delivery to Claude CLI
- ✅ Command processing returns UI feedback
- ✅ Mode affects prompt shaping (text wrapping)
- ✅ Error handling: clear messages, no silent failures

---

## Known Deferred Items (Phase 2+)

**Streaming STT** (Phase 2):
- Currently: buffer entire utterance before STT
- Phase 2: stream audio to Whisper, reduce latency for long queries
- Rationale: complexity vs. MVP scope trade-off

**Cloud STT Fallback** (Phase 2):
- Currently: local Whisper only
- Phase 2: API fallback if local crashes (with user awareness)
- Rationale: offline capability in MVP

**ringkas/jelaskan Commands** (Phase 2):
- Currently: placeholder "Not yet implemented"
- Phase 2: integrate with Claude or auxiliary LLM
- Rationale: MVP scope simplicity

**Session Persistence** (Phase 2):
- Currently: state dies with Claude CLI
- Phase 2: optional session recovery (nice-to-have)
- Rationale: simplicity, privacy (no stored state)

**Launcher** (Phase 2+):
- Currently: none (runtime-only)
- Phase 2: thin launcher for licensing, updates, distribution
- Rationale: game launcher model

---

## Governance

**This Layer 0 is LOCKED.**

No changes to foundational concepts without explicit architecture approval.

Minor clarifications (like the two applied here) are acceptable if they don't change design.

Suggested feature additions (streaming STT, cloud fallback, etc.) are Phase 2 or later.

---

## Architecture Readiness Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| Core concepts (DEC-001, 002, 003) | ✅ LOCKED | All three docs finalized |
| Clarifications applied | ✅ 2/2 | Utterance scope, safety scan scope |
| Game launcher compatibility | ✅ CONFIRMED | No network in critical path |
| Phase 1 scope | ✅ CLEAR | Audio, state, commands, safety |
| Deferred items | ✅ CLEAR | Streaming STT, cloud, launcher in Phase 2 |
| Success criteria | ✅ DEFINED | Latency SLA, command parsing, safety gates |

---

## Next Steps: Layer 1 Design

Ready to proceed to **JARVIS-LAY1** (Contracts):

1. **JARVIS-LAY1-001**: Audio Input & Command Contracts
2. **JARVIS-LAY1-002**: State & Mode Contracts
3. **JARVIS-LAY1-003**: Safety & Confirmation Contracts

---

**Status**: LAYER 0 COMPLETE & LOCKED
**Approval**: Lead Architect
**Date**: 2025-12-28

Proceed with confidence. Layer 0 is fully specified and ready for Layer 1 design.

