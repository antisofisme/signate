# JARVIS-L2-ARCH-001: Orchestration Loop Overview

**Status**: DRAFT (awaiting review)
**Date**: 2025-12-28
**Scope**: Layer 2 - Orchestration & Component Lifecycle

---

## Purpose

Define **how the five Layer 1 boundaries are orchestrated** and **how they coordinate without violating their contracts**.

This is the first layer where threading, async, and implementation details appear. It's also where most systems start breaking the Layer 1 contracts "just a little". This document prevents that.

Key principle: **Layer 1 boundaries are inviolable. Orchestration must respect them completely.**

---

## The Orchestration Model

### High-Level Flow

```
┌─────────────────────────────────────────────────────────┐
│  JARVIS MAIN LOOP                                       │
│  (runs while Claude CLI is alive)                       │
└─────────────────────────────────────────────────────────┘
    │
    ├─ Wait for input signal (hotkey press, keyboard, etc.)
    │
    ├─ Route to appropriate boundary:
    │     ├─ voice input → input boundary
    │     ├─ command → command executor
    │     └─ keyboard → input boundary
    │
    ├─ Process through chain:
    │     ├─ Input boundary → InputEvent | InputRejected
    │     ├─ If InputEvent:
    │     │    ├─ if command → command_executor → CLI interaction
    │     │    └─ if voice → safety_gate → prompt_shaper → CLI interaction
    │     ├─ If InputRejected → display error, return to loop
    │
    └─ Return to ready state, wait for next input
```

---

## The Five Boundaries and Their Roles

### Boundary 1: Input Boundary (L1-DEC-001)

**Responsibility**: Classify raw input

```
Raw signal (audio transcript, keyboard text, command)
  ↓
  1. Normalize (whitespace, case, encoding)
  2. Classify (determine input type)
  3. Validate type-specific rules
  4. Route decision
  ↓
InputEvent (classified, ready for routing)
  or
InputRejected (error + recovery action)
```

**What it CANNOT do**:
- ❌ Execute anything
- ❌ Modify state
- ❌ Make decisions based on content
- ❌ Call external services
- ❌ Store input for later

---

### Boundary 2: Command Executor (L1-DEC-002)

**Responsibility**: Execute commands, isolated from voice path

```
InputEvent(type="command", ...)
  ↓
  1. Extract command name & arguments
  2. Validate arguments
  3. Execute command (atomic)
  4. Return CommandResult
  ↓
CommandResult (success flag + display message)
```

**What it CANNOT do**:
- ❌ Send command text to Claude
- ❌ Go through safety gate
- ❌ Apply mode wrapping
- ❌ Call safety scanning
- ❌ Read terminal output

---

### Boundary 3: Safety Gate (Not formally L1, but critical)

**Responsibility**: Check voice input for dangerous patterns

```
InputEvent(type="voice", text)
  ↓
  1. Scan for dangerous patterns
  2. If dangerous: show confirmation dialog
  3. Wait for user Y/N
  4. If N: return to loop (rejected)
  5. If Y: pass through
  ↓
Safe voice input (or rejected)
```

**What it CANNOT do**:
- ❌ Scan CommandInput (commands are intentional)
- ❌ Auto-reject without confirmation
- ❌ Modify input
- ❌ Auto-retry

---

### Boundary 4: Prompt Shaper (L1-DEC-003)

**Responsibility**: Wrap voice input with mode prefix

```
VoiceInput + Mode
  ↓
  1. Lookup mode → prefix
  2. Concatenate: prefix + text
  3. Return wrapped prompt
  ↓
WrappedPrompt
```

**What it CANNOT do**:
- ❌ Apply context-aware logic
- ❌ Modify input based on content
- ❌ Call external services
- ❌ Adapt based on mode hints

---

### Boundary 5: CLI Interaction (L1-DEC-004)

**Responsibility**: Send text to Claude CLI, fire-and-forget

```
WrappedPrompt or CommandResult
  ↓
  1. Insert text into terminal
  2. Press Enter
  3. Return immediately
  4. DONE
  ↓
(Claude CLI processes independently)
```

**What it CANNOT do**:
- ❌ Read output
- ❌ Monitor progress
- ❌ Retry on any condition
- ❌ Wait for Claude
- ❌ Keep handles/callbacks/watchers

---

## Critical Invariants (Must Be Maintained)

### Invariant 1: Input Classification is Single-Pass

```
Input → Input Boundary → InputEvent | InputRejected
         (never revisited, never modified downstream)
```

**Why**: Ensures determinism, prevents cascading confusion

---

### Invariant 2: Command and Voice Paths Never Merge

```
Command path:  InputEvent(command) → command_executor → CLI
Voice path:    InputEvent(voice) → safety_gate → prompt_shaper → CLI

NEVER:
  ❌ command mixed with voice processing
  ❌ voice path skipping safety gate
  ❌ command going through prompt shaper
```

**Why**: Separations are absolute, not situational

---

### Invariant 3: Prompt Shaping is Deterministic

```
Same (text, mode) → same wrapped output (100% determinism)
No context-dependency, no conditional logic
```

**Why**: Enables auditing, prevents hidden behavior

---

### Invariant 4: CLI Interaction is Non-Blocking

```
send_to_cli(text) → insert → press_enter → return (no wait)
Jarvis does NOT:
  ❌ wait for response
  ❌ monitor execution
  ❌ tie handles
```

**Why**: Maintains fire-and-forget model, prevents coupling

---

### Invariant 5: Failures are Explicit & Non-Cascading

```
Failure at any boundary → explicit message → user action → loop restarts
NOT: failure auto-handled, state recovered, loop continues
```

**Why**: User always aware, can intervene, system remains auditable

---

## The Main Loop (Pseudocode)

```python
def main_loop():
    """
    Jarvis main orchestration loop.
    Runs while Claude CLI is alive.
    """

    # Initialize
    session = SessionState(mode="default", last_text=None)
    hotkey = setup_hotkey()

    # Main loop
    while claude_cli_is_alive():

        # ============ WAIT FOR INPUT ============
        input_signal = wait_for_input(
            timeout=INFINITY,  # wait until user acts
            listen_to=[hotkey, keyboard, commands]
        )

        # ============ INPUT BOUNDARY ============
        input_event = input_boundary.classify(input_signal)

        if input_event == InputRejected:
            # Failure at boundary: display error + recovery
            display_error(input_event.display)
            display_recovery(input_event.recovery_action)
            continue  # Loop restarts

        # ============ ROUTING ============
        if input_event.type == "command":
            # COMMAND PATH
            result = command_executor.execute(input_event)
            display_result(result.display)

            # Side effects (e.g., mode change)
            if result.mode_change:
                session.mode = result.mode_change

            continue  # Return to loop

        elif input_event.type in ["voice", "keyboard"]:
            # VOICE PATH

            # Safety gate
            if safety_gate.contains_danger(input_event.text):
                confirmed = display_confirmation_dialog(input_event.text)
                if not confirmed:
                    display("Operation canceled")
                    continue  # Return to loop

            # Prompt shaping
            wrapped_prompt = prompt_shaper.shape(
                text=input_event.text,
                mode=session.mode
            )

            # CLI interaction
            cli_adapter.send_to_claude(wrapped_prompt)

            # Side effects
            session.last_transcription = input_event.text

            continue  # Return to loop


def wait_for_input(timeout, listen_to):
    """
    Wait for user input from hotkey, keyboard, etc.
    This is BLOCKING until input arrives.
    """
    # Pseudocode: implementation details in Layer 3
    signal = blocking_wait(sources=listen_to, timeout=timeout)
    return signal


def input_boundary.classify(signal):
    """
    Classify raw signal as VoiceInput, CommandInput, or KeyboardInput.
    This is pure function, no side effects.
    """
    # Pseudocode: implementation details in Layer 3
    normalized = normalize(signal)
    input_type = determine_type(normalized)
    validated = validate(normalized, input_type)

    if not validated:
        return InputRejected(...)
    else:
        return InputEvent(...)


def command_executor.execute(command_input):
    """
    Execute command (kirim, mode, etc.).
    Atomic, returns CommandResult.
    """
    # Pseudocode: implementation details in Layer 3
    if command_input.command == "kirim":
        press_enter()
        return CommandResult(success=True, display="Sent ✓")

    elif command_input.command == "mode":
        if validate_mode(command_input.arguments["mode"]):
            return CommandResult(
                success=True,
                display=f"Mode: {mode}",
                mode_change=command_input.arguments["mode"]
            )
        else:
            return CommandResult(
                success=False,
                display="Unknown mode..."
            )


def safety_gate.contains_danger(text):
    """
    Scan text for dangerous patterns.
    Return True if danger detected.
    """
    # Pseudocode: implementation details in Layer 3
    patterns = ["rm -rf", "git reset", "DROP TABLE", ...]
    return any(pattern in text for pattern in patterns)


def prompt_shaper.shape(text, mode):
    """
    Wrap text with mode prefix.
    Pure function: same input → same output.
    """
    # Pseudocode: implementation details in Layer 3
    prefix_map = {
        "default": "",
        "coding": "[CODING] ",
        "debug": "[DEBUG] ",
        "explain": "[EXPLAIN] "
    }
    prefix = prefix_map[mode]
    wrapped = prefix + text
    return WrappedPrompt(wrapped_text=wrapped, mode_applied=mode)


def cli_adapter.send_to_claude(prompt):
    """
    Insert text into Claude CLI, press Enter, return immediately.
    Fire-and-forget: no return value, no wait.
    """
    # Pseudocode: implementation details in Layer 3
    insert_text(prompt.wrapped_text)
    sleep(100)  # let insertion complete
    press_key("Return")
    return  # DONE - do not monitor
```

---

## Component Lifecycle

### Startup

```
Main process starts
  ↓
Initialize session state (mode="default")
Initialize hotkey listener
Connect to Claude CLI (verify it's running)
  ↓
Enter main loop
```

### Runtime

```
Main loop iteration:
  Wait for input
  Process through boundaries
  Return to loop
(repeat until Claude CLI exits)
```

### Shutdown

```
Claude CLI exits or dies
  ↓
Main loop detects: claude_cli_is_alive() = False
  ↓
Exit loop
Clean up resources (hotkey listener, etc.)
Process terminates
```

---

## Session State Management

### What Session Owns

```
session.mode              # Current mode (default, coding, debug, explain)
session.last_transcription # Last voice input (for "ulang" command)
session.start_time        # When session began (for metrics)
session.input_count       # Number of inputs (for metrics)
session.error_count       # Number of errors (for metrics)
```

### What Session Does NOT Own

```
❌ Conversation history (Claude owns)
❌ User identity (not Jarvis' concern)
❌ Terminal state (Claude owns)
❌ Persistent preferences (Layer 0 forbids)
```

### State Reset

```
On Claude CLI exit: ALL session state cleared
  ↓ New Claude CLI start: new session, fresh start
```

---

## Error Propagation

### At Each Boundary

```
InputRejected → display error + recovery → loop
CommandResult(error) → display error → loop
Safety rejection → show dialog → loop (on N) or continue (on Y)
CLI interaction error → (handled locally, silent if insertion failed)
```

### Never Auto-Recover

```
❌ No retry loops
❌ No fallback attempts
❌ No state restoration
❌ User always decides next action
```

---

## Critical Design Notes

### Note 1: Hotkey Listener

```
Hotkey listener runs OUTSIDE main loop (separate thread/process)
Triggered by: hotkey press
Action: signal main loop to capture audio

MUST NOT:
  ❌ Process audio inside listener (blocking)
  ❌ Modify session state (race condition)
  ❌ Call external services (latency)
  ✅ Just signal main loop
```

### Note 2: Audio Capture

```
Audio capture is SYNCHRONOUS with hotkey
  hotkey down → start capture
  hotkey up → end capture
  VAD timeout → end capture (1.5s)

MUST NOT:
  ❌ Continue capturing after hotkey release (waste)
  ❌ Cache audio for later (privacy)
  ✅ Just capture what user spoke
```

### Note 3: STT is BLOCKING

```
Main loop is BLOCKED until STT returns
  insert_text() wait → process audio
  Whisper processes (≤ 1s target)
  STT returns or times out

MUST NOT:
  ❌ Async STT (complicates error handling)
  ❌ Background retry (violates transparency)
  ✅ Just wait for result or timeout

DESIGN INTENT:
Blocking STT is a deliberate choice to preserve:
  - Determinism (same input → same processing every time)
  - Explicit failure handling (no hidden retry loops)
  - Simple auditable flow (no async state races)

This constraint is non-negotiable. Future "optimizations" to async STT
will violate the Failure & Degradation Contract.
```

### Note 4: CLI Interaction is FIRE-AND-FORGET

```
After press_enter(), Jarvis control returns to loop
Claude processes independently
Jarvis does NOT:
  ❌ wait for response
  ❌ read output
  ❌ monitor progress

User monitors Claude's terminal
```

---

## Thread Safety Notes

### If Using Threads

```
Main loop thread:
  - Process input
  - Update session state
  - Call boundaries

Hotkey listener thread:
  - Detect hotkey
  - Signal main thread
  - DO NOT modify state

Rule: Only main loop thread modifies session state
```

### If Using Async/Await

```
Async main loop:
  - Wait for input (awaitable)
  - Process boundaries (synchronous, fast)
  - CLI interaction (awaitable, fire-and-forget)

Rule: Boundaries complete immediately (no await inside)
```

---

## Concrete Flow: Voice Input → Claude

```
User presses F12, speaks "build a function", releases F12

T0:  Main loop: wait_for_input() (blocking)
T1:  Hotkey listener: F12 detected, signal main loop
T2:  Main loop: audio_capture() starts
T3-T5: User speaks (audio accumulated)
T6:  F12 released, audio_capture() ends
T7:  Input boundary: classify(audio)
     → InputEvent(type="voice", text="build a function")
T8:  Routing: voice path selected
T9:  Safety gate: scan("build a function")
     → No danger, continue
T10: Prompt shaper: shape(text, mode="default")
     → WrappedPrompt(wrapped_text="build a function")
T11: CLI interaction: send_to_claude("build a function")
     → insert_text(), press_enter(), return
T12: Main loop: continue
     (Back to T0, wait for next input)

Total: ~1.2s from F12 press to Claude receiving input
```

---

## Concrete Flow: Command → Mode Change

```
User speaks "mode coding"

T0:  Main loop: wait_for_input()
T1-T5: Hotkey + audio capture
T6:  Input boundary: classify(audio)
     → InputEvent(type="command", command="mode", arguments={mode: "coding"})
T7:  Routing: command path selected
T8:  Command executor: execute(command)
     → Validate mode: "coding" ∈ allowed ✓
     → session.mode = "coding"
     → return CommandResult(success=True, display="🔵 CODING MODE")
T9:  Main loop: display_result("🔵 CODING MODE")
T10: Main loop: continue
     (Back to T0, now mode="coding" for next input)

Note: "mode coding" was NOT sent to Claude
      Next voice input will be wrapped as "[CODING] ..."
```

---

## Concrete Flow: Safety Rejection

```
User speaks "explain how to rm -rf safely"

T0-T6:  Audio capture → Input boundary
        → InputEvent(type="voice", text="explain how to rm -rf safely")
T7:     Routing: voice path
T8:     Safety gate: scan(text)
        → "rm -rf" detected → danger!
        → show confirmation dialog:
            "Destructive operation detected: rm -rf"
            "Continue? [Y] [N]"
T9:     User presses [N]
        → confirmed = False
T10:    Main loop: display("Operation canceled")
T11:    Main loop: continue (back to wait_for_input)

If user pressed [Y]:
T9:     confirmed = True
T10:    Continue to prompt shaper, CLI interaction
        (Claude receives: "explain how to rm -rf safely")
```

---

## Guard Rails for Layer 2 Implementation

✅ **REQUIRED**:
- Main loop must be simple and single-threaded (or properly synchronized)
- Session state mutations only in main loop thread
- Hotkey listener signals main loop only (no state changes)
- Audio capture is synchronous (blocks until hotkey release or timeout)
- STT is synchronous (blocks until result or timeout)
- All boundaries are pure functions (no side effects except state update)
- CLI interaction is synchronous but non-blocking (press Enter and return)

❌ **FORBIDDEN**:
- Background retry loops
- Async state mutation (race conditions)
- Hotkey listener processing audio (latency)
- Monitoring Claude's output
- Cache fallback on failure
- Silent error handling

---

## Summary: Orchestration Guarantees

| Guarantee | How Enforced |
|-----------|--------------|
| Input determinism | Input boundary is pure function |
| Command isolation | Separate code path for commands |
| Prompt determinism | Prompt shaper is pure function (lookup + concat) |
| Fire-and-forget | CLI interaction returns immediately, no handles |
| Explicit failure | Failures produce messages or self-evident terminal states |
| Session isolation | Only main loop modifies session state |
| No hidden retry | All loops observable in code, documented |

---

**Next**: JARVIS-L2-ARCH-002 (Component Specifications & Threading Model)

