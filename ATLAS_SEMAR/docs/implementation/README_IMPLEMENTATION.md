# JARVIS Implementation Guide

## Status

**Architecture**: LOCKED (Layers 0-3)
**Code Structure**: Reference skeleton ready
**Implementation**: Next phase (fill in methods)

---

## What This Skeleton Provides

```
jarvis/
├── __init__.py
├── main.py (entry point, component initialization)
│
├── components/
│   ├── main_loop.py → MainLoopOrchestrator
│   ├── hotkey_listener.py → HotkeyListener
│   ├── audio_capture.py → AudioCapture
│   ├── stt_adapter.py → STTAdapter
│   ├── input_boundary.py → InputBoundary
│   ├── command_executor.py → CommandExecutor
│   ├── safety_gate.py → SafetyGate
│   ├── prompt_shaper.py → PromptShaper
│   ├── cli_adapter.py → CLIAdapter
│   ├── ui_notifier.py → UINotifier
│   └── session_state.py → SessionState
│
├── models/
│   ├── input_models.py (InputEvent, InputRejected, etc.)
│   ├── result_models.py (CommandResult, ExecutionResult)
│   ├── signal_models.py (Toast, Dialog, ErrorDisplay)
│   └── session_models.py (SessionState data)
│
├── exceptions/
│   ├── jarvis_exceptions.py (all custom exceptions)
│   └── __init__.py
│
└── config/
    └── settings.py (constants, configuration)
```

## What Each File Contains

### Components

Each component has:
- Class definition with docstring (contract)
- `__init__` (initialization, no logic)
- Method signatures (no implementation)
- Detailed docstrings (what NOT to do, why)
- References to architecture documents

**Example: STTAdapter**
```python
class STTAdapter:
    """Contract: BLOCKING, SYNCHRONOUS, DETERMINISTIC"""

    def transcribe(self, audio: AudioBuffer) -> str:
        """
        Blocks until STT returns.
        Same audio → same transcript (every time).
        Cannot be async (violates Layer 1-DEC-005).
        """
        raise NotImplementedError("Implementation needed")
```

### Models

Pure data classes with:
- Field definitions
- Type hints
- Docstring explaining contract
- Validation methods (if applicable)

**Example: SessionState**
```python
@dataclass
class SessionState:
    """Owned by MainLoop (exclusive write)"""
    mode: str = "default"
    last_transcription: Optional[str] = None
    input_count: int = 0

    def update_mode(self, new_mode: str) -> None:
        """MainLoop calls this. Only MainLoop can mutate."""
        ...
```

### Exceptions

All exceptions inherit from `JarvisException`:
- `AudioCaptureError`
- `STTError`, `STTTimeoutError`, `STTConfidenceError`
- `InputClassificationError`
- `SafetyGateError`
- `CommandExecutionError`
- `PromptShapingError`
- `CLIInteractionError`
- `JarvisInternalError`

Each exception carries user-facing message + recovery hint.

---

## Implementation Checklist

### Phase 1: Core Loop (MainLoop + HotkeyListener)

- [ ] **HotkeyListener.run()**: Infinite loop detecting hotkey, calling event.set()
  - Use `pynput` or `keyboard` library
  - Hotkey: F12 (configurable)
  - Event: `threading.Event` (provided by MainLoop)

- [ ] **MainLoop.run()**: Orchestration loop
  - Wait for hotkey signal (event.wait())
  - Call AudioCapture.capture()
  - Call STTAdapter.transcribe()
  - Call InputBoundary.classify()
  - Route: command vs voice
  - Update SessionState
  - Loop back

### Phase 2: Input Processing (Boundaries)

- [ ] **AudioCapture.capture()**: Synchronous audio recording
  - Use `sounddevice` or `pyaudio`
  - Record while hotkey held
  - VAD timeout: 1.5s silence
  - Duration ceiling: 120s
  - Return AudioBuffer

- [ ] **STTAdapter.transcribe()**: Whisper local
  - Load model `openai-whisper`
  - Synchronous (no async)
  - Timeout: 1000ms
  - Confidence check: > 0.5
  - Return transcript or raise STTError

- [ ] **InputBoundary.classify()**: Grammar matching
  - Normalize text (strip, lowercase)
  - Detect commands: kirim, ulang, mode, help
  - Validate mode: default, coding, debug, explain
  - Return InputEvent or InputRejected

### Phase 3: Safety & Shaping (Voice Path)

- [ ] **SafetyGate.contains_danger()**: Keyword detection
  - Patterns: rm -rf, DROP TABLE, git reset, killall
  - Returns True/False

- [ ] **SafetyGate.show_confirmation()**: Dialog
  - Use `tkinter` or `zenity` for dialog
  - Show pattern + user's text
  - Wait for Y/N (no timeout)
  - Return True/False

- [ ] **PromptShaper.shape()**: Lookup + concat
  - Map: mode → prefix
  - Concat: prefix + text
  - Return shaped prompt

### Phase 4: Command Execution (Command Path)

- [ ] **CommandExecutor.execute()**: Run command
  - kirim: Press Enter (via xdotool)
  - ulang: Resend last transcription
  - mode: Change SessionState.mode
  - help: Show help text
  - Return CommandResult

### Phase 5: CLI & UI (Output)

- [ ] **CLIAdapter.send_to_claude()**: Keyboard simulation
  - Use `xdotool` (Linux) or `pyautogui` (cross-platform)
  - Insert text + press Enter
  - Fire-and-forget (return immediately)

- [ ] **UINotifier.display()**: Message display
  - Toast: Show briefly, return None
  - Dialog: Block until response, return bool
  - Error: Show with recovery hint
  - Use `tkinter`, `PyQt`, or terminal notifications

---

## Architectural Rules (Must Enforce)

### ✅ DO

- [ ] MainLoop blocks on audio and STT (intentional)
- [ ] HotkeyListener only signals (no state access)
- [ ] SessionState mutations ONLY in MainLoop
- [ ] All pure functions are deterministic
- [ ] Errors are explicit (user sees message)
- [ ] Fire-and-forget CLI (no monitoring)
- [ ] Dialogs block until user responds
- [ ] Commands skip safety gate (absolute path)

### ❌ DON'T

- [ ] Async STT (violates Layer 1-DEC-005)
- [ ] Auto-retry on failure (user decides)
- [ ] Silent error handling (all explicit)
- [ ] Cache fallback (no secondary memory)
- [ ] HotkeyListener logic (signal-only)
- [ ] Monitoring Claude output
- [ ] Auto-mode-change based on content
- [ ] Persistent state across CLI restart

---

## Testing Checklist

### Unit Tests (Components)

- [ ] **InputBoundary**: Same text → same classification
- [ ] **PromptShaper**: Same (text, mode) → same output
- [ ] **CommandExecutor**: Valid args → CommandResult
- [ ] **SafetyGate**: Pattern detection works
- [ ] **SessionState**: Mode changes recorded

### Integration Tests (Flow)

- [ ] **Voice input**: Audio → STT → Classification → Safety → Shaping → CLI
- [ ] **Command input**: Audio → Classification → Executor → CLI
- [ ] **Error handling**: Invalid input → Error message displayed
- [ ] **Threading**: HotkeyListener doesn't block MainLoop

### End-to-End Tests

- [ ] [ ] User says "hello world" → arrives at Claude
- [ ] [ ] User says "mode coding" → mode changed, confirmed
- [ ] [ ] User says "rm -rf /" → safety dialog appears
- [ ] [ ] User presses N on safety → cancelled
- [ ] [ ] STT timeout → error message shown
- [ ] [ ] Jarvis restart → session cleared

---

## Configuration (settings.py)

```python
# Audio
SAMPLE_RATE = 16000
AUDIO_DEVICE = None  # Auto-detect

# STT
STT_MODEL = "base"  # tiny, base, small, medium, large
STT_LANGUAGE = "en"
STT_TIMEOUT_MS = 1000
STT_CONFIDENCE_THRESHOLD = 0.5

# Hotkey
HOTKEY_KEY = "f12"

# VAD
VAD_TIMEOUT_MS = 1500  # 1.5s silence
DURATION_CEILING_MS = 120000  # 120s max

# UI
TOAST_DURATION_MS = 3000
DIALOG_TIMEOUT_MS = None  # No timeout (user controls)

# Commands
VALID_MODES = ["default", "coding", "debug", "explain"]
```

---

## Architecture References

When implementing, check these documents:

| Phase | Document | Key Point |
|-------|----------|-----------|
| Core | JARVIS-L2-ARCH-001 | Main loop pseudocode |
| Audio | JARVIS-DEC-001 | Latency SLA, VAD timing |
| STT | JARVIS-L3-ARCH-002 | MUST be blocking |
| Safety | JARVIS-DEC-003 | Keyword patterns |
| Error | JARVIS-L3-ARCH-003 | Signal types (Toast vs Dialog) |
| Threading | JARVIS-L3-ARCH-002 | MainLoop ownership |

---

## Common Pitfalls to Avoid

1. **Async STT temptation**: "Let's make STT async for responsiveness"
   - ❌ WRONG: Violates JARVIS-L3-ARCH-002 (breaks determinism)
   - ✅ RIGHT: Keep synchronous blocking (by design)

2. **Auto-retry on error**: "Let's retry STT if it times out"
   - ❌ WRONG: Violates JARVIS-L1-DEC-005 (hidden retry loop)
   - ✅ RIGHT: Explicit error message, user decides retry

3. **HotkeyListener processing**: "Let's capture audio in hotkey thread"
   - ❌ WRONG: Violates JARVIS-L3-ARCH-002 (thread violations)
   - ✅ RIGHT: Signal-only, MainLoop does capture

4. **Persistent state**: "Save mode/session to recover on crash"
   - ❌ WRONG: Violates JARVIS-DEC-002 (single-session law)
   - ✅ RIGHT: Fresh start every Claude CLI restart

5. **Context-aware prompting**: "Adjust prefix based on conversation"
   - ❌ WRONG: Violates JARVIS-L1-DEC-003 (mechanical wrapping)
   - ✅ RIGHT: Fixed mode → prefix, deterministic

---

## Ready to Implement

This skeleton provides:
- ✅ Clear component boundaries
- ✅ Method signatures aligned with architecture
- ✅ Docstrings with contracts (what NOT to do)
- ✅ Exception hierarchy
- ✅ Data models with validation
- ✅ No logic (pure structure)

All architectural decisions are made. Implementation is now straightforward:
1. Fill in method bodies
2. Follow docstring contracts
3. Write tests for each component
4. Verify against architecture docs
5. Deploy with confidence

---

**No ambiguity. No design decisions during coding. Just wiring.**

