# JARVIS-L1-DEC-005: Failure & Degradation Contract

**Status**: DRAFT (awaiting review)
**Date**: 2025-12-28
**Scope**: Layer 1 - Contracts & Boundaries

---

## Purpose

Define **how Jarvis fails gracefully** when any layer breaks, and **what the user experiences** in each failure case.

This is about dignity in failure. Not panic, not recovery attempts, not hidden retries. Just: clear signal to user + path to recovery.

Key principle: **All failures are explicit, reversible, and non-silent.**

---

## Core Contract: Explicit Failure

### Failure is NOT

```
❌ Retry automatically
❌ Fail silently
❌ Degrade without notification
❌ Adapt behavior on failure
❌ Cache fallback
❌ Hide the error from user
```

### Failure IS

```
✅ Immediate explicit message
✅ Clear description of what happened
✅ Explicit recovery action for user
✅ Return to known state
✅ Never assume success
✅ Never cover up problem
```

---

## Failure Modes & Contracts

### Failure Mode 1: STT Failure (Audio → Text)

**Trigger**:
```
Whisper (STT) crashes, times out, or returns empty/garbled
  └─ Audio buffer: valid
     Transcription: INVALID or MISSING
```

**User Experience**:
```
User: [F12, speaks, releases]
       [waits for STT]

System: (STT fails internally)

User sees: 🔴 Toast notification
           "STT failed. Please try again or type instead."
           [Audio buffer cleared]

User choice:
  A) [F12] again → repeat (new STT attempt)
  B) Type manually → continue without voice
```

**Contract**:
```python
class STTFailure(FailureMode):
    trigger: str = "STT timeout, crash, empty result, or garbled"
    display: str = "STT failed. Please try again or type instead."
    action: str = "clear_audio_buffer()"
    recovery: str = "user_manual_retry | user_manual_typing"
    explicit: bool = True
    reversible: bool = True
    silent: bool = False
```

**What Jarvis MUST NOT do**:
- ❌ Auto-retry STT
- ❌ Fall back to keyboard without asking
- ❌ Try to interpret partial transcript
- ❌ Degrade audio quality and retry
- ❌ Hide the error (message is mandatory)

---

### Failure Mode 2: Safety Gate Rejection

**Trigger**:
```
Voice input contains dangerous pattern (rm -rf, etc.)
  └─ Input: valid
     Safety scan: REJECTED
```

**User Experience**:
```
User: [F12, says: "explain how to rm -rf safely"]
       [releases]

System: (Safety gate detects danger)

User sees: ⚠️ Confirmation dialog
           "Destructive operation detected: rm -rf
            Continue? [Y] [N]"

User choice:
  A) Press Y → send to Claude anyway (user intent acknowledged)
  B) Press N → cancel (operation aborted, return to ready)
```

**Contract**:
```python
class SafetyRejection(FailureMode):
    trigger: str = "Voice input contains dangerous pattern"
    display: str = "Destructive operation detected: {pattern}"
    action: str = "show_confirmation_dialog()"
    recovery: str = "user_explicit_Y | user_explicit_N"
    explicit: bool = True
    reversible: bool = True
    silent: bool = False
```

**What Jarvis MUST NOT do**:
- ❌ Auto-send to Claude after safety rejection
- ❌ Require voice confirmation ("say yes")
- ❌ Time out and auto-reject
- ❌ Hide dangerous pattern from user
- ❌ Allow bypassing by rephrasing

---

### Failure Mode 3: Invalid Command Argument

**Trigger**:
```
Command parsed but argument invalid
  └─ "mode python" → mode not in [default, coding, debug, explain]
```

**User Experience**:
```
User: [Says: "mode python"]

System: (Command executor validates)

User sees: 🔴 Error message
           "Unknown mode 'python'. Modes: default, coding, debug, explain"

Result: Mode unchanged (still whatever it was before)

User can:
  A) Say "mode coding" → set valid mode
  B) Continue typing → use current mode
```

**Contract**:
```python
class InvalidCommandArg(FailureMode):
    trigger: str = "Command valid, but argument invalid"
    display: str = "Unknown mode '{value}'. Modes: {valid_list}"
    action: str = "no_state_change()"
    recovery: str = "user_reissue_command | user_continue"
    explicit: bool = True
    reversible: bool = True
    silent: bool = False
```

**What Jarvis MUST NOT do**:
- ❌ Auto-correct invalid argument
- ❌ Assume closest match (e.g., python → python-mode)
- ❌ Apply partial state change
- ❌ Re-interpret as voice input silently
- ❌ Hide the error

---

### Failure Mode 4: Keyboard Input Encoding Error

**Trigger**:
```
User types, but text contains invalid encoding
  └─ Corrupted UTF-8 or control characters
```

**User Experience**:
```
User: [Types text with corrupted encoding]
      [Presses Enter]

System: (Input validation fails)

User sees: 🔴 Error message
           "Invalid input: text contains unsupported characters"

User can:
  A) Delete/retype
  B) Copy-paste clean text
```

**Contract**:
```python
class EncodingError(FailureMode):
    trigger: str = "Text input encoding invalid"
    display: str = "Invalid input: text contains unsupported characters"
    action: str = "reject_input()"
    recovery: str = "user_retype"
    explicit: bool = True
    reversible: bool = True
    silent: bool = False
```

**What Jarvis MUST NOT do**:
- ❌ Strip characters silently
- ❌ Try to convert encoding
- ❌ Send corrupted text anyway
- ❌ Hide the error

---

### Failure Mode 5: Claude CLI Frozen or Unresponsive

**Trigger**:
```
Claude CLI not responding to input
  └─ Jarvis pressed Enter, but CLI not advancing
     (This is Claude's problem, not Jarvis')
```

**User Experience**:
```
User: [F12, voice input, released]
Jarvis: [inserted text, pressed Enter]
       [returned control immediately]

User watches terminal:
  [nothing happens for 30 seconds]

Jarvis: Does nothing (fire-and-forget principle)

User can:
  A) Press Ctrl+C → interrupt Claude
  B) Wait longer
  C) Press F12 again → send new input (override old)
```

**Contract**:
```python
class CLIUnresponsive(FailureMode):
    trigger: str = "Claude CLI frozen or stuck"
    display: str = "(nothing - Jarvis is not monitoring)"
    action: str = "no_action()"
    recovery: str = "user_interrupt | user_wait | user_override"
    explicit: bool = False  # User sees frozen terminal, figures it out
    reversible: bool = True  # Ctrl+C or new input works
    silent: bool = False  # Terminal shows the problem visually
```

**What Jarvis MUST NOT do**:
- ❌ Monitor Claude's responsiveness
- ❌ Send timeout warnings
- ❌ Auto-interrupt Claude
- ❌ Send follow-up clarification
- ❌ Assume failure and retry
- ✅ User's responsibility to manage Claude (fire-and-forget)

---

### Failure Mode 6: Jarvis Crashes

**Trigger**:
```
Jarvis process crashes or segfaults
  └─ Hotkey listener dies
     Session state lost
```

**User Experience**:
```
User: [Working normally]
      [Jarvis crashes silently]

User: [Presses F12] → nothing happens

User realizes: Jarvis is dead

User can:
  A) Restart Jarvis manually
  B) Use Claude CLI without Jarvis

Result: Session state is LOST
        Mode reset to "default"
        No recovery possible (no persistence)
```

**Contract**:
```python
class JarvisCrash(FailureMode):
    trigger: str = "Jarvis process crashes"
    display: str = "(none - Jarvis is dead)"
    action: str = "crash()"
    recovery: str = "user_restart_jarvis"
    explicit: bool = False  # User notices hotkey doesn't work
    reversible: bool = True  # User restarts
    silent: bool = False  # Absence is noticeable
    state_lost: bool = True  # Mode, session state all lost
```

**What Jarvis MUST NOT do**:
- ❌ Auto-restart itself
- ❌ Save state for recovery (violates Layer 0)
- ❌ Resume previous session
- ❌ Try to sync with Claude
- ✅ User restarts, starts fresh

---

## Failure Matrix

| Failure Mode | Trigger | User Sees | Recovery | Reversible | Silent |
|--------------|---------|-----------|----------|-----------|--------|
| STT Failure | STT crash | Error + message | Retry or type | ✅ | ✅ |
| Safety Reject | Dangerous pattern | Confirmation dialog | Y/N choice | ✅ | ✅ |
| Invalid Arg | Bad command arg | Error + hint | Retype command | ✅ | ✅ |
| Encoding Error | Bad UTF-8 | Error message | Retype | ✅ | ✅ |
| CLI Frozen | Claude stuck | (nothing - terminal frozen) | Interrupt/wait | ✅ | ✅ |
| Jarvis Crash | Process dies | (F12 doesn't work) | Restart | ✅ | ✅ |

---

## Allowed & Forbidden

### ✅ ALLOWED

- Display error message immediately
- Show recovery action to user
- Clear state on failure
- Let user decide next step
- Log failure for debugging
- Explicit notification
- Failures that are directly observable (terminal frozen, hotkey non-responsive)

### ❌ FORBIDDEN

- Auto-retry on any failure
- Hide error from user
- Assume failure and adapt
- Recover state without user action
- Cache fallback
- Silent degradation
- Background recovery attempt

**Definition of "non-silent"**: Failures are non-silent if they are either (a) displayed to user via message, or (b) directly observable by user in terminal/UI without additional explanation (e.g., terminal frozen, hotkey unresponsive). Hidden errors are forbidden; self-evident failures are acceptable.

---

## Five Concrete Scenarios

### Scenario 1: STT Timeout - EXPLICIT, REVERSIBLE

```
User: [F12, says "hello world", releases F12]
      [waits for transcription]

T0: STT starts (Whisper processing)
T1-T5: [network lag, model loading]
T10: STT timeout (> 1s, config max)

Display:
  🔴 Toast: "STT failed. Please try again or type instead."

State:
  - audio_buffer: cleared
  - last_transcription: unchanged
  - mode: unchanged
  - session: ready for new input

User choice:
  A) [F12] again → new STT attempt
  B) Type manually → continue

Result: ✅ EXPLICIT (user knows what happened)
        ✅ REVERSIBLE (can retry or type)
        ✅ NOT SILENT (message displayed)
```

---

### Scenario 2: Safety Gate Rejection - EXPLICIT CONFIRMATION

```
User: [F12, says "delete all files with rm -rf", releases]

T0: Transcription: "delete all files with rm -rf"
T1: Classify: VoiceInput
T2: Safety scan: "rm -rf" detected
T3: Show dialog:
    ┌────────────────────────────────┐
    │ ⚠️  DESTRUCTIVE OPERATION       │
    │                                │
    │ Detected: rm -rf               │
    │                                │
    │ Continue? [Y] [N]              │
    └────────────────────────────────┘

User: [Presses Y]
  → Send to Claude: "delete all files with rm -rf"

User: [Presses N]
  → Display: "Operation canceled"
  → Return to ready state

Result: ✅ EXPLICIT (danger highlighted)
        ✅ REVERSIBLE (can choose Y or N)
        ✅ NOT SILENT (confirmation required)
```

---

### Scenario 3: Invalid Command Argument - ERROR + HINT

```
User: [Says: "mode superior"]

T0: Transcription: "mode superior"
T1: Command parse: command="mode", argument="superior"
T2: Validate: "superior" ∉ allowed modes
T3: Return error:
    🔴 Error: "Unknown mode 'superior'. Modes: default, coding, debug, explain"

State:
  - mode: unchanged (still whatever it was)
  - session: ready

User can:
  A) Say "mode coding" → set valid mode
  B) Continue with current mode

Result: ✅ EXPLICIT (error shown)
        ✅ REVERSIBLE (mode unchanged, can retry)
        ✅ NOT SILENT (error message clear)
```

---

### Scenario 4: Claude CLI Frozen - USER'S PROBLEM

```
User: [F12, voice input]
Jarvis: [insert text, press Enter, return immediately]

User watches terminal:
  [nothing happens... waiting]
  [30 seconds pass, no response]

Jarvis: (does nothing, fire-and-forget)

User realizes: Claude is stuck

User can:
  A) [Ctrl+C] → interrupt Claude
  B) Wait more
  C) [F12] again → send new input (override)

Result: ✅ NOT SILENT (terminal shows problem)
        ✅ REVERSIBLE (can interrupt or override)
        ✅ User's responsibility (Jarvis doesn't monitor)
```

---

### Scenario 5: Jarvis Crashes - CLEAN FAILURE

```
T0-T30: User working normally with Jarvis
T30: [Jarvis crashes - segfault or exception]
     [process dies silently]

T31: User: [F12] → nothing happens
     User realizes: Jarvis is dead

User action:
  A) Restart Jarvis manually
  B) Use Claude without Jarvis (type manually)

State:
  - Session: LOST (no persistence)
  - Mode: reset to "default"
  - last_transcription: lost
  - audio_buffer: lost

Result: ⚠️ EXPLICIT (F12 doesn't work, user figures it out)
        ✅ REVERSIBLE (restart Jarvis from scratch)
        ✅ CLEAN (no lingering state, fresh start)
```

---

## Non-Negotiable Constraints

✅ **MUST HAVE**:
- All failures produce explicit message (except CLI frozen and Jarvis crash, which are self-evident)
- All failures are reversible (user can retry or take alternate path)
- No silent degradation (user always aware something failed)
- No auto-retry (user decides)
- No recovery from cache (user restarts)
- Clear recovery action shown to user

❌ **MUST NOT HAVE**:
- Auto-retry on failure
- Hidden error handling
- Assume failure means something else
- Cache fallback
- Background recovery
- State persistence across crash
- Auto-adapt behavior on failure

---

## Relationship to Other Layers

**Layer 0**:
- All failures must respect: no secondary memory, no background decision, single-session principle
- STT failure must not trigger cached audio
- Jarvis crash must not restore session

**Layer 1**:
- Input boundary: validate, reject explicitly
- Command executor: return error, not silently fail
- Prompt shaper: never silently degrade
- CLI interaction: never monitor for failure

**Layer 2+**:
- User interaction loop: handle failure display
- Error UI: toast, dialog, error message
- Retry logic: user-triggered only

---

## Summary Table

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Silence | Forbidden | User must know failure happened |
| Auto-retry | Forbidden | Violates transparency, creates loops |
| Recovery | User action | Jarvis doesn't decide recovery |
| State persistence | Forbidden | Layer 0: single-session, no memory |
| Monitoring | Forbidden | Fire-and-forget principle |
| Explicit message | Mandatory | User awareness is contract |

---

**Layer 1 Complete**: All 5 documents ready for final lock

