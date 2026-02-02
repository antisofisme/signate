# JARVIS Reference Implementation Skeleton

**Status**: ✅ READY FOR IMPLEMENTATION
**Date**: 2025-12-28
**Scope**: Code structure template (zero logic, pure contracts)

---

## What Was Delivered

### 1. Complete Component Classes (11 files)

```
jarvis/components/
├── main_loop.py             → MainLoopOrchestrator (coordinator)
├── hotkey_listener.py       → HotkeyListener (signal-only thread)
├── audio_capture.py         → AudioCapture (blocking audio)
├── stt_adapter.py           → STTAdapter (blocking STT, never async)
├── input_boundary.py        → InputBoundary (deterministic classifier)
├── command_executor.py      → CommandExecutor (atomic command runner)
├── safety_gate.py           → SafetyGate (keyword detection + dialog)
├── prompt_shaper.py         → PromptShaper (lookup + concat)
├── cli_adapter.py           → CLIAdapter (fire-and-forget)
├── ui_notifier.py           → UINotifier (display-only)
└── session_state.py         → SessionState (data holder)
```

**What each file contains**:
- Class definition with detailed docstring
- Initialization method (empty, no logic)
- All required methods with signatures
- Docstrings explaining contracts (what NOT to do)
- References to architecture documents (Layer 0-3)
- Raises statements for errors (no try/catch implementation)

### 2. Data Models (4 files)

```
jarvis/models/
├── input_models.py          → InputEvent, InputRejected, AudioBuffer, etc.
├── result_models.py         → CommandResult, ExecutionResult
├── signal_models.py         → Toast, Dialog, ErrorDisplay (UI signals)
└── session_models.py        → SessionState (data + validation methods)
```

**What each file contains**:
- @dataclass definitions with field types
- Type hints (int, str, Optional, Union, etc.)
- Docstrings explaining purpose
- Validation methods (update_mode, record_error, etc.)
- Enum definitions (SignalLevel, InputType, etc.)

### 3. Exception Hierarchy (2 files)

```
jarvis/exceptions/
├── jarvis_exceptions.py     → 11 custom exceptions
└── __init__.py              → Re-exports
```

**Exceptions defined**:
- `JarvisException` (base)
- `AudioCaptureError`
- `STTError`, `STTTimeoutError`, `STTConfidenceError`
- `InputClassificationError`
- `SafetyGateError`
- `PromptShapingError`
- `CommandExecutionError`
- `CLIInteractionError`
- `JarvisInternalError`

Each exception:
- Inherits from JarvisException
- Has user-facing message
- Has optional recovery_hint
- Carries context (e.g., confidence score for STT)

### 4. Entry Point (1 file)

```
jarvis/main.py              → Component initialization + main loop start
```

**What it does**:
- Initializes all 11 components
- Creates hotkey listener thread
- Wires components into MainLoop
- Starts listener thread
- Calls main_loop.run()
- Handles Ctrl+C gracefully

### 5. Documentation (2 files)

```
README_IMPLEMENTATION.md     → Step-by-step implementation guide
REFERENCE_IMPLEMENTATION_SKELETON.md → This file (what was delivered)
```

---

## File Structure Complete

```
jarvis/
├── __init__.py              ✅ Package init (imports MainLoop, SessionState)
├── main.py                  ✅ Entry point
│
├── components/              ✅
│   ├── __init__.py
│   ├── main_loop.py
│   ├── hotkey_listener.py
│   ├── audio_capture.py
│   ├── stt_adapter.py
│   ├── input_boundary.py
│   ├── command_executor.py
│   ├── safety_gate.py
│   ├── prompt_shaper.py
│   ├── cli_adapter.py
│   ├── ui_notifier.py
│   └── session_state.py
│
├── models/                  ✅
│   ├── __init__.py
│   ├── input_models.py
│   ├── result_models.py
│   ├── signal_models.py
│   └── session_models.py
│
├── exceptions/              ✅
│   ├── __init__.py
│   └── jarvis_exceptions.py
│
└── config/                  ⏳ (Optional: create if needed)
    └── settings.py
```

---

## Key Design Patterns Baked In

### 1. **No Logic = No Implementation Debt**

Every method raises `NotImplementedError` with comment "Implementation needed".

This forces implementor to:
- Read docstring (contract)
- Understand what NOT to do
- Make conscious implementation choice
- Can't accidentally add forgotten logic

### 2. **Docstrings Are Contracts**

Every class and method docstring includes:
- Purpose (what it does)
- Contract (what it MUST do)
- Anti-patterns (what it MUST NOT do)
- References to architecture docs

**Example**:
```python
def transcribe(self, audio: AudioBuffer) -> str:
    """
    BLOCKING: Synchronous signature (no async)
    DETERMINISTIC: Same audio → same transcript
    NO RETRY: Caller decides retry

    See JARVIS-L3-ARCH-002 for blocking justification
    """
    raise NotImplementedError("Implementation needed")
```

### 3. **Type Hints = Architectural Enforcement**

Component signatures enforce contracts via type system:

```python
# ✅ CORRECT: STT blocks (returns str, not Task)
def transcribe(self, audio: AudioBuffer) -> str:
    ...

# ❌ WRONG: Would violate contracts
def transcribe(self, audio: AudioBuffer) -> asyncio.Task[str]:
    ...
```

Implementor cannot accidentally make STT async without changing signature.

### 4. **Threading Separation Is Structural**

MainLoop and HotkeyListener are separate classes:
- Different modules
- Different purposes
- Different initialization
- HotkeyListener has NO access to SessionState

No way to accidentally share state between threads.

### 5. **Models Are Pure Data**

All models are @dataclass:
- No logic
- Field-based
- Type-checked
- Validation methods separate (not constructor side-effects)

### 6. **Exceptions Carry Context**

Exceptions aren't just error messages:

```python
class STTTimeoutError(STTError):
    def __init__(self, timeout_ms: int, max_allowed_ms: int = 1000):
        self.timeout_ms = timeout_ms
        self.max_allowed_ms = max_allowed_ms
        message = "STT failed. Please try again or type instead."
        super().__init__(message)
```

Caller can log context (how much was exceeded) without showing tech details to user.

---

## Skeleton Properties

### Zero Logic ✅
- All methods raise `NotImplementedError`
- No business logic in skeleton
- No "helpful" default implementations
- Pure structure only

### Architecturally Sound ✅
- Component boundaries match L3-ARCH-001
- Threading separation matches L3-ARCH-002
- Signal types match L3-ARCH-003
- All contracts documented in docstrings

### Type-Safe ✅
- Full type hints (int, str, Optional, Union, etc.)
- Type system enforces constraints (e.g., STT signature prevents async)
- Data models are type-checked
- Can run mypy/pyright immediately

### Handoff-Ready ✅
- No ambiguity (contracts in code)
- No design decisions left to decide
- Clear implementation checklist in README
- Test suggestions in README

---

## How to Use This Skeleton

### For Implementation

1. **Read docstrings carefully** (they are contracts, not suggestions)
2. **Follow implementation checklist** (README_IMPLEMENTATION.md, Phase 1-5)
3. **Replace `NotImplementedError` with actual code**
4. **Run tests against contracts** (not just functional tests)
5. **Check against architecture docs** (any deviation = bug)

### For Code Review

1. **Verify docstring contracts are met** (not just "does it work")
2. **Check threading rules** (only MainLoop mutates state)
3. **Verify error handling** (explicit messages, no silent errors)
4. **Check blocking decisions** (STT/audio must block)
5. **Reference architecture documents** (links in docstrings)

### For Testing

1. **Unit test each component** (pure functions deterministic?)
2. **Integration test flows** (voice, command, error paths)
3. **End-to-end test** (audio → Claude)
4. **Architecture compliance** (Layer 1-3 contracts met?)
5. **Threading test** (no race conditions?)

---

## What Happens Next

With skeleton complete:

### Phase 1: Fill In Methods
- Implement each method body
- Follow docstring contracts
- No design decisions needed (already made)
- Write unit tests per component

### Phase 2: Integration Testing
- Voice input → Claude
- Command input → Mode change
- Error cases → Correct messages
- Threading → No deadlock/race

### Phase 3: Deployment
- Package as .whl or .egg
- Distribute via game launcher
- Local-first (no SaaS in critical path)
- Can fail gracefully

---

## Architectural Guarantees Maintained

| Aspect | How Enforced |
|--------|-------------|
| Determinism | Pure functions only, signatures prevent async |
| No autonomy | Docstrings forbid auto-retry, recovery |
| Fire-and-forget | CLIAdapter signature returns None immediately |
| Single-writer | MainLoop owns state, others signal-only |
| Blocking by design | STT signature is sync, not async |
| Explicit failure | Exceptions carry user-facing messages |
| No silent errors | All errors are explicit (no try/catch hiding) |
| No persistence | SessionState resets per CLI restart |

---

## Summary

**Skeleton is production-ready** in the sense that:

✅ **No ambiguity**: All architectural decisions are made
✅ **No design during coding**: Structure enforces decisions
✅ **No logic debt**: Empty methods force conscious implementation
✅ **No surprise violations**: Type system + docstrings prevent accidents
✅ **Ready for handoff**: Clear checklist, references, and contracts

**From here**: Implementation is straightforward coding. No more architecture debates. Just wire contracts into code.

---

**Skeleton Complete. Ready for Implementation. 🚀**

