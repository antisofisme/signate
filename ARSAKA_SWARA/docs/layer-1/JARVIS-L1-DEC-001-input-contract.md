# JARVIS-L1-DEC-001: Input Contract

**Status**: DRAFT (awaiting review)
**Date**: 2025-12-28
**Scope**: Layer 1 - Contracts & Boundaries

---

## Purpose

Define **what constitutes a valid input to Jarvis** and **what Jarvis produces as output** from that input.

This contract is the boundary between:
- **User action** → (INPUT BOUNDARY) → **Jarvis processing**
- **Jarvis processing** → (OUTPUT BOUNDARY) → **Next stage** (CLI adapter, command executor, safety gate)

---

## Input Contract Definition

### What is an Input?

An **input** is a complete, unambiguous unit of user intent that Jarvis receives and must process.

```
User Action
  ↓
  (Hotkey press, text typed, voice spoken)
  ↓
Jarvis receives raw signal
  ↓
  (Normalize, segment, classify)
  ↓
Input (classified, ready for routing)
```

---

## Input Types

### Input Type 1: VoiceInput

**Trigger**: F12 (or configured hotkey) pressed → speech captured → silence/release detected

**Format**:
```python
class VoiceInput:
    text: str                 # Transcribed text from Whisper
    duration_ms: int          # Audio duration (e.g., 3500ms)
    confidence: float         # STT confidence (optional, for metrics)
    utterance_sequence: int   # 1st, 2nd, 3rd input in session (for ordering)
    timestamp: float          # When input became available
```

**Rules**:
- ✅ text is NOT empty and NOT whitespace-only
- ✅ duration_ms ≥ 300ms (minimum speech duration)
- ✅ duration_ms ≤ 120,000ms (technical ceiling; utterances >10s are considered degraded UX and may be rejected or redirected to typing)
- ✅ All non-printable characters removed (control chars, zero-width spaces)
- ✅ Leading/trailing whitespace trimmed

**What is rejected**:
- ❌ Empty transcript (STT returned nothing)
- ❌ STT confidence < 0.5: display warning and ask user to repeat or type manually (no auto-retry)
- ❌ Duration > 120s (fallback to manual typing)
- ❌ Garbled text (all non-ASCII or corruption detected)

**Output**: `VoiceInput` object or REJECT signal

---

### Input Type 2: CommandInput

**Trigger**: User says text that matches exact/prefix command grammar

**Format**:
```python
class CommandInput:
    command: str              # e.g., "kirim", "ulang", "mode"
    arguments: Dict[str, Any] # e.g., {"mode": "coding"}
    utterance_sequence: int   # ordinal in session
    timestamp: float
```

**Rules**:
- ✅ text matches exactly or as prefix to known command
- ✅ Case-insensitive match
- ✅ Whitespace-normalized
- ✅ command ∈ ["kirim", "ulang", "ringkas", "jelaskan", "mode", "help"]
- ✅ For "mode" command: mode_value ∈ ["default", "coding", "debug", "explain"]

**What is rejected**:
- ❌ Text matches command but with typos (e.g., "send" instead of "kirim")
- ❌ Partial match that's ambiguous (e.g., "mo" could be "mode" or user saying "mo...")
- ❌ Mode value not in allowed list (e.g., "mode python" → invalid)

**Output**: `CommandInput` object or REJECT signal (treat as VoiceInput instead)

---

### Input Type 3: KeyboardInput

**Trigger**: User types text directly (fallback from STT failure or manual mode)

**Format**:
```python
class KeyboardInput:
    text: str                 # User typed text
    source: str               # "fallback_stT" | "fallback_safety" | "manual"
    utterance_sequence: int
    timestamp: float
```

**Rules**:
- ✅ text is NOT empty and NOT whitespace-only
- ✅ All printable ASCII or UTF-8 (no control chars)
- ✅ Leading/trailing whitespace trimmed
- ✅ source describes why keyboard was used

**Special case**: If KeyboardInput follows VoiceInput rejection:
- ✅ display UI message: "STT failed, type instead"
- ✅ set source = "fallback_STT"

**What is rejected**:
- ❌ Empty text
- ❌ Only whitespace
- ❌ Corrupted encoding

**Output**: `KeyboardInput` object or REJECT signal (show error, return to ready state)

---

## Input Completion Signal

An input is **COMPLETE** and ready for processing when ONE of these is true:

### For VoiceInput:
- ✅ User releases hotkey (F12 key UP) → input complete
- ✅ Silence ≥ 1.5s detected (VAD timeout) → input complete
- ✅ Duration reaches max 120s → input complete (fallback to manual)

### For CommandInput:
- ✅ Text ends (user stops speaking or presses Enter) → input complete

### For KeyboardInput:
- ✅ User presses Enter → input complete

**Before completion signal**:
- ❌ Input is INCOMPLETE
- ❌ Jarvis does NOT process
- ❌ Jarvis may show UI feedback (e.g., "recording...")

---

## Input Processing Flow

```
User Action (hotkey, typing, speech)
    ↓
┌─────────────────────────────────────┐
│ SIGNAL RECEIVED                     │
│ (F12 down, keystroke, audio frame)  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ ACCUMULATION                        │
│ (buffer audio, buffer text)         │
│ "not complete yet"                  │
└─────────────────────────────────────┘
    ↓
[WAIT for completion signal]
    ↓
┌─────────────────────────────────────┐
│ COMPLETION DETECTED                 │
│ (F12 release, Enter pressed, etc.)  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ NORMALIZE & CLASSIFY                │
│ ✅ Clean data                       │
│ ✅ Determine input type             │
│ ✅ Create Input object              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ INPUT VALIDATION                    │
│ ✅ Check rules for type             │
│ ✅ Reject if invalid                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ INPUT READY FOR ROUTING             │
│ (to safety gate, command exec, etc.)│
└─────────────────────────────────────┘
```

---

## Input → Output Contract

### Successful Input Processing

```
Input (VoiceInput | CommandInput | KeyboardInput)
    ↓
Valid? (passes all rules)
    ├─ YES → Output: InputEvent(type, payload, timestamp)
    │        Ready for next stage
    │
    └─ NO → Output: InputRejected(reason, recover_action)
            Example: "STT confidence too low, please repeat"
```

### InputEvent (Output on Success)

```python
class InputEvent:
    input_type: str           # "voice" | "command" | "keyboard"
    text: str                 # Normalized text
    payload: Dict[str, Any]   # Full input object
    timestamp: float          # When input became available
    utterance_sequence: int   # Ordinal in session
    next_stage: str           # Where to route: "command_executor" | "safety_gate" | "prompt_shaper"
```

**Routing rules** (determined by input type):
- `CommandInput` → "command_executor"
- `VoiceInput` → "safety_gate"
- `KeyboardInput` → "safety_gate"

---

### InputRejected (Output on Failure)

```python
class InputRejected:
    reason: str               # Why input was rejected
    recover_action: str       # What user should do
    severity: str             # "error" | "warning" | "info"
    display_ui: bool          # Show message to user?
```

**Examples**:
```
reason: "STT confidence too low"
recover_action: "Please repeat"
severity: "warning"

reason: "Speech duration > 120 seconds"
recover_action: "Too long for voice input. Please type instead."
severity: "error"

reason: "Mode 'python' not recognized"
recover_action: "Modes: default, coding, debug, explain"
severity: "error"
```

---

## Allowed & Forbidden

### ✅ ALLOWED at Input Boundary

- Classify input as VoiceInput, CommandInput, or KeyboardInput
- Validate against type-specific rules
- Normalize whitespace, case, encoding
- Remove non-printable characters
- Reject invalid inputs
- Create InputEvent or InputRejected
- Set next_stage routing
- Display user-friendly error messages

### ❌ FORBIDDEN at Input Boundary

- Parse input semantically (that's Layer 2)
- Make decisions based on input content (that's Layer 2+)
- Execute commands (that's command_executor)
- Scan for safety patterns (that's safety_gate)
- Apply mode/wrapping (that's prompt_shaper)
- Call external services (that's Layer 2+)
- Store input for later use (that's session state)
- Retry transcription automatically (that's STT layer concern)

---

## Five Concrete Scenarios

### Scenario 1: Valid VoiceInput (PASS)

```
User: [Presses F12]
       [Says: "build a sorting function"]
       [Releases F12]

Flow:
  T0: F12 down → start audio capture
  T1: Whisper transcribes → "build a sorting function"
  T2: F12 up → completion signal
  T3: Normalize:
      - text: "build a sorting function" ✅
      - duration_ms: 2800 ✅ (2.8 seconds)
      - confidence: 0.92 ✅
  T4: Validate VoiceInput rules:
      - text not empty ✅
      - duration ≥ 300ms ✅
      - duration ≤ 120s ✅
      - no garbled chars ✅
  T5: Output:
      InputEvent(
        input_type="voice",
        text="build a sorting function",
        next_stage="safety_gate",
        timestamp=T2
      )

Result: ✅ PASS → Route to safety_gate
```

---

### Scenario 2: Invalid CommandInput (REJECT)

```
User: [Says: "send"]  (English word, not "kirim")

Flow:
  T0: Hotkey → capture
  T1: Whisper returns → "send"
  T2: Completion signal (release)
  T3: Normalize → "send"
  T4: Try command grammar match:
      - "send" ≠ "kirim" (exact match fails)
      - "send" doesn't start with "mode " (prefix fails)
      - "send" ≠ other commands
  T5: Classification: NOT a command
  T6: Re-classify as VoiceInput:
      InputEvent(
        input_type="voice",
        text="send",
        next_stage="safety_gate"
      )

Result: ✅ PASS (as VoiceInput) → Route to safety_gate
```

---

### Scenario 3: Valid CommandInput (PASS)

```
User: [Says: "mode coding"]

Flow:
  T0: Hotkey → capture
  T1: Whisper returns → "mode coding"
  T2: Release → completion
  T3: Normalize → "mode coding"
  T4: Try command grammar:
      - "mode coding" starts with "mode " ✅
      - extract argument: "coding"
      - "coding" ∈ allowed modes ✅
  T5: Classification: CommandInput ✅
  T6: Output:
      InputEvent(
        input_type="command",
        text="mode coding",
        payload=CommandInput(
          command="mode",
          arguments={"mode": "coding"}
        ),
        next_stage="command_executor"
      )

Result: ✅ PASS → Route to command_executor
```

---

### Scenario 4: STT Failure → Fallback to KeyboardInput (PASS)

```
User: [Presses F12]
       [Says something unintelligible]
       [Releases F12]

Flow:
  T0: F12 down → start capture
  T1: Audio captured
  T2: F12 up → signal complete
  T3: Whisper processes → ERROR (timeout or model crash)
  T4: Input validation:
      - Text is empty/None ✅ (reject as VoiceInput)
  T5: Output:
      InputRejected(
        reason="STT failed: Whisper timeout",
        recover_action="Please type instead",
        severity="error",
        display_ui=True
      )
  T6: UI displays: "STT failed, please type instead"
  T7: User types: "how do I fix this"
  T8: User presses Enter
  T9: Normalize → "how do I fix this"
  T10: Classification: KeyboardInput
  T11: Output:
       InputEvent(
         input_type="keyboard",
         text="how do I fix this",
         source="fallback_STT",
         next_stage="safety_gate"
       )

Result: ✅ PASS (with fallback) → Route to safety_gate
```

---

### Scenario 5: Invalid Mode Command (REJECT)

```
User: [Says: "mode python"]  (invalid mode name)

Flow:
  T0-T2: Capture complete → "mode python"
  T3: Normalize → "mode python"
  T4: Try command grammar:
      - "mode python" starts with "mode " ✅
      - extract argument: "python"
      - "python" ∉ allowed modes ["default", "coding", "debug", "explain"] ❌
  T5: Classification: NOT a valid command
  T6: Re-classify as VoiceInput:
      InputEvent(
        input_type="voice",
        text="mode python",
        next_stage="safety_gate"
      )
  T7: (Later, at safety_gate: no dangerous patterns, send to Claude)
      Claude might understand "mode python" contextually

Result: ✅ PASS (as voice) → Route to safety_gate
        (User may learn correct mode names from help or trial)
```

---

## Non-Negotiable Constraints

✅ **MUST HAVE**:
- Input type classification is deterministic (no ambiguity)
- VoiceInput requires completion signal (hotkey release or timeout)
- CommandInput matches exact/prefix grammar only
- KeyboardInput passes through with minimal validation
- Rejection includes recovery action (not just error)
- Next stage routing is determined at input boundary
- No semantic processing at input boundary
- All inputs normalized before classification
- **Input boundary must be fast, side-effect free, and idempotent** (can be called multiple times with same input, same output)

❌ **MUST NOT HAVE**:
- Semantic interpretation of input content
- Automatic retry on failure (ask user instead)
- Input storage for later processing
- Decision-making based on input text
- Network calls during input processing
- Command execution at input boundary
- Safety scanning before classification
- Mode application before routing

---

## Input Validation Matrix

| Input Type | Validation Rules | Rejection Severity | Recovery Action |
|-----------|-----------------|-------------------|-----------------|
| VoiceInput | text not empty, duration 300-120000ms, no garbled chars | error/warning | "Repeat please" or "Type instead" |
| CommandInput | exact/prefix match, mode in allowed set | error | "Unknown command" |
| KeyboardInput | text not empty, valid encoding | error | "Try again" |

---

## Relationship to Other Layers

**Layer 0**:
- DEC-001 defines audio pipeline → produces raw transcript
- Input contract consumes that transcript and classifies it

**Layer 2 (will define)**:
- Safety gate consumes InputEvent from safety_gate route
- Command executor consumes InputEvent from command_executor route
- Prompt shaper consumes InputEvent and applies mode

**Layer 3 (will implement)**:
- Whisper integration (STT)
- Audio capture, VAD
- Text input handling
- Input classification logic

---

## Summary Table

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Input types | Voice, Command, Keyboard | Covers all user interaction modes |
| Completion signal | Hotkey release, silence, Enter | User controls input boundary |
| Classification | Deterministic grammar match | No ambiguity, no guessing |
| Validation | Type-specific rules | Reject early, clear recovery |
| Routing | Determined at boundary | Single responsibility per stage |
| Forbidden | Semantic processing, execution, retry | Keep boundary thin |

---

**Next**: JARVIS-L1-DEC-002 (Command Execution Boundary)

