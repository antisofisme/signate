# JARVIS-L3-ARCH-001: Component Decomposition

**Status**: DRAFT (awaiting review)
**Date**: 2025-12-28
**Scope**: Layer 3 - Component Design & State Ownership

---

## Purpose

Define **all Jarvis components**, **who owns what state**, and **which functions are pure vs have side effects**.

This is the last place design prevents implementation mistakes. After this, code is code. So this document must be unambiguous enough that no one can "interpret creatively."

Key principle: **Every component has one responsibility. Every state mutation is traceable to one owner.**

---

## Component Inventory

### 10 Core Components

```
1. MainLoop              (orchestrates all)
2. HotkeyListener        (detects hotkey, signals main loop)
3. AudioCapture          (records voice)
4. STTAdapter            (wraps Whisper)
5. InputBoundary         (classifies input)
6. CommandExecutor       (executes commands)
7. SafetyGate            (scans for danger)
8. PromptShaper          (wraps text with prefix)
9. CLIAdapter            (sends to Claude CLI)
10. UINotifier           (displays messages to user)
```

Plus 1 shared resource:
```
11. SessionState         (mutable session data)
```

---

## Component Responsibilities & Ownership

### Component 1: MainLoop

**Responsibility**: Orchestrate all other components

**Type**: Coordinator (owns state mutations)

**Owns**:
- Session state
- Control flow

**Is Pure**: ❌ NO (coordinates side effects)

**Side Effects**: ✅ YES (many, but orchestrated)

**Thread**: Main thread ONLY

**Allowed Operations**:
- Call other components
- Mutate SessionState
- Display errors via UINotifier
- Make routing decisions

**Forbidden Operations**:
- ❌ Read/write terminal directly
- ❌ Call external services
- ❌ Modify component state
- ❌ Access hotkey listener internals

```python
class MainLoop:
    """Orchestrator, runs in main thread"""

    def __init__(self, session):
        self.session = session  # owns reference, mutates

    def run(self):
        while self.is_claude_alive():
            signal = self.wait_for_input()  # blocking
            event = self.input_boundary.classify(signal)  # pure

            if event.type == "command":
                result = self.command_executor.execute(event)
                self.ui_notifier.display(result.display)
            elif event.type == "voice":
                # ... process voice

            # Loop continues
```

---

### Component 2: HotkeyListener

**Responsibility**: Detect hotkey, signal main loop

**Type**: Event source (signal-only)

**Owns**: Nothing

**Is Pure**: ✅ YES (only side effect: signal)

**Side Effects**: Signal only (no state mutation)

**Thread**: Separate thread (background)

**Allowed Operations**:
- Detect hotkey press/release
- Signal main loop (thread-safe queue/event)
- Nothing else

**Forbidden Operations**:
- ❌ Mutate any state
- ❌ Process audio
- ❌ Call main loop directly
- ❌ Read SessionState
- ❌ Blocking operations (except for OS hotkey listener)

```python
class HotkeyListener:
    """Runs in background thread, signal-only"""

    def __init__(self, signal_queue):
        self.signal_queue = signal_queue  # thread-safe queue

    def start(self):
        # Register OS hotkey listener
        register_hotkey(F12, callback=self.on_hotkey_press)

    def on_hotkey_press(self):
        # ONLY action: put signal in queue
        self.signal_queue.put({"event": "hotkey_down"})

    def on_hotkey_release(self):
        self.signal_queue.put({"event": "hotkey_up"})

    # No other methods
```

---

### Component 3: AudioCapture

**Responsibility**: Record audio from hotkey press to release/silence

**Type**: Input source (semi-pure)

**Owns**: Temporary audio buffer (discarded after use)

**Is Pure**: ✅ YES (same audio → same buffer output)

**Side Effects**: Reads from microphone only

**Thread**: Main thread (blocking during capture)

**Allowed Operations**:
- Start recording on signal
- Accumulate audio frames
- Apply VAD (silence detection)
- Return audio buffer

**Forbidden Operations**:
- ❌ Store audio after return
- ❌ Retry on failure (return error instead)
- ❌ Call STT directly
- ❌ Mutate state

```python
class AudioCapture:
    """Captures audio synchronously"""

    def capture(self, timeout_ms=120000):
        """
        Blocks until hotkey release or timeout.
        Returns audio buffer or raises AudioError.
        """
        audio_buffer = []

        while True:
            # Wait for hotkey up or VAD timeout
            if hotkey_released() or vad_timeout():
                return AudioBuffer(audio_buffer)  # immutable

            frames = self.microphone.read()
            audio_buffer.extend(frames)

    # Pure function: no state mutation
```

---

### Component 4: STTAdapter

**Responsibility**: Convert audio to text using Whisper

**Type**: Translator (pure, synchronous)

**Owns**: Nothing

**Is Pure**: ✅ YES (same audio → same transcript)

**Side Effects**: Calls Whisper process

**Thread**: Main thread (blocking)

**Allowed Operations**:
- Load Whisper model (once, at startup)
- Process audio → text
- Return transcript or raise STTError

**Forbidden Operations**:
- ❌ Retry on timeout (raise error, let caller handle)
- ❌ Mutate state
- ❌ Cache results
- ❌ Call external APIs without error handling

```python
class STTAdapter:
    """Synchronous STT wrapper"""

    def __init__(self):
        self.model = self._load_whisper()  # once

    def transcribe(self, audio_buffer):
        """
        Blocks until Whisper returns.
        Returns transcript string or raises STTError.
        """
        try:
            result = self.model.transcribe(
                audio_buffer,
                timeout=800  # 800ms max
            )
            return result["text"]
        except Exception as e:
            raise STTError(str(e))

    # Pure: same input → same output or same error
```

---

### Component 5: InputBoundary

**Responsibility**: Classify input (voice, command, keyboard)

**Type**: Classifier (pure)

**Owns**: Nothing

**Is Pure**: ✅ YES (same input → same classification)

**Side Effects**: None

**Thread**: Main thread (fast)

**Allowed Operations**:
- Normalize text (whitespace, case, encoding)
- Match against command grammar
- Validate input rules
- Return InputEvent or InputRejected

**Forbidden Operations**:
- ❌ Semantic interpretation
- ❌ State mutation
- ❌ Side effects
- ❌ External calls

```python
class InputBoundary:
    """Pure classifier"""

    def classify(self, signal):
        """
        signal: dict with type and content
        returns: InputEvent or InputRejected

        Pure function: no side effects.
        """
        text = signal["content"]
        normalized = self._normalize(text)

        # Try command match
        if self._matches_command(normalized):
            return self._classify_as_command(normalized)

        # Voice input
        return self._classify_as_voice(normalized)

    def _normalize(self, text):
        """Pure: trim, lowercase, etc"""
        return text.strip().lower()

    def _matches_command(self, text):
        """Pure: exact/prefix match only"""
        return text in COMMAND_NAMES or any(...)
```

---

### Component 6: CommandExecutor

**Responsibility**: Execute commands (kirim, mode, help, etc.)

**Type**: Executor (mutates session state only)

**Owns**: None (MainLoop owns SessionState, passes it)

**Is Pure**: ❌ NO (mutates session via MainLoop)

**Side Effects**: State mutation + UI signaling

**Thread**: Main thread only

**Allowed Operations**:
- Execute command logic (check arguments, etc.)
- Return CommandResult
- Request MainLoop to mutate state (return result with mutation instruction)

**Forbidden Operations**:
- ❌ Directly mutate any state
- ❌ Call other components
- ❌ Call CLI adapter
- ❌ Retry on error

```python
class CommandExecutor:
    """Executes commands, returns result"""

    def execute(self, command_input):
        """
        Returns CommandResult with success flag and optional state mutation.
        MainLoop applies mutations.
        """
        if command_input.command == "mode":
            mode = command_input.arguments["mode"]
            if mode in VALID_MODES:
                return CommandResult(
                    success=True,
                    display=f"Mode: {mode}",
                    state_mutation={"mode": mode}  # MainLoop applies this
                )
            else:
                return CommandResult(
                    success=False,
                    display=f"Unknown mode: {mode}"
                )

        # No state mutation here - result only
```

---

### Component 7: SafetyGate

**Responsibility**: Scan voice input for dangerous patterns

**Type**: Validator (pure + UI interaction for confirmation)

**Owns**: Nothing

**Is Pure**: ✅ YES (same input → same danger detection)

**Side Effects**: Calls UINotifier for confirmation dialog

**Thread**: Main thread (blocks for user confirmation)

**Allowed Operations**:
- Scan text for patterns (pure)
- Request user confirmation (via UINotifier)
- Return approved or rejected

**Forbidden Operations**:
- ❌ Auto-reject without confirmation
- ❌ Auto-approve dangerous patterns
- ❌ Retry on user rejection
- ❌ Mutate state

```python
class SafetyGate:
    """Pattern scanner + confirmation"""

    def check(self, text, ui_notifier):
        """
        Returns: (is_safe, approved)
          - is_safe: bool (True if no dangerous patterns)
          - approved: bool (True if user approved dangerous text)
        """
        danger_pattern = self._scan(text)

        if not danger_pattern:
            return (True, True)  # safe, no confirmation needed

        # Dangerous pattern found
        confirmed = ui_notifier.ask_confirmation(danger_pattern)
        return (False, confirmed)

    def _scan(self, text):
        """Pure: return pattern or None"""
        patterns = ["rm -rf", "DROP TABLE", ...]
        for pattern in patterns:
            if pattern in text:
                return pattern
        return None
```

---

### Component 8: PromptShaper

**Responsibility**: Wrap voice input with mode prefix

**Type**: Transformer (pure)

**Owns**: Nothing

**Is Pure**: ✅ YES (same input → same output)

**Side Effects**: None

**Thread**: Main thread (fast)

**Allowed Operations**:
- Lookup mode → prefix
- Concatenate prefix + text
- Return WrappedPrompt

**Forbidden Operations**:
- ❌ Context-aware logic
- ❌ Text modification
- ❌ State access
- ❌ Side effects

```python
class PromptShaper:
    """Pure text wrapper"""

    PREFIX_MAP = {
        "default": "",
        "coding": "[CODING] ",
        "debug": "[DEBUG] ",
        "explain": "[EXPLAIN] "
    }

    def shape(self, text, mode):
        """
        Pure: same text+mode → same output
        """
        prefix = self.PREFIX_MAP.get(mode, "")
        wrapped = prefix + text
        return WrappedPrompt(wrapped_text=wrapped, mode_applied=mode)
```

---

### Component 9: CLIAdapter

**Responsibility**: Send text to Claude CLI (fire-and-forget)

**Type**: Output sink (non-blocking)

**Owns**: Nothing

**Is Pure**: ❌ NO (has side effect: modify terminal)

**Side Effects**: Insert text, press Enter

**Thread**: Main thread (but returns immediately)

**Allowed Operations**:
- Insert text into terminal
- Press Enter key
- Return immediately
- Log action (optional)

**Forbidden Operations**:
- ❌ Wait for response
- ❌ Read terminal output
- ❌ Monitor Claude's behavior
- ❌ Retry on perceived failure
- ❌ Keep handles/callbacks

```python
class CLIAdapter:
    """Fire-and-forget CLI sender"""

    def send(self, text):
        """
        Insert text and press Enter.
        Returns immediately. No return value.
        """
        self._insert_text(text)
        self._press_enter()
        # DONE - return immediately, do not monitor

    def _insert_text(self, text):
        """Type text into terminal (simulate user typing)"""
        for char in text:
            os.system(f"xdotool type '{char}'")
        time.sleep(0.1)

    def _press_enter(self):
        """Press Enter key"""
        os.system("xdotool key Return")
```

---

### Component 10: UINotifier

**Responsibility**: Display messages to user

**Type**: Output (side effects only)

**Owns**: UI state (visible vs hidden)

**Is Pure**: ❌ NO (displays to screen)

**Side Effects**: Render UI

**Thread**: Main thread OR async (non-blocking)

**Allowed Operations**:
- Display toast messages
- Show confirmation dialogs
- Display errors + recovery hints
- Hide UI on demand

**Forbidden Operations**:
- ❌ Make decisions (just display)
- ❌ Mutate session state
- ❌ Block main loop indefinitely
- ❌ Hide errors

```python
class UINotifier:
    """UI renderer - displays, doesn't decide"""

    def display_toast(self, message, duration_ms=3000):
        """Show temporary message"""
        # Implementation: Qt, tkinter, etc.
        pass

    def ask_confirmation(self, pattern):
        """
        Show dialog, wait for Y/N.
        Returns: bool (True if Y pressed)
        """
        # Modal dialog, blocks until user responds
        return True  # or False

    def display_error(self, error_msg, recovery):
        """Show error + what user should do"""
        pass
```

---

### Component 11: SessionState

**Responsibility**: Hold mutable session data

**Type**: Data holder (mutable)

**Owns**:
- mode (current mode)
- last_transcription (for "ulang" command)
- metrics (for debugging)

**Is Pure**: N/A (data, not function)

**Side Effects**: Mutations (thread-safe)

**Thread**: Main thread ONLY (mutated by MainLoop only)

**Allowed Operations**:
- Read by any component (for display/logic)
- Write by MainLoop only

**Forbidden Operations**:
- ❌ Write from hotkey listener
- ❌ Write from other threads
- ❌ Persist across session end
- ❌ Share with external systems

```python
class SessionState:
    """Immutable-friendly data holder"""

    def __init__(self):
        self.mode = "default"
        self.last_transcription = None
        self.start_time = time.time()
        self.input_count = 0

    def update_mode(self, new_mode):
        """Called only by MainLoop"""
        self.mode = new_mode

    def update_last_text(self, text):
        """Called only by MainLoop"""
        self.last_transcription = text

    # No writes from other threads
```

---

## State Ownership Matrix

| Component | Owns State | Mutates | Thread | Notes |
|-----------|-----------|---------|--------|-------|
| MainLoop | SessionState | ✅ | Main | Coordinator only |
| HotkeyListener | None | ❌ | Signal | Signals main loop |
| AudioCapture | Temporary buffer | ❌ | Main | Discards after return |
| STTAdapter | None | ❌ | Main | Pure translator |
| InputBoundary | None | ❌ | Main | Pure classifier |
| CommandExecutor | None | ❌ | Main | Returns mutations |
| SafetyGate | None | ❌ | Main | Pure validator |
| PromptShaper | None | ❌ | Main | Pure transformer |
| CLIAdapter | None | ❌ | Main | Side effect only |
| UINotifier | UI state | ✅ | Main/Async | Render only |

---

## Data Flow Diagram

```
┌──────────────┐
│ HotkeyListener│ (bg thread) → signal_queue
└──────────────┘                      ↓
                              ┌───────────────┐
                              │ MainLoop      │
                              │ (Main thread) │
                              └───────────────┘
                                  ↓↑ (calls)
                    ┌─────────────────────────────┐
                    ↓     ↓      ↓       ↓      ↓
            ┌──────────┐ ┌────────────┐ ┌──────────┐
            │ Audio    │ │ Input      │ │Command   │
            │ Capture  │ │ Boundary   │ │ Executor │
            └──────────┘ └────────────┘ └──────────┘
                    ↓     ↓      ↓       ↓      ↓
            ┌──────────┐ ┌──────────────────────┐
            │ STT      │ │ SafetyGate           │
            │ Adapter  │ │ PromptShaper         │
            └──────────┘ └──────────────────────┘
                                ↓
                        ┌──────────────┐
                        │ CLIAdapter   │
                        │ (send to CLI)│
                        └──────────────┘
                                ↓
                        [Claude CLI]
```

---

## Important Clarification: "Pure" Definition

**In this document, "Pure" means:**
- Deterministic output (same input → same output)
- No mutation of Jarvis SessionState
- No side effects on Jarvis state

**"Pure" does NOT mean:**
- ❌ Non-blocking (AudioCapture and STTAdapter block by design)
- ❌ Concurrency-safe to run in any thread (they must run in MainLoop)
- ❌ Can be optimized to async (blocking is architectural requirement, not implementation detail)

**Why this matters**: A pure function that blocks is still architecturally restricted. Future optimizers cannot move it off MainLoop without violating Layer 1 contracts.

---

## Critical Design Rules (From Layer 0-2, Enforced Here)

### Rule 1: Pure Functions Cannot Mutate
```
✅ InputBoundary.classify(text) → InputEvent (pure)
❌ InputBoundary.classify(text) → mutate SessionState (forbidden)
```

### Rule 2: Only MainLoop Mutates SessionState
```
✅ MainLoop: session.mode = "coding"
❌ HotkeyListener: session.mode = "coding" (forbidden)
❌ CommandExecutor: session.mode = "coding" (forbidden)
```

### Rule 3: HotkeyListener Never Does Anything But Signal
```
✅ HotkeyListener: signal_queue.put(event)
❌ HotkeyListener: capture_audio() (forbidden)
❌ HotkeyListener: mutate state (forbidden)
```

### Rule 4: CLIAdapter Never Reads
```
✅ CLIAdapter: insert_text(), press_enter(), return
❌ CLIAdapter: read_terminal_output() (forbidden)
❌ CLIAdapter: wait_for_response() (forbidden)
```

### Rule 5: SafetyGate Never Auto-Approves or Auto-Rejects
```
✅ SafetyGate: ask_user_confirmation() (via UINotifier)
❌ SafetyGate: auto_reject_dangerous_text() (forbidden)
❌ SafetyGate: auto_approve_after_timeout() (forbidden)
```

---

## What Layer 3 Prevents

**With this decomposition, it's impossible to:**
- Mutate state from hotkey listener (separate thread, signal-only)
- Have async STT (STTAdapter blocks main loop)
- Have hidden retry (all retries visible in MainLoop)
- Have side effects in pure functions (signature + docs forbid it)
- Have command leak to Claude (CommandExecutor doesn't call CLIAdapter)
- Have CLI reading output (CLIAdapter has no read method)

**These are architectural impossibilities, not guidelines.**

---

## Next Document (L3-ARCH-002)

Will define threading model that makes this decomposition enforceable in code.

---

**Next**: JARVIS-L3-ARCH-002 (Threading & Concurrency Model)

