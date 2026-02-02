# JARVIS-L1-DEC-002: Command Execution Boundary

**Status**: DRAFT (awaiting review)
**Date**: 2025-12-28
**Scope**: Layer 1 - Contracts & Boundaries

---

## Purpose

Define **the boundary between command execution and voice input processing**.

This contract prevents the most common mistake: treating commands and voice input the same way.

Key principle: **Command ≠ Voice Input. Their paths diverge at the boundary.**

---

## Core Contract: Commands vs Voice Input

### Fundamental Separation

```
InputEvent(type, text, payload)
  ↓
  ↓ input_type?
  ├─ "command"  →  COMMAND EXECUTION PATH
  │               (direct, no safety scan, no prompt wrapping)
  │
  └─ "voice"    →  VOICE INPUT PATH
  └─ "keyboard" →  (safety scan → prompt wrapping → Claude)
```

**This separation is NOT optional. It is architectural law.**

---

## Command Execution Path

### What Happens to CommandInput

```
CommandInput received
  ↓
Route to command_executor
  ↓
┌──────────────────────────────────────┐
│ COMMAND EXECUTION                    │
│                                      │
│ 1. Extract command name (kirim, etc)│
│ 2. Extract arguments (if "mode")    │
│ 3. Validate arguments               │
│ 4. Execute command action           │
│ 5. Return command result            │
│ 6. Display UI feedback              │
└──────────────────────────────────────┘
  ↓
COMMAND COMPLETE
(Does NOT go to Claude)
(Does NOT go through safety scan)
```

---

### Command Types & Actions

#### Command: `kirim` (Send)

**Contract**:
```python
# Input
CommandInput(
  command="kirim",
  arguments={}
)

# Execution
action: press_enter_in_cli()

# Output
CommandResult(
  success: True,
  display: "Sent ✓"
)

# Does NOT:
  ❌ Go to Claude CLI as text
  ❌ Go through safety scan
  ❌ Get wrapped with mode
```

---

#### Command: `ulang` (Resend)

**Contract**:
```python
# Input
CommandInput(
  command="ulang",
  arguments={}
)

# Execution
last_text = get_last_transcription()
if last_text:
  send_to_cli(last_text)
  action: press_enter_in_cli()
else:
  action: display_error("Nothing to resend")

# Output
CommandResult(
  success: True/False,
  display: "Resent: {text}" or "Nothing to resend"
)
```

---

#### Command: `mode <X>` (Set Mode)

**Contract**:
```python
# Input
CommandInput(
  command="mode",
  arguments={"mode": "coding"}
)

# Validation
if arguments["mode"] in ["default", "coding", "debug", "explain"]:
  action: set_session_mode(arguments["mode"])
  success: True
else:
  action: display_error(f"Unknown mode: {arguments['mode']}")
  success: False

# Output
CommandResult(
  success: True/False,
  display: "🔵 CODING MODE" or "Unknown mode..."
)

# Does NOT:
  ❌ Send anything to Claude
  ❌ Apply to next input (already applied immediately)
```

---

#### Command: `help`

**Contract**:
```python
# Input
CommandInput(
  command="help",
  arguments={}
)

# Execution
action: display_help_overlay()

# Output
CommandResult(
  success: True,
  display: (help text displayed)
)
```

---

#### Command: `ringkas`, `jelaskan` (Phase 2)

**Contract (MVP)**:
```python
# Input
CommandInput(
  command="ringkas",  # or "jelaskan"
  arguments={}
)

# Execution (Phase 2)
action: display_placeholder("Not yet implemented")

# Output
CommandResult(
  success: False,
  display: "Coming in Phase 2"
)
```

---

## The Safety Gate Contract

### Critical Enforcement: Safety Scan Only for Voice, NOT Commands

```
InputEvent received
  ↓
IF input_type == "command":
  ├─ Route to command_executor
  ├─ SKIP safety gate
  └─ Execute directly

IF input_type == "voice" or "keyboard":
  ├─ Route to safety_gate
  ├─ SCAN for dangerous patterns
  ├─ IF dangerous: ask confirmation
  └─ THEN send to Claude (if approved)
```

**Rationale**:
- Commands are **user-intentional, structured** (e.g., "kirim", "mode coding")
- Voice input is **free-form, may contain accidental danger** (e.g., "explain how to rm -rf")
- Safety gates protect against **accident**, not **intention**

---

### What This Prevents

#### ❌ MISTAKE #1: Scanning "kirim" for Safety

```
User says: "kirim"
Jarvis: classify as CommandInput
WRONG: scan "kirim" for dangerous patterns
WRONG: delay execution while scanning
WRONG: potentially reject valid command

CORRECT: Skip safety gate, execute immediately
```

#### ❌ MISTAKE #2: Scanning "mode coding" for Safety

```
User says: "mode coding"
Jarvis: classify as CommandInput
WRONG: scan "mode coding" for dangerous patterns
WRONG: waste time and create latency

CORRECT: Skip safety gate, extract mode argument, execute
```

#### ❌ MISTAKE #3: Sending "kirim" to Claude as Text

```
User says: "kirim"
Jarvis: classify as CommandInput
WRONG: apply prompt wrapping: "[CODING] kirim"
WRONG: send to Claude CLI: "type: [CODING] kirim"
WRONG: Claude processes as user input

CORRECT: execute command directly, do NOT send to Claude
```

---

## Command Execution Boundary Contract

### What Happens at the Boundary

**Input**: `InputEvent(input_type="command", ...)`

**Output**: `CommandResult(success, display, side_effects)`

```python
class CommandResult:
    success: bool                 # Did command execute successfully?
    display: str                  # UI message to show user
    side_effects: Dict[str, Any]  # State changes (e.g., mode set)
    next_state: str               # e.g., "ready_for_input"
```

**Execution Contract**:
1. Extract command name (deterministically)
2. Validate arguments (if applicable)
3. Execute action (kirim → press Enter, mode → set session mode, etc.)
4. Return CommandResult
5. Display feedback to user
6. Return to ready state

---

## Allowed & Forbidden

### ✅ ALLOWED at Command Execution Boundary

- Command parsing and validation
- Executing command actions (press Enter, set mode, display help)
- Updating session state (e.g., mode change)
- Displaying user-facing feedback
- Returning to ready state
- Logging command execution (for metrics)

### ❌ FORBIDDEN at Command Execution Boundary

- Sending command text to Claude CLI as input
- Running command output through safety gate
- Applying mode wrapping to commands
- Semantic interpretation of command
- Network calls (except Phase 2 placeholder commands)
- Modifying command behavior based on context
- Auto-executing next action (commands are atomic)

---

## Five Concrete Scenarios

### Scenario 1: Valid Command Execution (kirim) - PASS

```
InputEvent(
  input_type="command",
  command="kirim",
  text="kirim"
)

Flow:
  T0: Route to command_executor
  T1: Parse: command="kirim" ✅
  T2: Validate: no arguments needed ✅
  T3: Execute: press_enter_in_cli() → Enter key sent to Claude CLI
  T4: Result:
      CommandResult(
        success=True,
        display="Sent ✓",
        side_effects={"enter_pressed": True}
      )
  T5: Return to ready state

Result: ✅ PASS
        Command executed directly
        NOT sent to Claude as text
        NOT scanned for safety
```

---

### Scenario 2: Valid Command with Argument Validation (mode) - PASS

```
InputEvent(
  input_type="command",
  command="mode",
  arguments={"mode": "coding"}
)

Flow:
  T0: Route to command_executor
  T1: Parse: command="mode", mode_value="coding" ✅
  T2: Validate:
      "coding" ∈ ["default", "coding", "debug", "explain"] ✅
  T3: Execute: session.mode = "coding"
  T4: Result:
      CommandResult(
        success=True,
        display="🔵 CODING MODE",
        side_effects={"mode": "coding"}
      )
  T5: Return to ready state
  T6: Next voice input will be wrapped with "[CODING]" prefix

Result: ✅ PASS
        Mode changed immediately
        Affects next voice input
        NOT sent to Claude
```

---

### Scenario 3: Invalid Mode Argument (mode python) - COMMAND EXECUTOR REJECTS

```
InputEvent(
  input_type="command",
  command="mode",
  arguments={"mode": "python"}
)

Flow:
  T0: Route to command_executor
  T1: Parse: command="mode", mode_value="python"
  T2: Validate:
      "python" ∉ ["default", "coding", "debug", "explain"] ❌
  T3: Execute: invalid mode detected
  T4: Return CommandResult(
        success=False,
        display="Unknown mode 'python'. Modes: default, coding, debug, explain"
      )
  T5: Display error message to user

NOTE: Re-classification to VoiceInput happens at the INPUT BOUNDARY (L1-DEC-001),
not inside the command executor. The executor's job is to accept valid CommandInput
and execute it. If the command is invalid at parsing stage, the Input Boundary
should have re-classified it as VoiceInput before routing here.

Result: ⚠️ FAIL (invalid command)
        Executor returns error result
        User sees message
        Ready for next input
```

---

### Scenario 4: Accidental Dangerous Pattern in Voice Input - BLOCKED

```
User: [Says: "explain how to rm -rf safely"]

InputEvent(
  input_type="voice",
  text="explain how to rm -rf safely"
)

Flow:
  T0: Route to safety_gate (NOT command_executor)
  T1: Parse: NOT a command ✓
  T2: Safety scan: "rm -rf" detected → DANGER ⚠️
  T3: Action: Show confirmation dialog
      "Destructive operation detected: rm -rf
       Continue? [Y] [N]"
  T4a: IF user [Y]:
       Send to Claude: "explain how to rm -rf safely"
  T4b: IF user [N]:
       Display: "Operation canceled"
       Return to ready state

Result: ✅ PASS
        Safety gate protects against accident
        User can still proceed with intention
        Command path would have SKIPPED this gate
```

---

### Scenario 5: Rapid Command Sequence - ATOMIC

```
User: [Says: "mode coding"]
       Immediately [Says: "build a function"]

T0: InputEvent(type="command", command="mode", arguments={mode: "coding"})
    → Route to command_executor
    → Execute: session.mode = "coding"
    → Return CommandResult(success=True)

T1: InputEvent(type="voice", text="build a function")
    → Route to safety_gate
    → No danger detected
    → Apply mode wrapping: "[CODING] build a function"
    → Send to Claude CLI

Result: ✅ PASS
        Commands are atomic (complete before next input processed)
        Mode change is immediate and visible
        Next voice input automatically uses new mode
```

---

## Non-Negotiable Constraints

✅ **MUST HAVE**:
- CommandInput routes to command_executor, NEVER to safety_gate or Claude
- CommandInput NEVER goes through safety scanning
- CommandInput NEVER gets wrapped with mode/prompt shaping
- CommandInput parsing is deterministic (no semantic guessing)
- Invalid commands are re-classified as VoiceInput (fallback to Claude)
- Command execution is atomic (completes before next input accepted)
- Each command has explicit, defined behavior
- Command results displayed to user (not silent)

❌ **MUST NOT HAVE**:
- Commands sent to Claude CLI as text
- Commands scanned for safety patterns
- Commands getting mode wrapping
- Semantic interpretation of command meaning
- Auto-retry of failed commands
- Silent command execution (must display result)
- Commands that modify Claude behavior without user knowing
- Mixing command and voice paths

---

## Contract Violations (Examples of What NOT to Do)

### ❌ VIOLATION #1: Command Through Safety Gate

```
WRONG:
  CommandInput("kirim")
  → route to safety_gate
  → scan "kirim" (unnecessary)
  → delay execution

CORRECT:
  CommandInput("kirim")
  → route to command_executor
  → skip safety gate
  → execute immediately
```

### ❌ VIOLATION #2: Command Sent to Claude

```
WRONG:
  CommandInput("mode coding")
  → apply mode wrapping: "[CODING] mode coding"
  → send to Claude CLI
  → Claude sees user input: "mode coding"

CORRECT:
  CommandInput("mode coding")
  → execute: session.mode = "coding"
  → return to ready state
  → display: "🔵 CODING MODE"
  → do NOT send to Claude
```

### ❌ VIOLATION #3: Voice Input Skips Safety

```
WRONG:
  VoiceInput("rm -rf /")
  → skip safety_gate
  → send directly to Claude

CORRECT:
  VoiceInput("rm -rf /")
  → route to safety_gate
  → detect danger
  → ask confirmation
  → THEN send to Claude (if approved)
```

---

## Relationship to Other Layers

**Layer 0 (DEC-001, DEC-003)**:
- DEC-001: defines audio pipeline, produces transcript
- DEC-003: defines command grammar (what matches as command)
- This contract consumes those and enforces divergence

**Layer 2 (will define)**:
- Safety gate (consumes VoiceInput, NOT CommandInput)
- Prompt shaper (consumes VoiceInput, NOT CommandInput)
- CLI adapter (receives command results or wrapped voice)

**Layer 3 (will implement)**:
- command_executor function/class
- Route switching logic
- Mode setting in session state

---

## Summary Table

| Aspect | CommandInput | VoiceInput |
|--------|-------------|-----------|
| Route | command_executor | safety_gate |
| Safety scan | ❌ NO | ✅ YES |
| Mode wrap | ❌ NO | ✅ YES |
| Send to Claude | ❌ NO | ✅ YES (if approved) |
| Execution | Direct, atomic | Conditional on safety |
| Result | CommandResult | Text to Claude |

---

**Next**: JARVIS-L1-DEC-003 (Prompt Shaping Contract)

