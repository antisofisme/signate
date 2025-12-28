# JARVIS LAYER 1: DEC-001 & DEC-002 LOCKED

**Status**: ✅ LOCKED FOR L1-DEC-003
**Date**: 2025-12-28
**Approval**: Both documents reviewed, clarifications applied

---

## Pre-Lock Summary

### ✅ JARVIS-L1-DEC-001: Input Contract (LOCKED)

**Clarifications Applied**:

1. **Duration ceiling consistency** (120s vs <10s scope):
   - Added: "technical ceiling; utterances >10s are considered degraded UX"
   - Preserves Layer 0 law while allowing technical maximum

2. **STT confidence < 0.5** (no auto-retry):
   - Changed: "display warning and ask user to repeat or type manually (no auto-retry)"
   - Enforces Layer 0 constraint: no background decision making

3. **Input boundary principle** (fast, side-effect free, idempotent):
   - Added: "Input boundary must be fast, side-effect free, and idempotent"
   - Prevents future logic creep at boundary

**Contracts Defined**:
- VoiceInput: transcribed text, duration, confidence
- CommandInput: parsed command with arguments
- KeyboardInput: fallback from STT failure or manual typing
- InputEvent: success output (type, text, routing)
- InputRejected: failure output (reason, recovery action)

**Key Guarantees**:
- Input classification is deterministic
- Rejection includes recovery action (not silent)
- Routing to next stage determined at boundary
- No semantic processing at input boundary

---

### ✅ JARVIS-L1-DEC-002: Command Execution Boundary (LOCKED)

**Clarification Applied**:

1. **Re-classification responsibility** (input boundary vs executor):
   - Clarified: Input Boundary determines if input is valid command
   - Executor assumes input already classified correctly
   - Invalid command → executor returns error, not re-route
   - Re-classification to VoiceInput happens at Input Boundary, not inside executor

**Contracts Defined**:
- CommandInput → command_executor (direct path)
- VoiceInput → safety_gate → prompt_shaper → Claude (indirect path)
- 6 command types: kirim, ulang, mode, help, ringkas (Phase 2), jelaskan (Phase 2)
- CommandResult: success flag, display message, side effects

**Key Guarantees**:
- Commands NEVER go through safety gate
- Commands NEVER get wrapped with mode
- Commands NEVER sent to Claude as text input
- Command execution is atomic (completes before next input)
- Invalid commands return error result (clear feedback)
- Invalid command arguments handled by executor (error return)

---

## Layer 1 Architectural Summary

### Input Flow (Contract)

```
User Input (voice, keyboard, command)
    ↓
LAYER 1: INPUT BOUNDARY (L1-DEC-001)
  • Normalize & classify
  • Validate type-specific rules
  • Create InputEvent or InputRejected
  • Determine routing
    ↓
    ├─ CommandInput → LAYER 1: COMMAND EXECUTION (L1-DEC-002)
    │                  • Execute directly
    │                  • Skip safety gate
    │                  • Return CommandResult
    │
    └─ VoiceInput/KeyboardInput → LAYER 2+ (will define)
                                   • Safety gate
                                   • Prompt shaping
                                   • Claude CLI
```

### Responsibility Boundaries

| Stage | Responsibility | Allowed | Forbidden |
|-------|----------------|---------|-----------|
| Input Boundary (L1-001) | Classify, validate, route | Normalization, rule checking | Semantic processing, execution |
| Command Executor (L1-002) | Execute commands, return results | Command-specific logic, state updates | Safety scan, mode wrapping, CLI text send |
| Voice Path (L2+) | Safety & prompt wraping | Safety detection, mode application | Command execution, input re-routing |

---

## Consistency Checks

### ✅ Layer 0 → Layer 1 Consistency

| Layer 0 Law | Layer 1 Enforcement |
|------------|-------------------|
| Push-to-talk hotkey | Input Boundary completes on hotkey release |
| Latency ≤ 2s, optimized <10s | Input Boundary fast, no semantic processing |
| Command grammar strict, deterministic | Input Boundary uses exact/prefix grammar |
| Safety gates for voice only | Command Executor skips safety gate |
| No persistent memory | InputEvent is transient, no storage |
| Mode as local state | Command executor updates session.mode directly |
| Command ≠ voice input | Absolute path separation at boundary |

### ✅ Game Launcher Model Safety

- ❌ No authentication at input boundary
- ❌ No license checking in command executor
- ❌ No tenant model in contracts
- ❌ No network dependency
- ❌ No cloud assumptions

**Implication**: Launcher can wrap this without touching Layer 1.

---

## Locked Contracts (IMMUTABLE)

### Contract 1: Input Classification is Deterministic
```
Same input text → same InputEvent type (100% determinism)
No fuzzy matching, no context-dependent classification
```

### Contract 2: Command Path is Absolute
```
CommandInput ONLY routes to command_executor
NEVER through safety_gate
NEVER to Claude CLI as text
NEVER wrapped with mode
```

### Contract 3: Input Boundary is Thin
```
Classify, validate, route.
No execution, no decision-making, no side effects.
All processing fast, idempotent, side-effect free.
```

### Contract 4: Command Execution is Atomic
```
Command completes or fails entirely.
No partial state changes.
No cascading to next input.
```

### Contract 5: Failure is Explicit
```
All rejection/error has recovery action.
No silent failures.
No ambiguous error messages.
```

---

## Known Deferred (Phase 2+)

- ringkas, jelaskan commands (Phase 2 placeholder)
- Streaming STT (for long utterances, Phase 2)
- Cloud STT fallback (Phase 2)
- Session persistence (Phase 2)
- Launcher integration (Phase 2+)
- Custom command definitions (Phase 2+)

---

## Phase 1 Success Criteria

Before Layer 2, verify:

**Input Boundary (L1-DEC-001)**:
- ✅ VoiceInput: duration 300-120000ms, confidence metric, no garbling
- ✅ CommandInput: exact/prefix match only, mode argument validated
- ✅ KeyboardInput: no empty text, UTF-8 clean
- ✅ Routing: commands to executor, voice to gate (clear routing)
- ✅ Errors: all rejections include recovery action

**Command Execution (L1-DEC-002)**:
- ✅ kirim: press Enter, no text sent to Claude
- ✅ ulang: resend last transcription with new Enter
- ✅ mode: validate argument, update session state, display feedback
- ✅ help: display help overlay
- ✅ ringkas, jelaskan: Phase 2 placeholder (not yet implemented)
- ✅ Error handling: invalid command returns error result

**Contract Enforcement**:
- ✅ Commands NEVER scanned for safety
- ✅ Commands NEVER wrapped with mode
- ✅ Commands NEVER sent to Claude
- ✅ Invalid commands return error (don't re-route)
- ✅ Re-classification to voice happens at input boundary, not executor

---

## Governance

**These contracts are LOCKED.**

No changes to:
- Input classification determinism
- Command path separation
- Input boundary thinness
- Command atomicity
- Explicit failure handling

Minor clarifications (like those applied) are acceptable if they don't weaken guarantees.

Feature additions (Phase 2 commands, retry logic, context-aware routing) are deferred.

---

## Readiness for Layer 1-DEC-003

Layer 1 foundation is solid:
- ✅ Input contracts clear
- ✅ Command contracts clear
- ✅ Responsibility boundaries defined
- ✅ No SaaS leakage
- ✅ No hidden intelligence

**Next challenge**: Prompt Shaping Contract (L1-DEC-003)

This is where the biggest temptation for "hidden intelligence" appears. If Jarvis can remain simple and deterministic here, the foundation is truly unbreakable.

---

**Status**: LAYER 1 PARTIAL LOCK (DEC-001, 002 LOCKED, 003-005 PENDING)
**Approval**: Lead Architect
**Date**: 2025-12-28

Proceed to L1-DEC-003 with confidence. Foundation is solid.

